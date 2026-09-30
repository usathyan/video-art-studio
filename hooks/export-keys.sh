#!/usr/bin/env bash
# Makes keys entered in the plugin's config dialog visible to the va-* tools.
# Keys already present in the environment are left alone.
[ -n "${CLAUDE_ENV_FILE:-}" ] || exit 0
put() { [ -n "$2" ] && [ -z "${!1:-}" ] && printf 'export %s=%q\n' "$1" "$2" >> "$CLAUDE_ENV_FILE"; }
put OPENROUTER_API_KEY "${CLAUDE_PLUGIN_OPTION_OPENROUTER_API_KEY:-}"
put GEMINI_API_KEY     "${CLAUDE_PLUGIN_OPTION_GEMINI_API_KEY:-}"
put ELEVENLABS_API_KEY "${CLAUDE_PLUGIN_OPTION_ELEVENLABS_API_KEY:-}"
exit 0
