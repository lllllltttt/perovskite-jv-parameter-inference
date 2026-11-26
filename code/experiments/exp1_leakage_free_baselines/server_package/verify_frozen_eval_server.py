# -*- coding: utf-8 -*-
"""
Server-side copy of the Phase-0 frozen anchor check. Paths are derived from this
script's own location (data_frozen/ subdir), so it runs unchanged on any OS.
Writes phase0_frozen_eval_repro_server.txt in this directory.
Expected (matches frozen Stage-I / phase0_frozen_eval_repro.txt):
  mean Pearson r = 0.8069 ; 95% coverage range 0.9464-0.9692 ;
  mean Spearman(sigma,|err|) = 0.4283 ; recon mean MSE 1.211244e-05.
"""
import os, io
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from scipy.stats import pearsonr, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ_PATH = os.path.join(HERE, "data_frozen", "dataset_normalized.npz")
MODEL_DIR = os.path.join(HERE, "data_frozen", "vae-v6")

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}
PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]

out = io.open(os.path.join(HERE, "phase0_frozen_eval_repro_server.txt"), "w", encoding="utf-8")
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
P("TF version:", tf.__version__)
P("GPU visible:", [d.name for d in tf.config.list_physical_devices("GPU")])

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
decoder = keras.models.load_model(os.path.join(MODEL_DIR, "decoder.h5"))
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

z_mean, z_log_var, z = encoder.predict(J_test, verbose=0)
recon_test = decoder.predict(z_mean, verbose=0)
param_mu, sigma_raw = param_head.predict(z_mean, verbose=0)
param_sigma = sigma_fixed(sigma_raw)

error = np.abs(params_test - param_mu)
pearson = np.zeros(9)
for i in range(9):
    r, _ = pearsonr(params_test[:, i], param_mu[:, i])
    pearson[i] = r
P("===== FROZEN VAE-v6 point recovery (reference anchor) =====")
for i, name in enumerate(PARAM_NAMES):
    P("%-12s r=%.4f" % (name, pearson[i]))
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
P("95%% coverage range: %.4f - %.4f" % (emp_cov[:, -1].min(), emp_cov[:, -1].max()))

mse = np.mean((J_test - recon_test) ** 2, axis=1)
P("recon mean MSE: %.6e   median MSE: %.6e" % (mse.mean(), np.median(mse)))
out.close()
print("saved:", out.name)
