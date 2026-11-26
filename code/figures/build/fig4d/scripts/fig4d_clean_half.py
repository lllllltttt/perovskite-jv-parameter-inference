# -*- coding: utf-8 -*-
"""Figure 4(d) - text-free panel, half of the previous right-hand extension.

History of this panel's x window (left end never moved):

  2026-11-11  xlim  -0.55 .. 2.55    installed panel (numbers inside the boxes)
  earlier      xlim  -0.55 .. 2.90    right end +0.35 - judged too wide
  THIS FILE    xlim  -0.55 .. 2.725   right end +0.175

i.e. new right end = old right end + 0.5 x (2.90 - 2.55), exactly as asked.

  blank box-3 right edge (x = 2.25) -> right frame:
      15.58 pt (original) -> 30.33 pt (too wide) -> 23.35 pt (this file)
  "5.19" ink is 12.96 pt wide, so typing it 2 pt from the box still leaves
  8.4 pt to the frame - a small but visible margin, as requested.

The canvas and the plot rectangle are NOT touched (the panel is not squeezed):
only the visible x window changes, 3.10 -> 3.275 units, so each box is
24.58 pt wide on paper instead of 25.96 pt.

Still a text-free panel for PowerPoint assembly: only the five y tick numbers
are drawn; y tick numbers, short tick marks on both axes and the four spines
are kept; x category names, axis titles, units, the (d) letter, the n note and
the three medians 2.69 / 0.455 / 5.19 are absent.  Boxes, whiskers, median
lines and all 45 jittered dots per group are drawn exactly as in the
installed panel (same seeds, same colours, same alphas and line widths).

Data come from fig4_forward.collect(), which re-asserts every archived pin of
the frozen model - nothing is recomputed here.
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.text import Text
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from matplotlib.ticker import FixedLocator, NullFormatter

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIG = os.path.join(OUT, "figures")
PREV = os.path.join(OUT, "preview")
QA = os.path.join(OUT, "qa")
for _d in (FIG, PREV, QA):
    os.makedirs(_d, exist_ok=True)

BASE = r"E:\project\work1"
MS_SCRIPTS = os.path.join(BASE, "20261006",
                          "manuscript_figures_SI_integrated_v2_layout_final",
                          "scripts")
sys.path.insert(0, MS_SCRIPTS)
import figstyle as st          # noqa: E402
import fig4_forward as f4      # noqa: E402

plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

INK = st.INK
FS_TICK = st.FS_TICK            # 7.5 pt
TICK_LEN = 3.0
TICK_PAD = 2.5

# ------------------------------------------------------------------ sizes ---
D_W, D_H = 2.60, 2.44
D_M = dict(right=0.06, bottom=0.34, top=0.05)
BOX_W = 0.50
JIT = 0.13
MS = 2.2
ALPHA_PT = 0.45
ALPHA_BOX = 0.22

WINDOWS = [("full", "Full curve\n(0\u20131.3 V)"),
           ("le1", "0\u20131.0 V"),
           ("gt1", "> 1.0 V")]
Wd = [st.OKABE_ITO[0], st.OKABE_ITO[2], st.OKABE_ITO[3]]
D_YLBL = ["0.01", "0.1", "1", "10", "100"]

XLIM_OLD = (-0.55, 2.55)        # installed 2026-11-11 panel
XLIM_WIDE = (-0.55, 2.90)       # previous export, judged too wide
XLIM_NEW = (XLIM_OLD[0],
            round(XLIM_OLD[1]
                  + 0.5 * (XLIM_WIDE[1] - XLIM_OLD[1]), 6))    # 2.725
assert XLIM_NEW[0] == XLIM_OLD[0]
assert abs(XLIM_NEW[1] - 2.725) < 1e-12

D = f4.collect()


def text_pt(s, size=FS_TICK):
    return TextPath((0, 0), s, prop=FontProperties(family="Arial",
                                                   size=size)).get_extents().width


def left_margin(labels, gap_pt=3.5):
    return (TICK_LEN + TICK_PAD + max(text_pt(s) for s in labels) + gap_pt) / 72.0


D_LEFT = left_margin(D_YLBL)
AX_W_IN = D_W - D_LEFT - D_M["right"]
AX_W_PT = AX_W_IN * 72.0


def unit_pt(xlim):
    return AX_W_PT / (xlim[1] - xlim[0])


# ---------------------------------------------------------------- drawing ---
def draw_box_group(ax, vals, pos, color, seed):
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
    return vals, jit


def draw_d(fig):
    fw, fh = fig.get_size_inches()
    ax = fig.add_axes([D_LEFT / fw, D_M["bottom"] / fh, AX_W_IN / fw,
                       (D_H - D_M["bottom"] - D_M["top"]) / fh])
    recs = []
    for i, (k, _) in enumerate(WINDOWS):
        v, jit = draw_box_group(ax, D["rm"][k], i, Wd[i], 2026 + i)
        recs.append((i, v, jit))

    ax.set_yscale("log")
    ax.set_ylim(0.01, 200.0)
    ax.set_xlim(*XLIM_NEW)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["", "", ""])     # tick marks kept, names not drawn
    ax.yaxis.set_major_locator(FixedLocator([0.01, 0.1, 1.0, 10.0, 100.0]))
    ax.set_yticklabels(D_YLBL)
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(False)
    st.configure_axes(ax)
    ax.tick_params(axis="y", which="minor", length=2.0, width=0.6, color=INK)
    ax.tick_params(axis="x", which="major", labelbottom=False)
    return ax, recs


def new_fig(w, h):
    fig = plt.figure(figsize=(w, h))
    fig.patch.set_facecolor("white")
    return fig


def flatten_png(path, dpi):
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    bg.save(path, dpi=(dpi, dpi))


def save(fig, path, dpi=600):
    fig.savefig(path + ".png", dpi=dpi, facecolor="white")
    flatten_png(path + ".png", dpi)
    fig.savefig(path + ".pdf", facecolor="white")
    fig.savefig(path + ".svg", facecolor="white")


def canvas_text_out(fig):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bad = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        b = t.get_window_extent(renderer=r)
        if b.width <= 1.0 and b.height <= 1.0:
            continue
        if (b.x0 < -0.5 or b.y0 < -0.5 or b.x1 > fig.bbox.x1 + 0.5
                or b.y1 > fig.bbox.y1 + 0.5):
            bad.append((t.get_text()[:24], round(b.x0, 1), round(b.y0, 1),
                        round(b.x1, 1), round(b.y1, 1)))
    return bad


def box_stats(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    q1, q3 = np.percentile(a, 25), np.percentile(a, 75)
    iqr = q3 - q1
    return dict(n=int(a.size), min=float(a.min()), q1=float(q1),
                median=float(np.median(a)), q3=float(q3),
                whisker_lo=float(a[a >= q1 - 1.5 * iqr].min()),
                whisker_hi=float(a[a <= q3 + 1.5 * iqr].max()),
                max=float(a.max()))


def main():
    qa = {"panels": {}, "checks": {}}

    fig = new_fig(D_W, D_H)
    ax, recs = draw_d(fig)
    bad = canvas_text_out(fig)
    assert not bad, bad
    save(fig, os.path.join(FIG, "Fig4d_clean_half"))
    plt.close(fig)

    dstat = {k: box_stats(D["rm"][k]) for k, _ in WINDOWS}

    # ---- values, dots and scales must be the accepted ones ---------------
    assert abs(dstat["full"]["median"] - 2.69263) < 5e-4
    assert abs(dstat["le1"]["median"] - 0.45535) < 5e-4
    assert abs(dstat["gt1"]["median"] - 5.19160) < 5e-4
    old = json.load(open(os.path.join(
        BASE, "20261111_fig345_standalone_revision", "qa", "qa_fig4.json"),
        encoding="utf-8"))["panels"]["Fig4d"]["stats"]
    for k in dstat:
        for f in ("n", "min", "q1", "median", "q3", "whisker_lo",
                  "whisker_hi", "max"):
            assert abs(dstat[k][f] - old[k][f]) < 1e-9, (k, f)
    qa["checks"]["stats_identical_to_2026_11_11"] = True

    rng_check = {k: np.random.default_rng(2026 + i).uniform(-JIT, JIT, 45)
                 for i, (k, _) in enumerate(WINDOWS)}
    for i, (k, _) in enumerate(WINDOWS):
        assert np.allclose(recs[i][2], rng_check[k], atol=0, rtol=0)
    qa["checks"]["jitter_seeds"] = [2026, 2027, 2028]

    u_old, u_wide, u_new = (unit_pt(XLIM_OLD), unit_pt(XLIM_WIDE),
                            unit_pt(XLIM_NEW))
    a = BOX_W / 2.0
    blank = lambda xl, u: (xl[1] - (2 + a)) * u          # noqa: E731
    w519 = 12.96                    # ink width of "5.19", measured at 600 dpi
    qa["checks"]["x_geometry"] = dict(
        xlim_original=list(XLIM_OLD), xlim_previous= list(XLIM_WIDE),
        xlim_new=list(XLIM_NEW),
        right_delta_vs_original=round(XLIM_NEW[1] - XLIM_OLD[1], 4),
        right_delta_vs_previous=round(XLIM_NEW[1] - XLIM_WIDE[1], 4),
        half_rule_check=round(XLIM_OLD[1] + 0.5 * (XLIM_WIDE[1]
                                                   - XLIM_OLD[1]), 4),
        pt_per_unit=[round(u_old, 3), round(u_wide, 3), round(u_new, 3)],
        right_blank_pt=[round(blank(XLIM_OLD, u_old), 2),
                        round(blank(XLIM_WIDE, u_wide), 2),
                        round(blank(XLIM_NEW, u_new), 2)],
        box_width_pt=[round(BOX_W * u_old, 2), round(BOX_W * u_wide, 2),
                      round(BOX_W * u_new, 2)],
        text_5_19_width_pt=w519,
        blank_after_text_pt=round(blank(XLIM_NEW, u_new) - 2.0 - w519, 2))
    assert abs(qa["checks"]["x_geometry"]["half_rule_check"] - 2.725) < 1e-9
    assert qa["checks"]["x_geometry"]["blank_after_text_pt"] > 6.0, \
        qa["checks"]["x_geometry"]

    qa["panels"]["Fig4d_clean_half"] = dict(
        file="Fig4d_clean_half",
        canvas_in=[D_W, D_H],
        axes_rect_in=[round(D_LEFT, 5), D_M["bottom"], round(AX_W_IN, 5),
                      D_H - D_M["bottom"] - D_M["top"]],
        xlim=list(XLIM_NEW), xlim_original=list(XLIM_OLD),
        ylim=[0.01, 200.0], yticks=list(D_YLBL),
        xticks=[0, 1, 2], xticklabels_visible=False,
        text_in_image=["0.01", "0.1", "1", "10", "100"],
        stats=dstat)
    qa["checks"]["changed_vs_original"] = dict(
        xlim=[list(XLIM_OLD), list(XLIM_NEW)],
        right_end=[2.55, 2.725, "(= 2.55 + 0.5 x (2.90 - 2.55))"],
        right_blank_pt=[15.58, qa["checks"]["x_geometry"]["right_blank_pt"][2]],
        medians_printed="removed (typed in PowerPoint)",
        x_category_labels="removed",
        data="unchanged", box_stats="unchanged", jitter="unchanged",
        canvas="unchanged", axes_rect_in="unchanged",
        ylim="unchanged", yticks="unchanged")

    with open(os.path.join(QA, "qa_fig4d_half.json"), "w",
              encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    print(json.dumps(qa["checks"]["x_geometry"], indent=2, ensure_ascii=False))
    return qa


if __name__ == "__main__":
    main()
