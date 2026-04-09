import colorsys
import shutil
import subprocess
import urllib.request
from pathlib import Path
from yt_cli_player.config import THUMBS_CACHE_DIR

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def fetch_thumbnail(url: str, video_id: str) -> Path | None:
    """Download thumbnail JPEG to the cache dir and return its path.
    Returns the cached path immediately if the file already exists."""
    if not url:
        return None
    path = THUMBS_CACHE_DIR / f"{video_id}.jpg"
    if path.exists():
        return path
    try:
        urllib.request.urlretrieve(url, path)
        return path
    except (urllib.error.URLError, OSError):
        return None


def get_dominant_color(path: Path) -> str:
    """Return a vivid hex color derived from the thumbnail's average hue.
    Falls back to 'cyan' if Pillow is unavailable or the image can't be read."""
    if not _PIL_AVAILABLE:
        return "cyan"
    try:
        img = Image.open(path).convert("RGB")
        img = img.resize((50, 50), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        n = len(pixels)
        r = sum(p[0] for p in pixels) / n / 255
        g = sum(p[1] for p in pixels) / n / 255
        b = sum(p[2] for p in pixels) / n / 255
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        # Boost saturation and clamp brightness so muted thumbnails still
        # produce a vivid, readable border color on a dark terminal background.
        s = min(1.0, s * 2.5)
        v = max(0.65, min(1.0, v * 1.2))
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    except (OSError, ValueError, ZeroDivisionError):
        return "cyan"


def render_thumbnail(path: Path, width: int = 40, height: int = 11) -> str | None:
    """Render a thumbnail as Unicode block art via chafa.
    Returns the ANSI string, or None if chafa is not installed or rendering fails."""
    if not shutil.which("chafa"):
        return None
    try:
        result = subprocess.run(
            ["chafa", f"--size={width}x{height}", "--format=symbols", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout or None
    except (OSError, subprocess.TimeoutExpired):
        return None
