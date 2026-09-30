# Learnings from building the "Slowing Time" showcase → plugin improvements

Status: `[x]` already applied · `[ ]` to apply after the pilot chapter validates the approach.

## Guardrails & tools
- [x] `va-video` validates resolution / aspect / duration against the live model list before spending
      (Seedance 2.5 is 480p/720p only; Veo 3.1 takes only 4/6/8 s). Default resolution now 720p.
- [ ] `va-tts`: on 429, back off and retry; on a free-tier daily cap, stop with a plain explanation
      (Gemini free tier = 10 TTS requests/day; a 6-minute film needs ~35 takes). `va-doctor`/setup should warn.
- [ ] `va-music`: Lyria Pro returns ~127 s max. For longer beds, generate per section and crossfade;
      add a `va-music --sections` helper or document the pattern in the skills.
- [x] New `va-photos` tool: bake EXIF rotation, convert to sRGB, **strip EXIF/GPS**, stable ids,
      manifest with captions, numbered contact sheets per folder. (Done ad hoc in work/normalize.py + sheets.py.)
- [x] `va-captions --script`: align whisper word timings to the known script so proper nouns
      (Gotokuji, Setagaya, Kamogawa) are spelled right; whisper base.en mangles them.
- [ ] `va-critic`: per-chapter contact sheets; `judge()` still needs the user's thresholds.

## Workflow / skills
- [x] Narration per paragraph, not per chapter: exact timing control, and the silence between
      paragraphs becomes an editing tool (here: pauses lengthen as the trip slows).
- [ ] Personal photo stories: narrator is the author (first person, their sentences kept) — the
      "university professor" rule is for explainers only. Put this in photo-motion / video-director.
- [ ] Portrait-heavy sets in 16:9: portrait pages with typographic captions + diptychs/triptychs
      beat blurred-background fills. Keep photos ≤ native size (phone exports are often 1600 px).
- [ ] Package the data-driven HyperFrames photo-story generator (edit spec → one composition per
      chapter → silent renders → assemble with narration + ducked music) as `templates/photo-story/`. (The *cinematic* pipeline was packaged as `va-film`; the paper-journal
      slideshow generator is still project-local in projects/japan-trip/work/build.py.)
- [x] macOS privacy (TCC) blocks Claude Code from ~/Documents, ~/Desktop, ~/Pictures unless the terminal
      has access: setup + photo-motion should say "copy into projects/<slug>/source or grant access".

## Install / repo hygiene
- [x] `/video-art:new` writes a `.gitignore` for `projects/*/source/`, `work/`, renders — personal photos
      must never be committed by accident. (Applied in this repo's .gitignore.)
- [ ] Setup: mention Gemini billing (Tier 1) for anything longer than a short test.
- [x] `bunx skills add ... --all` sprays ~40 agent folders — setup uses `-a claude-code`.

## Round 2 — from the cinematic cut (applied in v0.2.0)
- [x] `va-ingest` (was `va-photos`): folder → clean media (GPS stripped), captions, text, contact sheets, project .gitignore
- [x] `va-reframe`: crop when orientation matches, else keep a band + outpaint sides + paste original back; drift metric
- [x] `va-beats`: sub-frame tempo, octave check (60 vs 120 bpm), window-latency phase fix, silence-safe sections
- [x] `va-film`: one film.json → plan (cost) · frames · shots (dry-run/--confirm, parallel) · score · cut
      (conform cache, style grade, HyperFrames overlay, looping end card, pre-ducked score, converging −14 LUFS master)
- [x] `config/styles.toml`: 5 videography presets; OFL fonts fetched on first use
- [x] `skills/film`: analysis → 2-round wizard → storyboard gate → test-shot gate → edit on sections
- Notes: Veo 3.1 / Fast do 1080p (Seedance 2.5 is 720p); crop the band before outpainting; use only the
  clean first seconds of a clip when the model invents text; faces: identity holds, expressions drift.
- [ ] Open: `judge()` thresholds in critic still user-owned; per-shot face similarity score; 9:16 layout pass.
