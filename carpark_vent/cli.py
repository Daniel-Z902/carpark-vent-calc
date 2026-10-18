"""Command line interface.

    carpark-vent run examples/example_2012.yaml -o build/ --formats xlsx,html,pdf,json
    carpark-vent editions
    carpark-vent template 2024 > my_project.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from carpark_vent import __version__
from carpark_vent.calcs import calculate_project
from carpark_vent.editions import EDITIONS, get_edition
from carpark_vent.loader import load_project
from carpark_vent.models import ProjectResult
from carpark_vent.report.common import fmt

FORMATS = ("xlsx", "html", "pdf", "json")


def _print_summary(res: ProjectResult) -> None:
    ed = res.project.edition
    print(f"{res.project.info.name or '(unnamed project)'} - {ed.title}")
    syms = ed.component_symbols
    head = f"{'Level':<16}" + "".join(f"{s + ' l/s':>10}" for s in syms) + f"{'Gov':>5}{'Exh m3/s':>10}{'MU m3/s':>9}{'Queue':>8}"
    print(head)
    print("-" * len(head))
    for r in res.levels:
        q = "-" if r.queue_exhaust_m3s is None else f"{r.queue_exhaust_m3s:.2f}"
        print(f"{r.level.name[:16]:<16}" + "".join(f"{fmt(r.components_ls[s]):>10}" for s in syms)
              + f"{r.governing:>5}{r.design_exhaust_m3s:>10.2f}{r.makeup_m3s:>9.2f}{q:>8}")
    print("-" * len(head))
    print(f"{'TOTAL':<16}" + " " * (10 * len(syms) + 5)
          + f"{res.total_design_exhaust_m3s:>10.2f}{res.total_makeup_m3s:>9.2f}{res.total_queue_exhaust_m3s:>8.2f}")
    for w in res.warnings:
        print(f"WARNING: {w}", file=sys.stderr)


def cmd_run(a: argparse.Namespace) -> int:
    project = load_project(a.input)
    res = calculate_project(project)
    _print_summary(res)
    formats = [f.strip().lower() for f in a.formats.split(",") if f.strip()]
    bad = set(formats) - set(FORMATS)
    if bad:
        raise SystemExit(f"unknown format(s) {sorted(bad)}; choose from {FORMATS}")
    out = Path(a.output)
    stem = a.stem or Path(a.input).stem
    written = []
    for f in formats:
        target = out / f"{stem}.{f}"
        if f == "xlsx":
            from carpark_vent.report.excel import write_excel

            written.append(write_excel(res, target, formulas=a.excel_formulas))
        elif f == "html":
            from carpark_vent.report.html import write_html

            written.append(write_html(res, target))
        elif f == "pdf":
            try:
                from carpark_vent.report.pdf import write_pdf
            except ImportError:
                raise SystemExit("PDF output needs reportlab: pip install '.[pdf]'") from None
            written.append(write_pdf(res, target))
        elif f == "json":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(res.to_dict(), indent=2) + "\n", encoding="utf-8")
            written.append(target)
    for p in written:
        print(f"wrote {p}")
    return 0


def cmd_editions(_: argparse.Namespace) -> int:
    for ed in EDITIONS.values():
        print(f"{ed.key}  {ed.title}{'  (superseded)' if ed.superseded else ''}")
        for sym, expr in ed.workbook_expressions.items():
            print(f"      {sym:<3} = {expr}")
        print(f"      make-up ratio {ed.makeup_ratio_default:g}; level fields: {', '.join(ed.level_fields)}")
        print(f"      usage factors: {dict(ed.usage_factors)}")
        if ed.vehicle_factors:
            print(f"      vehicle factors: {dict(ed.vehicle_factors)}")
    return 0


TEMPLATE_VALUES = {"n1": 50, "n2": 0, "d1": 60.0, "d2": 0.0, "d3": 0.0, "d4": 0.0, "T": "none", "E": 1, "F": 1,
                   "P": "residential", "P1": "residential", "P2": "residential", "A": 2000.0}


def cmd_template(a: argparse.Namespace) -> int:
    ed = get_edition(a.edition)
    lines = [
        f"# carpark_vent input - {ed.title}",
        f'edition: "{ed.key}"',
        "project:",
        '  name: "Project name"',
        '  number: ""',
        "  revision: A",
        '  arch_reference: "-"',
        '  client: ""',
        "  prepared_by: Daniel Zhang",
        '  checked_by: ""',
        '  date: ""',
        "exit_lanes: 1            # null to skip the queuing assessment",
    ]
    if ed.makeup_ratio_editable:
        lines.append(f"makeup_ratio: {ed.makeup_ratio_default}       # workbook note: 75-90%")
    lines.append("levels:")
    lines.append("  - name: BASEMENT 1")
    lines.append('    comment: ""')
    for f in ed.level_fields:
        if f == "T" and not ed.vehicle_factors:
            continue
        lines.append(f"    {f}: {TEMPLATE_VALUES[f]}")
    print("\n".join(lines))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="carpark-vent", description="Car park mechanical ventilation calculations")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="calculate a project file and write reports")
    r.add_argument("input", help="project file (.yaml/.yml/.json)")
    r.add_argument("-o", "--output", default="build", help="output directory (default: build)")
    r.add_argument("--formats", default="xlsx,html,pdf,json", help=f"comma list from {','.join(FORMATS)}")
    r.add_argument("--stem", help="output file name stem (default: input file stem)")
    r.add_argument("--excel-formulas", action="store_true",
                   help="write live Excel formulas in the mirrored sheet instead of values")
    r.set_defaults(func=cmd_run)
    e = sub.add_parser("editions", help="list supported editions and their constants")
    e.set_defaults(func=cmd_editions)
    t = sub.add_parser("template", help="print a starter YAML input for an edition")
    t.add_argument("edition", choices=list(EDITIONS))
    t.set_defaults(func=cmd_template)
    a = ap.parse_args(argv)
    try:
        return a.func(a)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
