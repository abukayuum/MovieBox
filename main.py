#!/usr/bin/env python3

from pathlib import Path
import sys

from cli import create_parser
from config import APP_NAME, APP_VERSION
from player import get_player, play_media, is_android_termux
from player.downloader import download_release
from providers import get_provider, list_providers
from tui import run_tui_app

# ANSI Color Codes for terminal formatting
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _get_val(obj, key, default=None):
    """Helper to read value from dictionary or object seamlessly."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def print_table(headers, rows, title=None):
    """Prints a cleanly aligned table using pure standard Python string methods."""
    if title:
        print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")
    if not rows:
        print("  (No rows)")
        return

    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for r in rows:
        for i in range(min(len(r), cols)):
            widths[i] = max(widths[i], len(str(r[i])))

    header_str = " | ".join(str(headers[i]).ljust(widths[i]) for i in range(cols))
    sep_str = "-+-".join("-" * widths[i] for i in range(cols))
    print(f"{BOLD}{header_str}{RESET}")
    print(f"{DIM}{sep_str}{RESET}")
    for r in rows:
        row_str = " | ".join(str(r[i] if i < len(r) else "").ljust(widths[i]) for i in range(cols))
        print(row_str)
    print()


def print_panel(content, title=None):
    """Prints a bordered box using simple pure Python formatting."""
    width = 72
    if title:
        header_text = f"+-- [ {title} ] "
        line_len = max(0, width - len(header_text))
        print(f"\n{BOLD}{CYAN}{header_text}{'-' * line_len}+{RESET}")
    else:
        print(f"\n{DIM}+{'-' * (width - 2)}+{RESET}")

    for line in str(content).split("\n"):
        print(f"| {line}")
    print(f"{DIM}+{'-' * (width - 2)}+{RESET}\n")


def run_search(query: str, provider_name: str = None, page: int = 1):
    provider = get_provider(provider_name)
    label = _get_val(provider, "label", "Provider")
    search_fn = _get_val(provider, "search")

    print(f"{CYAN}Searching '{query}' on {label}...{RESET}")
    results = search_fn(query, page=page) if search_fn else []
    if not results:
        print(f"{YELLOW}No items found for '{query}'.{RESET}")
        return

    headers = ["ID", "Type", "Title", "Year", "Rating"]
    rows = []
    for item in results:
        m_type = _get_val(item, "media_type", "movie")
        t_str = "SERIES" if m_type == "series" else "MOVIE"
        item_id = _get_val(item, "id", "")
        # Truncate long IDs for neat terminal display
        short_id = item_id if len(item_id) <= 24 else item_id[:21] + "..."
        title = _get_val(item, "title", "Untitled")
        year = _get_val(item, "year") or "N/A"
        rating = _get_val(item, "rating") or "N/A"
        rows.append([short_id, t_str, title, str(year), str(rating)])

    print_table(headers, rows, title=f"Search Results for '{query}' ({len(results)} items)")


def run_details(media_id: str, provider_name: str = None):
    provider = get_provider(provider_name)
    details_fn = _get_val(provider, "get_details")
    details = details_fn(media_id) if details_fn else None

    if not details:
        print(f"{RED}Could not retrieve details for ID {media_id}{RESET}")
        return

    title = _get_val(details, "title", "Untitled")
    year = _get_val(details, "year") or "N/A"
    m_type = _get_val(details, "media_type", "movie")
    rating = _get_val(details, "imdb_rating") or "N/A"
    genres = _get_val(details, "genres") or []
    genres_str = ", ".join(genres) if isinstance(genres, (list, tuple)) else str(genres)
    desc = _get_val(details, "description") or "No overview available"
    seasons = _get_val(details, "seasons") or []

    panel_body = (
        f"{BOLD}{title}{RESET} ({year})\n\n"
        f"Type: {str(m_type).upper()} | Rating: {rating}\n"
        f"Genres: {genres_str or 'N/A'}\n"
        f"Synopsis: {desc}\n"
        f"Seasons: {len(seasons)} available"
    )
    print_panel(panel_body, title="Media Overview")


def run_streams(media_id: str, season: int = 0, episode: int = 0, provider_name: str = None):
    provider = get_provider(provider_name)
    streams_fn = _get_val(provider, "get_streams")
    releases = streams_fn(media_id, season=season, episode=episode) if streams_fn else []

    if not releases:
        print(f"{YELLOW}No stream links found for this item.{RESET}")
        return

    headers = ["Quality", "Codec", "Title / Mirror", "URL"]
    rows = []
    for r in releases:
        quality = _get_val(r, "quality") or "HD"
        codec = _get_val(r, "codec") or "MP4"
        filename = _get_val(r, "filename") or "Stream"
        url = _get_val(r, "direct_url") or "N/A"
        short_url = url[:45] + ("..." if len(url) > 45 else "")
        rows.append([str(quality), str(codec), str(filename), short_url])

    print_table(headers, rows, title=f"Streams for {media_id} (S{season}E{episode})")


def run_play(media_id: str, season: int = 0, episode: int = 0, player_name: str = None, provider_name: str = None):
    provider = get_provider(provider_name)
    streams_fn = _get_val(provider, "get_streams")
    releases = streams_fn(media_id, season=season, episode=episode) if streams_fn else []

    if not releases:
        print(f"{RED}No streamable links found.{RESET}")
        return

    chosen = releases[0]
    filename = _get_val(chosen, "filename", "Movie")
    target_player = (player_name or ("intent" if is_android_termux() else "vlc")).lower().strip()

    print(f"{GREEN}Starting stream: {filename}{RESET}")
    print(f"{CYAN}Target Player Engine: {target_player.upper()}{RESET}")

    success = play_media(chosen, player_name=target_player, title=filename)
    if not success and target_player != "intent" and is_android_termux():
        print(f"{YELLOW}Falling back to Android Video Player Intent Chooser...{RESET}")
        success = play_media(chosen, player_name="intent", title=filename)

    if success:
        print(f"{GREEN}✔ Stream dispatched to player successfully!{RESET}")
    else:
        d_url = _get_val(chosen, "direct_url", "N/A")
        print(f"{YELLOW}Could not launch video player directly.{RESET}")
        print(f"{CYAN}Stream URL: {d_url}{RESET}")
        print(f"{DIM}Tip: On Android Termux, install VLC and run: termux-open <m3u_file> or python3 main.py play <id> --player intent{RESET}")


def run_download(media_id: str, season: int = 0, episode: int = 0, output: str = None, provider_name: str = None):
    provider = get_provider(provider_name)
    streams_fn = _get_val(provider, "get_streams")
    releases = streams_fn(media_id, season=season, episode=episode) if streams_fn else []

    if not releases:
        print(f"{RED}No download links found for this item.{RESET}")
        return

    chosen = releases[0]
    d_url = _get_val(chosen, "direct_url", "")
    fn = _get_val(chosen, "filename", f"video_{media_id}")

    ext = ".mp4" if (d_url and (".mpd" in d_url or "/dash/" in d_url)) else ".mkv"
    safe_name = "".join(c for c in fn if c.isalnum() or c in (" ", "-", "_", ".")).rstrip()
    if not safe_name:
        safe_name = f"video_{media_id}"
    if not safe_name.lower().endswith((".mp4", ".mkv", ".ts")):
        safe_name += ext

    out_path = Path(output) if output else Path("./downloads") / safe_name
    print(f"{GREEN}Downloading '{fn}' to {out_path}...{RESET}")
    success = download_release(chosen, out_path)
    if success:
        print(f"{GREEN}✔ Download completed: {out_path}{RESET}")
    else:
        print(f"{RED}✘ Download failed.{RESET}")


def run_providers():
    providers = list_providers()
    headers = ["Identifier", "Label", "Series Support", "Subtitles Support"]
    rows = []
    for p in providers:
        rows.append([
            p["name"],
            p["label"],
            "YES" if p.get("supports_series") else "NO",
            "YES" if p.get("supports_subtitles") else "NO",
        ])
    print_table(headers, rows, title="Registered Streaming Providers")


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command or args.command == "tui":
        run_tui_app()
    elif args.command == "search":
        run_search(args.query, provider_name=args.provider, page=args.page)
    elif args.command == "details":
        run_details(args.id, provider_name=args.provider)
    elif args.command == "streams":
        run_streams(args.id, season=args.season, episode=args.episode, provider_name=args.provider)
    elif args.command == "play":
        run_play(args.id, season=args.season, episode=args.episode, player_name=args.player, provider_name=args.provider)
    elif args.command == "download":
        run_download(args.id, season=args.season, episode=args.episode, output=args.output, provider_name=args.provider)
    elif args.command == "providers":
        run_providers()

print(f"{BOLD}{CYAN}{APP_NAME} v{APP_VERSION}{RESET}")
print(f"{BOLD}{CYAN}{APP_NAME} v{APP_VERSION}{RESET}")
if __name__ == "__main__":
    main()
