# -*- coding: utf-8 -*-
"""Figure 2 final scatter assets: six D-style density panels + two colour keys.

Deliverables for manual assembly in PowerPoint / Illustrator:

* six standalone panels (a1 a2 a3 blue, b1 b2 b3 orange), no titles, no panel
  letters, no axis names, no rho -- only points, the y = x guide, the frame,
  ticks and tick numbers;
* two standalone vertical colour keys ("Samples per bin");
* one assembly preview with all annotation present.

All panels share one frozen test set (n = 15,307), one point size, one alpha,
one draw order. Blue panels share one count->colour mapping, orange panels
share another. The reviewed D panel (b3) keeps its exact binning and counts.

Nothing in the manuscript, SI, official Figure 2 or the earlier D trial is
modified.
"""
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
PANEL_DIR = os.path.join(OUT, "panels")
CB_DIR = os.path.join(OUT, "colorbars")
PREVIEW_DIR = os.path.join(OUT, "preview")
QA_DIR = os.path.join(OUT, "qa")

BASE = r"E:\project\work1"
OLD = os.path.join(BASE, "20261108_fig2_supervisor_revision")
D_DIR = os.path.join(BASE, "20261109_fig2_b3_trial_D")

sys.path.insert(0, os.path.join(OLD, "scripts"))
sys.path.insert(0, os.path.join(D_DIR, "scripts"))
import fig2_data as FD
import fig2_b3_D as M

# ------------------------------------------------------------------ style --
INK = M.INK
MUTED = M.MUTED
FONT = M.FONT

FS_TICK = 7.0
FS_AXLAB = 7.5
FS_RHO = 7.5
FS_LETTER = 8.5
FS_COL = 8.0
FS_GROUP = 8.5

S_DOT = M.S_DOT
ALPHA_D = M.ALPHA_D
NBINS = M.NBINS
GUIDE_LW = 0.6

# panel canvas identical to the reviewed D panel: 2.3333 x 2.4833 in
P = M.P
ML, MR, MB, MT = M.ML, M.MR, M.MB, M.MT
WF, HF = P + ML + MR, P + MB + MT

# standalone colour-key canvas: same height as a panel, bar centred
CB_W = 0.60
CB_BAR_W = 0.085
CB_BAR_H = 1.20

CMAP_BLUE = LinearSegmentedColormap.from_list(
    "dos_density_blue",
    [(0.00, "#AFC3DF"), (0.35, "#86A3CE"), (0.60, "#4C72B0"),
     (0.80, "#36578C"), (1.00, "#1F3560")])
CMAP_ORANGE = M.CMAP

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

MINUS = "\u2212"
unified = M.unified


# --------------------------------------------------------------- preview text
def R(t):
    return ("r", t)


def I(t):
    return ("i", t)


def SB(t):
    return ("sub", t)


def SBI(t):
    return ("subi", t)


def SP(t):
    return ("sup", t)


def S():
    return ("sp", "")


def SPACE2():
    return ("sp2", "")


LOG = ("op", "log")


def _mathify(kind, text):
    if kind == "i":
        return text
    if kind == "op":
        return "\\" + text
    if kind == "sub":
        return "_{\\mathrm{%s}}" % text
    if kind == "subi":
        return "_{%s}" % text
    if kind == "sup":
        return "^{\\mathrm{%s}}" % text
    if kind == "supi":
        return "^{%s}" % text
    raise ValueError(kind)


def to_mathtext(runs):
    parts, buf, mode = [], [], None

    def flush():
        if not buf:
            return
        parts.append(("$" + "".join(buf) + "$") if mode == "m" else "".join(buf))
        del buf[:]

    for kind, text in runs:
        if kind == "r":
            if mode != "t":
                flush()
                mode = "t"
            buf.append(text)
        elif kind in ("sp", "sp2"):
            if mode != "t":
                flush()
                mode = "t"
            buf.append(" " if kind == "sp" else "  ")
        else:
            if mode != "m":
                flush()
                mode = "m"
            buf.append(_mathify(kind, text))
    flush()
    return "".join(parts)


