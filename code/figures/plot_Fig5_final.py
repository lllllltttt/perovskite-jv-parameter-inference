"""
plot_Fig5_final.py — Fig. 5 of the FINAL figure package (2026-08-23 revision).
==============================================================================
Inverse ambiguity revealed by nearest-neighbor J-V collisions within the
predefined sampling prior. All data come from collision_analysis/ ONLY plus
the frozen prediction arrays; no new analysis, no recomputed statistics.

  (a) Normalized J-V RMSE (log10) vs parameter-space distance for all 7,666
      deduplicated NN pairs; compact two-line statistics in the top-left
      (Spearman rho_s = 0.158, Pearson r = 0.079; N = 7,666). No trend line.
  (b) Median parameter distance by tier: Random baseline / All NN pairs /
      Closest 1% / 0.5% / 0.1% (frozen values 0.349 / 0.200 / 0.144 / 0.134 /
      0.102 at a uniform bar-top offset).
  (c) Per-parameter median |Delta_theta| within the closest-1% pairs
      (normalized log10 space), math-symbol y labels only, descending order
      tau_ETL .. Nc; values are the frozen manuscript Table 5 numbers
      (rad_c = 0.089).
  (d) Two representative single-parameter collision mini-panels side by side:
      (d1) tau_ETL 0.377 -> 0.988 at dJ = 9.3e-5; (d2) r_rad 0.712 -> 0.094
      at dJ = 2.0e-4. Curve 1 solid / curve 2 dashed; NO legend -- inline
      curve labels (tiny real line samples + ink text) sit in the empty
      LOWER-LEFT quadrant of each mini, stacked above the compact annotation
      block (parameter + transition + dJ) so nothing collides; mechanism
      sub-titles ("tau_ETL collision" / "r_rad collision") sit above each
      mini, with the centered group heading "Representative collisions"
      above them, clear of panel (b)'s category labels. The extreme
      reverse-bias tail of (d1) leaves the frame: both minis share the
      y range (-6, 33) mA cm^-2 so the two curves' overlap in the photovoltaic
      operating region is readable (same presentation class as Fig. 2's
      y-limit choice).

This is the micro-fix revision on top of the frozen Fig. 5 (no science, no
values, no axes ranges, no curves, no colours changed): (i) the inter-row gap
is widened (hspace 0.22 -> 0.38) so panel (b)'s two-line x-category labels no
longer crowd the (d) heading band; the "Representative collisions" heading is
now centred over the whole bottom-right subpanel (was left-aligned near the
panel-(d) tag); (ii) the two minis get a slightly wider internal gap (0.145 vs
0.12) and the top-right "curve 1/2" legend notes are replaced by inline
lower-left labels (line sample + ink text above the annotation block).

Frozen sources:
  collision_analysis/nearest_neighbor_pairs.csv        (7,666 pairs)
  collision_analysis/parameter_ambiguity_summary.csv   (closest-tier medians)
  collision_analysis/top_collision_pairs.csv           (representative cases)
  scripts/_frozen_preds.npz                            (frozen curves, params)
  manuscript_stage1_routeA_final_precision.md Table 5  (closest-1% display)

Outputs (candidate — the authoritative final_figures/Fig5/Fig5_final.* files
are NOT overwritten):
  final_figures/Fig5/Fig5_final_microfix.png / .pdf / .svg
  final_figures/Fig5/Fig5_final_microfix_large.png / .pdf / .svg
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import spearmanr, pearsonr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(BASE, "final_figures", "Fig5")
os.makedirs(OUT_DIR, exist_ok=True)

NN_CSV = os.path.join(BASE, "collision_analysis", "nearest_neighbor_pairs.csv")
AMB_CSV = os.path.join(BASE, "collision_analysis", "parameter_ambiguity_summary.csv")
TOP_CSV = os.path.join(BASE, "collision_analysis", "top_collision_pairs.csv")
NPZ = os.path.join(HERE, "_frozen_preds.npz")

STEM_COLOR = "#c9ced4"        # light gray stems (c)
INK = st.INK

# (d) mini-panel fonts: axis labels / ticks slightly smaller than the main
# (a)(b)(c) panels (FS_AXIS 8.5 / FS_TICK 7.5) so the minis read as insets.
FS_MINI_AXIS = 7.5
FS_MINI_TICK = 7.0

# Frozen closest-1% median |diff| display values (manuscript Table 5),
# keyed by CSV parameter name. These are the numbers that MUST appear in (c);
# rad_c displays 0.089 (the frozen manuscript value), not 0.088 (the unrounded
# CSV median 0.088487) — the assertion below pins CSV within manuscript rounding.
MEDS_CLOSEST1 = {
    "tau_ETL": 0.154, "mu_n_pvk": 0.118, "tau_HTL": 0.101,
    "tau_n_pvk": 0.101, "rad_c": 0.089, "tau_p_pvk": 0.087,
    "mu_p_pvk": 0.073, "Nv_eff_pvk": 0.060, "Nc_eff_pvk": 0.052,
}

# Math-symbol labels for (c) and (d). Package-wide canonical labels except the
# radiative coefficient, which reads r_rad here (Fig. 4 made the same choice).
LABELS = {
    "mu_n_pvk": r"$\mu_n$", "mu_p_pvk": r"$\mu_p$",
    "tau_n_pvk": r"$\tau_n$", "tau_p_pvk": r"$\tau_p$",
    "Nc_eff_pvk": r"$N_c$", "Nv_eff_pvk": r"$N_v$",
    "tau_ETL": r"$\tau_{\mathrm{ETL}}$", "tau_HTL": r"$\tau_{\mathrm{HTL}}$",
    "rad_c": r"$r_{\mathrm{rad}}$",
}

# Frozen tier medians (collision_summary.txt; the three closest tiers are
# additionally cross-checked against parameter_ambiguity_summary.csv).
TIER_MED = [0.3490, 0.1999, 0.1443, 0.1337, 0.1021]
TIER_LABELS = ["Random\nbaseline", "All NN\npairs", "Closest\n1%",
               "Closest\n0.5%", "Closest\n0.1%"]
TIER_DISPLAY = ["0.349", "0.200", "0.144", "0.134", "0.102"]

# Fixed identity of the two representative single-parameter collision cases.
CASE_PARAMS = ["tau_ETL", "rad_c"]          # (d1), (d2)
CASE_EXPECT = {"tau_ETL": ((1010, 2641), 9.3e-5),
               "rad_c":   ((8271, 10258), 2.0e-4)}


def _sci(x):
    """Mantissa/exponent split for '%.1f x 10^exp' display."""
    e = int(np.floor(np.log10(x)))
    m = x / 10.0 ** e
    return m, e


def load():
    """Load and assert every frozen number this figure depends on."""
    nn = pd.read_csv(NN_CSV)
    amb = pd.read_csv(AMB_CSV)
    top = pd.read_csv(TOP_CSV)
    d = np.load(NPZ)
    J_raw = d["J_test_raw"]
    V = d["V_GRID"]
    ptest = d["params_test"]
    pnames = list(d["param_names"])
    idx = {n: k for k, n in enumerate(pnames)}

    dJ = nn["dJ_rmse"].values
    dTh = nn["dTheta"].values
    assert len(nn) == 7666, len(nn)

    rho_sp, _p_sp = spearmanr(dJ, dTh)
    r_p, _p_p = pearsonr(dJ, dTh)
    print("Spearman=%.4f (p=%.3e)  Pearson=%.4f (p=%.3e)"
          % (rho_sp, _p_sp, r_p, _p_p))
    assert abs(rho_sp - 0.158) < 1e-3 and abs(r_p - 0.079) < 1e-3

    # tier medians: cross-check the closest tiers against the CSV
    for tier, expect in [("closest 1%", 0.1443), ("closest 0.5%", 0.1337),
                         ("closest 0.1%", 0.1021)]:
        got = float(amb[(amb["tier"] == tier) & (amb["parameter"] == "dTheta")
                        ]["median_abs_diff"].iloc[0])
        assert abs(got - expect) < 1e-3, (tier, got, expect)

    # closest-1% per-parameter medians: descending order + display values
    c1 = amb[(amb["tier"] == "closest 1%") & (amb["parameter"] != "dTheta")].copy()
    c1 = c1.sort_values("median_abs_diff", ascending=False)
    params = c1["parameter"].tolist()
    assert params == ["tau_ETL", "mu_n_pvk", "tau_HTL", "tau_n_pvk", "rad_c",
                      "tau_p_pvk", "mu_p_pvk", "Nv_eff_pvk", "Nc_eff_pvk"], params
    for _, row in c1.iterrows():
        p = row["parameter"]
        assert float(row["n_pairs"]) == 77, p
        assert abs(float(row["median_abs_diff"]) - MEDS_CLOSEST1[p]) < 1e-3, \
            (p, float(row["median_abs_diff"]))

    # representative cases from top_collision_pairs.csv
    rep = top[top["case_label"] == "REPRESENTATIVE"].reset_index(drop=True)
    cases = {}
    for p in CASE_PARAMS:
        row = rep.loc[rep["absd_" + p].idxmax()]
        cases[p] = row
    for p in CASE_PARAMS:
        i, j = int(cases[p]["i"]), int(cases[p]["j"])
        dJv = float(cases[p]["dJ_rmse"])
        (ie, je), dJe = CASE_EXPECT[p]
        assert i == ie and j == je, (p, i, j)
        assert abs(dJv - dJe) < 5e-6, (p, dJv)

    # transition values from the frozen parameter array (normalized)
    trans = {}
    for p in CASE_PARAMS:
        k = idx[p]
        i, j = int(cases[p]["i"]), int(cases[p]["j"])
        trans[p] = (float(ptest[i, k]), float(ptest[j, k]))
    assert abs(trans["tau_ETL"][0] - 0.377) < 5e-4 and \
           abs(trans["tau_ETL"][1] - 0.988) < 5e-4
    assert abs(trans["rad_c"][0] - 0.712) < 5e-4 and \
           abs(trans["rad_c"][1] - 0.094) < 5e-4

    return dict(nn=nn, dJ=dJ, dTh=dTh, rho=rho_sp, r=r_p,
                params=params, c1=c1, cases=cases, trans=trans,
                J_raw=J_raw, V=V, ptest=ptest, pnames=pnames, idx=idx)


def build_figure(size="journal"):
    """Build Fig. 5 and return (fig, info) for programmatic QC."""
    D = load()
    w = st.set_fig_width(size)
    H = w * 0.60
    fig = plt.figure(figsize=(w, H))
    gs = fig.add_gridspec(2, 2,
                          width_ratios=[1.15, 1.0], height_ratios=[1.0, 1.05],
                          left=0.13, right=0.985, top=0.875, bottom=0.135,
                          wspace=0.17, hspace=0.38)  # 0.22 -> 0.38: clears the
    # two-line (b) category labels from the panel-(d) heading band below them.

    axa = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, 0])
    axd = fig.add_subplot(gs[1, 1])

    # ---------------- (a) dJ vs dTheta scatter ----------------
    x = np.log10(D["dJ"])
    y = D["dTh"]
    sc = axa.scatter(x, y, s=2.0, alpha=0.30, color=st.OKABE_ITO[0],
                     linewidths=0, rasterized=True, zorder=2)
    axa.set_xlabel(r"$\log_{10}$ normalized J–V RMSE, $d_J$",
                   fontsize=st.FS_AXIS)
    axa.set_ylabel(r"Parameter distance, $d_\Theta$", fontsize=st.FS_AXIS)
    axa.set_xlim(-4.5, -0.85)
    axa.set_ylim(0.0, 0.63)
    axa.set_xticks([-4, -3, -2, -1])
    axa.set_yticks([0.0, 0.2, 0.4, 0.6])
    st.configure_axes(axa)
    stats_txt = axa.text(0.02, 0.985,
                         r"$\rho_s=0.158$,  $r=0.079$" + "\n" + r"$N=7{,}666$",
                         transform=axa.transAxes, fontsize=st.FS_ANNOT,
                         va="top", ha="left", color=INK, zorder=10)
    st.panel_label(axa, "(a)")

    # ---------------- (b) closest-tier ambiguity bars ----------------
    xpos = np.arange(len(TIER_MED))
    colors = ["#AAAAAA", st.OKABE_ITO[3], st.OKABE_ITO[0],
              st.OKABE_ITO[0], st.OKABE_ITO[0]]
    bars = axb.bar(xpos, TIER_MED, width=0.62, color=colors,
                   edgecolor="white", linewidth=0.5, zorder=3)
    bar_txts = []
    for i, v in enumerate(TIER_MED):
        t = axb.text(i, v + 0.007, TIER_DISPLAY[i], ha="center", va="bottom",
                     fontsize=st.FS_ANNOT, color=INK, zorder=4)
        bar_txts.append(t)
    axb.set_xticks(xpos)
    axb.set_xticklabels(TIER_LABELS, fontsize=st.FS_TICK)
    axb.set_ylabel(r"Median parameter distance, $d_\Theta$",
                   fontsize=st.FS_AXIS)
    axb.set_ylim(0.0, 0.40)
    st.configure_axes(axb)
    st.panel_label(axb, "(b)")

    # ---------------- (c) per-parameter closest-1% median ----------------
    params = D["params"]
    ypos = np.arange(len(params))[::-1]
    dots, stems, val_txts = [], [], []
    for yp, p in zip(ypos, params):
        xv = MEDS_CLOSEST1[p]
        h = axc.hlines(yp, 0.0, xv, color=STEM_COLOR, lw=1.4, zorder=1)
        dot = axc.plot([xv], [yp], "o", ms=5.0, color=st.OKABE_ITO[0],
                       zorder=2)[0]
        t = axc.text(xv + 0.005, yp, "%.3f" % xv, ha="left", va="center",
                     fontsize=st.FS_ANNOT, color=INK, zorder=3)
        stems.append(h)
        dots.append(dot)
        val_txts.append(t)
    axc.set_yticks(ypos)
    axc.set_yticklabels([LABELS[p] for p in params], fontsize=st.FS_TICK)
    axc.set_xlabel(r"Median $|\Delta\theta|$, closest 1% pairs" "\n"
                   r"(normalized $\log_{10}$ space)", fontsize=st.FS_AXIS)
    axc.set_xlim(0.0, 0.19)
    axc.set_ylim(-0.6, len(params) - 0.4)
    st.configure_axes(axc)
    st.panel_label(axc, "(c)")

    # ---------------- (d) two representative collision mini-panels ----------------
    axd.axis("off")
    insets, d_info = [], []
    for k, p in enumerate(CASE_PARAMS):
        c = D["cases"][p]
        i, j = int(c["i"]), int(c["j"])
        # two minis filling the (d) region with a slightly wider internal gap
        # (0.145 vs 0.12) so the two frames never read as one crowded block;
        # the right mini drops its y label so the gap opens further
        x0 = 0.01 + k * (0.42 + 0.145)           # 0.010 and 0.575
        ins = axd.inset_axes([x0, 0.16, 0.42, 0.74])
        l1 = ins.plot(D["V"], D["J_raw"][i], color=st.OKABE_ITO[0], lw=1.5,
                      label="curve 1", zorder=2)[0]
        l2 = ins.plot(D["V"], D["J_raw"][j], color=st.OKABE_ITO[3], ls="--",
                      lw=1.4, label="curve 2", zorder=2)[0]
        # unified x range 0-1.3 V; shared y range (-6, 33) prioritising the two
        # curves' overlap in the photovoltaic operating region (the extreme
        # reverse-bias tail of (d1) leaves the frame -- Fig. 2-style decision)
        ins.set_xlim(0.0, 1.3)
        ins.set_xticks([0.0, 0.5, 1.0, 1.3])
        ins.set_ylim(-6.0, 33.0)
        ins.set_yticks([0.0, 10.0, 20.0, 30.0])
        ins.set_xlabel("Voltage (V)", fontsize=FS_MINI_AXIS)
        if k == 0:
            ins.set_ylabel(r"$J$ (mA cm$^{-2}$)", fontsize=FS_MINI_AXIS)
        st.configure_axes(ins)
        ins.tick_params(axis="both", labelsize=FS_MINI_TICK)
        # mechanism subtitle ABOVE the mini (outside the coordinate area)
        axd.text(x0 + 0.21, 0.925, LABELS[p] + " collision",
                 transform=axd.transAxes, fontsize=st.FS_TITLE,
                 ha="center", va="bottom", color=INK)
        # compact annotation block, lower-left inside the mini (parameter,
        # transition and dJ; interpretation is reserved for the caption)
        t0, t1 = D["trans"][p]
        dJv = float(c["dJ_rmse"])
        m, e = _sci(dJv)
        sym = LABELS[p][1:-1]                    # strip the wrapping "$...$"
        ann = ins.text(0.035, 0.055,
                       r"$" + sym + r"$: $%.3f \rightarrow %.3f$" % (t0, t1)
                       + "\n" + r"$d_J = %.1f\times10^{%d}$" % (m, e),
                       transform=ins.transAxes, fontsize=st.FS_ANNOT,
                       ha="left", va="bottom", color=INK, zorder=5,
                       bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                 ec="none", alpha=0.55))
        # inline curve labels in the empty LOWER-LEFT quadrant, stacked above
        # the annotation block (both curves ride the ~24 mA/cm2 plateau at the
        # top of the mini, so the lower-left is free of curve data): tiny real
        # line samples immediately left of the ink labels; blue solid = curve 1,
        # orange dashed = curve 2. Replaces the old top-right legend notes.
        y1n, y2n = 0.60, 0.48
        sam1 = Line2D([0.055, 0.125], [y1n, y1n], transform=ins.transAxes,
                      color=st.OKABE_ITO[0], lw=1.5, clip_on=False, zorder=6)
        sam2 = Line2D([0.055, 0.125], [y2n, y2n], transform=ins.transAxes,
                      color=st.OKABE_ITO[3], lw=1.3, ls="--",
                      clip_on=False, zorder=6)
        ins.add_line(sam1)
        ins.add_line(sam2)
        n1 = ins.text(0.135, y1n, "curve 1", transform=ins.transAxes, ha="left",
                      va="center", fontsize=6.5, color=INK, zorder=7)
        n2 = ins.text(0.135, y2n, "curve 2", transform=ins.transAxes, ha="left",
                      va="center", fontsize=6.5, color=INK, zorder=7)
        insets.append(ins)
        d_info.append(dict(param=p, i=i, j=j, ins=ins, l1=l1, l2=l2,
                           ann=ann, sam1=sam1, sam2=sam2,
                           note1=n1, note2=n2, leg=None))
    # (d) panel label (outside, upper-left) + centered gray group heading,
    # sitting cleanly above the two minis and clear of panel (b)'s two-line
    # category labels (hspace was widened so the band between the rows has
    # room for both); centered over the whole bottom-right subpanel.
    st.panel_label(axd, "(d)")
    axd.text(0.5, 1.06, "Representative collisions", transform=axd.transAxes,
             fontsize=8.0, ha="center", va="bottom", color=st.MUTED)

    info = dict(axa=axa, axb=axb, axc=axc, axd=axd,
                scatter=sc, stats_txt=stats_txt,
                bars=bars, bar_txts=bar_txts,
                dots=dots, val_txts=val_txts,
                insets=insets, d_info=d_info)
    return fig, info


def main():
    for size in ("journal", "large"):
        fig, info = build_figure(size)
        stem = os.path.join(OUT_DIR, "Fig5_final_microfix2"
                            + ("_large" if size == "large" else ""))
        written = st.save_fig(fig, stem, svg=True)
        print("wrote:", ", ".join(written))


if __name__ == "__main__":
    main()
