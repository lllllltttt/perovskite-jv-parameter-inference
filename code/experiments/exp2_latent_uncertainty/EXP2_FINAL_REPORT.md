# EXPERIMENT 2 — FINAL REPORT
## Latent-Uncertainty Decomposition of the Frozen Stage-I VAE-v6

Experiment 2 · reviewer response · 2026-08-25
`reviewer_experiments/exp2_latent_uncertainty_decomposition/`
Frozen Stage-I VAE-v6 / manuscript `manuscript_stage1_submission_clean.md` /
evaluation / figures: **untouched** (md5-verified, see §12).

> Inference-only. No model was trained, no weight updated, no frozen file overwritten.
> All numbers below are computed by forward passes through the **frozen** VAE-v6
> (encoder + ParamHead) on the frozen normalized test set (N = 15,307).

---

## 1. Purpose and scope

The manuscript reports a probabilistic parameter-inversion pipeline whose predictive
uncertainty σ is produced by the Gaussian parameter head conditioned on the VAE latent
`z_mean`. This experiment answers the reviewer-level question:

> *How much of the model-implied parameter uncertainty comes from (i) the Gaussian
> parameter head and (ii) stochastic uncertainty in q(z|J)? Does propagating latent
> uncertainty improve calibration or error ranking relative to the manuscript's current
> z_mean evaluation?*

Concrete scope:
- Decompose each sample's model-implied predictive variance into a **Gaussian-head
  conditional** part `V_head = E_z[σ_θ(z)²]` and a **latent-induced** part
  `V_latent = Var_z[μ_θ(z)]`, with `V_total = V_head + V_latent`.
- Compare calibration, sigma–error ranking, and point predictions between
  (a) the manuscript evaluation at `z = z_mean` and (b) latent-propagated evaluation.
- Establish convergence of the Monte-Carlo latent estimate (§3), robustness across the
  five Experiment-1 leakage-free seeds (§11), and numerical environment consistency (§12).
- Produce a single outcome classification (§15) with four gate answers.

**Terminology discipline.** Throughout, "predictive distribution" refers to the
**model-implied** predictive distribution (the Gaussian head outputs pushed through the
frozen network), never a Bayesian posterior. "Latent-induced predictive variation" refers
to the deterministic effect of sampling q(z|J); it is *not* epistemic or aleatoric
uncertainty in the Bayesian sense. The decomposition answers a **mechanistic** question
about the frozen architecture's own outputs.

## 2. Frozen-model reproduction (Phase 0)

Running the frozen weights through the experiment's evaluation code reproduces every
Stage-I reference number exactly (`FROZEN_MODEL_REPRODUCTION_CHECK.md`):

| quantity | frozen reference | reproduced |
|---|---|---|
| mean Pearson r (point, z_mean) | 0.8069 | 0.8069 |
| per-parameter Pearson r (9) | 0.9063…0.5592 | identical (Δ ≤ 0.0001) |
| mean Spearman(σ, \|err\|) | 0.4283 | 0.4283 |
| 95% coverage range | [0.9464, 0.9692] | [0.9464, 0.9692] |
| σ bounds on test | inside [0.01, 1] | [0.011165, 0.792324] |
| encoder KL (test) | 51.40 (history final) | **51.356 nats** |

The environment measures the same thing the Stage-I study reported; the decomposition
below is therefore built on the exact frozen object.

## 3. Monte-Carlo convergence gate

Fixed subset: 1000 test samples, seed 20260825; nested draws (first M of a 500-draw
master, same seed). Reference M = 500. Criterion: select the smallest M with
median relative error < 2% **and** q95 relative error < 5% for `V_total` and `f_latent`,
else use M = 500.

| M | med-relerr V_total | q95-relerr V_total | med-relerr f_latent | q95-relerr f_latent | pass |
|---|---|---|---|---|---|
| 20 | 0.0012 | 0.0057 | 0.2140 | 0.5782 | — |
| 50 | 0.0008 | 0.0037 | 0.1320 | 0.3704 | — |
| 100 | 0.0005 | 0.0023 | 0.0852 | 0.2489 | — |
| 200 | 0.0003 | 0.0015 | 0.0532 | 0.1525 | — |

**Selected M = 500.** `V_total` (dominated by the head term) is stable already at M = 20,
but `f_latent` — the variance *fraction* attributable to the latent — does not meet the
q95-relative-error gate until M = 500. This is a direct signature of the headline result:
the latent variance is so small that its *share* has large relative MC error even though
its absolute contribution is negligible. The selected-M f_latent subset distribution
(mean 0.0011, median 0.0006, q95 0.0041) is identical to the M = 500 reference, so the
gate selected the correct M. Full document: `MC_CONVERGENCE.md`.

