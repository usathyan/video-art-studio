# Video Art Studio

**Turn a folder of photos into a film, directed with Claude.**

A plugin for Claude Code, in the terminal or the Claude desktop app. Point it at your photos,
clips and notes. Claude studies them, asks what you want to say, then animates your best shots,
scores them, cuts on the beat, grades, titles and mixes a finished film. It checks its own work
and tells you what it changed.

[![Slowing Time — a 60-second film made with Video Art Studio](docs/showcase/slowing-time-poster.jpg)](docs/showcase/slowing-time-60s.mp4)

**▶ [Watch "Slowing Time" (63 s)](docs/showcase/slowing-time-60s.mp4)**: made from one folder of
trip photos and [the blog post it tells](https://8thcross.substack.com/p/slowing-time).
[How it was made ↓](#showcase-how-slowing-time-was-made)

---

## Why a plugin, not a website?

**Your vision, not a template.** A video website gives you its presets and its look. Here you
direct a creative collaborator. Claude studies your material, asks what you want to say, and
builds the film with you. You can change any shot, line, grade or cut and rebuild. Every step is
a file you own (`film.json`, the frames, the clips), so nothing is locked inside someone else's app.

**The best models, on your budget.** The strongest image, video, voice and music models are paid
models, and they change every few months. This plugin doesn't resell them or lock you to one.
You bring your own keys, pay the providers directly at cost, and choose per shot:
- Veo 3.1 for a hero shot, Veo 3.1 Fast for the rest.
- A $0.15 test before a $1.60 take.
- Nothing paid at all for a photo slideshow.

Claude shows the estimate before anything is spent, and swapping in a new model is one line in
`config/models.toml`. Your photos go only to the providers you choose, and only when you approve
a generation. Everything else runs on your own computer.

---

## Quick start

**You need:** a Mac, [Homebrew](https://brew.sh), and [Claude Code](https://claude.com/claude-code).
You can use it from the terminal or from the Code tab of the Claude desktop app.

**1. Install.** One command installs the helper tools (ffmpeg, whisper, uv, node, yt-dlp), the
plugin, and a private file for your API keys:

```bash
git clone https://github.com/usathyan/video-art-studio.git && bash video-art-studio/install.sh
```

**2. Add your API keys** to `~/.config/video-art/.env`, the one place every tool reads them from:

```bash
open -t ~/.config/video-art/.env
```
```
# images, AI video and music: openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-...
# narration: aistudio.google.com/apikey
GEMINI_API_KEY=...
# optional, ElevenLabs music (paid plan)
ELEVENLABS_API_KEY=
```

Or let Claude do it in step 3. If your keys are already exported in `~/.zshrc`, it copies them
into the file without printing them.

**3. Make something.** Open a folder for your art in Claude, either in the terminal or the desktop
app's Code tab with a *local* session:

```bash
mkdir -p ~/VideoArt && cd ~/VideoArt && claude
```
```
/video-art:setup                       # checks tools and keys, makes a 5-second test video
/video-art:film ~/Pictures/japan-trip  # your first film
```

### Where it runs

| Where | Works? |
|---|---|
| **Terminal** (`claude`) | ✅ |
| **Claude desktop app → Code tab**, local session | ✅ installing once covers both: they share the same plugins and the same key file |
| **VS Code / JetBrains** Claude Code extensions | ✅ |
| Claude desktop app → **Chat** or **Cowork** tab, claude.ai chat | ❌ a different plugin system that can't run local tools (ffmpeg, whisper, the `va-*` commands) |
| Cloud sessions (claude.ai/code, a desktop "cloud" environment) | ❌ they don't load locally installed plugins |

In the desktop app: if setup can't find `ffmpeg`, quit and reopen the app so it picks up your
Homebrew `PATH`.

**No zip or upload needed.** The desktop app's **Customize → Plugins → Upload** is for Chat and
Cowork plugins, and it won't accept this one, because it ships local command-line tools. The
Code tab uses the same plugins as the terminal, so after step 1 it's already installed there.

---

## Guide: make a film from a folder

What you need: a folder with photos (and optionally short videos and any text: a blog post,
notes, captions). Phone photos are fine.

```
/video-art:film ~/Pictures/japan-trip
```

**1. Claude studies your material (free).** `va-ingest` copies the folder into
`projects/<name>/`. Photos are straightened, colour-corrected and **stripped of all metadata,
including GPS**. Your text is gathered and numbered contact sheets are made. Claude looks at every
photo, reads every word, and tells you what it sees: the story, the strongest shots, which ones
have people in them, and any risks such as low resolution or text in the images.

**2. The wizard asks you (two short rounds).**

| Question | Choices |
|---|---|
| How long? | 30 s teaser · **60 s film** · 90 s · 2–3 min |
| What's it about? | 2–3 story angles drawn from *your* material, or your own words |
| Videography style? | `cinematic-warm` · `documentary-clean` · `vintage-film` · `neon-night` · `monochrome` |
| Shape? | 16:9 · 9:16 (Reels/TikTok) · 1:1 |
| Voice? | music only · **music + a few of your own lines** · full voiceover (pick a voice) |
| Music? | a proposed mood arc (quiet → build → peak → breath → resolve), or your own track |
| Budget? | lean ≈ $4–6 · **standard ≈ $7–9** · premium ≈ $12–15 |
| People? | **subtle motion only** (faces checked) · places only · fully animated |

**3. Storyboard (free).** Claude picks 8–12 shots and writes them into one file, `film.json`:
photo, crop, camera move, model, spoken lines. `va-film plan` shows the shot table and the real
cost. **Nothing is spent until you approve it.**

**4. Frames, then two test shots.** `va-film frames` crops landscape photos and extends portrait
photos to the film's shape. The image model only paints the *sides*, and your original photo is
pasted back exactly in the middle. Two test shots are generated first (about $2). Claude checks
them for invented text and for faces that drift, and shows you. Then the rest are made.

**5. Score and voice.** `va-film score` composes an original score, records your lines, and
finds the beat and the music's sections (build, peak, breath, resolve).

**6. The edit follows the music.** Every cut lands on a beat. Energetic shots go in the peak,
slow-motion shots in the breath, the emotional shot on the swell. The film ends on its first
frame, so it loops.

**7. Cut, check, deliver.** `va-film cut` grades every shot to the chosen style and adds the
letterbox, title, place names, subtitles and transitions. It lowers the music under each spoken
line, mixes to streaming loudness (−14 LUFS), then runs the critic. Claude looks at every scene,
checks every spoken line can be heard, tells you honestly what the AI changed, and offers retakes.

Your film is in `projects/<name>/film/out/`. Want a vertical version? Change `aspect` to `9:16`
and re-run.

### Videography styles

| Style | Look |
|---|---|
| `cinematic-warm` | anamorphic letterbox, warm highlights and cool shadows, fine grain, elegant serif titles (the showcase) |
| `documentary-clean` | natural colour, full frame, modern sans-serif |
| `vintage-film` | faded warm stock, lifted blacks, heavy grain, classic serif |
| `neon-night` | deep contrast, cyan/magenta split-tone, bold grotesk titles |
| `monochrome` | black & white, rich contrast |

Presets live in `config/styles.toml`: a grade (an ffmpeg filter chain), grain, letterbox, fps and
fonts (open-licence fonts are downloaded on first use). Add your own.

---

## More you can make

| Type this (or just describe it) | What you get |
|---|---|
| `/video-art:film <folder>` | the cinematic film above |
| *"a 30-second living-photo loop from ~/Pictures/iceland, 4:5"* | **Living photos and photo stories:** water flows and clouds drift while the rest of your photo stays exactly as shot. Slow camera moves, parallax, captions, music cut to the beat. |
| `/video-art:new a 60-second explainer on the printing press, paper-collage style` | **Narrated explainers** in a signature style: script → style frame → cheap rough cut for approval → final with AI motion, music and word-timed captions |
| *"a 20-second generative loop of ink diffusing in water, indigo and gold, 1:1"* | **Generative art:** flow fields, particles and shaders that loop seamlessly for screens and exhibitions |
| `/video-art:setup` | checks tools and keys, then makes a 5-second test video |

Everything for a piece lives in `projects/<name>/`. Claude checks in at each stage and never
spends money without showing you the estimate first.

## What does it cost?

The plugin is free. You pay the AI providers directly, per use, and a lot costs nothing:

| Thing | Rough cost |
|---|---|
| Photo slideshows, camera moves, parallax, titles, generative loops | **free** (runs on your Mac) |
| One AI still image | about $0.01–0.10 |
| One minute of narration | a few cents |
| A music track | $0.04 for a 30-second clip, $0.08 for a full-length piece (Lyria) |
| One AI video clip | 6 s at 1080p: $0.60 (Veo 3.1 Fast) · 8 s: $1.60 (Veo 3.1) · 720p tests from $0.15 |
| **A 60-second cinematic film** (9 animated shots, score, voice) | **about $7–9**; "Slowing Time" cost $7.90 |

## The studio, and the models behind it

| In a real studio… | In Video Art Studio… | Models (**default** first) |
|---|---|---|
| a **director** plans every shot | Claude studies your material, storyboards, and keeps the look consistent | **the Claude model you use** (Opus 5.5 recommended) |
| an **illustrator** paints scenes | an image model extends or paints stills | **Gemini 3 Pro Image** · GPT Image 5.4 · Gemini 3.1 Flash Image (cheap drafts) · Higgsfield *(optional)* |
| a **camera crew** films moving shots | a video model turns one of your photos into a moving clip | Films: **Veo 3.1 Fast** (1080p) · **Veo 3.1** for hero shots. Also Seedance 2.5 (720p max) · Veo 3.1 Lite (cheap tests) · Kling 3.0 · Higgsfield *(optional)* |
| a **motion designer** animates titles and graphics | code animates type, letterbox, transitions, maps and collage | **HyperFrames** (HTML + GSAP, rendered in Chrome): no AI model, no fees |
| a **narrator** reads the lines | a voice model reads them, with the emotion you ask for | **Gemini 3.8 Flash TTS**, voice *Charon* (try Kore, Puck, Zephyr) |
| a **composer** writes the score | a music model writes an instrumental score with an arc | **Lyria 3 Pro** · Lyria 3 Clip (≤30 s) · ElevenLabs Music *(paid plan)* |
| a **captioner** times every word | speech recognition times each spoken word | **whisper.cpp** `base.en`, on your Mac |
| an **editor** cuts it together | cuts on the beat, grades to one look, lowers the music under the voice | **ffmpeg** + a beat detector, plus an OpenTimelineIO export for Resolve or Premiere |
| a **critic** watches the first cut | checks frames, loudness, and whether every spoken line can be heard | **Claude** + whisper.cpp + ffmpeg |

Images, video and music all run through one OpenRouter key, and narration uses a Gemini key.
Model choices live in `config/models.toml` (or per project in `.video-art/models.toml`).

---

## Showcase: how "Slowing Time" was made

![Six frames from Slowing Time](docs/showcase/slowing-time-frames.jpg)

**The material:** [*Slowing Time*](https://8thcross.substack.com/p/slowing-time), a Substack post
about a father taking his son to Japan for a year of university (10 days, Tokyo → Kyoto → Osaka),
with 125 photos from a phone and a rented Fujifilm X100VI.

**First attempt: a slideshow.** A 10:47 photo essay: every one of the 125 photos framed on paper,
the whole post narrated. It worked as a slideshow but not as a film, which is why the wizard
now aims for fewer, moving, beat-cut shots.

**Second attempt: the film (63 s).**
- **Brief:** 60 s, 16:9, the `cinematic-warm` style, music-led with 5 of the author's own lines,
  subtle motion allowed on people, $6–9.
- **9 shots from 9 photos:** torii tunnel · the quiet Sangenjaya crossing · Gotokuji's lucky cats ·
  a samba parade · Osaka neon · the Shinkansen window · the Arashiyama bamboo · the Shirakawa canal ·
  father and son in Akihabara.
- **Portraits made wide:** 5 portrait photos were cropped to their best band and extended to 16:9;
  the originals were pasted back pixel-exact.
- **Motion:** Veo 3.1 for the torii and the goodbye, Veo 3.1 Fast for the rest, all at 1080p.
  **$7.40.**
- **Score:** one Lyria cue with an arc ($0.08). Cuts land on its 126 bpm grid, and the bamboo and
  canal play in slow motion during its quiet middle: *slowing time*, literally.
- **Honest notes:** the goodbye shot widened both smiles a little, and the torii clip invented kanji
  deeper in the tunnel. Only its first 3.2 s is used, slowed down, so the real 納 and 奉 dominate.
  The critic's whisper check caught the score masking "under my wing"; the score is now pre-ducked
  under every line.

Total: **about $7.90**. The whole film can be rebuilt from its `film.json` with `va-film cut`.

---

## Reference

### Other ways to install

**From inside Claude Code in the terminal**, without cloning:

```
/plugin marketplace add usathyan/video-art-studio
/plugin install video-art@video-art
```

The plugin then also appears in the desktop app (**+ → Plugins**), which shares the same settings.
Then install the helper tools with
`brew install uv ffmpeg ffmpeg-full whisper-cpp yt-dlp node`, or let `/video-art:setup` do it.

### API keys

| Key | Needed for | Get it at |
|---|---|---|
| **OpenRouter** | AI images, AI video and music (one key covers Gemini, GPT Image, Veo, Seedance, Kling, Lyria…) | openrouter.ai/keys |
| **Gemini** | narration | aistudio.google.com/apikey |
| **ElevenLabs** *(optional)* | alternative music engine; needs a **paid** plan. Use the secret key starting `sk_`, not the key ID | elevenlabs.io → API keys |

- **One file:** `~/.config/video-art/.env`, readable only by you (`chmod 600`). Every tool reads it,
  in the terminal, the desktop app and IDEs alike.
- **Keys in the file win.** Shell variables only fill in a key the file doesn't set, which keeps
  scripts and CI working. Keys never go in the repo or in your art folders.
- **Why not `~/.zshrc`?** The desktop app doesn't read keys you `export` there. Ask Claude to
  *"import my API keys"* and it copies them into the file for you.
- **Inside Claude,** the plugin's `va-keys` command manages the file: `va-keys` shows which keys
  are set (masked), `va-keys edit` opens it, `va-keys import` copies from your shell.
- A ChatGPT Plus subscription isn't needed. OpenAI's image models are reachable through the
  OpenRouter key.

### What's inside

```
.claude-plugin/     plugin + marketplace manifests
skills/             how Claude directs each kind of piece
  film/               the film wizard: folder → analysis → questions → storyboard → film
  video-director/     narrated explainers: script → storyboard → rough cut → final
  photo-motion/       living photos and photo stories, without altering your photos
  generative-art/     code-driven abstract and looping pieces
  new/  setup/        start a piece · first-time setup
bin/va-*            command-line tools Claude runs (on its PATH while the plugin is enabled)
tools/*.py          …their Python source:
                      ingest (folder → clean media + contact sheets) · reframe (crop / extend)
                      film (plan · frames · shots · score · cut) · beats (tempo + sections)
                      keys (the API-key file) · image · video · tts · music · clips
                      assemble · captions · critic
config/models.toml  which AI models to use
config/styles.toml  videography style presets (grade, grain, letterbox, fonts)
templates/          film.example.json (a complete film spec) · brief.md
docs/               research notes with sources · the showcase
```

The motion-graphics engine is [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen
(Apache-2.0). Setup installs it into each art folder; it isn't bundled here.

### Developing the plugin

```bash
make install      # python + bun deps
make test lint    # unit tests + ruff
make smoke        # end-to-end check: 1 image + 1 voice line, no video spend
claude --plugin-dir .   # try local changes without reinstalling
```

## Credits

The workflow builds on posts by [@deedydas](https://x.com/deedydas/status/2104957026199900220)
and [@maxescu](https://x.com/maxescu/status/2104898184442962277). See
[docs/research.md](docs/research.md) for every source.

MIT licensed.
