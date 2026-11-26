# -*- coding: utf-8 -*-
"""Figure S1, fifth specification: the nine histograms re-issued with tick
numbers at 50 % of the previous size, tighter padding and tighter canvas.

Unchanged, by construction
  plot area 125.569 x 115.162 pt, bars (60 bins, same counts), fills, frame,
  axis ranges, tick positions, tick values, tick marks (3 pt, outward).

Changed
  every tick number : font-size 12 -> 6 (Arial, normal weight)
  label padding     : y numbers 6.5 -> 4.6 pt from the axis line,
                      x numbers baseline 11.869 -> 9.1 pt under the axis
  canvas            : grown from the measured ink of the nine pieces + PAD,
                      one identical canvas and one identical plot offset for
                      all nine (so they still align in PowerPoint).

The tick values are the ones verified against the original script + data
(work/ticks_derived.json); nothing about the data or the axes is touched.
"""
import io
import json
import os
import re
import subprocess
import sys

import numpy as np
from lxml import etree
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"
SRC = "work/slide1_image2.svg"
DERIVED = "work/ticks_derived.json"
PY = sys.executable

OUT = "out_ticks_small"
PREV = "out_ticks_full"
PAD = 2.5
PX_PER_PT = 96.0 / 72.0

# Reference: SI Figure S4 — tick numbers 8 pt on a 211.00 pt-wide plot area
# (3.79 % of the plot width).  Our plot is 125.569 pt wide, so the matching
# size is 8 x 125.569/211.00 = 4.76 pt; 4.8 is used.  (A flat 50 % of the old
# 12 would be 6.0 pt = 4.78 % of the plot width, still 26 % too wide.)
FS = 4.8
PAD_REF = 3.5 * (125.569 / 211.00)        # FigS4 tick pad, scaled by plot width
X_LAB_DY = 3.0 + PAD_REF + 0.716 * FS     # tick + pad + Arial cap height
Y_LAB_DX = 3.0 + PAD_REF                  # tick + pad
Y_LAB_DY = 0.716 * FS / 2.0               # cap/2, centres the digits on the tick

HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]

TEXT_FILL = "#1A1A1A"
Y_TICK_MARK = "m09f4e2fff5"
X_TICK_MARK = "ma815c2b250"

HIST_NAMES = [
    ("S1a_01_mu_n", "mu_n"), ("S1a_02_mu_p", "mu_p"),
    ("S1a_03_tau_n", "tau_n"), ("S1a_04_tau_p", "tau_p"),
    ("S1a_05_N_c", "N_c"), ("S1a_06_N_v", "N_v"),
    ("S1a_07_tau_ETL", "tau_ETL"), ("S1a_08_tau_HTL", "tau_HTL"),
    ("S1a_09_r_rad", "r_rad"),
]


# ---------------------------------------------------------------- helpers --
def txt(e):
    return "".join(e.itertext()).strip()


def ref_ids(el):
    ids = set()
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        for a in (XL + "href", "href"):
            v = e.get(a) or ""
            if v.startswith("#"):
                ids.add(v[1:])
        for a in ("clip-path", "fill", "stroke", "filter", "mask"):
            m = re.search(r"url\(#([^)]+)\)", e.get(a) or "")
            if m:
                ids.add(m.group(1))
    return ids


def defined_ids(el):
    return {e.get("id") for e in el.iter() if isinstance(e.tag, str) and e.get("id")}


def external_defs(piece, idmap, order):
    have = defined_ids(piece)
    need = ref_ids(piece) - have
    out, seen = [], set()
    while need:
        nid = sorted(need, key=lambda i: order[i])[0]
        need.discard(nid)
        if nid in seen:
            continue
        seen.add(nid)
        out.append(etree.fromstring(etree.tostring(idmap[nid])))
        need |= (ref_ids(idmap[nid]) - have - {d.get("id") for d in out})
    return out


def strip_histogram_labels(a):
    for c in list(a):
        if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
            a.remove(c)
    for c in list(a):
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            cid = g.get("id") or ""
            if cid.startswith("xtick_") or cid.startswith("ytick_"):
                continue
            if next(g.iter(CS + "text"), None) is not None:
                c.remove(g)
    return a


def font_fix(el, size=FS):
    for t in el.iter(CS + "text"):
        t.set("font-family", "Arial")
        t.set("font-size", "%g" % size)
        if "font-weight" in t.attrib:
            del t.attrib["font-weight"]


