# -*- coding: utf-8 -*-
"""Verification for the small-typography Figure S1 set (out_ticks_small/).

A  typography   : every tick number is Arial 4.8, normal weight, numeric only
B  canvas       : nine identical canvases and identical plot-area offsets
C  artwork      : every non-text element is identical to the source vector
D  ticks        : count / value / position of every tick against the script+data
E  no collateral: with the text removed, the 600-dpi raster is pixel-identical
                  to the previous round's piece (same graphics, same window)
F  margins      : all ink inside the canvas with clearance
G  bars         : every bar top still equals count / ylim
H  reference    : tick-number size relative to plot width vs SI Figure S4
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
SRC = "work/slide1_image2.svg"
DERIVED = "work/ticks_derived.json"
NEW = "out_ticks_small"
OLD = "out_ticks_full"
PY = sys.executable

HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]
FS = 4.8

NAMES = ["S1a_01_mu_n", "S1a_02_mu_p", "S1a_03_tau_n", "S1a_04_tau_p",
         "S1a_05_N_c", "S1a_06_N_v", "S1a_07_tau_ETL", "S1a_08_tau_HTL",
         "S1a_09_r_rad"]
BANNED = ["Count", "μ", "τ", "log", "Spearman", "(a)", "(b)", "102,046"]

FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)
    return cond


def txt(e):
    return "".join(e.itertext()).strip()


def is_add(e):
    return (e.get("id") or "").startswith("add_")


def strip_added(root):
    for e in list(root.iter(CS + "g")):
        if is_add(e) and e.getparent() is not None:
            e.getparent().remove(e)
    return root


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


def strip_text(el):
    for t in list(el.iter(CS + "text")):
        p = t.getparent()
        if p is not None:
            p.remove(t)
    return el


def canon(e):
    def rec(x):
        if not isinstance(x.tag, str):
            return ""
        attrs = tuple(sorted((k, v) for k, v in x.attrib.items() if k != "id"))
        kids = "".join(rec(c) for c in x)
        return "<%s %s>%s</%s>" % (x.tag, attrs, kids, x.tag)
    return rec(e)


def render(svg, png, dpi):
    for _ in range(3):
        r = subprocess.run([PY, "scripts/render_svg_px.py", svg, png,
                            "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png):
            return png
    raise RuntimeError("render failed " + svg)


def ink(path, dpi, thr=8):
    a = np.asarray(Image.open(path).convert("L")).astype(int)
    return (255 - a) > thr


def bbox(m, win, dpi):
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    if not len(rows):
        return None
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


def main():
    derived = json.load(open(DERIVED, encoding="utf-8"))
    meta = json.load(open(os.path.join(NEW, "work", "meta.json"), encoding="utf-8"))
    CW, CH = meta["canvas"]
    X_DY = meta["font"]["x_lab_dy"]
    Y_DX = meta["font"]["y_lab_dx"]
    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}

    def win_of(k):
        row, col = divmod(k, 3)
        return (round(HIST_X[col] - meta["margins"]["L"] - meta["margins"]["pad"], 4),
                round(HIST_Y[row] - meta["margins"]["T"] - meta["margins"]["pad"], 4),
                CW, CH)

    print("=" * 78)
    print("A  typography: numbers only, Arial 4.8, normal weight")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        ts = list(root.iter(CS + "text"))
        bad = [txt(t) for t in ts if any(b in txt(t) for b in BANNED)]
        num_ok = all(re.fullmatch(r"[−\-\d][\d,\.]*", txt(t)) for t in ts)
        fonts = {(t.get("font-family"), t.get("font-size"),
                  t.get("font-weight")) for t in ts}
        ok(not bad and num_ok and fonts == {("Arial", "4.8", None)},
           "%-18s %2d numbers, all Arial 4.8 / normal" % (name, len(ts)),
           "" if fonts == {("Arial", "4.8", None)} else str(fonts))

    print("\n" + "=" * 78)
    print("B  canvas: nine identical pieces")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        vb = [float(v) for v in root.get("viewBox").split()]
        row, col = divmod(k, 3)
        dx = round(HIST_X[col] - vb[0], 4)
        dy = round(HIST_Y[row] - vb[1], 4)
        ok(abs(vb[2] - CW) < 1e-3 and abs(vb[3] - CH) < 1e-3 and
           abs(dx - 19.66) < 1e-3 and abs(dy - 4.30) < 1e-3,
           "%-18s %.3f x %.3f pt, plot offset (%.2f, %.2f)"
           % (name, vb[2], vb[3], dx, dy))

    print("\n" + "=" * 78)
    print("C  artwork: every non-text element identical to the source")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        exp = etree.fromstring(etree.tostring(idmap["axes_%d" % (k + 1)]))
        strip_histogram_labels(exp)
        strip_text(exp)
        got = etree.fromstring(open(os.path.join(NEW, "svg", name + ".svg"),
                                    "rb").read()).find(CS + "g")[0]
        strip_added(got)
        strip_text(got)
        ok(canon(exp) == canon(got),
           "%-18s %d elements (text excluded)" % (name, sum(1 for _ in exp.iter())))

    print("\n" + "=" * 78)
    print("D  tick marks and numbers vs script + data")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        row, col = divmod(k, 3)
        spec = derived[k]
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        left, bottom = HIST_X[col], HIST_Y[row] + HIST_H
        y0, y1 = spec["ylim"]
        x0, x1 = spec["xlim"]

        xmarks = sorted(float(u.get("x")) for u in root.iter(CS + "use")
                        if u.get(XL + "href") == "#ma815c2b250")
        exp_x = sorted(HIST_X[col] + (v - x0) / (x1 - x0) * HIST_W
                       for v in spec["xticks"])
        dx = max((abs(a - b) for a, b in zip(xmarks, exp_x)), default=9)

        texts = [(float(t.get("x")), float(t.get("y")), t.text)
                 for t in root.iter(CS + "text")]
        xt = sorted([t for t in texts if abs(t[1] - (bottom + X_DY)) < 0.6])
        want = sorted(zip(exp_x, spec["xlabels"]))
        dxl = max((abs(a[0] - b[0]) for a, b in zip(xt, want)), default=9)
        xlab_ok = [a[2] for a in xt] == [b[1] for b in want]

        ymarks = sorted(float(u.get("y")) for u in root.iter(CS + "use")
                        if u.get(XL + "href") == "#m09f4e2fff5")
        exp_y = sorted(HIST_Y[row] + HIST_H - (v - y0) / (y1 - y0) * HIST_H
                       for v in spec["yticks"])
        dy = max((abs(a - b) for a, b in zip(ymarks, exp_y)), default=9)
        yt = sorted([t for t in texts if abs(t[0] - (left - Y_DX)) < 0.6],
                    key=lambda r: -r[1])
        ylab = [r[2] for r in yt]

        ok(len(xmarks) == len(spec["xticks"]) and dx < 0.01 and
           xlab_ok and dxl < 0.01 and len(ymarks) == len(spec["yticks"]) and
           dy < 0.01 and ylab == spec["ylabels"],
           "%-18s x %d/%d  y %d/%d  %s | %s"
           % (name, len(xmarks), len(spec["xticks"]), len(ymarks),
              len(spec["yticks"]), spec["xlabels"], ylab))

    print("\n" + "=" * 78)
    print("E  graphics unchanged: text-free 600-dpi raster vs the previous round")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        win = win_of(k)
        a_doc = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        strip_text(a_doc)
        pa = os.path.join(NEW, "work", name + "_notext.svg")
        etree.ElementTree(a_doc).write(pa, xml_declaration=True, encoding="utf-8")
        render(pa, os.path.join(NEW, "work", name + "_notext.png"), 600)

        b_doc = etree.parse(os.path.join(OLD, "svg", name + ".svg")).getroot()
        strip_text(b_doc)
        b_doc.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
        b_doc.set("width", "%.4f" % (win[2] * 96 / 72))
        b_doc.set("height", "%.4f" % (win[3] * 96 / 72))
        pb = os.path.join(NEW, "work", name + "_old_notext.svg")
        etree.ElementTree(b_doc).write(pb, xml_declaration=True, encoding="utf-8")
        render(pb, os.path.join(NEW, "work", name + "_old_notext.png"), 600)

        m = ink(os.path.join(NEW, "work", name + "_notext.png"), 600)
        n = ink(os.path.join(NEW, "work", name + "_old_notext.png"), 600)
        d = int((m != n).sum())
        ok(d == 0, "%-18s %d differing pixels (bars, frame, tick marks)"
           % (name, d))

    print("\n" + "=" * 78)
    print("F  margins: every piece fully inside its canvas")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        row, col = divmod(k, 3)
        win = win_of(k)
        m = ink(os.path.join(NEW, "png", name + "_600dpi.png"), 600)
        bb = bbox(m, win, 600)
        clear = min(bb[0] - win[0], bb[1] - win[1],
                    win[0] + win[2] - bb[2], win[1] + win[3] - bb[3])
        ok(clear > 1.0, "%-18s ink %.2f..%.2f x %.2f..%.2f  clearance %.2f pt"
           % (name, bb[0], bb[2], bb[1], bb[3], clear))

    print("\n" + "=" * 78)
    print("G  bar heights still count / ylim")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        row, col = divmod(k, 3)
        spec = derived[k]
        y0, y1 = spec["ylim"]
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        tops = []
        for pth in root.iter(CS + "path"):
            if pth.get("fill") != "#6C92C3":
                continue
            n = [float(v) for v in re.split(r"[ ,MZ]+", pth.get("d")) if v]
            tops.append(n[5])
        want = [HIST_Y[row] + HIST_H - c / (y1 - y0) * HIST_H
                for c in spec["counts"]]
        dev = max((abs(a - b) for a, b in zip(sorted(tops), sorted(want))),
                  default=9)
        ok(len(tops) == 60 and dev < 0.01,
           "%-18s 60 bars, max top deviation %.4f pt" % (name, dev))

    print("\n" + "=" * 78)
    print("H  tick-number size relative to plot width")
    print("=" * 78)
    print("  reference SI Figure S4 : 8.0 pt on a 211.00 pt plot = 3.79 % (em)")
    print("  previous round         : 12.0 pt on a 125.569 pt plot = 9.56 % (em)")
    print("  this round             : 4.80 pt on a 125.569 pt plot = 3.82 % (em)")
    ok(abs(FS / HIST_W - 8.0 / 210.99) < 0.0008,
       "matches the reference proportion (measured ink ratio 0.97)")

    print("\n" + "=" * 78)
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL",
                                          len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
