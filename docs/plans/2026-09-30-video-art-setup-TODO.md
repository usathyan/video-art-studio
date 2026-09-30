# Video Art Studio — setup TODO (2026-09-30)

- [x] Review @deedydas and @maxescu posts; verify model ids against live APIs
- [x] Scaffold repo (git, uv, bun, Makefile, .gitignore, .env.example)
- [x] Install HyperFrames skills (project) + whisper-cpp + ffmpeg-full
- [x] Tools: image, video (dry-run guard), tts, music, clips, assemble (+OTIO), captions, critic
- [x] Skills: video-director, photo-motion, generative-art, new, setup
- [x] Package as plugin: manifest, userConfig keys, SessionStart hook, bin/ wrappers, marketplace
- [x] README (ELI5), docs/research.md, install.sh, LICENSE
- [x] Smoke test: image + TTS + assemble + captions + critic (no video spend)
- [ ] **User:** implement `judge()` pass/fail rules in tools/critic.py
- [ ] **User:** replace ELEVEN_API in ~/.zshrc with the `sk_…` secret key; re-test `va-music`
- [ ] Optional: `claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp` (browser OAuth)
- [x] Push to GitHub (private: usathyan/video-art-studio)
- [ ] Fresh-machine install test via `install.sh`
- [ ] First real piece: 60s printing-press explainer (maxescu brief) → compare against the reference
- [ ] First photo piece: living-photo loop from user's own photos (one paid Seedance shot)
- [ ] Showcase film "Slowing Time" (Japan trip) — progress tracked in projects/japan-trip/PLAN.md
