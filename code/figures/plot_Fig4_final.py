"""
plot_Fig4_final.py — Fig. 4 (final) of the FINAL figure package.
=================================================================
"Predictive uncertainty and calibration in the clean simulation domain."

All numbers come from evaluation_fixed/ ONLY — the fixed softplus+0.01
sigma chain (sigma_theta = clip(softplus(sigma_raw) + 0.01, 0.01, 1.0)).
No data is altered or recomputed; every plotted value is asserted against
the frozen lists below before the figure is written.

  (a) Calibration curves: empirical vs nominal predictive-interval coverage
      at the 50 / 80 / 90 / 95% levels (y = x reference, neutral gray).
      9-parameter legend in 3 compact columns above the axes, no box.
  (b) Parameter-wise empirical coverage at the nominal 95% level — horizontal
      categorical dot plot; the y tick labels ARE the parameter names
      (mathematical symbols, canonical order). Range 0.946-0.969, 0.95 ref.
  (c) Spearman association between the predicted Gaussian-head predictive
      scale sigma_theta and the absolute point-prediction error |error| —
      horizontal lollipop (light-gray stem 0 -> rho, colored dot). Mean
      rho = 0.428 shown as a dotted reference line with the annotation near
      the top of the line, in an empty region (does not cover any dot).

Panel geometry: (a):(b):(c) width ratio 1.25 : 1.0 : 1.0, strictly equal
heights, panel labels only — no in-figure text titles, no code-style
parameter names (math symbols only), no scientific interpretation inside
the figure (all interpretation lives in the caption).

Frozen sources: evaluation_fixed/calibration_fixed.csv,
evaluation_fixed/uncertainty_error_fixed.csv.

Outputs:
  final_figures/Fig4/Fig4_final.png / .pdf
  final_figures/Fig4/Fig4_final_large.png / .pdf
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
OUT_DIR = os.path.join(BASE, "final_figures", "Fig4")
os.makedirs(OUT_DIR, exist_ok=True)

CAL_CSV = os.path.join(BASE, "evaluation_fixed", "calibration_fixed.csv")
UNC_CSV = os.path.join(BASE, "evaluation_fixed", "uncertainty_error_fixed.csv")

# expected 95% coverage (frozen manuscript; canonical param order)
COV95_EXPECTED = [0.947475, 0.952244, 0.95832, 0.959692, 0.946364,
                  0.949892, 0.969164, 0.966682, 0.966421]
# expected Spearman rho (frozen manuscript; canonical param order)
RHO_EXPECTED = [0.398191, 0.334319, 0.645906, 0.621839, 0.353014,
                0.244391, 0.377232, 0.464704, 0.414716]
MEAN_RHO_EXPECTED = 0.428        # frozen (actual mean 0.4283)

# unified mathematical parameter symbols (same order + same colors as the
# canonical st.PARAM_NAMES order); r_rad per the Fig.4 spec (NOT r_ad)
LABELS = [
    r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
    r"$N_c$", r"$N_v$", r"$\tau_\mathrm{ETL}$",
    r"$\tau_\mathrm{HTL}$", r"$r_\mathrm{rad}$",
]
# plain-text code names (for in-script checks ONLY — never drawn)
CODE_NAMES = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv",
              "tau_ETL", "tau_HTL", "rad_c"]


def _load_frozen():
    """Load + assert the frozen coverage/rho values; return (levels, cov, rho)."""
    cal = pd.read_csv(CAL_CSV)
    unc = pd.read_csv(UNC_CSV)

    levels = np.sort(cal["nominal"].unique())
    order = {p: i for i, p in enumerate(st.PARAM_NAMES)}
    pnames = sorted(cal["parameter"].unique(), key=lambda p: order[p])
    assert pnames == st.PARAM_NAMES, pnames

    cov = np.zeros((9, len(levels)))
    for j, lvl in enumerate(levels):
        for i, p in enumerate(pnames):
            row = cal[(cal["parameter"] == p) & (cal["nominal"] == lvl)]
            cov[i, j] = row["empirical_coverage"].iloc[0]

    for i, p in enumerate(pnames):
        c95 = float(cal[(cal["parameter"] == p) & (cal["nominal"] == 0.95)]
                    ["empirical_coverage"].iloc[0])
        assert abs(c95 - COV95_EXPECTED[i]) < 1e-4, (p, c95)
    for p, exp in zip(pnames, RHO_EXPECTED):
        got = float(unc.loc[unc["parameter"] == p, "spearman_rho"].iloc[0])
        assert abs(got - exp) < 1e-4, (p, got, exp)
    rho = unc.set_index("parameter").loc[pnames, "spearman_rho"].values
    assert abs(rho.mean() - MEAN_RHO_EXPECTED) < 5e-4, rho.mean()
    return levels, cov, rho


def build_figure(size="journal"):
    """Construct the figure (and return it + QC info) without saving."""
    levels, cov, rho = _load_frozen()
    mean_rho = rho.mean()
    ys = np.arange(9)[::-1]          # param 0 (mu_n) on top ... param 8 at bottom

    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 0.38))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.0],
                          left=0.085, right=0.99, top=0.76, bottom=0.16,
                          wspace=0.30)

    # ---------------- (a) calibration curves ----------------
    axa = fig.add_subplot(gs[0, 0])
    diag = np.array([0.45, 1.0])
    axa.plot(diag, diag, ls="--", color="#999999", lw=0.8, alpha=0.9, zorder=1)
    for i in range(9):
        axa.plot(levels, cov[i], marker="o", ms=3.5, lw=1.0, alpha=0.85,
                 color=st.OKABE_ITO[i], label=LABELS[i], zorder=2)
    axa.set_xlabel("Nominal coverage")
    axa.set_ylabel("Empirical coverage")
    axa.set_xlim(0.45, 1.0)
    axa.set_ylim(0.45, 1.0)
    axa.set_xticks([0.5, 0.8, 0.9, 0.95])
    axa.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    st.configure_axes(axa)
    # journal width: the four nominal levels 0.5/0.8/0.9/0.95 are close
    # together, so the x tick labels use 7.0 pt (still >= MIN_FS 6.5) to keep
    # all four clearly legible without overlap.
    for t in axa.get_xticklabels():
        t.set_fontsize(7.0)
    axa.grid(True, linestyle=":", color=st.GRID, linewidth=0.5, alpha=0.25)
    leg = axa.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=3,
                     frameon=False, fontsize=st.FS_LEGEND, handlelength=1.1,
                     columnspacing=0.9, handletextpad=0.5, borderaxespad=0.0)
    st.panel_label(axa, "(a)")

    # ---------------- (b) 95% coverage (horizontal dot plot) ----------------
    axb = fig.add_subplot(gs[0, 1])
    axb.axvline(0.95, ls="--", color="#777777", lw=0.9, zorder=1)
    axb.scatter(cov[:, -1], ys, s=30, color=[st.OKABE_ITO[i] for i in range(9)],
                edgecolor="white", linewidth=0.5, zorder=3)
    axb.set_yticks(ys)
    axb.set_yticklabels(LABELS)
    axb.set_xlabel("Empirical coverage at 95%\nnominal level")
    axb.set_xlim(0.94, 0.975)
    axb.set_xticks([0.94, 0.95, 0.96, 0.97])
    axb.set_ylim(-0.6, 9.0)
    st.configure_axes(axb)
    st.panel_label(axb, "(b)")

    # ---------------- (c) Spearman(sigma_theta, |error|) lollipop ------------
    axc = fig.add_subplot(gs[0, 2])
    for i in range(9):
        axc.plot([0.0, rho[i]], [ys[i], ys[i]], color="#c9ced4", lw=1.2, zorder=1)
        axc.plot(rho[i], ys[i], marker="o", ms=6, color=st.OKABE_ITO[i],
                 zorder=3)
    axc.axvline(mean_rho, ls=":", color="#555555", lw=1.1, zorder=2)
    # mean annotation just above the axes top, centred on the dotted line
    # (x in data coords, y in axes fraction) — empty region, no dot overlap.
    axc.text(mean_rho, 1.02, r"$\bar{\rho}=%.3f$" % mean_rho,
             transform=axc.get_xaxis_transform(), ha="center", va="bottom",
             fontsize=st.FS_ANNOT, color=st.MUTED)
    axc.set_yticks(ys)
    axc.set_yticklabels(LABELS)
    axc.set_xlabel(r"Spearman $\rho(\sigma_\theta,\ |\mathrm{error}|)$")
    axc.set_xlim(-0.02, 0.75)
    axc.set_xticks([0.0, 0.2, 0.4, 0.6])
    axc.set_ylim(-0.6, 9.0)
    st.configure_axes(axc)
    st.panel_label(axc, "(c)")

    info = dict(fig=fig, axa=axa, axb=axb, axc=axc, levels=levels, cov=cov,
                rho=rho, mean_rho=mean_rho, ys=ys, legend=leg, labels=LABELS)
    return fig, info


def main():
    levels, cov, rho = _load_frozen()
    print("95%% coverage range: %.4f - %.4f  (expected 0.946-0.969)"
          % (cov[:, -1].min(), cov[:, -1].max()))
    print("mean rho: %.4f  (frozen 0.428)" % rho.mean())
    print("nominal levels:", levels.tolist())

    for size in ("journal", "large"):
        fig, info = build_figure(size)
        stem = os.path.join(OUT_DIR, "Fig4_final"
                            + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
