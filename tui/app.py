import os
from pathlib import Path
import sys
from typing import List, Optional

from config import DEFAULT_PROVIDER, get_config, set_config
from player import get_player, list_available_players, play_media, build_mpv_command
from player.downloader import download_release
from providers import get_provider, list_providers
from .banner import get_banner

# ANSI Styling Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# In-memory TUI state dictionary
_tui_state = {
    "provider_name": DEFAULT_PROVIDER,
    "player_name": get_config("player", "vlc"),
}


def clear_screen():
    """Clears terminal screen using standard OS call."""
    try:
        os.system("clear" if os.name != "nt" else "cls")
    except Exception:
        pass


def print_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None):
    """Prints a cleanly aligned ASCII table using only standard Python."""
    if title:
        print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")
    if not rows:
        print("  (No items found)")
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


def print_panel(content: str, title: Optional[str] = None):
    """Prints a bordered text box using basic Python."""
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


def ask_prompt(msg: str, choices: Optional[List[str]] = None, default: Optional[str] = None) -> str:
    """Standard input helper prompting user."""
    suffix = ""
    if choices:
        suffix += f" [{' / '.join(choices)}]"
    if default is not None:
        suffix += f" (default: {default})"
    prompt_str = f"{CYAN}{msg}{suffix}: {RESET}"
    try:
        val = input(prompt_str).strip()
    except (EOFError, KeyboardInterrupt):
        return default or ""
    if not val and default is not None:
        return str(default)
    if choices and val not in choices:
        return default or val
    return val


def get_tui_state() -> dict:
    """Returns application state dictionary."""
    return _tui_state


def get_active_provider(state: Optional[dict] = None) -> dict:
    st = state or _tui_state
    return get_provider(st.get("provider_name", DEFAULT_PROVIDER))


def get_active_player_name(state: Optional[dict] = None) -> str:
    st = state or _tui_state
    return st.get("player_name", "intent")


def run_tui_app():
    """Main application lifecycle loop (procedural raw Python)."""
    state = _tui_state
    while True:
        clear_screen()
        print(get_banner())

        provider = get_active_provider(state)
        prov_label = provider.get("label") if isinstance(provider, dict) else getattr(provider, "label", "MovieBox")
        player_name = get_active_player_name(state)
        avail = ", ".join(list_available_players()) or "None"

        print(f"{BOLD}Status:{RESET} Provider: {GREEN}{prov_label}{RESET} | Player: {CYAN}{player_name.upper()}{RESET} | Available: {YELLOW}{avail}{RESET}")
        print(f"{DIM}{'-' * 70}{RESET}")

        print(f"{BOLD}Main Menu:{RESET}")
        print(f"  {CYAN}1.{RESET} Search Movies & TV Series")
        print(f"  {CYAN}2.{RESET} Switch Provider")
        print(f"  {CYAN}3.{RESET} Player Settings")
        print(f"  {CYAN}0.{RESET} Exit")
        print()

        choice = ask_prompt("Select an option", choices=["1", "2", "3", "4", "0"], default="1")

        if choice == "1":
            handle_search(state)
        elif choice == "2":
            handle_switch_provider(state)
        elif choice == "3":
            handle_settings(state)
        elif choice == "0":
            print(f"{YELLOW}Goodbye!{RESET}")
            break


def handle_search(state: dict):
    """Prompts query, searches provider, and renders results table."""
    print()
    query = ask_prompt("Enter movie or series title")
    if not query:
        return

    provider = get_active_provider(state)
    prov_label = provider.get("label", "Provider")
    search_fn = provider.get("search")

    print(f"\n{GREEN}Searching '{query}' on {prov_label}...{RESET}")
    try:
        results = search_fn(query) if search_fn else []
    except Exception as e:
        print(f"{RED}Search failed:{RESET} {e}")
        ask_prompt("\nPress Enter to return")
        return

    if not results:
        print(f"{YELLOW}No results found for '{query}'.{RESET}")
        ask_prompt("\nPress Enter to return")
        return

    display_search_results(state, results)


