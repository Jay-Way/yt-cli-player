#!/usr/bin/env bash
set -e

echo "=== yt-cli-player setup ==="

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y mpv python3.12-venv

# Create and activate virtualenv
if [ ! -d ".venv" ]; then
    echo "Creating virtualenv..."
    python3 -m venv .venv
fi
echo "Activating virtualenv..."
source .venv/bin/activate

# Install Python package
echo "Installing Python dependencies..."
pip install -e . -q

# Create config dir
mkdir -p "$HOME/.config/yt-cli-player"
mkdir -p "$HOME/.cache/yt-cli-player"

echo ""
echo "=== Google Cloud Console setup (one-time) ==="
echo ""
echo "1. Go to https://console.cloud.google.com and create a new project"
echo "2. Enable the YouTube Data API v3"
echo "   APIs & Services > Enable APIs > search 'YouTube Data API v3'"
echo "3. Create OAuth 2.0 credentials"
echo "   APIs & Services > Credentials > Create Credentials > OAuth client ID"
echo "   Application type: Desktop app"
echo "4. Download the JSON and save it to:"
echo "   $HOME/.config/yt-cli-player/client_secret.json"
echo "5. Add your Google account as a test user:"
echo "   APIs & Services > OAuth consent screen > Test users > Add users"
echo ""
echo "Then run: source .venv/bin/activate && yt-music login"
