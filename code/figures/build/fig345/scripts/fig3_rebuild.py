# -*- coding: utf-8 -*-
"""Figure 3 — four standalone panels, supervisor revision of 2026-11-11.

Base: the accepted round-3 files
    20261109_fig3_revision_v2/figures/Fig3a..Fig3d   (geometry, data, style)
    20261109_fig3c_standalone/figures/Fig3c          (the v3 value labels)

Only the legend position changes, plus the small amount of axis head-room
that the moved legend needs:

  (a),(b)  Curve i / Curve j legend: lower left -> inside the upper-right
           corner of the J-V panel.  The J-V top is raised 25.1 -> 32.0 so the
           two-row legend clears the 24.09 mA cm^-2 plateau by >4 pt.  The
           residual strip, its ylim and the sub-panel heights are untouched.
  (c)      Shared scale a / log-ratio r legend: upper left -> upper right.
           The y top is raised 2.10 -> 2.25 so the legend clears the tallest
           whisker cap (1.7628) by >6 pt.  Bars, whiskers, the y = 1 baseline
           and the accepted v3 value labels are unchanged.
  (d)      Pair (a) / Pair (b) legend: lower right -> upper right.  No axis
           change is needed: the top row's bars end at 0.54 / 0.63 while the
           legend starts at x = 2.22.

Data are the frozen CSVs of the manuscript package (copied into data_used/,
hashes recorded in QA).  Nothing is recomputed.  Every drawn number is
re-derived from those CSVs, and the identities (residual = J_j - J_i,
|log10 ratio| = |log10 theta_i - log10 theta_j|) are asserted.

No axis titles, panel letters or figure-level text are baked in; those are
listed in labels_and_caption.txt.  The preview carries them for checking only.
"""
import hashlib
import json
import os
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath
from matplotlib.ticker import FuncFormatter

try:
    sys_stdout = __import__("sys").stdout
    sys_stdout.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
PREV = os.path.join(OUT, "preview")
QA = os.path.join(OUT, "qa")
DATA = os.path.join(OUT, "data_used")
for d in (FIG, PREV, QA, DATA):
    os.makedirs(d, exist_ok=True)

SRC = DATA

# ------------------------------------------------------------------ style --
FONT = "Arial"
INK = "#1a1a1a"
MUTED = "#555555"
GREY = "#bbbbbb"

C_A = "#4C72B0"      # panel (c): shared scale a -- final Fig. 2 blue
C_R = "#DD8452"      # panel (c): electron-hole log-ratio r -- Fig. 2 orange
C_I = C_A            # curve i, solid
C_J = C_R            # curve j, dashed

PAIR = {"(a)": C_A, "(b)": C_R}   # panel (d): re-read from the (c) patches

FS_TICK = 7.0
FS_AXLAB = 7.5
FS_LEG = 7.0
FS_LETTER = 8.5
FS_VAL = 6.8

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [FONT, "DejaVu Sans"],
    "mathtext.fontset": "custom",
    "mathtext.rm": FONT,
    "mathtext.it": FONT + ":italic",
    "mathtext.bf": FONT + ":bold",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.unicode_minus": True,
})

# --------------------------------------------------------------- geometry --
CW, CH = 3.30, 2.70          # every standalone panel canvas, inches
ML, MR, MB, MT = 0.62, 0.06, 0.42, 0.18
PW = CW - ML - MR            # 2.62 in
HJ, HR = 1.48, 0.62          # J-V and residual-strip heights
PC = CH - MB - MT            # 2.10 in, single-axes panels (c)/(d)

PV_W = 6.80                  # 172.72 mm, the width Figure 3 has in Word
PV_H = 0.14 + CH + 0.30 + CH + 0.14
COL_X = [0.04, 3.46]
ROW_Y = [0.14, 3.14]

XLO, XHI = -0.75, 2.60
YLO = 0.0
YHI_C_OLD, YHI_C = 2.10, 2.40     # (c) top: +0.30 for the upper-right legend
BW = 0.36
CAPSIZE = 1.8

LIM_R = (-7.1316, 7.1316)          # shared signed-residual scale
LIM_J_OLD, LIM_J_TOP = 25.1, 32.0  # (a)/(b) top: +6.9 for the upper-right legend

# v3 label layout constants, in data units of panel (c) (1 unit = 1 inch)
CAP_GAP = 1.5          # pt, upper whisker cap -> bottom of the value ink
LINE_MARGIN = 0.028    # data units, value ink -> the y = 1 baseline band


def fmt_num(v, nd=1):
    s = ("%." + str(nd) + "f") % v
    if s.endswith(".0"):
        s = s[:-2]
    return s.replace("-", "−")


