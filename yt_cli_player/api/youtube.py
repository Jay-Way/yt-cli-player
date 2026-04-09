import re
from typing import Iterator
from googleapiclient.discovery import build
from yt_cli_player.auth.token_store import load_token
from yt_cli_player.api.models import Playlist, Video

_LIKED_PLAYLIST = Playlist(id="LL", title="Liked Videos", item_count=0)


def _build_service():
    creds = load_token()
    if not creds:
        raise RuntimeError("Not logged in. Run `yt-music login` first.")
    return build("youtube", "v3", credentials=creds)


def get_playlists() -> list[Playlist]:
    service = _build_service()
    playlists = [_LIKED_PLAYLIST]
    request = service.playlists().list(part="snippet,contentDetails", mine=True, maxResults=50)
    while request:
        resp = request.execute()
        for item in resp.get("items", []):
            playlists.append(Playlist(
                id=item["id"],
                title=item["snippet"]["title"],
                item_count=item["contentDetails"]["itemCount"],
                description=item["snippet"].get("description", ""),
            ))
        request = service.playlists().list_next(request, resp)
    return playlists


def _iso_to_seconds(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mins, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mins * 60 + s


def _fetch_durations(service, video_ids: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = service.videos().list(part="contentDetails", id=",".join(batch)).execute()
        for item in resp.get("items", []):
            result[item["id"]] = _iso_to_seconds(item["contentDetails"]["duration"])
    return result


def get_playlist_items(
    playlist_id: str, page_token: str | None = None
) -> tuple[list[Video], str | None]:
    """Returns (videos_on_page, next_page_token). next_page_token is None on last page."""
    service = _build_service()
    kwargs: dict = dict(part="snippet,contentDetails", playlistId=playlist_id, maxResults=50)
    if page_token:
        kwargs["pageToken"] = page_token

    resp = service.playlistItems().list(**kwargs).execute()
    next_token: str | None = resp.get("nextPageToken")

    videos: list[Video] = []
    video_ids: list[str] = []
    for item in resp.get("items", []):
        snippet = item["snippet"]
        if not snippet.get("thumbnails"):  # deleted / private
            continue
        vid_id = snippet["resourceId"]["videoId"]
        thumbnails = snippet.get("thumbnails", {})
        thumb_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or ""
        )
        video_ids.append(vid_id)
        videos.append(Video(
            video_id=vid_id,
            title=snippet["title"],
            channel=snippet.get("videoOwnerChannelTitle", ""),
            position=snippet["position"],
            thumbnail_url=thumb_url,
        ))

    if video_ids:
        durations = _fetch_durations(service, video_ids)
        for v in videos:
            v.duration_seconds = durations.get(v.video_id, 0)

    return videos, next_token


def get_all_playlist_items(playlist_id: str) -> Iterator[Video]:
    """Yields every video in a playlist, fetching pages lazily."""
    page_token: str | None = None
    while True:
        videos, page_token = get_playlist_items(playlist_id, page_token)
        yield from videos
        if not page_token:
            break
