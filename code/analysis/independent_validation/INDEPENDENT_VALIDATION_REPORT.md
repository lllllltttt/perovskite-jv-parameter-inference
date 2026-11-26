# INDEPENDENT VALIDATION REPORT
## Same-domain independent replication of the locked manuscript's recoverability and clean-domain uncertainty conclusions

**Date:** 2026-08-26
**Frozen model:** VAE-v6 (locked manuscript `manuscript_stage1_submission_locked.md`)
**Independent dataset:** `data/JV_database_9D_interface_lifetimes-3.csv` (N = 153,067)
**Reference dataset:** `data/JV_database_9D_interface_lifetimes-2.csv` (N = 102,046 retained; train 71,432 / val 15,307 / test 15,307)

---

## 0. Executive summary

The frozen VAE-v6 checkpoint, evaluated **without any retraining, scaler refit, hyperparameter change, or locked-manuscript edit** on a separately generated 153,067-sample physically filtered COMSOL simulation dataset, reproduces every headline quantitative result of the locked manuscript to within a few thousandths:

| quantity | original test | independent | Δ |
|---|---|---|---|
| Mean Pearson (9 params) | 0.8069 | **0.8068** | −0.0001 |
| 95% predictive coverage (mean) | 0.9574 | **0.9568** | −0.0006 |
| Mean Spearman(σ, \|err\|) | 0.4283 | **0.4324** | +0.0041 |
| Shared-scale vs ratio gap | 0.562 | **0.555** | −0.007 |

The new dataset sits **essentially inside the frozen normalization envelope** (only 0.018% of samples have any out-of-range J value after frozen scaling) and its marginal distributions are near-identical to the retained set (median log10 shifts ≤ 0.009 decades). **Overlap with the original retained set is zero** at both the parameter-vector and J–V-vector level, supporting its status as a separately generated dataset.

**Verdict: STRONG INDEPENDENT REPLICATION — WORTH INTEGRATING LIGHTLY.**
All three replication verdicts are the strongest available (Point recovery: STRONG; Calibration: REPRODUCED; Shared-scale ≫ ratio: PASS).

---

## 1. Phase 0 — Frozen artifact manifest

All artifacts were identified and verified **from code and files**; the complete manifest is in
`FROZEN_ARTIFACT_MANIFEST.md`. Key identities:

- Checkpoint: `data/vae-v6/vae-v6/encoder.h5`, `param_head.h5`, `decoder.h5` (+ `best.weights.h5`).
- J scaler: `data/J_scaler.pkl` — sklearn `MinMaxScaler`, per-column (131 features), fitted on the full retained set before the split.
- Parameter scaler: `data/param_scaler.pkl` — `{"scaler": MinMaxScaler, "log_mask": [True]*9}`, fitted on log10-transformed full retained set before the split.
- Parameter order: mu_n_pvk, mu_p_pvk, tau_n_pvk, tau_p_pvk, Nc_eff_pvk, Nv_eff_pvk, tau_ETL, tau_HTL, rad_c (identical in CSV, training, eval, and Exp3 code).
- Voltage grid: 131 points, `linspace(0, 1.3, 131)` → 0.00–1.30 V in 0.01-V steps, mA/cm².
- Point prediction: `ParamHead(mu_z)` — Gaussian head evaluated at the **latent mean**; no latent Monte-Carlo sampling.
- Predictive scale: `sigma = clip(softplus(raw) + 0.01, 0.01, 1.0)` (matches training exactly).
- **Pipeline reproducibility gate: PASS.** Re-running the frozen inference stack on the *original* test set reproduces the archived reference Pearson / 95% coverage / Spearman values to max deviation **5×10⁻⁵**. The independent numbers below are therefore fully comparable to the manuscript reference.

## 2. Phase 1 — Dataset compatibility gate

Full report: `DATASET_COMPATIBILITY_REPORT.md`. Summary:

