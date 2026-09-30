# art — development repo for the **video-art** Claude Code plugin

This repo *is* the plugin (and its own marketplace). User-facing behavior lives in `skills/`,
not here — this file is only for working on the plugin itself.

## Layout
- `.claude-plugin/plugin.json` manifest · `marketplace.json`
- API keys: `~/.config/video-art/.env` only (tools/common.py loads it; `va-keys` manages it)
- `skills/{film,video-director,photo-motion,generative-art,new,setup}/SKILL.md` — `film` is the folder→film wizard
- `bin/va-*` → `bin/_va_run` → `tools/<name>.py` via `uv run` (venv in `~/.cache/video-art/venv`)
- `config/models.toml` — the only place model IDs live (`make models` lists live IDs)
- `config/styles.toml` — videography presets used by `va-film` (grade, grain, letterbox, fonts)
- `templates/film.example.json` — full film spec; `projects/japan-trip/film.json` rebuilds the showcase
- `.claude/skills/` — HyperFrames skills installed for *this* folder (third-party, git-ignored)
- `projects/` — test pieces; `gen/` and `out/` are git-ignored

## Working rules
- Test changes with `claude --plugin-dir .` or `make smoke`; validate with `claude plugin validate .`
- Never run `va-video --confirm` in tests — video generation is billed per second.
- Keep skill text in plain language: the audience is artists and photographers.
- Record new sources/decisions in `docs/research.md`.
- Bump `version` in `plugin.json` for each release.
