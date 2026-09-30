# Video Art Studio

**A Claude Code plugin that turns your ideas and photographs into finished videos.**

You describe what you want in plain words. Claude writes the script, paints the pictures,
records the voice, adds music and captions, edits it all together, then watches the result
and fixes what looks wrong.

---

## What is it? (the five-year-old version)

Imagine a small film studio living inside your computer:

| In a real studio… | In Video Art Studio… |
|---|---|
| a **director** plans every shot | **Claude** plans the shots and keeps the look consistent |
| an **illustrator** paints scenes | an AI image model paints the stills |
| a **camera crew** films moving shots | an AI video model (Seedance, Veo, Kling) makes short moving clips |
| a **motion designer** animates titles and graphics | **HyperFrames** animates type, charts, and collage layers |
| a **narrator** reads the script | Gemini's voice model reads it, with feeling |
| a **composer** writes the score | ElevenLabs writes background music |
| an **editor** cuts it together | ffmpeg stitches everything into one video |
| a **critic** watches the first cut | Claude checks frames, sound levels, and whether the words match the script |

You stay the artist. You decide what it's about, how it should feel, and whether each draft is good enough.

## What can I make with it?

**If you're a photographer**
- *Living photos:* water keeps flowing and clouds keep drifting while the rest of your photo stays exactly as you shot it. Each one loops forever.
- *Photo stories:* a shoot becomes a paced slideshow with slow camera moves, captions, and music cut to the beat.
- *Parallax:* your subject lifts off the background with a gentle 3-D feel.
- *Portfolio reels* in 9:16 for Reels, 4:5 for Instagram, or 16:9 for your site.

**If you're an illustrator, designer, or painter**
- *Narrated explainers* in a signature style, such as "newspaper-cutout collage, torn edges, halftone".
- *Generative loops:* flow fields, particles, and shader art that repeat seamlessly for screens and exhibitions.
- *Motion graphics:* animated titles, maps, and data pieces.

## How do I use it?

After installing (below), open Claude Code in a folder and just ask:

```
make a 30-second living-photo loop from the pictures in ~/Pictures/iceland, 4:5 for Instagram
```
```
/video-art:new a 60-second explainer on the history of the printing press, paper-collage style
```
```
make an abstract 20-second generative loop of ink diffusing in water, deep indigo and gold, 1:1
```

Claude then works in stages and checks in with you at each one:

1. **Brief.** A few questions: shape, length, look, and budget.
2. **Look.** One style frame for you to approve.
3. **Animatic.** A rough cut built from stills and voice. It costs almost nothing, and you approve it before any money goes to AI video.
4. **Final.** AI motion, music, and captions are added.
5. **Critic.** Claude reviews its own cut and fixes problems before showing you.

Everything for a piece lives in `projects/<name>/`. The finished video is in `projects/<name>/out/`.

### Commands

| Type this | What it does |
|---|---|
| `/video-art:setup` | First-time setup: checks your tools and keys, then makes a 5-second test video |
| `/video-art:new [idea]` | Starts a new piece with a short questionnaire |
| *just describe it* | Claude picks the right workflow: explainer, photo motion, or generative |

## What does it cost?

The plugin is free. The AI services charge per use, and you can make a lot without spending anything:

| Thing | Rough cost |
|---|---|
| Photo slideshows, camera moves, parallax, titles, generative loops | **free** (runs on your Mac) |
| One AI still image | about $0.01–0.10 |
| One minute of narration | a few cents |
| One minute of music | about the price of a coffee, on your ElevenLabs plan |
| One AI video clip (5 seconds) | about $0.15 (Veo Lite, 720p) to $2.60 (Seedance 2.5, 1080p) |

Claude never spends money on AI video silently. It prints the estimated cost of each shot, adds them up, and waits for your OK. It also builds a cheap rough cut first, so you never pay to animate a shot you'd have cut anyway.

---

## Install

**You need:** a Mac, [Claude Code](https://claude.com/claude-code), and [Homebrew](https://brew.sh).

### Option A: one command

```bash
git clone https://github.com/usathyan/video-art-studio.git && bash video-art-studio/install.sh
```

This installs the helper tools (ffmpeg, whisper, uv, node, yt-dlp) and the plugin.

### Option B: from inside Claude Code

```
/plugin marketplace add usathyan/video-art-studio
/plugin install video-art@video-art
```

Then install the helper tools yourself with `brew install uv ffmpeg ffmpeg-full whisper-cpp yt-dlp node`, or run `/video-art:setup` and let Claude do it.

### Then, in any folder where you want to make art

```bash
mkdir -p ~/VideoArt && cd ~/VideoArt && claude
```
```
/video-art:setup
```

Setup walks you through the API keys, installs the motion-graphics engine into that folder, and makes a test video so you can see everything works.

### API keys: what each one is for

| Key | Needed for | Get it at |
|---|---|---|
| **OpenRouter** | AI images and AI video (one key covers Gemini, GPT Image, Seedance, Veo, Kling…) | openrouter.ai/keys |
| **Gemini** | narration | aistudio.google.com/apikey |
| **ElevenLabs** *(optional)* | background music. Use the secret key starting `sk_`, not the key ID | elevenlabs.io → API keys |

The easiest place to enter them is `/plugin` → **Video Art Studio** → **Configure**. They're stored in your system keychain. You can also put them in your shell profile or in `~/.config/video-art/.env`.

A ChatGPT Plus subscription isn't needed. OpenAI's image models are reachable through the OpenRouter key.

---

## What's inside (for the curious)

```
.claude-plugin/     plugin + marketplace manifests
skills/             how Claude should direct each kind of piece
  video-director/     narrated explainers: script → storyboard → animatic → final
  photo-motion/       your photographs, brought to life without altering them
  generative-art/     code-driven abstract and looping pieces
  new/  setup/        the two slash commands
bin/va-*            small command-line tools Claude calls (on PATH while the plugin is on)
tools/*.py            …their Python source: image, video, tts, music, clips, assemble, captions, critic
config/models.toml  which AI models to use; change them here or per project in .video-art/models.toml
templates/brief.md  the brief every piece starts from
docs/research.md    where these ideas came from, with sources
```

The motion-graphics engine is [HyperFrames](https://github.com/heygen-com/hyperframes) by HeyGen (Apache-2.0). Setup installs it into each art folder; it isn't bundled here.

### Developing the plugin

```bash
make install      # python + bun deps
make test lint    # unit tests + ruff
make smoke        # end-to-end check: 1 image + 1 voice line, no video spend
claude --plugin-dir .   # try local changes without reinstalling
```

## Credits

The workflow builds on posts by [@deedydas](https://x.com/deedydas/status/2104957026199900220)
and [@maxescu](https://x.com/maxescu/status/2104898184442962277). See [docs/research.md](docs/research.md)
for every source.

MIT licensed.
