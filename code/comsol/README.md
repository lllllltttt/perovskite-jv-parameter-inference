# COMSOL drivers

`1D_PSC_wen.mph` is the shared model: one-dimensional drift–diffusion, layer
stack FTO / HTL / perovskite / C₆₀ / SnO₂ / Ag, stationary study `std1`,
voltage sweep `range(0, 0.01, 1.3)` (131 points), current read out as
`semi.J0_1` in A m⁻².

Two campaigns used it, each run as four MATLAB segments against four COMSOL
server ports, one row of the sampling design per sample.

## `main_200k/` — main database (102,046 retained curves)

The published drivers.  Each file resolves its paths from its own location, so
the four segments run without editing once the repository is laid out as in the
top-level README:

| Constant | Resolves to |
|---|---|
| `input_path` | `<repo>/data/_assets/PSC_LHS_9D_interface_lifetimes_200000_3.csv` (asset `dataset_main_102046`) |
| `mph_path` | `<repo>/code/comsol/1D_PSC_wen.mph` |
| `result_dir` | `<repo>/result-main-200k/` |

| Script | Rows of the design | Port | Output |
|---|---|---|---|
| `run_PSC_9D_5.m` | 1 – 50,000 | 2036 | `Sample_%05d.mat` |
| `run_PSC_9D_6.m` | 50,001 – 100,000 | 2037 | `Sample_%05d.mat` |
| `run_PSC_9D_7.m` | 100,001 – 150,000 | 2038 | `Sample_%05d.mat` |
| `run_PSC_9D_8.m` | 150,001 – 200,000 | 2039 | `Sample_%05d.mat` |

Each `.mat` holds `Index` (= row number, which becomes `Sample_ID`), the nine
parameters and `J` (131 points) — the fields `code/pipeline/mat-csv.py` reads.
The drivers accept either design-file column convention: if `tau_ETL_in` /
`tau_HTL_in` are absent, a four-line block after `readtable()` aliases
`tau_interface_ETL_in` / `tau_interface_HTL_in` to them.

The only line to edit before a rerun is `addpath`, which points at the COMSOL
LiveLink installation.  Then, in MATLAB:

```matlab
cd code/comsol/main_200k
run_PSC_9D_5          % starts the COMSOL server on port 2036
```

The compiled CSV is produced by `code/pipeline/mat-csv.py`, which defaults to
`<repo>/result-main-200k/` as input and
`<repo>/results/JV_database_9D_interface_lifetimes-main-200k.csv` as output
(`--mat-dir`, `--out-csv` to override).

The four scripts as recovered from the server are kept byte-identical in
`archive/original_200k/`; the published versions differ from them in the
function name, the three path constants and the column alias only.

## `independent_300k/` — independent cohort (153,067 retained curves)

| Script | Rows of the design | Port |
|---|---|---|
| `run_PSC_9D_5.m` | 1 – 75,000 | 2036 |
| `run_PSC_9D_6.m` | 75,001 – 150,000 | 2037 |
| `run_PSC_9D_7.m` | 150,001 – 225,000 | 2038 |
| `run_PSC_9D_8.m` | 225,001 – 300,000 | 2039 |

Input design: `PSC_LHS_9D_interface_lifetimes_300000_5.csv` (asset
`design_independent_300000.tar.gz`).  Output: `Sample_%05d.mat` in the directory
named by `result_dir` in each file; the converter is run with `--mat-dir`
pointing at it.

## Parameter assignment (identical in both campaigns)

Mobilities in m² V⁻¹ s⁻¹, lifetimes in s, densities in m⁻³, and `rad_c` stored
in cm³ s⁻¹ and passed to COMSOL as `rad_c_in × 1e-6` m³ s⁻¹.

## Reference mesh

`mesh_statistics/` records the element distribution of the saved reference mesh
(`mesh1`), read in COMSOL 6.3 without re-meshing or solving: 112 elements over
the six domains as 10 / 1 / 85 / 1 / 10 / 5, so each 0.01 nm interface slab
carries one element.  The source model's SHA-256 matches the archived
`1D_PSC_wen.mph`.

## Requirements

COMSOL Multiphysics 6.3 with the Semiconductor Module, LiveLink for MATLAB and
MATLAB R2024b.  The servers are started externally, e.g.
`comsolmphserver.exe -port 2036`.
