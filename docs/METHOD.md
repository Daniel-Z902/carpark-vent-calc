# Calculation method (reverse-engineered from `carpark_calcs.xlsx`)

This describes what Daniel's workbook calculates and where each quantity lives,
so the Python package can be checked cell-for-cell. It is written in our own
words. **No text, tables or figures from AS 1668.2 are reproduced**; the
workbook's factor values and expressions are quoted only because they are the
logic being implemented. Check every factor against a licensed copy of the
Standard before relying on it.

The workbook was read with openpyxl twice (`data_only=False` for formulas,
`data_only=True` for Excel's cached results). It has four sheets, one per
edition, no named ranges other than print areas, no lookups (`VLOOKUP` etc.),
no macros and no cross-sheet references. Every sheet is self-contained.

| Sheet | Edition | Status in workbook | Example data |
|---|---|---|---|
| `Car Park Vent - AS1668 2024` | AS 1668.2-2024 | current | none (empty template) |
| `Car Park Vent - AS1668 2012` | AS 1668.2-2012 | current | BASEMENT 2, BASEMENT 1 |
| `Car Park Vent - AS1668 2002` | AS 1668.2-2002 | "SUPERSEDED" text box | B1, B2 |
| `Car Park Vent - AS1668 1991` | AS 1668.2-1991 | "SUPERSEDED" text box | B1, B2 |

## 1. Overall approach (all sheets)

For each car park level (one table row) the sheet works out several candidate
exhaust air flows in l/s, then:

1. **Design exhaust air flow** (m3/s) = the largest candidate / 1000.
2. **Design make-up air flow** (m3/s) = make-up ratio x design exhaust.
3. **Queuing areas**: two queue lengths (m) from the number of spaces per exit
   lane, and a **queue exhaust** (m3/s) = longer queue x 300 / 1000.
4. **Totals row**: sums of car spaces, floor area (2012/2024 only), design
   exhaust and make-up. Labelled "Excluding Loading Dock".

Blank rows: every formula is wrapped in `IF(n1="","",...)`, so a blank row
gives blank components and a design flow of 0 (`MAX` of blanks).

Units: n in spaces, d in metres, A in m2, components in l/s, design flows in
m3/s, queue lengths in m.

## 2. Header block (all sheets)

| Cell | Meaning |
|---|---|
| A1 / J1 (I1 on 2002, 1991) | Title and edition |
| B3 | Project name (blank in the file) |
| D3 | Revision ("rev A" on 2012/2024, "rev 1" on 2002/1991) |
| F3 | Architectural reference ("Arch: -" or "Arch: 23/05/2014") |
| B7 | Minimum flow constant (number) |
| B8:B10 | Text of the other candidate expressions (documentation only, not used by formulas) |
| rows 12-24 | Factor lists for P (usage) and T (vehicle type), values typed in column D |
| rows 25-31 | Symbol legend |
| Queuing block (L5:P19 on 2012/2024, K5:O17 on 2002, H5:L17 on 1991) | Queue expressions and the **number of exit lanes L** input |

## 3. Factor values used in the workbook

Parking usage factor P (rows 13-17, column D). Sheets cite Table 4.1 (1991,
2012, 2024) or Table 7.3 (2002).

| Use | 2024 / 2012 / 2002 | 1991 |
|---|---|---|
| Residential | 0.3 | 0.3 |
| Commercial | 0.5 | 0.5 |
| Retail | 0.7 | 0.7 |
| Entertainment / sports | 1.0 | 1.0 |
| Vehicle depots | 2.4 | 2.0 (diesel vehicle depots) |

Vehicle type factor T (rows 19-24, column D). Sheets cite Table 4.2 (2012,
2024) or Table 7.4 (2002); no T on the 1991 sheet.

| Vehicles | T |
|---|---|
| No special vehicle population | 1 |
| Diesel | 2.4 |
| LPG | 1 |
| CNG (typed as "CHG" in the sheet) | 1 |
| Electric | 0.1 |
| Motorcycles | 0.25 |

The staff exposure factor E and staff usage factor F are typed straight into
each row (cited as Table 4.3 / Table 7.5). The workbook has no table of E/F
values, so the package doesn't either.

These live in `carpark_vent/editions.py`. Input files may give P/T as numbers
or as names (`residential`, `diesel`, ...).

## 4. Sheet-by-sheet formulas

Below, *row r* is any level row. Python function names are in `calcs.py`.

### 4.1 AS 1668.2-2024 sheet (rows 34-41, total row 42)

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
P1 = 0.3.

### 4.2 AS 1668.2-2012 sheet (rows 34-41, total row 42)

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
| R, S, T | LB/LHU, LLU, queue exhaust | as 2024, using P (column J) and `$O$12` | |
| C42, K42, P42, Q42 | Totals | `=SUM` | |

Example data in the file: E34 and E35 are `=(...)/6` averages of six measured
driving distances. D35 `=C34`, so BASEMENT 2's spaces exit through BASEMENT 1.

Cached results: BASEMENT 2 Qc governs, 5.584875 m3/s; BASEMENT 1 Qc governs,
5.860375 m3/s; total 11.44525 m3/s exhaust, 9.1562 m3/s make-up.

### 4.3 AS 1668.2-2002 sheet (rows 33-39, total row 40), superseded

Inputs: C n1, D n2, E d1, F d2, G T, H F, I P, J A; N12 exit lanes. No E factor.

| Col | Quantity | Formula |
|---|---|---|
| K | Q minimum | `=$B$7` = 2000 |
| L | Qa | `=I*0.85*(100*C+C*E+D*F)`, i.e. P x 0.85 x (100 n1 + n1 d1 + n2 d2). **No T factor** (matches the B8 label) |
| M | Qb | `=2000*H*G` = 2000 x F x T |
| N | Qc | `=3*J` in rows 33-35, **`=3.5*J` in rows 36-39** (B10 label says 3 x A) |
| O | Design exhaust | `=MAX(K:N)/1000` |
| P | Make-up | `=0.75*O` (ratio hard-coded, not an input cell) |
| Q, R, S | Queue | as above with `$N$12` and P in column I |
| C40, O40, P40 | Totals | `=SUM` |

Example: D33 `=C34` (B2's 180 spaces pass through B1); D34 `=C35+D35` = 0.
Cached: 15.0 m3/s per level (Qc governs), total 30.0 / 22.5 m3/s.

### 4.4 AS 1668.2-1991 sheet (rows 27-33, total row 34), superseded

Inputs: C n1, D n2, E d1 (exit, own cars), F d2 (entry, own cars), G d3
(exit, through-cars), H d4 (entry, through-cars), I P, J A; K12 exit lanes.

| Col | Quantity | Formula |
|---|---|---|
| K | Qa minimum | `=$B$7` = 3000 |
| L | Qb exit | `=I*1.2*(100*C+C*E+D*G)` = P x 1.2 x (100 n1 + n1 d1 + n2 d3) |
| M | Qc entry | `=I*0.4*(100*C+C*F+D*H)` = P x 0.4 x (100 n1 + n1 d2 + n2 d4) |
| N | Qd area | `=3.5*J` |
| O | Design exhaust | `=MAX(K:N)/1000` |
| P | Make-up | `=0.75*O` |
| Q, R, S | Queue | as above with `$K$12` and P in column I |
| C34, O34, P34 | Totals | `=SUM` |

Note the symbols move on this sheet: Qa is the minimum and Qd the area term.
Cached: 17.5 m3/s per level (Qd governs), total 35.0 / 26.25 m3/s.

## 5. Queuing areas (all sheets)

With L exit lanes and nL = n1 / L spaces per lane (per level, using only that
level's n1):

* LB (hindered exit, barrier/checkpoint) and LHU (free exit to a heavy-traffic
  street) share one column: max(0, 2.2 x nL x P - 200) m
* LLU (free exit to a light-traffic street): max(0, 2.2 x nL x P - 400) m
* Queue exhaust = max(LB, LLU) x 300 / 1000 m3/s

The sheet notes say the queue length is for the owner to decide and the
authority to approve. On 2012/2024 an orange banner (L19) says "no dedicated
queuing areas applicable". If the exit-lane cell is blank the queue columns
are blank. The package does the same with `exit_lanes: null`.

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
2. **2002 Qc rate.** Rows 33-35 use 3 x A and rows 36-39 use 3.5 x A. The
   package uses 3 (matches the B10 label and the populated rows).
3. **Degenerate totals-row queue (2002, 1991).** Q40:S40 / Q34:S34 apply the
   queue formula to total n1 with a blank P, so they always show 0. The
   package reports per-level queues plus a summed queue exhaust instead.
4. **2002 has no T in Qa**, unlike 2012/2024. Kept as the sheet has it.
5. **Make-up ratio**: an input (Q31 = 0.8) on 2012/2024, hard-coded 0.75 on
   2002/1991. `makeup_ratio` in the input file overrides it, with a warning
   on the older editions.
6. **2024 P2 blank** counts as 0 (Excel blank-cell behaviour). The package
   warns if n2 x d2 > 0 and P2 is missing.
7. **n2 chaining** (`=C34`, `=C28+D28`) is entered by hand in the sheets, and
   the row order differs (2012 lists the lowest basement first; 2002/1991
   list B1 first). The package takes n2 as an explicit input.

## 8. Mapping to code

| Workbook | Code |
|---|---|
| Constants (B7, area rates, 0.4/0.85/1.2 coefficients, staff flows, ratios, factor lists) | `carpark_vent/editions.py` |
| Cell positions per sheet | `carpark_vent/layout.py` |
| Row formulas | `carpark_vent/calcs.py` |
| Row of inputs | `carpark_vent.models.Level` |
| Header / global cells | `ProjectInfo`, `Project.exit_lanes`, `Project.makeup_ratio` |
| Cached results for tests | `tests/golden/excel_cached.json` (`tools/extract_golden.py`) |
| Extra cases from LibreOffice-recalculated sheets | `tests/golden/libreoffice_recalc.json` (`tools/make_lo_scenarios.py`) |
