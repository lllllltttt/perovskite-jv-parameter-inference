# QA — random-subset stability analysis with duplicate collapse

Date: 2026-10-19. Delivery: `E:\project\work1\20261019_NN_stability`.
Base (read-only): `E:\project\work1\20261019_HC_revision_stage1_v2`.
Automated checks: `scripts/qa_checks.py` → `out/qa_checks.json` (run with the
same Python 3.12 interpreter; non-zero exit on any failure). Final result:
**38 checks, 0 failed**.

## 1. Scope and constraints

- Not started: COMSOL, model training, prediction, scaler refitting, the
  expanded-ratio experiment, and any manuscript/SI edit.
- Scripts import only standard-library modules, NumPy, pandas, matplotlib and
  threadpoolctl (used to report thread settings); the pickled scaler is loaded
  with `pickle`. The import scan in `qa_checks.py` finds no solver, training, or
  network module.
- All inputs were opened read-only. Their SHA256 values before and after the
  run match (section 6).

## 2. Pilot self-check fix

`scripts/pilot_train_eval.py` → `pilot/pilot_train_eval.py`.

- `record()` now assigns `status = "PASS" if ok else "FAIL"` and increments the
  failure counter for **every** `ok=False`. The old `EXPECTED-ERROR` branch,
  which hid a missing exception for `expected_sizes=None`, is removed. A
  correctly raised expected exception is passed to `record()` as `ok=True` and
  is therefore a PASS.
- The diff against the v2 base is confined to the docstring, `run_selftest`,
  and the argparse/main wiring. `make_split` and every production function are
  unchanged.
- Normal selftest: 9 PASS, `FAILURES: 0`, exit code 0
  (`pilot/logs/selftest_normal.txt`, `exit_codes.txt`).
- Fault injection (`--selftest --fault-injection`): a test-local wrapper around
  `make_split` wrongly accepts n = 2 for the duration of that single case, then
  the real binding is restored in a `finally` block. The case records
  `FAIL  no error raised`, the run ends with `FAILURES: 1`, and the CLI exits 1
  (`pilot/logs/selftest_fault_injection.txt`).
- Outside the selftest, `make_split(2, ...)` still raises `SplitError`
  (checked in-process by `qa_checks.py`).
- Fault injection touched no real, frozen, or original data; all selftest data
  are synthetic and generated in memory.

## 3. Reproduction of the archived analysis

`scripts/reproduce_original.py` copies `coordinates`, `nearest_neighbours`,
`dedup_undirected`, `random_pairs` and `tier_k` verbatim from
`20261006/figure_revision_phase1_v2_final/scripts/lib_v2.py` and follows
`fig3_pair_analysis_v2.py`.

Input verification (`out/reproduction/input_verification.json`):

| Check | Result |
|---|---|
| test curves × voltage points | 15,307 × 131; last voltage 1.3 V |
| parameter rows ↔ current rows | positional join in `_frozen_preds.npz`; inverse-scaler max abs difference 7.1e-15 |
| frozen normalized J ↔ dataset normalized J | max abs 2.98e-8 (float32 storage) |
| inverse transform to physical current | max abs relative to each voltage span 2.98e-8 |
| row correspondence cross-check | `jsc` equals |J| at 0 V to 0.0 absolute |
| a/r construction | a = 0.5(log₁₀pₙ + log₁₀pₚ), r = log₁₀pₙ − log₁₀pₚ, applied once to raw parameters |

Archived-result reproduction (`out/reproduction/reproduction_check.json`):

| Item | Result |
|---|---|
| unique undirected pairs | 11,245 vs 11,245; pair sets identical (0 either-only) |
| directed links / mutual pairs | 15,307 / 8,124 |
| curves touched / multi-pair / max degree | 15,307 / 5,859 / 5 |
| six Table S6 medians | max abs difference 2.22e-16 |
| tier pair counts | identical |
| random-pair baselines (seed 42, 199,985 pairs) | max abs difference 5.55e-17 |
| overall | `reproduction_ok = true` |

The nine-parameter random baseline in `benchmark_nn_cost.py` was **not** used,
and no value already in log₁₀ space was logged again.

## 4. Stability run integrity

`scripts/nn_stability.py` → `out/stability/per_replicate.csv`,
`run_manifest.json`, `run_log.txt`.

