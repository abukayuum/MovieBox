"""
MovieBox JSON Adapter (Basic Procedural Python - No Classes)
Maps raw MovieBox / OneRoom JSON payloads into plain dictionaries.
Updated directly from Rust mesamirh/MovieBox-Tui logic.
"""
import base64
import json
from typing import Any, Dict, List, Optional
from models.media import make_catalog_item, make_media_details, make_season, make_episode, make_dub_option
from models.release import make_release, make_source_mirror, make_subtitle_option
from .title import clean_moviebox_title, extract_year

STREAM_REFERER = "https://sportslive.wine"


def is_deprecation_notice_url(url: str) -> bool:
    """Checks if video URL is a dummy deprecation notice video."""
    if not url:
        return True
    lower = str(url).lower()
    return (
        "1c7de0bd3393702d9191801f15f88f8d" in lower
        or "9a0461bc39da389663bf3dbb17091d3f" in lower
        or "b164fbfb4347792950bdfbfb563d39d9" in lower
        or "/notice.mp4" in lower
        or "notice" in lower
        or ("macdn.aoneroom.com" in lower and "/other/" in lower and lower.endswith(".mp4") and len(url) < 80)
    )


def resolve_dash_manifest_from_policy(sign_cookie: str) -> Optional[str]:
    """
    Extracts direct .mpd DASH manifest URL from CloudFront policy or urlprefix in signCookie.
    Matches Rust adapt.rs logic exactly.
    """
    if not sign_cookie:
        return None
    try:
        parts = sign_cookie.split(";")
        for part in parts:
            trimmed = part.strip()
            # 1. Edge cache urlprefix format
            if "urlprefix=" in trimmed:
                prefix = trimmed.split("urlprefix=", 1)[1]
                b64_token = prefix.split(":", 1)[0].strip()
                normalized = b64_token.replace("-", "+").replace("_", "/")
                pad = (4 - (len(normalized) % 4)) % 4
                if pad > 0:
                    normalized += "=" * pad
                try:
                    decoded = base64.b64decode(normalized.encode()).decode("utf-8", errors="ignore")
                    if decoded.startswith("http"):
                        base_res = decoded.rstrip("*/").rstrip("/")
                        return f"{base_res}/index.mpd"
                except Exception:
                    pass

            # 2. CloudFront-Policy format
            if trimmed.startswith("CloudFront-Policy="):
                policy_raw = trimmed[len("CloudFront-Policy="):].strip()
                normalized = policy_raw.replace("-", "+").replace("_", "=").replace("~", "/")
                pad = (4 - (len(normalized) % 4)) % 4
                if pad > 0:
                    normalized += "=" * pad
                try:
                    dec = base64.b64decode(normalized.encode())
                    val = json.loads(dec.decode("utf-8"))
                    statements = val.get("Statement", [])
                    if statements and "Resource" in statements[0]:
                        res = statements[0]["Resource"].rstrip("*/").rstrip("/")
                        if res.startswith("http"):
                            return f"{res}/index.mpd"
                except Exception:
                    pass
    except Exception:
        pass
    return None


def subject_json_to_catalog_item(s: Dict[str, Any]) -> Optional[dict]:
    """Converts a raw MovieBox subject item into a catalog dictionary."""
    if not isinstance(s, dict):
        return None

    subj_id = str(s.get("subjectId") or s.get("id") or "")
    if not subj_id:
        return None

    title = str(s.get("title") or s.get("name") or "Unknown")
    stype = int(s.get("subjectType") or s.get("stype") or 1)
    media_type = "series" if stype == 2 else "movie"

    year_raw = str(s.get("releaseDate") or s.get("year") or s.get("releaseInfo") or "")
    year = extract_year(year_raw) or None

    cover = s.get("cover")
    poster_url = None
    if isinstance(cover, dict):
        poster_url = cover.get("url")
    if not poster_url:
        poster_url = s.get("coverUrl") or s.get("poster") or s.get("pic")

    season_count = None
    if "season" in s and s["season"]:
        try:
            season_count = int(s["season"])
        except (ValueError, TypeError):
            pass

    rating = None
    if "imdbRatingValue" in s and s["imdbRatingValue"]:
        rating = str(s["imdbRatingValue"])
    elif "rating" in s and s["rating"]:
        rating = str(s["rating"])

    return make_catalog_item(
        item_id=subj_id,
        title=title,
        media_type=media_type,
        provider="moviebox",
        year=year,
        poster_url=poster_url,
        season_count=season_count,
        rating=rating,
    )


