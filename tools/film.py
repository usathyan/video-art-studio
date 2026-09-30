"""va-film — build a beat-cut cinematic film from photos, driven by one film.json.

    va-film plan   projects/x/film.json          # validate + shot table + cost estimate (free)
    va-film frames projects/x/film.json          # reframe photos to the film aspect (cents)
    va-film shots  projects/x/film.json          # dry run: per-shot cost + total
    va-film shots  projects/x/film.json --confirm [--only a,b]   # generate AI clips (paid)
    va-film score  projects/x/film.json          # music + voice lines + beat/section map
    va-film cut    projects/x/film.json          # grade, cut on beats, titles, mix, master, critic

film.json (paths relative to its folder; see templates/film.example.json):
{
  "title": "Slowing Time", "subtitle": "Ten days in Japan", "slug": "slowing-time",
  "aspect": "16:9", "style": "cinematic-warm", "media": "work/media", "loudness": -14,
  "score": {"prompt": "...", "seconds": 64},              // or {"file": "my-track.mp3"}
  "voice": {"voice": "Charon", "style": "...", "subtitles": true,
            "lines": [{"text": "In Japan, people take time.", "shot": 0, "offset": 1.4}]},
  "shots": [{"id": "torii", "photo": "05-06.jpg", "band": [0.325, 0.925],
             "prompt": "slow dolly forward ...", "model": "cinematic", "duration": 8,
             "beats": 8, "in": 0, "speed": 0.42, "place": ["TOKYO", "東京"]}, ...],
  // voice line "shot" may be a shot index or "end" (the end card)
  "transitions": [{"type": "flash", "before": 4}, {"type": "dip", "before": 8}],
  "end": {"text": "また来ます", "sub": "I'll be back.", "beats": 8}
}
Shot fields: photo (from media) + band (portrait: keep this fraction of height, outpaint sides) or
anchor (landscape crop), prompt/model/duration for generation, beats = length in beats of the
score, in = source in-point, speed < 1 = slow motion, place = lower-third label. Optional "frame"
/ "clip" point at existing files to skip reframing / generation.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from common import CONFIG, ROOT, out_path

STYLES = tomllib.loads((ROOT / "config" / "styles.toml").read_text())
CACHE = Path.home() / ".cache" / "video-art"
GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"


# ------------------------------------------------------------------ spec -----
class Film:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.dir = self.path.parent
        self.spec = json.loads(self.path.read_text())
        s = self.spec
        self.slug = s.get("slug") or re.sub(r"[^a-z0-9]+", "-", s["title"].lower()).strip("-")
        self.style = STYLES[s.get("style", "cinematic-warm")]
        self.aspect = s.get("aspect", "16:9")
        a, b = (int(v) for v in self.aspect.split(":"))
        self.size = (1920, 1080) if a >= b else (1080, 1920)
        self.work = self.dir / "film"
        self.media = self.dir / s.get("media", "work/media")
        self.shots = s["shots"]

    def p(self, *parts) -> Path:
        return out_path(self.work.joinpath(*parts))

    def frame(self, sh) -> Path:
        return self.dir / sh["frame"] if sh.get("frame") else self.p("frames", f"{sh['id']}.jpg")

    def clip(self, sh) -> Path:
        return self.dir / sh["clip"] if sh.get("clip") else self.p("clips", f"{sh['id']}.mp4")

    def score_file(self) -> Path:
        sc = self.spec.get("score", {})
        return self.dir / sc["file"] if sc.get("file") else self.p("score.mp3")

    def beats(self) -> dict:
        f = self.p("beats.json")
        if not f.exists():
            sys.exit("no beat map yet — run `va-film score` first")
        return json.loads(f.read_text())

    def timeline(self) -> tuple[list[tuple[float, float]], tuple[float, float] | None]:
        """Shot (start, end) times on the beat grid, plus the end card span."""
        b = self.beats()
        first, period = b["first"], b["period"]
        t = lambda k: round(first + k * period, 3)
        spans, k = [], 0
        for i, sh in enumerate(self.shots):
            start = 0.0 if i == 0 else t(k)
            k += sh["beats"]
            spans.append((start, t(k)))
        end = self.spec.get("end")
        end_span = (t(k), min(t(k + end.get("beats", 8)), b["duration"] + 0.8)) if end else None
        return spans, end_span

    def total(self) -> float:
        spans, end = self.timeline()
        return (end or spans[-1])[1]


def validate(f: Film) -> list[str]:
    errs = []
    ids = [s["id"] for s in f.shots]
    if len(set(ids)) != len(ids):
        errs.append("shot ids must be unique")
    for s in f.shots:
        if (
            not s.get("clip")
            and not s.get("frame")
            and not (f.media / s.get("photo", "")).is_file()
        ):
            errs.append(f"{s['id']}: photo not found in {f.media}")
        if not s.get("clip") and not s.get("prompt"):
            errs.append(f"{s['id']}: needs a prompt (or an existing clip)")
        if "beats" not in s:
            errs.append(f"{s['id']}: needs beats (length on the score's beat grid)")
    for ln in f.spec.get("voice", {}).get("lines", []):
        if ln.get("shot") == "end":
            if not f.spec.get("end"):
                errs.append(
                    f"voice line {ln['text'][:30]!r}: shot 'end' but the film has no end card"
                )
        elif not 0 <= ln.get("shot", -1) < len(f.shots):
            errs.append(f"voice line {ln['text'][:30]!r}: shot index out of range")
    return errs


# ------------------------------------------------------------------ plan -----
def cmd_plan(f: Film, _a) -> None:
    from PIL import Image

    from video import estimate, model_info

    for e in validate(f):
        print("✗", e)
    total, infos = 0.0, {}
    print(f"{f.spec['title']} · {f.aspect} · style {f.spec.get('style', 'cinematic-warm')}")
    print(
        f"{'shot':14s} {'photo':12s} {'orient':9s} {'reframe':9s} {'model':22s} {'sec':>3s} {'est':>6s}"
    )
    for s in f.shots:
        orient, action = "-", "existing"
        if s.get("photo") and (f.media / s["photo"]).exists():
            w, h = Image.open(f.media / s["photo"]).size
            orient = "portrait" if h > w * 1.05 else "pano" if w > 2 * h else "landscape"
            r = f.size[0] / f.size[1]
            action = "crop" if (w > h * 1.05) == (r > 1) and "band" not in s else "outpaint"
        model = CONFIG["video"].get(s.get("model", "default"), s.get("model", "default"))
        usd = 0.0
        if not s.get("clip"):
            infos.setdefault(model, model_info(model))
            usd, _ = estimate(
                infos[model], s.get("duration", 6), "1080p" if "veo" in model else "720p", False
            )
            usd = usd or 0.0
        total += usd
        print(
            f"{s['id']:14s} {s.get('photo', '-'):12s} {orient:9s} {action:9s} {model:22s} "
            f"{s.get('duration', '-')!s:>3s} {f'${usd:.2f}':>6s}"
        )
    print(f"video total ≈ ${total:.2f}  (+ outpaints ≈ $0.05 each, score $0.08, voice ≈ cents)")


# ---------------------------------------------------------------- frames -----
def cmd_frames(f: Film, a) -> None:
    from reframe import reframe

    def one(s):
        out = f.frame(s)
        if s.get("clip") or out.exists():
            return f"{s['id']}: exists"
        drift = reframe(
            f.media / s["photo"],
            out,
            f.aspect,
            tuple(s["band"]) if s.get("band") else None,
            tuple(s.get("anchor", (0.5, 0.5))),
            f.size,
        )
        return f"{s['id']}: " + (
            "cropped"
            if drift is None
            else f"outpainted, centre drift {drift:.1f}" + ("  ⚠ check seams" if drift > 30 else "")
        )

    todo = [s for s in f.shots if not a.only or s["id"] in a.only.split(",")]
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(one, todo):
            print(line)
    print(f"review: open {f.work / 'frames'}")


# ----------------------------------------------------------------- shots -----
def cmd_shots(f: Film, a) -> None:
    from video import estimate, generate, model_info
    from video import validate as check_settings

    todo = [
        s
        for s in f.shots
        if not s.get("clip")
        and not f.clip(s).exists()
        and (not a.only or s["id"] in a.only.split(","))
    ]
    if not todo:
        print("all clips exist")
        return
    total, jobs = 0.0, []
    infos = {}
    for s in todo:
        model = CONFIG["video"].get(s.get("model", "default"), s.get("model", "default"))
        info = infos.setdefault(model, model_info(model))
        res = "1080p" if "1080p" in (info.get("supported_resolutions") or []) else "720p"
        check_settings(info, s.get("duration", 6), res, f.aspect)
        usd, _ = estimate(info, s.get("duration", 6), res, False)
        total += usd or 0
        print(f"{s['id']:14s} {model:22s} {s.get('duration', 6)}s {res}  ~${usd or 0:.2f}")
        if not f.frame(s).exists():
            sys.exit(f"{s['id']}: no frame yet — run `va-film frames` first")
        jobs.append(
            SimpleNamespace(
                model=model,
                prompt=s["prompt"],
                duration=s.get("duration", 6),
                resolution=res,
                aspect=f.aspect,
                audio=False,
                first=f.frame(s),
                last=None,
                ref=[],
                out=f.clip(s),
            )
        )
    print(f"total ≈ ${total:.2f}")
    if not a.confirm:
        print("dry run — re-run with --confirm to generate")
        return
    with ThreadPoolExecutor(len(jobs)) as ex:
        for out in ex.map(generate, jobs):
            print("✓", out)


# ----------------------------------------------------------------- score -----
def cmd_score(f: Film, _a) -> None:
    from beats import analyse
    from music import lyria
    from tts import synth

    sc = f.spec.get("score", {})
    score = f.score_file()
    if not score.exists():
        score.write_bytes(lyria(sc["prompt"], sc.get("seconds", 64)))
    v = f.spec.get("voice", {})
    for i, ln in enumerate(v.get("lines", [])):
        out = f.p("vo", f"line{i}.wav")
        if not out.exists():
            synth(
                ln["text"],
                out,
                v.get("voice", CONFIG["tts"]["voice"]),
                v.get("style", CONFIG["tts"]["style"]),
            )
    r = analyse(score)
    r.pop("_x")
    f.p("beats.json").write_text(json.dumps(r, indent=1))
    print(
        f"score {r['duration']}s · ≈{r['tempo']} bpm · beat {r['period']:.3f}s · first {r['first']}s"
    )
    for s in r["sections"]:
        print(f"  section change {s['change_db']:+5.1f} dB at beat {s['beat']:3d} ({s['t']:.1f}s)")
    have = sum(s["beats"] for s in f.shots) + f.spec.get("end", {}).get("beats", 0)
    print(
        f"shots use {have} beats of {len(r['beats'])} — adjust shot 'beats' so scene changes land on sections"
    )


# ------------------------------------------------------------------- cut -----
def fonts_for(style) -> dict[str, Path]:
    out = {}
    for fam in {style["title_font"], style["text_font"]}:
        rel = STYLES["FONTS"][fam]
        dst = (
            CACHE
            / "fonts"
            / Path(rel).name.replace("%5B", "[").replace("%5D", "]").replace("%2C", ",")
        )
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"https://github.com/google/fonts/raw/main/{rel}", dst)
        out[fam] = dst
    return out


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def conform(f: Film) -> list[tuple[str, float, float]]:
    st, (w, h) = f.style, f.size
    grade = f"{st['grade']},noise=alls={st['grain']}:allf=t"
    spans, end = f.timeline()
    assets = f.p("hf", "assets", "x").parent
    placed = []
    cache_f = f.p("hf", "conform.json")
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    for s, (t0, t1) in zip(f.shots, spans):
        d = round(t1 - t0, 3)
        key = json.dumps(
            [
                str(f.clip(s)),
                f.clip(s).stat().st_mtime,
                s.get("in", 0),
                s.get("speed", 1.0),
                d,
                grade,
                w,
                h,
                st["fps"],
            ]
        )
        if cache.get(s["id"]) == key and (assets / f"{s['id']}.mp4").exists():
            placed.append((s["id"], t0, t1))
            print(f"  {s['id']:14s} {t0:6.2f}–{t1:6.2f}  (cached)")
            continue
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}"
        if s.get("speed", 1.0) != 1.0:
            vf += f",setpts=PTS/{s['speed']},minterpolate=fps={st['fps']}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"
        vf += (
            f",fps={st['fps']},{grade},trim=duration={d},setpts=PTS-STARTPTS,"
            "tpad=stop_mode=clone:stop_duration=0.125"
        )
        ff(
            "-ss",
            str(s.get("in", 0)),
            "-i",
            str(f.clip(s)),
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-crf",
            "14",
            "-preset",
            "slow",
            "-pix_fmt",
            "yuv420p",
            str(assets / f"{s['id']}.mp4"),
        )
        placed.append((s["id"], t0, t1))
        cache[s["id"]] = key
        print(f"  {s['id']:14s} {t0:6.2f}–{t1:6.2f}  speed {s.get('speed', 1.0)}")
    cache_f.write_text(json.dumps(cache, indent=1))
    if end:  # hold the film's first frame → the film loops
        d = round(end[1] - end[0], 3)
        ff(
            "-i",
            str(assets / f"{f.shots[0]['id']}.mp4"),
            "-vf",
            f"select=eq(n\\,0),loop=loop=-1:size=1,fps={st['fps']},noise=alls={st['grain']}:allf=t,"
            f"trim=duration={d},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.125",
            "-an",
            "-c:v",
            "libx264",
            "-crf",
            "14",
            "-pix_fmt",
            "yuv420p",
            str(assets / "end.mp4"),
        )
        placed.append(("end", *end))
    return placed


def overlay_html(f: Film, placed, fonts) -> str:
    st, s = f.style, f.spec
    w, h = f.size
    total = placed[-1][2]
    bar = round((h - w / st["letterbox"]) / 2) if st["letterbox"] and w > h else 0
    up = (lambda x: x.upper()) if st["title_case"] == "upper" else (lambda x: x)
    spans = {pid: (t0, t1) for pid, t0, t1 in placed}
    face = "\n".join(
        f'@font-face {{ font-family: "F{i}"; src: url("assets/fonts/{p.name}"); }}'
        for i, p in enumerate(fonts.values())
    )
    fam = {name: f'"F{i}", serif' for i, name in enumerate(fonts)}
    vids = "\n".join(
        f'<video id="v-{pid}" src="assets/{pid}.mp4" muted playsinline data-start="{t0:.3f}" '
        f'data-duration="{t1 - t0:.3f}" data-track-index="0"></video>'
        for pid, t0, t1 in placed
    )
    # place labels: merge consecutive shots with the same place
    places, cur = [], None
    for sh, (t0, t1) in zip(f.shots, [spans[x["id"]] for x in f.shots]):
        pl = tuple(sh.get("place") or ())
        if pl and cur and cur[0] == pl and abs(cur[2] - t0) < 0.01:
            cur[2] = t1
        else:
            if cur:
                places.append(cur)
            cur = [pl, t0, t1] if pl else None
    if cur:
        places.append(cur)
    place_html = "\n".join(
        f'<div class="clip place" data-start="{a + 0.3:.2f}" data-duration="{b - a - 0.7:.2f}">'
        + "".join(f"<span>{escape(x)}</span>" for x in pl)
        + "</div>"
        for pl, a, b in places
    )
    v = s.get("voice", {})
    subs = []
    for i, ln in enumerate(v.get("lines", [])):
        key = "end" if ln["shot"] == "end" else f.shots[ln["shot"]]["id"]
        t = spans[key][0] + ln.get("offset", 0.4)
        ln["_t"] = t
        if v.get("subtitles", True):
            d = wav_len(f.p("vo", f"line{i}.wav")) + 0.4
            subs.append(
                f'<div class="clip sub" data-start="{t:.2f}" data-duration="{d:.2f}"><span>'
                f"{escape(ln['text'])}</span></div>"
            )
    first_end = spans[f.shots[0]["id"]][1]
    js = [
        'tl.fromTo("#title .t", {opacity:0, scale:1.08}, {opacity:1, scale:1, duration:2.8, ease:"power2.out"}, 1.8);',
        'tl.fromTo("#title .s", {opacity:0}, {opacity:0.85, duration:1.4}, 3.0);',
        f'tl.to("#title .t, #title .s", {{opacity:0, duration:0.8, ease:"power1.in"}}, {first_end - 0.9:.2f});',
    ]
    for tr in s.get("transitions", []):
        at = spans[f.shots[tr["before"]]["id"]][0]
        el = "#flash" if tr["type"] == "flash" else "#dip"
        js.append(
            f'tl.fromTo("{el}", {{opacity:0}}, {{opacity:1, duration:0.2, ease:"power2.in"}}, {at - 0.2:.3f});'
        )
        js.append(f'tl.to("{el}", {{opacity:0, duration:0.5, ease:"power2.out"}}, {at:.3f});')
    end = s.get("end")
    end_html = ""
    if end and "end" in spans:
        e0, e1 = spans["end"]
        end_html = (
            f'<div id="endc" class="clip center endc" data-start="{e0 + 0.5:.2f}" data-duration="{e1 - e0 - 0.5:.2f}">'
            f'<div class="t">{escape(end["text"])}</div><div class="s">{escape(end.get("sub", ""))}</div></div>'
        )
        js += [
            f'tl.fromTo("#endc .t", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:1.6, ease:"power2.out"}}, {e0 + 0.5:.2f});',
            f'tl.fromTo("#endc .s", {{opacity:0}}, {{opacity:1, duration:1.2}}, {e0 + 1.7:.2f});',
            f'tl.to("#endc .t, #endc .s", {{opacity:0, duration:1.2, ease:"power1.in"}}, {e1 - 1.35:.2f});',
        ]
    tf, xf = fam[st["title_font"]], fam[st["text_font"]]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width={w}, height={h}">
<title>{escape(s["title"])}</title><script src="assets/gsap.min.js"></script>
<style>
{face}
body {{ margin:0; background:#000; }}
#root {{ position:relative; width:100%; height:100%; overflow:hidden; background:#000; color:#fff; }}
video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.bar {{ position:absolute; left:0; right:0; height:{bar}px; background:#000; z-index:5; }}
.bar.t {{ top:0; }} .bar.b {{ bottom:0; }}
.fx {{ position:absolute; inset:0; pointer-events:none; z-index:4; opacity:0; }}
#flash {{ background: radial-gradient(ellipse at 70% 40%, {st["flash"]}, rgba(0,0,0,0) 72%); mix-blend-mode:screen; }}
#dip {{ background:#000; }}
.center {{ position:absolute; inset:0; z-index:6; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }}
#title {{ background: radial-gradient(ellipse 46% 30% at 50% 50%, rgba(0,0,0,0.5), rgba(0,0,0,0)); }}
#title .t {{ font-family:{tf}; font-size:{78 if w > h else 64}px; letter-spacing:{st["title_tracking"]}; text-shadow:0 2px 30px rgba(0,0,0,.55); }}
#title .s {{ margin-top:22px; font-family:{tf}; font-size:24px; letter-spacing:0.5em; text-shadow:0 1px 12px rgba(0,0,0,.6); }}
.place {{ position:absolute; left:{120 if w > h else 70}px; top:{max(bar // 2 - 16, 60)}px; z-index:7; display:flex; gap:22px; font-family:{tf}; font-size:22px; letter-spacing:0.5em; }}
.place span + span {{ opacity:.7; letter-spacing:.2em; }}
.sub {{ position:absolute; left:0; right:0; bottom:{max(bar // 2 - 25, 90)}px; z-index:7; display:flex; justify-content:center; }}
.sub span {{ font-family:{xf}; font-size:33px; color:rgba(255,255,255,.88); text-shadow:0 1px 10px rgba(0,0,0,.6); padding:0 60px; }}
.endc .t {{ font-family:{tf}; font-size:96px; letter-spacing:0.18em; text-shadow:0 2px 34px rgba(0,0,0,.6); }}
.endc .s {{ margin-top:16px; font-family:{xf}; font-size:40px; text-shadow:0 1px 16px rgba(0,0,0,.6); }}
</style></head><body>
<div id="root" data-composition-id="film" data-start="0" data-width="{w}" data-height="{h}" data-duration="{total:.3f}">
{vids}
<div id="flash" class="fx"></div><div id="dip" class="fx"></div>
<div id="title" class="clip center" data-start="1.8" data-duration="{first_end - 1.85:.2f}"><div class="t">{escape(up(s["title"]))}</div><div class="s">{escape(up(s.get("subtitle", "")))}</div></div>
{end_html}
{place_html}
{chr(10).join(subs)}
<div class="bar t"></div><div class="bar b"></div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
document.querySelectorAll(".place, .sub").forEach((el) => {{
  const s = parseFloat(el.dataset.start), d = parseFloat(el.dataset.duration);
  tl.fromTo(el, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6 }}, s);
  tl.to(el, {{ opacity: 0, duration: 0.5 }}, s + d - 0.55);
}});
window.__timelines["film"] = tl;
</script></body></html>
"""


