from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from yt_cli_player.config import CLIENT_SECRET_PATH, YOUTUBE_SCOPES
from yt_cli_player.auth.token_store import save_token, load_token


def get_credentials():
    """Return valid credentials if available, else None."""
    return load_token()


def login() -> str:
    """Run the OAuth browser flow. Returns the authenticated channel name."""
    if not CLIENT_SECRET_PATH.exists():
        raise FileNotFoundError(
            f"client_secret.json not found at {CLIENT_SECRET_PATH}\n"
            "Download it from Google Cloud Console > APIs & Services > Credentials\n"
            "Then place it at the path above, or set YOUTUBE_CLIENT_SECRET_PATH in .env"
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), YOUTUBE_SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)
    save_token(creds)
    service = build("youtube", "v3", credentials=creds)
    resp = service.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items", [])
    return items[0]["snippet"]["title"] if items else "unknown"
