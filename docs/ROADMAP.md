# Roadmap: suggested next features and Codex tasks

Each item suits one Codex task or PR. Anything that needs new values from a
Standard must take them as inputs or a `TODO(Daniel)` placeholder (see the
licensing rule in AGENTS.md).

## Quick wins
1. **Auto n2 chaining.** Optional `exits_via: <level name>` per level, so n2
   is filled in from the levels whose exit route passes through, replacing the
   hand-entered `=C34` cell on the 2012 sheet.
2. **Workbook importer.** `carpark-vent import carpark_calcs.xlsx --sheet 2012`
   turns an existing job workbook into a YAML input (using `layout.py`).
3. **Comparison mode.** Run one project against several editions side by side
   (e.g. 2012 vs 2024) for authority or peer-review discussions.
4. **Loading dock / other zones.** The totals say "Excluding Loading Dock".
   Add a separate zone list (loading dock, wash bays) with user-entered flows
   so the total plant flow can be reported.
5. **Fan and plant schedule.** Group levels into exhaust and supply systems,
   apply a user-set margin, and output a fan schedule table (flow, duty).

## Engineering features
6. **Jet fan (impulse) ventilation sizing.** Inputs for car park geometry,
   jet fan thrust and spacing rules supplied by Daniel. Report the jet fan
   count and layout check.
7. **CO monitoring / VSD control.** Detector count and placement by area
   (rules as inputs), staged fan speeds, and a control narrative output.
8. **Ductwork / transfer air checks.** Velocities at openings, make-up path
   sizing and pressure-drop estimates.
9. **Natural ventilation check.** Opening-area assessment as an alternative
   to mechanical exhaust (criteria as inputs).
10. **Smoke exhaust interface.** Flag where car park exhaust also serves
    smoke hazard management. Inputs only, no Standard text.

## Interfaces and reporting
11. **Streamlit web UI.** Edit levels in a table, see live results, download
    the Excel, PDF and HTML reports.
12. **n2 branding.** Logo, title block, document numbering, revision history
    table and engineer and certifier sign-off block in the PDF/Excel.
13. **Multi-revision projects.** Keep rev A/B/C inputs and show differences.
14. **Excel template injection.** Write results into a copy of an official
    n2 template workbook, not a generated sheet.

## Quality
15. Property-based tests (hypothesis) for monotonicity, e.g. more spaces never
    lowers Qa.
16. GitHub Actions CI: pytest on Python 3.10-3.13, ruff, build the wheel, and
    upload the example reports as artifacts.
17. Resolve the workbook quirks in METHOD.md section 7 once Daniel confirms
    the intended behaviour (hard-coded queue zeros on the 2012 and 2024
    sheets, the 300 l/s per m queue constant).
