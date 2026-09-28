"""
MovieBox HTTP Client (Basic Procedural Python - No Classes)
Maintains session state, host pool rotation, and cryptographic request dispatching using pure functions.
"""
import json
import logging
import time
from typing import Any, Dict, Optional
import requests
from . import crypto, session

logger = logging.getLogger("moviebox.client")

HOST_POOL = [
    "https://api6.aoneroom.com",
    "https://api5.aoneroom.com",
    "https://api4.aoneroom.com",
    "https://api4sg.aoneroom.com",
    "https://api3.aoneroom.com",
    "https://api6sg.aoneroom.com",
    "https://api.inmoviebox.com",
]

RETRY_STATUS_CODES = {403, 406, 407, 429, 500, 502, 503, 504}

# Global client state dictionary
_CLIENT_STATE = {
    "session": None,
    "active_host_idx": 0,
    "user_agent": None,
    "client_info": None,
    "spoofed_ip": None,
    "http": None,
}


def get_client_state():
    """Initializes or returns singleton client state dictionary."""
    if _CLIENT_STATE["http"] is None:
        ua, cinfo = crypto.generate_client_info_and_ua()
        _CLIENT_STATE["user_agent"] = ua
        _CLIENT_STATE["client_info"] = cinfo
        _CLIENT_STATE["spoofed_ip"] = crypto.random_spoofed_ip()
        s = requests.Session()
        s.headers.update({"User-Agent": ua})
        _CLIENT_STATE["http"] = s
    return _CLIENT_STATE


def ensure_session() -> str:
    """Ensures an active, valid session token is ready."""
    state = get_client_state()

    # 1. In-memory check
    if state["session"] and session.is_session_valid(state["session"]):
        return state["session"]["token"]

    # 2. Disk cache check
    persisted = session.load_persisted_session()
    if persisted and session.is_session_valid(persisted):
        state["session"] = persisted
        return persisted["token"]

    # 3. Request fresh visitor token
    fresh = fetch_fresh_session()
    state["session"] = fresh
    session.save_session(fresh)
    return fresh["token"]


def fetch_fresh_session() -> dict:
    """Calls visitor login endpoint to retrieve authentication JWT."""
    path = "/wefeed-mobile-bff/user-api/visitor-login"
    resp_data = request_hosts("POST", path, body="{}")
    token = resp_data.get("token") or (resp_data.get("data", {}).get("token") if isinstance(resp_data.get("data"), dict) else None)
    if not token:
        raise RuntimeError("Failed to obtain visitor token from MovieBox API")

    uid = str(resp_data.get("uid") or resp_data.get("userId") or "")
    return session.make_moviebox_session(token=token, user_id=uid)


def invalidate_session() -> None:
    """Clears memory and disk session cache."""
    state = get_client_state()
    state["session"] = None
    session.clear_persisted_session()


