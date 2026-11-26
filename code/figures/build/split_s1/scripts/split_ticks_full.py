# -*- coding: utf-8 -*-
"""Figure S1, fourth specification: all nine histograms carry their OWN
x-axis tick numbers and their OWN y-axis tick numbers.

The source slide was drawn with shared-axis conventions: x tick numbers only
on the bottom row, y tick numbers only in the left column.  Every histogram
axis has a different x range, and every one has a different y range, so the
hidden numbers are restored from the original script + data
(scripts/derive_ticks.py -> work/ticks_derived.json), never from a screenshot.

Kept verbatim from the source : bars, fills, frame, x tick marks (all nine),
                                y tick marks and numbers (left column),
                                x tick numbers (bottom row).
Added                        : x tick numbers on rows 0-1,
                                y tick marks + numbers on columns 1-2
                                (positions from each panel's own ylim, ticks
                                 from the same nice_ticks(0, max_count, 6)
                                 rule the original used on the left column).
Still absent                 : parameter names, "Count", log10(...) titles,
                                panel titles, (a)/(b), "N = 102,046".

Canvas of the nine histograms is unchanged (171.840 x 139.200 pt, plot area
125.569 x 115.162 pt at a fixed offset) so the pieces drop back into the same
PowerPoint grid.
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

OUT = "out_ticks_full"
PREV = "out_ticks"                      # previous (labels incomplete) set
PAD = 3.0
PX_PER_PT = 96.0 / 72.0

HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]
CANVAS_W, CANVAS_H = 171.840, 139.200        # from the previous round
OFF_X, OFF_Y = 39.36, 8.88                   # plot area inside the canvas

TEXT_FILL = "#1A1A1A"
X_LAB_DY = 11.869          # source: text y = plot bottom + 11.869
Y_LAB_DX = 6.5             # source: text x = plot left  - 6.5
Y_LAB_DY = 2.684           # source: text y = tick y + 2.684
Y_TICK_MARK = "m09f4e2fff5"   # 3-pt outward y tick, defined in axes_1

HIST_NAMES = [
    ("S1a_01_mu_n", "mu_n"), ("S1a_02_mu_p", "mu_p"),
    ("S1a_03_tau_n", "tau_n"), ("S1a_04_tau_p", "tau_p"),
    ("S1a_05_N_c", "N_c"), ("S1a_06_N_v", "N_v"),
    ("S1a_07_tau_ETL", "tau_ETL"), ("S1a_08_tau_HTL", "tau_HTL"),
    ("S1a_09_r_rad", "r_rad"),
]
HEAT_NAME = "S1b_heatmap_numbers"


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
        # deep copy: appending the live element would move it out of the
        # source document, emptying the <defs> it lives in (line2d_1)
        out.append(etree.fromstring(etree.tostring(idmap[nid])))
        need |= (ref_ids(idmap[nid]) - have - {d.get("id") for d in out})
    return out


def strip_histogram_labels(a):
    removed = []
    for c in list(a):
        if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
            removed.append((c.get("id"), txt(c)))
            a.remove(c)
    for c in list(a):
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            cid = g.get("id") or ""
            if cid.startswith("xtick_") or cid.startswith("ytick_"):
                continue                      # tick mark + tick number: keep
            if next(g.iter(CS + "text"), None) is not None:
                removed.append((cid or "(unnamed)", txt(g)))
                c.remove(g)
    return removed


def font_fix(el):
    n = 0
    for t in el.iter(CS + "text"):
        t.set("font-family", "Arial")
        t.set("font-size", "12")
        n += 1
    return n


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


def render(svg, png, dpi, bg=None):
    cmd = [PY, "scripts/render_svg_px.py", svg, png, "--dpi", str(dpi)]
    if bg:
        cmd += ["--bg", bg]
    for _ in range(3):
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png) and os.path.getsize(png) > 1000:
            return png
    raise RuntimeError("render failed: " + svg)


def ink_bbox(png, win, dpi, thr=8):
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (255 - a) > thr
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    if not len(rows):
        return None
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


# ------------------------------------------------------- add the tick text --
def axis_groups(a, prefix):
    """[(axis element, [tick group child, ...])] for xtick_/ytick_."""
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


def add_x_numbers(a, spec, row, col, k, log):
    """Rows 0-1 get the numbers their own x axis was drawn with."""
    groups = axis_groups(a, "xtick_")
    assert len(groups) == 1, "expected one x axis per panel"
    _, kids = groups[0]
    bottom = HIST_Y[row] + HIST_H

    # actual mark positions from the artwork
    marks, labels_present = [], []
    for g in kids:
        u = g.find(".//%suse" % CS)
        marks.append(float(u.get("x")))
        t = g.find(".//%stext" % CS)
        labels_present.append(None if t is None else t.text)

    # pair each derived tick with the nearest mark (verified < 0.01 pt)
    x0, x1 = spec["xlim"]
    pairs = []
    for lab, val in zip(spec["xlabels"], spec["xticks"]):
        pos = HIST_X[col] + (val - x0) / (x1 - x0) * HIST_W
        j = int(np.argmin([abs(p - pos) for p in marks]))
        assert abs(marks[j] - pos) < 0.01, (k, val, marks[j], pos)
        pairs.append((j, lab))
    pairs.sort()

    if row == 2:                     # bottom row already carries the numbers
        got = [labels_present[j] for j, _ in pairs]
        want = [lab for _, lab in pairs]
        assert got == want, (k, got, want)
        log.append("%-8s row2 x numbers already present, %d/%d verified"
                   % (spec["name"], len(got), len(want)))
        return 0

    n = 0
    for j, lab in pairs:
        if labels_present[j] is not None:
            assert labels_present[j] == lab
            continue
        g = kids[j]
        g.append(_mk_text_group("add_xtext_%d_%d" % (k, j), "middle",
                                marks[j], bottom + X_LAB_DY, lab))
        n += 1
    log.append("%-8s row%d x numbers added %d/%d" % (spec["name"], row, n, len(pairs)))
    return n


def add_y_numbers(a, spec, row, col, k, log):
    """Columns 1-2 get their own y numbers, at their own ylim."""
    groups = axis_groups(a, "ytick_")
    assert len(groups) == 1, "expected one y axis per panel"
    axis_el, kids = groups[0]
    left = HIST_X[col]
    y0, y1 = spec["ylim"]
    yticks, ylabels = spec["yticks"], spec["ylabels"]

    def ypos(v):
        return HIST_Y[row] + HIST_H - (v - y0) / (y1 - y0) * HIST_H

    have = [g.find(".//%suse" % CS) for g in kids]
    if all(u is not None for u in have):        # left column: keep verbatim
        got = [g.find(".//%stext" % CS).text for g in kids]
        assert got == ylabels, (k, got, ylabels)
        # y grows downward in SVG: smallest y holds the largest value
        dev = max(abs(float(u.get("y")) - ypos(v))
                  for u, v in zip(sorted(have, key=lambda u: float(u.get("y"))),
                                  sorted(yticks, reverse=True)))
        assert dev < 0.01, (k, dev)
        log.append("%-8s left column y numbers already present, %d/%d verified"
                   % (spec["name"], len(got), len(got)))
        return 0

    # the hidden axes kept N empty <g id="ytick_*"/> shells (the tick objects
    # the original locator had created); N need not equal the number of ticks
    # this panel actually gets, so reuse the shells and append the rest.
    n = 0
    for j, (v, lab) in enumerate(zip(yticks, ylabels)):
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
    log.append("%-8s col%d y numbers+marks added %d" % (spec["name"], col, n))
    return n


# ---------------------------------------------------------------- pipeline --
def main():
    for d in ("svg", "png", "preview", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    derived = json.load(open(DERIVED, encoding="utf-8"))
    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}

    def hist_win(row, col):
        """Same canvas size for all nine; origin follows the panel so the plot
        area keeps the identical (39.36, 8.88) offset inside every piece."""
        return (round(HIST_X[col] - OFF_X, 4), round(HIST_Y[row] - OFF_Y, 4),
                CANVAS_W, CANVAS_H)

    log, meta, added_total = [], [], 0

    for k, (name, short) in enumerate(HIST_NAMES):
        row, col = divmod(k, 3)
        a = etree.fromstring(etree.tostring(idmap["axes_%d" % (k + 1)]))
        gone = strip_histogram_labels(a)
        spec = dict(derived[k])
        assert spec["name"] == short, (spec["name"], short)
        added_total += add_x_numbers(a, spec, row, col, k, log)
        added_total += add_y_numbers(a, spec, row, col, k, log)
        font_fix(a)
        win = hist_win(row, col)
        svg = build([a], win, idmap, order,
                    os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        render(svg, png, 600)
        meta.append(dict(name=name, svg=svg, png=png, win=win,
                         px=Image.open(png).size,
                         removed=[t for _, t in gone]))

    # heat map: unchanged from the previous round (byte-identical copy)
    hs = os.path.join(OUT, "svg", HEAT_NAME + ".svg")
    with open(os.path.join(PREV, "svg", HEAT_NAME + ".svg"), "rb") as f:
        blob = f.read()
    with open(hs, "wb") as f:
        f.write(blob)
    hp = os.path.join(OUT, "png", HEAT_NAME + "_600dpi.png")
    with open(os.path.join(PREV, "png", HEAT_NAME + "_600dpi.png"), "rb") as f:
        blob = f.read()
    with open(hp, "wb") as f:
        f.write(blob)
    hv = etree.parse(hs).getroot().get("viewBox").split()
    meta.append(dict(name=HEAT_NAME, svg=hs, png=hp,
                     win=tuple(round(float(v), 4) for v in hv),
                     px=Image.open(hp).size, removed=[]))

    for line in log:
        print("  " + line)
    n_x = sum(int(l.split("added")[1].split("/")[0])
              for l in log if " x numbers added" in l)
    n_y = sum(int(l.split("added")[1])
              for l in log if " y numbers+marks added" in l)
    print("\n  added %d x numbers + %d y numbers (each with a 3-pt tick mark)"
          % (n_x, n_y))

    # ---- preview: pieces pasted back at their original positions --------
    s = 600 / 72.0
    X0 = min(m["win"][0] for m in meta)
    Y0 = min(m["win"][1] for m in meta)
    X1 = max(m["win"][0] + m["win"][2] for m in meta)
    Y1 = max(m["win"][1] + m["win"][3] for m in meta)
    canvas = Image.new("RGBA", (int(round((X1 - X0) * s)),
                                int(round((Y1 - Y0) * s))), (255, 255, 255, 255))
    for m in meta:
        apng = os.path.join(OUT, "work", m["name"] + "_alpha.png")
        render(m["svg"], apng, 600, bg="transparent")
        im = Image.open(apng).convert("RGBA")
        canvas.alpha_composite(im, (int(round((m["win"][0] - X0) * s)),
                                    int(round((m["win"][1] - Y0) * s))))
    prev = os.path.join(OUT, "preview", "FigureS1_allticks_preview_600dpi.png")
    canvas.convert("RGB").save(prev)
    print("\n  preview %s  %dx%d px = %.2f x %.2f pt"
          % (prev, canvas.size[0], canvas.size[1], X1 - X0, Y1 - Y0))

    json.dump(dict(pieces=meta, derived=derived,
                   added=added_total, preview=prev),
              open(os.path.join(OUT, "work", "meta.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