def wav_len(p: Path) -> float:
    return float(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(p),
            ],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    )


def hyperframes() -> list[str]:
    local = Path.cwd() / "node_modules" / ".bin" / "hyperframes"
    if shutil.which("hyperframes"):
        return ["hyperframes"]
    if local.exists():
        return [str(local)]
    return ["npx", "--yes", "hyperframes"]


def duck_score(f: Film, lines, total) -> Path:
    """Pre-shape the score: a smooth dip under every spoken line, deeper where the music is loud."""
    sr = 48000
    raw = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-i",
            str(f.score_file()),
            "-ac",
            "2",
            "-ar",
            str(sr),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
    t = np.arange(len(x)) / sr
    g = np.zeros(len(x))
    for i, ln in enumerate(lines):
        s0, d = ln["_t"], wav_len(f.p("vo", f"line{i}.wav"))
        seg = x[int(s0 * sr) : int((s0 + d) * sr)]
        loud = 20 * np.log10(np.sqrt((seg**2).mean()) + 1e-9) if len(seg) else -40
        depth = float(np.clip((loud + 20) * 0.8 + 6, 6, 14))
        a, b, r = s0 - 0.4, s0 + d + 0.3, 0.4
        w = np.clip((t - a) / r, 0, 1) * np.clip((b + r - t) / r, 0, 1)
        g = np.minimum(g, -depth * w * w * (3 - 2 * w))
    y = (x * (10 ** (g / 20))[:, None]).astype(np.float32)
    out = f.p("score-ducked.wav")
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
            "2",
            "-i",
            "-",
            "-t",
            f"{total:.3f}",
            str(out),
        ],
        input=y.tobytes(),
        check=True,
    )
    return out


