import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).parent / "golden"
REL_TOL = 1e-6
ABS_TOL = 1e-9  # for values that are exactly 0 in Excel


def load_cases(name: str) -> list[dict]:
    return json.loads((GOLDEN / name).read_text())["cases"]


def close(a, b) -> bool:
    return a == pytest.approx(b, rel=REL_TOL, abs=ABS_TOL)
