# PHASE1_REPORT_v2 — targeted revision of `figure_revision_phase1`

Independent delivery: `E:\project\work1\20261006\figure_revision_phase1_v2\`.
The phase-1 directory is not modified. No manuscript or SI Word file is
modified.

This round repaired the defects found in review, recomputed what depended on
them, and delivered the corrected figures, source data and reports. It did not
retrain the model, re-predict, refit the scaler, launch COMSOL, or change the
training or test split. The same frozen VAE-v6 model, scaler and splits are
used throughout.

Companion documents: `PATCH_NOTES.md` (what changed and why, with evidence),
`DATA_DICTIONARY.md` (table by table), `SOURCE_HASHES.csv` (every input),
`SYNC_CHECKLIST_v2.md` (main-text / SI positions to update).

---

## 1. Figure 3(d) — corrected computation and parameter labels

### 1.1 The defect

The phase-1 sketch computed `abs(np.log10(L[i,q] / L[j,q]))` with
`L = np.log10(params_test_raw)`, i.e. a logarithm of a ratio *of logarithms*,
and paired bar `k` with the label of parameter `8−k` for eight of the nine bars.

Worked example, pair (a), `mu_n_pvk`: raw 9.53e-4 and 2.78e-4; log10 −3.020907
and −3.555955; the sketch plotted `log10(0.849535) = 0.085403` where the correct
value is `|−3.020907 + 3.555955| = 0.628643`. Across both pairs the erroneous
value is 0.02–0.14 of the correct one (median 0.04), so the panel did not merely
mis-scale — it reordered the parameters.

### 1.2 Corrections

- Value: `abs(L[i,q] − L[j,q]) = |log10(θ_i/θ_j)|`.
- Label and value now come from the same index; the tick labels are consumed in
  the same slot order as the bars.
- The x axis is set from the corrected data, `0 … 2.805`, replacing the fixed
  `0 … 1.35`, so no bar is clipped (the largest corrected difference is 2.646 on
  `tau_p_pvk`, pair (a), which the old axis would have cut).

### 1.3 Verification performed

| check | result |
|---|---|
| corrected value recomputed independently from raw physical parameters as `abs(log10(θ_i/θ_j))` | max discrepancy **1.75e-15** over all 18 differences |
| all 18 differences (2 pairs × 9 parameters) listed individually | `source_data/fig3_case_parameter_check.csv` |
| single-parameter differences reconciled with paired coordinates | `Δr = Δlog10 p_n − Δlog10 p_p` and `Δa = ½(Δlog10 p_n + Δlog10 p_p)` hold to 1e-12 exactly |
| label-to-bar alignment | printed slot by slot at build time; the argmax parameter of each pair is drawn under its own label |
| x axis covers the data | limit 2.805 > observed max 2.646 |

The corrected per-pair values are in `fig3_case_parameters.csv` (raw values,
units, log values, signed and absolute log differences, and the erroneous
phase-1 value for comparison).

Which parameter carries the largest difference changes for pair (b): the
erroneous value pointed at `mu_n_pvk`, the corrected one at `tau_HTL`. For
pair (a) it stays `tau_p_pvk`.

### 1.4 Was it copied to other outputs?

Checked, not assumed. The defective expression occurs **only** at
`20261006/figure_revision_phase1/scripts/fig3_sketch.py:197`, plus the two v2
scripts that reproduce it deliberately in order to document it. The archived
analysis `work1_figures_reassembled_v5/scripts/fig3_ambiguity.py` is **correct**
on both counts (line 233 computes `abs(np.log10(raw[i,k]/raw[j,k]))` from the
raw values; line 244 aligns label and bar). The v1 sketch wrote no
nine-parameter values to disk — `fig3_example_pairs.csv` holds only coordinate
differences — and the v1 report never names the argmax parameter.

**Both defects were introduced by the phase-1 sketch, not inherited from the
archived package, and their effect was confined to the rendered Figure 3(d)
panel of that delivery.** No other output consumed them.

---

## 2. Figure 3 uses descriptive analysis this round

**Withdrawn:** the paired Wilcoxon signed-rank p-values and the per-pair
percentile bootstrap confidence intervals. They treated the tier pairs as
independent, but they are not: in the closest 1% tier 112 pairs are built from
196 distinct curves with 27 curves in more than one pair (24.6% of pairs involve
a repeated curve); at 0.5% it is 56 / 99 / 13; at 0.1% it is 11 / 21 / 1. These
are the counts supplied in review, re-verified here. Both procedures are invalid
as stated and appear nowhere in the v2 figure, summary or recommended text. The
old outputs stay in the phase-1 directory, unmodified.

**Also removed:** the judgements "decisive", "only DOS significant", and "the
other two merely underpowered".

**No replacement significance test and no new resampling scheme was added.**

**Kept:** distributions, medians, quartiles, pair counts, distinct sample
counts, and the per-pair fraction whose shared-scale difference is smaller than
its matching log-ratio difference. Dependence is now reported as a property of
the design rather than corrected for.

This applies only to the new Figure 3 analysis. The cross-seed tests in SI S13
are a different design and are untouched.

---

## 3. Distribution preview — truncation removed

The phase-1 preview used `ax.hist(..., range=(0, 2.0), density=True)`, which
drops every value above 2.0 and re-normalises the density on the retained part:

| coordinate | median | p95 | max | share above 2.0 |
|---|---|---|---|---|
| `a_mu` | 0.353 | 1.315 | 3.307 | 0.98% |
| `r_mu` | 0.810 | 3.125 | 4.992 | **16.86%** |
| `a_tau` | 0.312 | 1.489 | 2.737 | 0.87% |
| `r_tau` | 0.861 | 3.304 | 5.086 | **18.95%** |
| `a_D` | 0.404 | 1.497 | 3.869 | 1.65% |
| `r_D` | 0.944 | 3.303 | 5.096 | **20.35%** |

Roughly a fifth of each ratio coordinate was invisible and the visible part was
scaled up to compensate.

**Replaced by a full-range ECDF**, six panels, each showing the
nearest-neighbour pairs and the random pairs for one coordinate. Every value of
both sets is drawn; each curve accumulates to 1; the x range covers the complete
range of both groups. The normalisation is by that coordinate's own random-pair
median, stated in the axis label together with the pair count and the seed. The
`x = 1` random-baseline line is kept, dotted and labelled. Shared scale blue,
log-ratio orange, random pairs grey.

No truncation, no dropped points, and the random baseline was not changed to
improve the appearance of the curves. The raw log10 differences remain in the
summary table.

The corrected pair set is identical to the phase-1 pair set (checked by set
comparison), so this change is presentational only.

---

## 4. Tightened conclusions

### 4.1 Edge count

Replaced: "every curve has exactly one undirected edge".

Adopted: every test curve contributes one **directed** nearest-neighbour
relation; after mapping each relation to its unordered pair and deduplicating,
the result is **11,245 undirected edges covering all 15,307 test curves**, and a
curve may participate in more than one edge (5,859 curves do; the maximum is 5).

### 4.2 The mobility closest-1% ratio median

The baseline-normalised mobility log-ratio difference has median ≈ 1.035 in the
closest 1% tier. Permitted: it "does not show a smaller median difference than
the random-pair baseline".

Not written, and not to be written: that it is indistinguishable from random;
that the ratio carries no information; that only the shared scale is
constrained; that curve proximity is determined by the shared scale alone. The
median is a point summary of a distribution whose interquartile range spans
values both below and above 1, and the interval is not a test.

### 4.3 One calculation, not two

"Percent reduction of raw differences relative to the random baseline" and "the
value after dividing by the random median" are the same calculation expressed
two ways. Both are kept because they help the reader, but they are **not
independent verification** of one another, and wording such as "independently
proves the normalization did not manufacture the conclusion" has been deleted.

### 4.4 Adopted scope of the conclusion

On the current simulated test set, and against the random-pair baseline as
constructed here: for nearest-neighbour curves, the **shared-scale** differences
shrink more than the random baseline, while the **log-ratio** differences shrink
less. That is the whole claim.

### 4.5 Figure 2 and Figure 3 are different statements

Figure 2 reports the frozen estimator's prediction-recovery performance: how
well the model recovers the coordinates of a curve's parameters. Figure 3
reports parameter differences between neighbouring curves **in simulated data**.
Figure 3 is therefore not a proven causal explanation of Figure 2's performance,
and it is not a universal physical identifiability limit.

---

## 5. Representative cases — unchanged

Both pairs are kept: (a) test indices 2890 / 5067, (b) 500 / 4560. The selection
rule is unchanged and is stated on the figure — they are the most extreme
members of the closest 1% of corrected pairs under the existing normalized J–V
metric, chosen by maximising a specific normalised ratio difference, and are
deliberately extreme examples, not randomly drawn typical ones. No additional
filter such as "all shared scales must be small" was introduced.

| pair | normalized d_J | physical RMSE (mA cm⁻²) | max\|ΔJ\| (mA cm⁻²) | at V | Sample_ID |
|---|---|---|---|---|---|
| (a) 2890 / 5067 | 1.95e-4 | 0.713 | 5.283 | 1.30 V | 141475 / 71905 |
| (b) 500 / 4560 | 1.96e-4 | 0.532 | 3.124 | 1.30 V | 37892 / 87198 |

Each panel now carries: the physical current curves; the residual strip with its
direction made explicit as `ΔJ = J_j − J_i`; the physical-current RMSE and
max|ΔJ| in mA cm⁻²; both curves' six paired coordinate values, not only their
differences; all nine parameter differences; a statement that other parameters
change simultaneously; and a statement that a small normalised curve distance
does not by itself mean experimental indistinguishability. Indices are labelled
zero-based, with the database Sample_ID beside them; the mapping is asserted
each run and is available only because `params_phys[idx_test]` and
`J_phys[idx_test]` reproduce the frozen arrays exactly.

All nine parameters differ in both cases (|Δlog10| > 0.01 for 9 of 9). The
largest single difference is `tau_p_pvk` at |Δlog₁₀| = 2.646 (×443) for pair (a)
and `tau_HTL` at 1.544 (×35) for pair (b) — a consequence of the selection rule,
which maximises a ratio difference rather than asking which parameter dominates.

**One consequence is worth the author's attention, and it is recorded in the
sync checklist §G.** The manuscript currently names its two Figure 3 examples as
τ_ETL (differing by "approximately a factor of 280") and r_rad (a factor of 72).
Those two examples are test indices (1010, 2641) and (8271, 10258), and both
factors reproduce exactly from the raw parameters as ×278 and ×72 — so the
Word's numbers are correct and were computed from raw log₁₀ differences, not
from the double-log quantity. The sketch's pairs are different pairs, so if the
final figure keeps the sketch's examples, MS p25 and the Figure 3 caption must be
rewritten with ×443 (`tau_p_pvk`) and ×35 (`tau_HTL`). All four pairs — the two
in the Word and the two in the sketch — are present in the corrected pair set.

---

## 6. Figure 2 sketch

Structure kept: (a)–(c) shared scale, (d)–(f) log-ratio, (g) Pearson
correlation, (h) MAE reduction against the training-median baseline, with all
15,307 test curves in every panel.

| change | detail |
|---|---|
| (g)/(h) equal width | the bottom row is a 3×6 gridspec; each of (g) and (h) spans three columns, relieving the crowding in (h) |
| log10 units explicit | every panel is labelled in log10 units |
| physical unit basis stated | shared-scale axes state the Table 1 sampling basis the logarithm was taken in — m² V⁻¹ s⁻¹ (mobility), s (lifetime), m⁻³ (DOS); verified against the observed column ranges in `source_data/unit_basis_check.csv`; no unit was changed while keeping the original coordinate values |
| correlation named | "Pearson correlation ρ", so it cannot be read as the log-ratio coordinate *r* or as Spearman |
| ranges | identical x and y limits per panel; one common range across the three ratio panels, covering all true and predicted values |
| numbers unchanged | all six correlations and all six MAE reductions recomputed from the same frozen sources and asserted against the phase-1 values to 5e-7 before drawing |

| coordinate | Pearson ρ (true vs predicted) | MAE reduction vs training-median baseline |
|---|---|---|
| `a_mu` | 0.925 | 68.1% |
| `r_mu` | 0.429 | 8.4% |
| `a_tau` | 0.882 | 61.3% |
| `r_tau` | 0.352 | 2.7% |
| `a_D` | 0.925 | 66.3% |
| `r_D` | 0.266 | 0.8% |

The in-panel legends in (g) and (h) were removed: they duplicated the
figure-level legend and collided with the value labels.

---

## 7. Table S10 — uniform dedup rule for M1–M6

Full detail in `PATCH_NOTES.md` §4 and `TABLE_S10_DRAFT_V2.md`. In summary:

The archived pair construction kept a directed link only when it pointed
upward (`keep = arange(N) < nn_idx`), so every undirected edge whose only link
was the downward one was discarded. This affected all six metrics, dropping
3,345–3,579 edges each. The corrected rule — each sample's nearest neighbour →
`(min(i,j), max(i,j))` → unique — is now applied identically to M1–M6.

Each metric keeps its original definition, preprocessing, weights and random
baseline; `d_Θ` stays the fixed RMSE over the nine normalized-log parameters;
the random baseline stays the frozen seed-42 draw (199,985 pairs, median
`d_Θ` = 0.3490). The nearest-neighbour search is imported from `exp4_lib`, so
the metric definitions are the archived ones, and the recomputed directed links
are asserted identical to the archived `directed_nn_M*.csv`.

| metric | pairs (old → new) | median d_Θ all-NN (old → new) | closest 1% (old → new) |
|---|---|---|---|
| M1 | 7,666 → 11,245 | 0.1999 → 0.2021 | 0.1443 → 0.1452 |
| M2 | 7,635 → 11,060 | 0.2165 → 0.2194 | 0.1816 → 0.1885 |
| M3 | 7,638 → 11,104 | 0.2164 → 0.2191 | 0.1679 → 0.1808 |
| M4 | 7,666 → 11,208 | 0.2072 → 0.2092 | 0.1520 → 0.1509 |
| M5 | 7,670 → 11,212 | 0.2073 → 0.2094 | 0.1520 → 0.1509 |
| M6 | 7,691 → 11,036 | 0.2190 → 0.2220 | 0.1686 → 0.1838 |

The robustness conclusion survives for every metric tested; the SI's quoted
ranges must be updated to **0.202–0.222** and **0.145 (M1) to 0.189 (M2)**.

Two honest caveats, both pre-existing: for M2 the closest-0.1% median is higher
than the closest-1% median (0.2125 vs 0.1885), so the tier medians are not
monotone in this metric in the old numbers either; and the per-parameter
ambiguity ranking remains metric-dependent, as the SI already states.

No source definition was missing, and no substitute formula was invented. The
outcome was not presupposed — the script reports each metric's own corrected
numbers, including the non-monotonicity.

---

## 8. Independently checkable source data

| file | what it makes possible |
|---|---|
| `fig2_coordinates_per_sample.csv` | redraw the Figure 2 scatter panels — the phase-1 summary file could not |
| `fig3_random_pairs.csv.gz` | re-run the baseline without re-drawing: the actual (i, j) pairs, six raw and six normalised differences; original seed 42 and sampling rule |
| `fig3_case_curves.csv` | redraw the curve and residual panels: voltage, J_i, J_j, J_j − J_i |
| `fig3_case_parameters.csv` | check every nine-parameter difference from raw values and units |
| `fig3_case_coordinates.csv` | the two curves' six paired coordinates each, with raw and normalised differences |
| `nearest_neighbour_links.csv` | audit the directed → undirected dedup line by line |
| `DATA_DICTIONARY.md` | array row order, parameter column order, units, model/split provenance, random sampling rule, tier rounding, tied-distance handling |
| `SOURCE_HASHES.csv` | SHA-256, size and mtime of all 17 inputs |

Ties: nearest neighbours are taken with `np.argmin`, which returns the lowest
index among tied minima, so tied distances resolve deterministically in index
order. Tier size is `k = max(1, round(M·f))` with `M` the edge count, and tiers
are the `k` smallest distances under `np.argsort(kind='stable')`.

Existing summary tables from phase 1 are kept alongside the new pair tables. No
model weights, training arrays, COMSOL outputs or unrelated full files are
packaged.

---

## 9. Delivery, inspection and stop point

### 9.1 Delivered

- Corrected Figure 2 and Figure 3 sketches, both at journal and large size, in
  PNG, PDF and SVG, plus the updated SVGs.
- Full-range ECDF preview in PNG, PDF and SVG.
- Updated and new scripts, and the source data listed in §8.
- `PHASE1_REPORT_v2.md` (this file), `PATCH_NOTES.md`, `DATA_DICTIONARY.md`,
  `TABLE_S10_DRAFT_V2.md`, `SOURCE_HASHES.csv`.
- Updated main-text / SI sync checklist (`SYNC_CHECKLIST_v2.md`,
  `sync_checklist_v2.csv`).
- A ZIP of the complete v2 delivery.

### 9.2 Visual inspection actually performed

Every exported PNG was opened and read, and the PDFs were rendered and their
text checked — script success and file existence were not treated as evidence.

| checked | result |
|---|---|
| Figure 3 panel (d) nine-parameter labels against values | correct pairing confirmed slot by slot at build time and on the rendered image: `μ_n` top through `r_rad` bottom, argmax drawn under its own label |
| Figure 3 panel (d) axis range | 0 … 2.805, no bar clipped, tick labels present |
| Figure 3 (a)/(b) residual units and direction | `J_j − J_i` in mA cm⁻², symmetric limits, max value labelled |
| Figure 3 (a)/(b) annotation block | positioned in its own space; no overlap with legends or tick labels after the layout was restructured |
| Figure 3 (c) | medians, interquartile whiskers, random baseline line all legible; no p-value present |
| three panels re-rendered after collision fixes | confirmed clean on the second and third inspection passes |
| ECDF | all six curves reach 1; x covers both groups; no truncation; labels render as real text |
| Figure 2 | (a)–(h) letters, axis labels, unit strings, ρ values and percentage labels all legible; (g)/(h) equal width |
| panel letters | (a)–(h) present and correctly placed |
| PDF text | the PDFs carry real, selectable text (Type 42), not outlined glyphs; every string checked above reads correctly in the rendered PDF |
| rendered PDFs | kept in `_pdfcheck/` as evidence |

**Six layout defects were found by this inspection and fixed before delivery**
(three at the PNG stage, three more at the PDF stage): the global footnote
overlapped the bottom panels; the in-panel annotation overlapped the curve
legend; the value labels in panel (c) sat on the interquartile whisker caps; at
journal width the two cases' annotation blocks overprinted each other; the (c)
legend overlapped a value label; and the (d) panel letter collided with (c)'s
`0.94` label.

The last of these had a data consequence worth naming: panel (c)'s y range was
fixed at 1.62, which **clipped the lifetime log-ratio interquartile whisker**
(upper quartile 1.746) and pushed its label out of the axes. The range is now
computed from the data.

None of the six affected any number. To keep them from recurring quietly,
`fig3_sketch_v2.py` now measures the drawn text extents on the real renderer and
**asserts** that the annotations stay inside their halves, that every (c) label is
inside the frame and clear of both the legend and the (d) letter, and that no
whisker is clipped — printing the margins and aborting the build on a
regression, rather than exporting a defective figure.

### 9.3 Stop point

This remains a phase-1 revision, not final five-figure typesetting.
`Style_Sheet_20260928.md` is still missing; this is recorded as-is, the existing
styling was continued, and it is not a blocker for this round. Work stops here
for author and supervisor review, as instructed; the analysis was not extended
beyond the listed items.

---

## Appendix A — reproduction

```
cd E:\project\work1\20261006\figure_revision_phase1_v2\scripts
set PYTHONIOENCODING=utf-8
python _verify_review_findings.py      # verifies the four review findings
python fig3_case_analysis.py           # §1 case analysis + nine-parameter fix
python fig3_pair_analysis_v2.py        # §2, §3 descriptive analysis + ECDF
python fig2_paired_recovery_v2.py      # §6 Figure 2
python fig3_sketch_v2.py               # §1, §5 Figure 3
python si_table_s10_v2.py              # §7 Table S10, M1-M6
python make_data_dictionary.py         # §8 dictionary + input hashes
```

Run order matters only in that `fig3_sketch_v2.py` reads the tables written by
`fig3_case_analysis.py` and `fig3_pair_analysis_v2.py`, and
`make_data_dictionary.py` describes what the others produced.

## Appendix B — open items for author / supervisor

1. **Style sheet.** `Style_Sheet_20260928.md` was not found; final styling
   remains blocked on it.
2. **Figure 3 example rule.** Accept the current maximum-ratio-difference rule
   with panel (d) disclosing the accompanying shared-scale differences, or
   tighten it to pairs that are close in all coordinates.
3. **Table S10 wording.** Approve the updated ranges (all-NN 0.202–0.222;
   closest 1% 0.145 (M1) to 0.189 (M2)) and decide whether to mention the M2
   non-monotonicity in the SI text or only in the delivered table.
4. **Figure 3 inferential statistics.** Confirm that the Wilcoxon and bootstrap
   results should be withdrawn from the paper entirely rather than reported with
   a dependence caveat. Note for this decision: the scan in §F of the sync
   checklist shows the withdrawn statistics were never adopted into either Word
   file, so no Word correction depends on this choice.
5. **Which example pairs the final Figure 3 shows.** Keep the sketch's pairs
   (2890/5067, 500/4560) and rewrite the manuscript's τ_ETL / r_rad sentences
   with ×443 and ×35, or keep the manuscript's examples (1010/2641,
   8271/10258), whose ×280 / ×72 factors already stand. Sync checklist §G sets
   out both branches; this round did not choose.
