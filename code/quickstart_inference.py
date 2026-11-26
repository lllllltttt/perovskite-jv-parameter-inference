# -*- coding: utf-8 -*-
"""SMOKE TEST -- not a reproduction of the paper.

This script checks that the frozen model loads and behaves as documented on a
fixed 200-curve subset of the held-out test set that ships with the repository
(``data/examples/test_subset_200.npz``).  It cannot reproduce any published
number: the paper's accuracy figures are computed on all 15,307 test curves.
For those, run ``code/verify_frozen_metrics.py`` with the full dataset.

What is asserted
----------------
* array shapes and finiteness;
* mean reconstruction MSE in normalized J space against the stored expected
  value, within 10 %;
* mean predictive scale against the stored value, within 0.01;
* per-parameter Pearson r against the stored values, within 0.02.

Why these tolerances
--------------------
On a fixed TensorFlow build the computation is deterministic: re-running with
batch sizes 32 / 64 / 128 / 200 changes the mean MSE by 7e-12 relative and
leaves every r bit-identical.  Across TensorFlow versions the archived run and
this one differ by at most 4.9e-5 in normalized parameter units, which is
~2e-6 relative on the reconstruction.  The bands above are therefore more than
1,000x the observed numerical drift, while a wrong checkpoint, wrong subset or
wrong scaler changes these values by orders of magnitude.

Run from the repository root:

    python code/quickstart_inference.py
"""
import json
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
MSE_RTOL = 0.10
SIGMA_ATOL = 0.01
R_ATOL = 0.02


class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def main():
    exp = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "data", "examples",
                                      "expected_smoke_results.json"),
                         encoding="utf-8"))
    sub = np.load(paths.data_file("examples", "test_subset_200.npz"), allow_pickle=True)
    J = sub["J_test"].astype(np.float32)
    P = sub["params_test"]

    print("SMOKE TEST on a fixed 200-curve subset (not the paper's 15,307 curves)")
    failures = []

    if J.shape != (200, 131) or P.shape != (200, 9):
        failures.append(f"unexpected shapes J={J.shape} params={P.shape}")
    if not (np.all(np.isfinite(J)) and np.all(np.isfinite(P))):
        failures.append("non-finite values in the example subset")

    enc = keras.models.load_model(paths.model_file("encoder.h5"),
                                  custom_objects={"Sampling": Sampling}, compile=False)
    dec = keras.models.load_model(paths.model_file("decoder.h5"), compile=False)
    head = keras.models.load_model(paths.model_file("param_head.h5"), compile=False)

    z_mean, _z_log_var, _z = enc.predict(J, verbose=0)
    recon = dec.predict(z_mean, verbose=0)
    out = head.predict(z_mean, verbose=0)
    mu = out[0]
    sigma = np.clip(tf.nn.softplus(out[1]).numpy() + SIGMA_MIN, SIGMA_MIN, SIGMA_MAX)

    for name, arr in (("z_mean", z_mean), ("recon", recon), ("param_mu", mu),
                      ("sigma", sigma)):
        if not np.all(np.isfinite(arr)):
            failures.append(f"non-finite output in {name}")

    mse = float(np.mean((J - recon) ** 2))
    sig = float(sigma.mean())
    r = {str(n): float(np.corrcoef(mu[:, i], P[:, i])[0, 1])
         for i, n in enumerate(sub["param_names"])}

    print(f"\n{'quantity':34s} {'measured':>12s} {'expected':>12s} {'delta':>10s}")
    dm = abs(mse - exp["mse_mean"]) / exp["mse_mean"]
    print(f"{'mean reconstruction MSE':34s} {mse:12.4e} {exp['mse_mean']:12.4e} {dm:9.2%}")
    if dm > MSE_RTOL:
        failures.append(f"mean MSE {mse:.4e} is {dm:.1%} from the expected value")
    ds = abs(sig - exp["sigma_mean"])
    print(f"{'mean predictive scale':34s} {sig:12.5f} {exp['sigma_mean']:12.5f} {ds:10.4f}")
    if ds > SIGMA_ATOL:
        failures.append(f"mean sigma {sig:.5f} differs by {ds:.4f}")

    print("\nper-parameter Pearson r (normalized log10 space):")
    for n in exp["pearson_r"]:
        d = abs(r[n] - exp["pearson_r"][n])
        flag = "" if d <= R_ATOL else "  <-- FAIL"
        print(f"  {n:12s} {r[n]:8.4f}   expected {exp['pearson_r'][n]:.4f}   "
              f"|d| {d:.4f}{flag}")
        if d > R_ATOL:
            failures.append(f"r[{n}] {r[n]:.4f} differs from {exp['pearson_r'][n]:.4f}")

    if failures:
        print("\nFAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: frozen model loads and reproduces the smoke-test expectations.")
    print("For the paper's 15,307-curve metrics run code/verify_frozen_metrics.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
