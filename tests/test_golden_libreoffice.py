"""Golden tests against LibreOffice recalculations of Daniel's unchanged formulas
with synthetic inputs (tests/golden/libreoffice_recalc.json, built by
tools/make_lo_scenarios.py).  Covers the 2024 sheet and non-zero queues.

One documented workbook quirk is asserted rather than hidden: rows whose
queue cells are typed-in 0 instead of formulas (2012/2024 rows 34 and 37-41).
"""

import pytest

from carpark_vent.calcs import calculate_level
from carpark_vent.loader import project_from_dict

from conftest import close, load_cases

CASES = load_cases("libreoffice_recalc.json")


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_matches_libreoffice(case):
    project = project_from_dict(case["input"])
    ed = project.edition
    tot_design = tot_makeup = 0.0
    for lv, exp in zip(project.levels, case["expected"]["levels"]):
        assert exp["sheet_area_rate"] == ed.area_rate_ls_per_m2
        r = calculate_level(ed, lv, project.exit_lanes, project.effective_makeup_ratio)
        for sym, val in r.components_ls.items():
            assert close(val, exp[sym]), f"row {exp['row']} {sym}: {val} != {exp[sym]}"
        assert close(r.design_exhaust_m3s, exp["design"])
        assert close(r.makeup_m3s, exp["makeup"])
        if exp["queue_cells_are_formulas"]:
            assert close(r.queue_lb_lhu_m, exp["lb_lhu"]), f"row {exp['row']}"
            assert close(r.queue_llu_m, exp["llu"]), f"row {exp['row']}"
            assert close(r.queue_exhaust_m3s, exp["queue"]), f"row {exp['row']}"
        else:
            # Typed-in zeros in the workbook: the sheet cannot report a queue on this row.
            assert exp["lb_lhu"] == 0 and exp["llu"] == 0 and exp["queue"] == 0
        tot_design += r.design_exhaust_m3s
        tot_makeup += r.makeup_m3s
    assert close(tot_design, case["expected"]["totals"]["design"])
    assert close(tot_makeup, case["expected"]["totals"]["makeup"])
    assert close(sum(lv.n1 for lv in project.levels), case["expected"]["totals"]["n1"])


def test_scenarios_exercise_nonzero_queues_on_every_edition():
    for key in ("2024", "2012"):
        assert any(
            r["queue"] > 0 for c in CASES if c["input"]["edition"] == key for r in c["expected"]["levels"]
        ), key
