---
name: video-director
description: Use when the user asks for a narrated/explainer/documentary-style video, or a video mixing generated imagery, AI video shots and motion graphics. Orchestrates brief → script → storyboard → keyframes → animatic → approval → generation → assembly → captions → critic, using this repo's tools/ and the HyperFrames skills.
---

# Video Director

You are directing a short film. Work in `projects/<slug>/`. Keep a `projects/<slug>/PLAN.md` checklist
and update it as stages complete (survives context clears).

## 0. Brief (required before anything else)
Read or create `projects/<slug>/brief.md` from `${CLAUDE_PLUGIN_ROOT}/templates/brief.md`. It must pin down:
**what** (subject, message), **aspect ratio**, **length**, **style**, **roles** (which tool makes what).
If any is missing, ask once — all missing items in one question.

## 1. Script — `script.md`
- Narrate like a university professor who loves the subject: full, flowing sentences with
  subordinate clauses; concrete images over statistics; one idea per paragraph.
- **Avoid Claudisms**: no strings of short punchy fragments ("Fast. Cheap. Everywhere."), no
  "It's not X, it's Y", no stacked numbers/percentages, no "Let's dive in", no rhetorical
  question openers, no triplet lists as rhythm crutch. At most one number per scene.
- Budget ~150 spoken words per minute. Verify facts/dates; mark uncertain ones and check them.
- Mark per-line delivery with `{style: ...}` and inline Gemini tags (`<short pause>`, `<sigh>`).

## 2. Storyboard — `shots.md`
Table: `# | t_start | dur | narration line | visual | source`, where source ∈
`hf` (HyperFrames motion graphic/typography), `kf` (generated still + Ken Burns),
`vid` (AI video from keyframe), `clip` (CC footage via va-clips), `gen-art` (see generative-art skill).
Default to `hf`/`kf`; reserve `vid` for shots where motion *is* the point (Seedance for motion,
Veo for cinematic realism). No text inside generated images — all type is animated in HyperFrames.

## 3. Look & references
Generate ONE style/hero frame first (`va-image`), get approval, save to `refs/style.png`.
Pass `--ref refs/style.png` (plus character refs) to **every** later keyframe for consistency.

## 4. Voice
`va-tts` per line → `gen/vo/NN.wav`, then concat to `gen/vo.wav`
(`ffmpeg -f concat`). Re-time `shots.md` to the real VO durations.

## 5. Animatic (cheap, mandatory before paid video)
Keyframes as Ken Burns stills + HyperFrames graphics + VO → `va-assemble` → `out/animatic.mp4`.
Run the critic. Show the user. **Do not generate `vid` shots until the animatic is approved.**

## 6. Generation
`va-video ... --first gen/kfNN.png` — dry-run first, total the estimated cost for all
shots, tell the user the total, then re-run with `--confirm`. For a seamless loop, give the final
shot `--last` = the opening keyframe.

## 7. Music
`va-music "<mood, instrumentation, bpm>" --seconds <len>` (Lyria via OpenRouter: $0.04 ≤30s, $0.08 longer;
`--provider elevenlabs` if the user has a paid ElevenLabs plan). Instrumental only.

## 8. Assemble → captions → critic
`edit.json` → `va-assemble` → `va-captions` → `va-critic --script script.md`.
Read `contact.jpg` yourself and look for: style drift between shots, text in AI images,
awkward crops, dead frames. Fix and re-run until the critic passes and you'd defend every shot.
Credit any CC clips from `ATTRIBUTION.md` in an end card or description.

## Rules from practice
- Never end on a hard cut; loopable pieces end on the opening frame.
- ffmpeg does the heavy lifting; OTIO (`final.otio`) is only for hand-off to an NLE.
- Log every paid call's cost in `PLAN.md`.
