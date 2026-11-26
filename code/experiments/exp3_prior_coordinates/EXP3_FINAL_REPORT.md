# EXPERIMENT 3 FINAL REPORT
## Prior-Coordinate Recoverability Decomposition of the Six Paired Bulk Parameters

**Date:** 2026-08-25 · **Experiment dir:** `reviewer_experiments/exp3_prior_coordinate_recoverability/`
**Status:** COMPLETE · **Verdict:** **A — SHARED-SCALE RECOVERY DOMINATES**

---

## 1. Reviewer question addressed

Two interlocking questions from the reviewer on the frozen Stage-I manuscript
(VAE-v6, `manuscript_stage1_submission_clean.md`):

1. How much of the six paired bulk parameters' high apparent recoverability
   (mu_n 0.906, mu_p 0.919, tau_n 0.878, tau_p 0.881, Nc 0.909, Nv 0.896)
   corresponds to recovering the **shared average scale** (a_mu, a_tau, a_D)
   versus the **electron–hole asymmetry ratio** (r_mu, r_tau, r_D)?
2. How much better does the trained model perform than a **no-J–V, prior-only
   point predictor** in these natural prior coordinates?

The answer is quantified in log10-physical space throughout (decades), as
specified. Terminology follows the constraint set: we report *recoverability
under the effective retained simulation prior*, never "identifiability".

## 2. Scope, constraints, analysis-only guarantee

Analysis-only. **Nothing in this experiment trains, reruns COMSOL, modifies the
frozen manuscript or its figures, reruns the noise/collision analyses, or
introduces an independent-parameter synthetic prior.** No new COMSOL samples
were generated. The five multi-seed checkpoints and the det-AE/MLP baselines are
the precomputed, frozen outputs of Experiment 1 — read, never retrained.

## 3. Method, data, Phase-0 reproducibility

**Prior coordinates** (exact log10 identities). For each paired parameter
(mu_n/mu_p, tau_n/tau_p, Nc/Nv):

- shared scale  a = 0.5·(log10 p_n + log10 p_p)
- asymmetry ratio  r = log10 p_n − log10 p_p

**Data.** Frozen normalized dataset `data/dataset_normalized.npz` (N=102046;
train 71432 / val 15307 / test 15307). Frozen full-data scaler
(`data/param_scaler.pkl`) inverts normalized → log10 physical exactly
(Phase 0 verified to **3.6e-15**). Predictions are the frozen VAE-v6 test
predictions; multi-seed/architecture predictions come from EXP1
`eval_bundle.npz` (train-only normalized space, inverted by each run's own
train-only scaler).

**Phase 0 gate (must reproduce, STOP otherwise):** marginal frozen Pearson =
mu_n 0.906, mu_p 0.919, tau_n 0.878, tau_p 0.881, Nc 0.909, Nv 0.896 on
N=15307 — reproduced exactly (worst deviation 0.0004; see
`FROZEN_PREDICTION_REPRODUCTION_CHECK.md`). Inverse log10 reconstruction exact.
**Gate PASSED; experiment proceeded.**

## 4. Effective retained prior geometry

Test-population (N=15307) log10-physical coordinate spreads (`decades`):

| coordinate | SD | min | max |
|---|---|---|---|
| a_mu | 0.871 | −1.09 | +2.30 |
| r_mu | 0.162 | −0.64 | +0.57 |
| a_tau | 2.049 | −1.93 | +5.12 |
| r_tau | 0.162 | −0.61 | +0.57 |
| a_D | 0.682 | −0.95 | +1.85 |
| r_D | 0.160 | −0.57 | +0.58 |

The retained simulation prior is therefore dominated by **shared-scale
variation**: SD(a)/SD(0.5r) = 5.4 (mobility), **12.7** (lifetime), 4.3 (DOS).

## 5. Variance (pair) geometry — shared-scale dominance

For all three pairs, variance of the shared scale exceeds variance of the half
ratio by 18–162× (lifetime largest), and the a–r covariance is negligible:

| pair | Var(a) | Var(0.5r) | ratio | r(a, r) |
|---|---|---|---|---|
| mobility | 0.758 | 0.026 | 29.0 | −0.003 |
| lifetime | 4.197 | 0.026 | 162.3 | +0.004 |
| DOS | 0.465 | 0.026 | 17.9 | +0.008 |

The marginal electron–hole pair correlations (0.94 / 0.99 / 0.90 in the
manuscript) are **reproduced by pure algebra** of this geometry:
corr(n,p) = (1 − k²)/(1 + k²), k = SD(0.5r)/SD(a), giving
0.933 / 0.988 / 0.896 — within 0.007 of the manuscript values. **Filtering
induces essentially zero a–r dependence** (all |r(a,r)| < 0.02), so the 
geometric dominance is a property of the retained prior itself, not an artefact
of the filtering step.

## 6. Frozen-model recoverability in the six coordinates

