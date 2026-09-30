"""Critic: measure a render, then judge it. Claude reads the contact sheet + report.

    uv run tools/critic.py projects/x/out/final.mp4 [--script projects/x/script.md] [--every 2]

Writes next to the video:
  <name>.critic/contact.jpg   — frame grid (Claude Read()s this to eyeball composition/consistency)
  <name>.critic/report.json   — measurements + verdicts
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

from captions import script_words, transcribe


def run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stderr


def measure(video: Path, script: Path | None, every: float, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    dur = float(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(video),
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    n = min(36, max(4, int(dur / every)))  # frames sampled evenly across the whole video
    cols = 6 if n > 16 else 4
    n = -(-n // cols) * cols  # fill the last row
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            f"fps={n}/{dur},scale=480:-1,tile={cols}x{-(-n // cols)}",
            "-frames:v",
            "1",
            str(outdir / "contact.jpg"),
        ],
        check=True,
    )

    black = [
        float(x)
        for x in re.findall(
            r"black_duration:([\d.]+)",
            run(
                "ffmpeg",
                "-i",
                str(video),
                "-vf",
                "blackdetect=d=0.2:pix_th=0.08",
                "-an",
                "-f",
                "null",
                "-",
            ),
        )
    ]
    frozen = [
        float(x)
        for x in re.findall(
            r"freeze_duration: ([\d.]+)",
            run(
                "ffmpeg",
                "-i",
                str(video),
                "-vf",
                "freezedetect=n=0.003:d=1.5",
                "-an",
                "-f",
                "null",
                "-",
            ),
        )
    ]
    loud = run("ffmpeg", "-i", str(video), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-")
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)

    m = {
        "duration": dur,
        "black_segments": black,
        "frozen_segments": frozen,
        "lufs": float(lufs[-1]) if lufs else None,
        "true_peak_db": float(peak[-1]) if peak else None,
    }
    if script and script.exists():
        words = transcribe(video)
        heard = " ".join(w["word"] for w in words).lower()
        wanted = re.sub(r"<[^>]+>", " ", " ".join(script_words(script.read_text()))).lower()
        norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s).split()
        m["script_match"] = SequenceMatcher(None, norm(wanted), norm(heard)).ratio()
        m["speech_end"] = words[-1]["end"] if words else 0.0
    return m


def judge(m: dict) -> list[str]:
    """Turn measurements into a list of human-readable problems. Empty list = PASS.

    Available keys in m: duration, black_segments (list[s]), frozen_segments (list[s]),
    lufs (integrated loudness), true_peak_db, and if --script given: script_match (0..1),
    speech_end (s).

    TODO(you): decide what "good enough" means for this repo. Things to weigh:
      - loudness target: YouTube/web ≈ -14 LUFS, broadcast -23; how far off is tolerable?
      - peaks above ~-1 dBFS clip after platform re-encode
      - black: a 0.3s dip-to-black can be intentional; 2s is probably a bug
      - frozen: generative-art loops / title holds can legitimately freeze — maybe allow
        a longer freeze than for explainers?
      - script_match: TTS mispronunciations vs. dropped lines — ~0.85 catches missing sentences
      - speech_end vs duration: narration shouldn't be cut off, nor leave >3s of dead air
    """
    problems: list[str] = []
    # --- your 5-10 lines here ---
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--script", type=Path)
    ap.add_argument("--every", type=float, default=2.0, help="seconds between contact-sheet frames")
    a = ap.parse_args()
    outdir = a.video.with_suffix(".critic")
    m = measure(a.video, a.script, a.every, outdir)
    m["problems"] = judge(m)
    (outdir / "report.json").write_text(json.dumps(m, indent=2))
    print(json.dumps(m, indent=2))
    print(f"\ncontact sheet: {outdir / 'contact.jpg'}")
    print("PASS" if not m["problems"] else "FAIL")


if __name__ == "__main__":
    main()
