# EXP1 MANUSCRIPT IMPACT — 10 Reviewer Questions Answered

Experiment 1 · leakage-free multi-seed matched baseline benchmark · 2026-08-25
Primary numbers from the **local** environment (TF 2.20.0/Keras 3, the frozen study's
framework lineage); the server parallel run (TF 2.13/Keras 2, 15/15 identical runs,
anchor-checked) corroborates every qualitative conclusion. Frozen Stage-I manuscript
`manuscript_stage1_submission_clean.md` **untouched**; this document only *reports* impact.

Frozen single-seed reference (full-data scaler): mean r = **0.8069**.
Leakage-free VAE 5-seed mean r = **0.7954 ± 0.0100** (local) / 0.8056 ± 0.0067 (server).
Frozen 0.8069 sits above 4/5 leakage-free seeds ⇒ the full-data-scaling difference is
smaller than the seed spread.

---

## Q1. Does the current main recoverability hierarchy survive leakage-free training?

**YES — the mean hierarchy is reproduced exactly, in order.**

| rank | frozen | leakage-free VAE (5-seed mean) |
|---|---|---|
| 1 | mu_p 0.9194 | mu_p 0.9079 |
| 2 | Nc 0.9090 | Nc 0.8981 |
| 3 | mu_n 0.9063 | mu_n 0.8936 |
| 4 | Nv 0.8956 | Nv 0.8864 |
| 5 | tau_p 0.8808 | tau_p 0.8721 |
| 6 | tau_n 0.8783 | tau_n 0.8704 |
| 7 | tau_HTL 0.7199 | tau_HTL 0.7086 |
| 8 | tau_ETL 0.5936 | tau_ETL 0.5780 |
| 9 | rad_c 0.5592 | rad_c 0.5432 |

Adjacent-parameter spacing (0.005–0.012) is comparable to the 5-seed SD (0.007–0.024),
so individual *adjacent* parameters may swap rank in a single seed, but no group-level
order ever changes. Hierarchy headline **survives**.

## Q2. Do the six bulk vs interface/radiative group conclusions survive?

**YES.**

| group | frozen mean r | leakage-free VAE mean r | Δ |
|---|---|---|---|
| bulk (mu_n, mu_p, tau_n, tau_p, Nc, Nv) | 0.8982 | 0.8881 | −0.010 |
| interface (tau_ETL, tau_HTL) | 0.6568 | 0.6433 | −0.014 |
| radiative (rad_c) | 0.5592 | 0.5432 | −0.016 |

Order **bulk > interface > radiative** holds under leakage-free training; all three
groups shift down by a similar small amount (0.010–0.016), so every pairwise group
conclusion (bulk-vs-interface, bulk-vs-radiative, interface-vs-radiative) survives.

## Q3. Does clean-domain approximate calibration survive?

**YES.** 95% Gaussian coverage (leakage-free VAE, 5-seed mean, per parameter)
0.9487–0.9718, ALL-mean 0.9591 (frozen: 0.9464–0.9692, ALL 0.9615). All three
benchmark families land at 0.958–0.959 (vae 0.9591 / det_ae 0.9581 / mlp 0.9584).
Approximate near-nominal calibration is unchanged.

## Q4. Does sigma remain informative about prediction error?

**YES.** Mean Spearman(σ, |err|): frozen VAE 0.4283 → leakage-free VAE 0.4338
(local) / 0.4408 (server); det_ae 0.4505; mlp 0.4168. σ tracks absolute error in
every family, marginally *stronger* for the deterministic AE. Note for the manuscript:
the σ-informativeness claim is **not VAE-exclusive** — it holds for any model with the
Gaussian parameter head.

## Q5. Does multi-seed variance materially change any headline statement?

