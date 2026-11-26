# Reproduction status

This file distinguishes three things honestly:

* **verified here** — actually re-run during release preparation and compared
  against the published values;
* **archived only** — the scripts, inputs and outputs are shipped, but the step was
  not re-run during release preparation;
* **not reproducible from this release** — requires COMSOL, or a record that was
  never saved.

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
* The manuscript states that partition membership "cannot be reproduced from the
  documented splitting seed".  In this release it *is* recorded explicitly in
  `data/splits/split_indices_seed42.npz`, and that reconstruction was verified to
  reproduce the frozen arrays exactly.  The archive is therefore the authoritative
  record; the note in the Methods remains true for the seed alone.
* `Sample_ID` is the 1-based row of the 200,000-row LHS design.  Joining on it
  reproduces `mu_n_pvk`, `mu_p_pvk`, `tau_ETL`, `tau_HTL` and `rad_c` to the three
  significant digits stored in the retained CSV.

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
| \|ΔJsc\|, \|ΔVoc\|, \|ΔFF\|, \|ΔPCE\| medians | ibid. | 0.1119, 0.030, 0.0141, 0.4714 | 0.112, 0.030, 0.014, 0.471 |

The superseded collision table (7,666 pairs, `analysis/collision_analysis_superseded/`)
is shipped for provenance only and is **not** the analysis used in the paper.

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

## 6. Not reproducible from this release

* **COMSOL back-substitution, cycle gap, mesh study** (Table S18a–e, Figs. S3–S4,
  Table S9).  Regenerating these requires COMSOL Multiphysics 6.3 with LiveLink for
  MATLAB.  The archived outputs are included; the model file and drivers are
  included; no licence is.
* **The original 200,000-curve campaign** — the design table and the retained
  curves are included, but re-solving the 200,000 COMSOL runs is a multi-week
  cluster job.
* **Batch order / initial weights of the historical training run** — the paper says
  this was not recorded, and nothing in this release changes that.  See
  `docs/KNOWN_LIMITATIONS.md`.
