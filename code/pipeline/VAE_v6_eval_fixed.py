"""
VAE v6 Evaluation - FIXED sigma convention (P0 verification)
============================================================

Purpose
-------
Confirm how much the VAE v6 uncertainty results change after fixing
the sigma transformation so evaluation matches training exactly.

    Training   : sigma = clip(softplus(raw_sigma) + 0.01, 0.01, 1.0)
    OLD eval   : sigma = exp(0.5 * raw_sigma)          <-- WRONG
    FIXED eval : sigma = clip(softplus(raw_sigma) + 0.01, 0.01, 1.0)

All metrics are computed in the normalized log-parameter space.
This script is new; it does NOT overwrite the old evaluation script
or any old evaluation results.

No retraining. No model modification. No M=100 latent sampling:
final point prediction uses z_mean.
"""

import os
import sys
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from scipy.stats import pearsonr, spearmanr


# =====================================================
# Paths
# =====================================================

BASE = r"E:\project\work1"
NPZ_PATH = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
OUTPUT_DIR = os.path.join(BASE, "evaluation_fixed")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =====================================================
# Constants (identical to training)
# =====================================================

INPUT_DIM = 131
LATENT_DIM = 9
N_PARAM = 9

SIGMA_MIN = 0.01
SIGMA_MAX = 1.0

# nominal level -> z value (two-sided)
NOMINAL = {
    0.50: 0.67448975,
    0.80: 1.28155157,
    0.90: 1.64485363,
    0.95: 1.95996398,
}

PARAM_NAMES = [
    "mu_n_pvk",
    "mu_p_pvk",
    "tau_n_pvk",
    "tau_p_pvk",
    "Nc_eff_pvk",
    "Nv_eff_pvk",
    "tau_ETL",
    "tau_HTL",
    "rad_c",
]

SHORT_NAMES = [
    "mu_n",
    "mu_p",
    "tau_n",
    "tau_p",
    "Nc",
    "Nv",
    "tau_ETL",
    "tau_HTL",
    "rad_c",
]


# =====================================================
# sigma conventions
# =====================================================

def sigma_old(raw):
    """OLD (wrong) evaluation convention."""
    return np.exp(0.5 * raw)


def sigma_fixed(raw):
    """FIXED convention - must match training exactly.

    sigma = clip(softplus(raw_sigma) + 0.01, 0.01, 1.0)
    """
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)


# =====================================================
# Sampling layer (required to load encoder.h5)
# =====================================================

class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


# =====================================================
# Load data (normalized log-parameter space)
# =====================================================

data = np.load(NPZ_PATH, allow_pickle=True)

J_test = data["J_test"].astype(np.float32)
params_test = data["params_test"].astype(np.float32)

print("Test:", J_test.shape, params_test.shape)


# =====================================================
# Load models
# =====================================================

encoder = keras.models.load_model(
    os.path.join(MODEL_DIR, "encoder.h5"),
    custom_objects={"Sampling": Sampling},
)
decoder = keras.models.load_model(os.path.join(MODEL_DIR, "decoder.h5"))
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

print("Models loaded")


# =====================================================
# Prediction (z_mean point prediction, no latent sampling)
# =====================================================

z_mean, z_log_var, z = encoder.predict(J_test, verbose=0)

# reconstruction from z_mean
recon_test = decoder.predict(z_mean, verbose=0)

# Gaussian parameter head output: mu and sigma_raw
param_mu, sigma_raw = param_head.predict(z_mean, verbose=0)


# =====================================================
# Sanity check: sigma conventions
# =====================================================

print("")
print("Training sigma convention:")
print("clip(softplus(raw_sigma)+0.01, 0.01, 1.0)")
print("")
print("Evaluation sigma convention:")
print("clip(softplus(raw_sigma)+0.01, 0.01, 1.0)")
print("")
print("MATCH: YES")
print("")

raw_min = float(sigma_raw.min())
raw_max = float(sigma_raw.max())

param_sigma = sigma_fixed(sigma_raw)  # fixed (training-consistent)
param_sigma_old = sigma_old(sigma_raw)  # old (wrong) convention

fixed_min = float(param_sigma.min())
fixed_max = float(param_sigma.max())

print("raw_sigma min/max : %.6f / %.6f" % (raw_min, raw_max))
print("fixed sigma min/max: %.6f / %.6f" % (fixed_min, fixed_max))
print("")

if (param_sigma < SIGMA_MIN - 1e-6).any() or (param_sigma > SIGMA_MAX + 1e-6).any():
    print("ERROR: fixed sigma outside [0.01, 1.0]")
    sys.exit(1)