class TL(object):
    def __init__(self, fig, W, H):
        self.fig, self.W, self.H = fig, W, H

    def mtext(self, x_in, y_in, runs, size, color=INK, ha="left", rot=0.0):
        self.fig.text(x_in / self.W, 1.0 - y_in / self.H,
                      to_mathtext(runs), fontsize=size, color=color, ha=ha,
                      va="baseline", rotation=rot,
                      rotation_mode="anchor" if rot else "default")

    def ptext(self, x_in, y_in, s, size, color=INK, ha="left", va="baseline",
              weight="normal", rot=0.0):
        self.fig.text(x_in / self.W, 1.0 - y_in / self.H, s, fontsize=size,
                      color=color, ha=ha, va=va, fontweight=weight,
                      rotation=rot,
                      rotation_mode="anchor" if rot else "default")


# ------------------------------------------------------------------- data --
FAMILIES = [("mobility", "Mobility"), ("lifetime", "Bulk lifetime"),
            ("DOS", "Density of states")]
UNIT = {
    "mobility": "\u03bcn, \u03bcp (m\u00b2 V\u207b\u00b9 s\u207b\u00b9)",
    "lifetime": "\u03c4n, \u03c4p (s)",
    "DOS": "Nc, Nv (m\u207b\u00b3)",
}

# per-panel display limits are computed below; ticks follow from them.
# The limits are NOT rounded out to the tick grid: each end carries exactly
# PAD_FRAC of the joint span, so the outermost tick may sit inside the frame.
STEP_BLUE = 1.0
STEP_ORANGE = 0.5
PAD_FRAC = 0.02


def pad_limits(lo, hi, frac=PAD_FRAC):
    """Pad both ends by PAD_FRAC of the joint span; no tick-grid rounding.

    The limits are recorded to 4 decimals (0.0001 data units = 0.003 pt on
    the frame), so the values written to checklist.csv are the values used.
    """
    span = hi - lo
    return (round(float(lo - frac * span), 4), round(float(hi + frac * span), 4))


def ticks_between(lo, hi, step):
    k0 = math.ceil(lo / step - 1e-9)
    k1 = math.floor(hi / step + 1e-9)
    vals = [round(i * step, 10) for i in range(k0, k1 + 1)]
    return vals


def load_all():
    coords, _per = FD.load_coordinates()
    data = {}
    for fam in ("a", "r"):
        for lab, _title in FAMILIES:
            t, p, _tr = coords[(fam, lab)]
            rho = float(pearsonr(t, p)[0])
            assert len(t) == 15307
            data[(fam, lab)] = dict(t=t, p=p, rho=rho)
    # archived rho values (fig2_data.ARCHIVE) must be reproduced
    for key, (rho_ref, _red) in FD.ARCHIVE.items():
        assert abs(data[key]["rho"] - rho_ref) < 5e-7, key
    return data


def build_specs(data):
    specs = []
    # pooled orange display range
    lo_o = min(min(data[("r", l)]["t"].min(), data[("r", l)]["p"].min())
               for l, _ in FAMILIES)
    hi_o = max(max(data[("r", l)]["t"].max(), data[("r", l)]["p"].max())
               for l, _ in FAMILIES)
    lim_o = pad_limits(lo_o, hi_o)
    ticks_o = ticks_between(lim_o[0], lim_o[1], STEP_ORANGE)

    for fam in ("a", "r"):
        for col, (lab, title) in enumerate(FAMILIES):
            d = data[(fam, lab)]
            t, p = d["t"], d["p"]
            joint_lo = float(min(t.min(), p.min()))
            joint_hi = float(max(t.max(), p.max()))
            if fam == "a":
                lim = pad_limits(joint_lo, joint_hi)
                ticks = [int(v) for v in
                         ticks_between(lim[0], lim[1], STEP_BLUE)]
                fmt = "%d"
                panel_id = "a%d" % (col + 1)
            else:
                lim, ticks, fmt = lim_o, ticks_o, "%.1f"
                panel_id = "b%d" % (col + 1)

            # density grid: the reviewed D binning for b3; otherwise the same
            # recipe (x over true +-0.05, y over joint +-0.05), independent of
            # the final display limits
            if fam == "r" and lab == "DOS":
                box = (M.XLIM, M.YLIM)
                historical = True
            else:
                box = ((float(t.min()) - 0.05, float(t.max()) + 0.05),
                       (joint_lo - 0.05, joint_hi + 0.05))
                historical = False

            specs.append(dict(
                id=panel_id, fam=fam, lab=lab, title=title,
                t=t, p=p, rho=d["rho"],
                lim=lim, ticks=ticks, fmt=fmt,
                bin_x=box[0], bin_y=box[1], historical=historical,
            ))
    return specs


