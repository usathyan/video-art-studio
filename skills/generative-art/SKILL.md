---
name: generative-art
description: Use when the user asks for abstract, algorithmic, generative, shader, particle, flow-field or audio-reactive video art (no narration). Renders code-driven visuals deterministically to MP4, optionally as seamless loops or synced to music.
---

# Generative video art

Work in `projects/<slug>/`. Everything must be **deterministic**: seeded RNG, time derived from
frame number (never `Date.now()`/`performance.now()`), so every render is identical.

## Pick a medium
| Want | Use |
|---|---|
| 2D particles, flow fields, geometry, typography | HyperFrames composition with a `<canvas>` driven by the timeline (`/hyperframes-core`, `/hyperframes-animation` → Three.js / TypeGPU adapters) |
| Shaders (GLSL fragment art, raymarching) | HyperFrames + Three.js adapter `ShaderMaterial`, or TypeGPU |
| Beat-synced to a track | `/music-to-video` — `npx hyperframes beats` gives the beat grid |
| Math/diagram animation | Manim (`uvx manim`) — only if the piece is mathematical |
| Quick p5.js sketch exploration | `example-skills:algorithmic-art` for the idea, then port to HyperFrames for rendering |

## Seamless loops
Drive motion by phase `p = frame / totalFrames` (0→1) and use only periodic functions of
`2π·p` (sin/cos, noise sampled on a circle: `noise(r·cos θ, r·sin θ)`). Frame N must equal frame 0.
Verify: `ffmpeg -i out.mp4 -vf "select=eq(n\,0)" f0.png` vs the last frame.

## Mixing with generated media
Stills from `va-image` can be textures/displacement sources; AI clips from `va-video`
can be layered as video elements. Music from `va-music`.

## Finish
Render (`npx hyperframes render --quality looks`), then `va-critic out/<name>.mp4`
(no `--script`). Read the contact sheet; iterate on palette, density and pacing — not just correctness.
Save the seed + params that produced a keeper in `projects/<slug>/KEEPERS.md`.
