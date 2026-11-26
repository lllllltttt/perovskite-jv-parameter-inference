# -*- coding: utf-8 -*-
"""Full-test-set verification of the frozen model (15,307 curves).

This is the end-to-end check behind the paper's accuracy and calibration
numbers.  It needs the preprocessed dataset, i.e. the release asset
``dataset_main_102046.tar.gz`` (or the authoring machine's ``data/``):

    tar -xzf dataset_main_102046.tar.gz -C data/_assets
    JV_DATA_ROOT=$PWD/data/_assets python code/verify_frozen_metrics.py

It recomputes, from the frozen weights alone:

* mean and median reconstruction MSE in normalized J space;
* per-parameter Pearson r (normalized log10 space);
* per-parameter empirical coverage of the 95 % marginal Gaussian interval;
* mean Spearman correlation between the predictive scale and |error|.

Each is compared with the value printed in the paper / its supplementary
tables, embedded below as constants.  Nothing is retrained and no file is
written.  Exit code 0 means every check passed.
"""
import os
import sys

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
from tensorflow import keras            # noqa: E402
from tensorflow.keras import layers     # noqa: E402
import tensorflow as tf                 # noqa: E402

tf.get_logger().setLevel("ERROR")

NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk", "Nc_eff_pvk",
         "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]

MSE_MEAN_REF = 1.211244e-5      # Results, "Recoverability ..."
MSE_MEDIAN_REF = 2.969473e-6
R_REF = np.array([0.906268, 0.919434, 0.878266, 0.880803, 0.909047,
                  0.895604, 0.593605, 0.719923, 0.559174])       # Table 2 / S11b
COV_REF = np.array([0.947475, 0.952244, 0.958320, 0.959692, 0.946364,
                    0.949892, 0.969164, 0.966682, 0.966421])     # Table S2 (95 %)
RHO_MEAN_REF = 0.4283                                         # Results / Table S3

MSE_RTOL = 1e-3
R_ATOL = 2e-3
COV_ATOL = 3e-3
RHO_ATOL = 3e-3
Z95 = 1.959963984540054


class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        return z_mean + tf.exp(0.5 * z_log_var) * tf.random.normal(tf.shape(z_mean))


def main():
    npz = paths.data_file("dataset_normalized.npz")
    if not os.path.exists(npz):
        print(f"missing {npz}\n"
              "unpack dataset_main_102046.tar.gz and set JV_DATA_ROOT")
        return 2

    d = np.load(npz, allow_pickle=True)
    J = d["J_test"].astype(np.float32)
    P = d["params_test"]
    if J.shape != (15307, 131):
        print(f"unexpected test shape {J.shape}")
        return 2

    enc = keras.models.load_model(paths.model_file("encoder.h5"),
                                  custom_objects={"Sampling": Sampling}, compile=False)
    dec = keras.models.load_model(paths.model_file("decoder.h5"), compile=False)
    head = keras.models.load_model(paths.model_file("param_head.h5"), compile=False)

    z, _, _ = enc.predict(J, batch_size=1024, verbose=0)
    recon = dec.predict(z, batch_size=1024, verbose=0)
    out = head.predict(z, batch_size=1024, verbose=0)
    mu = out[0]
    sigma = np.clip(tf.nn.softplus(out[1]).numpy() + 0.01, 0.01, 1.0)
    err = np.abs(mu - P)

    fails = []

    per_curve = np.mean((J - recon) ** 2, axis=1)
    mse_mean, mse_med = float(per_curve.mean()), float(np.median(per_curve))
    print(f"n = {J.shape[0]}")
    print(f"{'reconstruction MSE mean':28s} {mse_mean:.6e}  ref {MSE_MEAN_REF:.6e}")
    print(f"{'reconstruction MSE median':28s} {mse_med:.6e}  ref {MSE_MEDIAN_REF:.6e}")
    for nm, val, ref in (("mean", mse_mean, MSE_MEAN_REF),
                         ("median", mse_med, MSE_MEDIAN_REF)):
        if abs(val - ref) / ref > MSE_RTOL:
            fails.append(f"MSE {nm} {val:.6e} vs {ref:.6e}")

    r = np.array([np.corrcoef(mu[:, i], P[:, i])[0, 1] for i in range(9)])
    cov = (err <= Z95 * sigma).mean(axis=0)
    rho = np.array([spearmanr(sigma[:, i], err[:, i]).statistic for i in range(9)])

    print(f"\n{'parameter':12s} {'r':>8s} {'ref':>8s} {'cov95':>8s} {'ref':>8s} "
          f"{'rho':>8s}")
    for i, n in enumerate(NAMES):
        print(f"{n:12s} {r[i]:8.4f} {R_REF[i]:8.4f} {cov[i]:8.4f} {COV_REF[i]:8.4f} "
              f"{rho[i]:8.4f}")
        if abs(r[i] - R_REF[i]) > R_ATOL:
            fails.append(f"r[{n}] {r[i]:.4f} vs {R_REF[i]:.4f}")
        if abs(cov[i] - COV_REF[i]) > COV_ATOL:
            fails.append(f"cov95[{n}] {cov[i]:.4f} vs {COV_REF[i]:.4f}")
    print(f"{'mean rho':12s} {rho.mean():8.4f} {'':8s} (ref {RHO_MEAN_REF:.4f})")
    if abs(rho.mean() - RHO_MEAN_REF) > RHO_ATOL:
        fails.append(f"mean rho {rho.mean():.4f} vs {RHO_MEAN_REF}")

    if fails:
        print("\nFAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("\nPASS: frozen model reproduces the published test-set metrics.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
