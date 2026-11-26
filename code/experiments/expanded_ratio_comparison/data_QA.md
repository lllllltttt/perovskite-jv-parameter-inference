# Data QA — expanded-ratio matched comparison (2026-10-21)

All numbers below are produced by `scripts/01_data_qa.py` and stored machine-readably in
`out/qa/qa_summary.json`, `out/qa/qa_checks.csv`, `out/qa/distribution_quantiles.csv`,
`out/qa/ratio_bin_shares.csv`, `out/qa/lhs_grid_recovery.csv`,
`out/qa/lhs_stratum_count_discrimination.csv`. The script recomputes everything from the two
CSVs read-only; no CSV, model, scaler or existing split was written or modified.

## 1. Files audited

| batch | dataset_id | path | shape | sha256 (first 16) |
|---|---|---|---|---|
| original ratio range | `orig200k` | `E:\project\work1\data\JV_database_9D_interface_lifetimes-2.csv` | 102,046 × 141 | `19aa6036ec4dafe6` |
| expanded ratio range | `exp50k` | `E:\project\work1\20261021\JV_database_9D_interface_lifetimes-newratio.csv` | 24,274 × 141 | `2664cbd7636c6ced` |

Both have 9 parameter columns in canonical order
(`mu_n_pvk, mu_p_pvk, tau_n_pvk, tau_p_pvk, Nc_eff_pvk, Nv_eff_pvk, tau_ETL, tau_HTL, rad_c`)
followed by `J_000 … J_130`; column lists are identical between batches and contain no duplicates.

The original-range file is the one that produced the frozen main model: its 102,046 rows equal
the 71,432 / 15,307 / 15,307 split sizes in the frozen `dataset_normalized.npz`.
`JV_database_9D_interface_lifetimes-3.csv` (153,067 rows) is the separate independent
validation batch and is **not** used here.

## 2. Filter rules — re-applied, not assumed

`script/mat-csv.py` applies, verbatim:

1. `J[:,0] > 0` — first current positive;
2. `(diff(sign(J)) < 0).any(axis=1)` — at least one negative sign change (a Voc-like crossing);
3. all currents finite;
4. `(diff(J) <= 0.2).all(axis=1)` — every adjacent increment ≤ 0.2 mA cm⁻².

Rule 2 is *not* "last current < 0" and rule 4 is *not* strict monotone decrease; the code above
is the operative definition and was copied unchanged. Re-applying it to the delivered files
rejects **0 rows in both batches** (102,046/102,046 and 24,274/24,274 kept; rule1..rule4 counts
all equal to n). The delivered CSVs are therefore already post-filter exports, and no filter
threshold was altered for this experiment.

## 3. Identifiers, uniqueness and duplicate/leakage check

| | original | expanded |
|---|---|---|
| n rows | 102,046 | 24,274 |
| Sample_ID unique | yes | yes |
| Sample_ID range | 2 – 200,000 | 1 – 50,000 |
| exact duplicate parameter vectors | 0 | 0 |
| byte-identical current curves | 0 | 0 |

Cross-batch: 0 shared parameter vectors at 8 significant figures. Sample_IDs are batch-local
(the same numeric ID in the two batches is a different sample); batches are distinguished by
`dataset_id` + `Sample_ID` throughout. Because there are no exact duplicates within or across
batches, an exact-count split needs no group assignment and cannot leak a duplicated sample.
Similar-looking curves with different parameters are the object of study and were **not**
removed.

## 4. Units

- `J` is stored in **mA cm⁻²**, i.e. COMSOL's A m⁻² multiplied by 0.1 (`J = np.squeeze(d["J"]) * 0.1`
  in `mat-csv.py`). Maximum short-circuit current density is 24.096 mA cm⁻² in *both* batches —
  the same physical ceiling, which would not happen if one batch had skipped the conversion.
