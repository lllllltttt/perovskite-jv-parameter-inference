"""
fig4_forward.py — reassembled main Figure 4.
============================================
"Physical response of inferred parameter combinations"

Panels
  (a)-(c) three archived representative back-substitution cases spanning the
          cycle-gap range (lowest / median / highest), each showing the target
          curve, the decoder reconstruction (from z) and the COMSOL response
          obtained by back-substituting the inferred parameter vector.
          -> re-used from the archived SI cycle audit
             (final_figures/scripts/plot_SI_S3_cycle_audit.py); the archived
             representative sample IDs are inherited unchanged, NOT re-selected.
  (d)     per-sample J-V RMSE distributions: full curve / 0-1.0 V / >1.0 V
          -> old Figure 6 panel (c) (plot_Fig6_noise_forward.py)
  (e)     device-metric absolute deviations |dJsc|, |dVoc|, |dFF|, |dPCE|
          -> old Figure 6 panel (d)

IMPORTANT extraction note (the one substantive numerical change relative to the
submitted old Figure 6 panel (d)): the per-sample CSV columns
`dVoc`/`dFF` derive from metrics stored ROUNDED in
`forward_validation_unbiased/forward_metrics_per_sample.csv` (Voc at 2 decimals,
FF at 6 decimals), which is why that table gives 0.0300 / 0.01413 rather than
the manuscript values. This script therefore does NOT read those columns. It
recomputes Jsc / Voc / FF / PCE directly from the frozen raw curves with the
manuscript's documented single extraction convention -- "unified continuous
linear zero-crossing", `device_metrics(..., voc_mode="interp")` of
supplementary_validation_v2/_tools/v2lib.py -- for both the target and the
COMSOL-predicted curve, and takes the median absolute deviation. These are the
values tabulated in manuscript_evidence_for_polish/evidence_report.md section
8.4 and required in the figure: 0.111897 / 0.022439 / 0.015533 / 0.471401 pp.
|dJsc| and the curve RMSEs use n = 45; |dVoc|, |dFF|, |dPCE| use n = 44 (one
predicted curve has no downward zero crossing).

Frozen sources
  final_figures/scripts/_frozen_preds.npz                    (target curves)
  data/J_scaler.pkl                                          (decoder -> mA/cm2)
  decoder_comsol_audit/decoder_comsol_metrics_per_sample.csv (case selection)
  forward_validation_unbiased/comsol_pred/Sample_*_pred.mat
  forward_validation_unbiased/comsol_true/Sample_*_true.mat
  forward_validation_unbiased/forward_metrics_per_sample.csv (curve RMSEs)

Outputs: figures/Figure4.{png,pdf,svg}  +  data_used/Figure4_plotting_values.csv
"""

import os
import re
import sys
import glob
import pickle

import numpy as np
import pandas as pd
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpecFromSubplotSpec
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st

# documented extraction convention (read-only import of the frozen helper)
sys.path.insert(0, os.path.join(st.BASE, "supplementary_validation_v2", "_tools"))
import v2lib                                   # noqa: E402

BASE = st.BASE
NPZ = st.NPZ
J_SCALER = os.path.join(BASE, "data", "J_scaler.pkl")
DC_CSV = os.path.join(BASE, "decoder_comsol_audit",
                      "decoder_comsol_metrics_per_sample.csv")
FW_DIR = os.path.join(BASE, "forward_validation_unbiased")
FW_PER = os.path.join(FW_DIR, "forward_metrics_per_sample.csv")
FW_PRED = os.path.join(FW_DIR, "comsol_pred")
FW_TRUE = os.path.join(FW_DIR, "comsol_true")

