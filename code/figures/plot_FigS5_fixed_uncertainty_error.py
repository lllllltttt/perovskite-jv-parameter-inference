"""
plot_FigS5_fixed_uncertainty_error.py — PUBLICATION-NOTATION micro-patch of
SI Fig. S5 "Predictive scale versus normalized error (fixed convention)".

TEXT/STYLE-ONLY cleanup (2026-08-29), the same treatment as the S4 pass.
Reads the SAME frozen inputs and model that VAE_v6_eval_fixed.py uses and
recomputes
    param_sigma = clip(softplus(raw)+0.01, 0.01, 1.0)   (x, predictive scale)
    error       = |params_test - param_mu|              (y, normalized abs err)
then draws the S5 3x3 scatter grid with the SAME data / rho values / colors /
markers / axis ranges / layout as before. Notation/style changes ONLY:

  1. suptitle "Uncertainty vs error (FIXED sigma)" ->
     "Predictive scale versus normalized error (fixed convention)"
  2. subplot titles: code-style short names -> manuscript mathtext
     (mu_n -> $\\mu_n$, ..., rad_c -> $r_{\\mathrm{rad}}$) and the
     correlation text becomes math rho:  e.g. "$\\mu_n$ ($\\rho = 0.398$)".
     The rho VALUE (%.3f) is unchanged.
  3. shared edge axis labels (bottom row / left column only):
     x "Predicted sigma (fixed)" -> "Predictive scale, $\\sigma_\\theta$"
     y "|error| (normalized)"    -> "Normalized absolute error"
  No confidence-interval / epistemic / experimental-uncertainty wording.

Writes ONLY to final_figures/SI_final_review/FigS5_fixed_uncertainty_error_3x3.{png,pdf,svg}
(the review copy). The frozen evaluation_fixed/* files are NOT touched.

QC gates asserted at the end:
  G1   per-parameter sigma stats == frozen sigma_statistics_fixed.csv (tol 2e-5)
  G1b  per-parameter mean|error| == frozen parameter_metrics.csv mae (tol 2e-4)
       AND spearman rho == frozen uncertainty_error_fixed.csv (tol 1e-4)
       -> proves x AND y data unchanged and the rho numbers in the titles
          unchanged
  G2   all 9 subplots xlim == (0, 0.5); identical across panels
  G3   y autoscaled per panel with ~5% margin (not one fixed common range)
  G4   every subplot title shows its frozen rho to 3 decimals (math-rho form)
  G5   PNG @600 dpi + PDF + SVG emitted (bbox_inches="tight")
  G6   no title / axis-label clipping; no subplot-title overlap with the axes
       above or with the suptitle
"""

import os
import re
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"   # reproducible forward pass

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
NPZ_PATH = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
FROZEN_CSV = os.path.join(BASE, "evaluation_fixed", "sigma_statistics_fixed.csv")
METRICS_CSV = os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv")
RHO_CSV = os.path.join(BASE, "evaluation_fixed", "uncertainty_error_fixed.csv")
OUT_DIR = os.path.join(BASE, "final_figures", "SI_final_review")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_STEM = os.path.join(OUT_DIR, "FigS5_fixed_uncertainty_error_3x3")

SIGMA_MIN = 0.01
SIGMA_MAX = 1.0
N_PARAM = 9
X_MAX = 0.5        # [S5 FIX 1] uniform x range (was 0-1.0)
TOL = 2e-5         # float round-off headroom, sigma stats
TOL_MAE = 2e-4     # mean |error| vs frozen CSV (CSV stores 6 decimals)
TOL_RHO = 1e-4     # spearman rho vs frozen CSV

PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
SHORT_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
               "tau_ETL", "tau_HTL", "rad_c"]
# manuscript math notation for the subplot titles (mathtext). Same glyphs as the
# other final figures / Fig. S4; r_rad spelled out ("rad_c" = radiation-
# recombination coefficient) matching Fig. 4 / Fig. S2, not Fig. 3's "r_ad".
MATH_LABELS = {
    "mu_n": r"$\mu_n$", "mu_p": r"$\mu_p$",
    "tau_n": r"$\tau_n$", "tau_p": r"$\tau_p$",
    "Nc": r"$N_c$", "Nv": r"$N_v$",
    "tau_ETL": r"$\tau_{\mathrm{ETL}}$",
    "tau_HTL": r"$\tau_{\mathrm{HTL}}$",
    "rad_c": r"$r_{\mathrm{rad}}$",
}
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9",
             "#CC79A7", "#F0E442", "#000000", "#999999"]


