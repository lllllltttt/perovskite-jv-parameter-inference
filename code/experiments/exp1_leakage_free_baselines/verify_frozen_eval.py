# -*- coding: utf-8 -*-
"""
Phase-0 anchor: reproduce the frozen VAE-v6 evaluation numbers using the
frozen checkpoint + frozen sigma convention, writing ONLY to this experiment
directory. Mirrors script/VAE_v6_eval_fixed.py logic; must not touch
evaluation_fixed/.
"""
import os, io, sys
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from scipy.stats import pearsonr, spearmanr

BASE = r"E:\project\work1"
EXPDIR = r"E:\project\work1\reviewer_experiments\exp1_leakage_free_baselines"
NPZ_PATH = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}
PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]

out = io.open(os.path.join(EXPDIR, "phase0_frozen_eval_repro.txt"), "w", encoding="utf-8")
def P(*a):
    print(*a)
    out.write(" ".join(str(x) for x in a) + "\n")

class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps

def sigma_fixed(raw):
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)

data = np.load(NPZ_PATH, allow_pickle=True)
J_test = data["J_test"].astype(np.float32)
params_test = data["params_test"].astype(np.float32)
P("test:", J_test.shape, params_test.shape)

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
decoder = keras.models.load_model(os.path.join(MODEL_DIR, "decoder.h5"))
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

z_mean, z_log_var, z = encoder.predict(J_test, verbose=0)
recon_test = decoder.predict(z_mean, verbose=0)
param_mu, sigma_raw = param_head.predict(z_mean, verbose=0)
param_sigma = sigma_fixed(sigma_raw)

error = np.abs(params_test - param_mu)
pearson = np.zeros(9); mae = np.zeros(9); rmse = np.zeros(9)
for i in range(9):
    r, _ = pearsonr(params_test[:, i], param_mu[:, i])
    pearson[i] = r
    mae[i] = float(np.mean(error[:, i]))
    rmse[i] = float(np.sqrt(np.mean((params_test[:, i] - param_mu[:, i]) ** 2)))

P("===== FROZEN VAE-v6 point recovery (reference anchor) =====")
for i, name in enumerate(PARAM_NAMES):
    P("%-12s r=%.4f  MAE=%.5f  RMSE=%.5f" % (name, pearson[i], mae[i], rmse[i]))
P("mean r: %.4f" % np.mean(pearson))

spearman_fixed = np.zeros(9)
for i in range(9):
    rho_f, p_f = spearmanr(param_sigma[:, i], error[:, i])
    spearman_fixed[i] = rho_f
P("mean Spearman(sigma,|err|): %.4f" % np.mean(spearman_fixed))

levels = sorted(NOMINAL.keys())
emp_cov = np.zeros((9, len(levels)))
for j, lvl in enumerate(levels):
    zz = NOMINAL[lvl]
    lo = param_mu - zz * param_sigma
    hi = param_mu + zz * param_sigma
    emp_cov[:, j] = np.mean((params_test >= lo) & (params_test <= hi), axis=0)
P("===== FROZEN VAE-v6 coverage (reference anchor) =====")
for j, lvl in enumerate(levels):
    P("nominal=%.2f  cov min/max: %.4f / %.4f" % (lvl, emp_cov[:, j].min(), emp_cov[:, j].max()))
    for i, name in enumerate(PARAM_NAMES):
        P("   %-12s %.4f" % (name, emp_cov[i, j]))
P("95%% coverage range: %.4f - %.4f" % (emp_cov[:, -1].min(), emp_cov[:, -1].max()))

mse = np.mean((J_test - recon_test) ** 2, axis=1)
P("recon mean MSE: %.6e   median MSE: %.6e" % (mse.mean(), np.median(mse)))

# sigma stats
P("===== FROZEN VAE-v6 sigma (mean/median per param) =====")
for i, name in enumerate(PARAM_NAMES):
    s = param_sigma[:, i]
    P("%-12s mean=%.5f median=%.5f" % (name, s.mean(), np.median(s)))

out.close()
print("saved:", out.name)
