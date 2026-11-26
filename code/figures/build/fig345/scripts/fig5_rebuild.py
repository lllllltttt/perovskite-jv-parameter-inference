# -*- coding: utf-8 -*-
"""Figure 5 — five standalone panels, supervisor revision 2026-11-11.

Only the legend placement changes relative to 20261110_fig5_standalone:

  * the one shared nine-parameter legend moves from (e)'s lower left to (a)'s
    lower right, two columns, one parameter family per row, r_rad alone on the
    last row.  It covers no curve and does not touch the ideal-calibration
    line; the nearest marker keeps 19.6 pt of clearance.
  * (e) therefore returns to the manuscript's y range, -3.0 .. 0.7, instead of
    the -3.3 that had been added only to fit the legend.

Everything else — data, colours, markers, x positions, tick lists, panel
sizes, the (b) legend — is unchanged.  The numbers come from
``fig5_intervals.load()`` of the manuscript package, which re-asserts every
archived pin (S15/S17/S17b/noise tables).  No model run, no re-prediction.

Each panel is drawn at its final print size (1 figure pt = 1 printed pt) with
an explicit axes rectangle and WITHOUT ``bbox_inches="tight"``, so the PNG,
PDF and SVG canvases are identical and PowerPoint cannot rescale them.

No axis titles, units, panel letters or figure text are baked in; those are
in labels_and_caption.txt.  The preview carries them for checking only.
"""
import os
import sys
import csv

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = (r"E:\project\work1\20261006"
       r"\manuscript_figures_SI_integrated_v2_layout_final\scripts")
sys.path.insert(0, SRC)
sys.path.insert(0, HERE)

import figstyle as st          # noqa: E402
import fig5_intervals as F5    # noqa: E402

FIG = os.path.join(ROOT, "figures")
LEG = os.path.join(ROOT, "legends")
PRE = os.path.join(ROOT, "preview")
DATA = os.path.join(ROOT, "data_used")

# ------------------------------------------------------------------ data ----
D = F5.load()
COV = np.asarray(D["cov"], float)        # (9, 4) marginal 95% coverage
RHO = np.asarray(D["rho"], float)        # (9,)   test-set Spearman rho
ISM = np.asarray(D["is_model"], float)   # (9,)   95% interval score, model
ISB = np.asarray(D["is_base"], float)    # (9,)   95% interval score, baseline
WORSE = np.asarray(D["worse"], bool)     # (9,)   frozen "worse than prior" flag
RMAT = np.asarray(D["r_mat"], float)     # (9, 5) noise vs correlation
CMAT = np.asarray(D["c_mat"], float)     # (9, 5) noise vs coverage
SREL = np.asarray(D["s_rel"], float)     # (9, 5) noise vs % change of mean sigma

N_P = 9
IDX = list(range(N_P))

# --------------------------------------------------------------- palette ----
# Four families, two shades each; first member darker + filled circle,
# second member lighter + filled square; r_rad alone, dark grey, circle.
# Light shades are chosen to stay legible as 1 pt lines on white.
PAL = [
    ("#004488", "o"),   # 0 mu_n      dark blue
    ("#6BA0D2", "s"),   # 1 mu_p      light blue
    ("#A85400", "o"),   # 2 tau_n     dark orange
    ("#D08F45", "s"),   # 3 tau_p     light orange
    ("#06695A", "o"),   # 4 Nc        dark teal-green
    ("#55AE9C", "s"),   # 5 Nv        light teal-green
    ("#5B2C83", "o"),   # 6 tau_ETL   dark purple
    ("#A98BC9", "s"),   # 7 tau_HTL   light purple
    ("#333333", "o"),   # 8 r_rad     dark grey
]
FAMILY = ["mu", "mu", "tau_el", "tau_el", "N", "N", "tau_etl", "tau_etl", "rad"]
PAIR = ["dark", "light", "dark", "light", "dark", "light",
        "dark", "light", "alone"]

# legend handle order: matplotlib fills a ncol=2 legend column by column, so
# the first five entries land in column 1 and the last four in column 2,
# which puts each family pair on one row and r_rad alone on the last row.
LEG_ORDER = [0, 2, 4, 6, 8, 1, 3, 5, 7]

# ------------------------------------------------------------- geometry -----
PW = {"a": (2.00, 1.75), "b": (2.00, 1.75),
      "c": (2.00, 1.50), "d": (2.00, 1.50), "e": (2.00, 1.50)}
