# Experiment design (frozen before training)

`config/experiment_config.json` was written by `scripts/02_make_splits.py` **before any model
was trained**, at 2026-10-21; its sha256 is recorded in every `logs/<run>/run.json`. The design
was not revised after seeing any test result.

## 1. What is compared

Two arms, retrained from scratch, identical in every respect except the prior of the three
ratio coordinates:

| arm | ratio prior | n used | shared scales |
|---|---|---|---|
| `original` | q ~ U(0.2, 5), linear | 24,274 (seeded subsample of 102,046) | unchanged |
| `expanded` | q ~ U(0.05, 20), linear | 24,274 (all delivered post-filter rows) | unchanged |

Shared-scale priors (identical in both arms): `mu_avg` 1e-6–1e-3, `tau_avg` 1e-9–1e-2,
`DOS_avg` 1e22–1e26, `tau_ETL` 1e-12–1e-8, `tau_HTL` 1e-14–1e-10, `rad_c` 1e-12–1e-9.

## 2. Network — transcribed, then audited against the frozen file

`scripts/vae_v6_model.py` is a transcription of `script/VAE-v6.py` with only path/IO removed.
Equivalence was checked term by term against the source file, not from memory:

| element | frozen `VAE-v6.py` | this experiment |
|---|---|---|
| input / latent / parameter dims | 131 / 9 / 9 | same |
| encoder | Dense 128 relu → Dense 64 relu → z_mean(9), z_log_var(9) → Sampling | same |
| decoder | Dense 64 relu → Dense 128 relu → Dense 131 sigmoid | same |
| parameter head | Dense 64 relu → Dense 32 relu → mu(9); sigma_raw(9) with bias init −3.0 | same |
| sigma | `clip(softplus(raw)+0.01, 0.01, 1.0)` | same |
| reconstruction loss | mean over batch of **sum** over 131 points of squared error | same |
| KL | `−0.5 · mean(Σ(1 + z_log_var − z_mean² − e^{z_log_var}))` | same |
| parameter loss | Gaussian NLL `0.5·(resid²/σ² + 2 log σ)`, summed over 9, mean over batch | same |
| total loss | `recon + 0.001·KL + 1.0·NLL` | same |
| optimiser | Adam(1e-3) | same |
| batch size / max epochs | 64 / 1000 | same |
| early stopping | `val_param_loss`, patience 50, restore best weights | same |
| LR schedule | `ReduceLROnPlateau(val_loss, factor 0.5, patience 15, min_lr 1e-6)` | same |
| checkpoint | `val_loss`, save best only | same (written from the submodels, see §7) |
| shuffle | `shuffle(16992).batch(64)` | `tf.data` shuffle(buffer = n_train, seed = training seed) |

The nine physical parameter labels and their order are unchanged and the head still predicts the
nine parameters; the network was **not** switched to predicting the six a/r coordinates, and the
output layer and loss were **not** altered for the wider range.

## 3. Seeds and audit trail

Five training seeds: 20261021, 20261022, 20261023, 20261024, 20261025. For each seed,
`keras.utils.set_random_seed(seed)` is called immediately before model construction in *both*
arms, and the same seed drives the shuffle buffer, so the same seed gives the same initial
weights, the same batch order and the same dropout/noise draws wherever the framework permits.

Audit records per run (`logs/<arm>_<seed>/run.json`): seed, config sha256, arm-cache sha256,
number of train/val/test rows, batch size, max epochs, **sha256 of the concatenated initial
weights**, environment (Python / NumPy / TensorFlow / Keras / platform), per-epoch train and
validation losses plus learning rate (`epochs.csv`, `history.json`), best epoch, stopped epoch,
stop reason, best `val_loss` and `val_param_loss`, wall time, and sha256 + size of every model
file.

Where strict correspondence is *not* possible and is therefore recorded rather than claimed:
the two arms draw different data, so after the first step the gradient sequences diverge; the
sampled latent noise depends on the number of steps executed, so two runs that stop at different
epochs cannot be element-wise aligned. What is guaranteed is identical initialisation, identical
batch-order rule, identical training-set size and identical optimisation settings.

## 4. Preprocessing

`log10` of the nine parameters, then a `MinMaxScaler` fitted on that arm's **train rows only**;
currents through a per-voltage `MinMaxScaler` also fitted on train only. Validation and test are
transformed with the training statistics and are never clipped; no test-set minimum or maximum is
used anywhere.