Pearson / Spearman, MAE & RMSE in decades, and the ratio error factor, frozen
VAE-v6, N=15307:

| coordinate | Pearson | Spearman | MAE (dec) | RMSE (dec) | med \|log err\| | 10^med |
|---|---|---|---|---|---|---|
| a_mu | **0.9250** | 0.9254 | 0.241 | 0.331 | 0.183 | — |
| r_mu | 0.4289 | 0.3837 | 0.230 | 0.292 | 0.196 | **1.571** |
| a_tau | **0.8819** | 0.8767 | 0.688 | 0.967 | 0.433 | — |
| r_tau | 0.3517 | 0.2980 | 0.243 | 0.305 | 0.208 | **1.614** |
| a_D | **0.9248** | 0.9272 | 0.194 | 0.260 | 0.148 | — |
| r_D | 0.2663 | 0.2169 | 0.245 | 0.308 | 0.214 | **1.637** |

**Shared scales recover very well (r ≈ 0.88–0.93); asymmetry ratios recover
weakly (r ≈ 0.27–0.43), and their median error is a constant ~1.6×** — i.e. the
model has essentially a scale-level handle on the ratio, not a fine one.

## 7. Paired-coordinate comparison (marginal vs shared-scale vs ratio)

| pair | marg r(n) | marg r(p) | shared a r | ratio r r |
|---|---|---|---|---|
| mobility | 0.906 | 0.919 | **0.925** | 0.429 |
| lifetime | 0.878 | 0.881 | **0.882** | 0.352 |
| DOS | 0.909 | 0.896 | **0.925** | 0.266 |

**The high marginal Pearson values are dominated by shared-scale recovery.**
For lifetime, marginal ≈ shared-scale exactly (0.878/0.881 vs 0.882); for
mobility and DOS the shared scale actually recovers slightly *better* than
either marginal. The asymmetry ratio adds an independent but much weaker channel
(r ≤ 0.43, MAE ≈ 0.23–0.25 decades regardless of family).

## 8. Information beyond a prior-only point predictor

Baseline = predicting each coordinate by its **training-only** mean / median
(no val/test targets, no J-V inputs — built purely from the retained prior).
Skill_RMSE = 1 − MSE_model / MSE_prior·mean; MAE-reduction likewise vs the
prior median:

| coordinate | model RMSE | prior-mean RMSE | **Skill_RMSE** | **MAE-reduction** |
|---|---|---|---|---|
| a_mu | 0.331 | 0.871 | **0.856** | 0.681 |
| r_mu | 0.292 | 0.323 | 0.184 | 0.084 |
| a_tau | 0.967 | 2.049 | **0.777** | 0.613 |
| r_tau | 0.305 | 0.323 | 0.110 | 0.027 |
| a_D | 0.260 | 0.682 | **0.855** | 0.663 |
| r_D | 0.308 | 0.320 | 0.070 | 0.008 |

For the three shared scales the J–V observable adds **0.78–0.86 of predictive
skill** over a prior-only point prediction. For the ratios the added skill is
**small but nonzero** (0.07–0.18); the retained prior alone already predicts the
ratio to ±0.32 decades, and J–V improves this only mildly.

## 9. Coordinate sensitivity to the J–V observable

S_i = mean over 131 voltages of |Pearson(coordinate_i, J(V))| on physical
J_test_raw (true coordinates):

| coordinate | S_i | recoverability r |
|---|---|---|
| a_mu | 0.378 | 0.925 |
| r_mu | 0.037 | 0.429 |
| a_tau | 0.500 | 0.882 |
| r_tau | 0.024 | 0.352 |
| a_D | 0.113 | 0.925 |
| r_D | 0.022 | 0.266 |

Sensitivity tracks recoverability: shared scales are 3–23× more J-V-sensitive
than their ratios. **a_D is the mild exception** (S = 0.113, the lowest shared
scale) yet still recovers at r = 0.925 — consistent with the same conclusion
(shared scale dominates) but flagged: its high recoverability is achieved with
lower per-voltage sensitivity.

## 10. Shuffled pairing control

True and predicted test samples re-paired at random (seed 20260826, 100 perms);
null distribution of Pearson r per coordinate: mean ≈ 0, SD ≈ 0.008, p95 ≈ 0.014.

Observed recoverability sits **29–111 SD above the null** for all six
coordinates (smallest: r_D at 29 SD). The recovered association is therefore a
genuine *sample-wise* signal — not a prior-marginal artefact. This does **not**
qualify the prior-assisted nature of the shared-scale channel; it shows the
model's predictions carry real per-sample information even where weak.

## 11. Multi-seed robustness (EXP1 VAE, 5 seeds)

Frozen-model coordinate Pearson vs the five independent EXP1 VAE seeds
(mean ± SD; predictions inverted through each run's own train-only scaler —
cross-check vs EXP1 `per_seed_metrics.csv`: max deviation **4.9e-07**):