# ---- test-index -> database Sample_ID map ----------------------------------
# The numbers in the (a)-(c) titles are LOCAL zero-based row indices into the
# frozen test-set arrays (all _frozen_preds.npz arrays are (15307, ...)), not
# database Sample_IDs. The `Sample_%05d_*.mat` filenames and the audit CSV's
# `sample_id` column merely reuse that local index. The genuine database
# Sample_ID is recovered below from the frozen split; the two documented
# anchors of supplementary_validation_v4/scripts/t0_verify_split_and_sampleid.py
# are asserted so a wrong or reordered split cannot pass silently.
PHYS_NPZ = os.path.join(BASE, "supplementary_validation_v4", "T2_control",
                        "_data_physical.npz")
ID_ANCHOR = {595: 117995, 12051: 69653}      # t0 v3 anchor, v2 wide anchor


def load_id_map():
    z = np.load(PHYS_NPZ, allow_pickle=True)
    idx_test = np.asarray(z["idx_test"], dtype=np.int64)
    sample_id = np.asarray(z["Sample_ID"], dtype=np.int64)
    assert idx_test.shape == (15307,), idx_test.shape
    assert sample_id.shape == (102046,), sample_id.shape
    for ti, exp in ID_ANCHOR.items():
        got = int(sample_id[idx_test[ti]])
        assert got == exp, (ti, got, exp)
    return idx_test, sample_id

# ------------------------------------------------------------- frozen pins --
MED_CG, MED_DEC, MED_COM = 2.562703, 1.885968, 2.692631      # cycle audit
RMSE_MED = {"full": 2.692631, "le1": 0.455349, "gt1": 5.191600}
DEV_MED = {"Jsc": (0.111897, 45), "Voc": (0.022439, 44),
           "FF": (0.015533, 44), "PCE": (0.471401, 44)}
DEV_UNIT = {"Jsc": r"mA cm$^{-2}$", "Voc": "V", "FF": r"$-$",
            "PCE": "pp"}
DEV_SYM = {"Jsc": r"$|\Delta J_\mathrm{sc}|$", "Voc": r"$|\Delta V_\mathrm{oc}|$",
           "FF": r"$|\Delta FF|$", "PCE": r"$|\Delta \mathrm{PCE}|$"}
DEV_ORDER = ["Jsc", "Voc", "FF", "PCE"]
# archived representative cases = cycle-gap percentiles 0 / 0.5 / 1.0 of the
# 45-sample cohort (selection inherited from the SI cycle audit, not made here)
CASE_Q = [0.0, 0.5, 1.0]
CASE_TAG = ["lowest", "median", "highest"]
CASE_SID_EXPECT = [12058, 595, 14499]

C_TARGET = "#333333"
C_DEC = st.OKABE_ITO[0]
C_COM = st.OKABE_ITO[3]


def load_mat_J(path):
    """A/m^2 -> mA/cm^2 (frozen unit convention of the forward-validation run)."""
    dd = loadmat(path, squeeze_me=True)
    J = np.asarray(dd["J"], dtype=np.float64)
    if J.ndim == 2:
        J = J[:, 0]
    return J * 0.1


