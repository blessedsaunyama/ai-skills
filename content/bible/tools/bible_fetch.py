#!/usr/bin/env python3
"""Fetch a Bible passage from BibleGateway and print it VERBATIM, one verse per line,
so every quote in a script is copied exactly (never from memory, never via a summariser).

Usage:
  python3 bible_fetch.py "Daniel 6"            (default version KJV)
  python3 bible_fetch.py "1 Samuel 17:40-50" --version NKJV
  python3 bible_fetch.py "Daniel 6:10,16,22" --out work/scripture.md

Prints:  Daniel 6:10  Now when Daniel knew ...   then the BibleGateway URL that was loaded.
Exit code 3 = could not load -> mark the quote UNVERIFIED (or try another public KJV source).
Standard library only (no pip installs).
"""
import html, re, sys, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
BOOKS = {  # BibleGateway span codes -> display names (only needed for the label)
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers", "Deut": "Deuteronomy", "Josh": "Joshua",
    "Judg": "Judges", "Ruth": "Ruth", "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Kings", "2Kgs": "2 Kings",
    "1Chr": "1 Chronicles", "2Chr": "2 Chronicles", "Ezra": "Ezra", "Neh": "Nehemiah", "Esth": "Esther", "Job": "Job",
    "Ps": "Psalm", "Prov": "Proverbs", "Eccl": "Ecclesiastes", "Song": "Song of Solomon", "Isa": "Isaiah", "Jer": "Jeremiah",
    "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah",
    "Jonah": "Jonah", "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah",
    "Mal": "Malachi", "Matt": "Matthew", "Mark": "Mark", "Luke": "Luke", "John": "John", "Acts": "Acts", "Rom": "Romans",
    "1Cor": "1 Corinthians", "2Cor": "2 Corinthians", "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians",
    "Col": "Colossians", "1Thess": "1 Thessalonians", "2Thess": "2 Thessalonians", "1Tim": "1 Timothy", "2Tim": "2 Timothy",
    "Titus": "Titus", "Phlm": "Philemon", "Heb": "Hebrews", "Jas": "James", "1Pet": "1 Peter", "2Pet": "2 Peter",
    "1John": "1 John", "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Revelation",
}


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    ref = a[0]
    ver = a[a.index("--version") + 1] if "--version" in a else "KJV"
    outp = a[a.index("--out") + 1] if "--out" in a else None
    url = "https://www.biblegateway.com/passage/?" + urllib.parse.urlencode({"search": ref, "version": ver})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
        page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"UNVERIFIED: could not load {url} ({e})"); sys.exit(3)
    m = re.search(r'<div class="passage-text">(.*?)<div class="passage-other-trans|<div class="passage-text">(.*?)<div class="footnotes', page, re.S)
    body = (m.group(1) or m.group(2)) if m else page
    body = re.sub(r"<h[1-6].*?</h[1-6]>", "", body, flags=re.S)                      # section headings are not Scripture
    body = re.sub(r'<sup[^>]*class="(?:footnote|crossreference)"[^>]*>.*?</sup>', "", body, flags=re.S)
    body = re.sub(r'<sup class="versenum">.*?</sup>|<span class="chapternum">.*?</span>', "", body, flags=re.S)
    verses, order = {}, []
    for sm in re.finditer(r'<span[^>]*class="text ([0-9A-Za-z]+)-(\d+)-(\d+)"[^>]*>(.*?)</span>(?=\s*(?:<span[^>]*class="text|</p>|<br|</div>|<span class="indent|$))', body, re.S):
        key = (sm.group(1), int(sm.group(2)), int(sm.group(3)))
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", sm.group(4)))).strip()
        if key not in verses:
            verses[key] = []; order.append(key)
        if txt:
            verses[key].append(txt)
    if not order:
        print(f"UNVERIFIED: no verses parsed from {url}"); sys.exit(3)
    lines = [f"{BOOKS.get(b, b)} {c}:{v} ({ver})  {' '.join(verses[(b, c, v)])}" for b, c, v in order]
    lines.append(f"\nSource (loaded): {url}")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(lines))
    if outp:
        open(outp, "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
