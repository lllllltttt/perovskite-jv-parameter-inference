# INDEPENDENT VALIDATION QC
## Gate-by-gate verification (G1–G14) + extra integrity checks

**Date:** 2026-08-26
**Scope:** frozen VAE-v6 evaluated on `JV_database_9D_interface_lifetimes-3.csv` (N=153,067)

---

## Mandated QC gates

| # | gate | result | evidence |
|---|---|---|---|
| G1 | New CSV schema verified | **PASS** | 141 cols (`Sample_ID` + 9 params + `J_000…J_130`); identical column names/order vs retained file. `DATASET_COMPATIBILITY_REPORT.md` §schema. |
| G2 | Same parameter meanings/units verified | **PASS** | Identical 9 params in identical order; all strictly positive; log10-range overlap near-exact (max Δlog-span 0.085). Phase-1 A. |
| G3 | Voltage grid / J convention verified | **PASS** | 131 points = 0.00–1.30 V step 0.01 V; J(V=0)>0; monotonic non-increasing (100% rows); zero-crossing present (100% rows); negative current at high V; mA/cm². Phase-1 B. |
| G4 | Original frozen scaler used unchanged | **PASS** | `J_scaler.pkl` / `param_scaler.pkl` loaded and applied via `.transform()` only; no `fit`, no new scaler, no `fit_transform`. `phase2_3_preprocess_infer.py`. |
| G5 | Original checkpoint used unchanged | **PASS** | Frozen `encoder.h5` + `param_head.h5` loaded read-only (`keras.load_model`, `custom_objects={"Sampling":...}`); `best.weights.h5` untouched. |
| G6 | No scaler refit | **PASS** | Same as G4; preprocessed values differ from refit values by construction (out-of-range fractions reported, 0.018% samples). |
| G7 | No model training / fine-tuning | **PASS** | Only `encoder.predict` / `param_head.predict` (inference). No gradients, no `fit()`, no optimizer. |
| G8 | No COMSOL run | **PASS** | No simulation tool invoked; all Phase-9 distribution data read from existing CSVs. |
| G9 | Original-vs-new overlap checked | **PASS** | Exact overlap in 6-decimal normalized space: **0/153,067** parameter vectors, **0/153,067** J–V vectors. Phase-1 D. |
| G10 | 9-parameter point metrics completed | **PASS** | Pearson / MAE / RMSE for all 9 params in normalized log10 space. `independent_parameter_metrics.csv`. |
| G11 | Calibration completed without recalibration | **PASS** | Frozen sigma, frozen z-quantiles; coverage at 50/80/90/95% for all 9 params; no recalibration/temperature scaling. `independent_calibration.csv`. |
| G12 | Sigma–error association completed | **PASS** | `Spearman(σ, |err|)` for all 9 params. `independent_uncertainty_error.csv`. |
| G13 | Shared-scale vs ratio replication completed | **PASS** | 6 coordinates (a_mu, r_mu, a_tau, r_tau, a_D, r_D) from frozen log10-physical predictions. `independent_prior_coordinate_recovery.csv`. |
| G14 | No locked-manuscript modification | **PASS** | No edit to `manuscript_stage1_submission_locked.md`; this validation only writes into `independent_validation/`. |

**All 14 mandated gates PASS.**

## Extra integrity checks

| check | result | evidence |
|---|---|---|
| Pipeline reproducibility on original test set | **PASS** | Max |Δ| vs archived reference: Pearson 4.7e-05, 95% cov 4.4e-05, Spearman 3.9e-05. `phase0_repro_check.py`. |
| Reference Pearson values verified vs locked manuscript | **PASS** | Table 2 (mu_n 0.906 … rad_c 0.559) matches `evaluation_fixed/parameter_metrics.csv` and the values used in this analysis. |
| Reference 95% coverage verified | **PASS** | `evaluation_fixed/calibration_fixed.csv` (0.9475 … 0.9664) matches mission values. |
| Reference Spearman values verified | **PASS** | `evaluation_fixed/uncertainty_error_fixed.csv` (0.3982 … 0.4147) matches mission values. |
| Exp3 coordinate references verified | **PASS** | `EXP3_FINAL_REPORT.md` §6 / `results/frozen_coordinate_recoverability.csv` (a_mu 0.9250 … r_D 0.2663) matches Table S11 of the locked manuscript. |
| Inference output integrity | **PASS** | No NaN in mu/sigma; sigma ∈ [0.0106, 0.8968] ⊂ [0.01, 1.0]; 153,067 prediction rows. |
| New dataset cleanliness | **PASS** | 0 missing / 0 inf / 0 duplicate rows / 0 duplicate parameter vectors / 0 malformed rows. |
| Independence of the new dataset | **PASS** | 0 exact overlap with retained set (parameter and J–V level); separate generation evidenced by different retained count (153,067 vs 102,046). |
| Domain-shift magnitude | **MILD** | ≤0.018% samples with any out-of-range J after frozen scaling; median log10 param shifts ≤ 0.009 decades. Labeled **distribution-shift replication** (conservative), consistent with the observed near-zero metric change. |

## Files verified (read-only) for reference values

- `evaluation_fixed/parameter_metrics.csv`
- `evaluation_fixed/calibration_fixed.csv`
- `evaluation_fixed/uncertainty_error_fixed.csv`
- `evaluation_fixed/evaluation_summary.txt`
- `reviewer_experiments/exp3_prior_coordinate_recoverability/EXP3_FINAL_REPORT.md`
- `manuscript_stage1_submission_locked.md` (Tables 2, S11)

## Scripts used (all inference/analysis only)

`phase0_repro_check.py`, `phase1_compatibility_check.py`, `phase2_3_preprocess_infer.py`,
`phase4_7_metrics.py`, `phase8_9_prior_dist.py`, `make_summary_figure.py`.

---

**QC verdict: ALL GATES PASS. Independent replication numbers are trustworthy and directly comparable to the locked-manuscript reference.**
