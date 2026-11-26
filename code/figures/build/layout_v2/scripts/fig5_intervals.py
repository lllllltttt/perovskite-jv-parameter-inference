"""
fig5_intervals.py — reassembled main Figure 5 (v3).
===================================================
"Predictive intervals and the effect of current noise"

v3 RESTRUCTURE (supervisor layout)
----------------------------------
The submitted figure carried six panels and put the Spearman association
between the predictive scale sigma_theta and the absolute error |error| in the
main text. The plan moves that panel to the supplementary information: it is a
diagnostic of the uncertainty machinery, not of the predictive performance the
figure is about. The main figure is therefore five panels:

  (a) clean-input marginal coverage: empirical vs nominal coverage of the nine
      parameters at the 50 / 80 / 90 / 95 % levels
      -> old Figure 4 panel (a) (plot_Fig4_final.py)
  (b) model-versus-training-baseline interval score at the nominal 95 % level,
      drawn as a nine-row connected dot plot (grey open marker = training-set
      empirical-quantile baseline, filled marker = model, thin connector, and
      an extra ring where the model is worse than the baseline); "lower is
      better". This replaces the redundant standalone 95 % coverage bar chart
      of old Figure 4 panel (b): panel (a) already carries the clean 95 %
      coverage, so the second panel is spent on a comparison instead.
      -> old Figure 4 panel (c) / Table S17b
  (c) predictive Pearson correlation vs added current noise
      -> old Figure 6 panel (a)
  (d) 95 % empirical coverage vs added current noise
      -> old Figure 6 panel (a)/(b)
  (e) predictive sigma change vs added current noise
      -> old Figure 6 panel (b) inset, expanded

  MOVED TO SI: Spearman rho between sigma_theta and |error|
      -> old Figure 4 panel (c) of the submitted package.
  The numbers are still computed and exported here (panel tag "SI" in the
  plotting table) so that the supplementary figure has one verified source,
  but they are not drawn in the main figure.

Layout: (a) | (b) | legend cell   over   (c) | (d) | (e).
The free top-right cell carries the shared nine-parameter legend for the
three noise sweeps, so no area is wasted and no figure-level legend is needed.

Baseline and provenance discipline (checked in code, not assumed)
  * The interval-score comparison uses the FROZEN main model (VAE-v6) on the
    frozen 15,307-sample test set. Model intervals are recomputed here from
    the frozen arrays (param_mu, param_sigma, params_test, params_test_raw)
    and mapped to physical log10 units with the frozen per-parameter envelope
    width R; the recomputed scores are asserted against the frozen table to
    1e-4 before anything is drawn.
  * Clipping rule: the reported model interval score uses the RAW Gaussian
    interval (mu +/- z*sigma, no clipping). This is the convention of the
    frozen table (S15_S17 ... is_0.95 == raw). The clipped variant is
    reported in the frozen tables as having identical coverage
    (cov_raw == cov_clip) and is not plotted.
  * `S15_S17_preprocessing_control_metrics.csv` carries FOUR runs:
    Historical (= M-main, the frozen VAE-v6 chain) plus L / T / Prior. Only
    the `Historical` rows are used. The L and T rows are the independently
    retrained preprocessing-control runs and MUST NOT be substituted here.
  * The empirical-quantile baseline interval is a function of the training
    partition only (sample-independent); its coverage is measured, not
    tuned, on the same test set.

Interval score (Gneiting-Raftery):
    IS = (u - l) + 2/(1-c) * (l - y)+ + 2/(1-c) * (y - u)+
Lower is better. Reported in log10 units of the physical parameter, i.e. the
normalized-space score multiplied by the frozen envelope width R. The word
"decade" is not used anywhere in this package: a decade is a factor of ten in
the linear parameter, whereas these are increments of log10 of the parameter,
and the two are not interchangeable.

Noise panel (e) note: `sigma_mean` is the mean predicted standard deviation in
NORMALIZED space. The per-parameter scaler is affine (x_log10 = a*x_norm + b),
so the standard deviation maps as s_log10 = a*s_norm and the PERCENTAGE change
reported in (e) is numerically identical in normalized and in physical log10
units. It is not the percentage change of sigma in the linear parameter.

Frozen sources
  manuscript_evidence_for_polish/existing_tables/main_model_calibration_S2.csv
  manuscript_evidence_for_polish/existing_tables/main_model_sigma_spearman.csv
  manuscript_evidence_for_polish/existing_tables/
      S15_S17_preprocessing_control_metrics.csv
  manuscript_evidence_for_polish/existing_tables/
      S17b_interval_score_model_vs_empirical_baseline.csv
  supplementary_validation_v3/A1_interval_repair/outputs/tables/a1v3_meta.json
  noise_robustness/noise_metrics_all.csv
  noise_robustness/noise_calibration_summary.csv
  noise_robustness/noise_uncertainty_summary.csv
  final_figures/scripts/_frozen_preds.npz

Outputs: figures/Figure5{,_large}.{png,pdf,svg}
         data_used/Figure5_plotting_values.csv
"""

