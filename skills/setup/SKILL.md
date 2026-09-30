---
name: setup
description: Set up Video Art Studio on this computer and in the current folder — installs missing tools, checks API keys, adds the HyperFrames motion-graphics skills to the project, and runs a tiny test video. Use on first run or when a va-* command fails for a missing dependency or key.
---

# Video Art Studio setup

Talk to the user in plain language — assume they are an artist, not a programmer.
Explain each install in one short sentence before running it.

1. Run `va-doctor` and show the result.
2. For each ✗ tool, offer to install it with Homebrew (macOS). If `brew` itself is missing,
   give them the one-line installer from https://brew.sh and stop until they've run it.
   Everything together: `brew install uv ffmpeg ffmpeg-full whisper-cpp yt-dlp node`.
   (`ffmpeg-full` sits alongside the normal ffmpeg; it's only used to draw captions.)
3. API keys — they live in ONE private file, `~/.config/video-art/.env`, read by every tool in the
   terminal, the desktop app and IDEs. Explain what each key is for and what it costs, then:
   - `va-keys` shows which keys are set (masked). If keys are exported in their shell profile,
     offer `va-keys import` (copies them into the file without printing them).
   - Otherwise `va-keys edit` creates the file (chmod 600) and opens it; they paste keys there.
     If they paste a key into chat instead, write it into the file for them — never echo it back.
   Only OpenRouter is essential (AI images, video, music). Gemini gives narration. ElevenLabs is an
   optional alternative music engine and needs a paid plan. Nothing is required for free slideshows.
   Only the Code tab (local session), terminal and IDEs can run this plugin — not Chat/Cowork or
   cloud sessions. If tools like ffmpeg are "not found" in the desktop app, reopen the app.
4. Motion-graphics engine (per project folder):
   `bunx skills add heygen-com/hyperframes -s '*' -a claude-code --copy -y`
   (or `npx` if bun is missing). Do **not** use `--all` — it writes into ~40 other tools' folders.
   Tell the user to restart Claude Code afterwards so the new skills load.
5. Smoke test (costs about one cent): make `projects/_hello/`, then
   - `va-image "a single paper-cut moon over a torn-paper sea, soft shadows, no text" -o projects/_hello/moon.png --model cheap`
   - if Gemini key: `va-tts "Every picture is a moment that refused to end." -o projects/_hello/vo.wav`
   - write `projects/_hello/edit.json` with one 5s shot of `moon.png` (`"move": "in"`) plus narration if present
   - `va-assemble projects/_hello/edit.json -o projects/_hello/hello.mp4`, then `va-critic projects/_hello/hello.mp4`
   - `open projects/_hello/hello.mp4` so they see it.
6. Finish with: "You're set. Try: *make a 30-second living-photo loop from the pictures in ~/Pictures/trip*
   or `/video-art:new`."
