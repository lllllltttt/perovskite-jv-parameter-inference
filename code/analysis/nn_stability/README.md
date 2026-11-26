# Random-subset stability analysis with duplicate collapse (M1)

Independent delivery at `E:\project\work1\20261019_NN_stability`,
derived read-only from `E:\project\work1\20261019_HC_revision_stage1_v2`.
No input, manuscript, or SI file was modified.

This round:

1. fixes the pilot self-check so that every `ok=False` case is a failure, and
   adds an isolated fault-injection negative control;
2. reproduces the archived Figure 3 / Table S6 nearest-neighbour analysis
   exactly from the frozen inputs;
3. repeats the M1 nearest-neighbour analysis on 1,000 random subsets of the
   15,307 test curves with duplicate collapse, using per-subset random-pair
   baselines and the archived tier rule;
4. reports medians and 2.5th–97.5th percentile ranges across replicates as
   **descriptive resampling percentile ranges**. These are not confidence
   intervals, not a bootstrap CI, and not independent experimental replicates.

Not done this round: COMSOL solves, model training or prediction, scaler
refitting, the expanded-ratio experiment, and any edit to the manuscript or SI.

## Contents

| Path | What it is |
|---|---|
| `pilot/pilot_train_eval.py` | fixed pilot script (every `ok=False` is `FAIL`) |
| `pilot/logs/selftest_normal.txt` | normal selftest, 9 PASS / 0 failures, exit 0 |
| `pilot/logs/selftest_fault_injection.txt` | negative control, 1 injected FAIL, exit 1 |
| `pilot/logs/exit_codes.txt` | recorded CLI exit codes |
| `scripts/reproduce_original.py` | archived-rule reproduction of pairs, S6, baselines |
| `out/reproduction/` | reproduction tables, checks, input hashes |
| `scripts/nn_stability.py` | resumable 1,000-replicate stability run |
| `out/stability/per_replicate.csv` | one row per replicate (101 fields) |
| `out/stability/summary.csv` | original value, replicate median, 2.5/97.5 percentiles |
| `out/stability/first500_vs_all1000.csv` | descriptive quantile comparison |
| `out/stability/interpretation_by_family.csv` | per-family shared-vs-ratio contrast |
| `out/stability/interpretation_all_three.csv` | replicates where a < r for all three families |
| `out/stability/closest01_volatility.csv` | closest-0.1% tier spread |
| `out/stability/nn_stability_results.{png,pdf,svg}` | result figure |
| `out/stability/figure_values.csv` | every plotted value |
| `docs/candidate_paragraphs.md` | candidate English Methods/Results/Limitations text |
| `QA.md` | verification report |
| `MANIFEST.json` | input/code hashes, seed, threads, timing, outputs |

## Reproduction of the archived analysis

`scripts/reproduce_original.py` copies the archived functions verbatim from
`20261006/figure_revision_phase1_v2_final/scripts/lib_v2.py` and uses the same
inputs (`data/dataset_normalized.npz`, `final_figures/scripts/_frozen_preds.npz`,
`data/param_scaler.pkl`, `data/J_scaler.pkl`). It reproduces 11,245 unique
undirected pairs with an identical pair set, the six Table S6 medians to
2.2e-16, and the random-pair baselines to 5.6e-17. The nine-parameter random
baseline in `benchmark_nn_cost.py` was not used.

## Stability design

- Replicate seed: `np.random.default_rng([20261019, rep])`, `rep = 1..1000`.
- Each replicate draws 15,307 indices with replacement, collapses duplicates,
  and rebuilds the directed nearest-neighbour graph on the unique subset using
  the frozen normalized 131-point currents (Euclidean, self-distance excluded,
  ties to the lowest subset index). Directed links are converted to ordered
  `(min, max)` keys and deduplicated.
- Actual `n_unique` is recorded, not fixed at 15,307.
- Random-pair baselines are redrawn from the same subset with the archived rule
  (`default_rng(42)`, 200,000 ordered index pairs, self-pairs dropped).
- Tiers use `k = max(1, round(n_pairs × f))` for f = 10%, 5%, 1%, 0.5%, 0.1%.
- The run stops at 1,000 replicates. The first 10 were a trial and are included.

## Results at a glance

Percentile pairs below are the 2.5th–97.5th percentiles across the 1,000
replicates (descriptive resampling ranges, not confidence intervals).

- Duplicate collapse leaves a median of 9,674 distinct curves per replicate
  (9,597–9,750) and 7,089 unique undirected pairs (7,016–7,155). The
  closest-0.1% tier always contains 7 pairs.
- All-pairs normalized medians (mobility / lifetime / DOS): shared scale
  0.366 / 0.327 / 0.427, log-ratio 0.826 / 0.869 / 0.953. The full-sample
  values are 0.353 / 0.312 / 0.404 and 0.810 / 0.861 / 0.944. The ratio values
  lie inside their percentile ranges; the three shared-scale values fall below
  the 2.5th percentile, a systematic upward offset of +0.013 to +0.023 when
  fewer curves are available.
- Shared-scale medians are below ratio medians in all three families in every
  replicate at the all-pair, 10%, 5% and 1% tiers, in 99.5% of replicates at
  0.5%, and in 58.9% at 0.1%.
- At the closest 0.1% tier (7 pairs) the medians are volatile, e.g. the
  lifetime shared-scale median is 0.280 (0.064–0.751) against 0.118 in the
  full sample, and the mobility ratio median spans 0.145–1.761 (median 0.698).
- First 500 vs all 1,000 replicates: maximum shift in a normalized median is
  0.0047, in a 2.5th percentile 0.0097, and in a 97.5th percentile 0.0197.
- 1,000 replicates completed with 0 failures and 0 retries: 759 s of replicate
  compute (median 0.756 s per replicate) and 753.5 s wall for the resumed run
  from replicate 11 to 1,000. Threads were library defaults (16 OpenBLAS/OpenMP
  threads reported); timings are not single-core or linear-scaling claims.

## Running

```
python scripts/reproduce_original.py
python scripts/nn_stability.py --target 1000     # resumes from per_replicate.csv
python scripts/summarize.py
python scripts/make_figure.py
python scripts/make_manifest.py
python scripts/qa_checks.py
```

Python 3.12, NumPy 2.3.5, pandas 2.3.3, matplotlib 3.10.8. Threads were left at library
defaults (OpenBLAS/OpenMP reported 16). Timings are measured wall-clock values,
not single-core or linear-scaling claims.

## Interpretation guardrails

- "Random-subset stability analysis with duplicate collapse" is the only name
  used for the procedure.
- Percentiles are descriptive resampling percentile ranges, not bootstrap 95%
  CIs and not a CI for the original 15,307-curve statistic.
- No p-values are computed; replicates share most curves and are not an
  independent experimental sample size.
- The analysis does not upgrade the descriptive neighbour comparisons to strict
  non-uniqueness or universal identifiability, and does not replace the
  supervisor-required bootstrap uncertainty analysis.