**NO.** Seed SDs: vae 0.0100, det_ae 0.0068, mlp 0.0088 (mean r units). The frozen
single-seed 0.8069 lies *inside* the leakage-free VAE 5-seed range (0.7823–0.8090).
Every headline statement that holds at the frozen point estimate also holds for every
individual seed (hierarchy, group order, calibration, σ-informativeness). The one
qualitative upgrade: point estimates should now carry mean±SD, and the 
single-seed-vs-multi-seed spread (up to ±0.013 for VAE) is the honest uncertainty.

## Q6. Does VAE outperform deterministic AE?

**NO.** Local: det_ae 0.8128 ± 0.0068 > VAE 0.7954 ± 0.0100 (Δ −0.0175, paired-t
p = 0.005). Server: det_ae 0.8054 ≈ VAE 0.8056 (Δ +0.0002, p = 0.92). The two
environments disagree on the *sign* — the deterministic AE edges the VAE on the local
benchmark and ties it on the server. **No VAE advantage is supportable; the comparison
is environment-sensitive and at best a statistical tie.**

## Q7. Does VAE outperform direct MLP?

**QUALIFIED — directionally yes, not significant.** Local Δ(vae−mlp) = +0.0060
(paired-t p = 0.099); server +0.0122 (p = 0.042, marginal). The robust and significant
statement is about the **AE family**: det_ae beats MLP by +0.0235 (local, p = 0.004)
and +0.0119 (server, p = 0.016). The reconstruction-regularized AE framework (with or
without the variational branch) beats a direct input→parameter MLP of matched trunk;
the variational branch itself adds nothing measurable on top of the deterministic AE.

## Q8. Should architecture be claimed as a contribution?

**NO — reframe.** The VAE-specific (variational) machinery adds no measurable value
over the matched deterministic AE (Q6). The claims that ARE supported:
- the **reconstruction-regularized autoencoder + Gaussian parameter head** framework
  adds value over direct MLP regression (Q7) — this is the defensible architectural
  statement;
- the **probabilistic parameter head (σ)** remains informative about error (Q4).
Recommended phrasing for the manuscript/rebuttal: "a reconstruction-regularized
autoencoder with a Gaussian parameter head" (VAE as one member of the family), not
"the variational autoencoder architecture as such."

## Q9. Should original Stage-I numerical tables be replaced?

**NO.** The tables were computed with full-data scaling; leakage-free re-training shifts
per-parameter r by −0.008 to −0.016 (mean −0.0115 local; −0.0013 server), i.e. **small /
negligible** and mostly within seed spread. The published numbers remain approximately
reproducible. Recommended: keep the frozen tables, add a methods footnote that scalers
were fit on the full retained set and that a train-only-scaler re-run moves mean r by
≲0.02, and cite this experiment for the multi-seed leakage-free corroboration.

## Q10. Is any core paper conclusion invalidated?

**NO — with one claim reframed.** Surviving: parameter recoverability from J-V;
bulk>interface>radiative hierarchy; approximate uncertainty calibration; σ
informativeness. The single claim affected is the **VAE-as-contribution** framing
(Q8): the variational branch specifically is not supported, and the manuscript's
architectural claims should be attributed to the AE+Gaussian-head framework. No
*scientific* conclusion fails.

---

## Summary

| Q | Answer | One-line basis |
|---|---|---|
| 1 hierarchy survives | **YES** | exact same mean order, groups intact |
| 2 group conclusions survive | **YES** | bulk>interface>radiative in both |
| 3 calibration survives | **YES** | 95% cov 0.959 vs nominal 0.95 |
| 4 σ informative | **YES** | ρ≈0.42–0.45, all families |
| 5 multi-seed changes headline | **NO** | SD≤0.010; frozen inside seed range |
| 6 VAE > det_AE | **NO** | local −0.0175, server tie |
| 7 VAE > MLP | **QUALIFIED** | +0.006 ns; AE-family effect robust |
| 8 architecture as contribution | **NO (reframe)** | claim AE+Gaussian-head, not VAE |
| 9 replace tables | **NO** | Δ≤0.016, small/negligible |
| 10 core conclusion invalidated | **NO** | one framing reframe only |
