# FINAL FIGURE CAPTIONS — VAE-v6 Stage-I manuscript

Date: 2026-08-23 · Wording is frozen-consistent with
`manuscript_stage1_routeA_final_precision.md` (Section numbers as cited).
Captions are submission-ready; remove any bracketed production notes before
typesetting.

---

## Figure 1

**Workflow of the simulation-informed variational autoencoder (VAE) for
probabilistic parameter inversion.** (a) Device stack of the p–i–n perovskite
solar cell studied in this work: FTO / NiOₓ (hole-transport layer, HTL) /
perovskite absorber / C₆₀ (electron-transport layer, ETL) / Ag. Nine device
parameters are inverted: electron and hole mobility (μₙ, μₚ), electron and
hole bulk lifetimes (τₙ, τₚ), effective conduction- and valence-band density
of states (Nc, Nv), and the carrier lifetimes of the ETL and HTL (τ_ETL,
τ_HTL), together with the radiative recombination coefficient rad_c. (b) The
drift–diffusion COMSOL model generates synthetic current–voltage (J–V) curves
from a Latin-hypercube sampling prior in which the bulk mobility, lifetime,
and density-of-states pairs are drawn from shared average-and-ratio latent
variables (a physically constrained prior whose induced correlation structure
the paper explicitly accounts for). (c) Dataset construction: 200,000
candidate samples → 102,046 retained (51.0%) after the physical-plausibility
filter → split 71,432 / 15,307 / 15,307 into train / validation / test (seed
42). (d) Inverse workflow: a standard 0–1.3 V J–V curve (131 points) is mapped
by the encoder to a 9-dimensional probabilistic latent code z, from which a
decoder reconstructs the curve and a Gaussian parameter head predicts the nine
parameter means together with per-parameter predictive scales.

## Figure 2

**VAE-v6 architecture and decoder reconstruction.** (a) Architecture of the
probabilistic inversion model: an encoder (131 → 128 → 64, ReLU) outputs the
posterior mean and log-variance of a 9-dimensional latent code z, with a
reparametrized sample z = μz + σz ⊙ ε; the decoder (9 → 64 → 128 → 131,
sigmoid) reconstructs the normalized J–V curve, and a Gaussian parameter head
(9 → 64 → 32) outputs the parameter means μθ and raw scales, with the fixed
predictive scale σθ = clip(softplus(σraw) + 0.01, 0.01, 1.0). The model is
trained with the frozen objective L = L_recon + 10⁻³·L_KL + L_NLL; the dashed
decorations mark the two uncertainty terms. No cycle-consistency branch is
included (discussed in Section 4.1). (b) Representative decoder
reconstructions from the frozen chain: three test samples selected by
observable power-conversion-efficiency (PCE) terciles only (indices 4708 /
193 / 12940; PCE 8.4% / 16.1% / 20.6%). Solid lines are the target curves,
dashed lines the decoder output in physical current units (mA cm⁻²). The
decoder reproduces the full photovoltaic operating region; the extreme
reverse-bias tail of the highest-PCE sample leaves the frame. (c) Test-set
distribution of the normalized reconstruction mean-squared error
(N = 15,307): mean 1.21 × 10⁻⁵, median 2.97 × 10⁻⁶.

## Figure 3

**Point recovery and the sensitivity–recoverability link.** (a) Parity plots
of true vs predicted parameters on the test set (normalized log10 space,
shared [0,1] axes, y = x dashed, Pearson r annotated): bulk transport and
lifetime parameters are recovered with high accuracy (r = 0.88–0.92), the
interface lifetimes and radiative coefficient only moderately (r = 0.56–0.72).
(b) J–V linear sensitivity S_log (the parameter-averaged absolute
log10-space Pearson correlation between each parameter and the current at each
voltage point, recomputed on the test set; Section 3.4) vs recoverability r.
The correlation is positive but **not significant** (Spearman ρ = 0.53,
p = 0.14); no significance claim is made.

## Figure 4

**Predictive uncertainty and calibration in the clean simulation domain.**
(a) Empirical vs nominal predictive-interval coverage at the 50 / 80 / 90 /
95% levels on the clean in-domain test set (N = 15,307; y = x reference): the
intervals are approximately calibrated. (b) Parameter-wise empirical coverage
at the nominal 95% level (range 0.946–0.969 across the nine parameters;
0.95 reference). (c) Spearman association between the predicted
Gaussian-head predictive scale σθ and the absolute point-prediction error per
parameter: positive for all nine parameters (mean ρ̄ = 0.428). All quantities
use the fixed predictive scale σθ = clip(softplus(σraw) + 0.01, 0.01, 1.0);
the intervals are predictive intervals (not confidence intervals), evaluated
in the clean simulation domain.

## Figure 5

**Inverse ambiguity revealed by nearest-neighbor J–V collisions within the
predefined sampling prior.** (a) Relationship between normalized J–V proximity
and parameter-space proximity for the 7,666 deduplicated nearest-neighbor
pairs of the test set (dJ log10-scaled): the coupling is weak (Spearman
ρ_s = 0.158, Pearson r = 0.079), i.e. near-identical curves do not imply
near-identical parameters. (b) Median parameter distance for random pairs
(0.349), all nearest-neighbor pairs (0.200), and increasingly close J–V tiers
(closest 1% / 0.5% / 0.1%: 0.144 / 0.134 / 0.102), in normalized log10
parameter space. (c) Parameter-wise ambiguity within the closest 1% of pairs
(n = 77; median |Δθ| per parameter, normalized log10 space): the ambiguity
concentrates in the interface carrier lifetimes (τ_ETL, τ_HTL), the electron
mobility, and the radiative coefficient (r_rad; values as in Table 5).
(d) Two representative collision pairs showing extremely similar J–V
responses despite substantial changes in individual inferred parameters:
τ_ETL 0.377 → 0.988 at d_J = 9.3 × 10⁻⁵, and r_rad 0.712 → 0.094 at
d_J = 2.0 × 10⁻⁴ (curve 1 solid, curve 2 dashed). All distances are quoted in
the normalized log10 space of the predefined sampling prior; these are
observational descriptions of the model's input–output structure within this
prior, not causal claims about the underlying physics, and no claim about the
resolution of a specific measurement is made.