INS = dict(bottom=0.19, top=0.06, right=0.06)   # bottom holds 7.5 pt numbers
GUT = 0.20                # white gutter at the left edge for the PPT y title
PROV_LEFT = 0.42          # provisional left margin, measured afterwards

MS = 3.2                  # curve marker size, all four curve panels
LW = 1.0                  # curve line width
MS_B = 4.4                # (b) dot-plot markers (different chart type)
MS_RING = 7.6
FS_LEG = 6.8
FS_LEG_B = 6.8
FS_PARAM = 7.0            # (b) y tick names

X_TICKS = [0.0, 0.5, 1.0, 1.5, 2.0]
X_LABELS = ["0", "0.5", "1.0", "1.5", "2.0"]
X_LIM = (-0.06, 2.06)

INK = st.INK


def new_fig(w, h, dpi=100):
    fig = plt.figure(figsize=(w, h), dpi=dpi)
    fig.patch.set_facecolor("white")
    return fig


def add_ax(fig, x0, y0, w, h, prov=PROV_LEFT, gut=GUT):
    fw, fh = fig.get_size_inches()        # the FIGURE, never the panel
    return fig.add_axes([(x0 + gut + prov) / fw,
                         (y0 + INS["bottom"]) / fh,
                         (w - gut - prov - INS["right"]) / fw,
                         (h - INS["bottom"] - INS["top"]) / fh])


def tighten_left(fig, ax, x0, y0, w, h, pad_pt=3.5, gut=GUT):
    """Measure the y tick labels and give the axes exactly that margin,
    on top of the fixed white gutter that holds the PowerPoint y title."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    labs = [t for t in ax.get_yticklabels() if t.get_text()]
    wid = 0.0
    if labs:
        wid = max(t.get_window_extent(r).width for t in labs) / fig.dpi
    left = gut + wid + (3.0 + pad_pt) / 72.0 + 0.004
    fw, fh = fig.get_size_inches()
    ax.set_position([(x0 + left) / fw,
                     (y0 + INS["bottom"]) / fh,
                     (w - left - INS["right"]) / fw,
                     (h - INS["bottom"] - INS["top"]) / fh])
    fig.canvas.draw()
    return left


def legend_clearance(fig, ax, leg, extra_pt=0.0):
    """Markers inside the legend box (must be 0) and the smallest gap, in pt."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = leg.get_window_extent(r)
    pts = []
    for ln in ax.lines:
        xd, yd = np.asarray(ln.get_xdata(), float), np.asarray(ln.get_ydata(), float)
        if ln.get_marker() in ("o", "s") and xd.size:
            pts.append(np.column_stack([xd, yd]))
    if not pts:
        return 0, None
    P = ax.transData.transform(np.vstack(pts))
    inside = int(np.sum((P[:, 0] >= bb.x0) & (P[:, 0] <= bb.x1)
                        & (P[:, 1] >= bb.y0) & (P[:, 1] <= bb.y1)))
    dx = np.maximum(np.maximum(bb.x0 - P[:, 0], P[:, 0] - bb.x1), 0.0)
    dy = np.maximum(np.maximum(bb.y0 - P[:, 1], P[:, 1] - bb.y1), 0.0)
    gap = np.sqrt(dx ** 2 + dy ** 2) - extra_pt * fig.dpi / 72.0
    return inside, float(gap.min()) * 72.0 / fig.dpi


def set_left(fig, ax, x0, y0, w, h, left):
    fw, fh = fig.get_size_inches()
    ax.set_position([(x0 + left) / fw,
                     (y0 + INS["bottom"]) / fh,
                     (w - left - INS["right"]) / fw,
                     (h - INS["bottom"] - INS["top"]) / fh])
    fig.canvas.draw()


def _label_width(strings, fs):
    """Widest label in inches, measured with the same font as the ticks."""
    fig = new_fig(2.0, 0.6)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    best = 0.0
    for s in strings:
        t = fig.text(0.1, 0.5, s, fontsize=fs)
        best = max(best, t.get_window_extent(r).width / fig.dpi)
        t.remove()
    plt.close(fig)
    return best


CDE_LABELS = {"c": ["0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"],
              "d": ["0.70", "0.80", "0.90", "1.00"],
              "e": ["-3", "-2", "-1", "0"]}
