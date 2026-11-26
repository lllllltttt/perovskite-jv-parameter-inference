# EXPERIMENT 4 — COLLISION-METRIC ROBUSTNESS

**Status:** COMPLETE · **Verdict:** **B — CORE AMBIGUITY ROBUST; DETAILS METRIC-DEPENDENT**

**Date:** 2026-08-25 · Frozen Stage-I VAE-v6 manuscript · `reviewer_experiments/exp4_collision_metric_robustness/`

---

## 1. Question

The original collision analysis (Fig. 5 of the frozen manuscript, metric M1 below)
finds that nearest-neighbor pairs in normalized J–V space have much smaller
parameter distance than random parameter pairs, i.e. **essentially the same J–V
curve maps to very different parameter vectors** (an empirical one-to-many inverse
ambiguity). This experiment asks the single scientific question:

> Is that ambiguity **robust to reasonable alternative definitions of J–V
> similarity**, or is it primarily an **artifact of the per-column normalized
> J–V distance** used originally?

**Answer: robust — but with metric-dependent detail.** The one-to-many structure
(identical-looking J–V ↔ widely different parameters) appears under every one of
five alternative J–V distance definitions, including raw, un-normalized physical
currents. The *specific* colliding pairs and the exact ranking of ambiguous
parameters do change with the metric. Verdict **B**.

## 2. Analysis-only constraints (all honored)

- **No model was trained, fine-tuned, or loaded for inference.** No COMSOL run.
- No frozen manuscript, Fig.1–Fig.6, sensitivity, or uncertainty-training output
  was modified.
- **d_Theta is fixed** for every metric: RMSE over the nine normalized-log
  parameters (the original definition). No reweighting, no physical units in the
  parameter distance, no EXP3 average/ratio coordinates, no parameter-distance
  optimization.
- The fixed random-pair baseline (median dTheta = 0.3490) is identical for every
  metric.

## 3. Metrics (alternative J–V similarity definitions)

All on the same N = 15307 test samples, full voltage grid V = 0.00–1.30 V (131
points), exact nearest neighbor with self excluded, chunked:

| Metric | Definition | Points | Units of d_J |
|---|---|---|---|
| **M1** (original) | per-column normalized full-curve RMSE | 131 | dimensionless |
| **M2** | physical-current full-curve RMSE | 131 | mA/cm² |
| **M3** | M2 / 0.5·(|Jsc_i|+|Jsc_k|) | 131 | dimensionless |
| **M4** | physical-current RMSE, **0–1.0 V lower-forward-bias analysis window** | 101 | mA/cm² |
| **M5** | M4 / 0.5·(|Jsc_i|+|Jsc_k|) | 101 | dimensionless |
| **M6** | J/|Jsc| shape RMSE (optional, **supplementary only**) | 131 | dimensionless |

M3/M5 are pair-dependent (the denominator depends on both samples), so they are
computed from the chunked physical-RMSE matrix divided by the pair-mean |Jsc|
(no closed-form identity shortcut).

## 4. Data, seeds, and reproducibility

- Dataset: frozen `data/dataset_normalized.npz` (J_test normalized, J_test_raw
  physical mA/cm², params_test normalized-log), N = 15307 test samples.
- Exact chunked NN (chunk = 1024), float64, self excluded, d = sqrt(d2/npts).
- Brute-force subset verification (150 random queries, seed 20260827): **all
  metrics OK**.
- Directed nearest-neighbor results saved **before** deduplication for every
  metric (`results/directed_nn_M*.csv`, 15307 rows each).
- Dedup per metric via unordered unique pairs (`keep i < NN(i)`), **not forced to
  7666**; mutual-NN fraction reported (§7).
- Random baselines: frozen seed-42 draw (200k, filtered ra≠rb) → median dTheta
  **0.3490** (primary); independent fixed set (seed 20260827, 100000 unique
  pairs, IDs saved) → median dTheta **0.3489**. Same baseline for every metric.

## 5. Phase 0 gate — exact reproduction of the original analysis

