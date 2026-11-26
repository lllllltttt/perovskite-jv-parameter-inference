# PATCH_NOTES — figure_revision_phase1_v2

What changed relative to `20261006/figure_revision_phase1`, why, and what the
evidence is. The phase-1 directory is untouched; this is an independent copy.

Scope honoured: no model retraining, no re-prediction, no COMSOL, no edit to any
manuscript or SI Word file, and the same frozen VAE-v6 model, scaler, training
split and test split throughout.

---

## 1. Figure 3(d) — wrong quantity and wrong labels  *(must-fix)*

**What was wrong.** The phase-1 sketch computed, for each of the nine
parameters,

```python
L = np.log10(params_test_raw)                      # L is ALREADY log10
vals = [abs(np.log10(L[i, q] / L[j, q])) for q in range(9)]   # fig3_sketch.py:197
```

so it plotted `|log10(log10 θ_i / log10 θ_j)|` — a logarithm of a ratio *of
logarithms* — instead of `|log10(θ_i/θ_j)|`. Worked example for pair (a),
`mu_n_pvk`: raw values 9.53e-4 and 2.78e-4, log10 values −3.020907 and
−3.555955, and the code computed `log10(0.849535) = 0.085403` where the correct
value is `|−3.020907 − (−3.555955)| = 0.628643`. Across both pairs the erroneous
value is 0.02–0.14 of the correct one (median 0.04), so the panel was not merely
mis-scaled — it reordered the parameters.

**Labels.** `ks = np.arange(9)[::-1]` was paired with
`[st.PARAM_LABELS[q] for q in ks]`, so each tick carried parameter `8−k`'s label
while plotting parameter `k`'s value. Eight of the nine labels sat against the
wrong bar (only the middle one, `Nc_eff_pvk` at tick 4, matched by coincidence).

**Fix.** `vals = abs(L[i, q] - L[j, q])`; value and label are now taken from the
same index. The x axis is set from the corrected data (`0 … 2.805`) instead of a
fixed `0 … 1.35`, so no bar is clipped (the largest corrected difference is
2.646 on `tau_p_pvk` for pair (a), which the old axis would have cut).

**Verification actually performed** (`scripts/fig3_case_analysis.py`,
`source_data/fig3_case_parameter_check.csv`):

- The corrected value was recomputed a second, independent way — straight from
  the raw physical parameters as `abs(np.log10(θ_i/θ_j))` — and compared with
  the log difference `abs(L_i − L_j)` for all 18 differences (2 pairs × 9
  parameters). Maximum discrepancy **1.75e-15**, i.e. floating-point noise. All
  18 are listed individually in the CSV and in the run log.
- The corrected single-parameter differences were reconciled with the paired
  coordinates by exact algebraic identity: for each family,
  `Δr = Δlog10 p_n − Δlog10 p_p` and `Δa = ½(Δlog10 p_n + Δlog10 p_p)`, both
  asserted to 1e-12. They hold exactly.
- Which parameter carries the largest difference changes for pair (b):
  the erroneous value pointed at `mu_n_pvk`, the corrected one at `tau_HTL`.
  For pair (a) it stays `tau_p_pvk`.

**Was it copied anywhere else?** Checked, not assumed:

| searched | result |
|---|---|
| every `*.py` under `E:\project\work1` for `log10(…[i…] / …[j…])` | the defective expression exists **only** at `20261006/figure_revision_phase1/scripts/fig3_sketch.py:197`, plus the two v2 scripts that deliberately reproduce it to document it |
| the archived analysis `work1_figures_reassembled_v5/scripts/fig3_ambiguity.py` | **correct**: line 233 uses `abs(np.log10(raw[i,k] / raw[j,k]))` — log10 of the ratio of *raw* values; line 349 does the same for the source table; line 244 uses `set_yticklabels(st.PARAM_LABELS, …)` with `ks`, correctly aligned |
| data files written by the v1 sketch | `fig3_example_pairs.csv` contains only the six coordinate differences (`absd_a_mu` … `absd_r_D`). The nine-parameter values were never written to any file. |
| the v1 report text | describes panel (d) generically ("all nine parameter differences of the two examples") and never names the argmax parameter, so no wrong number or name propagated |

**Conclusion: both defects were introduced by the phase-1 sketch itself, not
inherited from the archived package, and their impact was confined to the
rendered Figure 3(d) panel of the v1 delivery.** No other output, table or
analysis consumed them. This is a check result, not an assumption: the search
above is the basis for it.