def compute_counts(specs):
    for s in specs:
        s["counts"], s["H"] = M.binned_counts(
            s["t"], s["p"], s["bin_x"], s["bin_y"], NBINS)
        s["max_count"] = int(s["counts"].max())
        s["occupied"] = int((s["H"] > 0).sum())
    vmax_b = max(s["max_count"] for s in specs if s["fam"] == "a")
    vmax_o = max(s["max_count"] for s in specs if s["fam"] == "r")
    norm_b = LogNorm(vmin=1.0, vmax=float(vmax_b))
    norm_o = LogNorm(vmin=1.0, vmax=float(vmax_o))
    for s in specs:
        s["norm"] = norm_b if s["fam"] == "a" else norm_o
        s["cmap"] = CMAP_BLUE if s["fam"] == "a" else CMAP_ORANGE
    return norm_b, norm_o


# ---------------------------------------------------------------- drawing --
def style_axes(ax):
    ax.tick_params(axis="both", which="major", direction="out", length=3.0,
                   width=0.7, labelsize=FS_TICK, colors=INK, top=False,
                   right=False, pad=2.5)
    for sp in ax.spines.values():
        sp.set_color(INK)
        sp.set_linewidth(0.7)
    ax.set_facecolor("none")


def draw_panel(ax, s):
    order = np.argsort(s["counts"], kind="stable")
    ax.scatter(s["t"][order], s["p"][order], s=S_DOT,
               c=s["counts"][order], cmap=s["cmap"], norm=s["norm"],
               alpha=ALPHA_D, linewidths=0, edgecolors="none",
               rasterized=True, zorder=2)
    lo, hi = s["lim"]
    ax.plot([lo, hi], [lo, hi], ls=(0, (4.0, 2.4)), color=MUTED,
            lw=GUIDE_LW, zorder=3, solid_capstyle="butt",
            dash_capstyle="butt")
    ax.set_xlim(*s["lim"])
    ax.set_ylim(*s["lim"])
    ax.set_xticks(s["ticks"])
    ax.set_yticks(s["ticks"])
    ax.xaxis.set_major_formatter(unified(s["fmt"]))
    ax.yaxis.set_major_formatter(unified(s["fmt"]))
    ax.set_aspect("equal", adjustable="box")
    style_axes(ax)


def panel_fig(s):
    fig = plt.figure(figsize=(WF, HF), dpi=100)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([ML / WF, MB / HF, P / WF, P / HF])
    draw_panel(ax, s)
    return fig, ax


def colorbar_fig(cmap, norm, ticks):
    fig = plt.figure(figsize=(CB_W, HF), dpi=100)
    fig.patch.set_facecolor("white")
    bar_top = (HF - CB_BAR_H) / 2.0
    cax = fig.add_axes([0.10 / CB_W, 1.0 - (bar_top + CB_BAR_H) / HF,
                        CB_BAR_W / CB_W, CB_BAR_H / HF])
    sm = ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, ticks=ticks)
    cb.ax.minorticks_off()
    cb.outline.set_linewidth(0.5)
    cb.outline.set_edgecolor(INK)
    cb.ax.tick_params(labelsize=FS_TICK, length=2.5, width=0.6, colors=INK,
                      pad=2, direction="out")
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: "%d" % v))
    fig.text(0.42 / CB_W, 0.5, "Samples per bin", rotation=90, ha="center",
             va="center", fontsize=FS_RHO, color=INK)
    return fig, cb


# --------------------------------------------------------------- preview ---
PREV_LEFT, PREV_GAP = 0.50, 0.48
Y_GROUP1 = 0.19
Y_COLNAME = 0.445
Y_LETTER1 = 0.605
Y_P1_TOP = 0.688
Y_P1_BOT = Y_P1_TOP + P
Y_XLAB1 = Y_P1_BOT + 0.275
Y_GROUP2 = Y_XLAB1 + 0.245
Y_LETTER2 = Y_GROUP2 + 0.16
Y_P2_TOP = Y_LETTER2 + 0.083
Y_P2_BOT = Y_P2_TOP + P
Y_XLAB2 = Y_P2_BOT + 0.275
PREV_W = 7.32
PREV_H = Y_XLAB2 + 0.12


def panel_left(col):
    return PREV_LEFT + col * (P + PREV_GAP)


