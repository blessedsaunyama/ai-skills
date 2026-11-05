"""Read a .psd: list layers, export the flattened image, image layers and text.

    python psd_import.py design.psd --out WORK_DIR/psd
Writes: flat.png, layers/NN-name.png, layers.json (name, kind, box, visible, text).
If the file is too complex (smart objects, effects, >60 layers) it says so: then ask
the user for a flattened PNG export instead.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psd")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        from psd_tools import PSDImage
    except ImportError:
        sys.exit("psd-tools is not installed. Ask the user, then: python3 -m pip install psd-tools")
    out = Path(a.out)
    (out / "layers").mkdir(parents=True, exist_ok=True)
    psd = PSDImage.open(a.psd)
    flat = psd.composite()
    if flat is not None:
        flat.save(out / "flat.png")
    info, complex_bits, n = [], [], 0
    for layer in psd.descendants():
        n += 1
        d = {"name": layer.name, "kind": layer.kind, "visible": layer.visible, "box": list(layer.bbox)}
        if layer.kind == "type":
            try:
                d["text"] = layer.text
            except Exception:
                d["text"] = None
        if layer.kind == "smartobject":
            complex_bits.append(f"smart object '{layer.name}'")
        if getattr(layer, "has_effects", lambda: False)():
            complex_bits.append(f"effects on '{layer.name}'")
        if layer.kind in ("pixel", "smartobject", "shape") and layer.visible:
            try:
                im = layer.composite()
                if im is not None:
                    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", layer.name)[:40]
                    p = out / "layers" / f"{n:02d}-{safe}.png"
                    im.save(p)
                    d["png"] = str(p)
            except Exception as e:
                d["error"] = str(e)
        info.append(d)
    (out / "layers.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"PSD {psd.width}x{psd.height}, {n} layers -> {out}")
    texts = [d["text"] for d in info if d.get("text")]
    if texts:
        print("Text found:\n  " + "\n  ".join(t.replace("\r", " / ") for t in texts))
    if n > 60 or complex_bits:
        print("COMPLEX: " + ("; ".join(complex_bits[:6]) or f"{n} layers") +
              "\n  -> use flat.png as a reference, or ask the user for a flattened PNG export.")


if __name__ == "__main__":
    main()
