"""Word-level captions: whisper.cpp → ASS (word-highlight) → burned into video.

    uv run tools/captions.py in.mp4 -o out.mp4 [--words-per-line 6] [--no-burn]
                             [--script script.md] [--audio narration.wav]

--script  keep whisper's timings but show the script's exact words (fixes proper nouns
          whisper mishears, e.g. "Gotokuji"). Lines starting with "#" or "key:" are ignored.
--audio   transcribe this clean narration stem instead of the video's final mix.

Also writes <in>.words.json (word, start, end) — the critic reuses it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

from common import CONFIG, ffmpeg_with_libass

MODEL_DIR = Path.home() / ".cache" / "whisper"
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{}.bin"


def model_path() -> Path:
    name = CONFIG["asr"]["model"]
    p = MODEL_DIR / f"ggml-{name}.bin"
    if not p.exists():
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        print(f"downloading whisper model {name} …")
        urllib.request.urlretrieve(MODEL_URL.format(name), p)
    return p


def transcribe(media: Path) -> list[dict]:
    """Return [{'word', 'start', 'end'}] in seconds."""
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(media),
                "-ar",
                "16000",
                "-ac",
                "1",
                str(wav),
            ],
            check=True,
        )
        base = Path(td) / "t"
        subprocess.run(
            [
                "whisper-cli",
                "-m",
                str(model_path()),
                "-f",
                str(wav),
                "-ml",
                "1",
                "-sow",
                "-ojf",
                "-of",
                str(base),
                "-np",
            ],
            check=True,
            capture_output=True,
        )
        data = json.loads(base.with_suffix(".json").read_text())
    words = []
    for seg in data["transcription"]:
        w = seg["text"].strip()
        if w:
            words.append(
                {
                    "word": w,
                    "start": seg["offsets"]["from"] / 1000,
                    "end": seg["offsets"]["to"] / 1000,
                }
            )
    return words


def script_words(text: str) -> list[str]:
    lines = [
        ln for ln in text.splitlines() if ln.strip() and not re.match(r"\s*(#|[A-Za-z_]+:\s)", ln)
    ]
    return " ".join(lines).replace("*", "").split()


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align_to_script(words: list[dict], script: list[str]) -> list[dict]:
    """Relabel whisper words with the script's words, keeping whisper's timing."""
    heard = [_norm(w["word"]) for w in words]
    wanted = [_norm(w) for w in script]
    out: list[dict] = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, heard, wanted, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            out += [{**words[i], "word": script[j]} for i, j in zip(range(i1, i2), range(j1, j2))]
        elif op == "replace":  # different word counts: spread script words over the heard span
            t0, t1 = words[i1]["start"], words[i2 - 1]["end"]
            step = (t1 - t0) / (j2 - j1)
            out += [
                {"word": script[j], "start": t0 + k * step, "end": t0 + (k + 1) * step}
                for k, j in enumerate(range(j1, j2))
            ]
        elif op == "insert" and out:  # script words whisper missed: squeeze after previous word
            prev = out[-1]
            out += [
                {"word": script[j], "start": prev["end"], "end": prev["end"]} for j in range(j1, j2)
            ]
        # "delete": whisper heard something not in the script (breath, filler) → drop it
    return out


def _ts(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def to_ass(words: list[dict], per_line: int, w: int, h: int) -> str:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Helvetica Neue,{h // 18},&H0000D7FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,60,60,{h // 12},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for i in range(0, len(words), per_line):
        chunk = words[i : i + per_line]
        # \kf = karaoke fill: each word highlights as it is spoken
        text = " ".join(f"{{\\kf{int((x['end'] - x['start']) * 100)}}}{x['word']}" for x in chunk)
        lines.append(
            f"Dialogue: 0,{_ts(chunk[0]['start'])},{_ts(chunk[-1]['end'])},Cap,,0,0,0,,{text}"
        )
    return head + "\n".join(lines) + "\n"


def probe_size(video: Path) -> tuple[int, int]:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    w, h = out.split(",")
    return int(w), int(h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--words-per-line", type=int, default=6)
    ap.add_argument("--no-burn", action="store_true")
    ap.add_argument("--script", type=Path, help="text whose exact words the captions should show")
    ap.add_argument("--audio", type=Path, help="clean narration stem to transcribe")
    a = ap.parse_args()

    words = transcribe(a.audio or a.video)
    if a.script:
        words = align_to_script(words, script_words(a.script.read_text()))
    a.video.with_suffix(".words.json").write_text(json.dumps(words, indent=1))
    ass = a.video.with_suffix(".ass")
    ass.write_text(to_ass(words, a.words_per_line, *probe_size(a.video)))
    print(f"{len(words)} words → {ass}")
    if a.no_burn:
        return
    out = a.out or a.video.with_name(a.video.stem + ".captioned.mp4")
    subprocess.run(
        [
            ffmpeg_with_libass(),
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(a.video),
            "-vf",
            f"ass={ass}",
            "-c:a",
            "copy",
            str(out),
        ],
        check=True,
    )
    print(out)


if __name__ == "__main__":
    main()
