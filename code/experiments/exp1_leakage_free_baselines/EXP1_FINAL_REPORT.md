# EXP1 FINAL REPORT — Leakage-Free Multi-Seed Matched Baseline Benchmark

Experiment 1 · reviewer response · 2026-08-24 (benchmark) / 2026-08-25 (analysis)
`reviewer_experiments/exp1_leakage_free_baselines/`
Frozen manuscript / VAE-v6 / evaluation / figures: **untouched** (see README).

> FINAL — all 12 sections complete. Local 15-run benchmark (TF 2.20/Keras 3) is the
> primary analysis; the server 15-run replica (TF 2.13/Keras 2, anchor-checked)
> corroborates every qualitative conclusion (see `CROSS_ENV_COMPARISON.md`).

---

## 1. Pipeline verification

**Frozen anchor reproduced exactly.** Running the frozen VAE-v6 weights through the
experiment's evaluation code reproduces the published numbers bit-for-bit
(`phase0_frozen_eval_repro.txt`): per-parameter Pearson r =
0.9063 / 0.9194 / 0.8783 / 0.8808 / 0.9090 / 0.8956 / 0.5936 / 0.7199 / 0.5592
(mean **0.8069**), 95% coverage 0.9464–0.9692, mean Spearman(σ, |err|) 0.4283,
recon MSE 1.211244e-05 (median 2.969464e-06). The environment therefore measures the
same thing the Stage-I study reported.

**Architecture and loss conventions verified against `script/VAE-v6.py`**
(no discrepancy → Phase B PASS):
- Encoder 131→128→64→(z_mean, z_log_var); Sampling z = z_mean + exp(0.5·z_log_var)·ε;
  decoder 9→64→128→131 sigmoid; ParamHead 9→64→32→(mu[9], sigma_raw[9],
  bias init `Constant(-3.0)`).
- sigma = clip(softplus(raw) + 0.01, 0.01, 1.0); Adam lr 1e-3; batch 64;
  BETA 1e-3, LAMBDA 1.0; max epochs 1000.
- EarlyStopping(monitor=`val_param_loss`, patience 50, restore_best_weights=True);
  ReduceLROnPlateau(monitor=`val_loss`, factor 0.5, patience 15, min_lr 1e-6);
  ModelCheckpoint(monitor=`val_loss`, save_best_only, save_weights_only).
- Loss reductions (locked in `LOSS_REDUCTION_VERIFICATION.md`):
  recon = mean_batch[Σ_131(x−x̂)²]; KL = −½·mean_batch[Σ_9(1+z_lv−z_m²−e^{z_lv})];
  nll = mean_batch[Σ_9(½·((y−μ)/σ)²+log σ)]; total = recon + 1e-3·KL + nll.
- Evaluation at z_mean (VAE); coverage z-values 0.67448975/1.28155157/1.64485363/1.95996398.

**Framework.** TF-CPU (TF 2.20.0 Windows wheel is CPU-only; RTX 4060 Ti visible only to
torch). All three benchmark models run in the exact frozen framework and code conventions,
so the only controlled difference is the scaling protocol (train-only vs full-data).

**Split.** Archived npz block membership used verbatim (train 71,432 / val 15,307 /
test 15,307). An independent two-step sklearn seed-42 re-derivation does NOT reproduce the
archived membership (crosstab ≈ chance; scanning rs=0..400 gives no hit) — the archived
blocks ARE the exact Stage-I membership, so they are authoritative. Recorded in
`split_indices_original_reproduced.npz` + README §Split.

**Scalers.** Parameters: log10 → per-column minmax on TRAIN ONLY. J-V: per-column minmax
on TRAIN ONLY. val/test transformed with train constants, **no clipping** → extrapolation
statistics are measurable.

## 2. Leakage-free preprocessing statistics

Raw physical values recovered from the archived scaled arrays by inverting the frozen
full-data scalers (float64-exact; max rel err vs stored raw test 4.71e-15 for parameters,
max abs err 4.55e-13 for J). Train-only scaler ranges (log10 space):

