# -*- coding: utf-8 -*-
"""
Cross-environment numerical QC (EXP2 spec §17).

SELF-CONTAINED: runs identically on the local box and on the server
(no import of exp2_lib). Uses 500 fixed test samples (seed 20260825) and the
FROZEN Stage-I VAE-v6. Recomputes the decomposition (M=500, seeded draws)
and prints a compact JSON summary of:
  per-parameter median f_latent, median sigma_total, median ratio_sigma,
  mean mu_total, 95% moment-matched coverage

Usage:  python server_qc.py [--out <path.json>] [--tag local|server]
Run locally and on the server; compare the two JSON files.
Without arguments it writes cross_env_server.json with env=local (double-clicking
the script or RUN_ME.bat works; RUN_ME.bat passes --tag server automatically).

Files needed (in the same working directory):
  data_frozen/vae-v6/{encoder,param_head}.h5
  data_frozen/dataset_normalized.npz
"""
import os, sys, json, argparse
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
N_PARAM = 9
SUBSET_SEED = 20260825
EPS_SEED = 20260825
M = 500
SUBSET = 500

# All defaults are anchored to THIS file's folder, so the script runs identically
# whether launched from a terminal, double-clicked, or run in an IDE whose
# working directory points elsewhere (e.g. PyCharm default = project root).
HERE = os.path.dirname(os.path.abspath(__file__))

class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps

def softplus_np(x):
    x = np.asarray(x, dtype=np.float64)
    return np.maximum(x, 0.0) + np.log1p(np.exp(-np.abs(x)))

def sigma_fixed(raw):
    s = softplus_np(raw) + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX).astype(np.float32)

def ph_batch(ph, z):
    out = ph(tf.constant(np.asarray(z, dtype=np.float32)), training=False)
    return np.asarray(out[0], np.float32), sigma_fixed(np.asarray(out[1]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "cross_env_server.json"))
    ap.add_argument("--tag", default="local",
                    help="label written into the JSON 'env' field (use 'server' on the server)")
    ap.add_argument("--model_dir", default=os.path.join(HERE, "data_frozen", "vae-v6"))
    ap.add_argument("--data", default=os.path.join(HERE, "data_frozen", "dataset_normalized.npz"))
    a = ap.parse_args()

    enc = keras.models.load_model(os.path.join(a.model_dir, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling, "_Sampling": Sampling})
    ph = keras.models.load_model(os.path.join(a.model_dir, "param_head.h5"))
    d = np.load(a.data, allow_pickle=True)
    J = d["J_test"].astype(np.float32)
    true = d["params_test"].astype(np.float32)

    rng_idx = np.random.default_rng(SUBSET_SEED)
    idx = rng_idx.choice(J.shape[0], size=SUBSET, replace=False)
    idx.sort()
    J = J[idx]; true = true[idx]

    z_mean, z_log_var, _ = enc.predict(J, verbose=0)
    z_mean = z_mean.astype(np.float32); z_log_var = z_log_var.astype(np.float32)
    rng = np.random.default_rng(EPS_SEED)
    eps = rng.standard_normal((SUBSET, M, N_PARAM)).astype(np.float32)

    z = z_mean[:, None, :] + np.exp(0.5 * z_log_var)[:, None, :] * eps
    mu_d, sig_d = ph_batch(ph, z.reshape(-1, 9))
    mu_d = mu_d.reshape(SUBSET, M, 9); sig_d = sig_d.reshape(SUBSET, M, 9)
    vh = (sig_d ** 2).mean(axis=1)
    vl = mu_d.var(axis=1)
    vt = vh + vl
    fl = np.zeros_like(vt); nz = vt > 1e-12; fl[nz] = vl[nz] / vt[nz]
    mu_tot = mu_d.mean(axis=1)
    sig_tot = np.sqrt(vt)
    mz, sz = ph_batch(ph, z_mean)
    ratio = sig_tot / np.maximum(sz, 1e-12)
    lo = mu_tot - 1.95996398 * sig_tot; hi = mu_tot + 1.95996398 * sig_tot
    cov95 = np.mean((true >= lo) & (true <= hi), axis=0)

    out = {
        "env": a.tag,
        "subset_seed": SUBSET_SEED, "eps_seed": EPS_SEED, "M": M,
        "n": int(SUBSET),
        "median_f_latent": [float(np.median(fl[:, j])) for j in range(9)],
        "median_sigma_total": [float(np.median(sig_tot[:, j])) for j in range(9)],
        "median_ratio_sigma": [float(np.median(ratio[:, j])) for j in range(9)],
        "mean_mu_total": [float(mu_tot[:, j].mean()) for j in range(9)],
        "cov95_moment": [float(c) for c in cov95],
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)
    print("saved:", a.out)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
