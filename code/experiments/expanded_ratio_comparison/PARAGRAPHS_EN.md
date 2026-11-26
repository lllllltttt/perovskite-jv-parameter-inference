# Candidate English paragraphs — for main text / SI (NOT written into any Word file)

Status: draft text only. Nothing in this file has been inserted into the manuscript or the
Supplementary Information; both were left untouched in this round. Every number below is taken
from `RESULTS.md` / `out/metrics/*` (v2, the corrected evaluation) and can be regenerated from
`out/predictions/*.csv`.

Terminology used consistently: "shared-scale coordinates" (a_mu, a_tau, a_D) and "ratio
coordinates" (r_mu, r_tau, r_D); "original-range arm" (q ∈ 0.2–5) and "expanded-range arm"
(q ∈ 0.05–20).

---

## 1. Methods — matched comparison design

> To separate the effect of the ratio prior from that of the shared-scale prior, we repeated the
> training protocol on two data sets of identical size but different ratio support. Both arms
> contained 24,274 samples: the expanded arm used every delivered row generated with all three
> electron–hole ratios sampled uniformly between 0.05 and 20, while the original arm used a seeded
> subsample of the same size drawn from the original 0.2–5 database. The shared-scale priors,
> interface-lifetime and radiative-recombination priors, network architecture, loss, optimiser,
> batch size, epoch cap and early-stopping rule were left unchanged. Each arm was split once, with
> a fixed seed, into 16,992 training, 3,641 validation and 3,641 test rows; the split was shared by
> all five training seeds (20261021–20261025), and the two arms were trained from scratch rather
> than compared against the published model, whose scalers were fitted on the full retained
> database. Parameter and current normalisation statistics were fitted on each arm's own training
> rows only and applied unchanged to validation and test data.

## 2. Methods — evaluation protocol

> Point predictions were taken from the deterministic path used throughout this work: the encoder
> latent mean passed through the parameter head, with no latent sampling. For every evaluation the
> input current and the output parameter vector were normalised and de-normalised with the scalers
> of the arm that the model was trained on; the test arm supplied the rows, the ground truth and
> the baselines. Metrics were computed in the physical log10 parameter space, using the
> shared-scale and ratio coordinates a = (log10 p_n + log10 p_p)/2 and r = log10 p_n − log10 p_p
> for each of the mobility, lifetime and density pairs, as well as the nine individual parameters.
> We report Pearson correlation, mean absolute error, root-mean-square error, R² with respect to
> the test-set mean and Skill_MSE with respect to a constant predictor equal to the test arm's
> training-set mean. Two comparisons are given: each model on its own test distribution, and both
> models on the same test set with a common baseline. The five seeds are replicate trainings on one
> data set, so we report per-seed values and mean ± sample SD and did not add significance tests.

## 3. Results — widening the ratio prior did not reduce ratio error

> Widening the ratio support by roughly a factor of four left the ratio coordinates poorly
> recovered in both arms. On its own test distribution, the expanded-range model reached a
> Skill_MSE of 0.141 ± 0.010 for r_mu, 0.126 ± 0.034 for r_tau and 0.089 ± 0.004 for r_D, compared
> with 0.141 ± 0.011, 0.073 ± 0.012 and 0.049 ± 0.010 for the original-range model. The
> corresponding RMSE in log10 units increased for all three coordinates (0.380 versus 0.299, 0.381
> versus 0.307 and 0.405 versus 0.322), as did the MAE. For the shared-scale coordinates the
> changes were small and mixed: a_mu improved (Skill 0.780 versus 0.764; RMSE 0.409 versus 0.426
> log10 units) while a_tau and a_D deteriorated slightly (Skill 0.724 versus 0.742 and 0.654 versus
> 0.703). The gap between the shared scales and the ratios remains large in every family — 0.64
> versus 0.62 for mobility, 0.60 versus 0.67 for lifetime and 0.57 versus 0.65 for density
> (expanded versus original) — but it narrowed for lifetime and density and widened slightly for
> mobility. That narrowing did not come from smaller ratio errors, which rose in all three
> families; it came from a lower shared-scale Skill in the lifetime and density families.

## 4. Results — the apparent ratio Skill gain is a baseline-variance effect

> The Skill_MSE of r_tau and r_D was higher in the expanded arm, but this reflects the change in
> the spread of the truth rather than a smaller prediction error. Because the ratios were sampled
> uniformly on a linear scale over a fourfold wider interval, the training-mean baseline MSE on
> the expanded test set is 1.62–1.65 times its original-range value for all three ratio
> coordinates, while the model RMSE is 1.24–1.27 times larger. Writing Skill = 1 − MSE/MSE_baseline,
> the numerator and denominator grew by nearly the same factor for r_mu, leaving its Skill
> unchanged (0.141 versus 0.141), and the denominator grew slightly faster for r_tau and r_D. The
> physical-log10 error, which is the quantity relevant to inverse design, increased everywhere.
> For the shared-scale coordinates the baseline MSE is essentially unchanged between the two test
> sets, so their small Skill differences do reflect changes in absolute error.

## 5. Results — common-test comparison

