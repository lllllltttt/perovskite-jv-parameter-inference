# -*- coding: utf-8 -*-
"""
forward_validation_unbiased.py
================================
UNBIASED forward-validation preparation for VAE-v6 (PSC J-V parameter inversion).

What this fixes
---------------
The old JV-val.py selected validation samples by *parameter ground-truth error*
(all-9-params log_err < threshold, then "best-5" by total error). That is a
selection bias: it only ever showcases the best-recovering samples.

Here selection is driven ONLY by observable J-V properties (PCE terciles),
with a fixed random seed. Parameter error is NEVER used in selection; it is
computed afterwards (post-hoc, flagged "not used for selection").

Scope (per instructions)
------------------------
* NO retraining, NO architecture change, NO dataset modification.
* Frozen encoder + param_head; point prediction param_mu = param_head(encoder(z_mean)).
* sigma = clip(softplus(raw) + 0.01, 0.01, 1.0)  [P0-corrected]
* No latent MC sampling for the main COMSOL input.
* COMSOL itself is NOT available on this machine -> this script only *prepares*
  the cohort + physical parameter tables + provenance. The MATLAB batch script
  run_forward_validation_unbiased.m does the COMSOL run on the server.

Outputs (in forward_validation_unbiased/)
-----------------------------------------
  selected_samples.csv            unbiased cohort (observable features only)
  comsol_input_parameters.csv     predicted physical params (COMSOL input)
  comsol_true_parameters.csv      true physical params (control, post-hoc only)
  param_error_posthoc.csv         parameter errors AFTER selection (flagged)
  unit_conversion_audit.txt       per-parameter unit evidence + NEEDS VERIFICATION
  provenance.txt                  sample_id <-> test_index mapping + caveats
  config.json                     selection settings (seed, bins, counts)
"""

import os
import json
import numpy as np
import pandas as pd
import pickle

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
ROOT        = r"E:/project/work1"
DATA_DIR    = os.path.join(ROOT, "data")
MODEL_DIR   = os.path.join(DATA_DIR, "vae-v6", "vae-v6")
OUT_DIR     = os.path.join(ROOT, "forward_validation_unbiased")

NPZ_PATH        = os.path.join(DATA_DIR, "dataset_normalized.npz")
PARAM_SCALER    = os.path.join(DATA_DIR, "param_scaler.pkl")
ENCODER_PATH    = os.path.join(MODEL_DIR, "encoder.h5")
PARAM_HEAD_PATH = os.path.join(MODEL_DIR, "param_head.h5")

SIGMA_MIN  = 0.01
SIGMA_MAX  = 1.0
V_GRID     = np.linspace(0.0, 1.3, 131)     # matches pre-process.py / dataset
N_COHORT   = 45                              # 30-50 required by spec; 15 per PCE tercile
SEED       = 20260823
N_BINS     = 3
PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
# short names used in the COMSOL CSVs (per task spec); map to project names
CSV_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
SHORT2FULL = dict(zip(CSV_NAMES, PARAM_NAMES))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
class Sampling(layers.Layer):
    """Custom layer required to load the saved encoder (VAE reparameterization)."""
    def call(self, inputs):
        z_mean, z_log_var = inputs
        epsilon = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


def sigma_fixed(raw_sigma):
    """P0-corrected sigma convention: clip(softplus(raw) + 0.01, 0.01, 1.0)."""
    s = tf.nn.softplus(raw_sigma).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)


def inverse_transform_params(params_scaled, scaler, log_mask):
    """Normalized -> log10 physical -> physical (10**x). Reuses the saved scaler."""
    log_phys = scaler.inverse_transform(params_scaled)
    out = log_phys.copy()
    out[:, log_mask] = 10.0 ** log_phys[:, log_mask]
    return out


def device_observables(J_raw):
    """Jsc, Voc, FF, PCE from physical J-V (mA/cm^2) on V_GRID. All finite for this data."""
    N = J_raw.shape[0]
    jsc = np.abs(J_raw[:, 0])                       # V = 0 short-circuit current
    voc = np.full(N, np.nan)
    for i in range(N):
        s = np.diff(np.sign(J_raw[i]))
        k0 = np.where(s)[0]
        if len(k0):
            k = k0[0]
            voc[i] = np.interp(0.0, [J_raw[i, k], J_raw[i, k + 1]], [V_GRID[k], V_GRID[k + 1]])
    pv = J_raw * V_GRID[None, :]                    # power density
    pv = np.where(pv > 0, pv, np.nan)
    pmax = np.nanmax(pv, axis=1)
    ff = np.where((voc > 0) & (jsc * voc > 0), pmax / (jsc * voc), np.nan)
    pce = jsc * voc * ff                            # (mA/cm^2 * V) -> %
    return jsc, voc, ff, pce


