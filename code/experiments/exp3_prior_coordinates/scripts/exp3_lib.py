# -*- coding: utf-8 -*-
"""
EXP3 shared library — prior-coordinate recoverability analysis.

Inference/analysis only. Never trains, never writes outside EXP3.
All parameter coordinates are expressed in LOG10 PHYSICAL space
(log10 of the physical parameter values) recovered via the EXACT frozen
Stage-I parameter scaler (log10 -> MinMax, fit on the FULL retained set).
"""
import os, pickle
import numpy as np
from scipy.stats import pearsonr, spearmanr

BASE = r"E:\project\work1"
EXP1 = os.path.join(BASE, "reviewer_experiments", "exp1_leakage_free_baselines")
EXP3 = os.path.join(BASE, "reviewer_experiments", "exp3_prior_coordinate_recoverability")

DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
FROZEN_VAE = os.path.join(BASE, "data", "vae-v6", "vae-v6")

# manuscript parameter order
PARAM_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]

# 0-based indices of the six paired bulk parameters
PAIR_ORDER = ["mobility", "lifetime", "DOS"]
PAIRS = {"mobility": (0, 1), "lifetime": (2, 3), "DOS": (4, 5)}
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
PAIR_OF_COORD = {"a_mu": "mobility", "r_mu": "mobility",
                 "a_tau": "lifetime", "r_tau": "lifetime",
                 "a_D": "DOS", "r_D": "DOS"}
COORD_LABEL = {
    "a_mu": "shared scale, mobility", "r_mu": "log-ratio, mobility",
    "a_tau": "shared scale, lifetime", "r_tau": "log-ratio, lifetime",
    "a_D": "shared scale, DOS", "r_D": "log-ratio, DOS",
}

# ----------------------------------------------------------------------
# frozen (full-data) parameter scaler -> log10 physical
# ----------------------------------------------------------------------
_NPZ = None
def _npz():
    global _NPZ
    if _NPZ is None:
        _NPZ = np.load(DATA_NPZ)
    return _NPZ

_FROZEN = None
def frozen_scaler():
    global _FROZEN
    if _FROZEN is None:
        with open(os.path.join(BASE, "data", "param_scaler.pkl"), "rb") as f:
            _FROZEN = pickle.load(f)["scaler"]
    return _FROZEN

def frozen_norm_to_log10(norm):
    """(N,9) normalized log10 values -> (N,9) log10 physical."""
    sc = frozen_scaler()
    return np.asarray(norm, np.float64) * sc.data_range_ + sc.data_min_

def frozen_test():
    """Frozen normalized test J/params + raw physical test J/params."""
    d = _npz()
    return dict(
        J_test=d["J_test"].astype(np.float32),
        params_test=d["params_test"].astype(np.float32),
        params_test_raw=d["params_test_raw"].astype(np.float64),
        J_test_raw=d["J_test_raw"].astype(np.float64),
    )

def frozen_train_params_log10():
    """Frozen normalized TRAIN params -> (N,9) log10 physical. Train-only."""
    return frozen_norm_to_log10(_npz()["params_train"].astype(np.float64))

def frozen_retained_params_log10():
    """FULL retained population (train+val+test, N=102046) -> log10 physical."""
    L = [frozen_norm_to_log10(_npz()[k].astype(np.float64))
         for k in ("params_train", "params_val", "params_test")]
    return np.concatenate(L, axis=0)

# ----------------------------------------------------------------------
# coordinate transforms (exact log-space identities, log10 physical input)
# ----------------------------------------------------------------------
def coords_from_log10(L):
    """(N,9) log10 physical -> (N,6) [a_mu, r_mu, a_tau, r_tau, a_D, r_D]."""
    L = np.asarray(L, np.float64)
    return np.column_stack([
        0.5 * (L[:, 0] + L[:, 1]),  L[:, 0] - L[:, 1],
        0.5 * (L[:, 2] + L[:, 3]),  L[:, 2] - L[:, 3],
        0.5 * (L[:, 4] + L[:, 5]),  L[:, 4] - L[:, 5],
    ])

