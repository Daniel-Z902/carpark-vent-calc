"""Shared wording and formatting for all report formats.

Descriptions here are n2's own plain-English wording.  Do not paste
definitions or notes from the Standards (see AGENTS.md).
"""

from __future__ import annotations

from carpark_vent.editions import Edition
from carpark_vent.models import ProjectResult

DISCLAIMER = (
    "Factors and constants are those used in n2's car park ventilation workbook. "
    "Confirm all factors against a licensed copy of the cited Standard before issue."
)

UNITS = {
    "n1": "", "n2": "", "d1": "m", "d2": "m", "T": "", "E": "", "F": "",
    "P": "", "P1": "", "P2": "", "A": "m2",
}


def legend(ed: Edition) -> list[tuple[str, str]]:
    """Symbol definitions in our own words, by edition."""
    t_staff = ed.staff_table_ref or ""
    rows = [
        ("n1", "Car spaces on the level considered"),
        ("n2", "Car spaces elsewhere whose exit route passes through this level"),
        ("d1", "Mean exit driving distance for cars parked on this level (m)"),
        ("d2", "Mean driving distance through this level for the n2 cars (m)"),
    ]
    if ed.key == "2024":
        rows += [("P1", f"Parking usage factor for the n1 cars ({ed.usage_table_ref})"),
                 ("P2", f"Parking usage factor for the n2 cars ({ed.usage_table_ref})")]
    else:
        rows += [("P", f"Parking usage factor ({ed.usage_table_ref})")]
    rows += [("T", f"Vehicle type factor ({ed.vehicle_table_ref})")]
    if "E" in ed.level_fields:
        rows += [("E", f"Staff exposure factor ({t_staff})")]
    rows += [("F", f"Staff usage factor ({t_staff})"), ("A", "Floor area of the level (m2)")]
    return rows


QUEUE_LEGEND = [
    ("L", "Number of exit lanes"),
    ("nL", "Car spaces per exit lane = n1 / L"),
    ("LB", "Queue length, exit through a barrier or checkpoint (m)"),
    ("LLU", "Queue length, free exit to a light-traffic street (m)"),
    ("LHU", "Queue length, free exit to a heavy-traffic street (m)"),
]
QUEUE_EXPRESSIONS = [
    ("LB", "2.2 x nL x P - 200"),
    ("LLU", "2.2 x nL x P - 400"),
    ("LHU", "2.2 x nL x P - 200"),
    ("nL", "n1 / L"),
    ("Queue exhaust", "max(LB, LLU) x 300 / 1000  (m3/s)"),
]

USAGE_LABELS = {
    "residential": "Residential",
    "commercial": "Commercial",
    "retail": "Retail",
    "entertainment_sports": "Entertainment / sports",
    "vehicle_depot": "Vehicle depots",
}
VEHICLE_LABELS = {
    "none": "No special vehicle population",
    "diesel": "Diesel vehicles",
    "lpg": "LPG vehicles",
    "cng": "CNG vehicles",
    "electric": "Electric vehicles",
    "motorcycle": "Motorcycles",
}


def fmt(x: float | None, dp: int = 0) -> str:
    if x is None:
        return "-"
    return f"{x:,.{dp}f}"


def fmt_input(x: float | None) -> str:
    if x is None:
        return "-"
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.4g}" if abs(x) < 10 else f"{x:,.2f}"


def summary_rows(res: ProjectResult) -> list[tuple[str, str]]:
    ed = res.project.edition
    rows = [
        ("Basis", f"{ed.title}" + (" (superseded)" if ed.superseded else "")),
        ("Levels", str(len(res.levels))),
        ("Total car spaces (n1)", fmt(res.total_n1)),
    ]
    if res.total_area_m2:
        rows.append(("Total floor area", f"{fmt(res.total_area_m2)} m2"))
    rows += [
        ("Total design exhaust air flow", f"{fmt(res.total_design_exhaust_m3s, 2)} m3/s"),
        (f"Total design make-up air flow ({res.project.effective_makeup_ratio:.0%})",
         f"{fmt(res.total_makeup_m3s, 2)} m3/s"),
    ]
    if res.project.exit_lanes is not None:
        rows.append(("Total queue exhaust", f"{fmt(res.total_queue_exhaust_m3s, 2)} m3/s"))
    return rows
