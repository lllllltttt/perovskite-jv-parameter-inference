# Data dictionary

All arrays are float64 unless noted.  The parameter order is **fixed** and identical in
every file in this release:

| # | Column | Symbol | Unit | Transform | Range in the retained data (log10) |
|---|--------|--------|------|-----------|-------------------------------------|
| 0 | `mu_n_pvk`   | μₙ  | m² V⁻¹ s⁻¹ | log10 | −6.3410 … −2.6517 |
| 1 | `mu_p_pvk`   | μₚ  | m² V⁻¹ s⁻¹ | log10 | −6.3449 … −2.6757 |
| 2 | `tau_n_pvk`  | τₙ  | s           | log10 | −9.3206 … −1.6556 |
| 3 | `tau_p_pvk`  | τₚ  | s           | log10 | −9.3487 … −1.6904 |
| 4 | `Nc_eff_pvk` | N꜀  | m⁻³         | log10 | 22.6665 … 26.3483 |
| 5 | `Nv_eff_pvk` | Nᵥ  | m⁻³         | log10 | 22.6345 … 26.3385 |
| 6 | `tau_ETL`    | τ_ETL | s         | log10 | −12 … −8 |
| 7 | `tau_HTL`    | τ_HTL | s         | log10 | −14 … −10 |
| 8 | `rad_c`      | r_rad | cm³ s⁻¹   | log10 | −12 … −9 |

`log_transform_mask` is `[True] * 9`: every parameter is log10-transformed before
min–max scaling.  The ranges above are the fitted scaler bounds (`data_min_`,
`data_max_`) of `models/param_scaler.pkl`, i.e. they are taken over all 102,046
retained curves.

**Why some individual values exceed the sampling limits in Table 1.**
The bulk pairs are constructed as pₙ = g·√q and pₚ = g/√q with g log-uniform over the
range in Table 1 and q uniform on 0.2–5.  The shared scale g therefore spans
10⁻⁶–10⁻³ m² V⁻¹ s⁻¹ (mobility), 10⁻⁹–10⁻² s (bulk lifetime) and 10²²–10²⁶ m⁻³
(density of states), while each individual counterpart may deviate by up to √5 ≈ 2.24.
That is why, for example, `Nc_eff_pvk` reaches 2.23 × 10²⁶ m⁻³ and `tau_n_pvk`
reaches 2.2 × 10⁻² s.

**Units inside COMSOL.**  `rad_c` is stored and sampled in cm³ s⁻¹ and the COMSOL
driver multiplies by 10⁻⁶ when setting the model parameter (cm³ s⁻¹ → m³ s⁻¹).  All
other parameters are passed without conversion.

## Voltage grid

`V = linspace(0, 1.3, 131)` V, step 0.01 V.  Column `J_000` is 0 V and `J_130` is
1.3 V.  Current density is in mA cm⁻².

---

## 1. `data/` — curated small files (in the repository)

### `data/splits/split_indices_seed42.npz`
The recorded partition, recovered exactly and verified against the frozen arrays
(`ALL arrays match`, see `docs/REPRODUCE.md`).

| Key | Shape | Meaning |
|---|---|---|
| `idx_train` | (71432,) int64 | row indices into the retained CSV, 0-based |
| `idx_val`   | (15307,) int64 | |
| `idx_test`  | (15307,) int64 | |
| `sample_id_all`   | (102046,) int64 | `Sample_ID` column, same order as the CSV |
| `sample_id_train/val/test` | as above | `Sample_ID` for each partition |

`Sample_ID` is the 1-based row number of the retained curve in the 200,000-row Latin
hypercube design (`PSC_LHS_9D_interface_lifetimes_200000_3.csv`).  It is unique and
strictly increasing over the 102,046 retained rows, so
`sample_id → LHS row` is a direct lookup.  The retained CSV stores parameters rounded
to three significant digits, the LHS file stores them at full precision.

### `data/examples/test_subset_200.npz`
A fixed, deterministic 200-curve subset of the test partition
(`numpy.random.default_rng(20261127).choice(15307, 200)`), used by
`code/quickstart_inference.py` so that the minimal example runs without downloading
the full dataset.

| Key | Shape | Meaning |
|---|---|---|
| `J_test` | (200,131) float32 | min–max-normalized current |
| `params_test` | (200,9) | min–max-normalized log10 parameters |
| `J_test_raw` | (200,131) | physical current, mA cm⁻² |
| `params_test_raw` | (200,9) | physical parameters, original units |
| `test_index` | (200,) | 0-based position within the 15,307-row test array |
| `log_transform_mask`, `param_names` | | as above |

---

## 2. Release assets — large files