def display_search_results(state: dict, items: List[dict]):
    """Displays catalog items in an aligned table and lets user choose one."""
    while True:
        clear_screen()
        headers = ["#", "Type", "Title", "Year", "Rating", "Provider"]
        rows = []

        for idx, item in enumerate(items, 1):
            m_type = item.get("media_type") if isinstance(item, dict) else getattr(item, "media_type", "movie")
            title = item.get("title") if isinstance(item, dict) else getattr(item, "title", "Untitled")
            year = item.get("year") if isinstance(item, dict) else getattr(item, "year", "N/A")
            rating = item.get("rating") if isinstance(item, dict) else getattr(item, "rating", None)
            prov = item.get("provider") if isinstance(item, dict) else getattr(item, "provider", "")

            type_badge = "SERIES" if m_type == "series" else "MOVIE"
            rating_str = f"{rating}" if rating else "N/A"
            rows.append([
                str(idx),
                type_badge,
                title,
                str(year or "N/A"),
                rating_str,
                prov,
            ])

        print_table(headers, rows, title=f"Search Results ({len(items)} found)")
        print(f"{DIM}Enter number to open details, or 0 to go back{RESET}")

        choice = ask_prompt("Select", default="0")
        if choice == "0" or not choice.isdigit():
            break

        val = int(choice)
        if 1 <= val <= len(items):
            selected = items[val - 1]
            sel_id = selected.get("id") if isinstance(selected, dict) else getattr(selected, "id")
            handle_media_details(state, sel_id)


def handle_media_details(state: dict, media_id: str):
    """Fetches and displays full synopsis, episodes, and stream options."""
    provider = get_active_provider(state)
    details_fn = provider.get("get_details")

    print(f"\n{GREEN}Loading media details...{RESET}")
    try:
        details = details_fn(media_id) if details_fn else None
    except Exception as e:
        print(f"{RED}Failed to fetch details:{RESET} {e}")
        ask_prompt("Press Enter to continue")
        return

    if not details:
        print(f"{RED}Could not load media details.{RESET}")
        ask_prompt("Press Enter to continue")
        return

    is_series = details.get("is_series") if isinstance(details, dict) else getattr(details, "is_series", False)
    seasons = details.get("seasons", []) if isinstance(details, dict) else getattr(details, "seasons", [])

    season = 0
    episode = 0

    if is_series and seasons:
        season, episode = select_season_and_episode(details)
        if season == 0:
            return

    handle_stream_selection(state, details, season=season, episode=episode)


def select_season_and_episode(details: dict) -> tuple:
    """Interactive season and episode picker."""
    clear_screen()
    title = details.get("title", "Series") if isinstance(details, dict) else getattr(details, "title", "Series")
    seasons = details.get("seasons", []) if isinstance(details, dict) else getattr(details, "seasons", [])

    headers = ["#", "Season", "Episodes"]
    rows = []
    for idx, s in enumerate(seasons, 1):
        num = s.get("number", idx) if isinstance(s, dict) else getattr(s, "number", idx)
        eps = s.get("episodes", []) if isinstance(s, dict) else getattr(s, "episodes", [])
        rows.append([str(idx), f"Season {num}", str(len(eps))])

    print_table(headers, rows, title=f"{title} - Select Season")
    s_choice = ask_prompt("Choose season (0 to cancel)", default="1")
    if s_choice == "0" or not s_choice.isdigit():
        return 0, 0

    s_idx = int(s_choice) - 1
    if not (0 <= s_idx < len(seasons)):
        return 0, 0

    selected_season = seasons[s_idx]
    s_num = selected_season.get("number", 1) if isinstance(selected_season, dict) else getattr(selected_season, "number", 1)
    episodes = selected_season.get("episodes", []) if isinstance(selected_season, dict) else getattr(selected_season, "episodes", [])

    clear_screen()
    ep_headers = ["Ep #", "Title"]
    ep_rows = []
    for ep in episodes:
        ep_num = ep.get("number", 1) if isinstance(ep, dict) else getattr(ep, "number", 1)
        ep_title = ep.get("title", f"Episode {ep_num}") if isinstance(ep, dict) else getattr(ep, "title", f"Episode {ep_num}")
        ep_rows.append([f"E{ep_num:02d}", ep_title])

    print_table(ep_headers, ep_rows, title=f"Season {s_num} - Select Episode")
    ep_choice = ask_prompt("Enter Episode number (0 to cancel)", default="1")
    if ep_choice == "0" or not ep_choice.isdigit():
        return 0, 0

    return s_num, int(ep_choice)