def build_preview(specs, norm_b, norm_o, path):
    fig = plt.figure(figsize=(PREV_W, PREV_H), dpi=100)
    fig.patch.set_facecolor("white")
    tl = TL(fig, PREV_W, PREV_H)
    rows = {"a": (Y_P1_TOP, Y_LETTER1, "a"), "r": (Y_P2_TOP, Y_LETTER2, "b")}

    for s in specs:
        col = int(s["id"][1]) - 1
        x0 = panel_left(col)
        y_top = rows[s["fam"]][0]
        ax = fig.add_axes([x0 / PREV_W, 1.0 - (y_top + P) / PREV_H,
                           P / PREV_W, P / PREV_H])
        draw_panel(ax, s)
        tl.mtext(x0 + P / 2.0, y_top + P + 0.275,
                 [R("True "), I("a" if s["fam"] == "a" else "r")],
                 FS_AXLAB, ha="center")
        tl.mtext(x0 - 0.315, y_top + P / 2.0,
                 [R("Predicted "), I("a" if s["fam"] == "a" else "r")],
                 FS_AXLAB, ha="center", rot=90)
        tl.mtext(x0 + P - 0.115, y_top + P - 0.115,
                 [I("\u03c1"), S(), R("="), S(), R("%.3f" % s["rho"])],
                 FS_RHO, ha="right")
        tl.ptext(x0 - 0.02, y_top - 0.075, "(%s)" % s["id"], FS_LETTER,
                 weight="bold")

    for col, (lab, title) in enumerate(FAMILIES):
        tl.ptext(panel_left(col) + P / 2.0, Y_COLNAME, title, FS_COL,
                 ha="center")

    # row labels
    fig.patches.append(Rectangle((PREV_LEFT / PREV_W,
                                  1.0 - (Y_GROUP1 - 0.006) / PREV_H),
                                 0.085 / PREV_W, 0.085 / PREV_H,
                                 transform=fig.transFigure,
                                 facecolor=CMAP_BLUE(0.6),
                                 edgecolor="none", zorder=5))
    tl.mtext(PREV_LEFT + 0.155, Y_GROUP1,
             [R("Shared scale"), SPACE2(), I("a"), R(" = ("), LOG, SB("10"),
              S(), I("p"), SBI("n"), R(" + "), LOG, SB("10"), S(),
              I("p"), SBI("p"), R(")/2")], FS_GROUP)
    fig.patches.append(Rectangle((PREV_LEFT / PREV_W,
                                  1.0 - (Y_GROUP2 - 0.006) / PREV_H),
                                 0.085 / PREV_W, 0.085 / PREV_H,
                                 transform=fig.transFigure,
                                 facecolor=CMAP_ORANGE(0.6),
                                 edgecolor="none", zorder=5))
    tl.mtext(PREV_LEFT + 0.155, Y_GROUP2,
             [R("Electron\u2013hole log-ratio"), SPACE2(), I("r"), R(" = "),
              LOG, SB("10"), R("("), I("p"), SBI("n"), R("/"),
              I("p"), SBI("p"), R(")")], FS_GROUP)

    # one colour key at the right of each row
    bar_x = panel_left(2) + P + 0.10
    for fam, norm, cmap, y_top in (("a", norm_b, CMAP_BLUE, Y_P1_TOP),
                                   ("r", norm_o, CMAP_ORANGE, Y_P2_TOP)):
        yc = y_top + P / 2.0
        bar_top = yc - CB_BAR_H / 2.0
        cax = fig.add_axes([bar_x / PREV_W,
                            1.0 - (bar_top + CB_BAR_H) / PREV_H,
                            CB_BAR_W / PREV_W, CB_BAR_H / PREV_H])
        sm = ScalarMappable(norm=norm, cmap=cmap)
        cb = fig.colorbar(sm, cax=cax, ticks=[1, 2, 5, 10, 20])
        cb.ax.minorticks_off()
        cb.outline.set_linewidth(0.5)
        cb.outline.set_edgecolor(INK)
        cb.ax.tick_params(labelsize=FS_TICK, length=2.5, width=0.6,
                          colors=INK, pad=2, direction="out")
        cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: "%d" % v))
        fig.text((bar_x + CB_BAR_W + 0.235) / PREV_W, 1.0 - yc / PREV_H,
                 "Samples per bin", rotation=90, ha="center", va="center",
                 fontsize=FS_RHO, color=INK)

    items, bad = text_report(fig, PREV_W, PREV_H)
    fig.savefig(path, dpi=600, facecolor="white")
    plt.close(fig)
    return items, bad


