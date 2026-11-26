# -*- coding: utf-8 -*-
"""Comparison figures: Skill_MSE and physical log10 error side by side.

fig02_skill_and_error.{png,pdf,svg}   own-distribution comparison (table A)
fig03_common_test_paired.{png,pdf,svg} paired model differences on the two
                                       common test sets (table B)

All plotted numbers come from out/metrics/*.csv; the figure-values file lists
every plotted value so the figures can be rebuilt from the prediction files.
"""
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MET = os.path.join(ROOT, "out", "metrics")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
LABEL = {"a_mu": r"$a_\mu$", "r_mu": r"$r_\mu$", "a_tau": r"$a_\tau$",
         "r_tau": r"$r_\tau$", "a_D": r"$a_D$", "r_D": r"$r_D$"}
C_OLD, C_NEW = "#0072B2", "#D55E00"
plt.rcParams.update({"font.size": 8, "axes.labelsize": 9,
                     "axes.titlesize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False})


def bar_panel(ax, long, metric, title, ylabel):
    vals = {}
    for arm in ("original", "expanded"):
        g = long[long["model_arm"] == arm]
        means, sds, pts = [], [], []
        for c in COORDS:
            v = g[g["quantity"] == c][metric].astype(float).to_numpy()
            means.append(np.nanmean(v))
            sds.append(np.nanstd(v, ddof=1))
            pts.append(v)
        vals[arm] = (np.array(means), np.array(sds), pts)
    x = np.arange(len(COORDS))
    w = 0.36
    for k, (arm, col, lab) in enumerate((
            ("original", C_OLD, "original 0.2–5 (own test)"),
            ("expanded", C_NEW, "expanded 0.05–20 (own test)"))):
        m, s, pts = vals[arm]
        ax.bar(x + (k - 0.5) * w, m, w, color=col, alpha=0.85, label=lab,
               yerr=s, capsize=2, error_kw={"lw": 0.8})
        for i, p in enumerate(pts):
            ax.plot(np.full(len(p), x[i] + (k - 0.5) * w), p, "o", ms=2.4,
                    color="black", alpha=0.55, mew=0)
    ax.set_xticks(x)
    ax.set_xticklabels([LABEL[c] for c in COORDS])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.axhline(0, color="black", lw=0.6)
    ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    return vals


def main():
    long = pd.read_csv(os.path.join(MET, "table_B_common_tests.csv"))
    A = long[long["test_arm"] == long["model_arm"]]
    fv = []

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    vals_skill = bar_panel(
        axes[0], A, "skill_mse",
        "(a) Skill$_\\mathrm{MSE}$ (higher is better)", "Skill$_{MSE}$")
    vals_rmse = bar_panel(
        axes[1], A, "rmse",
        "(b) RMSE in physical log$_{10}$ (lower is better)",
        "RMSE (log$_{10}$ units)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.05),
               ncol=2, frameon=False, handlelength=1.4, columnspacing=1.6)
    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(os.path.join(FIG, "fig02_skill_and_error." + ext),
                    dpi=600, facecolor="white", bbox_inches="tight")
    plt.close(fig)

    for arm in ("original", "expanded"):
        for i, c in enumerate(COORDS):
            for metric, store in (("skill_mse", vals_skill), ("rmse", vals_rmse)):
                v = store[arm][2][i]
                for s, x in zip(v, range(len(v))):
                    fv.append({"figure": "fig02", "arm": arm, "coordinate": c,
                               "metric": metric, "seed_index": s, "value": x})
            fv.append({"figure": "fig02", "arm": arm, "coordinate": c,
                       "metric": "skill_mse_mean", "seed_index": "",
                       "value": vals_skill[arm][0][i]})
            fv.append({"figure": "fig02", "arm": arm, "coordinate": c,
                       "metric": "rmse_mean", "seed_index": "",
                       "value": vals_rmse[arm][0][i]})

    # ---------------- fig03: paired differences on common tests --------
    # Plotted quantity is the physical log10 error, not Skill: Skill is
    # measured against each test set's own baseline and its differences
    # inherit the baseline-variance change, while delta-RMSE answers directly
    # whether the prediction error moved.
    P = pd.read_csv(os.path.join(MET, "paired_differences.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for ax, test_arm, title in zip(
            axes, ("original", "expanded"),
            ("(a) common original-range test", "(b) common expanded-range test")):
        g = P[P["test_arm"] == test_arm]
        x = np.arange(len(COORDS))
        for i, c in enumerate(COORDS):
            v = g[g["quantity"] == c]["diff_new_minus_old_rmse"].to_numpy()
            ax.plot(np.full(len(v), i), v, "o", ms=3, color=C_NEW, alpha=0.6,
                    mew=0)
            ax.plot([i - 0.22, i + 0.22], [np.mean(v)] * 2, color="black",
                    lw=1.8)
            for s, val in enumerate(v):
                fv.append({"figure": "fig03", "test_arm": test_arm,
                           "coordinate": c, "metric": "diff_rmse",
                           "seed_index": s, "value": val})
        ax.set_xticks(x)
        ax.set_xticklabels([LABEL[c] for c in COORDS])
        ax.set_title(title)
        ax.axhline(0, color="black", lw=0.6)
        ax.grid(axis="y", ls=":", lw=0.5, alpha=0.5)
    axes[0].set_ylabel("Δ RMSE\n(log$_{10}$ units)")
    fig.text(0.5, -0.01,
             "Δ = expanded-trained − original-trained; negative means the "
             "expanded model has the smaller error",
             ha="center", va="top", fontsize=7)
    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(os.path.join(FIG, "fig03_common_test_paired." + ext),
                    dpi=600, facecolor="white", bbox_inches="tight")
    plt.close(fig)

    pd.DataFrame(fv).to_csv(os.path.join(FIG, "figure_values.csv"), index=False)
    print("figures written; values ->", os.path.join(FIG, "figure_values.csv"))


if __name__ == "__main__":
    main()
