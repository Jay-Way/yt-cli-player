import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable
from yt_cli_player.api.models import Video
from yt_cli_player.config import IPC_SOCKET_PATH, CACHE_DIR
from yt_cli_player.player.ipc import MpvIPC, wait_for_socket

_MPV_LOG = CACHE_DIR / "mpv.log"
# Use the yt-dlp that lives next to our Python interpreter (i.e., the venv copy).
_YTDLP_PATH = Path(sys.executable).parent / "yt-dlp"


class Player:
    def __init__(
        self,
        videos: list[Video],
        start_index: int = 0,
        on_track_change: Callable[[Video], None] | None = None,
    ):
        self.videos = videos
        self._index = start_index
        self._proc: subprocess.Popen | None = None
        self._ipc: MpvIPC | None = None
        self._stopped = False
        self.on_track_change = on_track_change
        self.last_error: str = ""  # last mpv stderr snippet, for display

    @property
    def current(self) -> Video | None:
        if 0 <= self._index < len(self.videos):
            return self.videos[self._index]
        return None

    def _launch(self, video: Video) -> None:
        if os.path.exists(IPC_SOCKET_PATH):
            os.unlink(IPC_SOCKET_PATH)
        ytdlp_opt = (
            f"--script-opts=ytdl_hook-ytdl_path={_YTDLP_PATH}"
            if _YTDLP_PATH.exists()
            else ""
        )
        # --log-file writes directly to a file regardless of --no-terminal,
        # unlike stdout/stderr redirection which --no-terminal suppresses.
        cmd = [
            "mpv",
            "--no-video",
            "--no-terminal",
            "--msg-level=all=warn",
            f"--log-file={_MPV_LOG}",
            "--ytdl-format=bestaudio/best",
            f"--input-ipc-server={IPC_SOCKET_PATH}",
        ]
        if ytdlp_opt:
            cmd.append(ytdlp_opt)
        cmd.append(video.url)
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if wait_for_socket(timeout=5.0):
            time.sleep(0.15)  # let socket start accepting connections
            try:
                self._ipc = MpvIPC()
            except OSError:
                self._ipc = None

    def play(self) -> None:
        """Block until the full queue finishes or stop() is called."""
        while not self._stopped and self.current:
            video = self.current
            if self.on_track_change:
                self.on_track_change(video)
            started_at = time.monotonic()
            self._launch(video)
            self._proc.wait()
            elapsed = time.monotonic() - started_at
            self._close_ipc()
            if self._stopped:
                break
            # If mpv exited in under 3 s it almost certainly failed (yt-dlp error,
            # network issue, etc.). Record the error and wait briefly so we don't
            # spin through the entire queue in a second.
            if elapsed < 3.0:
                try:
                    lines = [l for l in _MPV_LOG.read_text(errors="replace").splitlines() if l.strip()]
                    self.last_error = lines[-1] if lines else f"mpv exited immediately (exit code {self._proc.returncode})"
                except Exception:
                    self.last_error = f"mpv exited immediately (exit code {self._proc.returncode})"
                time.sleep(2.0)
            self._index += 1

    def toggle_pause(self) -> None:
        if self._ipc:
            self._ipc.toggle_pause()

    def next(self) -> None:
        self._index += 1
        self._kill_current()

    def stop(self) -> None:
        self._stopped = True
        self._kill_current()

    def _close_ipc(self) -> None:
        if self._ipc:
            self._ipc.close()
            self._ipc = None

    def _kill_current(self) -> None:
        if self._ipc:
            try:
                self._ipc.quit()
            except OSError:
                pass
            self._close_ipc()
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def get_position(self) -> float | None:
        if self._ipc:
            return self._ipc.get_property("time-pos")
        return None

    def is_paused(self) -> bool:
        if self._ipc:
            val = self._ipc.get_property("pause")
            return bool(val)
        return False
