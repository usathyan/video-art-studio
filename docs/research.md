# Research notes & sources

Compiled 2026-09-30 while designing Video Art Studio. Every claim that shaped a design decision
is listed with where it came from. Items marked **verified** were checked against a live API or by
running the tool on this machine.

## Source posts (the starting point)

### 1. Deedy (@deedydas) — "getting the best out of Opus 5.5 for video generation"
<https://x.com/deedydas/status/2104957026199900220> (fetched via the fxtwitter mirror API because x.com blocks scrapers)

The full post recommends:
- Use Claude Code, not the app.
- Use the OpenRouter API to reach image, video, and audio models with one key.
- Use Gemini 3.8 TTS, and have Claude build a skill from the API to put emotion into the voice.
- Use Manim, HyperFrames, or Motion Canvas for motion graphics and HTML-grounded video.
- Use "GPT 2.5 Image Sunburst" for keyframes, and Veo 3.1 or Seedance 2.5 for generation. Seedance handles motion shots better. Keep reference images for consistency, and make an animatic before the full video.
- Add a script-planning skill, and assemble with OpenTimelineIO.
- Tell it to avoid Claudisms such as short punchy sentences and lots of numbers: "Narrate like a university professor."
- Let it use yt-dlp search to pull Creative Commons clips from real videos.
- Use ElevenLabs for background music.
- Add a caption skill that gets word-level timed subtitles from an ASR model.
- Add a critic skill that validates audio and video quality from screenshots and transcription.
- In each prompt, give: what you want, aspect ratio, length, and style. ffmpeg does most of the actual video work.
- The example was a 4-minute "Neocloud" business explainer.

**How we checked it**
- **Verified:** `bytedance/seedance-2.5`, `google/veo-3.1`, and `gemini-3.8-flash-tts` all exist on the user's keys.
- **Not found:** "GPT 2.5 Image Sunburst" isn't a model id on OpenRouter. We use `google/gemini-3-pro-image`, with `openai/gpt-5.4-image-2` as the alternative.
- **Adopted** as skills and tools: the animatic gate, reference images, the professor voice and anti-Claudism rules, CC clips with attribution, word-level captions, and the critic.
- **Adjusted:** OTIO is export-only (an `.otio` file for NLE hand-off). ffmpeg renders, because OTIO is an interchange format and has no renderer.

### 2. Alex Patrascu (@maxescu) — "Claude Opus 5.5 Max + Higgsfield"
<https://x.com/maxescu/status/2104898184442962277>

The prompt used a structure we adopted as the brief template:
- **Task:** a 60-second motion-graphic explainer on the history of the printing press.
- **Roles:** Higgsfield makes every image (stills only), and Claude makes all motion graphics and animation.
- **Style:** newspaper cutouts with mixed-media collage (torn edges, halftone, soft shadows, bold editorial type).
- **Rules:** accurate facts and dates, no text inside generated images (all type is animated), a consistent look, and an ending on the opening frame so it loops, never a hard cut.

**Adopted:** the Task/Roles/Style/Rules brief (`templates/brief.md`), the no-text-in-images rule, and the loop-on-opening-frame rule, which is implemented with `va-video --first X --last X`.

## Tools & services

