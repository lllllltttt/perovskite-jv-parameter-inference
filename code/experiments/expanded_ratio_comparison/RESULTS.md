# Results — expanded ratio-range matched comparison (v2, 2026-10-21)

**Revision status.** This is the corrected evaluation. The ten trained models, the two data splits,
the four scalers and the raw data are byte-identical to the first delivery (70/70 hashes checked);
only the evaluation of a model on the *other* arm's test set was repaired. In v1 both the input
normalisation and the output inverse transform of a cross-arm evaluation used the **test** arm's
scalers; v2 uses the **model** arm's scalers for both, with the test arm supplying rows, truth and
baselines. Root cause, blast radius and the before/after numbers are in `PATCH_NOTES.md`. Table A
(each model on its own test) is unchanged, as it must be.

Ten runs (2 arms × 5 seeds), all `completed`, all terminated by early stopping on
`val_param_loss` (patience 50), no failures and no substitutions. Training length: original arm
401–585 epochs, expanded arm 317–503; wall time 159.9–255.5 s per run on one CPU. Every number
below is regenerated from `out/predictions/*.csv` by `scripts/04_evaluate.py` and independently
re-checked by three separate scripts:

- `scripts/06_verify.py` — 70 checks, 0 FAIL; max recomputation difference 6.7e-16.
- `scripts/11_validate_inference.py` — 23 checks, 0 FAIL (provenance, independent reference path,
  model alignment, fault injection, metric/a–r algebra, hash invariance).
- `scripts/12_before_after.py` — diagonal reproduces v1 with max |Δ| = 1.6e-15.

## 1. Headline

Under identical data volume (24,274 rows, 16,992 train / 3,641 val / 3,641 test), identical
network, loss, optimiser and stopping rules, and with the shared-scale sampling priors unchanged:

1. **The ratio coordinates are still recovered poorly in both arms, and widening the prior does
   not change that in normalised terms.** In-distribution Skill_MSE for `r_mu` is 0.141 ± 0.011
   (original) vs 0.141 ± 0.010 (expanded); for `r_tau` 0.073 ± 0.012 vs 0.126 ± 0.034; for `r_D`
   0.049 ± 0.010 vs 0.089 ± 0.004. All three remain far below the shared scales (0.65–0.78).
2. **The apparent Skill gains for the ratio coordinates come with a larger baseline variance, not
   with smaller error.** The training-mean baseline MSE on the expanded test is 1.62–1.65× that of
   the original test for all three ratio coordinates, while the physical-log10 RMSE is 24–27 %
   *larger* (e.g. `r_mu`: 0.2985 → 0.3796). Decomposing `Skill = 1 − MSE/MSE_base` shows the
   numerator grew roughly as fast as the denominator.
3. **The shared-scale and ratio coordinates behave very differently in the corrected cross-arm
   comparison.** With the scaler error removed, both models keep a large positive Skill on `a`
   when tested on the other arm's distribution (0.45–0.67), while every ratio coordinate falls far
   below the constant-predictor baseline (−1.1 to −2.4). The v1 statement that both
   cross-evaluations are out-of-distribution with five of six coordinates negative in each
   direction is **withdrawn** (§3.3).
4. **Inside the old ratio window on identical rows, the ratio degradation of the expanded model
   persists.** Restricting to rows whose matching ratio lies in 0.2–5, its ratio RMSE is
   0.24–0.27 log10 larger than the original model's, whereas the two models are tied on two of
   three shared scales (§5). The v1 claim that the expanded model is better on `a` inside that band
   is **withdrawn**; only `a_D` remains better.

No direction was presupposed and none is asserted beyond these statements.

## 2. Table A — each model on its own distribution

Mean ± sample SD over the five training seeds (n = 3,641 test rows per arm). `a` and `r` are in
physical log10 parameter space. **These values are identical to v1** (max |Δ| over the 900 rows of
this table = 1.6e-15, floating-point level), which is the expected behaviour of the repair: on the
diagonal the correct and the buggy scaler are the same scaler.