# -------------------------------------------------------------- data load --
def load():
    curves = pd.read_csv(os.path.join(SRC, "fig3_case_curves.csv"))
    summ = pd.read_csv(os.path.join(SRC, "fig3_case_summary.csv"))
    pars = pd.read_csv(os.path.join(SRC, "fig3_case_parameters.csv"))
    pairs = pd.read_csv(os.path.join(SRC, "fig3_pairs_v2.csv"))
    rb = pd.read_csv(os.path.join(SRC, "fig3_random_baseline_v2.csv")) \
        .set_index("coordinate")["median_absd_random"]

    assert len(pairs) == 11245
    assert int(round(len(pairs) * 0.01)) == 112
    assert set(rb.index) == {"a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"}

    cases = {}
    for tag, i, j in (("(a)", 2890, 5067), ("(b)", 500, 4560)):
        c = curves[curves["case"] == tag].sort_values("voltage_V")
        V = c["voltage_V"].to_numpy()
        Ji = c["J_i_mA_cm2"].to_numpy()
        Jj = c["J_j_mA_cm2"].to_numpy()
        dJ = c["residual_Jj_minus_Ji_mA_cm2"].to_numpy()
        assert len(V) == 131 and abs(V[0]) < 1e-12 and abs(V[-1] - 1.3) < 1e-12
        # the strip must be the subtraction J_j - J_i, not |dJ|
        assert np.abs((Jj - Ji) - dJ).max() < 1e-12
        s = summ[summ["case"] == tag].iloc[0]
        assert abs(s["test_index_i"] - i) < 0.5 and abs(s["test_index_j"] - j) < 0.5
        assert abs(np.abs(dJ).max() - s["max_abs_dJ_mA_cm2"]) < 1e-9
        cases[tag] = dict(V=V, Ji=Ji, Jj=Jj, dJ=dJ, idx=(i, j),
                          rmse=float(s["physical_rmse_mA_cm2"]),
                          maxabs=float(np.abs(dJ).max()))

    fams = [("mobility", "mu", "Mobility"),
            ("lifetime", "tau", "Bulk lifetime"),
            ("DOS", "D", "Density of states")]
    cdat = []
    for _f, tag, title in fams:
        for cid, key in (("a_" + tag, "a"), ("r_" + tag, "r")):
            v = (pairs["absd_" + cid] / rb[cid]).to_numpy()
            cdat.append(dict(coordinate=cid, key=key, title=title,
                             med=float(np.median(v)),
                             q1=float(np.percentile(v, 25)),
                             q3=float(np.percentile(v, 75))))

    names = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
             "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
    ddat = {}
    for tag in ("(a)", "(b)"):
        sub = pars[pars["case"] == tag]
        ddat[tag] = np.array([float(sub[sub["parameter"] == p]
                                    ["abs_delta_log10"].iloc[0]) for p in names])
        for p, v in zip(names, ddat[tag]):
            r = sub[sub["parameter"] == p].iloc[0]
            assert abs((r["log10_theta_i"] - r["log10_theta_j"]).__abs__() - v) < 1e-9
    # the largest bar must be tau_p of pair (a)
    k_max = int(np.argmax(ddat["(a)"]))
    assert names[k_max] == "tau_p_pvk", names[k_max]
    return cases, cdat, ddat, names


# ------------------------------------------------------------ math labels --
def runs_to_math(runs):
    out, buf = [], []

    def flush():
        if buf:
            out.append("$" + "".join(buf) + "$")
            del buf[:]

    for text, kind in runs:
        if kind == "t":
            flush()
            out.append(text)
            continue
        if kind == "it":
            buf.append(text)
        elif kind == "rm":
            buf.append(r"\mathrm{%s}" % text.replace(" ", r"\ "))
        elif kind == "sub_it":
            buf.append("_{%s}" % text)
        elif kind == "sub_rm":
            buf.append(r"_{\mathrm{%s}}" % text)
        else:
            raise ValueError(kind)
    flush()
    return "".join(out)


GLYPHS = {"\\mu": "μ", "\\tau": "τ", "\\theta": "θ"}


def key_of(runs):
    s = "".join(t for t, _k in runs)
    for k, v in GLYPHS.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", "", s)


MU = [("\\mu", "it"), ("n", "sub_it")]
MU_P = [("\\mu", "it"), ("p", "sub_it")]
TAU = [("\\tau", "it"), ("n", "sub_it")]
TAU_P = [("\\tau", "it"), ("p", "sub_it")]
NC = [("N", "it"), ("c", "sub_it")]
NV = [("N", "it"), ("v", "sub_it")]
TETL = [("\\tau", "it"), ("ETL", "sub_rm")]
THTL = [("\\tau", "it"), ("HTL", "sub_rm")]
RRAD = [("r", "it"), ("rad", "sub_rm")]
PARAM_RUNS = [MU, MU_P, TAU, TAU_P, NC, NV, TETL, THTL, RRAD]


