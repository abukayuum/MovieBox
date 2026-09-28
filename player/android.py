import os
import shutil
import subprocess
from typing import List, Optional


def is_android_termux() -> bool:
    """Checks if running inside Android Termux environment."""
    return (
        os.path.exists("/data/data/com.termux")
        or "TERMUX_VERSION" in os.environ
        or shutil.which("termux-open-url") is not None
        or shutil.which("termux-open") is not None
        or shutil.which("am") is not None
    )


def is_android_intent_available() -> bool:
    """Checks if Android intent launcher is available."""
    if is_android_termux():
        return True
    return (
        shutil.which("am") is not None
        or shutil.which("termux-open-url") is not None
        or shutil.which("termux-open") is not None
    )


def _get_release_field(release, field, default=None):
    if isinstance(release, dict):
        return release.get(field, default)
    return getattr(release, field, default)


def build_android_intent_command(
    release,
    target_package: Optional[str] = None,
    stream_url: Optional[str] = None,
    title: Optional[str] = None,
) -> List[str]:
    """Builds Android Activity Manager (am start) CLI command."""
    target_url = stream_url or _get_release_field(release, "direct_url") or ""
    headers = _get_release_field(release, "headers") or {}

    if headers and ("Cookie" in headers or "/dash/" in target_url or target_url.endswith(".mpd")):
        try:
            from .proxy import get_proxy_stream_url
            target_url = get_proxy_stream_url(target_url, headers)
        except Exception:
            pass

    am_bin = shutil.which("am") or "/system/bin/am"

    cmd = [
        am_bin, "start",
        "-a", "android.intent.action.VIEW",
        "-d", target_url,
        "-t", "video/*",
    ]

    if target_package:
        cmd.extend(["-p", target_package])

    header_lines = []
    if "Referer" in headers:
        header_lines.append(f"Referer: {headers['Referer']}")
        cmd.extend(["--es", "Referer", headers["Referer"]])
        cmd.extend(["--es", "http-referrer", headers["Referer"]])
    if "User-Agent" in headers:
        header_lines.append(f"User-Agent: {headers['User-Agent']}")
        cmd.extend(["--es", "User-Agent", headers["User-Agent"]])
    if "Cookie" in headers:
        header_lines.append(f"Cookie: {headers['Cookie']}")
        cmd.extend(["--es", "Cookie", headers["Cookie"]])

    if header_lines:
        cmd.extend(["--esa", "android.media.intent.extra.HTTP_HEADERS", ",".join(header_lines)])

    filename = _get_release_field(release, "filename")
    if title or filename:
        cmd.extend(["--es", "title", title or filename])

    return cmd


def play_android_intent(
    release,
    target_package: Optional[str] = None,
    stream_url: Optional[str] = None,
    title: Optional[str] = None,
) -> bool:
    """Launches stream on Android."""
    target_url = stream_url or _get_release_field(release, "direct_url") or ""

    cmd = build_android_intent_command(release, target_package=target_package, stream_url=stream_url, title=title)
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if res.returncode == 0:
            return True
    except Exception:
        pass

    if shutil.which("termux-open-url"):
        try:
            subprocess.Popen(["termux-open-url", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    if shutil.which("termux-open"):
        try:
            subprocess.Popen(["termux-open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    if shutil.which("xdg-open"):
        try:
            subprocess.Popen(["xdg-open", target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    return False
