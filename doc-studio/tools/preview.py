#!/usr/bin/env python3
"""Preview: turn a DOCX/PPTX/XLSX/PDF into page pictures so Claude can look at the result before showing it.

  python tools/preview.py FILE [--out DIR] [--dpi 60] [--pages 1-4] [--sheet]
    --sheet   also join all pages into one contact sheet (<name>_sheet.png): one picture to look at
Office files -> PDF with LibreOffice (soffice) if installed, else Microsoft Office on Windows (via PowerShell).
PDF -> PNG with pdftoppm (Poppler) or pypdfium2, whichever exists.
Optional: if nothing is available it says so; the documents themselves are fine without it.
Never changes the input file.
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path


def to_pdf(src, out_dir):
    src = Path(src).resolve()
    if src.suffix.lower() == ".pdf":
        return src
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir = out_dir.resolve()
    pdf = out_dir / (src.stem + "_" + src.suffix.lstrip(".").lower() + ".pdf")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    for c in [r"C:\Program Files\LibreOffice\program\soffice.exe", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]:
        if not soffice and Path(c).exists():
            soffice = c
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(src)],
                       capture_output=True, timeout=180)
        made = out_dir / (src.stem + ".pdf")
        if made.exists():
            made.replace(pdf)
            return pdf
    if os.name == "nt":
        ext = src.suffix.lower()
        ps = {
            ".docx": f"$w=New-Object -ComObject Word.Application;$w.Visible=$false;$d=$w.Documents.Open('{src}',$false,$true);"
                     f"$d.Fields.Update()|Out-Null;$d.SaveAs([ref]'{pdf}',[ref]17);$d.Close([ref]0);$w.Quit()",
            ".pptx": f"$p=New-Object -ComObject PowerPoint.Application;$d=$p.Presentations.Open('{src}',$true,$false,$false);"
                     f"$d.SaveAs('{pdf}',32);$d.Close();$p.Quit()",
            ".xlsx": f"$x=New-Object -ComObject Excel.Application;$x.Visible=$false;$x.DisplayAlerts=$false;$b=$x.Workbooks.Open('{src}',0,$true);"
                     f"$b.ExportAsFixedFormat(0,'{pdf}');$b.Close($false);$x.Quit()",
        }.get(ext)
        if ps:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=240)
            if not pdf.exists() and r.stderr:
                print("Office conversion error: " + r.stderr.strip()[:400], file=sys.stderr)
            if pdf.exists():
                return pdf
    sys.exit("preview: no converter found (install LibreOffice, or open the file yourself)")


def to_png(pdf, out_dir, dpi, pages):
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / Path(pdf).stem
    for old in out_dir.glob(Path(pdf).stem + "-*.png"):
        old.unlink()
    first, last = (pages.split("-") + [None])[:2] if pages else (None, None)
    if shutil.which("pdftoppm"):
        cmd = ["pdftoppm", "-r", str(dpi), "-png"]
        if first:
            cmd += ["-f", first, "-l", last or first]
        subprocess.run(cmd + [str(pdf), str(stem)], capture_output=True)
    else:
        try:
            import pypdfium2 as pdfium
        except ImportError:
            sys.exit(f"preview: PDF is at {pdf}, but no PDF->PNG tool (pdftoppm or pypdfium2) is installed")
        doc = pdfium.PdfDocument(str(pdf))
        a = int(first or 1) - 1
        b = int(last or first or len(doc))
        for i in range(a, min(b, len(doc))):
            doc[i].render(scale=dpi / 72).to_pil().save(f"{stem}-{i + 1}.png")
    return sorted(out_dir.glob(Path(pdf).stem + "-*.png"))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    out = Path(a[a.index("--out") + 1]) if "--out" in a else Path(tempfile.gettempdir()) / "doc-studio-preview"
    dpi = int(a[a.index("--dpi") + 1]) if "--dpi" in a else 60
    pages = a[a.index("--pages") + 1] if "--pages" in a else None
    pdf = to_pdf(a[0], out)
    pngs = to_png(pdf, out.resolve(), dpi, pages)
    for p in pngs:
        print(p)
    if "--sheet" in a and pngs:
        print(sheet(pngs, out.resolve() / (Path(pdf).stem + "_sheet.png")))


def sheet(pngs, dest, cols=None):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in pngs]
    cols = cols or (4 if ims[0].width > ims[0].height else 3)
    w, h = max(i.width for i in ims), max(i.height for i in ims)
    rows = (len(ims) + cols - 1) // cols
    out = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 8) + 8), (120, 120, 120))
    for k, im in enumerate(ims):
        out.paste(im, (8 + (k % cols) * (w + 8), 8 + (k // cols) * (h + 8)))
    out.save(dest)
    return dest


if __name__ == "__main__":
    main()
