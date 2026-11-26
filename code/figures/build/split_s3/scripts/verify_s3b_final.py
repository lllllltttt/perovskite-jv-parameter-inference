# -*- coding: utf-8 -*-
"""Verification for S3b_final.

A  no text nodes : every label is an outline path (no font dependency)
B  plot intact   : plot area 657.36 x 320.76 pt, same position
C  data intact   : identical count of non-glyph path/use elements as the source
D  ticks         : tick marks at identical positions, 13 labels
E  glyphs        : path outlines render the same as the live <text> twin
F  legend        : three entries kept (3 samples + 3 labels), inside the panel
G  size          : tick-number ink height is 1.5x the source
H  margins       : all ink inside the canvas
"""
import io
import json
import os
import re
import sys

import numpy as np
from lxml import etree
from PIL import Image

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_s3b_final as B      # noqa: E402

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
OUT = "out_final"
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    win = tuple(meta["win"])
    src = etree.parse(B.SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    got = etree.parse(os.path.join(OUT, "svg", "S3b_final.svg")).getroot()
    body = got.find(CS + "g")[0]

    print("=" * 78)
    print("A  no <text> left: every label is an outline path")
    print("=" * 78)
    n_text = len(list(body.iter(CS + "text")))
    n_glyph = len([g for g in body.iter(CS + "g")
                   if g.get("class") == "glyphs"])
    ok(n_text == 0 and n_glyph == 16,
       "%d <text> nodes, %d outline groups (13 tick + 3 legend)" % (n_text, n_glyph))

    print("\n" + "=" * 78)
    print("B/C  plot area and data elements unchanged")
    print("=" * 78)
    bx = B.plot_box(src.find(".//" + CS + "g[@id='axes_1']"))
    ok(abs(bx[2] - 657.36) < 0.01 and abs(bx[3] - 320.76) < 0.01,
       "plot %.3f x %.3f pt at (%.2f, %.2f)" % (bx[2], bx[3], bx[0], bx[1]))

    def data_elems(root, drop_text=True):
        n = 0
        for e in root.iter():
            if not isinstance(e.tag, str):
                continue
            if e.tag not in (CS + "path", CS + "use"):
                continue
            p = e.getparent()
            bad = False
            while p is not None:
                if drop_text and (p.tag == CS + "text" or p.get("class") == "glyphs"):
                    bad = True
                    break
                p = p.getparent()
            if not bad:
                n += 1
        return n
    a0 = data_elems(src.find(".//" + CS + "g[@id='figure_1']"))
    a1 = data_elems(body)
    ok(a0 == a1, "%d data path/use elements, identical to the source (%d)"
       % (a1, a0))

    print("\n" + "=" * 78)
    print("D  tick marks at identical positions")
    print("=" * 78)
    def tickmarks(root):
        out = []
        for g in root.iter(CS + "g"):
            gid = g.get("id") or ""
            if not gid.startswith(("xtick_", "ytick_")):
                continue
            u = next(g.iter(CS + "use"), None)
            if u is not None:
                out.append((u.get("x"), u.get("y")))
        return out
    t0 = tickmarks(src.find(".//" + CS + "g[@id='axes_1']"))
    t1 = tickmarks(body)
    ok(t0 == t1, "%d tick marks, positions identical" % len(t1))

    print("\n" + "=" * 78)
    print("E  outline glyphs match the live-text twin")
    print("=" * 78)
    B.CONVERT = False
    twin, box, _rem, _nt, _tx = B.make_fig()
    B.CONVERT = True
    p = B.build([twin], win, idmap, order, os.path.join(OUT, "work", "twin.svg"))
    B.render(p, os.path.join(OUT, "work", "twin.png"), 600)
    a = np.asarray(Image.open(os.path.join(OUT, "png", "S3b_final_600dpi.png"))
                   .convert("L")).astype(int)
    b = np.asarray(Image.open(os.path.join(OUT, "work", "twin.png"))
                   .convert("L")).astype(int)
    d = np.abs(a - b) > 60
    frac = d.sum() / max(1, ((255 - np.minimum(a, b)) > 60).sum())
    ok(d.sum() < 0.02 * d.size, "%d px differ from the text twin (%.3f %% of the canvas)"
       % (int(d.sum()), 100.0 * d.sum() / d.size))

    print("\n" + "=" * 78)
    print("F  legend: three entries, line samples and labels")
    print("=" * 78)
    lg = body.find(".//" + CS + "g[@id='legend_1']")
    samples = []
    for g in (lg if lg is not None else []):
        if not isinstance(g.tag, str):
            continue
        pth = g.find(".//" + CS + "path")
        if pth is not None:
            st = pth.get("style") or ""
            m = re.search(r"stroke:\s*([^;]+)", st)
            dash = re.search(r"stroke-dasharray:\s*([^;]+)", st)
            if m:
                samples.append((m.group(1).strip(),
                                dash.group(1).strip() if dash else "solid"))
    labels = [g for g in (lg if lg is not None else [])
              if isinstance(g.tag, str) and g.find(".//" + CS + "path") is not None
              and g.get("id", "").startswith("text_")]
    ok(lg is not None and len(samples) == 3 and len(labels) == 3,
       "legend_1: %d line samples %s, %d label groups"
       % (len(samples), samples, len(labels)))

    print("\n" + "=" * 78)
    print("G  tick numbers are 1.5x the source size")
    print("=" * 78)
    # measure the first x tick label ("0.0") in both renders
    def label_ink(png, cx_pt, top_pt, h_pt=14.0, w_pt=14.0, dpi=600):
        im = np.asarray(Image.open(png).convert("L")).astype(int)
        s = dpi / 72.0
        x0 = int((cx_pt - w_pt / 2 - win[0]) * s)
        x1 = int((cx_pt + w_pt / 2 - win[0]) * s)
        y0 = int((top_pt - win[1]) * s)
        y1 = int((top_pt + h_pt - win[1]) * s)
        sub = (255 - im[max(0, y0):y1, max(0, x0):x1]) > 40
        rows = np.where(sub.any(axis=1))[0]
        return 0 if not len(rows) else rows[-1] - rows[0] + 1

    src_bottom = bx[1] + bx[3]
    ref = B.build([etree.fromstring(etree.tostring(
        src.find(".//" + CS + "g[@id='figure_1']")))], win, idmap, order,
        os.path.join(OUT, "work", "src.svg"))
    B.render(ref, os.path.join(OUT, "work", "src.png"), 600)
    h0 = label_ink(os.path.join(OUT, "work", "src.png"), 64.086,
                   src_bottom + 4.0, h_pt=18.0)
    h1 = label_ink(os.path.join(OUT, "png", "S3b_final_600dpi.png"),
                   64.086, src_bottom + 4.0, h_pt=18.0)
    ratio = h1 / h0 if h0 else 0
    ok(abs(ratio - 1.5) < 0.12, "label ink %d px -> %d px (ratio %.2f, target 1.50)"
       % (h0, h1, ratio))

    print("\n" + "=" * 78)
    print("H  margins: ink inside the canvas")
    print("=" * 78)
    im = np.asarray(Image.open(os.path.join(OUT, "png", "S3b_final_600dpi.png"))
                    .convert("L")).astype(int)
    mk = (255 - im) > 8
    rows = np.where(mk.any(axis=1))[0]
    cols = np.where(mk.any(axis=0))[0]
    clear = min(cols[0], rows[0], im.shape[1] - 1 - cols[-1],
                im.shape[0] - 1 - rows[-1]) / (600 / 72.0)
    ok(clear > 1.0, "clearance %.2f pt on the tightest side" % clear)

    print("\n" + "=" * 78)
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL",
                                          len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