- Schema: identical 141 columns (`Sample_ID` + 9 params + `J_000…J_130`), identical parameter order, identical column names.
- Parameter ranges: near-identical; max |Δ log-span| = **0.085** (Nv_eff), most ≤ 0.02.
- J–V conventions: 131 points, J(V=0) > 0, monotonic non-increasing sweep (100% of rows, both), zero crossing present (100% of rows), negative current at high forward bias. No "reverse-bias" labeling used.
- Data quality: 0 missing, 0 inf, 0 duplicated rows, 0 duplicated parameter vectors, 0 malformed rows in both files.
- Overlap with original retained set: **0** exact parameter-vector overlaps and **0** exact J–V-vector overlaps (6-decimal normalized space, both directions).
- Data-generation compatibility: same generator family (PSC_LHS_9D_interface_lifetimes, LHS, seed 42 concept), same COMSOL drift-diffusion family/geometry (archived recipe), same physical filtering concept. The new file carries 153,067 retained rows vs 102,046 — a separately generated draw.

> **Verdict: COMPATIBILITY PASS WITH MILD SHIFT — REPORT AS DISTRIBUTION-SHIFT REPLICATION.**
> The shift is *mild* in the precise sense that the normalized out-of-range fractions (below) are tiny and the marginal distributions overlap almost perfectly. We nonetheless label it a distribution-shift replication because generation was independent and the exact generation script for the −3 file is not archived in the repo.

## 3. Phase 2 — Frozen preprocessing only (out-of-range diagnostics)

Frozen transforms applied with `.transform()` only — no fitting on the new data.

| quantity | value |
|---|---|
| J values below 0 after frozen scaling | 0.0006% |
| J values above 1 after frozen scaling | 0.0003% |
| Samples with ≥ 1 out-of-range J value | 0.0176% |
| Per-parameter normalized out-of-range (any) | ≤ 0.0033% (all 9 params) |

The new dataset is effectively inside the frozen normalization envelope. The only extremal difference: new-data minimum J at V=1.30 V is −6517.22 vs the frozen scaler's −6358.76 (both ~−6.4×10³ mA/cm²), affecting <0.02% of samples.

## 4. Phase 3 — Frozen model inference

- N = 153,067 independent samples encoded through the frozen encoder; Gaussian head evaluated at z_mean.
- Outputs: `independent_predictions.csv` (153,067 rows × 55 cols: sample_id, true physical, true log10, true normalized, predicted normalized, predicted physical, sigma for all 9 params).
- Predicted normalized range [−0.419, 1.376]; sigma range [0.0106, 0.8968] ⊂ [0.01, 1.0]; no NaNs.

## 5. Phase 4 — Primary replication metrics (normalized log10 space)

Source: `independent_parameter_metrics.csv`.

| param | orig r | indep r | Δr | orig MAE | indep MAE | orig RMSE | indep RMSE |
|---|---|---|---|---|---|---|---|
| mu_n | 0.9063 | 0.9067 | +0.0004 | 0.0747 | 0.0746 | 0.1014 | 0.1012 |
| mu_p | 0.9194 | 0.9195 | +0.0000 | 0.0703 | 0.0708 | 0.0950 | 0.0948 |
| tau_n | 0.8783 | 0.8793 | +0.0010 | 0.0908 | 0.0903 | 0.1284 | 0.1273 |
| tau_p | 0.8808 | 0.8820 | +0.0012 | 0.0921 | 0.0915 | 0.1271 | 0.1260 |
| Nc | 0.9090 | 0.9087 | −0.0004 | 0.0588 | 0.0593 | 0.0794 | 0.0801 |
| Nv | 0.8956 | 0.8954 | −0.0002 | 0.0649 | 0.0651 | 0.0840 | 0.0841 |
| tau_ETL | 0.5936 | 0.5885 | −0.0051 | 0.1881 | 0.1897 | 0.2343 | 0.2357 |
| tau_HTL | 0.7199 | 0.7186 | −0.0014 | 0.1579 | 0.1592 | 0.2021 | 0.2037 |
| rad_c | 0.5592 | 0.5625 | +0.0034 | 0.1918 | 0.1910 | 0.2403 | 0.2390 |
| **mean** | **0.8069** | **0.8068** | **−0.0001** | 0.1100 | 0.1102 | 0.1436 | 0.1436 |

Max per-parameter Pearson change = 0.0051 (tau_ETL, −). MAE/RMSE changes are ≤ 0.002.

## 6. Phase 5 — Recoverability-hierarchy replication

Group means (Pearson):