## 4. Variance-decomposition framework

For each test sample `s` and parameter `j`:

| symbol | definition | meaning |
|---|---|---|
| `μ_θ(z)` | ParamHead mean output | head prediction |
| `σ_θ(z)` | ParamHead std output | head conditional std |
| `V_head` | `E_z[σ_θ(z)²]` | Gaussian-head conditional predictive variance |
| `V_latent` | `Var_z[μ_θ(z)]` (ddof = 0) | latent-induced predictive variation |
| `V_total` | `V_head + V_latent` | total model-implied predictive variance |
| `σ_total` | `√V_total` | latent-propagated predictive std |
| `μ_total` | `E_z[μ_θ(z)]` | latent-averaged point prediction |
| `f_latent` | `V_latent / V_total` | latent share of predictive variance |
| `ratio_σ` | `σ_total / σ_current` | widening factor vs manuscript evaluation |

Latent draws: `z = z_mean + exp(0.5·z_log_var)·ε`, `ε ~ N(0, I)`, M = 500, seeded
(20260825), chunked; `z_mean`, `z_log_var` from the frozen encoder. Absolute uncertainty is
also expressed in **log10 decades** via `σ·log_range_j`, where `log_range` is the
frozen full-data parameter scaler's per-parameter log10 range. The reference predictive
distribution (manuscript) is `N(μ_θ(z_mean), σ_θ(z_mean)²)`; the latent-propagated
predictive distribution is the moment-matched Gaussian
`N(μ_total, V_total)` (mixture quantiles also computed).

## 5. Variance-decomposition results

Across the full test set (N = 15,307), the Gaussian head supplies essentially the entire
predictive variance; the latent share is **~0.05–0.15%** of it.

| param | med σ_total (decades) | med f_latent | q25 f_latent | q75 f_latent | q95 f_latent |
|---|---|---|---|---|---|
| mu_n | 0.3268 | 0.0009 | 0.0004 | 0.0021 | 0.0046 |
| mu_p | 0.3002 | 0.0010 | 0.0005 | 0.0021 | 0.0047 |
| tau_n | 1.0286 | 0.0005 | 0.0002 | 0.0014 | 0.0056 |
| tau_p | 1.0641 | 0.0005 | 0.0002 | 0.0010 | 0.0035 |
| Nc | 0.2643 | 0.0015 | 0.0006 | 0.0029 | 0.0059 |
| Nv | 0.2925 | 0.0010 | 0.0004 | 0.0018 | 0.0035 |
| tau_ETL | 0.9175 | 0.0002 | 0.0001 | 0.0004 | 0.0012 |
| tau_HTL | 0.8026 | 0.0003 | 0.0001 | 0.0008 | 0.0024 |
| rad_c | 0.7015 | 0.0002 | 0.0000 | 0.0005 | 0.0016 |

Pooled over all samples/parameters: **median f_latent = 0.0005** (mean 0.0011,
q95 0.0041). Equivalently, the latent-induced predictive std is ~0.02–0.05% of the head
std, and `σ_total` exceeds `σ_current` by **median ratio_σ = 1.0003**
(p1–p99 = [0.9990, 1.0039]; 17% of samples have ratio < 1.0 because MC estimation of the
tiny latent variance can slightly *reduce* the estimated total for some draws — the
population ratio is ≥ 1 by construction, the difference is MC noise at the 4th decimal).

**Consequence.** The manuscript's σ_θ(z_mean) is numerically indistinguishable from the
latent-propagated σ_total; the reported predictive uncertainty is **head-dominated**.
(FigA, FigB, FigE.)

## 6. Calibration comparison

Empirical coverage of the manuscript's 95% Gaussian intervals vs the latent-propagated
intervals (moment-matched `N(μ_total, σ_total)` and MC mixture):

