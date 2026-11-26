# PATCH_NOTES — cross-arm evaluation repair (v2, 2026-10-21)

This file documents the defect found in the first delivery of the expanded-ratio matched
comparison (`E:\project\work1\20261021_expanded_ratio_comparison\`), what it affected, how it was
repaired, and what conclusions change. The v1 delivery is left untouched; v2 is a new directory.

---

## 1. Root cause

`04_evaluate.py` in v1 loaded the data of the **test** arm and used *that arm's* two scalers for
every evaluation, regardless of which arm the model had been trained on. In pseudocode, v1 did:

```python
# v1 — WRONG for model_arm != test_arm
J_scaled_test = J_scaled[test_arm][idx]                     # input normalisation of test arm
mu_norm       = model(model_arm, seed).predict(J_scaled_test)
L_pred        = param_scaler[test_arm].inverse_transform(mu_norm)   # output of test arm
```

That is correct on the diagonal (`model_arm == test_arm`, where it is the only possible choice)
and wrong for every cross-arm combination. Two independent errors are compounded:

1. **Input normalisation.** The current at each of the 131 voltages was mapped with the test
   arm's `current_scaler`. The two arms' current scalers are fitted on different training windows
   (e.g. `current_scaler` data ranges differ by up to ~2× in the upper voltage columns), so the
   model received inputs on the wrong scale.
2. **Output inverse transform.** The normalised parameter vector returned by the model was
   mapped back to physical log10 with the test arm's `param_scaler`. The model head was trained to
   predict in the *model* arm's normalised space, so both the scale (`data_range_`) and the offset
   (`data_min_`) were wrong — a different error for each of the nine parameters.

The wrong-scaler combination is therefore not a small perturbation: it changes the interpretation
of both the model input and the model output.

## 2. Correct rule (implemented in v2)

```python
J_phys  = arm[test_arm]["J"][idx]                      # archived physical J, mA/cm^2
J_input = current_scaler[model_arm].transform(J_phys)  # model arm's input scaler
mu_norm = model(model_arm, seed).predict(J_input)      # z_mean -> param head mu
L_pred  = param_scaler[model_arm].inverse_transform(mu_norm)   # model arm's output scaler
L_true  = arm[test_arm]["params_log10"][idx]           # truth from the test arm
```

Baselines remain the **test arm's**: Skill_MSE against its training mean, MAE reduction against its
training median, R²_test against the test mean. Both models therefore share rows, truth and
denominator within a column, while each uses its own I/O scalers.

Other properties preserved exactly:

- Physical currents are read directly from the archived arm cache (`arm_<arm>.npz`, key `J`);
  nothing is reconstructed by inverting `J_scaled`. The same-arm identity
  `current_scaler[arm].transform(J) == J_scaled` is asserted and holds with max difference **0.0**.
- Point prediction remains encoder `z_mean` → head `mu`; no latent sampling, no clipping of inputs
  or outputs, no checkpoint reselection, no metric redefinition.

## 3. Blast radius

| artefact | affected? | note |
|---|---|---|
| data, splits, scalers, config, 60 model files | **no** | 70/70 sha256 identical to v1 |
| 10 same-arm predictions (`pred_<arm>_<seed>__on_<arm>.csv`) | **no** | numerically identical: max \|Δ\| 1.4e-14 on the log10 and coordinate columns |
| 10 cross-arm predictions (`...__on_<other>.csv`) | **yes** | regenerated |
| Table A (own distribution) | no | identical to 1e-15 |
| Table B diagonal columns | no | identical |
| Table B cross columns (15 quantities × 5 seeds × 2 directions) | **yes** | regenerated |
| Paired differences on cross-arm tests | **yes** | regenerated |
| `fig03_common_test_paired` (ΔRMSE on both common tests) | **yes** | both panels contain cross-arm values |
| `fig02_skill_and_error`, `fig01_data_distributions` | no | Table A / data only; re-rendered files are byte-identical to v1 (sha256 match) |
| overlap-band diagnostic, original-model rows | **yes** | the original model on the expanded test is a cross evaluation |
| overlap-band diagnostic, expanded-model rows | no | diagonal |
| all cross-arm narrative in v1 RESULTS / PARAGRAPHS | **yes** | rewritten (§6) |

Changed cells: 150/150 cross-arm RMSE values and 60/60 cross-arm coordinate Skill values differ
from v1. Of the 60 coordinate Skill cells, **14 change sign** — all of them `a_mu` (7) and `a_D`
(7); `a_tau` was already positive. At the level of the nine single parameters, 53 of 90 cross-arm
Skill cells change sign.

Largest single change: `expanded` model on the `original` test, seed 20261025, `r_tau`
Skill_MSE −5.154 → −2.007 (Δ = +3.147), i.e. v1's widely negative outlier was created by the
scaler error. The change is not uniformly a "correction upwards": the same coordinate changed from
−0.581 to −2.102 at seed 20261021.

## 4. Why Table A must reproduce, and with what tolerance

On the diagonal the correct scaler and the buggy scaler are literally the same object, so the only
possible difference is floating-point non-determinism. Observed:

| check | value |
|---|---|
| max \|v2 − v1\| over all 900 diagonal metric rows (6 metrics × 15 quantities × 10 model/seed) | **1.6e-15** |
| max \|v2 − v1\| for diagonal `rmse` | 0.0 exactly |
| `06_verify.py` recomputation from prediction CSVs | 6.7e-16 over 720 values |
| `11_validate_inference.py` independent reference path (64-row batch, four combinations) | 3.6e-15 |

Tolerance basis: the values are float64; one ulp of a typical metric near 0.1–1 is ≈1–2e-16, and
a small number of operations (sum of 3,641 squared residuals, division) accumulates a few ulp. The
assertion threshold in `12_before_after.py` is 1e-12, four orders of magnitude above the observed
1.6e-15 and far below any physically meaningful change (the smallest cross-arm change is ~1e-2).
The diagonal path was additionally shown to be *bitwise* identical for raw inputs (archived
`J_scaled` vs `transform(J)` = 0.0) and for the predictions themselves, so no part of the diagonal
difference comes from the repaired code path.

## 5. Before/after, per coordinate

Common original-range test, mean over five seeds (`before_after_summary.csv`):

| coord | Skill v1 | Skill v2 | Δ | RMSE v1 | RMSE v2 | Δ |
|---|---|---|---|---|---|---|
| a_mu (exp model) | −0.1355 | **0.6495** | +0.785 | 0.9315 | **0.5189** | −0.413 |
| a_tau (exp model) | 0.4097 | 0.6727 | +0.263 | 1.5658 | 1.1679 | −0.398 |
| a_D (exp model) | −0.2574 | **0.5760** | +0.833 | 0.7592 | 0.4439 | −0.315 |
| r_mu (exp model) | −1.1750 | −1.6428 | −0.468 | 0.4741 | 0.5235 | +0.049 |
| r_tau (exp model) | −1.7588 | −1.9763 | −0.217 | 0.5087 | 0.5496 | +0.041 |
| r_D (exp model) | −1.3559 | −2.4308 | −1.075 | 0.5068 | 0.6118 | +0.105 |

Common expanded-range test, mean over five seeds:

| coord | Skill v1 | Skill v2 | Δ | RMSE v1 | RMSE v2 | Δ |
|---|---|---|---|---|---|---|
| a_mu (orig model) | −0.0339 | **0.6380** | +0.672 | 0.8834 | 0.5235 | −0.360 |
| a_tau (orig model) | 0.2032 | 0.6672 | +0.464 | 1.8189 | 1.1764 | −0.642 |
| a_D (orig model) | −0.1510 | **0.4466** | +0.598 | 0.7017 | 0.4874 | −0.214 |
| r_mu (orig model) | −0.9667 | −1.1121 | −0.145 | 0.5742 | 0.5951 | +0.021 |
| r_tau (orig model) | −0.4936 | −1.2020 | −0.708 | 0.4973 | 0.6045 | +0.107 |
| r_D (orig model) | −1.1010 | −1.5619 | −0.461 | 0.6146 | 0.6789 | +0.064 |

Common pattern: the shared scales were **understated** by v1 (Skill far too negative, RMSE far too
large) and the ratios were **understated in difficulty** (Skill too close to zero or not negative
enough). The sign of the v1 conclusion about ratios ("the other arm is a disaster") was right;
the sign about shared scales ("the other arm is also a disaster") was an artefact.

## 6. Conclusions withdrawn and retained

**Withdrawn**

1. "Both cross-evaluations are out of distribution and five of six coordinates fall below the
   constant-predictor baseline in each direction." Corrected: the shared-scale coordinates remain
   strongly positive on the other arm's test (0.45–0.67); only the three ratio coordinates are
   negative. The blanket "OOD" label is replaced by a per-family statement (`RESULTS.md` §3.4).
2. "The expanded model is better on shared scales and worse on ratios inside the old overlap
   band." Corrected: on identical in-band rows the models are tied on `a_mu` and `a_tau`
   (|ΔRMSE| ≤ 0.006 log10); only `a_D` favours the expanded model (0.4105 vs 0.4700).
3. "The mechanism is a fixed individual-parameter bound: `q` near 20 pushes `mu_n` and `mu_p` to
   opposite ends of a shared log range." Corrected sampling statement: the shared scale `g` is
   fixed by design and `p_n = g√q`, `p_p = g/√q`; widening `q` widens each individual parameter's
   range by 4×. See `data_QA.md` §7.3.
4. The numeric values of all cross-arm cells in v1 STATEMENTS, including the claim that a single
   `r_tau` seed produced an SD of 1.93.

**Retained (recomputed, unchanged)**

1. Table A in full, and the conclusion that widening the ratio prior did not reduce ratio error in
   physical log10 units (RMSE +24 to +27 % against a 1.62–1.65× growth of the baseline).
2. The baseline-variance decomposition of the ratio Skill "gain".
3. The 5/5 sign consistency of the paired comparisons across training seeds (signs of the paired
   differences are unchanged in direction for all six coordinates, though the magnitudes changed).
4. The equal-volume density caveat, now supported by the per-family slice: the expanded model is
   worse at `r` even on rows whose `r` lies inside the old window.
5. All scientific boundaries (training replicates not independent simulations; SD not a CI; low
   Skill does not prove absence of information).

## 7. Validation performed for the repair

`scripts/11_validate_inference.py` (23 checks, 0 FAIL; writes `out/qa/inference_validation.json`
and `out/qa/fault_injection_log.json`). It does not import the evaluator's prediction helper; it
re-implements the reference path from raw files.

| group | checks |
|---|---|
| provenance | 20 rows, one per model/seed/test; input and output scaler **owner == model_arm**; model/scaler/split/truth hashes match files on disk |
| same-arm identity | archived `J_scaled` equals `transform(J)` to 0.0 |
| alignment | both models see identical Sample_ID order, source_row and truth (max 0.0); baselines identical within a common test |
| independent reference path | 64-row extreme-heavy batch, four (model, test) combinations, recomputed from `arm_*.npz` + HDF5 + pickles: prediction diff 3.553e-15, truth diff 3.553e-15 |
| fault injection | A: output scaler swapped to test arm → detected, 0.257 log10 shift. B: input scaler swapped → detected, 3.634 log10. C: forged provenance row with wrong owner → detected. Faults run on a 64-row copy; the official predictions and models were not touched (verified by re-hashing 20 prediction CSVs and the 60 model files afterwards) |
| metrics | all 300 coordinate metric rows recomputed from the prediction CSVs, max 6.7e-16; 0 undefined |
| algebra | `a = (L0+L1)/2`, `r = L0−L1` on true and predicted columns, max 1.1e-14; **no second log10** (`10**true_log10` vs `true_phys`, max 4.3e-13) |
| invariance | 70/70 data/model/scaler/split/config hashes identical to v1; raw CSV hashes match the frozen config |

Note on the fault magnitudes: A alone shifts the output by 0.257 log10 on the 64-row test, B alone
by 3.634. v1 applied both at once, which is why some v1 cells were off by more than either single
fault: the two errors do not cancel.

`scripts/06_verify.py` re-ran on the new tables: 70 checks, 0 FAIL. `scripts/12_before_after.py`
asserts the diagonal tolerance and writes `before_after_metrics.csv`.

## 8. Model dependency

No retraining. The ten model directories are byte-identical to v1 and to the independent model
package:

- local: `models/{original,expanded}_{20261021..20261025}/{encoder,decoder,param_head}.h5`
- upstream archive: `E:\project\work1\20261021_expanded_ratio_comparison\deliverables\models_20261021.zip`,
  sha256 `6617018bca8471e46c30966123317c2e24cb873ce827eccdfbb1558761aee3f8` (4,259,060 bytes)
- per-file sha256 for every model actually used: `out/metrics/inference_provenance.csv` (20 rows ×
  encoder/decoder/param_head) and `out/metrics/eval_manifest.json`

The complete v1 delivery, including v1 predictions and v1 tables, is at
`E:\project\work1\20261021_expanded_ratio_comparison\deliverables\review_package_20261021.zip`
(sha256 `4bb1e3f270b8696439bee81d5dfbc4f83b78e4acc98dba4f7faf6fee9cb5de57`, 33,278,991 bytes) and is not modified.

## 9. Files changed in v2

| file | change |
|---|---|
| `scripts/04_evaluate.py` | rewritten prediction path (§2), adds `input_scaler_arm` / `output_scaler_arm` columns and `inference_provenance.csv` |
| `scripts/11_validate_inference.py` | **new** — 23-check independent validation + fault injection |
| `scripts/12_before_after.py` | **new** — v1→v2 comparison tables |
| `scripts/10_slice_diagnostic.py` | unchanged code, re-run (cross-arm rows change) |
| `scripts/05_figures.py` | unchanged code, re-run |
| `out/predictions/*__on_*` | 20 files regenerated (10 diagonal numerically identical, max \|Δ\| 1.4e-14 on log10/coordinate columns; 10 cross changed) |
| `out/metrics/*` | all tables regenerated; `inference_provenance.csv`, `before_after_*` added |
| `figures/fig03_common_test_paired.*` | regenerated from corrected data |
| `RESULTS.md` | rewritten cross-arm sections; withdrawn/retained list §7 |
| `PARAGRAPHS_EN.md` | corrected candidate text |
| `data_QA.md` | §6 three-count provenance; §7.3 corrected sampling rule |
| `EXPERIMENT_DESIGN.md` | §4 scaler spans corrected; §5 scaler-ownership rule; §6 per-family reading |
| `README.md` | v2 layout and reproduce order |
| manuscript / SI (Word) | **not touched** |

## 10. Reproduce

```
py -3 scripts\04_evaluate.py          # 20 predictions + all metric tables + provenance
py -3 scripts\11_validate_inference.py  # must print FAILURES 0 and exit 0
py -3 scripts\12_before_after.py      # must print diagonal max |v2-v1| < 1e-12
py -3 scripts\05_figures.py
py -3 scripts\10_slice_diagnostic.py
py -3 scripts\06_verify.py            # 70 checks, 0 FAIL
py -3 scripts\09_report_numbers.py
py -3 scripts\08_package.py
```
