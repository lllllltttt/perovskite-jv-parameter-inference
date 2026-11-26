# -*- coding: utf-8 -*-
"""Verify the twelve value labels of Figure S10 and that nothing else moved.

V1  each label text is the 3-dp mean of its five seeds (U+2212 for negatives)
V2  the label sits above its summary bar, right of it (left for the last group)
V3  the box was pure white before the label was added -> no dot, bar, grid,
    zero line or frame is covered
V4  the only pixels that changed vs the approved render are inside the boxes
V5  every box is inside the axes with >= 0.8 pt clearance
V6  the SVG tree equals the approved one once the six text groups are removed
V7  Arial outlines only (no <text>), U+2212 glyph for negatives, 600 dpi
"""
import json
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
                   "metrics", "paired_differences.csv")
OUT = os.path.join(BASE, "20261119_si_s10_labels", "out")
WORK = os.path.join(BASE, "20261119_si_s10_labels", "work")
OLD = os.path.join(BASE, "20261117_figs9_common", "out")
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
COL = "diff_new_minus_old_rmse"
PX = 600 / 72.0
FIG_H = 169.79
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-64s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def canon(el):
    e = etree.fromstring(etree.tostring(el))
    for x in e.iter():
        if x.text is not None and not x.text.strip():
            x.text = None
        if x.tail is not None and not x.tail.strip():
            x.tail = None
    return etree.tostring(e)


def normalise(root):
    mapping = {}

    def key(v):
        if v not in mapping:
            mapping[v] = "ID%d" % len(mapping)
        return mapping[v]

    for el in list(root.iter("{%s}date" % "http://purl.org/dc/elements/1.1/")):
        el.text = "DATE"
    for el in root.iter():
        i = el.get("id")
        if i and re.match(r"^[pm][0-9a-f]{10,}$", i):
            el.set("id", key(i))
        cp = el.get("clip-path")
        if cp:
            el.set("clip-path", "url(#%s)" % key(cp[5:-1]))
        h = el.get(XL + "href")
        if h and h.startswith("#") and re.match(r"^[pm][0-9a-f]{10,}$", h[1:]):
            el.set(XL + "href", "#" + key(h[1:]))
    return root


