"""Last.fm API client for retrieving artist statistics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import pylast
from dateutil import parser

logger = logging.getLogger(__name__)


class LastFMClient:
    """Client for interacting with the Last.fm API."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        username: str,
        verbose: bool = False,
    ) -> None:
        """Initialize the Last.fm client.

        Args:
            api_key: Last.fm API key
            api_secret: Last.fm API secret
            username: Last.fm username
            verbose: Whether to enable verbose logging
        """
        self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
        self.user = self.network.get_user(username)
        self.username = username
        self.verbose = verbose

        if verbose:
            logger.info(f"Initialized Last.fm client for user: {username}")

    def get_recent_tracks(
        self, limit: Optional[int] = None
    ) -> List[pylast.PlayedTrack]:
        """Get recent tracks for the user.

        Args:
            limit: Maximum number of tracks to retrieve

        Returns:
            List of played tracks
        """
        if self.verbose:
            logger.info(f"Fetching recent tracks (limit: {limit})")

        return self.user.get_recent_tracks(limit=limit)

    def get_top_artists(
        self, period: str = "overall", limit: Optional[int] = None
    ) -> List[pylast.TopItem]:
        """Get top artists for the user.

        Args:
            period: Time period ("overall", "7day", "1month", "3month", "6month", "12month")
            limit: Maximum number of artists to retrieve

        Returns:
            List of top artists with play counts
        """
        if self.verbose:
            logger.info(f"Fetching top artists for period: {period} (limit: {limit})")

        return self.user.get_top_artists(period=period, limit=limit)

    def get_artist_playcount(self, artist_name: str) -> int:
        """Get the play count for a specific artist.

        Args:
            artist_name: Name of the artist

        Returns:
            Number of times the artist has been played
        """
        artist = self.network.get_artist(artist_name)
        try:
            playcount = self.user.get_artist_playcount(artist)
            if self.verbose:
                logger.info(f"Artist '{artist_name}' has been played {playcount} times")
            return playcount
        except pylast.WSError:
            if self.verbose:
                logger.warning(f"Failed to get play count for artist: {artist_name}")
            return 0

    def get_artists_by_playcount(
        self, threshold: int, time_filter: Optional[str] = None
    ) -> List[Tuple[str, int]]:
        """Get artists with play counts above the threshold.

        Args:
            threshold: Minimum number of plays to include an artist
            time_filter: Optional time filter (e.g., "60 days", "200 plays")

        Returns:
            List of (artist_name, play_count) tuples for artists above the threshold
        """
        if time_filter is None:
            # Get all-time top artists
            artists = self.get_top_artists(limit=None)
            filtered_artists = [
                (artist.item.name, artist.weight)
                for artist in artists
                if int(artist.weight) >= threshold
            ]

            if self.verbose:
                logger.info(
                    f"Found {len(filtered_artists)} artists with at least {threshold} plays"
                )

            return filtered_artists

        # Parse time filter
        if "days" in time_filter:
            days = int(time_filter.split()[0])
            since_date = datetime.now() - timedelta(days=days)

            if self.verbose:
                logger.info(f"Filtering tracks from the last {days} days")

            return self._get_artists_from_recent_tracks(threshold, since_date)

        elif "plays" in time_filter:
            plays = int(time_filter.split()[0])

            if self.verbose:
                logger.info(f"Filtering based on the last {plays} plays")

            return self._get_artists_from_recent_tracks(threshold, limit_tracks=plays)

        else:
            raise ValueError(f"Invalid time filter format: {time_filter}")

    def _get_artists_from_recent_tracks(
        self,
        threshold: int,
        since_date: Optional[datetime] = None,
        limit_tracks: Optional[int] = None,
    ) -> List[Tuple[str, int]]:
        """Get artists from recent tracks with play counts above the threshold.

        Args:
            threshold: Minimum number of plays to include an artist
            since_date: Only consider tracks after this date
            limit_tracks: Only consider this many recent tracks

        Returns:
            List of (artist_name, play_count) tuples for artists above the threshold
        """
        recent_tracks = self.get_recent_tracks(limit=limit_tracks)

        # Count plays per artist
        artist_counts = {}

        for track in recent_tracks:
            # Skip if track is before since_date
            if since_date:
                track_date = parser.parse(track.playback_date)
                if track_date < since_date:
                    continue

            artist_name = track.track.artist.name
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1

        # Filter by threshold
        filtered_artists = [
            (artist, count)
            for artist, count in artist_counts.items()
            if count >= threshold
        ]

        if self.verbose:
            logger.info(
                f"Found {len(filtered_artists)} artists with at least {threshold} plays"
            )

        return sorted(filtered_artists, key=lambda x: x[1], reverse=True)