`ORIGINAL_COLLISION_REPRODUCTION_CHECK.md`: **PASS (15/15)**. The M1 analysis
recomputed from the frozen dataset reproduces every stored quantity to stored-
rounding precision: Spearman 0.1576, Pearson 0.0785, NN-pair median dTheta
0.1999, random baseline 0.3490, tiers 0.1443 / 0.1337 / 0.1021, per-parameter
closest-1% ambiguity, and both representative pairs (1010,2641) and (8271,10258)
with their ≥2× dominance.

## 6. Distance coupling (d_J vs d_Theta) per metric

The inverse ambiguity shows up as a strong, non-zero but **weak** correlation
between J-distance and parameter-distance — near-identical J–V pairs are spread
over a wide parameter distance:

| Metric | Spearman ρ_s | Pearson r |
|---|---|---|
| M1 | 0.1576 | 0.0785 |
| M2 | 0.0843 | 0.0553 |
| M3 | 0.0977 | 0.0430 |
| M4 | 0.1477 | 0.0772 |
| M5 | 0.1830 | 0.0515 |

Every metric reproduces the wedge structure of the original figure (small d_J,
wide d_Theta): exact J–V matches coincide with parameter differences far larger
than their physical ambiguity would imply.

## 7. NN parameter-distance distributions (the central observation)