_CDE_LEFT = None


def cde_left():
    """One left margin for (c)(d)(e): the widest of the three tick columns.

    Identical plot areas are what lets the three panels be aligned in
    PowerPoint, so the margin is a single measured value, never per panel.
    """
    global _CDE_LEFT
    if _CDE_LEFT is None:
        wid = max(_label_width(v, st.FS_TICK) for v in CDE_LABELS.values())
        _CDE_LEFT = GUT + wid + (3.0 + 3.5) / 72.0 + 0.004
    return _CDE_LEFT


def canvas_text_out(fig, pad=0.5):
    """Text artists that stick out of the canvas, measured in display px."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    bad = []
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        bb = t.get_window_extent(renderer=r)
        if bb.x0 < -pad or bb.y0 < -pad or bb.x1 > W + pad or bb.y1 > H + pad:
            bad.append(t.get_text())
    return bad


# ------------------------------------------------------------------ (a) -----
def draw_a(fig, x0=0.0, y0=0.0):
    w, h = PW["a"]
    ax = add_ax(fig, x0, y0, w, h)
    # ideal calibration y = x/100; drawn over a wider span and clipped, so it
    # meets the left spine at (48, 0.48) and the top spine at (100, 1.00)
    ax.plot([40.0, 103.0], [0.40, 1.03], ls="--", lw=0.8, color="#999999",
            zorder=1, dash_capstyle="butt", clip_on=True)
    xs = np.asarray(F5.LEVELS, float) * 100.0
    for i in IDX:
        ax.plot(xs, COV[i], color=PAL[i][0], marker=PAL[i][1], ms=MS,
                lw=LW, zorder=3, markeredgewidth=0)
    ax.set_xlim(48.0, 102.0)
    ax.set_xticks([50, 60, 70, 80, 90, 100])
    ax.set_ylim(0.42, 1.0)
    ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["0.5", "0.6", "0.7", "0.8", "0.9", "1.0"])
    st.configure_axes(ax)
    left = tighten_left(fig, ax, x0, y0, w, h)
    # the ONE shared nine-parameter key now lives here, clear of all nine
    # curves and of the ideal-calibration line (both stay above y = 0.70)
    leg = ax.legend(param_legend_handles(), param_legend_labels(),
                    ncol=2, loc="lower right", frameon=False,
                    fontsize=FS_LEG, handletextpad=0.35,
                    columnspacing=0.80, labelspacing=0.16,
                    handlelength=1.0, borderaxespad=0.20, borderpad=0.10)
    leg.set_zorder(10)
    return ax, left, leg


# ------------------------------------------------------------------ (b) -----
# The lower-right corner of (b) is the only free area, and it is narrow: the
# full wording ("training-quantile baseline", "model interval", "model worse")
# would push the key over the tau_ETL / r_rad points.  Short keys here, full
# wording in labels_and_caption.txt and in the caption itself.
B_LEG_LABELS = ["Baseline", "Model", "Worse"]


def b_legend_handles(ms=MS_B, ring=MS_RING):
    return [
        Line2D([], [], ls="none", marker="o", ms=ms, mfc="white",
               mec=F5.C_BASE, mew=1.0),
        Line2D([], [], ls="none", marker="o", ms=ms, color=F5.C_MODEL,
               markeredgewidth=0),
        Line2D([], [], ls="none", marker="o", ms=ring, mfc="none",
               mec=F5.C_WORSE, mew=1.2),
    ]


def draw_b(fig, x0=0.0, y0=0.0):
    w, h = PW["b"]
    ax = add_ax(fig, x0, y0, w, h, gut=0.0)   # no y title in (b)
    ys = np.arange(N_P)[::-1].astype(float)
    for i in IDX:                                  # connector, baseline->model
        ax.plot([ISB[i], ISM[i]], [ys[i], ys[i]], color="#c9ced4", lw=1.1,
                zorder=1, solid_capstyle="round")
    ax.plot(ISB, ys, ls="none", marker="o", ms=MS_B, mfc="white",
            mec=F5.C_BASE, mew=1.0, zorder=3)
    ax.plot(ISM, ys, ls="none", marker="o", ms=MS_B, color=F5.C_MODEL,
            markeredgewidth=0, zorder=4)
    ax.plot(ISM[WORSE], ys[WORSE], ls="none", marker="o", ms=MS_RING,
            mfc="none", mec=F5.C_WORSE, mew=1.2, zorder=5)
    ax.set_yticks(ys)
    ax.set_yticklabels(st.PARAM_LABELS)
    ax.set_ylim(-0.7, 8.7)
    ax.set_xlim(0.0, 7.6)
    ax.set_xticks([0, 2, 4, 6])
    st.configure_axes(ax)
    for t in ax.get_yticklabels():
        t.set_fontsize(FS_PARAM)
    left = tighten_left(fig, ax, x0, y0, w, h, gut=0.0)
    leg = ax.legend(b_legend_handles(), B_LEG_LABELS, loc="lower right",
                    frameon=False, fontsize=FS_LEG_B, handletextpad=0.45,
                    borderaxespad=0.25, labelspacing=0.32,
                    handlelength=1.2, borderpad=0.1)
    leg.set_zorder(10)
    return ax, left, leg


# ------------------------------------------------------------ (c)(d)(e) -----
def _noise_axes(ax):
    ax.set_xlim(*X_LIM)
    ax.set_xticks(X_TICKS)
    ax.set_xticklabels(X_LABELS)


def draw_c(fig, x0=0.0, y0=0.0):
    w, h = PW["c"]
    ax = add_ax(fig, x0, y0, w, h)
    for i in IDX:
        ax.plot(F5.NOISE_X, RMAT[i], color=PAL[i][0], marker=PAL[i][1],
                ms=MS, lw=LW, zorder=3, markeredgewidth=0)
    _noise_axes(ax)
    ax.set_ylim(0.35, 1.0)
    ax.set_yticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"])
    st.configure_axes(ax)
    set_left(fig, ax, x0, y0, w, h, cde_left())
    return ax, cde_left()


def draw_d(fig, x0=0.0, y0=0.0):
    w, h = PW["d"]
    ax = add_ax(fig, x0, y0, w, h)
    ax.axhline(0.95, ls="--", lw=0.9, color="#555555", zorder=1,
               dash_capstyle="butt")
    for i in IDX:
        ax.plot(F5.NOISE_X, CMAT[i], color=PAL[i][0], marker=PAL[i][1],
                ms=MS, lw=LW, zorder=3, markeredgewidth=0)
    _noise_axes(ax)
    ax.set_ylim(0.68, 1.0)
    ax.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["0.70", "0.80", "0.90", "1.00"])
    st.configure_axes(ax)
    set_left(fig, ax, x0, y0, w, h, cde_left())
    return ax, cde_left()


def param_legend_handles(ms=MS):
    return [Line2D([], [], color=PAL[i][0], marker=PAL[i][1], ms=ms, lw=LW,
                   markeredgewidth=0) for i in LEG_ORDER]


def param_legend_labels():
    return [st.PARAM_LABELS[i] for i in LEG_ORDER]


def draw_e(fig, x0=0.0, y0=0.0):
    w, h = PW["e"]
    ax = add_ax(fig, x0, y0, w, h)
    ax.axhline(0.0, lw=0.8, color="#bbbbbb", zorder=1)
    for i in IDX:
        ax.plot(F5.NOISE_X, SREL[i], color=PAL[i][0], marker=PAL[i][1],
                ms=MS, lw=LW, zorder=3, markeredgewidth=0)
    _noise_axes(ax)
    # the manuscript's range; the -3.3 of the previous standalone round was
    # only there to fit the shared legend, which now sits in (a)
    ax.set_ylim(-3.0, 0.7)
    ax.set_yticks([-3, -2, -1, 0])
    ax.set_yticklabels(["-3", "-2", "-1", "0"])
    st.configure_axes(ax)
    left = cde_left()
    set_left(fig, ax, x0, y0, w, h, left)
    return ax, left, None


# -------------------------------------------------------------- exporters ---
def save(fig, stem, folder=FIG):
    os.makedirs(folder, exist_ok=True)
    base = os.path.join(folder, stem)
    fig.savefig(base + ".png", dpi=600, facecolor="white")
    fig.savefig(base + ".pdf", facecolor="white")
    fig.savefig(base + ".svg", facecolor="white")


def _shrink_to_legend(fig, ax, make_legend, pad_in=0.02):
    """Crop a legend-only canvas to exactly the legend's own size."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = make_legend().get_window_extent(r)
    w = bb.width / fig.dpi + 2 * pad_in
    h = bb.height / fig.dpi + 2 * pad_in
    fig.set_size_inches(w, h)
    ax.set_position([0, 0, 1, 1])
    make_legend()
    return fig


