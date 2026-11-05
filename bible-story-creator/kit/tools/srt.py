#!/usr/bin/env python3
"""Captions (.srt) from the timing files written by timing.py.

  python3 srt.py work/ out/Title.srt [--max-words 7]
Uses work/words.json (per-word times) and groups words into short readable cues that break at punctuation.
Captions must match the narration word for word (the script is the source). Burn in only if asked:
  ffmpeg -i out/Title.mp4 -vf "subtitles=out/Title.srt:force_style='Fontsize=14,Outline=2,MarginV=60'" -c:a copy out/Title_captioned.mp4
(For 9:16 keep MarginV high enough to stay above the platform's bottom UI; see formats.py safe 9x16.)
"""
import json, os, re, sys


def ts(t):
    h, r = divmod(max(0.0, t), 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


a = sys.argv[1:]
if len(a) < 2:
    print(__doc__); sys.exit(1)
mw = int(a[a.index("--max-words") + 1]) if "--max-words" in a else 7
words = json.load(open(os.path.join(a[0], "words.json"), encoding="utf-8"))
cues, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) >= mw or re.search(r"[.!?;:,]$", w["w"]) and len(cur) >= 3 or re.search(r"[.!?]$", w["w"]):
        cues.append(cur); cur = []
if cur:
    cues.append(cur)
with open(a[1], "w", encoding="utf-8") as f:
    for i, c in enumerate(cues, 1):
        f.write(f"{i}\n{ts(c[0]['s'])} --> {ts(c[-1]['e'] + 0.15)}\n{' '.join(x['w'] for x in c)}\n\n")
print(a[1], len(cues), "cues")
