"""Image/text-to-video via OpenRouter. DRY-RUN BY DEFAULT — prints estimated cost.

    uv run tools/video.py "slow dolly-in, paper layers drift" -o projects/x/gen/shot03.mp4 \
        --first projects/x/gen/kf03.png [--last kf04.png] --duration 6 [--model cinematic] --confirm

Model audio is OFF by default: narration + music are mixed at assembly, and generated
audio would clash (and costs ~2x on Veo).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import httpx

from common import CONFIG, check, key, out_path
from image import data_url

API = "https://openrouter.ai/api/v1"


# Output frame sizes for token-priced models (Seedance): tokens = W × H × fps × seconds / 1024
_SIZES = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160)}
_TOKEN_FPS = 24


def estimate(model: str, duration: int, resolution: str, audio: bool) -> tuple[float | None, str]:
    """(usd, explanation) from OpenRouter's live pricing table. usd is None if unpriceable."""
    r = check(httpx.get(f"{API}/videos/models", headers=_auth(), timeout=30)).json()
    m = next((x for x in r["data"] if x["id"] == model), None)
    if not m:
        raise SystemExit(f"unknown video model {model}")
    p = m["pricing_skus"]
    aud = "with_audio" if audio else "without_audio"
    res = resolution.lower()

    per_sec = [  # most specific first; value is USD per second
        f"duration_seconds_{aud}_{res}",
        f"duration_seconds_{aud}",
        f"image_to_video_duration_seconds_{res}",
        f"duration_seconds_{res}",
        "duration_seconds",
    ]
    for k in per_sec:
        if k in p:
            return float(p[k]) * duration, f"{k}=${p[k]}/s × {duration}s"
    cents = [  # value is US cents per second
        f"cents_per_second_output_{res}",
        f"cents_per_video_output_second_{res}",
        "cents_per_second_output",
    ]
    for k in cents:
        if k in p:
            return float(p[k]) / 100 * duration, f"{k}={p[k]}¢/s × {duration}s"
    tok_key = f"video_tokens_{res}" if f"video_tokens_{res}" in p else "video_tokens"
    if tok_key in p and res in _SIZES:
        w, h = _SIZES[res]
        tokens = w * h * _TOKEN_FPS * duration / 1024
        return tokens * float(
            p[tok_key]
        ), f"{tokens:,.0f} tokens ({w}x{h}@{_TOKEN_FPS}fps) × ${p[tok_key]}"
    return None, f"cannot price this model/resolution from {p}"


def _auth() -> dict:
    return {"Authorization": f"Bearer {key('openrouter')}"}


def generate(args) -> Path:
    body: dict = {
        "model": args.model,
        "prompt": args.prompt,
        "duration": args.duration,
        "resolution": args.resolution,
        "aspect_ratio": args.aspect,
        "generate_audio": args.audio,
    }
    frames = [(args.first, "first_frame"), (args.last, "last_frame")]
    body["frame_images"] = [
        {"type": "image_url", "image_url": {"url": data_url(p)}, "frame_type": t}
        for p, t in frames
        if p
    ]
    if args.ref:
        body["input_references"] = [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in args.ref
        ]
    job = httpx.post(f"{API}/videos", headers=_auth(), json=body, timeout=120)
    check(job)
    job_id = job.json()["id"]
    print(f"job {job_id} submitted")
    while True:
        time.sleep(10)
        st = httpx.get(f"{API}/videos/{job_id}", headers=_auth(), timeout=60).json()
        print(f"  {st['status']}")
        if st["status"] == "completed":
            break
        if st["status"] == "failed":
            raise SystemExit(f"generation failed: {st}")
    vid = httpx.get(f"{API}/videos/{job_id}/content?index=0", headers=_auth(), timeout=300)
    check(vid)
    out_path(args.out).write_bytes(vid.content)
    print(f"cost: {st.get('usage', {}).get('cost')}")
    return args.out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", required=True, type=Path)
    ap.add_argument("--model", default="default")
    ap.add_argument("--first", type=Path)
    ap.add_argument("--last", type=Path)
    ap.add_argument("--ref", action="append", type=Path, default=[])
    ap.add_argument("--duration", type=int, default=5)
    ap.add_argument("--resolution", default="1080p")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument(
        "--audio", action="store_true", help="let the model generate audio (usually no)"
    )
    ap.add_argument("--confirm", action="store_true", help="actually spend money")
    ap.add_argument(
        "--max-usd", type=float, help="spend ceiling; required when the cost can't be estimated"
    )
    a = ap.parse_args()
    a.model = CONFIG["video"].get(a.model, a.model)
    usd, why = estimate(a.model, a.duration, a.resolution, a.audio)
    shown = f"~${usd:.2f}" if usd is not None else "UNKNOWN"
    print(f"{a.model}  {a.duration}s {a.resolution} {a.aspect}  est {shown}  ({why})")
    if not a.confirm:
        print("dry run — re-run with --confirm to generate")
        return
    if usd is None and a.max_usd is None:
        raise SystemExit(
            "refusing: cost unknown for this model — pass --max-usd to accept the risk"
        )
    if usd is not None and a.max_usd is not None and usd > a.max_usd:
        raise SystemExit(f"refusing: estimate ${usd:.2f} exceeds --max-usd {a.max_usd}")
    print(generate(a))


if __name__ == "__main__":
    main()