def search_json_to_catalog(payload: Dict[str, Any]) -> List[dict]:
    """Extracts catalog items list from search API response."""
    items: List[dict] = []
    data = payload.get("data", payload)
    results = data.get("results", [])
    subjects = []
    if results and isinstance(results, list):
        first = results[0]
        if isinstance(first, dict):
            subjects = first.get("subjects", [])
    if not subjects:
        subjects = data.get("list", [])

    for s in subjects:
        cat_item = subject_json_to_catalog_item(s)
        if cat_item:
            items.append(cat_item)
    return items


def details_json_to_media_details(payload: Dict[str, Any]) -> Optional[dict]:
    """Parses full media details JSON into dictionary."""
    data = payload.get("data", payload)
    subject = data.get("subject", data)
    subj_id = str(subject.get("subjectId") or subject.get("id") or "")
    if not subj_id:
        return None

    title = str(subject.get("title") or "Unknown")
    stype = int(subject.get("subjectType") or subject.get("stype") or 1)
    media_type = "series" if stype == 2 else "movie"

    year_raw = str(subject.get("releaseDate") or subject.get("year") or "")
    year = extract_year(year_raw) or None

    description = subject.get("description") or subject.get("intro")
    tagline = subject.get("tagline")
    imdb_rating = str(subject.get("imdbRatingValue") or subject.get("rating") or "") or None
    director = subject.get("director")
    stars = subject.get("stars")

    cover = subject.get("cover")
    poster_url = cover.get("url") if isinstance(cover, dict) else (subject.get("coverUrl") or subject.get("poster"))

    duration_raw = subject.get("duration")
    duration = None
    if duration_raw:
        try:
            sec = int(duration_raw)
            if sec > 0:
                duration = f"{sec // 60}m"
        except Exception:
            duration = str(duration_raw)

    genres = []
    g_raw = subject.get("genre") or subject.get("genres")
    if isinstance(g_raw, list):
        genres = [str(x) for x in g_raw]

    # Parse Seasons & Episodes
    seasons: List[dict] = []
    seasons_obj = subject.get("seasons", {})
    if isinstance(seasons_obj, dict):
        seasons_arr = seasons_obj.get("seasons", [])
    elif isinstance(seasons_obj, list):
        seasons_arr = seasons_obj
    else:
        seasons_arr = []

    for s in seasons_arr:
        se_num = int(s.get("se", 1))
        episodes = []
        ep_nums = s.get("episodeNumbers", [])
        if ep_nums:
            for ep_num in ep_nums:
                episodes.append(make_episode(season=se_num, number=int(ep_num)))
        elif "maxEp" in s and s["maxEp"]:
            for ep_num in range(1, int(s["maxEp"]) + 1):
                episodes.append(make_episode(season=se_num, number=ep_num))
        seasons.append(make_season(number=se_num, episodes=episodes))

    # Parse Dubs (audio tracks)
    dubs: List[dict] = []
    dubs_arr = subject.get("dubs", [])
    if isinstance(dubs_arr, list):
        for d in dubs_arr:
            d_id = str(d.get("subjectId") or d.get("id") or "")
            lang = str(d.get("lanName") or d.get("language") or "Unknown")
            label = str(d.get("title") or d.get("name") or lang)
            if d_id:
                dubs.append(make_dub_option(subject_id=d_id, language=lang, label=label))

    return make_media_details(
        item_id=subj_id,
        title=title,
        media_type=media_type,
        provider="moviebox",
        year=year,
        description=description,
        tagline=tagline,
        imdb_rating=imdb_rating,
        director=director,
        stars=stars,
        poster_url=poster_url,
        duration=duration,
        genres=genres,
        seasons=seasons,
        dubs=dubs,
    )


