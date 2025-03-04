"""Command-line interface for lastify."""

import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from lastify.lastfm import LastFMClient
from lastify.spotify import SpotifyClient
from lastify.utils import (
    get_lastfm_config,
    get_spotify_config,
    save_lastfm_config,
    save_spotify_config,
    setup_logging,
)

logger = logging.getLogger(__name__)
console = Console()


@click.command()
@click.option("--username", required=True, help="Last.fm username")
@click.option(
    "--threshold",
    type=int,
    required=True,
    help="Minimum number of listens to consider an artist",
)
@click.option(
    "--limit-artists",
    type=int,
    help="Maximum number of artists to follow",
)
@click.option(
    "--last",
    help='Limit consideration to recent plays (e.g., "60 days", "200 plays")',
)
@click.option(
    "--match-mode",
    type=click.Choice(["strict", "fuzzy", "interactive"]),
    default="strict",
    help="Artist matching mode",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--dry-run", is_flag=True, help="Test without actually following artists")
@click.option("--show-progress", is_flag=True, help="Show progress bars for long operations")
@click.option(
    "--top",
    type=int,
    default=None,
    help="Use top N artists from Last.fm instead of counting plays",
)
@click.option(
    "--lastfm-api-key",
    help="Last.fm API key (will be saved for future use)",
)
@click.option(
    "--lastfm-api-secret",
    help="Last.fm API secret (will be saved for future use)",
)
@click.option(
    "--spotify-client-id",
    help="Spotify client ID (will be saved for future use)",
)
@click.option(
    "--spotify-client-secret",
    help="Spotify client secret (will be saved for future use)",
)
@click.option(
    "--spotify-redirect-uri",
    help="Spotify redirect URI (will be saved for future use)",
    default="http://localhost:8888/callback",
)
def main(
    username: str,
    threshold: int,
    limit_artists: Optional[int],
    last: Optional[str],
    match_mode: str,
    verbose: bool,
    dry_run: bool,
    show_progress: bool,
    top: Optional[int],
    lastfm_api_key: Optional[str],
    lastfm_api_secret: Optional[str],
    spotify_client_id: Optional[str],
    spotify_client_secret: Optional[str],
    spotify_redirect_uri: Optional[str],
) -> None:
    """Follow your most listened to Last.fm artists on Spotify.

    Example usage:

    # Follow all artists with at least 50 plays
    lastify --username your_lastfm_username --threshold 50

    # Follow up to 10 artists with at least 20 plays in the last 60 days
    lastify --username your_lastfm_username --threshold 20 --last "60 days" --limit-artists 10

    # Dry run with fuzzy matching and verbose output
    lastify --username your_lastfm_username --threshold 30 --match-mode fuzzy --verbose --dry-run

    # Follow your top 50 artists from Last.fm (faster method)
    lastify --username your_lastfm_username --top 50

    # Follow your top 20 artists from the last month with a minimum of 5 plays
    lastify --username your_lastfm_username --top 20 --last "1 month" --threshold 5
    """
    # Setup logging
    setup_logging(verbose)

    if verbose:
        console.print("[bold]Running lastify with the following options:[/bold]")
        console.print(f"  Username: {username}")
        console.print(f"  Threshold: {threshold}")
        console.print(f"  Limit artists: {limit_artists}")
        console.print(f"  Last: {last}")
        console.print(f"  Match mode: {match_mode}")
        console.print(f"  Verbose: {verbose}")
        console.print(f"  Dry run: {dry_run}")
        console.print(f"  Show progress: {show_progress}")
        if top:
            console.print(f"  Top artists: {top}")

    # Save API configurations if provided
    if lastfm_api_key or lastfm_api_secret:
        save_lastfm_config(lastfm_api_key, lastfm_api_secret)
        if verbose:
            console.print("[green]Saved Last.fm API configuration[/green]")

    if spotify_client_id or spotify_client_secret or spotify_redirect_uri:
        save_spotify_config(spotify_client_id, spotify_client_secret, spotify_redirect_uri)
        if verbose:
            console.print("[green]Saved Spotify API configuration[/green]")

    # Load API configurations
    lastfm_config = get_lastfm_config()
    spotify_config = get_spotify_config()

    # Check if required configurations are available
    if not lastfm_config.get("api_key") or not lastfm_config.get("api_secret"):
        console.print(
            "[red]Last.fm API key and secret are required. "
            "Please provide them using the --lastfm-api-key and --lastfm-api-secret options, "
            "or set them as environment variables (LASTFM_API_KEY, LASTFM_API_SECRET).[/red]"
        )
        sys.exit(1)

    if (
        not spotify_config.get("client_id")
        or not spotify_config.get("client_secret")
        or not spotify_config.get("redirect_uri")
    ):
        console.print(
            "[red]Spotify client ID, client secret, and redirect URI are required. "
            "Please provide them using the --spotify-client-id, --spotify-client-secret, "
            "and --spotify-redirect-uri options, "
            "or set them as environment variables "
            "(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI).[/red]"
        )
        sys.exit(1)

    # Initialize clients
    try:
        lastfm_client = LastFMClient(
            api_key=lastfm_config["api_key"],
            api_secret=lastfm_config["api_secret"],
            username=username,
            verbose=verbose,
        )

        spotify_client = SpotifyClient(
            client_id=spotify_config["client_id"],
            client_secret=spotify_config["client_secret"],
            redirect_uri=spotify_config["redirect_uri"],
            verbose=verbose,
        )
    except Exception as e:
        console.print(f"[red]Failed to initialize clients: {str(e)}[/red]")
        sys.exit(1)

    # Get artists by play count
    console.print(f"[bold]Getting artists with at least {threshold} plays...[/bold]")
    try:
        artists = lastfm_client.get_artists_by_playcount(threshold, last, show_progress=show_progress, top_n=top)
    except Exception as e:
        console.print(f"[red]Failed to get artists: {str(e)}[/red]")
        sys.exit(1)

    if not artists:
        console.print(f"[yellow]No artists found with at least {threshold} plays[/yellow]")
        sys.exit(0)

    console.print(f"[green]Found {len(artists)} artists with at least {threshold} plays[/green]")

    if verbose:
        # Display artists in a table
        table = Table(title=f"Artists with at least {threshold} plays")
        table.add_column("Artist", style="cyan")
        table.add_column("Plays", justify="right", style="green")

        for artist_name, play_count in artists:
            table.add_row(artist_name, str(play_count))

        console.print(table)

    # Follow artists on Spotify
    console.print(
        f"[bold]Following artists on Spotify (match mode: {match_mode}, dry run: {dry_run})...[/bold]"
    )
    results = spotify_client.follow_artists(
        artists=artists,
        match_mode=match_mode,
        dry_run=dry_run,
        limit=limit_artists,
    )

    # Print results
    if results["followed"]:
        console.print(f"[green]Successfully followed {len(results['followed'])} artists:[/green]")
        for artist, play_count in results["followed"]:
            console.print(f"  ✓ {artist} ({play_count} plays)")

    if results["skipped"]:
        console.print(f"[blue]Skipped {len(results['skipped'])} artists (dry run):[/blue]")
        for artist, play_count in results["skipped"]:
            console.print(f"  ⏩ {artist} ({play_count} plays)")

    if results["failed_to_match"]:
        console.print(f"[yellow]Failed to match {len(results['failed_to_match'])} artists:[/yellow]")
        for artist, play_count in results["failed_to_match"]:
            console.print(f"  ❓ {artist} ({play_count} plays)")

    if results["failed_to_follow"]:
        console.print(f"[red]Failed to follow {len(results['failed_to_follow'])} artists:[/red]")
        for artist, play_count in results["failed_to_follow"]:
            console.print(f"  ❌ {artist} ({play_count} plays)")

    console.print("[bold green]Done![/bold green]")


if __name__ == "__main__":
    main()  # pragma: no cover