def log10_from_coords(C):
    """(N,6) [a_mu,r_mu,a_tau,r_tau,a_D,r_D] -> (N,9) log10 physical (paired cols)."""
    C = np.asarray(C, np.float64)
    a_mu, r_mu, a_tau, r_tau, a_D, r_D = C[:, 0], C[:, 1], C[:, 2], C[:, 3], C[:, 4], C[:, 5]
    return np.column_stack([
        a_mu + 0.5 * r_mu, a_mu - 0.5 * r_mu,
        a_tau + 0.5 * r_tau, a_tau - 0.5 * r_tau,
        a_D + 0.5 * r_D, a_D - 0.5 * r_D,
    ])

def coord_metrics(coord_true, coord_pred):
    """Per-coordinate metrics in log10 units (decades). coord: (N,) float64."""
    t = np.asarray(coord_true, np.float64); p = np.asarray(coord_pred, np.float64)
    err = np.abs(t - p)
    return dict(
        pearson_r=float(pearsonr(t, p)[0]),
        spearman_rho=float(spearmanr(t, p)[0]),
        mae_decades=float(np.mean(err)),
        rmse_decades=float(np.sqrt(np.mean((t - p) ** 2))),
        median_abs_log_error=float(np.median(err)),
        p90_abs_log_error=float(np.percentile(err, 90)),
        median_abs_ratio_error=float(np.median(err)),   # same quantity, in decades
        ratio_factor=float(10.0 ** np.median(err)),
    )

# ----------------------------------------------------------------------
# EXP1 leakage-free checkpoints (read precomputed eval_bundle.npz; no retrain)
# ----------------------------------------------------------------------
_LF_NPZ = None
def lf_npz():
    global _LF_NPZ
    if _LF_NPZ is None:
        _LF_NPZ = np.load(os.path.join(EXP1, "leakage_free_dataset.npz"))
    return _LF_NPZ

_LF_SC = None
def lf_scaler():
    global _LF_SC
    if _LF_SC is None:
        with open(os.path.join(EXP1, "train_only_scalers.pkl"), "rb") as f:
            _LF_SC = pickle.load(f)
    return _LF_SC

def lf_test_true_log10():
    """log10 physical true test params under the leakage-free protocol."""
    return np.log10(lf_npz()["params_test_raw"].astype(np.float64))

def lf_norm_to_log10(norm):
    """Invert the train-only param scaler: normalized -> log10 physical."""
    sc = lf_scaler()
    mn = sc["param_min_log10"].astype(np.float64)
    mx = sc["param_max_log10"].astype(np.float64)
    return np.asarray(norm, np.float64) * (mx - mn) + mn

def exp1_eval_bundle(family, seed):
    return np.load(os.path.join(EXP1, "models", family, "seed%d" % seed,
                                "eval_bundle.npz"), allow_pickle=True)

FAMILIES = ["vae", "det_ae", "mlp"]
SEEDS = [20260824, 20260825, 20260826, 20260827, 20260828]

# ----------------------------------------------------------------------
# frozen model z_mean predictions (inference only)
# ----------------------------------------------------------------------
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

class _Sampling(layers.Layer):
    """Frozen encoder Sampling layer (custom_objects on load)."""
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps

_ENC = _PH = None
def _frozen_submodels():
    global _ENC, _PH
    if _ENC is None:
        _ENC = keras.models.load_model(
            os.path.join(FROZEN_VAE, "encoder.h5"),
            custom_objects={"Sampling": _Sampling, "_Sampling": _Sampling})
        _PH = keras.models.load_model(os.path.join(FROZEN_VAE, "param_head.h5"))
    return _ENC, _PH

def frozen_pred_log10():
    """Frozen VAE-v6 z_mean point predictions -> (N,9) log10 physical."""
    enc, ph = _frozen_submodels()
    t = frozen_test()
    z_out = enc.predict(t["J_test"], verbose=0)
    z_mean = np.asarray(z_out[0], np.float64)
    mu = np.asarray(ph(tf.constant(np.asarray(z_mean, np.float32)), training=False)[0],
                    np.float64)
    return frozen_norm_to_log10(mu)
