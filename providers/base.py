"""
Base Provider Specification (Basic Procedural Python - No Classes)
Standard dictionary specification for streaming content providers.
"""

def make_provider(name, label, search_func, details_func, streams_func, supports_series=True, supports_subtitles=True):
    """Creates a provider dictionary with callable functions."""
    return {
        "name": str(name),
        "label": str(label),
        "search": search_func,
        "get_details": details_func,
        "get_streams": streams_func,
        "supports_series": bool(supports_series),
        "supports_subtitles": bool(supports_subtitles),
    }
