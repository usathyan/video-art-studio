"""Shared helpers: config, API keys, paths."""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
USER_DIR = Path.home() / ".config" / "video-art"

# Keys: real env vars win, then ./.env in the working folder, then ~/.config/video-art/.env
load_dotenv(Path.cwd() / ".env")
load_dotenv(USER_DIR / ".env")

# Models: plugin defaults, overridden per-project by ./.video-art/models.toml
CONFIG = tomllib.loads((ROOT / "config" / "models.toml").read_text())
_override = Path.cwd() / ".video-art" / "models.toml"
if _override.exists():
    for section, vals in tomllib.loads(_override.read_text()).items():
        CONFIG.setdefault(section, {}).update(vals)

_KEY_ALIASES = {
    "openrouter": ["OPENROUTER_API_KEY"],
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "eleven": ["ELEVEN_API", "ELEVENLABS_API_KEY"],
}


def key(service: str) -> str:
    for name in _KEY_ALIASES[service]:
        if val := os.environ.get(name):
            return val
    sys.exit(
        f"missing API key for {service}: set one of {_KEY_ALIASES[service]} (see .env.example)"
    )


def ffmpeg_with_libass() -> str:
    """Homebrew's default ffmpeg lacks libass; prefer keg-only ffmpeg-full when present."""
    for cand in (
        os.environ.get("FFMPEG_FULL"),
        "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
        "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
    ):
        if cand and Path(cand).exists():
            return cand
    return "ffmpeg"


def out_path(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def check(resp):
    """raise_for_status, but show the API's own error message (they're usually actionable)."""
    if resp.is_error:
        sys.exit(
            f"{resp.request.method} {resp.request.url.host} → {resp.status_code}: {resp.text[:600]}"
        )
    return resp
