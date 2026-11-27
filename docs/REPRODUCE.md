# Reproduction status

This file records three things:

* **verified here** — re-run during release preparation and compared against the
  published values;
* **archived only** — the scripts, inputs and outputs are shipped, but the step was
  not re-run;
* **needs COMSOL or an unrecovered file** — the inputs or the software required to
  rerun the step are not both available.

Environment used for every check below: Python 3.12.6, TensorFlow 2.20.0,
Keras 3.15.1, NumPy 2.3.5, scikit-learn 1.8.0, Matplotlib 3.10.8, Windows 11,
CPU only.

---

## 1. Dataset, split and scalers — **verified**

`data/splits/split_indices_seed42.npz` was reconstructed from
`JV_database_9D_interface_lifetimes-2.csv` with

```python
idx_train, idx_temp = train_test_split(np.arange(102046), test_size=0.30, random_state=42)
idx_val,  idx_test  = train_test_split(idx_temp,     test_size=0.50, random_state=42)
```

and compared against the frozen `dataset_normalized.npz`:

| check | result |
|---|---|
| sizes 71,432 / 15,307 / 15,307 | exact |
| `params_test_raw` equals CSV rows at `idx_test` | **exact, element-wise** |
| `J_test_raw` equals CSV rows at `idx_test` | **exact, element-wise** |
| `params_train`, `params_val`, `J_train`, `J_test` after re-fitting the scalers | **allclose, exact to < 1e-12** |
| `param_scaler.pkl` `data_min_`, `scale_` vs a fresh fit on all 102,046 rows | identical; one `data_max_` entry differs by 2.2e-16 |
| `J_scaler.pkl` vs a fresh fit | identical |

Notes:
* The frozen pickles were written by scikit-learn 1.3.2; loading them under 1.8.0
  emits an `InconsistentVersionWarning`.  The refitted scaler agrees to machine
  precision, so the warning is benign for this data.
* The train/validation/test **row indices and their `Sample_ID` mapping are
  archived** in `data/splits/split_indices_seed42.npz`.  They can also be
  rebuilt from three documented ingredients together: the retained CSV **row
  order**, the two-step `train_test_split` (30 % then 50/50) and `random_state
  = 42`.  Knowing the seed alone is not sufficient — the row order and the
  split calls are part of the recipe.  The archived indices were verified to
  reproduce the frozen arrays element-wise.  The manuscript's Methods describe
  this; the earlier sentence stating that membership could not be reproduced
  from the seed has been replaced in the current manuscript.
* `Sample_ID` is the 1-based row of the 200,000-row LHS design.  Joining on it
  reproduces `mu_n_pvk`, `mu_p_pvk`, `tau_ETL`, `tau_HTL` and `rad_c` to the three
  significant digits stored in the retained CSV.
* Independent cross-check: the SI's own per-sample table
  (`T8.2_per_sample_full_precision.csv`) records test index 595 ↔ `Sample_ID`
  117995, and `data/splits/split_indices_seed42.npz` gives `sample_id_test[595] =
  117995`.  An independently produced table therefore agrees with the reconstructed
  partition.

## 2. Frozen model loading and inference — **verified**

`models/vae-v6/{encoder,decoder,param_head}.h5` were loaded with a `Sampling`
custom layer and run on all 15,307 test curves (`z_mean` inference path, exactly as
in `code/pipeline/00_extract_frozen_predictions.py`).

| quantity | this run | paper | verdict |
|---|---|---|---|
| reconstruction MSE, mean | 1.211244e-05 | 1.211e-5 | match |
| reconstruction MSE, median | 2.969473e-06 | 2.969e-6 | match |
| per-parameter Pearson r, μₙ … Nᵥ | 0.906 / 0.919 / 0.878 / 0.881 / 0.909 / 0.896 | 0.878–0.919 | match |
| τ_ETL, τ_HTL, r_rad | 0.594 / 0.720 / 0.559 | 0.594 / 0.72 / 0.55–0.58 | match |

