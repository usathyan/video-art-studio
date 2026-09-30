"""Narration via Gemini TTS, with emotion/style control.

    uv run tools/tts.py -o projects/x/gen/vo/01.wav "The press did not arrive all at once. <short pause> It crept."
                        [--style "hushed, conspiratorial"] [--voice Kore]

Two levers for emotion (Gemini docs):
  --style        sustained delivery for the whole line ("wry, amused")
  inline tags    moment-level: <short pause>, <sigh>, <laugh>, <whisper> ... inside the text
Keep the text itself a verbatim transcript — no stage directions in prose.
"""

from __future__ import annotations

import argparse
import base64
import wave
from pathlib import Path

from google import genai

from common import CONFIG, key, out_path


def synth(text: str, out: Path, voice: str, style: str) -> Path:
    client = genai.Client(api_key=key("gemini"))
    res = client.interactions.create(
        model=CONFIG["tts"]["model"],
        input=[
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "annotations": [{"type": "speech_metadata", "style": style}],
                    }
                ],
            }
        ],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voice}]},
    )
    audio = base64.b64decode(res.output_audio.data)
    out = out_path(out)
    if audio[:4] == b"RIFF":
        out.write_bytes(audio)
    else:  # raw 24kHz 16-bit mono PCM
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(audio)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("-o", "--out", required=True, type=Path)
    ap.add_argument("--voice", default=CONFIG["tts"]["voice"])
    ap.add_argument("--style", default=CONFIG["tts"]["style"])
    a = ap.parse_args()
    print(synth(a.text, a.out, a.voice, a.style))


if __name__ == "__main__":
    main()
