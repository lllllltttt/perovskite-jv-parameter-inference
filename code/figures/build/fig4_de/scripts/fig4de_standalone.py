# -*- coding: utf-8 -*-
"""Figure 4 (d) and (e) - standalone net assets.

Redraws the two lower panels of the manuscript's Figure 4 from the same frozen
data the manuscript figure uses (`fig4_forward.collect()` is imported and
called, so every archived pin is re-asserted here).  Nothing is re-predicted and
COMSOL is not re-run.

(d)  per-sample J-V RMSE in three voltage windows, base-10 log axis with plain
     decimal major ticks 0.01 / 0.1 / 1 / 10 / 100.
(e)  |dJsc|, |dVoc|, |dFF|, |dPCE| - one panel each, linear axes from zero.

Every panel is drawn on an exact print-size canvas (1 pt in figure = 1 pt in
print) with explicit axes rectangles and no tight bbox, so the four (e) canvases
and plot areas are identical to the hundredth of an inch.

No in-panel text: no (d)/(e) labels, axis titles, units, n, medians or category
names.  Those live in labels_and_caption.txt and are placed by the author in
PPT.  The preview PNG is the only file that carries them.
"""

import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.text import Text
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FixedLocator, NullFormatter, MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
PREV = os.path.join(OUT, "preview")
DATA = os.path.join(OUT, "data_used")
QA = os.path.join(OUT, "qa")
for _d in (FIG, PREV, DATA, QA):
    os.makedirs(_d, exist_ok=True)

BASE = r"E:\project\work1"
SRC = os.path.join(BASE, "20261006",
                   "manuscript_figures_SI_integrated_v2_layout_final", "scripts")
sys.path.insert(0, SRC)
import figstyle as st          # noqa: E402
import fig4_forward as f4      # noqa: E402

plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42

INK = st.INK
FS_TICK = st.FS_TICK            # 7.5 pt, the figure package's tick size
TICK_LEN = 3.0                  # pt, outward (figstyle.configure_axes)
TICK_PAD = 2.5                  # pt, matplotlib default label pad

# ------------------------------------------------------------------ sizes ---
D_W, D_H = 2.60, 2.20           # (d) canvas, inches
E_W, E_H = 1.68, 1.00           # (e) canvas, identical for all four
D_M = dict(right=0.06, bottom=0.10, top=0.05)
E_M = dict(right=0.05, bottom=0.075, top=0.05)
# bottom: the y=0 tick label is centred on the axis bottom, so it
# needs half a label height below the axes or it clips the canvas.

BOX_W = 0.50
JIT = 0.13                      # half-width of the horizontal jitter
MS = 2.2
ALPHA_PT = 0.45
ALPHA_BOX = 0.22

WINDOWS = [("full", "Full curve\n(0\u20131.3 V)"),
           ("le1", "0\u20131.0 V"),
           ("gt1", "> 1.0 V")]
Wd = [st.OKABE_ITO[0], st.OKABE_ITO[2], st.OKABE_ITO[3]]   # blue/green/orange

E_ORDER = ["Jsc", "Voc", "FF", "PCE"]
E_XTL = {"Jsc": r"$|\Delta J_\mathrm{sc}|$", "Voc": r"$|\Delta V_\mathrm{oc}|$",
         "FF": r"$|\Delta FF|$", "PCE": r"$|\Delta \mathrm{PCE}|$"}
E_UNIT = {"Jsc": r"mA cm$^{-2}$", "Voc": "V", "FF": None, "PCE": "pp"}
BLUE = st.OKABE_ITO[0]

D_YLBL = ["0.01", "0.1", "1", "10", "100"]

# The frozen data, collected once (collect() re-asserts every archived pin).
D = f4.collect()


# ------------------------------------------------------------------ text ----
def text_pt(s, size=FS_TICK, weight="normal"):
    """Width of a plain (non-mathtext) string in points, Arial metrics."""
    fp = FontProperties(family="Arial", size=size, weight=weight)
    return TextPath((0, 0), s, prop=fp).get_extents().width


