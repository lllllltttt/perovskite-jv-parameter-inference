# -*- coding: utf-8 -*-
"""
EXP3 §17 — figure production (EXP3_FigA-F). Analysis-only: every panel reads a
results/*.csv (or the frozen model's stored test predictions) — nothing trains,
nothing reruns COMSOL, no frozen manuscript content is modified.

Figure set (frozen Stage-I model unless stated):
  Fig A  Coordinate recoverability: (a) Pearson r, 6 coords; (b) skill_RMSE
         = J-V information beyond the train-only prior point predictor.
  Fig B  Paired decomposition: marginal (n,p) vs shared-scale a vs ratio r.
  Fig C  Prior geometry: SD(a) vs SD(0.5r) per pair + algebra-reproduced
         marginal pair correlation vs manuscript values.
  Fig D  Predicted-vs-truth scatter (log10 physical), 2x3 grid of the 6 coords.
  Fig E  Coordinate sensitivity to J(V) vs recoverability r (labeled scatter).
  Fig F  Architecture robustness: mean +/- SD Pearson across 5 EXP1 seeds
         for vae / det_ae / mlp.

Outputs: figures/EXP3_Fig{A..F}.png (600 dpi) + .pdf
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"E:\project\work1\final_figures\scripts")
from exp3_lib import (EXP3, COORDS, PAIR_ORDER, PAIRS, coords_from_log10,
                      frozen_test, frozen_norm_to_log10, frozen_pred_log10)
import figure_style as fs

RES = os.path.join(EXP3, "results")
FIG = os.path.join(EXP3, "figures")
os.makedirs(FIG, exist_ok=True)

# ---- read CSVs ---------------------------------------------------------
def read_csv(name):
    with open(os.path.join(RES, name), newline="") as f:
        return list(csv.DictReader(f))

rec    = {r["coordinate"]: r for r in read_csv("frozen_coordinate_recoverability.csv")}
arch   = read_csv("architecture_coordinate_summary.csv")
sens   = {r["coordinate"]: r for r in read_csv("coordinate_sensitivity.csv")}
paired = read_csv("paired_coordinate_comparison.csv")
geom   = {(r["pair"], r["population"]): r for r in read_csv("pair_geometry.csv")}
shuf   = read_csv("shuffled_pairing_null.csv")
GRAY, MUTED, INK = "#999999", "#555555", "#1a1a1a"

# ---- model predictions for Fig D ---------------------------------------
print("loading frozen predictions for Fig D ...")
true_L = frozen_norm_to_log10(frozen_test()["params_test"])
pred_L = frozen_pred_log10()
C_true, C_pred = coords_from_log10(true_L), coords_from_log10(pred_L)

BLUE, ORANGE, GREEN, RED = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2], fs.PALETTE[3]
FAM_COL = {"vae": BLUE, "det_ae": ORANGE, "mlp": GREEN}

# ======================================================================
# Fig A — coordinate recoverability + info beyond prior
# ======================================================================
fig, axes = plt.subplots(1, 2, figsize=(fs.set_fig_width("journal"), 3.1),
                         constrained_layout=True)
for ax in axes:
    fs.configure_axes(ax)

x = np.arange(6)
a_mask = np.array([c.startswith("a_") for c in COORDS])
ax = axes[0]
vals = [float(rec[c]["pearson_r"]) for c in COORDS]
ax.bar(x[a_mask], [v for v, m in zip(vals, a_mask) if m], width=0.62,
       color=BLUE, label="shared scale $a$")
ax.bar(x[~a_mask], [v for v, m in zip(vals, a_mask) if not m], width=0.62,
       color=ORANGE, label="asymmetry ratio $r$")
ax.set_xticks(x); ax.set_xticklabels(COORDS, fontsize=fs.FS_TICK)
ax.set_ylim(0, 1.02)
ax.set_ylabel("Pearson $r$ (frozen model)", fontsize=fs.FS_AXIS)
ax.axhline(0.014, color=GRAY, ls=":", lw=1)
ax.text(0.01, 0.05, "shuffled-null p95 \u2248 0.014", transform=ax.transAxes,
        fontsize=fs.FS_ANNOT, color=MUTED, va="bottom")
ax.legend(loc="lower right", fontsize=fs.FS_LEGEND, frameon=False)
fs.panel_label(ax, "(a)")

ax = axes[1]
vals = [float(rec[c]["skill_rmse"]) for c in COORDS]
ax.bar(x[a_mask], [v for v, m in zip(vals, a_mask) if m], width=0.62,
       color=BLUE)
ax.bar(x[~a_mask], [v for v, m in zip(vals, a_mask) if not m], width=0.62,
       color=ORANGE)
ax.set_xticks(x); ax.set_xticklabels(COORDS, fontsize=fs.FS_TICK)
ax.set_ylim(0, 1.02)
ax.set_ylabel("Skill$_{RMSE}$ vs prior-only", fontsize=fs.FS_AXIS)
ax.text(0.01, 0.97, "1 \u2212 MSE$_{model}$/MSE$_{prior\\,mean}$",
        transform=ax.transAxes, fontsize=fs.FS_ANNOT, va="top", ha="left",
        color=MUTED)
fs.panel_label(ax, "(b)")
fs.save_fig(fig, os.path.join(FIG, "EXP3_FigA"))
print("EXP3_FigA done")

# ======================================================================
# Fig B — paired decomposition (marginal vs shared-scale vs ratio)
# ======================================================================
fig, ax = plt.subplots(figsize=(fs.set_fig_width("journal"), 3.1),
                       constrained_layout=True)
fs.configure_axes(ax)
pairs = [p["pair"] for p in paired]
xw = np.arange(len(pairs))
w = 0.2
for off, (key, col, lab) in enumerate(
        [("r_marginal1", GRAY, "marginal n"),
         ("r_marginal2", "#bfbfbf", "marginal p"),
         ("r_shared", BLUE, "shared scale $a$"),
         ("r_ratio", ORANGE, "ratio $r$")]):
    v = [float(p[key]) for p in paired]
    ax.bar(xw + (off - 1.5) * w, v, width=w, color=col, label=lab)
ax.set_xticks(xw); ax.set_xticklabels(pairs, fontsize=fs.FS_TICK)
ax.set_ylabel("Pearson $r$ (frozen model)", fontsize=fs.FS_AXIS)
ax.set_ylim(0, 1.02)
ax.axhline(0.014, color=GRAY, ls=":", lw=1)
ax.legend(loc="lower left", fontsize=fs.FS_LEGEND, frameon=False, ncol=4)
fs.save_fig(fig, os.path.join(FIG, "EXP3_FigB"))
print("EXP3_FigB done")

# ======================================================================
# Fig C — prior geometry: SD(a) vs SD(0.5r) + algebra reproduction
# ======================================================================
fig, axes = plt.subplots(1, 2, figsize=(fs.set_fig_width("journal"), 3.1),
                         constrained_layout=True)
for ax in axes:
    fs.configure_axes(ax)

ax = axes[0]
pairs = [p["pair"] for p in paired]
sd_a  = [float(geom[(p, "test")]["sd_average"]) for p in pairs]
sd_h  = [float(geom[(p, "test")]["sd_half_log_ratio"]) for p in pairs]
xw = np.arange(len(pairs)); w = 0.34
ax.bar(xw - w/2, sd_a, width=w, color=BLUE, label="SD$(a)$ shared scale")
ax.bar(xw + w/2, sd_h, width=w, color=ORANGE, label="SD$(0.5\\,r)$ ratio")
ax.set_xticks(xw); ax.set_xticklabels(pairs, fontsize=fs.FS_TICK)
ax.set_ylabel("SD (decades, log10 phys)", fontsize=fs.FS_AXIS)
ax.set_ylim(0, 2.4)
ax.legend(fontsize=fs.FS_LEGEND, frameon=False, loc="upper right")
for i, (sa, sh) in enumerate(zip(sd_a, sd_h)):
    ax.text(i, sa + 0.06, "%.1f\u00d7" % (sa / sh), ha="center",
            fontsize=fs.FS_ANNOT, color=INK)
fs.panel_label(ax, "(a)")

ax = axes[1]
manu = {"mobility": 0.94, "lifetime": 0.99, "DOS": 0.90}
alg  = {"mobility": float(geom[("mobility", "test")]["marginal_pair_pearson"]),
        "lifetime": float(geom[("lifetime", "test")]["marginal_pair_pearson"]),
        "DOS":      float(geom[("DOS", "test")]["marginal_pair_pearson"])}
xs = np.arange(len(pairs)); w = 0.34
ax.bar(xs - w/2, [alg[p] for p in pairs], width=w, color=BLUE,
       label="algebra corr$(n,p)$")
ax.bar(xs + w/2, [manu[p] for p in pairs], width=w, color=GRAY,
       label="manuscript corr")
ax.set_xticks(xs); ax.set_xticklabels(pairs, fontsize=fs.FS_TICK)
ax.set_ylim(0.7, 1.02)
ax.set_ylabel("Pairwise correlation", fontsize=fs.FS_AXIS)
ax.legend(fontsize=fs.FS_LEGEND, frameon=False, loc="lower left")
fs.panel_label(ax, "(b)")
fs.save_fig(fig, os.path.join(FIG, "EXP3_FigC"))
print("EXP3_FigC done")

# ======================================================================
# Fig D — predicted vs truth, 2x3 grid (log10 physical decades)
# ======================================================================
fig, axes = plt.subplots(2, 3, figsize=(fs.set_fig_width("journal"), 4.4),
                         constrained_layout=True)
for ci, ax in enumerate(axes.flat):
    fs.configure_axes(ax)
    t, p = C_true[:, ci], C_pred[:, ci]
    r = pearsonr(t, p)[0]
    lo = min(t.min(), p.min()); hi = max(t.max(), p.max())
    pad = 0.06 * (hi - lo)
    ax.scatter(t, p, s=1.2, color=BLUE, alpha=0.18, rasterized=True)
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], ls="--", color=GRAY,
            lw=1)
    ax.set_xlim(lo - pad, hi + pad); ax.set_ylim(lo - pad, hi + pad)
    ax.set_title(COORDS[ci], fontsize=fs.FS_TITLE)
    ax.text(0.04, 0.95, "$r$ = %.3f" % r, transform=ax.transAxes, va="top",
            fontsize=fs.FS_ANNOT, color=INK)
    if ci // 3 == 1:
        ax.set_xlabel("true (decades)", fontsize=fs.FS_AXIS)
    if ci % 3 == 0:
        ax.set_ylabel("predicted (decades)", fontsize=fs.FS_AXIS)
    fs.panel_label(ax, "(" + "abcdef"[ci] + ")")
fs.save_fig(fig, os.path.join(FIG, "EXP3_FigD"))
print("EXP3_FigD done")

# ======================================================================
# Fig E — sensitivity to J(V) vs recoverability
# ======================================================================
fig, ax = plt.subplots(figsize=(4.2, 3.4), constrained_layout=True)
fs.configure_axes(ax)
for c in COORDS:
    s = float(sens[c]["sensitivity_S"]); r = float(rec[c]["pearson_r"])
    col = BLUE if c.startswith("a_") else ORANGE
    ax.scatter(s, r, s=60, color=col, zorder=3, edgecolor="white", lw=0.6)
    ax.annotate(c, (s, r), textcoords="offset points", xytext=(6, 5),
                fontsize=fs.FS_ANNOT, color=INK)
ax.set_xlabel("sensitivity $S_i$ = mean$_V$|corr$(c_i, J(V))$|",
              fontsize=fs.FS_AXIS)
ax.set_ylabel("Pearson $r$ (recoverability)", fontsize=fs.FS_AXIS)
ax.set_xlim(0, 0.62); ax.set_ylim(0, 1.05)
ax.axhline(0.014, color=GRAY, ls=":", lw=1)
ax.text(0.03, 0.06, "shuffled-null p95", fontsize=fs.FS_ANNOT,
        color=MUTED)
fs.save_fig(fig, os.path.join(FIG, "EXP3_FigE"))
print("EXP3_FigE done")

# ======================================================================
# Fig F — architecture robustness (5 EXP1 seeds, mean +/- SD)
# ======================================================================
fig, ax = plt.subplots(figsize=(fs.set_fig_width("journal"), 3.3),
                       constrained_layout=True)
fs.configure_axes(ax)
fam_order = ["vae", "det_ae", "mlp"]
x = np.arange(6); w = 0.26
for fi, fam in enumerate(fam_order):
    means = [float(next(r["pearson_mean"] for r in arch
                        if r["family"] == fam and r["coordinate"] == c)) for c in COORDS]
    sds   = [float(next(r["pearson_sd"] for r in arch
                        if r["family"] == fam and r["coordinate"] == c)) for c in COORDS]
    ax.bar(x + (fi - 1) * w, means, width=w, yerr=sds, capsize=2.5,
           color=FAM_COL[fam], label=fam, error_kw=dict(lw=0.8))
ax.set_xticks(x); ax.set_xticklabels(COORDS, fontsize=fs.FS_TICK)
ax.set_ylabel("Pearson $r$ (mean \u00b1 SD, 5 seeds)", fontsize=fs.FS_AXIS)
ax.set_ylim(0, 1.05)
ax.legend(fontsize=fs.FS_LEGEND, frameon=False, loc="upper right")
fs.save_fig(fig, os.path.join(FIG, "EXP3_FigF"))
print("EXP3_FigF done")

print("all EXP3 figures written to %s" % FIG)
