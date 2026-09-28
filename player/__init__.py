from typing import List, Optional
from .mpv import is_mpv_available, play_mpv, build_mpv_command
from .android import is_android_termux, is_android_intent_available, play_android_intent, build_android_intent_command
from .vlc import VLCPlayer, is_vlc_available, play_vlc, build_vlc_command


def is_player_available(name: str) -> bool:
    """Checks if requested player is available on current system."""
    p = str(name).lower().strip()
    if p == "mpv":
        return is_mpv_available()
    if p == "vlc":
        return is_vlc_available()
    if p in ("intent", "mx", "android"):
        return is_android_intent_available()
    return False


def list_available_players() -> List[str]:
    """Lists installed or usable video player engines."""
    available = []
    if is_vlc_available():
        available.append("vlc")
    if is_mpv_available():
        available.append("mpv")
    if is_android_intent_available():
        available.append("intent")
    if not available:
        available = ["vlc", "mpv", "intent"]
    return available


def play_media(release, player_name: Optional[str] = None, stream_url: Optional[str] = None, title: Optional[str] = None) -> bool:
    """Dispatches media playback to the designated or best available player."""
    default_player = "intent" if is_android_termux() else ("vlc" if is_vlc_available() else "mpv")
    p = (player_name or default_player).lower().strip()

    if p == "vlc" and is_vlc_available():
        return play_vlc(release, stream_url=stream_url, title=title)
    if p == "mpv" and is_mpv_available():
        return play_mpv(release, stream_url=stream_url, title=title)
    if p in ("intent", "mx", "android") or is_android_termux():
        pkg = "com.mxtech.videoplayer.ad" if p == "mx" else None
        return play_android_intent(release, target_package=pkg, stream_url=stream_url, title=title)

    # Fallback player attempts
    if is_vlc_available():
        return play_vlc(release, stream_url=stream_url, title=title)
    return play_mpv(release, stream_url=stream_url, title=title)


def get_player(name: Optional[str] = None):
    """Returns player controller dictionary for procedural invocation."""
    default_player = "intent" if is_android_termux() else ("vlc" if is_vlc_available() else "mpv")
    p = (name or default_player).lower().strip()

    def _build_command(release, title=None):
        if p == "vlc":
            return build_vlc_command(release, title=title)
        if p == "mpv":
            return build_mpv_command(release, title=title)
        return build_android_intent_command(release, title=title)

    return {
        "name": p,
        "play": lambda release, title=None: play_media(release, player_name=p, title=title),
        "build_command": _build_command,
        "is_available": lambda: is_player_available(p),
    }


__all__ = [
    "is_player_available",
    "list_available_players",
    "play_media",
    "get_player",
    "play_mpv",
    "play_vlc",
    "play_android_intent",
    "build_mpv_command",
    "build_vlc_command",
    "build_android_intent_command",
    "VLCPlayer",
]