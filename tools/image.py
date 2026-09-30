"""Keyframe / still generation via OpenRouter.

    uv run tools/image.py "prompt" -o projects/x/gen/kf01.png [--ref assets/refs/style.png ...]
                                   [--model alt] [--aspect 16:9]

Reference images (--ref) are how you keep characters and style consistent across shots:
generate one hero/style frame first, then pass it as --ref to every later keyframe.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
from pathlib import Path

import httpx

from common import CONFIG, check, key, out_path


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def generate(prompt: str, out: Path, model: str, refs: list[Path], aspect: str) -> Path:
    content: list[dict] = [{"type": "text", "text": prompt}]
    content += [{"type": "image_url", "image_url": {"url": data_url(r)}} for r in refs]
    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key('openrouter')}"},
        json={
            "model": model,
            "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": content}],
            "image_config": {"aspect_ratio": aspect},
        },
        timeout=300,
    )
    check(resp)
    msg = resp.json()["choices"][0]["message"]
    images = msg.get("images") or []
    if not images:
        raise SystemExit(f"no image returned; model said: {msg.get('content')!r}")
    b64 = images[0]["image_url"]["url"].split(",", 1)[1]
    out_path(out).write_bytes(base64.b64decode(b64))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", required=True, type=Path)
    ap.add_argument("--model", default="default", help="key in [image] config or a full model id")
    ap.add_argument("--ref", action="append", type=Path, default=[])
    ap.add_argument("--aspect", default="16:9")
    a = ap.parse_args()
    model = CONFIG["image"].get(a.model, a.model)
    print(generate(a.prompt, a.out, model, a.ref, a.aspect))


if __name__ == "__main__":
    main()
