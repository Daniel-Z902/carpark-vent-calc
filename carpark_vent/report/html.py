"""Self-contained HTML calculation report (no external assets; print-friendly)."""

from __future__ import annotations

import html
from datetime import date
from pathlib import Path

from carpark_vent import __version__
from carpark_vent.models import ProjectResult
from carpark_vent.report.common import DISCLAIMER, QUEUE_EXPRESSIONS, fmt, fmt_input, legend, summary_rows

CSS = """
@page { size: A4 landscape; margin: 14mm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #222; margin: 24px; }
header { display: flex; justify-content: space-between; align-items: flex-end;
         border-bottom: 3px solid #1F497D; padding-bottom: 6px; margin-bottom: 14px; }
header .co { font-size: 15pt; font-weight: bold; color: #1F497D; }
header .doc { text-align: right; font-size: 9pt; color: #555; }
h1 { font-size: 15pt; margin: 4px 0 2px; } h2 { font-size: 12pt; color: #1F497D; margin: 20px 0 6px;
     border-bottom: 1px solid #ccc; } h3 { font-size: 10.5pt; margin: 12px 0 4px; }
table { border-collapse: collapse; margin: 4px 0 10px; }
th, td { border: 1px solid #bbb; padding: 3px 7px; }
th { background: #DCE6F1; font-weight: bold; text-align: center; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td.in { background: #EEF3FA; } td.res { background: #F2DCDB; } td.des { background: #EEECE1; font-weight: bold; }
td.gov { font-weight: bold; color: #C0504D; }
table.kv th { text-align: left; background: #F2F2F2; width: 260px; }
.superseded { color: #9C0006; background: #FFC7CE; padding: 1px 6px; font-weight: bold; }
.warn { background: #FFF2CC; border: 1px solid #E6B800; padding: 6px 10px; margin: 8px 0; }
.small { font-size: 8.5pt; color: #555; } code { font-size: 9pt; }
footer { margin-top: 24px; border-top: 1px solid #ccc; padding-top: 6px; font-size: 8.5pt; color: #666; }
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def render_html(res: ProjectResult) -> str:
    p = res.project
    ed = p.edition
    info = p.info
    o: list[str] = []
    w = o.append
    w("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    w(f"<title>Car park ventilation - {_e(info.name)}</title><style>{CSS}</style></head><body>")
    w(f"<header><div><div class='co'>{_e(info.company)}</div>"
      f"<h1>Car Park Mechanical Ventilation Calculation</h1>"
      f"<div>{_e(ed.title)}{' <span class=superseded>SUPERSEDED</span>' if ed.superseded else ''}</div></div>"
      f"<div class='doc'>Job {_e(info.number) or '-'} &middot; Rev {_e(info.revision)}<br>"
      f"{_e(info.date) or date.today().isoformat()}</div></header>")

    w("<h2>1. Project details</h2><table class='kv'>")
    for k, v in [("Project", info.name), ("Job number", info.number), ("Client", info.client),
                 ("Revision", info.revision), ("Architectural reference", info.arch_reference),
                 ("Prepared by", info.prepared_by), ("Checked by", info.checked_by), ("Date", info.date)]:
        w(f"<tr><th>{_e(k)}</th><td>{_e(v) or '-'}</td></tr>")
    w("</table>")
    if info.notes:
        w(f"<p>{_e(info.notes)}</p>")

    w("<h2>2. Method</h2><p>The design exhaust air flow for each level is the highest of:</p><table>")
    w("<tr><th>Symbol</th><th>Expression (as used in the n2 workbook)</th></tr>")
    for sym, expr in ed.workbook_expressions.items():
        w(f"<tr><td>{_e(sym)}</td><td><code>{_e(expr)}</code></td></tr>")
    w(f"</table><p>Design exhaust (m3/s) = max of the above / 1000. Make-up air = "
      f"{p.effective_makeup_ratio:.0%} of design exhaust"
      f"{'' if ed.makeup_ratio_editable else ' (fixed in the workbook for this edition)'}.</p>")
    if p.exit_lanes is not None:
        w(f"<p>Queuing areas (number of exit lanes L = {fmt_input(p.exit_lanes)}):</p><table>")
        for sym, expr in QUEUE_EXPRESSIONS:
            w(f"<tr><td>{_e(sym)}</td><td><code>{_e(expr)}</code></td></tr>")
        w("</table><p class='small'>Queue length to be determined by the building owner or their "
          "representative and is subject to approval by the relevant authority.</p>")
        if p.queue_note:
            w(f"<p><b>{_e(p.queue_note)}</b></p>")
    w("<h3>Symbols</h3><table>")
    for sym, text in legend(ed):
        w(f"<tr><td>{_e(sym)}</td><td>{_e(text)}</td></tr>")
    w("</table>")

    w("<h2>3. Inputs</h2><table><tr><th>Level</th><th>Comment</th>")
    for f in ed.level_fields:
        w(f"<th>{_e(f)}</th>")
    w("</tr>")
    for lr in res.levels:
        lv = lr.level
        w(f"<tr><td class='in'>{_e(lv.name)}</td><td class='in'>{_e(lv.comment)}</td>")
        for f in ed.level_fields:
            label = lv.labels.get(f)
            val = fmt_input(getattr(lv, f))
            w(f"<td class='in num' title='{_e(label or '')}'>{val}{(' <span class=small>(' + _e(label) + ')</span>') if label else ''}</td>")
        w("</tr>")
    w("</table>")

    w("<h2>4. Step-by-step results</h2>")
    for lr in res.levels:
        w(f"<h3>{_e(lr.level.name)}{(' - ' + _e(lr.level.comment)) if lr.level.comment else ''}</h3><table>")
        w("<tr><th>Item</th><th>Calculation</th><th>Result</th><th>Unit</th></tr>")
        for sym, expr, val in lr.steps:
            unit = ("m3/s" if sym in ("Design exhaust", "Make-up air", "Queue exhaust")
                    else "m" if sym in ("LB / LHU", "LLU") else "l/s")
            cls = "des" if sym == "Design exhaust" else "gov" if sym == lr.governing else ""
            w(f"<tr><td class='{cls}'>{_e(sym)}</td><td><code>{_e(expr)}</code></td>"
              f"<td class='num {cls}'>{fmt(val, 0 if unit == 'l/s' else 3)}</td><td>{unit}</td></tr>")
        w(f"</table><p class='small'>Governing component: <b>{_e(lr.governing)}</b></p>")

    w("<h2>5. Summary</h2><table><tr><th>Level</th><th>n1</th>")
    for s in ed.component_symbols:
        w(f"<th>{s} (l/s)</th>")
    w("<th>Governs</th><th>Design exhaust (m3/s)</th><th>Make-up (m3/s)</th>")
    if p.exit_lanes is not None:
        w("<th>LB/LHU (m)</th><th>LLU (m)</th><th>Queue exhaust (m3/s)</th>")
    w("</tr>")
    for lr in res.levels:
        w(f"<tr><td>{_e(lr.level.name)}</td><td class='num'>{fmt(lr.level.n1)}</td>")
        for s in ed.component_symbols:
            w(f"<td class='num res{' gov' if s == lr.governing else ''}'>{fmt(lr.components_ls[s])}</td>")
        w(f"<td>{lr.governing}</td><td class='num des'>{fmt(lr.design_exhaust_m3s, 2)}</td>"
          f"<td class='num des'>{fmt(lr.makeup_m3s, 2)}</td>")
        if p.exit_lanes is not None:
            w(f"<td class='num'>{fmt(lr.queue_lb_lhu_m, 1)}</td><td class='num'>{fmt(lr.queue_llu_m, 1)}</td>"
              f"<td class='num'>{fmt(lr.queue_exhaust_m3s, 2)}</td>")
        w("</tr>")
    span = len(ed.component_symbols) + 2
    w(f"<tr><th>TOTAL</th><th class='num'>{fmt(res.total_n1)}</th><th colspan='{span - 1}' style='text-align:right'>"
      f"Excluding loading dock:</th><th class='num'>{fmt(res.total_design_exhaust_m3s, 2)}</th>"
      f"<th class='num'>{fmt(res.total_makeup_m3s, 2)}</th>")
    if p.exit_lanes is not None:
        w(f"<th></th><th></th><th class='num'>{fmt(res.total_queue_exhaust_m3s, 2)}</th>")
    w("</tr></table><table class='kv'>")
    for k, v in summary_rows(res):
        w(f"<tr><th>{_e(k)}</th><td>{_e(v)}</td></tr>")
    w("</table>")
    if res.warnings:
        w("<div class='warn'><b>Warnings</b><ul>" + "".join(f"<li>{_e(x)}</li>" for x in res.warnings) + "</ul></div>")
    w(f"<footer>{_e(DISCLAIMER)}<br>Generated by carpark_vent {__version__}.</footer></body></html>")
    return "\n".join(o)


def write_html(res: ProjectResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(res), encoding="utf-8")
    return path
