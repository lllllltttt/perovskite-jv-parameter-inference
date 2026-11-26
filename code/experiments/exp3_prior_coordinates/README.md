# EXPERIMENT 3 — Prior-Coordinate Recoverability Decomposition

**Status:** COMPLETE · **Verdict:** **A — SHARED-SCALE RECOVERY DOMINATES**

Reviewer-driven, **analysis-only** experiment on the frozen Stage-I VAE-v6
manuscript. Nothing was retrained; no COMSOL run; no frozen manuscript or figure
modified. All predictions are precomputed (frozen VAE-v6 test predictions, plus
the five-seed × three-architecture EXP1 checkpoints read from disk).

## Question

How much of the six paired bulk parameters' high apparent recoverability
(mu_n 0.906, mu_p 0.919, tau_n 0.878, tau_p 0.881, Nc 0.909, Nv 0.896) is
recovery of the **shared average scale** (a_mu, a_tau, a_D) versus the
**electron–hole asymmetry ratio** (r_mu, r_tau, r_D)? And how much better is the
model than a no-J–V, prior-only point predictor in these natural prior
coordinates?

## Answer

- Shared scales recover very well: Pearson **0.88–0.93**, Skill_RMSE over a
  prior-only predictor **0.78–0.86**.
- Asymmetry ratios recover weakly but genuinely: Pearson **0.27–0.43**,
  Skill_RMSE **0.07–0.18**, median ratio error ~1.6×, still **29–111 SD above a
  shuffled-null**.
- The marginal pair correlations (0.94/0.99/0.90) are reproduced by the retained
  prior's geometry alone (SD(a)/SD(0.5r) = 4–13, r(a,r)≈0): shared-scale
  dominance is a property of the effective retained prior.
- The hierarchy is architecture-stable (VAE/det-AE/MLP, 5 seeds each) and the
  frozen model sits within ~1 SD of the 5-seed VAE means.

## Directory

```
EXP3_FINAL_REPORT.md         15-section report + EXPERIMENT 3 VERDICT + 5 gates
EXP3_REVIEWER_QUESTIONS.md   Q1–Q10 answers for the reviewer
EXP3_MANUSCRIPT_IMPACT.md    10-item advisory impact record
EXP3_QC.md                   programmatic QC (12/12 PASS)
FROZEN_PREDICTION_REPRODUCTION_CHECK.md   Phase 0 gate (exact reproduction)
scripts/exp3_lib.py          shared library (coordinate transforms, scalers)
scripts/phase0_repro.py      Phase 0 reproduction check
scripts/prior_geometry.py    prior geometry + variance geometry (§7–8)
scripts/recoverability.py    recoverability + paired comparison + prior baseline (§4–6,9–10)
scripts/sensitivity.py       coordinate sensitivity to J(V) (§12)
scripts/shuffled.py          shuffled-pairing null control (§11)
scripts/multiseed.py         EXP1 5-seed + architecture robustness (§13–14)
scripts/figures.py           EXP3_FigA–F (§17)
scripts/qc.py                §19 QC (12 assertions)
results/*.csv               all numeric outputs
figures/EXP3_FigA–F.png/.pdf   figures (600 dpi PNG + vector PDF)
```

## Gate summary (§25)

| Gate | Answer |
|---|---|
| ORIGINAL RECOVERABILITY HIERARCHY SURVIVES | **YES** |
| HIGH BULK RECOVERABILITY IS PARTLY PRIOR-ASSISTED | **YES** |
| J–V ADDS SAMPLE-SPECIFIC INFORMATION BEYOND THE PRIOR | **YES** |
| CURRENT CORE SCIENTIFIC FRAMEWORK SURVIVES | **YES** |
| NEW TRAINING REQUIRED | **NO** |

Per the experiment specification, **Experiment 3 is the final experiment of this
series. Experiment 4 is not started.**
