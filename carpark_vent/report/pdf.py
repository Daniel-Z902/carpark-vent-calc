"""PDF calculation report (requires the optional ``reportlab`` dependency: pip install .[pdf])."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from carpark_vent import __version__
from carpark_vent.models import ProjectResult
from carpark_vent.report.common import DISCLAIMER, QUEUE_EXPRESSIONS, fmt, fmt_input, legend, summary_rows

NAVY = colors.HexColor("#1F497D")
HEAD = colors.HexColor("#DCE6F1")


def _table(data, widths=None, header=True, zebra=False):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), HEAD), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8)]
    t.setStyle(TableStyle(style))
    return t


def write_pdf(res: ProjectResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    p, ed, info = res.project, res.project.edition, res.project.info
    ss = getSampleStyleSheet()
    h1, h2, body, small = ss["Title"], ss["Heading2"], ss["BodyText"], ss["BodyText"].clone("small", fontSize=7.5)
    h1.alignment = 0
    h2.textColor = NAVY

    def on_page(canvas, doc):
        canvas.saveState()
        w, h = landscape(A4)
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(2)
        canvas.line(15 * mm, h - 14 * mm, w - 15 * mm, h - 14 * mm)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(NAVY)
        canvas.drawString(15 * mm, h - 12 * mm, info.company)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(w - 15 * mm, h - 12 * mm,
                               f"{info.name} | Job {info.number or '-'} | Rev {info.revision} | {ed.title}")
        canvas.drawString(15 * mm, 9 * mm, f"carpark_vent {__version__}")
        canvas.drawRightString(w - 15 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    s: list = [Paragraph("Car Park Mechanical Ventilation Calculation", h1),
               Paragraph(ed.title + (" - <font color='#9C0006'><b>SUPERSEDED</b></font>" if ed.superseded else ""), body)]

    s += [Paragraph("1. Project details", h2)]
    s += [_table([[k, v or "-"] for k, v in [
        ("Project", info.name), ("Job number", info.number), ("Client", info.client), ("Revision", info.revision),
        ("Architectural reference", info.arch_reference), ("Prepared by", info.prepared_by),
        ("Checked by", info.checked_by), ("Date", info.date)]], widths=[55 * mm, 120 * mm], header=False)]
    if info.notes:
        s.append(Paragraph(info.notes, body))

    s += [Paragraph("2. Method", h2), Paragraph("Design exhaust air flow per level is the highest of:", body)]
    s += [_table([["Symbol", "Expression (as used in the n2 workbook)"]] +
                 [[k, v] for k, v in ed.workbook_expressions.items()], widths=[20 * mm, 150 * mm])]
    s.append(Paragraph(f"Design exhaust (m3/s) = max / 1000. Make-up air = {p.effective_makeup_ratio:.0%} of design exhaust.", body))
    if p.exit_lanes is not None:
        s.append(Paragraph(f"Queuing areas, exit lanes L = {fmt_input(p.exit_lanes)}:", body))
        s.append(_table([[a, b] for a, b in QUEUE_EXPRESSIONS], widths=[30 * mm, 140 * mm], header=False))
    s.append(_table([["Symbol", "Meaning"]] + [list(x) for x in legend(ed)], widths=[20 * mm, 150 * mm]))

    s += [Paragraph("3. Inputs", h2)]
    s.append(_table([["Level", "Comment", *ed.level_fields]] +
                    [[lr.level.name, lr.level.comment, *[fmt_input(getattr(lr.level, f)) for f in ed.level_fields]]
                     for lr in res.levels]))

    s += [Paragraph("4. Step-by-step results", h2)]
    for lr in res.levels:
        rows = [["Item", "Calculation", "Result", "Unit"]]
        for sym, expr, val in lr.steps:
            unit = ("m3/s" if sym in ("Design exhaust", "Make-up air", "Queue exhaust")
                    else "m" if sym in ("LB / LHU", "LLU") else "l/s")
            rows.append([sym, Paragraph(expr, small), fmt(val, 0 if unit == "l/s" else 3), unit])
        rows.append(["Governs", lr.governing, "", ""])
        t = _table(rows, widths=[28 * mm, 170 * mm, 25 * mm, 15 * mm])
        s.append(KeepTogether([Paragraph(f"<b>{lr.level.name}</b> {lr.level.comment}", body), t, Spacer(1, 4)]))

    s += [Paragraph("5. Summary", h2)]
    head = ["Level", "n1", *[f"{x} (l/s)" for x in ed.component_symbols], "Governs", "Exhaust (m3/s)", "Make-up (m3/s)"]
    if p.exit_lanes is not None:
        head += ["Queue (m3/s)"]
    rows = [head]
    for lr in res.levels:
        row = [lr.level.name, fmt(lr.level.n1), *[fmt(lr.components_ls[x]) for x in ed.component_symbols],
               lr.governing, fmt(lr.design_exhaust_m3s, 2), fmt(lr.makeup_m3s, 2)]
        if p.exit_lanes is not None:
            row.append(fmt(lr.queue_exhaust_m3s, 2))
        rows.append(row)
    tot = ["TOTAL", fmt(res.total_n1), *[""] * len(ed.component_symbols), "", fmt(res.total_design_exhaust_m3s, 2),
           fmt(res.total_makeup_m3s, 2)]
    if p.exit_lanes is not None:
        tot.append(fmt(res.total_queue_exhaust_m3s, 2))
    rows.append(tot)
    t = _table(rows)
    t.setStyle(TableStyle([("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 8), ("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.black),
                           ("ALIGN", (1, 1), (-1, -1), "RIGHT")]))
    s.append(t)
    s.append(Paragraph("Totals exclude loading dock exhaust.", small))
    s.append(_table([[k, v] for k, v in summary_rows(res)], widths=[80 * mm, 80 * mm], header=False))
    if res.warnings:
        s += [Paragraph("Warnings", h2)] + [Paragraph("- " + x, body) for x in res.warnings]
    s += [Spacer(1, 8), Paragraph(DISCLAIMER, small)]

    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=20 * mm, bottomMargin=15 * mm,
                            title=f"Car park ventilation - {info.name}", author=info.prepared_by or info.company)
    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    return path
