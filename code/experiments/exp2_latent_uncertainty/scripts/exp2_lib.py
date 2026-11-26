# -*- coding: utf-8 -*-
"""
exp2_lib.py — shared library for EXP2 latent-uncertainty decomposition.

INFERENCE-ONLY. Loads the frozen Stage-I VAE-v6 (data/vae-v6/vae-v6/) and
the EXP1 leakage-free VAE checkpoints WITHOUT retraining. No weights are
ever modified; no optimizer is ever invoked.

Core quantities (spec §3):
  V_head   = E_z[ sigma_theta(z)^2 ]                 (Gaussian-head variance)
  V_latent = Var_z[ mu_theta(z) ]                    (latent-induced variance, ddof=0)
  V_total  = V_head + V_latent                       (law of total variance)
  mu_total = E_z[ mu_theta(z) ]                      (total predictive mean)
  sigma_total = sqrt(V_total)
  f_latent = V_latent / V_total ; f_head = 1 - f_latent

Monte-Carlo estimates use M draws z^(m) ~ q(z|J) = N(z_mean, diag(exp(0.5 z_log_var))^2)
and evaluate the frozen Gaussian parameter head at every draw.

Terminology discipline (spec §1): everything here is "model-implied predictive"
variation. Nothing is claimed to be a Bayesian posterior over physical parameters.

Conventions locked to the frozen evaluation (script/VAE_v6_eval_fixed.py):
  sigma = clip(softplus(raw) + 0.01, 0.01, 1.0)
  point evaluation at z = z_mean for "current".
"""
import os, pickle
import numpy as np
from scipy.stats import pearsonr, spearmanr

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

BASE = r"E:\project\work1"
EXP2 = os.path.join(BASE, "reviewer_experiments", "exp2_latent_uncertainty_decomposition")
EXP1 = os.path.join(BASE, "reviewer_experiments", "exp1_leakage_free_baselines")
FROZEN_MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
FROZEN_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
INPUT_DIM, LATENT_DIM, N_PARAM = 131, 9, 9
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}

PARAM_FULL = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
              "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
PARAM_SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
               "tau_ETL", "tau_HTL", "rad_c"]

# log10 domain range (decades) consumed by the frozen model — from the FULL-data
# parameter scaler (data/param_scaler.pkl): all 9 params are log10-transformed,
# so one unit of normalized space == log_range_j log10 decades.
PARAM_LOG_RANGE = np.array([3.689340, 3.669144, 7.664964, 7.658352,
                            3.681787, 3.703979, 4.000000, 4.000000, 3.000000])


class _Sampling(layers.Layer):
    """Sampling layer required to deserialize the frozen encoder.h5."""
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def softplus_np(x):
    """Stable softplus; matches tf.nn.softplus to float precision."""
    x = np.asarray(x, dtype=np.float64)
    return np.maximum(x, 0.0) + np.log1p(np.exp(-np.abs(x)))


def sigma_fixed_np(raw):
    """Frozen sigma convention: clip(softplus(raw)+0.01, 0.01, 1.0)."""
    s = softplus_np(raw) + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX).astype(np.float32)


# ---------------- frozen model loading ----------------

def load_frozen_submodels(model_dir=FROZEN_MODEL_DIR):
    encoder = keras.models.load_model(
        os.path.join(model_dir, "encoder.h5"),
        custom_objects={"Sampling": _Sampling, "_Sampling": _Sampling})
    param_head = keras.models.load_model(os.path.join(model_dir, "param_head.h5"))
    return encoder, param_head


def load_frozen_test():
    """Frozen (full-data-scaler) test split from the archived npz."""
    d = np.load(FROZEN_NPZ, allow_pickle=True)
    return (d["J_test"].astype(np.float32), d["params_test"].astype(np.float32))


def load_lf_test():
    """Leakage-free (train-only scaler) test split for the EXP1 checkpoints."""
    d = np.load(os.path.join(EXP1, "leakage_free_dataset.npz"), allow_pickle=False)
    return (d["J_test"].astype(np.float32), d["params_test"].astype(np.float32))


# ---------------- encoder pass ----------------

def encode_zstats(encoder, J):
    """Return (z_mean, z_log_var) for a J batch (single pass, deterministic)."""
    z_mean, z_log_var, _ = encoder.predict(np.asarray(J, dtype=np.float32), verbose=0)
    return z_mean.astype(np.float32), z_log_var.astype(np.float32)


# ---------------- Monte-Carlo decomposition ----------------

def param_head_batch(param_head, z):
    """Forward the frozen param_head on a (B,9) tensor; returns (mu, sigma)."""
    out = param_head(tf.constant(np.asarray(z, dtype=np.float32)), training=False)
    mu = np.asarray(out[0], dtype=np.float32)
    raw = np.asarray(out[1], dtype=np.float32)
    return mu, sigma_fixed_np(raw)


