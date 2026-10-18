"""If the source workbook is available locally, check the committed golden JSON
still matches it (catches edits to carpark_calcs.xlsx).  Skipped in CI/Codex,
where the workbook is not committed.  Override the path with CARPARK_XLSX."""

import json
import os
from pathlib import Path

import pytest

from conftest import GOLDEN, ROOT

XLSX = Path(os.environ.get("CARPARK_XLSX", ROOT / "carpark_calcs.xlsx"))


@pytest.mark.skipif(not XLSX.exists(), reason="carpark_calcs.xlsx not present")
def test_golden_json_is_up_to_date():
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from extract_golden import extract

    fresh = extract(XLSX)
    committed = json.loads((GOLDEN / "excel_cached.json").read_text())
    assert fresh["cases"] == committed["cases"]