def sigma_fixed(raw):
    """FIXED convention - must match training exactly (same as the original)."""
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)


class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


# ------------------------------------------------------------------ data ----
data = np.load(NPZ_PATH, allow_pickle=True)
J_test = data["J_test"].astype(np.float32)
params_test = data["params_test"].astype(np.float32)
print("Test:", J_test.shape, params_test.shape)

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

z_mean, _, _ = encoder.predict(J_test, verbose=0)
param_mu, sigma_raw = param_head.predict(z_mean, verbose=0)
param_sigma = sigma_fixed(sigma_raw)
error = np.abs(params_test - param_mu)          # y data, |error| (normalized)
print("param_sigma:", param_sigma.shape, "min %.6f max %.6f"
      % (param_sigma.min(), param_sigma.max()))
print("error      :", error.shape, "min %.6f max %.6f"
      % (error.min(), error.max()))

frozen_sig = pd.read_csv(FROZEN_CSV)
frozen_met = pd.read_csv(METRICS_CSV)
frozen_rho = pd.read_csv(RHO_CSV)
assert list(frozen_sig["parameter"]) == PARAM_NAMES
assert list(frozen_met["parameter"]) == PARAM_NAMES
assert list(frozen_rho["parameter"]) == PARAM_NAMES

# ================================================================== QC G1 ====
stats = np.zeros((N_PARAM, 6))          # mean, median, q25, q75, min, max
for i in range(N_PARAM):
    s = param_sigma[:, i]
    stats[i] = [np.mean(s), np.median(s), np.percentile(s, 25),
                np.percentile(s, 75), s.min(), s.max()]
maxdiff_sig = 0.0
for i in range(N_PARAM):
    row = frozen_sig.iloc[i]
    want = [row["mean"], row["median"], row["q25"], row["q75"],
            row["min"], row["max"]]
    maxdiff_sig = max(maxdiff_sig, max(abs(stats[i][k] - want[k]) for k in range(6)))
print("G1  max |recomputed sigma - frozen| = %.3e" % maxdiff_sig)
if maxdiff_sig > TOL:
    print("FATAL: sigma data would change. Aborting.")
    sys.exit(1)

# ================================================================= QC G1b ====
mae = np.array([float(np.mean(error[:, i])) for i in range(N_PARAM)])
rho = np.array([spearmanr(param_sigma[:, i], error[:, i])[0]
                for i in range(N_PARAM)])
maxdiff_mae = max(abs(mae[i] - frozen_met.iloc[i]["mae"]) for i in range(N_PARAM))
maxdiff_rho = max(abs(rho[i] - frozen_rho.iloc[i]["spearman_rho"])
                  for i in range(N_PARAM))
print("G1b max |mean error - frozen mae| = %.3e" % maxdiff_mae)
print("G1b max |recomputed rho - frozen| = %.3e" % maxdiff_rho)
if maxdiff_mae > TOL_MAE or maxdiff_rho > TOL_RHO:
    print("FATAL: error data / rho numbers would change. Aborting.")
    sys.exit(1)

# ---------------------------------------------------------------- render ----
fig, axes = plt.subplots(3, 3, figsize=(11, 9))
for i, ax in enumerate(axes.ravel()):
    x = param_sigma[:, i]
    y = error[:, i]
    ax.scatter(x, y, s=4, alpha=0.35, color=OKABE_ITO[0], linewidths=0)  # [S5 FIX 5] style kept
    # manuscript mathtext label + math rho; the rho VALUE (%.3f) is the same
    # frozen number as before — only the notation / spacing changes
    ax.set_title("%s ($\\rho = %.3f$)" % (MATH_LABELS[SHORT_NAMES[i]], rho[i]),
                 fontsize=11.5)                                           # [S5 FIX 4]
    ax.set_xlim(0.0, X_MAX)        # [S5 FIX 1] 0-1.0 -> 0-0.5, uniform
    ax.margins(y=0.05)             # [S5 FIX 2] ~5% y padding, natural per-panel scale
    ax.tick_params(labelsize=10)   # [S5 FIX 4]
    if i >= 6:
        ax.set_xlabel(r"Predictive scale, $\sigma_\theta$", fontsize=11.5)
    if i % 3 == 0:
        ax.set_ylabel("Normalized absolute error", fontsize=11.5)
fig.suptitle("Predictive scale versus normalized error (fixed convention)",
             fontsize=15, y=0.97)
fig.subplots_adjust(wspace=0.19, hspace=0.26, top=0.92, bottom=0.08)     # [S5 FIX 3]
for ext in ("png", "pdf", "svg"):
    kw = {"bbox_inches": "tight", "facecolor": "white"}
    if ext == "png":
        kw["dpi"] = 600
    fig.savefig(OUT_STEM + "." + ext, **kw)