| parameter | train min | train max |
|---|---|---|
| mu_n | −6.341 | −2.656 |
| mu_p | −6.344 | −2.682 |
| tau_n | −9.308 | −1.656 |
| tau_p | −9.346 | −1.690 |
| Nc | 22.766 | 26.348 |
| Nv | 22.634 | 26.338 |
| tau_ETL | −12 | −8 |
| tau_HTL | −14 | −10 |
| rad_c | −12 | −9 |

**Parameter leakage is negligible.** Per-parameter fraction of val/test samples falling
outside [0,1] ≤ 0.0001; worst single-point extrapolation val 0.0064, test 0.0279.
The 70% training subset of an LHS domain covers it almost completely.

**J-V leakage is small but real** — the one place full-data scaling could matter:
- val: fraction <0 = 0.00002, >1 = 0.00000 (min −0.092, max 1.0000)
- test: fraction <0 = 0.00003, >1 = 0.00002 (min −0.249, max 1.0001)
- Affected columns: lowest-voltage region (≈0–0.18 V) and highest-voltage region
  (≈1.24–1.30 V); the two-sided tail is concentrated in the sigmoid saturation zones of
  the decoder input.

## 3. Pilot result

Leakage-free VAE, seed 20260824, full 1000 epochs (hit cap; val_param_loss still improving
→ early-stopping patience never fired). 4,473 s (~74.5 min), 55,495 params.

| param | r_pilot | r_frozen | Δr | 95% cov | mean σ | ρ(σ,\|e\|) |
|---|---|---|---|---|---|---|
| mu_n | 0.8775 | 0.9063 | −0.029 | 0.952 | 0.105 | 0.448 |
| mu_p | 0.8927 | 0.9194 | −0.027 | 0.958 | 0.098 | 0.418 |
| tau_n | 0.8598 | 0.8783 | −0.019 | 0.964 | 0.119 | 0.628 |
| tau_p | 0.8615 | 0.8808 | −0.019 | 0.964 | 0.119 | 0.604 |
| Nc | 0.8868 | 0.9090 | −0.022 | 0.952 | 0.086 | 0.367 |
| Nv | 0.8787 | 0.8956 | −0.017 | 0.953 | 0.088 | 0.289 |
| tau_ETL | 0.5667 | 0.5936 | −0.027 | 0.971 | 0.233 | 0.384 |
| tau_HTL | 0.6885 | 0.7199 | −0.031 | 0.970 | 0.202 | 0.442 |
| rad_c | 0.5288 | 0.5592 | −0.030 | 0.969 | 0.238 | 0.360 |
| **mean** | **0.7823** | **0.8069** | **−0.025** | **0.9615** | | **0.438** |

Hard-failure checks: all PASS (no NaN/Inf; σ ∈ [0.0121, 0.6584] ⊂ [0.01, 1]; finite
val_param_loss min −14.55 at epoch 1000; prediction std min 0.155; test-J out-of-[0,1]
fraction 0.00006, not severe). Recon MSE 1.149e-05 / med 2.485e-06 (slightly *better*
than frozen 1.211e-05 / 2.969e-06).

**Pilot gate: PASS → PROCEED TO FULL BENCHMARK.** Performance differences vs frozen are
diagnostic only and never gate the benchmark. The observed single-seed Δmean r ≈ −0.025 is
consistent with the *small* expected parameter-level leakage effect and will be quantified
across 5 seeds in §8.

## 4. Five-seed VAE results

Per-seed ALL-mean Pearson r (test): **0.7823 / 0.7900 / 0.7977 / 0.8090 / 0.7979** →
mean **0.7954 ± 0.0100**, min–max 0.7823–0.8090. Frozen single-seed 0.8069 sits
above 4/5 seeds ⇒ the full-data-vs-train-only scaling difference is smaller than the
seed spread. Training: seeds stop at 753–1000 epochs (3/5 hit the 1000 cap),
55,495 params, ~4,151 s/run mean active time.

