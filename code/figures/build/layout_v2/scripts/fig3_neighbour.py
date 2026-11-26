# -*- coding: utf-8 -*-
"""
fig3_sketch_v2.py — Figure 3 layout sketch, v2 (defects fixed).
================================================================
Reads the v2 source-data tables rather than recomputing, so the drawn figure
and the delivered numbers cannot disagree.

Fixes relative to the phase-1 sketch
------------------------------------
panel (d)  v1 plotted abs(log10(L_i/L_j)) with L already log10, i.e. a ratio of
           logarithms, and placed parameter 0's value against parameter 8's
           label. Both are corrected: the value is abs(L_i - L_j) =
           |log10(theta_i/theta_j)|, and value and label come from the same
           index. The x axis is set from the corrected data instead of a fixed
           0-1.35, so no bar is clipped.
panels (a),(b)  now carry, for each curve, the six paired-coordinate values
           themselves (not only their differences), the physical-current RMSE
           and max|dJ| in mA cm^-2, and an explicit residual direction
           dJ = J_j - J_i. Zero-based test indices identify the two members;
           the database Sample_IDs and the text that duplicated the caption
           were moved out of the figure into SI T6.7 this round, and the
           middle row was resized to the shorter block.
panel (c)  descriptive only: medians with the interquartile range. No p-value
           and no confidence interval appears anywhere, because the tier pairs
           are not independent (see fig3_pair_analysis_v2.py).

Read-only on the frozen project; writes only inside this v2 directory.
"""
import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpecFromSubplotSpec

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_v2 as L
import figstyle as st

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
FIGDIR = os.path.join(OUT, "figures")

C_SHARED = st.OKABE_ITO[0]
C_RATIO = st.OKABE_ITO[3]
C_CURVE1 = st.OKABE_ITO[0]
C_CURVE2 = st.OKABE_ITO[3]

PAIRS = pd.read_csv(os.path.join(DATADIR, "fig3_pairs_v2.csv"))
CASE_SUM = pd.read_csv(os.path.join(DATADIR, "fig3_case_summary.csv"))
CASE_PAR = pd.read_csv(os.path.join(DATADIR, "fig3_case_parameters.csv"))
CASE_CRD = pd.read_csv(os.path.join(DATADIR, "fig3_case_coordinates.csv"))
CASE_CRV = pd.read_csv(os.path.join(DATADIR, "fig3_case_curves.csv"))
RB = pd.read_csv(os.path.join(DATADIR, "fig3_random_baseline_v2.csv")) \
    .set_index("coordinate")["median_absd_random"]

FAM_TAG = [("mobility", "mob.", "mu"), ("lifetime", "life.", "tau"),
           ("DOS", "DOS", "D")]

# Parameter k is drawn in bar slot KS[k]; the tick label list is consumed in the
# same slot order, so the label for slot KS[k] must be PARAM_LABELS[k]. This is
# the single line whose phase-1 version was reversed.
KS = np.arange(9)[::-1]
YLABELS = [st.PARAM_LABELS[k] for k in range(len(L.PARAM_NAMES))]
assert len(YLABELS) == 9


def annotation(tag, i, j, why):
    """Per-curve coordinate listing + physical residual summary for one case.

    Every line is kept short enough to fit inside this case's half of the
    annotation row at journal width; `build` measures the drawn extents and
    fails loudly if any line overflows into the neighbouring case.
    """
    s = CASE_SUM[CASE_SUM["test_index_i"] == i].iloc[0]
    # One head line, not two. The database Sample_IDs and the provenance note
    # that used to sit here ("database IDs, mapping verified") are handover
    # information, not figure content: the same two curves are identified by
    # test index in the figure, and both index and Sample_ID are given in the
    # SI case table (T6.7) and in data_used/fig3_case_summary.csv. The figure
    # keeps what a reader needs to read the panels: the indices, the
    # coordinates and the physical residuals with their units.
    head = "pair %s  —  test index %d / %d  (0-based)" % (tag, i, j)
    body = [r"$d_J$ RMSE = %.3f mA cm$^{-2}$;  $\max|\Delta J|$ = %.3f"
            % (s["physical_rmse_mA_cm2"], s["max_abs_dJ_mA_cm2"]),
            r"   mA cm$^{-2}$ at $V$ = %.2f V;  residual $\Delta J = J_j - J_i$"
            % s["max_abs_dJ_at_V"],
            r"paired coordinates (physical log$_{10}$),  $i$ $\to$ $j$:"]
    for fam, short, _t in FAM_TAG:
        c = CASE_CRD[(CASE_CRD["test_index_i"] == i)
                     & (CASE_CRD["family"] == fam)].iloc[0]
        # the printed pair must be the pair whose difference is tabulated
        assert abs((c["coord_a_i"] - c["coord_a_j"]) - c["delta_a"]) < 1e-12
        assert abs((c["coord_r_i"] - c["coord_r_j"]) - c["delta_r"]) < 1e-12
        body.append("   %-5s $a$ %+7.2f $\\to$ %+7.2f   $r$ %+6.2f $\\to$ %+6.2f"
                    % (short, c["coord_a_i"], c["coord_a_j"],
                       c["coord_r_i"], c["coord_r_j"]))
    # The three closing lines that used to sit here ("all nine parameters
    # differ simultaneously ...", "a small normalised curve distance is not
    # experimental indistinguishability ...") restated the caption and were
    # removed with it; the footer below keeps the two restrictions that have to
    # be readable on the figure itself.
    return head, "\n".join(body)


