import os
import random
import shutil
import sys

import click
from rich.console import Console

from yt_cli_player.api.youtube import get_all_playlist_items, get_playlists
from yt_cli_player.auth.oauth import login as do_login
from yt_cli_player.auth.token_store import delete_token
from yt_cli_player.config import IPC_SOCKET_PATH
from yt_cli_player.player.ipc import MpvIPC
from yt_cli_player.player.mpv_player import Player
from yt_cli_player.ui.browser import show_playlist_items, show_playlists
from yt_cli_player.ui.now_playing import run_player_ui

console = Console()


@click.group()
def main():
    """yt-music — play YouTube playlists from the terminal, audio only."""


@main.command()
def login():
    """Authenticate with your YouTube account via OAuth."""
    try:
        channel = do_login()
        console.print(f"[green]Logged in as:[/green] {channel}")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
def logout():
    """Clear stored authentication token."""
    delete_token()
    console.print("[yellow]Logged out.[/yellow]")


@main.command()
def browse():
    """Browse your playlists and pick tracks to play interactively."""
    _require_mpv()
    with console.status("Fetching playlists..."):
        try:
            playlists = get_playlists()
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)

    playlist = show_playlists(playlists)
    if not playlist:
        return

    videos = _fetch_playlist(playlist.title, playlist.id)
    if not videos:
        return

    page = 0
    while True:
        selected, action = show_playlist_items(videos, playlist.title, page)
        if action == "quit":
            return
        if action == "next":
            page += 1
        elif action == "prev":
            page -= 1
        elif action == "back":
            playlist = show_playlists(playlists)
            if not playlist:
                return
            videos = _fetch_playlist(playlist.title, playlist.id)
            if not videos:
                return
            page = 0
        elif action == "play" and selected:
            start = videos.index(selected)
            run_player_ui(Player(videos, start_index=start))
            return


@main.command()
def status():
    """Show what is currently playing (requires an active yt-music session)."""
    if not os.path.exists(IPC_SOCKET_PATH):
        console.print("[yellow]Nothing is playing.[/yellow]")
        return

    try:
        ipc = MpvIPC()
    except OSError:
        console.print("[yellow]Nothing is playing.[/yellow]")
        return

    try:
        title = ipc.get_property("media-title") or "Unknown"
        pos = ipc.get_property("time-pos") or 0.0
        duration = ipc.get_property("duration") or 0.0
        paused = ipc.get_property("pause") or False
    finally:
        ipc.close()

    def fmt(s: float) -> str:
        s = int(s)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    state = "[yellow]⏸ PAUSED[/yellow]" if paused else "[green]▶ PLAYING[/green]"
    bar_width = 30
    filled = min(int(bar_width * pos / duration), bar_width) if duration > 0 else 0
    progress = "█" * filled + "─" * (bar_width - filled)
    console.print(f"{state}  {title}")
    console.print(f"[dim]{fmt(pos)}  {progress}  {fmt(duration)}[/dim]")


@main.command()
@click.option("--shuffle", is_flag=True, help="Shuffle the queue before playing.")
def play(shuffle):
    """Play your Liked Videos. Add --shuffle to randomise order."""
    _require_mpv()
    videos = _fetch_playlist("Liked Videos", "LL")
    if not videos:
        return
    if shuffle:
        random.shuffle(videos)
    run_player_ui(Player(videos))


# ── helpers ──────────────────────────────────────────────────────────────────

def _require_mpv() -> None:
    if not shutil.which("mpv"):
        console.print("[red]mpv not found.[/red] Install with: [bold]sudo apt install mpv[/bold]")
        sys.exit(1)


def _fetch_playlist(title: str, playlist_id: str):
    with console.status(f"Fetching [bold]{title}[/bold]..."):
        try:
            videos = list(get_all_playlist_items(playlist_id))
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)
    if not videos:
        console.print("[yellow]No playable videos found in this playlist.[/yellow]")
    return videos
