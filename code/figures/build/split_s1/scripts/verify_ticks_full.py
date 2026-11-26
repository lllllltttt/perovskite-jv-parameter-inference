# -*- coding: utf-8 -*-
"""Verification for the all-ticks Figure S1 set (out_ticks_full/).

A  wording           : no parameter names / Count / log10 titles / panel tags
B  canvas           : nine identical canvases, identical plot-area offset
C  retained artwork : every surviving element is byte-identical to the source
D  tick completeness: x and y tick count / value / position per panel, against
                      work/ticks_derived.json (script + data), not the picture
E  no collateral    : 600-dpi render differs from the source piece only inside
                      the ink of the added elements
F  margins          : all ink inside the canvas, with clearance
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
NEW = "out_ticks_full"
OLD = "out_ticks"
PY = sys.executable

HIST_W, HIST_H = 125.569, 115.162
HIST_X = [44.2399, 209.992, 375.743]
HIST_Y = [35.4384, 198.969, 362.5]
CANVAS_W, CANVAS_H = 171.840, 139.200
OFF_X, OFF_Y = 39.36, 8.88
X_LAB_DY, Y_LAB_DX, Y_LAB_DY = 11.869, 6.5, 2.684

NAMES = ["S1a_01_mu_n", "S1a_02_mu_p", "S1a_03_tau_n", "S1a_04_tau_p",
         "S1a_05_N_c", "S1a_06_N_v", "S1a_07_tau_ETL", "S1a_08_tau_HTL",
         "S1a_09_r_rad"]
BANNED = ["Count", "μ", "τ", "log", "Spearman", "(a)", "(b)", "102,046",
          "Retained", "Pairwise", "N ="]

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


def font_fix(el):
    for t in el.iter(CS + "text"):
        t.set("font-family", "Arial")
        t.set("font-size", "12")


def canon(e):
    """id-free canonical form: structure + attributes (minus ids) + text."""
    def rec(x):
        if not isinstance(x.tag, str):
            return ""
        attrs = tuple(sorted((k, v) for k, v in x.attrib.items() if k != "id"))
        kids = "".join(rec(c) for c in x)
        return "<%s %s>%s</%s>" % (x.tag, attrs, kids, x.tag)
    return rec(e)


def render(svg, png, dpi):
    cmd = [PY, "scripts/render_svg_px.py", svg, png, "--dpi", str(dpi)]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError("render failed " + svg)
    return png


def ink(path, win, dpi, thr=8):
    a = np.asarray(Image.open(path).convert("L")).astype(int)
    return (255 - a) > thr


def bbox_from_mask(m, win, dpi):
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    if not len(rows):
        return None
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


def dilate(m, n):
    out = m.copy()
    for _ in range(n):
        d = out.copy()
        d[1:, :] |= out[:-1, :]
        d[:-1, :] |= out[1:, :]
        d[:, 1:] |= out[:, :-1]
        d[:, :-1] |= out[:, 1:]
        out = d
    return out


# ---------------------------------------------------------------- checks ---
def main():
    derived = json.load(open(DERIVED, encoding="utf-8"))
    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}

    print("=" * 78)
    print("A  wording: only tick numbers may remain")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        texts = [txt(t) for t in root.iter(CS + "text")]
        bad = [t for t in texts
               if any(b in t for b in BANNED)]
        num_ok = all(re.fullmatch(r"[−\-\d][\d,\.]*", t) for t in texts)
        ok(not bad and num_ok, "%-18s %2d numbers, no wording" % (name, len(texts)),
           "" if not bad else "leaked %s" % bad)

    print("\n" + "=" * 78)
    print("B  canvas: nine identical pieces")
    print("=" * 78)
    boxes = []
    for k, name in enumerate(NAMES):
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        vb = [float(v) for v in root.get("viewBox").split()]
        boxes.append(vb)
        row, col = divmod(k, 3)
        dx = round(HIST_X[col] - vb[0], 4)
        dy = round(HIST_Y[row] - vb[1], 4)
        ok(abs(vb[2] - CANVAS_W) < 1e-3 and abs(vb[3] - CANVAS_H) < 1e-3 and
           abs(dx - OFF_X) < 1e-3 and abs(dy - OFF_Y) < 1e-3,
           "%-18s canvas %.3f x %.3f  offset (%.3f, %.3f)"
           % (name, vb[2], vb[3], dx, dy))

    print("\n" + "=" * 78)
    print("C  retained artwork identical to the source")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        exp = etree.fromstring(etree.tostring(idmap["axes_%d" % (k + 1)]))
        strip_histogram_labels(exp)
        font_fix(exp)
        got = etree.fromstring(open(os.path.join(NEW, "svg", name + ".svg"),
                                    "rb").read())
        got = got.find(CS + "g")[0]
        strip_added(got)
        same = canon(exp) == canon(got)
        n_el = sum(1 for _ in exp.iter())
        ok(same, "%-18s %d elements, nothing changed or lost" % (name, n_el))

    print("\n" + "=" * 78)
    print("D  tick marks and numbers, per panel, against script + data")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        row, col = divmod(k, 3)
        spec = derived[k]
        root = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        left = HIST_X[col]
        bottom = HIST_Y[row] + HIST_H
        y0, y1 = spec["ylim"]
        x0, x1 = spec["xlim"]

        # --- x marks ---------------------------------------------------
        xmarks = sorted(float(u.get("x")) for u in root.iter(CS + "use")
                        if u.get(XL + "href") == "#ma815c2b250")
        exp_x = sorted(HIST_X[col] + (v - x0) / (x1 - x0) * HIST_W
                       for v in spec["xticks"])
        dx = max(abs(a - b) for a, b in zip(xmarks, exp_x)) if xmarks else 9

        # --- x numbers -------------------------------------------------
        xtexts = [(t.get("x"), t.get("y"), t.text) for t in root.iter(CS + "text")]
        xt = [(float(x), float(y), s) for x, y, s in xtexts
              if abs(float(y) - (bottom + X_LAB_DY)) < 0.01]
        xt.sort()
        want = sorted(zip(exp_x, spec["xlabels"]))
        dxl = max((abs(a[0] - b[0]) for a, b in zip(xt, want)), default=9)
        same_lab = [a[2] for a in xt] == [b[1] for b in want]
        ok(len(xmarks) == len(spec["xticks"]) and dx < 0.01 and
           len(xt) == len(want) and dxl < 0.01 and same_lab,
           "%-18s x: %d marks, %d numbers %s"
           % (name, len(xmarks), len(xt), [b[1] for b in want]))

        # --- y marks + numbers ----------------------------------------
        ymarks = sorted(float(u.get("y")) for u in root.iter(CS + "use")
                        if u.get(XL + "href") == "#m09f4e2fff5")
        exp_y = sorted(HIST_Y[row] + HIST_H - (v - y0) / (y1 - y0) * HIST_H
                       for v in spec["yticks"])
        dy = max(abs(a - b) for a, b in zip(ymarks, exp_y)) if ymarks else 9
        yt = [(float(x), float(y), s) for x, y, s in xtexts
              if abs(float(x) - (left - Y_LAB_DX)) < 0.01]
        yt.sort(key=lambda r: -r[1])
        ylab = [r[2] for r in yt]
        yposok = all(abs(r[1] - (p + Y_LAB_DY)) < 0.01
                     for r, p in zip(yt, sorted(exp_y, reverse=True)))
        ok(len(ymarks) == len(spec["yticks"]) and dy < 0.01 and
           len(yt) == len(spec["yticks"]) and ylab == spec["ylabels"] and yposok,
           "%-18s y: %d marks, %d numbers %s (ylim 0-%.2f)"
           % (name, len(ymarks), len(yt), ylab, y1))

    print("\n" + "=" * 78)
    print("E  nothing else moved: 600-dpi diff vs the source piece")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        row, col = divmod(k, 3)
        win = (round(HIST_X[col] - OFF_X, 4), round(HIST_Y[row] - OFF_Y, 4),
               CANVAS_W, CANVAS_H)

        # mask = ink of the added elements alone
        new = etree.parse(os.path.join(NEW, "svg", name + ".svg")).getroot()
        added = etree.Element(CS + "svg",
                              nsmap={None: "http://www.w3.org/2000/svg",
                                     "xlink": "http://www.w3.org/1999/xlink"})
        for a in ("width", "height", "viewBox"):
            added.set(a, new.get(a))
        g = etree.SubElement(added, CS + "g")
        defs = new.find(CS + "defs")
        for d in defs:
            g.append(etree.fromstring(etree.tostring(d)))
        for e in new.iter(CS + "g"):
            if is_add(e):
                g.append(etree.fromstring(etree.tostring(e)))
        ms = os.path.join(NEW, "work", name + "_added.svg")
        etree.ElementTree(added).write(ms, xml_declaration=True, encoding="utf-8")
        mp = render(ms, os.path.join(NEW, "work", name + "_added.png"), 600)
        mask = dilate(ink(mp, win, 600), 6)

        a = np.asarray(Image.open(os.path.join(NEW, "png",
                                               name + "_600dpi.png")).convert("L"))
        b = np.asarray(Image.open(os.path.join(OLD, "png",
                                               name + "_600dpi.png")).convert("L"))
        diff = a != b
        outside = int((diff & ~mask).sum())
        inside = int((diff & mask).sum())
        ok(outside == 0, "%-18s diff %6d px, all inside the added ink"
           % (name, inside), "outside=%d" % outside if outside else "")

    print("\n" + "=" * 78)
    print("F  margins: every piece fully inside its canvas")
    print("=" * 78)
    for k, name in enumerate(NAMES):
        row, col = divmod(k, 3)
        win = (round(HIST_X[col] - OFF_X, 4), round(HIST_Y[row] - OFF_Y, 4),
               CANVAS_W, CANVAS_H)
        m = ink(os.path.join(NEW, "png", name + "_600dpi.png"), win, 600)
        bb = bbox_from_mask(m, win, 600)
        L, T = HIST_X[col] - bb[0], HIST_Y[row] - bb[1]
        R, B = bb[2] - (HIST_X[col] + HIST_W), bb[3] - (HIST_Y[row] + HIST_H)
        clear = min(bb[0] - win[0], bb[1] - win[1],
                    win[0] + win[2] - bb[2], win[1] + win[3] - bb[3])
        ok(clear > 0.5, "%-18s margins L%.2f T%.2f R%.2f B%.2f  clearance %.2f pt"
           % (name, L, T, R, B, clear))

    print("\n" + "=" * 78)
    print("G  bar heights: count / ylim reproduces every painted bar top")
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
            nums = [float(v) for v in re.split(r"[ ,MZ]+", pth.get("d")) if v]
            tops.append(nums[5])          # x0 ybase x1 ybase x1 ytop x0 ytop
        want = [HIST_Y[row] + HIST_H - c / (y1 - y0) * HIST_H
                for c in spec["counts"]]
        dev = max((abs(a - b) for a, b in zip(sorted(tops), sorted(want))),
                  default=9)
        ok(len(tops) == 60 and dev < 0.01,
           "%-18s 60 bars, max top deviation %.4f pt" % (name, dev))

    print("\n" + "=" * 78)
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL", len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
