"""
MovieBox API Cryptography and Signature Engine
Translates the proprietary MovieBox (OneRoom / WeFeed) request signing mechanism into Python.
"""
import base64
import hashlib
import hmac
import json
import random
import time
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qsl, urlparse

DEFAULT_SECRET_BYTES = (
    b"\xef\xa8\x91\x97\x4e\xec\xd3\x14\x8d\xf6\x3a\xa6\x11\x60\x2d\xef"
    b"\xd1\x01\x25\x9b\xa5\x21\x02\x2c\x57\xae\x05\x66\xbd\x8e"
)

SIGNATURE_BODY_MAX_BYTES = 102400

def md5_hex(data: bytes) -> str:
    """Calculates MD5 hex digest for given byte payload."""
    return hashlib.md5(data).hexdigest()

def generate_x_client_token(ts_ms: int) -> str:
    """Generates the x-client-token header combining timestamp and reversed-timestamp MD5."""
    ts_str = str(ts_ms)
    reversed_ts = ts_str[::-1]
    token_hash = md5_hex(reversed_ts.encode("utf-8"))
    return f"{ts_str},{token_hash}"

def sorted_query_string(url: str) -> str:
    """Sorts query parameters deterministically by key for canonical URL calculation."""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return ""
        qsl = parse_qsl(parsed.query, keep_blank_values=True)
        qsl_sorted = sorted(qsl, key=lambda pair: pair[0])
        return "&".join(f"{k}={v}" for k, v in qsl_sorted)
    except Exception:
        return ""

def build_canonical_string(
    method: str,
    accept: str,
    content_type: str,
    url: str,
    body: Optional[str],
    timestamp_ms: int,
) -> str:
    """
    Constructs canonical request string formatted for HMAC signing:
    METHOD\\nACCEPT\\nCONTENT_TYPE\\nBODY_LENGTH\\nTIMESTAMP\\nBODY_HASH\\nCANONICAL_URL
    """
    try:
        parsed = urlparse(url)
        path = parsed.path
        query = sorted_query_string(url)
        canonical_url = f"{path}?{query}" if query else path
    except Exception:
        canonical_url = url

    if body is not None and len(body) > 0:
        body_bytes = body.encode("utf-8")
        body_len = str(len(body_bytes))
        truncated = body_bytes[:SIGNATURE_BODY_MAX_BYTES]
        body_hash = md5_hex(truncated)
    else:
        body_len = ""
        body_hash = ""

    return (
        f"{method.upper()}\n"
        f"{accept}\n"
        f"{content_type}\n"
        f"{body_len}\n"
        f"{timestamp_ms}\n"
        f"{body_hash}\n"
        f"{canonical_url}"
    )

def generate_x_tr_signature(
    method: str,
    accept: str,
    content_type: str,
    url: str,
    body: Optional[str],
    timestamp_ms: int,
) -> str:
    """Produces the base64-encoded HMAC-MD5 signature expected in x-tr-signature."""
    canonical = build_canonical_string(
        method, accept, content_type, url, body, timestamp_ms
    )
    mac = hmac.new(DEFAULT_SECRET_BYTES, canonical.encode("utf-8"), hashlib.md5)
    sig_b64 = base64.b64encode(mac.digest()).decode("ascii")
    return f"{timestamp_ms}|2|{sig_b64}"

def random_hex(length: int) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))

def random_uuid() -> str:
    return f"{random_hex(8)}-{random_hex(4)}-{random_hex(4)}-{random_hex(4)}-{random_hex(12)}"

def random_spoofed_ip() -> str:
    prefixes = [
        "103.241", "49.36", "117.195", "106.198", "122.162",
        "157.32", "182.70", "103.58", "27.60", "59.90",
    ]
    p = random.choice(prefixes)
    return f"{p}.{random.randint(1, 254)}.{random.randint(1, 254)}"

def generate_client_info_and_ua() -> Tuple[str, str]:
    """Generates authentic Android device parameters and matching User-Agent string."""
    android_versions = [
        ("12", "S1B.220414.015"),
        ("13", "TQ2A.230405.003"),
        ("11", "RP1A.200720.011"),
    ]
    redmi_devices = [
        ("22101316G", "Redmi"),
        ("2201117TY", "Redmi"),
        ("23078RKD5C", "Redmi"),
    ]
    version_codes = [50020119, 50020120, 50020121]
    timezones = ["Asia/Kolkata", "Asia/Dhaka", "America/New_York", "Europe/London"]

    android = random.choice(android_versions)
    device = random.choice(redmi_devices)
    v_code = random.choice(version_codes)
    tz = random.choice(timezones)
    gaid = random_uuid()
    device_id = random_hex(32)

    user_agent = (
        f"com.community.oneroom/{v_code} (Linux; U; Android {android[0]}; en_US; "
        f"{device[0]}; Build/{android[1]}; Cronet/135.0.7012.3)"
    )

    client_info_dict = {
        "package_name": "com.community.oneroom",
        "version_name": "4.0.01.0813.03",
        "version_code": v_code,
        "os": "android",
        "os_version": android[0],
        "install_ch": "ps",
        "device_id": device_id,
        "install_store": "ps",
        "gaid": gaid,
        "brand": device[1],
        "model": device[0],
        "system_language": "en",
        "net": "NETWORK_WIFI",
        "region": "US",
        "timezone": tz,
        "sp_code": "40401",
        "X-Play-Mode": "2",
    }
    client_info_json = json.dumps(client_info_dict, separators=(",", ":"))
    return user_agent, client_info_json

def build_signed_headers(
    method: str,
    url: str,
    body: Optional[str] = None,
    auth_token: Optional[str] = None,
    user_agent: Optional[str] = None,
    client_info: Optional[str] = None,
    spoofed_ip: Optional[str] = None,
) -> Dict[str, str]:
    """Generates all verified MovieBox request headers with cryptographic signatures."""
    ts_ms = int(time.time() * 1000)
    accept = "application/json"
    content_type = "application/json"

    client_token = generate_x_client_token(ts_ms)
    signature = generate_x_tr_signature(method, accept, content_type, url, body, ts_ms)

    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Linux; Android 12)",
        "Accept": accept,
        "Content-Type": content_type,
        "Connection": "keep-alive",
        "x-client-token": client_token,
        "x-tr-signature": signature,
        "x-client-info": client_info or "{}",
        "x-client-status": "0",
        "x-forwarded-for": spoofed_ip or random_spoofed_ip(),
    }

    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    return headers