def left_margin(labels, gap_pt=3.5):
    # TextPath returns the glyph outline, a little narrower than the Text
    # window extent that matplotlib uses for layout (side bearings + the
    # ascent/descent box), so the margin carries 3.5 pt of clearance rather
    # than 1.5; measured after "0.01" first sat 1.6 px outside the canvas.
    """Left margin in inches needed for a y tick column made of `labels`."""
    return (TICK_LEN + TICK_PAD + max(text_pt(s) for s in labels) + gap_pt) / 72.0


D_LEFT = left_margin(D_YLBL)


def e_ticks(vmax, max_intervals=4):
    """Equidistant round ticks from zero, their labels, and the axis top.

    Step from the readable 1/2/2.5/4/5 ladder (not matplotlib's default, whose
    1.5/3/6/8 factors produced 0.8- and 0.6-wide steps here), choosing the
    smallest step that needs at most `max_intervals` intervals.  The top tick
    always lies at or above the largest sample, so the maximum is never
    unlabelled."""
    vmax = float(vmax)
    best = None
    for k in range(-8, 9):
        for m in (1.0, 2.0, 2.5, 4.0, 5.0):
            step = m * 10.0 ** k
            n = int(np.ceil(vmax / step - 1e-12))
            if 2 <= n <= max_intervals:
                if best is None or step < best[0]:
                    best = (step, n)
    step, n = best
    ticks = [i * step for i in range(n + 1)]
    dec = 0 if step >= 1 else (1 if step >= 0.1 else 2)
    top = max(vmax * 1.03, ticks[-1] * 1.02)
    return top, ticks, ["%.*f" % (dec, x) for x in ticks]


E_LBL = {k: e_ticks(float(np.nanmax(np.abs(np.asarray(D["dev"][k], float)))))
         for k in E_ORDER}
E_LEFT = left_margin([s for _, _, labs in E_LBL.values() for s in labs])


# ---------------------------------------------------------------- drawing ---
def draw_box_group(ax, vals, pos, color, seed):
    """Box + jittered raw points; whiskers 1.5 IQR; no flier markers."""
    vals = np.asarray(vals, float)
    vals = vals[np.isfinite(vals)]
    ax.boxplot([vals], positions=[pos], widths=BOX_W, patch_artist=True,
               showfliers=False,
               boxprops=dict(facecolor=to_rgba(color, ALPHA_BOX),
                             edgecolor=INK, linewidth=0.6),
               medianprops=dict(color="black", linewidth=1.0, zorder=4),
               whiskerprops=dict(color="black", linewidth=0.7, zorder=2),
               capprops=dict(color="black", linewidth=0.7, zorder=2))
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-JIT, JIT, vals.size)
    ax.plot(pos + jit, vals, marker="o", ms=MS, ls="none", mew=0,
            color=color, alpha=ALPHA_PT, zorder=3, clip_on=True)


def draw_d(fig, x0, y0, w=D_W, h=D_H):
    fw, fh = fig.get_size_inches()          # canvas, not panel, on a preview
    ax = fig.add_axes([(x0 + D_LEFT) / fw, (y0 + D_M["bottom"]) / fh,
                       (w - D_LEFT - D_M["right"]) / fw,
                       (h - D_M["bottom"] - D_M["top"]) / fh])
    for i, (k, _) in enumerate(WINDOWS):
        draw_box_group(ax, D["rm"][k], i, Wd[i], 2026 + i)

    ax.set_yscale("log")
    # The >1.0 V group reaches 113.3 mA cm^-2, so the top of the axis is 200:
    # the 100 tick must not be pushed to the top edge and no point is cut.
    ax.set_ylim(0.01, 200.0)
    ax.set_xlim(-0.55, 2.55)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["", "", ""])
    ax.yaxis.set_major_locator(FixedLocator([0.01, 0.1, 1.0, 10.0, 100.0]))
    ax.set_yticklabels(D_YLBL)
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(False)
    st.configure_axes(ax)
    ax.tick_params(axis="y", which="minor", length=2.0, width=0.6, color=INK)
    return ax


def draw_e(fig, x0, y0, key, w=E_W, h=E_H):
    fw, fh = fig.get_size_inches()          # canvas, not panel, on a preview
    ax = fig.add_axes([(x0 + E_LEFT) / fw, (y0 + E_M["bottom"]) / fh,
                       (w - E_LEFT - E_M["right"]) / fw,
                       (h - E_M["bottom"] - E_M["top"]) / fh])
    a = np.abs(np.asarray(D["dev"][key], float))
    draw_box_group(ax, a, 0, BLUE, 2026 + 10 + E_ORDER.index(key))

    top, ticks, labels = E_LBL[key]
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(0.0, top)
    ax.set_xticks([])                     # one group: no x axis numbers
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.set_yticklabels(labels)
    ax.grid(False)
    st.configure_axes(ax)
    return ax


def new_fig(w, h):
    fig = plt.figure(figsize=(w, h))
    fig.patch.set_facecolor("white")
    return fig


def save(fig, stem):
    fig.savefig(stem + ".png", dpi=600, facecolor="white")
    fig.savefig(stem + ".pdf", facecolor="white")
    fig.savefig(stem + ".svg", facecolor="white")
    plt.close(fig)


def canvas_text_out(fig):
    """Every visible Text artist must sit inside the exact canvas."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bad = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        b = t.get_window_extent(renderer=r)
        if b.width <= 1.0 and b.height <= 1.0:
            continue                      # un-drawn twin the ticker keeps at 1x1
        if (b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > fig.bbox.x1 + 0.5
                or b.y1 > fig.bbox.y1 + 0.5):
            bad.append((t.get_text()[:24], round(b.x0, 1), round(b.y0, 1),
                        round(b.x1, 1), round(b.y1, 1)))
    return bad


# --------------------------------------------------------------- preview ----
def build_preview():
    """(d) left, (e) 2x2 right, at the 6.80 in text width, with all the text
    the author will place in PPT (this is the only file carrying text)."""
    W, H = 6.80, 2.84
    fig = new_fig(W, H)
    xd, yd = 0.36, 0.34
    axd = draw_d(fig, xd, yd)
    x1, x2 = 3.20, 5.04
    y2, y1 = 0.34, 1.54
    pos = {k: (x, y) for k, (x, y) in zip(
        E_ORDER, [(x1, y1), (x2, y1), (x1, y2), (x2, y2)])}
    axs = {k: draw_e(fig, x, y, k) for k, (x, y) in pos.items()}

    def T(x_in, y_in, s, **kw):
        fig.text(x_in / W, y_in / H, s, color=kw.pop("color", INK), **kw)

    T(xd - 0.02, 2.61, "(d)", fontsize=10.5, fontweight="bold", ha="left",
      va="bottom")
    T(x1 - 0.02, 2.61, "(e)", fontsize=10.5, fontweight="bold", ha="left",
      va="bottom")

    T(0.30, yd + 1.06, "J\u2013V RMSE (mA cm$^{-2}$)", rotation=90,
      fontsize=8.5, ha="center", va="center")

    for i, (_, lab) in enumerate(WINDOWS):
        px = axd.transData.transform((i, axd.get_ylim()[0]))[0] / fig.dpi
        # bottom-aligned, so the two-line first name and the one-line others
        # share one baseline block instead of staggering
        T(px, 0.10, lab, fontsize=7.0, ha="center", va="bottom",
          linespacing=1.25)

    px = axd.transAxes.transform((0.02, 0.99))[0] / fig.dpi
    py = axd.transAxes.transform((0.02, 0.99))[1] / fig.dpi
    T(px, py, "$n$ = 45 per window", fontsize=7.0, ha="left", va="top")

    # No per-group median numbers here: in a panel this narrow "5.19" would
    # touch the right spine.  They are listed in labels_and_caption.txt.

    for k, (x, y) in pos.items():
        T(x + E_LEFT + 0.03, y + E_H + 0.03, E_XTL[k], fontsize=7.5,
          ha="left", va="bottom")
        if E_UNIT[k]:
            # just outside the panel canvas, left of the tick-number column
            # (inside it the rotated unit collided with "1.0" of |dPCE|)
            T(x - 0.02, y + E_H / 2, E_UNIT[k], rotation=90, fontsize=7.0,
              ha="center", va="center")
        a = np.abs(np.asarray(D["dev"][k], float))
        px, py = axs[k].transAxes.transform((0.97, 0.95)) / fig.dpi
        T(px, py, "%.3f" % float(np.nanmedian(a)), fontsize=7.0,
          ha="right", va="top")

    T((x1 + x2 + E_W) / 2.0, 0.05,
      "one predicted curve has no downward zero crossing and is excluded\n"
      "from  |\u0394V$_{oc}$|, |\u0394FF|  and  |\u0394PCE|  ($n$ = 44)",
      fontsize=7.0, ha="center", va="bottom", linespacing=1.35)

    bad = canvas_text_out(fig)
    fig.savefig(os.path.join(PREV, "Fig4de_preview.png"), dpi=600,
                facecolor="white")
    fig.savefig(os.path.join(PREV, "Fig4de_preview.pdf"), facecolor="white")
    plt.close(fig)
    return bad


# ------------------------------------------------------------------ main ----
def box_stats(a):
    a = np.asarray(a, float)
    q1, q3 = np.percentile(a, 25), np.percentile(a, 75)
    iqr = q3 - q1
    return dict(n=a.size, min=float(a.min()), q1=float(q1),
                median=float(np.median(a)), q3=float(q3),
                whisker_lo=float(a[a >= q1 - 1.5 * iqr].min()),
                whisker_hi=float(a[a <= q3 + 1.5 * iqr].max()),
                max=float(a.max()))


def main():
    fig = new_fig(D_W, D_H)
    draw_d(fig, 0.0, 0.0)
    assert not canvas_text_out(fig), canvas_text_out(fig)
    save(fig, os.path.join(FIG, "Fig4d"))

    for k in E_ORDER:
        fig = new_fig(E_W, E_H)
        draw_e(fig, 0.0, 0.0, k)
        assert not canvas_text_out(fig), canvas_text_out(fig)
        save(fig, os.path.join(FIG, "Fig4e_" + k))

    bad = build_preview()
    print("preview text outside canvas:", bad)

    rows = []
    for k, _ in WINDOWS:
        for v in np.asarray(D["rm"][k], float):
            rows.append(dict(window=k, rmse_mA_cm2=v))
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "Figure4d_per_sample.csv"),
                              index=False)

    rows = []
    for k in E_ORDER:
        a = np.abs(np.asarray(D["dev"][k], float))
        for v in a[np.isfinite(a)]:
            rows.append(dict(metric=k, abs_dev=v))
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "Figure4e_per_sample.csv"),
                              index=False)

    stat = []
    for k, _ in WINDOWS:
        stat.append(dict(panel="d", group=k,
                         unit="mA cm-2", **box_stats(D["rm"][k])))
    for k in E_ORDER:
        a = np.abs(np.asarray(D["dev"][k], float))
        stat.append(dict(panel="e", group=k,
                         unit={"Jsc": "mA cm-2", "Voc": "V", "FF": "-",
                               "PCE": "pp"}[k],
                         **box_stats(a[np.isfinite(a)])))
    pd.DataFrame(stat).to_csv(os.path.join(DATA, "Figure4de_box_stats.csv"),
                              index=False)
    print("wrote figures, preview and tables")


if __name__ == "__main__":
    main()