Archived per-sample arrays (`_frozen_preds.npz`) agree with the fresh run to
4.9e-5 absolute in normalized parameter units, 1.1e-6 for the reconstructions, and
`np.allclose` passes for the reconstructions.  The small parameter-space offset is
a TensorFlow-version floating-point difference (the archive was produced with an
earlier TensorFlow build); it is ~5e-5 of the unit interval and does not move any
reported digit.

## 3. Headline metrics recomputed from the archived tables — **verified**

| quantity | table | value | paper |
|---|---|---|---|
| 95% empirical coverage, 9 parameters | `analysis/evaluation_fixed/calibration_fixed.csv` | 0.9464 … 0.9692 | 0.946–0.969 |
| mean Spearman(σ, \|error\|) | `analysis/evaluation_fixed/uncertainty_error_fixed.csv` | 0.4283 | 0.428 |
| nearest-neighbour pairs (corrected rule) | `code/collision_revision_v2/source_data/fig3_pairs_v2.csv` | 11,245 | 11,245 |
| random-pair baseline | `code/collision_revision_v2/source_data/fig3_random_pairs.csv.gz` | 199,985 | 199,985 |
| mean Pearson r at 0% noise | `analysis/noise_robustness/noise_metrics_all.csv` | 0.8069 | 0.807 |
| forward-validation RMSE median | `analysis/forward_validation_unbiased/forward_metrics_summary.csv` | 2.6926 mA cm⁻² | 2.69 |
| \|ΔJsc\| median (n = 45) | `figures/build/fig4_de/data_used/Figure4e_per_sample.csv` | 0.111897 mA cm⁻² | 0.112 |
| \|ΔVoc\| median (n = 44) | ibid. | **0.022439 V** | 0.022 |
| \|ΔFF\| median (n = 44) | ibid. | **0.015533 (dimensionless)** = 1.5533 percentage points | 1.6 pp |
| \|ΔPCE\| median (n = 44) | ibid. | **0.471401 percentage points** (the PCE column is already in pp) | 0.471 pp |

The superseded collision table (7,666 pairs, `analysis/collision_analysis_superseded/`)
is shipped for provenance only and is **not** the analysis used in the paper.

### Device metrics: which table is authoritative

The device deviations quoted in the paper, drawn in Figure 4e and tabulated in
Table S8 are computed by `code/device_metrics.py` with the **interpolated**
downward zero crossing and **44 of 45 cases** for Voc, FF and PCE (one
back-substituted curve has no downward crossing inside 0–1.3 V).  The same four
medians are obtained independently from the SI's own per-sample table
(`data/tables/submission_v8/T8.2_per_sample_full_precision.csv`):

| metric | n | median |
|---|---|---|
| Jsc (mA cm⁻²) | 45 | 0.111897 |
| Voc (V) | 44 | 0.022439 |
| FF (dimensionless) | 44 | 0.015533 → 1.5533 pp |
| PCE (percentage points) | 44 | 0.471401 |

**Archived version.** `analysis/forward_validation_unbiased/forward_metrics_summary.csv`
holds a `device_mae` block with Voc median 0.030 V and FF median 0.0141.  That
block was produced by `forward_validation_postprocess.py`, which rounds Voc to
0.01 V before differencing and keeps the undefined-FF case in the sample.
Current results use `code/device_metrics.py`, whose values are the ones in the
table above.  The file is kept unchanged (see the `SUPERSEDED.md` beside it).

**Units.** FF is a dimensionless fraction; multiplying by 100 once gives
percentage points (1.5533 pp).  PCE is already stored in percentage points, so
its deviation (0.471401) must **not** be multiplied again.  The (e) panel script
`fig4e_ff_pp.py` applies the ×100 to FF only.

## 4. Quickstart — **verified**

`python code/quickstart_inference.py` runs against `data/examples/test_subset_200.npz`
and exits 0.  It is the command quoted in the README.

## 5. Archived but not re-run

These steps ship with scripts, inputs and outputs, but were not re-executed during
release preparation:

* the 15 leakage-free benchmark trainings (Table S13) — the trained models and their
  `eval_bundle.npz` are included;
* the ten ratio-range models (Tables S19–S25) — models, both arms' data and per-run
  predictions are included;