import os
import sys
import json

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st

BASE = st.BASE
EV = os.path.join(BASE, "manuscript_evidence_for_polish", "existing_tables")
CAL_CSV = os.path.join(EV, "main_model_calibration_S2.csv")
RHO_CSV = os.path.join(EV, "main_model_sigma_spearman.csv")
S15_CSV = os.path.join(EV, "S15_S17_preprocessing_control_metrics.csv")
S17B_CSV = os.path.join(EV, "S17b_interval_score_model_vs_empirical_baseline.csv")
A1_META = os.path.join(BASE, "supplementary_validation_v3", "A1_interval_repair",
                       "outputs", "tables", "a1v3_meta.json")
NOISE = os.path.join(BASE, "noise_robustness")
N_MET = os.path.join(NOISE, "noise_metrics_all.csv")
N_CAL = os.path.join(NOISE, "noise_calibration_summary.csv")
N_UNC = os.path.join(NOISE, "noise_uncertainty_summary.csv")

# ------------------------------------------------------------- frozen pins --
LEVELS = [0.50, 0.80, 0.90, 0.95]
Z = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}
COV95 = [0.947475, 0.952244, 0.958320, 0.959692, 0.946364,
         0.949892, 0.969164, 0.966682, 0.966421]
RHO = [0.398191, 0.334319, 0.645906, 0.621839, 0.353014,
       0.244391, 0.377232, 0.464704, 0.414716]
MEAN_RHO = 0.4283
IS_MODEL95 = [1.691110, 1.538768, 3.883600, 3.839046, 1.359168,
              1.434626, 3.994252, 3.332993, 2.967536]
IS_BASE95 = [3.174343, 3.173351, 6.997207, 6.973871, 2.781404,
             2.837432, 3.897954, 3.892600, 2.927081]
N_TEST = 15307

NOISE_LV = ["0%", "0.2%", "0.5%", "1.0%", "2.0%"]
NOISE_X = [0.0, 0.2, 0.5, 1.0, 2.0]

C_MODEL = st.OKABE_ITO[0]
C_BASE = "#9AA3AB"
C_WORSE = st.OKABE_ITO[3]


def iscore(lo, hi, y, c):
    """Gneiting-Raftery interval score; lower is better."""
    return ((hi - lo) + 2.0 / (1.0 - c) * np.clip(lo - y, 0, None)
            + 2.0 / (1.0 - c) * np.clip(y - hi, 0, None))


