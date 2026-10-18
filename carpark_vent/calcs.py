"""Pure calculation functions.

Each function mirrors one workbook formula; the arithmetic is written in the
same operand order as the Excel cell so results are bit-for-bit identical to
Excel's cached values wherever Excel uses IEEE doubles (which it does).

Cell references below use the 2012 sheet unless stated; METHOD.md has the
full map for every sheet.
"""

from __future__ import annotations

from carpark_vent.editions import (
    QUEUE_COEFF,
    QUEUE_EXHAUST_LS_PER_M,
    QUEUE_OFFSET_HINDERED_M,
    QUEUE_OFFSET_LIGHT_M,
    Edition,
)
from carpark_vent.models import Level, LevelResult, Project, ProjectResult

# --------------------------------------------------------------------------
# Car-movement (exit / entry) components
# --------------------------------------------------------------------------


def qa_2024(n1: float, n2: float, d1: float, d2: float, P1: float, P2: float, E: float, T: float) -> float:
    """2024 sheet N34: =0.4*(P1*(100*n1+n1*d1)+P2*(n2*d2))*E*T   [l/s]."""
    return 0.4 * (P1 * (100 * n1 + n1 * d1) + P2 * (n2 * d2)) * E * T


def qa_2012(n1: float, n2: float, d1: float, d2: float, P: float, T: float, E: float) -> float:
    """2012 sheet M34: =P*0.85*(100*n1+n1*d1+n2*d2)*T*E   [l/s]."""
    return P * 0.85 * (100 * n1 + n1 * d1 + n2 * d2) * T * E


# --------------------------------------------------------------------------
# Staff, area and minimum components
# --------------------------------------------------------------------------


def staff_flow(staff_flow_ls: float, F: float, T: float) -> float:
    """Qb: =1000*F*T (2024 O34) or =2000*F*T (2012 N34)   [l/s]."""
    return staff_flow_ls * F * T


def area_flow(rate_ls_per_m2: float, A: float) -> float:
    """Qc: =rate*A, rate 1.5 (2024) or 2.5 (2012) l/s.m2   [l/s]."""
    return rate_ls_per_m2 * A


def design_exhaust_m3s(components_ls: list[float]) -> float:
    """=MAX(Q:Qc)/1000  (2012 P34)   [m3/s]."""
    return max(components_ls) / 1000


def makeup_m3s(ratio: float, design_m3s: float) -> float:
    """=$Q$31 times the design-exhaust cell (2012 P34, 2024 Q34)   [m3/s]."""
    return ratio * design_m3s


# --------------------------------------------------------------------------
# Queuing areas
# --------------------------------------------------------------------------


def queue_length_m(n1: float, exit_lanes: float, P: float, offset_m: float) -> float:
    """=IF((2.2*(n1/L)*P-offset)<0,0,2.2*(n1/L)*P-offset)   [m].

    offset = 200 for LB / LHU (2012 R35) and 400 for LLU (2012 S35).
    """
    value = QUEUE_COEFF * (n1 / exit_lanes) * P - offset_m
    return 0 if value < 0 else value


def queue_exhaust_m3s(lb_lhu_m: float, llu_m: float) -> float:
    """=IF(MAX(LB:LLU)<0,0,MAX(LB:LLU)*300/1000)   (2012 T35)   [m3/s]."""
    m = max(lb_lhu_m, llu_m)
    return 0 if m < 0 else m * QUEUE_EXHAUST_LS_PER_M / 1000


# --------------------------------------------------------------------------
# Level and project assembly
# --------------------------------------------------------------------------


def _g(x: float) -> str:
    """Compact number formatting for substituted expressions."""
    return f"{x:.6g}" if isinstance(x, float) and not float(x).is_integer() else f"{x:g}"