### `dataset_main_102046.tar.gz`
| File | Size | Contents |
|---|---|---|
| `JV_database_9D_interface_lifetimes-2.csv` | 259 MB | **The main dataset.** 102,046 rows × 141 columns: `Sample_ID`, the 9 parameters, `J_000`…`J_130`. |
| `PSC_LHS_9D_interface_lifetimes_200000_3.csv` | 48 MB | The 200,000-row Latin hypercube design (seed 42). Columns: `Sample_ID`, the 9 latent sampling variables (`mu_avg`, `mu_ratio`, `tau_avg`, `tau_ratio`, `DOS_avg`, `DOS_ratio`, `tau_interface_ETL`, `tau_interface_HTL`, `rad_c`), the constructed physical parameters (`mu_n_pvk` … `rad_c`), and the values actually written to COMSOL (`*_in`). |
| `dataset_normalized.npz` | 131 MB | Arrays consumed by training/evaluation, see below. |
| `param_scaler.pkl` | 1 KB | `{"scaler": MinMaxScaler, "log_mask": bool[9]}` fitted on all 102,046 rows. |
| `J_scaler.pkl` | 6 KB | `MinMaxScaler` with one min/max pair per voltage column, fitted on all 102,046 rows. |

`dataset_normalized.npz` keys:

| Key | Shape | Meaning |
|---|---|---|
| `J_train` / `J_val` / `J_test` | (71432,131) / (15307,131) / (15307,131) | normalized current |
| `params_train` / `params_val` / `params_test` | (·,9) | normalized log10 parameters |
| `J_test_raw` | (15307,131) | physical current, mA cm⁻² |
| `params_test_raw` | (15307,9) | physical parameters |
| `log_transform_mask` | (9,) bool | all True |
| `param_names` | (9,) str | the order above |

The scalers were fitted on the **full** 102,046-curve set before partitioning
(manuscript Methods, "Partitioning and preprocessing").  This is why the primary
evaluation is not a fully isolated holdout, as stated in the paper.  The
training-only-scaling control is Table S15–S17.

### `dataset_independent_153067.tar.gz`
`JV_database_9D_interface_lifetimes-3.csv` (388 MB) — the separately generated
same-domain cohort of 153,067 curves used for Table S14.  Same 141-column layout,
independent `Sample_ID` numbering (1 … 300,000, i.e. drawn from a separate 300,000-curve
campaign).  No retraining or scaler refit was applied to this cohort.

### `independent_validation.tar.gz`
`preprocessed_independent.npz` plus the scripts and result tables in
`code/analysis/independent_validation/`.

### `exp1_benchmark.tar.gz`
`reviewer_experiments/exp1_leakage_free_baselines/` in full: the leakage-free dataset
(`leakage_free_dataset.npz`), training-only scalers, `split_indices_original_reproduced.npz`,
and the 15 trained models (VAE / deterministic AE / MLP × 5 seeds) with their
`eval_bundle.npz`.  Source of Table S13.

### `exp2_latent.tar.gz`
`reviewer_experiments/exp2_latent_uncertainty_decomposition/` in full, including the
500 latent draws.  Source of Table S12.

### `expanded_ratio.tar.gz`
`20261021_expanded_ratio_comparison_v2/` in full: both arms' preprocessed arrays
(`arm_original.npz`, `arm_expanded.npz`), per-arm scalers, split manifests, the ten
trained models, all per-run predictions, and the figure values.  Source of
Tables S19–S25 and Figs. S9–S11.

### `preprocessing_control.tar.gz`
`supplementary_validation_v4/T2_control/` in full: the H/L/T control runs, their
weights, `scaler_meta.npz`, training histories and the per-sample table
`control_per_sample.csv` (15,307 rows).  Source of Tables S15–S17.

### `interval_repair_A1.tar.gz`
`supplementary_validation_v3/A1_interval_repair/` — the empirical-quantile interval
baseline used in Table S17b.

### `figure_source.tar.gz`
`_frozen_preds.npz` (per-sample predictions, reconstructions, predictive scales and
device observables for all 15,307 test curves) plus the per-figure value tables and the
figure-composition decks.  See `docs/FIGURE_SOURCE_MAP.md`.

---

## 3. Normalization conventions — which scaler belongs to which result

| Result family | Normalization fitted on |
|---|---|
| Main model (accuracy, calibration, collision, noise, forward validation, Tables S2–S9, S11–S12, S14) | **all 102,046 retained curves** |
| Ratio-range comparison, both arms (Tables S19–S25, Figs. S9–S11) | **each arm's own training rows only** (16,992 curves per arm) |
| Leakage-free benchmark (Table S13) | **training subset only**, applied unchanged to val/test |
| Preprocessing-scope control L / T (Tables S15–S17) | L: full data; T: training subset only |

Do not mix them: absolute skill values are not comparable across these rows.

## 4. Baselines

* **MAE reduction** (Table 2, Table S11b) uses the **training-set median** of each
  parameter as the fixed baseline.
* **MSE skill** (`Skill_MSE = 1 − MSE_model / MSE_baseline`) uses the **training-set
  mean** of the corresponding test arm.
* **Cycle gap** is the RMSE between the decoder reconstruction and the COMSOL curve
  generated from the *predicted* parameters, over the stated voltage window.
* **COMSOL back-substitution error** is the difference between that COMSOL(pred) curve
  and the *target* curve — a different quantity from the cycle gap.