def collect():
    d = np.load(NPZ, allow_pickle=True)
    V = d["V_GRID"]
    Jraw = d["J_test_raw"]
    with open(J_SCALER, "rb") as f:
        js = pickle.load(f)
    recon_phys = js.inverse_transform(d["recon_test"])

    sids = sorted(int(re.search(r"Sample_(\d+)_", p).group(1))
                  for p in glob.glob(os.path.join(FW_PRED, "Sample_*_pred.mat")))
    assert len(sids) == 45, len(sids)

    comsol, target, dec = {}, {}, {}
    dev = {k: [] for k in DEV_ORDER}
    for sid in sids:
        Jt = load_mat_J(os.path.join(FW_TRUE, "Sample_%05d_true.mat" % sid))
        Jp = load_mat_J(os.path.join(FW_PRED, "Sample_%05d_pred.mat" % sid))
        # the archived target of the audit is J_test_raw[sid]; the .mat copy is
        # the same curve (agrees to ~1e-7 mA/cm2 = float32 store precision), so
        # use the frozen array itself to keep the audit identity exact
        assert np.max(np.abs(Jt - Jraw[sid])) < 1e-5, sid
        Jt = Jraw[sid]
        comsol[sid], target[sid], dec[sid] = Jp, Jt, recon_phys[sid]
        mt = v2lib.device_metrics(Jt, voc_mode="interp")
        mp = v2lib.device_metrics(Jp, voc_mode="interp")
        for k in DEV_ORDER:
            ok = np.isfinite(mp[k]) and np.isfinite(mt[k])
            dev[k].append(mp[k] - mt[k] if ok else np.nan)
    for k, (med_e, n_e) in DEV_MED.items():
        a = np.abs(np.asarray(dev[k], float))
        m = float(np.nanmedian(a))
        assert abs(m - med_e) < 1e-6, (k, m, med_e)
        assert int(np.isfinite(a).sum()) == n_e, (k, int(np.isfinite(a).sum()))
    print("device-metric medians reproduced:",
          {k: DEV_MED[k][0] for k in DEV_ORDER})

    df = pd.read_csv(DC_CSV)
    assert len(df) == 45
    assert abs(float(df["cycle_gap"].median()) - MED_CG) < 1e-3
    assert abs(float(df["rmse_decoder"].median()) - MED_DEC) < 1e-3
    assert abs(float(df["rmse_comsol"].median()) - MED_COM) < 1e-3
    order = np.argsort(df["cycle_gap"].values)
    cases = [(int(df.iloc[order[int(q * (len(df) - 1))]]["sample_id"]),
              float(df.iloc[order[int(q * (len(df) - 1))]]["cycle_gap"]))
             for q in CASE_Q]
    assert [c[0] for c in cases] == CASE_SID_EXPECT, [c[0] for c in cases]
    for sid, cg in cases:
        got = float(np.sqrt(np.mean((comsol[sid] - dec[sid]) ** 2)))
        assert abs(got - cg) < 1e-3, (sid, got, cg)
    print("representative cases (local test index):", cases)

    idx_test, sample_id = load_id_map()
    db_id = {ti: int(sample_id[idx_test[ti]]) for ti in sids}
    print("test index -> database Sample_ID:",
          {ti: db_id[ti] for ti, _ in cases})

    fw = pd.read_csv(FW_PER)
    assert len(fw) == 45
    rm = {"full": fw["rmse_full"].values, "le1": fw["rmse_0to1V"].values,
          "gt1": fw["rmse_gt1V"].values}
    for k, arr in rm.items():
        assert abs(float(np.median(arr)) - RMSE_MED[k]) < 1e-5, (k, np.median(arr))
        assert arr.min() > 0
    return dict(V=V, comsol=comsol, target=target, dec=dec, dev=dev, df=df,
                cases=cases, rm=rm, db_id=db_id)


