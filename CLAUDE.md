# art — development repo for the **video-art** Claude Code plugin

This repo *is* the plugin (and its own marketplace). User-facing behavior lives in `skills/`,
not here — this file is only for working on the plugin itself.

## Layout
- `.claude-plugin/plugin.json` manifest (+ `userConfig` API keys) · `marketplace.json`
- `skills/{video-director,photo-motion,generative-art,new,setup}/SKILL.md`
- `bin/va-*` → `bin/_va_run` → `tools/<name>.py` via `uv run` (venv in `~/.cache/video-art/venv`)
- `hooks/export-keys.sh` — SessionStart: userConfig keys → `CLAUDE_ENV_FILE`
- `config/models.toml` — the only place model IDs live (`make models` lists live IDs)
- `.claude/skills/` — HyperFrames skills installed for *this* folder (third-party, git-ignored)
- `projects/` — test pieces; `gen/` and `out/` are git-ignored

## Working rules
- Test changes with `claude --plugin-dir .` or `make smoke`; validate with `claude plugin validate .`
- Never run `va-video --confirm` in tests — video generation is billed per second.
- Keep skill text in plain language: the audience is artists and photographers.
- Record new sources/decisions in `docs/research.md`.
- Bump `version` in `plugin.json` for each release.
