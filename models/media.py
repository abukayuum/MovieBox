MEDIA_TYPE_MOVIE = "movie"
MEDIA_TYPE_SERIES = "series"


def make_catalog_item(item_id, title, media_type="movie", provider="moviebox", year=None, poster_url=None, season_count=None, rating=None):
    """Creates a catalog item dictionary."""
    return {
        "id": str(item_id or ""),
        "title": str(title or ""),
        "media_type": str(media_type or MEDIA_TYPE_MOVIE),
        "provider": str(provider or "moviebox"),
        "year": str(year) if year is not None else None,
        "poster_url": str(poster_url) if poster_url else None,
        "season_count": int(season_count) if season_count is not None else None,
        "rating": str(rating) if rating is not None else None,
    }


def make_episode(season, number, title=None, overview=None):
    """Creates an episode dictionary."""
    return {
        "season": int(season or 1),
        "number": int(number or 1),
        "title": str(title) if title else f"Episode {number}",
        "overview": str(overview) if overview else None,
    }


def make_season(number, episodes=None):
    """Creates a season dictionary."""
    return {
        "number": int(number or 1),
        "episodes": list(episodes or []),
    }


def make_dub_option(subject_id, language, label):
    """Creates an audio track / dub option dictionary."""
    return {
        "subject_id": str(subject_id or ""),
        "language": str(language or ""),
        "label": str(label or language or ""),
    }


def make_media_details(
    item_id,
    title,
    media_type="movie",
    provider="moviebox",
    year=None,
    description=None,
    tagline=None,
    imdb_rating=None,
    director=None,
    stars=None,
    poster_url=None,
    duration=None,
    genres=None,
    seasons=None,
    dubs=None,
):
    """Creates a media details dictionary."""
    m_type = str(media_type or MEDIA_TYPE_MOVIE)
    seasons_list = list(seasons or [])
    is_series = m_type == MEDIA_TYPE_SERIES or len(seasons_list) > 0

    return {
        "id": str(item_id or ""),
        "title": str(title or ""),
        "media_type": MEDIA_TYPE_SERIES if is_series else MEDIA_TYPE_MOVIE,
        "provider": str(provider or "moviebox"),
        "year": str(year) if year is not None else None,
        "description": str(description) if description else None,
        "tagline": str(tagline) if tagline else None,
        "imdb_rating": str(imdb_rating) if imdb_rating else None,
        "director": str(director) if director else None,
        "stars": str(stars) if stars else None,
        "poster_url": str(poster_url) if poster_url else None,
        "duration": str(duration) if duration else None,
        "genres": list(genres or []),
        "seasons": seasons_list,
        "dubs": list(dubs or []),
        "is_series": is_series,
    }


def CatalogItem(id="", title="", media_type="movie", provider="moviebox", year=None, poster_url=None, season_count=None, rating=None, **kwargs):
    """Functional catalog item constructor returning dictionary."""
    return make_catalog_item(item_id=id, title=title, media_type=media_type, provider=provider, year=year, poster_url=poster_url, season_count=season_count, rating=rating)


def MediaDetails(id="", title="", media_type="movie", provider="moviebox", year=None, description=None, tagline=None, imdb_rating=None, director=None, stars=None, poster_url=None, duration=None, genres=None, seasons=None, dubs=None, **kwargs):
    """Functional media details constructor returning dictionary."""
    return make_media_details(item_id=id, title=title, media_type=media_type, provider=provider, year=year, description=description, tagline=tagline, imdb_rating=imdb_rating, director=director, stars=stars, poster_url=poster_url, duration=duration, genres=genres, seasons=seasons, dubs=dubs)


MediaType = type("MediaType", (), {
    "MOVIE": MEDIA_TYPE_MOVIE,
    "SERIES": MEDIA_TYPE_SERIES,
    "movie": MEDIA_TYPE_MOVIE,
    "series": MEDIA_TYPE_SERIES,
})

