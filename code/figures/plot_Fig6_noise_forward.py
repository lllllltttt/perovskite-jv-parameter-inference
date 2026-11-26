"""
plot_Fig6_noise_forward.py — Fig. 6 of the FINAL figure package.
=================================================================
Noise robustness + unbiased forward validation (frozen evidence):

  (a) Point-prediction Pearson r vs input noise level (0/0.2/0.5/1/2% of
      |Jsc|), mean over 30 MC realizations. Group means (bulk / interface /
      radiative) plus the 9-parameter mean (black, hollow diamonds).
  (b) 95% empirical coverage vs the same noise levels (nominal 0.95 dashed
      reference); inset: mean predictive scale sigma is FLAT across noise
      levels (the uncertainty does not adapt to measurement noise) — the
      interpretation is reserved for the caption.
  (c) Unbiased 45-sample COMSOL forward validation: RMSE between the
      predicted-parameter re-simulation and the target curve — full curve,
      0-1.0 V operating region, >1.0 V high forward bias (all 45 samples).
      Logarithmic y-axis so the 0-1.0 V distribution is readable (all values
      strictly > 0; asserted). Individual per-sample points overlaid.
  (d) Device-metric preservation: |dJsc|, |dVoc|, |dFF|, |dPCE| as four
      2x2 distribution mini-panels, each on its own independent native-unit
      scale (all available frozen per-sample values as a jittered strip
      overlaid on a compact boxplot, plus a frozen-median annotation). No
      common cross-metric axis; no per-mini N label (stated once in the
      caption).

Frozen sources: noise_robustness/*.csv, forward_validation_unbiased/*.csv.
No new analysis; every plotted number asserted against the frozen sources.

Outputs:
  final_figures/Fig6/Fig6_noise_forward.png / .pdf
  final_figures/Fig6/Fig6_noise_forward_large.png / .pdf
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(BASE, "final_figures", "Fig6")
os.makedirs(OUT_DIR, exist_ok=True)

NM_CSV = os.path.join(BASE, "noise_robustness", "noise_metrics_all.csv")
NC_CSV = os.path.join(BASE, "noise_robustness", "noise_calibration_summary.csv")
NU_CSV = os.path.join(BASE, "noise_robustness", "noise_uncertainty_summary.csv")
FW_SUM = os.path.join(BASE, "forward_validation_unbiased", "forward_metrics_summary.csv")
FW_PER = os.path.join(BASE, "forward_validation_unbiased", "forward_metrics_per_sample.csv")

# frozen expected values
R_AT_0PCT = [0.9063, 0.9194, 0.8783, 0.8808, 0.9090, 0.8956, 0.5936, 0.7199, 0.5592]
R_AT_1PCT = [0.8407, 0.8548, 0.8520, 0.8546, 0.8220, 0.8200, 0.5152, 0.6626, 0.5137]
COV_95_0PCT = [0.9475, 0.9522, 0.9583, 0.9597, 0.9464, 0.9499, 0.9692, 0.9667, 0.9664]
COV_95_1PCT = [0.8746, 0.8705, 0.9091, 0.9201, 0.8364, 0.8695, 0.9336, 0.9272, 0.9323]
MU_N_SIGMA_0PCT = 0.0927499532699585   # frozen sigma_mean of mu_n at 0% noise

# frozen device-metric medians / quartiles (forward_metrics_summary.csv
# "device_mae": median / q25 / q75)
DMED_FROZEN = {"dJsc": 0.1119, "dVoc": 0.03, "dFF": 0.0141, "dPCE": 0.4714}
DQ1_FROZEN = {"dJsc": 0.0224, "dVoc": 0.01, "dFF": 0.0089, "dPCE": 0.1887}
DQ3_FROZEN = {"dJsc": 0.2518, "dVoc": 0.04, "dFF": 0.0227, "dPCE": 0.928}

GROUP_MARK = {"bulk": ("o", "#0072B2"), "interface": ("s", "#E69F00"),
              "radiative": ("^", "#009E73")}
GROUP_OF = {"mu_n_pvk": "bulk", "mu_p_pvk": "bulk", "tau_n_pvk": "bulk",
            "tau_p_pvk": "bulk", "Nc_eff_pvk": "bulk", "Nv_eff_pvk": "bulk",
            "tau_ETL": "interface", "tau_HTL": "interface", "rad_c": "radiative"}

# (d) mini-panel: metric column -> (math y-label, display median, unit suffix)
DMETRICS = [
    ("dJsc", r"$|\Delta J_{sc}|$", "0.112", r"mA cm$^{-2}$"),
    ("dVoc", r"$|\Delta V_{oc}|$", "0.030", "V"),
    ("dFF",  r"$|\Delta FF|$",     "0.014", ""),
    ("dPCE", r"$|\Delta PCE|$",    "0.471", "pp"),
]


def load():
    """Read frozen sources once and assert every value used by the figure."""
    nm = pd.read_csv(NM_CSV)
    nc = pd.read_csv(NC_CSV)
    nu = pd.read_csv(NU_CSV)
    fw = pd.read_csv(FW_PER)

    order = {p: i for i, p in enumerate(st.PARAM_NAMES)}
    pnames = sorted(nm["parameter"].unique(), key=lambda p: order[p])
    levels = ["0%", "0.2%", "0.5%", "1.0%", "2.0%"]
    xl = np.arange(len(levels))

    # r matrix [param, level]
    rmat = np.zeros((9, 5))
    for i, p in enumerate(pnames):
        for j, lvl in enumerate(levels):
            rmat[i, j] = nm[(nm.parameter == p) & (nm.noise == lvl)]["r_mean"].iloc[0]
    for i, p in enumerate(pnames):
        assert abs(rmat[i, 0] - R_AT_0PCT[i]) < 1e-3, (p, rmat[i, 0])
        assert abs(rmat[i, 3] - R_AT_1PCT[i]) < 1e-3, (p, rmat[i, 3])
    rmean = rmat.mean(axis=0)
    # QC requirement: mean r at clean ~0.807, unchanged
    assert abs(rmean[0] - 0.807) < 1e-3, rmean[0]

    # 95% coverage matrix [param, level] -- all 5 levels are frozen in the CSV
    cov95 = np.zeros((9, 5))
    for i, p in enumerate(pnames):
        for j, lvl in enumerate(levels):
            row = nc[(nc.parameter == p) & (nc.noise == lvl) & (nc.nominal == 0.95)]
            cov95[i, j] = row["coverage_mean"].iloc[0]
    for i, p in enumerate(pnames):
        assert abs(cov95[i, 0] - COV_95_0PCT[i]) < 1e-3, (p, cov95[i, 0])
        assert abs(cov95[i, 3] - COV_95_1PCT[i]) < 1e-3, (p, cov95[i, 3])
    # noisy coverage at 2% stays within the frozen range (no value change)
    assert cov95[:, 4].min() >= 0.723 - 1e-3 and cov95[:, 4].max() <= 0.887 + 1e-3

    # sigma flatness: mean over the 9 params of sigma_mean per level. The
    # predictive scale must NOT adapt to the input noise level (frozen
    # finding). Assert mu_n at 0% matches the frozen number and the spread
    # across levels is tiny.
    sig_mean = np.zeros(5)
    for j, lvl in enumerate(levels):
        sig_mean[j] = nu[nu.noise == lvl]["sigma_mean"].mean()
    mu_n_0 = float(nu[(nu.parameter == "mu_n_pvk") & (nu.noise == "0%")]["sigma_mean"].iloc[0])
    assert abs(mu_n_0 - MU_N_SIGMA_0PCT) < 1e-6
    assert sig_mean.max() - sig_mean.min() < 0.005, "sigma not flat across noise!"

    # forward RMSE columns
    fw_rmse_full = fw["rmse_full"].values
    fw_rmse_01 = fw["rmse_0to1V"].values
    fw_rmse_gt = fw["rmse_gt1V"].values
    assert len(fw) == 45
    assert abs(np.median(fw_rmse_full) - 2.693) < 1e-2
    assert abs(np.median(fw_rmse_01) - 0.455) < 1e-2
    assert abs(np.median(fw_rmse_gt) - 5.19) < 1e-2
    # log-scale safety: every RMSE value strictly > 0 (no epsilon added)
    for c, name in [(fw_rmse_full, "full"), (fw_rmse_01, "0-1V"), (fw_rmse_gt, ">1V")]:
        assert c.min() > 0, "%s RMSE has non-positive values; log scale unsafe" % name

    # device metrics: frozen median + IQR (q25/q75) from the per-sample table,
    # asserted against the frozen summary numbers. The per-sample table has 45
    # rows; sample 31 (test_index 12051) has no simulated Voc/FF/PCE, so
    # |dVoc|, |dFF|, |dPCE| carry 44 values (frozen NaN gap -- keep as-is, do
    # not impute or drop the sample's valid columns).
    dmeta, darr = {}, {}
    for col in ("dJsc", "dVoc", "dFF", "dPCE"):
        a = fw[col].abs().dropna()
        med = float(a.median())
        q1 = float(a.quantile(0.25))
        q3 = float(a.quantile(0.75))
        assert abs(med - DMED_FROZEN[col]) < 1e-3, (col, med)
        assert abs(q1 - DQ1_FROZEN[col]) < 2e-3, (col, q1)
        assert abs(q3 - DQ3_FROZEN[col]) < 2e-3, (col, q3)
        assert len(a) == (45 if col == "dJsc" else 44), (col, len(a))
        dmeta[col] = dict(med=med, q1=q1, q3=q3)
        darr[col] = a.values

    return dict(pnames=pnames, xl=xl, rmat=rmat, rmean=rmean, cov95=cov95,
                sig_mean=sig_mean,
                fw_rmse=(fw_rmse_full, fw_rmse_01, fw_rmse_gt),
                dmeta=dmeta, darr=darr)


# (d) mini-panel fonts: axis labels / ticks slightly smaller than the main
# (a)(b)(c) panels so the 2x2 minis read as insets at journal width.
FS_MINI_AXIS = 6.8
FS_MINI_TICK = 6.5
FS_MINI_TITLE = 7.5    # metric symbol above each mini (>= MIN_FS 6.5)

XT_LABELS = ["0", "0.2", "0.5", "1", "2"]
X_AXIS_LABEL = r"Synthetic current noise (% of $|J_\mathrm{sc}|$)"


def build_figure(size):
    D = load()
    xl = D["xl"]
    rmat, rmean, cov95 = D["rmat"], D["rmean"], D["cov95"]
    pnames = D["pnames"]
    fw_rmse_full, fw_rmse_01, fw_rmse_gt = D["fw_rmse"]

    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 0.62))
    # Compact vertical spacing: hspace reduced from 0.72 so the inter-row
    # white band shrinks (rows get taller, not the figure); top nudged up to
    # reclaim the band above panel (a). The remaining gap still keeps the
    # top row's x labels clear of the bottom-row (c)(d) panel labels.
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1],
                          left=0.09, right=0.99, top=0.90, bottom=0.12,
                          wspace=0.42, hspace=0.50)

    # ---------------- (a) r vs noise ----------------
    axa = fig.add_subplot(gs[0, 0])
    for i, p in enumerate(pnames):
        g = GROUP_OF[p]
        mk, col = GROUP_MARK[g]
        if g == "bulk":
            axa.plot(xl, rmat[i], marker=mk, ms=4, color=col, lw=1.0,
                     alpha=0.75, mfc="white")
        else:
            axa.plot(xl, rmat[i], marker=mk, ms=5, color=col, lw=1.4,
                     mfc="white")
    # mean over the 9 parameters: black, thicker, hollow diamond
    mean_line, = axa.plot(xl, rmean, color="#000000", lw=1.9, marker="D",
                          ms=6, mfc="white", zorder=3)
    axa.set_xticks(xl)
    axa.set_xticklabels(XT_LABELS)
    axa.set_xlabel(X_AXIS_LABEL)
    axa.set_ylabel("Pearson $r$")
    axa.set_ylim(0.35, 1.0)
    st.configure_axes(axa)
    # compact single-row legend ABOVE the panel (outside the data area)
    handles = [Patch(fc="#0072B2", label="bulk (6)"),
               Patch(fc="#E69F00", label="interface (2)"),
               Patch(fc="#009E73", label="radiative (1)"),
               Line2D([0], [0], color="#000000", marker="D", ms=6,
                      mfc="white", lw=1.6, label="mean (9 params)")]
    # compact 2x2 legend ABOVE the panel (outside the data area). A single
    # 4-entry row is wider than the journal-width panel, so 2x2 keeps it
    # within the panel and clear of the (a) label. Anchor moved down (1.40 ->
    # 1.31) so the legend sits just above the axes instead of near the figure
    # top, cutting the top whitespace (the 2x2 legend is ~0.4 in tall, so
    # 1.31 keeps its bottom a small margin above the axes at journal width).
    leg_a = axa.legend(handles=handles, ncol=2, loc="upper center",
                       bbox_to_anchor=(0.5, 1.31), frameon=False,
                       fontsize=st.FS_LEGEND, columnspacing=1.2,
                       handlelength=1.4, handletextpad=0.5)
    st.panel_label(axa, "(a)")

    # ---------------- (b) coverage vs noise + sigma inset ----------------
    axb = fig.add_subplot(gs[0, 1])
    for i, p in enumerate(pnames):
        axb.plot(xl, cov95[i], color=st.OKABE_ITO[i % 9],
                 lw=1.1, alpha=0.8, marker="o", ms=3, mfc="white")
    axb.axhline(0.95, ls="--", color="#555555", lw=0.9)
    axb.set_xticks(xl)
    axb.set_xticklabels(XT_LABELS)
    axb.set_xlabel(X_AXIS_LABEL)
    axb.set_ylabel("95% empirical coverage")
    axb.set_ylim(0.6, 1.0)
    st.configure_axes(axb)
    # inset: flat sigma (mean over 9 params; tight y-range makes the
    # flatness visible; range across levels = 0.0014). Slightly smaller and
    # further toward the bottom-right corner than the previous inset, clear
    # of the coverage curves. Only a sparse subset of the x tick labels is
    # kept (0, 1, 2) so the inset ticks do not compete with the main x-axis;
    # the trend is unchanged (all 5 levels still plotted).
    axins = axb.inset_axes([0.62, 0.045, 0.30, 0.24])
    axins.plot(xl, D["sig_mean"], marker="o", ms=3, color="#D55E00", lw=1.0)
    axins.set_xticks([0, 3, 4])
    axins.set_xticklabels(["0", "1", "2"])
    axins.set_ylabel(r"Mean $\sigma_\theta$", fontsize=st.FS_TITLE)
    axins.set_ylim(0.128, 0.138)
    axins.yaxis.set_major_locator(MaxNLocator(nbins=3))
    st.configure_axes(axins)
    axins.tick_params(axis="both", labelsize=6.5)
    st.panel_label(axb, "(b)")

    # ---------------- (c) forward RMSE, log scale ----------------
    axc = fig.add_subplot(gs[1, 0])
    data = [fw_rmse_full, fw_rmse_01, fw_rmse_gt]
    labels = ["Full curve", "0–1.0 V", ">1.0 V"]
    meds = [np.median(x) for x in data]
    med_fmt = ["%.2f", "%.3f", "%.2f"]
    bp = axc.boxplot(data, positions=[0, 1, 2], widths=0.5, patch_artist=True,
                     showfliers=False,
                     medianprops=dict(color="black", lw=1.2))
    for patch, col in zip(bp["boxes"], [st.OKABE_ITO[0], st.OKABE_ITO[2],
                                        st.OKABE_ITO[3]]):
        patch.set_facecolor(col); patch.set_alpha(0.55)
    # all 45 individual per-sample points per category (deterministic jitter)
    rng = np.random.default_rng(2026)
    for pos, x in zip([0, 1, 2], data):
        jit = rng.uniform(-0.16, 0.16, len(x))
        axc.plot(pos + jit, x, marker="o", ms=2.2, ls="none", color="#333333",
                 alpha=0.38, zorder=1)
    # frozen median annotations placed BESIDE each box at the median height
    # (the 0-1.0 V box is too short to hold a label above its median inside
    # the box, so the values sit to the right of each box -- clear of the
    # box median line and of the overlaid points, which end at x = i + 0.16)
    for i, (m, fmt) in enumerate(zip(meds, med_fmt)):
        axc.text(i + 0.45, m, fmt % m, ha="left", va="center",
                 fontsize=st.FS_ANNOT, color=st.INK, zorder=6)
    axc.set_yscale("log")
    axc.set_ylim(0.01, 150)
    axc.set_xlim(-0.6, 3.05)
    axc.set_xticks([0, 1, 2])
    axc.set_xticklabels(labels, fontsize=st.FS_TICK)
    # log scale expressed by the ticks; the caption states the axis is
    # logarithmic (no "log scale" text in the axis label)
    axc.set_ylabel(r"J–V RMSE (mA cm$^{-2}$)")
    st.configure_axes(axc)
    st.panel_label(axc, "(c)")

    # ---------------- (d) device metrics: 2x2 distribution mini-panels -----
    # Full redo of the visual expression (data unchanged): each mini-panel
    # shows ALL available frozen per-sample values as a jittered strip
    # overlaid on a compact boxplot (same visual language as (c)), on its own
    # independent native-unit scale. The metric symbol titles each mini; the
    # y-axis carries the unit; the frozen median + unit is annotated top-right.
    # No per-mini "N = 45" label (the cohort size is stated once in the
    # caption); no (d1)-(d4) labels -- only the panel label (d).
    axd = fig.add_subplot(gs[1, 1])
    axd.axis("off")
    mini_pos = [[0.05, 0.56, 0.44, 0.38], [0.55, 0.56, 0.44, 0.38],
                [0.05, 0.05, 0.44, 0.38], [0.55, 0.05, 0.44, 0.38]]
    title_xy = [(0.27, 0.97), (0.77, 0.97), (0.27, 0.46), (0.77, 0.46)]
    rng_d = np.random.default_rng(2026)   # same deterministic jitter seed as (c)
    minis, d_boxes, d_strips = [], [], []
    for (col, sym, valtxt, unit), pos, (tx, ty) in zip(DMETRICS, mini_pos,
                                                       title_xy):
        axd.text(tx, ty, sym, transform=axd.transAxes, ha="center",
                 va="bottom", fontsize=FS_MINI_TITLE, color=st.INK)
        ax = axd.inset_axes(pos)
        a = D["darr"][col]
        dm = D["dmeta"][col]
        med, q1, q3 = dm["med"], dm["q1"], dm["q3"]
        bp = ax.boxplot([a], positions=[0], widths=0.5, patch_artist=True,
                        showfliers=False,
                        medianprops=dict(color="black", lw=1.1))
        for patch in bp["boxes"]:
            patch.set_facecolor(st.OKABE_ITO[0]); patch.set_alpha(0.55)
        jit = rng_d.uniform(-0.16, 0.16, len(a))
        strip = ax.plot(jit, a, marker="o", ms=2.2, ls="none", color="#333333",
                        alpha=0.38, zorder=1)[0]
        ax.set_xlim(-0.5, 0.5)
        ax.set_xticks([])
        ax.set_ylim(0, float(a.max()) * 1.08)
        if unit:
            ax.set_ylabel(unit, fontsize=FS_MINI_AXIS)
        ax.text(0.97, 0.95, (valtxt + ((" " + unit) if unit else "")),
                transform=ax.transAxes, ha="right", va="top",
                fontsize=st.FS_ANNOT, color=st.INK)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        st.configure_axes(ax)
        ax.tick_params(axis="y", labelsize=FS_MINI_TICK)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        minis.append(ax); d_boxes.append(bp); d_strips.append(strip)
    st.panel_label(axd, "(d)")

    info = dict(axa=axa, axb=axb, axc=axc, axd=axd,
                mean_line=mean_line, leg_a=leg_a, axins=axins,
                minis=minis, d_boxes=d_boxes, d_strips=d_strips, xl=xl)
    return fig, info


def main():
    for size in ("journal", "large"):
        fig, _ = build_figure(size)
        stem = os.path.join(OUT_DIR,
                            "Fig6_noise_forward" + ("_large" if size == "large" else ""))
        st.save_fig(fig, stem)
        print("wrote:", stem)


if __name__ == "__main__":
    main()