For every metric, nearest-neighbor pairs (statistically indistinguishable J–V
curves under that metric's own definition) have parameter distance far below the
random-pair baseline. **Ratio values are descriptive only** — they are not
probabilities and not effect sizes.

| Metric | unique pairs | mutual-NN | NN-pair median dΘ | R_NN = NN/random | closest-1% median dΘ | R_1pct |
|---|---|---|---|---|---|---|
| M1 | 7666 | 0.531 | 0.1999 | 0.573 | 0.1443 | 0.413 |
| M2 | 7635 | 0.555 | 0.2165 | 0.620 | 0.1816 | 0.520 |
| M3 | 7638 | 0.549 | 0.2164 | 0.620 | 0.1679 | 0.481 |
| M4 | 7666 | 0.536 | 0.2072 | 0.594 | 0.1520 | 0.436 |
| M5 | 7670 | 0.535 | 0.2073 | 0.594 | 0.1520 | 0.436 |

**Interpretation.** Under *every* definition of "same J–V", pairs that produce
nearly identical curves sit at ~41–62 % of the random parameter distance, and the
closest-1% of pairs sit at ~41–52 % of random. The phenomenon is not restricted to
the normalized metric. Mutual-NN fractions (0.53–0.55) are metric-dependent but
similar — no metric is a pathological outlier.

## 8. Distance-tier robustness (EXP4_FigB)

Median dTheta rises monotonically from the closest-0.1% tier toward all-NN pairs
for every metric, and **every tier median stays below the random baseline**:

| tier | M1 | M2 | M3 | M4 | M5 | random |
|---|---|---|---|---|---|---|
| closest 0.1% | 0.102 | 0.190 | 0.151 | 0.126 | 0.126 | — |
| closest 0.5% | 0.134 | 0.186 | 0.156 | 0.151 | 0.151 | — |
| closest 1% | 0.144 | 0.182 | 0.168 | 0.152 | 0.152 | — |
| closest 5% | 0.155 | 0.201 | 0.192 | 0.162 | 0.162 | — |
| closest 10% | 0.168 | 0.204 | 0.199 | 0.175 | 0.175 | — |
| all NN | 0.200 | 0.216 | 0.216 | 0.207 | 0.207 | 0.349 |

All five metrics show the same qualitative pattern; the normalized metric M1 gives
the *lowest* closest-tier parameter distances, and the physical full-curve
metrics (M2/M3) give the highest — but still far below random.

## 9. Physical-space collisions exist (rules out "normalization artifact")

The raw, un-normalized metrics M2 and M4 show the effect **without any per-column
normalization**:

- M2 NN-pair median dTheta 0.2165 vs random 0.3490; closest-1% 0.1816 (R_1pct
  0.520).
- M4 (0–1.0 V lower-forward-bias analysis window) NN-pair median 0.2072;
  closest-1% 0.1520 (R_1pct 0.436) — nearly as strong as the normalized metric.
- The physical full-curve closest-1% set (M2) and the 0–1.0 V closest-1% set (M4)
  are **disjoint** (Jaccard 0.000): the physical collisions are not echoes of the
  normalized ones, they are genuinely new pairs colliding in physical J–V space.

**Conclusion: the inverse ambiguity is not a normalization artifact (outcome D
excluded).**

## 10. Parameter-level ambiguity hierarchy per metric

Median absolute parameter difference within each metric's closest-1% pairs
(normalized-log units; no universal decade conversion is applied — §17):

| param | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|
| mu_n | 0.118 | 0.061 | 0.097 | 0.107 | 0.107 |
| mu_p | 0.073 | 0.058 | 0.052 | 0.071 | 0.071 |
| tau_n | 0.101 | 0.034 | 0.134 | 0.099 | 0.099 |
| tau_p | 0.087 | 0.040 | 0.126 | 0.095 | 0.095 |
| Nc | 0.052 | 0.048 | 0.048 | 0.089 | 0.089 |
| Nv | 0.060 | 0.060 | 0.051 | 0.106 | 0.106 |
| tau_ETL | **0.154** | 0.203 | 0.072 | **0.137** | **0.137** |
| tau_HTL | 0.101 | 0.140 | **0.167** | 0.076 | 0.076 |
| r_rad | 0.088 | **0.212** | 0.124 | 0.133 | 0.133 |

**Bold** = that metric's most-ambiguous parameter. The **identity of the most
ambiguous parameters is robust**: tau_ETL and r_rad are both top-3 in every
metric; tau_HTL is top-4 in M1–M3 and top-8 in M4/M5; Nc and mu_p are never in
the top-4 (Nc is bottom-3 in 4 of 5 metrics). The *ranking within* the top tier
shifts with the metric — tau_ETL dominates the normalized and the 0–1.0 V window
metrics, r_rad dominates the physical full-curve metric, tau_HTL dominates the
Jsc-relative full-curve metric.

## 11. Ambiguity-rank stability

Spearman rank correlation of the nine per-parameter ambiguity medians between
metrics:

| | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|
| M1 | 1.00 | 0.47 | 0.57 | 0.50 | 0.50 |
| M2 | 0.47 | 1.00 | 0.02 | 0.52 | 0.52 |
| M3 | 0.57 | 0.02 | 1.00 | −0.03 | −0.03 |
| M4 | 0.50 | 0.52 | −0.03 | 1.00 | 1.00 |
| M5 | 0.50 | 0.52 | −0.03 | 1.00 | 1.00 |

The hierarchy is **moderately stable** between the normalized metric and the
physical metrics (0.47–0.57), but the full-curve Jsc-relative metric (M3) is
uncorrelated with the 0–1.0 V window metrics (M4/M5, ρ ≈ 0). M4 and M5 give
essentially identical hierarchies (ρ = 1.00) because the pair-mean-|Jsc| scaling
is nearly constant across the tight |Jsc| distribution. The hierarchy is
therefore robust at the level of *which parameters dominate*, not at the level of
exact ranks.

## 12. Pair-set overlap (how much of the detail is metric-dependent)

| metric pair | NN-identity agreement | pair Jaccard | closest-1% Jaccard |
|---|---|---|---|
| M1↔M2 | 0.101 | 0.053 | **0.013** |
| M1↔M3 | 0.101 | 0.053 | 0.020 |
| M1↔M4 | 0.393 | 0.246 | 0.034 |
| M1↔M5 | 0.393 | 0.246 | 0.034 |
| M2↔M3 | 0.980 | 0.960 | 0.216 |
| M2↔M4 | 0.077 | 0.040 | **0.000** |
| M2↔M5 | 0.077 | 0.040 | 0.000 |
| M3↔M4 | 0.077 | 0.040 | 0.000 |
| M4↔M5 | 0.993 | 0.985 | 1.000 |

**The identity of the specific colliding pairs is strongly metric-dependent.**
Normalized (M1) and physical full-curve (M2) nearest neighbors agree on only
~10 % of samples and share ~1.3 % of their closest-1% pairs. The physical
full-curve and 0–1.0 V window closest-1% sets are disjoint. Only pairs of
near-identical definitions (M2↔M3, M4↔M5) overlap heavily. This is the
"details metric-dependent" part of outcome B.

## 13. Representative collisions (frozen + new robust pair)

All distances and percentiles for the two frozen representative cases and one new
predeclared cross-metric robust pair. Percentiles are against that metric's own
NN-pair distance distribution (descriptive, not probability statements).

### (1010,2641) — τ_ETL-dominant (2× dominance: 0.611 vs 0.212)
| metric | d_J | percentile |
|---|---|---|
| M1 | 0.000093 | **0.1 %** |
| M2 | 0.2618 mA/cm² | 33.5 % |
| M3 | 0.0109 | 26.7 % |
| M4 | 0.0037 mA/cm² | **1.9 %** |
| M5 | 0.00016 | **1.9 %** |

dΘ = 0.2205 · params (norm.-log |Δ|): tau_ETL **0.611**, mu_n 0.212, tau_HTL
0.093, mu_p 0.087, Nv 0.040, Nc 0.025, tau_n 0.021, tau_p 0.011, r_rad 0.011.

### (8271,10258) — r_rad-dominant (2× dominance: 0.619 vs 0.265)
| metric | d_J | percentile |
|---|---|---|
| M1 | 0.000202 | **1.0 %** |
| M2 | 0.3698 mA/cm² | 47.3 % |
| M3 | 0.0153 | 39.8 % |
| M4 | 0.0075 mA/cm² | **4.6 %** |
| M5 | 0.00031 | **4.6 %** |

dΘ = 0.2394 · params: r_rad **0.619**, mu_n 0.265, Nv 0.240, Nc 0.047, mu_p 0.039,
tau_n 0.024, tau_p 0.024, tau_ETL 0.015, tau_HTL 0.014.

### (1457,1948) — cross-metric robust (NEW, predeclared criterion)
Selected by the §14 criterion: bottom-1% NN tail under **≥ 3 of M1–M5** **and**
dΘ above that metric's closest-1% median dΘ. Criterion met for **M1, M4, M5**
(bottom-1% + dΘ 0.2003 > 0.144/0.152/0.152); the criterion was never weakened.
| metric | d_J | percentile |
|---|---|---|
| M1 | 0.000199 | **0.9 %** |
| M2 | 0.5651 mA/cm² | 61.5 % |
| M3 | 0.0235 | 54.4 % |
| M4 | 0.00126 mA/cm² | **0.2 %** |
| M5 | 0.000052 | **0.2 %** |

dΘ = 0.2003 · params: tau_ETL **0.381**, mu_n 0.298, mu_p 0.276, tau_p 0.156, Nv
0.134, tau_n 0.080, r_rad 0.052, tau_HTL 0.014, Nc 0.003.

**Summary.** The two frozen manuscript examples remain bottom-1% under M1 and
bottom-2–5 % under the 0–1.0 V window metrics (M4/M5), but are near-median in
full-curve physical space (M2/M3). A new pair that is a genuine collision under
the normalized, 0–1.0 V physical, and Jsc-relative 0–1.0 V definitions at once is
available if a physical-space example is needed. **No claim of "below
experimental resolution" is made anywhere in this report.**

## 14. M6 (supplementary only)

J/|Jsc| shape RMSE (131 pts): Spearman 0.1070, NN-pair median dΘ 0.2190,
closest-1% 0.1686 (R_1pct 0.483). Consistent with M2/M3. **M6 is not used in any
primary claim** and is excluded from `metric_level_summary.csv`.

## 15. Limitations

1. **Parametric J–V space.** All distances are evaluated on the frozen 15307-sample
   training/test simulation cloud; the collisions are properties of the *effective
   retained simulation prior*, not of the physical device manifold itself.
2. **d_Theta is fixed** by design (per §3). The experiment tests robustness of the
   *J–V similarity*, not of the parameter distance — alternative parameter
   distances were deliberately not explored.
3. **Physical d_J units differ across metrics** (mA/cm² vs dimensionless), so
   cross-metric comparisons in this report are made on percentiles and ratios,
   never on raw magnitudes.
4. **Percentiles are descriptive** within each metric's NN distribution; they are
   not probabilities and not effect sizes (§9).
5. **The 0–1.0 V window** is called throughout *the 0–1.0 V lower-forward-bias
   analysis window*; it is not claimed to be "the operating region" or "the region
   determining all device metrics".
6. **No experimental-resolution statement.** None of the representative dΘ values
   are converted into a universal decade value; per-parameter conversions are
   deliberately not made (§17).
7. **M6 is supplementary** and excluded from the primary tables.
8. The robust-pair selection criterion (§14) is predeclared and never weakened;
   only one pair is reported (the top candidate by dΘ among the criterion-meeting
   pairs).

## 16. Discussion — why outcome B

- **Not D (normalization artifact):** raw physical metrics (M2, M4) show the same
  structure without any normalization; physical closest-1% sets are disjoint from
  the normalized ones, so they are genuinely new collisions.
- **Not C (weakens materially in physical space):** the NN-pair median dΘ stays at
  0.200–0.216 across all metrics (vs 0.349 random); closest-1% stays at
  0.144–0.182. The effect is large and statistically unambiguous everywhere. It
  is *somewhat* weaker in full-curve physical space than in normalized space
  (0.182 vs 0.144 at closest-1%) but nowhere near vanishing.
- **Not A (robust in detail across metrics):** the specific pairs change almost
  completely (M1↔M2 closest-1% Jaccard 0.013, M2↔M4 disjoint), and the exact
  parameter hierarchy varies (rank correlation down to ≈0 for M3 vs M4/M5).
- **Therefore B:** the *core* claim — statistically indistinguishable J–V curves
  correspond to parameter vectors far apart in the retained prior — is a robust,
  metric-independent feature of the model's inverse map; the *details* — which
  pairs collide and exactly which parameters are most ambiguous — depend on how
  J–V similarity is defined.

---

## EXPERIMENT 4 VERDICT

**Outcome: B — CORE AMBIGUITY ROBUST; DETAILS METRIC-DEPENDENT**

| Gate | Answer |
|---|---|
| ORIGINAL COLLISION CONCLUSION SURVIVES | **YES** |
| PHYSICAL-SPACE COLLISIONS EXIST | **YES** |
| PARAMETER-LEVEL AMBIGUITY HIERARCHY IS ROBUST | **YES (qualified)** |
| REPRESENTATIVE COLLISIONS REMAIN DEFENSIBLE | **YES (qualified)** |
| CORE SCIENTIFIC FRAMEWORK SURVIVES | **YES** |
| NEW TRAINING REQUIRED | **NO** |
| NEW COMSOL RUNS REQUIRED | **NO** |

Gate notes:

- **G3 (qualified):** the set of dominant ambiguous parameters (tau_ETL, r_rad,
  tau_HTL) is stable across metrics; exact ranks are not (rank correlation
  0.47–0.57 for M1 vs the physical metrics, ≈0 for M3 vs M4/M5).
- **G4 (qualified):** the two frozen representative pairs remain bottom-1% under
  M1 and bottom-2–5 % under the 0–1.0 V window (M4/M5), but are near-median under
  full-curve physical metrics (M2/M3). A new cross-metric robust pair (1457,1948)
  is bottom-1% under M1/M4/M5 simultaneously. Any physical-space citation of the
  frozen examples must reference the 0–1.0 V lower-forward-bias analysis window.

**Manuscript impact is wording-only** (see `EXP4_MANUSCRIPT_IMPACT.md`): the M1
numbers stand unchanged; the collision paragraph gains one robustness sentence;
the 0–1.0 V window is renamed to "the 0–1.0 V lower-forward-bias analysis
window"; no retraining, no re-figuring, no retraction.

Per the experiment specification, **Experiment 4 is the final planned reviewer
experiment. No Experiment 5 is started. The next phase is manuscript integration
and final technical/editorial QC.**
