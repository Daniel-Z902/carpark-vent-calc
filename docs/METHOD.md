# Calculation method (reverse-engineered from `carpark_calcs.xlsx`)

This describes what Daniel's workbook calculates and where each quantity lives,
so the Python package can be checked cell-for-cell. It is written in our own
words. **No text, tables or figures from AS 1668.2 are reproduced**; the
workbook's factor values and expressions are quoted only because they are the
logic being implemented. Check every factor against a licensed copy of the
Standard before relying on it.

The workbook was read with openpyxl twice (`data_only=False` for formulas,
`data_only=True` for Excel's cached results). This package implements the
2012 and 2024 sheets. They have no named ranges other than print areas, no
lookups (`VLOOKUP` etc.), no macros and no cross-sheet references. Each
sheet is self-contained.

2012 is the default edition. 2024 is selected with `edition: "2024"`.

| Sheet | Edition | Status in workbook | Example data |
|---|---|---|---|
| `Car Park Vent - AS1668 2012` | AS 1668.2-2012 | current (default) | BASEMENT 2, BASEMENT 1 |
| `Car Park Vent - AS1668 2024` | AS 1668.2-2024 | current | none (empty template) |

## 1. Overall approach (both sheets)

For each car park level (one table row) the sheet works out several candidate
exhaust air flows in l/s, then:

1. **Design exhaust air flow** (m3/s) = the largest candidate / 1000.
2. **Design make-up air flow** (m3/s) = make-up ratio x design exhaust.
3. **Queuing areas**: two queue lengths (m) from the number of spaces per exit
   lane, and a **queue exhaust** (m3/s) = longer queue x 300 / 1000.
4. **Totals row**: sums of car spaces, floor area, design exhaust and
   make-up. Labelled "Excluding Loading Dock".

Blank rows: every formula is wrapped in `IF(n1="","",...)`, so a blank row
gives blank components and a design flow of 0 (`MAX` of blanks).

Units: n in spaces, d in metres, A in m2, components in l/s, design flows in
m3/s, queue lengths in m.

## 2. Header block (both sheets)

| Cell | Meaning |
|---|---|
| A1 / J1 | Title and edition |
| B3 | Project name (blank in the file) |
| D3 | Revision ("rev A") |
| F3 | Architectural reference ("Arch: -") |
| B7 | Minimum flow constant (number) |
| B8:B10 | Text of the other candidate expressions (documentation only, not used by formulas) |
| rows 12-24 | Factor lists for P (usage) and T (vehicle type), values typed in column D |
| rows 25-31 | Symbol legend |
| Queuing block (L5:P19) | Queue expressions and the **number of exit lanes L** input |

## 3. Factor values used in the workbook

Parking usage factor P (rows 13-17, column D). Both sheets cite Table 4.1.
2012 has one factor, P. 2024 splits it into P1 (spaces on the level) and P2
(spaces exiting through the level). The values are the same.

| Use | P |
|---|---|
| Residential | 0.3 |
| Commercial | 0.5 |
| Retail | 0.7 |
| Entertainment / sports | 1.0 |
| Vehicle depots | 2.4 |

Vehicle type factor T (rows 19-24, column D). Both sheets cite Table 4.2.

| Vehicles | T |
|---|---|
| No special vehicle population | 1 |
| Diesel | 2.4 |
| LPG | 1 |
| CNG (typed as "CHG" in the sheet) | 1 |
| Electric | 0.1 |
| Motorcycles | 0.25 |

The staff exposure factor E and staff usage factor F are typed straight into
each row (cited as Table 4.3). The workbook has no table of E/F values, so
the package doesn't either.

These live in `carpark_vent/editions.py`. Input files may give P/T (or P1/P2)
as numbers or as names (`residential`, `diesel`, ...).

## 4. Sheet-by-sheet formulas

Below, *row r* is any level row. Python function names are in `calcs.py`.

### 4.1 AS 1668.2-2012 sheet (rows 34-41, total row 42) — default

Inputs: C n1, D n2, E d1, F d2, G T, H E, I F, J P, K A; O12 exit lanes;
Q31 make-up ratio 0.8.

| Col | Quantity | Formula | Python |
|---|---|---|---|
| L | Q minimum | `=$B$7` = 2000 | |
| M | Qa | `=J*0.85*(100*C+C*E+D*F)*G*H`, i.e. P x 0.85 x (100 n1 + n1 d1 + n2 d2) x T x E | `qa_2012` |
| N | Qb | `=2000*I*G` = 2000 x F x T | `staff_flow` |
| O | Qc | `=2.5*K` = 2.5 x A | `area_flow` |
| P | Design exhaust | `=MAX(L:O)/1000` | |
| Q | Make-up | `=$Q$31*P` | |
| R, S, T | LB/LHU, LLU, queue exhaust | as section 5, using P (column J) and `$O$12` | |
| C42, K42, P42, Q42 | Totals | `=SUM` | |

Example data in the file: E34 and E35 are `=(...)/6` averages of six measured
driving distances. D35 `=C34`, so BASEMENT 2's spaces exit through BASEMENT 1.

Cached results: BASEMENT 2 Qc governs, 5.584875 m3/s; BASEMENT 1 Qc governs,
5.860375 m3/s; total 11.44525 m3/s exhaust, 9.1562 m3/s make-up.

### 4.2 AS 1668.2-2024 sheet (rows 34-41, total row 42)

Inputs: A level, B comment, C n1, D n2, E d1, F d2, G T, H E, I F, J P1,
K P2, L A. Global inputs: O12 exit lanes L, Q31 make-up ratio (0.8; note in
Q30 says "75-90%").

| Col | Quantity | Formula (row r) | Python |
|---|---|---|---|
| M | Q, minimum (l/s) | `=$B$7` = 1000 | `Edition.q_min_ls` |
| N | Qa, car movement (l/s) | `=0.4*(J*(100*C+C*E)+K*(D*F))*H*G`, i.e. 0.4 x (P1 x (100 n1 + n1 d1) + P2 x n2 d2) x E x T | `qa_2024` |
| O | Qb, staff (l/s) | `=1000*I*G` = 1000 x F x T | `staff_flow` |
| P | Qc, floor area (l/s) | `=1.5*L` = 1.5 x A | `area_flow` |
| Q | Design exhaust (m3/s) | `=MAX(M:P)/1000` | `design_exhaust_m3s` |
| R | Make-up (m3/s) | `=$Q$31*Q` | `makeup_m3s` |
| S | LB / LHU (m) | `=MAX(0, 2.2*(C/$O$12)*J-200)` (written as nested IF) | `queue_length_m(..., 200)` |
| T | LLU (m) | same with -400 | `queue_length_m(..., 400)` |
| U | Queue exhaust (m3/s) | `=IF(MAX(S:T)<0,0,MAX(S:T)*300/1000)` | `queue_exhaust_m3s` |
| C42, L42, Q42, R42 | Totals | `=SUM(...)` | `calculate_project` |

The queue uses **P1** (column J). Template defaults in row 34: T = E = F = 1,
P1 = 0.3. The sheet has no filled example rows; the 2024 tests use the
LibreOffice cases instead.

## 5. Queuing areas (both sheets)

With L exit lanes and nL = n1 / L spaces per lane (per level, using only that
level's n1):

* LB (hindered exit, barrier/checkpoint) and LHU (free exit to a heavy-traffic
  street) share one column: max(0, 2.2 x nL x P - 200) m
* LLU (free exit to a light-traffic street): max(0, 2.2 x nL x P - 400) m
* Queue exhaust = max(LB, LLU) x 300 / 1000 m3/s

On 2024 the parking factor in those expressions is P1.

The sheet notes say the queue length is for the owner to decide and the
authority to approve. An orange banner (L19) says "no dedicated queuing
areas applicable". If the exit-lane cell is blank the queue columns are
blank. The package does the same with `exit_lanes: null`.

## 6. Precision and rounding

Cached values are stored at full double precision. The display formats
(`#,##0` for l/s, `#,##0.0` for m3/s) round only what you see. Python keeps
the same operand order as each Excel formula, so the example results match
exactly (bit-for-bit for the 2012 case), well inside the 1e-6 relative test
tolerance. Reports round for display only.

## 7. Workbook quirks the package handles on purpose

1. **Hard-coded queue zeros.** On the 2012 and 2024 sheets, rows 34 and 37-41
   hold typed-in `0` in the LB/LHU and LLU columns, not formulas. Only rows
   35-36 calculate a queue. The package applies the formula to every level.
2. **Make-up ratio** is an input on both sheets (Q31 = 0.8; the note in Q30
   says "75-90%"). `makeup_ratio` in the input file overrides it. Omit it and
   the edition default (0.8) is used.
3. **2024 P2 blank** counts as 0 (Excel blank-cell behaviour). The package
   warns if n2 x d2 > 0 and P2 is missing.
4. **n2 chaining** (`=C34` on the 2012 sheet, so BASEMENT 2's spaces exit
   through BASEMENT 1) is entered by hand. The 2012 sheet lists the lowest
   basement first. The 2024 sheet has no example rows. The package takes n2
   as an explicit input.

## 8. Mapping to code

| Workbook | Code |
|---|---|
| Constants (B7, area rates, 0.4/0.85 coefficients, staff flows, ratios, factor lists) | `carpark_vent/editions.py` |
| Cell positions per sheet | `carpark_vent/layout.py` |
| Row formulas | `carpark_vent/calcs.py` |
| Row of inputs | `carpark_vent.models.Level` |
| Header / global cells | `ProjectInfo`, `Project.exit_lanes`, `Project.makeup_ratio` |
| Cached results for tests | `tests/golden/excel_cached.json` (`tools/extract_golden.py`) |
| Extra cases from LibreOffice-recalculated sheets | `tests/golden/libreoffice_recalc.json` (`tools/make_lo_scenarios.py`) |