| coord | Skill orig | Skill exp | ΔSkill | RMSE orig | RMSE exp | ΔRMSE | MAE orig | MAE exp |
|---|---|---|---|---|---|---|---|---|
| a_mu | 0.7641 ± 0.0070 | 0.7796 ± 0.0061 | **+0.0155** | 0.4257 ± 0.0064 | 0.4085 ± 0.0056 | **−0.0172** | 0.3182 | 0.3089 |
| r_mu | 0.1410 ± 0.0114 | 0.1409 ± 0.0102 | −0.0001 | 0.2985 ± 0.0020 | 0.3796 ± 0.0023 | **+0.0811** | 0.2346 | 0.2893 |
| a_tau | 0.7417 ± 0.0034 | 0.7238 ± 0.0034 | −0.0179 | 1.0376 ± 0.0069 | 1.0716 ± 0.0066 | +0.0340 | 0.7690 | 0.7857 |
| r_tau | 0.0729 ± 0.0116 | 0.1262 ± 0.0343 | +0.0533 | 0.3068 ± 0.0019 | 0.3808 ± 0.0074 | **+0.0740** | 0.2415 | 0.2872 |
| a_D | 0.7027 ± 0.0290 | 0.6539 ± 0.0107 | **−0.0488** | 0.3714 ± 0.0181 | 0.3857 ± 0.0060 | +0.0143 | 0.2828 | 0.2974 |
| r_D | 0.0491 ± 0.0097 | 0.0888 ± 0.0037 | +0.0397 | 0.3221 ± 0.0016 | 0.4049 ± 0.0008 | **+0.0828** | 0.2576 | 0.3013 |

Pearson (coordinates): a_mu 0.874→0.883, r_mu 0.376→0.376, a_tau 0.861→0.851, r_tau 0.297→0.368,
a_D 0.839→0.809, r_D 0.225→0.299. `R²_test` differs from Skill only in the fourth decimal
because the test-mean and training-mean baselines nearly coincide for these splits; it is not
Pearson².

Nine single parameters (Skill_MSE, original → expanded): `mu_n` 0.7286→0.7224, `mu_p` 0.7589→0.7694,
`tau_n` 0.7333→0.7159, `tau_p` 0.7419→0.7200, `Nc` 0.6754→0.6195, `Nv` 0.6572→0.5804,
`tau_ETL` 0.2578→0.2859, `tau_HTL` 0.4191→0.3559, `rad_c` 0.2320→0.2704. Six of nine are lower in
the expanded arm; the two that improve most (`rad_c`, `tau_ETL`) are the weakest-recovered
quantities in both arms.

`MAE_reduction` is near zero for the ratio coordinates in both arms (r_mu 0.063→0.021, r_tau
0.019→0.020, r_D −0.009→−0.005), i.e. the models barely beat a constant equal to the training
median on the ratios, whereas they clearly beat it on the shared scales (0.46–0.59).

Per-seed spread (Skill, coordinates): the SD is 0.5–4 % of the mean for the shared scales but
8–27 % for the ratio coordinates, whose Skill sits near zero. The arms' five-seed ranges are
disjoint for `a_mu`, `a_tau`, `a_D` and `r_D`; they overlap for `r_mu` (0.125–0.156 vs
0.126–0.152) and for `r_tau`, where the expanded arm's spread reaches down to 0.070, close to the
original arm's mean of 0.073.

## 3. Table B — same test set, both models, common baseline

Both models are scored on the same rows with the *test arm's* training mean/median baselines, so
the baseline MSE is identical for the two models within a column. The model's own input and
output scalers are used in every cell (v2 rule). All values below differ from v1; the diagonal
columns (each model on its own test) are unchanged by construction.

### 3.1 Common original-range test (3,641 old-batch rows)

| coord | baseline MSE | Skill orig | Skill exp | RMSE orig | RMSE exp | MAE orig | MAE exp |
|---|---|---|---|---|---|---|---|
| a_mu | 0.7683 | 0.7641 ± 0.0070 | 0.6495 ± 0.0057 | 0.4257 | 0.5189 | 0.3182 | 0.3911 |
| r_mu | 0.1037 | 0.1410 ± 0.0114 | −1.6428 ± 0.0341 | 0.2985 | 0.5235 | 0.2346 | 0.4156 |
| a_tau | 4.1678 | 0.7417 ± 0.0034 | 0.6727 ± 0.0054 | 1.0376 | 1.1679 | 0.7690 | 0.9006 |
| r_tau | 0.1015 | 0.0729 ± 0.0116 | −1.9763 ± 0.0913 | 0.3068 | 0.5496 | 0.2415 | 0.4341 |
| a_D | 0.4647 | 0.7027 ± 0.0290 | 0.5760 ± 0.0132 | 0.3714 | 0.4439 | 0.2828 | 0.3484 |
| r_D | 0.1091 | 0.0491 ± 0.0097 | −2.4308 ± 0.1477 | 0.3221 | 0.6118 | 0.2576 | 0.5127 |