def master(src: Path, out: Path, target: float) -> tuple[float, float]:
    """Gain to the loudness target + true-peak limiter; returns (LUFS, true peak dB)."""

    def measure(p):
        o = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                str(p),
                "-af",
                "ebur128=peak=true",
                "-vn",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        ).stderr
        return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1]), float(
            re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)[-1]
        )

    lufs, _ = measure(src)
    gain, limit = target - lufs, 0.84
    for _ in range(5):  # converge on the target; tighten the ceiling only if true peak > -1 dB
        ff(
            "-i",
            str(src),
            "-c:v",
            "copy",
            "-af",
            f"volume={gain:.2f}dB,alimiter=limit={limit:.3f}:attack=3:release=80:level=false,aresample=48000",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
            str(out),
        )
        lufs, peak = measure(out)
        if peak > -1.0:
            limit *= 10 ** ((-1.3 - peak) / 20)
        elif abs(lufs - target) <= 0.5:
            break
        else:
            gain += target - lufs
    return lufs, peak


def cmd_cut(f: Film, _a) -> None:
    from assemble import build
    from critic import measure

    for e in validate(f):
        sys.exit(f"✗ {e}")
    print("conform + grade")
    placed = conform(f)
    total = placed[-1][2]
    hf = f.p("hf", "index.html").parent
    assets = hf / "assets"
    (assets / "fonts").mkdir(exist_ok=True)
    fonts = fonts_for(f.style)
    for p in fonts.values():
        shutil.copy2(p, assets / "fonts" / p.name)
    gsap = CACHE / "gsap.min.js"
    if not gsap.exists():
        urllib.request.urlretrieve(GSAP_URL, gsap)
    shutil.copy2(gsap, assets / "gsap.min.js")
    (hf / "index.html").write_text(overlay_html(f, placed, fonts))
    env = {"HYPERFRAMES_SKIP_SKILLS": "1", "PATH": __import__("os").environ["PATH"]}
    lint = subprocess.run(
        [*hyperframes(), "lint"], cwd=hf, capture_output=True, text=True, env=env, check=False
    )
    if " 0 error" not in lint.stdout + lint.stderr:
        sys.exit(f"overlay lint failed:\n{lint.stdout[-2000:]}")
    print("render picture (HyperFrames)")
    r = subprocess.run(
        [
            *hyperframes(),
            "render",
            "--quality",
            "delivery",
            "--fps",
            str(f.style["fps"]),
            "--output",
            str(f.p("picture.mp4")),
        ],
        cwd=hf,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode:
        sys.exit(f"render failed:\n{(r.stdout + r.stderr)[-3000:]}")
    print("voice + ducked score + mix")
    lines = f.spec.get("voice", {}).get("lines", [])
    edit = {
        "fps": f.style["fps"],
        "size": list(f.size),
        "shots": [{"src": "picture.mp4", "dur": total}],
    }
    if lines:
        ins, flt = [], []
        for i, ln in enumerate(lines):
            ins += ["-i", str(f.p("vo", f"line{i}.wav"))]
            flt.append(f"[{i}:a]aresample=48000,adelay={int(ln['_t'] * 1000)}[a{i}]")
        mix = (
            "".join(f"[a{i}]" for i in range(len(lines)))
            + f"amix=inputs={len(lines)}:normalize=0,apad"
        )
        ff(
            *ins,
            "-filter_complex",
            ";".join(flt) + ";" + mix + "[o]",
            "-map",
            "[o]",
            "-t",
            f"{total:.3f}",
            "-ac",
            "1",
            "-ar",
            "48000",
            str(f.p("voice.wav")),
        )
        edit["narration"] = "voice.wav"
    edit["music"] = duck_score(f, lines, total).name
    edit["music_db"] = -2
    build(edit, f.work, f.p("mix.mp4"))
    out = f.p("out", f"{f.slug}.mp4")
    lufs, peak = master(f.p("mix.mp4"), out, f.spec.get("loudness", -14))
    m = measure(out, None, 1.8, out.with_suffix(".critic"))
    print(
        f"\n{out}\n{total:.1f}s · {lufs:.1f} LUFS · true peak {peak:.1f} dB · "
        f"black {m['black_segments']} · contact sheet {out.with_suffix('.critic')}/contact.jpg"
    )
    if lines:
        from captions import transcribe

        heard = " ".join(w["word"] for w in transcribe(out))
        print(f"heard: {heard}\nwanted: {' / '.join(ln['text'] for ln in lines)}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("cmd", choices=["plan", "frames", "shots", "score", "cut"])
    ap.add_argument("film", type=Path)
    ap.add_argument("--confirm", action="store_true", help="shots: actually spend money")
    ap.add_argument("--only", help="comma-separated shot ids")
    a = ap.parse_args()
    f = Film(a.film)
    {
        "plan": cmd_plan,
        "frames": cmd_frames,
        "shots": cmd_shots,
        "score": cmd_score,
        "cut": cmd_cut,
    }[a.cmd](f, a)


if __name__ == "__main__":
    main()
