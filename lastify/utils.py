"""Utility functions for the lastify package."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure the root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_config_path() -> Path:
    """Get the path to the config file.

    Returns:
        Path to the config file
    """
    config_dir = Path.home() / ".lastify"
    config_dir.mkdir(exist_ok=True)

    return config_dir / "config.json"


def load_config() -> Dict:
    """Load configuration from the config file.

    Returns:
        Configuration dictionary
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        return {}


def save_config(config: Dict) -> None:
    """Save configuration to the config file.

    Args:
        config: Configuration dictionary
    """
    config_path = get_config_path()

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save config: {str(e)}")


def get_lastfm_config() -> Dict:
    """Get Last.fm API configuration.

    Returns:
        Last.fm API configuration dictionary
    """
    config = load_config()

    lastfm_config = config.get("lastfm", {})

    # Try to get from environment variables if not in config
    if not lastfm_config.get("api_key"):
        lastfm_config["api_key"] = os.environ.get("LASTFM_API_KEY")

    if not lastfm_config.get("api_secret"):
        lastfm_config["api_secret"] = os.environ.get("LASTFM_API_SECRET")

    return lastfm_config


def get_spotify_config() -> Dict:
    """Get Spotify API configuration.

    Returns:
        Spotify API configuration dictionary
    """
    config = load_config()

    spotify_config = config.get("spotify", {})

    # Try to get from environment variables if not in config
    if not spotify_config.get("client_id"):
        spotify_config["client_id"] = os.environ.get("SPOTIFY_CLIENT_ID")

    if not spotify_config.get("client_secret"):
        spotify_config["client_secret"] = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not spotify_config.get("redirect_uri"):
        spotify_config["redirect_uri"] = os.environ.get(
            "SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"
        )

    return spotify_config


def save_lastfm_config(
    api_key: Optional[str] = None, api_secret: Optional[str] = None
) -> None:
    """Save Last.fm API configuration.

    Args:
        api_key: Last.fm API key
        api_secret: Last.fm API secret
    """
    config = load_config()

    if "lastfm" not in config:
        config["lastfm"] = {}

    if api_key:
        config["lastfm"]["api_key"] = api_key

    if api_secret:
        config["lastfm"]["api_secret"] = api_secret

    save_config(config)


def save_spotify_config(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: Optional[str] = None,
) -> None:
    """Save Spotify API configuration.

    Args:
        client_id: Spotify client ID
        client_secret: Spotify client secret
        redirect_uri: Redirect URI for authentication
    """
    config = load_config()

    if "spotify" not in config:
        config["spotify"] = {}

    if client_id:
        config["spotify"]["client_id"] = client_id

    if client_secret:
        config["spotify"]["client_secret"] = client_secret

    if redirect_uri:
        config["spotify"]["redirect_uri"] = redirect_uri

    save_config(config)