- 1,000 rows, replicate numbers 1–1000 consecutive, no duplicate or missing
  replicate, no NaN/Inf in any field.
- Seeds: base 20261019; per replicate
  `np.random.default_rng([20261019, rep])`; random-pair seed 42.
- Each replicate: 15,307 draws with replacement → duplicate collapse →
  directed nearest-neighbour graph on the unique subset → ordered (min, max)
  dedup → per-subset random-pair baseline → six coordinates over all pairs and
  five tiers.
- Realized subset size: median 9,674 distinct curves; 2.5th–97.5th percentile
  9,597–9,750; min 9,516, max 9,791. Pair count: median 7,089; range
  7,016–7,155 (2.5th–97.5th), min 6,966, max 7,236.
- Tier sizes equal `max(1, round(n_pairs × f))` in every replicate; the
  closest-0.1% tier contains 7 pairs throughout.
- Determinism: replicates 1, 500 and 1,000 were recomputed from scratch in a
  separate process and match every stored field to 1e-12 (elapsed time
  excluded). Only the timing field differs.
- Resume: rows are appended and fsynced one at a time; a partially written last
  line is truncated on restart. The 10-replicate trial is included as
  replicates 1–10; the resumed run continued from replicate 11.
- Failures: 0. Retries: 0. `completed_replicates = 1000`, `target = 1000`.
- Timing: 759.0 s summed over the 1,000 replicates (median 0.756 s, min 0.724 s,
  max 1.030 s); 753.5 s wall for the resumed run
  (2026-10-19T05:45:14Z → 05:57:46Z). The 10-replicate trial took 9.0 s wall
  including input loading.
- Threads: no environment override; OpenBLAS and OpenMP reported 16 threads.
  The timings are measured values and are not presented as single-core or
  linear-scaling results.

## 5. Summary, comparison and figure

- `summary.csv` holds, for every quantity, the original full-sample value (where
  one exists), the median across replicates, the 2.5th and 97.5th percentiles,
  the replicate minimum and maximum, and the replicate count. Values agree with
  `per_replicate.csv` to below 1e-12.
- `first500_vs_all1000.csv`: for the normalized statistics, the largest shift
  between the first 500 replicates and all 1,000 is 0.0047 in a median, 0.0097
  in a 2.5th percentile, and 0.0197 in a 97.5th percentile. The integer counts
  shift by at most 2 in the median (reported but not a stability concern).
- `figure_values.csv` reproduces every plotted value from `summary.csv` and
  `per_replicate.csv`; panel (b) differences were recomputed from the paired
  normalized medians. The PNG, PDF and SVG were regenerated from the final CSV
  and the PNG was opened and inspected: marker positions match the tabulated
  medians and the percentile bars match the tabulated ranges; both panels state
  that the ranges are not confidence intervals.
- `closest01_volatility.csv` records the closest-0.1% spread; the tier has
  7 pairs, 12–14 distinct curves, 0–2 curves in multiple pairs, and at most 3
  pairs per curve.

## 6. Files and hashes

`MANIFEST.json` lists the SHA256 of every input, every script, and every
delivered output, together with the seed, thread settings, timings, completed
count and empty failure/retry lists.

Input SHA256 values (unchanged before and after):

| Input | SHA256 prefix |
|---|---|
| `data/dataset_normalized.npz` | `0993b312a3516b4d…` |
| `final_figures/scripts/_frozen_preds.npz` | `ad156cd18c1933e8…` |
| `data/param_scaler.pkl` | `70cdc709d7130a75…` |
| `data/J_scaler.pkl` | `3b82a2541bd77c59…` |

## 7. Interpretation boundary

The name used is "random-subset stability analysis with duplicate collapse".
The percentiles are descriptive resampling percentile ranges, not bootstrap
95% confidence intervals and not a CI for the original 15,307-curve statistic.
No p-values were computed, the replicates are not independent experimental
samples, and no claim of strict non-uniqueness or universal identifiability is
made. The analysis complements but does not replace the supervisor-required
bootstrap uncertainty analysis.

## 8. Reproduce

```
python scripts/reproduce_original.py
python scripts/nn_stability.py --target 1000
python scripts/summarize.py
python scripts/make_figure.py
python scripts/qa_checks.py
python scripts/make_manifest.py
```

`make_manifest.py` must run after `qa_checks.py` so that `out/qa_checks.json` is
included in the manifest.
