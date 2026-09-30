"""Beat grid + section map of a music track, so cuts can land on beats and scenes on sections.

    uv run tools/beats.py score.mp3 [-o beats.json]

Prints tempo, beat period, first beat, a 2-second loudness bar chart and the biggest loudness
changes ("sections"), each snapped to the nearest beat. JSON: {tempo, period, first, beats,
sections: [{t, beat, change_db}], duration}.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

SR, HOP, WIN = 22050, 512, 2048
LATENCY = WIN / SR  # an onset registers once it enters the analysis window → shift grid later


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(SR),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32)


def onset_strength(x: np.ndarray) -> np.ndarray:
    win = np.hanning(WIN)
    frames = [np.abs(np.fft.rfft(x[i : i + WIN] * win)) for i in range(0, len(x) - WIN, HOP)]
    s = np.log1p(np.array(frames))
    flux = np.maximum(s[1:] - s[:-1], 0).sum(1)
    return (flux - flux.mean()) / (flux.std() + 1e-9)


def _peak(ac: np.ndarray, lo: int, hi: int) -> float:
    """Sub-frame lag of the autocorrelation maximum in [lo, hi] (parabolic interpolation)."""
    i = lo + int(np.argmax(ac[lo : hi + 1]))
    if 0 < i < len(ac) - 1:
        a, b, c = ac[i - 1], ac[i], ac[i + 1]
        den = a - 2 * b + c
        if den:
            return i + 0.5 * (a - c) / den
    return float(i)


def grid(flux: np.ndarray, lo: float = 60, hi: float = 170) -> tuple[float, float]:
    """Return (period_s, first_beat_s) from autocorrelation of the onset curve."""
    fps = SR / HOP
    ac = np.correlate(flux, flux, "full")[len(flux) - 1 :]
    lag = _peak(ac, int(60 * fps / hi), int(60 * fps / lo))
    # octave check: prefer the faster pulse when its peak is nearly as strong
    h = lag / 2
    if 60 * fps / h <= hi:
        half = _peak(ac, max(int(h) - 2, 1), int(h) + 2)
        if ac[round(half)] >= 0.8 * ac[round(lag)]:
            lag = half
    # phase: offset that puts the most onset energy on the grid
    n = int(len(flux) / lag)
    phase = max(
        range(int(lag)),
        key=lambda o: sum(flux[min(int(o + k * lag), len(flux) - 1)] for k in range(n)),
    )
    return lag / fps, (phase / fps + LATENCY) % (lag / fps)


def sections(x: np.ndarray, beats: np.ndarray, n: int = 6, min_gap: float = 6.0) -> list[dict]:
    hop = SR // 10
    k = len(x) // hop
    db = np.maximum(20 * np.log10(np.sqrt((x[: k * hop].reshape(k, hop) ** 2).mean(1)) + 1e-9), -60)
    sm = np.convolve(db, np.ones(10) / 10, "same")  # 1 s smoothing
    change = np.zeros_like(sm)
    change[10:-10] = sm[20:] - sm[:-20]  # level after minus level before (±1 s)
    picks: list[dict] = []
    for i in np.argsort(-np.abs(change)):
        t = i / 10
        if abs(change[i]) < 3 or any(abs(t - p["t"]) < min_gap for p in picks):
            continue
        b = int(np.argmin(abs(beats - t)))
        picks.append(
            {"t": round(float(beats[b]), 3), "beat": b, "change_db": round(float(change[i]), 1)}
        )
        if len(picks) == n:
            break
    return sorted(picks, key=lambda p: p["t"])


def analyse(path: Path) -> dict:
    x = load(path)
    period, first = grid(onset_strength(x))
    dur = len(x) / SR
    beats = np.arange(first, dur, period)
    return {
        "tempo": round(60 / period, 1),
        "period": round(period, 4),
        "first": round(first, 3),
        "beats": [round(float(b), 3) for b in beats],
        "sections": sections(x, beats),
        "duration": round(dur, 2),
        "_x": x,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    r = analyse(a.audio)
    x = r.pop("_x")
    out = a.out or a.audio.with_suffix(".beats.json")
    out.write_text(json.dumps(r, indent=1))
    print(
        f"tempo ≈{r['tempo']} bpm · beat every {r['period']:.3f}s · first beat {r['first']}s "
        f"· {len(r['beats'])} beats · {r['duration']}s"
    )
    step = SR * 2
    for i in range(0, len(x) - step // 2, step):
        lvl = 20 * np.log10(np.sqrt((x[i : i + step] ** 2).mean()) + 1e-9)
        print(f"{i / SR:5.0f}s {lvl:6.1f} dB " + "#" * max(0, int((lvl + 45) / 1.2)))
    for s in r["sections"]:
        print(f"section change {s['change_db']:+5.1f} dB at beat {s['beat']} ({s['t']}s)")
    print(out)


if __name__ == "__main__":
    main()
