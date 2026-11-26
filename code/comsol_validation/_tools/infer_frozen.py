# -*- coding: utf-8 -*-
"""
infer_frozen.py -- FROZEN VAE-v6 inference (z_mean convention), TF backend.

Deterministic inference exactly as the frozen evaluation / independent-validation
path:  z_mean = encoder(J_norm)[0];  mu,sigma_raw = param_head(z_mean);
sigma = clip(softplus(sigma_raw)+0.01, 0.01, 1.0).  Point prediction = mu.
No latent re-sampling (so mesh/perturbation differences are not polluted by
sampling noise).

J_norm is the frozen per-column MinMax-normalized curve(s) (N,131), float32.
Outputs are normalized log10 units (mu) and normalized sigma.  Use v2lib
norm_to_log10 / log10_to_norm to move to log10 physical.
"""
import os
import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

BASE = r"E:\project\work1"
MODEL = os.path.join(BASE, "data", "vae-v6", "vae-v6")
SIGMA_MIN, SIGMA_MAX = 0.01, 1.0

class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        return z_mean + tf.exp(0.5 * z_log_var) * tf.random.normal(tf.shape(z_mean))

_ENC = _PH = _DEC = None

def _models():
    global _ENC, _PH, _DEC
    if _ENC is None:
        _ENC = keras.models.load_model(os.path.join(MODEL, "encoder.h5"),
                                       custom_objects={"Sampling": Sampling})
        _PH = keras.models.load_model(os.path.join(MODEL, "param_head.h5"))
        _DEC = keras.models.load_model(os.path.join(MODEL, "decoder.h5"))
    return _ENC, _PH

def decoder():
    _models()
    return _DEC

def predict(J_norm, batch_size=1024, verbose=0):
    """J_norm: (N,131) float32 normalized. Returns dict(z_mean, mu, sigma)
    all float64 (N,9); mu,sigma in normalized log10 units."""
    enc, ph = _models()
    J = np.asarray(J_norm, np.float32)
    if J.ndim == 1:
        J = J[None, :]
    z_out = enc.predict(J, batch_size=batch_size, verbose=verbose)
    z_mean = np.asarray(z_out[0], np.float64)
    preds = ph(tf.constant(np.asarray(z_mean, np.float32), dtype=tf.float32),
               training=False)
    mu = np.asarray(preds[0], np.float64)
    raw = np.asarray(preds[1], np.float64)
    sigma = np.clip(np.log1p(np.exp(raw)) + SIGMA_MIN, SIGMA_MIN, SIGMA_MAX)
    if np.isnan(mu).any() or np.isnan(sigma).any():
        raise RuntimeError("NaN in frozen inference output")
    return dict(z_mean=z_mean, mu=mu, sigma=sigma)
