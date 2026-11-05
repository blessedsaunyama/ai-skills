"""Spec -> Excel .xlsx (openpyxl) and CSV. Both use the same datasets, so they always match."""
import csv, re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .common import LETTERS, palette, plain, questions
from .docx_r import L


def safe_name(s, used):
    n = re.sub(r"[\[\]\*\?/\\:]", "", plain(s))[:31] or "Sheet"
    base, k = n, 2
    while n.lower() in used:
        n = f"{base[:28]}_{k}"; k += 1
    used.add(n.lower())
    return n


def datasets(spec):
    """[(name, columns, rows, opts)] from spec['sheets'], else from table blocks. Quiz handled separately."""
    out = []
    for s in spec.get("sheets") or []:
        out.append((s.get("name", "Data"), s.get("columns") or [], s.get("rows") or [], s))
    if not out:
        for k, b in enumerate(b for b in spec["blocks"] if b.get("type") == "table"):
            out.append((b.get("caption") or f"Table {k + 1}", b.get("columns") or [], b.get("rows") or [], b))
    return out


def quiz_rows(spec):
    qs = questions(spec)
    n = max((len(q.get("choices", [])) for q in qs), default=0)
    cols = ["#", "Question"] + [LETTERS[i] for i in range(n)]
    rows = [[k, plain(q.get("q", ""))] + [plain(c) for c in q.get("choices", [])] + [""] * (n - len(q.get("choices", [])))
            for k, q in enumerate(qs, 1)]
    key = [[k, str(q.get("answer", "")).upper(), plain(q.get("explain", ""))] for k, q in enumerate(qs, 1)]
    return cols, rows, key, n