def build(size):
    D = collect()
    V, comsol = D["V"], D["comsol"]
    target, dec = D["target"], D["dec"]
    dev, df, cases, rm = D["dev"], D["df"], D["cases"], D["rm"]

    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 0.900))
    # `left` is set by the two-line rotated ylabel of the (a)-(c) residual
    # strips, which is the leftmost text on the canvas; at journal width it
    # ran 5.65 pt past the canvas edge at 0.085.
    gs = fig.add_gridspec(2, 6, left=0.098, right=0.985, top=0.900,
                          bottom=0.105, wspace=1.60, hspace=0.62,
                          height_ratios=[1.0, 0.92])

    # ---------------- (a)-(c) representative back-substitution cases --------
    # Each case is a curve panel plus its own residual strip, sharing a
    # voltage axis. The residual is formed pointwise, J_x(V) - J_target(V),
    # from the frozen curves themselves; nothing is read off a rendered image
    # and no archived case is swapped.
    resid_max = 0.0
    for k, (tag, sid, cg) in enumerate(cases and
                                       [(CASE_TAG[i], cases[i][0], cases[i][1])
                                        for i in range(3)]):
        inner = GridSpecFromSubplotSpec(
            2, 1, subplot_spec=gs[0, 2 * k:2 * k + 2],
            hspace=0.0, height_ratios=[1.0, 0.42])
        ax = fig.add_subplot(inner[0])
        axr = fig.add_subplot(inner[1], sharex=ax)

        ax.axhline(0.0, color="#bbbbbb", lw=0.7, zorder=1)
        ax.plot(V, target[sid], color=C_TARGET, lw=1.5, zorder=4,
                label="Target (COMSOL)")
        ax.plot(V, dec[sid], color=C_DEC, lw=1.2, ls="--", zorder=3,
                label="Decoder reconstruction (from $z$)")
        ax.plot(V, comsol[sid], color=C_COM, lw=1.2, ls="-.", zorder=2,
                label=r"COMSOL response from $\hat{\theta}$")
        lo = min(target[sid].min(), dec[sid].min(), comsol[sid].min())
        hi = max(target[sid].max(), dec[sid].max(), comsol[sid].max())
        R = hi - lo
        ax.set_xlim(0.0, 1.3)
        ax.set_ylim(lo - 0.08 * R, hi + 0.30 * R)
        # Keep only the y ticks inside the view. MaxNLocator returns one step
        # beyond each end, and those two labels are never painted -- the lower
        # one falls under the residual strip's opaque box, the upper one above
        # the panel -- but they still carry a text bounding box, and a
        # geometry-only QA pass measures bounding boxes: it reported the lower
        # one as three separate overlaps with the strip's tick numbers and with
        # its rotated ylabel. Dropping them changes no pixel and stops the
        # measurement disagreeing with the render.
        _y0, _y1 = ax.get_ylim()
        ax.set_yticks([t for t in ax.get_yticks() if _y0 <= t <= _y1])
        ax.set_xticks([0.0, 0.5, 1.0])
        # the voltage axis belongs to the residual strip below, so the curve
        # panel carries no x tick labels of its own
        ax.tick_params(axis="x", labelbottom=False)
        # Each case keeps its own y range, so each panel must carry its own
        # numeric y ticks and its own unit -- a shared axis label on (a) alone
        # left (b) and (c) with unlabelled, unreadable scales.
        ax.set_ylabel(r"$J$ (mA cm$^{-2}$)")
        st.configure_axes(ax)
        # `sid` is a zero-based index into the frozen test set, not a database
        # Sample_ID (mapped and asserted in load_id_map()).
        # Two lines: the single-line form of the third title ("Test index 14499
        # — highest cycle gap") is wider than its panel at journal width.
        ax.set_title("Test index %d\n%s cycle gap" % (sid, tag),
                     fontsize=st.FS_TITLE, color=st.INK, pad=4.0)
        ax.text(0.030, 0.985,
                r"$d_\mathrm{gap}$ = %.3g" % cg + "\n"
                r"$d_\mathrm{dec}$ = %.3g,  $d_\mathrm{COM}$ = %.3g"
                % (float(df[df.sample_id == sid]["rmse_decoder"].iloc[0]),
                   float(df[df.sample_id == sid]["rmse_comsol"].iloc[0])),
                transform=ax.transAxes, fontsize=st.FS_ANNOT, va="top", ha="left",
                color=st.INK, linespacing=1.45)
        st.panel_label(ax, "(%s)" % "abc"[k], dy=1.13)

        # ---- operating-region inset, highest cycle-gap case only -----------
        # Case (c) reaches about -1.5 A cm^-2 in reverse bias, so a single
        # linear axis compresses the whole power-generating quadrant into the
        # top 5% of the panel and the three curves look superimposed there. The
        # full range is kept -- the high-bias divergence is the point of this
        # case -- and the operating window is repeated at a readable scale in
        # an inset. Only this case gets one: (a) and (b) are already readable
        # at full range, and an inset on every panel would be noise.
        if tag == "highest":
            op = (V >= 0.0) & (V <= 1.0)        # the 0-1.0 V window of panel (d)
            # Big enough to read: the first attempt at 0.6 x 0.45 of the axes
            # left the tick numbers at ~5 pt and the three curves merged into
            # one line, which is worse than no inset at all. The window is
            # labelled on the inset itself rather than marked on the full-range
            # axes -- a 30 mA cm^-2 band inside a 2000 mA cm^-2 axis is a 1.4%
            # sliver, and a box drawn around it says nothing.
            axi = ax.inset_axes([0.088, 0.048, 0.812, 0.556])
            axi.axhline(0.0, color="#bbbbbb", lw=0.6, zorder=1)
            axi.plot(V[op], target[sid][op], color=C_TARGET, lw=1.1, zorder=4)
            axi.plot(V[op], dec[sid][op], color=C_DEC, lw=1.0, ls="--",
                     zorder=3)
            axi.plot(V[op], comsol[sid][op], color=C_COM, lw=1.0, ls="-.",
                     zorder=2)
            ylo = min(target[sid][op].min(), dec[sid][op].min(),
                      comsol[sid][op].min())
            yhi = max(target[sid][op].max(), dec[sid][op].max(),
                      comsol[sid][op].max())
            yr = yhi - ylo
            axi.set_xlim(0.0, 1.0)
            axi.set_ylim(ylo - 0.16 * yr, yhi + 0.20 * yr)
            axi.set_xticks([0.0, 0.5, 1.0])
            axi.yaxis.set_major_locator(MaxNLocator(nbins=3))
            # NO ylabel on the inset. A rotated label sits outside the inset's
            # own left edge, which is inside the full-range panel -- exactly
            # where that panel's -500 / -1000 / -1500 tick numbers are, and the
            # two strings printed on top of each other.
            #
            # The unit sits INSIDE the inset, low and to the left -- not above
            # it, and not as a title. Two measured reasons, both found by
            # looking at the 600 dpi render rather than at the geometry report:
            #
            #  * Above the inset is a 23 px band between its top edge and the
            #    flat 0-level part of the three curves, and the old two-line
            #    title is 25 px, so its first line printed straight along the
            #    curves -- the black target line ran through "same curves".
            #    A one-line title does not fit either: the descending branch of
            #    the curve crosses that band at x ~ 640 px, which is inside the
            #    centred title's own width.
            #  * Inside, the lower-left is empty white, because the curves sit
            #    at the top of the window until V ~ 0.9. But the room is
            #    narrow: "same curves, operating region 0-1.0 V" measures
            #    168 px against the 131 px interior, and "operating region
            #    0-1.0 V" alone is 107 px, which puts its right end at 0.85 of
            #    the width where the curve has already come down to meet it.
            #    The unit is 56 px and clears it comfortably.
            #
            # What is left out is carried where it belongs: the inset's own x
            # axis prints 0.0 / 0.5 / 1.0, so the window is on the axes, and
            # the figure caption names it.
            axi.text(0.040, 0.055, r"$J$ (mA cm$^{-2}$)",
                     transform=axi.transAxes, ha="left", va="bottom",
                     fontsize=st.FS_ANNOT, color=st.INK)
            st.configure_axes(axi)
            axi.tick_params(axis="both", labelsize=st.FS_TICK - 1.5,
                            length=2.0, pad=1.5)
            for s in axi.spines.values():
                s.set_linewidth(0.7)

        # ---- residual strip, same colours and dash patterns as above -------
        d_dec = dec[sid] - target[sid]
        d_com = comsol[sid] - target[sid]
        resid_max = max(resid_max, float(np.abs(d_dec).max()),
                        float(np.abs(d_com).max()))
        axr.axhline(0.0, color="#bbbbbb", lw=0.7, zorder=1)
        axr.plot(V, d_dec, color=C_DEC, lw=1.0, ls="--", zorder=3)
        axr.plot(V, d_com, color=C_COM, lw=1.0, ls="-.", zorder=2)
        axr.set_xlim(0.0, 1.3)
        axr.set_ylim(-1.30 * resid_max, 1.30 * resid_max)
        axr.set_xticks([0.0, 0.5, 1.0])
        axr.set_xlabel("Voltage (V)")
        axr.set_ylabel(r"$\Delta J$" "\n" r"(mA cm$^{-2}$)",
                       fontsize=st.FS_ANNOT)
        axr.set_yticks([-resid_max, 0.0, resid_max])
        axr.set_yticklabels(["%.3g" % -resid_max, "0", "%.3g" % resid_max])
        st.configure_axes(axr)
        axr.tick_params(axis="both", labelsize=st.FS_TICK - 0.5)

    # one shared unit note for the three annotations, in the gap between the
    # residual strips and the (d)/(e) row
    p0 = gs[0, 0:6].get_position(fig)
    fig.text(p0.x0 + p0.width / 2, p0.y0 - 0.103,
             r"Lower strips: $\Delta J = J_x - J_\mathrm{target}$; "
             r"$d_\mathrm{gap}$, $d_\mathrm{dec}$ and $d_\mathrm{COM}$ are "
             r"curve RMSEs in mA cm$^{-2}$",
             ha="center", va="center", fontsize=st.FS_ANNOT, color=st.INK)

    hs, ls = fig.axes[0].get_legend_handles_labels()
    # The legend cannot live at the top of the canvas: at journal width the
    # three entries are wider than the top margin is tall and they land on the
    # (a)-(c) panel labels. It goes in the band above (d)/(e) instead.
    fig.legend(hs, ls, loc="center", bbox_to_anchor=(0.5, p0.y0 - 0.067),
               ncol=3, frameon=False, fontsize=st.FS_LEGEND,
               handlelength=2.0, columnspacing=1.8, handletextpad=0.5)

    # ---------------- (d) J-V RMSE distributions ---------------------------
    axd = fig.add_subplot(gs[1, 0:3])
    keys = ["full", "le1", "gt1"]
    data = [rm[k] for k in keys]
    labels = ["Full curve\n(0–1.3 V)", "0–1.0 V", "> 1.0 V"]
    fmt = ["%.2f", "%.3f", "%.2f"]
    bp = axd.boxplot(data, positions=[0, 1, 2], widths=0.46,
                     patch_artist=True, showfliers=False,
                     medianprops=dict(color="black", lw=1.1))
    for patch, col in zip(bp["boxes"], [st.OKABE_ITO[0], st.OKABE_ITO[2],
                                        st.OKABE_ITO[3]]):
        patch.set_facecolor(col)
        patch.set_alpha(0.55)
    rng = np.random.default_rng(2026)
    for pos, x in zip([0, 1, 2], data):
        jit = rng.uniform(-0.15, 0.15, len(x))
        axd.plot(pos + jit, x, marker="o", ms=2.2, ls="none", color="#333333",
                 alpha=0.38, zorder=1)
    for i, (m, f) in enumerate(zip([np.median(x) for x in data], fmt)):
        axd.text(i + 0.40, m, f % m, ha="left", va="center",
                 fontsize=st.FS_ANNOT, color=st.INK, zorder=6)
    axd.set_yscale("log")
    axd.set_ylim(0.01, 150)
    axd.set_xlim(-0.6, 3.0)
    axd.set_xticks([0, 1, 2])
    axd.set_xticklabels(labels, fontsize=st.FS_ANNOT)
    axd.set_ylabel(r"J–V RMSE (mA cm$^{-2}$)")
    st.configure_axes(axd)
    axd.text(0.02, 0.97, r"$n$ = 45 per window", transform=axd.transAxes,
             fontsize=st.FS_ANNOT, ha="left", va="top", color=st.INK)
    st.panel_label(axd, "(d)", dx=-0.10)

    # ---------------- (e) device-metric absolute deviations ----------------
    gse = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[1, 3:6],
                                  wspace=1.05, hspace=1.30)
    rng2 = np.random.default_rng(2026)
    for i, key in enumerate(DEV_ORDER):
        r, c = divmod(i, 2)
        ax = fig.add_subplot(gse[r, c])
        a = np.abs(np.asarray(dev[key], float))
        a = a[np.isfinite(a)]
        med = float(np.median(a))
        bp = ax.boxplot([a], positions=[0], widths=0.5, patch_artist=True,
                        showfliers=False,
                        medianprops=dict(color="black", lw=1.1))
        for patch in bp["boxes"]:
            patch.set_facecolor(st.OKABE_ITO[0])
            patch.set_alpha(0.55)
        jit = rng2.uniform(-0.15, 0.15, len(a))
        ax.plot(jit, a, marker="o", ms=2.0, ls="none", color="#333333",
                alpha=0.38, zorder=1)
        ax.set_xlim(-0.5, 0.5)
        ax.set_xticks([])
        ax.set_ylim(0, float(a.max()) * 1.30)
        ax.set_title(DEV_SYM[key], fontsize=st.FS_TITLE, color=st.INK, pad=3.0)
        ax.text(0.98, 0.95, "%.3f" % med, transform=ax.transAxes,
                ha="right", va="top", fontsize=st.FS_ANNOT, color=st.INK)
        if DEV_UNIT[key] != r"$-$":
            ax.set_ylabel(DEV_UNIT[key], fontsize=st.FS_ANNOT)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        st.configure_axes(ax)
        ax.tick_params(axis="y", labelsize=st.FS_TICK)

    pos = gs[1, 3:6].get_position(fig).bounds
    axe = fig.add_axes(pos)
    axe.axis("off")
    axe.patch.set_visible(False)
    axe.text(0.0, 1.14, "(e)", fontsize=st.FS_PANEL, fontweight="bold",
             va="bottom", ha="left", color=st.INK, transform=axe.transAxes)
    axe.text(0.5, -0.055,
             "one predicted curve has no downward zero crossing\n"
             "and is excluded from $|\\Delta V_\\mathrm{oc}|$, "
             "$|\\Delta FF|$ and $|\\Delta \\mathrm{PCE}|$  ($n$ = 44)",
             transform=axe.transAxes, ha="center", va="top",
             fontsize=st.FS_ANNOT, color=st.INK, linespacing=1.5)

    stem = os.path.join(st.FIGDIR, "Figure4"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)


