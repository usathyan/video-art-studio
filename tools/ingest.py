"""Ingest a folder of photos, videos and text into a project Claude can reason about.

    uv run tools/ingest.py ~/Pictures/japan -o projects/japan

Writes into <out>/:
  source.md             every text file found (posts, notes, captions), concatenated with headers
  work/media/<id>.jpg   photos: EXIF rotation baked in, sRGB, ALL metadata (incl. GPS) stripped
  work/media/<id>.mp4   videos: copied as-is (probed for size/duration)
  work/manifest.json    one entry per item: id, kind, orientation, size, taken-at, caption, folder
  work/sheets/*.jpg     numbered contact sheets (one per source folder) for visual review
  .gitignore            keeps personal source material and working files out of git

Ids are "<folder index>-<item index>" in name order, e.g. 03-12. Captions are picked up from
captions.txt files ("NN  caption" lines) and from `[IMAGE NN — caption]` markers in markdown.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

PHOTO = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}
VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
TEXT = {".md", ".txt", ".markdown"}
SRGB = ImageCms.createProfile("sRGB")
DATETIME_TAGS = (36867, 36868, 306)  # DateTimeOriginal, DateTimeDigitized, DateTime

try:  # HEIC support is optional
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    pass


def orientation(w: int, h: int) -> str:
    if w > h * 2:
        return "pano"
    if h > w * 1.05:
        return "portrait"
    return "landscape"


def taken_at(im: Image.Image) -> str | None:
    exif = im.getexif()
    sub = exif.get_ifd(0x8769) if exif else {}
    for tag in DATETIME_TAGS:
        raw = sub.get(tag) or exif.get(tag)
        if raw:
            try:
                # EXIF stores local wall-clock time with no zone, so a naive datetime is the honest value
                return datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S").isoformat()  # noqa: DTZ007
            except ValueError:
                continue
    return None


def clean_photo(src: Path, dst: Path) -> dict:
    """Bake rotation, convert to sRGB, save without any metadata. Returns size + capture time."""
    im = Image.open(src)
    when = taken_at(im)
    im = ImageOps.exif_transpose(im) or im
    if icc := im.info.get("icc_profile"):
        try:
            im = ImageCms.profileToProfile(
                im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), SRGB, outputMode="RGB"
            )
        except ImageCms.PyCMSError:
            pass
    im = im.convert("RGB")
    im.save(dst, quality=92)  # no exif= / icc_profile= → metadata (incl. GPS) is dropped
    return {"w": im.width, "h": im.height, "taken": when}


def probe_video(src: Path) -> dict:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height:format=duration:format_tags=creation_time",
            "-of",
            "json",
            str(src),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    j = json.loads(out)
    s = (j.get("streams") or [{}])[0]
    fmt = j.get("format", {})
    return {
        "w": s.get("width", 0),
        "h": s.get("height", 0),
        "duration": round(float(fmt.get("duration", 0)), 2),
        "taken": (fmt.get("tags") or {}).get("creation_time"),
    }


def captions_for(folder: Path) -> dict[str, str]:
    caps: dict[str, str] = {}
    for f in folder.glob("captions.txt"):
        for line in f.read_text(errors="ignore").splitlines():
            if m := re.match(r"\s*(\d{1,3})\s+(.+)", line):
                caps[m.group(1).zfill(2)] = m.group(2).strip()
    for f in folder.glob("*.md"):
        for m in re.finditer(
            r"\[IMAGE\s+(\d{1,3})\s*[—:-]\s*([^\]]+)\]", f.read_text(errors="ignore")
        ):
            caps.setdefault(m.group(1).zfill(2), m.group(2).strip())
    return caps


def sheet(items: list[dict], media: Path, out: Path) -> None:
    cols = 4 if len(items) > 6 else 3
    tw, th = 400, 300
    rows = -(-len(items) // cols)
    canvas = Image.new("RGB", (cols * tw, rows * th), "black")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except OSError:
        font = ImageFont.load_default()
    for i, it in enumerate(items):
        x, y = (i % cols) * tw, (i // cols) * th
        if it["kind"] == "photo":
            im = Image.open(media / it["file"])
        else:  # first frame of a video
            frame = media / f"{it['id']}.thumb.jpg"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-ss",
                    "0.5",
                    "-i",
                    str(media / it["file"]),
                    "-frames:v",
                    "1",
                    str(frame),
                ],
                check=False,
            )
            im = Image.open(frame) if frame.exists() else Image.new("RGB", (16, 9), "gray")
        im.thumbnail((tw - 6, th - 6))
        canvas.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        label = it["id"] + (" ▶" if it["kind"] == "video" else "")
        draw.rectangle([x, y, x + 12 + 16 * len(label), y + 32], fill="black")
        draw.text((x + 6, y + 2), label, fill="yellow", font=font)
    canvas.save(out, quality=80)


def ingest(src: Path, out: Path) -> list[dict]:
    media = out / "work" / "media"
    sheets = out / "work" / "sheets"
    media.mkdir(parents=True, exist_ok=True)
    sheets.mkdir(parents=True, exist_ok=True)
    folders = sorted({p.parent for p in src.rglob("*") if p.is_file()}, key=str)
    manifest, texts = [], []
    for fi, folder in enumerate(folders):
        caps = captions_for(folder)
        files = sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))
        items = []
        n = 0
        for p in files:
            ext = p.suffix.lower()
            if ext in TEXT:
                if p.name != "captions.txt":
                    texts.append(p)
                continue
            if ext not in PHOTO | VIDEO:
                continue
            n += 1
            num = m.group(1).zfill(2) if (m := re.match(r"(\d{1,3})", p.name)) else f"{n:02d}"
            pid = f"{fi:02d}-{n:02d}"
            rel = str(folder.relative_to(src)) if folder != src else "."
            if ext in PHOTO:
                info = clean_photo(p, media / f"{pid}.jpg")
                item = {"id": pid, "kind": "photo", "file": f"{pid}.jpg", **info}
            else:
                shutil.copy2(p, media / f"{pid}{ext}")
                info = probe_video(p)
                item = {"id": pid, "kind": "video", "file": f"{pid}{ext}", **info}
            item.update(
                orientation=orientation(item["w"], item["h"]),
                folder=rel,
                source=p.name,
                caption=caps.get(num, ""),
            )
            items.append(item)
        if items:
            sheet(items, media, sheets / f"{fi:02d}-{folder.name or 'root'}.jpg")
            manifest += items
    (out / "work" / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    parts = [f"<!-- {t.relative_to(src)} -->\n{t.read_text(errors='ignore')}" for t in texts]
    (out / "source.md").write_text("\n\n".join(parts))
    (out / ".gitignore").write_text(
        "# personal media and working files stay local\nwork/\nsource/\nout/\n"
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args()
    m = ingest(a.folder.expanduser(), a.out)
    photos = [x for x in m if x["kind"] == "photo"]
    kinds = {
        k: sum(1 for x in m if x["orientation"] == k) for k in ("landscape", "portrait", "pano")
    }
    print(f"{len(photos)} photos, {len(m) - len(photos)} videos · {kinds}")
    print(f"captions: {sum(1 for x in m if x['caption'])}/{len(m)} · text: {a.out / 'source.md'}")
    print(f"contact sheets: {a.out / 'work' / 'sheets'}")


if __name__ == "__main__":
    main()