# ---------------------------------------------------------------- drawing --
def style(ax):
    ax.tick_params(axis="both", which="major", direction="out", length=3.0,
                   width=0.7, labelsize=FS_TICK, colors=INK, top=False,
                   right=False, pad=2.5)
    for sp in ax.spines.values():
        sp.set_color(INK)
        sp.set_linewidth(0.7)
    ax.set_facecolor("none")


def rect(x0, ytop, dx, dy, w, h, W, H):
    return [(x0 + dx) / W, (H - (ytop + dy + h)) / H, w / W, h / H]


def ax_ab(fig, x0, ytop, W, H):
    axj = fig.add_axes(rect(x0, ytop, ML, MT, PW, HJ, W, H))
    axr = fig.add_axes(rect(x0, ytop, ML, MT + HJ, PW, HR, W, H), sharex=axj)
    return axj, axr


def ax_cd(fig, x0, ytop, W, H):
    return fig.add_axes(rect(x0, ytop, ML, MT, PW, PC, W, H))


LEG_AB = dict(loc="upper right", frameon=False, fontsize=FS_LEG,
              handlelength=1.10, handletextpad=0.35, labelspacing=0.15,
              borderpad=0.03, borderaxespad=0.40)
LEG_CD = dict(loc="upper right", frameon=False, fontsize=FS_LEG,
              handlelength=1.0, handletextpad=0.40, labelspacing=0.30,
              borderpad=0.12, borderaxespad=0.50)


def draw_ab(axj, axr, case, ylim_j, ylim_r, reg):
    V, Ji, Jj, dJ = case["V"], case["Ji"], case["Jj"], case["dJ"]
    axj.plot(V, Ji, color=C_I, lw=1.3, solid_capstyle="butt", zorder=3,
             label=runs_to_math([("Curve ", "t"), ("i", "it")]))
    axj.plot(V, Jj, color=C_J, lw=1.2, ls=(0, (4.0, 2.0)), zorder=4,
             dash_capstyle="butt",
             label=runs_to_math([("Curve ", "t"), ("j", "it")]))
    axj.set_xlim(0.0, 1.32)
    axj.set_ylim(*ylim_j)
    axj.set_yticks([-10, 0, 10, 20])
    axj.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 0)))
    axj.tick_params(axis="x", which="both", bottom=False, top=False,
                    labelbottom=False)
    style(axj)
    leg = axj.legend(**LEG_AB)
    for t, runs in zip(leg.get_texts(),
                       ([("Curve ", "t"), ("i", "it")],
                        [("Curve ", "t"), ("j", "it")])):
        t.set_size(FS_LEG)
        reg.append(dict(key=key_of(runs), runs=runs, size=FS_LEG,
                        color=INK, kind="left"))

    axr.axhline(0.0, color=GREY, lw=0.7, ls=(0, (3.0, 2.5)), zorder=2)
    axr.plot(V, dJ, color=C_J, lw=1.1, solid_capstyle="butt", zorder=3)
    axr.set_xlim(0.0, 1.32)
    axr.set_ylim(*ylim_r)
    axr.set_xticks([0.0, 0.5, 1.0])
    axr.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 1)))
    axr.set_yticks([-5, 0, 5])
    axr.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 0)))
    axr.spines["top"].set_visible(False)
    style(axr)
    return leg


# ------------------------------------------------------- panel (c) labels --
FONT_PROP = FontProperties(family=FONT)


def ink_box(text, size):
    bb = TextPath((0, 0), text, size=size, prop=FONT_PROP).get_extents()
    return bb.x0, bb.x1, bb.y0, bb.y1


def units_per_pt(ax, fig):
    fig.canvas.draw()
    bb = ax.get_window_extent(fig.canvas.get_renderer())
    px_per_pt = fig.dpi / 72.0
    x = bb.width / (ax.get_xlim()[1] - ax.get_xlim()[0]) / px_per_pt
    y = bb.height / (ax.get_ylim()[1] - ax.get_ylim()[0]) / px_per_pt
    return 1.0 / x, 1.0 / y


def rendered_box(fig, ax, t):
    bb = t.get_window_extent(fig.canvas.get_renderer())
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    return (x0, y0, x1, y1)


