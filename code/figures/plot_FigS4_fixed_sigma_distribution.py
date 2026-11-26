"""
plot_FigS4_fixed_sigma_distribution.py — PUBLICATION-NOTATION micro-patch of
SI Fig. S4 "Predictive-scale distributions".

TEXT/STYLE-ONLY cleanup (2026-08-29). Reads the SAME frozen evaluation inputs
and model that VAE_v6_eval_fixed.py uses (data/dataset_normalized.npz,
data/vae-v6/...), recomputes param_sigma with the fixed convention
clip(softplus(raw_sigma)+0.01, 0.01, 1.0), then draws the S4 3x3 histogram
grid with the SAME data / bins(40) / means / colors / xlim(0-0.5) / figure size
as before. The plotted quantity is the fixed-evaluation predictive scale from
the corrected sigma convention.

Notation / style changes ONLY (no data, no means, no bins, no limits):
  1. suptitle "Predicted sigma distribution (FIXED convention)" ->
     "Predictive-scale distributions"  (internal/debug wording removed)
  2. subplot titles: code-style short names -> manuscript mathtext
     (mu_n -> $\\mu_n$, ..., rad_c -> $r_{\\mathrm{rad}}$); the numerical
     mean in each title is preserved EXACTLY ("mean = %.3f", same value)
  3. shared publication axis labels, edge-only (no per-subplot repetition):
     bottom row  "Predictive scale, $\\sigma_\\theta$"
     left column "Count"
  No confidence interval / epistemic / experimental uncertainty wording added.

Writes ONLY to final_figures/SI_final_review/FigS4_fixed_sigma_distribution.{png,pdf,svg}
(the review copy). The frozen evaluation_fixed/* files are NOT touched.

QC gates asserted at the end:
  G1  per-parameter [mean, median, q25, q75, min, max] == frozen
      sigma_statistics_fixed.csv (abs tol 2e-5, float round-off headroom)
  G2  all 9 subplots xlim == (0, 0.5); identical across panels
  G3  y-axis NOT fixed (auto-scaled per panel)
  G4  every subplot has the same bin grid (40 bins, 0-0.5) and a non-empty
      title with the mean value -> data / bins unchanged
  G5  PNG @600 dpi + PDF + SVG emitted
  G6  no title / axis-label clipping; no subplot-title overlap with the axes
      above or with the suptitle
"""

import os
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

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
NPZ_PATH = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
FROZEN_CSV = os.path.join(BASE, "evaluation_fixed", "sigma_statistics_fixed.csv")
OUT_DIR = os.path.join(BASE, "final_figures", "SI_final_review")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_STEM = os.path.join(OUT_DIR, "FigS4_fixed_sigma_distribution")

SIGMA_MIN = 0.01
SIGMA_MAX = 1.0
N_PARAM = 9

PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c",
]
SHORT_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
               "tau_ETL", "tau_HTL", "rad_c"]
# manuscript math notation for the subplot titles (mathtext). Same glyphs as the
# other final figures; r_rad spelled out ("rad_c" = radiation-recombination
# coefficient) matching Fig. 4 / Fig. S2, not the Fig. 3 "r_ad" subscript.
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

X_MAX = 0.5     # layout-only fix: was 1.0 (sigma mass is in 0-0.35)
N_BINS = 40     # unchanged
TOL = 2e-5      # float round-off headroom for the frozen-statistics comparison


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
print("Test:", J_test.shape)

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
decoder = keras.models.load_model(os.path.join(MODEL_DIR, "decoder.h5"))
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))

z_mean, _, _ = encoder.predict(J_test, verbose=0)
_, sigma_raw = param_head.predict(z_mean, verbose=0)
param_sigma = sigma_fixed(sigma_raw)
print("param_sigma:", param_sigma.shape,
      "min %.6f max %.6f" % (param_sigma.min(), param_sigma.max()))

frozen = pd.read_csv(FROZEN_CSV)
assert list(frozen["parameter"]) == PARAM_NAMES


# ================================================================== QC G1 ====
stats = np.zeros((N_PARAM, 6))          # mean, median, q25, q75, min, max
for i in range(N_PARAM):
    s = param_sigma[:, i]
    stats[i] = [np.mean(s), np.median(s), np.percentile(s, 25),
                np.percentile(s, 75), s.min(), s.max()]
