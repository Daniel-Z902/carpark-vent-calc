"""Unit tests of the individual formulas (hand-checked numbers)."""

import pytest

from carpark_vent import calcs
from carpark_vent.editions import EDITIONS, get_edition
from carpark_vent.loader import project_from_dict
from carpark_vent.models import Level


def test_qa_2024_hand_calc():
    # 0.4 x (0.3 x (100x200 + 200x60) + 0.5 x (50x40)) x 1 x 1 = 0.4 x (9600 + 1000) = 4240
    assert calcs.qa_2024(200, 50, 60, 40, 0.3, 0.5, 1, 1) == pytest.approx(4240)


def test_qa_2012_hand_calc():
    assert calcs.qa_2012(53, 64, 54.505, 68.97, 0.3, 1, 1) == pytest.approx(3213.725475)


def test_1991_exit_and_entry():
    assert calcs.qb_exit_1991(148, 180, 45, 15, 0.5) == pytest.approx(14496)
    assert calcs.qc_entry_1991(148, 180, 45, 15, 0.5) == pytest.approx(4832)


def test_queue_clamped_at_zero_and_positive_branch():
    assert calcs.queue_length_m(100, 1, 0.3, 200) == 0
    # 2.2 x 500 x 0.7 - 200 = 570 ; -400 = 370 ; exhaust = 570 x 0.3 = 171 m3/s
    assert calcs.queue_length_m(500, 1, 0.7, 200) == pytest.approx(570)
    assert calcs.queue_length_m(500, 1, 0.7, 400) == pytest.approx(370)
    assert calcs.queue_exhaust_m3s(570, 370) == pytest.approx(171)
    assert calcs.queue_length_m(500, 2, 0.7, 200) == pytest.approx(185)


def test_governing_component_and_minimum():
    ed = get_edition("2012")
    r = calcs.calculate_level(ed, Level(name="x", n1=1, P=0.3, A=10), 1, 0.8)
    assert r.governing == "Q" and r.design_exhaust_m3s == 2.0
    assert r.makeup_m3s == pytest.approx(1.6)


def test_queue_skipped_when_no_exit_lanes():
    r = calcs.calculate_level(get_edition("2012"), Level(name="x", n1=10, P=0.3), None, 0.8)
    assert r.queue_exhaust_m3s is None and r.queue_lb_lhu_m is None


def test_2024_uses_P1_for_queue_and_warns_on_missing_P2():
    p = project_from_dict({"edition": 2024, "levels": [{"name": "B1", "n1": 500, "n2": 10, "d2": 5, "P1": 0.7}]})
    res = calcs.calculate_project(p)
    assert res.levels[0].queue_lb_lhu_m == pytest.approx(570)
    assert any("P2" in w for w in res.warnings)


def test_factor_names_resolve():
    p = project_from_dict({"edition": "2012", "levels": [{"name": "B1", "n1": 1, "P": "retail", "T": "diesel"}]})
    assert p.levels[0].P == 0.7 and p.levels[0].T == 2.4


@pytest.mark.parametrize("bad", [
    {"edition": "2012", "levels": [{"name": "B1", "n1": 1, "P": 0.3, "P1": 0.3}]},   # P1 not a 2012 field
    {"edition": "2012", "levels": [{"name": "B1", "n1": 1, "P": "carwash"}]},          # unknown factor
    {"edition": "1999", "levels": [{"name": "B1", "n1": 1}]},                          # unknown edition
    {"edition": "2012", "levels": [{"name": "B1", "n1": 1, "p": 0.3}]},                # typo key
    {"edition": "2012", "levels": []},
])
def test_invalid_inputs_raise(bad):
    with pytest.raises(ValueError):
        calcs.calculate_project(project_from_dict(bad))


def test_missing_P_raises():
    with pytest.raises(ValueError, match="'P' is required"):
        calcs.calculate_project(project_from_dict({"edition": "2012", "levels": [{"name": "B1", "n1": 1}]}))


def test_superseded_editions_warn():
    for key in ("2002", "1991"):
        assert EDITIONS[key].superseded
        res = calcs.calculate_project(project_from_dict({"edition": key, "levels": [{"name": "B", "n1": 1, "P": 0.3}]}))
        assert any("SUPERSEDED" in w for w in res.warnings)
