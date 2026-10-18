# carpark-vent

Car park mechanical ventilation calculations for Australian projects. This is
a Python port of n2 Engineering Consultants' car park ventilation workbook
(`carpark_calcs.xlsx`). It implements the AS 1668.2-2012 sheet (the edition
currently in use, and the default) and the AS 1668.2-2024 sheet, which is
fully supported and selected with `edition: "2024"`.

For each car park level it calculates the candidate exhaust flows (minimum,
car movement, staff, floor area), the governing **design exhaust air flow**,
the **make-up air flow** and the **queuing-area** lengths and exhaust. It
then writes a calculation report: an Excel file laid out like the original
sheet, plus HTML, PDF and JSON.

> Only the calculation logic and constants from the n2 workbook are in this
> repository. No text, tables or figures from Australian Standards. Check
> factors against your licensed copy of the Standard before issuing a
> calculation.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # dev = pytest + reportlab (PDF)
# or: pip install -e ".[pdf]"  /  pip install -e .   (no PDF)
```

Requires Python 3.10+. Dependencies: `openpyxl`, `PyYAML`, and optionally
`reportlab`.

## Usage

```bash
carpark-vent run examples/example_2012.yaml -o build/        # xlsx, html, pdf, json
carpark-vent run my_job.yaml --formats xlsx,pdf --excel-formulas
carpark-vent template > my_job.yaml                           # 2012 starter (the default)
carpark-vent template 2024 > my_job.yaml                      # 2024 starter
carpark-vent editions                                          # constants per edition
python -m carpark_vent ...                                     # same thing
```

`--excel-formulas` writes live Excel formulas, in the workbook's own style,
into the mirrored sheet. Without it the sheet holds the values Python
calculated.

### Input file (YAML or JSON)

```yaml
edition: "2012"                 # optional; 2012 (default) or 2024
project:
  name: Example residential basement
  number: N2-EXAMPLE
  revision: A
  arch_reference: "-"
  prepared_by: Daniel Zhang
exit_lanes: 1                   # null = skip queuing assessment
makeup_ratio: 0.8               # optional; edition default otherwise
levels:
  - name: BASEMENT 1
    n1: 53                      # spaces on this level
    n2: 64                      # spaces elsewhere that exit through this level
    d1: [93.95, 73.73, 53.1]    # list -> averaged
    d2: 68.97
    T: none                     # or a number
    E: 1
    F: 1
    P: residential              # or a number
    A: 2344.15                  # m2
```

2012 uses one parking usage factor `P`. 2024 uses `P1` for the spaces on
the level and `P2` for the spaces exiting through it. Both editions use
`T`, `E`, `F`, `n1`, `n2`, `d1`, `d2` and `A`. Unknown or unused keys are
rejected so typos can't slip through. Omit `edition` and the file is read
as 2012. Run `carpark-vent template` (or `carpark-vent template 2024`) for
a starting point.

### Example

```text
$ carpark-vent run examples/example_2012.yaml -o build/
Example residential basement (workbook 2012 sheet) - AS 1668.2-2012
Level                Q l/s    Qa l/s    Qb l/s    Qc l/s  Gov  Exh m3/s  MU m3/s   Queue
BASEMENT 2           2,000     2,475     2,000     5,585   Qc      5.58     4.47    0.00
BASEMENT 1           2,000     3,214     2,000     5,860   Qc      5.86     4.69    0.00
TOTAL                                                             11.45     9.16    0.00
```

These match the cached values on the workbook's 2012 sheet.

### Python API

```python
from carpark_vent import calculate_project
from carpark_vent.loader import load_project
from carpark_vent.report import write_excel, write_html, write_pdf

res = calculate_project(load_project("examples/example_2024.yaml"))
print(res.total_design_exhaust_m3s)
write_excel(res, "build/job.xlsx"); write_html(res, "build/job.html"); write_pdf(res, "build/job.pdf")
```

## Tests

```bash
pytest
```

* `tests/test_golden_excel.py` compares the 2012 example against Excel's
  cached values (`tests/golden/excel_cached.json`), with a relative
  tolerance of 1e-6. The 2024 sheet in the workbook is an empty template.
* `tests/test_golden_libreoffice.py` compares against synthetic cases. These
  were made by writing inputs into the unchanged workbook formulas and
  recalculating with LibreOffice. They cover the 2024 sheet and non-zero
  queues on both editions.
* The live-formula round trip and the workbook drift check are skipped
  automatically when `soffice` or `carpark_calcs.xlsx` is not available.

## Layout

```
carpark_vent/      package: editions.py (constants), models.py, calcs.py (pure formulas),
                   loader.py (YAML/JSON), layout.py (workbook cell map), cli.py, report/
tests/             pytest suite + golden/ JSON
tools/             extract_golden.py, make_lo_scenarios.py (regenerate golden data)
examples/          sample inputs
docs/METHOD.md     how the workbook works, cell by cell
docs/ROADMAP.md    next features
```

The source workbook is **not** committed (`*.xlsx` is in `.gitignore`). Put
it at the repo root to run the drift test or regenerate the golden data.
