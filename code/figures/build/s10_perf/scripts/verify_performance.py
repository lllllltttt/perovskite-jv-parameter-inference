# -*- coding: utf-8 -*-
"""Verify the two re-issued performance panels against the frozen metrics.

D1  panel (a) is pixel-identical to the approved comparison_a.png
D2  panel (b) draws no bars: no filled path in #3A5C94 / #CA7241
D3  every summary point sits exactly at the mean of the five seed values
D4  every small dot sits exactly at a seed value (5 per group and arm)
D5  every error bar spans mean +/- sample SD (ddof = 1)
D6  original is left of expanded in every group; no line joins parameters
D7  x: six tick marks, no numbers; y: the original ticks; ylim 0-1.13538
D8  four-sided frame #404040 0.5 pt; canvas identical to panel (a)
D9  Arial glyphs as outlines, nothing clipped
"""
import os
import re
import sys

import numpy as np
import pandas as pd
from lxml import etree
from PIL import Image

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"

BASE = r"E:\project\work1"
CSV = os.path.join(BASE, "20261021_expanded_ratio_comparison_v2", "out",
                   "metrics", "table_B_common_tests.csv")
OUT = os.path.join(BASE, "20261119_model_perf", "out")
REF_A = os.path.join(BASE, "20261117_figs9_compare", "out", "comparison_a.png")

COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
C_OLD, C_NEW = "#3a5c94", "#ca7241"
YLIM = (0.0, 1.13538)
YTICKS = np.arange(0, 1.01, 0.2)
PATCHY = 3.036            # half of the 0.36 data-unit offset in pt (x scale)
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-64s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def data():
    df = pd.read_csv(CSV)
    A = df[df["test_arm"] == df["model_arm"]]
    out = {}
    for arm in ("original", "expanded"):
        g = A[A["model_arm"] == arm]
        m, s, p = [], [], []
        for c in COORDS:
            v = g[g["quantity"] == c]["rmse"].astype(float).to_numpy()
            m.append(np.mean(v)); s.append(np.std(v, ddof=1)); p.append(v)
        out[arm] = (np.array(m), np.array(s), p)
    return out


def parse(name):
    return etree.parse(os.path.join(OUT, name)).getroot()


def axes_box(root):
    ax = [g for g in root.iter(CS + "g")
          if (g.get("id") or "").startswith("axes_")][0]
    v = [float(x) for x in re.findall(r"-?\d+\.?\d*",
                                      ax.find(CS + "g").find(CS + "path").get("d"))]
    xs, ys = v[0::2], v[1::2]
    return ax, (min(xs), min(ys), max(xs), max(ys))