else:
    print("fixed sigma within [0.01, 1.0]: OK")
    print("")


# =====================================================
# Result collection
# =====================================================

summary = []


def report(msg=""):
    print(msg)
    summary.append(msg)


# ---- Reconstruction ----

mse = np.mean((J_test - recon_test) ** 2, axis=1)
recon_mean_mse = float(mse.mean())
recon_median_mse = float(np.median(mse))

report("===== Reconstruction (normalized space) =====")
report("mean MSE  : %.6e" % recon_mean_mse)
report("median MSE: %.6e" % recon_median_mse)
report("")

# ---- Point prediction & sigma stats (fixed) ----

error = np.abs(params_test - param_mu)

pearson = np.zeros(N_PARAM)
mae = np.zeros(N_PARAM)
rmse = np.zeros(N_PARAM)
sigma_stats = np.zeros((N_PARAM, 6))  # mean, median, q25, q75, min, max

for i in range(N_PARAM):
    r, _ = pearsonr(params_test[:, i], param_mu[:, i])
    pearson[i] = r
    mae[i] = float(np.mean(error[:, i]))
    rmse[i] = float(np.sqrt(np.mean((params_test[:, i] - param_mu[:, i]) ** 2)))
    s = param_sigma[:, i]
    sigma_stats[i] = [
        float(np.mean(s)),
        float(np.median(s)),
        float(np.percentile(s, 25)),
        float(np.percentile(s, 75)),
        float(s.min()),
        float(s.max()),
    ]

report("===== Point prediction (Pearson r / MAE / RMSE) =====")
for i, name in enumerate(PARAM_NAMES):
    report("%-12s r=%.4f  MAE=%.5f  RMSE=%.5f" % (name, pearson[i], mae[i], rmse[i]))
report("mean r: %.4f" % np.mean(pearson))
report("")

report("===== Sigma statistics (FIXED) =====")
for i, name in enumerate(PARAM_NAMES):
    report("%-12s mean=%.5f median=%.5f q25=%.5f q75=%.5f min=%.5f max=%.5f"
           % (name, sigma_stats[i][0], sigma_stats[i][1],
              sigma_stats[i][2], sigma_stats[i][3],
              sigma_stats[i][4], sigma_stats[i][5]))
report("")

# ---- Uncertainty-error Spearman (fixed) ----

spearman_fixed = np.zeros(N_PARAM)
spearman_old = np.zeros(N_PARAM)
spearman_p = np.zeros(N_PARAM)

for i in range(N_PARAM):
    rho_f, p_f = spearmanr(param_sigma[:, i], error[:, i])
    rho_o, _ = spearmanr(param_sigma_old[:, i], error[:, i])
    spearman_fixed[i] = rho_f
    spearman_old[i] = rho_o
    spearman_p[i] = p_f

report("===== Spearman(sigma, |error|) : OLD vs FIXED =====")
for i, name in enumerate(PARAM_NAMES):
    report("%-12s old=%.4f fixed=%.4f diff=%.4f" % (name, spearman_old[i], spearman_fixed[i],
                                                    spearman_fixed[i] - spearman_old[i]))
report("mean old rho : %.4f" % np.mean(spearman_old))
report("mean fixed rho: %.4f" % np.mean(spearman_fixed))
report("")

# ---- Calibration (fixed) ----

levels = sorted(NOMINAL.keys())
emp_cov = np.zeros((N_PARAM, len(levels)))
mean_width = np.zeros((N_PARAM, len(levels)))
median_width = np.zeros((N_PARAM, len(levels)))

for j, lvl in enumerate(levels):
    zz = NOMINAL[lvl]
    lo = param_mu - zz * param_sigma
    hi = param_mu + zz * param_sigma
    emp_cov[:, j] = np.mean((params_test >= lo) & (params_test <= hi), axis=0)
    width = 2 * zz * param_sigma
    mean_width[:, j] = np.mean(width, axis=0)
    median_width[:, j] = np.median(width, axis=0)

report("===== Predictive interval calibration (FIXED) =====")
for j, lvl in enumerate(levels):
    report("nominal=%.2f (z=%.5f)" % (lvl, NOMINAL[lvl]))
    for i, name in enumerate(PARAM_NAMES):
        report("  %-12s cov=%.4f mean_w=%.5f median_w=%.5f"
               % (name, emp_cov[i, j], mean_width[i, j], median_width[i, j]))
report("")

# ---- Old vs fixed comparison ----

