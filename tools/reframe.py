"""Reframe a photo to a film aspect ratio without inventing more than necessary.

    uv run tools/reframe.py photo.jpg -o shot.jpg                   # auto: crop if possible
    uv run tools/reframe.py photo.jpg -o shot.jpg --band 0.33 0.93  # portrait: keep this band, outpaint sides
    uv run tools/reframe.py photo.jpg -o shot.jpg --aspect 9:16

Photos whose orientation matches the film (landscape/pano for 16:9) are cropped (anchor with --anchor x y, 0..1). Portraits
(or any photo narrower than the target) keep a horizontal band (fractions of the height) and the
image model fills ONLY the sides; the original pixels are then pasted back over the centre so the
photograph itself is exact. Prints "centre drift" (0-255): how much the model altered the middle —
above ~30 means the model re-imagined the photo and the seams may show; retry or pick another band.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

from common import CONFIG
from image import generate

OUTPAINT_PROMPT = (
    "This is a photograph placed in the middle of a wider frame; the flat gray areas on the left "
    "and right are empty. Fill ONLY the gray areas by naturally continuing the scene outward (same "
    "light, lens, perspective, colour and grain) so it reads as one seamless photograph. Do not "
    "change, move, rescale or restyle anything in the existing photo. No text, no borders."
)


def ratio(aspect: str) -> float:
    a, b = aspect.split(":")
    return float(a) / float(b)


def crop_to(im: Image.Image, r: float, ax: float = 0.5, ay: float = 0.5) -> Image.Image:
    w, h = im.size
    tw, th = (w, round(w / r)) if w / h < r else (round(h * r), h)
    x, y = round((w - tw) * ax), round((h - th) * ay)
    return im.crop((x, y, x + tw, y + th))


def band_canvas(im: Image.Image, band: tuple[float, float], r: float):
    """Crop a horizontal band and centre it on a gray canvas of aspect r. Returns (canvas, src, x)."""
    y0, y1 = round(band[0] * im.height), round(band[1] * im.height)
    src = im.crop((0, y0, im.width, y1))
    w = round(src.height * r)
    x = (w - src.width) // 2
    canvas = Image.new("RGB", (w, src.height), (128, 128, 128))
    canvas.paste(src, (x, 0))
    return canvas, src, x


def paste_back(gen: Image.Image, canvas: Image.Image, src: Image.Image, x: int, feather: int = 40):
    """Composite the original band over the generated frame with a soft edge; return (image, drift)."""
    gen = gen.convert("RGB").resize(canvas.size, Image.LANCZOS)
    drift = (
        sum(
            ImageStat.Stat(
                ImageChops.difference(gen.crop((x, 0, x + src.width, src.height)), src)
            ).mean
        )
        / 3
    )
    mask = Image.new("L", canvas.size, 0)
    mask.paste(255, (x + feather, 0, x + src.width - feather, src.height))
    mask = mask.filter(ImageFilter.GaussianBlur(feather / 2))
    return Image.composite(canvas, gen, mask), drift


def reframe(
    path: Path,
    out: Path,
    aspect: str = "16:9",
    band=None,
    anchor=(0.5, 0.5),
    size: tuple[int, int] | None = None,
) -> float | None:
    r = ratio(aspect)
    im = Image.open(path).convert("RGB")
    size = size or ((1920, 1080) if r >= 1 else (1080, 1920))
    same_orientation = (im.width > im.height * 1.05) == (r > 1)
    if band is None and same_orientation:  # crop (never invent pixels when a crop will do)
        crop_to(im, r, *anchor).resize(size, Image.LANCZOS).save(out, quality=95)
        return None
    canvas, src, x = band_canvas(im, band or (0.2, 0.8), r)
    tmp = out.with_suffix(".canvas.png")
    canvas.save(tmp)
    raw = out.with_suffix(".raw.png")
    generate(OUTPAINT_PROMPT, raw, CONFIG["image"]["default"], [tmp], aspect)
    final, drift = paste_back(Image.open(raw), canvas, src, x)
    final.resize(size, Image.LANCZOS).save(out, quality=95)
    return drift


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument(
        "--band",
        nargs=2,
        type=float,
        metavar=("TOP", "BOTTOM"),
        help="fractions of height to keep when outpainting (e.g. 0.33 0.93)",
    )
    ap.add_argument("--anchor", nargs=2, type=float, default=(0.5, 0.5), metavar=("X", "Y"))
    a = ap.parse_args()
    drift = reframe(a.photo, a.out, a.aspect, tuple(a.band) if a.band else None, tuple(a.anchor))
    if drift is None:
        print(f"{a.out}  (cropped, no generation)")
    else:
        warn = "  ⚠ high — check the seams" if drift > 30 else ""
        print(f"{a.out}  (outpainted sides, centre drift {drift:.1f}/255){warn}")


if __name__ == "__main__":
    main()