- `rad_c` is the **pre-MATLAB raw value**: it lies in [1.0001e-12, 9.996e-10], inside the sampled
  range 1e-12 – 1e-9. `run_PSC_9D_8.m` multiplies by 1e-6 only when handing the value to COMSOL;
  no extra 1e-6 is present in the CSV. (Had it been applied twice, values would be ~1e-18.)
- All nine parameters are finite and positive in both batches.

## 5. Voltage grid and the 131 points — provenance

The CSVs contain no voltage column. The 0–1.3 V / 131-point grid is inherited from the
acquisition script `matlab&mph/run_PSC_9D_8.m`, which refuses to write a row unless
`mphglobal(model,'semi.J0_1')` returns exactly 131 values (comment in the file: "0~1.3V，步长
0.01V，共131点"), and from `pre-process.py` (`V = np.linspace(0, 1.3, 131)`). This is a chain of
documented conventions, not an independent measurement from the delivered files; it is recorded
here as such. The 131 columns are present and ordered `J_000…J_130` in both batches.

## 6. Provenance of the expanded batch (and what is missing)

Three different counts are relevant and must not be conflated:

| count | what it means | evidence |
|---|---|---|
| **50,000** | planned samples of the Latin hypercube | Sample_IDs span 1–50,000; declared N = 50,000 |
| **49,999** | MAT files present on disk (readable simulation outputs) | one MAT file absent for the 50,000 submitted samples |
| **24,274** | rows in the delivered post-filter CSV, i.e. samples that passed the four acceptance rules **and** were exported | CSV row count |

So 25,726 of the 50,000 planned samples are not in the delivered table: one is the missing MAT
file, and the other 25,725 are absent for reasons that **cannot be determined from the delivered
files**. Because the export is already post-filter, a sample that was simulated but rejected by
rules 1–4 is indistinguishable from one whose conversion never produced a usable row; no
per-sample reason is recorded. In particular, the 49,999 readable MAT files must **not** be
described as "accepted" or "physically retained" — only 24,274 rows are known to have passed the
filter and been delivered, and the status of the other 25,725 is unknown. No sample was invented,
re-run or assigned a guessed reason. The experiment uses all 24,274 delivered rows.

| item | evidence | verdict |
|---|---|---|
| ratio ranges | q ∈ [0.0512, 20.0] for all three ratios | linear-uniform 0.05–20 |
| log-variable ranges | g_mu ∈ [1.0e-6, 1.0e-3], g_tau ∈ [1.0e-9, 1.0e-2], g_D ∈ [1.0e22, 1.0e26]; tau_ETL/HTL, rad_c within their archived bounds | unchanged |
| LHS structure | `floor(u·50000)` unique for 99.81–99.99 % of rows (vs 38.46 % expected for iid uniform) | consistent with a 50,000-row Latin hypercube |
| one MAT missing | 49,999 MAT files for 50,000 submitted samples | **one sample absent; its Sample_ID cannot be determined from the delivered files** |

The LHS stratum test separates 50,000 from coarse alternatives but saturates for any finer
candidate, so it supports (does not prove) N = 50,000; see
`out/qa/lhs_stratum_count_discrimination.csv`. It cannot recover the *identity* of the missing
sample — that needs the original `/home/student2/parameter/..._newratio.csv` input file or the
COMSOL run log, neither of which is present locally.

The pre-filter distribution (which q values were rejected by the filter) **cannot be
recomputed**: only post-filter CSVs were delivered. Coarse retention is 24,274/50,000 = 48.5 %
for the expanded batch and 102,046/200,000 = 51.0 % for the original batch, but no
retention-by-ratio-bin statement can be derived from these files and none is made.

## 7. Sampling-distribution comparison

### 7.1 Ratios (the manipulated variable)

| quantity | batch | mean | sd | p5 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|---|---|---|
| q_mu | original | 2.585 | 1.386 | 0.434 | 1.379 | 2.582 | 3.784 | 4.751 | 5.020 |
| q_mu | expanded | 9.950 | 5.764 | 1.013 | 4.970 | 9.938 | 14.925 | 18.979 | 20.0 |
| q_tau | original | 2.603 | 1.385 | 0.443 | 1.403 | 2.602 | 3.801 | 4.760 | 5.023 |
| q_tau | expanded | 10.033 | 5.745 | 1.054 | 5.077 | 10.022 | 15.015 | 18.998 | 20.0 |
| q_D | original | 2.582 | 1.382 | 0.436 | 1.382 | 2.573 | 3.776 | 4.753 | 5.019 |
| q_D | expanded | 9.883 | 5.776 | 0.984 | 4.849 | 9.786 | 14.894 | 18.961 | 20.0 |

Share of samples by ratio band:

| band | q_mu orig | q_mu exp | q_tau orig | q_tau exp | q_D orig | q_D exp |
|---|---|---|---|---|---|---|
| q < 0.2 | 0.001 % | 0.762 % | 0.005 % | 0.746 % | 0.004 % | 0.824 % |
| 0.2 ≤ q ≤ 5 | 99.955 % | 24.413 % | 99.958 % | 23.836 % | 99.956 % | 24.973 % |
| q > 5 | 0.044 % | 74.825 % | 0.037 % | 75.418 % | 0.040 % | 74.203 % |

Samples with **all three** ratios inside the old 0.2–5 box: original 101,913 (99.87 %),
expanded **356 (1.47 %)**.

Because both batches sample q **linearly uniformly**, the distribution of log10 q is not
symmetric: its density is proportional to q, so it rises towards the upper bound. Widening
0.2–5 → 0.05–20 therefore does not merely inflate the variance of log q — it moves the median
by **+0.59 dex** (log10 q ≈ 0.41 → 1.00) and moves the mode from 5 (log10 = 0.70) to 20
(log10 = 1.30), while adding only a thin low-q tail (0.8 % of rows below 0.2). The two arms are
thus *not* nested in any equal-weighted sense: 74.8 % of the expanded batch lies beyond the old
upper bound and only 1.5 % of it lies inside the old three-ratio cube.

### 7.2 Shared scales (held fixed by design)

| quantity | batch | p5 | median | p95 |
|---|---|---|---|---|
| g_mu | original | 1.44e-6 | 3.61e-5 | 7.31e-4 |
| g_mu | expanded | 1.43e-6 | 3.59e-5 | 7.20e-4 |
| g_tau | original | 1.92e-9 | 1.15e-6 | 3.94e-3 |
| g_tau | expanded | 1.95e-9 | 1.10e-6 | 4.01e-3 |
| g_D | original | 5.18e23 | 9.31e24 | 7.90e25 |
| g_D | expanded | 6.28e23 | 1.04e25 | 8.00e25 |

The shared scales are very close between batches (as intended; `g_D` differs most, about 10 % in
the median), as are the two interface lifetimes and `rad_c` (full quantiles in
`out/qa/distribution_quantiles.csv`).

Two readings that must not be over-interpreted:

- The delivered marginals are **post-filter**, so they are the sampled priors multiplied by the
  acceptance function of the four filter rules. They are not flat per decade even though the
  shared scales were sampled log-uniformly (visible for `g_D` in `figures/fig01_data_distributions`).
  The two arms are distorted by the same acceptance function, which is what makes them
  comparable; the pre-filter density is not recoverable from these files.
- The CSVs carry no unit column. Stored magnitudes are consistent with SI units
  (mobility 1e-6–1e-3 m² V⁻¹ s⁻¹, i.e. 0.01–10 cm² V⁻¹ s⁻¹; DOS in m⁻³); the figure labels
  follow that convention. A constant unit factor would not change any log-scale comparison.

### 7.3 What the widening actually changes (sampling rule)

Both arms use the same sampling rule: a shared scale `g` is drawn from a fixed log-uniform prior,
and the two partners are constructed from it as

    p_n = g·√q ,      p_p = g/√q      (so p_n·p_p = g² for every sample).

The sampling rule therefore fixes the geometric mean of each pair at `g` and puts the whole ratio
information into `q`. Only the bounds of `q` change between arms (linear-uniform 0.2–5 vs
0.05–20); the bounds of `g`, `tau_ETL`, `tau_HTL` and `rad_c` are identical.

Consequence that is often stated wrongly: this is **not** a scheme with fixed individual-parameter
bounds in which a large `q` forces `mu_n` and `mu_p` towards opposite ends of a shared log range.
There are no fixed per-parameter bounds to be pushed against. What widening `q` does is widen the
range that *each* individual parameter can take around `g`: for a given `g`, `p_n/g = √q` spans a
factor of 20 in the expanded arm against 5 in the original arm (a 4-fold expansion of the
per-parameter span), and symmetrically for `p_p`. The consequence for this comparison is that the
marginal distributions of the individual parameters `mu_n`, `mu_p`, … necessarily differ between
the arms even though the sampling rule for `g` is unchanged; only the *rule* is held fixed, not
the induced marginals of the nine parameters. The residual p5/median shifts in `g_D` between arms
are post-filter selection effects (the four acceptance rules act on the current curves, which
depend on the parameter values), not a change in the `g` prior.

No sample was deleted or reweighted to force the two distributions to align.


## 8. Split design (written to `config/experiment_config.json` before any training)

- All 24,274 delivered expanded rows are used (see §6 for the 50,000 / 49,999 / 24,274 distinction).
- The original arm uses a seeded subsample of the same size: `default_rng(20261021).choice`
  without replacement, then sorted. **24,274 rows**, so both arms have identical counts.
- Split rule: `default_rng(seed).permutation(n)`; the first 16,992 indices are train, the next
  3,641 validation, the last 3,641 test. Exact counts, disjointness and full coverage are
  asserted in the script.
- Split seeds: original `[20261021, 101]`, expanded `[20261021, 102]`. One fixed split per arm,
  shared by all five training seeds.
- Result (both arms): **train 16,992 / val 3,641 / test 3,641**.
- Outputs: `data/split_manifest_<arm>.csv` (`dataset_id, Sample_ID, source_row, split`) and
  `data/split_summary.json` (counts, scaler ranges, train/test truth means, manifest sha256).
  Manifest sha256: original `d47cb467…`, expanded `c35599f0…`.

Both arms were trained from scratch. The frozen main model's predictions are **not** used as the
original-range control; the frozen model was itself fitted with full-retention scalers, so its
numbers are not comparable to either arm here.

## 9. Preprocessing actually applied, and its recorded caveat

- `log10` of the nine parameters (all nine satisfy max/min > 100, the rule from `pre-process.py`),
  then `MinMaxScaler` **fitted on that arm's own training rows only**. Validation and test are
  transformed with the training statistics; nothing is clipped.
- Currents: per-voltage `MinMaxScaler` fitted on that arm's training rows only.
- Parameter scaler ranges differ between arms because the q range moved the log-parameter
  extremes: e.g. `mu_n` range 3.641 (original) vs 4.148 (expanded) decades, `mu_p` 3.639 vs
  4.289, `Nc` 3.426 vs 4.065. The nine physical labels and their order are unchanged; the head
  still predicts the nine parameters, not the a/r coordinates.
- Consequence, recorded up front: independent scalers change the effective normalisation and
  hence the relative weight of the nine NLL terms. This experiment therefore measures the
  effect of the *whole* re-specified training distribution (ratio range + the scalers it
  induces), not a perfectly isolated range effect. The frozen main model additionally used
  full-retention scalers, so differences against its historical numbers are **not** attributed
  to the ratio range.

## 10. Blocking issues

None. No unit conflict and no parameter/batch mismatch was found, so formal training proceeded
as planned. Open data-side items are limited to (i) the one missing MAT sample whose identity
cannot be recovered locally and (ii) the unavailable pre-filter data, both recorded above.
