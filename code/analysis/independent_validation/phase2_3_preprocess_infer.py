# -*- coding: utf-8 -*-
"""
Phase 2 + Phase 3 — FROZEN PREPROCESSING ONLY + FROZEN MODEL INFERENCE
Independent dataset validation of frozen VAE-v6.

Frozen transforms applied to the NEW dataset:
  params: log10 -> ORIGINAL MinMaxScaler.transform (no refit)
  J     :          ORIGINAL per-column MinMaxScaler.transform (no refit)
Out-of-range diagnostics (domain-shift diagnosis).

Frozen inference:
  z_mean = encoder(J_scaled)[0]
  mu, sigma_raw = param_head(z_mean)
  sigma = clip(softplus(sigma_raw) + 0.01, 0.01, 1.0)   # frozen convention
  point prediction = ParamHead(mu_z) -> mu   (no latent sampling)

Outputs:
  independent_validation/preprocessed_independent.npz   (normalized data, reusable)
  independent_validation/independent_predictions.csv
  independent_validation/preprocessing_out_of_range.txt
"""
import os, csv, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

BASE = r"E:\project\work1"
NEW = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-3.csv")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
OUT = os.path.join(BASE, "independent_validation")
os.makedirs(OUT, exist_ok=True)

PARAM_COLS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
              "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SIGMA_MIN, SIGMA_MAX = 0.01, 1.0

# ----------------------------------------------------------------------
# 1. Load data
# ----------------------------------------------------------------------
df = pd.read_csv(NEW)
sid = df["Sample_ID"].values.astype(np.int64)
J_raw = df[[c for c in df.columns if c.startswith("J_")]].values.astype(np.float64)
P_raw = df[PARAM_COLS].values.astype(np.float64)
N = len(df)
print("new dataset rows:", N, "J shape:", J_raw.shape, "P shape:", P_raw.shape)

# ----------------------------------------------------------------------
# 2. Frozen scalers
# ----------------------------------------------------------------------
with open(os.path.join(BASE, "data", "param_scaler.pkl"), "rb") as f:
    psc = pickle.load(f)["scaler"]
with open(os.path.join(BASE, "data", "J_scaler.pkl"), "rb") as f:
    jsc = pickle.load(f)
log_mask = np.array([True] * 9)

# ----------------------------------------------------------------------
# 3. Apply ORIGINAL frozen transforms (transform only, no fit)
# ----------------------------------------------------------------------
P_log10 = np.log10(P_raw)                        # all params log10 (log_mask all True)
P_norm = psc.transform(P_log10)                  # original min/max scaler
J_norm = jsc.transform(J_raw)                    # original per-column min/max scaler

# ----------------------------------------------------------------------
# 4. Out-of-range diagnostics
# ----------------------------------------------------------------------
out = []
out.append("Phase 2 - FROZEN PREPROCESSING OUT-OF-RANGE DIAGNOSTICS")
out.append("=" * 60)
out.append("")

j_below = float(np.mean(J_norm < 0.0))
j_above = float(np.mean(J_norm > 1.0))
samp_oor = float(np.mean((J_norm < 0.0).any(axis=1) | (J_norm > 1.0).any(axis=1)))
out.append("J scaled values outside [0,1] (fraction of all J values):")
out.append("  below 0 : %.6f  (%.4f%%)" % (j_below, 100 * j_below))
out.append("  above 1 : %.6f  (%.4f%%)" % (j_above, 100 * j_above))
out.append("  fraction of SAMPLES with >=1 out-of-range J value: %.6f  (%.4f%%)"
           % (samp_oor, 100 * samp_oor))
out.append("")

p_below = np.mean(P_norm < 0.0, axis=0)
p_above = np.mean(P_norm > 1.0, axis=0)
out.append("Parameter normalized values outside original [0,1] range (per param):")
for i, c in enumerate(PARAM_COLS):
    out.append("  %-10s  below=%.6f (%.4f%%)   above=%.6f (%.4f%%)   any=%.6f (%.4f%%)"
               % (c, p_below[i], 100 * p_below[i],
                  p_above[i], 100 * p_above[i],
                  p_below[i] + p_above[i], 100 * (p_below[i] + p_above[i])))