def save_param_legend():
    fig = new_fig(2.4, 1.1)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    def mk():
        return ax.legend(param_legend_handles(ms=3.4), param_legend_labels(),
                         ncol=2, loc="center", frameon=False,
                         fontsize=FS_LEG, handletextpad=0.35,
                         columnspacing=0.9, labelspacing=0.28,
                         handlelength=1.1, borderpad=0.0)
    mk()
    _shrink_to_legend(fig, ax, mk)
    save(fig, "Fig5_param_legend", LEG)
    plt.close(fig)


def save_color_map():
    """A flat table of the nine curves: marker, label, hex, family, pair."""
    W, H = 3.22, 2.05
    fig = new_fig(W, H, dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    y = H - 0.14
    T(fig, 0.06, y, "parameter", fontsize=7.5, ha="left", fontweight="bold")
    T(fig, 0.80, y, "marker", fontsize=7.5, ha="left", fontweight="bold")
    T(fig, 1.24, y, "colour", fontsize=7.5, ha="left", fontweight="bold")
    T(fig, 1.78, y, "family / pair", fontsize=7.5, ha="left",
      fontweight="bold")
    T(fig, 2.62, y, "panels", fontsize=7.5, ha="left", fontweight="bold")
    step = (y - 0.14) / 9.0
    for n, i in enumerate(IDX):
        yy = y - step * (n + 1)
        T(fig, 0.06, yy, st.PARAM_LABELS[i], fontsize=7.5, ha="left",
          va="center")
        ax.plot([0.80, 1.05], [yy + 0.055, yy + 0.055], color=PAL[i][0],
                lw=1.0, clip_on=False)
        ax.plot([0.925], [yy + 0.055], marker=PAL[i][1], ms=3.4,
                color=PAL[i][0], markeredgewidth=0, clip_on=False)
        T(fig, 1.24, yy, PAL[i][0], fontsize=7.0, ha="left", va="center",
          family="DejaVu Sans")
        T(fig, 1.78, yy, "%s / %s" % (FAMILY[i], PAIR[i]), fontsize=7.0,
          ha="left", va="center")
        T(fig, 2.62, yy, "a, c, d, e", fontsize=7.0, ha="left", va="center")
    fig.savefig(os.path.join(LEG, "Fig5_color_map.png"), dpi=600,
                facecolor="white")
    fig.savefig(os.path.join(LEG, "Fig5_color_map.svg"), facecolor="white")
    fig.savefig(os.path.join(LEG, "Fig5_color_map.pdf"), facecolor="white")
    plt.close(fig)


def save_b_legend():
    fig = new_fig(2.4, 1.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    def mk():
        return ax.legend(b_legend_handles(ms=4.8, ring=7.8), B_LEG_LABELS,
                         loc="center", frameon=False, fontsize=FS_LEG_B,
                         handletextpad=0.45, labelspacing=0.32,
                         handlelength=1.2, borderpad=0.0)
    mk()
    _shrink_to_legend(fig, ax, mk)
    save(fig, "Fig5b_marker_legend", LEG)
    plt.close(fig)


# --------------------------------------------------------------- preview ----
PW_TXT = dict(fontsize=st.FS_AXIS, color=INK)

TITLES = {
    "a": dict(x="Nominal level (%)", y="Empirical coverage"),
    "b": dict(x="95% interval score (log$_{10}$ units)\n(lower is better)",
              y=None),
    "c": dict(x="Current noise (% of $|J_\\mathrm{sc}|$)",
              y="Pearson correlation, $\\rho$"),
    "d": dict(x="Current noise (% of $|J_\\mathrm{sc}|$)",
              y="Empirical 95% coverage"),
    "e": dict(x="Current noise (% of $|J_\\mathrm{sc}|$)",
              y="Change in mean $\\sigma_\\theta$\n(% of its clean-input value)"),
}


def T(fig, x, y, s, **kw):
    fw, fh = fig.get_size_inches()
    kw.setdefault("fontsize", st.FS_AXIS)
    kw.setdefault("color", INK)
    kw.setdefault("ha", "center")
    kw.setdefault("va", "center")
    return fig.text(x / fw, y / fh, s, **kw)


def build_preview():
    W, H = 6.80, 4.70
    fig = new_fig(W, H, dpi=200)
    y_bot, y_top = 0.62, 2.66
    place = {"a": (1.20, y_top), "b": (3.60, y_top),
             "c": (0.00, y_bot), "d": (2.40, y_bot), "e": (4.80, y_bot)}
    out = {}
    out["a"] = draw_a(fig, *place["a"])
    out["b"] = draw_b(fig, *place["b"])
    out["c"] = draw_c(fig, *place["c"])
    out["d"] = draw_d(fig, *place["d"])
    out["e"] = draw_e(fig, *place["e"])
    fw, fh = fig.get_size_inches()
    # the bottom row uses the same shared left margin as the exported files
    left = cde_left()
    for k in "cde":
        x0, y0 = place[k]
        w, h = PW[k]
        set_left(fig, out[k][0], x0, y0, w, h, left)
    fig.canvas.draw()
    for k in "abcde":
        ax = out[k][0]
        x0, y0 = place[k]
        w, h = PW[k]
        T(fig, x0, y0 + h + 0.055, "(%s)" % k, fontsize=st.FS_PANEL,
          fontweight="bold", ha="left", va="center")
        T(fig, x0 + w / 2.0, y0 - 0.30, TITLES[k]["x"], linespacing=1.25)
        if TITLES[k]["y"]:
            T(fig, x0 + GUT / 2.0, y0 + h / 2.0, TITLES[k]["y"], rotation=90,
              va="center", ha="center", linespacing=1.2)
    # footnote under the bottom row
    T(fig, W / 2.0, 0.075,
      "panels (c)–(e): five noise levels 0, 0.2, 0.5, 1, 2 % of each curve's "
      "$|J_\\mathrm{sc}|$; 1.5 is only a tick", fontsize=st.FS_ANNOT,
      color=st.MUTED)
    bad = canvas_text_out(fig, pad=1.0)
    assert not bad, "preview text outside the canvas: %s" % bad
    fig.savefig(os.path.join(PRE, "Fig5_preview.png"), dpi=200,
                facecolor="white")
    fig.savefig(os.path.join(PRE, "Fig5_preview.pdf"), facecolor="white")
    plt.close(fig)


# ------------------------------------------------------------ data tables ---
def write_tables():
    os.makedirs(DATA, exist_ok=True)
    # 1. colour / marker map
    p = os.path.join(DATA, "Figure5_color_map.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "key", "label_plain", "family", "pair_role",
                    "color_hex", "marker", "marker_size_pt",
                    "panels", "legend_row"])
        row_of = {0: 1, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 5}
        for i in IDX:
            w.writerow([i, st.PARAM_NAMES[i], st.PARAM_SHORT[i], FAMILY[i],
                        PAIR[i], PAL[i][0], PAL[i][1], MS,
                        "a,c,d,e", row_of[i]])
    # 2. plotting values
    p = os.path.join(DATA, "Figure5_plotting_values.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["panel", "param_key", "series", "x", "y"])
        for i in IDX:
            for k, lv in enumerate(F5.LEVELS):
                w.writerow(["a", st.PARAM_NAMES[i], "coverage", lv * 100.0,
                            "%.9g" % COV[i, k]])
            w.writerow(["b", st.PARAM_NAMES[i], "baseline", "", "%.9g" % ISB[i]])
            w.writerow(["b", st.PARAM_NAMES[i], "model", "", "%.9g" % ISM[i]])
            w.writerow(["b", st.PARAM_NAMES[i], "model_worse", "",
                        str(bool(WORSE[i]))])
            for k, nx in enumerate(F5.NOISE_X):
                w.writerow(["c", st.PARAM_NAMES[i], "spearman_rho", nx,
                            "%.9g" % RMAT[i, k]])
                w.writerow(["d", st.PARAM_NAMES[i], "coverage95", nx,
                            "%.9g" % CMAT[i, k]])
                w.writerow(["e", st.PARAM_NAMES[i], "pct_change_mean_sigma",
                            nx, "%.9g" % SREL[i, k]])


def line_clearance(fig, ax, leg, xs, ys):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = leg.get_window_extent(r)
    P = ax.transData.transform(np.column_stack([xs, ys]))
    dx = np.maximum(np.maximum(bb.x0 - P[:, 0], P[:, 0] - bb.x1), 0.0)
    dy = np.maximum(np.maximum(bb.y0 - P[:, 1], P[:, 1] - bb.y1), 0.0)
    return float(np.sqrt(dx ** 2 + dy ** 2).min()) * 72.0 / fig.dpi


# ------------------------------------------------------------------ main ----
def main():
    for d in (FIG, LEG, PRE, DATA):
        os.makedirs(d, exist_ok=True)

    specs = [("a", draw_a), ("b", draw_b), ("c", draw_c),
             ("d", draw_d), ("e", draw_e)]
    report = {}
    for name, fn in specs:
        w, h = PW[name]
        fig = new_fig(w, h)
        res = fn(fig)
        ax = res[0]
        leg = res[2] if len(res) > 2 else None
        bad = canvas_text_out(fig)
        assert not bad, "text outside the %s canvas: %s" % (name, bad)
        save(fig, "Fig5" + name)
        rep = dict(canvas=[w, h], ylim=[round(v, 6) for v in ax.get_ylim()],
                   xticks=[round(float(v), 6) for v in ax.get_xticks()],
                   yticks=[round(float(v), 6) for v in ax.get_yticks()],
                   n_curves=len([ln for ln in ax.lines
                                 if ln.get_marker() in ("o", "s")]))
        if leg is not None:
            fig.canvas.draw()
            r = fig.canvas.get_renderer()
            bb = leg.get_window_extent(r)
            rep["legend_in"] = [round(bb.width / fig.dpi, 3),
                                round(bb.height / fig.dpi, 3)]
            hit, gap = legend_clearance(fig, ax, leg)
            rep["legend_hits"], rep["legend_gap_pt"] = hit, round(gap, 2)
            rep["legend_texts"] = [t.get_text() for t in leg.get_texts()]
            assert hit == 0, "legend covers a marker in (%s)" % name
            if name == "a":
                xs = np.linspace(40.0, 103.0, 400)
                rep["ideal_line_gap_pt"] = round(
                    line_clearance(fig, ax, leg, xs, xs / 100.0), 2)
                assert rep["ideal_line_gap_pt"] > 6.0, rep
                rep["legend_ncol"] = 2
                rep["legend_rows"] = [
                    [st.PARAM_LABELS[0], st.PARAM_LABELS[1]],
                    [st.PARAM_LABELS[2], st.PARAM_LABELS[3]],
                    [st.PARAM_LABELS[4], st.PARAM_LABELS[5]],
                    [st.PARAM_LABELS[6], st.PARAM_LABELS[7]],
                    [st.PARAM_LABELS[8], None]]
        if name == "e":
            rep["data_min"] = round(float(np.nanmin(SREL)), 4)
            rep["data_max"] = round(float(np.nanmax(SREL)), 4)
            assert np.nanmin(SREL) > ax.get_ylim()[0] + 0.02
            assert np.nanmax(SREL) < ax.get_ylim()[1] - 0.02
        report[name] = rep
        plt.close(fig)

    save_param_legend()
    save_b_legend()
    save_color_map()
    build_preview()
    write_tables()

    qa = {"panels": report,
          "checks": {
              "n_parameters": 9, "n_levels": 5,
              "nominal_levels": [float(v) for v in F5.LEVELS],
              "noise_x": [float(v) for v in F5.NOISE_X],
              "worse_index": [int(i) for i in np.where(WORSE)[0]],
              "c_metric": "Pearson correlation",
              "e_ylim_restored": [-3.0, 0.7],
              "e_ylim_previous_standalone": [-3.3, 0.7],
          }}
    with open(os.path.join(ROOT, "qa", "qa_fig5.json"), "w",
              encoding="utf-8") as f:
        import json
        json.dump(qa, f, indent=2, ensure_ascii=False)

    print("Figure 5 standalone panels")
    for k, v in report.items():
        print("  Fig5%s  canvas %.2f x %.2f in  ylim %s  xticks %s  %s"
              % (k, v["canvas"][0], v["canvas"][1], v["ylim"], v["xticks"],
                 v.get("legend_in", "")))
        if "legend_gap_pt" in v:
            print("        legend box %.3f x %.3f in, 0 markers inside, "
                  "nearest marker %.1f pt away"
                  % (v["legend_in"][0], v["legend_in"][1], v["legend_gap_pt"]))


if __name__ == "__main__":
    main()
