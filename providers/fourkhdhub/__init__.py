import base64
import codecs
import json
import re
from typing import Any, Dict, List, Optional
import urllib.parse
import requests

from models.media import make_catalog_item, make_media_details
from models.release import make_release, make_source_mirror

BASE_URL = "https://4khdhub.one"
NAME = "fourkhdhub"
LABEL = "4KHDHub (4K & 1080p)"
SUPPORTS_SERIES = True
SUPPORTS_SUBTITLES = True

_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://4khdhub.one/",
})


def get_metadata():
    return {
        "name": NAME,
        "label": LABEL,
        "supports_series": SUPPORTS_SERIES,
        "supports_subtitles": SUPPORTS_SUBTITLES,
    }


def fourkhdhub_search(query: str, page: int = 1) -> List[dict]:
    items: List[dict] = []
    trimmed = str(query or "").strip()
    if not trimmed:
        return []

    try:
        url = f"{BASE_URL}/?s={urllib.parse.quote(trimmed)}"
        resp = _session.get(url, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            cards = re.findall(
                r'<a\s+href="([^"]+)"\s+class="movie-card"[^>]*>.*?<img\s+src="([^"]+)"\s+alt="([^"]+)"',
                html,
                re.DOTALL,
            )
            if not cards:
                cards = re.findall(
                    r'<article[^>]*>.*?<a\s+href="([^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"',
                    html,
                    re.DOTALL,
                )

            for rel_link, img_url, raw_title in cards:
                full_link = f"{BASE_URL}{rel_link}" if rel_link.startswith("/") else rel_link
                is_series = "series" in rel_link.lower() or "season" in raw_title.lower()

                items.append(
                    make_catalog_item(
                        item_id=full_link,
                        title=raw_title.strip() or "4K Title",
                        media_type="series" if is_series else "movie",
                        provider=NAME,
                        poster_url=img_url,
                        rating="4K / HDR",
                    )
                )
    except Exception:
        pass
    return items


def fourkhdhub_get_details(media_id: str) -> Optional[dict]:
    try:
        resp = _session.get(media_id, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            title_match = re.search(r'<title>(.*?)</title>', html, re.I)
            raw_title = title_match.group(1).split("-")[0].strip() if title_match else "4K Title"

            img_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html, re.I)
            poster = img_match.group(1) if img_match else None

            desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, re.I)
            desc = desc_match.group(1) if desc_match else "4K Ultra-HD release mirror from 4KHDHub."

            is_series = "series" in media_id.lower() or "season" in raw_title.lower()

            return make_media_details(
                item_id=media_id,
                title=raw_title,
                media_type="series" if is_series else "movie",
                provider=NAME,
                poster_url=poster,
                description=desc,
            )
    except Exception:
        pass
    return None


def resolve_hubcloud_direct_url(greenmotors_url: str) -> Dict[str, Any]:
    result = {
        "direct_url": None,
        "mirrors": [],
    }

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    })

    try:
        # Step 1: Decode Greenmotors token
        r1 = s.get(greenmotors_url, timeout=10)
        m = re.search(r"s\('o',\s*'([^']+)'", r1.text)
        hubcloud_url = None
        if m:
            tok = m.group(1)
            s1 = base64.b64decode(tok).decode("utf-8", "ignore")
            s2 = base64.b64decode(s1).decode("utf-8", "ignore")
            rot = codecs.decode(s2, "rot_13")
            payload = json.loads(base64.b64decode(rot).decode("utf-8", "ignore"))
            hubcloud_url = base64.b64decode(payload.get("o", "")).decode("utf-8", "ignore")

        if not hubcloud_url or not hubcloud_url.startswith("http"):
            m_direct = re.search(r'href=[\"\'](https?://(?:hubcloud|gamerxyt)[^\"]+)[\"\']', r1.text)
            if m_direct:
                hubcloud_url = m_direct.group(1)

        if not hubcloud_url or not hubcloud_url.startswith("http"):
            return result

        result["mirrors"].append(make_source_mirror("HubCloud Page", hubcloud_url, direct_file=False))

        # Step 2: Fetch HubCloud / Gamerxyt page
        r2 = s.get(hubcloud_url, headers={"Referer": greenmotors_url}, timeout=10)
        target_page_url = hubcloud_url
        page_html = r2.text

        m_gamer = re.search(r'href=[\"\'](https?://gamerxyt\.com/[^\"]+)[\"\']', r2.text)
        if m_gamer:
            target_page_url = m_gamer.group(1)
            r3 = s.get(target_page_url, headers={"Referer": hubcloud_url}, timeout=10)
            page_html = r3.text

        # Step 3: Cloudflare R2 Stream
        m_r2 = re.search(r'href=[\"\'](https?://[^\"]*r2\.cloudflarestorage[^\"]+)[\"\']', page_html)
        if m_r2:
            r2_url = m_r2.group(1)
            result["direct_url"] = r2_url
            result["mirrors"].insert(0, make_source_mirror("Cloudflare R2 Direct", r2_url, direct_file=True))
            return result

        m_watch = re.search(r'[\"\']https?://vdplay\.pages\.dev/\?u=([^\"]+)[\"\']', page_html)
        if m_watch:
            try:
                r2_url = base64.b64decode(m_watch.group(1)).decode()
                result["direct_url"] = r2_url
                result["mirrors"].insert(0, make_source_mirror("Cloudflare R2 Stream", r2_url, direct_file=True))
                return result
            except Exception:
                pass

        # Step 4: GPDL / Google CDN
        m_gpdl = re.search(r'href=[\"\'](https?://(?:gpdl|fastdl|download)\.[^\"]+)[\"\']', page_html)
        if m_gpdl:
            gpdl_url = m_gpdl.group(1)
            try:
                r4 = s.get(gpdl_url, headers={"Referer": target_page_url}, allow_redirects=True, timeout=10)
                if "dl.php" in r4.url and "link=" in r4.url:
                    from urllib.parse import parse_qs, urlparse
                    qs = parse_qs(urlparse(r4.url).query)
                    direct_cdn = qs.get("link", [None])[0]
                    if direct_cdn:
                        result["direct_url"] = direct_cdn
                        result["mirrors"].insert(0, make_source_mirror("Google CDN Direct", direct_cdn, direct_file=True))
                        return result
                elif any(ext in r4.url.lower() for ext in [".mkv", ".mp4"]):
                    result["direct_url"] = r4.url
                    result["mirrors"].insert(0, make_source_mirror("Google CDN Stream", r4.url, direct_file=True))
                    return result
            except Exception:
                pass

        # Step 5: Direct Media URL on page
        m_media = re.search(r'href=[\"\'](https?://[^\"]+\.(?:mkv|mp4)[^\"]*)[\"\']', page_html, re.I)
        if m_media:
            result["direct_url"] = m_media.group(1)
            result["mirrors"].insert(0, make_source_mirror("Direct Video File", m_media.group(1), direct_file=True))
            return result

    except Exception:
        pass

    return result


