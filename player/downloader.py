import os
import shutil
from pathlib import Path
from urllib.parse import urlparse
import yt_dlp


def _get_field(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class QuietLogger:
    """Silences redundant logs and only outputs actionable errors/warnings."""

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(f"\n[Error] {msg}")


def _progress_hook(d):
    """Clean inline progress bar without terminal spam."""
    status = d.get("status")

    if status == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        speed = d.get("speed")
        eta = d.get("eta")

        speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "-- KB/s"
        eta_str = f"{int(eta // 60):02d}:{int(eta % 60):02d}" if eta else "--:--"

        frag_index = d.get("fragment_index")
        frag_count = d.get("fragment_count")

        if frag_index and frag_count:
            pct = (frag_index / frag_count) * 100
            dl_mb = downloaded / (1024 * 1024)
            print(
                f"\r[Downloading] {pct:5.1f}% | Frag: {frag_index}/{frag_count} | {dl_mb:6.1f} MB | {speed_str} | ETA: {eta_str}",
                end="",
                flush=True,
            )
        elif total:
            pct = (downloaded / total) * 100
            dl_mb = downloaded / (1024 * 1024)
            tot_mb = total / (1024 * 1024)
            print(
                f"\r[Downloading] {pct:5.1f}% | {dl_mb:6.1f}/{tot_mb:.1f} MB | {speed_str} | ETA: {eta_str}",
                end="",
                flush=True,
            )
        else:
            dl_mb = downloaded / (1024 * 1024)
            print(f"\r[Downloading] {dl_mb:6.1f} MB | {speed_str}", end="", flush=True)

    elif status == "finished":
        print("\n[Merging] Finalizing downloaded file...")


def download_release(release, output_path: Path) -> bool:
    url = _get_field(release, "direct_url")
    if not url:
        print("[Error] No direct_url found in release data.")
        return False

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure dynamic file extension matching
    outtmpl = str(output_path.with_suffix("")) + ".%(ext)s"

    headers = dict(_get_field(release, "headers") or {})

    # Set dynamic Referer based on the stream URL if not provided by the provider
    if "Referer" not in headers and "referer" not in headers:
        parsed_url = urlparse(url)
        headers["Referer"] = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    # Default generic User-Agent if missing
    if "User-Agent" not in headers and "user-agent" not in headers:
        headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

    cookie_str = headers.pop("cookie", None) or headers.pop("Cookie", None)

    ydl_opts = {
        "outtmpl": outtmpl,
        "http_headers": headers,
        "logger": QuietLogger(),
        "progress_hooks": [_progress_hook],
        "hls_prefer_native": True,          # Use native Python downloader for HLS fragments
        "skip_unavailable_fragments": True, # Avoid failing on missing/corrupt segments
        "fragment_retries": 15,
        "retries": 15,
        "continuedl": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
    }

    # Use ffmpeg for post-processing/merging if available in system PATH
    if shutil.which("ffmpeg"):
        ydl_opts["ffmpeg_location"] = shutil.which("ffmpeg")

    if cookie_str:
        ydl_opts["http_headers"]["Cookie"] = cookie_str

    print(f"\n[Starting Download] -> {output_path.name}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Resolve output file extension and replace incomplete temporary files
        base_dir = output_path.parent
        base_name = output_path.stem
        for f in base_dir.glob(f"{base_name}.*"):
            if not f.name.endswith(".part") and not f.name.endswith(".ytdl"):
                if f.resolve() != output_path.resolve():
                    if output_path.exists():
                        output_path.unlink()
                    f.replace(output_path)
                break

        print("\n[Success] Download complete.")
        return True

    except Exception as e:
        print(f"\n[Error] Download interrupted: {e}")
        return False
