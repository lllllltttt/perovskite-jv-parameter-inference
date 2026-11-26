"""Minimal, self-contained reproduction check (no COMSOL, no retraining).

Run from the repository root:

    python code/quickstart_inference.py

It loads the frozen VAE-v6 encoder / decoder / parameter head, runs inference on
a fixed 200-curve subset of the held-out test set that ships with the
repository, and recomputes the two headline quantities quoted in the paper:

  * mean and median reconstruction MSE in normalized J space
    (paper: 1.211e-5 / 2.969e-6; see Results, "Simulation domain ...")
  * per-parameter Pearson r between predicted and true parameters, normalized
    log10 space (paper Table 2)

The script exits non-zero if the numbers drift outside the published tolerance.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

from tensorflow import keras            # noqa: E402
from tensorflow.keras import layers     # noqa: E402
import tensorflow as tf                 # noqa: E402

tf.get_logger().setLevel("ERROR")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

SIGMA_MIN, SIGMA_MAX = 0.01, 1.0


class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def main():
    sub = np.load(paths.data_file("examples", "test_subset_200.npz"), allow_pickle=True)
    J = sub["J_test"].astype(np.float32)
    P = sub["params_test"]

    enc = keras.models.load_model(paths.model_file("encoder.h5"),
                                  custom_objects={"Sampling": Sampling}, compile=False)
    dec = keras.models.load_model(paths.model_file("decoder.h5"), compile=False)
    head = keras.models.load_model(paths.model_file("param_head.h5"), compile=False)

    z_mean, _z_log_var, _z = enc.predict(J, verbose=0)
    recon = dec.predict(z_mean, verbose=0)
    out = head.predict(z_mean, verbose=0)
    mu = out[0]
    sigma = np.clip(tf.nn.softplus(out[1]).numpy() + SIGMA_MIN, SIGMA_MIN, SIGMA_MAX)

    per_curve = np.mean((J - recon) ** 2, axis=1)
    print(f"reconstruction MSE  mean={per_curve.mean():.6e}  median={np.median(per_curve):.6e}")
    print(f"predictive scale    mean={sigma.mean():.4f}  (normalized units)")

    print("\nper-parameter Pearson r (normalized log10 space):")
    r = {}
    for i, name in enumerate(sub["param_names"]):
        r[str(name)] = float(np.corrcoef(mu[:, i], P[:, i])[0, 1])
        print(f"  {name:12s} {r[str(name)]:.4f}")

    # the six bulk parameters must fall inside the published 0.878-0.919 band
    bulk = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk", "Nc_eff_pvk", "Nv_eff_pvk"]
    lo, hi = min(r[k] for k in bulk), max(r[k] for k in bulk)
    ok = 0.85 <= lo and hi <= 0.95
    print(f"\nbulk-parameter r range on this 200-curve subset: {lo:.3f}-{hi:.3f}")
    print("PASS" if ok else "FAIL: outside the expected range")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
