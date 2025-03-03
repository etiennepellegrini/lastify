"""Tests for the lastify package."""

import os
from unittest.mock import MagicMock, patch

import pytest

from lastify import __version__
from lastify.lastfm import LastFMClient
from lastify.spotify import SpotifyClient
from lastify.utils import (
    get_lastfm_config,
    get_spotify_config,
    load_config,
    save_config,
)


def test_version():
    """Test that the version is set correctly."""
    assert __version__ == "0.1.0"


@patch("pylast.LastFMNetwork")
@patch("pylast.User")
def test_lastfm_client_init(mock_user, mock_network):
    """Test LastFMClient initialization."""
    # Setup mocks
    mock_network.return_value.get_user.return_value = mock_user

    # Create client
    client = LastFMClient(
        api_key="test_key", api_secret="test_secret", username="test_user"
    )

    # Check that LastFMNetwork was called correctly
    mock_network.assert_called_once_with(api_key="test_key", api_secret="test_secret")

    # Check that get_user was called correctly
    mock_network.return_value.get_user.assert_called_once_with("test_user")

    # Check that the client has the correct attributes
    assert client.network == mock_network.return_value
    assert client.user == mock_user
    assert client.username == "test_user"


@patch("spotipy.Spotify")
def test_spotify_client_init(mock_spotify):
    """Test SpotifyClient initialization."""
    # Setup mocks
    mock_spotify.return_value.current_user.return_value = {"display_name": "test_user"}

    # Create client
    client = SpotifyClient(
        client_id="test_id",
        client_secret="test_secret",
        redirect_uri="test_uri",
        verbose=True,
    )

    # Check that Spotify was initialized
    assert mock_spotify.call_count == 1

    # Check that the client has the correct attribute
    assert client.sp == mock_spotify.return_value


@patch("lastify.utils.get_config_path")
def test_load_config(mock_get_config_path, tmp_path):
    """Test load_config function."""
    # Create a temporary config file
    config_file = tmp_path / "config.json"
    config_file.write_text('{"test": "value"}')

    # Mock get_config_path to return our temporary file
    mock_get_config_path.return_value = config_file

    # Load the config
    config = load_config()

    # Check that the config was loaded correctly
    assert config == {"test": "value"}


@patch("lastify.utils.get_config_path")
def test_save_config(mock_get_config_path, tmp_path):
    """Test save_config function."""
    # Create a temporary config file
    config_file = tmp_path / "config.json"

    # Mock get_config_path to return our temporary file
    mock_get_config_path.return_value = config_file

    # Save a config
    save_config({"test": "value"})

    # Check that the config was saved correctly
    assert config_file.read_text() == '{\n    "test": "value"\n}'


@patch("lastify.utils.load_config")
@patch("os.environ")
def test_get_lastfm_config(mock_environ, mock_load_config):
    """Test get_lastfm_config function."""
    # Setup mocks
    mock_load_config.return_value = {"lastfm": {"api_key": "config_key"}}
    mock_environ.get.return_value = "env_secret"

    # Get config
    config = get_lastfm_config()

    # Check that the config was loaded correctly
    assert config == {"api_key": "config_key", "api_secret": "env_secret"}


@patch("lastify.utils.load_config")
@patch("os.environ")
def test_get_spotify_config(mock_environ, mock_load_config):
    """Test get_spotify_config function."""
    # Setup mocks
    mock_load_config.return_value = {
        "spotify": {"client_id": "config_id", "redirect_uri": "config_uri"}
    }
    mock_environ.get.return_value = "env_secret"

    # Get config
    config = get_spotify_config()

    # Check that the config was loaded correctly
    assert config == {
        "client_id": "config_id",
        "client_secret": "env_secret",
        "redirect_uri": "config_uri",
    }
