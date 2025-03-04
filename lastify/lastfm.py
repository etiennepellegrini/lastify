"""Last.fm API client for retrieving artist statistics."""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pylast
from dateutil import parser
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

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
        self,
        limit: Optional[int] = None,
        time_from: Optional[int] = None,
        time_to: Optional[int] = None,
        show_progress: bool = False,
    ) -> List[pylast.PlayedTrack]:
        """Get recent tracks for the user with date filtering.

        Args:
            limit: Maximum number of tracks to retrieve (None for all available)
            time_from: Optional start timestamp (Unix time)
            time_to: Optional end timestamp (Unix time)
            show_progress: Whether to show a progress bar

        Returns:
            List of played tracks
        """
        if self.verbose:
            from_str = (
                f"from {datetime.fromtimestamp(time_from).strftime('%Y-%m-%d')}"
                if time_from
                else ""
            )
            to_str = (
                f"to {datetime.fromtimestamp(time_to).strftime('%Y-%m-%d')}"
                if time_to
                else ""
            )
            date_range = f" ({from_str} {to_str})".strip() if from_str or to_str else ""
            logger.info(
                f"Fetching recent tracks{date_range} (limit: {limit if limit else 'all'})"
            )

        try:
            # pylast doesn't directly support pagination through the get_recent_tracks method
            # and has unusual parameter names for date filters
            kwargs = {}

            # Set limit parameter
            if limit is not None:
                kwargs["limit"] = limit
            else:
                # Use a reasonable default if no limit specified
                kwargs["limit"] = 1000

            # Set date range parameters - pylast uses different parameter names
            # than what the Last.fm API documentation shows
            if time_from is not None:
                # Try different parameter variations since pylast isn't consistent
                kwargs["time_from"] = time_from

            if time_to is not None:
                kwargs["time_to"] = time_to

            # Simple single request approach - pylast handles pagination internally
            tracks = self.user.get_recent_tracks(**kwargs)

            if self.verbose:
                track_count = len(tracks) if isinstance(tracks, list) else 0
                logger.info(f"Retrieved {track_count} tracks")

            return tracks if isinstance(tracks, list) else []

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error retrieving tracks: {error_msg}")

            # Try with a simpler approach if there are parameter errors
            try:
                # Fall back to simplest possible call with just a limit
                logger.info("Trying with simpler parameters...")
                simple_limit = limit if limit is not None else 500
                tracks = self.user.get_recent_tracks(limit=simple_limit)

                if time_from is not None or time_to is not None:
                    logger.warning("Date filtering not applied in fallback method")

                if self.verbose:
                    track_count = len(tracks) if isinstance(tracks, list) else 0
                    logger.info(f"Retrieved {track_count} tracks with fallback method")

                return tracks if isinstance(tracks, list) else []

            except Exception as alt_e:
                logger.error(f"Fallback approach also failed: {str(alt_e)}")
                return []

    def get_tracks_by_date_range(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        show_progress: bool = False,
    ) -> List[pylast.PlayedTrack]:
        """Get all tracks between two dates.

        Args:
            start_date: Start date
            end_date: End date (defaults to now)
            show_progress: Whether to show a progress bar

        Returns:
            List of played tracks
        """
        if end_date is None:
            end_date = datetime.now()

        if self.verbose:
            logger.info(
                f"Fetching tracks from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )

        # Convert dates to timestamps
        time_from = int(start_date.timestamp())
        time_to = int(end_date.timestamp())

        # Get tracks with date filtering
        return self.get_recent_tracks(
            time_from=time_from, time_to=time_to, show_progress=show_progress
        )

    def get_artists_from_tracks(
        self, tracks: List[pylast.PlayedTrack], threshold: int = 1
    ) -> List[Tuple[str, int]]:
        """Count artist plays from a list of tracks.

        Args:
            tracks: List of played tracks
            threshold: Minimum number of plays to include an artist

        Returns:
            List of (artist_name, play_count) tuples above threshold
        """
        # Count plays per artist
        artist_counts = {}
        for track in tracks:
            artist_name = track.track.artist.name
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1

        # Filter by threshold
        filtered_artists = [
            (artist, count)
            for artist, count in artist_counts.items()
            if count >= threshold
        ]

        # Sort by play count (descending)
        return sorted(filtered_artists, key=lambda x: x[1], reverse=True)

    def get_top_n_artists(
        self, n: int, period: str = "overall"
    ) -> List[Tuple[str, int]]:
        """Get the top N artists for the user.

        Args:
            n: Number of top artists to retrieve
            period: Time period ("overall", "7day", "1month", "3month", "6month", "12month")

        Returns:
            List of (artist_name, play_count) tuples
        """
        if self.verbose:
            logger.info(f"Fetching top {n} artists for period: {period}")

        top_artists = self.user.get_top_artists(period=period, limit=n)

        # Convert to our standard format of (artist_name, play_count)
        artist_playcounts = [
            (artist.item.name, int(artist.weight)) for artist in top_artists
        ]

        if self.verbose:
            logger.info(f"Retrieved {len(artist_playcounts)} top artists")

        return artist_playcounts

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

    def map_time_filter_to_period(self, time_filter: str) -> str:
        """Map a time filter string to a Last.fm period.

        Args:
            time_filter: Time filter string (e.g., "7 days", "1 month")

        Returns:
            Last.fm period string
        """
        if "7" in time_filter and "day" in time_filter:
            return "7day"
        elif "1" in time_filter and "month" in time_filter:
            return "1month"
        elif "3" in time_filter and "month" in time_filter:
            return "3month"
        elif "6" in time_filter and "month" in time_filter:
            return "6month"
        elif ("12" in time_filter and "month" in time_filter) or "year" in time_filter:
            return "12month"
        else:
            return "overall"

    def get_artists_by_playcount(
        self,
        threshold: int,
        time_filter: Optional[str] = None,
        show_progress: bool = False,
        top_n: Optional[int] = None,
    ) -> List[Tuple[str, int]]:
        """Get artists with play counts above the threshold or top N artists.

        Args:
            threshold: Minimum number of plays to include an artist
            time_filter: Optional time filter (e.g., "60 days", "200 plays")
            show_progress: Whether to show a progress bar
            top_n: If specified, returns the top N artists regardless of threshold

        Returns:
            List of (artist_name, play_count) tuples
        """
        # If top_n is specified, use the top artists method
        if top_n is not None:
            if self.verbose:
                logger.info(f"Getting top {top_n} artists")

            # Map time filter to period if provided
            period = "overall"
            if time_filter:
                period = self.map_time_filter_to_period(time_filter)

            artists = self.get_top_n_artists(n=top_n, period=period)

            # Filter by threshold if specified
            if threshold > 0:
                filtered_artists = [
                    (artist_name, play_count)
                    for artist_name, play_count in artists
                    if play_count >= threshold
                ]

                if self.verbose:
                    logger.info(
                        f"Found {len(filtered_artists)} artists from top {top_n} with at least {threshold} plays"
                    )

                return filtered_artists

            if self.verbose:
                logger.info(f"Retrieved top {len(artists)} artists")

            return artists

        # Normal flow using play count threshold
        if time_filter is None:
            # Get all-time top artists
            artists = self.get_top_n_artists(n=1000)  # Use a reasonable limit
            filtered_artists = [
                (artist_name, play_count)
                for artist_name, play_count in artists
                if play_count >= threshold
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

            # Get tracks in date range
            tracks = self.get_tracks_by_date_range(
                start_date=since_date, show_progress=show_progress
            )

            # Count artists from these tracks
            artists = self.get_artists_from_tracks(tracks, threshold)

            if self.verbose:
                logger.info(
                    f"Found {len(artists)} artists with at least {threshold} plays in the last {days} days"
                )

            return artists

        elif "plays" in time_filter:
            plays = int(time_filter.split()[0])

            if self.verbose:
                logger.info(f"Filtering based on the last {plays} plays")

            # Get the specified number of recent tracks
            tracks = self.get_recent_tracks(limit=plays, show_progress=show_progress)

            # Count artists from these tracks
            artists = self.get_artists_from_tracks(tracks, threshold)

            if self.verbose:
                logger.info(
                    f"Found {len(artists)} artists with at least {threshold} plays in the last {plays} scrobbles"
                )

            return artists

        else:
            raise ValueError(f"Invalid time filter format: {time_filter}")
