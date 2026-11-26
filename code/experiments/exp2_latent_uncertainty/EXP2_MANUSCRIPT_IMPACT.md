# EXP2 MANUSCRIPT IMPACT — 10 Reviewer Questions Answered

Experiment 2 · latent-uncertainty decomposition of the frozen Stage-I VAE-v6 · 2026-08-25
All numbers from forward passes through the **frozen** VAE-v6 on the frozen normalized
test set (N = 15,307), M = 500 latent draws (seed 20260825). Frozen manuscript
`manuscript_stage1_submission_clean.md` **untouched**; this document only *reports* impact.

Reference for the questions below:
- med `f_latent` (latent share of predictive variance) = **0.0005** (mean 0.0011, q95 0.0041)
- med `ratio_σ` (σ_total/σ_current) = **1.0003**; p1–p99 [0.9990, 1.0039]
- 95% coverage: current 0.9475–0.9692 → moment-matched Δ ≤ 0.0002, MC mixture Δ ≤ 0.004
- ρ_total − ρ_current ≈ **0.0000** (mean); point Pearson Δ = **+0.000009**
- encoder posterior std exp(0.5·z_log_var) ≈ **0.0017–0.0039** (near-point), KL = 51.356 nats

---

## Q1. Is "probabilistic parameter inversion" still defensible?

**YES, with a wording reframe.** The pipeline is genuinely probabilistic: a Gaussian
parameter head conditioned on a stochastic latent produces a model-implied predictive
distribution over parameters. What Experiment 2 shows is *where* the variance lives: in
the head, not in the latent. So the defensible sentence is "the model yields a
probabilistic (Gaussian-head) predictive distribution over parameters, whose variance is
supplied almost entirely by the heteroscedastic head" — and the *indefensible* version is
anything implying "latent sampling is the source of the uncertainty." The machinery is
probabilistic; the variance source is the head.

## Q2. Does latent propagation change any reported σ value?

**No, numerically.** `σ_total = √(V_head + V_latent)` differs from the manuscript's
`σ_θ(z_mean)` by median factor 1.0003 (i.e. +0.03%), with p99 ≤ 1.0039 (+0.4%). For the
purpose of any table, figure, coverage interval, or ranking in the manuscript, the two are
indistinguishable to four decimal places. No reported number needs correcting.

## Q3. Where does the σ–error ranking information come from — head or latent?

**From the head's σ output, overwhelmingly.** ρ_total (using latent-propagated σ) equals
ρ_current (using σ_θ(z_mean)) to ~0.0000 mean. The latent-mean-only ranker ρ_latent
(Spearman between `μ_total`-based |error| and σ) drops to ≈ 0.1–0.4 and is even negative
for tau_ETL (−0.13) and rad_c (−0.20). The manuscript's mean ρ(σ, |err|) = 0.4283 is a
property of the Gaussian head and survives latent propagation unchanged.

## Q4. Does latent propagation improve calibration?

**No — and it does not degrade it either.** Moment-matched coverage changes by ≤ 0.0002
at all parameters and levels; the MC-mixture (fully accounting for the latent mixture's
non-Gaussianity) is ≤ 0.004 lower. There is no calibration gain to claim from "sampling
the latent" — the distribution is already essentially the head's.

## Q5. Should the manuscript's calibration numbers be replaced?

**No.** The reported 95% coverage band [0.9464, 0.9692] reproduces exactly (Phase 0) and
the latent-propagated numbers coincide to ≤ 0.0002. Replacing them would change nothing
and would risk confusing the reader into thinking latent propagation matters. Keep the
numbers; if desired, add a one-sentence SI note (see §24 candidate).

## Q6. Should the VAE latent be claimed as a main uncertainty source?

**NO.** The data directly contradict any such claim: the latent contributes a median
0.05% of predictive variance (q95 0.4%). "Stochastic encoding → predictive uncertainty"
framings in the abstract/discussion must be removed or reframed as "the latent's
contribution to predictive variance is minor (~0.1%); the Gaussian head supplies the
predictive uncertainty." This is the single concrete manuscript action.

## Q7. Does this reinforce Experiment 1's architecture-neutral interpretation?

