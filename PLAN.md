# yt-cli-player — Implementation Plan & Progress

A terminal-based YouTube music player for Ubuntu. No video — audio only.

---

## Tech Stack

| Component | Choice |
|---|---|
| CLI framework | Click 8.x (already installed) |
| UI / output | Rich 13.x (already installed) |
| YouTube metadata | google-api-python-client + google-auth-oauthlib |
| Audio playback | mpv (subprocess) + JSON IPC socket |
| Stream extraction | mpv's built-in yt-dlp hook (`/usr/bin/yt-dlp` already installed) |
| Token storage | keyring (SecretService/libsecret) |
| Config | python-dotenv |

---

## Project Structure

```
yt-cli-player/
├── pyproject.toml
├── setup.sh
├── PLAN.md                         ← this file
├── .env.example
└── yt_cli_player/
    ├── cli.py                      # Click group: login, logout, browse, play, status
    ├── config.py
    ├── auth/
    │   ├── oauth.py                # InstalledAppFlow, token refresh
    │   └── token_store.py          # keyring save/load
    ├── api/
    │   ├── youtube.py              # playlists.list, playlistItems.list, videos.list
    │   └── models.py               # Video, Playlist dataclasses
    ├── player/
    │   ├── mpv_player.py           # subprocess launch, queue management
    │   └── ipc.py                  # Unix socket JSON IPC
    └── ui/
        ├── browser.py              # Rich tables for selection
        └── now_playing.py          # Rich Live display + keyboard input
```

---

## Phases

### Phase 0 — Project Bootstrap ✅
- [x] Create `pyproject.toml` with dependencies and `yt-music` entry point
- [x] Create package skeleton (`__init__.py` files, directory structure)
- [x] Create `setup.sh` (`sudo apt install mpv python3.12-venv && python3 -m venv .venv && pip install -e .`)
- [x] Create `.env.example` with `YOUTUBE_CLIENT_SECRET_PATH`
- [x] Document Google Cloud Console setup steps (in `setup.sh` output)

**Google Cloud setup (manual step):**
1. Go to console.cloud.google.com → new project
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials → Desktop App
4. Download `client_secret.json` → place at `~/.config/yt-cli-player/client_secret.json`
5. Add your Google account as a test user (OAuth consent screen → Test users)

---

### Phase 1 — OAuth 2.0 Authentication ✅
- [x] `auth/oauth.py` — `InstalledAppFlow` with `run_local_server(port=0)`
- [x] Scope: `https://www.googleapis.com/auth/youtube.readonly`
- [x] `auth/token_store.py` — `save_token()` / `load_token()` via `keyring`
- [x] Auto-refresh expired tokens on load
- [x] `yt-music login` command — runs flow, prints authenticated channel name
- [x] `yt-music logout` command — clears stored token

**Gotchas:**
- Liked Videos playlist (`LL`) returns 404 without OAuth — never use API key alone
- App must stay in "Testing" mode; add your Google account as a test user

---

### Phase 2 — YouTube Data API Integration ✅
- [x] `api/models.py` — `Video` and `Playlist` dataclasses
- [x] `api/youtube.py` — build client from stored credentials
- [x] `get_playlists()` — fetches user playlists; hardcode "Liked Videos" (`LL`) at top
- [x] `get_playlist_items(playlist_id, page_token)` — with pagination support
- [x] Batch-fetch durations via `videos.list(id=comma_separated)` (50 per call)
- [x] Filter deleted/private videos (no thumbnails → skip)

**Gotchas:**
- `playlistItems.list` does NOT return duration — must batch-fetch via `videos.list`
- API quota: 10,000 units/day (1 unit per list call, 50 items per call — fine for personal use)

---

### Phase 3 — Playlist Browser TUI ✅
- [x] `ui/browser.py` — `show_playlists()` with numbered Rich table
- [x] `show_playlist_items()` — title (60 char truncated), channel, duration columns
- [x] Pagination: `n` next page / `p` previous page
- [x] `yt-music browse` command wires it all together

---

### Phase 4 — mpv Playback Engine ✅
- [x] `player/ipc.py` — Unix socket client, `send_command()`, `get_property()`
- [x] `player/mpv_player.py` — launch mpv subprocess:
  ```
  mpv --no-video --no-terminal --really-quiet \
      --input-ipc-server=/tmp/yt-cli-player.sock \
      "https://www.youtube.com/watch?v=VIDEO_ID"
  ```
