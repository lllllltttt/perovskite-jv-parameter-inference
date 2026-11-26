# -*- coding: utf-8 -*-
"""
e2v2_figures.py -- summary figures for E2-v2.
  e2v2_fig_mesh_convergence.png   windowed RMSE-vs-frozen-ref vs element count
                                  (log x): <=1V/gen0 floor + >1V divergence.
  e2v2_fig_window_substitution.png per-rep attribution: d_mu (max over 9 params)
                                  of each 1V recombination from each parent curve.
"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(TASK, "outputs")

m = pd.read_csv(os.path.join(OUT, "e2v2_mesh_windowed_rmse.csv"))
dm = pd.read_csv(os.path.join(OUT, "e2v2_device_metrics.csv"))
sub = pd.read_csv(os.path.join(OUT, "e2v2_inverse_window_substitution.csv"))
par = {"3741": 131019, "5808": 87146, "7693": 23756, "8874": 138740,
       "14179": 180278, "14912": 65444}
SID = {int(k): v for k, v in par.items()}

# ---- fig 1: windowed RMSE vs nelem (default tol chain only) ----
mm = m[(m.level_type.isin(["ref", "mesh"]))].copy()
mm["sid"] = mm.test_index.map(SID)
fig, ax = plt.subplots(figsize=(7.2, 4.6))
WINC = {"le1": ("tab:blue", "o", "$\\leq$1 V", 3741),
        "gen0": ("tab:green", "s", "gen ($\\leq$V$_{oc,t}$)", 14179),
        "gt1": ("tab:red", "^", ">1 V", 3741),
        "full": ("tab:purple", "v", "full", 5808)}
for win, (col, mk, lab, ti) in WINC.items():
    for t2, g in mm.groupby("test_index"):           # faint: every rep
        g = g.sort_values("nelem")
        ax.plot(g.nelem, g["vs_ref_rmse_" + win], mk + "-", ms=3.5, color=col,
                alpha=0.30, lw=0.7)
    g = mm[mm.test_index == ti].sort_values("nelem")  # solid: representative
    ax.plot(g.nelem, g["vs_ref_rmse_" + win], mk + "-", color=col, lw=1.6, ms=6,
            label="%s (ti %d)" % (lab, ti))
ax.axvline(112, color="0.4", ls=":", lw=1)
ax.text(112, 2.5e-3, " frozen m=1\n nelem 112", ha="right", fontsize=8, color="0.3")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("mesh elements, $n_{elem}$  (refinement $\\rightarrow$ right)")
ax.set_ylabel("windowed RMSE vs frozen m=1 curve  (mA/cm$^2$)")
ax.set_title("E2-v2: windowed mesh convergence, 6 representatives\n"
             "$\\leq$1 V / gen0 floor near 1e-3..1e-1 ;  >1 V (and full) diverge with mesh")
ax.grid(True, which="both", alpha=0.3)
ax.legend(fontsize=8, loc="lower right", framealpha=0.9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "e2v2_fig_mesh_convergence.png"), dpi=200)
plt.close(fig)

# ---- fig 2: window-substitution attribution ----
two = sub[sub.config.isin(["full_ref_gt1__fine_le1", "full_fine_gt1__ref_le1"])].copy()
two["sid"] = two.test_index.map(SID)
labmap = {"full_ref_gt1__fine_le1": "fine $\\leq$1 V + ref >1 V",
          "full_fine_gt1__ref_le1": "ref $\\leq$1 V + fine >1 V"}
fig, ax = plt.subplots(figsize=(8.4, 3.9))
x = np.arange(len(two)); w = 0.20
c1, c2 = "tab:blue", "tab:red"
for off, (col, tag) in zip([-w / 2 - 0.02, w / 2 + 0.02], [(c1, "d vs full-REF"),
                                                          (c2, "d vs full-FINE")]):
    ax.bar(x + off, two["d_mu_vs_ref" if tag.endswith("REF") else "d_mu_vs_fine"],
           w, color=col, alpha=0.75, label=tag)
ax.axhline(0.10, color="k", ls="--", lw=0.8)
ax.text(len(two) - 0.4, 0.10, "0.1$\\sigma$ threshold", fontsize=7, va="bottom", ha="right")
xt = [("%s\nti %d" % (labmap[c], s)) for c, s in zip(two.config, two.test_index)]
ax.set_xticks(x); ax.set_xticklabels(xt, fontsize=7.5)
ax.set_ylabel("max-over-params |$\\Delta \\mu$| (normalized units)")
ax.set_title("E2-v2: window substitution — mesh-sensitivity of inverse $\\mu$ is a >1 V tail artefact\n"
             "(swapping only the >1 V segment flips prediction to that parent; the $\\leq$1 V/gen0 region cannot distinguish meshes)")
ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "e2v2_fig_window_substitution.png"), dpi=200)
plt.close(fig)
print("saved e2v2_fig_mesh_convergence.png / e2v2_fig_window_substitution.png ->", OUT)
