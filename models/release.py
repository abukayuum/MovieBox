def make_source_mirror(label, resolver_url, headers=None, direct_file=True):
    """Creates a source mirror dictionary."""
    return {
        "label": str(label or "Direct"),
        "resolver_url": str(resolver_url or ""),
        "headers": dict(headers or {}),
        "direct_file": bool(direct_file),
    }


def make_subtitle_option(name, url):
    """Creates a subtitle option dictionary."""
    return {
        "name": str(name or "Unknown"),
        "url": str(url or ""),
    }


def resolution_to_number(quality_str):
    """Parses quality string like '1080p', '4k', '720p' to integer for sorting."""
    if not quality_str:
        return 0
    q = str(quality_str).strip().lower()
    if "4k" in q or "uhd" in q or "2160" in q:
        return 2160
    if "1080" in q:
        return 1080
    if "720" in q:
        return 720
    if "480" in q:
        return 480
    if "360" in q:
        return 360
    # Try digits extraction
    digits = "".join(ch for ch in q if ch.isdigit())
    return int(digits) if digits else 0


def make_release(
    provider,
    filename,
    quality=None,
    codec=None,
    language=None,
    size_bytes=None,
    season=None,
    episode=None,
    mirrors=None,
    resource_id=None,
    subtitles=None,
    direct_url=None,
    headers=None,
):
    """Creates a release dictionary matching Rust MovieBox Release struct."""
    mirrors_list = list(mirrors or [])
    h_dict = dict(headers or {})
    d_url = direct_url

    if not d_url and mirrors_list:
        d_url = mirrors_list[0].get("resolver_url")
        if not h_dict:
            h_dict = mirrors_list[0].get("headers", {})

    if d_url and not mirrors_list:
        mirrors_list = [make_source_mirror("Direct", d_url, h_dict)]

    return {
        "provider": str(provider or "moviebox"),
        "filename": str(filename or ""),
        "quality": str(quality) if quality else None,
        "codec": str(codec) if codec else None,
        "language": str(language) if language else None,
        "size_bytes": int(size_bytes) if size_bytes is not None else None,
        "season": int(season) if season is not None else None,
        "episode": int(episode) if episode is not None else None,
        "direct_url": d_url,
        "headers": h_dict,
        "mirrors": mirrors_list,
        "subtitles": list(subtitles or []),
        "resource_id": str(resource_id) if resource_id is not None else None,
    }


def Release(provider="moviebox", filename="", quality=None, codec=None, language=None, size_bytes=None, season=None, episode=None, mirrors=None, resource_id=None, subtitles=None, direct_url=None, headers=None, **kwargs):
    """Functional release constructor returning dictionary."""
    return make_release(
        provider=provider,
        filename=filename,
        quality=quality,
        codec=codec,
        language=language,
        size_bytes=size_bytes,
        season=season,
        episode=episode,
        mirrors=mirrors,
        resource_id=resource_id,
        subtitles=subtitles,
        direct_url=direct_url,
        headers=headers,
    )


def SourceMirror(label="Direct", resolver_url="", headers=None, direct_file=True, **kwargs):
    """Functional mirror constructor returning dictionary."""
    return make_source_mirror(label=label, resolver_url=resolver_url, headers=headers, direct_file=direct_file)


def SubtitleOption(name="Unknown", url="", **kwargs):
    """Functional subtitle constructor returning dictionary."""
    return make_subtitle_option(name=name, url=url)

