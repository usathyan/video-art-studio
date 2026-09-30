"""Find & fetch Creative-Commons clips with yt-dlp, logging attribution.

    uv run tools/clips.py search "gutenberg press replica demonstration" [-n 15]
    uv run tools/clips.py get <url> -o projects/x/gen/clips/press.mp4 --section 00:01:10-00:01:18

Every download appends to <project>/ATTRIBUTION.md — CC-BY requires credit in the final piece.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

CC = "Creative Commons"


def search(query: str, n: int) -> None:
    out = subprocess.run(
        ["yt-dlp", f"ytsearch{n}:{query}", "-j", "--skip-download", "--no-warnings"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    hits = [json.loads(line) for line in out.splitlines() if line.strip()]
    cc = [h for h in hits if CC in (h.get("license") or "")]
    for h in cc:
        print(
            f"{h['webpage_url']}  {h.get('duration_string', '?'):>8}  {h['title'][:70]}  — {h.get('channel')}"
        )
    print(f"{len(cc)}/{len(hits)} results are Creative Commons")


def get(url: str, out: Path, section: str | None) -> None:
    meta = json.loads(
        subprocess.run(["yt-dlp", "-j", url], capture_output=True, text=True, check=True).stdout
    )
    if CC not in (meta.get("license") or ""):
        raise SystemExit(f"refusing: license is {meta.get('license')!r}, not Creative Commons")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "-f",
        "bv*[height<=1080]+ba/b",
        "--merge-output-format",
        "mp4",
        "-o",
        str(out),
        url,
    ]
    if section:
        cmd[1:1] = ["--download-sections", f"*{section}", "--force-keyframes-at-cuts"]
    subprocess.run(cmd, check=True)
    project = next((p for p in out.parents if p.parent.name == "projects"), out.parent)
    with (project / "ATTRIBUTION.md").open("a") as f:
        f.write(f'- "{meta["title"]}" by {meta.get("channel")} — {url} — {meta["license"]}\n')
    print(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-n", type=int, default=15)
    g = sub.add_parser("get")
    g.add_argument("url")
    g.add_argument("-o", "--out", type=Path, required=True)
    g.add_argument("--section", help="HH:MM:SS-HH:MM:SS")
    a = ap.parse_args()
    search(a.query, a.n) if a.cmd == "search" else get(a.url, a.out, a.section)


if __name__ == "__main__":
    main()