print("wrote", OUT_STEM + ".{png,pdf,svg}")

# ================================================================== QC =======
fig.canvas.draw()
ok = []


def chk(name, cond, note=""):
    ok.append(bool(cond))
    print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))


chk("G1 sigma data", maxdiff_sig <= TOL,
    "max |recomputed - frozen| = %.2e (x-data unchanged)" % maxdiff_sig)
chk("G1b error+rho", maxdiff_mae <= TOL_MAE and maxdiff_rho <= TOL_RHO,
    "max |mean err diff| = %.2e, max |rho diff| = %.2e (y-data + rho unchanged)"
    % (maxdiff_mae, maxdiff_rho))

lims = [ax.get_xlim() for ax in axes.ravel()]
chk("G2 xlim", all(abs(l[0]) < 1e-9 and abs(l[1] - X_MAX) < 1e-9 for l in lims),
    "all 9 subplots xlim = (0, %.1f), identical" % X_MAX)

pad_frac = []
for i, ax in enumerate(axes.ravel()):
    y = error[:, i]
    yl = ax.get_ylim()
    rng = y.max() - y.min()
    pad_frac.append((yl[1] - yl[0]) / rng - 1.0)
ylims = [ax.get_ylim() for ax in axes.ravel()]
chk("G3 y autoscale", all(0.05 <= p <= 0.15 for p in pad_frac)
    and len(set(round(y[1], 3) for y in ylims)) > 2,
    "per-panel y autoscale, margin pad frac %.2f-%.2f (target ~0.10)"
    % (min(pad_frac), max(pad_frac)))

titles_ok = True
for i, ax in enumerate(axes.ravel()):
    t = ax.get_title()
    # new math-rho title form: e.g. "$\mu_n$ ($\rho = 0.398$)"
    m = re.search(r"\\rho\s*=\s*([-\d.]+)", t)
    if not m or abs(float(m.group(1)) - round(frozen_rho.iloc[i]["spearman_rho"], 3)) > 5e-4:
        titles_ok = False
chk("G4 titles rho", titles_ok,
    "all 9 titles carry their frozen rho to 3 decimals (math-rho form)")

from PIL import Image
im = Image.open(OUT_STEM + ".png")
dpi = im.info.get("dpi", (0, 0))[0]
chk("G5 exports", abs(dpi - 600) < 1.0
    and os.path.exists(OUT_STEM + ".pdf")
    and os.path.exists(OUT_STEM + ".svg"),
    "PNG %dx%d @%.0f + PDF + SVG" % (im.size[0], im.size[1], dpi))

# ---- G6: publication-notation layout — no clipping / no overlap ----------
fig.canvas.draw()
ren = fig.canvas.get_renderer()
fb = fig.bbox


def _inside(artist):
    e = artist.get_window_extent(ren)
    return (e.x0 >= -0.5 and e.y0 >= -0.5
            and e.x1 <= fb.width + 0.5 and e.y1 <= fb.height + 0.5)


clip_ok = True
for ax in axes.ravel():
    clip_ok = clip_ok and _inside(ax.title)
for ax in axes[-1]:
    clip_ok = clip_ok and _inside(ax.xaxis.label)
for ax in axes[:, 0]:
    clip_ok = clip_ok and _inside(ax.yaxis.label)
chk("G6a no title/axis-label clipping", clip_ok)

st = fig._suptitle
over_ok = True
for r in range(3):
    for c in range(3):
        ax = axes[r, c]
        te = ax.title.get_window_extent(ren)
        ae = ax.get_window_extent(ren)
        if te.y0 < ae.y1:                  # title dips into its own axes
            over_ok = False
        if r > 0:
            ab = axes[r - 1, c].get_window_extent(ren)
            if te.y1 > ab.y0:              # title reaches the axes above
                over_ok = False
        if r == 0 and st is not None:
            se = st.get_window_extent(ren)
            if te.y1 > se.y0:              # row-0 title collides with suptitle
                over_ok = False
chk("G6b no title/axes/suptitle overlap", over_ok)

# info: tail fraction above 0.5 (context for the new xlim)
print()
for i in range(N_PARAM):
    frac = float((param_sigma[:, i] > X_MAX).mean())
    if frac > 0:
        print("  %-7s  %.2f%% of samples above 0.5 (clipped at right edge)"
              % (SHORT_NAMES[i], 100 * frac))

print()
print("GATES: %d/%d PASS" % (sum(ok), len(ok)))
plt.close(fig)
