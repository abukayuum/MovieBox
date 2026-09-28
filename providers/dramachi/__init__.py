import urllib.parse
from typing import List, Optional
import requests
from models.media import make_catalog_item, make_media_details, make_season, make_episode
from models.release import make_release, make_source_mirror

BASE_URL = "https://api.nodeobjects.com/"
IMAGE_CDN = "https://static.nodeobjects.com/thumbnail/"
NAME = "dramachi"
LABEL = "Dramachi (Direct MKV/MP4)"
SUPPORTS_SERIES = True
SUPPORTS_SUBTITLES = False

_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})


def get_metadata():
    """Returns provider metadata dictionary."""
    return {
        "name": NAME,
        "label": LABEL,
        "supports_series": SUPPORTS_SERIES,
        "supports_subtitles": SUPPORTS_SUBTITLES,
    }


def dramachi_search(query: str, page: int = 1) -> List[dict]:
    """Searches Dramachi catalog."""
    trimmed = str(query or "").strip()
    if not trimmed:
        return []

    url = f"{BASE_URL}?interface=search&q={urllib.parse.quote(trimmed)}&filter=all&page={page}"
    try:
        resp = _session.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", [])
        catalog: List[dict] = []

        for item in items:
            item_id = str(item.get("id", ""))
            title = str(item.get("title") or item.get("common_title") or "Unknown")
            year = str(item.get("year", "")) or None
            thumb = item.get("thumb")
            poster_url = f"{IMAGE_CDN}{thumb}" if thumb else None
            content_type = str(item.get("content", "")).lower()
            media_type = "series" if "series" in content_type else "movie"

            catalog.append(
                make_catalog_item(
                    item_id=item_id,
                    title=title,
                    media_type=media_type,
                    provider=NAME,
                    year=year,
                    poster_url=poster_url,
                )
            )
        return catalog
    except Exception:
        return []


def dramachi_get_details(media_id: str) -> Optional[dict]:
    """Fetches details for Dramachi title."""
    title_id = str(media_id or "").split("::")[0].strip()
    if not title_id:
        return None

    url = f"{BASE_URL}?interface=title_v2&id={urllib.parse.quote(title_id)}"
    try:
        resp = _session.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        albums = data.get("album", [])
        if not albums:
            return None
        album = albums[0]

        title = str(album.get("title") or "Unknown")
        is_movie = str(album.get("content", "")).lower() in ["movies", "movie"]
        media_type = "movie" if is_movie else "series"

        thumb = album.get("thumb")
        poster_url = f"{IMAGE_CDN}{thumb}" if thumb else None
        year = str(album.get("year", "")) or None
        description = album.get("storyline") or album.get("synopsis")
        director = album.get("director")
        stars = album.get("writers")
        duration = album.get("runtime")
        genres_raw = album.get("genres", "")
        genres = [g.strip() for g in genres_raw.split(",") if g.strip()]

        seasons_dict = data.get("seasons", {})
        seasons: List[dict] = []

        if isinstance(seasons_dict, dict):
            s_num = 1
            for key, val in seasons_dict.items():
                episodes: List[dict] = []
                versions = val.get("versions", []) if isinstance(val, dict) else []
                rip = versions[0].get("rip", key) if versions else key

                try:
                    ep_resp = _session.get(
                        f"{BASE_URL}?interface=eplist&season={urllib.parse.quote(str(rip))}&id={urllib.parse.quote(title_id)}",
                        timeout=10,
                    )
                    if ep_resp.status_code == 200:
                        ep_data = ep_resp.json().get("episode_list", [])
                        for idx, ep_item in enumerate(ep_data, 1):
                            episodes.append(
                                make_episode(
                                    season=s_num,
                                    number=idx,
                                    title=ep_item.get("f_title") or f"Episode {idx}",
                                )
                            )
                except Exception:
                    pass

                if not episodes:
                    episodes.append(make_episode(season=s_num, number=1, title="Full Movie / Episode 1"))

                seasons.append(make_season(number=s_num, episodes=episodes))
                s_num += 1

        if not seasons:
            seasons.append(make_season(number=1, episodes=[make_episode(season=1, number=1, title="Main Video")]))

        return make_media_details(
            item_id=title_id,
            title=title,
            media_type=media_type,
            provider=NAME,
            year=year,
            description=description,
            director=director,
            stars=stars,
            poster_url=poster_url,
            duration=duration,
            genres=genres,
            seasons=seasons,
            dubs=[],
        )
    except Exception:
        return None


def dramachi_get_streams(media_id: str, season: int = 0, episode: int = 0) -> List[dict]:
    """Fetches direct CDN playable release for Dramachi."""
    title_id = str(media_id or "").split("::")[0].strip()
    if not title_id:
        return []

    url = f"{BASE_URL}?interface=title_v2&id={urllib.parse.quote(title_id)}"
    try:
        resp = _session.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        seasons_dict = data.get("seasons", {})
        rip_to_query = "hd Rip"

        if isinstance(seasons_dict, dict) and seasons_dict:
            keys = list(seasons_dict.keys())
            target_key = keys[(season - 1) % len(keys)] if season > 0 else keys[0]
            val = seasons_dict[target_key]
            versions = val.get("versions", []) if isinstance(val, dict) else []
            if versions:
                rip_to_query = versions[0].get("rip", target_key)
            else:
                rip_to_query = target_key

        ep_url = f"{BASE_URL}?interface=eplist&season={urllib.parse.quote(str(rip_to_query))}&id={urllib.parse.quote(title_id)}"
        ep_resp = _session.get(ep_url, timeout=10)
        ep_resp.raise_for_status()
        ep_list = ep_resp.json().get("episode_list", [])

        if not ep_list:
            return []

        target_ep = ep_list[0]
        if episode > 0 and episode <= len(ep_list):
            target_ep = ep_list[episode - 1]

        fid = target_ep.get("fid", "")
        disk = target_ep.get("disk", "")
        quality = target_ep.get("quality", "HD")
        filename = target_ep.get("f_title", f"{title_id}.mkv")

        if not fid or not disk:
            return []

        get_file_url = f"{BASE_URL}?interface=getFile&fid={urllib.parse.quote(str(fid))}&findex={urllib.parse.quote(str(disk))}"
        file_resp = _session.get(get_file_url, timeout=10)
        file_resp.raise_for_status()
        file_data = file_resp.json()

        host_info = file_data.get("hostInfo", {})
        file_info_list = file_data.get("fileInfo", [])
        if not host_info or not file_info_list:
            return []

        file_info = file_info_list[0]
        host = host_info.get("host", "").rstrip("/")
        raw_url = file_info.get("url", "").lstrip("/")

        if not host or not raw_url:
            return []

        direct_stream_url = f"https://{host}/cdn/{raw_url}"
        real_filename = file_info.get("filename") or filename

        mirror = make_source_mirror(
            label=f"Dramachi Direct CDN ({quality})",
            resolver_url=direct_stream_url,
            headers={"User-Agent": "Mozilla/5.0"},
            direct_file=True,
        )

        return [
            make_release(
                provider=NAME,
                filename=real_filename,
                quality=quality,
                codec="MKV/H264",
                language="English/Asian",
                size_bytes=None,
                season=season if season > 0 else None,
                episode=episode if episode > 0 else None,
                mirrors=[mirror],
                direct_url=direct_stream_url,
                headers={"User-Agent": "Mozilla/5.0"},
                subtitles=[],
            )
        ]
    except Exception:
        return []
