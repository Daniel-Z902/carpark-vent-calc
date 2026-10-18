"""Edition-specific constants, exactly as used in ``carpark_calcs.xlsx``.

Every number here was read from the source workbook (cell references are
given in the comments).  Table numbers are cited as the workbook cites them.
Do NOT add text, tables or figures copied from the Standards themselves - if
a value is not in the workbook it does not belong here without Daniel's
sign-off (see AGENTS.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

# --- Queuing-area constants (identical on the 2012 and 2024 sheets) --------
# Workbook rows 8-11 of the queuing block, e.g. 2012 sheet L8:M11 and the
# formulas in columns R:T (2012) / S:U (2024).
QUEUE_COEFF = 2.2             # multiplier on (n1 / L) x P
QUEUE_OFFSET_HINDERED_M = 200.0     # LB (hindered exit) and LHU (heavy-traffic street)
QUEUE_OFFSET_LIGHT_M = 400.0        # LLU (unhindered exit, light-traffic street)
QUEUE_EXHAUST_LS_PER_M = 300.0      # "*300/1000" in the Queue Exhaust column (l/s per m, see METHOD.md)


@dataclass(frozen=True)
class Edition:
    """Constants for one edition sheet of the workbook."""

    key: str
    sheet_name: str
    title: str
    superseded: bool
    q_min_ls: float                  # minimum flow, cell B7
    area_rate_ls_per_m2: float       # Qc = rate x A
    makeup_ratio_default: float      # cell Q31
    makeup_ratio_editable: bool      # True where the workbook exposes it as an input cell
    staff_flow_ls: float             # Qb = staff_flow x F x T
    usage_factors: Mapping[str, float]
    vehicle_factors: Mapping[str, float]
    usage_table_ref: str
    vehicle_table_ref: str | None
    staff_table_ref: str | None
    # Symbols of the flow components in the order they appear in the sheet.
    component_symbols: tuple[str, ...] = field(default=())
    # Level fields used by this edition (for validation and reports).
    level_fields: tuple[str, ...] = field(default=())
    # Expression strings exactly as typed in the workbook (rows 7-10, column B).
    workbook_expressions: Mapping[str, str] = field(default_factory=dict)

    @property
    def short(self) -> str:
        return f"AS 1668.2-{self.key}"


# Default when an input file or the template command does not name an edition.
# 2012 is the edition in current use; 2024 is supported and selected explicitly.
DEFAULT_EDITION = "2012"

# P - parking usage factors (workbook rows 13-17, column D).
_USAGE = MappingProxyType(
    {
        "residential": 0.3,          # D13
        "commercial": 0.5,           # D14
        "retail": 0.7,               # D15
        "entertainment_sports": 1.0,  # D16
        "vehicle_depot": 2.4,        # D17
    }
)
# T - vehicle type factors (workbook rows 19-24, column D).
_VEHICLE = MappingProxyType(
    {
        "none": 1.0,         # D19 no special vehicle population
        "diesel": 2.4,       # D20
        "lpg": 1.0,          # D21
        "cng": 1.0,          # D22 (workbook label reads "CHG")
        "electric": 0.1,     # D23
        "motorcycle": 0.25,  # D24
    }
)

EDITIONS: Mapping[str, Edition] = MappingProxyType(
    {
        "2024": Edition(
            key="2024",
            sheet_name="Car Park Vent - AS1668 2024",
            title="AS 1668.2-2024",
            superseded=False,
            q_min_ls=1000.0,               # B7
            area_rate_ls_per_m2=1.5,       # P34: 1.5*L34
            makeup_ratio_default=0.8,      # Q31 (note Q30: "75-90%")
            makeup_ratio_editable=True,
            staff_flow_ls=1000.0,          # O34: 1000*I34*G34
            usage_factors=_USAGE,
            vehicle_factors=_VEHICLE,
            usage_table_ref="Table 4.1",
            vehicle_table_ref="Table 4.2",
            staff_table_ref="Table 4.3",
            component_symbols=("Q", "Qa", "Qb", "Qc"),
            level_fields=("n1", "n2", "d1", "d2", "T", "E", "F", "P1", "P2", "A"),
            workbook_expressions=MappingProxyType(
                {
                    "Q": "1000 l/s minimum",
                    "Qa": "0.4 x (P1 x (100 x n1 + n1 x d1) + P2 x (n2 x d2)) x E x T",
                    "Qb": "1000 x F x T",
                    "Qc": "1.5 x A l/s",
                }
            ),
        ),
        "2012": Edition(
            key="2012",
            sheet_name="Car Park Vent - AS1668 2012",
            title="AS 1668.2-2012",
            superseded=False,
            q_min_ls=2000.0,               # B7
            area_rate_ls_per_m2=2.5,       # O34: 2.5*K34
            makeup_ratio_default=0.8,      # Q31 (note Q30: "75-90%")
            makeup_ratio_editable=True,
            staff_flow_ls=2000.0,          # N34: 2000*I34*G34
            usage_factors=_USAGE,
            vehicle_factors=_VEHICLE,
            usage_table_ref="Table 4.1",
            vehicle_table_ref="Table 4.2",
            staff_table_ref="Table 4.3",
            component_symbols=("Q", "Qa", "Qb", "Qc"),
            level_fields=("n1", "n2", "d1", "d2", "T", "E", "F", "P", "A"),
            workbook_expressions=MappingProxyType(
                {
                    "Q": "2000 l/s minimum",
                    "Qa": "0.85 x P x (100 x n1 + n1 x d1 + n2 x d2) x E x T",
                    "Qb": "2000 x F x T",
                    "Qc": "2.5 x A l/s",
                }
            ),
        ),
    }
)


def get_edition(key: str | int) -> Edition:
    """Return the :class:`Edition` for ``"2012"`` (the default) or ``"2024"``."""
    k = str(key).strip()
    for prefix in ("AS1668.2-", "AS 1668.2-", "AS1668-", "AS 1668-"):
        if k.upper().startswith(prefix.upper()):
            k = k[len(prefix):]
    if k not in EDITIONS:
        names = ", ".join(dict.fromkeys((DEFAULT_EDITION, *EDITIONS)))
        raise ValueError(f"Unknown edition {key!r}; expected one of {names} ({DEFAULT_EDITION} is the default)")
    return EDITIONS[k]
