# -*- coding: utf-8 -*-
"""
Compact summary figure for the independent-dataset validation:
  (a) per-parameter Pearson: original test set vs independent dataset
  (b) prior-coordinate recovery: shared scales vs ratios, original vs independent

Uses the project's unified figure_style (final_figures/scripts/figure_style.py).
Output: independent_validation/independent_validation_summary.png (+ pdf)
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(r"E:\project\work1", "final_figures", "scripts"))
from figure_style import (OKABE_ITO, MUTED, INK, configure_axes, set_labels,
                          panel_label, save_fig, FS_AXIS, FS_TICK, FS_LEGEND)

OUT = r"E:\project\work1\independent_validation"

SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
LABELS = [r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
          r"$N_c$", r"$N_v$", r"$\tau_\mathrm{ETL}$", r"$\tau_\mathrm{HTL}$",
          r"$r_\mathrm{ad}$"]

pm = pd.read_csv(os.path.join(OUT, "independent_parameter_metrics.csv"))
orig_r = pm["original_test_pearson"].values[:9]
ind_r = pm["independent_pearson"].values[:9]

pc = pd.read_csv(os.path.join(OUT, "independent_prior_coordinate_recovery.csv"))
coords = pc["coordinate"].tolist()
orig_c = pc["original_pearson"].values
ind_c = pc["independent_pearson"].values
types = pc["type"].values  # shared_scale / ratio

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.09, 3.1))

# ---------------- panel (a): per-parameter Pearson -----------------------
x = np.arange(9)
w = 0.38
b1 = ax1.bar(x - w / 2, orig_r, w, color=OKABE_ITO[0], label="Original test (N=15,307)",
             edgecolor="white", linewidth=0.3)
b2 = ax1.bar(x + w / 2, ind_r, w, color=OKABE_ITO[2], label="Independent (N=153,067)",
             edgecolor="white", linewidth=0.3)
ax1.axhline(0.8069, color=MUTED, linestyle="--", linewidth=0.8)
ax1.text(8.35, 0.8069 + 0.012, "orig. mean", fontsize=6.5, color=MUTED, ha="right")
ax1.set_xticks(x)
ax1.set_xticklabels(LABELS, fontsize=FS_TICK)
ax1.set_ylim(0.5, 1.0)
ax1.set_ylabel("Pearson $r$ (normalized log10)", fontsize=FS_AXIS)
ax1.legend(fontsize=6.5, frameon=False, loc="lower right")
configure_axes(ax1)
panel_label(ax1, "(a)")

# ---------------- panel (b): prior coordinates ---------------------------
xc = np.arange(6)
cc = [OKABE_ITO[0] if t == "shared_scale" else OKABE_ITO[1] for t in types]
b3 = ax2.bar(xc - w / 2, orig_c, w, color=cc, edgecolor="white", linewidth=0.3,
             alpha=0.55)
b4 = ax2.bar(xc + w / 2, ind_c, w, color=cc, edgecolor="white", linewidth=0.3)
ax2.set_xticks(xc)
ax2.set_xticklabels([r"$a_\mu$", r"$r_\mu$", r"$a_\tau$", r"$r_\tau$",
                     r"$a_D$", r"$r_D$"], fontsize=FS_TICK)
ax2.set_ylim(0.0, 1.0)
ax2.set_ylabel("Pearson $r$", fontsize=FS_AXIS)
configure_axes(ax2)
panel_label(ax2, "(b)")

# custom legend for panel (b): shared / ratio
from matplotlib.patches import Patch
handles = [Patch(facecolor=OKABE_ITO[0], alpha=0.55, label="shared scale"),
           Patch(facecolor=OKABE_ITO[1], alpha=0.55, label="ratio"),
           Patch(facecolor="white", edgecolor=INK, hatch=None, label=""),
           ]
# use bars: solid = independent, faded = original
h2 = [Patch(facecolor=OKABE_ITO[2], label="Independent", edgecolor="white"),
      Patch(facecolor=OKABE_ITO[0], alpha=0.55, label="Original (faded)"),
      Patch(facecolor=OKABE_ITO[0], alpha=0.55, label="shared scale"),
      Patch(facecolor=OKABE_ITO[1], alpha=0.55, label="ratio")]
ax2.legend(handles=h2, fontsize=6.0, frameon=False, loc="upper right", ncol=2,
           handlelength=1.2, columnspacing=0.9)

fig.tight_layout(w_pad=2.2)
save_fig(fig, os.path.join(OUT, "independent_validation_summary"),
         dpi=600, pdf=True, svg=False)
print("saved independent_validation_summary.png/.pdf")
