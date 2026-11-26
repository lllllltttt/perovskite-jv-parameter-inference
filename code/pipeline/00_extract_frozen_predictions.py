"""
00_extract_frozen_predictions.py
================================
PLOTTING SUPPORT ONLY — regenerates per-sample predictions from the FROZEN
VAE-v6 chain so Fig2b (reconstructions) and Fig3a (parity) can be drawn.

This is NOT a new analysis. It reproduces the exact frozen inference
protocol of `script/VAE_v6_eval_fixed.py` and `script/forward_validation_unbiased.py`:
  z_mean, z_log_var, z = encoder.predict(J_test)          # point prediction
  recon_test           = decoder.predict(z_mean)          # normalized J space
  param_mu, sigma_raw  = param_head.predict(z_mean)
  sigma                = clip(softplus(sigma_raw)+0.01, 0.01, 1.0)   # FIXED convention

Nothing is retrained, no COMSOL is run, no metric is recomputed beyond what
the frozen scripts already compute. Output: a single .npz with per-sample
arrays consumed by the figure scripts.

Fig2b sample selection is observable-driven ONLY (PCE terciles, sample with
PCE nearest each tercile median) — deterministic, no seed.
"""

import os
import pickle
import sys
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Paths are resolved relative to the repository (see code/paths.py); set
# JV_DATA_ROOT / JV_MODEL_ROOT to point at unpacked release assets instead.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402
import device_metrics as dm  # noqa: E402

NPZ_PATH = paths.data_file("dataset_normalized.npz")
MODEL_DIR = os.path.join(paths.model_dir(), "vae-v6")
PARAM_SCALER = paths.scaler_file("param_scaler.pkl")
OUT_NPZ = os.environ.get(
    "JV_OUT_NPZ", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "_frozen_preds.npz"))

V_GRID = np.linspace(0.0, 1.3, 131)

SIGMA_MIN = 0.01
SIGMA_MAX = 1.0


class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def sigma_fixed(raw):
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)


def device_observables(J_raw):
    """Jsc, Voc, FF, PCE for a stack of physical J-V curves (mA cm^-2).

    Delegates to ``code/device_metrics.py``, the same convention the published
    Figure 4e / Table S8 numbers use: the FIRST DOWNWARD zero crossing,
    linearly interpolated; NaN for every dependent metric when there is none.

    History: this function used to take the first sign change of either
    direction and feed ``np.interp`` an argument array that decreases, which
    both mis-handles a reverse-bias tail and is not the linear root.  On the
    15,307 test curves every first change is downward, so only the
    interpolation was affected (|dV_oc| <= 0.01 V, one grid step).  PCE is
    invariant (FF = Pmax/(Jsc*Voc) cancels Voc), so the Figure 2b sample
    selection and every published device metric are unchanged.  See
    docs/REPRODUCE.md, "Voc extraction".
    """
    res = [dm.device_metrics(j) for j in J_raw]
    return (np.array([r["Jsc"] for r in res]),
            np.array([r["Voc"] for r in res]),
            np.array([r["FF"] for r in res]),
            np.array([r["PCE"] for r in res]))


def main():
    data = np.load(NPZ_PATH, allow_pickle=True)
    J_test = data["J_test"].astype(np.float32)
    J_test_raw = data["J_test_raw"].astype(np.float64)
    params_test = data["params_test"].astype(np.float64)          # normalized
    params_test_raw = data["params_test_raw"].astype(np.float64)  # physical

    with open(PARAM_SCALER, "rb") as f:
        sd = pickle.load(f)
    scaler = sd["scaler"]

    encoder = keras.models.load_model(
        os.path.join(MODEL_DIR, "encoder.h5"),
        custom_objects={"Sampling": Sampling})
    decoder = keras.models.load_model(os.path.join(MODEL_DIR, "decoder.h5"))
    param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

    z_mean, z_log_var, z = encoder.predict(J_test, verbose=0)
    recon_test = decoder.predict(z_mean, verbose=0)                 # normalized J
    out = param_head.predict(z_mean, verbose=0)
    param_mu = out[0].astype(np.float64)                            # normalized log10
    sigma_raw = out[1].astype(np.float64)
    sigma = sigma_fixed(sigma_raw)

    # physical-space inverse (log10 -> 10**x) for parity axes / device metrics
    log_phys = scaler.inverse_transform(param_mu)
    params_pred_phys = log_phys.copy()
    log_mask = np.asarray(data["log_transform_mask"], dtype=bool)
    params_pred_phys[:, log_mask] = 10.0 ** log_phys[:, log_mask]

    jsc, voc, ff, pce = device_observables(J_test_raw)

    # Fig2b: one representative sample per observable PCE tercile (nearest median)
    edges = np.percentile(pce, [100.0 / 3, 200.0 / 3])
    bin_id = np.digitize(pce, edges, right=False)
    reps = []
    for b in range(3):
        idx_b = np.where(bin_id == b)[0]
        mid = np.median(pce[idx_b])
        reps.append(int(idx_b[np.argmin(np.abs(pce[idx_b] - mid))]))
    reps = np.array(reps, dtype=int)
    assert len(np.unique(reps)) == 3

    np.savez(
        OUT_NPZ,
        V_GRID=V_GRID.astype(np.float64),
        J_test=J_test.astype(np.float32),
        J_test_raw=J_test_raw,
        params_test=params_test,
        params_test_raw=params_test_raw,
        param_mu=param_mu,
        param_sigma=sigma,
        sigma_raw=sigma_raw,
        recon_test=recon_test.astype(np.float32),
        z_mean=z_mean.astype(np.float32),
        params_pred_phys=params_pred_phys,
        jsc=jsc, voc=voc, ff=ff, pce=pce,
        fig2b_repr_indices=reps,
        fig2b_repr_PCE=pce[reps],
        param_names=np.asarray(data["param_names"]),
    )
    print("saved:", OUT_NPZ)
    print("shapes: recon", recon_test.shape, "param_mu", param_mu.shape,
          "sigma", sigma.shape, "z", z_mean.shape)
    print("recon MSE mean/median: %.6e / %.6e"
          % (np.mean((J_test - recon_test) ** 2),
             np.median(np.mean((J_test - recon_test) ** 2, axis=1))))
    print("fig2b representative test indices:", reps, "PCE:", np.round(pce[reps], 3))


if __name__ == "__main__":
    main()