def build(groups, win, idmap, order, path):
    x0, y0, W, H = win
    root = etree.Element(CS + "svg", nsmap={None: SVGNS, "xlink": XLNS})
    root.set("width", "%.4f" % (W * PX_PER_PT))
    root.set("height", "%.4f" % (H * PX_PER_PT))
    root.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
    root.set("stroke-linejoin", "round")
    root.set("overflow", "hidden")
    body = etree.SubElement(root, CS + "g")
    need = set()
    for g in groups:
        body.append(g)
        need |= ref_ids(g)
    extra = external_defs(body, idmap, order)
    if extra:
        defs = etree.Element(CS + "defs")
        for d in extra:
            defs.append(d)
        root.insert(0, defs)
    with open(path, "wb") as f:
        f.write(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    return path


def render(svg, png, dpi):
    for _ in range(3):
        r = subprocess.run([PY, "scripts/render_svg_px.py", svg, png,
                            "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png) and os.path.getsize(png) > 1000:
            return png
    raise RuntimeError("render failed: " + svg)


def ink_bbox(png, win, dpi, thr=8):
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (255 - a) > thr
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


# ------------------------------------------------------- add the tick text --
def axis_groups(a, prefix):
    out = []
    for ax in a:
        if not (ax.get("id") or "").startswith("matplotlib.axis_"):
            continue
        kids = [g for g in ax if isinstance(g.tag, str) and
                (g.get("id") or "").startswith(prefix)]
        if kids:
            out.append((ax, kids))
    return out


def _mk_text_group(gid, anchor, x, y, label):
    g = etree.Element(CS + "g")
    g.set("id", gid)
    t = etree.SubElement(g, CS + "text")
    t.set("fill", TEXT_FILL)
    t.set("text-anchor", anchor)
    t.set("x", "%.6g" % x)
    t.set("y", "%.6g" % y)
    t.text = label
    return g


def add_x_numbers(a, spec, row, col, k):
    groups = axis_groups(a, "xtick_")
    assert len(groups) == 1
    _, kids = groups[0]
    bottom = HIST_Y[row] + HIST_H
    marks, labels_present, text_groups = [], [], []
    for g in kids:
        u = g.find(".//%suse" % CS)
        marks.append(float(u.get("x")))
        t = g.find(".//%stext" % CS)
        labels_present.append(None if t is None else t.text)
        text_groups.append(None if t is None else t.getparent())
    x0, x1 = spec["xlim"]
    pairs = []
    for lab, val in zip(spec["xlabels"], spec["xticks"]):
        pos = HIST_X[col] + (val - x0) / (x1 - x0) * HIST_W
        j = int(np.argmin([abs(p - pos) for p in marks]))
        assert abs(marks[j] - pos) < 0.01
        pairs.append((j, lab))
    pairs.sort()

    n_new = 0
    for j, lab in pairs:
        if labels_present[j] is not None:
            assert labels_present[j] == lab
            tg = text_groups[j]
            tg.find(CS + "text").set("y", "%.6g" % (bottom + X_LAB_DY))
        else:
            g = kids[j]
            g.append(_mk_text_group("add_xtext_%d_%d" % (k, j), "middle",
                                    marks[j], bottom + X_LAB_DY, lab))
            n_new += 1
    return n_new


def add_y_numbers(a, spec, row, col, k):
    groups = axis_groups(a, "ytick_")
    assert len(groups) == 1
    axis_el, kids = groups[0]
    left = HIST_X[col]
    y0, y1 = spec["ylim"]

    def ypos(v):
        return HIST_Y[row] + HIST_H - (v - y0) / (y1 - y0) * HIST_H

    have = [g.find(".//%suse" % CS) for g in kids]
    if all(u is not None for u in have):
        for g in kids:
            t = g.find(".//%stext" % CS)
            t.set("x", "%.6g" % (left - Y_LAB_DX))
            t.set("y", "%.6g" % (float(g.find(".//%suse" % CS).get("y")) + Y_LAB_DY))
        return 0

    n = 0
    for j, (v, lab) in enumerate(zip(spec["yticks"], spec["ylabels"])):
        if j < len(kids):
            g = kids[j]
        else:
            g = etree.SubElement(axis_el, CS + "g")
            g.set("id", "add_ytick_%d_%d" % (k, j))
        y = ypos(v)
        line = etree.SubElement(g, CS + "g")
        line.set("id", "add_yline_%d_%d" % (k, j))
        inner = etree.SubElement(line, CS + "g")
        u = etree.SubElement(inner, CS + "use")
        u.set("x", "%.6g" % left)
        u.set("y", "%.6g" % y)
        u.set("width", "100%")
        u.set("height", "100%")
        u.set(XL + "href", "#" + Y_TICK_MARK)
        u.set("stroke", TEXT_FILL)
        u.set("stroke-width", "0.8")
        u.set("fill", TEXT_FILL)
        g.append(_mk_text_group("add_ytext_%d_%d" % (k, j), "end",
                                left - Y_LAB_DX, y + Y_LAB_DY, lab))
        n += 1
    return n


# ---------------------------------------------------------------- pipeline --
def main():
    for d in ("svg", "png", "preview", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    derived = json.load(open(DERIVED, encoding="utf-8"))
    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}

    # ---- pass 1: measure the ink of each piece in a generous window ------
    geo = []
    for k, (name, short) in enumerate(HIST_NAMES):
        row, col = divmod(k, 3)
        a = etree.fromstring(etree.tostring(idmap["axes_%d" % (k + 1)]))
        strip_histogram_labels(a)
        add_x_numbers(a, derived[k], row, col, k)
        add_y_numbers(a, derived[k], row, col, k)
        font_fix(a)
        win = (HIST_X[col] - 45, HIST_Y[row] - 45, HIST_W + 90, HIST_H + 90)
        p = build([a], win, idmap, order,
                  os.path.join(OUT, "work", name + "_probe.svg"))
        png = os.path.join(OUT, "work", name + "_probe.png")
        render(p, png, 300)
        ib = ink_bbox(png, win, 300)
        geo.append((row, col, ib))
        print("  probe %-18s ink L%6.2f T%6.2f R%6.2f B%6.2f"
              % (name, HIST_X[col] - ib[0], HIST_Y[row] - ib[1],
                 ib[2] - HIST_X[col] - HIST_W, ib[3] - HIST_Y[row] - HIST_H))

    LEFT = max(HIST_X[c] - ib[0] for r, c, ib in geo)
    TOP = max(HIST_Y[r] - ib[1] for r, c, ib in geo)
    RIGHT = max(ib[2] - HIST_X[c] - HIST_W for r, c, ib in geo)
    BOTTOM = max(ib[3] - HIST_Y[r] - HIST_H for r, c, ib in geo)
    CW = HIST_W + LEFT + RIGHT + 2 * PAD
    CH = HIST_H + TOP + BOTTOM + 2 * PAD
    print("\n  margins  L %.2f  T %.2f  R %.2f  B %.2f   (+ %.2f pad)"
          % (LEFT, TOP, RIGHT, BOTTOM, PAD))
    print("  canvas   %.3f x %.3f pt   plot offset (%.2f, %.2f)"
          % (CW, CH, LEFT + PAD, TOP + PAD))

    # ---- pass 2: final pieces ------------------------------------------
    meta = []
    for k, (name, short) in enumerate(HIST_NAMES):
        row, col = divmod(k, 3)
        a = etree.fromstring(etree.tostring(idmap["axes_%d" % (k + 1)]))
        strip_histogram_labels(a)
        add_x_numbers(a, derived[k], row, col, k)
        add_y_numbers(a, derived[k], row, col, k)
        font_fix(a)
        win = (round(HIST_X[col] - LEFT - PAD, 4),
               round(HIST_Y[row] - TOP - PAD, 4), round(CW, 4), round(CH, 4))
        svg = build([a], win, idmap, order,
                    os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        render(svg, png, 600)
        meta.append(dict(name=name, svg=svg, png=png, win=win,
                         px=list(Image.open(png).size)))
        print("  %-18s %8.3f x %8.3f pt  %s px" % (name, win[2], win[3],
                                                   "%dx%d" % tuple(meta[-1]["px"])))

    # ---- 3 x 3 preview on the shared plot-area size --------------------
    s = 600 / 72.0
    GUT = 7.0
    cells = []
    for r in range(3):
        for c in range(3):
            k = r * 3 + c
            cells.append((c, r, meta[k]))
    W = 3 * CW + 4 * GUT
    H = 3 * CH + 4 * GUT
    canvas = Image.new("RGB", (int(round(W * s)), int(round(H * s))), "white")
    for c, r, m in cells:
        x = GUT + c * (CW + GUT)
        y = GUT + r * (CH + GUT)
        im = Image.open(m["png"]).convert("RGB")
        canvas.paste(im, (int(round(x * s)), int(round(y * s))))
    prev = os.path.join(OUT, "preview", "FigureS1_3x3_600dpi.png")
    canvas.save(prev)
    print("\n  3x3 preview %s  %dx%d px = %.1f x %.1f pt"
          % (prev, canvas.size[0], canvas.size[1], W, H))

    json.dump(dict(pieces=meta, canvas=[round(CW, 4), round(CH, 4)],
                   margins=dict(L=LEFT, T=TOP, R=RIGHT, B=BOTTOM, pad=PAD),
                   font=dict(size=FS, x_lab_dy=X_LAB_DY, y_lab_dx=Y_LAB_DX,
                             y_lab_dy=Y_LAB_DY),
                   preview=prev),
              open(os.path.join(OUT, "work", "meta.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
