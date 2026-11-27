# Source verification: recovered COMSOL drivers and 300,000-row design

Four MATLAB drivers and one 300,000-row sampling table were recovered from the
simulation server on 2026-11-27 and are now archived.  This note records what
each file is and how that was established.

| File | SHA-256 | Role |
|---|---|---|
| `run_PSC_9D_5.m` | `4d015a32…ded28` | main campaign, rows 1–50,000, port 2036 |
| `run_PSC_9D_6.m` | `960ef524…5f902` | main campaign, rows 50,001–100,000, port 2037 |
| `run_PSC_9D_7.m` | `9e88899b…ef286` | main campaign, rows 100,001–150,000, port 2038 |
| `run_PSC_9D_8.m` | `50f2999f…36f0d` | main campaign, rows 150,001–200,000, port 2039 |
| `PSC_LHS_9D_interface_lifetimes_300000_5.csv` | `44bd6b84…ea34d6` | 300,000-row design of the independent cohort |

The four scripts are archived in `code/comsol/main_200k/`; the design table is
the release asset `design_independent_300000.tar.gz`.

## 1. The four drivers are the main-database campaign

* **Input.** All four read `PSC_LHS_9D_interface_lifetimes_200000.csv` — a
  200,000-row design — and `mph_path` points at `1D_PSC_wen.mph`.
* **Row coverage.** `start_idx`/`end_idx` are 1–50,000, 50,001–100,000,
  100,001–150,000 and 150,001–200,000: four contiguous segments covering
  1–200,000 with no overlap and no gap.  Ports 2036–2039 are distinct, so the
  segments could run concurrently.
* **Output contract.** Each row writes `Sample_%05d.mat` containing `Index`
  (the loop index = design row), the nine parameters and `J` (131 points).
  `script/mat-csv.py` reads exactly `Index`, `mu_n_pvk`, `mu_p_pvk`,
  `tau_n_pvk`, `tau_p_pvk`, `Nc_eff_pvk`, `Nv_eff_pvk`, `tau_ETL`, `tau_HTL`,
  `rad_c` and `J`, and uses `Index` as `Sample_ID`.  Field names, units and file
  naming match one to one.  The retained database has `Sample_ID` 2–200,000,
  i.e. a subset of the four segments.
* **Numerical cross-check.** The 102,046 retained curves match the archived
  200,000-row design row by row on `Sample_ID`: all 102,046 join, maximum
  relative difference 4.97e-3, i.e. the retained CSV stores the design values
  rounded to three significant digits.  The few rows that are not bit-identical
  after rounding are exact ties at the fourth digit (`7.145e-06 → 7.15e-06`),
  where the CSV writer rounded half up and `numpy.round` rounds half to even.

**Confirmed:** the four scripts are the drivers of the 200,000-row campaign that
produced the main database.  Two constants differ from the archived companions
and are recorded rather than altered:

* the input file is named `…_200000.csv` (no `_3` suffix) and uses
  `tau_ETL_in` / `tau_HTL_in`, whereas `script/LHS.py` emits `…_200000_3.csv`
  with `tau_interface_ETL_in` / `tau_interface_HTL_in`; the values are the same
  design, as the row-level match above shows;
* the scripts write `result-9D-interface-lifetimes/`, while `mat-csv.py` reads
  `result-9D-interface-lifetimes-2/`.  The `-2` suffix is not present in the
  recovered scripts; we treat it as a later copy or rename of the output
  directory, and have no file that records that step.

`run_PSC_9D_8.m` declares `function run_PSC_9D_7()` in its first line — a
copy/paste artefact.  The body is the fourth segment (port 2039, rows
150,001–200,000).  The file is archived unchanged.

## 2. The 300,000-row table is the independent cohort's design

* **Shape.** 300,000 data rows, 19 columns: `Sample_ID`, nine sampled variables
  (`mu_avg`, `mu_ratio`, `tau_avg`, `tau_ratio`, `DOS_avg`, `DOS_ratio`,
  `tau_ETL`, `tau_HTL`, `rad_c`), and the nine constructed parameters
  (`mu_n_pvk` … `rad_c`) plus the three values written to COMSOL
  (`tau_ETL_in`, `tau_HTL_in`, `rad_c_in`).  `Sample_ID` runs 1…300,000,
  unique and increasing, equal to the row number.
* **Values.** All nine constructed parameters are finite and positive, with the
  ranges in `docs/DATA_DICTIONARY.md`.  The parameters are stored directly, not
  as `g`/`q`; `mu_avg`/`mu_ratio` etc. are the sampled coordinates the
  constructed values were built from.
* **Match to the retained cohort.** Joining the 153,067 rows of
  `JV_database_9D_interface_lifetimes-3.csv` on `Sample_ID` gives 153,067
  matches and no unmatched rows.  For every one of the nine parameters the
  retained value equals the design value rounded to three significant digits:
  153,067/153,067 exact for all nine (maximum relative difference 2.9e-16,
  floating-point representation only).  The other 146,933 design rows did not
  pass the four retention filters and are not in the retained file.

**Confirmed:** the table is the sampling design of the independent cohort, and
`Sample_ID` is its 1-based row number.

## 3. What is still not archived

* The server-side MATLAB output directories (`result-9D-interface-lifetimes/`,
  `…-2/`, `…-3/`), i.e. the `Sample_*.mat` files.  The derived CSVs and the 45
  back-substitution curves are archived.
* Any record of the `-2` directory rename or copy.
* Per-slab mesh element counts inside the two 0.01 nm interface slabs
  (`docs/COMSOL_REPRODUCIBILITY_GAPS.md`, G1).

## How to reproduce these checks

```bash
python code/verify_source_provenance.py --design <design csv> --retained <retained csv>
```

The script repeats the join, the three-significant-digit comparison and the
range/finiteness checks, and prints the counts above.