| group | params | orig | indep |
|---|---|---|---|
| bulk transport / lifetime / DOS | mu_n, mu_p, tau_n, tau_p, Nc, Nv | 0.8982 | **0.8986** |
| interfacial slabs | tau_ETL, tau_HTL | 0.6568 | **0.6535** |
| radiative coefficient | rad_c | 0.5592 | **0.5625** |

- Six bulk parameters remain a high-recoverability group (0.879–0.920 indep; orig 0.878–0.919).
- tau_ETL / tau_HTL remain clearly weaker (0.589 / 0.719 vs orig 0.594 / 0.720).
- rad_c remains the single weakest parameter (0.563 vs orig 0.559).

> **HIERARCHY REPRODUCED.** bulk ≫ interfacial ≥ radiative, identical to the locked manuscript.

## 7. Phase 6 — Clean-domain predictive calibration (frozen sigma, no recalibration)

Source: `independent_calibration.csv`. Empirical coverage at all nominal levels:

| level | orig mean | indep mean | Δ |
|---|---|---|---|
| 50% | 0.479 | 0.4766 | −0.003 |
| 80% | 0.797 | 0.7968 | −0.000 |
| 90% | 0.908 | 0.9072 | −0.001 |
| 95% | 0.9574 | **0.9568** | −0.0006 |

Per-parameter 95% coverage (orig → indep): mu_n 0.9475→0.9480, mu_p 0.9522→0.9491, tau_n 0.9583→0.9580, tau_p 0.9597→0.9607, Nc 0.9464→0.9457, Nv 0.9499→0.9488, tau_ETL 0.9692→0.9696, tau_HTL 0.9667→0.9661, rad_c 0.9664→0.9655. Max per-param Δ = 0.0031.

No recalibration, no temperature scaling, no interval rescaling — the frozen Gaussian-head calibration **transfers unchanged**.

> **CALIBRATION REPRODUCED.**

## 8. Phase 7 — Uncertainty–error association

Source: `independent_uncertainty_error.csv`. `Spearman(predicted sigma, |error|)`:

| param | orig | indep | Δ |
|---|---|---|---|
| mu_n | 0.398 | 0.401 | +0.003 |
| mu_p | 0.334 | 0.340 | +0.006 |
| tau_n | 0.646 | 0.646 | +0.000 |
| tau_p | 0.622 | 0.615 | −0.006 |
| Nc | 0.353 | 0.360 | +0.007 |
| Nv | 0.244 | 0.255 | +0.011 |
| tau_ETL | 0.377 | 0.392 | +0.015 |
| tau_HTL | 0.465 | 0.469 | +0.004 |
| rad_c | 0.415 | 0.413 | −0.002 |
| **mean** | **0.428** | **0.432** | **+0.004** |

σ remains informative on the independent dataset — the association is if anything marginally stronger. All Spearman p-values are effectively 0 (N = 153,067).

## 9. Phase 8 — Prior-coordinate replication (shared-scale vs ratio)

Source: `independent_prior_coordinate_recovery.csv`. Same Exp3 formulas in log10-physical space.

| coord | orig r | indep r | Δ |
|---|---|---|---|
| a_mu (shared) | 0.9250 | 0.9253 | +0.0003 |
| r_mu (ratio) | 0.4289 | 0.4326 | +0.0037 |
| a_tau (shared) | 0.8819 | 0.8830 | +0.0011 |
| r_tau (ratio) | 0.3517 | 0.3525 | +0.0008 |
| a_D (shared) | 0.9248 | 0.9247 | −0.0001 |
| r_D (ratio) | 0.2663 | 0.2826 | +0.0163 |

- Shared-scale mean: 0.9106 → 0.9110 (Δ +0.0004).
- Ratio mean: 0.3490 → 0.3559 (Δ +0.0069).
- **Shared-minus-ratio gap: 0.562 → 0.555.** The dominant shared-scale channel and the weak-but-real ratio channel both reproduce, with essentially unchanged separation.

> **SHARED-SCALE ≫ RATIO REPLICATION: PASS.** No new independent-prior experiment was run.

## 10. Phase 9 — Distribution comparison (diagnostic only, no COMSOL)

