#!/usr/bin/env python3
"""Fetch Bible verses VERBATIM from bible.com (YouVersion), for translations BibleGateway doesn't have, e.g. Shona.

  python tools/bible_fetch_yv.py "John 3:16-17" [--version SNA2002] [--out FILE]
  python tools/bible_fetch_yv.py --list          known Shona versions

Use one verse or one range per call (Book chapter:verse[-verse]). Prints the text exactly as the page gives it,
the human reference in that language (e.g. "Johani 3:16-17") and the URL it loaded.
Exit code 3 = could not load or parse -> mark the quote UNVERIFIED. Never machine-translate a verse instead.
Modern translations are copyrighted: keep quotes short and always name the version. Standard library only.
"""
import html, json, re, sys, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
VERSIONS = {  # abbreviation -> (bible.com id, name). Checked on bible.com/languages/sna, Nov 2026.
    "SNA2002": (1960, "Shona Bible 1949, revised 2002"),
    "SUB": (4046, "Shona Union Bible"),
    "SCLB": (2262, "Bhaibheri Idzva reChiShona"),
    "BDSC": (32, "Bhaibheri Dzvene MuChiShona Chanhasi"),
}
USFM = {
    "genesis": "GEN", "exodus": "EXO", "leviticus": "LEV", "numbers": "NUM", "deuteronomy": "DEU", "joshua": "JOS", "judges": "JDG",
    "ruth": "RUT", "1 samuel": "1SA", "2 samuel": "2SA", "1 kings": "1KI", "2 kings": "2KI", "1 chronicles": "1CH", "2 chronicles": "2CH",
    "ezra": "EZR", "nehemiah": "NEH", "esther": "EST", "job": "JOB", "psalm": "PSA", "psalms": "PSA", "proverbs": "PRO",
    "ecclesiastes": "ECC", "song of solomon": "SNG", "isaiah": "ISA", "jeremiah": "JER", "lamentations": "LAM", "ezekiel": "EZK",
    "daniel": "DAN", "hosea": "HOS", "joel": "JOL", "amos": "AMO", "obadiah": "OBA", "jonah": "JON", "micah": "MIC", "nahum": "NAM",
    "habakkuk": "HAB", "zephaniah": "ZEP", "haggai": "HAG", "zechariah": "ZEC", "malachi": "MAL", "matthew": "MAT", "mark": "MRK",
    "luke": "LUK", "john": "JHN", "acts": "ACT", "romans": "ROM", "1 corinthians": "1CO", "2 corinthians": "2CO", "galatians": "GAL",
    "ephesians": "EPH", "philippians": "PHP", "colossians": "COL", "1 thessalonians": "1TH", "2 thessalonians": "2TH",
    "1 timothy": "1TI", "2 timothy": "2TI", "titus": "TIT", "philemon": "PHM", "hebrews": "HEB", "james": "JAS", "1 peter": "1PE",
    "2 peter": "2PE", "1 john": "1JN", "2 john": "2JN", "3 john": "3JN", "jude": "JUD", "revelation": "REV",
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if "--list" in a:
        for k, (i, n) in VERSIONS.items():
            print(f"  {k:8} id {i:<5} {n}")
        return
    if not a:
        print(__doc__); sys.exit(1)
    ver = (a[a.index("--version") + 1] if "--version" in a else "SNA2002").upper()
    outp = a[a.index("--out") + 1] if "--out" in a else None
    m = re.fullmatch(r"\s*((?:[1-3]\s)?[A-Za-z ]+?)\s+(\d+):(\d+)(?:-(\d+))?\s*", a[0])
    if not m:
        sys.exit("reference must look like 'John 3:16' or '1 John 4:7-8'")
    book = USFM.get(m.group(1).lower().strip())
    if not book:
        sys.exit(f"unknown book '{m.group(1)}' (use the English name)")
    if ver not in VERSIONS:
        sys.exit(f"unknown version {ver}; known: {', '.join(VERSIONS)} (or add its bible.com id to VERSIONS)")
    vid = VERSIONS[ver][0]
    usfm = f"{book}.{m.group(2)}.{m.group(3)}" + (f"-{m.group(4)}" if m.group(4) else "")
    url = f"https://www.bible.com/bible/{vid}/{usfm}.{ver}"
    try:
        page = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"UNVERIFIED: could not load {url} ({e})"); sys.exit(3)
    data = page.replace('\\"', '"')
    hit = re.search(r'"verses":\[\{"reference":\{"human":"([^"]+)".*?"content":"((?:[^"\\]|\\.)*)"', data, re.S)
    if not hit:
        print(f"UNVERIFIED: no verse text found at {url}"); sys.exit(3)
    human = hit.group(1)
    text = json.loads('"' + hit.group(2) + '"') if "\\" in hit.group(2) else hit.group(2)
    text = text.replace("\\n", " ")  # line breaks in poetry arrive as a literal backslash-n
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    lines = [f"{human} ({ver})  {text}", f"\nVersion: {VERSIONS[ver][1]}", f"Source (loaded): {url}"]
    print("\n".join(lines))
    if outp:
        with open(outp, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n\n")


if __name__ == "__main__":
    main()
