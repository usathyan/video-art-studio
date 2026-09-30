---
name: new
description: Start a new video piece — asks a few friendly questions, writes the brief, and hands off to the right workflow (explainer, photo story, or generative loop).
argument-hint: "[idea or path to photos]"
---

# New piece

The user's idea (may be empty): $ARGUMENTS

1. If the idea is empty, ask what they want to make. Otherwise infer as much as you can.
2. Ask the remaining questions in ONE message with AskUserQuestion (max 4):
   - **Kind:** story/explainer with narration · my photos brought to life · abstract generative loop
   - **Shape:** 16:9 (YouTube/web) · 9:16 (Reels/TikTok) · 4:5 (Instagram) · 1:1
   - **Length:** 15s · 30s · 60s · longer
   - **Look / budget:** free only · up to ~$5 of AI motion · up to ~$20
3. Make `projects/<short-slug>/`, fill `brief.md` from `${CLAUDE_PLUGIN_ROOT}/templates/brief.md`
   with their answers plus a proposed style line, and show it to them in a few lines.
4. Hand off: narration → `video-art:video-director`; their photos → `video-art:photo-motion`;
   abstract → `video-art:generative-art`.
