# EXPERIMENT 4 — REVIEWER QUESTIONS (Q1–Q10)

Answers address the one scientific question of the experiment: is the empirical
one-to-many inverse ambiguity (near-identical J–V ↔ very different parameters)
robust to alternative definitions of J–V similarity? Frozen model, analysis-only.

---

**Q1. Is the one-to-many inverse ambiguity real, or an artifact of the per-column
normalized J–V distance?**

Real. It survives under every one of five alternative similarity definitions,
including raw physical-current RMSE with **no normalization at all** (M2) and a
Jsc-relative shape metric (M3, M5). All metrics give NN-pair median parameter
distance 0.200–0.216 vs 0.349 for random parameter pairs, and closest-1% medians
0.144–0.182. Outcome D (normalization artifact) is excluded.

**Q2. Do physical-space metrics still show "identical-looking curves ↔ very
different parameters"?**

Yes. M2 (physical full curve) NN-pair median dΘ 0.2165, closest-1% 0.1816;
M4 (0–1.0 V lower-forward-bias analysis window) 0.2072 / 0.1520. Both far below
the 0.3490 random baseline. The physical closest-1% sets are disjoint from the
normalized ones (Jaccard 0.000 vs M2) — these are genuinely new physical
collisions, not echoes of M1.

**Q3. Do the specific colliding pairs agree across metrics?**

Mostly not. NN-identity agreement between M1 and M2 is 10.1 %, closest-1% pair
Jaccard 0.013. M2 and M4 closest-1% sets are disjoint. Heavy overlap only occurs
between near-identical definitions (M2↔M3 pair Jaccard 0.96; M4↔M5 0.98). The
core phenomenon is metric-independent; the identity of the colliding pairs is
metric-dependent.

**Q4. Which parameters are most ambiguous, and is the hierarchy stable?**

τ_ETL and r_rad are top-3 in every metric; τ_HTL is top-4 in the full-curve
metrics; Nc and mu_p are never in the top-4. The exact ranking within the top
tier shifts with the metric (τ_ETL first under M1/M4/M5, r_rad first under M2,
τ_HTL first under M3). Ambiguity-rank Spearman between the normalized and the
physical metrics is 0.47–0.57; between M3 and M4/M5 it is ≈0. Robust in which
parameters dominate, metric-dependent in exact rank.

**Q5. Are the two manuscript representative cases still collisions in physical
space?**

Qualified yes. (1010,2641) τ_ETL-dominant and (8271,10258) r_rad-dominant remain
bottom-1% under M1 and bottom-2–5 % under M4/M5 (the 0–1.0 V lower-forward-bias
analysis window), but are near-median under the full-curve physical metrics
(M2: 33–47 %; M3: 27–40 %). They remain defensible as normalized-metric
collisions and as 0–1.0 V-window collisions; a physical full-curve citation of
these two examples is not supported.

**Q6. What is the role of the 0–1.0 V lower-forward-bias analysis window vs the
full curve?**

The two windows probe different parts of the J–V curve. The 0–1.0 V window (101
points, M4/M5) gives parameter-distance behavior nearly as strong as the
normalized metric (closest-1% 0.152 vs 0.144) and is where the frozen
representative pairs collide. The full curve (M2/M3) is dominated by the
higher-bias portion, shows weaker (but still far-below-random) ambiguity, and
collides on a disjoint set of pairs. The window is deliberately called the
"0–1.0 V lower-forward-bias analysis window," never "the operating region."

**Q7. Is there a pair that is simultaneously a bottom-1% collision under several
metrics?**

Yes — predeclared, criterion never weakened. (1457,1948): bottom-1% under M1, M4,
and M5 (≥3 of M1–M5 as specified) with dΘ = 0.2003 above each of those metrics'
closest-1% median dΘ. It is the top candidate (largest dΘ) among the
criterion-meeting pairs and is reported as `cross_metric_robust`.

**Q8. Does the mutual-NN / dedup structure change with the metric?**

Mildly. Unique-pair counts are 7666 (M1), 7635 (M2), 7638 (M3), 7666 (M4),
7670 (M5) — deliberately **not** forced to 7666. Mutual-NN fractions are 0.531
(M1), 0.555 (M2), 0.549 (M3), 0.536 (M4), 0.535 (M5). No metric is an outlier;
the phenomenon is not driven by a metric-specific dedup pathology.

**Q9. Quantitatively, how far below random are the colliding pairs?**

Descriptive ratios only (not probabilities, not effect sizes): all-NN R_NN
0.573–0.620; closest-1% R_1pct 0.413–0.520. Random-pair median dΘ = 0.3490
(frozen seed-42 draw; independent seed-20260827 set gives 0.3489). Every tier
median for every metric is below the random baseline.

**Q10. Does the manuscript's collision claim survive, and what must change?**

Survives. The original M1 numbers (Fig. 5) are reproduced exactly and remain the
primary result. Required changes are wording-only: (i) one sentence noting that
the ambiguity is robust under alternative J–V similarity definitions including
raw physical currents; (ii) rename any "operating region" reference to "the
0–1.0 V lower-forward-bias analysis window"; (iii) if a physical-space example is
cited, use the 0–1.0 V window and/or the new cross-metric pair (1457,1948). No
retraining, no re-figuring, no retraction.
