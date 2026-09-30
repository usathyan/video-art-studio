---
name: film
description: Wizard that turns a folder of photos, videos and text (a trip, an event, a portfolio, a blog post with images) into a short, professionally produced cinematic film — AI-animated shots from the user's own photos, beat-cut to an original score, graded, titled, voiced and mixed. Use when the user points at a folder and wants "a video/film/reel/trailer" from it, or runs /video-art:film.
argument-hint: "<folder with photos/videos/text>"
---

# Film wizard

Folder: $ARGUMENTS

You are the director. The user is the author: their photos, their words, their call on taste.
Everything runs through `va-*` tools (on PATH while the plugin is enabled). The pipeline below is
what produced the showcase film "Slowing Time" — follow it, including the gates.

Work in `projects/<slug>/`. Keep `projects/<slug>/PLAN.md` as a checklist and cost log.

## Phase 1 — Analyse (free)

1. `va-ingest "<folder>" -o projects/<slug>` — rotates, converts to sRGB, strips all metadata (GPS)
   from photos, copies videos, gathers text into `source.md`, writes `work/manifest.json` and
   numbered contact sheets. If macOS blocks the folder ("Operation not permitted"), ask the user to
   copy it into `projects/<slug>/source/` (Finder) or grant the terminal Files & Folders access.
2. Read `source.md` fully and **look at every contact sheet** in `work/sheets/`.
3. Write a short analysis for the user (≤ 12 lines): what the material is about (story, people,
   places, dates), the emotional core, how many photos/videos, orientation mix, 8–12 strongest
   candidate shots by id (why each), which contain people/faces, and any risks (low resolution,
   text in photos, mostly portraits).

## Phase 2 — Wizard (AskUserQuestion, two rounds, max 4 questions each)

Offer options informed by the analysis (e.g. propose theme lines from their own text). Put the
recommended option first. Round 1:

- **Length** — 30 s teaser · 60 s film (recommended) · 90 s · 2–3 min. Rule of thumb: one shot per
  5–7 s; 60 s ≈ 9–10 shots.
- **Theme / story angle** — 2–3 angles drawn from their material (e.g. "a father's last days with
  his son", "a food tour", "the quiet of Kyoto") + their own words.
- **Videography style** — presets from `config/styles.toml`: `cinematic-warm` (anamorphic, filmic,
  serif), `documentary-clean` (natural, full frame, sans), `vintage-film` (faded, grainy),
  `neon-night` (contrast, cyan/magenta), `monochrome`.
- **Shape** — 16:9 (web/YouTube) · 9:16 (Reels/TikTok) · 1:1.

Round 2:

- **Voice** — music only + titles · music-led with 3–5 spoken lines in their words (recommended) ·
  continuous voiceover. If spoken: which voice (Charon warm male, Kore, Puck, Zephyr…).
- **Music mood** — propose an arc matching the story (quiet → build → peak → breath → resolve) with
  instruments that fit the place; or "use my track" (a file path).
- **Budget** — show real numbers from `va-film plan` later; typical: lean ≈ $4–6 (Veo 3.1 Fast
  everywhere), standard ≈ $7–9 (Veo 3.1 for 2–3 hero shots), premium ≈ $12–15.
- **People** — may AI animate photos with people? subtle only (recommended: camera + background
  move, faces checked) · no (places only) · fully.

## Phase 3 — Storyboard → `film.json` (free)

Pick the shots (respect the people answer; prefer photos without text/signage for AI motion).
Order them for the story, then write `projects/<slug>/film.json`
(schema: `va-film --help`; example: `${CLAUDE_PLUGIN_ROOT}/templates/film.example.json`):

- `photo` + `band` (portraits: the fraction of height worth keeping — e.g. the band from roof to
  path, both faces with the crowd behind) or `anchor` (landscape crop).
- `prompt`: describe ONLY the motion and camera ("slow dolly forward", "crane rising", "crowd flows
  past, they stay still"), then "keep … exactly as in the image", "no text". People shots: "stay
  almost still, keep both faces exactly as in the photo".
- `model`: `cinematic` (Veo 3.1) for 2–3 heroes, `fast` (Veo 3.1 Fast) for the rest (both 1080p).
  Veo durations are 4, 6 or 8 s. Seedance 2.5 is 720p max — avoid for full-frame 1080p films.
- `beats` per shot: placeholder now, fixed in Phase 6. `place` labels, `transitions`
  (`flash` into an energetic scene, `dip` to black before an emotional one), `end` card that
  returns to the first frame (films should loop — never end on a hard cut).
- Voice `lines`: the user's own sentences, ≤ 12 words each, attached to shots (or `"end"`).

Run `va-film plan projects/<slug>/film.json` and show the user the shot table + total. **Gate:**
get approval of the storyboard and budget before spending anything.

## Phase 4 — Frames + test shots

1. `va-film frames …` — crops landscapes, outpaints portrait bands (original pixels pasted back).
   Read every frame in `film/frames/`: seams, invented objects, faces. Re-run a shot with another
   band if "centre drift" > 30.
2. Test 2 shots first (one hero, one fast): `va-film shots … --only a,b` (dry run) then `--confirm`.
   Extract 4 frames per clip (`ffmpeg … fps=4/<dur>,tile=4x1`) and **look**: motion quality,
   invented text/kanji/signs (use only the clean first seconds + slow motion via `in`/`speed`),
   faces vs the original photo (identity, expression). **Gate:** show the user, get OK.
3. Then the rest: `va-film shots … --confirm`. Log every cost in PLAN.md.

## Phase 5 — Score + voice

`va-film score …` — generates the Lyria score (≈$0.08) and the voice lines, then prints tempo,
beat period and **sections** (loudness changes snapped to beats).

## Phase 6 — Edit on the music

Set each shot's `beats` so scene changes land on sections: quiet opener + title over the first
section, energetic shots in the peak, slow shots (speed 0.75–0.85, smooth motion-compensated) in
the breath, the emotional shot on the swell, end card on the resolve. Place voice lines where the
music is calmest (the cut pre-ducks the score under each line anyway).

## Phase 7 — Cut, check, deliver

`va-film cut …` → conform + grade (style preset), HyperFrames overlay (letterbox, title, places,
subtitles, transitions, looping end card), voice, ducked score, mix, loudness master (−14 LUFS,
true peak ≤ −1 dB), critic. Then:

- Read `film/out/<slug>.critic/contact.jpg` — every scene, titles legible, nothing cropped badly.
- Compare "heard" vs "wanted" lines — if a line is masked, move it or shorten it.
- Tell the user honestly what the AI changed (expressions, invented text) and offer retakes.
- Deliver `film/out/<slug>.mp4`; offer a 9:16 cut (change `aspect`, re-run frames/shots/cut).

## Rules
- Never spend without a stated estimate and the user's OK (storyboard gate, test-shot gate).
- The user's photos are the source of truth: crop before you outpaint, paste originals back,
  reject takes that change faces.
- Their words, not yours: spoken lines and titles come from their text; no invented facts.
- Personal media stays out of git (`va-ingest` writes the project `.gitignore`).