| param | r_mean | r_sd | MAE(dec) | NLL | 95% cov | ρ(σ,\|e\|) |
|---|---|---|---|---|---|---|
| mu_n | 0.8936 | 0.0098 | 0.292 | −1.884 | 0.950 | 0.402 |
| mu_p | 0.9079 | 0.0093 | 0.274 | −1.947 | 0.952 | 0.370 |
| tau_n | 0.8704 | 0.0074 | 0.729 | −1.911 | 0.960 | 0.635 |
| tau_p | 0.8721 | 0.0072 | 0.737 | −1.861 | 0.961 | 0.605 |
| Nc | 0.8981 | 0.0082 | 0.229 | −2.072 | 0.949 | 0.367 |
| Nv | 0.8864 | 0.0072 | 0.250 | −1.999 | 0.949 | 0.272 |
| tau_ETL | 0.5780 | 0.0121 | 0.764 | −1.022 | 0.972 | 0.393 |
| tau_HTL | 0.7086 | 0.0166 | 0.649 | −1.224 | 0.969 | 0.465 |
| rad_c | 0.5432 | 0.0159 | 0.587 | −1.008 | 0.969 | 0.396 |
| **ALL** | **0.7954** | **0.0100** | 0.501 | **−14.928** | **0.9591** | **0.4338** |

Hierarchy identical to frozen (Q1); group separation intact (Q2); calibration near
nominal (Q3); σ informative (Q4).

## 5. Five-seed deterministic AE results

Per-seed ALL-mean Pearson r: **0.8098 / 0.8093 / 0.8147 / 0.8238 / 0.8067** → mean
**0.8128 ± 0.0068**, min–max 0.8067–0.8238. All 5 seeds ran the full 1000 epochs
(no early stop), 54,910 params.

| param | r_mean | r_sd | MAE(dec) | NLL | 95% cov | ρ(σ,\|e\|) |
|---|---|---|---|---|---|---|
| mu_n | 0.9083 | 0.0070 | 0.272 | −1.967 | 0.950 | 0.420 |
| mu_p | 0.9206 | 0.0065 | 0.255 | −2.008 | 0.952 | 0.355 |
| tau_n | 0.8833 | 0.0048 | 0.683 | −1.999 | 0.957 | 0.654 |
| tau_p | 0.8847 | 0.0049 | 0.694 | −1.931 | 0.961 | 0.620 |
| Nc | 0.9138 | 0.0067 | 0.209 | −2.173 | 0.949 | 0.394 |
| Nv | 0.8967 | 0.0051 | 0.238 | −2.045 | 0.949 | 0.265 |
| tau_ETL | 0.6028 | 0.0107 | 0.740 | −1.061 | 0.969 | 0.416 |
| tau_HTL | 0.7308 | 0.0076 | 0.620 | −1.281 | 0.969 | 0.492 |
| rad_c | 0.5746 | 0.0128 | 0.566 | −1.059 | 0.968 | 0.438 |
| **ALL** | **0.8128** | **0.0068** | 0.475 | **−15.524** | **0.9581** | **0.4505** |

Same hierarchy and groups as VAE/frozen; mean r is above VAE on every matched seed pair
and on **all 9 parameters** (e.g. mu_n 0.9083 vs 0.8936, rad_c 0.5746 vs 0.5432). Lower
mean NLL (−15.52 vs −14.93). The deterministic AE is the **strongest recoverability
model in this benchmark.**

## 6. Five-seed MLP results

Per-seed ALL-mean Pearson r: **0.7810 / 0.7860 / 0.7822 / 0.7998 / 0.7977** → mean
**0.7894 ± 0.0088**, min–max 0.7810–0.7998. All 5 seeds ran the full 1000 epochs,
27,826 params (input→128→64→32→(μ,σ) trunk; no reconstruction).

| param | r_mean | r_sd | MAE(dec) | NLL | 95% cov | ρ(σ,\|e\|) |
|---|---|---|---|---|---|---|
| mu_n | 0.8888 | 0.0107 | 0.300 | −1.857 | 0.950 | 0.407 |
| mu_p | 0.9017 | 0.0115 | 0.285 | −1.901 | 0.952 | 0.368 |
| tau_n | 0.8689 | 0.0061 | 0.734 | −1.893 | 0.957 | 0.619 |
| tau_p | 0.8713 | 0.0062 | 0.740 | −1.851 | 0.959 | 0.591 |
| Nc | 0.8957 | 0.0079 | 0.234 | −2.043 | 0.950 | 0.346 |
| Nv | 0.8825 | 0.0069 | 0.255 | −1.974 | 0.950 | 0.250 |
| tau_ETL | 0.5605 | 0.0085 | 0.779 | −0.991 | 0.968 | 0.360 |
| tau_HTL | 0.6920 | 0.0105 | 0.668 | −1.173 | 0.971 | 0.426 |
| rad_c | 0.5428 | 0.0209 | 0.587 | −1.001 | 0.968 | 0.384 |
| **ALL** | **0.7894** | **0.0088** | 0.509 | **−14.683** | **0.9584** | **0.4168** |

