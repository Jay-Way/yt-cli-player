# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and running

```bash
bash setup.sh                     # Install mpv, create venv, install package
source .venv/bin/activate
pip install -e .                  # Reinstall after editing pyproject.toml
yt-music --help
```

The CLI entry point is `yt-music`, mapped to `yt_cli_player.cli:main` in `pyproject.toml`.

## Architecture

The app is a terminal YouTube music player that authenticates via OAuth, fetches playlists from the YouTube Data API v3, and plays audio using mpv with yt-dlp as the format resolver.

**Data flow:**
1. `cli.py` — Click command group; imports lazily to keep startup fast
2. `auth/` — `oauth.py` runs the browser OAuth flow; `token_store.py` persists credentials in the system keychain via `keyring`, with automatic refresh on load
3. `api/youtube.py` — Builds a Google API service from stored credentials; fetches playlists and video items (with duration enrichment via a second `videos.list` call per page)
4. `player/mpv_player.py` — `Player` launches mpv as a subprocess with `--no-video` and an IPC socket; iterates through the video queue, treating any exit under 3 s as a failure and pausing before skipping
5. `player/ipc.py` — `MpvIPC` communicates with mpv over a Unix domain socket at `/tmp/yt-cli-player.sock` using the mpv JSON IPC protocol; handles async event interleaving when matching responses by `request_id`
6. `ui/now_playing.py` — Runs `Player.play()` in a daemon thread, keyboard input in another, and renders a `rich.Live` panel at 2 Hz on the alternate screen buffer; uses `tty.setcbreak` (not `setraw`) to preserve Rich's output post-processing
7. `ui/browser.py` — Interactive numbered list for playlist/track selection with pagination

**Key design decisions:**
- mpv is controlled exclusively via IPC; the yt-dlp binary inside the venv is injected via `--script-opts=ytdl_hook-ytdl_path=...` so the venv version is used rather than the system one
- OAuth token is stored in the OS keychain (not a file); `load_token` silently refreshes expired tokens
- The Liked Videos playlist (`id="LL"`) is a hardcoded sentinel always shown first; it's not returned by the playlists API
- Deleted/private videos are detected by absent `thumbnails` in the snippet and silently skipped

## Configuration

`config.py` is imported at module level and creates `~/.config/yt-cli-player/` and `~/.cache/yt-cli-player/` on first import. The only env var is `YOUTUBE_CLIENT_SECRET_PATH` (also loadable from a `.env` file in the project root).

mpv logs to `~/.cache/yt-cli-player/mpv.log` — check this first when tracks skip immediately.