---

## 2. Figure 3 — inferential statistics withdrawn  *(must-fix)*

The phase-1 figure and report carried paired Wilcoxon signed-rank p-values and
per-pair percentile bootstrap confidence intervals for the tier comparisons.
They are withdrawn. The tiers are not independent samples: in the closest 1%
tier, 112 pairs are built from 196 distinct curves and 27 curves appear in more
than one pair (24.6% of pairs involve a repeated curve); at 0.5% it is
56/99/13, and at 0.1% it is 11/21/1. Those are exactly the counts the review
supplied, re-verified here (`_verify_review_findings.py`, section F4).

Both procedures assume independent pairs, so neither is valid as stated. They
are removed from the figure, from the summary and from the recommended text.
Old outputs remain in the phase-1 directory, unmodified; the new report states
that they are not adopted because sample dependence was not handled.

**No replacement significance test and no new resampling scheme was
introduced.** What is kept is purely descriptive: distributions, medians,
quartiles, pair counts, distinct sample counts, and the per-pair fraction whose
shared-scale difference is smaller than its matching log-ratio difference.
The dependence numbers are reported alongside, as a property of the design.

This applies only to the new Figure 3 analysis. The cross-seed tests in SI S13
are a different design and are untouched.

---

## 3. Distribution preview — truncation removed  *(must-fix)*

The phase-1 preview used
`ax.hist(..., range=(0, 2.0), density=True)`. That drops every value above 2.0
and re-normalises the density on the retained part. The share of values above
2.0 is **16.86%** (`r_mu`), **18.95%** (`r_tau`) and **20.35%** (`r_D`); the
corresponding raw maxima are 4.99, 5.09 and 5.10. So roughly a fifth of each
ratio coordinate was invisible, and the visible part was scaled up to compensate.

**Fix.** The preview is now a full-range ECDF: all six coordinates, each showing
the nearest-neighbour pairs and the random pairs; every value of both sets is
plotted; each curve accumulates to 1; the x range covers the complete range of
both groups. The normalisation is by each coordinate's own random-pair median,
stated in the axis label together with the pair count and the seed, and the
`x = 1` reference line is drawn dotted and labelled. Shared scale is blue,
log-ratio orange, random pairs grey.

No value is dropped, no point is removed, and the random baseline is not
changed to make the curves look better. The raw log10 differences are still
available in the accompanying summary table.

---

## 4. Table S10 — the dedup rule applied uniformly to M1–M6  *(this round)*

**What was wrong.** The archived EXP4 pair construction used

```python
keep = np.arange(N) < nn_idx        # exp4_lib.dedup
```

which keeps a directed link only when it points *upward*. An unordered edge
`{i, j}` whose only directed link is the downward one (`i > NN(i) = j`) is
discarded, so the pair set is smaller than the set of distinct
nearest-neighbour edges. This affects all six metrics, not just M1:

| metric | pairs kept by the archived rule | distinct undirected edges | edges silently dropped |
|---|---|---|---|
| M1 | 7,666 | 11,245 | 3,579 |
| M2 | 7,635 | 11,060 | 3,425 |
| M3 | 7,638 | 11,104 | 3,466 |
| M4 | 7,666 | 11,208 | 3,542 |
| M5 | 7,670 | 11,212 | 3,542 |
| M6 | 7,691 | 11,036 | 3,345 |

**Fix.** Each sample finds its nearest neighbour, the link is mapped to
`(min(i,j), max(i,j))`, and duplicates are removed with
`key = lo*N + hi; np.unique(key, return_index=True)` — the same rule as the
mentor's, applied identically to M1–M6.

**What was deliberately not changed.** Each metric keeps its original
definition, preprocessing, weights and random-baseline rule:
M1 normalized full-curve RMSE (131 pts); M2 physical-current full-curve RMSE;
M3 = M2 divided by the pair-mean |Jsc|; M4 physical-current 0–1.0 V RMSE
(101 pts); M5 = M4 divided by the pair-mean |Jsc|; M6 = J/|Jsc| shape RMSE
(supplementary only). `d_Θ` remains the fixed RMSE over the nine normalized-log
parameters, identical by construction for every metric, and the random baseline
remains the frozen seed-42 draw of 200,000 ordered pairs with self-pairs removed
(199,985 retained, median d_Θ = 0.3490).

