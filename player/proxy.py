"""
Local HTTP Sidecar Proxy (Basic Procedural Python - No Classes)
Solves the issue where external media players (VLC, MX Player) drop authentication cookies/headers on DASH segments.
Implements stream forwarding with pure socket functions.
"""
import base64
import json
import socket
import threading
import urllib.parse
from typing import Dict, Tuple, Optional
import requests

DEFAULT_PROXY_PORT = 8765
_PROXY_LOCK = threading.Lock()
_ACTIVE_PORT: Optional[int] = None
_RUNNING = False


def encode_proxy_token(upstream_url: str, headers: Dict[str, str]) -> str:
    """Encodes upstream URL and authentication headers into a URL-safe Base64 token."""
    payload = {
        "u": str(upstream_url or ""),
        "h": dict(headers or {}),
    }
    dumped = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    return base64.urlsafe_b64encode(dumped).decode("ascii").rstrip("=")


def decode_proxy_token(token: str) -> Tuple[str, Dict[str, str]]:
    """Decodes a URL-safe Base64 token into upstream URL and headers."""
    padding = (4 - (len(token) % 4)) % 4
    padded = token + ("=" * padding)
    raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    data = json.loads(raw)
    return data.get("u", ""), data.get("h", {})


def is_port_in_use(port: int) -> bool:
    """Checks if a local TCP port is already open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def handle_proxy_client(conn: socket.socket):
    """Handles an incoming proxy HTTP connection using pure procedural socket calls."""
    try:
        conn.settimeout(10.0)
        data = conn.recv(4096).decode("utf-8", errors="ignore")
        if not data:
            return

        lines = data.split("\r\n")
        req_line = lines[0] if lines else ""
        parts = req_line.split(" ")
        if len(parts) < 2:
            return
        method, req_path = parts[0], parts[1]

        # Parse client headers
        client_headers = {}
        for line in lines[1:]:
            if not line:
                break
            if ":" in line:
                hk, hv = line.split(":", 1)
                client_headers[hk.strip()] = hv.strip()

        parsed = urllib.parse.urlparse(req_path)
        path = parsed.path.lstrip("/")

        # Expected path format: proxy/h/<token>/<optional_subpath>
        p_parts = path.split("/", 2)
        if len(p_parts) < 2 or p_parts[0] != "proxy" or p_parts[1] != "h":
            resp = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 25\r\n\r\nInvalid proxy path format"
            conn.sendall(resp)
            return

        token_and_sub = p_parts[2] if len(p_parts) > 2 else ""
        t_parts = token_and_sub.split("/", 1)
        token = t_parts[0]
        subpath = t_parts[1] if len(t_parts) > 1 else ""

        try:
            upstream_url, auth_headers = decode_proxy_token(token)
        except Exception:
            resp = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 20\r\n\r\nInvalid proxy token"
            conn.sendall(resp)
            return

        if not upstream_url:
            resp = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 21\r\n\r\nMissing upstream URL"
            conn.sendall(resp)
            return

        target_url = urllib.parse.urljoin(upstream_url, subpath) if subpath else upstream_url

        req_headers = {
            "User-Agent": auth_headers.get("User-Agent", "Mozilla/5.0"),
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        req_headers.update(auth_headers)
        if "Range" in client_headers:
            req_headers["Range"] = client_headers["Range"]

        upstream_resp = requests.request(
            method=method,
            url=target_url,
            headers=req_headers,
            stream=True,
            timeout=15,
            allow_redirects=True,
        )

        status_line = f"HTTP/1.1 {upstream_resp.status_code} OK\r\n"
        resp_headers = [
            status_line,
            "Access-Control-Allow-Origin: *\r\n",
            "Access-Control-Allow-Methods: GET, HEAD, OPTIONS\r\n",
            "Access-Control-Allow-Headers: *\r\n",
        ]

        forward_fields = [
            "Content-Type", "Content-Length", "Content-Range",
            "Accept-Ranges", "Last-Modified", "ETag",
        ]
        for f in forward_fields:
            if f in upstream_resp.headers:
                resp_headers.append(f"{f}: {upstream_resp.headers[f]}\r\n")

        resp_headers.append("\r\n")
        conn.sendall("".join(resp_headers).encode("latin1"))

        if method != "HEAD":
            for chunk in upstream_resp.iter_content(chunk_size=65536):
                if chunk:
                    conn.sendall(chunk)
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _proxy_server_thread(sock: socket.socket):
    global _RUNNING
    while _RUNNING:
        try:
            conn, _ = sock.accept()
            t = threading.Thread(target=handle_proxy_client, args=(conn,), daemon=True)
            t.start()
        except Exception:
            break


def ensure_proxy_running(port: int = DEFAULT_PROXY_PORT) -> int:
    """Ensures local background proxy daemon is running and returns the active port."""
    global _ACTIVE_PORT, _RUNNING
    with _PROXY_LOCK:
        if _ACTIVE_PORT and is_port_in_use(_ACTIVE_PORT):
            return _ACTIVE_PORT

        chosen_port = port
        while chosen_port < port + 50:
            if not is_port_in_use(chosen_port):
                break
            chosen_port += 1

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", chosen_port))
            s.listen(128)
            _RUNNING = True
            _ACTIVE_PORT = chosen_port
            t = threading.Thread(target=_proxy_server_thread, args=(s,), daemon=True)
            t.start()
            return chosen_port
        except Exception:
            _ACTIVE_PORT = chosen_port
            return chosen_port


def get_proxy_stream_url(upstream_url: str, headers: Dict[str, str], host: Optional[str] = None) -> str:
    """
    Generates a hierarchical proxy stream URL for external players.
    Example: http://127.0.0.1:8765/proxy/h/<token>/index.mpd
    """
    token = encode_proxy_token(upstream_url, headers)
    parsed = urllib.parse.urlparse(upstream_url)
    filename = parsed.path.split("/")[-1] or "index.mpd"

    if not host:
        active_port = ensure_proxy_running(DEFAULT_PROXY_PORT)
        host = f"http://127.0.0.1:{active_port}"

    return f"{host.rstrip('/')}/proxy/h/{token}/{filename}"