### 3.2 Common expanded-range test (3,641 expanded-batch rows)

| coord | baseline MSE | Skill orig | Skill exp | RMSE orig | RMSE exp | MAE orig | MAE exp |
|---|---|---|---|---|---|---|---|
| a_mu | 0.7572 | 0.6380 ± 0.0086 | 0.7796 ± 0.0061 | 0.5235 | 0.4085 | 0.4102 | 0.3089 |
| r_mu | 0.1677 | −1.1121 ± 0.0353 | 0.1409 ± 0.0102 | 0.5951 | 0.3796 | 0.5265 | 0.2893 |
| a_tau | 4.1585 | 0.6672 ± 0.0076 | 0.7238 ± 0.0034 | 1.1764 | 1.0716 | 0.8664 | 0.7857 |
| r_tau | 0.1660 | −1.2020 ± 0.0673 | 0.1262 ± 0.0343 | 0.6045 | 0.3808 | 0.5305 | 0.2872 |
| a_D | 0.4299 | 0.4466 ± 0.0436 | 0.6539 ± 0.0107 | 0.4874 | 0.3857 | 0.3721 | 0.2974 |
| r_D | 0.1799 | −1.5619 ± 0.0753 | 0.0888 ± 0.0037 | 0.6789 | 0.4049 | 0.6186 | 0.3013 |

### 3.3 Paired per-seed differences

`expanded − original`, same rows, same seed (`out/metrics/paired_differences.csv`,
`paired_difference_summary.csv`). ΔSkill_MSE, mean ± SD over seeds, positive seeds out of five:

| coord | ΔSkill on original test | pos/5 | ΔSkill on expanded test | pos/5 |
|---|---|---|---|---|
| a_mu | −0.115 ± 0.011 | 0 | +0.142 ± 0.011 | 5 |
| r_mu | −1.784 ± 0.041 | 0 | +1.253 ± 0.045 | 5 |
| a_tau | −0.069 ± 0.007 | 0 | +0.057 ± 0.005 | 5 |
| r_tau | −2.049 ± 0.091 | 0 | +1.328 ± 0.071 | 5 |
| a_D | −0.127 ± 0.025 | 0 | +0.207 ± 0.041 | 5 |
| r_D | −2.480 ± 0.143 | 0 | +1.651 ± 0.076 | 5 |

Every coordinate has the same sign in all five seeds. The v1 report described a large `r_tau` SD
on the original test driven by one seed (ΔSkill −5.24); after the fix the SD is 0.091 and the
per-seed differences are −1.93 to −2.16, so that outlier was an artefact of the scaler error.

### 3.4 How to read the cross-arm columns

The corrected numbers separate two situations that v1 merged:

- **Shared scales (`a_mu`, `a_tau`, `a_D`).** The `g` prior is the same in both arms, so these
  targets are drawn from the same distribution and lie inside both training supports. Both models
  keep a large positive Skill on the other arm's test set: expanded-on-original 0.576–0.673,
  original-on-expanded 0.447–0.667, i.e. 68–92 % of each model's own-distribution Skill. A
  sizeable drop, but not a collapse, and no support violation is involved.
- **Ratio coordinates (`r_mu`, `r_tau`, `r_D`).** Every cross-arm cell is far below the
  constant-predictor baseline (−1.11 to −2.43). The two directions are not symmetric in *why*:
  when the original-range model is evaluated on the expanded test, 75.3–76.1 % of its ratio
  targets lie outside its training support (0.2–5); when the expanded-range model is evaluated on
  the original test, all ratio targets lie inside its support (0.05–20) but only ≈24 % of its
  training rows do. Since Skill is grossly negative in both, leaving the support is not necessary
  for the failure — low training density in a sub-window is sufficient.