Recorded consequence: because each arm has its own scalers, the effective normalisation and the
relative weight of the nine NLL terms differ slightly between arms (per-parameter log10 spans
across the nine parameters: 3.00–7.65 decades in the original arm and 3.00–7.97 decades in the
expanded arm; each arm's full vectors are in `data/split_summary.json`). The comparison therefore
measures the effect of the re-specified training distribution as a whole, not a perfectly isolated
range effect. The frozen main model used full-retention scalers, so no difference against its
historical numbers is attributed to the ratio range.

## 5. Evaluation protocol

- Point prediction: encoder `z_mean` → parameter head `mu`, no latent sampling, identical for both
  arms and for both test sets.
- Scalers belong to the **model arm**, not to the test arm (v2 correction, 2026-10-21). For a
  model trained on arm *m* and evaluated on arm *t*:
  `J_input = current_scaler[m].transform(J_physical[t][idx])`, then
  `L_pred = param_scaler[m].inverse_transform(mu)`. The physical currents (mA cm⁻²) are read
  directly from the archived arm cache; `J_scaled` is never un-scaled to reconstruct them. For
  `m == t` the transformed input is asserted bit-for-bit against the archived `J_scaled`
  (max difference 0.0). No clipping is applied to inputs or outputs.
- Baselines belong to the **test arm**: Skill_MSE uses the test arm's training mean, MAE reduction
  its training median, R²_test the test mean — identical for both models within a column.
- Space: physical log10 parameter space after inverse transform (`L = mu·data_range_ + data_min_`).
- Coordinates: `a = (L_n + L_p)/2`, `r = L_n − L_p`, in the order
  `a_mu, r_mu, a_tau, r_tau, a_D, r_D`; the nine single parameters are reported as well.
- Metrics, from `20261019_HC_revision_stage1_v2/scripts/metrics_lib.py` (imported verbatim, sha256
  recorded): Pearson, MAE, RMSE, R²_test, Skill_MSE, MAE reduction.
  - `Skill_MSE = 1 − SSE_model / Σ(y − ȳ_train)²`, baseline = **training-mean constant**.
  - `R²_test = 1 − SSE_model / Σ(y − ȳ_test)²`; it is **not** Pearson² and both are reported.
  - `MAE reduction = 1 − MAE_model / mean|y − median_train|`, baseline = **training median**.
  - A zero denominator yields **NaN plus an `undefined` flag**, never a silent 0 or Inf; negative
    values are retained. Every row is audited in `out/metrics/eval_manifest.json`.
- No prediction method differs between arms or test sets.

## 6. Two table families

**Table A** (`out/metrics/table_A_own_distribution.csv`) — each arm's model on its own test set,
with that arm's own training baselines. The two rows rest on different test distributions and
different denominators, so a Skill difference between arms in this table alone is **not** evidence
of improved recovery.

**Table B** (`out/metrics/table_B_common_tests.csv`) — same-test-set comparison:
on the common original-range test (3,641 rows) both models are scored with the *original arm's*
training mean/median; on the common expanded-range test (3,641 rows) both are scored with the
*expanded arm's* training baselines. Raw MAE, RMSE, baseline MSE and per-seed model differences
are given, negative Skill/R² retained.

The cross terms in Table B (expanded model on the original test and vice versa) are **not**
called out-of-distribution as a blanket statement. Each arm's test distribution differs from the
other model's training distribution mainly in the ratio coordinates: the shared scales are drawn
from the same prior and mostly inside both training supports, whereas the ratio coordinates
differ in support and (for the equal-volume design) in local density. Results must therefore be
read per coordinate family; a single "OOD" label for the whole six-coordinate vector would
overstate what is known.

Paired differences (`paired_differences.csv`, `paired_difference_summary.csv`) are
`expanded − original` per seed, with mean, sample SD, and the count of positive/negative seeds.
The five seeds are five training runs on one data set, not five independent simulation data
sets; no significance test is added.

## 7. Execution notes (implementation, not design changes)

- Keras 3 no longer infers the optimisation direction from a metric name, so the callbacks carry
  an explicit `mode="min"`. This states what Keras 2 inferred for the `*loss` monitors; no
  monitored quantity, patience or threshold changed.
- Keras 3 refuses `save_weights()` on the subclassed VAE container (it has no `build()` of its own
  because `train_step` drives the submodels directly). The best-`val_loss` checkpoint is therefore
  written from the three functional submodels (`encoder/decoder/param_head.weights.h5`), same
  monitor and same save-best-only rule.
- `tensorflow` 2.20.0 is the version recorded in the paper's environment notes; it was installed
  locally for this experiment. Deterministic ops are enabled
  (`tf.config.experimental.enable_op_determinism()`), and oneDNN custom ops are disabled to keep
  numerical reduction order reproducible.
- The ten runs are driven by `scripts/07_run_formal.py`: one worker per arm, so both arms meet the
  same concurrent CPU load at each seed step. Per-run wall time, status and stop reason are logged.

## 8. Isolation of the small-batch pipeline test

`scripts/03a_smoke_test.py` used 512 train / 128 validation rows and 2 epochs per arm. It checked
forward pass, the three loss terms, an explicit gradient-tape step (all gradients present,
non-zero global norm), `fit`, save/load of the encoder with the custom `Sampling` layer,
inverse transformation through the parameter scaler, and evaluation — on **validation only**. It
asserted that no test row was touched, wrote only to `models/_smoke` and `logs/_smoke`, used seed 7,
and selected no hyperparameter from any score. Its weights were never used as a formal
initialisation.

A separate 3-epoch timing probe (`--tag timing`) measured ≈1.3 s/epoch; its weights were deleted
and are excluded from the model set. It is recorded here and in `logs/` so the probe is not
mistaken for one of the ten formal runs.
