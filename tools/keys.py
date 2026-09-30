"""Manage API keys in ~/.config/video-art/.env — the one place every va-* tool reads them from.

    va-keys            create the file if needed (private, 600), show which keys are set (masked)
    va-keys edit       ...and open it in your editor (TextEdit on macOS if $EDITOR isn't set)
    va-keys import     copy keys that are already exported in your shell profile into the file

Values are never printed; only the first and last few characters are shown.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

from common import _KEY_ALIASES, KEYS_FILE

TEMPLATE = """# Video Art Studio — API keys (private: only your user can read this file)
# One key per line, no quotes. Leave optional ones empty.

# Images, AI video and music (Gemini/GPT Image, Veo, Seedance, Kling, Lyria) — openrouter.ai/keys
OPENROUTER_API_KEY=

# Narration (Gemini TTS) — aistudio.google.com/apikey
GEMINI_API_KEY=

# Optional: ElevenLabs music (paid plan; the secret key starts with sk_) — elevenlabs.io
ELEVENLABS_API_KEY=
"""
PURPOSE = {
    "openrouter": "images · video · music",
    "gemini": "narration",
    "eleven": "ElevenLabs music (optional)",
}


def ensure() -> Path:
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not KEYS_FILE.exists():
        KEYS_FILE.write_text(TEMPLATE)
    os.chmod(KEYS_FILE.parent, 0o700)
    os.chmod(KEYS_FILE, 0o600)
    return KEYS_FILE


def mask(v: str) -> str:
    return f"{v[:6]}…{v[-4:]}" if len(v) > 14 else "set"


def status() -> None:
    vals = dotenv_values(KEYS_FILE)
    print(f"{KEYS_FILE}  (permissions {oct(KEYS_FILE.stat().st_mode)[-3:]})")
    for svc, names in _KEY_ALIASES.items():
        found = next(
            ((n, vals[n]) for n in names if vals.get(n) and not vals[n].startswith("#")), None
        )
        where = "file"
        if not found:
            found = next(((n, os.environ[n]) for n in names if os.environ.get(n)), None)
            where = "shell only — the desktop app won't see it; run `va-keys import`"
        line = f"{mask(found[1] or '')} ({found[0]}, {where})" if found else "missing"
        print(f"  {PURPOSE[svc]:28s} {line}")


def set_key(name: str, value: str) -> None:
    lines = KEYS_FILE.read_text().splitlines()
    for i, ln in enumerate(lines):
        if ln.split("=", 1)[0].strip() == name:
            lines[i] = f"{name}={value}"
            break
    else:
        lines.append(f"{name}={value}")
    KEYS_FILE.write_text("\n".join(lines) + "\n")


def shell_value(name: str) -> str:
    """Read an exported variable the way a login shell would see it (zsh/bash profile)."""
    if os.environ.get(name):
        return os.environ[name]
    shell = os.environ.get("SHELL", "/bin/zsh")
    rc = "~/.zshrc" if "zsh" in shell else "~/.bashrc"
    out = subprocess.run(
        [shell, "-c", f'source {rc} >/dev/null 2>&1; printf %s "${{{name}}}"'],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout.strip()


def import_from_shell() -> None:
    have = dotenv_values(KEYS_FILE)
    for svc, names in _KEY_ALIASES.items():
        if any(have.get(n) for n in names):
            print(f"  {PURPOSE[svc]:28s} already in file — kept")
            continue
        for n in names:
            if v := shell_value(n):
                set_key(names[0], v)
                print(f"  {PURPOSE[svc]:28s} imported from ${n}")
                break
        else:
            print(f"  {PURPOSE[svc]:28s} not found in your shell")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("action", nargs="?", choices=["show", "edit", "import"], default="show")
    a = ap.parse_args()
    ensure()
    if a.action == "import":
        import_from_shell()
        os.chmod(KEYS_FILE, 0o600)
    if a.action == "edit":
        editor = os.environ.get("EDITOR")
        cmd = (
            [editor, str(KEYS_FILE)]
            if editor
            else (
                ["open", "-t", str(KEYS_FILE)]
                if sys.platform == "darwin" and shutil.which("open")
                else ["nano", str(KEYS_FILE)]
            )
        )
        subprocess.run(cmd, check=False)
    status()


if __name__ == "__main__":
    main()
