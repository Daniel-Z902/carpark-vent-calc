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
    makeup_ratio_cell: str | None   # None where the sheet hard-codes 0.75
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
        "2002": SheetLayout(
            "2002", 31, 32, 33, 39, 40, "B7", "N12", None,
            inputs=MappingProxyType(dict(name="A", comment="B", n1="C", n2="D", d1="E", d2="F", T="G", F="H",
                                         P="I", A="J")),
            outputs=MappingProxyType(dict(Q="K", Qa="L", Qb="M", Qc="N", design="O", makeup="P", lb_lhu="Q",
                                          llu="R", queue="S")),
            totals=MappingProxyType(dict(n1="C", design="O", makeup="P")),
            queue_block_col="K",
        ),
        "1991": SheetLayout(
            "1991", 25, 26, 27, 33, 34, "B7", "K12", None,
            inputs=MappingProxyType(dict(name="A", comment="B", n1="C", n2="D", d1="E", d2="F", d3="G", d4="H",
                                         P="I", A="J")),
            outputs=MappingProxyType(dict(Qa="K", Qb="L", Qc="M", Qd="N", design="O", makeup="P", lb_lhu="Q",
                                          llu="R", queue="S")),
            totals=MappingProxyType(dict(n1="C", design="O", makeup="P")),
            queue_block_col="H",
        ),
    }
)