def measure_overflow(fig, texts, cell):
    """Widest right edge of `texts` minus the right edge of `cell`, in px.

    Positive means the text runs past its own cell and into the neighbouring
    panel. Measured on the real renderer, so this is the layout defect itself
    and not a proxy for it.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    box = cell.get_window_extent(renderer=r)
    worst, which = -1e9, ""
    for t in texts:
        bb = t.get_window_extent(renderer=r)
        if bb.x1 - box.x1 > worst:
            worst, which = bb.x1 - box.x1, t.get_text()[:48]
    return worst, which


def build(size):
    F = L.load_frozen()
    V, J = F["V"], F["J"]
    k_pool = L.tier_k(len(PAIRS), 0.01)

    w = st.set_fig_width(size)
    fig = plt.figure(figsize=(w, w * 1.12))
    # top 0.945 rather than 0.888: the removed suptitle frees the band above the
    # curve panels, and the extra height goes to panels (a)/(b) and their
    # residual strips.
    # left 0.106 rather than 0.092: the two-line rotated ylabel of the residual
    # strips ("J_j - J_i" over "(mA cm^-2)") is the leftmost text on the canvas
    # and at journal width it started 5.5 px outside the figure box, which makes
    # savefig(bbox_inches="tight") quietly widen the delivered PNG. Measured on
    # the live renderer by scripts/qa_layout.py.
    #
    # The middle row is the per-case annotation and it is the real constraint on
    # this layout. At the 7 pt floor the block is now a 1-line bold head plus a
    # 6-line body: measured on the renderer, 15 px + 99 px = 114 px of text,
    # against 178 px before the caption-duplicating lines and the Sample_ID head
    # line were removed. The row was 0.955 of the cell unit (169 px at journal
    # width) for the longer block; it is sized to the shorter one now, and the
    # height that frees (~0.25 unit) goes to the curve panels in row 1 and the
    # (c)/(d) panels in row 3, which were both squeezed by the old ratio. The
    # body is anchored to the measured head height in points rather than to a
    # fixed fraction of the row, so head and body cannot collide at any row
    # height, and the assertion below still checks the block clears row 3.
    gs = fig.add_gridspec(3, 6, left=0.106, right=0.985, top=0.955,
                          bottom=0.185, wspace=1.15, hspace=0.155,
                          height_ratios=[1.300, 0.700, 0.995])

    # one common current range for both curve panels, so the two cases can be
    # compared directly; a little extra room at the bottom for the legend
    allJ = np.concatenate([J[i] for _t, i, _j, _w in L.CASES]
                          + [J[j] for _t, _i, j, _w in L.CASES])
    vmin, vmax = float(allJ.min()), float(allJ.max())
    span = vmax - vmin
    YLIM = (vmin - 0.34 * span, vmax + 0.12 * span)

    ANN = []          # the four annotation texts, checked against (c)/(d) below
    for col0, (tag, i, j, why) in zip((0, 3), L.CASES):
        inner = GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[0, col0:col0 + 3],
                                        hspace=0.0, height_ratios=[1.0, 0.42])
        ax = fig.add_subplot(inner[0])
        axr = fig.add_subplot(inner[1], sharex=ax)
        ax.plot(V, J[i], color=C_CURVE1, lw=1.4, zorder=3,
                label="curve $i$ (index %d)" % i)
        ax.plot(V, J[j], color=C_CURVE2, lw=1.2, ls="--", zorder=3,
                label="curve $j$ (index %d)" % j)
        ax.set_xlim(0.0, 1.3); ax.set_ylim(*YLIM)
        ax.set_yticks([0, 10, 20])
        ax.tick_params(axis="x", labelbottom=False)
        ax.set_ylabel(r"$J$ (mA cm$^{-2}$)")
        ax.legend(loc="lower left", frameon=False, fontsize=st.FS_ANNOT,
                  handlelength=1.4, handletextpad=0.4)
        st.configure_axes(ax)
        st.panel_label(ax, tag)
        ax.text(0.985, 0.965, why, transform=ax.transAxes,
                fontsize=st.FS_ANNOT, color=st.MUTED,
                ha="right", va="top")

        dJ = J[j] - J[i]
        mj = float(np.abs(dJ).max())
        axr.axhline(0.0, color="#bbbbbb", lw=0.7)
        axr.plot(V, dJ, color=C_CURVE2, lw=1.0)
        axr.set_xlim(0.0, 1.3)
        axr.set_ylim(-1.35 * mj, 1.35 * mj)
        axr.set_xticks([0.0, 0.5, 1.0])
        axr.set_yticks([-mj, 0.0, mj])
        axr.set_yticklabels(["%.3g" % -mj, "0", "%.3g" % mj])
        axr.set_xlabel("Voltage (V)", fontsize=st.FS_ANNOT)
        axr.set_ylabel(r"$J_j-J_i$" "\n(mA cm$^{-2}$)", fontsize=st.FS_ANNOT)
        axr.tick_params(axis="both", labelsize=st.FS_TICK - 1.0)
        st.configure_axes(axr)

        # the per-case annotation gets its own space between the strips and the
        # bottom panels, so it cannot land on top of a legend or an axis
        axa = fig.add_subplot(gs[1, col0:col0 + 3]); axa.axis("off")
        head, body = annotation(tag, i, j, why)
        # 0.96 rather than 1.0: the row's top edge sits 29 px under the residual
        # strips, whose x label ("Voltage (V)") hangs ~20 px below its axes, and
        # at 1.0 the bold head grazed it by 3.6 px. The 7 px are free — the
        # block still clears the (c)/(d) row by 23 px.
        th = axa.text(0.0, 0.96, head, transform=axa.transAxes, va="top",
                      ha="left", fontsize=st.FS_ANNOT, color=st.INK,
                      fontweight="bold", linespacing=1.5)
        # The body starts a fixed number of POINTS below the head, not at a
        # fixed fraction of the row. At a fraction the head-to-body gap scales
        # with the row while the head does not, so a fraction that clears the
        # head at one row height buries it at another; this way the two cannot
        # collide whatever the row height becomes.
        fig.canvas.draw()
        _r0 = fig.canvas.get_renderer()
        row_px = axa.get_window_extent(renderer=_r0).height
        head_px = th.get_window_extent(renderer=_r0).height
        tb = axa.text(0.0, 0.96 - (head_px + 5.0) / row_px, body,
                      transform=axa.transAxes, va="top",
                      ha="left", fontsize=st.FS_ANNOT, color=st.INK,
                      linespacing=1.6)
        ANN.extend([th, tb])
        over, which = measure_overflow(fig, [th, tb], axa)
        print("  [fit] case %s annotation overflow %+.1f px  (widest: %s)"
              % (tag, over, which))
        assert over <= 0.0, (
            "case %s annotation runs %+.1f px past its half of the figure; "
            "shorten the line starting %r" % (tag, over, which))

    # ---------------- (c) descriptive population comparison ---------------
    axc = fig.add_subplot(gs[2, 0:3])
    x = np.arange(3); bw = 0.36
    med_a, iqr_a, med_r, iqr_r = [], [], [], []
    for fam, _s, tag in FAM_TAG:
        for cid, sink_m, sink_q in (("a_" + tag, med_a, iqr_a),
                                    ("r_" + tag, med_r, iqr_r)):
            v = (PAIRS["absd_" + cid] / RB[cid]).values
            sink_m.append(float(np.median(v)))
            sink_q.append([float(np.percentile(v, 25)),
                           float(np.percentile(v, 75))])
    c_lab = []
    for xs, ms, qs, col in ((x - bw / 2, med_a, iqr_a, C_SHARED),
                            (x + bw / 2, med_r, iqr_r, C_RATIO)):
        axc.bar(xs, ms, bw, color=col, edgecolor="white", lw=0.5, zorder=3,
                label=("Shared scale $a$" if col == C_SHARED
                       else "Electron–hole log-ratio $r$"))
        axc.errorbar(xs, ms, yerr=[[m - q[0] for m, q in zip(ms, qs)],
                                   [q[1] - m for m, q in zip(ms, qs)]],
                     fmt="none", ecolor=st.INK, elinewidth=0.7, capsize=1.8,
                     zorder=4)
        for xi, m, q in zip(xs, ms, qs):
            # above the bar and above the interquartile whisker cap, on a white
            # patch so the value stays legible where the two coincide
            c_lab.append(
                axc.text(xi, max(m, q[1]) + 0.035, "%.2f" % m, ha="center",
                         va="bottom", fontsize=st.FS_ANNOT, color=st.INK,
                         zorder=6,
                         bbox=dict(boxstyle="square,pad=0.05", fc="white",
                                   ec="none", alpha=0.85)))
    axc.axhline(1.0, color=st.MUTED, lw=1.0, ls="--", zorder=4)
    axc.text(-0.55, 1.04, "random pairs (baseline = 1)", ha="left", va="bottom",
             fontsize=st.FS_ANNOT, color=st.MUTED)
    axc.set_xticks(x)
    axc.set_xticklabels([f for f, _s, _t in FAM_TAG], fontsize=st.FS_ANNOT)
    # the y range is taken from the data so that no interquartile whisker is
    # clipped and every value label sits inside the frame. The phase-1 sketch
    # fixed this at 1.62, which cut the lifetime log-ratio whisker at 1.75 and
    # pushed its label out of the axes onto the (d) panel letter.
    ALL_MQ = list(zip(med_a + med_r, iqr_a + iqr_r))
    whisk_top = max(q[1] for _m, q in ALL_MQ)
    axc.set_xlim(-0.6, 2.6)
    axc.set_ylim(0, whisk_top * 1.20)
    assert whisk_top <= axc.get_ylim()[1], "whisker clipped"
    axc.set_yticks([0.0, 0.5, 1.0, 1.5])
    # The pair set is stated on the panel itself, with the count read from the
    # table rather than typed: "all pairs" and "a tier subset" are different
    # claims, and the phase-1 sketch left the reader to guess which one (c) used.
    axc.set_ylabel("Median  $|\\Delta$coord$|$ / random median\n"
                   "(all %s corrected undirected pairs;\n"
                   "whiskers: interquartile range)" % "{:,}".format(len(PAIRS)),
                   fontsize=st.FS_ANNOT)
    # one row of two entries, so the key stays clear of the tallest value label
    leg_c = axc.legend(loc="upper left", frameon=False, fontsize=st.FS_ANNOT,
                       handlelength=1.2, handletextpad=0.5, ncol=2,
                       columnspacing=1.1, labelspacing=0.25, borderpad=0.1,
                       borderaxespad=0.2)
    st.configure_axes(axc)
    t_c = st.panel_label(axc, "(c)", dx=-0.175)

    # ---------------- (d) all nine parameter differences, corrected --------
    axd = fig.add_subplot(gs[2, 3:6])
    ks = KS
    bh = 0.36
    vmax = 0.0
    for tag, i, j, _why in L.CASES:
        sub = CASE_PAR[CASE_PAR["test_index_i"] == i]
        # value and label come from the SAME index: vals[k] belongs to param k
        vals = np.array([float(sub[sub["parameter"] == p]
                               ["abs_delta_log10"].iloc[0])
                         for p in L.PARAM_NAMES])
        vmax = max(vmax, float(vals.max()))
        axd.barh(ks + (bh / 2 if tag == "(a)" else -bh / 2), vals, bh,
                 color=(C_CURVE1 if tag == "(a)" else C_CURVE2),
                 edgecolor="white", linewidth=0.4, label="pair %s" % tag)
    axd.set_yticks(ks)
    axd.set_yticklabels(YLABELS, fontsize=st.FS_ANNOT)
    axd.set_xlabel(r"$|\log_{10}(\theta_i/\theta_j)|$   (log$_{10}$ units)",
                   fontsize=st.FS_ANNOT)
    axd.set_xlim(0, vmax * 1.06)      # set from the corrected data, no clipping
    axd.legend(loc="lower right", frameon=False, fontsize=st.FS_ANNOT)
    st.configure_axes(axd)
    t_d = st.panel_label(axd, "(d)", dx=-0.32)

    # ---- (c)/(d) layout check: labels inside the frame, clear of the legend,
    # ---- and the (d) panel letter clear of (c)'s value labels ---------------
    fig.canvas.draw()
    rr = fig.canvas.get_renderer()
    cbox = axc.get_window_extent(renderer=rr)
    lbox = leg_c.get_window_extent(renderer=rr)
    worst_in, worst_leg, worst_d = 0.0, 0.0, 0.0
    for t in c_lab:
        bb = t.get_window_extent(renderer=rr)
        worst_in = max(worst_in, bb.x1 - cbox.x1, cbox.x0 - bb.x0,
                       bb.y1 - cbox.y1)
        worst_leg = max(worst_leg, min(bb.x1, lbox.x1) - max(bb.x0, lbox.x0)
                        if (min(bb.y1, lbox.y1) - max(bb.y0, lbox.y0)) > 0 else 0.0)
    dbb = t_d.get_window_extent(renderer=rr)
    for t in c_lab:
        bb = t.get_window_extent(renderer=rr)
        if (min(bb.y1, dbb.y1) - max(bb.y0, dbb.y0)) > 0:
            worst_d = max(worst_d, min(bb.x1, dbb.x1) - max(bb.x0, dbb.x0))
    print("  [fit] (c) labels: %+.1f px outside the frame, %+.1f px into the "
          "legend, %+.1f px into the (d) letter" % (worst_in, worst_leg, worst_d))
    assert worst_in <= 0.0, "a (c) value label sits outside the axes"
    assert worst_leg <= 0.0, "a (c) value label overlaps the legend"
    assert worst_d <= 0.0, "the (d) panel letter collides with a (c) label"

    # The per-case annotation above must stop before the (c)/(d) row starts.
    # qa_layout.py caught this one as a 646 px^2 text-on-text overlap between
    # the annotation body and (c)'s legend; measuring against the panel boxes
    # instead of the legend text makes the check independent of where in the
    # panel the legend happens to sit.
    dbox = axd.get_window_extent(renderer=rr)
    worst_ann = -1e9
    for t in ANN:
        bb = t.get_window_extent(renderer=rr)
        worst_ann = max(worst_ann, max(b.y1 - bb.y0 for b in (cbox, dbox)))
    print("  [fit] annotation block: %+.1f px clear of the (c)/(d) row"
          % (-worst_ann))
    assert worst_ann <= 0.0, (
        "the per-case annotation runs %.1f px into the (c)/(d) row; raise the "
        "middle height_ratio" % worst_ann)

    # Two lines, not four. The full selection rule, the sample counts of every
    # tier and the independence caveat belong to the caption and the SI; what
    # has to be readable on the figure itself is only that these two cases are
    # chosen by a rule rather than drawn at random, and that panel (c) is
    # descriptive. Everything else was moved out this round.
    fig.text(0.5, 0.128,
             "Cases (a), (b): deliberately extreme members of the closest 1%% "
             "of corrected pairs ($n$ = %d), selected by the stated rule —\n"
             "not randomly drawn typical cases. Panel (c): descriptive only; "
             "the tier pairs share samples, so no p-value and no confidence "
             "interval is reported." % k_pool,
             ha="center", va="top", fontsize=st.FS_ANNOT,
             color=st.MUTED, linespacing=1.55)

    # No figure-level title: the manuscript caption names the figure, the sample
    # count and the pairing rule. The v2 preview's one-line suptitle repeated
    # all three.
    stem = os.path.join(FIGDIR, "Figure3"
                        + ("_large" if size == "large" else ""))
    st.save_fig(fig, stem)
    print("wrote:", stem)


def main():
    build("journal")
    build("large")
    # ---- value/label alignment proof ------------------------------------
    # Parameter k is drawn at slot KS[k] and the tick at KS[k] carries
    # YLABELS[k], so the drawn value and the drawn label share the index k.
    print("  slot -> (parameter drawn there, label drawn there):")
    for k in range(9):
        slot = int(KS[k])
        lab_at_slot = YLABELS[int(np.where(KS == slot)[0][0])]
        assert lab_at_slot == st.PARAM_LABELS[k], (k, lab_at_slot)
        print("     y=%-2d  %-12s  %s" % (slot, L.PARAM_NAMES[k], lab_at_slot))
    for tag, i, _j, _why in L.CASES:
        sub = CASE_PAR[CASE_PAR["test_index_i"] == i]
        v = [float(sub[sub["parameter"] == p]["abs_delta_log10"].iloc[0])
             for p in L.PARAM_NAMES]
        k = int(np.argmax(v))
        assert YLABELS[k] == st.PARAM_LABELS[k]
        print("  %s argmax value %.3f belongs to %s, drawn at y=%d, labelled %s"
              % (tag, v[k], L.PARAM_NAMES[k], int(KS[k]), YLABELS[k]))
    print("  panel (d) x limit = 0 .. %.3f (from corrected data)"
          % (float(CASE_PAR["abs_delta_log10"].max()) * 1.06))


if __name__ == "__main__":
    main()
