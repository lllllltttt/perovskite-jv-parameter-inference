# -*- coding: utf-8 -*-
"""
Pipeline reproducibility gate: run the SAME frozen inference stack on the
ORIGINAL test set (dataset_normalized.npz J_test) and confirm the metrics match
the archived evaluation_fixed outputs to high precision.

This validates that the independent-dataset numbers are comparable to the
locked-manuscript numbers (same model, same scalers, same conventions).
"""
import os, pickle
import numpy as np
import tensorflow as tf
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
from tensorflow import keras
from tensorflow.keras import layers
from scipy.stats import pearsonr, spearmanr

BASE = r"E:\project\work1"
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}
PARAM = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]

class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

d = np.load(NPZ)
J_test = d["J_test"].astype(np.float32)
params_test = d["params_test"].astype(np.float64)

def sigma_fixed(raw):
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)

z_out = encoder.predict(J_test, batch_size=1024, verbose=0)
z_mean = np.asarray(z_out[0], np.float64)
mu, raw_sigma = param_head.predict(z_mean.astype(np.float32), batch_size=1024, verbose=0)
mu = np.asarray(mu, np.float64)
sigma = sigma_fixed(raw_sigma)

err = np.abs(params_test - mu)
pearson = [pearsonr(params_test[:, i], mu[:, i])[0] for i in range(9)]
spearman = [spearmanr(sigma[:, i], err[:, i])[0] for i in range(9)]
zz = NOMINAL[0.95]
lo = mu - zz * sigma; hi = mu + zz * sigma
cov95 = np.mean((params_test >= lo) & (params_test <= hi), axis=0)

REF_P = [0.9063, 0.9194, 0.8783, 0.8808, 0.9090, 0.8956, 0.5936, 0.7199, 0.5592]
REF_C = [0.9475, 0.9522, 0.9583, 0.9597, 0.9464, 0.9499, 0.9692, 0.9667, 0.9664]
REF_S = [0.3982, 0.3343, 0.6459, 0.6218, 0.3530, 0.2444, 0.3772, 0.4647, 0.4147]

print("%-9s %8s %8s %8s | %8s %8s | %8s %8s" %
      ("param", "orig_r", "repro_r", "d_r", "orig_c95", "repro_c95", "orig_rho", "repro_rho"))
maxd_r = maxd_c = maxd_s = 0.0
for i in range(9):
    dr = abs(pearson[i] - REF_P[i]); dc = abs(cov95[i] - REF_C[i]); ds = abs(spearman[i] - REF_S[i])
    maxd_r = max(maxd_r, dr); maxd_c = max(maxd_c, dc); maxd_s = max(maxd_s, ds)
    print("%-9s %8.4f %8.4f %+8.4f | %8.4f %8.4f | %8.4f %8.4f"
          % (PARAM[i], REF_P[i], pearson[i], pearson[i]-REF_P[i],
             REF_C[i], cov95[i], REF_S[i], spearman[i]))

print("\nmax |Δ Pearson| = %.6f  max |Δ 95cov| = %.6f  max |Δ Spearman| = %.6f"
      % (maxd_r, maxd_c, maxd_s))
print("mean repro r = %.4f (ref %.4f)" % (np.mean(pearson), np.mean(REF_P)))

ok = maxd_r < 2e-3 and maxd_c < 2e-3 and maxd_s < 2e-3
print("\nREPRODUCIBILITY GATE:", "PASS" if ok else "FAIL")
