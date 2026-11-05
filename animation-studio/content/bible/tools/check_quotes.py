#!/usr/bin/env python3
"""Check that every quoted string in a script appears word for word in the fetched source text.

  python3 check_quotes.py script.txt scripture.md [egw.md ...]
Rules: text inside "..." or “...” is a quote. A quote may be shortened with "..." (each part must match, in order).
Only the first letter's case and trailing punctuation are forgiven (starting a sentence with a capital is normal).
Exit code 1 if any quote is not found: fix it from the source text, or mark it UNVERIFIED.
Standard library only.
"""
import re, sys

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 3:
    print(__doc__); sys.exit(2)
norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()
script = norm(open(sys.argv[1], encoding="utf-8").read())
src = norm(" ".join(open(f, encoding="utf-8").read() for f in sys.argv[2:]))
bad = 0
for q in re.findall(r'"([^"]+)"', script):
    parts = [p.strip(" .,;:?!") for p in re.split(r"\.\.\.|…", q) if p.strip(" .,;:?!")]
    pos, ok = 0, True
    for p in parts:
        cands = [p, p[:1].lower() + p[1:], p[:1].upper() + p[1:]]
        hits = [src.find(c, pos) for c in cands if src.find(c, pos) >= 0]
        if not hits:
            ok = False; break
        pos = min(hits) + len(p)
    bad += not ok
    print(("OK    " if ok else "NOT FOUND ") + f'"{q}"')
print(f"\n{'all quotes verified' if not bad else f'{bad} quote(s) not found: fix or mark UNVERIFIED'}")
sys.exit(1 if bad else 0)