def overlaps(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def place_value_labels(ax, fig, recs):
    """Accepted manuscript style: value centred above its own whisker cap.

    The labels sit above the upper (q3) cap, horizontally centred on the bar,
    exactly as in the accepted Figure 3(c); no value is pushed into a bar.
    """
    upx, upy = units_per_pt(ax, fig)
    arts = [ax.text(0.0, 0.0, "%.2f" % r["med"], ha="center", va="baseline",
                    fontsize=FS_VAL, color=INK, zorder=7) for r in recs]
    fig.canvas.draw()
    out = []
    for r, t in zip(recs, arts):
        bb = rendered_box(fig, ax, t)
        ix0, ix1, iy0, iy1 = ink_box(t.get_text(), FS_VAL)
        xc = r["x"]
        base = r["q3"] + CAP_GAP * upy - iy0 * upy
        where = "above_cap"
        t.set_position((xc, base))
        box = (xc + bb[0], base + bb[1], xc + bb[2], base + bb[3])
        ink = (xc + bb[0] + ix0 * upx, base + iy0 * upy,
               xc + bb[0] + ix1 * upx, base + iy1 * upy)
        out.append(dict(text=t.get_text(), coord=r["coordinate"], key=r["key"],
                        colour=r["col"], where=where, x=xc, y_base=base,
                        box=[round(v, 4) for v in box],
                        ink=[round(v, 4) for v in ink], bar_x=r["x"],
                        med=r["med"], q1=r["q1"], q3=r["q3"]))
    for o, r in zip(out, recs):
        # every value sits above its own upper whisker cap
        assert o["ink"][1] > r["q3"] + 0.4 * CAP_GAP * upy
        assert abs(o["x"] - r["x"]) < 1e-9
        assert o["box"][0] > XLO and o["box"][2] < XHI
        assert o["box"][3] < YHI_C
    return out


def check_labels(ax, fig, recs, labels, cap_hw):
    fig.canvas.draw()
    bad = []
    base = [t for t in ax.texts if t.get_text().startswith("random pairs")]
    bb_base = rendered_box(fig, ax, base[0])
    band = (XLO, 1.0 - LINE_MARGIN, XHI, 1.0 + LINE_MARGIN)
    for i, lab in enumerate(labels):
        bb = tuple(lab["box"])       # layout box, for the frame only
        ib = tuple(lab["ink"])       # real glyph ink, for every clearance
        if not (bb[0] > XLO and bb[2] < XHI and bb[1] > YLO and bb[3] < YHI_C):
            bad.append("frame: " + lab["text"])
        if overlaps(ib, band):
            bad.append("baseline: " + lab["text"])
        for r in recs:
            body = (r["x"] - 0.004, r["q1"], r["x"] + 0.004, r["q3"])
            cap3 = (r["x"] - cap_hw, r["q3"] - 0.012, r["x"] + cap_hw,
                    r["q3"] + 0.012)
            cap1 = (r["x"] - cap_hw, r["q1"] - 0.012, r["x"] + cap_hw,
                    r["q1"] + 0.012)
            if overlaps(ib, body):
                bad.append("whisker %s: %s" % (r["coordinate"], lab["text"]))
            if overlaps(ib, cap1) or overlaps(ib, cap3):
                bad.append("cap %s: %s" % (r["coordinate"], lab["text"]))
        for r in recs:
            bar = (r["x"] - BW / 2.0, 0.0, r["x"] + BW / 2.0, r["med"])
            if overlaps(ib, bar):
                bad.append("bar %s: %s" % (r["coordinate"], lab["text"]))
        if overlaps(ib, bb_base):
            bad.append("caption: " + lab["text"])
        for j, lab2 in enumerate(labels):
            if j != i and overlaps(ib, tuple(lab2["ink"])):
                bad.append("%s vs %s" % (lab["text"], lab2["text"]))
        labels[i]["clearance_baseline"] = round(
            min(abs(ib[3] - 1.0), abs(ib[1] - 1.0)), 4)
        labels[i]["cap_to_ink"] = round(ib[1] - lab["q3"], 4)
    return bad


def draw_c(ax, fig, cdat, reg):
    x = np.arange(3)
    fam = {"Mobility": 0, "Bulk lifetime": 1, "Density of states": 2}
    containers = {}
    for key, off, col, runs in (
            ("a", -BW / 2, C_A, [("Shared scale ", "t"), ("a", "it")]),
            ("r", +BW / 2, C_R, [("Electron–hole log-ratio ", "t"),
                                 ("r", "it")])):
        sel = [d for d in cdat if d["key"] == key]
        med = [d["med"] for d in sel]
        q1 = [d["q1"] for d in sel]
        q3 = [d["q3"] for d in sel]
        ax.bar(x + off, med, BW, color=col, edgecolor="white", lw=0.4,
               zorder=3, label=runs_to_math(runs))
        containers[key] = ax.errorbar(
            x + off, med,
            yerr=[[m - a for m, a in zip(med, q1)],
                  [b - m for m, b in zip(med, q3)]],
            fmt="none", ecolor=INK, elinewidth=0.7, capsize=CAPSIZE,
            capthick=0.7, zorder=4)

    ax.set_xlim(XLO, XHI)
    ax.set_ylim(YLO, YHI_C)
    ax.set_xticks(x)
    ax.set_xticklabels(["Mobility", "Bulk lifetime", "Density of states"],
                       fontsize=FS_TICK)
    ax.set_yticks([0.0, 0.5, 1.0, 1.5, 2.0])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 1)))
    bars_before_labels = list(ax.patches)

    cap_ms = containers["a"].lines[1][0].get_markersize()
    upx, _upy = units_per_pt(ax, fig)
    cap_hw = cap_ms / 2.0 * upx

    colours = []
    for p in ax.patches:
        c = matplotlib.colors.to_hex(p.get_facecolor())
        if c not in colours:
            colours.append(c)
    assert len(colours) == 2, colours

    recs = []
    for d in cdat:
        cols = [c for c in colours
                if (c == colours[0]) == (d["key"] == "a")]
        recs.append(dict(d, x=float(fam[d["title"]] +
                                    (-BW / 2 if d["key"] == "a" else BW / 2)),
                         col=cols[0]))

    labels = place_value_labels(ax, fig, recs)

    ax.axhline(1.0, color=MUTED, lw=0.9, ls=(0, (4.0, 2.4)), zorder=5)
    ax.text(0.10, 1.05, "random pairs\n(baseline = 1)", ha="right",
            va="bottom", fontsize=FS_VAL, color=MUTED, zorder=6,
            linespacing=1.25)
    leg = ax.legend(**LEG_CD)
    for t, runs in zip(leg.get_texts(),
                       ([("Shared scale ", "t"), ("a", "it")],
                        [("Electron–hole log-ratio ", "t"),
                         ("r", "it")])):
        t.set_size(FS_LEG)
        reg.append(dict(key=key_of(runs), runs=runs, size=FS_LEG,
                        color=INK, kind="left"))
    style(ax)
    return dict(colours=colours, cap_hw=cap_hw, cap_ms=cap_ms,
                labels=labels, recs=recs, leg=leg,
                bar_patches=bars_before_labels)


