"""Golden tests: Python results vs the Excel *cached* values in carpark_calcs.xlsx.

Cases are stored in tests/golden/excel_cached.json (regenerate with
``python tools/extract_golden.py``).  Tolerance: 1e-6 relative.
"""

import pytest

from carpark_vent import calculate_project
from carpark_vent.loader import project_from_dict

from conftest import close, load_cases

CASES = [c for c in load_cases("excel_cached.json") if c["input"]["levels"]]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_levels_match_excel(case):
    res = calculate_project(project_from_dict(case["input"]))
    for r, exp, cells in zip(res.levels, case["expected"]["levels"], case["cells"]):
        for sym, val in r.components_ls.items():
            assert close(val, exp[sym]), f"{r.level.name} {sym} ({cells[sym]}): {val} != {exp[sym]}"
        assert close(r.design_exhaust_m3s, exp["design"]), cells["design"]
        assert close(r.makeup_m3s, exp["makeup"]), cells["makeup"]
        assert close(r.queue_lb_lhu_m, exp["lb_lhu"]), cells["lb_lhu"]
        assert close(r.queue_llu_m, exp["llu"]), cells["llu"]
        assert close(r.queue_exhaust_m3s, exp["queue"]), cells["queue"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_totals_match_excel(case):
    res = calculate_project(project_from_dict(case["input"]))
    t = case["expected"]["totals"]
    assert close(res.total_n1, t["n1"])
    assert close(res.total_design_exhaust_m3s, t["design"])
    assert close(res.total_makeup_m3s, t["makeup"])
    if "A" in t:
        assert close(res.total_area_m2, t["A"])


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_minimum_flow_constant_matches_cell_B7(case):
    from carpark_vent.editions import get_edition

    assert get_edition(case["input"]["edition"]).q_min_ls == case["workbook_q_min"]


def test_bitwise_identical_where_possible():
    """Operand order mirrors Excel, so the 2012 example is exact, not just within tolerance."""
    case = next(c for c in CASES if c["id"] == "excel-2012")
    res = calculate_project(project_from_dict(case["input"]))
    assert res.levels[0].components_ls["Qa"] == case["expected"]["levels"][0]["Qa"]
    assert res.total_makeup_m3s == case["expected"]["totals"]["makeup"]


def test_2024_sheet_has_no_example_data():
    """The 2024 sheet is an empty template; covered by LibreOffice cases instead."""
    case = next(c for c in load_cases("excel_cached.json") if c["id"] == "excel-2024")
    assert case["input"]["levels"] == []
    assert case["expected"]["totals"]["design"] == 0


def test_distance_list_is_averaged_like_sheet_E34():
    case = next(c for c in CASES if c["id"] == "excel-2012")
    data = {**case["input"], "levels": [dict(lv) for lv in case["input"]["levels"]]}
    data["levels"][0]["d1"] = [91.31, 71.09, 48.2, 53.57, 33.53, 12.21]   # 2012 sheet E34
    res = calculate_project(project_from_dict(data))
    assert res.levels[0].level.d1 == case["input"]["levels"][0]["d1"]
    assert close(res.levels[0].components_ls["Qa"], case["expected"]["levels"][0]["Qa"])
