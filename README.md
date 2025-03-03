# Lastify

A Python CLI tool to follow your most-listened Last.fm artists on Spotify.

## Features

- Gets artist statistics from Last.fm based on play counts
- Creates a list of all artists played more than a specified threshold
- Follows those artists on Spotify using your authentication
- Filter options for recent listens (e.g., "60 days" or "200 plays")
- Limit the number of artists followed
- Multiple matching modes to handle artist name variations:
  - `strict`: Only exact matches
  - `fuzzy`: Uses string similarity algorithms to match similar names
  - `interactive`: Asks you to select the correct artist from potential matches
- Verbose logging for detailed information
- Dry-run mode to test without actually following artists

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions and troubleshooting.

Quick start:
```bash
# Clone the repository
git clone https://github.com/yourusername/lastify.git
cd lastify

# Install with Poetry
poetry install

# Run the tool
poetry run lastify --help
```

## Development

If you're interested in contributing to this project, please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and development setup instructions.

## Usage

```bash
# Basic usage - follow all artists with at least 10 plays
lastify --username your_lastfm_username --threshold 10

# Follow artists with at least 5 plays in the last 60 days
lastify --username your_lastfm_username --threshold 5 --last "60 days"

# Follow artists from your last 200 plays
lastify --username your_lastfm_username --threshold 3 --last "200 plays"

# Limit to following only the top 20 artists
lastify --username your_lastfm_username --threshold 10 --limit-artists 20

# Use fuzzy matching for artist names
lastify --username your_lastfm_username --threshold 10 --match-mode fuzzy

# Interactive mode to confirm artist matches
lastify --username your_lastfm_username --threshold 10 --match-mode interactive

# Test run without actually following artists
lastify --username your_lastfm_username --threshold 10 --dry-run

# Verbose output for debugging
lastify --username your_lastfm_username --threshold 10 --verbose
```

### Command Options

```
Usage: lastify [OPTIONS]

  Follow your most listened to Last.fm artists on Spotify.

Options:
  --username TEXT                Last.fm username  [required]
  --threshold INTEGER            Minimum number of listens to consider an
                                 artist  [required]
  --limit-artists INTEGER        Maximum number of artists to follow
  --last TEXT                    Limit consideration to recent plays (e.g., "60
                                 days", "200 plays")
  --match-mode [strict|fuzzy|interactive]
                                 Artist matching mode  [default: strict]
  --verbose                      Enable verbose output
  --dry-run                      Test without actually following artists
  --lastfm-api-key TEXT          Last.fm API key (will be saved for future use)
  --lastfm-api-secret TEXT       Last.fm API secret (will be saved for future
                                 use)
  --spotify-client-id TEXT       Spotify client ID (will be saved for future
                                 use)
  --spotify-client-secret TEXT   Spotify client secret (will be saved for
                                 future use)
  --spotify-redirect-uri TEXT    Spotify redirect URI (will be saved for future
                                 use)
  --help                         Show this message and exit
```

## Configuration

API keys and settings are stored in `~/.lastify/config.json`. You can set them in three ways:

1. Command-line arguments (shown above)
2. Environment variables:
   ```
   export LASTFM_API_KEY=your_lastfm_api_key
   export LASTFM_API_SECRET=your_lastfm_api_secret
   export SPOTIFY_CLIENT_ID=your_spotify_client_id
   export SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   export SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
   ```
3. Directly editing the config file:
   ```json
   {
     "lastfm": {
       "api_key": "your_lastfm_api_key",
       "api_secret": "your_lastfm_api_secret"
     },
     "spotify": {
       "client_id": "your_spotify_client_id",
       "client_secret": "your_spotify_client_secret",
       "redirect_uri": "http://localhost:8888/callback"
     }
   }
   ```

## Examples

### Follow artists with minimum 20 plays, using fuzzy matching:

```bash
lastify --username your_lastfm_username --threshold 20 --match-mode fuzzy
```

### Test run to see what would be followed, with detailed output:

```bash
lastify --username your_lastfm_username --threshold 10 --dry-run --verbose
```

### Follow the top 15 artists from the last 30 days:

```bash
lastify --username your_lastfm_username --threshold 3 --last "30 days" --limit-artists 15
```

## Project Structure

```
lastify/
├── pyproject.toml         # Poetry configuration
├── README.md              # This file
├── INSTALL.md             # Installation instructions
├── CONTRIBUTING.md        # Development and contribution guidelines
├── lastify/
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface
│   ├── lastfm.py          # Last.fm API client
│   ├── spotify.py         # Spotify API client
│   └── utils.py           # Utility functions
└── tests/                 # Test files
```

## License

MIT
