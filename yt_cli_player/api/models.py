from dataclasses import dataclass


@dataclass
class Playlist:
    id: str
    title: str
    item_count: int
    description: str = ""


@dataclass
class Video:
    video_id: str
    title: str
    channel: str
    duration_seconds: int = 0
    position: int = 0
    thumbnail_url: str = ""

    @property
    def duration_str(self) -> str:
        m, s = divmod(self.duration_seconds, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"
