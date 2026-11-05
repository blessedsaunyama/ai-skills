#!/usr/bin/env python3
"""Fetch an Ellen G. White chapter from text.egwwritings.org and print every paragraph
VERBATIM with its reference code, so quotes can be copied exactly (never from memory).

Usage:
  python3 egw_fetch.py <url-or-id> [--grep word1,word2] [--out file.md]
    <url-or-id>  https://text.egwwritings.org/read/88.2409   or just   88.2409
    --grep       only print paragraphs containing ANY of these words (case-insensitive)
    --out        also save the result as markdown (use it for the study-notes file)

Find the chapter id with a web search such as:
  "Prophets and Kings" "In the Lions' Den" text.egwwritings.org
Exit code 3 = page could not be loaded -> mark every EGW item UNVERIFIED.
Standard library only (no pip installs).
"""
import html, re, sys, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def clean(fragment):
    t = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def paragraphs(page):
    out = []
    for m in re.finditer(r'<p class="para[^"]*" id="([\d.]+)">(.*?)</p>', page, re.S):
        pid, body = m.group(1), m.group(2)
        code_m = re.search(r'<span class="refCode"[^>]*>(.*?)<a', body, re.S)
        code = clean(code_m.group(1)) if code_m else ""
        text = clean(re.sub(r'<span class="refCode".*', "", body, flags=re.S))
        if text:
            out.append((code, text, pid))
    return out


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__); sys.exit(1)
    src = args[0]
    url = src if src.startswith("http") else f"https://text.egwwritings.org/read/{src}"
    grep = []
    if "--grep" in args:
        grep = [w.strip().lower() for w in args[args.index("--grep") + 1].split(",") if w.strip()]
    outp = args[args.index("--out") + 1] if "--out" in args else None
    try:
        page = fetch(url)
    except Exception as e:
        print(f"UNVERIFIED: could not load {url} ({e})"); sys.exit(3)
    title_m = re.search(r"<title>(.*?)</title>", page, re.S)
    title = clean(title_m.group(1)) if title_m else "?"
    paras = paragraphs(page)
    if not paras:
        print(f"UNVERIFIED: no paragraphs found at {url} (layout changed or blocked)"); sys.exit(3)
    lines = [f"# {title}", f"Source (loaded): {url}", ""]
    for code, text, pid in paras:
        if grep and not any(w in text.lower() for w in grep):
            continue
        lines.append(f"**{code or '(no code)'}** {text}  \n<{url.split('#')[0]}#{pid}>\n")
    res = "\n".join(lines)
    sys.stdout.reconfigure(encoding="utf-8")
    print(res)
    if outp:
        open(outp, "w", encoding="utf-8").write(res + "\n")


if __name__ == "__main__":
    main()