def render_xlsx(spec, out):
    pal, fonts = palette(spec)
    wb = Workbook()
    used = set()
    thin = Side(style="thin", color="BBBBBB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    hfill = PatternFill("solid", fgColor=pal["primary"])
    soft = PatternFill("solid", fgColor=pal["soft"])
    body = fonts["body"]

    def header(ws, row, cols):
        for j, c in enumerate(cols, 1):
            cell = ws.cell(row=row, column=j, value=plain(c))
            cell.font = Font(bold=True, color="FFFFFF", name=body); cell.fill = hfill; cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    def grid(ws, r0, rows, ncols, stripe=True):
        for i, r in enumerate(rows):
            for j in range(ncols):
                v = r[j] if j < len(r) else None
                if isinstance(v, str) and not v.startswith("="):
                    v = plain(v)
                cell = ws.cell(row=r0 + i, column=j + 1, value=v)
                cell.border = border; cell.font = Font(name=body)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if stripe and i % 2 == 1:
                    cell.fill = soft

    def widths(ws, cols, rows, given=None):
        for j in range(max(len(cols), len(given or []), max((len(r) for r in rows), default=0))):
            if given and j < len(given):
                w = given[j]
            else:
                vals = [str(cols[j]) if j < len(cols) else ""] + [str(r[j]) for r in rows if j < len(r) and r[j] is not None]
                w = min(60, max(6, max(len(plain(v)) for v in vals) + 2))
            ws.column_dimensions[get_column_letter(j + 1)].width = w

    # Summary sheet (every document opens with the summary)
    ws = wb.active; ws.title = safe_name(L(spec, "summary"), used)
    s = spec.get("summary") or {}
    ws["A1"] = plain(spec.get("title", "")); ws["A1"].font = Font(bold=True, size=16, color=pal["primary"], name=fonts["heading"])
    r = 2
    if spec.get("subtitle"):
        ws.cell(row=r, column=1, value=plain(spec["subtitle"])).font = Font(italic=True, color=pal["accent"], name=body); r += 1
    meta = "  ·  ".join(x for x in [spec.get("author"), spec.get("date"), spec.get("audience")] if x)
    if meta:
        ws.cell(row=r, column=1, value=meta).font = Font(size=9, color=pal["muted"], name=body); r += 1
    r += 1
    for label, val in [(L(spec, "topic"), s.get("topic", "")), (L(spec, "points"), "\n".join("• " + plain(k) for k in s.get("key_points", []))),
                       (L(spec, "takeaway"), s.get("takeaway", ""))]:
        a = ws.cell(row=r, column=1, value=label); a.font = Font(bold=True, color=pal["primary"], name=body); a.alignment = Alignment(vertical="top")
        b = ws.cell(row=r, column=2, value=plain(val)); b.alignment = Alignment(wrap_text=True, vertical="top"); b.font = Font(name=body)
        b.fill = soft
        ws.row_dimensions[r].height = max(15, 15 * (str(val).count("\n") + 1 + len(plain(val)) // 90))
        r += 1
    if spec.get("disclaimer"):
        r += 1; ws.cell(row=r, column=1, value=plain(spec["disclaimer"])).font = Font(italic=True, size=9, color=pal["muted"], name=body)
    sheets_list = [d[0] for d in datasets(spec)] + (["Quiz"] if questions(spec) else [])
    if sheets_list:
        r += 2; ws.cell(row=r, column=1, value="Sheets").font = Font(bold=True, name=body)
        ws.cell(row=r, column=2, value=", ".join(sheets_list)).font = Font(name=body)
    ws.column_dimensions["A"].width = 16; ws.column_dimensions["B"].width = 95

    # Data sheets
    for name, cols, rows, opts in datasets(spec):
        ws = wb.create_sheet(safe_name(name, used))
        n = max(len(cols), max((len(x) for x in rows), default=0))
        r0 = 1
        if cols:
            header(ws, 1, cols); r0 = 2
        grid(ws, r0, rows, n, stripe=opts.get("stripe", True))
        widths(ws, cols, rows, opts.get("widths"))
        for j, fmt in enumerate(opts.get("number_formats") or []):
            if fmt:
                for i in range(r0, r0 + len(rows)):
                    ws.cell(row=i, column=j + 1).number_format = fmt
        if cols:
            ws.freeze_panes = "A2"
            if rows:
                ws.auto_filter.ref = f"A1:{get_column_letter(n)}{len(rows) + 1}"
        for k, tot in enumerate(opts.get("totals") or []):  # e.g. {"label": "Total", "column": "C", "func": "SUM"}
            rr = r0 + len(rows) + k
            ws.cell(row=rr, column=1, value=tot.get("label", "Total")).font = Font(bold=True, name=body)
            c = tot["column"]
            ws[f"{c}{rr}"] = f"={tot.get('func', 'SUM')}({c}{r0}:{c}{r0 + len(rows) - 1})"
            ws[f"{c}{rr}"].font = Font(bold=True, name=body)
            ws[f"{c}{rr}"].number_format = ws[f"{c}{r0}"].number_format

    # Quiz: questions, a dropdown for the answer, automatic marking and a score
    if questions(spec):
        cols, rows, key, n = quiz_rows(spec)
        wq = wb.create_sheet(safe_name("Quiz", used))
        wk_name = safe_name(L(spec, "answers"), used)
        allc = cols + ["Your answer", "Result"]
        header(wq, 1, allc)
        grid(wq, 2, rows, len(cols))
        ya, res = get_column_letter(len(cols) + 1), get_column_letter(len(cols) + 2)
        dv = DataValidation(type="list", formula1='"' + ",".join(LETTERS[:n]) + '"', allow_blank=True)
        wq.add_data_validation(dv)
        for i in range(2, len(rows) + 2):
            c = wq[f"{ya}{i}"]; c.border = border; c.fill = PatternFill("solid", fgColor="FFF7D6"); dv.add(c)
            c.alignment = Alignment(horizontal="center")
            wq[f"{res}{i}"] = f"=IF({ya}{i}=\"\",\"\",IF(UPPER({ya}{i})='{wk_name}'!B{i},\"Correct\",\"Wrong\"))"
            wq[f"{res}{i}"].border = border
        last = len(rows) + 1
        green, red = PatternFill("solid", fgColor="D9F2E3"), PatternFill("solid", fgColor="F9DADA")
        wq.conditional_formatting.add(f"{res}2:{res}{last}", FormulaRule(formula=[f'{res}2="Correct"'], fill=green))
        wq.conditional_formatting.add(f"{res}2:{res}{last}", FormulaRule(formula=[f'{res}2="Wrong"'], fill=red))
        sr = last + 2
        wq.cell(row=sr, column=2, value="Score").font = Font(bold=True, name=body)
        wq[f"{ya}{sr}"] = f'=COUNTIF({res}2:{res}{last},"Correct")&" / {len(rows)}"'
        wq[f"{ya}{sr}"].font = Font(bold=True, color=pal["primary"], name=body)
        widths(wq, allc, [r + ["", ""] for r in rows], [5, 55] + [24] * n + [13, 11])
        wq.freeze_panes = "C2"
        wk = wb.create_sheet(wk_name)
        header(wk, 1, ["#", "Answer", "Explanation"]); grid(wk, 2, key, 3); widths(wk, ["#", "Answer", "Explanation"], key, [5, 9, 80])

    # References + credits
    refs, creds = spec.get("references") or [], spec.get("credits") or []
    if refs or creds:
        wr = wb.create_sheet(safe_name(L(spec, "refs"), used))
        header(wr, 1, ["#", "Reference", "Link"])
        grid(wr, 2, [[k, plain(x.get("text", "")), x.get("url", "")] for k, x in enumerate(refs, 1)], 3, stripe=False)
        for i, x in enumerate(refs, 2):
            if x.get("url"):
                wr.cell(row=i, column=3).hyperlink = x["url"]; wr.cell(row=i, column=3).font = Font(color=pal["primary"], underline="single")
        if creds:
            r = len(refs) + 3
            header(wr, r, ["Image", "Author / licence", "Source"])
            grid(wr, r + 1, [[c.get("image", ""), " — ".join(x for x in [c.get("author"), c.get("licence")] if x), c.get("source", "")] for c in creds], 3, stripe=False)
        widths(wr, [], [], [5, 80, 60])
    # print setup: fit each sheet to one page wide, landscape when wide, repeat the header row
    for w in wb.worksheets:
        w.sheet_properties.pageSetUpPr.fitToPage = True
        w.page_setup.fitToWidth, w.page_setup.fitToHeight = 1, 0
        w.page_setup.paperSize = w.PAPERSIZE_LETTER if str(spec.get("page", "A4")).upper() == "LETTER" else w.PAPERSIZE_A4
        if w.max_column > 4:
            w.page_setup.orientation = "landscape"
        if w.title != wb.worksheets[0].title and w.max_row > 1:
            w.print_title_rows = "1:1"
        w.oddFooter.center.text = "Page &P of &N"
    wb.properties.title = plain(spec.get("title", "")); wb.properties.creator = spec.get("author") or ""
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def render_csv(spec, out):
    """One CSV per dataset (+ quiz.csv). UTF-8 with BOM so Excel opens accents correctly.
    CSV can't hold a summary, so <name>_summary.txt carries the summary and references."""
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    stem = out.with_suffix("")
    files = []
    sets = datasets(spec)
    if questions(spec):
        cols, rows, key, n = quiz_rows(spec)
        sets.append(("quiz", cols + ["Answer", "Explanation"], [r + k[1:] for r, k in zip(rows, key)], {}))
    for k, (name, cols, rows, _) in enumerate(sets):
        p = out if len(sets) == 1 else Path(f"{stem}_{re.sub(r'[^a-z0-9]+', '-', plain(name).lower()).strip('-')}.csv")
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if cols:
                w.writerow([plain(c) for c in cols])
            for r in rows:
                w.writerow([plain(v) if isinstance(v, str) else v for v in r])
        files.append(str(p))
    s = spec.get("summary") or {}
    lines = [plain(spec.get("title", "")), "", f"{L(spec, 'summary').upper()}", f"{L(spec, 'topic')}: {plain(s.get('topic', ''))}",
             f"{L(spec, 'points')}:"] + [f"  - {plain(x)}" for x in s.get("key_points", [])] + [f"{L(spec, 'takeaway')}: {plain(s.get('takeaway', ''))}"]
    if spec.get("disclaimer"):
        lines += ["", plain(spec["disclaimer"])]
    lines += ["", "Files: " + ", ".join(Path(f).name for f in files)]
    if spec.get("references"):
        lines += ["", L(spec, "refs") + ":"] + [f"  {k}. {plain(r.get('text', ''))} {r.get('url', '')}".rstrip() for k, r in enumerate(spec["references"], 1)]
    sp = Path(f"{stem}_summary.txt")
    sp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    files.append(str(sp))
    return files