# ------------------------------------------------------------------ checks --
def text_report(fig, W, H):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items, bad = [], []
    for t in fig.findobj(Text):
        s = t.get_text()
        if not s.strip():
            continue
        bb = t.get_window_extent(r)
        items.append(s)
        if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > W * fig.dpi + 0.5 \
                or bb.y1 > H * fig.dpi + 0.5:
            bad.append(s)
    return items, bad


def flatten_png(path, dpi=900):
    """Write an opaque white RGB PNG (no alpha channel)."""
    im = Image.open(path)
    if im.mode != "RGB":
        im.convert("RGB").save(path, dpi=(dpi, dpi))


def main():
    for d in (PANEL_DIR, CB_DIR, PREVIEW_DIR, QA_DIR):
        os.makedirs(d, exist_ok=True)

    data = load_all()
    specs = build_specs(data)
    norm_b, norm_o = compute_counts(specs)

    # b3 must reproduce the reviewed D counts exactly
    b3 = [s for s in specs if s["id"] == "b3"][0]
    old_qa = json.load(open(os.path.join(D_DIR, "qa", "qa_report.json"),
                            encoding="utf-8"))
    assert b3["historical"]
    assert b3["max_count"] == old_qa["max_bin_count"] == 31
    assert b3["occupied"] == old_qa["occupied_bins"] == 3775

    ticks_cb = [1, 2, 5, 10, 20]
    records = []

    # ---- six panels -------------------------------------------------------
    for s in specs:
        fig, ax = panel_fig(s)
        items, bad = text_report(fig, WF, HF)
        pos = ax.get_position()
        rec = dict(
            id=s["id"], title=s["title"], family=s["fam"],
            xlim=list(s["lim"]), ylim=list(s["lim"]),
            xticks=list(s["ticks"]), yticks=list(s["ticks"]),
            fmt=s["fmt"],
            n=int(len(s["t"])),
            n_out=int(np.sum((s["t"] < s["lim"][0]) | (s["t"] > s["lim"][1]) |
                             (s["p"] < s["lim"][0]) | (s["p"] > s["lim"][1]))),
            bin_x=[float(s["bin_x"][0]), float(s["bin_x"][1])],
            bin_y=[float(s["bin_y"][0]), float(s["bin_y"][1])],
            historical_binning=bool(s["historical"]),
            max_bin_count=s["max_count"], occupied_bins=s["occupied"],
            norm_vmax=float(s["norm"].vmax),
            axes_in=[pos.width * WF, pos.height * HF],
            text_items=items, text_outside=bad,
        )
        assert rec["n_out"] == 0 and len(s["t"]) == 15307
        assert abs(pos.width * WF - P) < 1e-9
        assert abs(pos.height * HF - P) < 1e-9
        assert not bad
        # the outermost markers must sit clear of the frame: the data-edge
        # margin equals PAD_FRAC of the axis span, i.e. 2 % of 126.96 pt,
        # and has to exceed the marker radius with a visible gap left over
        rad_pt = math.sqrt(float(S_DOT) / math.pi)
        # the padded limits span (1 + 2*PAD_FRAC) * S, so the data edge sits
        # PAD_FRAC/(1 + 2*PAD_FRAC) of the axis length inside the frame
        edge_pt = PAD_FRAC / (1.0 + 2.0 * PAD_FRAC) * P * 72.0
        rec["edge_margin_pt"] = round(edge_pt, 3)
        rec["marker_radius_pt"] = round(rad_pt, 3)
        rec["edge_clearance_pt"] = round(edge_pt - rad_pt, 3)
        assert rec["edge_clearance_pt"] > 0.25, rec["edge_clearance_pt"]
        stem = os.path.join(PANEL_DIR, "%s_%s" % (s["id"], s["title"].replace(" ", "_")))
        fig.savefig(stem + ".png", dpi=900, facecolor="white")
        fig.savefig(stem + ".pdf", dpi=900, facecolor="white")
        fig.savefig(stem + ".svg", dpi=900, facecolor="white")
        plt.close(fig)
        flatten_png(stem + ".png")
        records.append(rec)
        print("panel %s  lim %.4f %.4f  ticks %s  n_out %d  edge %.2f pt "
              "(clearance %.2f)  maxcount %d"
              % (s["id"], s["lim"][0], s["lim"][1], s["ticks"], rec["n_out"],
                 rec["edge_margin_pt"], rec["edge_clearance_pt"],
                 s["max_count"]))

    # ---- two colour keys --------------------------------------------------
    cb_records = []
    for name, cmap, norm in (
            ("Colorbar_shared_scale_blue", CMAP_BLUE, norm_b),
            ("Colorbar_log_ratio_orange", CMAP_ORANGE, norm_o)):
        fig, cb = colorbar_fig(cmap, norm, ticks_cb)
        items, bad = text_report(fig, CB_W, HF)
        assert not bad, bad
        stem = os.path.join(CB_DIR, name)
        fig.savefig(stem + ".png", dpi=900, facecolor="white")
        fig.savefig(stem + ".pdf", dpi=900, facecolor="white")
        fig.savefig(stem + ".svg", dpi=900, facecolor="white")
        plt.close(fig)
        flatten_png(stem + ".png")
        cb_records.append(dict(name=name, ticks=ticks_cb,
                               vmin=float(norm.vmin), vmax=float(norm.vmax),
                               bar_w_in=CB_BAR_W, bar_h_in=CB_BAR_H,
                               canvas_in=[CB_W, HF], text_items=items))
        print("colour key %s  norm 1..%g" % (name, norm.vmax))

    # ---- preview ----------------------------------------------------------
    prev_items, prev_bad = build_preview(
        specs, norm_b, norm_o,
        os.path.join(PREVIEW_DIR, "Figure2_assembly_preview.png"))
    assert not prev_bad, prev_bad
    flatten_png(os.path.join(PREVIEW_DIR, "Figure2_assembly_preview.png"),
                dpi=600)
    preview_info = dict(png_mm=[PREV_W * 25.4, PREV_H * 25.4],
                        text_items=prev_items, text_outside=prev_bad)

    qa = dict(
        n_test=15307,
        point=dict(s=S_DOT, alpha=ALPHA_D, nbins=NBINS,
                   draw_order="counts ascending, stable"),
        shared_norm=dict(blue=[1.0, float(norm_b.vmax)],
                         orange=[1.0, float(norm_o.vmax)]),
        cbar_ticks=ticks_cb,
        cmap_blue=["#AFC3DF", "#86A3CE", "#4C72B0", "#36578C", "#1F3560"],
        cmap_orange=["#F1B285", "#E79A66", "#DD8452", "#C66733", "#9C3D0B"],
        panels=records, colorbars=cb_records, preview=preview_info,
        panel_canvas_in=[WF, HF], panel_box_in=[P, P],
    )
    with open(os.path.join(QA_DIR, "qa_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump(qa, fh, indent=2, ensure_ascii=False)

    # ---- checklist.csv ----------------------------------------------------
    with open(os.path.join(OUT, "checklist.csv"), "w", encoding="utf-8-sig") as fh:
        fh.write("panel,title,xlim,ylim,major_ticks,n_plotted,n_outside,"
                 "bin_x,bin_y,max_bin_count,shared_norm_vmax,"
                 "edge_margin_pt,edge_clearance_pt\n")
        for r in records:
            fh.write('%s,%s,"%s","%s","%s",%d,%d,"%s","%s",%d,%g,%.3f,%.3f\n'
                     % (r["id"], r["title"], r["xlim"], r["ylim"],
                        r["xticks"], r["n"], r["n_out"],
                        [round(v, 4) for v in r["bin_x"]],
                        [round(v, 4) for v in r["bin_y"]],
                        r["max_bin_count"], r["norm_vmax"],
                        r["edge_margin_pt"], r["edge_clearance_pt"]))

    # ---- labels.txt -------------------------------------------------------
    with open(os.path.join(OUT, "labels.txt"), "w", encoding="utf-8") as fh:
        fh.write("# Figure 2 final assets -- copy-ready labels\n")
        fh.write("# a = shared scale = (log10 p_n + log10 p_p) / 2\n")
        fh.write("# r = electron-hole log-ratio = log10(p_n / p_p)\n")
        fh.write("# n, p, c, v are subscripts in the unit strings\n\n")
        for s in specs:
            r = [x for x in records if x["id"] == s["id"]][0]
            coord = "a" if s["fam"] == "a" else "r"
            unit = UNIT[s["lab"]] if s["fam"] == "a" else "dimensionless"
            fh.write("%s  %s\n" % (s["id"], s["title"]))
            fh.write("    x axis: True %s\n" % coord)
            fh.write("    y axis: Predicted %s\n" % coord)
            fh.write("    unit: %s\n" % unit)
            fh.write("    rho: %.6f  (%.3f)\n" % (s["rho"], s["rho"]))
            fh.write("\n")

    print("preview %.2f x %.2f mm" % (PREV_W * 25.4, PREV_H * 25.4))


if __name__ == "__main__":
    main()
