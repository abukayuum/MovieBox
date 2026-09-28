import os
import shutil
import subprocess
from typing import List, Optional

try:
    from .proxy import get_proxy_stream_url
except ImportError:
    get_proxy_stream_url = None


def find_vlc_path() -> Optional[str]:
    vlc_cmd = shutil.which("vlc")
    if vlc_cmd:
        return vlc_cmd

    default_paths = [
        os.path.expandvars(r"%ProgramFiles%\VideoLAN\VLC\vlc.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"),
    ]
    for path in default_paths:
        if os.path.isfile(path):
            return path
    return None


def is_vlc_available() -> bool:
    return find_vlc_path() is not None


def _get_release_field(release, field, default=None):
    if isinstance(release, dict):
        return release.get(field, default)
    return getattr(release, field, default)


def resolve_media_url(release, stream_url: Optional[str] = None) -> Optional[str]:
    target_url = stream_url or _get_release_field(release, "direct_url") or _get_release_field(release, "stream_url") or _get_release_field(release, "url") or ""
    headers = _get_release_field(release, "headers") or {}

    # android.py er moto proxy call kora
    if get_proxy_stream_url and (headers or "/dash/" in str(target_url) or str(target_url).endswith(".mpd")):
        try:
            target_url = get_proxy_stream_url(target_url, headers)
        except Exception:
            pass

    return str(target_url) if target_url else None


def build_vlc_command(release, title: Optional[str] = None, stream_url: Optional[str] = None) -> List[str]:
    vlc_bin = find_vlc_path() or "vlc"
    url = resolve_media_url(release, stream_url=stream_url)

    if not url:
        return []

    cmd = [vlc_bin, url]

    t = title or _get_release_field(release, "filename") or _get_release_field(release, "title")
    if t:
        cmd.extend(["--meta-title", str(t)])

    return cmd


def play_vlc(release, stream_url: Optional[str] = None, title: Optional[str] = None) -> bool:
    vlc_bin = find_vlc_path()
    if not vlc_bin:
        return False

    url = resolve_media_url(release, stream_url=stream_url)
    if not url:
        return False

    cmd = [vlc_bin, url]

    t = title or _get_release_field(release, "filename") or _get_release_field(release, "title")
    if t:
        cmd.extend(["--meta-title", str(t)])

    try:
        vlc_dir = os.path.dirname(vlc_bin)
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "DETACHED_PROCESS", 0)

        subprocess.Popen(
            cmd,
            cwd=vlc_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return True
    except Exception as e:
        print(f"Error launching VLC: {e}")
        return False


class VLCPlayer:
    def __init__(self, executable_path: Optional[str] = None):
        self.executable_path = executable_path or find_vlc_path()

    def is_available(self) -> bool:
        return is_vlc_available()

    def play(self, release, title: Optional[str] = None, stream_url: Optional[str] = None) -> bool:
        return play_vlc(release, stream_url=stream_url, title=title)