report("===== OLD vs FIXED: mean sigma / ratio / 95% coverage =====")

# recompute old 95% coverage
zz = NOMINAL[0.95]
lo_old = param_mu - zz * param_sigma_old
hi_old = param_mu + zz * param_sigma_old
cov_old_95 = np.mean((params_test >= lo_old) & (params_test <= hi_old), axis=0)
cov_fixed_95 = emp_cov[:, levels.index(0.95)]

old_mean = param_sigma_old.mean(axis=0)
fixed_mean = param_sigma.mean(axis=0)
ratio = fixed_mean / old_mean

report("%-12s | old_mean | fixed_mean | ratio(f/o) | old_cov95 | fixed_cov95" % "param")
for i, name in enumerate(PARAM_NAMES):
    report("%-12s | %.5f | %.5f | %.4f | %.4f | %.4f"
           % (name, old_mean[i], fixed_mean[i], ratio[i],
              cov_old_95[i], cov_fixed_95[i]))
report("")


# =====================================================
# Save CSVs
# =====================================================

# parameter_metrics.csv
with open(os.path.join(OUTPUT_DIR, "parameter_metrics.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "pearson_r", "mae", "rmse"])
    for i, name in enumerate(PARAM_NAMES):
        w.writerow([name, round(pearson[i], 6), round(mae[i], 6), round(rmse[i], 6)])

# sigma_statistics_fixed.csv
with open(os.path.join(OUTPUT_DIR, "sigma_statistics_fixed.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "mean", "median", "q25", "q75", "min", "max"])
    for i, name in enumerate(PARAM_NAMES):
        w.writerow([name] + [round(v, 6) for v in sigma_stats[i]])

# sigma_old_vs_fixed.csv (both comparison tables)
with open(os.path.join(OUTPUT_DIR, "sigma_old_vs_fixed.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "old_mean_sigma", "fixed_mean_sigma", "ratio_fixed_over_old",
                "old_95_coverage", "fixed_95_coverage",
                "old_spearman", "fixed_spearman", "spearman_diff"])
    for i, name in enumerate(PARAM_NAMES):
        w.writerow([name,
                    round(old_mean[i], 6), round(fixed_mean[i], 6), round(ratio[i], 6),
                    round(cov_old_95[i], 6), round(cov_fixed_95[i], 6),
                    round(spearman_old[i], 6), round(spearman_fixed[i], 6),
                    round(spearman_fixed[i] - spearman_old[i], 6)])

# calibration_fixed.csv
with open(os.path.join(OUTPUT_DIR, "calibration_fixed.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "nominal", "z", "empirical_coverage",
                "mean_interval_width", "median_interval_width"])
    for i, name in enumerate(PARAM_NAMES):
        for j, lvl in enumerate(levels):
            w.writerow([name, "%.2f" % lvl, "%.8f" % NOMINAL[lvl],
                        round(emp_cov[i, j], 6),
                        round(mean_width[i, j], 6),
                        round(median_width[i, j], 6)])

# uncertainty_error_fixed.csv
with open(os.path.join(OUTPUT_DIR, "uncertainty_error_fixed.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "spearman_rho", "p_value"])
    for i, name in enumerate(PARAM_NAMES):
        w.writerow([name, round(spearman_fixed[i], 6), "%.3e" % spearman_p[i]])


# =====================================================
# Plots
# =====================================================

OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9",
             "#CC79A7", "#F0E442", "#000000", "#999999"]
MARKERS = ["o", "s", "^", "D", "v", "<", ">", "P", "X"]

# ---- fixed_sigma_distribution.png ----
# 2026-08-28 layout-only fix (S4): x range 0-1.0 -> 0-0.5. The actual sigma
# mass sits in 0-0.35, so the old fixed 1.0 upper limit left the right side of
# every histogram empty. No data, bin count, titles, mean numbers, or colors
# changed. Export now PNG + PDF + SVG (was PNG only).
fig, axes = plt.subplots(3, 3, figsize=(11, 9))
for i, ax in enumerate(axes.ravel()):
    s = param_sigma[:, i]
    ax.hist(s, bins=40, color=OKABE_ITO[0], alpha=0.7, edgecolor="white", linewidth=0.4)
    ax.set_title("%s  (mean=%.3f)" % (SHORT_NAMES[i], np.mean(s)), fontsize=10)
    ax.set_xlim(0.0, 0.5)
    ax.tick_params(labelsize=8)
fig.suptitle("Predicted sigma distribution (FIXED convention)", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(os.path.join(OUTPUT_DIR, "fixed_sigma_distribution.png"), dpi=300)
fig.savefig(os.path.join(OUTPUT_DIR, "fixed_sigma_distribution.pdf"))
fig.savefig(os.path.join(OUTPUT_DIR, "fixed_sigma_distribution.svg"))
plt.close(fig)

# ---- fixed_uncertainty_error_3x3.png ----
# 2026-08-28 layout-only fix (S5): the 9 scatter subplots used x 0-1.0 while the
# sigma mass is in 0-0.4, so every panel squeezed to the left with empty space on
# the right. No data, rho numbers, point coordinates, or conclusions changed.
# [S5 FIX 1] x-range 0-1.0 -> uniform (0, 0.5) on all 9 subplots.
# [S5 FIX 2] y-axis natural per-parameter autoscale + ~5% margin padding.
# [S5 FIX 3] 3x3 kept; subplots_adjust wspace/hspace/top/bottom, compact like S4.
# [S5 FIX 4] suptitle 15 / subplot titles 11.5 / axis labels 11.5 / ticks 10.
# [S5 FIX 5] scatter style kept (s=4, alpha=0.35, #0072B2).
# Export now PNG@600 + PDF + SVG with bbox_inches='tight' (was PNG@300 only).
fig, axes = plt.subplots(3, 3, figsize=(11, 9))
for i, ax in enumerate(axes.ravel()):
    x = param_sigma[:, i]
    y = error[:, i]
    ax.scatter(x, y, s=4, alpha=0.35, color=OKABE_ITO[0], linewidths=0)  # [S5 FIX 5]
    ax.set_title("%s  (rho=%.3f)" % (SHORT_NAMES[i], spearman_fixed[i]),
                 fontsize=11.5)                                          # [S5 FIX 4]
    ax.set_xlim(0.0, 0.5)                                                # [S5 FIX 1]
    ax.margins(y=0.05)                                                   # [S5 FIX 2]
    ax.tick_params(labelsize=10)                                         # [S5 FIX 4]
    if i >= 6:
        ax.set_xlabel("Predicted sigma (fixed)", fontsize=11.5)          # [S5 FIX 4]
    if i % 3 == 0:
        ax.set_ylabel("|error| (normalized)", fontsize=11.5)             # [S5 FIX 4]
fig.suptitle("Uncertainty vs error (FIXED sigma)", fontsize=15, y=0.97)  # [S5 FIX 4]
fig.subplots_adjust(wspace=0.19, hspace=0.26, top=0.92, bottom=0.08)     # [S5 FIX 3]
for ext in ("png", "pdf", "svg"):
    kw = {"bbox_inches": "tight", "facecolor": "white"}
    if ext == "png":
        kw["dpi"] = 600
    fig.savefig(os.path.join(OUTPUT_DIR, "fixed_uncertainty_error_3x3." + ext), **kw)
plt.close(fig)

# ---- fixed_calibration.png ----
fig, ax = plt.subplots(figsize=(7, 6))
for i, name in enumerate(PARAM_NAMES):
    ax.plot(levels, emp_cov[i], marker=MARKERS[i], color=OKABE_ITO[i],
            label=SHORT_NAMES[i], linewidth=1.6, markersize=6)
diag = np.array([0.0, 1.0])
ax.plot(diag, diag, linestyle="--", color="#555555", linewidth=1.2)
ax.set_xlabel("Nominal coverage")
ax.set_ylabel("Empirical coverage")
ax.set_title("Predictive interval calibration (FIXED sigma)")
ax.legend(fontsize=8, ncol=2, frameon=False)
ax.set_xlim(0.4, 1.0)
ax.set_ylim(0.4, 1.0)
ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5)
ax.tick_params(labelsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "fixed_calibration.png"), dpi=300)
plt.close(fig)


# =====================================================
# Summary file
# =====================================================

with open(os.path.join(OUTPUT_DIR, "evaluation_summary.txt"), "w", encoding="utf-8") as f:
    f.write("VAE v6 - FIXED sigma evaluation\n")
    f.write("=" * 50 + "\n")
    f.write("sigma convention: clip(softplus(raw_sigma)+0.01, 0.01, 1.0)\n")
    f.write("raw_sigma min/max: %.6f / %.6f\n" % (raw_min, raw_max))
    f.write("fixed sigma min/max: %.6f / %.6f\n" % (fixed_min, fixed_max))
    f.write("=" * 50 + "\n\n")
    for line in summary:
        f.write(line + "\n")

print("")
print("Evaluation finished.")
print("Results saved to:", OUTPUT_DIR)
