import argparse

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="moviebox",
        description="MovieBox-TUI: Stream Movies, Series & IPTV in your terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # TUI command (default if no command given)
    subparsers.add_parser("tui", help="Launch interactive Terminal User Interface")

    # Search command
    search_p = subparsers.add_parser("search", help="Search for movies or series")
    search_p.add_argument("query", help="Title to search for")
    search_p.add_argument("--provider", "-p", default=None, help="Content provider (moviebox, addons, tv, fourkhdhub)")
    search_p.add_argument("--page", type=int, default=1, help="Page number")

    # Details command
    details_p = subparsers.add_parser("details", help="Get media details by ID")
    details_p.add_argument("id", help="Media or Subject ID")
    details_p.add_argument("--provider", "-p", default=None, help="Content provider")

    # Streams command
    streams_p = subparsers.add_parser("streams", help="Fetch playable stream releases")
    streams_p.add_argument("id", help="Media or Subject ID")
    streams_p.add_argument("--season", "-s", type=int, default=0, help="Season number")
    streams_p.add_argument("--episode", "-e", type=int, default=0, help="Episode number")
    streams_p.add_argument("--provider", "-p", default=None, help="Content provider")

    # Play command
    play_p = subparsers.add_parser("play", help="Directly stream media in video player")
    play_p.add_argument("id", help="Media or Subject ID")
    play_p.add_argument("--season", "-s", type=int, default=0, help="Season number")
    play_p.add_argument("--episode", "-e", type=int, default=0, help="Episode number")
    play_p.add_argument("--player", choices=["vlc", "mpv", "intent", "mx"], default=None, help="Target player (VLC, MPV, Android Intent Chooser, MX Player)")
    play_p.add_argument("--provider", "-p", default=None, help="Content provider")

    # Download command (Termux & PC CLI)
    dl_p = subparsers.add_parser("download", help="Download media to MP4/MKV video file")
    dl_p.add_argument("id", help="Media or Subject ID")
    dl_p.add_argument("--season", "-s", type=int, default=0, help="Season number")
    dl_p.add_argument("--episode", "-e", type=int, default=0, help="Episode number")
    dl_p.add_argument("--output", "-o", default=None, help="Custom output filepath")
    dl_p.add_argument("--provider", "-p", default=None, help="Content provider")

    # TV command
    tv_p = subparsers.add_parser("tv", help="Browse or play Live TV channels")
    tv_p.add_argument("--search", "-s", default=None, help="Search channel name")
    tv_p.add_argument("--category", "-c", default=None, help="Filter by category (Sports, News, Bangla, Movies)")
    tv_p.add_argument("--play", default=None, help="Play channel by exact name or URL")

    # Providers command
    subparsers.add_parser("providers", help="List registered streaming providers")

    return parser
