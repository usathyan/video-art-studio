# Slowing Time — cinematic cut (design, approved 2026-09-30)

Replaces the 10:47 slideshow rough cut (kept in work/renders/rough-cut.mp4 as the long version).

## Brief
~60 s, 16:9, 9 AI-animated shots from the user's own photos + a looping end card. Music-led,
4 spoken lines in his words. Stylish, professionally produced — explicitly *not* a slideshow.
Budget $6–9. People (father, son) may move only subtly; faces must match the photos.

## Shots (≈ timings; final cuts snap to the score's beats)
| # | t | photo | move | model | voice |
|---|---|---|---|---|---|
| 1 | 0–6 | 05-06 torii tunnel | slow push through the gates; title resolves | Veo 3.1, 8 s | "In Japan, people take time." |
| 2 | 6–11 | 01-09 crossing | high angle, crowd moving silently | Veo 3.1 Fast, 6 s | |
| 3 | 11–16 | 03-01 lucky cats | lateral glide along the rows | Veo 3.1 Fast, 6 s | |
| 4 | 16–21 | 03-19 samba dancer | energy peak on the drop | Veo 3.1 Fast, 6 s | |
| 5 | 21–27 | 04-05 Shinkansen window | fields rush past; match-cut to Kyoto | Veo 3.1 Fast, 6 s | "These were the last few days of Ajay under my wing." |
| 6 | 27–34 | 07-07 bamboo | camera rises; music near silence | Veo 3.1, 8 s | "You want those days to go slow. Japan obliged." |
| 7 | 34–40 | 05-15 Shirakawa canal | night, gold on water | Veo 3.1 Fast, 6 s | |
| 8 | 40–46 | 08-01 Shinsekai neon | quick lift, full volume | Veo 3.1 Fast, 6 s | |
| 9 | 46–56 | 09-03 father & son, Akihabara | crowd moves behind them, slow push-in | Veo 3.1, 8 s | "Then the real goodbye, at Tokyo Station." |
| end | 56–62 | shot 1's first frame | また来ます · I'll be back — loops | still + type | "Mata kimasu. I'll be back." |

## Look
Full-bleed, 2.39:1 letterbox, 24 fps. One grade for all clips (warm highlights, cool deep shadows,
soft contrast, fine grain, light vignette). Type: Shippori Mincho, white, wide tracking — title,
place lower-thirds (TOKYO 東京 / KYOTO 京都 / OSAKA 大阪), spoken lines as understated subtitles.
Mostly beat-synced hard cuts; one motion match-cut, one light-leak into Osaka, dip to black before
the goodbye; last frame = first frame.

## Sound
One Lyria Pro cue with an arc (quiet → Tokyo build → parade peak → bamboo near-silence → Osaka
swell → piano resolve). Beat grid drives cut points. 4 new Charon takes, music ducked under them.
Master −14 LUFS.

## Pipeline & guardrails
1. Reframe portraits to 16:9 with Gemini 3 Pro Image (outpaint), then paste the original photo back
   over the centre so the user's pixels are exact; check the seam.
2. Image-to-video at 1080p, no model audio. Dry-run cost before every call; 2-shot test first.
3. People shots: compare faces (first/mid/last frame vs original); reject drifted takes.
4. HyperFrames overlay for type/letterbox/transitions; ffmpeg grade + assemble + mix.
Deliverables: `out/slowing-time-60s.mp4`, poster frame, README showcase (on approval).