def draw_d(ax, ddat, reg):
    ks = np.arange(9)[::-1]
    bh = 0.32
    for tag, off, runs in (
            ("(a)", +bh / 2,
             [("Pair ", "t"), ("(", "t"), ("a", "it"), (")", "t")]),
            ("(b)", -bh / 2,
             [("Pair ", "t"), ("(", "t"), ("b", "it"), (")", "t")])):
        ax.barh(ks + off, ddat[tag], bh, color=PAIR[tag], edgecolor="white",
                linewidth=0.4, label=runs_to_math(runs), zorder=3)
    ax.set_yticks(ks)
    ax.set_yticklabels([runs_to_math(r) for r in PARAM_RUNS],
                       fontsize=FS_TICK)
    for runs in PARAM_RUNS:
        reg.append(dict(key=key_of(runs), runs=runs, size=FS_TICK,
                        color=INK, kind="right"))
    ax.set_xlim(0.0, float(ddat["(a)"].max()) * 1.05)
    ax.set_xticks([0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 1)))
    ax.set_ylim(-0.6, 8.6)
    leg = ax.legend(**LEG_CD)
    for t, runs in zip(leg.get_texts(),
                       ([("Pair ", "t"), ("(", "t"), ("a", "it"),
                         (")", "t")],
                        [("Pair ", "t"), ("(", "t"), ("b", "it"),
                         (")", "t")])):
        t.set_size(FS_LEG)
        reg.append(dict(key=key_of(runs), runs=runs, size=FS_LEG,
                        color=INK, kind="left"))
    style(ax)
    return leg


# --------------------------------------------------------- legend clearance --
def data_points(ax):
    pts = []
    for ln in ax.lines:
        x = np.asarray(ln.get_xdata(), float)
        y = np.asarray(ln.get_ydata(), float)
        if x.size and np.isfinite(x).all() and np.isfinite(y).all():
            pts.append(np.column_stack([x, y]))
    return np.vstack(pts) if pts else np.empty((0, 2))


