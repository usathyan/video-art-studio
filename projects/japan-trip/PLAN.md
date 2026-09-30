# Slowing Time — showcase film (plan & progress)

Source: `source/Substack-Package/` (post + 125 photos by the user; personal — git-ignored).
Working files: `work/` (git-ignored). Showcase deliverables → `docs/showcase/` (small, EXIF-free).

## Concept
The film's tempo *is* the story: Tokyo cuts quickly (parade shots ~1s), Kyoto holds long,
the goodbye nearly stops. The father narrates in first person, condensed from his own post
(his sentences kept wherever possible; no facts added). Look = the Substack journal:
warm paper ground, serif type, photos framed at ~native size, captions from captions.txt
set as typography, chapter cards "Day N · title". Opens on the torii tunnel (00-01) and
ends on it again, so the film loops.

## Constraints (from review)
- 1600px long edge → landscapes framed ≤ native size; full-bleed only for a few, gentle zoom
- 61 portraits → framed pages / diptychs, never cropped through heads
- every one of the 125 photo ids must appear (generator asserts)
- fonts local via @font-face (serif + Noto Serif JP subset for 山頂 / また来ます)
- TTS per chapter; shot timing from measured VO durations
- captions: whisper timings + script words (alignment); clean + captioned versions
- AI motion only after animatic approval + stated total; no people; check aspect support
- commit: poster + ≤25MB trailer only; ask user about public/private

## Progress
- [x] Read post, viewed all 125 photos (contact sheets in work/sheets)
- [x] .gitignore source/work/hf; normalize photos → work/photos (sRGB, rotated, EXIF stripped) + photos.json
- [x] Probe: Lyria Pro ≈127 s max; Seedance 2.5 = 480p/720p only, all aspects; Veo 4/6/8 s
- [x] Fonts: Shippori Mincho (titles + Japanese) + EB Garamond (captions), local @font-face
- [x] Narration script (script.md) — 993 words, first person, his sentences
- [x] TTS per paragraph (34 takes, Gemini Charon) — needed Gemini billing (free tier = 10/day)
- [x] Generator work/build.py → 12 HyperFrames chapters; pilot Day 5 verified; all 125 ids asserted
- [x] Score: 8 Lyria cues ($0.64 incl. probe) crossfaded per act → audio/music-bed.wav
- [x] Rough cut work/renders/rough-cut.mp4 (10:47, -17.9 LUFS, script-aligned captions ok)
- [ ] **Waiting:** review with user (runtime, voice, look, AI shots + cost, public/private)
- [ ] AI hero shots (approved) → final master + captioned + trailer + poster
- [ ] README showcase section; commit on approval

## Proposed AI motion (not generated — needs approval), Seedance 2.5, 720p, no people
| photo | shot | aspect | secs | est |
|---|---|---|---|---|
| 07-07 | bamboo sways, seamless loop (first = last frame) | 9:16 | 10 | $2.31 |
| 05-06 | slow push into the torii tunnel | 9:16 | 6 | $1.39 |
| 04-05 | Japan rolling past the Shinkansen window | 9:16 | 8 | $1.85 |
| 05-15 | Shirakawa canal: water shimmer, leaves stir, loop | 9:16 | 6 | $1.39 |
| 06-04 | Shimogamo torii: trees sway, light shifts, loop | 16:9 | 6 | $1.39 |
Total ≈ $8.33. Spend so far: Lyria $0.64 + Lyria test clip $0.04 + TTS (Gemini billing, cents).

## Cinematic cut (DESIGN.md) — status 2026-09-30
- [x] Reframed 5 portraits to 16:9 (Gemini 3 Pro Image outpaint + original pasted back), cropped 4 landscapes
- [x] 9 AI shots, Veo 3.1 / Veo 3.1 Fast @1080p — $7.40 (test $2.20 + batch $5.20)
- [x] Lyria score with arc ($0.08), beat grid 0.952 s; 5 Charon lines; score pre-ducked under each line
- [x] Conform/grade (ffmpeg), HyperFrames overlay (letterbox, title, places, subtitles, flash, dip, loop end)
- [x] out/slowing-time-60s.mp4 — 63.5 s, 1080p24, −14.9 LUFS, −1.6 dBTP; out/poster.jpg
- [x] User approved the film ("keep it"); showcase + wizard committed in v0.2.0
