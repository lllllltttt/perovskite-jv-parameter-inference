# COMSOL drivers

`1D_PSC_wen.mph` is the shared model: one-dimensional drift–diffusion, layer
stack FTO / HTL / perovskite / C₆₀ / SnO₂ / Ag, stationary study `std1`,
voltage sweep `range(0, 0.01, 1.3)` (131 points), current read out as
`semi.J0_1` in A m⁻².

Two campaigns used it.  Each was run as four MATLAB segments against four
COMSOL server ports, with one row of the sampling design per sample.

## `main_200k/` — main database (102,046 retained curves)

| Script | Rows of the design | Port | Function name in file |
|---|---|---|---|
| `run_PSC_9D_5.m` | 1 – 50,000 | 2036 | `run_PSC_9D_5` |
| `run_PSC_9D_6.m` | 50,001 – 100,000 | 2037 | `run_PSC_9D_6` |
| `run_PSC_9D_7.m` | 100,001 – 150,000 | 2038 | `run_PSC_9D_7` |
| `run_PSC_9D_8.m` | 150,001 – 200,000 | 2039 | `run_PSC_9D_7` (copy/paste; the body uses port 2039 and rows 150,001–200,000) |

Input design: `PSC_LHS_9D_interface_lifetimes_200000.csv`, 200,000 rows.
Output: `Sample_%05d.mat` per row, containing `Index` (= row number, which
becomes `Sample_ID`), the nine parameters and `J` (131 points).  `script/mat-csv.py`
reads exactly those fields and applies the four retention filters.

Two constants in these files differ from the archived companions and are worth
knowing when rerunning them:

* the design file is named `…_200000.csv` (no `_3` suffix) and uses the column
  names `tau_ETL_in` / `tau_HTL_in`, whereas `script/LHS.py` emits
  `…_200000_3.csv` with `tau_interface_ETL_in` / `tau_interface_HTL_in`.  The
  values are the same design; the retained curves match the archived `_3` file
  (see `docs/SOURCE_VERIFICATION.md`).
* the output directory is `result-9D-interface-lifetimes/`, while `mat-csv.py`
  reads `result-9D-interface-lifetimes-2/`.

The only lines to edit before a rerun are `addpath`, `input_path`, `mph_path`,
`result_dir`, and `N` / `start_idx` at the top of each file.

### Adapted copies (`main_200k/adapted/`)

The archived originals are kept byte-for-byte.  `main_200k/adapted/` holds four
copies that differ from them in three places only:

* the function name matches the file name (`run_PSC_9D_8.m` no longer declares
  `run_PSC_9D_7()`);
* the three path constants point at relative names: the design file
  `PSC_LHS_9D_interface_lifetimes_200000_3.csv`, the model `1D_PSC_wen.mph`, and
  the output directory `result-main-200k/`;
* a four-line block after `readtable()` aliases `tau_ETL_in` / `tau_HTL_in` to
  `tau_interface_ETL_in` / `tau_interface_HTL_in` when the design file uses the
  older column names, so either file convention can be read.

Row ranges, ports, the parameter assignment, the sweep and the output format are
unchanged.  To run a segment:

```matlab
cd code/comsol/main_200k/adapted      % or give absolute paths in the header
run_PSC_9D_5                          % starts the COMSOL server on port 2036
```

The adapted copies were generated mechanically and checked statically with
`python code/verify_comsol_scripts.py`; they have **not** been executed here,
because that requires a COMSOL licence.  The originals are the files that
produced the database.

## `independent_300k/` — independent cohort (153,067 retained curves)

| Script | Rows of the design | Port |
|---|---|---|
| `run_PSC_9D_5.m` | 1 – 75,000 | 2036 |
| `run_PSC_9D_6.m` | 75,001 – 150,000 | 2037 |
| `run_PSC_9D_7.m` | 150,001 – 225,000 | 2038 |
| `run_PSC_9D_8.m` | 225,001 – 300,000 | 2039 |

Input design: `PSC_LHS_9D_interface_lifetimes_300000_5.csv` (release asset
`design_independent_300000.tar.gz`).  Output: `result-9D-interface-lifetimes-3/`,
which `script/mat-csv.py` turns into `JV_database_9D_interface_lifetimes-3.csv`.

Both batches use the same parameter assignment: mobilities in m² V⁻¹ s⁻¹,
lifetimes in s, densities in m⁻³, and `rad_c` stored in cm³ s⁻¹ and passed to
COMSOL as `rad_c_in × 1e-6` m³ s⁻¹.

## Requirements

COMSOL Multiphysics 6.3 with the Semiconductor Module, LiveLink for MATLAB and
MATLAB R2024b.  The servers are started externally, e.g.
`comsolmphserver.exe -port 2036`.