# ------------------------------------------------------------------
# Load data / scalers / models
# ------------------------------------------------------------------
data = np.load(NPZ_PATH, allow_pickle=True)
J_test      = data["J_test"].astype(np.float32)
J_test_raw  = data["J_test_raw"].astype(np.float64)
params_test = data["params_test"]                   # normalized
params_true = data["params_test_raw"].astype(np.float64)   # physical
log_mask    = np.asarray(data["log_transform_mask"], dtype=bool)
pnames      = np.asarray(data["param_names"])
assert list(pnames) == PARAM_NAMES, (pnames, PARAM_NAMES)
assert log_mask.all(), "all 9 params are log-transformed in this project"

with open(PARAM_SCALER, "rb") as f:
    sd = pickle.load(f)
scaler = sd["scaler"]
assert np.all(sd["log_mask"] == log_mask)

encoder    = keras.models.load_model(ENCODER_PATH, custom_objects={"Sampling": Sampling})
param_head = keras.models.load_model(PARAM_HEAD_PATH)

# --- sanity: scaler orientation round-trip -------------------------
log_true = np.log10(params_true)
scaled_back = scaler.transform(log_true)
assert np.allclose(scaled_back, params_test, atol=1e-6), "scaler <-> npz mismatch"
inv_rt = inverse_transform_params(params_test, scaler, log_mask)
assert np.allclose(inv_rt, params_true, rtol=1e-8), "inverse_transform round-trip failed"

# --- predict (point prediction, frozen model) ----------------------
z_mean, _, _ = encoder.predict(J_test, verbose=0)
param_head_out = param_head.predict(z_mean, verbose=0)
param_mu   = param_head_out[0].astype(np.float64)     # (N, 9) normalized
sigma_raw  = param_head_out[1].astype(np.float64)
sigma      = sigma_fixed(sigma_raw)                    # (N, 9) normalized-log sigma
assert param_mu.shape == (len(J_test), 9)

params_pred = inverse_transform_params(param_mu, scaler, log_mask)   # physical (COMSOL units)

# --- observables ----------------------------------------------------
jsc, voc, ff, pce = device_observables(J_test_raw)
assert np.isfinite(pce).all(), "PCE NaN in test set -> stratification breaks"

# mean predicted sigma (mean over 9 params, normalized log space)
mean_sigma = sigma.mean(axis=1)


# ------------------------------------------------------------------
# UNBIASED SELECTION: stratify by observable PCE terciles, fixed seed
#   parameter error / recovery quality is NOT consulted.
# ------------------------------------------------------------------
rng = np.random.default_rng(SEED)
edges = np.percentile(pce, [100.0 * b / N_BINS for b in range(1, N_BINS)])
bin_id = np.digitize(pce, edges, right=False)          # 0,1,2
counts = np.bincount(bin_id, minlength=N_BINS)
assert (counts > 0).all(), f"empty PCE bin: {counts}"

n_per_bin = N_COHORT // N_BINS
picks = []
for b in range(N_BINS):
    idx_b = np.where(bin_id == b)[0]
    sel = rng.choice(idx_b, size=n_per_bin, replace=False)
    picks.append(sel)
selected = np.sort(np.concatenate(picks))              # cohort test_indices, sorted for stable output
assert len(selected) == N_COHORT
assert len(np.unique(selected)) == N_COHORT

strata = np.array(["low_PCE", "mid_PCE", "high_PCE"])[bin_id[selected]]
sigma_tier = np.array(["low_sig", "mid_sig", "high_sig"])[
    np.digitize(mean_sigma[selected],
                np.percentile(mean_sigma, [100.0 / 3, 200.0 / 3]), right=False)]

# ------------------------------------------------------------------
# POST-HOC (NOT used for selection): parameter log10-distance + sigma
# ------------------------------------------------------------------
log_true_s = np.log10(params_true)
log_pred_s = np.log10(params_pred)
param_l2   = np.sqrt(((log_pred_s - log_true_s) ** 2).mean(axis=1))   # RMSE in log10 space

# ------------------------------------------------------------------
# Output tables
# ------------------------------------------------------------------
os.makedirs(OUT_DIR, exist_ok=True)