* the H/L/T preprocessing-scope control (Tables S15–S17) — weights and per-sample
  output are included;
* the latent-uncertainty draws (Table S12) — the 500-draw arrays are included;
* figure regeneration — the panel scripts and the composed layout decks are
  included, but no figure was re-rendered during release preparation.

## 6. Steps that need COMSOL or an unrecovered file

* **COMSOL back-substitution, cycle gap, mesh study** (Table S18a–e, Figs. S3–S4,
  Table S9).  The model file, the drivers, the input parameter vectors and the
  archived outputs are included.  Rerunning them requires COMSOL Multiphysics
  6.3 with the Semiconductor Module and LiveLink for MATLAB.
* **Main simulation campaign.**  The 200,000-row sampling design, the 102,046
  retained curves and the archived analysis are included.  The batch driver that
  produced the retained database was not recovered, so the campaign cannot be
  re-solved exactly as it was run.
* **Independent cohort.**  The 153,067 retained curves and their evaluation are
  included; the original 300,000-row sampling design was not recovered.
* **Batch order and initial weights of the historical training run.**  Not
  recorded.  The final weights are archived, and loading them reproduces the
  reported numbers.

## 7. Voc extraction (fixed in v1.0.1; unchanged since)

`code/pipeline/00_extract_frozen_predictions.py` used to derive the device
observables with two defects:

1. it took the **first sign change of either direction**, so a reverse-bias tail
   (negative → positive) would have been mistaken for an open-circuit crossing;
2. it called `np.interp(0, [J_k, J_k+1], [V_k, V_k+1])`, whose x-argument (the
   current) decreases along the sweep.  `np.interp` requires an increasing
   argument, so the result was one grid node rather than the linear root — for
   `J = [1, -1]` over `V = [1.26, 1.27]` it returns 1.27 V instead of 1.265 V.

The canonical extractor is now `code/device_metrics.py`: first **downward**
crossing, unique linear root, NaN for every dependent metric when no crossing
exists, NaN propagation for non-finite currents.  It is bit-identical
(≤ 1e-12) to the archived `v2lib.device_metrics` that produced Figure 4e and
Table S8, checked on all 15,307 test curves and all 90 forward-validation
curves.

**Impact on published results: none.**  On the 15,307 test curves every first
sign change is downward, so only defect 2 acted, and only on the `voc` and `ff`
arrays of `_frozen_preds.npz`:

| array | max abs change | note |
|---|---|---|
| `voc` | 1.0e-2 V | one grid step, always towards the true root |
| `ff` | 8.0e-3 | follows from the Voc change |
| `pce` | 3.6e-15 | invariant: `FF = Pmax/(Jsc·Voc)` cancels Voc |
| everything else | 0 | identical |
| `fig2b_repr_indices` | none | selection is PCE-based, and PCE is unchanged |

No figure, table or statistic in the paper depends on the old `voc`/`ff` arrays;
the published device metrics come from the corrected extractor path.  The
frozen `_frozen_preds.npz` is **not** overwritten — the recomputed file was
written to a separate directory and compared item by item.

The boundary cases above are covered by `code/tests/test_device_metrics.py`
(`python -m unittest discover -s code/tests`).

## 8. Finite-value checks in `verify_frozen_metrics.py`

The verifier checks the test-set inputs (`J_test`, `params_test`), the model
outputs (`z_mean`, `recon_test`, `param_mu`, `param_sigma`) and every derived
metric (MSE, Pearson r, 95 % coverage, Spearman rho) for NaN and Inf before
comparing anything with the published values.  Any non-finite value is named in
the report and the script exits 1 without printing PASS; a missing or
malformed input exits 2.  Shape mismatches are reported the same way.

The checks live in `code/metric_checks.py` and are covered by
`code/tests/test_metric_checks.py`.  A typical failure looks like:

```
FAIL: non-finite input
  - J_test: 1 of 2005217 values are not finite
```

The earlier verifier compared `abs(value - reference) / reference > tol`.
With `value = NaN` that comparison is False, so a corrupted input produced a
silent PASS; the explicit check above closes that path.