def main():
    P = pd.read_csv(CSV)
    want = {}
    for arm, stem in (("original", "common_test_a"), ("expanded", "common_test_b")):
        g = P[P["test_arm"] == arm]
        want[stem] = [float(np.mean(g[g["quantity"] == c][COL].astype(float)))
                      for c in COORDS]

    meta = json.load(open(os.path.join(WORK, "labels.json")))
    print("=" * 84)
    for stem in ("common_test_a", "common_test_b"):
        print(stem)
        root = etree.parse(os.path.join(OUT, stem + ".svg")).getroot()
        old = etree.parse(os.path.join(OLD, stem + ".svg")).getroot()
        ax = [g for g in root.iter(CS + "g")
              if (g.get("id") or "").startswith("axes_")][0]

        groups = []
        for c in ax:
            if not (c.get("id") or "").startswith("text_"):
                continue
            com = [n.text.strip() for n in c if not isinstance(n.tag, str)
                   and n.text and n.text.strip()]
            if com:
                groups.append((c, com[0]))
        strings = [s for _, s in groups]

        exp = [("\u2212" if v < 0 else "") + "%.3f" % abs(v)
               for v in want[stem]]
        ok(len(groups) == 6 and strings == exp,
           "V1 six labels = 3-dp mean of the five seeds",
           " | ".join(strings))

        # axes rect (SVG coordinates, y down)
        v = [float(x) for x in re.findall(
            r"-?\d+\.?\d*", ax.find(CS + "g").find(CS + "path").get("d"))]
        xs, ys = v[0::2], v[1::2]
        AX0, AY0, AX1, AY1 = min(xs), min(ys), max(xs), max(ys)

        # summary bars: 2-point black 1.8 pt paths
        bars = []
        for p in ax.iter(CS + "path"):
            st = p.get("style") or ""
            if "stroke: #000000; stroke-width: 1.8" in st:
                q = [float(t) for t in re.findall(r"-?\d+\.?\d*", p.get("d"))]
                bars.append((min(q[0], q[2]), max(q[0], q[2]), q[1]))

        # label origin + bbox (figure points, y up -> convert to SVG)
        side_ok = above_ok = box_ok = True
        for k, (g, s) in enumerate(groups):
            tr = g.find(CS + "g").get("transform")
            m = re.search(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\)", tr)
            tx, ty = float(m.group(1)), float(m.group(2))     # SVG coords
            info = meta[stem][k]
            x0, y0, x1, y1 = info["box"]                      # points, y up
            bx0, bx1, by = bars[k]
            if info["side"] == "right":
                side_ok &= (x0 >= bx1 - 0.05)
            else:
                side_ok &= (x1 <= bx0 + 0.05)
            above_ok &= (ty < by - 0.5)
            sy0, sy1 = FIG_H - y1, FIG_H - y0
            box_ok &= (x0 >= AX0 + 0.8 and x1 <= AX1 - 0.8
                       and sy0 >= AY0 + 0.8 and sy1 <= AY1 - 0.8)
        ok(side_ok, "V2a every label on the correct side of its bar")
        ok(above_ok, "V2b every baseline above its bar")
        ok(box_ok, "V5 boxes inside the axes, >= 0.8 pt from the frame")

        # pixel comparison against the approved render
        new = np.asarray(Image.open(os.path.join(OUT, stem + ".png")).convert("RGB")).astype(int)
        oldp = np.asarray(Image.open(os.path.join(OLD, stem + ".png")).convert("RGB")).astype(int)
        boxes_px = []
        for info in meta[stem]:
            x0, y0, x1, y1 = info["box"]
            c0 = int(np.floor(x0 * PX)) - 2
            c1 = int(np.ceil(x1 * PX)) + 2
            r0 = int(np.floor((FIG_H - y1) * PX)) - 2
            r1 = int(np.ceil((FIG_H - y0) * PX)) + 2
            boxes_px.append((max(r0, 0), r1, max(c0, 0), c1))
        mask = np.zeros(new.shape[:2], bool)
        for (r0, r1, c0, c1) in boxes_px:
            mask[r0:r1, c0:c1] = True
        diff = (new != oldp).any(axis=2)
        outside = int((diff & ~mask).sum())
        ok(outside == 0 and int(diff.sum()) > 0,
           "V4 only the label boxes changed",
           "%d px changed, %d outside" % (diff.sum(), outside))

        whites = []
        for (r0, r1, c0, c1) in boxes_px:
            crop = oldp[r0:r1, c0:c1]
            whites.append(float((crop.min(axis=2) >= 250).mean()))
        ok(min(whites) == 1.0,
           "V3 every box was pure white before (no dot/bar/grid/frame)",
           "min white %.1f%%" % (100 * min(whites)))

        # tree equality apart from the labels
        rn = etree.fromstring(etree.tostring(root))
        axn = [g for g in rn.iter(CS + "g")
               if (g.get("id") or "").startswith("axes_")][0]
        removed = 0
        for c in list(axn):
            if not (c.get("id") or "").startswith("text_"):
                continue
            if any(not isinstance(n.tag, str) and n.text and n.text.strip()
                   for n in c):
                axn.remove(c)
                removed += 1
        ok(removed == 6 and canon(normalise(rn)) == canon(normalise(
            etree.fromstring(etree.tostring(old)))),
           "V6 SVG tree identical to the approved panel apart from the labels",
           "removed %d groups" % removed)

        ntext = len(list(root.iter(CS + "text")))
        hrefs = [u.get(XL + "href") or "" for u in root.iter(CS + "use")]
        glyph = [h for h in hrefs if re.match(r"^#[A-Za-z]+-", h)]
        bad = [h for h in glyph if not h.startswith("#ArialMT-")]
        minus = sum(1 for g, _ in groups
                    if "#ArialMT-2212" in [u.get(XL + "href")
                                           for u in g.iter(CS + "use")])
        im = Image.open(os.path.join(OUT, stem + ".png"))
        ok(ntext == 0 and not bad and abs(im.info.get("dpi", (0,))[0] - 600) < 1
           and im.size == Image.open(os.path.join(OLD, stem + ".png")).size,
           "V7 Arial outlines, no <text>, 600 dpi, same canvas",
           "%d glyphs, %d minus glyphs" % (len(glyph), minus))

    print("=" * 84)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
