# yt-music

<img width="967" height="411" alt="Bildschirmfoto vom 2026-04-08 12-41-23" src="https://github.com/user-attachments/assets/9e2cb609-fe46-4024-b714-adabd03d17c3" />


A terminal-based YouTube music player for Ubuntu. Browse your playlists and play audio directly from the command line — no browser, no video, no ads.

## Features

- Log in to your YouTube account via OAuth (opens a browser tab once, then stores the token)
- Browse all your playlists in an interactive numbered menu
- Play your **Liked Videos** playlist with a single command
- Shuffle any playlist
- Audio-only playback via mpv — no video downloaded or rendered
- Live now-playing display with progress bar
- Panel border color adapts to the dominant color of the current track's thumbnail
- Real-time equalizer visualizer powered by [cava](https://github.com/karlstav/cava) (optional)
- Album art display in the terminal via [chafa](https://hpjansson.org/chafa/) (optional, off by default)
- Keyboard controls: pause, skip, quit
- Skips deleted or private videos automatically
- Pagination for large playlists

## Cost

**Free.** The YouTube Data API v3 has a quota of 10,000 units per day at no charge — no credit card or billing required, just a free Google account. The operations this tool uses (fetching playlists, playlist items, and video durations) each cost 1 unit. A typical session uses around 30–40 units, so you would need to open the app roughly 300 times in a single day to get anywhere near the limit.

## Requirements

- Ubuntu (tested on 24.04)
- Python 3.10+
- A Google account with YouTube

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourname/yt-cli-player.git
cd yt-cli-player
```

### 2. Run setup

```bash
bash setup.sh
```

You may need to install python first, or if it's already installed, check which version and update `setup.sh` it if necessary.
For example, if you have python 3.13 installed, change `python3.12-venv` to `python3.13-venv` in `setup.sh`.
This installs `mpv` and `python3.12-venv` via apt, creates a Python virtualenv, and installs the package and all dependencies.

### 3. Set up Google Cloud credentials

This is a one-time step to get a YouTube API key tied to your account.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project
2. Navigate to **APIs & Services → Enable APIs & Services**, search for **YouTube Data API v3**, and enable it
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Download the generated JSON file
4. Save the file to:
   ```
   ~/.config/yt-cli-player/client_secret.json
   ```
5. Go to **APIs & Services → OAuth consent screen → Audience → Test users** and add your Google account

### 4. Activate the virtualenv and log in

```bash
source .venv/bin/activate
yt-music login
```

A browser tab will open. Log in with your Google account and approve access. You only need to do this once — the token is stored securely in your system keychain and refreshed automatically.

## Making yt-music globally available

After installation you can run `yt-music` from anywhere without activating the virtualenv first.

### Option A — symlink (recommended)

Create a symlink from the venv binary into `~/.local/bin`, which is already on your PATH on Ubuntu:

```bash
mkdir -p ~/.local/bin
ln -s "$PWD/.venv/bin/yt-music" ~/.local/bin/yt-music
```

Run this once from inside the project directory. The command will then be available in every new terminal session immediately.

To verify:
```bash
which yt-music   # should print ~/.local/bin/yt-music
yt-music --help
```

### Option B — shell alias

Add an alias to your `~/.zshrc`:

```bash
echo "alias yt-music='$HOME/yt-cli-player/.venv/bin/yt-music'" >> ~/.zshrc
source ~/.zshrc
```

Adjust the path if you cloned the repo somewhere other than `~/yt-cli-player`.

---

## Usage

### Log in / out

```bash
yt-music login     # OAuth flow, opens browser tab
yt-music logout    # Clear stored token
```

### Browse playlists interactively

<img width="1248" height="610" alt="Bildschirmfoto vom 2026-04-08 13-00-32" src="https://github.com/user-attachments/assets/33cf66ff-ad40-47b9-a1f4-1468c4689222" />


```bash
yt-music browse
```

Shows a numbered list of your playlists (Liked Videos is always first). Select a playlist, then select a track to start playback from that position. The rest of the playlist continues in order.

Navigation:
- Type a **number** and press Enter to select
- **n** — next page
- **p** — previous page
- **b** — go back to playlist list
- **q** — quit

### Play Liked Videos

```bash
yt-music play           # Play Liked Videos in order
yt-music play --shuffle # Play Liked Videos in random order
```

### Playback controls

While a track is playing:

| Key | Action |
|-----|--------|
| `space` | Pause / resume |
| `n` | Skip to next track |
| `q` or `Ctrl+C` | Stop and quit |

## Optional features

### Equalizer visualizer

Requires [cava](https://github.com/karlstav/cava):

```bash
sudo apt install cava
```

Once installed, a row of `▁▂▃▄▅▆▇█` bars appears in the now-playing panel, animated in real time and colored to match the current track. To disable:

```
SHOW_VISUALIZER=false
```

### Album art

Requires [chafa](https://hpjansson.org/chafa/):

```bash
sudo apt install chafa
```

Displays the track thumbnail as Unicode block art above the track info. Off by default. To enable:

```
SHOW_THUMBNAIL=true
```

### Configuration

Create a `.env` file in the project root (see `.env.example`) to set options permanently:

```env
SHOW_VISUALIZER=true
SHOW_THUMBNAIL=false
```

## Troubleshooting

**No sound / tracks skipping immediately**

Check the mpv log for errors:
```bash
cat ~/.cache/yt-cli-player/mpv.log
```

The most common cause is an outdated yt-dlp. Update it:
```bash
source .venv/bin/activate
pip install -U yt-dlp
```

**`client_secret.json` not found**

Make sure the file is at `~/.config/yt-cli-player/client_secret.json`. You can also set a custom path:
```bash
export YOUTUBE_CLIENT_SECRET_PATH=/path/to/client_secret.json
yt-music login
```

Or add it to a `.env` file in the project root (see `.env.example`).

**"Not logged in" error**

Run `yt-music login` to authenticate.

**mpv not found**

```bash
sudo apt install mpv
```
