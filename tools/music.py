"""Background music: Google Lyria 3 via OpenRouter (default) or ElevenLabs.

    uv run tools/music.py "sparse felt piano, warm tape hiss, curious, 80bpm" --seconds 60 \
        -o projects/x/gen/music.mp3 [--provider elevenlabs]

Lyria: <=30s uses the clip model ($0.04), longer uses the pro model ($0.08 per song).
The result is trimmed to --seconds with a short fade-out; assemble.py loops it if the cut runs longer.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import tempfile
from pathlib import Path

import httpx

from common import CONFIG, check, key, out_path

CLIP_MAX_SECONDS = 30


def lyria(prompt: str, seconds: float) -> bytes:
    """Stream a Lyria generation from OpenRouter; returns the encoded audio (MP3)."""
    cfg = CONFIG["music"]
    model = cfg["lyria_clip"] if seconds <= CLIP_MAX_SECONDS else cfg["lyria_pro"]
    ask = f"Instrumental only, no vocals. About {round(seconds)} seconds long. {prompt}"
    chunks: list[str] = []
    with httpx.stream(
        "POST",
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key('openrouter')}"},
        json={
            "model": model,
            "stream": True,
            "modalities": ["text", "audio"],
            "audio": {"format": "mp3"},
            "messages": [{"role": "user", "content": ask}],
        },
        timeout=600,
    ) as r:
        if r.is_error:
            r.read()
            check(r)
        for line in r.iter_lines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            d = json.loads(line[6:])
            if "error" in d:
                raise SystemExit(f"lyria error: {d['error']}")
            for c in d.get("choices", []):
                if data := (c.get("delta", {}).get("audio") or {}).get("data"):
                    chunks.append(data)
            if cost := (d.get("usage") or {}).get("cost"):
                print(f"{model}  cost: ${cost}")
    if not chunks:
        raise SystemExit("lyria returned no audio")
    return b"".join(base64.b64decode(c) for c in chunks)


def elevenlabs(prompt: str, seconds: float) -> bytes:
    r = httpx.post(
        "https://api.elevenlabs.io/v1/music?output_format=mp3_48000_192",
        headers={"xi-api-key": key("eleven")},
        json={
            "prompt": prompt,
            "music_length_ms": int(seconds * 1000),
            "model_id": CONFIG["music"]["eleven_model"],
            "force_instrumental": True,
        },
        timeout=600,
    )
    return check(r).content


def fit(audio: bytes, seconds: float, out: Path) -> None:
    """Trim to length with a 2s fade-out, re-encoding to whatever format `out` names."""
    with tempfile.NamedTemporaryFile(suffix=".mp3") as src:
        src.write(audio)
        src.flush()
        fade = max(seconds - 2, 0)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", src.name, "-t", str(seconds),
             "-af", f"afade=t=out:st={fade}:d=2", str(out_path(out))],
            check=True,
        )  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("-o", "--out", required=True, type=Path)
    ap.add_argument(
        "--provider", choices=["lyria", "elevenlabs"], default=CONFIG["music"]["provider"]
    )
    a = ap.parse_args()
    gen = lyria if a.provider == "lyria" else elevenlabs
    fit(gen(a.prompt, a.seconds), a.seconds, a.out)
    print(a.out)


if __name__ == "__main__":
    main()
