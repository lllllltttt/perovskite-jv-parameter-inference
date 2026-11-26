# -*- coding: utf-8 -*-
"""One concise result figure for the random-subset stability analysis.

All plotted values are read from out/stability/summary.csv and
out/stability/per_replicate.csv; nothing is hard-coded.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = r"E:\project\work1"
STAB = os.path.join(BASE, "20261019_NN_stability", "out", "stability")
OUT = STAB

COORD_IDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
FAMILIES = [("mobility", "a_mu", "r_mu", "#0072B2"),
            ("lifetime", "a_tau", "r_tau", "#009E73"),
            ("DOS", "a_D", "r_D", "#CC79A7")]
SETS = [("all", "all"), ("t10", "10%"), ("t5", "5%"), ("t1", "1%"),
        ("t05", "0.5%"), ("t01", "0.1%")]
SHARED_C = "#0072B2"
RATIO_C = "#D55E00"


def main():
    S = pd.read_csv(os.path.join(STAB, "summary.csv")).set_index("quantity")
    R = pd.read_csv(os.path.join(STAB, "per_replicate.csv"))
    n = len(R)

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(7.09, 3.05),
        gridspec_kw={"width_ratios": [1.05, 1.0]})
    fv = []

    # ---------------------------------------------------------- panel (a) ---
    xs = np.arange(6)
    for i, cid in enumerate(COORD_IDS):
        col = SHARED_C if cid.startswith("a_") else RATIO_C
        o = S.loc["norm_all_" + cid]
        ax1.plot([i, i], [o["p2_5"], o["p97_5"]], color=col, lw=5.5,
                 alpha=0.35, solid_capstyle="butt", zorder=2)
        ax1.plot(i, o["original"], marker="o", ms=5.0, mfc="white",
                 mec="black", mew=1.0, zorder=4)
        ax1.plot(i, o["rep_median"], marker="o", ms=4.0, color=col,
                 mec=col, zorder=5)
        fv.append(dict(panel="a", series="norm_all_" + cid, x=i,
                       original=o["original"], median=o["rep_median"],
                       p2_5=o["p2_5"], p97_5=o["p97_5"]))
    ax1.axhline(1.0, color="0.45", lw=0.7, ls=":", zorder=1)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([r"$a_\mu$", r"$r_\mu$", r"$a_\tau$",
                         r"$r_\tau$", r"$a_D$", r"$r_D$"], fontsize=8)
    for x in (1.5, 3.5):
        ax1.axvline(x, color="0.88", lw=0.7, zorder=0)
    ax1.set_ylabel("median |Δcoord| / random-pair median", fontsize=8)
    ax1.set_title("(a) all nearest-neighbour pairs (N = {:,})".format(n),
                  fontsize=8.6, loc="left")
    ax1.text(0.02, 0.63,
             "filled: replicate median\nopen: original full sample\n"
             "bars: 2.5th–97.5th percentile\n(not a confidence interval)",
             transform=ax1.transAxes, fontsize=6.8, va="top", color="0.25")
    ax1.set_ylim(0, 1.15 * max(
        float(S.loc["norm_all_" + c, "p97_5"]) for c in COORD_IDS))

    # ---------------------------------------------------------- panel (b) ---
    for fam, ca, cr, col in FAMILIES:
        med, lo, hi = [], [], []
        for tag, _ in SETS:
            d = R["norm_%s_%s" % (tag, cr)].values - \
                R["norm_%s_%s" % (tag, ca)].values
            med.append(np.median(d))
            lo.append(np.percentile(d, 2.5))
            hi.append(np.percentile(d, 97.5))
        x = np.arange(len(SETS))
        ax2.fill_between(x, lo, hi, color=col, alpha=0.13, lw=0)
        ax2.plot(x, med, color=col, lw=1.5, marker="o", ms=3.0,
                 label=fam)
        for xi, (m, l, h) in enumerate(zip(med, lo, hi)):
            fv.append(dict(panel="b", series=fam, x=xi,
                           original=np.nan, median=m, p2_5=l, p97_5=h))
    ax2.axhline(0.0, color="0.45", lw=0.7, ls=":")
    ax2.set_xticks(np.arange(len(SETS)))
    ax2.set_xticklabels([s[1] for s in SETS], fontsize=8)
    ax2.set_xlabel("pair subset (all pairs, then closest fraction)", fontsize=8)
    ax2.set_ylabel("normalized median(r) − normalized median(a)", fontsize=8)
    ax2.set_title("(b) ratio-minus-shared contrast by tier", fontsize=9,
                  loc="left")
    ax2.legend(fontsize=7, frameon=False, loc="lower left")
    ax2.text(0.02, 0.97,
             "line: replicate median\n"
             "band: 2.5th–97.5th percentile\n"
             "descriptive resampling range,\n"
             "not a confidence interval",
             transform=ax2.transAxes, fontsize=6.8, va="top", color="0.25")

    for ax in (ax1, ax2):
        ax.tick_params(labelsize=7.5, length=2.5, width=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_linewidth(0.6)
        ax.spines["bottom"].set_linewidth(0.6)

    pd.DataFrame(fv).to_csv(os.path.join(OUT, "figure_values.csv"), index=False)
    fig.tight_layout(pad=0.6)
    for ext in ("png", "pdf", "svg"):
        p = os.path.join(OUT, "nn_stability_results." + ext)
        fig.savefig(p, dpi=300, facecolor="white")
        print("wrote", p)
    plt.close(fig)


if __name__ == "__main__":
    main()
