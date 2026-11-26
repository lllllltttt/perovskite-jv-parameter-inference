# -*- coding: utf-8 -*-
"""Figure 3 panels (a) and (b) — shared Y axes, supervisor request 2026-11-12.

Supervisor instruction
----------------------
"a, b share the Y axes; only (a) keeps the Y axis title, the tick numbers and
the legend; (b) does not repeat them."

State found before the change (verified here in code, not from a screenshot)
---------------------------------------------------------------------------
Both panels were already built from one geometry and one pair of axis
specifications, so nothing about the ranges or the tick positions had to move:

    canvas            3.30 x 2.70 in for both
    upper axes rect   x 0.62 in, width 2.62 in, y 1.04 in, height 1.48 in
    lower axes rect   x 0.62 in, width 2.62 in, y 0.42 in, height 0.62 in
    J axis            ylim -11.2 .. 32.0, yticks -10, 0, 10, 20
    residual axis     ylim -7.1316 .. 7.1316, yticks -5, 0, 5
    x axis            0.0 .. 1.32, ticks 0.0 / 0.5 / 1.0 (lower axes only)

Therefore the only edit is subtractive and confined to (b): the four upper and
three lower Y tick *labels* and the Curve i / Curve j legend are not drawn.
Tick marks (3.0 pt, outward), spines, x ticks and every drawn curve are
untouched.  Because the axes are placed with explicit add_axes rectangles and
not with a layout engine, hiding text cannot resize or shift anything.

Everything else is byte-for-byte the accepted 2026-11-11 construction:
same colours (#4C72B0 solid i, #DD8452 dashed j), line widths (1.3 / 1.2 /
1.1 pt), dash pattern, residual direction (J_j - J_i), data and sample pairs.

No axis titles, panel letters or figure-level text are baked in; those are
listed in labels_and_caption.txt.  The preview carries them for checking only.
"""
import hashlib
import json
import os
import shutil

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

try:
    __import__("sys").stdout.reconfigure(errors="replace")
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

SRC_PKG = os.path.join(os.path.dirname(OUT), "20261111_fig345_standalone_revision")
SRC = os.path.join(SRC_PKG, "data_used")

# ------------------------------------------------------------------ style --
FONT = "Arial"
INK = "#1a1a1a"
GREY = "#bbbbbb"
C_I = "#4C72B0"      # curve i, solid
C_J = "#DD8452"      # curve j, dashed

FS_TICK = 7.0
FS_AXLAB = 7.5
FS_LEG = 7.0
FS_LETTER = 8.5

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

XLO, XHI = 0.0, 1.32
LIM_J = (-11.2, 32.0)              # shared J-V scale, both panels
LIM_R = (-7.1316, 7.1316)          # shared signed-residual scale, both panels
YT_J = [-10, 0, 10, 20]
YT_R = [-5, 0, 5]
XT = [0.0, 0.5, 1.0]

# preview assembly (checking only; the real assembly is done in PowerPoint)
PV_W = 0.06 + 3.30 + 0.10 + 3.30 + 0.06
PV_H = 0.08 + CH + 0.32
COL_X = [0.06, 3.46]
PANEL_Y = 0.32


def fmt_num(v, nd=1):
    s = ("%." + str(nd) + "f") % v
    if s.endswith(".0"):
        s = s[:-2]
    return s.replace("-", "−")


# -------------------------------------------------------------- data load --
def load():
    curves = pd.read_csv(os.path.join(SRC, "fig3_case_curves.csv"))
    summ = pd.read_csv(os.path.join(SRC, "fig3_case_summary.csv"))

    cases = {}
    for tag, i, j in (("(a)", 2890, 5067), ("(b)", 500, 4560)):
        c = curves[curves["case"] == tag].sort_values("voltage_V")
        V = c["voltage_V"].to_numpy()
        Ji = c["J_i_mA_cm2"].to_numpy()
        Jj = c["J_j_mA_cm2"].to_numpy()
        dJ = c["residual_Jj_minus_Ji_mA_cm2"].to_numpy()
        assert len(V) == 131 and abs(V[0]) < 1e-12 and abs(V[-1] - 1.3) < 1e-12
        # the strip must be J_j - J_i, not |dJ|
        assert np.abs((Jj - Ji) - dJ).max() < 1e-12
        s = summ[summ["case"] == tag].iloc[0]
        assert abs(s["test_index_i"] - i) < 0.5 and abs(s["test_index_j"] - j) < 0.5
        assert abs(np.abs(dJ).max() - s["max_abs_dJ_mA_cm2"]) < 1e-9
        cases[tag] = dict(V=V, Ji=Ji, Jj=Jj, dJ=dJ, idx=(i, j))

    # data extents that the shared scales have to contain
    for tag, c in cases.items():
        c["J_min"] = float(min(c["Ji"].min(), c["Jj"].min()))
        c["J_max"] = float(max(c["Ji"].max(), c["Jj"].max()))
        c["r_min"] = float(c["dJ"].min())
        c["r_max"] = float(c["dJ"].max())
    union = dict(J_min=min(c["J_min"] for c in cases.values()),
                 J_max=max(c["J_max"] for c in cases.values()),
                 r_min=min(c["r_min"] for c in cases.values()),
                 r_max=max(c["r_max"] for c in cases.values()))
    return cases, union


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