def decompose_zs(z_mean, z_log_var, eps, param_head):
    """
    Full per-sample Monte-Carlo decomposition.

    z_mean, z_log_var : (S, 9) per-sample encoder stats (S = n test samples)
    eps               : (S, M, 9) standard-normal draws (already drawn, seeded)
    param_head        : frozen head model

    Returns dict with per-sample (S, 9) float32 arrays:
      mu_current, sigma_current, mu_total, sigma_total,
      V_head, V_latent, V_total, f_latent, f_head, delta_mu, ratio_sigma,
      sigma_head, sigma_latent   (sqrt of V_head / V_latent per sample)
    """
    S, M, D = eps.shape
    z = (z_mean[:, None, :] + np.exp(0.5 * z_log_var)[:, None, :] * eps)  # (S,M,9)
    mu, sigma = param_head_batch(param_head, z.reshape(-1, D))           # (S*M, 9)
    mu = mu.reshape(S, M, D)
    sigma = sigma.reshape(S, M, D)

    mu_total = mu.mean(axis=1)                                   # E_z[mu]
    V_head = (sigma ** 2).mean(axis=1)                           # E_z[sigma^2]
    V_latent = mu.var(axis=1)                                    # population var (ddof=0)
    V_total = V_head + V_latent
    f_latent = np.zeros_like(V_total)
    nz = V_total > 1e-12
    f_latent[nz] = V_latent[nz] / V_total[nz]
    f_head = 1.0 - f_latent

    # current (z_mean) evaluation
    mu_zm, sig_zm = param_head_batch(param_head, z_mean)
    mu_current = mu_zm.reshape(S, D)
    sigma_current = sig_zm.reshape(S, D)

    sigma_total = np.sqrt(V_total)
    sigma_head = np.sqrt(V_head)
    sigma_latent = np.sqrt(V_latent)

    return dict(mu_current=mu_current, sigma_current=sigma_current,
                mu_total=mu_total, sigma_total=sigma_total,
                V_head=V_head, V_latent=V_latent, V_total=V_total,
                f_head=f_head, f_latent=f_latent,
                delta_mu=mu_total - mu_current,
                ratio_sigma=sigma_total / np.maximum(sigma_current, 1e-12),
                sigma_head=sigma_head, sigma_latent=sigma_latent)


def draw_eps(n_samples, M, seed):
    """Reproducible standard-normal draw array (n_samples, M, 9)."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n_samples, M, LATENT_DIM)).astype(np.float32)


# ---------------- mixture predictive quantiles ----------------

def mixture_quantiles(mu, sigma, K, qs, seed):
    """
    Draw theta ~ N(mu, sigma) for K samples per latent draw, return empirical
    quantiles per test sample/parameter.

    mu, sigma : (S, M, 9) per-draw head outputs
    qs        : quantile fractions to estimate (e.g. [0.025, 0.25, 0.75, 0.975])
    Returns   : (len(qs), S, 9) quantile estimates.
    """
    S, M, D = mu.shape
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((S, M, K, D)).astype(np.float32)
    th = mu[:, :, None, :] + sigma[:, :, None, :] * e            # (S, M, K, D)
    th = th.reshape(S, M * K, D)
    q = np.quantile(th, qs, axis=1)                              # (len(qs), S, D)
    return q.astype(np.float32)


# ---------------- metrics ----------------

def per_param_pearson(true, pred):
    return np.array([pearsonr(true[:, j], pred[:, j])[0] for j in range(9)])


def per_param_spearman(a, b):
    return np.array([spearmanr(a[:, j], b[:, j])[0] for j in range(9)])


def coverage_at_levels(true, lo, hi, levels=None):
    """Empirical coverage per parameter at each nominal level -> (9, len(levels)).
    lo, hi are (N,9) or (N,9,L); per-level slices are used."""
    levels = sorted(NOMINAL.keys()) if levels is None else levels
    cov = np.zeros((9, len(levels)))
    for j, lvl in enumerate(levels):
        _lo = lo[..., j] if np.ndim(lo) == 3 else lo
        _hi = hi[..., j] if np.ndim(hi) == 3 else hi
        cov[:, j] = np.mean((true >= _lo) & (true <= _hi), axis=0)
    return cov


def gaussian_intervals(mu, sigma, levels=None):
    """Return (lo, hi) arrays (N,9,len(levels)) for mu +/- z*sigma."""
    levels = sorted(NOMINAL.keys()) if levels is None else levels
    lo = np.stack([mu - NOMINAL[lvl] * sigma for lvl in levels], axis=-1)
    hi = np.stack([mu + NOMINAL[lvl] * sigma for lvl in levels], axis=-1)
    return lo, hi