def main():
    for size in ("journal", "large"):
        build(size)

    D = collect()
    rows = []
    for tag, sid, cg in [(CASE_TAG[i], D["cases"][i][0], D["cases"][i][1])
                         for i in range(3)]:
        rows.append(dict(panel="a-c",
                         item="test index %d (%s)" % (sid, tag),
                         value=cg, unit=r"mA cm$^{-2}$", n=1,
                         sample_id_db=D["db_id"][sid],
                         definition="cycle gap = RMSE(decoder, COMSOL); "
                                    "index is a zero-based row index into the "
                                    "frozen test set, not a database Sample_ID",
                         source="decoder_comsol_audit/"
                                "decoder_comsol_metrics_per_sample.csv"))
    for k in ("full", "le1", "gt1"):
        rows.append(dict(panel="d", item="rmse_" + k,
                         value=float(np.median(D["rm"][k])),
                         unit=r"mA cm$^{-2}$", n=len(D["rm"][k]),
                         definition="per-sample J-V RMSE",
                         source="forward_validation_unbiased/"
                                "forward_metrics_per_sample.csv"))
    for key in DEV_ORDER:
        rows.append(dict(panel="e", item="abs_d" + key, value=DEV_MED[key][0],
                         unit={"Jsc": r"mA cm$^{-2}$", "Voc": "V",
                               "FF": "-", "PCE": "percentage points"}[key],
                         n=DEV_MED[key][1],
                         definition="median |predicted - target|; unified "
                                    "continuous linear zero-crossing "
                                    "(v2lib.device_metrics, voc_mode='interp')",
                         source="forward_validation_unbiased/"
                                "comsol_{true,pred}/Sample_*.mat"))
    pd.DataFrame(rows).to_csv(
        os.path.join(st.DATADIR, "Figure4_plotting_values.csv"), index=False)
    print("wrote plotting table")


if __name__ == "__main__":
    main()
