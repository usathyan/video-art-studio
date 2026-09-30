---
name: photo-motion
description: Use when the user wants to bring their own photographs or artwork to life as video — animated photo stories, cinemagraphs / living photos, parallax "2.5D" moves, portfolio reels, exhibition loops, or a music-synced slideshow of a shoot.
---

# Photo motion — the artist's own images, moving

The user's photographs are the art. Every technique here must **preserve the original image**
(composition, color, subject) and add motion around it. Never "improve" or restyle a photo unless asked.

Work in `projects/<slug>/`. Copy (don't move) source photos into `projects/<slug>/photos/`.
Keep `PLAN.md` updated.

## 1. Understand the set
Read every photo (look at them). Note subject, light, palette, orientation, and which images
belong together. Propose an order and a mood in 3–5 lines, then ask the user to confirm:
aspect ratio (16:9 web, 9:16 Reels/Stories, 4:5 Instagram feed, 1:1), length, music yes/no,
narration yes/no, and budget for AI motion (can be $0).

## 2. Pick a treatment per photo (cheapest that works)
| Treatment | Cost | How |
|---|---|---|
| **Slow move** (Ken Burns push/pull/pan) | free | `edit.json` shot with `"move": "in"|"out"` → `va-assemble` |
| **Parallax 2.5D** (foreground slides over background) | free | HyperFrames: cut subject with `npx hyperframes remove-background`, layer subject + background, animate at different speeds (`/hyperframes-keyframes`) |
| **Typographic story** (title, caption, location, date) | free | HyperFrames motion graphics over the photo (`/motion-graphics`) |
| **Living photo / cinemagraph** (water flows, hair moves, clouds drift) | ~$0.15 (Veo Lite 720p) – $2.60 (Seedance 2.5 1080p) per 5s | `va-video "<only the motion, e.g. 'gentle ripples on the water, everything else still, locked-off camera'>" --first photos/x.jpg --last photos/x.jpg --resolution 720p` — same first & last frame = seamless loop; test on `--model cheap` first |
| **Camera move into the scene** | ~$1–2.60 per 5s | `va-video --first photos/x.jpg --model cinematic` with a precise camera instruction |

Default to free treatments; propose AI motion only for 1–3 hero images, with the total cost.
Always dry-run `va-video` first and state the estimate before `--confirm`.

Prompting AI motion on real photos: describe **only what moves** and say "locked-off camera,
preserve the photograph exactly". Reject any output where faces, text or the composition drift —
compare the first frame of the result to the original.

## 3. Sound
- Music: `va-music "<mood, instrumentation, bpm>" --seconds <len>`; for cutting to the beat use
  `/music-to-video` (HyperFrames beat grid).
- Optional narration or the photographer's own voice memo: `va-tts` or their audio file, then
  `va-captions` for word-timed captions.

## 4. Assemble, review, deliver
`va-assemble edit.json -o out/<slug>.mp4` → `va-critic out/<slug>.mp4` → Read `contact.jpg`.
Check: no photo cropped through a subject's head, no color shift from the originals,
holds are long enough to actually look at a photograph (≥3s each; 5–6s for hero images).
Render extra aspect ratios only after the main one is approved.
Credit the photographer (the user) in the end card if they want one.
