import re
from typing import List, Optional
from urllib.parse import quote_plus, unquote, urljoin
import requests
from bs4 import BeautifulSoup

from models.media import make_catalog_item, make_media_details
from models.release import make_release, make_source_mirror
from .ftp_servers import POPULAR_BDIX_SERVERS

NAME = "bdix"
LABEL = "BDIX FTP (Bangladesh)"
SUPPORTS_SERIES = True
SUPPORTS_SUBTITLES = True

BASE_URL = "http://naturalbd.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "http://naturalbd.com/",
}


def get_metadata():
    """Returns provider metadata dictionary."""
    return {
        "name": NAME,
        "label": LABEL,
        "supports_series": SUPPORTS_SERIES,
        "supports_subtitles": SUPPORTS_SUBTITLES,
    }


def bdix_get_servers() -> List[dict]:
    """Returns list of curated BDIX servers."""
    return POPULAR_BDIX_SERVERS


def bdix_search(query: str, page: int = 1) -> List[dict]:
    """Searches NaturalBD and returns catalog items."""
    q_clean = str(query or "").strip()
    q_lower = q_clean.lower()
    items: List[dict] = []
    seen_ids = set()

    # ১. NaturalBD থেকে লাইভ সার্চ
    if q_clean and q_lower not in ["all", "bdix", "ftp"]:
        search_url = f"{BASE_URL}/search?q={quote_plus(q_clean)}"
        try:
            res = requests.get(search_url, headers=HEADERS, timeout=7)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")

                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    title = a.get_text(strip=True)

                    if "/watch/" in href and href.endswith(".html"):
                        slug = href.split("/watch/")[-1].replace(".html", "").strip()

                        # বাটন টেক্সট ও ডুপ্লিকেট বাদ দেওয়া
                        if not slug or slug in seen_ids:
                            continue
                        if not title or title.upper() in ["WATCH NOW", "DOWNLOAD", "PLAY", "VIEW"]:
                            continue

                        seen_ids.add(slug)

                        # সাল এক্সট্র্যাক্ট করা
                        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", slug)
                        year = year_match.group(0) if year_match else "BDIX"

                        items.append(
                            make_catalog_item(
                                item_id=f"naturalbd_{slug}",
                                title=title,
                                media_type="movie",
                                provider=NAME,
                                year=year,
                                rating="HD",
                            )
                        )
        except Exception:
            pass

    # ২. যদি কোনো রেজাল্ট না পায় বা ব্রাউজ মোড হয়, তবে বিল্ট-ইন সার্ভার লিস্ট দেখানো
    if not items:
        servers = bdix_get_servers()
        for s in servers:
            s_name = s.get("name", "")
            s_cat = s.get("category", "")
            s_desc = s.get("description", "")
            if not q_lower or q_lower in s_name.lower() or q_lower in s_cat.lower() or q_lower in s_desc.lower():
                safe_id = f"bdix_{s_name.lower().replace(' ', '_').replace('/', '_')}"
                if safe_id not in seen_ids:
                    seen_ids.add(safe_id)
                    items.append(
                        make_catalog_item(
                            item_id=safe_id,
                            title=f"{s_name} [{s_cat}]",
                            media_type="movie",
                            provider=NAME,
                            year="BDIX",
                            rating=s.get("speed", "1Gbps"),
                        )
                    )

    return items


def bdix_get_details(media_id: str) -> Optional[dict]:
    """Fetches details for selected movie."""
    if str(media_id).startswith("naturalbd_"):
        slug = media_id.replace("naturalbd_", "")
        target_url = f"{BASE_URL}/watch/{slug}.html"

        try:
            res = requests.get(target_url, headers=HEADERS, timeout=7)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")

                title_elem = soup.find("meta", property="og:title")
                title = title_elem["content"] if title_elem else slug.replace("-", " ").title()

                desc_elem = soup.find("meta", property="og:description")
                desc = desc_elem["content"] if desc_elem else "BDIX High-Speed Streaming Mirror."

                genres = [g.get_text(strip=True) for g in soup.find_all("a", href=re.compile(r"/genre/"))]

                return make_media_details(
                    item_id=media_id,
                    title=title,
                    media_type="movie",
                    provider=NAME,
                    description=desc,
                    genres=genres if genres else ["Action", "BDIX"],
                    imdb_rating="BDIX",
                )
        except Exception:
            pass

    return make_media_details(
        item_id=media_id,
        title="BDIX Mirror",
        media_type="movie",
        provider=NAME,
        description="Bangladesh National Internet Exchange (BDIX) high-speed mirror.",
        genres=["BDIX", "FTP"],
        imdb_rating="BDIX",
    )


def bdix_get_streams(media_id: str, season: int = 0, episode: int = 0) -> List[dict]:
    mirrors: List[dict] = []
    target_name = "Movie"

    if str(media_id).startswith("naturalbd_"):
        slug = media_id.replace("naturalbd_", "")
        target_url = f"{BASE_URL}/watch/{slug}.html"
        target_name = slug.replace("-", " ").title()

        try:
            res = requests.get(target_url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                html_text = res.text

                # পেজ স্ক্রিপ্ট থেকে আসল .m3u8 লিংক খোঁজা
                m3u8_matches = re.findall(r"src:\s*['\"]([^'\"]+\.m3u8[^'\"]*)['\"]", html_text)
                for raw_link in m3u8_matches:
                    # স্পেস ঠিক রাখা (%20 ফরম্যাটে রাখা যাতে প্লেয়ারে এরর না আসে)
                    stream_url = raw_link.strip().replace(" ", "%20")

                    # ১. আসল HLS লাইভ স্ট্রিম (যা ব্রাউজারে সফলভাবে চলে)
                    mirrors.append(
                        make_source_mirror(
                            label="NaturalBD HLS Stream (Default)",
                            resolver_url=stream_url,
                            headers=HEADERS,
                            direct_file=True,
                        )
                    )

                    # ২. বিকল্প হিসেবে ডাইরেক্ট পাথ (যদি সার্ভার সাপোর্ট করে)
                    if ".mp4/playlist.m3u8" in stream_url:
                        direct_file_url = stream_url.replace("/playlist.m3u8", "")
                        mirrors.append(
                            make_source_mirror(
                                label="NaturalBD Direct MP4",
                                resolver_url=direct_file_url,
                                headers=HEADERS,
                                direct_file=True,
                            )
                        )
        except Exception:
            pass

    if not mirrors:
        return []

    return [
        make_release(
            provider=NAME,
            filename=f"{target_name} [BDIX 1080p]",
            quality="1080p",
            codec="HLS/m3u8",
            language="Multi",
            mirrors=mirrors,
            direct_url=mirrors[0]["resolver_url"],
            headers=HEADERS,
        )
    ]

