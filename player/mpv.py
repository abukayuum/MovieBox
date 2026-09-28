import shutil
import subprocess
from typing import List, Optional


def is_mpv_available() -> bool:
    """Checks if mpv binary exists in PATH."""
    return shutil.which("mpv") is not None


def _get_release_field(release, field, default=None):
    if isinstance(release, dict):
        return release.get(field, default)
    return getattr(release, field, default)


def build_mpv_command(release, stream_url: Optional[str] = None, title: Optional[str] = None) -> List[str]:
    """Constructs mpv CLI command array."""
    target_url = stream_url or _get_release_field(release, "direct_url") or ""
    cmd = ["mpv"]

    display_title = title or _get_release_field(release, "filename")
    if display_title:
        cmd.append(f"--force-media-title={display_title}")

    headers = _get_release_field(release, "headers") or {}
    header_fields = []
    for k, v in headers.items():
        header_fields.append(f"{k}: {v}")

    if header_fields:
        cmd.append(f"--http-header-fields={','.join(header_fields)}")

    subtitles = _get_release_field(release, "subtitles") or []
    for sub in subtitles[:3]:
        sub_url = sub.get("url") if isinstance(sub, dict) else getattr(sub, "url", None)
        if sub_url:
            cmd.append(f"--sub-file={sub_url}")

    quality = _get_release_field(release, "quality")
    if quality and str(quality).endswith("p"):
        try:
            res_height = int(str(quality)[:-1])
            cmd.append(f"--ytdl-format=bestvideo[height<={res_height}]+bestaudio/best[height<={res_height}]/best")
        except Exception:
            pass

    cmd.append(target_url)
    return cmd


def play_mpv(release, stream_url: Optional[str] = None, title: Optional[str] = None) -> bool:
    """Launches mpv player."""
    cmd = build_mpv_command(release, stream_url=stream_url, title=title)
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False