For that reason the blanket label "both cross-evaluations are out of distribution" is not used
here. "The test distribution differs" and "the target lies outside the training prior support"
are different statements, and only the second is true of the original-model-on-expanded-test case.
Neither column is a like-for-like estimate of "recovery got better/worse": the rows and the
baselines differ from each model's own test.

## 4. Why the ratio Skill moves: baseline variance, not error

`Skill_MSE = 1 − MSE_model / MSE_trainmean`. Between the two test sets (Table A, own
distribution of each arm):

| coord | baseline MSE old → new | factor | RMSE old → new | factor |
|---|---|---|---|---|
| r_mu | 0.1037 → 0.1677 | 1.62 | 0.2985 → 0.3796 | 1.27 |
| r_tau | 0.1015 → 0.1660 | 1.64 | 0.3068 → 0.3808 | 1.24 |
| r_D | 0.1091 → 0.1799 | 1.65 | 0.3221 → 0.4049 | 1.26 |
| a_mu | 0.7683 → 0.7572 | 0.99 | 0.4257 → 0.4085 | 0.96 |
| a_tau | 4.1678 → 4.1585 | 1.00 | 1.0376 → 1.0716 | 1.03 |
| a_D | 0.4647 → 0.4299 | 0.92 | 0.3714 → 0.3857 | 1.04 |

For the ratio coordinates the baseline MSE grew 1.62–1.65× and the model MSE grew 1.24–1.27×
(RMSE) squared, i.e. 1.54–1.61×. `r_mu` Skill is therefore unchanged; for `r_tau` and `r_D` the
denominator grew slightly faster than the numerator, raising Skill even though the absolute error
rose. The absolute error did not decrease anywhere for the ratios. For the shared scales the
denominator barely moved (factor 0.92–1.00), so their Skill differences (+0.016 `a_mu`, −0.018
`a_tau`, −0.049 `a_D`) are genuine small changes in error.

**Is the shared-scale/ratio gap closing?** Computing the gap within each family directly from
Table A (a Skill − r Skill, same arm):

| family | gap, original arm | gap, expanded arm | change |
|---|---|---|---|
| mobility | 0.623 | 0.639 | +0.016 (slightly wider) |
| lifetime | 0.669 | 0.598 | −0.071 (narrower) |
| DOS | 0.654 | 0.565 | −0.089 (narrower) |

The gap remains large and obvious — 0.57–0.64 Skill units in every family, 17–55× the between-seed
SD of the gap — but it narrowed for lifetime and DOS. It did **not** narrow because ratio recovery
improved: the ratio Skill rose (0.073→0.126, 0.049→0.089) while the ratio RMSE also rose
(0.307→0.381, 0.322→0.405), and the shared-scale Skill fell (0.742→0.724, 0.703→0.654). The raw
RMSE difference between the mean `a` and mean `r` coordinates is not used as the primary evidence
here, because the six coordinates have very different natural spreads (the `a_tau` RMSE is ≈1
log10 in every arm, the ratios ≈0.3–0.4), so a difference of group means mixes the coordinates'
scales. Skill differences are the primary quantity; the RMSE figures are reported alongside them.

## 5. Auxiliary diagnostic — the overlap band

Post-hoc, from the same prediction files, no retraining (`scripts/10_slice_diagnostic.py`,
`out/metrics/diagnostic_overlap_slice*.csv`). On the common expanded test, restricted to rows
whose **matching parameter family's** `q` lies inside the old 0.2–5 window — i.e. the `r` of that
family, one family at a time — the two models are compared on identical rows. This is **not** the
set of rows with all three `q` inside the old box: that intersection contains only 1.4 % of the
expanded test (51 rows), too few to analyse. Actual n per subset: mobility 899, lifetime 871,
DOS 874 (of 3,641).

| coord | n | RMSE orig | RMSE exp | MAE orig | MAE exp |
|---|---|---|---|---|---|
| a_mu | 899 | 0.4451 ± 0.0027 | 0.4459 ± 0.0061 | 0.3438 | 0.3353 |
| a_tau | 871 | 1.0799 ± 0.0109 | 1.0741 ± 0.0091 | 0.7863 | 0.7965 |
| a_D | 874 | 0.4700 ± 0.0171 | 0.4105 ± 0.0043 | 0.3521 | 0.3211 |
| r_mu | 899 | 0.3162 ± 0.0018 | 0.5552 ± 0.0048 | 0.2496 | 0.4693 |
| r_tau | 871 | 0.3221 ± 0.0058 | 0.5478 ± 0.0110 | 0.2513 | 0.4564 |
| r_D | 874 | 0.3262 ± 0.0046 | 0.5907 ± 0.0021 | 0.2635 | 0.4953 |

