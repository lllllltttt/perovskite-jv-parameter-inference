# EXPERIMENT 4 — MANUSCRIPT IMPACT

Advisory record only. **No frozen manuscript, figure, or result file was
modified by this experiment.** Every item below is a recommendation for the
integration phase that follows this experiment.

| # | Question | Answer | Notes / suggested wording |
|---|---|---|---|
| 1 | Do any of the original Fig. 5 (M1) numbers change? | **NO** | M1 reproduced exactly: Spearman 0.1576, Pearson 0.0785, NN med 0.1999, tiers 0.1443/0.1337/0.1021, per-param ambiguity, both representative pairs. |
| 2 | Does the core collision claim (near-identical J–V ↔ very different parameters) survive? | **YES** | Robust under all 5 alternative metrics; NN dΘ 0.20–0.22 vs random 0.349 everywhere. |
| 3 | Should the manuscript add a robustness statement? | **YES (wording)** | Add one sentence to the collision paragraph: "The same one-to-many structure appears under alternative J–V similarity definitions, including raw physical-current RMSE over the full curve and over the 0–1.0 V lower-forward-bias analysis window (NN-pair parameter distance 0.20–0.22 vs 0.35 for random parameter pairs); the specific colliding pairs and the ranking of the most ambiguous parameters depend on the metric." |
| 4 | Is any "operating region" wording present that must change? | **YES (if present)** | Wherever the 101-point 0–1.0 V window is discussed, use "the 0–1.0 V lower-forward-bias analysis window" / "the 0–1.0 V region". Never "the operating region" or "the region determining all device metrics". |
| 5 | Are the two representative cases (1010,2641) and (8271,10258) still defensible? | **YES (qualified)** | Keep as normalized-metric (M1) examples and as 0–1.0 V-window examples (pct 1.9–4.6 %); do **not** cite them as full-curve physical-space examples (M2/M3 pct 27–47 %). If a physical example is needed, the new predeclared cross-metric pair (1457,1948) is bottom-1% under M1/M4/M5. |
| 6 | Should any figure in the manuscript change? | **NO** | Fig. 5 content stands. EXP4 figures (EXP4_FigA–F) are reviewer material. |
| 7 | Should the SI gain a robustness table? | **QUALIFIED** | Optional: a short SI table (like `distance_tiers_by_metric.csv`) showing closest-tier dΘ per metric vs the random baseline would pre-empt the reviewer question at publication time. |
| 8 | Is retraining / re-running COMSOL / recomputing sensitivity required? | **NO** | Analysis-only throughout. |
| 9 | Is any manuscript claim retracted or weakened? | **NO** | The impact is additive (one robustness sentence + wording fix). |
| 10 | Is the verdict relevant to other reviewer experiments? | **YES** | Consistent with EXP1 (leakage-free baselines) and EXP2 (latent-uncertainty decomposition): all reviewers' alternative-metric probes confirm the core scientific framework; no retrain needed. |

---

**Bottom line for the integration phase:** the manuscript survives Experiment 4
with **wording-only** changes — one robustness sentence in the collision
paragraph and a terminology fix for the 0–1.0 V window. All M1 numbers,
representative cases (with the window qualifier), and the overall conclusion
stand. No new training, no new COMSOL runs, no new simulation samples.