def load():
    d = np.load(st.NPZ, allow_pickle=True)
    y_true, mu, sig = d["params_test"], d["param_mu"], d["param_sigma"]
    raw = d["params_test_raw"]
    names = [str(n) for n in d["param_names"]]
    assert names == st.PARAM_NAMES, names
    assert y_true.shape == (N_TEST, 9), y_true.shape

    meta = json.load(open(A1_META))
    env_lo = np.asarray(meta["env_lo_log10"], float)
    R = np.asarray(meta["R_decades"], float)
    assert meta["n_test"] == N_TEST
    assert meta["levels"] == LEVELS

    # --- verify model / scaler / test set / clipping against the frozen table
    cal = pd.read_csv(CAL_CSV)
    cov = np.zeros((9, 4))
    for i, p in enumerate(names):
        for j, lv in enumerate(LEVELS):
            cov[i, j] = float(cal[(cal.parameter == p)
                                  & (cal.nominal == lv)]
                              ["empirical_coverage"].iloc[0])
            # recompute from the frozen arrays: same test set, frozen chain
            ins = np.abs(mu[:, i] - y_true[:, i]) <= Z[lv] * sig[:, i]
            lo = np.clip(mu[:, i] - Z[lv] * sig[:, i], 0.0, 1.0)
            hi = np.clip(mu[:, i] + Z[lv] * sig[:, i], 0.0, 1.0)
            covc = ((y_true[:, i] >= lo) & (y_true[:, i] <= hi)).mean()
            assert abs(float(ins.mean()) - cov[i, j]) < 1e-5, (p, lv)
            assert abs(float(covc) - float(ins.mean())) < 1e-12, (p, lv)
    for i in range(9):
        assert abs(cov[i, 3] - COV95[i]) < 1e-5, (names[i], cov[i, 3])

    # --- interval score: recomputed from the RAW (unclipped) Gaussian
    # endpoints and mapped from normalized to physical log10 units
    # (meta["R_decades"] is a key of the frozen JSON; the width it holds is an
    # increment of log10 of the parameter, quoted in log10 units here)
    is_model = np.array([
        float(np.mean(iscore(mu[:, i] - Z[0.95] * sig[:, i],
                             mu[:, i] + Z[0.95] * sig[:, i],
                             y_true[:, i], 0.95))) * R[i]
        for i in range(9)])
    for i in range(9):
        assert abs(is_model[i] - IS_MODEL95[i]) < 1e-4, (names[i], is_model[i])

    s17 = pd.read_csv(S17B_CSV)
    base = s17[s17.level == 0.95].set_index("param")
    # S17b indexes parameters by the short code names, not the csv column names
    is_base = np.array([float(base.loc[st.PARAM_SHORT[i], "prior_is_dec_mean"])
                        for i in range(9)])
    worse = np.array([bool(base.loc[st.PARAM_SHORT[i], "raw_worse_than_prior"])
                      for i in range(9)])
    for i in range(9):
        assert abs(is_base[i] - IS_BASE95[i]) < 1e-6, (names[i], is_base[i])
    assert worse.tolist() == [False] * 6 + [True, False, True], worse
    # the baseline is a training-partition quantity, identical for every level
    assert len(s17) == 36 and set(s17.level) == set(LEVELS)

    # --- the S15_S17 table must be read on the Historical run only ----------
    s15 = pd.read_csv(S15_CSV)
    assert set(s15.model) == {"Historical", "L", "T", "Prior"}, set(s15.model)
    hist = s15[(s15.model == "Historical") & (s15.kind == "model")] \
        .set_index("param")
    for i, n in enumerate(names):
        assert abs(float(hist.loc[n, "is_0.95"]) - IS_MODEL95[i]) < 1e-5, n
        assert abs(float(hist.loc[n, "cov_0.95"]) - COV95[i]) < 1e-5, n
    # the L / T control runs differ from the frozen main model -- they must
    # never be substituted for it
    for run in ("L", "T"):
        alt = s15[(s15.model == run) & (s15.kind == "model")].set_index("param")
        assert any(abs(float(alt.loc[n, "is_0.95"]) - IS_MODEL95[i]) > 1e-4
                   for i, n in enumerate(names)), run

    # --- Spearman(sigma, |error|) -- computed for the SI panel -------------
    rho_csv = pd.read_csv(RHO_CSV).set_index("parameter")
    rho = np.array([float(rho_csv.loc[n, "spearman_rho"]) for n in names])
    for i in range(9):
        assert abs(rho[i] - RHO[i]) < 1e-5, (names[i], rho[i])
    assert abs(rho.mean() - MEAN_RHO) < 5e-5, rho.mean()

    # --- noise experiment ---------------------------------------------------
    nmet = pd.read_csv(N_MET)
    ncal = pd.read_csv(N_CAL)
    nunc = pd.read_csv(N_UNC)
    r_mat = np.array([[float(nmet[(nmet.parameter == p) & (nmet.noise == lv)]
                                 ["r_mean"].iloc[0]) for lv in NOISE_LV]
                      for p in names])
    c_mat = np.array([[float(ncal[(ncal.parameter == p) & (ncal.noise == lv)
                                  & (ncal.nominal == 0.95)]
                             ["coverage_mean"].iloc[0]) for lv in NOISE_LV]
                      for p in names])
    s_mat = np.array([[float(nunc[(nunc.parameter == p) & (nunc.noise == lv)]
                                 ["sigma_mean"].iloc[0]) for lv in NOISE_LV]
                      for p in names])
    # the clean column of the noise tables must be the frozen clean evaluation
    for i, n in enumerate(names):
        assert abs(r_mat[i, 0] - float(hist.loc[n, "pearson"])) < 1e-6, n
    assert abs(r_mat.mean(axis=0)[0] - 0.807) < 1e-3, r_mat.mean(axis=0)[0]
    assert abs(r_mat.mean(axis=0)[3] - 0.748) < 2e-3
    assert abs(r_mat.mean(axis=0)[4] - 0.672) < 2e-3
    for i in range(9):
        assert abs(c_mat[i, 0] - COV95[i]) < 1e-5, names[i]
    assert 0.836 - 1e-3 <= c_mat[:, 3].min() and c_mat[:, 3].max() <= 0.934 + 1e-3
    assert 0.722 - 1e-3 <= c_mat[:, 4].min() and c_mat[:, 4].max() <= 0.887 + 1e-3
    s_rel = 100.0 * (s_mat - s_mat[:, [0]]) / s_mat[:, [0]]
    assert abs(s_rel.min() - (-2.336)) < 5e-3, s_rel.min()
    assert np.abs(s_rel).max() < 3.0
    return dict(names=names, cov=cov, rho=rho, is_model=is_model,
                is_base=is_base, worse=worse, r_mat=r_mat, c_mat=c_mat,
                s_rel=s_rel)


