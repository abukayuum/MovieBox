from typing import Dict, List, Optional
from config import DEFAULT_PROVIDER

from .moviebox import (
    moviebox_search,
    moviebox_get_details,
    moviebox_get_streams,
    NAME as MOVIEBOX_NAME,
    LABEL as MOVIEBOX_LABEL,
)
from .fourkhdhub import (
    fourkhdhub_search,
    fourkhdhub_get_details,
    fourkhdhub_get_streams,
    NAME as FOURKHDHUB_NAME,
    LABEL as FOURKHDHUB_LABEL,
)
from .dramachi import (
    dramachi_search,
    dramachi_get_details,
    dramachi_get_streams,
    NAME as DRAMACHI_NAME,
    LABEL as DRAMACHI_LABEL,
)
from .bdix import (
    bdix_search,
    bdix_get_details,
    bdix_get_streams,
    NAME as BDIX_NAME,
    LABEL as BDIX_LABEL,
)

# Registry dictionary containing provider specifications
_PROVIDERS: Dict[str, dict] = {
    "moviebox": {
        "name": MOVIEBOX_NAME,
        "label": MOVIEBOX_LABEL,
        "supports_series": True,
        "supports_subtitles": True,
        "search": moviebox_search,
        "get_details": moviebox_get_details,
        "get_streams": moviebox_get_streams,
    },
    "fourkhdhub": {
        "name": FOURKHDHUB_NAME,
        "label": FOURKHDHUB_LABEL,
        "supports_series": True,
        "supports_subtitles": True,
        "search": fourkhdhub_search,
        "get_details": fourkhdhub_get_details,
        "get_streams": fourkhdhub_get_streams,
    },
    "dramachi": {
        "name": DRAMACHI_NAME,
        "label": DRAMACHI_LABEL,
        "supports_series": True,
        "supports_subtitles": False,
        "search": dramachi_search,
        "get_details": dramachi_get_details,
        "get_streams": dramachi_get_streams,
    },
    "bdix": {
        "name": BDIX_NAME,
        "label": BDIX_LABEL,
        "supports_series": True,
        "supports_subtitles": False,
        "search": bdix_search,
        "get_details": bdix_get_details,
        "get_streams": bdix_get_streams,
    },
}


def get_provider(name: Optional[str] = None) -> dict:
    """Retrieves a provider dictionary by unique name. Defaults to DEFAULT_PROVIDER."""
    p_name = (name or DEFAULT_PROVIDER).lower().strip()
    if p_name not in _PROVIDERS:
        return _PROVIDERS.get(DEFAULT_PROVIDER, list(_PROVIDERS.values())[0])
    return _PROVIDERS[p_name]


def list_providers() -> List[Dict[str, any]]:
    """Returns metadata list of all active working providers."""
    return [
        {
            "name": p["name"],
            "label": p["label"],
            "supports_series": p["supports_series"],
            "supports_subtitles": p["supports_subtitles"],
        }
        for p in _PROVIDERS.values()
    ]


__all__ = [
    "get_provider",
    "list_providers",
    "moviebox_search",
    "moviebox_get_details",
    "moviebox_get_streams",
    "fourkhdhub_search",
    "fourkhdhub_get_details",
    "fourkhdhub_get_streams",
    "dramachi_search",
    "dramachi_get_details",
    "dramachi_get_streams",
    "bdix_search",
    "bdix_get_details",
    "bdix_get_streams",
]