def _components(ed: Edition, lv: Level) -> tuple[dict[str, float], list[tuple[str, str, float]], list[str]]:
    warnings: list[str] = []
    steps: list[tuple[str, str, float]] = []
    comps: dict[str, float] = {}

    def need(name: str) -> float:
        v = getattr(lv, name)
        if v is None:
            raise ValueError(f"Level {lv.name!r}: '{name}' is required for {ed.title}")
        return float(v)

    if ed.key == "2024":
        P1 = need("P1")
        if lv.P2 is None:
            P2 = 0.0
            if lv.n2 and lv.d2:
                warnings.append(
                    f"Level {lv.name!r}: P2 not given; treated as 0 (as a blank cell in the workbook) "
                    "although n2 x d2 > 0"
                )
        else:
            P2 = float(lv.P2)
        comps["Q"] = ed.q_min_ls
        steps.append(("Q", "minimum", comps["Q"]))
        comps["Qa"] = qa_2024(lv.n1, lv.n2, lv.d1, lv.d2, P1, P2, lv.E, lv.T)
        steps.append((
            "Qa",
            f"0.4 x ({_g(P1)} x (100 x {_g(lv.n1)} + {_g(lv.n1)} x {_g(lv.d1)}) + {_g(P2)} x ({_g(lv.n2)} x {_g(lv.d2)}))"
            f" x {_g(lv.E)} x {_g(lv.T)}",
            comps["Qa"],
        ))
        comps["Qb"] = staff_flow(ed.staff_flow_ls, lv.F, lv.T)
        steps.append(("Qb", f"{_g(ed.staff_flow_ls)} x {_g(lv.F)} x {_g(lv.T)}", comps["Qb"]))
        comps["Qc"] = area_flow(ed.area_rate_ls_per_m2, lv.A)
        steps.append(("Qc", f"{_g(ed.area_rate_ls_per_m2)} x {_g(lv.A)}", comps["Qc"]))
    elif ed.key == "2012":
        P = need("P")
        comps["Q"] = ed.q_min_ls
        steps.append(("Q", "minimum", comps["Q"]))
        comps["Qa"] = qa_2012(lv.n1, lv.n2, lv.d1, lv.d2, P, lv.T, lv.E)
        steps.append((
            "Qa",
            f"{_g(P)} x 0.85 x (100 x {_g(lv.n1)} + {_g(lv.n1)} x {_g(lv.d1)} + {_g(lv.n2)} x {_g(lv.d2)})"
            f" x {_g(lv.T)} x {_g(lv.E)}",
            comps["Qa"],
        ))
        comps["Qb"] = staff_flow(ed.staff_flow_ls, lv.F, lv.T)
        steps.append(("Qb", f"{_g(ed.staff_flow_ls)} x {_g(lv.F)} x {_g(lv.T)}", comps["Qb"]))
        comps["Qc"] = area_flow(ed.area_rate_ls_per_m2, lv.A)
        steps.append(("Qc", f"{_g(ed.area_rate_ls_per_m2)} x {_g(lv.A)}", comps["Qc"]))
    else:  # pragma: no cover - guarded by get_edition
        raise ValueError(ed.key)
    return comps, steps, warnings


def queue_P(ed: Edition, lv: Level) -> float:
    """Parking usage factor used in the queue formulas (P1 on the 2024 sheet, column J)."""
    v = lv.P1 if ed.key == "2024" else lv.P
    return float(v) if v is not None else 0.0


def calculate_level(
    edition: Edition, level: Level, exit_lanes: float | None, makeup_ratio: float
) -> LevelResult:
    comps, steps, warnings = _components(edition, level)
    design = design_exhaust_m3s(list(comps.values()))
    governing = max(comps, key=lambda k: comps[k])  # first max in sheet order
    makeup = makeup_m3s(makeup_ratio, design)
    steps.append(("Design exhaust", f"max({', '.join(comps)}) / 1000", design))
    steps.append(("Make-up air", f"{_g(makeup_ratio)} x {_g(design)}", makeup))

    lb = llu = qx = None
    if exit_lanes is not None:
        if exit_lanes <= 0:
            raise ValueError("exit_lanes must be > 0 (or null to skip the queue assessment)")
        P = queue_P(edition, level)
        lb = queue_length_m(level.n1, exit_lanes, P, QUEUE_OFFSET_HINDERED_M)
        llu = queue_length_m(level.n1, exit_lanes, P, QUEUE_OFFSET_LIGHT_M)
        qx = queue_exhaust_m3s(lb, llu)
        nl = f"({_g(level.n1)} / {_g(exit_lanes)})"
        steps.append(("LB / LHU", f"max(0, 2.2 x {nl} x {_g(P)} - 200)", lb))
        steps.append(("LLU", f"max(0, 2.2 x {nl} x {_g(P)} - 400)", llu))
        steps.append(("Queue exhaust", "max(LB, LLU) x 300 / 1000", qx))

    return LevelResult(
        level=level,
        components_ls=comps,
        governing=governing,
        design_exhaust_m3s=design,
        makeup_m3s=makeup,
        queue_lb_lhu_m=lb,
        queue_llu_m=llu,
        queue_exhaust_m3s=qx,
        steps=tuple(steps),
        warnings=tuple(warnings),
    )


def calculate_project(project: Project) -> ProjectResult:
    ed = project.edition
    ratio = project.effective_makeup_ratio
    warnings: list[str] = []
    if not ed.makeup_ratio_editable and project.makeup_ratio is not None and project.makeup_ratio != ed.makeup_ratio_default:
        warnings.append(
            f"{ed.title} sheet hard-codes the make-up ratio at {ed.makeup_ratio_default}; "
            f"using the project override {project.makeup_ratio}"
        )
    if ed.superseded:
        warnings.append(f"{ed.title} is marked SUPERSEDED in the source workbook")

    results = tuple(calculate_level(ed, lv, project.exit_lanes, ratio) for lv in project.levels)
    for r in results:
        warnings.extend(r.warnings)

    # Totals row (2012 row 42): =SUM(C34:C41), =SUM(K34:K41), =SUM(P34:P41), =SUM(Q34:Q41)
    return ProjectResult(
        project=project,
        levels=results,
        total_n1=sum(r.level.n1 for r in results),
        total_area_m2=sum(r.level.A for r in results),
        total_design_exhaust_m3s=sum(r.design_exhaust_m3s for r in results),
        total_makeup_m3s=sum(r.makeup_m3s for r in results),
        total_queue_exhaust_m3s=sum(r.queue_exhaust_m3s or 0.0 for r in results),
        warnings=tuple(warnings),
    )
