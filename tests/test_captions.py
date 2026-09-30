import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from captions import _ts, to_ass


def test_timestamp_format():
    assert _ts(3725.5) == "1:02:05.50"


def test_ass_groups_words_and_karaoke_timing():
    words = [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(7)]
    ass = to_ass(words, per_line=3, w=1920, h=1080)
    lines = [ln for ln in ass.splitlines() if ln.startswith("Dialogue")]
    assert len(lines) == 3
    assert "{\\kf40}w0" in lines[0]
