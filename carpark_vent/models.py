"""Typed inputs and results.

Inputs are plain frozen dataclasses so the calculation layer stays pure and
dependency-free.  :mod:`carpark_vent.loader` turns YAML/JSON into these.
Units follow the workbook: counts, metres, m2, l/s for components and m3/s
for design flows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from carpark_vent.editions import DEFAULT_EDITION, Edition, get_edition


@dataclass(frozen=True)
class ProjectInfo:
    """Header block (workbook row 3: Project / rev / Arch)."""

    name: str = ""
    number: str = ""
    revision: str = "A"
    arch_reference: str = "-"        # workbook F3 "Arch: ..." (drawing set / date)
    client: str = ""
    prepared_by: str = ""
    checked_by: str = ""
    date: str = ""
    company: str = "n2 Engineering Consultants"
    notes: str = ""


@dataclass(frozen=True)
class Level:
    """One car park level - one row of the workbook level table.

    Not every field is used by every edition; see ``Edition.level_fields``.

    n1  car spaces on this level
    n2  car spaces elsewhere whose exit route passes through this level
    d1  mean exit driving distance for cars parked on this level (m)
    d2  mean exit distance through this level for the n2 cars (m)
    T   vehicle type factor
    E   staff exposure factor
    F   staff usage factor
    P   parking usage factor (2012)
    P1  parking usage factor for the n1 cars (2024)
    P2  parking usage factor for the n2 cars (2024)
    A   floor area (m2)
    """

    name: str
    n1: float
    comment: str = ""
    n2: float = 0.0
    d1: float = 0.0
    d2: float = 0.0
    T: float = 1.0
    E: float = 1.0
    F: float = 1.0
    P: float | None = None
    P1: float | None = None
    P2: float | None = None
    A: float = 0.0
    # Human-readable labels when a factor was given by name (e.g. "residential").
    labels: dict[str, str] = field(default_factory=dict, compare=False)


@dataclass(frozen=True)
class Project:
    """A full calculation: header, edition, global inputs and levels.

    ``edition_key`` defaults to 2012. Pass ``"2024"`` to use that edition.
    """

    levels: tuple[Level, ...]
    edition_key: str = DEFAULT_EDITION
    info: ProjectInfo = field(default_factory=ProjectInfo)
    exit_lanes: float | None = 1.0      # workbook "L = No. of exit lanes" (O12); None = queue not assessed
    makeup_ratio: float | None = None   # None -> edition default (0.8)
    queue_note: str = "No dedicated queuing areas applicable"   # workbook L19 banner

    @property
    def edition(self) -> Edition:
        return get_edition(self.edition_key)

    @property
    def effective_makeup_ratio(self) -> float:
        return self.edition.makeup_ratio_default if self.makeup_ratio is None else float(self.makeup_ratio)


@dataclass(frozen=True)
class LevelResult:
    level: Level
    components_ls: dict[str, float]          # edition symbols in sheet order, l/s
    governing: str                           # symbol of the largest component (first on ties)
    design_exhaust_m3s: float
    makeup_m3s: float
    queue_lb_lhu_m: float | None             # LB / LHU queue length (m)
    queue_llu_m: float | None                # LLU queue length (m)
    queue_exhaust_m3s: float | None
    steps: tuple[tuple[str, str, float], ...] = ()   # (symbol, substituted expression, value) for reports
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectResult:
    project: Project
    levels: tuple[LevelResult, ...]
    total_n1: float
    total_area_m2: float
    total_design_exhaust_m3s: float
    total_makeup_m3s: float
    total_queue_exhaust_m3s: float
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly summary of the results."""
        ed = self.project.edition
        return {
            "edition": ed.title,
            "project": self.project.info.__dict__.copy(),
            "global_inputs": {
                "exit_lanes": self.project.exit_lanes,
                "makeup_ratio": self.project.effective_makeup_ratio,
            },
            "levels": [
                {
                    "name": r.level.name,
                    "comment": r.level.comment,
                    "inputs": {f: getattr(r.level, f) for f in ed.level_fields},
                    "components_ls": r.components_ls,
                    "governing": r.governing,
                    "design_exhaust_m3s": r.design_exhaust_m3s,
                    "makeup_m3s": r.makeup_m3s,
                    "queue_lb_lhu_m": r.queue_lb_lhu_m,
                    "queue_llu_m": r.queue_llu_m,
                    "queue_exhaust_m3s": r.queue_exhaust_m3s,
                    "warnings": list(r.warnings),
                }
                for r in self.levels
            ],
            "totals": {
                "n1": self.total_n1,
                "area_m2": self.total_area_m2,
                "design_exhaust_m3s": self.total_design_exhaust_m3s,
                "makeup_m3s": self.total_makeup_m3s,
                "queue_exhaust_m3s": self.total_queue_exhaust_m3s,
            },
            "warnings": list(self.warnings),
        }