The nearest-neighbour search itself is **imported from `exp4_lib`**, so the
metric implementations are the archived ones and cannot drift, and the
recomputed directed links are asserted identical to the archived
`directed_nn_M*.csv` before use
(`source_data/si_table_s10_directed_nn_verify.csv`).

**Outcome — reported as it came out, not as hoped.** The corrected numbers move
by little, and the paper's robustness conclusion survives the fix for every
metric tested:

| metric | median d_Θ all-NN (old → new) | random | closest 1% (old → new) |
|---|---|---|---|
| M1 | 0.1999 → 0.2021 | 0.3490 | 0.1443 → 0.1452 |
| M2 | 0.2165 → 0.2194 | 0.3490 | 0.1816 → 0.1885 |
| M3 | 0.2164 → 0.2191 | 0.3490 | 0.1679 → 0.1808 |
| M4 | 0.2072 → 0.2092 | 0.3490 | 0.1520 → 0.1509 |
| M5 | 0.2073 → 0.2094 | 0.3490 | 0.1520 → 0.1509 |
| M6 | 0.2190 → 0.2220 | 0.3490 | 0.1686 → 0.1838 |

Every metric still puts nearest-neighbour curves far below the random parameter
distance, and every closest-1% median stays well under the random baseline. The
quoted ranges in the SI must nevertheless be updated (see the sync checklist):
the all-NN range becomes **0.202–0.222** (was 0.200–0.219) and the closest-1%
range becomes **0.145 (M1) to 0.189 (M2)** (was 0.144 to 0.182).

Two honest caveats, both pre-existing and neither introduced by this fix:

- For M2 the closest-0.1% median d_Θ is *higher* than the closest-1% value
  (0.2125 vs 0.1885; archived 0.1898 vs 0.1816). The tier medians are not
  monotone in tier tightness for this metric, in the old numbers as well as the
  new. The SI text should not imply monotonicity.
- Per-parameter ambiguity rankings remain metric-dependent, which is what the SI
  already says. Under the corrected pair set the M1 closest-1% ranking is
  `tau_ETL > mu_n > tau_HTL > r_rad > tau_n > tau_p > mu_p > Nv > Nc`; M2 puts
  `r_rad` and `tau_HTL` first, M3 and M6 put `tau_HTL` first, M4/M5 put
  `tau_ETL` first.

**Nothing is presupposed.** The script does not test whether the alternative
metrics "should" agree; it reports each metric's own corrected numbers, and the
non-monotonicity above is stated rather than smoothed over.

No source definition was missing: all six metrics are fully defined in
`exp4_lib.py`, and no substitute formula was invented.

---

## 5. Figure 2 — sketch completed, numbers untouched

Structure kept: panels (a)–(c) shared scale, (d)–(f) log-ratio, (g) Pearson
correlation, (h) MAE reduction against the training-median baseline; all 15,307
test curves in every panel.

1. **(g) and (h) are now equal width.** The bottom row is a 3×6 gridspec in
   which each of (g) and (h) spans three columns, which relieves the crowding in
   (h).
2. **The coordinates are labelled in log10 units**, per panel, and the
   shared-scale axes state the physical unit basis the logarithm was taken in:
   m² V⁻¹ s⁻¹ for mobility, s for lifetime, m⁻³ for DOS — the Table 1 sampling
   basis, verified against the observed column ranges
   (`source_data/unit_basis_check.csv`) and not silently changed.
3. **The correlation is named "Pearson correlation ρ"** in the axis label, so it
   cannot be read as the log-ratio coordinate *r* or as a Spearman statistic.
4. **Per-panel x and y limits are identical**, and the three ratio panels share
   one common range covering every true and predicted value.
5. The correlations, MAE reductions and training-coordinate medians are
   **unchanged**: they are recomputed from the same frozen sources and asserted
   against the phase-1 values to 5e-7 before the figure is drawn.

The in-panel legends in (g) and (h) were removed because they duplicated the
figure-level legend and collided with the value labels.

---

## 6. Representative cases — kept, as instructed

Both pairs are unchanged: (a) test indices 2890 / 5067, (b) 500 / 4560. The
selection rule is unchanged and is stated on the figure: they are the most
extreme members of the closest 1% of corrected pairs under the existing
normalized J–V metric, chosen by maximising a specific normalised ratio
difference — deliberately extreme examples, not randomly drawn typical ones. No
filter such as "all shared scales must be small" was added.

