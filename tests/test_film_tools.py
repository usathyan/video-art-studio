import json
import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import beats
import film
import ingest
import reframe


@pytest.fixture(autouse=True)
def _no_paid_calls(monkeypatch):
    """Tests must never reach a paid API."""

    def boom(*a, **k):
        raise AssertionError("test tried to call a paid generation API")

    monkeypatch.setattr(reframe, "generate", boom)


# ------------------------------------------------------------------ ingest ---


def _photo_with_exif(path: Path, w=60, h=40, orientation=6):
    im = Image.new("RGB", (w, h), (200, 40, 40))
    exif = Image.Exif()
    exif[274] = orientation  # rotate 90° CW on display
    exif[306] = "2026:08:25 05:40:00"
    gps = {1: "N", 2: (35.0, 0.0, 0.0)}
    exif[0x8825] = gps
    im.save(path, exif=exif)


def test_ingest_rotates_strips_gps_and_reads_captions(tmp_path):
    src = tmp_path / "trip" / "05-fushimi"
    src.mkdir(parents=True)
    _photo_with_exif(src / "01-gate.jpg")
    (src / "captions.txt").write_text("01  The grand gate at dawn.\n")
    (src / "post.md").write_text("# Day 5\nUp at four fifteen.\n")
    out = tmp_path / "proj"
    m = ingest.ingest(tmp_path / "trip", out)
    item = m[0]
    assert item["kind"] == "photo" and item["caption"] == "The grand gate at dawn."
    assert (item["w"], item["h"]) == (40, 60)  # rotation baked in
    assert item["orientation"] == "portrait"
    assert item["taken"].startswith("2026-08-25T05:40")
    cleaned = Image.open(out / "work" / "media" / item["file"])
    assert len(cleaned.getexif()) == 0  # no EXIF → no GPS
    assert "Up at four fifteen" in (out / "source.md").read_text()
    assert (out / ".gitignore").read_text().count("work/") == 1
    assert list((out / "work" / "sheets").glob("*.jpg"))


# ------------------------------------------------------------------- beats ---


def test_beats_finds_tempo_of_click_track(tmp_path):
    sr, period = 22050, 0.5  # 120 bpm
    x = np.zeros(int(sr * 12), dtype=np.float32)
    for t in np.arange(0.25, 12, period):
        i = int(t * sr)
        x[i : i + 400] = np.hanning(400) * 0.9
    wav = tmp_path / "click.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "f32le",
            "-ar",
            str(sr),
            "-ac",
            "1",
            "-i",
            "-",
            str(wav),
        ],
        input=x.tobytes(),
        check=True,
    )
    r = beats.analyse(wav)
    assert abs(r["period"] - period) < 0.02
    assert (
        abs((r["first"] - 0.25) % period) < 0.05
        or abs((r["first"] - 0.25) % period - period) < 0.05
    )


# ----------------------------------------------------------------- reframe ---


def test_reframe_crops_landscape_without_generation(tmp_path):
    src = tmp_path / "wide.jpg"
    Image.new("RGB", (1600, 1067), "green").save(src)
    out = tmp_path / "out.jpg"
    assert reframe.reframe(src, out, "16:9") is None
    assert Image.open(out).size == (1920, 1080)


def test_band_canvas_and_paste_back_keep_original_pixels():
    im = Image.new("RGB", (900, 1600), (10, 120, 200))
    canvas, src, x = reframe.band_canvas(im, (0.25, 0.75), 16 / 9)
    assert canvas.size == (round(800 * 16 / 9), 800) and src.size == (900, 800)
    fake_gen = Image.new("RGB", canvas.size, (250, 250, 0))  # model output: sides filled
    fake_gen.paste(src, (x, 0))
    final, drift = reframe.paste_back(fake_gen, canvas, src, x)
    assert drift < 1
    cx = x + src.width // 2
    assert final.getpixel((cx, 400)) == (10, 120, 200)  # centre is the original
    assert final.getpixel((5, 400)) == (250, 250, 0)  # sides are generated


# -------------------------------------------------------------------- film ---


def _film(tmp_path, shots, end=None, voice=None):
    (tmp_path / "work" / "media").mkdir(parents=True)
    for s in shots:
        Image.new("RGB", (1600, 900)).save(tmp_path / "work" / "media" / s["photo"])
    spec = {"title": "Test Film", "shots": shots, "score": {"prompt": "x"}}
    if end:
        spec["end"] = end
    if voice:
        spec["voice"] = voice
    p = tmp_path / "film.json"
    p.write_text(json.dumps(spec))
    f = film.Film(p)
    f.p("beats.json").write_text(
        json.dumps(
            {"first": 0.05, "period": 1.0, "duration": 30.0, "beats": [0.05 + k for k in range(30)]}
        )
    )
    return f


def test_timeline_cuts_on_beats_and_holds_end(tmp_path):
    shots = [
        {"id": "a", "photo": "a.jpg", "prompt": "p", "beats": 4},
        {"id": "b", "photo": "b.jpg", "prompt": "p", "beats": 6},
    ]
    f = _film(tmp_path, shots, end={"text": "fin", "beats": 5})
    spans, end = f.timeline()
    assert spans == [(0.0, 4.05), (4.05, 10.05)]
    assert end == (10.05, 15.05)
    assert f.total() == 15.05
    assert f.slug == "test-film"


def test_validate_reports_missing_pieces(tmp_path):
    f = _film(
        tmp_path,
        [{"id": "a", "photo": "a.jpg", "beats": 4}],
        voice={"lines": [{"text": "hi", "shot": 3}]},
    )
    errs = film.validate(f)
    assert any("needs a prompt" in e for e in errs)
    assert any("out of range" in e for e in errs)


def test_every_style_is_complete_and_has_fonts():
    styles = tomllib.loads((ROOT / "config" / "styles.toml").read_text())
    fonts = styles.pop("FONTS")
    keys = {
        "label",
        "grade",
        "grain",
        "letterbox",
        "fps",
        "title_font",
        "text_font",
        "title_case",
        "title_tracking",
        "flash",
    }
    for name, st in styles.items():
        assert keys <= st.keys(), name
        assert st["title_font"] in fonts and st["text_font"] in fonts, name
