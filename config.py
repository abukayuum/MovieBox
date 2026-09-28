"""
MovieBox-TUI Configuration (Basic Procedural Python - No Classes)
Handles application settings, caching paths, default providers, and players.
"""
import os
from pathlib import Path

APP_NAME = "MovieBox-TUI"
APP_VERSION = "2.1.0"

# Base Cache & Config Directories
HOME_DIR = Path.home()
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", str(HOME_DIR / ".cache"))) / "moviebox_tui"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", str(HOME_DIR / ".config"))) / "moviebox_tui"

# Ensure directories exist
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Default Stream Referer & Headers
DEFAULT_STREAM_REFERER = "https://sportslive.wine"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Provider Settings
DEFAULT_PROVIDER = "moviebox"
ENABLED_PROVIDERS = ["moviebox", "fourkhdhub", "dramachi", "bdix"]

# Player Settings
SUPPORTED_PLAYERS = ["mpv", "intent", "mx"]
DEFAULT_PLAYER = "vlc"

# Default configuration dictionary
DEFAULT_CONFIG = {
    "provider": DEFAULT_PROVIDER,
    "player": DEFAULT_PLAYER,
    "cache_dir": str(CACHE_DIR),
    "download_dir": str(HOME_DIR / "Downloads" / "MovieBox"),
    "subtitles_enabled": True,
    "default_resolution": "1080p",
}

# Current in-memory configuration
_CURRENT_CONFIG = dict(DEFAULT_CONFIG)


def get_config(key=None, default=None):
    """Get full config dictionary or a specific key value."""
    if key is None:
        return dict(_CURRENT_CONFIG)
    return _CURRENT_CONFIG.get(key, default)


def set_config(key, value):
    """Set a specific config option."""
    _CURRENT_CONFIG[key] = value
    return _CURRENT_CONFIG


def reset_config():
    """Reset configuration to defaults."""
    global _CURRENT_CONFIG
    _CURRENT_CONFIG = dict(DEFAULT_CONFIG)
    return _CURRENT_CONFIG
