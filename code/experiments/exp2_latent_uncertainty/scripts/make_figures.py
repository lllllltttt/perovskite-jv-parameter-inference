# -*- coding: utf-8 -*-
"""
EXP2 reviewer-analysis figures (spec §19). Reads results/*.csv + the
sample-level npz. Does NOT touch the frozen Fig.1-Fig.6.

FigA variance decomposition (median head vs latent fraction, stacked + latent zoom)
FigB absolute uncertainty components in log10 decades (head / latent / total)
FigC current vs latent-propagated calibration (per-param, moment + mixture)
FigD error ranking (rho_current / rho_latent / rho_total)
FigE sigma widening (sigma_total / sigma_current distribution)
FigF encoder latent diagnostics (z_mean SD vs posterior latent std)
FigG latent-induced parameter correlation heatmap (descriptive only)
"""
import os, sys, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import EXP2, PARAM_SHORT, PARAM_LOG_RANGE

RES = os.path.join(EXP2, "results")
FIG = os.path.join(EXP2, "figures")
os.makedirs(FIG, exist_ok=True)

C_HEAD = "#0072B2"; C_LAT = "#E69F00"; C_TOT = "#009E73"
C_CUR = "#D55E00"; C_MIX = "#56B4E9"

d = np.load(os.path.join(RES, "sample_level_decomposition.npz"))
X = np.arange(9)

def csvrows(name):
    with open(os.path.join(RES, name), newline="", encoding="utf-8") as f:
        return list(csv.reader(f))  # header row + data rows