def fourkhdhub_get_streams(media_id: str, season: int = 0, episode: int = 0) -> List[dict]:
    releases: List[dict] = []
    try:
        resp = _session.get(media_id, timeout=10)
        if resp.status_code != 200:
            return []

        html = resp.text

        file_sections = re.findall(
            r'<div class=\"download-item[^>]*>.*?<div class=\"flex-1[^\"]*font-semibold\">(.*?)</div>.*?<div class=\"file-title\">(.*?)</div>.*?href=[\"\'](https?://greenmotors\.club[^\"]+)[\"\'].*?Download HubCloud',
            html,
            re.DOTALL | re.I,
        )

        if not file_sections:
            file_sections = re.findall(
                r'<div class=\"file-title\">(.*?)</div>.*?href=[\"\'](https?://greenmotors\.club[^\"]+)[\"\'].*?Download HubCloud',
                html,
                re.DOTALL | re.I,
            )
            file_sections = [("", fs[0], fs[1]) for fs in file_sections]

        for header, file_title, hub_link in file_sections:
            clean_title = re.sub(r'<[^>]+>', ' ', file_title).strip()
            clean_header = re.sub(r'<[^>]+>', ' ', header).strip()
            full_title = clean_title or clean_header or "4K Ultra-HD Stream"
            lower_title = full_title.lower()

            # Filter for specific episode if series
            if season > 0 and episode > 0:
                ep_pattern = f"e{episode:02d}"
                s_pattern = f"s{season:02d}"
                if (s_pattern not in lower_title and ep_pattern not in lower_title and 
                    f"ep{episode:02d}" not in lower_title and f"episode {episode}" not in lower_title):
                    continue

            # SKIP Zip files for streaming (VLC cannot stream ZIP packages)
            is_zip = ".zip" in lower_title or "zip" in clean_header.lower()
            if is_zip and (season > 0 and episode > 0):
                continue

            check_title = lower_title.replace("4khdhub", "").replace("4k-hdhub", "")
            quality = "1080p HD"
            if "2160p" in check_title or "4k" in check_title:
                quality = "2160p 4K"
            elif "720p" in check_title:
                quality = "720p HD"

            codec = "HEVC" if ("hevc" in lower_title or "h.265" in lower_title or "x265" in lower_title) else "H.264"

            # Always resolve direct streaming URL
            res_data = resolve_hubcloud_direct_url(hub_link)
            direct_stream = res_data.get("direct_url")

            # Only append release if direct playable stream is successfully extracted!
            if not direct_stream:
                continue

            safe_filename = full_title
            if not is_zip and not safe_filename.lower().endswith((".mkv", ".mp4", ".ts")):
                safe_filename += ".mkv"
            elif is_zip and not safe_filename.lower().endswith(".zip"):
                safe_filename += ".zip"

            mirrors = res_data.get("mirrors") or [make_source_mirror(f"{quality} Direct", direct_stream, direct_file=True)]

            releases.append(
                make_release(
                    provider=NAME,
                    filename=safe_filename,
                    quality=quality,
                    codec=codec,
                    mirrors=mirrors,
                    direct_url=direct_stream,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://hubcloud.ist/",
                    },
                )
            )

            if len(releases) >= 8:
                break

    except Exception:
        pass

    return releases