def handle_stream_selection(state: dict, details: dict, season: int = 0, episode: int = 0):
    """Fetches releases and allows direct playback or download."""
    title = details.get("title", "Item") if isinstance(details, dict) else getattr(details, "title", "Item")
    media_id = details.get("id", "") if isinstance(details, dict) else getattr(details, "id", "")
    provider = get_active_provider(state)
    streams_fn = provider.get("get_streams")

    target_label = f"{title} (S{season:02d}E{episode:02d})" if season > 0 else title
    print(f"\n{GREEN}Fetching streams for {target_label}...{RESET}")
    try:
        releases = streams_fn(media_id, season=season, episode=episode) if streams_fn else []
    except Exception as e:
        print(f"{RED}Failed to fetch streams:{RESET} {e}")
        ask_prompt("Press Enter to continue")
        return

    if not releases:
        print(f"{YELLOW}No stream links found for this item.{RESET}")
        ask_prompt("Press Enter to continue")
        return

    while True:
        clear_screen()
        prov_name = details.get("provider", "moviebox") if isinstance(details, dict) else getattr(details, "provider", "moviebox")
        year = details.get("year", "N/A") if isinstance(details, dict) else getattr(details, "year", "N/A")
        desc = details.get("description", "") if isinstance(details, dict) else getattr(details, "description", "")

        header_box = f"Media: {target_label} | Provider: {prov_name} | Year: {year or 'N/A'}"
        if desc:
            header_box += f"\nSynopsis: {desc[:250]}..."
        print_panel(header_box, title="Stream Selection")

        headers = ["#", "Quality", "Codec", "Mirror Title", "Subtitles"]
        rows = []
        for idx, rel in enumerate(releases, 1):
            q = rel.get("quality", "HD") if isinstance(rel, dict) else getattr(rel, "quality", "HD")
            c = rel.get("codec", "MP4") if isinstance(rel, dict) else getattr(rel, "codec", "MP4")
            fn = rel.get("filename", "Stream") if isinstance(rel, dict) else getattr(rel, "filename", "Stream")
            subs = rel.get("subtitles", []) if isinstance(rel, dict) else getattr(rel, "subtitles", [])
            subs_str = f"YES ({len(subs)})" if len(subs) > 0 else "None"
            rows.append([str(idx), q or "HD", c or "MP4", fn, subs_str])

        print_table(headers, rows, title="Available Releases")
        print(f"{DIM}Select stream number to Play / Download, or 0 to go back{RESET}")

        choice = ask_prompt("Action", default="1")
        if choice == "0" or not choice.isdigit():
            break

        idx = int(choice) - 1
        if 0 <= idx < len(releases):
            selected_release = releases[idx]
            handle_release_actions(state, selected_release, title)


def handle_release_actions(state: dict, release: dict, title: str):
    """Play or download chosen release."""
    player_name = get_active_player_name(state)
    print()
    print(f"{BOLD}Release Options:{RESET}")
    print(f"  {CYAN}1.{RESET} Play in Video Player ({player_name.upper()})")
    print(f"  {CYAN}2.{RESET} Download to Disk")
    print(f"  {CYAN}3.{RESET} Show Direct Stream URL")
    print(f"  {CYAN}0.{RESET} Back")

    action = ask_prompt("Choose", choices=["1", "2", "3", "0"], default="1")
    if action == "1":
        print(f"{GREEN}Launching {player_name.upper()}...{RESET}")
        success = play_media(release, player_name=player_name, title=title)
        if not success:
            print(f"{RED}Could not launch {player_name}. Check if player is installed.{RESET}")
            ask_prompt("Press Enter to continue")
    elif action == "2":
        fn = release.get("filename", "video") if isinstance(release, dict) else getattr(release, "filename", "video")
        safe_fn = "".join(c for c in fn if c.isalnum() or c in (" ", "-", "_", ".")).rstrip() + ".mp4"
        dl_dir = Path(get_config("download_dir", str(Path.home() / "Downloads" / "MovieBox")))
        out = dl_dir / safe_fn
        print(f"{CYAN}Downloading to: {out}{RESET}")
        download_release(release, out)
        ask_prompt("Download operation finished. Press Enter to continue")
    elif action == "3":
        d_url = release.get("direct_url", "N/A") if isinstance(release, dict) else getattr(release, "direct_url", "N/A")
        print_panel(f"Direct Stream URL:\n{d_url}", title="Stream Link")
        ask_prompt("Press Enter to continue")