| coordinate | frozen | 5-seed VAE mean ± SD |
|---|---|---|
| a_mu | 0.925 | 0.913 ± 0.009 |
| r_mu | 0.429 | 0.427 ± 0.012 |
| a_tau | 0.882 | 0.874 ± 0.007 |
| r_tau | 0.352 | 0.346 ± 0.009 |
| a_D | 0.925 | 0.914 ± 0.007 |
| r_D | 0.266 | 0.285 ± 0.014 |

The frozen model sits within ~1 SD of the 5-seed means for every coordinate.
**The shared-scale-vs-ratio conclusion survives seed variation** — the gap is
0.6+ Pearson in every seed.

## 12. Architecture stability (VAE / det-AE / MLP)

Mean ± SD Pearson over 5 seeds each:

| coordinate | VAE | det-AE | MLP |
|---|---|---|---|
| a_mu | 0.913 ± 0.009 | 0.926 ± 0.006 | 0.907 ± 0.010 |
| r_mu | 0.427 ± 0.012 | 0.443 ± 0.016 | 0.406 ± 0.003 |
| a_tau | 0.874 ± 0.007 | 0.886 ± 0.004 | 0.872 ± 0.006 |
| r_tau | 0.346 ± 0.009 | 0.346 ± 0.014 | 0.344 ± 0.006 |
| a_D | 0.914 ± 0.007 | 0.927 ± 0.005 | 0.912 ± 0.007 |
| r_D | 0.285 ± 0.014 | 0.300 ± 0.024 | 0.242 ± 0.016 |

**Architecture-stable.** Every family shows the same scientific pattern:
shared scales 0.87–0.93, ratios 0.24–0.44; min shared-vs-ratio gap = 0.44
(det-AE). The coordinate-level recoverability hierarchy is not a VAE artefact.

## 13. Outcome selection

**Outcome A — SHARED-SCALE RECOVERY DOMINATES.**

- The high apparent recoverability of the six paired bulk parameters is, in the
  natural prior coordinates, **mostly recovery of the shared average scale**
  (a: r 0.88–0.93, skill 0.78–0.86).
- The electron–hole asymmetry ratio recovers weakly (r 0.27–0.43, skill
  0.07–0.18) but **genuinely** (29+ SD above shuffled null) — it carries
  sample-specific information beyond the prior, just not the dominant share.
- This pattern is explained by the retained prior geometry (shared-scale
  variance 18–162× the half-ratio variance) and is stable across seeds and
  architectures.

Options B (both comparable), C (mixed by family) and D (prior structure needs a
major reframing of the model) are **not** selected: the shared-vs-ratio
imbalance is universal across all three families, and the prior geometry already
explains the manuscript's marginal correlations without invalidating the model's
per-sample predictive association.

## 14. Manuscript impact summary

The core scientific claims survive, but **terminology and interpretive wording
must change** (full 10-item list in `EXP3_MANUSCRIPT_IMPACT.md`). In brief:
"high recoverability of bulk parameters" must be reported as shared-scale
recoverability under the effective retained prior; the asymmetry ratio is a
weak-but-real secondary channel; and high marginal Pearson must not be phrased
as parameter-wise identification.

## 15. Limitations

- Log10-physical coordinates inherit the log-transformed target space of the
  frozen training pipeline; metrics are decade-based, not linear.
- The prior-only baseline is intentionally crude (single point predictor). It
  answers the reviewer's question ("better than a no-J-V predictor") but is not
  a full generative prior.
- Sensitivity S_i is descriptive (6 points); no significance claim is made.
- Results describe the effective retained simulation prior — nothing here
  probes prior-independent identifiability (explicitly out of scope).

---

## EXPERIMENT 3 VERDICT

**Outcome A — SHARED-SCALE RECOVERY DOMINATES.**

| Gate | Question | Answer |
|---|---|---|
| G1 | ORIGINAL RECOVERABILITY HIERARCHY SURVIVES | **YES** |
| G2 | HIGH BULK RECOVERABILITY IS PARTLY PRIOR-ASSISTED | **YES** |
| G3 | J–V ADDS SAMPLE-SPECIFIC INFORMATION BEYOND THE PRIOR | **YES** |
| G4 | CURRENT CORE SCIENTIFIC FRAMEWORK SURVIVES | **YES** |
| G5 | NEW TRAINING REQUIRED | **NO** |

**One-line summary for the manuscript:** the trained model's high recoverability
of the six paired bulk parameters is predominantly shared-scale recovery
(a r ≈ 0.88–0.93; 0.78–0.86 skill over a prior-only predictor), with a
weak-but-real asymmetry-ratio channel (r ≈ 0.27–0.43; still 29+ SD above a
shuffled-null), explained by the retained simulation prior's shared-scale
dominance — all stable across seeds and architectures.