## Figure 6

**Robustness to synthetic current perturbations and unbiased forward
validation.** (a) Point-prediction accuracy (Pearson r) vs the level of
additive Gaussian current perturbation applied to the input J–V curves,
expressed as a percentage of |Jsc| (0 / 0.2 / 0.5 / 1 / 2%; per-curve noise
standard deviation, 30 Monte-Carlo realizations per level). Group means are
shown for the bulk (6 parameters), interface (2), and radiative (1) groups,
together with the overall mean over the nine parameters (black, hollow
diamonds): accuracy degrades only moderately and the recoverability hierarchy
of Fig. 3 is preserved. This is robustness to synthetic perturbation, not
validation under experimental noise. (b) Empirical 95% predictive-interval
coverage at the same perturbation levels (dashed line: nominal 0.95); coverage
declines at higher noise. The inset shows the Gaussian-head mean predictive
scale σθ, which remains nearly unchanged as the input noise increases (0.1337 →
0.1323 across levels) — the predictive intervals characterize uncertainty
within the clean simulation domain and do not adapt to measurement noise.
(c) Unbiased COMSOL forward validation: all 45 samples (selected without
parameter-error filtering) were re-simulated from their inferred parameter
combinations in the original drift–diffusion simulator and compared with the
targets; individual per-sample values are overlaid on the boxes. The vertical
axis is logarithmic. Median RMSE 2.69 mA cm⁻² over the full curve,
0.455 mA cm⁻² in the photovoltaic operating region (0–1.0 V), and
5.19 mA cm⁻² in high forward bias (> 1.0 V): forward agreement is
substantially better in the operating region than in the > 1.0 V tail. The
true-parameter control reproduces the targets exactly (median RMSE
< 10⁻⁶ mA cm⁻²), confirming the pipeline. (d) Device-metric preservation
across the same 45-sample cohort: each of the four panels shows the
distribution of the absolute forward error for one metric in its native unit —
|ΔJsc| (mA cm⁻²), |ΔVoc| (V), |ΔFF| (dimensionless), |ΔPCE| (percentage
points) — with every available per-sample value plotted as an individual point
over a compact boxplot (median line). |ΔJsc| uses all 45 samples; |ΔVoc|,
|ΔFF|, and |ΔPCE| use the 44 samples for which a simulated value was recorded
(one sample's simulated Voc/FF/PCE are absent from the frozen record). Median
|ΔJsc| = 0.112 mA cm⁻², |ΔVoc| = 0.030 V, |ΔFF| = 0.014 (dimensionless),
|ΔPCE| = 0.471 percentage points. Because the metrics carry different units,
each panel has its own independent scale; the panels are not on a common
quantitative scale and the metrics are not directly comparable across
panels — the actual values are given explicitly.

---

## Supplementary captions

**Figure S3. Decoder–COMSOL cycle-consistency audit (supports Section 4.1).**
(a) Representative cases for the 45-sample unbiased cohort ordered by the
cycle gap (the RMSE between the decoder reconstruction and the COMSOL
re-simulation of the inferred parameters): lowest, Q25, median, Q75, highest
cycle gap, plus (f) the true-parameter COMSOL control. The decoder
reconstructs the target curves well, while the physical re-simulation of the
inferred parameters degrades mainly in high forward bias; the control shows
the drift–diffusion forward pass is exact. (b) Voltage-resolved RMSE across
the 45 samples: decoder vs target, COMSOL(predicted parameters) vs target, and
decoder vs COMSOL(predicted parameters), with the 1%-of-Jsc measurement-noise
floor (0.21 mA cm⁻²) for reference; the vertical dashed–dotted line marks
1.0 V. (c) Cycle-gap statistics: full-gap distribution (median 2.56 mA cm⁻²);
the region-paired boxplot shows the gap concentrates in the > 1.0 V region
(median 5.30 vs 0.47 mA cm⁻² in 0–1.0 V); no significant association with the
parameter error or with the predictive scale is found. This discrepancy
reflects the absence of an explicit physical cycle-consistency constraint in
the current architecture.

**Figure S_noise. Full-parameter noise-robustness detail (supports Fig. 6a/b).**
(a) Pearson r vs input noise level for all nine parameters individually
(bulk: μₙ, μₚ, τₙ, τₚ, Nc, Nv; interface: τ_ETL, τ_HTL; radiative: rad_c);
(b) 95% empirical coverage vs noise level for all nine parameters (0.95
reference); (c) per-parameter mean predictive scale σθ across noise levels —
the scale is flat for every parameter, i.e. the model does not adapt its
intervals to measurement noise. Color code as in (a).

**Figure S6 (AE baseline comparison) — pending source data; see
`FINAL_FIGURE_QC.md` §S6.** Deterministic autoencoder baselines (AE-v1,
AE-v2) vs the probabilistic VAE-v6: point-accuracy comparison, showing the
probabilistic model retains competitive accuracy while providing calibrated
predictive scales. *Not produced yet: the AE-v1/AE-v2 test-set accuracy lives
only on the training cluster.*