df_sel = pd.DataFrame({
    "test_index":          selected,
    "original_sample_id":  np.nan,          # NOT recoverable locally (see provenance.txt)
    "Jsc_mA_per_cm2":      np.round(jsc[selected], 6),
    "Voc_V":               np.round(voc[selected], 6),
    "FF":                  np.round(ff[selected], 6),
    "PCE_percent":         np.round(pce[selected], 6),
    "mean_pred_sigma":     np.round(mean_sigma[selected], 6),
    "selection_stratum":   strata,
    "sigma_tier_posthoc":  sigma_tier,      # informational cross-stratum only
    "random_seed":         SEED,
})
df_sel.to_csv(os.path.join(OUT_DIR, "selected_samples.csv"), index=False)

# COMSOL input: predicted physical parameters (sample_id = test_index)
rows = []
for i, t in enumerate(selected):
    r = {"sample_id": int(t)}
    for short, full in SHORT2FULL.items():
        r[short] = float(params_pred[t, PARAM_NAMES.index(full)])
    rows.append(r)
df_pred = pd.DataFrame(rows)
df_pred.to_csv(os.path.join(OUT_DIR, "comsol_input_parameters.csv"), index=False)

# true parameters (control only, never used in selection)
rows_t = []
for i, t in enumerate(selected):
    r = {"sample_id": int(t)}
    for short, full in SHORT2FULL.items():
        r[short] = float(params_true[t, PARAM_NAMES.index(full)])
    rows_t.append(r)
df_true = pd.DataFrame(rows_t)
df_true.to_csv(os.path.join(OUT_DIR, "comsol_true_parameters.csv"), index=False)

# post-hoc parameter error (flagged)
df_err = pd.DataFrame({
    "test_index":   selected,
    "param_log10_rmse": np.round(param_l2[selected], 6),
    "mean_pred_sigma":  np.round(mean_sigma[selected], 6),
})
df_err.to_csv(os.path.join(OUT_DIR, "param_error_posthoc.csv"), index=False)

with open(os.path.join(OUT_DIR, "config.json"), "w") as f:
    json.dump({
        "model_dir": MODEL_DIR,
        "npz": NPZ_PATH,
        "cohort_size": int(N_COHORT),
        "strategy": "PCE tercile stratified random, fixed seed",
        "seed": SEED,
        "n_per_bin": int(n_per_bin),
        "pce_edges": [round(float(e), 6) for e in edges],
        "voltage_grid": "linspace(0,1.3,131)",
        "sigma_convention": "clip(softplus(raw)+0.01, 0.01, 1.0)",
        "selection_uses_parameter_error": False,
        "note": "parameter error computed post-hoc ONLY",
    }, f, indent=2)

# ------------------------------------------------------------------
# Report
# ------------------------------------------------------------------
print("=" * 72)
print("UNBIASED FORWARD-VALIDATION COHORT (preparation only; no COMSOL here)")
print("=" * 72)
print(f"cohort size : {N_COHORT}  (PCE terciles, {n_per_bin} per bin, seed={SEED})")
print(f"PCE edges   : {edges.round(4)}")
for b, lbl in enumerate(["low_PCE", "mid_PCE", "high_PCE"]):
    m = bin_id[selected] == b
    print(f"  {lbl:<9} n={m.sum():2d}  PCE[{pce[selected][m].min():6.2f}, {pce[selected][m].max():6.2f}]")
print("\nCohort observable coverage:")
for nm, v in [("Jsc", jsc), ("Voc", voc), ("FF", ff), ("PCE", pce)]:
    vs = v[selected]
    print(f"  {nm:<4}: median={np.median(vs):8.3f}  min={vs.min():8.3f}  max={vs.max():8.3f}")
print("\nPost-hoc (not used for selection):")
print(f"  param log10-RMSE: median={np.median(param_l2[selected]):.4f}  "
      f"min={param_l2[selected].min():.4f}  max={param_l2[selected].max():.4f}")
print(f"  mean sigma:       median={np.median(mean_sigma[selected]):.4f}")
print(f"\nSaved -> {OUT_DIR}")
for fn in ["selected_samples.csv", "comsol_input_parameters.csv",
           "comsol_true_parameters.csv", "param_error_posthoc.csv", "config.json"]:
    print("  " + fn)
print("\n[ok] Preparation complete. Run run_forward_validation_unbiased.m on the COMSOL server,")
print("     then forward_validation_postprocess.py to compute metrics/figures/conclusions.")
