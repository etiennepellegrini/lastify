"""Spotify API client for searching and following artists."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from thefuzz import fuzz, process

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Client for interacting with the Spotify API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        verbose: bool = False,
    ) -> None:
        """Initialize the Spotify client.

        Args:
            client_id: Spotify client ID
            client_secret: Spotify client secret
            redirect_uri: Redirect URI for authentication
            verbose: Whether to enable verbose logging
        """
        scope = "user-follow-read user-follow-modify"
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
            )
        )
        self.verbose = verbose

        if verbose:
            user_info = self.sp.current_user()
            logger.info(
                f"Initialized Spotify client for user: {user_info['display_name']}"
            )

    def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Search for an artist on Spotify.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Artist information if found, None otherwise
        """
        results = self.sp.search(q=f"artist:{artist_name}", type="artist", limit=1)

        if not results["artists"]["items"]:
            if self.verbose:
                logger.warning(f"No results found for artist: {artist_name}")
            return None

        artist = results["artists"]["items"][0]

        if self.verbose:
            logger.info(f"Found artist: {artist['name']} (ID: {artist['id']})")

        return artist

    def fuzzy_search_artist(
        self, artist_name: str, threshold: int = 80
    ) -> Optional[Dict[str, Any]]:
        """Search for an artist on Spotify using fuzzy matching.

        Args:
            artist_name: Name of the artist to search for
            threshold: Minimum similarity score (0-100) to consider a match

        Returns:
            Artist information if found with score above threshold, None otherwise
        """
        # First try exact search
        exact_match = self.search_artist(artist_name)
        if exact_match and exact_match["name"].lower() == artist_name.lower():
            return exact_match

        # If no exact match, try a broader search
        results = self.sp.search(q=artist_name, type="artist", limit=10)

        if not results["artists"]["items"]:
            if self.verbose:
                logger.warning(
                    f"No fuzzy match results found for artist: {artist_name}"
                )
            return None

        # Get artist names from results
        artists = results["artists"]["items"]
        artist_names = [artist["name"] for artist in artists]

        # Find best match
        best_match, score = process.extractOne(
            artist_name, artist_names, scorer=fuzz.ratio
        )

        if score < threshold:
            if self.verbose:
                logger.warning(
                    f"Best fuzzy match for '{artist_name}' is '{best_match}' "
                    f"with score {score}, below threshold {threshold}"
                )
            return None

        # Get the artist info for the best match
        best_artist = next(
            (artist for artist in artists if artist["name"] == best_match), None
        )

        if self.verbose:
            logger.info(
                f"Fuzzy matched '{artist_name}' to '{best_match}' with score {score}"
            )

        return best_artist

    def interactive_search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Search for an artist on Spotify with interactive user confirmation.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Artist information if confirmed by user, None otherwise
        """
        # First try exact search
        exact_match = self.search_artist(artist_name)
        if exact_match and exact_match["name"].lower() == artist_name.lower():
            return exact_match

        # If no exact match, try a broader search
        results = self.sp.search(q=artist_name, type="artist", limit=5)

        if not results["artists"]["items"]:
            logger.warning(f"No results found for artist: {artist_name}")
            return None

        # Get artist options
        artists = results["artists"]["items"]

        # Display options to user
        print(f"\nSearching for artist: {artist_name}")
        print("Found these potential matches:")

        for i, artist in enumerate(artists):
            print(
                f"{i+1}. {artist['name']} (Followers: {artist['followers']['total']})"
            )

        print("0. None of these")

        # Get user choice
        while True:
            try:
                choice = int(input("Enter your choice (0-5): "))
                if 0 <= choice <= len(artists):
                    break
                print(f"Please enter a number between 0 and {len(artists)}")
            except ValueError:
                print("Please enter a valid number")

        if choice == 0:
            logger.info(f"User rejected all matches for artist: {artist_name}")
            return None

        selected_artist = artists[choice - 1]
        logger.info(
            f"User selected '{selected_artist['name']}' for artist: {artist_name}"
        )
        return selected_artist

    def follow_artist(self, artist_id: str) -> bool:
        """Follow an artist on Spotify.

        Args:
            artist_id: ID of the artist to follow

        Returns:
            True if successful, False otherwise
        """
        try:
            self.sp.user_follow_artists([artist_id])

            if self.verbose:
                artist = self.sp.artist(artist_id)
                logger.info(
                    f"Successfully followed artist: {artist['name']} (ID: {artist_id})"
                )

            return True
        except Exception as e:
            logger.error(f"Failed to follow artist (ID: {artist_id}): {str(e)}")
            return False

    def follow_artists(
        self,
        artists: List[Tuple[str, int]],
        match_mode: str = "strict",
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, List]:
        """Follow multiple artists on Spotify.

        Args:
            artists: List of (artist_name, play_count) tuples
            match_mode: Artist matching mode ("strict", "fuzzy", "interactive")
            dry_run: Whether to actually follow the artists or just simulate
            limit: Maximum number of artists to follow

        Returns:
            Dictionary with lists of successful, failed, and skipped artists
        """
        results = {
            "followed": [],
            "failed_to_match": [],
            "failed_to_follow": [],
            "skipped": [],
            "already_followed": [],
        }

        # Limit number of artists if specified
        if limit:
            artists = artists[:limit]

        if self.verbose:
            logger.info(
                f"Processing {len(artists)} artists with match mode: {match_mode}, "
                f"dry run: {dry_run}"
            )

        for artist_name, play_count in artists:
            if self.verbose:
                logger.info(f"Processing artist: {artist_name} ({play_count} plays)")

            # Search for the artist based on the match mode
            artist = None
            if match_mode == "strict":
                artist = self.search_artist(artist_name)
            elif match_mode == "fuzzy":
                artist = self.fuzzy_search_artist(artist_name)
            elif match_mode == "interactive":
                artist = self.interactive_search_artist(artist_name)
            else:
                logger.error(f"Unknown match mode: {match_mode}")
                continue

            # If no match found, add to failed list
            if not artist:
                results["failed_to_match"].append((artist_name, play_count))
                continue

            # Check if artists is already followed
            follow = self.sp.current_user_following_artists([artist["id"]])
            if follow:
                results["already_followed"].append((artist["name"], play_count))
                continue

            # Follow the artist if not in dry run mode
            if not dry_run:
                success = self.follow_artist(artist["id"])
                if success:
                    results["followed"].append((artist["name"], play_count))
                else:
                    results["failed_to_follow"].append((artist_name, play_count))
            else:
                if self.verbose:
                    logger.info(
                        f"[DRY RUN] Would follow artist: {artist['name']} (ID: {artist['id']})"
                    )
                results["skipped"].append((artist["name"], play_count))

        return results