def main():
    D = data()
    print("=" * 82)

    # ---- D1: panel a -----------------------------------------------------
    a_png = os.path.join(OUT, "performance_a_skill.png")
    i1 = np.asarray(Image.open(a_png).convert("RGB")).astype(int)
    i2 = np.asarray(Image.open(REF_A).convert("RGB")).astype(int)
    ok(i1.shape == i2.shape and int((i1 != i2).any(axis=2).sum()) == 0,
       "D1 panel (a) identical to the approved bar chart",
       "%dx%d, %d px differ" % (*i1.shape[:2], 0 if i1.shape != i2.shape
                                else int((i1 != i2).any(axis=2).sum())))

    # ---- panel b ----------------------------------------------------------
    root = parse("performance_b_rmse.svg")
    ax, (X0, Y0, X1, Y1) = axes_box(root)
    H = Y1 - Y0
    scale = (YLIM[1] - YLIM[0]) / H

    def ydata(y):
        return (Y1 - float(y)) * scale + YLIM[0]

    def xdata(x):
        return (float(x) - X0) / (X1 - X0)

    # D2: no bar geometry ------------------------------------------------
    filled = [p for p in root.iter(CS + "path")
              if any(c in (p.get("style") or "") for c in (C_OLD, C_NEW))]
    rects = [e for e in root.iter(CS + "rect")
             if (e.getparent().tag if e.getparent() is not None else "") != CS + "clipPath"]
    ok(not filled and not rects, "D2 no bars / no filled columns",
       "%d filled paths, %d rects" % (len(filled), len(rects)))

    # summary points: <g id=line2d_25/26> hold 6 uses each
    groups = {g.get("id"): g for g in ax.iter(CS + "g") if g.get("id")}
    sum_o = [u for u in groups["line2d_25"].iter(CS + "use")]
    sum_e = [u for u in groups["line2d_26"].iter(CS + "use")]
    xc = [xdata(u.get("x")) for u in sum_o]
    xe = [xdata(u.get("x")) for u in sum_e]
    yo = [ydata(u.get("y")) for u in sum_o]
    ye = [ydata(u.get("y")) for u in sum_e]
    m_o, s_o, p_o = D["original"]
    m_e, s_e, p_e = D["expanded"]
    ok(np.allclose(yo, m_o, atol=2e-5) and np.allclose(ye, m_e, atol=2e-5),
       "D3 summary points = mean of the five runs",
       "max |dy| %.1e / %.1e" % (np.abs(np.array(yo) - m_o).max(),
                                 np.abs(np.array(ye) - m_e).max()))

    # dots: line2d_13..18 original, 19..24 expanded
    dot_ids_o = ["line2d_%d" % i for i in range(13, 19)]
    dot_ids_e = ["line2d_%d" % i for i in range(19, 25)]
    do = [[ydata(u.get("y")) for u in groups[g].iter(CS + "use")] for g in dot_ids_o]
    de = [[ydata(u.get("y")) for u in groups[g].iter(CS + "use")] for g in dot_ids_e]
    ok(all(len(v) == 5 for v in do + de)
       and np.allclose(do, p_o, atol=2e-5) and np.allclose(de, p_e, atol=2e-5),
       "D4 five dots per group = the five seed values",
       "max |dy| %.1e / %.1e" % (np.abs(np.array(do) - p_o).max(),
                                 np.abs(np.array(de) - p_e).max()))

    # error bars: LineCollection segments + caps
    segs = []
    for g in ax.iter(CS + "g"):
        if (g.get("id") or "").startswith("LineCollection"):
            for p in g.iter(CS + "path"):
                v = [float(t) for t in re.findall(r"-?\d+\.?\d*", p.get("d"))]
                segs.append(v)
    ok(len(segs) == 12 and all(abs(v[0] - v[2]) < 1e-9 for v in segs),
       "D6a error bars are vertical segments only",
       "%d segments" % len(segs))
    seg_y = {}
    for v in segs:
        seg_y.setdefault(round(xdata(v[0]), 9), []).append(
            sorted([ydata(v[1]), ydata(v[3])]))
    # sorted x alternates original, expanded within each of the six groups
    lo_sorted = [seg_y[x][0][0] for x in sorted(seg_y)]
    hi_sorted = [seg_y[x][0][1] for x in sorted(seg_y)]
    got_lo = np.array(lo_sorted[0::2] + lo_sorted[1::2])
    got_hi = np.array(hi_sorted[0::2] + hi_sorted[1::2])
    want_lo = np.concatenate([m_o - s_o, m_e - s_e])
    want_hi = np.concatenate([m_o + s_o, m_e + s_e])
    ok(np.allclose(got_lo, want_lo, atol=2e-5)
       and np.allclose(got_hi, want_hi, atol=2e-5),
       "D5 error bars span mean +/- sample SD (ddof=1)",
       "max |d| %.1e" % max(np.abs(got_lo - want_lo).max(),
                            np.abs(got_hi - want_hi).max()))

    # original left of expanded, constant offsets
    want_dx = 0.36 / (len(COORDS) - 1 + 2 * 0.62)      # 0.36 data units
    dx = np.array(xe) - np.array(xc)
    ok(all(e > o for o, e in zip(xc, xe))
       and np.allclose(dx, want_dx, atol=1e-6),
       "D6b original always left of expanded, same offset as the bars",
       "dx = %.6f axis fraction (= 0.36 data units)" % dx[0])

    # D7 ticks
    xt = groups["matplotlib.axis_1"]
    n_xtick = sum(1 for g in xt.iter(CS + "g") if (g.get("id") or "").startswith("xtick"))
    n_xtext = sum(1 for g in xt.iter(CS + "g") if (g.get("id") or "").startswith("text"))
    yt = groups["matplotlib.axis_2"]
    n_ytick = sum(1 for g in yt.iter(CS + "g") if (g.get("id") or "").startswith("ytick"))
    # y tick values from the tick mark positions
    yv = sorted(ydata(u.get("y")) for g in yt.iter(CS + "g")
                if (g.get("id") or "").startswith("ytick")
                for u in g.iter(CS + "use")
                if u.get(XL + "href") and u.get("x") is not None)
    ok(n_xtick == 6 and n_xtext == 0 and n_ytick == 6
       and np.allclose(yv, YTICKS, atol=2e-4),
       "D7 six bare x ticks, y ticks 0.0-1.0, ylim 0-1.13538",
       "x %d (labels %d), y %d -> %s" % (n_xtick, n_xtext, n_ytick,
                                         np.round(yv, 3).tolist()))

    # D8 frame + canvas
    spines = [p for p in ax.iter(CS + "path")
              if "#404040" in (p.get("style") or "")
              and "stroke-width: 0.5" in (p.get("style") or "")]
    ca, cb = root.get("viewBox").split()[2:4]
    rb = parse("performance_a_skill.svg")
    ok(len(spines) >= 4 and rb.get("viewBox").split()[2:4] == [ca, cb],
       "D8 four-sided frame, same canvas as panel (a)",
       "%d frame paths, canvas %s x %s pt" % (len(spines), ca, cb))

    # D9 glyphs + clearance
    ntext = len(list(root.iter(CS + "text")))
    hrefs = [u.get(XL + "href") or "" for u in root.iter(CS + "use")]
    glyph = [h for h in hrefs if re.match(r"^#[A-Za-z]+-", h)]
    bad = [h for h in glyph if not h.startswith("#ArialMT-")]
    im = Image.open(os.path.join(OUT, "performance_b_rmse.png"))
    g = np.asarray(im.convert("L")).astype(int)
    mk = (255 - g) > 8
    rr = np.where(mk.any(axis=1))[0]
    cc = np.where(mk.any(axis=0))[0]
    clr = min(cc[0], rr[0], g.shape[1] - 1 - cc[-1], g.shape[0] - 1 - rr[-1]) / (600 / 72.0)
    ok(ntext == 0 and glyph and not bad and abs(im.info.get("dpi", (0,))[0] - 600) < 1
       and clr > 2.0,
       "D9 Arial outlines only, 600 dpi, clearance %.2f pt" % clr,
       "%d glyph uses" % len(glyph))

    print("=" * 82)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
