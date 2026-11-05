"""Check and tidy contact details before they go on a design.

    python validate.py phone "0772 123 456"     -> +263 77 212 3456
    python validate.py email info@example.org
    python validate.py url arcetel.com
    python validate.py spec design.json         -> checks every contact in a spec
Exit code 1 if anything is invalid. Default country for local numbers: Zimbabwe (+263).
"""
import json
import re
import sys

EMAIL = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
DOMAIN = re.compile(r"^(https?://)?([A-Za-z0-9-]+\.)+[A-Za-z]{2,}(:\d+)?(/[^\s]*)?$")
HANDLE = re.compile(r"^@?[A-Za-z0-9._]{2,30}$")


def phone(value, country="263"):
    digits = re.sub(r"[^\d+]", "", value)
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith("0") and not digits.startswith("00"):
        digits = "+" + country + digits[1:]
    if not digits.startswith("+"):
        digits = "+" + digits
    n = digits[1:]
    if not n.isdigit() or not 8 <= len(n) <= 15:
        return False, value, "phone must have 8-15 digits"
    if n.startswith("263"):
        rest = n[3:]
        if len(rest) != 9:
            return False, value, "Zimbabwe numbers have 9 digits after +263 (e.g. +263 77 123 4567)"
        if rest[0] == "7" and rest[1] not in "1378":
            return True, f"+263 {rest[:2]} {rest[2:5]} {rest[5:]}", "unusual mobile prefix: please double-check"
        return True, f"+263 {rest[:2]} {rest[2:5]} {rest[5:]}", ""
    return True, "+" + n, ""


def email(value):
    v = value.strip()
    return (bool(EMAIL.match(v)), v.lower(), "" if EMAIL.match(v) else "not a valid email address")


def url(value):
    v = value.strip()
    ok = bool(DOMAIN.match(v))
    pretty = re.sub(r"^https?://", "", v).rstrip("/")
    pretty = re.sub(r"^www\.", "www.", pretty)
    return ok, pretty, "" if ok else "not a valid web address (example: www.example.org)"


def handle(value):
    v = value.strip()
    if v.startswith("http"):
        return url(v)
    ok = bool(HANDLE.match(v))
    return ok, (v if v.startswith("@") else "@" + v), "" if ok else "handles use letters, numbers, . and _ only"


CHECKS = {"phone": phone, "whatsapp": phone, "email": email, "website": url, "url": url,
          "facebook": handle, "instagram": handle, "tiktok": handle, "x": handle, "youtube": handle, "social": handle}


def check(kind, value):
    fn = CHECKS.get(kind)
    if not fn:
        return True, value, ""
    return fn(value)


def check_spec(spec):
    problems, fixed = [], []
    for c in spec.get("contacts", []):
        ok, pretty, msg = check(c["type"], c["value"])
        if not ok:
            problems.append(f"{c['type']}: '{c['value']}' - {msg}")
        else:
            if msg:
                problems.append(f"{c['type']}: '{c['value']}' - WARNING {msg}")
            c["value"] = pretty
        fixed.append(c)
    spec["contacts"] = fixed
    return problems


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    kind, value = sys.argv[1], sys.argv[2]
    if kind == "spec":
        with open(value, encoding="utf-8") as fh:
            s = json.load(fh)
        probs = check_spec(s)
        for c in s["contacts"]:
            print(f"OK  {c['type']:10} {c['value']}")
        for p in probs:
            print("!!  " + p)
        sys.exit(1 if any("WARNING" not in p for p in probs) else 0)
    ok, pretty, msg = check(kind, value)
    print(("OK  " if ok else "BAD ") + pretty + (f"   ({msg})" if msg else ""))
    sys.exit(0 if ok else 1)
