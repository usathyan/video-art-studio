# Film wizard — turn the "Slowing Time" workflow into a plugin feature (2026-09-30)

Goal: `/video-art:film <folder>` → analyze a folder of photos/videos/text → wizard (length, theme,
videography style, voice, music, budget, faces) → storyboard → test shots → full generation →
beat-cut, graded, titled, mixed film. Everything we did by hand for the showcase becomes tools.

## What the showcase taught us (and what each becomes)
| Manual step in the showcase | Becomes |
|---|---|
| normalize.py + sheets.py (rotate, sRGB, strip GPS, captions, contact sheets) | `va-ingest` |
| reframe.py (crop band → outpaint sides → paste original back → drift check) | `va-reframe` |
| numpy beat grid + section analysis | `va-beats` |
| edit.py conform/grade/overlay + hand-ducked score + two-step loudness | `va-film` (plan / shots / score / cut) driven by one `film.json` |
| grade chain, letterbox, fonts, transitions chosen ad hoc | `config/styles.toml` presets |
| questions asked one by one in chat | `skills/film` wizard (AskUserQuestion rounds) |

## Tasks
- [x] Plan (this file)
- [x] `va-ingest` + tests
- [x] `va-reframe` + tests (paste-back / band math, no API)
- [x] `va-beats` + tests (synthetic click track)
- [x] `config/styles.toml` (5 presets)
- [x] `va-film` plan/shots/score/cut + tests (timing, style, spec validation)
- [x] Rebuild the showcase from `film.json` with `va-film cut` using existing clips (no new spend)
- [x] `skills/film/SKILL.md` wizard; route `new` to it; update setup/doctor
- [x] README: guide ("make a film from a folder") + showcase result (poster + compressed clip)
- [x] Update learnings doc, bump version 0.2.0, validate, lint, test
- [x] Commit + push
