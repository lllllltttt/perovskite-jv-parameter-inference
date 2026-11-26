# EXPERIMENT 4 — Collision-Metric Robustness

**Status:** COMPLETE · **Verdict:** **B — CORE AMBIGUITY ROBUST; DETAILS METRIC-DEPENDENT**

Reviewer-driven, **analysis-only** experiment on the frozen Stage-I VAE-v6
manuscript. No model was retrained, no COMSOL run, no frozen manuscript or figure
modified, no sensitivity/uncertainty output recomputed, no new simulation
samples. Only the frozen dataset and frozen collision outputs are read.

## Question

Is the empirical one-to-many inverse ambiguity in the original nearest-neighbor
collision analysis (near-identical J–V curves ↔ very different parameter vectors)
robust to reasonable alternative definitions of J–V similarity — or primarily an
artifact of the per-column normalized J–V distance?

## Answer

- The ambiguity is **robust**: under all five J–V distance definitions
  (normalized full curve, physical full curve, physical/Jsc-relative full curve,
  physical 0–1.0 V window, 0–1.0 V/Jsc-relative), nearest-neighbor pairs have
  median parameter distance **0.200–0.216 vs 0.349 for random parameter pairs**;
  closest-1% medians are 0.144–0.182. It is **not** a normalization artifact
  (raw physical metrics show it with no normalization at all).
- The **details are metric-dependent**: normalized and physical full-curve NN
  identities agree on only ~10 % of samples (closest-1% Jaccard 0.013); the
  physical full-curve and 0–1.0 V closest-1% sets are disjoint. The dominant
  ambiguous parameters (τ_ETL, r_rad, τ_HTL) are stable across metrics, but exact
  ranks are not.
- Both frozen representative collisions stay bottom-1% under M1 and bottom-2–5 %
  under the 0–1.0 V window; a new predeclared cross-metric pair (1457,1948) is
  bottom-1% under M1/M4/M5 simultaneously.
- QC **17/17 PASS** (70/70 lines). Manuscript impact is **wording-only**.

## Directory

```
EXP4_FINAL_REPORT.md             16 sections + EXPERIMENT 4 VERDICT + 6 gates
EXP4_REVIEWER_QUESTIONS.md       Q1–Q10 answers for the reviewer
EXP4_MANUSCRIPT_IMPACT.md        10-item advisory impact record
EXP4_QC.md                       programmatic QC (PASS)
ORIGINAL_COLLISION_REPRODUCTION_CHECK.md   Phase 0 gate (15/15 PASS)
scripts/exp4_lib.py              shared library (distances, dedup, baselines)
scripts/phase0.py                Phase 0 exact M1 reproduction
scripts/metrics.py               M1–M6 computation + all result CSVs (§4–14)
scripts/figures.py               EXP4_FigA–F (§22)
scripts/qc.py                    §24 QC (17 assertions)
results/*.csv                    all numeric outputs (incl. directed_nn_M*.csv)
figures/EXP4_FigA–F.png/.pdf     figures (600 dpi PNG + vector PDF)
```

## Key numbers (frozen VAE-v6, N = 15307)

- Random-pair baseline median dΘ = 0.3490 (seed 42, frozen; seed 20260827
  set = 0.3489).
- NN-pair median dΘ by metric: M1 0.1999 · M2 0.2165 · M3 0.2164 · M4 0.2072 ·
  M5 0.2073 (R_NN 0.57–0.62).
- Closest-1% median dΘ: M1 0.1443 · M2 0.1816 · M3 0.1679 · M4 0.1520 ·
  M5 0.1520 (R_1pct 0.41–0.52).
- Spearman(dJ,dΘ): M1 0.1576 · M2 0.0843 · M3 0.0977 · M4 0.1477 · M5 0.1830.
- Closest-1% set overlap: M1↔M2 0.013, M2↔M4 0.000, M4↔M5 1.000.
- M6 (shape, supplementary): Spearman 0.1070, closest-1% 0.1686.

## Gate summary

| Gate | Answer |
|---|---|
| ORIGINAL COLLISION CONCLUSION SURVIVES | **YES** |
| PHYSICAL-SPACE COLLISIONS EXIST | **YES** |
| PARAMETER-LEVEL AMBIGUITY HIERARCHY IS ROBUST | **YES (qualified)** |
| REPRESENTATIVE COLLISIONS REMAIN DEFENSIBLE | **YES (qualified)** |
| CORE SCIENTIFIC FRAMEWORK SURVIVES | **YES** |
| NEW TRAINING REQUIRED | **NO** |
| NEW COMSOL RUNS REQUIRED | **NO** |

Per the experiment specification, **Experiment 4 is the final planned reviewer
experiment — no Experiment 5 is started.** The next phase is manuscript
integration and final technical/editorial QC.
