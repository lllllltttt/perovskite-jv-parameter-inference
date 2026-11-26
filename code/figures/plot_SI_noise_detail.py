"""
plot_SI_noise_detail.py — SI noise-robustness detail (the "full 9" panel the
main Fig. 6a condenses to bulk/interface/radiative groups).

  (a) Full 9-parameter Pearson r vs additive current noise level
      (0/0.2/0.5/1/2% of |Jsc|), every parameter individually labeled.
  (b) Full 9-parameter 95% empirical coverage vs noise level (all five
      levels), y = 0.95 reference.
  (c) Per-parameter mean predictive scale sigma across noise levels —
      the flatness of Fig. 6b is per-parameter, not just the group mean.

Frozen sources: noise_robustness/noise_metrics_all.csv,
noise_robustness/noise_calibration_summary.csv,
noise_robustness/noise_uncertainty_summary.csv. No new analysis.

Outputs under final_figures/SI/ (PNG 600dpi + vector PDF).
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
SI_DIR = os.path.join(BASE, "final_figures", "SI")
os.makedirs(SI_DIR, exist_ok=True)

NM_CSV = os.path.join(BASE, "noise_robustness", "noise_metrics_all.csv")
NC_CSV = os.path.join(BASE, "noise_robustness", "noise_calibration_summary.csv")
NU_CSV = os.path.join(BASE, "noise_robustness", "noise_uncertainty_summary.csv")

INK = "#22262b"
GRAY = "#5a6470"


def main():
    nm = pd.read_csv(NM_CSV)
    nc = pd.read_csv(NC_CSV)
    nu = pd.read_csv(NU_CSV)

    order = {p: i for i, p in enumerate(st.PARAM_NAMES)}
    pnames = sorted(nm["parameter"].unique(), key=lambda p: order[p])
    levels = ["0%", "0.2%", "0.5%", "1.0%", "2.0%"]
    xl = np.arange(5)

    rmat = np.zeros((9, 5))
    cov95 = np.zeros((9, 5))
    sig = np.zeros((9, 5))
    for i, p in enumerate(pnames):
        for j, lvl in enumerate(levels):
            rmat[i, j] = nm[(nm.parameter == p) & (nm.noise == lvl)]["r_mean"].iloc[0]
            cov95[i, j] = nc[(nc.parameter == p) & (nc.noise == lvl)
                             & (nc.nominal == 0.95)]["coverage_mean"].iloc[0]
            sig[i, j] = nu[(nu.parameter == p) & (nu.noise == lvl)]["sigma_mean"].iloc[0]

    # frozen anchors: r at 0% and 1%, coverage at 0% / 1% / 2%
    R0 = [0.9063, 0.9194, 0.8783, 0.8808, 0.9090, 0.8956, 0.5936, 0.7199, 0.5592]
    R1 = [0.8407, 0.8548, 0.8520, 0.8546, 0.8220, 0.8200, 0.5152, 0.6626, 0.5137]
    C0 = [0.9475, 0.9522, 0.9583, 0.9597, 0.9464, 0.9499, 0.9692, 0.9667, 0.9664]
    C1 = [0.8746, 0.8705, 0.9091, 0.9201, 0.8364, 0.8695, 0.9336, 0.9272, 0.9323]
    C2 = [0.7906, 0.7880, 0.8378, 0.8580, 0.7225, 0.7772, 0.8838, 0.8688, 0.8870]
    for i, p in enumerate(pnames):
        assert abs(rmat[i, 0] - R0[i]) < 1e-3 and abs(rmat[i, 3] - R1[i]) < 1e-3, p
        assert abs(cov95[i, 0] - C0[i]) < 1e-3, p
        assert abs(cov95[i, 3] - C1[i]) < 1e-3, p
        assert abs(cov95[i, 4] - C2[i]) < 1e-3, p
    print("noise-detail assertions OK (r / coverage match frozen rows)")

    w = st.set_fig_width("journal")
    fig = plt.figure(figsize=(w, w * 0.92))
    gs = fig.add_gridspec(3, 1, left=0.11, right=0.99, top=0.95, bottom=0.08,
                          hspace=0.95)

    # (a) full-9 recoverability vs noise
    axa = fig.add_subplot(gs[0, 0])
    for i, p in enumerate(pnames):
        axa.plot(xl, rmat[i], marker="o", ms=4, color=st.OKABE_ITO[i % 9],
                 lw=1.2, mfc="white", label=st.PARAM_SHORT[i])
    axa.set_xticks(xl)
    axa.set_xticklabels(levels)
    axa.set_xlabel("input noise level")
    axa.set_ylabel("Pearson $r$")
    axa.set_ylim(0.35, 1.0)
    st.configure_axes(axa)
    axa.legend(fontsize=st.FS_LEGEND, ncol=3, frameon=False, loc="lower left",
               handlelength=1.4)
    axa.text(0.0, 1.10, "(a)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axa.transAxes, color=INK)
    axa.text(0.045, 1.10, "full 9-parameter recoverability vs noise",
             fontsize=st.FS_ANNOT, color=GRAY, va="top", transform=axa.transAxes)

    # (b) full-9 coverage vs noise
    axb = fig.add_subplot(gs[1, 0])
    for i, p in enumerate(pnames):
        axb.plot(xl, cov95[i], marker="s", ms=4, color=st.OKABE_ITO[i % 9],
                 lw=1.2, mfc="white", label=st.PARAM_SHORT[i])
    axb.axhline(0.95, ls="--", color="#555555", lw=1.0)
    axb.set_xticks(xl)
    axb.set_xticklabels(levels)
    axb.set_xlabel("input noise level")
    axb.set_ylabel("95% empirical coverage")
    axb.set_ylim(0.6, 1.0)
    st.configure_axes(axb)
    axb.text(0.0, 1.10, "(b)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axb.transAxes, color=INK)
    axb.text(0.045, 1.10, "full 9-parameter calibration vs noise",
             fontsize=st.FS_ANNOT, color=GRAY, va="top", transform=axb.transAxes)

    # (c) per-parameter sigma flatness
    axc = fig.add_subplot(gs[2, 0])
    for i, p in enumerate(pnames):
        axc.plot(xl, sig[i], marker="^", ms=4, color=st.OKABE_ITO[i % 9],
                 lw=1.2, mfc="white", label=st.PARAM_SHORT[i])
    axc.set_xticks(xl)
    axc.set_xticklabels(levels)
    axc.set_xlabel("input noise level")
    axc.set_ylabel(r"mean $\sigma_\theta$")
    st.configure_axes(axc)
    axc.text(0.0, 1.10, "(c)", fontsize=st.FS_PANEL, fontweight="bold",
             va="top", transform=axc.transAxes, color=INK)
    axc.text(0.045, 1.10, "per-parameter predictive scale does not adapt to noise",
             fontsize=st.FS_ANNOT, color=GRAY, va="top", transform=axc.transAxes)

    st.save_fig(fig, os.path.join(SI_DIR, "FigS_noise_detail"))
    print("SI noise-detail figure written to", SI_DIR)


if __name__ == "__main__":
    main()
