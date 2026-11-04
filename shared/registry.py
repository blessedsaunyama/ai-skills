"""Read shared/tools.yaml (the software registry) with the standard library only.

tools.yaml uses a small, strict YAML subset so no PyYAML is needed before anything is installed:
  - 2-space indentation, `key: value`, `key:` opening a nested map, `- item` list entries (scalars only)
  - inline lists `[a, b, "c d"]`, quoted or plain strings, true/false/null, integers; `#` comments on their own line
Usage:  from registry import load; REG = load(); REG["tools"]["kdenlive"]["install"]["winget"]
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _scalar(v):
    v = v.strip()
    if v in ("", "~", "null"):
        return None
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if (v[0] == v[-1]) and v[0] in "\"'" and len(v) >= 2:
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        items, cur, q = [], "", None
        for ch in inner:
            if q:
                cur += ch
                if ch == q:
                    q = None
            elif ch in "\"'":
                q = ch; cur += ch
            elif ch == ",":
                items.append(_scalar(cur)); cur = ""
            else:
                cur += ch
        items.append(_scalar(cur))
        return items
    return v


def parse(text):
    root = {}
    stack = [(-1, root)]                      # (indent, container)
    pending = None                            # (indent, parent dict, key) for a `key:` whose type is decided by the next line
    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        ind = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if pending and ind > pending[0]:
            _, parent, key = pending
            parent[key] = [] if line.startswith("- ") else {}
            stack.append((pending[0], parent[key]))
        elif pending:
            pending[1][pending[2]] = None
        pending = None
        while stack and ind <= stack[-1][0]:
            stack.pop()
        cont = stack[-1][1]
        if line.startswith("- "):
            if not isinstance(cont, list):
                raise ValueError(f"tools.yaml line {n}: list item outside a list")
            cont.append(_scalar(line[2:]))
            continue
        m = re.match(r"([A-Za-z0-9_.\-]+):(?:\s+(.*))?$", line)
        if not m:
            raise ValueError(f"tools.yaml line {n}: cannot read '{line}'")
        key, val = m.group(1), m.group(2)
        if val is None or val.strip() == "":
            pending = (ind, cont, key)
        else:
            cont[key] = _scalar(val)
    if pending:
        pending[1][pending[2]] = None
    return root


def load(path=None):
    return parse((Path(path) if path else HERE / "tools.yaml").read_text(encoding="utf-8"))