- [x] Poll for IPC socket readiness before connecting (10 × 100ms)
- [x] Queue management — auto-advance on mpv exit code 0
- [x] `ui/now_playing.py` — Rich `Live` display (title, elapsed, progress bar)
- [x] Keyboard input thread: `space` pause, `n` next, `q` quit

**Gotchas:**
- Use `--no-terminal --really-quiet` or mpv hijacks the terminal and clobbers Rich output
- IPC socket is created asynchronously — poll before connecting
- Age-restricted/region-locked videos: catch non-zero mpv exit and skip

---

### Phase 5 — Polish
- [x] `yt-music play` plays Liked Videos by default; `--shuffle` flag randomises order (the separate `--liked` flag was not needed)
- [x] `yt-music play --shuffle` flag
- [x] Startup check: `shutil.which('mpv')` with helpful install error (`_require_mpv()` in `cli.py`)
- [x] `yt-music status` — query IPC socket for current track info (reads `media-title`, `time-pos`, `duration`, `pause` from `/tmp/yt-cli-player.sock`)
- [ ] Handle `RefreshError` → prompt re-login (`token_store.py` calls `creds.refresh()` but does not catch `google.auth.exceptions.RefreshError`)
- [ ] JSON metadata cache in `~/.cache/yt-cli-player/` with 1-hour TTL

---

### Phase 6 — Thumbnail Display + Eye Candy ✅

Show the current track's YouTube thumbnail inside the terminal while a track is playing.

**Config option:** Add `SHOW_THUMBNAIL` (bool, default `true`) to `config.py`, readable from the `.env` file via `python-dotenv`. When `false`, the now-playing panel renders exactly as today.

**Rendering approach:** Use the [chafa](https://hpjansson.org/chafa/) CLI tool to convert the thumbnail JPEG to Unicode/ANSI block art and embed the output as a `rich.Text` inside the now-playing panel. Chafa supports sixel, kitty, and block-character output and auto-detects the terminal's capabilities.

**Implementation steps:**

1. **`config.py`** — add `SHOW_THUMBNAIL = os.getenv("SHOW_THUMBNAIL", "true").lower() != "false"`.

2. **`api/models.py`** — add a `thumbnail_url` field to `Video` (populated from `snippet.thumbnails.medium.url` or `high.url` in `youtube.py`).

3. **`ui/thumbnail.py`** (new module):
   - `fetch_thumbnail(url: str) -> Path | None` — download JPEG to a temp file in `CACHE_DIR/thumbs/<video_id>.jpg`, return cached path if already present.
   - `render_thumbnail(path: Path, width: int = 24) -> str | None` — shell out to `chafa --size=<width>x12 --format=symbols <path>` and return the ANSI string, or `None` if chafa is not installed (`shutil.which("chafa")`).

4. **`ui/now_playing.py`** — when `SHOW_THUMBNAIL` is true, fetch and render the thumbnail in a background thread (so a slow download doesn't stall the UI refresh), cache the rendered ANSI string per video ID, and prepend it to the panel body.

5. **`setup.sh`** — add `sudo apt install -y chafa` to the system-dependencies line (alongside mpv). Add a note that chafa is optional; the player works without it.

**Implemented:**
- `ui/thumbnail.py` — `fetch_thumbnail`, `render_thumbnail`, `get_dominant_color` (Pillow, stdlib colorsys)
- `ui/visualizer.py` — `CavaVisualizer`: writes a cava config to `CACHE_DIR/cava.conf`, launches cava as a subprocess in raw ASCII mode, reads bar values in a background thread; `render()` returns a Rich `Text` of `▁▂▃▄▅▆▇█` chars styled with the dominant color
- `ui/now_playing.py` — thumbnail and color fetched in a background thread per track; panel border uses the dominant color; CAVA bars rendered above the controls; refresh rate bumped to 4 Hz for smooth animation
- `config.py` — `SHOW_THUMBNAIL` (default off), `SHOW_VISUALIZER` (default on)
- `pyproject.toml` — added `Pillow>=10.0`
- Sixel/kitty protocols can interfere with Rich's alternate screen buffer — default to `--format=symbols` (Unicode block art) which is universally safe; advanced protocol selection can be a follow-up.

---

## CLI Commands (target)

```
yt-music login          # OAuth flow, opens browser
yt-music logout         # clear stored token
yt-music browse         # interactive playlist → track browser
yt-music play --liked   # immediately queue shuffled Liked Videos
yt-music status         # show currently playing track
```

---

## Progress Log

| Date | Milestone |
|---|---|
| 2026-04-08 | Project created, all 5 phases implemented |
| — | Pending: first real test with Google credentials |