def build(size):
    D = load()
    names, cov = D["names"], D["cov"]
    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 0.690))
    # Five panels in a 2 x 3 grid; the top-right cell is not a panel, it holds
    # the shared nine-parameter legend for the three noise sweeps below it.
    gs = fig.add_gridspec(2, 3, left=0.085, right=0.985, top=0.900,
                          bottom=0.100, wspace=0.46, hspace=0.62)

    # ---------------- (a) clean calibration curves --------------------------
    axa = fig.add_subplot(gs[0, 0])
    diag = np.array([0.42, 1.0])
    axa.plot(diag, diag, ls="--", color="#999999", lw=0.8, zorder=1)
    for i in range(9):
        axa.plot(LEVELS, cov[i], marker="o", ms=3.2, lw=1.0, alpha=0.85,
                 color=st.PARAM_COLORS[i], zorder=2)
    axa.set_xlim(0.42, 1.0)
    axa.set_ylim(0.42, 1.0)
    axa.set_xticks(LEVELS)
    axa.set_xticklabels(["50", "80", "90", "95"])
    axa.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    axa.set_xlabel("Nominal level (%)")
    axa.set_ylabel("Empirical coverage")
    st.configure_axes(axa)
    st.panel_label(axa, "(a)", dx=-0.26)

    # ---------------- (b) interval score, model vs baseline @ 95% -----------
    # Connected dot plot rather than grouped bars: nine rows, one comparison
    # each, so the reader scans a single horizontal distance per parameter.
    axb = fig.add_subplot(gs[0, 1])
    ism, isb, worse = D["is_model"], D["is_base"], D["worse"]
    ys = np.arange(9)[::-1]
    for i in range(9):
        axb.plot([isb[i], ism[i]], [ys[i], ys[i]], color="#c9ced4", lw=1.3,
                 zorder=1, solid_capstyle="round")
    axb.plot(isb, ys, ls="none", marker="o", ms=5.0, mfc="white",
             mec=C_BASE, mew=1.1, zorder=3,
             label="Training-quantile baseline")
    axb.plot(ism, ys, ls="none", marker="o", ms=5.2, color=C_MODEL,
             zorder=4, label="Model interval")
    # the extra ring is the only cue that the model lost on this parameter
    axb.plot(np.asarray(ism)[worse], ys[worse], ls="none", marker="o",
             ms=8.6, mfc="none", mec=C_WORSE, mew=1.3, zorder=5,
             label="Model worse than baseline")
    axb.set_yticks(ys)
    axb.set_yticklabels(st.PARAM_LABELS, fontsize=st.FS_ANNOT)
    axb.set_ylim(-0.7, 8.7)
    axb.set_xlim(0.0, 7.6)
    axb.set_xticks([0, 2, 4, 6])
    # "log10 units", not "decades": these are increments of log10 of the
    # parameter, and a decade is a factor of ten in the linear parameter.
    axb.set_xlabel(r"Interval score (log$_{10}$ units)"
                   "\n95%; lower is better", fontsize=st.FS_AXIS - 1.0)
    # No in-axes legend: at journal width a three-entry legend is ~110 pt wide
    # inside a 117 pt panel, so however it is anchored it lands on the data.
    # The keys for this panel are in the free top-right cell, below.
    st.configure_axes(axb)
    st.panel_label(axb, "(b)", dx=-0.30)

    # ---------------- free cell: panel keys ---------------------------------
    # Two stacked legends: the three marker keys of panel (b), then the shared
    # nine-parameter colour key for the three noise sweeps (c)-(e).
    axl = fig.add_subplot(gs[0, 2])
    axl.axis("off")
    l1 = axl.legend(
        handles=[Line2D([0], [0], ls="none", marker="o", ms=5.0, mfc="white",
                        mec=C_BASE, mew=1.1, label="Training-quantile baseline"),
                 Line2D([0], [0], ls="none", marker="o", ms=5.2,
                        color=C_MODEL, label="Model interval"),
                 Line2D([0], [0], ls="none", marker="o", ms=8.0, mfc="none",
                        mec=C_WORSE, mew=1.3, label="Model worse")],
        loc="upper left", bbox_to_anchor=(-0.02, 1.02), frameon=False,
        fontsize=st.FS_LEGEND - 0.5, handlelength=1.2, handletextpad=0.5,
        labelspacing=0.42, borderpad=0.0,
        title="Panel (b)", title_fontsize=st.FS_LEGEND - 0.5)
    axl.add_artist(l1)
    handles = [Line2D([0], [0], color=st.PARAM_COLORS[i], lw=1.4,
                      marker="o", ms=3.5, label=st.PARAM_LABELS[i])
               for i in range(9)]
    axl.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.02, 0.62),
               ncol=1, frameon=False, fontsize=st.FS_LEGEND,
               handlelength=1.6, handletextpad=0.6, labelspacing=0.34,
               borderpad=0.0, title="Panels (c)–(e)",
               title_fontsize=st.FS_LEGEND)

    # ---------------- (c) predictive correlation vs noise -------------------
    axc = fig.add_subplot(gs[1, 0])
    for i in range(9):
        axc.plot(NOISE_X, D["r_mat"][i], marker="o", ms=3.2, lw=1.0,
                 alpha=0.8, color=st.PARAM_COLORS[i], zorder=2)
    axc.set_ylim(0.35, 1.0)
    axc.set_xticks(NOISE_X)
    axc.set_xticklabels(["0", "0.2", "0.5", "1", "2"])
    axc.set_xlabel("Current noise\n(% of $|J_\\mathrm{sc}|$)",
                   fontsize=st.FS_AXIS - 1.0)
    # rho, not r: throughout the manuscript r is the electron-hole ratio
    # r = log10(p_n/p_p), and rho is the Pearson correlation (as in Figure 2).
    axc.set_ylabel(r"Pearson correlation, $\rho$")
    st.configure_axes(axc)
    st.panel_label(axc, "(c)", dx=-0.26)

    # ---------------- (d) 95% marginal coverage vs noise --------------------
    axd = fig.add_subplot(gs[1, 1])
    for i in range(9):
        axd.plot(NOISE_X, D["c_mat"][i], marker="o", ms=3.2, lw=1.0,
                 alpha=0.8, color=st.PARAM_COLORS[i], zorder=2)
    axd.axhline(0.95, ls="--", color="#555555", lw=0.9, zorder=1)
    axd.text(2.02, 0.955, "nominal 0.95", fontsize=st.FS_ANNOT,
             color=st.MUTED, ha="right", va="bottom")
    axd.set_ylim(0.68, 1.0)
    axd.set_xticks(NOISE_X)
    axd.set_xticklabels(["0", "0.2", "0.5", "1", "2"])
    axd.set_xlabel("Current noise\n(% of $|J_\\mathrm{sc}|$)",
                   fontsize=st.FS_AXIS - 1.0)
    axd.set_ylabel("95% coverage")
    st.configure_axes(axd)
    st.panel_label(axd, "(d)", dx=-0.26)

    # ---------------- (e) change in predicted scale vs noise ----------------
    axe = fig.add_subplot(gs[1, 2])
    for i in range(9):
        axe.plot(NOISE_X, D["s_rel"][i], marker="o", ms=3.2, lw=1.0,
                 alpha=0.8, color=st.PARAM_COLORS[i], zorder=2)
    axe.axhline(0.0, color="#bbbbbb", lw=0.8, zorder=1)
    axe.set_ylim(-3.0, 0.7)
    axe.set_xticks(NOISE_X)
    axe.set_xticklabels(["0", "0.2", "0.5", "1", "2"])
    axe.set_xlabel("Current noise\n(% of $|J_\\mathrm{sc}|$)",
                   fontsize=st.FS_AXIS - 1.0)
    axe.set_ylabel("Change in mean $\\sigma_\\theta$\n"
                   "(% of its clean-input value)")
    st.configure_axes(axe)
    st.panel_label(axe, "(e)", dx=-0.26)

    stem = os.path.join(st.FIGDIR, "Figure5"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)
    return fig


