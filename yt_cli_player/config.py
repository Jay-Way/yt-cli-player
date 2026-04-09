import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "yt-cli-player"
CACHE_DIR = Path.home() / ".cache" / "yt-cli-player"
CLIENT_SECRET_PATH = Path(
    os.getenv("YOUTUBE_CLIENT_SECRET_PATH", str(CONFIG_DIR / "client_secret.json"))
)
IPC_SOCKET_PATH = "/tmp/yt-cli-player.sock"
KEYRING_SERVICE = "yt-cli-player"
KEYRING_USERNAME = "oauth_token"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

SHOW_THUMBNAIL = os.getenv("SHOW_THUMBNAIL", "false").lower() not in ("false", "0", "")
SHOW_VISUALIZER = os.getenv("SHOW_VISUALIZER", "true").lower() not in ("false", "0", "")
THUMBS_CACHE_DIR = CACHE_DIR / "thumbs"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