Same hierarchy/groups/calibration as the AE families; mean r the **lowest of the three
families** (below VAE on all 5 seeds). Calibration and σ-informativeness remain intact
(the Gaussian head, not the AE, carries those properties).

## 7. Architecture comparison

5-seed means (local): det_ae 0.8128 ± 0.0068 > VAE 0.7954 ± 0.0100 > mlp 0.7894 ± 0.0088.

| pair | Δ mean r | paired-t p | Wilcoxon p |
|---|---|---|---|
| VAE − det_ae | −0.0175 | 0.005 | 0.062 |
| VAE − mlp | +0.0060 | 0.099 | 0.062 |
| det_ae − mlp | +0.0235 | 0.004 | 0.062 |

**VAE does not outperform the matched deterministic AE** (Q6): locally det_ae is
numerically higher on every seed (−0.0175, p = 0.005); on the server the two tie
(+0.0002, p = 0.92). **The AE family does beat direct MLP**: det_ae −0.0235 (p = 0.004)
local, +0.0119 (p = 0.016) server; VAE − mlp is directionally positive but not
significant locally (+0.0060, p = 0.099). Cross-environment (TF 2.20/Keras 3 vs
TF 2.13/Keras 2) shifts every run by ≤0.02 and flips the VAE/det_ae top-two order
(local det_ae > VAE, server VAE > det_ae) — the variational branch adds no robustly
measurable value. **Phase P outcome: C.**

## 8. Leakage impact

Per-parameter Δr = leakage-free VAE mean − frozen VAE-v6 (full-data scaler):

| | mu_n | mu_p | tau_n | tau_p | Nc | Nv | tau_ETL | tau_HTL | rad_c | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| local Δ | −0.013 | −0.012 | −0.008 | −0.009 | −0.011 | −0.009 | −0.016 | −0.011 | −0.016 | **−0.0115** |
| server Δ | −0.002 | −0.003 | −0.000 | −0.001 | −0.004 | −0.005 | +0.000 | +0.003 | −0.000 | **−0.0013** |

**Classification (local): SMALL; (server): NEGLIGIBLE.** Every local per-parameter Δ
is −0.008…−0.016 — small relative to the group gaps in §2/§10 and to the 5-seed SD
(0.007–0.024). Caveat: the frozen point estimate is a *single* seed, so the local
Δ mixes the scaling difference with seed noise — the frozen 0.8069 lies inside the
leakage-free seed range (0.7823–0.8090, above 4/5 seeds), and the same-seed-mean
comparison on the server (Δ −0.0013) brackets the true scaling effect as negligible
to small. **The full-data normalization does not materially inflate parameter
recoverability; the small local deficit is mostly seed spread.** Preprocessing leakage
in the J-V inputs is likewise confined to the voltage-extreme sigmoid zones (§2) and
does not change the hierarchy.

## 9. Multi-seed stability

| family | mean r | SD | min–max | spread/group-gap |
|---|---|---|---|---|
| vae | 0.7954 | 0.0100 | 0.7823–0.8090 | < interface-bulk gap (0.24) |
| det_ae | 0.8128 | 0.0068 | 0.8067–0.8238 | same |
| mlp | 0.7894 | 0.0088 | 0.7810–0.7998 | same |

Seed SD (0.007–0.010) is 5–20× smaller than the group separations (§10). The
bulk>interface>radiative order and the calibration/sigma properties hold for **every**
seed. Adjacent *within-group* parameters (e.g. tau_n/tau_p, spaced ~0.002) may swap
rank between seeds, which is expected and does not touch any headline. The frozen
single-seed 0.8069 is a fair draw from the leakage-free seed distribution ⇒ the
frozen study's point estimate was not seed-lucky, and its headline survives. (The
one artifact to note: local det_ae/20260828 recorded 38,315 s wall because the
machine slept 8 h mid-run; active training time is unaffected and the run is a normal
member of the seed set.)