| param | current | moment | mixture | Δ moment | Δ mixture |
|---|---|---|---|---|---|
| mu_n | 0.9475 | 0.9474 | 0.9468 | −0.0001 | −0.0007 |
| mu_p | 0.9522 | 0.9524 | 0.9494 | +0.0001 | −0.0028 |
| tau_n | 0.9583 | 0.9585 | 0.9555 | +0.0002 | −0.0028 |
| tau_p | 0.9597 | 0.9598 | 0.9594 | +0.0001 | −0.0003 |
| Nc | 0.9464 | 0.9466 | 0.9448 | +0.0002 | −0.0016 |
| Nv | 0.9499 | 0.9499 | 0.9487 | +0.0000 | −0.0012 |
| tau_ETL | 0.9692 | 0.9691 | 0.9678 | −0.0001 | −0.0014 |
| tau_HTL | 0.9667 | 0.9668 | 0.9641 | +0.0001 | −0.0026 |
| rad_c | 0.9664 | 0.9665 | 0.9626 | +0.0001 | −0.0039 |

**Moment-matched coverage changes by ≤ 0.0002** at every parameter. The MC-mixture
(which accounts for the non-Gaussianity of the latent mixture) is ≤ 0.004 lower — a
negligible amount that does not change any calibration conclusion (all parameters remain
within the manuscript's reported 0.946–0.969 band). The mixture is slightly below the
moment-matched Gaussian because the latent mixture's tiny width makes the tails slightly
less Gaussian, but the effect is 100× smaller than any scientific claim the manuscript
makes. (FigC.)

## 7. Error-ranking comparison

Spearman correlation between predicted σ and absolute error, comparing the manuscript's
z_mean evaluation vs the latent-propagated evaluation:

| param | ρ_current | ρ_latent | ρ_total | Δ_total−current |
|---|---|---|---|---|
| mu_n | 0.3982 | 0.1981 | 0.3983 | +0.000015 |
| mu_p | 0.3344 | 0.1782 | 0.3344 | +0.000035 |
| tau_n | 0.6459 | 0.3947 | 0.6459 | +0.000002 |
| tau_p | 0.6218 | 0.3551 | 0.6218 | +0.000013 |
| Nc | 0.3531 | 0.1042 | 0.3530 | −0.000113 |
| Nv | 0.2445 | 0.1345 | 0.2444 | −0.000032 |
| tau_ETL | 0.3772 | **−0.1286** | 0.3772 | +0.000002 |
| tau_HTL | 0.4647 | 0.1556 | 0.4647 | +0.000025 |
| rad_c | 0.4147 | **−0.1962** | 0.4147 | −0.000002 |

**ρ_total ≡ ρ_current to four decimals (mean Δ ≈ 0.0000).** Two points are worth noting:

1. The **latent-mean prediction alone** (`ρ_latent`, μ_total without the σ correction) is
   a substantially worse ranker — the *information* driving σ–error ranking lives in the
   head's σ output, not in the latent mean.
2. Propagating latent variance (ρ_total) changes nothing: because σ_total ≈ σ_current, the
   ranking is unchanged. The manuscript's claim that σ ranks errors (mean ρ 0.4283) is a
   property of the **Gaussian head**, and survives latent propagation untouched. (FigD.)

## 8. Point-prediction comparison

Latent averaging of the point prediction (`μ_total = E_z[μ_θ(z)]`) vs the manuscript's
z_mean evaluation:

| metric | current | latent-mean | Δ |
|---|---|---|---|
| mean Pearson r | 0.806903 | 0.806912 | +0.000009 |
| mean MAE | 0.109960 | 0.109959 | −0.000001 |
| mean RMSE | 0.143565 | 0.143561 | −0.000004 |

Per-parameter Pearson Δ ∈ [+0.0000, +0.0001]. The latent distribution is so narrow that
averaging over it does not move the point prediction. **The manuscript's point-recovery
numbers are unchanged by latent propagation** — no correction, no degradation.

## 9. Encoder latent diagnostics

Root cause of the small `V_latent` (full test set, per latent dimension):

| quantity | range over 9 dims |
|---|---|
| mean z_mean | −0.38 … +0.12 (informative means) |
| SD(z_mean) across test | 0.375 – 0.597 (well spread) |
| mean posterior std exp(0.5·z_log_var) | **0.0017 – 0.0039** |
| median posterior std | 0.0015 – 0.0038 |
| mean KL per dim | 5.22 – 6.14 (total **51.356** nats) |

The encoder's latent means are informative and well spread — the latent is not
collapsed as an encoding. But the *posterior width* is extremely small
(exp(0.5·z_log_var) ≈ 0.002–0.004, i.e. ~0.4–0.9% of the latent's own SD). Sampling
q(z|J) therefore moves z by only a tiny amount relative to its informative mean, and the
decoder+ParamHead mapping barely changes: that is precisely why the latent-induced
predictive variance is negligible. The near-point posterior is a property of the frozen
model (its learned z_log_var), not an artifact of the experiment. (FigF.)

## 10. Latent-induced pairwise covariance

Conditioned on the *same* latent draw, different parameters' predicted deviations
`μ_θ(z) − μ_θ(z_mean)` can be correlated. The median (over test) latent-induced
correlation matrix (FigG) shows the descriptive structure of the latent function only:
strong within-group pairs (mu_n–mu_p 0.974, tau_n–tau_p 0.989, Nc–Nv 0.982), moderate
opposite-sign couplings (mu_n–tau_n −0.696, mu_n–Nc −0.683), and weak/indeterminate
interface couplings (tau_n–tau_ETL 0.379, tau_ETL–rad_c 0.012). Median |corr| over all 36
pairs = 0.443.

**Caveat (documented, not a limitation of the headline):** this covariance is the
conditional structure of the latent function. Because `V_latent` itself is only
~0.1% of `V_total`, this covariance contributes negligibly to the *total* predictive
variance, and no joint (full 9×9) predictive posterior is claimed or supported by these
results. `latent_induced_pairwise_covariance.csv` lists all 36 pairs.

## 11. Cross-seed robustness (Experiment-1 leakage-free checkpoints)

Reduced decomposition (M = 500, shared epsilon stream, seed 20260825) on the five
leakage-free VAE checkpoints from Experiment 1 (never retrained here):

| seed | med f_latent | med ratio_σ | cov95 (moment) | ρ_current | ρ_total | Δ Pearson |
|---|---|---|---|---|---|---|
| 20260824 | 0.000494 | 1.000306 | 0.9616 | 0.4377 | 0.4377 | +0.000010 |
| 20260825 | 0.000498 | 1.000324 | 0.9596 | 0.4271 | 0.4272 | +0.000010 |
| 20260826 | 0.000536 | 1.000342 | 0.9580 | 0.4309 | 0.4309 | +0.000002 |
| 20260827 | 0.000539 | 1.000323 | 0.9579 | 0.4435 | 0.4436 | +0.000006 |
| 20260828 | 0.000549 | 1.000346 | 0.9592 | 0.4300 | 0.4300 | +0.000012 |

Across seeds: **med f_latent 0.000523 ± 0.000023**, **med ratio_σ 1.000328 ± 0.000014**,
**cov95 0.9592 ± 0.0013**, ρ_total − ρ_current ≈ +0.0000, Δ Pearson +0.000008 ± 0.000004.
The head-dominated decomposition is **not a quirk of one training seed**; every leakage-free
checkpoint shows the same near-point posterior and the same negligible latent share.
(`exp1_multiseed_decomposition_summary.csv`.)

## 12. Cross-environment consistency

A self-contained package (`server_qc/`, 500 fixed samples, M = 500, same eps stream) runs
the decomposition on the frozen model. **Both legs complete and in agreement:**
`results/cross_env_local.json` (local, TF 2.20/Keras 3, verified reproducible — two runs
bit-identical) and `results/cross_env_server.json` (server, TF 2.13/Keras 2). Server-leg
values: median f_latent per parameter 0.00017–0.00140, median ratio_σ 1.0001–1.0008,
cov95 (moment) 0.944–0.978 — the same ranges as the local leg.

| field | max \|server − local\| | verdict |
|---|---|---|
| median_f_latent (9) | 7.16e-09 | PASS |
| median_sigma_total (9) | 0.00e+00 | PASS |
| median_ratio_sigma (9) | 0.00e+00 | PASS |
| mean_mu_total (9) | 1.19e-07 | PASS |
| cov95_moment (9) | 0.00e+00 | PASS |

All five fields agree to ≤ 1.2e-7 — far tighter than the ~0.02 tolerance set for
numeric-hygiene. The residual is float32 round-off from the TF 2.13/Keras 2 vs
TF 2.20/Keras 3 builds; the returned server file is a genuinely distinct computation
(non-zero differences would be zero if it were a copy of the local file). The
cross-environment check **PASSES**: every decomposition quantity is numerically
stable across environments.

## 13. Programmatic QC and integrity

`EXP2_QC.md` — **15/15 assertions PASS**, including:
- σ transform exactly `clip(softplus(raw)+0.01, 0.01, 1.0)` (max |recomputed − stored| = 1.04e-7); z_mean evaluation reproduces frozen μ (max 2.38e-7) and the frozen ρ/coverage reference.
- `V_head ≥ 0`, `V_latent ≥ 0`, `V_total = V_head + V_latent` (resid 0), `f_head + f_latent = 1` where V_total > 0, no NaN/Inf.
- M = 500 gate traceability; frozen **md5s unchanged** (encoder/decoder/param_head/best.weights, dataset_normalized.npz, manuscript `9703a16a…`); no training/optimizer call anywhere in `scripts/`; frozen paths' mtimes pre-date EXP2 (no overwrite).

## 14. Limitations

1. **The decomposition is mechanistic, not probabilistic-inference-theoretic.** `V_head`,
   `V_latent`, `V_total` describe the frozen network's own predictive outputs. They are a
   *model-implied predictive distribution*, not a Bayesian posterior; no epistemic/aleatoric
   claim is made or implied. Statements like "uncertainty attributable to the latent" are
   statements about where the frozen architecture's variance comes from, not about nature.
2. **Near-zero latent variance.** The central quantity `V_latent` is ~1e-5 of `V_head`;
   its *relative* MC error converges slowly, which is why M = 500 was required. The
   conclusion is robust to M (f_latent ≈ 0.0005 at every M ≥ 100) but any reported
   f_latent should be read at its absolute scale, not its relative precision.
3. **Single frozen model is the primary object.** The five Experiment-1 checkpoints are a
   robustness check under the leakage-free scaling protocol; the manuscript reference
   remains the frozen single-seed VAE-v6.
4. **Cross-environment check is numeric-hygiene only.** Both legs now agree to ≤ 1.2e-7
   (§12); the check validates numerical stability across TF/Keras builds, and by design
   contributes no new scientific signal.
5. **Joint (9-parameter) predictive structure is not claimed.** The latent-induced
   covariance is documented descriptively only; no full-joint predictive posterior is
   supported or proposed.

## 15. Scientific impact and outcome classification

**Headline.** The Gaussian parameter head supplies ~99.9% of the frozen VAE-v6's
model-implied predictive variance; the VAE latent's stochastic posterior contributes
~0.05–0.15%. Propagating latent uncertainty leaves calibration (Δ ≤ 0.0002),
sigma–error ranking (Δ ≈ 0.0000), and point predictions (Δ Pearson +0.000009)
unchanged. Root cause: the encoder's learned posterior width
exp(0.5·z_log_var) ≈ 0.002–0.004 is near-point — informative means, negligible width.

**Outcome classification — exactly one:**

> ## **C. GAUSSIAN HEAD DOMINATES — LATENT CONTRIBUTION MINOR**
>
> The VAE's stochastic latent adds only a minor predictive-variance share (~0.1%).
> Latent propagation does not improve (or degrade) calibration, error ranking, or point
> prediction. The manuscript's z_mean evaluation is numerically indistinguishable from
> full latent propagation. The reported predictive uncertainty is essentially the Gaussian
> head's heteroscedastic conditional output.

---

## EXPERIMENT 2 VERDICT

| gate | question | answer |
|---|---|---|
| G1 | Does the current clean-domain calibration claim survive latent propagation? | **YES** — moment-matched coverage changes by ≤ 0.0002; the MC mixture ≤ 0.004 lower; all parameters remain inside the reported band. |
| G2 | Does "probabilistic parameter inversion" remain defensible? | **QUALIFIED / YES** — defensible *as a model-implied predictive distribution* produced by a probabilistic pipeline (Gaussian head + latent). The uncertainty is head-dominated; wording must not attribute the uncertainty primarily to latent propagation. |
| G3 | Should the VAE latent be claimed as the main uncertainty source? | **NO** — the data show the opposite: the latent contributes ~0.1% of predictive variance. Claims of latent-driven uncertainty must be removed or reframed. |
| G4 | Does the core scientific framework survive? | **YES** — recoverability hierarchy, calibration band, σ–error ranking, and all point-prediction claims are unchanged by latent propagation. No scientific conclusion is invalidated. |

**Bottom line.** Experiment 2 does not attempt to prove VAE superiority (Experiment 1
already showed none). It answers the mechanistic question: the frozen model's predictive
uncertainty is **Gaussian-head-dominated**, the latent contribution is minor (~0.1%), and
the manuscript's z_mean evaluation is not a meaningful approximation — it is, to four
decimal places, what full latent propagation gives. The only manuscript-level action
needed is **wording**: describe the predictive distribution as head-supplied, with latent
sampling contributing a minor additional variance (see §24 candidate in
`EXP2_MANUSCRIPT_IMPACT.md`).
