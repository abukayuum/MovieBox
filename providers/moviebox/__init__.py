"""
MovieBox Provider Functions (Basic Procedural Python - No Classes)
Updated directly from Rust mesamirh/MovieBox-Tui logic.
"""
from typing import List, Optional
from . import adapt, client

NAME = "moviebox"
LABEL = "MovieBox VIP"
SUPPORTS_SERIES = True
SUPPORTS_SUBTITLES = True


def get_metadata():
    """Returns provider metadata dictionary."""
    return {
        "name": NAME,
        "label": LABEL,
        "supports_series": SUPPORTS_SERIES,
        "supports_subtitles": SUPPORTS_SUBTITLES,
    }


def moviebox_search(query: str, page: int = 1) -> List[dict]:
    """Searches MovieBox for movies and TV series."""
    data = client.moviebox_api_search(query=query, page=page)
    return adapt.search_json_to_catalog(data)


def moviebox_get_details(media_id: str) -> Optional[dict]:
    """Fetches details for MovieBox subject."""
    data = client.moviebox_api_get_details(media_id)
    return adapt.details_json_to_media_details(data)


def moviebox_get_streams(media_id: str, season: int = 0, episode: int = 0) -> List[dict]:
    """Fetches playable streams and DASH manifests for subject/episode."""
    releases: List[dict] = []
    state = client.get_client_state()
    user_agent = state.get("user_agent") or "Mozilla/5.0 (Linux; Android 12)"

    try:
        play_info = client.moviebox_api_get_play_info(media_id, season, episode)
        releases.extend(
            adapt.play_info_json_to_releases(
                play_info,
                season=season,
                episode=episode,
                user_agent=user_agent,
            )
        )
    except Exception:
        pass

    # If play_info was empty, try secondary resource endpoint
    if not releases:
        try:
            res_data = client.moviebox_api_get_resources(media_id, season, episode, page=1, per_page=20)
            items = res_data.get("list", []) if isinstance(res_data, dict) else []
            for item in items:
                down_url = item.get("downloadUrl") or item.get("url") or ""
                if down_url and not adapt.is_deprecation_notice_url(down_url):
                    fn = item.get("name") or f"Resource {item.get('id', '')}"
                    res_num = item.get("resolution") or 1080
                    releases.append({
                        "provider": "moviebox",
                        "filename": f"{fn} [{res_num}p]",
                        "quality": f"{res_num}p",
                        "codec": "MP4",
                        "language": "English",
                        "size_bytes": item.get("size"),
                        "season": season if season > 0 else None,
                        "episode": episode if episode > 0 else None,
                        "direct_url": down_url,
                        "headers": {"Referer": adapt.STREAM_REFERER, "User-Agent": user_agent},
                        "mirrors": [{"label": "Direct CDN", "resolver_url": down_url, "headers": {"Referer": adapt.STREAM_REFERER}, "direct_file": True}],
                        "subtitles": [],
                        "resource_id": str(item.get("id") or ""),
                    })
        except Exception:
            pass

    return releases
