import json
import keyring
import keyring.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from yt_cli_player.config import KEYRING_SERVICE, KEYRING_USERNAME


def save_token(creds: Credentials) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, creds.to_json())


def load_token() -> Credentials | None:
    data = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    if not data:
        return None
    creds = Credentials.from_authorized_user_info(json.loads(data))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(creds)
    return creds if creds.valid else None


def delete_token() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass
