import select
import sys
import termios
import threading
import tty
import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from yt_cli_player.api.models import Video
from yt_cli_player.player.mpv_player import Player

console = Console()


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _progress_bar(elapsed: float, total: float, width: int = 30) -> str:
    if total <= 0:
        return "─" * width
    filled = min(int(width * elapsed / total), width)
    return "█" * filled + "─" * (width - filled)


def _make_panel(player: Player, current: Video | None) -> Panel:
    if not current:
        return Panel("[dim]No track playing[/dim]", title="[bold cyan]yt-music[/bold cyan]")

    elapsed = player.get_position() or 0.0
    total = current.duration_seconds
    paused = player.is_paused()

    if player.last_error:
        status = f"[red]✗ ERROR[/red] [dim]{player.last_error[:80]}[/dim]"
    elif paused:
        status = "[yellow]⏸ PAUSED[/yellow]"
    else:
        status = "[green]▶ PLAYING[/green]"

    bar = _progress_bar(elapsed, total)
    time_line = f"{_fmt_time(elapsed)}  {bar}  {_fmt_time(total)}"
    controls = "[dim]space[/dim] pause/resume   [dim]n[/dim] next   [dim]q[/dim] quit"

    body = (
        f"{status}\n\n"
        f"[bold]{current.title}[/bold]\n"
        f"[dim]{current.channel}[/dim]\n\n"
        f"{time_line}\n\n"
        f"{controls}"
    )
    return Panel(body, title="[bold cyan]yt-music[/bold cyan]", border_style="cyan")


def run_player_ui(player: Player) -> None:
    current_video: Video | None = player.current
    stop_event = threading.Event()

    def on_track_change(video: Video) -> None:
        nonlocal current_video
        current_video = video

    player.on_track_change = on_track_change

    play_thread = threading.Thread(target=player.play, daemon=True)
    play_thread.start()

    fd = sys.stdin.fileno()
    old_term = termios.tcgetattr(fd)

    def keyboard_loop() -> None:
        # Cbreak mode: disables ICANON (line buffering) and ECHO so we get
        # character-at-a-time input, but keeps OPOST enabled so \n → \r\n
        # output post-processing still works. setraw() would kill OPOST and
        # break Rich's panel rendering. Set once for the session, not per keypress.
        tty.setcbreak(fd)
        try:
            while not stop_event.is_set():
                # select() with 0.1 s timeout so we don't block the stop check
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r:
                    continue
                ch = sys.stdin.read(1)
                if ch == " ":
                    player.toggle_pause()
                elif ch == "n":
                    player.next()
                elif ch in ("q", "\x03"):  # q or Ctrl+C
                    player.stop()
                    stop_event.set()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_term)

    kb_thread = threading.Thread(target=keyboard_loop, daemon=True)
    kb_thread.start()

    # screen=True uses the alternate screen buffer (like vim/htop).
    # It clears and redraws the whole screen each refresh instead of doing
    # cursor-up arithmetic, which breaks when terminal mode changes underneath it.
    with Live(
        _make_panel(player, current_video),
        console=console,
        refresh_per_second=2,
        screen=True,
    ) as live:
        while not stop_event.is_set() and play_thread.is_alive():
            live.update(_make_panel(player, current_video))
            time.sleep(0.5)

    stop_event.set()
    play_thread.join(timeout=3)
