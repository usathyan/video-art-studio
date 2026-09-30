---
name: new
description: Start a new video piece — asks a few friendly questions and hands off to the right workflow (cinematic film from a folder, narrated explainer, photo story, or generative loop).
argument-hint: "[idea or path to a folder]"
---

# New piece

The user's idea (may be empty): $ARGUMENTS

1. If they gave a folder of photos/videos/text (or want "a film/trailer/reel of my trip/event"),
   hand off to `video-art:film` with that folder — it analyses the material and runs the wizard.
2. Otherwise ask what they want to make (one AskUserQuestion, max 4 questions: kind, shape, length,
   budget), write `projects/<slug>/brief.md` from `${CLAUDE_PLUGIN_ROOT}/templates/brief.md`, and
   hand off: cinematic film from photos → `video-art:film`; narrated explainer →
   `video-art:video-director`; a gentle photo story / living photos → `video-art:photo-motion`;
   abstract → `video-art:generative-art`.
