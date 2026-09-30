"""Assemble a video from an edit list (JSON) with ffmpeg; also export an OpenTimelineIO file.

    uv run tools/assemble.py projects/x/edit.json -o projects/x/out/final.mp4

edit.json (paths relative to the json file):
{
  "fps": 30, "size": [1920, 1080],
  "shots": [
    {"src": "gen/shot01.mp4", "in": 0.0, "dur": 5.0},
    {"src": "gen/kf02.png",  "dur": 4.0, "move": "in"},         # still → Ken Burns (in|out|none)
    {"src": "out/hf-title.mp4", "dur": 3.0, "xfade": 0.6}         # xfade = crossfade INTO this shot
  ],
  "narration": "gen/vo.wav",
  "music": "gen/music.mp3", "music_db": -16
}

Shot audio is always dropped (model-generated audio clashes with narration).
OTIO is an interchange format only — it lets you open the cut in Resolve/Premiere; ffmpeg renders.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import opentimelineio as otio

IMG = {".png", ".jpg", ".jpeg", ".webp"}


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def normalize(shot: dict, base: Path, fps: int, w: int, h: int, dst: Path) -> None:
    src = base / shot["src"]
    fit = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},format=yuv420p"
    if src.suffix.lower() in IMG:
        frames = int(shot["dur"] * fps)
        move = shot.get("move", "in")
        z = {"in": "1+0.0008*on", "out": "1.12-0.0008*on", "none": "1"}[move]
        vf = (
            f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='{z}':d={frames}:s={w}x{h}:fps={fps}:x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2',"
            "setsar=1,format=yuv420p"
        )
        ff("-loop", "1", "-i", str(src), "-t", str(shot["dur"]), "-vf", vf, "-an", str(dst))
    else:
        ff(
            "-ss",
            str(shot.get("in", 0)),
            "-t",
            str(shot["dur"]),
            "-i",
            str(src),
            "-vf",
            fit,
            "-an",
            str(dst),
        )


def build(edit: dict, base: Path, out: Path) -> None:
    fps, (w, h) = edit.get("fps", 30), edit.get("size", [1920, 1080])
    shots = edit["shots"]
    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, s in enumerate(shots):
            p = Path(td) / f"{i:03d}.mp4"
            normalize(s, base, fps, w, h, p)
            parts.append(p)

        # chain xfades; offset = running length minus overlap
        inputs, chain, last, t = [], [], "0:v", shots[0]["dur"]
        for p in parts:
            inputs += ["-i", str(p)]
        for i, s in enumerate(shots[1:], 1):
            x = s.get("xfade", 0)
            label = f"v{i}"
            if x > 0:
                chain.append(
                    f"[{last}][{i}:v]xfade=transition=fade:duration={x}:offset={t - x}[{label}]"
                )
                t += s["dur"] - x
            else:
                chain.append(f"[{last}][{i}:v]concat=n=2:v=1:a=0[{label}]")
                t += s["dur"]
            last = label

        audio_in, a_filter = [], []
        n = len(parts)
        if edit.get("narration"):
            audio_in += ["-i", str(base / edit["narration"])]
            a_filter.append(f"[{n}:a]aresample=48000,apad[nar]")
            n += 1
        if edit.get("music"):
            audio_in += ["-stream_loop", "-1", "-i", str(base / edit["music"])]
            db = edit.get("music_db", -16)
            a_filter.append(
                f"[{n}:a]aresample=48000,volume={db}dB,afade=t=out:st={max(t - 2, 0)}:d=2[mus]"
            )
        if edit.get("narration") and edit.get("music"):
            # duck music under the voice
            a_filter.append(
                "[nar]asplit[nar1][nar2];[mus][nar1]sidechaincompress=threshold=0.05:ratio=6:release=400[duck];"
                "[nar2][duck]amix=inputs=2:duration=first:normalize=0[aout]"
            )
        elif edit.get("narration"):
            a_filter.append("[nar]anull[aout]")
        elif edit.get("music"):
            a_filter.append("[mus]anull[aout]")

        graph = ";".join(chain + a_filter) or "[0:v]null[v0]"
        vout = f"[{last}]" if chain else "[v0]"
        maps = ["-map", vout] + (["-map", "[aout]"] if a_filter else [])
        out.parent.mkdir(parents=True, exist_ok=True)
        ff(
            *inputs,
            *audio_in,
            "-filter_complex",
            graph,
            *maps,
            "-t",
            f"{t:.3f}",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out),
        )
    write_otio(edit, base, out.with_suffix(".otio"), fps)
    print(f"{out}  ({t:.2f}s)")


def write_otio(edit: dict, base: Path, path: Path, fps: int) -> None:
    tl = otio.schema.Timeline(name=path.stem)
    track = otio.schema.Track(name="V1")
    for s in edit["shots"]:
        rng = otio.opentime.TimeRange(
            otio.opentime.RationalTime(s.get("in", 0) * fps, fps),
            otio.opentime.RationalTime(s["dur"] * fps, fps),
        )
        ref = otio.schema.ExternalReference(target_url=str((base / s["src"]).resolve()))
        track.append(
            otio.schema.Clip(name=Path(s["src"]).stem, media_reference=ref, source_range=rng)
        )
    tl.tracks.append(track)
    otio.adapters.write_to_file(tl, str(path))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("edit", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args()
    build(json.loads(a.edit.read_text()), a.edit.parent, a.out)


if __name__ == "__main__":
    main()
