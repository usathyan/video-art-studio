#!/usr/bin/env bash
# End-to-end smoke test. Costs ~1 image + 1 TTS line. Never calls video models.
set -euo pipefail
cd "$(dirname "$0")/.."
P=projects/_smoke
mkdir -p $P/gen $P/out
LINE="Before the press, every book was copied by hand, one patient letter at a time, and a single volume could take a scribe the better part of a year."
echo "$LINE" > $P/script.md
uv run tools/image.py "Newspaper-cutout collage: a medieval scribe's desk, quill and parchment, layered torn paper, halftone texture, soft shadows, no text" \
  -o $P/gen/kf01.png --model cheap
uv run tools/tts.py "$LINE" -o $P/gen/vo.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $P/gen/vo.wav)
python3 - "$DUR" > $P/edit.json <<'PY'
import json, sys
d = float(sys.argv[1]) + 0.5
print(json.dumps({"fps": 30, "size": [1280, 720],
  "shots": [{"src": "gen/kf01.png", "dur": d / 2, "move": "in"},
            {"src": "gen/kf01.png", "dur": d / 2 + 0.6, "move": "out", "xfade": 0.6}],
  "narration": "gen/vo.wav"}))
PY
uv run tools/assemble.py $P/edit.json -o $P/out/smoke.mp4
uv run tools/captions.py $P/out/smoke.mp4 -o $P/out/smoke.captioned.mp4
uv run tools/critic.py $P/out/smoke.captioned.mp4 --script $P/script.md
uv run tools/video.py "slow push-in" -o $P/gen/never.mp4 --first $P/gen/kf01.png --duration 5 --model cheap  # dry run