# ============ FigA — variance decomposition ============
v = csvrows("variance_decomposition_by_parameter.csv")
v = [r for r in v if r[0] != "parameter"]
med_f_head = np.array([1.0 - float(r[8]) for r in v])
med_f_lat = np.array([float(r[8]) for r in v])
q25_f = np.array([float(r[9]) for r in v])
q75_f = np.array([float(r[10]) for r in v])

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), gridspec_kw={"width_ratios": [1.0, 1.0]})
ax = axes[0]
ax.bar(X, med_f_head, color=C_HEAD, label="Gaussian head share")
ax.bar(X, med_f_lat, bottom=med_f_head, color=C_LAT, label="latent share")
ax.set_xticks(X); ax.set_xticklabels(PARAM_SHORT, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("median variance fraction")
ax.set_ylim(0, 1.01)
ax.set_title("(a) variance decomposition (head + latent)", fontsize=10)
ax.legend(fontsize=8, frameon=False)

ax = axes[1]
ax.bar(X, 100 * med_f_lat, color=C_LAT)
ax.errorbar(X, 100 * med_f_lat,
            yerr=[100 * (med_f_lat - q25_f), 100 * (q75_f - med_f_lat)],
            fmt="none", ecolor="#333333", capsize=2, linewidth=0.8)
ax.set_xticks(X); ax.set_xticklabels(PARAM_SHORT, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("latent share of variance [%]")
ax.set_title("(b) latent share (median + IQR) — zoomed", fontsize=10)
for i, val in enumerate(100 * med_f_lat):
    ax.text(i, 100 * med_f_lat[i] + 0.006, "%.3f" % val, ha="center", va="bottom", fontsize=6.5)
fig.suptitle("EXP2 FigA — model-implied predictive variance: Gaussian head vs latent sampling",
             fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(os.path.join(FIG, "EXP2_FigA.png"), dpi=300)
plt.close(fig)

# ============ FigB — uncertainty components in decades ============
sig_head_dec = np.sqrt(d["V_head"]) * PARAM_LOG_RANGE[None, :]
sig_lat_dec = np.sqrt(d["V_latent"]) * PARAM_LOG_RANGE[None, :]
sig_tot_dec = np.sqrt(d["V_total"]) * PARAM_LOG_RANGE[None, :]

def med_iqr(a):
    return np.median(a, axis=0), np.percentile(a, 25, axis=0), np.percentile(a, 75, axis=0)

mh, lh, hh = med_iqr(sig_head_dec)
ml, ll, hl = med_iqr(sig_lat_dec)
mt, lt, ht = med_iqr(sig_tot_dec)

fig, ax = plt.subplots(figsize=(10.5, 4.6))
w = 0.27
ax.bar(X - w, mt, w, yerr=[mt - lt, ht - mt], capsize=2.5, color=C_TOT, label="total")
ax.bar(X, mh, w, yerr=[mh - lh, hh - mh], capsize=2.5, color=C_HEAD, label="head")
ax.bar(X + w, ml, w, yerr=[ml - ll, hl - ml], capsize=2.5, color=C_LAT, label="latent")
ax.set_yscale("log")
ax.set_xticks(X); ax.set_xticklabels(PARAM_SHORT, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("sigma (median + IQR) [log10 decades]")
ax.set_title("EXP2 FigB — predictive std converted to log10 decades (median + IQR)",
             fontsize=11)
ax.legend(fontsize=8, frameon=False)
ax.grid(True, which="both", axis="y", linestyle=":", linewidth=0.4, alpha=0.4)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "EXP2_FigB.png"), dpi=300)
plt.close(fig)

# ============ FigC — calibration comparison ============
crows = csvrows("calibration_comparison.csv")
crows = [r for r in crows if r[0] != "parameter"]
levels = [0.50, 0.80, 0.90, 0.95]
def get_cal(key):
    m = {}
    for r in crows:
        p = r[0]; lvl = float(r[1])
        m[(p, lvl)] = float(r[2 if key == "cur" else 3 if key == "mom" else 4])
    return m
cur = get_cal("cur"); mom = get_cal("mom"); mix = get_cal("mix")

fig, axes = plt.subplots(3, 3, figsize=(12.5, 11))
for i, ax in enumerate(axes.ravel()):
    p = PARAM_SHORT[i]
    ax.plot([0.4, 1.0], [0.4, 1.0], "--", color="#999999", linewidth=1)
    ax.plot(levels, [cur[(p, l)] for l in levels], "o-", color=C_CUR, label="z_mean", linewidth=1.5, markersize=5)
    ax.plot(levels, [mom[(p, l)] for l in levels], "s-", color=C_TOT, label="moment-matched", linewidth=1.5, markersize=5)
    ax.plot(levels, [mix[(p, l)] for l in levels], "^-", color=C_MIX, label="MC mixture", linewidth=1.5, markersize=5)
    ax.set_title(p, fontsize=10)
    ax.set_xlim(0.4, 1.0); ax.set_ylim(0.4, 1.0)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.4)
    if i == 0:
        ax.legend(fontsize=7, loc="lower right", frameon=False)
    if i >= 6:
        ax.set_xlabel("nominal coverage")
    if i % 3 == 0:
        ax.set_ylabel("empirical coverage")
fig.suptitle("EXP2 FigC — calibration: current vs latent-propagated (moment-matched) vs MC mixture",
             fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(os.path.join(FIG, "EXP2_FigC.png"), dpi=300)
plt.close(fig)

# ============ FigD — error ranking ============
rrows = csvrows("error_ranking_comparison.csv")
rrows = [r for r in rrows if r[0] != "parameter"]
rho_cur = np.array([float(r[1]) for r in rrows])
rho_lat = np.array([float(r[3]) for r in rrows])
rho_tot = np.array([float(r[4]) for r in rrows])

fig, ax = plt.subplots(figsize=(10.5, 4.6))
w = 0.27
ax.axhline(0, color="#555555", linewidth=1.0)
ax.bar(X - w, rho_cur, w, color=C_CUR, label=r"$\rho_{\mathrm{current}}$ (z_mean)")
ax.bar(X, rho_lat, w, color=C_LAT, label=r"$\rho_{\mathrm{latent}}$")
ax.bar(X + w, rho_tot, w, color=C_TOT, label=r"$\rho_{\mathrm{total}}$")
ax.set_xticks(X); ax.set_xticklabels(PARAM_SHORT, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("Spearman(sigma, |error|)")
ax.set_title("EXP2 FigD — sigma–error ranking: current vs latent-propagated", fontsize=11)
ax.legend(fontsize=8, frameon=False)
ax.grid(True, axis="y", linestyle=":", linewidth=0.4, alpha=0.4)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "EXP2_FigD.png"), dpi=300)
plt.close(fig)

# ============ FigE — sigma widening ============
ratio = d["ratio_sigma"]
fig, ax = plt.subplots(figsize=(10.5, 4.6))
bp = ax.boxplot([ratio[:, j] for j in range(9)], positions=X, widths=0.55,
                showfliers=False, patch_artist=True, medianprops=dict(color="#111111"))
for patch, col in zip(bp["boxes"], [C_TOT] * 9):
    patch.set_facecolor(col); patch.set_alpha(0.55)
ax.axhline(1.0, color="#555555", linewidth=1.2, linestyle="--")
ax.set_xticks(X); ax.set_xticklabels(PARAM_SHORT, rotation=30, ha="right", fontsize=8)
ax.set_ylabel(r"$\sigma_{total}/\sigma_{current}$")
ax.set_ylim(0.998, 1.007)
for j in range(9):
    ax.text(j, np.median(ratio[:, j]) + 0.0002, "%.4f" % np.median(ratio[:, j]),
            ha="center", va="bottom", fontsize=6.5)
ax.set_title("EXP2 FigE — latent propagation widening of predictive sigma (boxes = IQR; no outliers drawn)",
             fontsize=10)
ax.grid(True, axis="y", linestyle=":", linewidth=0.4, alpha=0.4)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "EXP2_FigE.png"), dpi=300)
plt.close(fig)

