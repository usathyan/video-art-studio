.PHONY: help venv install clean test lint format run models smoke critic

help:  ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

venv:  ## create python venv
	uv venv

install: venv  ## install python + bun deps, check toolchain
	uv sync
	bun install
	bunx hyperframes doctor || true

clean:  ## remove caches and smoke-test output
	rm -rf .ruff_cache .pytest_cache tools/__pycache__ projects/_smoke/gen projects/_smoke/out

test:  ## run unit tests
	uv run pytest -q

lint:  ## ruff check
	uv run ruff check tools tests

format:  ## ruff format
	uv run ruff format tools tests

run:  ## open Claude Code here with this plugin loaded from source
	claude --plugin-dir .

models:  ## list live image/video/TTS model ids to update config/models.toml
	@curl -s https://openrouter.ai/api/v1/videos/models -H "Authorization: Bearer $$OPENROUTER_API_KEY" | python3 -c "import sys,json;[print('video', m['id']) for m in json.load(sys.stdin)['data']]"
	@curl -s https://openrouter.ai/api/v1/models | python3 -c "import sys,json;[print('image', m['id']) for m in json.load(sys.stdin)['data'] if 'image' in m['architecture']['output_modalities']]"
	@curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$$GEMINI_API_KEY&pageSize=200" | python3 -c "import sys,json;[print('tts  ', m['name'][7:]) for m in json.load(sys.stdin)['models'] if 'tts' in m['name']]"

smoke:  ## free-ish end-to-end check: 1 image, 1 TTS line, assemble, captions, critic
	./scripts/smoke.sh

critic:  ## make critic V=path/to.mp4 [S=script.md]
	uv run tools/critic.py $(V) $(if $(S),--script $(S))