**YES.** Experiment 1 showed the VAE adds no robust accuracy/calibration advantage over a
deterministic autoencoder. Experiment 2 shows that even the *uncertainty* the VAE
produces is not coming from its stochastic latent — it is the deterministic head's
heteroscedastic output. The two results jointly support: the VAE's distinguishing
component (stochastic latent sampling) is neither needed for accuracy nor responsible for
the reported uncertainty. "The reported uncertainty is Gaussian-head-supplied" is
consistent with, and strengthens, the EXP1 conclusion that the VAE latent is not the
architectural driver of the results.

## Q8. Does the frozen model support a full joint (9-parameter) predictive posterior?

**No, and none is claimed.** `V_total` is computed per parameter; the decomposition
captures each parameter's marginal predictive variance. A full joint posterior over all 9
parameters would require propagating the latent covariance through the head — the
latent-induced covariance documented in §10/FigG exists but contributes negligibly to
total variance. Any manuscript text implying a joint credible region over parameters is
not supported by the frozen evaluation (and was not, before this experiment).

## Q9. How should the latent-induced pairwise covariance be handled?

**Document descriptively only.** `latent_induced_pairwise_covariance.csv` / FigG record
the median conditional correlation structure of the latent function (e.g. mu_n–mu_p 0.974,
tau_n–tau_p 0.989, Nc–Nv 0.982; mu_n–tau_n −0.696; rad_c–tau_n −0.217). Because V_latent is
~0.1% of V_total, this structure does not enter the total predictive variance in any
material way. If reported, it must be labeled "conditional structure of the latent
function, descriptive only; latent share of predictive variance ≈ 0.1%."

## Q10. Is any scientific conclusion in the manuscript invalidated?

**No.** Recoverability hierarchy (Pearson 0.8069 reproduced exactly; latent averaging Δ
+0.000009), calibration band [0.9464, 0.9692], σ–error ranking (ρ mean 0.4283), and all
point-prediction claims are unchanged by latent propagation. The only changes required
are **wording** (Q1/Q6) and optional **documentation** (Q5/Q9). Verdict: **no scientific
conclusion is invalidated; G4 = YES.**

---

## §24 — Reviewer-facing wording candidates (Outcome C)

Outcome C: **Gaussian head dominates; latent contribution minor.**

### C1. Abstract-level (one sentence, replacing latent-driven-uncertainty framing)

> "The reported predictive uncertainty over parameters is supplied primarily by the
> heteroscedastic Gaussian parameter head; stochastic sampling of the VAE latent
> distribution contributes only a minor additional predictive variance (~0.1% of the
> total), so the point and interval evaluation at the latent mean is numerically
> representative of the full predictive distribution."

### C2. Methods-level (one sentence, after the σ definition)

> "σ for each parameter is the Gaussian head's conditional standard deviation evaluated
> at the latent mean; a latent-uncertainty decomposition confirms that sampling the
> encoder posterior (posterior width exp(½·log σ_z²) ≈ 0.002–0.004) adds <0.15% of the
> predictive variance, and that the resulting calibration, error ranking, and point
> predictions coincide with the latent-mean evaluation to ≤0.0002."

### C3. Discussion/limitations (one paragraph, for reviewers)

> "The model-implied predictive distribution over parameters is Gaussian-head-dominated:
> a Monte-Carlo decomposition of the frozen Stage-I VAE-v6 shows the latent-induced
> predictive variance is a median 0.05% (q95 0.4%) of the total, the widening of the
> predictive standard deviation from latent propagation is 0.03% (median), and latent
> propagation leaves 95% coverage (Δ ≤ 0.0002), σ–error ranking (Δ ≈ 0.0000), and point
> recovery (Δ Pearson +0.00001) unchanged. These are properties of the frozen model's own
> outputs — a model-implied predictive distribution, not a Bayesian posterior. They
> indicate that the reported predictive uncertainty is carried by the Gaussian parameter
> head, with the stochastic latent contributing a minor additional variance, and that
> evaluating the predictive distribution at the latent mean is representative to the
> reported precision."

**Usage note.** Only C3 is a *limitation-grade* statement (it exposes the mechanism);
C1/C2 are *strength-of-claim* corrections. If the journal allows only one edit, apply C1
in the abstract and C2 in Methods; C3 is for the response letter or SI.