def handle_live_tv(state: dict):
    """Displays categorized IPTV channels with instant playback."""
    channels = tv_get_all_channels()
    categories = sorted(list(set(c.get("category", "General") for c in channels)))

    while True:
        clear_screen()
        print(f"\n{BOLD}{CYAN}=== Live TV - Categories ==={RESET}")

        for idx, cat in enumerate(categories, 1):
            count = sum(1 for c in channels if c.get("category") == cat)
            print(f"  {CYAN}{idx}.{RESET} {cat} {DIM}({count} channels){RESET}")
        print(f"  {CYAN}0.{RESET} Back to Main Menu\n")

        choice = ask_prompt("Select category", default="1")
        if choice == "0" or not choice.isdigit():
            break

        cat_idx = int(choice) - 1
        if 0 <= cat_idx < len(categories):
            selected_cat = categories[cat_idx]
            cat_channels = [c for c in channels if c.get("category") == selected_cat]

            clear_screen()
            ch_headers = ["#", "Channel Name", "Country"]
            ch_rows = []
            for c_idx, ch in enumerate(cat_channels, 1):
                ch_rows.append([str(c_idx), ch.get("name", "Channel"), ch.get("country") or "Global"])

            print_table(ch_headers, ch_rows, title=f"Category: {selected_cat}")
            ch_choice = ask_prompt("Select channel to play (0 to cancel)", default="1")
            if ch_choice != "0" and ch_choice.isdigit():
                c_num = int(ch_choice) - 1
                if 0 <= c_num < len(cat_channels):
                    target_ch = cat_channels[c_num]
                    player_name = get_active_player_name(state)
                    print(f"{GREEN}Starting live stream: {target_ch.get('name')}...{RESET}")
                    play_media(target_ch, player_name=player_name, stream_url=target_ch.get("stream_url"), title=target_ch.get("name"))
                    ask_prompt("Stream playing. Press Enter to continue")


def handle_switch_provider(state: dict):
    """Allows switching active provider."""
    providers = list_providers()
    clear_screen()
    print(f"\n{BOLD}{CYAN}=== Select Content Provider ==={RESET}")

    current_p = state.get("provider_name", DEFAULT_PROVIDER)
    for idx, p in enumerate(providers, 1):
        active_mark = f" {GREEN}(Active){RESET}" if p["name"] == current_p else ""
        print(f"  {CYAN}{idx}.{RESET} {p['label']}{active_mark}")

    choice = ask_prompt("Choose provider", default="1")
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(providers):
            state["provider_name"] = providers[idx]["name"]
            set_config("provider", state["provider_name"])
            print(f"{GREEN}Switched to {providers[idx]['label']}{RESET}")


def handle_settings(state: dict):
    """Configures player preferences."""
    clear_screen()
    curr = state.get("player_name", "vlc")
    print(f"\n{BOLD}{CYAN}=== Player Settings ==={RESET}")
    print(f"Current default player: {GREEN}{curr.upper()}{RESET}")
    print("Available players on system: " + ", ".join(list_available_players()))
    print()
    print("  1. Set to MPV")
    print("  2. Set to Android Intent Chooser")
    print("  0. Back\n")

    c = ask_prompt("Choose", choices=["1", "2", "3", "0"], default="1")
    if c == "1":
        state["player_name"] = "mpv"
        set_config("player", "mpv")
        set_config("player", "vlc")
    elif c == "2":
        state["player_name"] = "intent"
        set_config("player", "intent")


def MovieBoxTuiApp():
    """Functional wrapper for backward-compatibility (runs without classes)."""
    return {"run": run_tui_app}