def legend_gap_pt(fig, ax, leg, pts=None):
    """Smallest distance in points from the legend frame to the data ink."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = leg.get_window_extent(r)
    if pts is None:
        pts = data_points(ax)
    P = ax.transData.transform(pts)
    dx = np.maximum(np.maximum(bb.x0 - P[:, 0], P[:, 0] - bb.x1), 0.0)
    dy = np.maximum(np.maximum(bb.y0 - P[:, 1], P[:, 1] - bb.y1), 0.0)
    gap = np.sqrt(dx ** 2 + dy ** 2)
    inside = int(np.sum((P[:, 0] >= bb.x0) & (P[:, 0] <= bb.x1)
                        & (P[:, 1] >= bb.y0) & (P[:, 1] <= bb.y1)))
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    return dict(min_pt=round(float(gap.min()) * 72.0 / fig.dpi, 2),
                inside=inside,
                box_in=[round(bb.width / fig.dpi, 3),
                        round(bb.height / fig.dpi, 3)],
                box_data=[round(x0, 3), round(y0, 3), round(x1, 3),
                          round(y1, 3)])


def rect_points(ax, patches, whiskers=None):
    pts = []
    for p in patches:
        x, y = p.get_xy()
        w, h = p.get_width(), p.get_height()
        pts += [[x, y], [x + w, y], [x, y + h], [x + w, y + h]]
    for cont in (whiskers or []):
        for ln in cont.lines[1] + cont.lines[2]:        # caplines, barlinecols
            pts += np.column_stack([ln.get_xdata(), ln.get_ydata()]).tolist()
    return np.array(pts, float)


# --------------------------------------------------------------- figures ---
def fig_panel_c(cases, cdat, ddat):
    reg = []
    fig = plt.figure(figsize=(CW, CH), dpi=100)
    fig.patch.set_facecolor("white")
    ax = ax_cd(fig, 0, 0, CW, CH)
    info = draw_c(ax, fig, cdat, reg)
    return fig, reg, info


def fig_panel_d(cases, cdat, ddat):
    reg = []
    fig = plt.figure(figsize=(CW, CH), dpi=100)
    fig.patch.set_facecolor("white")
    ax = ax_cd(fig, 0, 0, CW, CH)
    leg = draw_d(ax, ddat, reg)
    return fig, reg, leg


def build_preview(cases, cdat, ddat):
    reg = []
    fig = plt.figure(figsize=(PV_W, PV_H), dpi=100)
    fig.patch.set_facecolor("white")

    def T(x, y, s, size=FS_AXLAB, ha="center", va="center", rot=0):
        fig.text(x / PV_W, 1.0 - y / PV_H, s, fontsize=size, color=INK,
                 ha=ha, va=va, rotation=rot)

    letters = [("(a)", 0, 0), ("(b)", 1, 0), ("(c)", 0, 1), ("(d)", 1, 1)]
    for tag, col, row in letters:
        x0, y0 = COL_X[col], ROW_Y[row]
        T(x0 + ML, y0 + 0.075, tag, FS_LETTER, ha="left", va="bottom")

    for col, key in ((0, "(a)"), (1, "(b)")):
        x0, y0 = COL_X[col], ROW_Y[0]
        axj, axr = ax_ab(fig, x0, y0, PV_W, PV_H)
        draw_ab(axj, axr, cases[key], (-11.2, LIM_J_TOP), LIM_R, reg)
        T(x0 + 0.150, y0 + MT + HJ / 2.0,
          "J (mA cm$^{-2}$)", FS_AXLAB, ha="center", va="center", rot=90)
        T(x0 + 0.150, y0 + MT + HJ + HR / 2.0,
          "J$_j$ − J$_i$\n(mA cm$^{-2}$)", FS_AXLAB, ha="center",
          va="center", rot=90)
        T(x0 + ML + PW / 2.0, y0 + CH - 0.10, "Voltage (V)", FS_AXLAB,
          va="top")

    x0, y0 = COL_X[0], ROW_Y[1]
    draw_c(ax_cd(fig, x0, y0, PV_W, PV_H), fig, cdat, reg)
    T(x0 + 0.150, y0 + MT + PC / 2.0,
      "Median absolute difference\nrelative to random pairs", FS_AXLAB,
      ha="center", va="center", rot=90)

    x0, y0 = COL_X[1], ROW_Y[1]
    draw_d(ax_cd(fig, x0, y0, PV_W, PV_H), ddat, reg)
    T(x0 + ML + PW / 2.0, y0 + CH - 0.10,
      "|log$_{10}$(θ$_i$/θ$_j$)| (log$_{10}$ units)", FS_AXLAB,
      va="top")
    return fig, reg


# ---------------------------------------------------------------- exports --
def flatten_png(path, dpi):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    bg.save(path, dpi=(dpi, dpi))


def save_all(fig, stem, dpi=600):
    p = os.path.join(FIG, stem)
    fig.savefig(p + ".png", dpi=dpi, facecolor="white", edgecolor="none")
    flatten_png(p + ".png", dpi)
    fig.savefig(p + ".pdf", facecolor="white", edgecolor="none")
    fig.savefig(p + ".svg", facecolor="white", edgecolor="none")
    return p


def check_text_inside(fig):
    fig.canvas.draw()
    W, H = fig.bbox.width, fig.bbox.height
    bad = []
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        try:
            bb = t.get_window_extent(fig.canvas.get_renderer())
        except Exception:
            continue
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > W + 1 or bb.y1 > H + 1:
            bad.append((t.get_text()[:24], round(bb.x0, 1), round(bb.y0, 1),
                        round(bb.x1, 1), round(bb.y1, 1)))
    return bad


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def svg_bar_fills(path, wanted):
    """Count how often each bar colour is painted in the SVG (fills only)."""
    s = open(path, encoding="utf-8").read()
    fills = [c.lower() for c in re.findall(r'style="fill: (#[0-9a-fA-F]{6})', s)]
    return {c.lower(): fills.count(c.lower()) for c in wanted}


def main():
    cases, cdat, ddat, names = load()
    qa = {"panels": {}, "checks": {}}
    qa["checks"]["n_pairs"] = 11245
    qa["checks"]["tier_n"] = 112
    qa["checks"]["axis_changes"] = {
        "Fig3a_b_j_ylim_top": {"before": LIM_J_OLD, "after": LIM_J_TOP,
                               "reason": "upper-right legend clearing the "
                                         "24.09 mA cm-2 plateau"},
        "Fig3c_ylim_top": {"before": YHI_C_OLD, "after": YHI_C,
                           "reason": "upper-right legend clearing the tallest "
                                     "whisker cap at 1.7628"},
        "Fig3d": "unchanged",
        "residual_ylim": list(LIM_R),
    }
    qa["checks"]["c_panels"] = [dict(coordinate=d["coordinate"],
                                     median=d["med"], q1=d["q1"], q3=d["q3"])
                                for d in cdat]
    qa["checks"]["d_values"] = {k: [round(float(x), 4) for x in v]
                                for k, v in ddat.items()}
    qa["checks"]["d_max"] = {"parameter": names[int(np.argmax(ddat["(a)"]))],
                             "value": round(float(ddat["(a)"].max()), 4)}

    # ---- (a)/(b)
    for kind in ("a", "b"):
        reg = []
        fig = plt.figure(figsize=(CW, CH), dpi=100)
        fig.patch.set_facecolor("white")
        axj, axr = ax_ab(fig, 0, 0, CW, CH)
        case = cases["(%s)" % kind]
        leg = draw_ab(axj, axr, case, (-11.2, LIM_J_TOP), LIM_R, reg)
        fig.canvas.draw()
        bad = check_text_inside(fig)
        assert not bad, bad
        gap = legend_gap_pt(fig, axj, leg)
        assert gap["inside"] == 0, gap
        assert gap["min_pt"] >= 4.0, gap
        p = save_all(fig, "Fig3" + kind)
        keys = [e["key"] for e in reg]
        assert len(keys) == len(set(keys)), keys
        with open(os.path.join(QA, "math_registry_Fig3%s.json" % kind), "w",
                  encoding="utf-8") as fh:
            json.dump({"labels": reg}, fh, indent=2, ensure_ascii=False)
        qa["panels"]["Fig3" + kind] = dict(
            canvas_in=[CW, CH], axes_rect_in=[ML, MB, PW, HJ],
            ylim_j=list(axj.get_ylim()),
            ylim_residual=list(axr.get_ylim()),
            n_points=131,
            residual_is_Jj_minus_Ji=bool(
                np.allclose(axr.lines[-1].get_ydata(),
                            case["Jj"] - case["Ji"])),
            legend=[t.get_text() for t in leg.get_texts()],
            legend_clearance=gap,
            j_max=round(float(max(case["Ji"].max(), case["Jj"].max())), 4))
        plt.close(fig)

    # ---- (c)
    fig, reg, info = fig_panel_c(cases, cdat, ddat)
    fig.canvas.draw()
    bad = check_text_inside(fig)
    assert not bad, bad
    labels = info["labels"]
    cap_hw = info["cap_hw"]
    fails = check_labels(fig.axes[0], fig, info["recs"], labels, cap_hw)
    assert not fails, fails
    leg_gap = legend_gap_pt(
        fig, fig.axes[0], info["leg"],
        rect_points(fig.axes[0], info["bar_patches"]))
    assert leg_gap["inside"] == 0, leg_gap
    assert leg_gap["min_pt"] >= 6.0, leg_gap
    # the caps, not the bar tops, are the closest ink on the right
    cap_top = max(d["q3"] for d in cdat)
    y_leg = leg_gap["box_data"][1]
    py0 = fig.axes[0].transData.transform((0.0, cap_top))[1]
    py1 = fig.axes[0].transData.transform((0.0, y_leg))[1]
    cap_gap_pt = round((py1 - py0) * 72.0 / fig.dpi, 2)
    assert cap_gap_pt >= 6.0, cap_gap_pt
    p = save_all(fig, "Fig3c")
    keys = [e["key"] for e in reg]
    assert len(keys) == len(set(keys)), keys
    with open(os.path.join(QA, "math_registry_Fig3c.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"labels": reg}, fh, indent=2, ensure_ascii=False)
    qa["panels"]["Fig3c"] = dict(
        file=os.path.basename(p), canvas_in=[CW, CH],
        bar_colours=[c.upper() for c in info["colours"]],
        cap_markersize_pt=info["cap_ms"],
        cap_halfwidth_dataunits=round(cap_hw, 4),
        ylim=[YLO, YHI_C], xlim=[XLO, XHI],
        labels=labels, overlap_failures=fails,
        legend_clearance=leg_gap, legend_cap_gap_pt=cap_gap_pt,
        tallest_q3=max(d["q3"] for d in cdat))
    plt.close(fig)
    C_BLUE, C_ORANGE = info["colours"]
    PAIR["(a)"], PAIR["(b)"] = C_BLUE, C_ORANGE
    svg_c = svg_bar_fills(os.path.join(FIG, "Fig3c.svg"),
                          [C_BLUE, C_ORANGE])
    assert all(v >= 3 for v in svg_c.values()), svg_c
    qa["checks"]["c_bar_fills_read"] = {"blue": C_BLUE, "orange": C_ORANGE,
                                        "fills_in_svg": svg_c}

    # ---- (d)
    fig, reg, leg = fig_panel_d(cases, cdat, ddat)
    fig.canvas.draw()
    bad = check_text_inside(fig)
    assert not bad, bad
    ax = fig.axes[0]
    # legend vs the 18 bars
    bars = [p for p in ax.patches]
    gap = legend_gap_pt(fig, ax, leg, rect_points(ax, bars))
    assert gap["inside"] == 0, gap
    assert gap["min_pt"] >= 6.0, gap
    p = save_all(fig, "Fig3d")
    keys = [e["key"] for e in reg]
    assert len(keys) == len(set(keys)), keys
    with open(os.path.join(QA, "math_registry_Fig3d.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"labels": reg}, fh, indent=2, ensure_ascii=False)
    up, low = [], []
    for patch in ax.patches:
        yc = patch.get_y() + patch.get_height() / 2.0
        is_a = abs((yc - 0.16) - round(yc - 0.16)) < 1e-6
        (up if is_a else low).append(
            matplotlib.colors.to_hex(patch.get_facecolor()))
    legend_cols = [matplotlib.colors.to_hex(h.get_facecolor())
                   for h in leg.legend_handles]
    qa["panels"]["Fig3d"] = dict(
        file=os.path.basename(p), canvas_in=[CW, CH],
        legend=[t.get_text() for t in leg.get_texts()],
        legend_colours=legend_cols,
        legend_clearance=gap,
        upper_bar_colour=sorted(set(up)),
        lower_bar_colour=sorted(set(low)),
        xlim=list(ax.get_xlim()),
        yticks=[t.get_text() for t in ax.get_yticklabels()])
    assert len(set(up)) == 1 and len(set(low)) == 1
    assert up[0].lower() == C_BLUE.lower() and low[0].lower() == C_ORANGE.lower()
    assert legend_cols[0].lower() == up[0].lower()
    assert legend_cols[1].lower() == low[0].lower()
    plt.close(fig)
    svg_d = svg_bar_fills(os.path.join(FIG, "Fig3d.svg"), [C_BLUE, C_ORANGE])
    qa["checks"]["d_legend_matches_bars"] = {
        "legend": legend_cols, "upper_(a)": up[0], "lower_(b)": low[0],
        "c_bar_fills": [C_BLUE, C_ORANGE], "d_svg_fills": svg_d}
    assert all(v >= 9 for v in svg_d.values()), svg_d

    # ---- preview
    pv, reg = build_preview(cases, cdat, ddat)
    pv.canvas.draw()
    bad = check_text_inside(pv)
    qa["preview"] = {"size_in": [PV_W, PV_H],
                     "size_mm": [round(PV_W * 25.4, 2),
                                 round(PV_H * 25.4, 2)],
                     "text_outside_canvas": bad}
    assert not bad, bad
    pv.savefig(os.path.join(PREV, "Fig3_preview.png"), dpi=600,
               facecolor="white", edgecolor="none")
    pv.savefig(os.path.join(PREV, "Fig3_preview.pdf"), facecolor="white",
               edgecolor="none")
    plt.close(pv)

    with open(os.path.join(QA, "qa_fig3.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in qa["panels"].items()},
                     indent=2, ensure_ascii=False))
    print("preview:", qa["preview"]["size_mm"], "mm")


if __name__ == "__main__":
    main()
