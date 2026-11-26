# -*- coding: utf-8 -*-
"""Figure 4 (d) and (e) - standalone panels, supervisor revision 2026-11-11.

Same frozen data and the same drawing code as 20261110_fig4de_standalone
(`fig4_forward.collect()` re-asserts every archived pin), with two changes:

  * the median value of every box is now printed in the image: horizontally
    centred on its box, its ink bottom 1.6 pt above the true median line.
    (d) all three numbers fit inside the box.  In (e) |dVoc| (V), |dFF| (pp)
    and |dPCE| (pp) fit inside their boxes; the |dJsc| box is only ~4.6 pt
    tall, so its number sits immediately above the box, centred, with its
    baseline 2 pt above the upper whisker cap on a 1.2 pt white halo (the cap
    stays fully visible).
  * the three (d) window names are kept in the image as x tick labels (they
    are category labels, not an axis title).

FF is multiplied by 100 exactly once (fraction -> percentage points); PCE is
already in percent and is not multiplied.  Jsc uses 45 samples, the other
three metrics 44.  The four (e) canvases and plot areas stay identical, and
the (d) plot area keeps its 2.05 in height (the canvas grows 2.20 -> 2.44 to
make room for the two-line first category label).

No axis titles, units, panel letters, metric titles, n or figure text are
baked in; those are in labels_and_caption.txt.  The preview carries them for
checking only.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import to_rgba
from matplotlib.text import Text
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FixedLocator, NullFormatter

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

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
plt.rcParams["ps.fonttype"] = 42

INK = st.INK
FS_TICK = st.FS_TICK            # 7.5 pt
FS_MED = 7.0
TICK_LEN = 3.0
TICK_PAD = 2.5

# ------------------------------------------------------------------ sizes ---
D_W, D_H = 2.60, 2.44           # (d) canvas: 2.05 in plot + 0.34 bottom
E_W, E_H = 1.68, 1.00
D_M = dict(right=0.06, bottom=0.34, top=0.05)
E_M = dict(right=0.05, bottom=0.075, top=0.05)

BOX_W = 0.50
JIT = 0.13
MS = 2.2
ALPHA_PT = 0.45
ALPHA_BOX = 0.22

WINDOWS = [("full", "Full curve\n(0\u20131.3 V)"),
           ("le1", "0\u20131.0 V"),
           ("gt1", "> 1.0 V")]
Wd = [st.OKABE_ITO[0], st.OKABE_ITO[2], st.OKABE_ITO[3]]

E_ORDER = ["Jsc", "Voc", "FF", "PCE"]
E_XTL = {"Jsc": r"$|\Delta J_\mathrm{sc}|$",
         "Voc": r"$|\Delta V_\mathrm{oc}|$",
         "FF": r"$|\Delta \mathrm{FF}|$",
         "PCE": r"$|\Delta \mathrm{PCE}|$"}
E_UNIT = {"Jsc": r"mA cm$^{-2}$", "Voc": "V", "FF": "pp", "PCE": "pp"}
BLUE = st.OKABE_ITO[0]

D_YLBL = ["0.01", "0.1", "1", "10", "100"]

D = f4.collect()

# ---------------------------------------------------------------- helpers ---
FP = FontProperties(family="Arial")


def text_pt(s, size=FS_TICK):
    return TextPath((0, 0), s, prop=FontProperties(family="Arial",
                                                   size=size)).get_extents().width


def left_margin(labels, gap_pt=3.5):
    return (TICK_LEN + TICK_PAD + max(text_pt(s) for s in labels) + gap_pt) / 72.0


D_LEFT = left_margin(D_YLBL)


def e_ticks(vmax, max_intervals=4):
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


def e_values(key):
    a = np.abs(np.asarray(D["dev"][key], float))
    return a * 100.0 if key == "FF" else a


E_LBL = {k: e_ticks(float(np.nanmax(e_values(k)))) for k in E_ORDER}
E_LEFT = left_margin([s for _, _, labs in E_LBL.values() for s in labs])

MED_TEXT = {"full": "2.69", "le1": "0.455", "gt1": "5.19",
            "Jsc": "0.112", "Voc": "0.022", "FF": "1.6", "PCE": "0.471"}


def ink_height_pt(s, size=FS_MED):
    bb = TextPath((0, 0), s, size=size, prop=FontProperties(family="Arial",
                                                           size=size)) \
        .get_extents()
    return bb.y1 - bb.y0


def median_y_px(ax, pos, med):
    fig = ax.figure
    fig.canvas.draw()
    return ax.transData.transform((pos, med))[1]


def place_median(ax, pos, med, q1, q3, top_lim, text, log=False, cap=None):
    """Ink bottom of `text` 1.6 pt above the median line, centred on `pos`.

    'inside' when the ink stays 0.6 pt below the box top; otherwise the label
    goes just above the box, centred, and must not cut the upper whisker cap:
    it is fitted into the band between q3 and the cap (white glyph halo, line
    left visible through the gaps), or, if that band is too short, placed
    above the cap on a small white backing.  All comparisons are in display
    pixels, so they hold on the log axis too.
    """
    fig = ax.figure
    fig.canvas.draw()
    dpi = fig.dpi
    gap_px = 1.6 * dpi / 72.0
    ink_px = ink_height_pt(text) * dpi / 72.0
    p_med = median_y_px(ax, pos, med)
    inv = ax.transData.inverted()

    def y_of(py):
        return float(inv.transform((0.0, py))[1])

    box_top_px = ax.transData.transform((pos, q3))[1]
    cap_px = (ax.transData.transform((pos, cap))[1]
              if cap is not None and np.isfinite(cap) else None)
    margin_px = 0.6 * dpi / 72.0
    where = None
    if box_top_px - (p_med + gap_px + ink_px) >= margin_px:
        where = "inside"
        y_base = y_of(p_med + gap_px)
    band_px = (cap_px - box_top_px) if cap_px is not None else 0.0
    if where is None and band_px >= ink_px + 2 * margin_px:
        where = "above_band"
        y_base = y_of(box_top_px + (band_px - ink_px) / 2.0)
    if where is None:
        where = "above_cap"
        base_px = (cap_px if cap_px is not None else box_top_px)             + 2.0 * dpi / 72.0
        y_base = y_of(base_px)
    kw = dict(ha="center", va="baseline", fontsize=FS_MED, color=INK,
              zorder=8, clip_on=False)
    t = ax.text(pos, y_base, text, **kw)
    t.set_path_effects([pe.withStroke(linewidth=1.2, foreground="white")])
    fig.canvas.draw()
    bb = t.get_window_extent(fig.canvas.get_renderer())
    rec = dict(text=text, where=where, x=pos, y_base=round(y_base, 5),
               ink_top_data=round(y_of(bb.y1), 5),
               ink_bottom_pt_above_q3=round((bb.y0 - box_top_px) * 72.0 / dpi, 2),
               gap_to_box_top_pt=round((box_top_px - bb.y1) * 72.0 / dpi, 2),
               gap_to_axis_top_pt=round(
                   (ax.transData.transform((pos, top_lim))[1] - bb.y1)
                   * 72.0 / dpi, 2))
    if where == "above_cap":
        rec["label_baseline_above_cap_pt"] = 2.0
    if where == "above_band":
        rec["label_centred_in_band_q3_cap"] = True
    return t, rec


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
    return vals


# ---------------------------------------------------------------- drawing ---
def draw_d(fig, x0, y0, w=D_W, h=D_H, labels=True):
    fw, fh = fig.get_size_inches()
    ax = fig.add_axes([(x0 + D_LEFT) / fw, (y0 + D_M["bottom"]) / fh,
                       (w - D_LEFT - D_M["right"]) / fw,
                       (h - D_M["bottom"] - D_M["top"]) / fh])
    recs = []
    for i, (k, _) in enumerate(WINDOWS):
        v = draw_box_group(ax, D["rm"][k], i, Wd[i], 2026 + i)
        recs.append((i, v))

    ax.set_yscale("log")
    ax.set_ylim(0.01, 200.0)
    ax.set_xlim(-0.55, 2.55)
    ax.set_xticks([0, 1, 2])
    if labels:
        ax.set_xticklabels([lab for _, lab in WINDOWS], fontsize=FS_TICK,
                           linespacing=1.2)
    else:
        ax.set_xticklabels(["", "", ""])
    ax.yaxis.set_major_locator(FixedLocator([0.01, 0.1, 1.0, 10.0, 100.0]))
    ax.set_yticklabels(D_YLBL)
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(False)
    st.configure_axes(ax)
    ax.tick_params(axis="y", which="minor", length=2.0, width=0.6, color=INK)

    info = []
    for i, v in recs:
        q1, q3 = np.percentile(v, 25), np.percentile(v, 75)
        _t, r = place_median(ax, i, float(np.median(v)), q1, q3, 200.0,
                             MED_TEXT[WINDOWS[i][0]], log=True)
        info.append(r)
    return ax, info


def draw_e(fig, x0, y0, key, w=E_W, h=E_H):
    fw, fh = fig.get_size_inches()
    ax = fig.add_axes([(x0 + E_LEFT) / fw, (y0 + E_M["bottom"]) / fh,
                       (w - E_LEFT - E_M["right"]) / fw,
                       (h - E_M["bottom"] - E_M["top"]) / fh])
    a = e_values(key)
    v = draw_box_group(ax, a, 0, BLUE, 2026 + 10 + E_ORDER.index(key))

    top, ticks, labels = E_LBL[key]
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(0.0, top)
    ax.set_xticks([])
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.set_yticklabels(labels)
    ax.grid(False)
    st.configure_axes(ax)

    q1, q3 = np.percentile(v, 25), np.percentile(v, 75)
    iqr = q3 - q1
    hi = v[v <= q3 + 1.5 * iqr]
    cap = float(hi.max()) if hi.size else float(q3)
    _t, r = place_median(ax, 0.0, float(np.median(v)), q1, q3, top,
                         MED_TEXT[key], cap=cap)
    r["whisker_top"] = round(cap, 6)
    r["n"] = int(v.size)
    return ax, r


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


def save(fig, stem, dpi=600):
    fig.savefig(stem + ".png", dpi=dpi, facecolor="white")
    flatten_png(stem + ".png", dpi)
    fig.savefig(stem + ".pdf", facecolor="white")
    fig.savefig(stem + ".svg", facecolor="white")
    plt.close(fig)


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


# --------------------------------------------------------------- preview ----
def build_preview():
    W, H = 6.80, 3.00
    fig = new_fig(W, H)
    xd, yd = 0.36, 0.34
    axd, infod = draw_d(fig, xd, yd)
    x1, x2 = 3.20, 5.04
    y2, y1 = 0.34, 1.54
    pos = {k: (x, y) for k, (x, y) in zip(
        E_ORDER, [(x1, y1), (x2, y1), (x1, y2), (x2, y2)])}
    axs, infoe = {}, {}
    for k, (x, y) in pos.items():
        axs[k], infoe[k] = draw_e(fig, x, y, k)

    def T(x_in, y_in, s, **kw):
        fig.text(x_in / W, y_in / H, s, color=kw.pop("color", INK), **kw)

    T(xd - 0.02, 2.79, "(d)", fontsize=8.5, ha="left", va="bottom")
    T(x1 - 0.02, 2.58, "(e)", fontsize=8.5, ha="left", va="bottom")

    T(0.28, yd + 1.025, "J\u2013V RMSE (mA cm$^{-2}$)", rotation=90,
      fontsize=8.0, ha="center", va="center")

    for k, (x, y) in pos.items():
        T(x + E_LEFT + 0.03, y + E_H + 0.04, E_XTL[k], fontsize=8.0,
          ha="left", va="bottom")
        T(x - 0.02, y + E_H / 2, E_UNIT[k], rotation=90, fontsize=7.0,
          ha="center", va="center")

    T((x1 + x2 + E_W) / 2.0, 0.06,
      "one predicted curve has no downward zero crossing and is excluded\n"
      "from  |\u0394V$_{oc}$|, |\u0394FF|  and  |\u0394PCE|  ($n$ = 44)",
      fontsize=7.0, ha="center", va="bottom", linespacing=1.35)

    bad = canvas_text_out(fig)
    fig.savefig(os.path.join(PREV, "Fig4_preview.png"), dpi=600,
                facecolor="white")
    flatten_png(os.path.join(PREV, "Fig4_preview.png"), 600)
    fig.savefig(os.path.join(PREV, "Fig4_preview.pdf"), facecolor="white")
    plt.close(fig)
    return bad, infod, infoe


# ------------------------------------------------------------------ main ----
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
    # ---- (d)
    fig = new_fig(D_W, D_H)
    axd, infod = draw_d(fig, 0.0, 0.0)
    bad = canvas_text_out(fig)
    assert not bad, bad
    save(fig, os.path.join(FIG, "Fig4d"))

    dstat = {k: box_stats(D["rm"][k]) for k, _ in WINDOWS}
    # the values the supervisor asked us to confirm
    assert abs(dstat["full"]["median"] - 2.69263) < 5e-4
    assert abs(dstat["le1"]["median"] - 0.45535) < 5e-4
    assert abs(dstat["gt1"]["median"] - 5.19160) < 5e-4
    qa["panels"]["Fig4d"] = dict(
        canvas_in=[D_W, D_H], axes_rect_in=[D_LEFT, D_M["bottom"],
                                            D_W - D_LEFT - D_M["right"],
                                            D_H - D_M["bottom"] - D_M["top"]],
        ylim=list(axd.get_ylim()),
        yticks=[t.get_text() for t in axd.get_yticklabels()],
        xticklabels=[t.get_text() for t in axd.get_xticklabels()],
        stats=dstat, medians=infod)

    # ---- (e)
    estat = {}
    rects = {}
    for k in E_ORDER:
        fig = new_fig(E_W, E_H)
        ax, rec = draw_e(fig, 0.0, 0.0, k)
        bad = canvas_text_out(fig)
        assert not bad, bad
        stem = "Fig4e_" + ("FF_pp" if k == "FF" else k)
        save(fig, os.path.join(FIG, stem))
        a = e_values(k)
        a = a[np.isfinite(a)]
        assert rec["n"] == (45 if k == "Jsc" else 44)
        estat[k] = dict(n=int(a.size), median=float(np.median(a)),
                        box=box_stats(a), label=rec)
        rects[k] = list(ax.get_position().bounds)
        qa["panels"]["Fig4e_" + k] = dict(
            file=stem, canvas_in=[E_W, E_H],
            axes_rect_in=[E_LEFT, E_M["bottom"], E_W - E_LEFT - E_M["right"],
                          E_H - E_M["bottom"] - E_M["top"]],
            axes_rect_fraction=rects[k], ylim=list(ax.get_ylim()),
            yticks=[t.get_text() for t in ax.get_yticklabels()],
            n=int(a.size), median=float(np.median(a)), label=rec, unit=k)

    # the four plot areas must be identical
    ref = np.array(rects["Jsc"])
    for k in E_ORDER[1:]:
        assert np.allclose(ref, np.array(rects[k]), atol=1e-12), (k, rects)
    qa["checks"]["e_axes_identical"] = True
    qa["checks"]["e_axes_rect_fraction"] = rects["Jsc"]

    # medians and units the supervisor asked for
    assert abs(estat["Jsc"]["median"] - 0.111897) < 5e-5
    assert abs(estat["Voc"]["median"] - 0.022439) < 5e-5
    assert abs(estat["FF"]["median"] - 1.55331) < 5e-4
    assert abs(estat["PCE"]["median"] - 0.471401) < 5e-5
    assert abs(estat["FF"]["box"]["max"] - 6.49263) < 5e-4
    assert abs(estat["PCE"]["box"]["max"] - 1.94779) < 5e-4
    qa["checks"]["medians"] = {k: round(estat[k]["median"], 6)
                               for k in E_ORDER}

    bad, infod2, infoe = build_preview()
    qa["preview"] = {"size_in": [6.80, 3.00],
                     "size_mm": [172.72, 76.2],
                     "text_outside_canvas": bad}
    assert not bad, bad

    # tables
    rows = []
    for k, _ in WINDOWS:
        for v in np.asarray(D["rm"][k], float):
            rows.append(dict(window=k, rmse_mA_cm2=v))
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "Figure4d_per_sample.csv"),
                              index=False)
    rows = []
    for k in E_ORDER:
        a = e_values(k)
        for v in a[np.isfinite(a)]:
            rows.append(dict(metric=k, abs_dev=v,
                             unit="pp" if k in ("FF", "PCE") else
                             ("V" if k == "Voc" else "mA cm-2")))
    pd.DataFrame(rows).to_csv(os.path.join(DATA, "Figure4e_per_sample.csv"),
                              index=False)
    stat = []
    for k, _ in WINDOWS:
        stat.append(dict(panel="d", group=k, unit="mA cm-2",
                         **box_stats(D["rm"][k])))
    for k in E_ORDER:
        stat.append(dict(panel="e", group=k,
                         unit="pp" if k in ("FF", "PCE") else
                         ("V" if k == "Voc" else "mA cm-2"),
                         **box_stats(e_values(k))))
    pd.DataFrame(stat).to_csv(os.path.join(DATA, "Figure4de_box_stats.csv"),
                              index=False)

    with open(os.path.join(QA, "qa_fig4.json"), "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    print(json.dumps(qa["panels"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