def request_hosts(
    method: str,
    path: str,
    body: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatches request across HOST_POOL with automatic failover."""
    state = get_client_state()
    start_idx = state["active_host_idx"]
    num_hosts = len(HOST_POOL)

    for attempt in range(num_hosts):
        idx = (start_idx + attempt) % num_hosts
        base_url = HOST_POOL[idx]
        url = f"{base_url}{path}"

        headers = crypto.build_signed_headers(
            method=method,
            url=url,
            body=body,
            auth_token=auth_token,
            user_agent=state["user_agent"],
            client_info=state["client_info"],
            spoofed_ip=state["spoofed_ip"],
        )

        try:
            if method.upper() == "POST":
                resp = state["http"].post(
                    url,
                    data=body.encode("utf-8") if body else None,
                    headers=headers,
                    timeout=8,
                )
            else:
                resp = state["http"].get(url, headers=headers, timeout=8)

            # Check x-user header for updated tokens
            x_user = resp.headers.get("x-user")
            if x_user:
                try:
                    x_user_data = json.loads(x_user)
                    new_tok = x_user_data.get("token")
                    if new_tok:
                        state["session"] = session.make_moviebox_session(new_tok)
                        session.save_session(state["session"])
                except Exception:
                    pass

            if resp.status_code in RETRY_STATUS_CODES:
                logger.warning("MovieBox host %s returned status %d", base_url, resp.status_code)
                time.sleep(0.05)
                continue

            resp.raise_for_status()
            data = resp.json()

            # Mark this host as active for future requests
            state["active_host_idx"] = idx

            # Unwrap {"code": 0, "data": ...}
            if isinstance(data, dict) and "data" in data and data.get("code") == 0:
                return data["data"]
            return data

        except Exception as e:
            logger.debug("Request to %s failed: %s", url, e)
            continue

    raise RuntimeError("All MovieBox API hosts exhausted or unreachable")


def request(
    method: str,
    path: str,
    body: Optional[str] = None,
    authenticated: bool = True,
) -> Dict[str, Any]:
    """Authenticated request wrapper with automatic retry on token expiration."""
    token = ensure_session() if authenticated else None
    try:
        return request_hosts(method, path, body=body, auth_token=token)
    except Exception:
        # Invalidate session and retry once
        invalidate_session()
        token = ensure_session() if authenticated else None
        return request_hosts(method, path, body=body, auth_token=token)


def moviebox_api_search(query: str, page: int = 1, per_page: int = 15) -> Dict[str, Any]:
    """Searches movies and TV series."""
    path = "/wefeed-mobile-bff/subject-api/search/v2"
    payload = json.dumps(
        {
            "keyword": query,
            "page": page,
            "perPage": per_page,
            "subjectType": 0,
        },
        separators=(",", ":"),
    )
    return request("POST", path, body=payload)


def moviebox_api_get_details(subject_id: str) -> Dict[str, Any]:
    """Fetches metadata, overview, cast, and season numbers."""
    path = f"/wefeed-mobile-bff/subject-api/get?subjectId={subject_id}"
    details = request("GET", path)

    # If it's a TV series, fetch full season episodes list
    stype = details.get("subjectType") or details.get("stype") or 1
    if stype == 2:
        season_path = f"/wefeed-mobile-bff/subject-api/season-info?subjectId={subject_id}"
        try:
            season_info = request("GET", season_path)
            details["seasons"] = season_info
        except Exception:
            pass

    return details


def moviebox_api_get_play_info(subject_id: str, season: int = 0, episode: int = 0) -> Dict[str, Any]:
    """Fetches primary direct streams with resolutions and cookies."""
    if season == 0 and episode == 0:
        path = f"/wefeed-mobile-bff/subject-api/play-info/v2?subjectId={subject_id}"
    else:
        path = (
            f"/wefeed-mobile-bff/subject-api/play-info/v2?subjectId={subject_id}"
            f"&se={season}&ep={episode}"
        )
    return request("GET", path)


def moviebox_api_get_resources(
    subject_id: str,
    season: int = 0,
    episode: int = 0,
    page: int = 1,
    per_page: int = 20,
) -> Dict[str, Any]:
    """Fetches secondary community mirrors and resource links."""
    if season == 0 and episode == 0:
        path = f"/wefeed-mobile-bff/subject-api/resource?subjectId={subject_id}&page={page}&perPage={per_page}"
    else:
        path = (
            f"/wefeed-mobile-bff/subject-api/resource?subjectId={subject_id}"
            f"&se={season}&ep={episode}&page={page}&perPage={per_page}"
        )
    return request("GET", path)


def moviebox_api_get_ext_captions(subject_id: str, resource_id: str) -> Dict[str, Any]:
    """Fetches external subtitles."""
    path = f"/wefeed-mobile-bff/subject-api/get-ext-captions?subjectId={subject_id}&resourceId={resource_id}"
    return request("GET", path)


def MovieBoxClient():
    """Functional client helper returning MovieBox API methods."""
    return {
        "ensure_session": ensure_session,
        "search": moviebox_api_search,
        "get_details": moviebox_api_get_details,
        "get_play_info": moviebox_api_get_play_info,
        "get_resources": moviebox_api_get_resources,
        "get_ext_captions": moviebox_api_get_ext_captions,
    }