| Topic | Finding | Source |
|---|---|---|
| HyperFrames | HeyGen's open-source HTML+CSS+GSAP → MP4 renderer, built for coding agents and shipped with Claude Code skills. Released 2026-04-17, Apache-2.0. Install with `npx skills add heygen-com/hyperframes`. **Verified:** v0.8.96 `doctor` passes here. `--all` writes into about 40 agent folders, so use `-a claude-code`. | [HyperFrames README](https://cdn.jsdelivr.net/gh/heygen-com/hyperframes@main/README.md) · [Menon Lab write-up](https://themenonlab.blog/blog/hyperframes-claude-code-writes-renders-videos) · [noqta overview](https://www.noqta.tn/en/blog/heygen-hyperframes-html-to-mp4-ai-agent-video-2026) |
| OpenRouter video | `POST /api/v1/videos` returns a job id. Poll `GET /api/v1/videos/{id}`, then download from `/content?index=0`. Supports `frame_images` (first/last frame) and `input_references`. Launched 2026-04-15. **Verified:** a live `/videos/models` list with per-second pricing (29 models). | [OpenRouter video docs](https://openrouter.ai/docs/guides/overview/multimodal/video-generation) · [announcement](https://openrouter.ai/blog/video-generation) · [video models](https://openrouter.ai/collections/video-models) |
| OpenRouter images | chat-completions with `modalities: ["image","text"]`, returning base64 in `message.images`. **Verified** by the smoke test. | OpenRouter API |
| Gemini TTS | `client.interactions.create(model="gemini-3.8-flash-tts", …)`. Turn-level `style` sets sustained emotion, and inline tags such as `<short pause>` and `<sigh>` handle moments. **Verified** by the smoke test. | [Gemini speech generation docs](https://ai.google.dev/gemini-api/docs/speech-generation) |
| ElevenLabs music | `POST /v1/music` with `prompt`, `music_length_ms`, `model_id` (`music_v1`/`v2`/`v2_5`), and `force_instrumental`. Keys start with `sk_`, and the key *ID* is rejected. | [ElevenLabs compose API](https://elevenlabs.io/docs/api-reference/music/compose) |
| Higgsfield | Remote MCP server (browser OAuth, no key): `claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp`. Covers Kling 3.0, Seedance 2.0, Veo 3.1, Soul (character consistency), and more. | [techsy.io setup guide](https://techsy.io/en/blog/higgsfield-mcp-claude-code) · [workingnotworking article](https://workingnotworking.com/?p=965) |
| Remotion (alternative) | React-based video-as-code with official agent skills (`npx skills add remotion-dev/skills`). A company license is required for teams larger than 3 people, and HyperFrames is Apache-2.0, so HyperFrames is the default. **Verified** in the license: free for individuals and for-profit orgs with up to 3 employees. | [Remotion LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) · [OpenReplay guide](https://blog.openreplay.com/making-videos-claude-code-remotion/) · [Remotion skills guide](https://gaga.art/blog/?p=1287) |
| Captions | whisper.cpp (`brew install whisper-cpp`) with `-ml 1 -sow -ojf` gives word-level timestamps. Homebrew's default `ffmpeg` 9 has no libass, so burning subtitles needs the keg-only `ffmpeg-full`. **Verified** here. | local testing |
| Claude Code plugins | `bin/` goes on the Bash PATH, `${CLAUDE_PLUGIN_ROOT}` is substituted in skill content, `userConfig` with `sensitive: true` stores keys in the keychain and exports them to hooks as `CLAUDE_PLUGIN_OPTION_<KEY>`. A SessionStart hook can write `export` lines to `CLAUDE_ENV_FILE`, and they persist into later Bash commands. The tradeoff is that the keys then sit in that session env file as plain text. | [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference) · [Hooks: persist environment variables](https://code.claude.com/docs/en/hooks#persist-environment-variables) |

| Seedance pricing | OpenRouter prices Seedance per video token. tokens = W × H × fps × seconds / 1024, and $10.70/M for 2.5 matches OpenRouter's `0.0000107`. `va-video` uses this at 24 fps. **Verified** against the live pricing table. | [Segmind: Seedance token pricing](https://blog.segmind.com/seedance-2-vs-seedance-2-fast-how-video-token-pricing-actually-works) · [Segmind: Seedance 2.5 pricing](https://blog.segmind.com/seedance-2-5-pricing-fal-charges-95-more-per-token-than-segmind/) |

## Other approaches considered

- **Manim.** Best for mathematical animation, so the `generative-art` skill references it for math pieces only.
- **Motion Canvas.** A TypeScript alternative that the deedydas post names. It overlaps HyperFrames, which already ships Claude Code skills, so we didn't add it. We didn't check whether Motion Canvas has its own agent skills.
- **Higgsfield MCP.** Useful for character consistency (Soul ID). It's billed through Higgsfield credits rather than OpenRouter. **Decision (2026-09-30):** bundled in `plugin.json` `mcpServers` (HTTP, no key), so it installs with the plugin. Each user signs in once with `/mcp`. Anyone who also added it with `claude mcp add` gets a second copy of the tools and should remove the user-scope copy.
- **p5.js through the `algorithmic-art` skill.** Good for sketching ideas, then porting them to HyperFrames for deterministic renders.
