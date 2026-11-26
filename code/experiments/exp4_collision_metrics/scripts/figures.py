# -*- coding: utf-8 -*-
"""
EXP4 §22 — figure production (EXP4_FigA-F). Analysis-only: every panel reads a
results/*.csv (or recomputes the exact-NN distance used in metrics.py through
the shared library). Nothing trains, nothing reruns COMSOL, no frozen
manuscript content is modified.

Figure set (frozen Stage-I model, fixed d_Theta = RMSE over 9 norm.-log params):
  Fig A  dJ vs dTheta, 5 panels (M1-M5), random baseline line.
  Fig B  Distance-tier robustness (central): median dTheta vs tier per metric,
         all-NN and closest-0.1% tiers, vs random baseline.
  Fig C  Per-parameter ambiguity heatmap (metric x param), closest-1% median |d|.
  Fig D  Ambiguity-rank stability heatmap (rank 1..9 per metric).
  Fig E  NN pair-set overlap: closest-1% Jaccard between metrics.
  Fig F  Representative collisions: J-V curves + 9-param |d| bars.

Outputs: figures/EXP4_Fig{A..F}.png (600 dpi) + .pdf
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"E:\project\work1\final_figures\scripts")
from exp4_lib import (EXP4, PARAM_OUT, P_test, J_test, J_raw, V_FULL,
                      nn_for_metric, dedup)
import figure_style as fs

RES = os.path.join(EXP4, "results")
FIG = os.path.join(EXP4, "figures")
os.makedirs(FIG, exist_ok=True)

PRIMARY = ["M1", "M2", "M3", "M4", "M5"]
PARAM_LAB = [r"$\mu_n$", r"$\mu_p$", r"$\tau_n$", r"$\tau_p$",
             r"$N_c$", r"$N_v$", r"$\tau_\mathrm{ETL}$",
             r"$\tau_\mathrm{HTL}$", r"$r_\mathrm{rad}$"]
RAND_MED = 0.349021
BLUE, ORANGE, GREEN, RED = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2], fs.PALETTE[3]
GRAY, MUTED, INK = "#999999", "#555555", "#1a1a1a"
MCOL = {m: fs.PALETTE[i] for i, m in enumerate(PRIMARY)}
DJLAB = {"M1": r"$d_J$ (norm. full-curve RMSE)",
         "M2": r"$d_J$ (physical RMSE, mA cm$^{-2}$)",
         "M3": r"$d_J$ (physical / 0.5$|J_\mathrm{sc}|$ pair)",
         "M4": r"$d_J$ (physical 0-1.0 V RMSE, mA cm$^{-2}$)",
         "M5": r"$d_J$ (0-1.0 V / 0.5$|J_\mathrm{sc}|$ pair)"}


def read_csv(name):
    with open(os.path.join(RES, name), newline="") as f:
        return list(csv.DictReader(f))


def nn_pairs(m):
    """Directed NN -> dedup (I, J, dJ, dTh) for one metric (recompute, matches metrics.py)."""
    nn_idx, dJ = nn_for_metric(m)
    I, J = dedup(nn_idx)
    P = P_test()
    return I, J, dJ[I], np.sqrt(np.mean((P[I] - P[J]) ** 2, axis=1))


# ======================================================================
# Fig A — dJ vs dTheta, 5 panels
# ======================================================================
fig, axes = plt.subplots(1, 5, figsize=(fs.set_fig_width("journal"), 2.75),
                         constrained_layout=True)
for m, ax in zip(PRIMARY, axes):
    fs.configure_axes(ax)
    I, J, dj, dt = nn_pairs(m)
    ax.scatter(dj, dt, s=1.0, color=MCOL[m], alpha=0.16, rasterized=True)
    ax.axhline(RAND_MED, color=GRAY, ls=":", lw=1)
    ax.set_xscale("log")
    ax.set_ylim(0, max(0.75, dt.max() * 1.02))
    ax.set_title(m, fontsize=fs.FS_TITLE, pad=2)
    if m == "M1":
        ax.set_ylabel(r"$d_\Theta$ (param RMSE)", fontsize=fs.FS_AXIS)
    ax.set_xlabel("$d_J$", fontsize=fs.FS_AXIS)
    ax.text(0.97, 0.03, "$\u03c1_s$=%.3f" %
            float(read_csv("metric_level_summary.csv")
                  [{"M1": 0, "M2": 1, "M3": 2, "M4": 3, "M5": 4}[m]]["spearman_dJ_dTheta"]),
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=fs.FS_ANNOT, color=INK)
    fs.panel_label(ax, "(" + "abcde"[PRIMARY.index(m)] + ")")
axes[0].text(0.005, 0.97, "random baseline", transform=axes[0].transAxes,
             fontsize=fs.FS_ANNOT, color=MUTED, va="top", rotation=90)
fs.save_fig(fig, os.path.join(FIG, "EXP4_FigA"))
print("EXP4_FigA done")

# ======================================================================
# Fig B — distance-tier robustness (central)
# ======================================================================
tiers = read_csv("distance_tiers_by_metric.csv")
tier_order = ["closest_01", "closest_05", "closest_1", "closest_5",
              "closest_10", "all_NN"]
xlabs = ["closest\n0.1%", "closest\n0.5%", "closest\n1%", "closest\n5%",
         "closest\n10%", "all NN", "random"]
xs = np.arange(len(tier_order))
fig, ax = plt.subplots(figsize=(fs.set_fig_width("journal"), 3.3),
                       constrained_layout=True)
fs.configure_axes(ax)
for m in PRIMARY:
    v = [float(r["median_dTheta"]) for r in tiers
         if r["metric"] == m and r["tier"] in tier_order]
    ax.plot(xs, v, "-o", ms=3.5, lw=1.4, color=MCOL[m], label=m)
ax.axhline(RAND_MED, color=GRAY, ls=":", lw=1)
ax.text(len(xs) - 0.55, RAND_MED + 0.006, "random-pair baseline\n(%.3f)" % RAND_MED,
        fontsize=fs.FS_ANNOT, color=MUTED, va="bottom", ha="right")
ax.set_xticks(np.arange(len(xlabs)))
ax.set_xticklabels(xlabs, fontsize=fs.FS_TICK)
ax.set_ylabel(r"median $d_\Theta$ (param RMSE)", fontsize=fs.FS_AXIS)
ax.set_ylim(0.05, 0.42)
ax.legend(fontsize=fs.FS_LEGEND, frameon=False, loc="lower right", ncol=5)
fs.save_fig(fig, os.path.join(FIG, "EXP4_FigB"))
print("EXP4_FigB done")

# ======================================================================
# Fig C — per-parameter ambiguity heatmap
# ======================================================================
amb = read_csv("per_parameter_ambiguity_by_metric.csv")
M = np.zeros((len(PRIMARY), 9))
for r in amb:
    if r["metric"] in PRIMARY:
        M[PRIMARY.index(r["metric"]), PARAM_OUT.index(r["parameter"])] = \
            float(r["median_abs_delta_closest1pct"])
fig, ax = plt.subplots(figsize=(fs.set_fig_width("journal"), 2.6),
                       constrained_layout=True)
im = ax.imshow(M, cmap="Blues", vmin=0, vmax=0.22, aspect="auto")
ax.set_xticks(np.arange(9)); ax.set_xticklabels(PARAM_LAB, fontsize=fs.FS_TICK)
ax.set_yticks(np.arange(5)); ax.set_yticklabels(PRIMARY, fontsize=fs.FS_TICK)
ax.set_xticks(np.arange(-0.5, 9, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.2)
ax.tick_params(which="minor", length=0)
for i in range(5):
    for j in range(9):
        ax.text(j, i, "%.3f" % M[i, j], ha="center", va="center",
                fontsize=fs.FS_ANNOT, color=INK)
ax.set_xlabel("parameter", fontsize=fs.FS_AXIS)
ax.set_ylabel("metric", fontsize=fs.FS_AXIS)
ax.set_title("closest-1% median |$\u0394$param| (norm.-log)",
             fontsize=fs.FS_TITLE, pad=3)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.ax.tick_params(labelsize=fs.FS_TICK)
fs.save_fig(fig, os.path.join(FIG, "EXP4_FigC"))
print("EXP4_FigC done")

# ======================================================================
# Fig D — ambiguity-rank stability heatmap
# ======================================================================
R = np.zeros((len(PRIMARY), 9), int)
for r in amb:
    if r["metric"] in PRIMARY:
        R[PRIMARY.index(r["metric"]), PARAM_OUT.index(r["parameter"])] = \
            int(r["ambiguity_rank"])
fig, ax = plt.subplots(figsize=(fs.set_fig_width("journal"), 2.6),
                       constrained_layout=True)
im = ax.imshow(R, cmap="YlGnBu_r", vmin=1, vmax=9, aspect="auto")
ax.set_xticks(np.arange(9)); ax.set_xticklabels(PARAM_LAB, fontsize=fs.FS_TICK)
ax.set_yticks(np.arange(5)); ax.set_yticklabels(PRIMARY, fontsize=fs.FS_TICK)
ax.set_xticks(np.arange(-0.5, 9, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.2)
ax.tick_params(which="minor", length=0)
for i in range(5):
    for j in range(9):
        ax.text(j, i, "%d" % R[i, j], ha="center", va="center",
                fontsize=fs.FS_ANNOT, color=INK)
ax.set_xlabel("parameter", fontsize=fs.FS_AXIS)
ax.set_ylabel("metric", fontsize=fs.FS_AXIS)
ax.set_title("ambiguity rank (1 = most ambiguous, closest-1%)",
             fontsize=fs.FS_TITLE, pad=3)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.ax.tick_params(labelsize=fs.FS_TICK)
fs.save_fig(fig, os.path.join(FIG, "EXP4_FigD"))
print("EXP4_FigD done")

# ======================================================================
# Fig E — NN pair-set overlap (closest-1% Jaccard)
# ======================================================================
ov = read_csv("pair_set_overlap.csv")
O = np.zeros((5, 5))
for r in ov:
    if r["metric_A"] in PRIMARY and r["metric_B"] in PRIMARY:
        O[PRIMARY.index(r["metric_A"]), PRIMARY.index(r["metric_B"])] = \
            float(r["closest1pct_jaccard"])
fig, ax = plt.subplots(figsize=(fs.set_fig_width("journal"), 2.6),
                       constrained_layout=True)
im = ax.imshow(O, cmap="Purples", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(np.arange(5)); ax.set_xticklabels(PRIMARY, fontsize=fs.FS_TICK)
ax.set_yticks(np.arange(5)); ax.set_yticklabels(PRIMARY, fontsize=fs.FS_TICK)
ax.set_xticks(np.arange(-0.5, 5, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.2)
ax.tick_params(which="minor", length=0)
for i in range(5):
    for j in range(5):
        ax.text(j, i, "%.3f" % O[i, j], ha="center", va="center",
                fontsize=fs.FS_ANNOT, color=INK)
ax.set_xlabel("metric B", fontsize=fs.FS_AXIS)
ax.set_ylabel("metric A", fontsize=fs.FS_AXIS)
ax.set_title("closest-1% pair-set Jaccard overlap",
             fontsize=fs.FS_TITLE, pad=3)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.ax.tick_params(labelsize=fs.FS_TICK)
fs.save_fig(fig, os.path.join(FIG, "EXP4_FigE"))
print("EXP4_FigE done")

# ======================================================================
# Fig F — representative collisions (J-V curves + param |d| bars)
# ======================================================================
rep = read_csv("representative_collision_metric_check.csv")
Xr, Xn = J_raw(), J_test()
V = V_FULL
case_short = {"tau_ETL_dominant": "$\u03c4_\\mathrm{ETL}$-dominant",
              "r_rad_dominant": "$r_\\mathrm{rad}$-dominant",
              "cross_metric_robust": "cross-metric robust"}
fig, axes = plt.subplots(2, 3, figsize=(fs.set_fig_width("journal"), 4.1),
                         constrained_layout=True)
for ci, r in enumerate(rep):
    i, j = int(r["i"]), int(r["j"])
    ax = axes[0, ci]
    fs.configure_axes(ax)
    ax.plot(V, Xr[i], "-", color=BLUE, lw=1.1, label="sample %d" % i)
    ax.plot(V, Xr[j], "--", color=ORANGE, lw=1.1, label="sample %d" % j)
    ax.set_xlabel(r"$V$ (V)", fontsize=fs.FS_AXIS)
    if ci == 0:
        ax.set_ylabel(r"$J$ (mA cm$^{-2}$)", fontsize=fs.FS_AXIS)
    ax.text(0.04, 0.06, "$d_\\Theta$=%.3f" % float(r["dTheta"]),
            transform=ax.transAxes, fontsize=fs.FS_ANNOT, color=INK)
    ax.text(0.04, 0.94, "$p_{M1}$=%.1f%%  $p_{M4}$=%.1f%%" %
            (float(r["pct_M1"]) * 100, float(r["pct_M4"]) * 100),
            transform=ax.transAxes, va="top", fontsize=fs.FS_ANNOT, color=MUTED)
    if ci == 2:
        ax.legend(fontsize=fs.FS_LEGEND, frameon=False, loc="upper left")
    fs.panel_label(ax, "(" + "abc"[ci] + ")", dy=1.0)

    ax = axes[1, ci]
    fs.configure_axes(ax)
    ad = np.array([float(r["absd_" + p]) for p in PARAM_OUT])
    dom = int(np.argmax(ad))
    colors = [RED if k == dom else GRAY for k in range(9)]
    ax.bar(np.arange(9), ad, color=colors, width=0.66)
    ax.set_xticks(np.arange(9))
    ax.set_xticklabels(PARAM_LAB, fontsize=fs.FS_TICK, rotation=40)
    ax.set_ylim(0, max(0.68, ad.max() * 1.1))
    if ci == 0:
        ax.set_ylabel(r"$|\Delta \mathrm{param}|$ (norm.-log)",
                      fontsize=fs.FS_AXIS)
    ax.text(dom, ad[dom] + 0.02, "%.2f" % ad[dom], ha="center",
            fontsize=fs.FS_ANNOT, color=RED)
    fs.panel_label(ax, "(" + "def"[ci] + ")", dy=1.0)
    ax.set_title(case_short[r["case"]], fontsize=fs.FS_TITLE, pad=2)
fs.save_fig(fig, os.path.join(FIG, "EXP4_FigF"))
print("EXP4_FigF done")

print("all EXP4 figures written to %s" % FIG)
