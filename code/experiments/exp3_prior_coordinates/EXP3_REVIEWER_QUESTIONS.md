# EXPERIMENT 3 — Reviewer Questions Answered (Q1–Q10)

**Experiment dir:** `reviewer_experiments/exp3_prior_coordinate_recoverability/`
**Figures:** `figures/EXP3_FigA–F` · **Results:** `results/*.csv` · **QC:** `EXP3_QC.md` (12/12 PASS)
**Full analysis:** `EXP3_FINAL_REPORT.md`

All numbers are for the frozen Stage-I model on the frozen test set (N=15307)
unless stated. Log10-physical (decade) space throughout. Terminology follows the
constraint set: "recoverability under the effective retained simulation prior",
"shared-scale recoverability", "asymmetry-ratio recoverability",
"information beyond a prior-only point prediction".

---

### Q1. How much of the six paired bulk parameters' high apparent recoverability is shared-scale vs asymmetry-ratio?

**Answer.** Shared-scale recoverability dominates almost completely. In the
natural prior coordinates:

| pair | marginal Pearson (n / p) | shared scale a | ratio r |
|---|---|---|---|
| mobility | 0.906 / 0.919 | **0.925** | 0.429 |
| lifetime | 0.878 / 0.881 | **0.882** | 0.352 |
| DOS | 0.909 / 0.896 | **0.925** | 0.266 |

The marginal Pearson values (0.88–0.92) sit essentially on the shared-scale
recoverability (0.88–0.93). The electron–hole ratio recovers at r = 0.27–0.43.
In terms of predictive information beyond the prior (Skill_RMSE), the split is
even starker: shared scales 0.78–0.86, ratios 0.07–0.18.
*(EXP3_FigA, FigB, FigD; §6–8)*

### Q2. Is the asymmetry ratio recoverable at all, or is its apparent signal pure noise?

**Answer.** It is real but weak. The shuffled-pairing control (true vs predicted
test samples randomly re-paired, 100 perms, seed 20260826) gives a null
distribution of Pearson r with mean ≈ 0, SD ≈ 0.008, p95 ≈ 0.014. The observed
ratio recoverability sits **29–111 SD above the null** (smallest: r_D at 29 SD).
The model's ratio predictions carry genuine per-sample information; the median
ratio error is a constant ~1.6× (10^0.20 = 1.57/1.61/1.64) across all three
families. We do **not** claim the ratio is "noise" — only that its recoverable
share is small relative to the shared scale. *(§10; shuffled_pairing_null.csv)*

### Q3. Doesn't the high marginal pair correlation (0.94/0.99/0.90) mean mu_n/mu_p etc. are degenerate and cannot be separately recovered?

**Answer.** The high correlation is real and is **exactly reproduced by the
retained prior geometry alone**: corr(n,p) = (1 − k²)/(1 + k²) with
k = SD(0.5r)/SD(a) gives 0.933 / 0.988 / 0.896 (manuscript: 0.94 / 0.99 / 0.90,
worst deviation 0.007). It is the algebraic consequence of shared-scale
dominance in the prior (SD(a)/SD(0.5r) = 4–13). That is the correct reading of
"degeneracy": the shared scale dominates the retained prior and the model
recovers it; the asymmetry ratio is a narrow but non-degenerate channel.
*(§5; pair_geometry.csv)*

### Q4. Would a predictor that ignores the J–V entirely (prior-only) do just as well?

**Answer.** No — but the gap is concentrated in the shared scales. A prior-only
point predictor (training-set mean per coordinate, no val/test targets, no J-V)
achieves RMSE 0.32–0.87 decades on shared scales; the frozen model cuts that by
78–86%. For ratios the prior-only predictor already achieves ±0.32 decades and
the model improves it only 7–18%. So: **J–V adds large sample-specific
information beyond the prior for shared scales and small-but-real information
for ratios.** *(§8; frozen_coordinate_recoverability.csv, original_param_baseline.csv)*

### Q5. Is the shared-scale-vs-ratio hierarchy a VAE artefact?

**Answer.** No. The same decomposition on the five independent EXP1 seeds of the
VAE, and on det-AE and MLP (5 seeds each), gives the identical pattern:
shared scales 0.87–0.93, ratios 0.24–0.44, minimum shared-vs-ratio gap 0.44
(det-AE). The frozen manuscript model sits within ~1 SD of the 5-seed VAE means
on all six coordinates. The coordinate-level recoverability hierarchy is
architecture-stable. *(§11–12; architecture_coordinate_summary.csv)*

### Q6. Does the model actually use the J–V, or is it exploiting the prior marginal?

**Answer.** Both, in the correct proportions. (i) The shuffled control shows the
predictions carry genuine sample-wise association with the true coordinates, not
a prior-marginal echo (29+ SD above null). (ii) The sensitivity analysis — mean
|Pearson(coordinate, J(V))| over 131 voltages on physical J — mirrors
recoverability: shared scales are 3–23× more J-V-sensitive than ratios
(a_D = 0.113 is the mild exception, lowest shared-scale sensitivity, still
r = 0.925). (iii) The prior-only baseline shows the J–V is what supplies most of
the shared-scale predictive skill. The model uses the J–V; the prior supplies
the scale-level structure it is fitting. *(§9–10)*

### Q7. Is the weak ratio recovery a physical limitation of J–V or a model limitation?

**Answer.** This experiment does not separate the two and explicitly does not
claim prior-independent identifiability. What it shows: under the effective
retained prior the ratio's variance is small (SD ≈ 0.16 decades), its J–V
sensitivity is low (S ≈ 0.02–0.04), and its recoverable share is correspondingly
small and stable across architectures. Whether a differently shaped prior or a
different model could do better is out of scope. *(§9, §15)*

### Q8. What exactly do "recoverability" and "identifiability" mean here?

**Answer.** By constraint, "recoverability" is used strictly as *recoverability
under the effective retained simulation prior* — how well the trained model
recovers coordinates that actually vary in the retained training distribution.
We do not use the word "identifiability", and no prior-independent identifiability
claim is made or implied. High marginal Pearson is reported as shared-scale
recoverability, not as parameter-wise identification. *(§2, §15)*

### Q9. How robust are the numbers across seeds and samples?

**Answer.** (i) 5-seed VAE: max |recomputed vs EXP1 reported| marginal Pearson =
4.9e-07; frozen model within ~1 SD of the 5-seed means on every coordinate.
(ii) All reported correlations are on the full N=15307 test set; the geometry
tables include both retained (N=102046) and test populations and agree to the
3rd decimal. (iii) 12/12 programmatic QC assertions PASS (`EXP3_QC.md`). *(§3, §11)*

### Q10. What must change in the manuscript?

**Answer.** No retraining and no figure re-generation are needed; the wording
must be tightened. Ten concrete items are listed in
`EXP3_MANUSCRIPT_IMPACT.md`. The headline change: replace "high recoverability
of the six bulk parameters" with "shared-scale recoverability dominating under
the effective retained prior, plus a weak-but-real asymmetry-ratio channel", and
drop any phrasing that reads as parameter-wise identification. The reviewer
question is answered with Outcome A (SHARED-SCALE RECOVERY DOMINATES).
*(EXP3_MANUSCRIPT_IMPACT.md)*