Source: `original_vs_independent_summary.csv`. In log10 physical space:

- All nine parameters: median shift ≤ **0.009 decades**, IQR (q25/q75) shifts ≤ 0.007 decades. Min/max nearly identical.
- J observables: Jsc median 23.742 (both); Voc median 1.160 V (both); Jmin median −31.7 vs −32.0; Jmax median 23.742 (both).
- No PCE column is present in either CSV, so no PCE comparison (as expected — PCE is derived in the device-metric layer, not stored).

Interpretation: the independent dataset is a separately generated draw from an **effectively identical simulation domain**; differences that could affect performance are limited to tiny sampling/filtering details and the slightly wider high-voltage current tail. The near-zero performance change is consistent with this.

## 11. Phase 11 — Replication verdicts

### A. Point recovery
**STRONG REPLICATION.** Mean Pearson 0.8068 vs 0.8069 (Δ = −0.0001); max per-param change 0.005; recoverability hierarchy reproduced with the same group ordering and near-identical group means.

### B. Calibration
**CALIBRATION REPRODUCED.** All four nominal levels transfer within ≤ 0.003 of the original means, with the frozen sigma unmodified.

### C. Prior-coordinate conclusion
**SHARED-SCALE ≫ RATIO REPLICATION: PASS.** Gap 0.555 (independent) vs 0.562 (original).

## 12. Phase 12 — Manuscript impact decision

**OUTCOME A — STRONG REPLICATION.**

Recommendation: **worth adding as a concise independent simulation replication result.**

- Suggested placement: 1–2 sentences in Results or Limitations/Discussion + one compact SI table (the summary table in this report); no restructuring of main figures, no retraining.
- Suggested wording must say **"separately generated simulation dataset"** — e.g.:
  > "The frozen model reproduces its recoverability hierarchy, approximately calibrated predictive intervals, and shared-scale-dominated bulk recovery on a **separately generated simulation dataset** (153,067 physically filtered COMSOL curves; mean Pearson 0.807 vs 0.807 on the original retained set; 95% coverage 0.957 vs 0.957), indicating that the reported conclusions are robust to independent regeneration of the same simulation domain."
- Do **not** use: "external experimental validation", "out-of-domain validation", or "experimental generalization".

## 13. Hard-constraint compliance

| action | done? |
|---|---|
| Retrain / fine-tune VAE-v6 | **NO** |
| Train any new model | **NO** |
| Refit J scaler / parameter scaler | **NO** (`.transform()` only) |
| Alter / select a new checkpoint | **NO** (frozen `encoder.h5` / `param_head.h5` loaded read-only) |
| Optimize hyperparameters / modify architecture | **NO** |
| Run COMSOL / regenerate simulations | **NO** |
| Merge new data into training set | **NO** |
| Change the locked manuscript | **NO** |
| Noise augmentation / new collision analysis / Stage II / new model | **NO** |

## 14. Outputs produced

| file | content |
|---|---|
| `FROZEN_ARTIFACT_MANIFEST.md` | authoritative frozen artifacts (verified from code) |
| `DATASET_COMPATIBILITY_REPORT.md` | Phase 1 compatibility gate |
| `preprocessing_out_of_range.txt` | Phase 2 out-of-range diagnostics |
| `independent_predictions.csv` | Phase 3 frozen predictions (153,067 × 55) |
| `independent_parameter_metrics.csv` | Phase 4 point metrics (orig vs indep) |
| `independent_calibration.csv` | Phase 6 calibration, all 4 levels |
| `independent_uncertainty_error.csv` | Phase 7 σ–error association |
| `independent_prior_coordinate_recovery.csv` | Phase 8 shared/ratio coordinates |
| `original_vs_independent_summary.csv` | Phase 9 distribution summary |
| `independent_validation_summary.png` / `.pdf` | compact summary figure (Pearson panel + coordinate panel) |
| `INDEPENDENT_VALIDATION_QC.md` | QC gates G1–G14 |

Scripts (reproducible, read-only on all frozen artifacts): `phase1_compatibility_check.py`, `phase2_3_preprocess_infer.py`, `phase4_7_metrics.py`, `phase8_9_prior_dist.py`, `phase0_repro_check.py`, `make_summary_figure.py`.
