import shutil
import subprocess
import threading
from rich.text import Text
from yt_cli_player.config import CACHE_DIR

_CAVA_CONF = CACHE_DIR / "cava.conf"
_BAR_CHARS = " ▁▂▃▄▅▆▇█"
_MAX_VAL = 8

_CONF_TEMPLATE = """\
[general]
bars = {bars}
framerate = 25

[input]
method = pulse
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = {max_val}
bar_delimiter = 59
"""


class CavaVisualizer:
    def __init__(self, bars: int = 24):
        self.bars = bars
        self._proc: subprocess.Popen | None = None
        self._values: list[int] = [0] * bars
        self._lock = threading.Lock()

    @staticmethod
    def available() -> bool:
        return shutil.which("cava") is not None

    def start(self) -> None:
        if not self.available():
            return
        _CAVA_CONF.write_text(_CONF_TEMPLATE.format(bars=self.bars, max_val=_MAX_VAL))
        self._proc = subprocess.Popen(
            ["cava", "-p", str(_CAVA_CONF)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        threading.Thread(target=self._read_loop, daemon=True).start()

    def is_active(self) -> bool:
        return self._proc is not None

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None

    def render(self, color: str = "cyan") -> Text:
        """Return a Rich Text of bar characters styled with the given color."""
        with self._lock:
            vals = self._values.copy()
        bar_str = "".join(_BAR_CHARS[min(v, _MAX_VAL)] for v in vals)
        t = Text(bar_str)
        t.stylize(color)
        return t

    def _read_loop(self) -> None:
        if not self._proc or not self._proc.stdout:
            return
        for line in self._proc.stdout:
            parts = line.strip().rstrip(";").split(";")
            if len(parts) == self.bars:
                try:
                    values = [int(x) for x in parts]
                    with self._lock:
                        self._values = values
                except ValueError:
                    pass