LEG_AB = dict(loc="upper right", frameon=False, fontsize=FS_LEG,
              handlelength=1.10, handletextpad=0.35, labelspacing=0.15,
              borderpad=0.03, borderaxespad=0.40)


def draw_ab(axj, axr, case, hide_y):
    """Draw one panel. hide_y=True is panel (b): tick marks stay, tick labels
    and the Curve i / Curve j legend are not created."""
    V, Ji, Jj, dJ = case["V"], case["Ji"], case["Jj"], case["dJ"]
    axj.plot(V, Ji, color=C_I, lw=1.3, solid_capstyle="butt", zorder=3,
             label="Curve $i$")
    axj.plot(V, Jj, color=C_J, lw=1.2, ls=(0, (4.0, 2.0)), zorder=4,
             dash_capstyle="butt", label="Curve $j$")
    axj.set_xlim(XLO, XHI)
    axj.set_ylim(*LIM_J)
    axj.set_yticks(YT_J)
    axj.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 0)))
    axj.tick_params(axis="x", which="both", bottom=False, top=False,
                    labelbottom=False)
    style(axj)
    leg = None
    if not hide_y:
        leg = axj.legend(**LEG_AB)
        for t, s in zip(leg.get_texts(), ("Curve $i$", "Curve $j$")):
            t.set_size(FS_LEG)
            assert t.get_text() == s, (t.get_text(), s)

    axr.axhline(0.0, color=GREY, lw=0.7, ls=(0, (3.0, 2.5)), zorder=2)
    axr.plot(V, dJ, color=C_J, lw=1.1, solid_capstyle="butt", zorder=3)
    axr.set_xlim(XLO, XHI)
    axr.set_ylim(*LIM_R)
    axr.set_xticks(XT)
    axr.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 1)))
    axr.set_yticks(YT_R)
    axr.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_num(v, 0)))
    axr.spines["top"].set_visible(False)
    style(axr)

    if hide_y:
        # tick marks and frame stay; only the numbers go
        for ax in (axj, axr):
            ax.tick_params(axis="y", which="both", labelleft=False,
                           labelright=False)
    return leg


# ------------------------------------------------------------ measurements --
def bbox_in(fig, ax):
    fig.canvas.draw()
    bb = ax.get_window_extent(fig.canvas.get_renderer())
    return [bb.x0 / fig.dpi, bb.y0 / fig.dpi,
            bb.width / fig.dpi, bb.height / fig.dpi]


def tick_y_px(fig, ax):
    fig.canvas.draw()
    return [float(ax.transData.transform((0.0, y))[1]) for y in ax.get_yticks()]


def clearance_pt(ax, lo, hi):
    """Empty distance between the data extent and each end of the axis, pt."""
    y0, y1 = ax.get_ylim()
    h_in = ax.get_window_extent().height / ax.figure.dpi
    span = y1 - y0
    return dict(bottom_pt=round((lo - y0) / span * h_in * 72.0, 2),
                top_pt=round((y1 - hi) / span * h_in * 72.0, 2))


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


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- preview --
def build_preview(cases):
    fig = plt.figure(figsize=(PV_W, PV_H), dpi=100)
    fig.patch.set_facecolor("white")

    def T(x, y, s, size=FS_AXLAB, ha="center", va="center", rot=0):
        fig.text(x / PV_W, 1.0 - y / PV_H, s, fontsize=size, color=INK,
                 ha=ha, va=va, rotation=rot)

    for col, tag in ((0, "(a)"), (1, "(b)")):
        x0 = COL_X[col]
        axj, axr = ax_ab(fig, x0, PANEL_Y, PV_W, PV_H)
        draw_ab(axj, axr, cases[tag], hide_y=(col == 1))
        T(x0 + ML, PANEL_Y - 0.075, tag, FS_LETTER, ha="left", va="bottom")
        T(x0 + ML + PW / 2.0, PANEL_Y + CH - 0.10, "Voltage (V)", FS_AXLAB,
          va="top")
        if col == 0:                       # (a) carries the shared Y titles
            T(x0 + 0.150, PANEL_Y + MT + HJ / 2.0,
              "J (mA cm$^{-2}$)", FS_AXLAB, ha="center", va="center", rot=90)
            T(x0 + 0.150, PANEL_Y + MT + HJ + HR / 2.0,
              "J$_j$ − J$_i$\n(mA cm$^{-2}$)", FS_AXLAB, ha="center",
              va="center", rot=90)
    return fig