Reading, family by family:

- **Shared scales.** The two models are tied on `a_mu` (0.4451 vs 0.4459) and `a_tau` (1.0799 vs
  1.0741); the expanded model is better on `a_D` (0.4105 vs 0.4700). The v1 statement that the
  expanded model is better on `a` inside the band is therefore **withdrawn** for two of the three
  scales; only the DOS family supports it.
- **Ratios.** The expanded model is worse on the same rows by 0.23–0.26 log10 in all three
  families. The ratio degradation is not confined to rows whose `r` lies outside the old window:
  it is present on identical rows whose `r` is inside it.

Two readings are consistent with this pattern and cannot be separated with these data: (i) 76 % of
the expanded model's training rows have `r` outside the old window, so its `r` function is fitted
mostly elsewhere; (ii) at fixed capacity and fixed data volume, a wider target support reduces the
resolution available inside any fixed sub-window. Both are descriptive statements about this
design. The slice conditions on `r` only; it is not a randomised control and it does not match the
joint law of the parameters. It is reported as a diagnostic and does not change §1–§4.

## 6. Seed consistency

- The five seeds are five training runs on one data set, not five independent simulation data
  sets. No significance test is added and none should be read into the ± values, which are
  sample SDs across initialisations.
- Sign agreement is 5/5 (or 0/5) for every coordinate in the paired table, so the directions in
  §2–§3 are not seed noise.
- Per-seed ranges (Skill, own test): a_mu 0.756–0.775 / 0.770–0.784; r_mu 0.125–0.156 /
  0.126–0.152; a_tau 0.739–0.747 / 0.719–0.727; r_tau 0.063–0.088 / 0.070–0.155; a_D 0.671–0.729 /
  0.642–0.668; r_D 0.037–0.064 / 0.083–0.093 (original / expanded).
- The largest between-seed spread is `r_tau` Skill in the expanded arm (SD 0.034, range
  0.070–0.155); the ratio/shared-scale gap (≈0.6 Skill) is still 17 times that SD.

## 7. Corrections relative to the v1 evaluation

All changes are produced by the scaler-ownership repair; no data, model, split, scaler, metric
definition or baseline was touched. Full table: `before_after_metrics.csv` (1,800 rows: 20
model/test/seed combinations × 15 quantities × 6 metrics) and `before_after_summary.csv`.

**Withdrawn (depended on the buggy cross-arm predictions):**

- "Both cross-evaluations are out of distribution, and five of six coordinates fall below the
  constant-predictor baseline in each direction." In v2 the shared-scale coordinates remain
  clearly positive in both directions (0.45–0.67); only the three ratio coordinates are negative.
- "The expanded model is better on the shared scales and worse on the ratios inside the old
  overlap band." After the fix the models are tied on `a_mu` and `a_tau`; only `a_D` favours the
  expanded model.
- "The mechanism is a fixed individual-parameter bound: a ratio near 20 forces `mu_n` and `mu_p`
  to opposite ends of the shared log range." There are no fixed per-parameter bounds in the
  sampling rule; the shared scale `g` is fixed and `p_n = g√q`, `p_p = g/√q`. See `data_QA.md`
  §7.3.
- The magnitudes of all 15 cross-arm cells, and the v1 claim of one `r_tau` seed driving an SD of
  1.93.

**Retained (recomputed and unchanged, or strengthened):**

- Table A in full, and with it the conclusion that widening the linear-uniform ratio prior did not
  reduce ratio error in physical log10 units (RMSE rose 24–27 % against a 1.62–1.65× baseline
  growth).
- The decomposition that the ratio Skill increase is a baseline-variance effect and not an error
  reduction.
- The 5/5 sign consistency of the paired comparisons across training seeds.
- The equal-volume density caveat, now backed by the per-family slice: the expanded model is worse
  at `r` even on rows whose `r` is inside the old window.
- The scientific boundaries: five seeds are training replicates, not independent simulations; ± is
  an SD, not a confidence interval; a low Skill does not prove that the J–V curve carries no ratio
  information.

