#!/usr/bin/env bash
# Video Art Studio — one-step installer (macOS).
#
#   bash install.sh                 # from a clone of this repo
#   bash install.sh usathyan/video-art-studio   # straight from GitHub
#
# 1. installs the command-line tools the plugin uses (Homebrew)
# 2. registers this repo as a Claude Code plugin marketplace
# 3. installs the video-art plugin for your user account
set -euo pipefail

SOURCE="${1:-$(cd "$(dirname "$0")" && pwd)}"
say() { printf "\n\033[1m%s\033[0m\n" "$*"; }

say "1/3  Checking Homebrew"
if ! command -v brew >/dev/null; then
  echo "Homebrew is needed. Install it from https://brew.sh (one line), then run this again."
  exit 1
fi

say "2/3  Installing tools: uv, ffmpeg, ffmpeg-full, whisper-cpp, yt-dlp, node"
brew install uv ffmpeg ffmpeg-full whisper-cpp yt-dlp node

say "3/3  Installing the Claude Code plugin"
if ! command -v claude >/dev/null; then
  echo "Claude Code isn't installed. See https://claude.com/claude-code, then run this again."
  exit 1
fi
claude plugin marketplace add "$SOURCE"
claude plugin install video-art@video-art

# one private file for API keys, read by the terminal, the desktop app and IDEs alike
mkdir -p "$HOME/.config/video-art" && chmod 700 "$HOME/.config/video-art"
KEYS="$HOME/.config/video-art/.env"
[ -f "$KEYS" ] || printf 'OPENROUTER_API_KEY=\nGEMINI_API_KEY=\nELEVENLABS_API_KEY=\n' > "$KEYS"
chmod 600 "$KEYS"

cat <<'EOF'

  Done. Next:
    1. Open a folder for your art:   mkdir -p ~/VideoArt && cd ~/VideoArt && claude
    2. Add your API keys:            open -t ~/.config/video-art/.env
       (or let /video-art:setup do it — it can import keys already in your ~/.zshrc)
    3. In Claude Code type:          /video-art:setup
       (checks everything, adds the motion-graphics engine, makes a 5-second test video)
    4. Then just ask, e.g.:          make a 30-second living-photo loop from ~/Pictures/iceland

EOF
