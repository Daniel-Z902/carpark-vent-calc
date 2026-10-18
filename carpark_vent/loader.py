"""Load a project from a YAML or JSON file (or a plain dict).

Schema (see examples/ and README.md)::

    edition: "2012"            # 2024 | 2012 | 2002 | 1991
    project: {name, number, revision, arch_reference, client,
              prepared_by, checked_by, date, company, notes}
    exit_lanes: 1              # L; null to skip the queuing assessment
    makeup_ratio: 0.8          # optional, defaults to the edition value
    queue_note: "..."          # optional banner text for the queuing block
    levels:
      - name: BASEMENT 1
        comment: ""
        n1: 53
        n2: 64
        d1: [93.95, 73.73, 53.1]   # a list is averaged, like =(a+b+c)/3 in the sheet
        d2: 68.97
        T: none                  # number or a key of the edition's vehicle factors
        E: 1
        F: 1
        P: residential           # number or a key of the edition's usage factors
        A: 2344.15
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from carpark_vent.editions import Edition, get_edition
from carpark_vent.models import Level, Project, ProjectInfo

_LEVEL_KEYS = {"name", "comment", "n1", "n2", "d1", "d2", "d3", "d4", "T", "E", "F", "P", "P1", "P2", "A"}
_DISTANCES = ("d1", "d2", "d3", "d4")
_TOP_KEYS = {"edition", "project", "exit_lanes", "makeup_ratio", "queue_note", "levels"}


def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where}: expected a number, got {value!r}")
    return float(value)


def _distance(value: Any, where: str) -> float:
    """A distance may be a number or a list of numbers (arithmetic mean)."""
    if isinstance(value, Sequence) and not isinstance(value, str):
        if not value:
            raise ValueError(f"{where}: empty distance list")
        vals = [_number(v, where) for v in value]
        return sum(vals) / len(vals)
    return _number(value, where)


def _factor(value: Any, table: Mapping[str, float], table_name: str, where: str) -> tuple[float, str | None]:
    if isinstance(value, str):
        key = value.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        if key not in table:
            raise ValueError(f"{where}: unknown {table_name} {value!r}; choose from {sorted(table)} or give a number")
        return table[key], key
    return _number(value, where), None


def level_from_dict(data: Mapping[str, Any], edition: Edition, index: int = 0) -> Level:
    unknown = set(data) - _LEVEL_KEYS
    if unknown:
        raise ValueError(f"levels[{index}]: unknown keys {sorted(unknown)}")
    name = str(data.get("name", f"Level {index + 1}"))
    where = f"levels[{index}] ({name})"
    if "n1" not in data:
        raise ValueError(f"{where}: 'n1' is required")
    unused = {k for k in data if k in _LEVEL_KEYS - {"name", "comment"}} - set(edition.level_fields)
    if unused:
        raise ValueError(f"{where}: {sorted(unused)} not used by {edition.title} (uses {list(edition.level_fields)})")

    kw: dict[str, Any] = {"name": name, "comment": str(data.get("comment", "") or "")}
    labels: dict[str, str] = {}
    for key in ("n1", "n2", "E", "F", "A"):
        if key in data and data[key] is not None:
            kw[key] = _number(data[key], f"{where}.{key}")
    for key in _DISTANCES:
        if key in data and data[key] is not None:
            kw[key] = _distance(data[key], f"{where}.{key}")
    for key in ("P", "P1", "P2"):
        if key in data and data[key] is not None:
            kw[key], label = _factor(data[key], edition.usage_factors, "usage factor", f"{where}.{key}")
            if label:
                labels[key] = label
    if "T" in data and data["T"] is not None:
        kw["T"], label = _factor(data["T"], edition.vehicle_factors, "vehicle type", f"{where}.T")
        if label:
            labels["T"] = label
    return Level(labels=labels, **kw)


def project_from_dict(data: Mapping[str, Any]) -> Project:
    unknown = set(data) - _TOP_KEYS
    if unknown:
        raise ValueError(f"unknown top-level keys {sorted(unknown)}")
    if "edition" not in data:
        raise ValueError("'edition' is required (2024, 2012, 2002 or 1991)")
    edition = get_edition(data["edition"])
    info_data = dict(data.get("project") or {})
    info_fields = set(ProjectInfo.__dataclass_fields__)
    bad = set(info_data) - info_fields
    if bad:
        raise ValueError(f"project: unknown keys {sorted(bad)}")
    info = ProjectInfo(**{k: ("" if v is None else str(v)) for k, v in info_data.items()})
    levels_data = data.get("levels") or []
    if not levels_data:
        raise ValueError("at least one level is required")
    levels = tuple(level_from_dict(lv, edition, i) for i, lv in enumerate(levels_data))
    exit_lanes = data.get("exit_lanes", 1)
    makeup = data.get("makeup_ratio")
    kwargs: dict[str, Any] = {}
    if "queue_note" in data:
        kwargs["queue_note"] = str(data["queue_note"] or "")
    return Project(
        edition_key=edition.key,
        levels=levels,
        info=info,
        exit_lanes=None if exit_lanes is None else _number(exit_lanes, "exit_lanes"),
        makeup_ratio=None if makeup is None else _number(makeup, "makeup_ratio"),
        **kwargs,
    )


def load_project(path: str | Path) -> Project:
    """Load a ``.yaml``/``.yml`` or ``.json`` project file."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(text)
    elif p.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"{p}: expected a .yaml, .yml or .json file")
    if not isinstance(data, Mapping):
        raise ValueError(f"{p}: top level must be a mapping")
    return project_from_dict(data)