Each pair now carries: the physical current curves and the residual with its
direction made explicit (`ΔJ = J_j − J_i`); the physical-current RMSE and
max|ΔJ| in mA cm⁻²; all nine parameter differences; both curves' six paired
coordinate values (not only their differences); a statement that other
parameters change simultaneously; and a statement that a small normalised curve
distance does not by itself mean experimental indistinguishability. The indices
are labelled zero-based with the database Sample_ID beside them, and the mapping
is asserted on every run.

| pair | RMSE (mA cm⁻²) | max\|ΔJ\| (mA cm⁻²) | at V | Sample_ID |
|---|---|---|---|---|
| (a) 2890 / 5067 | 0.713 | 5.283 | 1.30 V | 141475 / 71905 |
| (b) 500 / 4560 | 0.532 | 3.124 | 1.30 V | 37892 / 87198 |

---

## 7. New independently checkable source data

| file | purpose |
|---|---|
| `fig2_coordinates_per_sample.csv` | every test sample's six coordinates, truth and prediction — the phase-1 `Figure2_paired_values.csv` was a summary and could not redraw the scatter |
| `fig3_random_pairs.csv.gz` | the actual random pairs (i, j) with their six raw absolute and six baseline-normalised coordinate differences; original seed 42 and sampling method, no favourable resampling |
| `fig3_case_curves.csv` | both pairs: voltage, J_i, J_j, residual J_j − J_i |
| `fig3_case_parameters.csv` | both pairs' nine parameters: physical values, units, log values, absolute log differences |
| `fig3_case_coordinates.csv` | both ends' six paired coordinates, raw differences, baseline-normalised differences |
| `nearest_neighbour_links.csv` | every test sample's directed nearest-neighbour index and distance, so the directed → undirected dedup can be audited line by line |
| `DATA_DICTIONARY.md` + `SOURCE_HASHES.csv` | array row order, parameter column order, units, model/split sources, random sampling rule, tier rounding, tied-distance handling, and SHA-256 of every input |

Model weights, training arrays, COMSOL outputs and unrelated full files are not
packaged.

---

## 8. Layout defects found by rendering the PDFs (and fixed)

The exported PDFs were rendered and read back, not just assumed to match the
PNGs. Three real collisions showed up at journal width and were fixed. They were
presentational only — no number changed — but they would have shipped.

| defect | where | fix |
|---|---|---|
| the two cases' annotation blocks overprinted each other | Figure 3, the row between the residual strips and the bottom panels | the head is split over two lines, the residual and closing sentences are re-wrapped to shorter lines, the body starts lower, and the selection rule (already in the figure footnote) is dropped from the inline block |
| the `(c)` legend overlapped a value label | Figure 3(c) | the key is drawn as one row of two entries instead of two rows, so it clears the tallest label |
| the `(d)` panel letter collided with `(c)`'s `0.94` label | Figure 3, between panels (c) and (d) | the `(c)` y range is now taken from the data (`whisk_top * 1.20`) instead of being fixed at 1.62 |

The third is worth spelling out: the fixed `ylim = (0, 1.62)` **clipped the
lifetime log-ratio interquartile whisker**, whose upper quartile is 1.746. The
whisker cap was cut off by the frame and its value label was pushed outside the
axes, on top of the `(d)` letter. The range is now computed from the data and an
assertion fails the build if any whisker would be clipped.

To keep this from silently recurring, `fig3_sketch_v2.py` now **measures the
drawn text extents on the real renderer and asserts** that (i) neither case's
annotation runs past its half of the figure, (ii) every `(c)` value label is
inside the axes, clear of the legend and clear of the `(d)` letter, and (iii) no
whisker is clipped. The build prints the margins; a regression aborts the run
instead of producing a figure. The rendered PDFs are kept in `_pdfcheck/` as the
evidence for this section.

## 9. What this delivery did not do

- It did not modify any manuscript or SI Word file, and it did not touch the
  phase-1 directory.
- It did not retrain, re-predict, or launch COMSOL.
- It did not add significance tests or complex resampling to Figure 3.
- It did not extend the analysis beyond the items listed above.

`Style_Sheet_20260928.md` was still not found in the project; this is recorded
as-is and the existing styling was continued. It is not a blocker for this
round.