def play_info_json_to_releases(
    payload: Dict[str, Any],
    season: int,
    episode: int,
    user_agent: str,
) -> List[dict]:
    """Extracts playable releases from play-info API endpoint into plain dictionary list."""
    data = payload.get("data", payload)
    raw_title = data.get("title", "MovieBox Stream")
    clean_title = clean_moviebox_title(raw_title)

    streams = data.get("streams") or data.get("list") or data.get("resources") or []
    if not isinstance(streams, list):
        return []

    # Parse Subtitles
    subtitles: List[dict] = []
    ext_captions = data.get("extCaptions", [])
    if isinstance(ext_captions, list):
        seen_urls = set()
        for cap in ext_captions:
            url = cap.get("url")
            if url and url not in seen_urls and not is_deprecation_notice_url(url):
                seen_urls.add(url)
                name = cap.get("lanName") or cap.get("lan") or "Unknown"
                subtitles.append(make_subtitle_option(name=str(name), url=url))

    releases: List[dict] = []

    for s in streams:
        fmt = str(s.get("format") or "MP4").upper()
        codec = s.get("codecName") or s.get("codec") or fmt
        size_bytes = None
        if "size" in s and s["size"]:
            try:
                size_bytes = int(s["size"])
            except Exception:
                pass

        resolutions_str = str(s.get("resolutions") or data.get("displayResolutions") or "1080,720,480")
        sign_cookie = s.get("signCookie", "")
        stream_url = s.get("url", "")

        manifest_url = resolve_dash_manifest_from_policy(sign_cookie)
        if not manifest_url:
            if stream_url and stream_url.startswith("http") and not is_deprecation_notice_url(stream_url):
                manifest_url = stream_url

        if not manifest_url:
            continue

        res_list = [int(r.strip()) for r in resolutions_str.split(",") if r.strip().isdigit()]
        if not res_list:
            res_list = [1080, 720, 480]

        # Headers for player (Referer + UA + Cookie)
        headers = {
            "Referer": STREAM_REFERER,
            "User-Agent": user_agent,
        }
        if sign_cookie:
            clean_cookie = "; ".join(p.strip() for p in sign_cookie.split(";") if p.strip())
            headers["Cookie"] = clean_cookie

        # 1. Primary Auto / Adaptive Stream
        if season > 0 and episode > 0:
            fn_auto = f"{clean_title} S{season:02d}E{episode:02d} [Auto / Adaptive] [{codec}]"
        else:
            fn_auto = f"{clean_title} [Auto / Adaptive] [{codec}]"

        mirror_auto = make_source_mirror(
            label=f"Auto Adaptive {codec}",
            resolver_url=manifest_url,
            headers=headers,
            direct_file=True,
        )

        releases.append(
            make_release(
                provider="moviebox",
                filename=fn_auto,
                quality="multi",
                codec=codec,
                language="English/Multi",
                size_bytes=size_bytes,
                season=season if season > 0 else None,
                episode=episode if episode > 0 else None,
                mirrors=[mirror_auto],
                subtitles=subtitles,
                direct_url=manifest_url,
                headers=headers,
            )
        )

        # 2. Individual quality options (1080p, 720p, etc.)
        for res in sorted(res_list, reverse=True):
            if season > 0 and episode > 0:
                fn_res = f"{clean_title} S{season:02d}E{episode:02d} [{res}p] [{codec}]"
            else:
                fn_res = f"{clean_title} [{res}p] [{codec}]"

            mirror_res = make_source_mirror(
                label=f"{res}p {codec}",
                resolver_url=manifest_url,
                headers=headers,
                direct_file=True,
            )

            releases.append(
                make_release(
                    provider="moviebox",
                    filename=fn_res,
                    quality=f"{res}p",
                    codec=codec,
                    language="English/Multi",
                    size_bytes=size_bytes,
                    season=season if season > 0 else None,
                    episode=episode if episode > 0 else None,
                    mirrors=[mirror_res],
                    subtitles=subtitles,
                    direct_url=manifest_url,
                    headers=headers,
                )
            )

    # Sort releases: Auto / multi first (highest priority), then highest resolution descending
    def sort_key(rel: dict):
        q = rel.get("quality") or ""
        if q == "multi":
            return (99999, rel.get("size_bytes") or 0)
        digits = "".join(filter(str.isdigit, q))
        return (int(digits) if digits else 0, rel.get("size_bytes") or 0)

    releases.sort(key=sort_key, reverse=True)
    return releases