# ============ FigF — encoder latent diagnostics ============
erows = csvrows("encoder_latent_diagnostics.csv")
erows = [r for r in erows if r[0] != "latent_dim"]
sd_z = np.array([float(r[2]) for r in erows])
m_post = np.array([float(r[3]) for r in erows])

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))
ax = axes[0]
ax.bar(X, sd_z, color=C_HEAD)
ax.set_xticks(X); ax.set_xticklabels(X, fontsize=8)
ax.set_xlabel("latent dimension"); ax.set_ylabel("SD(z_mean) across test set")
ax.set_title("(a) latent mean spread (informative encoding)", fontsize=10)
ax = axes[1]
ax.bar(X, m_post, color=C_LAT)
ax.set_yscale("log")
ax.set_xticks(X); ax.set_xticklabels(X, fontsize=8)
ax.set_xlabel("latent dimension"); ax.set_ylabel("mean posterior std exp(0.5 z_log_var)")
ax.set_title("(b) posterior latent std (near-point posterior)", fontsize=10)
fig.suptitle("EXP2 FigF — encoder latent diagnostics: informative means, negligible width", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(os.path.join(FIG, "EXP2_FigF.png"), dpi=300)
plt.close(fig)

# ============ FigG — latent-induced correlation heatmap ============
C = d["C_latent"]
v = np.sqrt(np.einsum("sii->si", C))
corr = np.zeros((15307, 9, 9))
for i in range(9):
    for k in range(9):
        den = v[:, i] * v[:, k]
        safe = den > 1e-16
        corr[safe, i, k] = C[safe, i, k] / den[safe]
        corr[~safe, i, k] = np.nan
med_corr = np.nanmedian(corr, axis=0)

fig, ax = plt.subplots(figsize=(8.2, 6.6))
im = ax.imshow(med_corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(X); ax.set_yticks(X)
ax.set_xticklabels(PARAM_SHORT, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(PARAM_SHORT, fontsize=8)
for i in range(9):
    for k in range(9):
        val = med_corr[i, k]
        ax.text(k, i, "%.2f" % val if not np.isnan(val) else "nan",
                ha="center", va="center", fontsize=6.5,
                color="#111111" if abs(val) < 0.6 else "white")
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label("median latent-induced correlation", fontsize=9)
ax.set_title("EXP2 FigG — latent-induced parameter correlation (median over test)\n"
             "descriptive of the latent function ONLY; latent share of predictive variance ≈ 0.1%",
             fontsize=9.5)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "EXP2_FigG.png"), dpi=300)
plt.close(fig)

print("figures written to", FIG)
import glob
for f in sorted(glob.glob(os.path.join(FIG, "EXP2_Fig*.png"))):
    print(" ", os.path.basename(f))
