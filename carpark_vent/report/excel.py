"""Excel report that mirrors the layout of Daniel's workbook sheets.

Sheet 1 reproduces the edition sheet (same columns, header block, fills,
number formats, landscape print setup).  By default it holds the values
computed in Python; ``formulas=True`` writes live Excel formulas in the
same style as the source workbook instead (Excel recalculates on open).
Sheet 2 lists step-by-step substituted calculations; sheet 3 is a summary.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import column_index_from_string, get_column_letter

from carpark_vent.editions import EDITIONS
from carpark_vent.layout import LAYOUTS
from carpark_vent.models import ProjectResult
from carpark_vent.report.common import (
    DISCLAIMER,
    QUEUE_EXPRESSIONS,
    QUEUE_LEGEND,
    USAGE_LABELS,
    VEHICLE_LABELS,
    legend,
    summary_rows,
)

ARIAL = "Arial"


def _fill(rgb: str) -> PatternFill:
    return PatternFill("solid", fgColor="FF" + rgb)


# Approximations of the theme colours used in the source workbook.
F_INPUT = _fill("C6D9F1")       # level inputs (dk2, tint 0.8)
F_COMPONENT = _fill("E6B9B8")   # Q / Qa / Qb / Qc (accent2, tint 0.4)
F_DESIGN = _fill("C4BD97")      # design exhaust / make-up (lt2, darker)
F_PROJECT = _fill("FAC090")
F_REV = _fill("92D050")
F_ARCH = _fill("FFEB9C")
F_SYMBOL = _fill("DAEEF3")
F_EXPR = _fill("C3D69B")
F_LANES = _fill("E46C0A")
F_RATIO = _fill("FFFF00")
F_BANNER = _fill("FFC000")
F_SUPERSEDED = _fill("FFC7CE")

HAIR = Side(style="hair")
MEDIUM = Side(style="medium")
BOX = Border(left=HAIR, right=HAIR, top=HAIR, bottom=HAIR)

WIDTHS = {  # from the source sheets
    "2024": {"A": 13.3, "B": 22.7, "C": 5.7, "L": 7.3, "N": 7.7, "O": 6.6, "P": 10.6, "Q": 10.0, "S": 6.1, "T": 7.4, "U": 7.6},
    "2012": {"A": 13.3, "B": 22.7, "C": 5.7, "K": 9.7, "L": 7.3, "N": 7.7, "O": 6.6, "P": 10.6, "Q": 10.0, "R": 5.9, "S": 6.1, "T": 7.4},
    "2002": {"A": 11.1, "B": 22.7, "C": 5.7, "J": 9.7, "K": 7.3, "M": 7.7, "N": 6.6, "O": 10.6, "P": 10.0, "Q": 5.9, "R": 6.1, "S": 7.4},
    "1991": {"A": 11.1, "B": 30.6, "C": 5.7, "J": 9.7, "K": 7.3, "M": 7.7, "N": 6.6, "O": 10.6, "P": 10.0, "Q": 5.9, "R": 6.1, "S": 7.4},
}
HEADERS = {"name": "Level", "comment": "Comment", "design": "Design Exhaust Air Flow",
           "makeup": "Design Make-up Air Flow", "lb_lhu": "LB LHU", "llu": "LLU", "queue": "Queue Exhaust"}
UNITS = {"d1": "(m)", "d2": "(m)", "d3": "(m)", "d4": "(m)", "A": "(m2)", "Q": "(l/s)", "Qa": "(l/s)",
         "Qb": "(l/s)", "Qc": "(l/s)", "Qd": "(l/s)", "design": "(m3/s)", "makeup": "(m3/s)", "lb_lhu": "(m)",
         "llu": "(m)", "queue": "(m3/s)"}


def _put(ws, ref, value, *, bold=False, size=10, fill=None, align=None, fmt=None, border=None, color=None):
    c = ws[ref]
    c.value = value
    c.font = Font(name=ARIAL, size=size, bold=bold, color=color)
    if fill is not None:
        c.fill = fill
    if align:
        c.alignment = Alignment(horizontal="left" if align == "wrap" else align, vertical="center", wrap_text=align == "wrap")
    if fmt:
        c.number_format = fmt
    if border is not None:
        c.border = border
    return c


def _shift(col: str, n: int) -> str:
    return get_column_letter(column_index_from_string(col) + n)


def _abs(ref: str) -> str:
    col = "".join(ch for ch in ref if ch.isalpha())
    row = ref[len(col):]
    return f"${col}${row}"


def _mirror_sheet(ws, res: ProjectResult, formulas: bool) -> None:
    proj = res.project
    ed = proj.edition
    lay = LAYOUTS[ed.key]
    title_col = "J" if ed.key in ("2024", "2012") else "I"

    # --- header block --------------------------------------------------------
    _put(ws, "A1", "Car Park Mechanical Ventilation Calculation - ", bold=True, size=14)
    _put(ws, f"{title_col}1", f"Australian Standard {ed.title}", bold=True, size=14)
    if ed.superseded:
        _put(ws, "P1", "(SUPERSEDED)", fill=F_SUPERSEDED, color="FF9C0006", size=11)
    _put(ws, "A2", proj.info.company, size=9, color="FF595959")
    if proj.info.number:
        _put(ws, "F2", f"Job No: {proj.info.number}", size=9)
    _put(ws, "A3", "Project:", size=11)
    _put(ws, "B3", proj.info.name, bold=True, size=12, fill=F_PROJECT, align="left")
    _put(ws, "C3", None, fill=F_PROJECT)
    _put(ws, "D3", f"rev {proj.info.revision}", bold=True, fill=F_REV)
    _put(ws, "F3", f"Arch: {proj.info.arch_reference}", size=11, fill=F_ARCH, color="FF9C6500")
    _put(ws, "A5", "Highest of the following determines the required exhaust air flow rate:", bold=True)

    for i, (sym, expr) in enumerate(ed.workbook_expressions.items()):
        r = 7 + i
        _put(ws, f"A{r}", f"{sym} =", fill=F_SYMBOL, align="right")
        if i == 0:
            _put(ws, f"B{r}", ed.q_min_ls, fill=F_EXPR, align="left", fmt="0")
            _put(ws, f"C{r}", "l/s minimum")
        else:
            _put(ws, f"B{r}", expr, fill=F_EXPR, align="left")

    # usage / vehicle factor blocks (values as in the workbook)
    _put(ws, "A12", "P =", align="right")
    _put(ws, "B12", f"Parking usage factor ({ed.usage_table_ref})")
    for i, (k, v) in enumerate(ed.usage_factors.items()):
        _put(ws, f"B{13 + i}", f"{USAGE_LABELS.get(k, k)} =")
        _put(ws, f"D{13 + i}", v)
    next_row = 18
    if ed.vehicle_factors:
        _put(ws, "A18", "T =", align="right")
        _put(ws, "B18", f"Vehicle type factor ({ed.vehicle_table_ref})")
        for i, (k, v) in enumerate(ed.vehicle_factors.items()):
            _put(ws, f"B{19 + i}", f"{VEHICLE_LABELS.get(k, k)} =")
            _put(ws, f"D{19 + i}", v)
        next_row = 25
    for i, (sym, text) in enumerate([x for x in legend(ed) if x[0] not in ("P", "P1", "P2", "T")]):
        _put(ws, f"A{next_row + i}", f"{sym} =", align="right")
        _put(ws, f"B{next_row + i}", text)

    # queuing block
    qc = lay.queue_block_col
    _put(ws, f"{qc}5", "Queuing Areas", bold=True)
    _put(ws, f"{qc}6", "(Queue length to be determined by the building owner or their representative,")
    _put(ws, f"{qc}7", " and is subject to approval by the relevant authority)")
    for i, (sym, expr) in enumerate(QUEUE_EXPRESSIONS[:4]):
        _put(ws, f"{qc}{8 + i}", f"{sym} =")
        _put(ws, f"{_shift(qc, 1)}{8 + i}", expr)
    _put(ws, f"{qc}12", "L =")
    _put(ws, f"{_shift(qc, 1)}12", "No. of exit lanes =")
    _put(ws, lay.exit_lanes_cell, proj.exit_lanes, fill=F_LANES, align="center")
    _put(ws, f"{_shift(lay.exit_lanes_cell[0], 1)}12", "(Enter Value)", size=9, fill=F_EXPR)
    for i, (sym, text) in enumerate(QUEUE_LEGEND[1:]):
        _put(ws, f"{qc}{14 + i}", f"{sym} =")
        _put(ws, f"{_shift(qc, 1)}{14 + i}", text)
    if ed.key in ("2024", "2012") and proj.queue_note:
        _put(ws, f"{qc}19", proj.queue_note, fill=F_BANNER, align="left")
        ws.merge_cells(f"{qc}19:{_shift(qc, 9)}19")

    ratio = proj.effective_makeup_ratio
    if lay.makeup_ratio_cell:
        rc = lay.makeup_ratio_cell
        _put(ws, f"{rc[0]}{int(rc[1:]) - 1}", "75-90%", align="center")
        _put(ws, f"{_shift(rc[0], -1)}{rc[1:]}", "Make-up ratio", size=9, align="right")
        _put(ws, rc, ratio, fill=F_RATIO, align="center", fmt="0%")

    # --- level table --------------------------------------------------------------
    hr, ur, r0 = lay.header_row, lay.units_row, lay.first_data_row
    cols = {**lay.inputs, **lay.outputs}
    for key, col in cols.items():
        top = Border(top=MEDIUM) if key == "design" else None
        _put(ws, f"{col}{hr}", HEADERS.get(key, key), bold=True, size=9 if key in HEADERS and key not in ("name", "comment") else 10,
             align="center", border=top)
        ws[f"{col}{hr}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if key in UNITS:
            _put(ws, f"{col}{ur}", UNITS[key], bold=True, align="center")
    ws.row_dimensions[hr].height = 36

    lanes_ref = _abs(lay.exit_lanes_cell)
    ratio_ref = _abs(lay.makeup_ratio_cell) if lay.makeup_ratio_cell else None
    syms = list(ed.component_symbols)
    for i, lr in enumerate(res.levels):
        r = r0 + i
        lv = lr.level
        ref = {k: f"{c}{r}" for k, c in cols.items()}
        for key, col in lay.inputs.items():
            val = getattr(lv, key)
            _put(ws, ref[key], val if val != "" else None, fill=F_INPUT, border=BOX,
                 align=None if key in ("name", "comment") else "center")
        if formulas:
            f = _row_formulas(ed.key, ref, lanes_ref, ratio_ref, ratio, proj.exit_lanes is not None)
        else:
            f = {**lr.components_ls, "design": lr.design_exhaust_m3s, "makeup": lr.makeup_m3s,
                 "lb_lhu": lr.queue_lb_lhu_m, "llu": lr.queue_llu_m, "queue": lr.queue_exhaust_m3s}
        for s in syms:
            _put(ws, ref[s], f[s], fill=F_COMPONENT, border=BOX, align="center", fmt="#,##0")
        _put(ws, ref["design"], f["design"], bold=True, size=11, fill=F_DESIGN, border=BOX, align="center", fmt="#,##0.0")
        _put(ws, ref["makeup"], f["makeup"], bold=True, size=11, fill=F_DESIGN, border=BOX, align="center", fmt="#,##0.0")
        _put(ws, ref["lb_lhu"], f["lb_lhu"], size=9, align="center", fmt="0.0")
        _put(ws, ref["llu"], f["llu"], size=9, align="center", fmt="0.0")
        _put(ws, ref["queue"], f["queue"], bold=True, size=9, align="center", fmt="#,##0.0")

    tr = r0 + len(res.levels)
    last = tr - 1
    top = Border(top=MEDIUM)
    _put(ws, f"A{tr}", "TOTAL", bold=True, border=top)
    for key, col in lay.totals.items():
        if formulas:
            val = f"=SUM({col}{r0}:{col}{last})"
        else:
            val = {"n1": res.total_n1, "A": res.total_area_m2, "design": res.total_design_exhaust_m3s,
                   "makeup": res.total_makeup_m3s}[key]
        fmt = "#,##0.0" if key in ("design", "makeup") else "#,##0"
        _put(ws, f"{col}{tr}", val, bold=True, size=12 if key in ("design", "makeup") else 10, border=top,
             align="center", fmt=fmt)
    _put(ws, f"{_shift(lay.outputs['design'], -1)}{tr}", "Excluding Loading Dock:", size=9, align="right")
    _put(ws, f"A{tr + 2}", DISCLAIMER, size=8, color="FF595959")

    for col, w in WIDTHS[ed.key].items():
        ws.column_dimensions[col].width = w
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    last_col = lay.outputs["queue"]
    ws.print_area = f"A1:{last_col}{tr + 2}"
    ws.oddFooter.left.text = "&F"
    ws.oddFooter.right.text = "Printed: &D @ &T"


def _row_formulas(key: str, c: dict[str, str], lanes: str, ratio_ref: str | None, ratio: float,
                  queue: bool) -> dict[str, str | None]:
    """Live formulas in the style of the source workbook (uniform for every row)."""
    ed = EDITIONS[key]
    f: dict[str, str | None] = {}
    if key == "2024":
        f["Q"] = "=$B$7"
        f["Qa"] = f"=0.4*({c['P1']}*(100*{c['n1']}+{c['n1']}*{c['d1']})+{c['P2']}*({c['n2']}*{c['d2']}))*{c['E']}*{c['T']}"
        f["Qb"] = f"={ed.staff_flow_ls:g}*{c['F']}*{c['T']}"
        f["Qc"] = f"={ed.area_rate_ls_per_m2:g}*{c['A']}"
        pq = c["P1"]
    elif key == "2012":
        f["Q"] = "=$B$7"
        f["Qa"] = f"={c['P']}*0.85*(100*{c['n1']}+{c['n1']}*{c['d1']}+{c['n2']}*{c['d2']})*{c['T']}*{c['E']}"
        f["Qb"] = f"={ed.staff_flow_ls:g}*{c['F']}*{c['T']}"
        f["Qc"] = f"={ed.area_rate_ls_per_m2:g}*{c['A']}"
        pq = c["P"]
    elif key == "2002":
        f["Q"] = "=$B$7"
        f["Qa"] = f"={c['P']}*0.85*(100*{c['n1']}+{c['n1']}*{c['d1']}+{c['n2']}*{c['d2']})"
        f["Qb"] = f"={ed.staff_flow_ls:g}*{c['F']}*{c['T']}"
        f["Qc"] = f"={ed.area_rate_ls_per_m2:g}*{c['A']}"
        pq = c["P"]
    else:
        f["Qa"] = "=$B$7"
        f["Qb"] = f"={c['P']}*1.2*(100*{c['n1']}+{c['n1']}*{c['d1']}+{c['n2']}*{c['d3']})"
        f["Qc"] = f"={c['P']}*0.4*(100*{c['n1']}+{c['n1']}*{c['d2']}+{c['n2']}*{c['d4']})"
        f["Qd"] = f"={ed.area_rate_ls_per_m2:g}*{c['A']}"
        pq = c["P"]
    syms = ed.component_symbols
    f["design"] = f"=MAX({c[syms[0]]}:{c[syms[-1]]})/1000"
    f["makeup"] = f"={ratio_ref or repr(ratio)}*{c['design']}"
    if queue:
        base = f"2.2*({c['n1']}/{lanes})*{pq}"
        f["lb_lhu"] = f'=IF({lanes}="","",IF(({base}-200)<0,0,{base}-200))'
        f["llu"] = f'=IF({lanes}="","",IF(({base}-400)<0,0,{base}-400))'
        rng = f"{c['lb_lhu']}:{c['llu']}"
        f["queue"] = f'=IF({lanes}="","",IF(MAX({rng})<0,0,MAX({rng})*300/1000))'
    else:
        f["lb_lhu"] = f["llu"] = f["queue"] = None
    return f


def _steps_sheet(ws, res: ProjectResult) -> None:
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 80
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 8
    _put(ws, "A1", f"Step-by-step calculation - {res.project.edition.title}", bold=True, size=14)
    _put(ws, "A2", res.project.info.name, size=11)
    r = 4
    for lr in res.levels:
        _put(ws, f"A{r}", lr.level.name, bold=True, size=11, fill=F_INPUT)
        if lr.level.comment:
            _put(ws, f"B{r}", lr.level.comment, size=9)
        r += 1
        for sym, expr, val in lr.steps:
            unit = "m3/s" if sym in ("Design exhaust", "Make-up air", "Queue exhaust") else "m" if sym in ("LB / LHU", "LLU") else "l/s"
            _put(ws, f"B{r}", sym)
            _put(ws, f"C{r}", expr)
            _put(ws, f"D{r}", val, fmt="#,##0.000" if unit != "l/s" else "#,##0.0", align="right",
                 bold=sym == "Design exhaust")
            _put(ws, f"E{r}", unit)
            r += 1
        _put(ws, f"B{r}", "Governs")
        _put(ws, f"C{r}", lr.governing, bold=True)
        r += 2


def _summary_sheet(ws, res: ProjectResult) -> None:
    info = res.project.info
    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 60
    _put(ws, "A1", "Calculation summary", bold=True, size=14)
    rows = [("Company", info.company), ("Project", info.name), ("Job number", info.number),
            ("Client", info.client), ("Revision", info.revision), ("Architectural reference", info.arch_reference),
            ("Prepared by", info.prepared_by), ("Checked by", info.checked_by), ("Date", info.date)]
    rows += summary_rows(res)
    r = 3
    for k, v in rows:
        _put(ws, f"A{r}", k, bold=True)
        _put(ws, f"B{r}", v)
        r += 1
    r += 1
    _put(ws, f"A{r}", "Level", bold=True)
    _put(ws, f"B{r}", "Design exhaust / make-up / queue (m3/s) - governing", bold=True)
    for lr in res.levels:
        r += 1
        q = "-" if lr.queue_exhaust_m3s is None else f"{lr.queue_exhaust_m3s:.2f}"
        _put(ws, f"A{r}", lr.level.name)
        _put(ws, f"B{r}", f"{lr.design_exhaust_m3s:.2f} / {lr.makeup_m3s:.2f} / {q} - {lr.governing}")
    if res.warnings:
        r += 2
        _put(ws, f"A{r}", "Warnings", bold=True)
        for w in res.warnings:
            r += 1
            _put(ws, f"A{r}", w)
    if info.notes:
        r += 2
        _put(ws, f"A{r}", "Notes", bold=True)
        _put(ws, f"B{r}", info.notes, align="wrap")
    r += 2
    _put(ws, f"A{r}", DISCLAIMER, size=8, color="FF595959")


def write_excel(res: ProjectResult, path: str | Path, *, formulas: bool = False) -> Path:
    path = Path(path)
    wb = Workbook()
    ws = wb.active
    ws.title = res.project.edition.sheet_name[:31]
    _mirror_sheet(ws, res, formulas)
    _steps_sheet(wb.create_sheet("Calculation steps"), res)
    _summary_sheet(wb.create_sheet("Summary"), res)
    wb.properties.creator = res.project.info.prepared_by or res.project.info.company
    wb.properties.title = f"Car park ventilation - {res.project.info.name}"
    if formulas:
        wb.calculation.fullCalcOnLoad = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
