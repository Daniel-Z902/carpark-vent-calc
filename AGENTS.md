# AGENTS.md: guidance for Codex and other coding agents

## What this is
A Python port of n2's car park ventilation workbook (`carpark_calcs.xlsx`,
the AS 1668.2-2012 and AS 1668.2-2024 sheets). 2012 is the default edition
(the one currently in use). 2024 is fully supported and selected explicitly.
The workbook is the reference. Results must keep matching its cached values.
Read `docs/METHOD.md` before changing any calculation.

## Licensing rule (hard requirement)
- **Never** add text, tables, figures, clause wording, notes or definitions
  copied or closely paraphrased from Australian Standards (AS 1668.2, AS 1668.1,
  NCC-referenced standards, etc.). Not in code, comments, docs, tests,
  fixtures or commit messages.
- You may implement only logic and constants that already exist in the n2
  workbook, or that Daniel supplies explicitly in an issue or PR.
- Cite references by number only, e.g. `# AS 1668.2 Table 4.1` or
  `# AS 1668.2 Cl 4.x`, and only where the workbook (or Daniel) gives that
  reference. Don't guess clause numbers.
- If a feature needs values the repo doesn't have (e.g. jet fan thrust rules,
  CO limits), add a typed input or a config placeholder with a `TODO(Daniel):
  confirm value` and leave it out of the constants.
- Don't commit `*.xlsx` source workbooks (they are git-ignored).

## Project structure
- `carpark_vent/editions.py`: constants per edition (one `Edition` each). Every value has a workbook cell comment.
- `carpark_vent/calcs.py`: pure functions, one per workbook formula, with the same operand order as Excel. No I/O.
- `carpark_vent/models.py`: frozen dataclasses (`Level`, `Project`, `ProjectInfo`, `LevelResult`, `ProjectResult`).
- `carpark_vent/loader.py`: YAML/JSON to models, with strict validation (unknown keys are errors).
- `carpark_vent/layout.py`: cell map of each sheet (used by the golden extractor and the Excel writer).
- `carpark_vent/report/`: `excel.py` (mirrors the workbook layout), `html.py`, `pdf.py` (reportlab, optional), `common.py` (shared wording).
- `carpark_vent/cli.py`: `carpark-vent run|editions|template`.
- `tests/`: pytest; `tests/golden/*.json` hold the golden cases.
- `tools/`: scripts that regenerate the golden JSON from the workbook.

## How to run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                   # must stay green
carpark-vent run examples/example_2012.yaml -o build/
```
Tests that need LibreOffice (`soffice`) or the workbook skip automatically.
Don't delete or loosen golden tests. If a deliberate change alters results,
explain why in the PR and get Daniel's sign-off.

## Coding conventions
- Python 3.10+, type hints throughout, `from __future__ import annotations`.
- Calculation code stays pure: numbers in, numbers out, no file or network
  access, no global state.
- Units in names or docstrings (`_ls`, `_m3s`, `_m`, `_m2`). Inputs follow
  the workbook symbols (`n1`, `d1`, `P1`, `A`, ...).
- New editions or methods: add an `Edition` entry, a formula function with a
  docstring quoting the Excel formula or n2 expression, golden or hand-checked
  tests, and a section in `docs/METHOD.md`.
- Keep the workbook quirks listed in METHOD.md section 7 visible. Don't
  "fix" them silently.
- Line length 120 (ruff config in `pyproject.toml`). Keep dependencies
  minimal; new ones go in `pyproject.toml` (optional extras where possible).
- Commit messages: imperative and short, e.g. `Add jet fan sizing inputs`.
