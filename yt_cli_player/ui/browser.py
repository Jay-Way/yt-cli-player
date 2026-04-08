import math
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from yt_cli_player.api.models import Playlist, Video

console = Console()
PAGE_SIZE = 20


def _trunc(text: str, n: int = 60) -> str:
    return text[:n - 1] + "…" if len(text) > n else text


def show_playlists(playlists: list[Playlist]) -> Playlist | None:
    console.clear()
    table = Table(title="Your Playlists", header_style="bold cyan", show_lines=False)
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", min_width=30)
    table.add_column("Videos", justify="right", width=8)
    for i, pl in enumerate(playlists, 1):
        count = str(pl.item_count) if pl.item_count else "?"
        table.add_row(str(i), _trunc(pl.title), count)
    console.print(table)
    choice = Prompt.ask("\nSelect playlist (number) or [bold]q[/bold] to quit", default="q")
    if choice.lower() == "q":
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(playlists):
            return playlists[idx]
    except ValueError:
        pass
    return None


def show_playlist_items(
    videos: list[Video], playlist_title: str, page: int = 0
) -> tuple[Video | None, str]:
    """
    Show a page of tracks. Returns (selected_video | None, action).
    action is one of: 'play', 'next', 'prev', 'back', 'quit'
    """
    total_pages = max(1, math.ceil(len(videos) / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_items = videos[start:start + PAGE_SIZE]

    console.clear()
    table = Table(
        title=f"{_trunc(playlist_title, 50)}  [dim](page {page + 1}/{total_pages})[/dim]",
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=5)
    table.add_column("Title", min_width=40)
    table.add_column("Channel", min_width=20)
    table.add_column("Duration", justify="right", width=9)
    for i, v in enumerate(page_items, start + 1):
        table.add_row(str(i), _trunc(v.title), _trunc(v.channel, 30), v.duration_str)
    console.print(table)

    hints = ["number to play"]
    if page > 0:
        hints.append("[bold]p[/bold] prev")
    if page < total_pages - 1:
        hints.append("[bold]n[/bold] next")
    hints += ["[bold]b[/bold] back", "[bold]q[/bold] quit"]
    choice = Prompt.ask(f"\n{', '.join(hints)}", default="b")

    ch = choice.lower().strip()
    if ch == "q":
        return None, "quit"
    if ch == "b":
        return None, "back"
    if ch == "n":
        return None, "next"
    if ch == "p":
        return None, "prev"
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(videos):
            return videos[idx], "play"
    except ValueError:
        pass
    return None, "back"