## 8. What this does not show

- It does not show that the J–V curve contains no ratio information, and it does not show
  universal non-identifiability. It shows that under this data volume, this sampling distribution,
  these filter rules, this architecture and these training rules, widening the linear-uniform
  ratio prior produced no reduction of ratio error.
- It does not isolate the ratio range as the only changed factor: each arm has its own scalers
  (per-parameter log10 spans 3.00–7.65 vs 3.00–7.97 decades across the nine parameters), so the
  effective normalisation and the relative weight of the nine NLL terms differ. The comparison is
  of the re-specified training distribution as a whole.
- It does not separate "different test distribution" from "outside training support" in the
  cross-arm cells beyond the per-coordinate statement in §3.4; the two directions confound support
  and density.
- It says nothing about the frozen main model's numbers. That model used full-retention scalers
  and a different split; no difference against its published metrics is attributable to the ratio
  range.
- No nearest-neighbour confidence interval and no bootstrap were run, per the scope of this round;
  the wider prior is not a resolution of the old-distribution NN CI question.

## 9. Limitations and unfinished items

1. **Sample counts must be kept apart**: 50,000 planned Latin-hypercube samples, 49,999 readable
   MAT files, 24,274 rows in the delivered post-filter CSV. One MAT file is missing and its
   Sample_ID cannot be recovered from the delivered files; the other 25,725 absent samples have no
   recorded reason (`data_QA.md` §6). No sample was invented or re-run.
2. **The pre-filter data do not exist locally**, so the retention of the new prior cannot be
   decomposed by ratio bin; only the coarse 48.5 % (expanded) and 51.0 % (original) retention is
   known. All distributions in this report are post-filter.
3. **The equal-volume design dilutes any fixed sub-region.** With 24,274 rows spread over four
   times the `q` width, only ~24 % of the expanded rows have a given ratio inside 0.2–5 (≈4,100 of
   the 16,992 training rows, against 16,992 in the original arm), and only 1.5 % have all three
   ratios inside the old cube. Part of the cross-arm and in-band degradation is this density
   dilution, which is intrinsic to an equal-volume comparison and cannot be separated from the
   prior width without a further experiment (not run here).
4. **Early stopping interacted with the prior.** The original arm trained 401–585 epochs, the
   expanded arm 317–503; both stopped by the same rule on the same monitor, but the two arms did
   not stop at the same point, so the number of gradient steps is not matched.
5. The overlap-band diagnostic (§5) is post-hoc, matched only on the matching ratio, and not a
   randomised control.
6. Not done, by instruction: manuscript/SI edits, COMSOL runs, retraining, hyperparameter search,
   AE/MLP baselines, learning curves over data volume, NN confidence intervals, bootstrap.

## 10. Where each claim lives

| claim | file |
|---|---|
| data acceptance, units, distributions, sample counts | `data_QA.md`, `out/qa/*` |
| architecture equivalence, design freeze, evaluation/scaler rule | `EXPERIMENT_DESIGN.md`, `config/experiment_config.json` |
| root cause, blast radius, fix | `PATCH_NOTES.md` |
| Table A / Table B / paired / mean±SD | `out/metrics/table_A_own_distribution.csv`, `table_B_common_tests.csv`, `paired_differences.csv`, `paired_difference_summary.csv`, `summary_mean_sd.csv` |
| v1 → v2 per-cell changes | `out/metrics/before_after_metrics.csv`, `before_after_summary.csv` |
| per-sample truth and prediction | `out/predictions/pred_<model>_<seed>__on_<test>.csv` (20 files) |
| which model, scaler, split and truth each prediction used | `out/metrics/inference_provenance.csv` (20 rows) |
| baseline-variance decomposition | §4 here; `table_B_common_tests.csv` columns `sse_train_mean`, `n` |
| overlap-band diagnostic | `out/metrics/diagnostic_overlap_slice.csv` |
| figures | `figures/fig02_skill_and_error.*`, `figures/fig03_common_test_paired.*`, `figures/figure_values.csv` |
| run provenance | `logs/<arm>_<seed>/run.json`, `logs/formal_run_status.json` |
| independent recomputation (3 scripts) | `out/qa/verification.json`, `out/qa/inference_validation.json`, `out/qa/fault_injection_log.json` |
