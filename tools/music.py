"""Background music via ElevenLabs.

    uv run tools/music.py "sparse felt piano, warm tape hiss, curious, 80bpm" --seconds 60 \
        -o projects/x/gen/music.mp3
"""

from __future__ import annotations

import argparse
from pathlib import Path

import httpx

from common import CONFIG, check, key, out_path


def compose(prompt: str, seconds: float, out: Path) -> Path:
    r = httpx.post(
        "https://api.elevenlabs.io/v1/music?output_format=mp3_48000_192",
        headers={"xi-api-key": key("eleven")},
        json={
            "prompt": prompt,
            "music_length_ms": int(seconds * 1000),
            "model_id": CONFIG["music"]["model"],
            "force_instrumental": True,
        },
        timeout=600,
    )
    check(r)
    out_path(out).write_bytes(r.content)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("-o", "--out", required=True, type=Path)
    a = ap.parse_args()
    print(compose(a.prompt, a.seconds, a.out))


if __name__ == "__main__":
    main()
