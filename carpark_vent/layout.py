"""Cell map of each sheet in ``carpark_calcs.xlsx``.

Used by the golden-value extractor (tools/extract_golden.py) and by the Excel
report writer, so the generated report keeps Daniel's column layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class SheetLayout:
    edition_key: str
    header_row: int                 # row with "Level", "Comment", "n1", ...
    units_row: int
    first_data_row: int
    last_data_row: int              # template rows available in the workbook
    total_row: int
    q_min_cell: str                 # B7
    exit_lanes_cell: str
    makeup_ratio_cell: str          # Q31 on both supported sheets
    # field -> column letter.  Inputs use Level field names; outputs use
    # component symbols plus the keys below.
    inputs: Mapping[str, str]
    outputs: Mapping[str, str]
    totals: Mapping[str, str]       # quantity -> column letter on total_row
    queue_block_col: str            # left column of the "Queuing Areas" block


_COMMON_OUT = ("design", "makeup", "lb_lhu", "llu", "queue")

LAYOUTS: Mapping[str, SheetLayout] = MappingProxyType(
    {
        "2024": SheetLayout(
            "2024", 32, 33, 34, 41, 42, "B7", "O12", "Q31",
            inputs=MappingProxyType(dict(name="A", comment="B", n1="C", n2="D", d1="E", d2="F", T="G", E="H",
                                         F="I", P1="J", P2="K", A="L")),
            outputs=MappingProxyType(dict(Q="M", Qa="N", Qb="O", Qc="P", design="Q", makeup="R", lb_lhu="S",
                                          llu="T", queue="U")),
            totals=MappingProxyType(dict(n1="C", A="L", design="Q", makeup="R")),
            queue_block_col="L",
        ),
        "2012": SheetLayout(
            "2012", 32, 33, 34, 41, 42, "B7", "O12", "Q31",
            inputs=MappingProxyType(dict(name="A", comment="B", n1="C", n2="D", d1="E", d2="F", T="G", E="H",
                                         F="I", P="J", A="K")),
            outputs=MappingProxyType(dict(Q="L", Qa="M", Qb="N", Qc="O", design="P", makeup="Q", lb_lhu="R",
                                          llu="S", queue="T")),
            totals=MappingProxyType(dict(n1="C", A="K", design="P", makeup="Q")),
            queue_block_col="L",
        ),
    }
)