def main():
    for size in ("journal", "large"):
        build(size)

    D = load()
    rows = []
    for i, n in enumerate(D["names"]):
        for j, lv in enumerate(LEVELS):
            rows.append(dict(panel="a", item=n, level=lv,
                             value=D["cov"][i, j], unit="coverage",
                             source="existing_tables/main_model_calibration_S2.csv"))
        # the Spearman association is no longer drawn in the main figure; the
        # numbers are still recorded here, tagged SI, so the supplementary
        # panel has one verified source.
        rows.append(dict(panel="SI", item=n, level=np.nan, value=D["rho"][i],
                         unit="Spearman rho",
                         source="existing_tables/main_model_sigma_spearman.csv"))
        rows.append(dict(panel="b", item=n + "_model", level=0.95,
                         value=D["is_model"][i], unit="log10 units",
                         source="existing_tables/"
                                "S15_S17_preprocessing_control_metrics.csv "
                                "(Historical only)"))
        rows.append(dict(panel="b", item=n + "_baseline", level=0.95,
                         value=D["is_base"][i], unit="log10 units",
                         source="existing_tables/"
                                "S17b_interval_score_model_vs_empirical_"
                                "baseline.csv"))
        for j, lv in enumerate(NOISE_LV):
            rows.append(dict(panel="c", item=n, level=NOISE_X[j],
                             value=D["r_mat"][i, j], unit="Pearson r",
                             source="noise_robustness/noise_metrics_all.csv"))
            rows.append(dict(panel="d", item=n, level=NOISE_X[j],
                             value=D["c_mat"][i, j], unit="coverage",
                             source="noise_robustness/"
                                    "noise_calibration_summary.csv"))
            rows.append(dict(panel="e", item=n, level=NOISE_X[j],
                             value=D["s_rel"][i, j], unit="% change",
                             source="noise_robustness/"
                                    "noise_uncertainty_summary.csv"))
    pd.DataFrame(rows).to_csv(
        os.path.join(st.DATADIR, "Figure5_plotting_values.csv"), index=False)
    print("wrote plotting table")


if __name__ == "__main__":
    main()
