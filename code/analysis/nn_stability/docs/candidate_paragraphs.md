# Candidate English paragraphs (not inserted)

Status: draft text for review. The manuscript and SI were not modified.

Suggested insertion points in `Manuscript_20261007_HC1015_revised.docx`:

- **Methods** — end of §"Curve similarity and parameter ambiguity" (after
  P0076), as a new sub-paragraph or subsection.
- **Results** — after P0025, before the metric-sensitivity paragraph P0026.
- **Discussion/Limitations** — after P0045.

Every number below is taken from
`out/stability/summary.csv`, `interpretation_by_family.csv`,
`interpretation_all_three.csv`, `closest01_volatility.csv` and
`first500_vs_all1000.csv`. Percentiles are the 2.5th and 97.5th percentiles
across 1,000 replicates and are **descriptive resampling percentile ranges**,
not confidence intervals.

---

## Methods

**Random-subset stability with duplicate collapse.** To assess how strongly the
pairwise summaries depend on the composition of the test set, the
nearest-neighbour construction was repeated on 1,000 random subsets of the
15,307 test curves. For replicate *k*, 15,307 indices were drawn with
replacement using `numpy.random.default_rng([20261019, k])` and collapsed to
distinct original curves; the directed nearest-neighbour graph was then rebuilt
on that subset with the same rule as above (Euclidean distance over the 131
normalized currents, self-distance excluded, ties broken by the lowest subset
index), and directed links were converted to ordered (min, max) keys and
deduplicated. Because of duplicate collapse the number of distinct curves is not
fixed at 15,307; the realized value was recorded for every replicate.
Random-pair baselines were redrawn from the same subset with the archived rule,
and the six paired coordinates were summarized over all pairs and over the
closest 10%, 5%, 1%, 0.5% and 0.1% of pairs with
*k* = max(1, round(*n*<sub>pairs</sub> × *f*)). All 1,000 replicates completed
without failure. Medians and 2.5th–97.5th percentiles across replicates are
reported as descriptive resampling percentile ranges; they are not confidence
intervals for the full-test-set statistic, and the replicates are not
independent experimental samples.

---

## Results

**Paragraph 1 — overall stability.** To test the dependence of these summaries
on the particular test set, the analysis was repeated on 1,000 random subsets
with duplicate collapse (Methods). A subset contained a median of 9,674 distinct
curves (2.5th–97.5th percentile 9,597–9,750), close to the 15,307(1 − e<sup>−1</sup>)
≈ 9,678 expected under sampling with replacement, and yielded a median of 7,089
unique undirected pairs (7,016–7,155). Over all pairs, the replicate medians of
the normalized coordinate differences were 0.366 (0.358–0.376) and 0.826
(0.801–0.848) for the mobility shared scale and log-ratio, 0.327 (0.319–0.337)
and 0.869 (0.848–0.893) for bulk lifetime, and 0.427 (0.416–0.439) and 0.953
(0.928–0.978) for density of states. The shared-scale median was below the
corresponding ratio median in all three families in every replicate at the
all-pair, closest-10%, closest-5% and closest-1% tiers, and in 99.5% of
replicates at closest 0.5%. The full-sample ratio values (0.810, 0.861 and
0.944) lie within these percentile ranges, whereas the full-sample shared-scale
values (0.353, 0.312 and 0.404) lie below the 2.5th percentile; the replicate
medians are higher by 0.013–0.023 for the shared scales and 0.008–0.016 for the
ratios. This upward offset is consistent with each subset offering fewer
potential neighbours, so that nearest-neighbour pairs are farther apart in
current space: the raw shared-scale differences increase by 4–6%, the raw ratio
differences by less than 2%, and the random-pair baselines change by less than
0.5%.

**Paragraph 2 — closest 0.1%.** At the closest 0.1% tier, duplicate collapse
leaves seven pairs in every replicate (12–14 distinct curves, at most three
pairs per curve). The six normalized medians then vary widely: the
2.5th–97.5th percentile ranges are 0.104–0.458 (mobility shared scale),
0.145–1.761 (mobility ratio), 0.064–0.751 (lifetime shared scale), 0.197–1.021
(lifetime ratio), 0.089–0.546 (density-of-states shared scale) and 0.575–1.399
(density-of-states ratio). In this tier the shared-scale median remains below
the ratio median in 79.3%, 72.0% and 100% of replicates for mobility, bulk
lifetime and density of states, respectively, but in all three families
simultaneously in only 58.9%. The full-sample lifetime shared-scale value of
0.118 lies well below the replicate median of 0.280, reflecting the change from
11 full-sample pairs to seven subset pairs. These tier-specific values describe
small pair sets and are not stable properties of the sampling distribution.

**Optional sentence for the existing Fig. 3 paragraph (P0025).** Repeating the
comparison on 1,000 random subsets leaves the same ordering at the all-pair and
closest-1% tiers in every replicate, whereas the closest-0.1% ordering varies
across subsets (new stability figure).

---

## Discussion / Limitations

The random-subset analysis addresses only one source of variability. Resampling
the test curves changes which curves can become neighbours, but every subset is
scored with the same frozen model and scalers and is drawn from the same
simulated sampling distribution. The percentile ranges therefore describe
sensitivity to test-set composition; they do not include uncertainty from model
fitting, scaler estimation, simulation error or measurement noise, and they are
not a confidence interval for the full-test-set statistic. Because the subsets
share most of their curves, the 1,000 replicates are not independent
experimental samples and no significance test is attached. At the closest 0.1%
tier the pair count is small (seven), and the ordering of shared-scale and
ratio differences is not stable across subsets; such tier values should be read
as descriptions of particular small pair sets. Nor do they strengthen the
neighbour comparisons into evidence of strict non-uniqueness or a universal
identifiability limit. These results complement rather than replace a bootstrap
uncertainty analysis, which addresses a different question and requires a
separately justified resampling methodology.

---

## Notes for the reviewer

- The analysis name used throughout is "random-subset stability analysis with
  duplicate collapse".
- The closest-0.1% result is the main caveat: with seven pairs, the six
  normalized medians span ranges of roughly a factor of 2–12, and the
  shared-scale-below-ratio ordering holds for all three families in only 58.9%
  of replicates.
- The all-pair shared-scale values lie below the 2.5th percentile of the
  replicate distribution because each subset has about 9,674 rather than 15,307
  curves; the full-sample comparison and the subset comparison answer slightly
  different questions and should not be presented as interchangeable.
- No p-values are reported and none should be derived from these percentiles.
- 中文说明：本轮结果是描述性稳定性分析，不能替代导师要求的 bootstrap 置信区间；
  后者所需的重采样方案仍待方法学论证后再执行。