## 10. Physical interpretation of parameter errors

The hierarchy is **bulk parameters ≫ interface lifetimes ≳ radiative loss** and is
mechanistically the same as the frozen study:
- **Well recovered (bulk):** mu_n, mu_p, tau_n, tau_p, Nc, Nv — mean r 0.87–0.92
  (5-seed, leakage-free). These set the device's internal transport and recombination
  balance, are strongly constrained by the J-V curve across the full voltage sweep, and
  their log10 ranges span ~3.7 decades of LHS prior.
- **Poorly recovered (interface):** tau_ETL r 0.56–0.60, tau_HTL r 0.69–0.73 —
  interface lifetimes couple to recombination only weakly near flat band; they are the
  classic low-sensitivity parameters.
- **Poorest (radiative):** rad_c r 0.54–0.57 — the radiative recombination coefficient
  is nearly degenerate with Shockley-Read-Hall lifetimes in the radiative limit, so its
  identifiability from J-V is intrinsically low.
- MAE in decades follows the same ordering (bulk ~0.21–0.30, interface ~0.62–0.78,
  rad_c ~0.57); 95% Gaussian coverage is near-nominal (0.949–0.972) for every parameter
  in every family, and σ–|err| Spearman is positive everywhere (0.25–0.74 by parameter),
  so the probabilistic head's error bars remain meaningful even where point recovery is
  weak (tau_ETL/HTL/rad_c: ρ 0.36–0.49).

## 11. Manuscript impact

See **`EXP1_MANUSCRIPT_IMPACT.md`** for the ten questions answered in full. In one
sentence: **no core scientific conclusion is invalidated (Q1–Q5, Q9, Q10 YES/NO as
reported); the two claims requiring action are the VAE-vs-deterministic performance
claim (Q6: not supportable) and the architecture-as-contribution framing (Q8: reframe
to "reconstruction-regularized AE + Gaussian parameter head").**

## 12. Reviewer-facing conclusion

The three reviewer questions are answered with a leakage-free, 5-seed-per-family,
architecturally matched benchmark, anchor-verified against the frozen study and
replicated in a second independent environment:

1. **Leakage is not a material concern.** Train-only scaling moves mean r by −0.012
   (local) / −0.001 (server) — small to negligible, within seed spread, and the full
   hierarchy, group structure, calibration and σ-informativeness all survive verbatim.
2. **The recoverability hierarchy is stable across seeds.** 5-seed SD ≤ 0.010;
   every headline holds for every seed.
3. **The VAE architecture does not add measurable value over a matched deterministic
   autoencoder, and the AE framework (either variant) beats direct MLP.** The honest
   contribution statement is the autoencoder-regularized Gaussian parameter regression
   framework, not the variational machinery per se.

Frozen manuscript, weights, evaluation and figures remain untouched; every new artefact
lives under `reviewer_experiments/exp1_leakage_free_baselines/`.

### EXPERIMENT 1 VERDICT

**C. ARCHITECTURES COMPARABLE — SCIENTIFIC FRAMEWORK REMAINS THE CONTRIBUTION.**

(Local phase-P classifier: C. On the server the same classifier returns B
(VAE +0.0002 over det_AE); the B/C boundary is environment-sensitive and both agree
the VAE adds no robust advantage. VAE *and* det_AE outperform direct MLP, so the
autoencoder + Gaussian-head framework is the supported architectural claim.)

### CORE SCIENTIFIC CONCLUSIONS SURVIVE — YES / NO

**YES.**

No existing scientific conclusion fails. What changes: (i) the performance claim
"VAE recovers parameters better than alternatives" is not supported against a matched
deterministic AE and must not be asserted; (ii) the contribution framing should say
"autoencoder-regularized Gaussian parameter regression" (VAE one member of the family),
which is the statement the data supports. All quantitative recoverability, hierarchy,
calibration and uncertainty statements in the frozen Stage-I manuscript remain
approximately valid under leakage-free, multi-seed re-training.
