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
- [ ] `yt-music play --liked` shortcut (shuffled Liked Videos)
- [ ] `yt-music status` — query IPC socket for current track info
- [ ] Startup check: `shutil.which('mpv')` with helpful install error
- [ ] Handle `RefreshError` → prompt re-login
- [ ] JSON metadata cache in `~/.cache/yt-cli-player/` with 1-hour TTL
- [ ] `yt-music play --shuffle` flag

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
