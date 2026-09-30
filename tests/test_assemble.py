import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from assemble import build


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def test_single_shot_with_narration(tmp_path):
    """Regression: one shot + audio used to reference an undefined [v0] label."""
    _ff("-f", "lavfi", "-i", "color=c=gray:s=320x180:d=2", str(tmp_path / "a.mp4"))
    _ff("-f", "lavfi", "-i", "sine=f=440:d=2", str(tmp_path / "vo.wav"))
    edit = {
        "fps": 10,
        "size": [320, 180],
        "shots": [{"src": "a.mp4", "dur": 2}],
        "narration": "vo.wav",
    }
    (tmp_path / "e.json").write_text(json.dumps(edit))
    out = tmp_path / "out.mp4"
    build(edit, tmp_path, out)
    assert out.stat().st_size > 0