> On each common test set, both models were scored against the same baseline, computed from that
> test arm's training data. On the original-range test the original-range model was better on all
> six coordinates in all five seeds (Skill_MSE differences, expanded minus original, between
> −0.07 and −2.48); on the expanded-range test the expanded-range model was better on all six
> (+0.06 to +1.65). Read by coordinate family, the shared scales transfer between the two test
> distributions: the expanded-range model keeps a positive Skill on the original test (0.58–0.67)
> and the original-range model on the expanded test (0.45–0.67), 68–92 % of their own-distribution
> values. The ratio coordinates do not transfer: every cross-arm value is far below the
> constant-predictor baseline (−1.11 to −2.43). The two directions differ in kind. When the
> original-range model is evaluated on the expanded test, 75–76 % of its ratio targets lie outside
> its training support; when the expanded-range model is evaluated on the original test, all ratio
> targets lie inside its support (0.05–20), but only about a quarter of its training rows do.
> These cells therefore quantify specialisation to the training prior, not a like-for-like measure
> of recovery quality, and we do not attach a single out-of-distribution label to all six
> coordinates.

## 6. SI — data provenance and acceptance

> The expanded batch was generated with the acquisition workflow used for the original database,
> with only the sampling bounds of the three ratio variables changed. Of the 50,000 planned
> Latin-hypercube samples, 49,999 MAT files are present; 24,274 rows passed the four acceptance
> rules of the original data processing and were exported in the delivered table. One MAT file is
> missing, and its Sample_ID cannot be recovered from the delivered files; for the remaining
> 25,725 samples the reason for absence is not recorded, so they are neither counted as accepted
> nor classified as rejected, and no sample was regenerated. Re-applying the four rules (positive
> first current, at least one negative change in the sign of the current across adjacent voltages,
> finite currents, and adjacent current increments no larger than 0.2 mA cm⁻²) rejects no row in
> either delivered table, confirming that both exports are post-filter. The delivered tables
> contain no exact duplicate parameter vectors or current curves, within or across batches, so
> exact-count splitting without group assignment cannot leak a sample between training and test
> partitions.

## 7. SI — how the ratio prior differs between the arms

> Both batches sample a shared scale g for each parameter pair from the same log-uniform prior and
> construct the partners as p_n = g√q and p_p = g/√q; only the bounds of the linear-uniform q
> prior change between the arms. Widening q therefore widens the range that each individual
> parameter can take around g by a factor of four, and it also changes the induced distribution of
> log10 q: because the ratios were sampled uniformly on a linear scale in both batches, the median
> log10 q moves from about 0.41 to about 1.00 (+0.59 decades), the mode moves from the old upper
> bound to the new one, and the added low-ratio tail is thin (below 0.8 % of rows have q < 0.2).
> In the expanded batch, 74.2–75.4 % of rows have a given ratio above 5, 23.8–25.0 % fall inside
> the old 0.2–5 window, and only 1.47 % have all three ratios inside the old three-ratio box. The
> two arms are therefore not nested in any equal-weighted sense, and the equal-volume design
> necessarily reduces the density of samples inside the old window. All reported distributions are
> post-filter and are the sampled priors multiplied by the shared acceptance function; the
> pre-filter density cannot be reconstructed from the delivered files.

## 8. Limitations paragraph

> Three aspects of the design bound the interpretation. First, widening the ratio range induces
> different parameter scaler ranges (per-parameter log10 spans of 3.00–7.97 decades versus
> 3.00–7.65 decades across the nine parameters), so the two arms differ in normalisation and in
> the relative weighting of the nine likelihood terms; the comparison therefore concerns the
> re-specified training distribution as a whole rather than an isolated change of one sampling
> bound. Second, with equal data volume the density of samples inside the old ratio window falls
> by roughly a factor of four, and on identical rows whose matching ratio lies inside that window
> the expanded-range model is still worse on all three ratio coordinates (by 0.23–0.26 log10),
> while the two models are tied on two of the three shared scales. This degradation cannot be
> attributed to prior width alone with the present design. Third, both arms stopped early by the
> same rule but at different epochs (original 401–585, expanded 317–503), so the number of
> parameter updates is not exactly matched. No nearest-neighbour confidence interval or bootstrap
> resampling was performed in this comparison.

---

## Wording cautions applied

- No sentence claims that the J–V curves contain no ratio information, and none claims universal
  non-identifiability; §3 is limited to the observed setting (data volume, sampling, filtering,
  architecture, training rules).
- §4 attributes the ratio Skill increase to baseline variance while stating the raw RMSE increase
  alongside it; it does not call the increase a "false improvement" in isolation.
- §5 reports both Skill and absolute error, and reads the cross-arm results per coordinate family;
  it no longer labels all six coordinates out-of-distribution, and it separates "the test
  distribution differs" from "the target lies outside the training support".
- The claim that the shared-scale/ratio gap "did not close" is not used; §3 states that the gap
  remains large while naming the families in which it narrowed, and does not rest on a difference
  of raw RMSE between coordinates with different natural spreads.
- §6 keeps the three sample counts apart (50,000 planned, 49,999 MAT files, 24,274 exported rows)
  and does not describe the 49,999 as accepted.
- The published model is not used as a control; §1 states why.
- No causal language ("because of the ratio range") is used where the scalers and density change
  together with the prior.