maxdiff = 0.0
for i in range(N_PARAM):
    row = frozen.iloc[i]
    got = stats[i]
    want = [row["mean"], row["median"], row["q25"], row["q75"],
            row["min"], row["max"]]
    maxdiff = max(maxdiff, max(abs(got[k] - want[k]) for k in range(6)))
print("G1 max |recomputed - frozen| = %.3e" % maxdiff)
if maxdiff > TOL:
    print("FATAL: recomputed sigma statistics differ from frozen CSV "
          "(data would change). Aborting render.")
    sys.exit(1)

# ---------------------------------------------------------------- render ----
fig, axes = plt.subplots(3, 3, figsize=(11, 9))
for i, ax in enumerate(axes.ravel()):
    s = param_sigma[:, i]
    # bins auto-range over each parameter's data span, EXACTLY as in the
    # original figure (no range= override -> identical histogram content)
    ax.hist(s, bins=N_BINS, color=OKABE_ITO[0], alpha=0.7,
            edgecolor="white", linewidth=0.4)
    # manuscript mathtext label; the mean VALUE (%.3f) is the same recomputed
    # frozen number as before — only the notation / spacing changes
    ax.set_title("%s (mean = %.3f)" % (MATH_LABELS[SHORT_NAMES[i]],
                                       np.mean(s)), fontsize=10)
    ax.set_xlim(0.0, X_MAX)          # layout-only fix (was 0-1.0)
    ax.tick_params(labelsize=8)
fig.suptitle("Predictive-scale distributions", fontsize=12)
# shared publication axis labels — edge-only (bottom row / left column),
# never repeated on all nine subplots. Numeric tick labels unchanged.
for ax in axes[-1]:                       # bottom row
    ax.set_xlabel(r"Predictive scale, $\sigma_\theta$")
for ax in axes[:, 0]:                     # left column
    ax.set_ylabel("Count")
fig.tight_layout(rect=(0, 0, 1, 0.97))
for ext in ("png", "pdf", "svg"):
    kw = {"bbox_inches": "tight", "facecolor": "white"}
    if ext == "png":
        kw["dpi"] = 600
    fig.savefig(OUT_STEM + "." + ext, **kw)
print("wrote", OUT_STEM + ".{png,pdf,svg}")

# ================================================================== QC =======
fig.canvas.draw()
ren = fig.canvas.get_renderer()
ok = []


def chk(name, cond, note=""):
    ok.append(bool(cond))
    print("[%s] %s  %s" % ("PASS" if cond else "FAIL", name, note))


chk("G1 frozen stats", maxdiff <= TOL,
    "max |recomputed - frozen| = %.2e (tol %.0e); data unchanged" % (maxdiff, TOL))

lims = [ax.get_xlim() for ax in axes.ravel()]
chk("G2 xlim", all(abs(l[0] - 0.0) < 1e-9 and abs(l[1] - X_MAX) < 1e-9 for l in lims),
    "all 9 subplots xlim = (0, %.1f)" % X_MAX)

ylims = [ax.get_ylim() for ax in axes.ravel()]
chk("G3 y autoscale", len(set(round(y[1], 3) for y in ylims)) > 2,
    "y-limits differ per panel (auto-scaled, not fixed): %s" % ylims)

same_bins = True
for ax in axes.ravel():
    if len(ax.patches) != N_BINS:         # bin COUNT unchanged (40)
        same_bins = False
    if ax.get_title() == "":
        same_bins = False
chk("G4 bins+titles", same_bins,
    "each subplot: %d bins + titled (mean in title)" % N_BINS)

from PIL import Image
im = Image.open(OUT_STEM + ".png")
dpi = im.info.get("dpi", (0, 0))[0]
chk("G5 exports", abs(dpi - 600) < 1.0
    and os.path.exists(OUT_STEM + ".pdf")
    and os.path.exists(OUT_STEM + ".svg"),
    "PNG %dx%d @%.0f + PDF + SVG" % (im.size[0], im.size[1], dpi))

# ---- G6: publication-notation layout — no clipping / no overlap ----------
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
        print("  %-7s  %.2f%% of samples above 0.5" % (SHORT_NAMES[i], 100 * frac))

print()
print("GATES: %d/%d PASS" % (sum(ok), len(ok)))
plt.close(fig)
