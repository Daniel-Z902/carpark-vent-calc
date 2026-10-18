"""Extract golden test cases (inputs + Excel cached results) from carpark_calcs.xlsx.

    python tools/extract_golden.py [path/to/carpark_calcs.xlsx] [-o tests/golden/excel_cached.json]

Loads the workbook twice (formulas and cached values).  Only numbers, cell
references and Daniel's own formula strings are written - no descriptive
text from the sheets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import openpyxl

from carpark_vent.editions import EDITIONS
from carpark_vent.layout import LAYOUTS


def _num(v):
    return None if v is None or v == "" else v


def extract(path: Path) -> dict:
    wf = openpyxl.load_workbook(path, data_only=False)
    wv = openpyxl.load_workbook(path, data_only=True)
    cases = []
    for key, ed in EDITIONS.items():
        lay = LAYOUTS[key]
        f, v = wf[ed.sheet_name], wv[ed.sheet_name]
        levels, expected, cells = [], [], []
        for row in range(lay.first_data_row, lay.last_data_row + 1):
            if v[f"{lay.inputs['n1']}{row}"].value is None:
                continue
            lv = {}
            for field, col in lay.inputs.items():
                val = v[f"{col}{row}"].value
                if val is not None and val != "":
                    lv[field] = val if field not in ("name", "comment") else str(val)
            lv.setdefault("name", f"row {row}")
            levels.append(lv)
            out = {k: _num(v[f"{col}{row}"].value) for k, col in lay.outputs.items()}
            out["queue_cells_are_formulas"] = all(
                isinstance(f[f"{lay.outputs[k]}{row}"].value, str) and f[f"{lay.outputs[k]}{row}"].value.startswith("=")
                for k in ("lb_lhu", "llu")
            )
            expected.append(out)
            cells.append({k: f"{col}{row}" for k, col in {**lay.inputs, **lay.outputs}.items()})
        totals = {k: _num(v[f"{col}{lay.total_row}"].value) for k, col in lay.totals.items()}
        exit_lanes = v[lay.exit_lanes_cell].value
        case = {
            "id": f"excel-{key}",
            "source": f"Excel cached values, sheet '{ed.sheet_name}'",
            "input": {
                "edition": key,
                "exit_lanes": None if exit_lanes in (None, "") else exit_lanes,
                "makeup_ratio": v[lay.makeup_ratio_cell].value if lay.makeup_ratio_cell else None,
                "levels": levels,
            },
            "workbook_q_min": v[lay.q_min_cell].value,
            "expected": {"levels": expected, "totals": totals},
            "cells": cells,
        }
        cases.append(case)
    return {"workbook": path.name, "cases": cases}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("xlsx", nargs="?", default="carpark_calcs.xlsx")
    ap.add_argument("-o", "--output", default="tests/golden/excel_cached.json")
    a = ap.parse_args()
    data = extract(Path(a.xlsx))
    Path(a.output).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {a.output}: " + ", ".join(f"{c['id']} ({len(c['input']['levels'])} levels)" for c in data["cases"]))


if __name__ == "__main__":
    main()