out.append("")
out.append("Note: out-of-range here means outside the ORIGINAL training min/max per")
out.append("column. Small percentages indicate the new dataset sits essentially inside")
out.append("the frozen normalization envelope (mild shift).")
out.append("")

# also record J physical extremes touched by normalization
out.append("J physical extremes at which the frozen scaler saturates:")
out.append("  V=0.00  min=%.4f max=%.4f   (new data min=%.4f max=%.4f)"
           % (jsc.data_min_[0], jsc.data_max_[0], J_raw[:, 0].min(), J_raw[:, 0].max()))
out.append("  V=1.30  min=%.4f max=%.4f   (new data min=%.4f max=%.4f)"
           % (jsc.data_min_[-1], jsc.data_max_[-1], J_raw[:, -1].min(), J_raw[:, -1].max()))
out.append("")

with open(os.path.join(OUT, "preprocessing_out_of_range.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n".join(out))

# save intermediate normalized arrays for downstream phases
np.savez_compressed(
    os.path.join(OUT, "preprocessed_independent.npz"),
    sample_id=sid,
    P_raw=P_raw,
    P_log10=P_log10,
    P_norm=P_norm.astype(np.float32),
    J_norm=J_norm.astype(np.float32),
    J_raw=J_raw,
)
print("\nsaved preprocessed_independent.npz")

# ----------------------------------------------------------------------
# 5. Frozen model inference
# ----------------------------------------------------------------------
class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

def sigma_fixed(raw):
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)

z_out = encoder.predict(J_norm.astype(np.float32), batch_size=1024, verbose=0)
z_mean = np.asarray(z_out[0], np.float64)
mu_norm, sigma_raw = param_head.predict(z_mean.astype(np.float32),
                                        batch_size=1024, verbose=0)
mu_norm = np.asarray(mu_norm, np.float64)
sigma_raw = np.asarray(sigma_raw, np.float64)
sigma = sigma_fixed(sigma_raw)

print("\nz_mean shape:", z_mean.shape, " mu_norm:", mu_norm.shape, " sigma:", sigma.shape)
print("mu_norm range: [%.4f, %.4f]" % (mu_norm.min(), mu_norm.max()))
print("sigma range: [%.6f, %.6f]" % (sigma.min(), sigma.max()))
if (sigma < SIGMA_MIN - 1e-6).any() or (sigma > SIGMA_MAX + 1e-6).any():
    raise RuntimeError("sigma outside [0.01,1.0]")
print("sigma within [0.01,1.0]: OK")

# invert mu_norm -> log10 physical -> physical
mu_log10 = mu_norm * psc.data_range_ + psc.data_min_
mu_phys = 10.0 ** mu_log10

# ----------------------------------------------------------------------
# 6. Save independent_predictions.csv
# ----------------------------------------------------------------------
hdr = (["sample_id"] +
       ["true_%s" % c for c in PARAM_COLS] +
       ["true_log10_%s" % c for c in PARAM_COLS] +
       ["true_norm_%s" % c for c in PARAM_COLS] +
       ["pred_norm_%s" % c for c in PARAM_COLS] +
       ["pred_phys_%s" % c for c in PARAM_COLS] +
       ["sigma_%s" % c for c in PARAM_COLS])

with open(os.path.join(OUT, "independent_predictions.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(hdr)
    for i in range(N):
        row = [sid[i]]
        row += ["%.6e" % v for v in P_raw[i]]
        row += ["%.8f" % v for v in P_log10[i]]
        row += ["%.8f" % v for v in P_norm[i]]
        row += ["%.8f" % v for v in mu_norm[i]]
        row += ["%.6e" % v for v in mu_phys[i]]
        row += ["%.8f" % v for v in sigma[i]]
        w.writerow(row)
print("\nsaved independent_predictions.csv  (%d rows x %d cols)" % (N, len(hdr)))

# quick sanity: no NaN in outputs
assert not np.isnan(mu_norm).any() and not np.isnan(sigma).any()
print("inference outputs: no NaN - OK")
print("\nPhase 2+3 complete.")
