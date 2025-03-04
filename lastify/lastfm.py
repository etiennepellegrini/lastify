"""Last.fm API client for retrieving artist statistics."""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import pylast
from dateutil import parser
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

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
        batch_size: int = 200,
        show_progress: bool = False
    ) -> List[pylast.PlayedTrack]:
        """Get recent tracks for the user with pagination and date filtering.

        Args:
            limit: Maximum number of tracks to retrieve (None for all available)
            time_from: Optional start timestamp (Unix time)
            time_to: Optional end timestamp (Unix time)
            batch_size: Number of tracks per API request (max 200)
            show_progress: Whether to show a progress bar

        Returns:
            List of played tracks
        """
        if self.verbose:
            from_str = f"from {datetime.fromtimestamp(time_from).strftime('%Y-%m-%d')}" if time_from else ""
            to_str = f"to {datetime.fromtimestamp(time_to).strftime('%Y-%m-%d')}" if time_to else ""
            date_range = f" ({from_str} {to_str})".strip() if from_str or to_str else ""
            logger.info(f"Fetching recent tracks{date_range} (limit: {limit if limit else 'all'})")

        # Ensure batch_size doesn't exceed API maximum
        batch_size = min(batch_size, 200)

        # First, make a request to get an initial batch and check response format
        kwargs = {
            'limit': 1
        }

        # Add time filtering parameters if provided
        if time_from is not None:
            kwargs['time_from'] = time_from
        if time_to is not None:
            kwargs['time_to'] = time_to

        initial_tracks = self.user.get_recent_tracks(**kwargs)

        # Determine total number of tracks available (may be limited by Last.fm API)
        if hasattr(initial_tracks, "total_pages"):
            # For newer pylast versions that expose pagination info directly
            total_pages = initial_tracks.total_pages
            total_tracks = total_pages * batch_size  # Estimate
            if self.verbose:
                logger.info(f"API reports {total_pages} pages of tracks")
        else:
            # Default to a reasonable number if we can't determine
            total_pages = 50  # Last.fm typically limits to 50 pages
            total_tracks = total_pages * batch_size
            if self.verbose:
                logger.info(f"Unable to determine total tracks, using default of {total_tracks}")

        # If limit is specified, adjust our estimated total
        if limit is not None:
            total_tracks = min(total_tracks, limit)
            total_pages = (total_tracks + batch_size - 1) // batch_size

        all_tracks = []

        # Set up progress bar if requested
        if show_progress and total_pages > 1:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn()
            ) as progress:
                fetch_task = progress.add_task(f"Fetching {total_tracks} tracks...", total=total_pages)

                for page_num in range(1, total_pages + 1):
                    # Set up parameters for this page
                    kwargs = {
                        'limit': batch_size
                    }

                    # Add time filtering parameters if provided
                    if time_from is not None:
                        kwargs['time_from'] = time_from
                    if time_to is not None:
                        kwargs['time_to'] = time_to

                    # pylast doesn't use a 'page' parameter; instead it uses a 'startpage' parameter
                    # for the specific page we want
                    if page_num > 1:
                        kwargs['startpage'] = page_num

                    page_tracks = self.user.get_recent_tracks(**kwargs)

                    # Add tracks from this page
                    if isinstance(page_tracks, list):
                        all_tracks.extend(page_tracks)
                    else:
                        # If no tracks were returned, break the loop
                        break

                    progress.update(fetch_task, advance=1)

                    # If we reached the limit, stop fetching
                    if limit is not None and len(all_tracks) >= limit:
                        all_tracks = all_tracks[:limit]
                        break

                    # If we got fewer tracks than batch_size, we've reached the end
                    if len(page_tracks) < batch_size:
                        break
        else:
            # No progress bar, just fetch pages
            for page_num in range(1, total_pages + 1):
                if self.verbose and total_pages > 1:
                    logger.info(f"Fetching page {page_num}/{total_pages}...")

                # Set up parameters for this page
                kwargs = {
                    'limit': batch_size
                }

                # Add time filtering parameters if provided
                if time_from is not None:
                    kwargs['time_from'] = time_from
                if time_to is not None:
                    kwargs['time_to'] = time_to

                # pylast doesn't use a 'page' parameter; instead it uses a 'startpage' parameter
                if page_num > 1:
                    kwargs['startpage'] = page_num

                page_tracks = self.user.get_recent_tracks(**kwargs)

                # Add tracks from this page
                if isinstance(page_tracks, list):
                    all_tracks.extend(page_tracks)
                else:
                    # If no tracks were returned, break the loop
                    break

                # If we reached the limit, stop fetching
                if limit is not None and len(all_tracks) >= limit:
                    all_tracks = all_tracks[:limit]
                    break

                # If we got fewer tracks than batch_size, we've reached the end
                if len(page_tracks) < batch_size:
                    break

        if self.verbose:
            logger.info(f"Retrieved {len(all_tracks)} tracks total")

        return all_tracks

    def _chunk_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        chunk_days: int = 90
    ) -> List[Tuple[int, int]]:
        """Split a large date range into smaller chunks to avoid API limitations.

        Args:
            start_date: Start date
            end_date: End date
            chunk_days: Number of days per chunk

        Returns:
            List of (from_timestamp, to_timestamp) tuples
        """
        chunks = []
        current_date = start_date

        while current_date < end_date:
            next_date = min(current_date + timedelta(days=chunk_days), end_date)

            # Convert to Unix timestamps
            from_ts = int(current_date.timestamp())
            to_ts = int(next_date.timestamp())

            chunks.append((from_ts, to_ts))
            current_date = next_date

        return chunks

    def get_tracks_by_date_chunks(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        chunk_days: int = 90,
        show_progress: bool = False
    ) -> List[pylast.PlayedTrack]:
        """Get all tracks between dates by splitting into multiple requests.

        Args:
            start_date: Start date
            end_date: End date (defaults to now)
            chunk_days: Number of days per chunk
            show_progress: Whether to show a progress bar

        Returns:
            List of played tracks
        """
        if end_date is None:
            end_date = datetime.now()

        if self.verbose:
            logger.info(f"Fetching tracks from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Split date range into chunks
        date_chunks = self._chunk_date_range(start_date, end_date, chunk_days)

        if self.verbose:
            logger.info(f"Split date range into {len(date_chunks)} chunks")

        all_tracks = []

        # Set up progress bar if requested
        if show_progress and len(date_chunks) > 1:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TimeRemainingColumn()
            ) as progress:
                chunk_task = progress.add_task(f"Processing date ranges...", total=len(date_chunks))

                for i, (from_ts, to_ts) in enumerate(date_chunks):
                    if self.verbose:
                        from_date = datetime.fromtimestamp(from_ts)
                        to_date = datetime.fromtimestamp(to_ts)
                        logger.info(f"Fetching chunk {i+1}/{len(date_chunks)}: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")

                    # Get tracks for this date range
                    chunk_tracks = self.get_recent_tracks(
                        time_from=from_ts,
                        time_to=to_ts,
                        show_progress=False  # Don't show nested progress bars
                    )

                    all_tracks.extend(chunk_tracks)
                    progress.update(chunk_task, advance=1)
        else:
            # No progress bar
            for i, (from_ts, to_ts) in enumerate(date_chunks):
                if self.verbose:
                    from_date = datetime.fromtimestamp(from_ts)
                    to_date = datetime.fromtimestamp(to_ts)
                    logger.info(f"Fetching chunk {i+1}/{len(date_chunks)}: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")

                # Get tracks for this date range
                chunk_tracks = self.get_recent_tracks(
                    time_from=from_ts,
                    time_to=to_ts,
                    show_progress=show_progress
                )

                all_tracks.extend(chunk_tracks)

        return all_tracks

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
        self, threshold: int, time_filter: Optional[str] = None, show_progress: bool = False
    ) -> List[Tuple[str, int]]:
        """Get artists with play counts above the threshold.

        Args:
            threshold: Minimum number of plays to include an artist
            time_filter: Optional time filter (e.g., "60 days", "200 plays")
            show_progress: Whether to show a progress bar

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

            # Use the optimized date-filtered approach
            return self._get_artists_from_date_range(
                threshold=threshold,
                since_date=since_date,
                show_progress=show_progress
            )

        elif "plays" in time_filter:
            plays = int(time_filter.split()[0])

            if self.verbose:
                logger.info(f"Filtering based on the last {plays} plays")

            # For limiting by number of plays, we use the direct approach
            # since we need exactly that many plays
            return self._get_artists_from_recent_tracks(
                threshold=threshold,
                limit_tracks=plays,
                show_progress=show_progress
            )

        else:
            raise ValueError(f"Invalid time filter format: {time_filter}")

    def _get_artists_from_date_range(
        self,
        threshold: int,
        since_date: datetime,
        end_date: Optional[datetime] = None,
        show_progress: bool = False,
    ) -> List[Tuple[str, int]]:
        """Get artists from tracks within a date range with play counts above the threshold.

        Args:
            threshold: Minimum number of plays to include an artist
            since_date: Start date for filtering
            end_date: End date for filtering (defaults to now)
            show_progress: Whether to show a progress bar

        Returns:
            List of (artist_name, play_count) tuples for artists above the threshold
        """
        if end_date is None:
            end_date = datetime.now()

        # Get tracks in date range using chunked approach to overcome API limitations
        tracks = self.get_tracks_by_date_chunks(
            start_date=since_date,
            end_date=end_date,
            show_progress=show_progress
        )

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

        if self.verbose:
            logger.info(
                f"Found {len(filtered_artists)} artists with at least {threshold} plays"
            )

        return sorted(filtered_artists, key=lambda x: x[1], reverse=True)

    def _get_artists_from_recent_tracks(
        self,
        threshold: int,
        since_date: Optional[datetime] = None,
        limit_tracks: Optional[int] = None,
        show_progress: bool = False,
    ) -> List[Tuple[str, int]]:
        """Get artists from recent tracks with play counts above the threshold.

        Args:
            threshold: Minimum number of plays to include an artist
            since_date: Only consider tracks after this date
            limit_tracks: Only consider this many recent tracks
            show_progress: Whether to show a progress bar

        Returns:
            List of (artist_name, play_count) tuples for artists above the threshold
        """
        # Convert since_date to Unix timestamp if provided
        time_from = None
        if since_date:
            time_from = int(since_date.timestamp())

        # Get recent tracks with optimized approach
        recent_tracks = self.get_recent_tracks(
            limit=limit_tracks,
            time_from=time_from,
            show_progress=show_progress
        )

        # Count plays per artist
        artist_counts = {}
        for track in recent_tracks:
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