def main():
    cases, union = load()
    qa = {"request": "2026-11-12 supervisor: a/b share the Y axes; only (a) "
                     "keeps the Y titles, tick numbers and legend",
          "before": {}, "after": {}, "checks": {}}

    # ---- 1. what was measured before any change --------------------------
    qa["before"] = dict(
        canvas_in=[CW, CH],
        axes_rect_j_in=[ML, MB + HR, PW, HJ],
        axes_rect_residual_in=[ML, MB, PW, HR],
        ylim_j=list(LIM_J), yticks_j=YT_J,
        ylim_residual=list(LIM_R), yticks_residual=YT_R,
        xlim=[XLO, XHI], xticks=XT,
        data_extent_union_in={k: round(v, 4) for k, v in union.items()},
        note="identical specification was already used for (a) and (b); only "
             "the Y tick labels and the legend of (b) are removed")

    # ---- 2. build both panels -------------------------------------------
    figs, legs, bboxes, ticks = {}, {}, {}, {}
    for kind, tag in (("a", "(a)"), ("b", "(b)")):
        fig = plt.figure(figsize=(CW, CH), dpi=100)
        fig.patch.set_facecolor("white")
        axj, axr = ax_ab(fig, 0, 0, CW, CH)
        leg = draw_ab(axj, axr, cases[tag], hide_y=(kind == "b"))
        figs[kind], legs[kind] = (fig, axj, axr), leg
        fig.canvas.draw()
        bad = check_text_inside(fig)
        assert not bad, bad
        bboxes[kind] = dict(j=bbox_in(fig, axj), r=bbox_in(fig, axr))
        ticks[kind] = dict(y_j=[round(v, 2) for v in tick_y_px(fig, axj)],
                           y_r=[round(v, 2) for v in tick_y_px(fig, axr)],
                           yticks_j=[float(v) for v in axj.get_yticks()],
                           yticks_r=[float(v) for v in axr.get_yticks()])

    # ---- 3. the Y axes really are shared --------------------------------
    for key in ("yticks_j", "yticks_r"):
        assert ticks["a"][key] == ticks["b"][key], key
    for key in ("y_j", "y_r"):
        d = max(abs(x - y) for x, y in zip(ticks["a"][key], ticks["b"][key]))
        assert d < 1e-9, (key, d)
    qa["checks"]["shared_y"] = dict(
        yticks_j=ticks["a"]["yticks_j"],
        yticks_r=ticks["a"]["yticks_r"],
        max_tick_mark_position_delta_px=max(
            max(abs(x - y) for x, y in zip(ticks["a"]["y_j"],
                                           ticks["b"]["y_j"])),
            max(abs(x - y) for x, y in zip(ticks["a"]["y_r"],
                                           ticks["b"]["y_r"]))),
        ok=True)

    # ---- 4. identical axes geometry, and no clipping ---------------------
    for part in ("j", "r"):
        d = max(abs(x - y) for x, y in zip(bboxes["a"][part],
                                           bboxes["b"][part]))
        assert d < 1e-6, (part, d, bboxes["a"][part], bboxes["b"][part])
    qa["checks"]["identical_axes_geometry"] = dict(
        j_axes_box_a_in=[round(v, 6) for v in bboxes["a"]["j"]],
        j_axes_box_b_in=[round(v, 6) for v in bboxes["b"]["j"]],
        r_axes_box_a_in=[round(v, 6) for v in bboxes["a"]["r"]],
        r_axes_box_b_in=[round(v, 6) for v in bboxes["b"]["r"]],
        max_delta_in=0.0, ok=True)

    clip = {}
    for kind, tag in (("a", "(a)"), ("b", "(b)")):
        axj, axr = figs[kind][1], figs[kind][2]
        c = cases[tag]
        clip[kind] = dict(
            J_clearance_pt=clearance_pt(axj, c["J_min"], c["J_max"]),
            residual_clearance_pt=clearance_pt(axr, c["r_min"], c["r_max"]),
            J_min=c["J_min"], J_max=c["J_max"],
            residual_min=c["r_min"], residual_max=c["r_max"])
        assert clip[kind]["J_clearance_pt"]["bottom_pt"] > 2.0
        assert clip[kind]["J_clearance_pt"]["top_pt"] > 2.0
        assert clip[kind]["residual_clearance_pt"]["bottom_pt"] > 2.0
        assert clip[kind]["residual_clearance_pt"]["top_pt"] > 2.0
    qa["checks"]["no_clipping"] = clip

    # ---- 5. what each panel now shows -----------------------------------
    shown = {}
    for kind in ("a", "b"):
        axj, axr = figs[kind][1], figs[kind][2]
        fig = figs[kind][0]
        fig.canvas.draw()
        shown[kind] = dict(
            y_ticklabels_j=[t.get_text() for t in axj.get_yticklabels()
                            if t.get_visible()],
            y_ticklabels_r=[t.get_text() for t in axr.get_yticklabels()
                            if t.get_visible()],
            legend=None if legs[kind] is None
            else [t.get_text() for t in legs[kind].get_texts()],
            y_tick_marks_j=len([t for t in axj.yaxis.get_major_ticks()
                                if t.tick1line.get_visible()]),
            y_tick_mark_len_pt=axj.yaxis.get_major_ticks()[0].tick1line
                               .get_markersize(),
            x_ticklabels=[t.get_text() for t in axr.get_xticklabels()
                          if t.get_visible()],
            spines_visible_j=sorted(k for k, sp in axj.spines.items()
                                    if sp.get_visible()),
            spines_visible_r=sorted(k for k, sp in axr.spines.items()
                                    if sp.get_visible()))
    assert shown["a"]["y_ticklabels_j"] == ["−10", "0", "10", "20"], shown["a"]
    assert shown["a"]["y_ticklabels_r"] == ["−5", "0", "5"], shown["a"]
    assert shown["b"]["y_ticklabels_j"] == [], shown["b"]
    assert shown["b"]["y_ticklabels_r"] == [], shown["b"]
    assert shown["a"]["legend"] == ["Curve $i$", "Curve $j$"]
    assert shown["b"]["legend"] is None
    assert shown["a"]["y_tick_marks_j"] == shown["b"]["y_tick_marks_j"] == 4
    assert shown["a"]["y_tick_mark_len_pt"] == shown["b"]["y_tick_mark_len_pt"]
    assert shown["a"]["x_ticklabels"] == shown["b"]["x_ticklabels"] == \
        ["0", "0.5", "1"], shown["a"]["x_ticklabels"]
    qa["checks"]["visible_text"] = shown

    # ---- 6. export -------------------------------------------------------
    manifest = {}
    for kind in ("a", "b"):
        fig = figs[kind][0]
        p = save_all(fig, "Fig3" + kind)
        for ext in ("png", "pdf", "svg"):
            manifest["figures/Fig3%s.%s" % (kind, ext)] = sha(p + "." + ext)
        qa["after"]["Fig3" + kind] = dict(
            canvas_in=[CW, CH],
            axes_rect_j_in=[round(v, 4) for v in bboxes[kind]["j"]],
            axes_rect_residual_in=[round(v, 4) for v in bboxes[kind]["r"]],
            ylim_j=list(figs[kind][1].get_ylim()),
            ylim_residual=list(figs[kind][2].get_ylim()),
            yticks_j=[float(v) for v in figs[kind][1].get_yticks()],
            yticks_residual=[float(v) for v in figs[kind][2].get_yticks()],
            y_tick_labels="drawn" if kind == "a" else "hidden",
            y_axis_title_inside_pdf="none (axis titles are PowerPoint text)",
            y_axis_title_policy=("add for (a) only" if kind == "a"
                                 else "do not add"),
            legend="drawn" if kind == "a" else "hidden",
            n_points=131,
            residual_is_Jj_minus_Ji=bool(
                np.allclose(figs[kind][2].lines[-1].get_ydata(),
                            cases["(%s)" % kind]["Jj"]
                            - cases["(%s)" % kind]["Ji"])))
        plt.close(fig)

    # ---- 7. preview ------------------------------------------------------
    pv = build_preview(cases)
    pv.canvas.draw()
    bad = check_text_inside(pv)
    assert not bad, bad
    pv.savefig(os.path.join(PREV, "Fig3ab_preview.png"), dpi=600,
               facecolor="white", edgecolor="none")
    pv.savefig(os.path.join(PREV, "Fig3ab_preview.pdf"), facecolor="white",
               edgecolor="none")
    plt.close(pv)
    qa["preview"] = dict(size_in=[PV_W, PV_H],
                         size_mm=[round(PV_W * 25.4, 2),
                                  round(PV_H * 25.4, 2)],
                         gutter_in=round(COL_X[1] - COL_X[0] - CW, 3),
                         text_outside_canvas=bad)

    with open(os.path.join(QA, "qa_fig3ab.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    with open(os.path.join(QA, "hashes_figures.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(qa["after"], indent=2, ensure_ascii=False))
    print("preview:", qa["preview"]["size_mm"], "mm")


if __name__ == "__main__":
    main()
