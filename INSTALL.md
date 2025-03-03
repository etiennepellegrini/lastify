# Installation Guide

## Python Version Compatibility

This package has been updated to support Python 3.13. The original version used `python-Levenshtein` for fuzzy string matching, which doesn't yet support Python 3.13 due to internal C API changes.

## Installation Steps

1. Ensure you have Poetry installed:
   ```bash
   # Install with pipx (recommended)
   pipx install poetry
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lastify.git
   cd lastify
   ```

3. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

4. Verify the installation:
   ```bash
   poetry run lastify --help
   ```

## Troubleshooting

### If you encounter installation errors:

1. Make sure you're using Python 3.8 or newer:
   ```bash
   python --version
   ```

2. Try updating Poetry:
   ```bash
   pipx upgrade poetry
   ```

3. You can create a new virtual environment with a specific Python version:
   ```bash
   poetry env use /path/to/python
   ```

4. Clear Poetry's cache if needed:
   ```bash
   poetry cache clear --all pypi
   ```

## API Keys Setup

Before using the tool, you'll need to set up API keys for Last.fm and Spotify:

### Last.fm API

1. Create a Last.fm API account at https://www.last.fm/api/account/create
2. Note down your API key and API secret

### Spotify API

1. Go to the Spotify Developer Dashboard at https://developer.spotify.com/dashboard/
2. Create a new application
3. Set a redirect URI (e.g., `http://localhost:8888/callback`)
4. Note down your client ID and client secret

You can provide these keys directly when running the tool, or set them as environment variables:

```bash
export LASTFM_API_KEY=your_lastfm_api_key
export LASTFM_API_SECRET=your_lastfm_api_secret
export SPOTIFY_CLIENT_ID=your_spotify_client_id
export SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
export SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
```

## Changes from Original Version

- Replaced `fuzzywuzzy` and `python-Levenshtein` with `thefuzz` (a maintained fork that provides better Python 3 compatibility)
- Updated code to work with the newer library
