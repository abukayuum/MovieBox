"""
MovieBox Session and JWT Claims Management (Basic Procedural Python - No Classes)
Handles visitor login sessions, JWT expiration checks, and disk caching with plain dicts.
"""
import base64
import json
import time
from pathlib import Path
from config import CACHE_DIR

SESSION_FILE = Path(CACHE_DIR) / "moviebox_session.json"


def parse_jwt_claims(token: str):
    """Decodes JWT payload safely using standard base64 and parses userId and exp."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None, None
        payload_b64 = parts[1]
        pad_len = (4 - (len(payload_b64) % 4)) % 4
        padded = payload_b64 + ("=" * pad_len)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))

        uid = str(payload.get("userId") or payload.get("uid") or payload.get("sub") or "")
        exp = payload.get("exp")
        if exp is not None:
            exp = int(exp)
        return (uid if uid else None), exp
    except Exception:
        return None, None


def make_moviebox_session(token: str, user_id=None):
    """Creates a session dictionary."""
    uid, exp = parse_jwt_claims(token)
    return {
        "token": str(token),
        "user_id": str(user_id or uid or ""),
        "expires_at": exp,
        "created_at": int(time.time()),
    }


def is_session_valid(session) -> bool:
    """Checks if a session dictionary is valid and not expired."""
    if not session or not isinstance(session, dict):
        return False
    token = session.get("token")
    if not token or not str(token).strip():
        return False
    now = int(time.time())
    expires_at = session.get("expires_at")
    if expires_at is not None:
        return now + 60 < int(expires_at)
    created_at = session.get("created_at", 0)
    return now < int(created_at) + (7 * 24 * 3600)


def load_persisted_session():
    """Loads session dictionary from local disk cache if valid."""
    try:
        if not SESSION_FILE.exists():
            return None
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            session = json.load(f)
        if is_session_valid(session):
            return session
    except Exception:
        pass
    return None


def save_session(session) -> None:
    """Saves session dictionary to local disk cache."""
    try:
        if not session or not isinstance(session, dict):
            return
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f)
    except Exception:
        pass


def clear_persisted_session() -> None:
    """Deletes cached session."""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
    except Exception:
        pass
