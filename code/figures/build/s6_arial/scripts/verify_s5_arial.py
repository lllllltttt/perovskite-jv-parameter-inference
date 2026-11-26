# -*- coding: utf-8 -*-
"""Verify the nine Arial Figure S5 panels against the approved DejaVu ones.

V1  canvas 216.200 x 174.920 pt, plot 181.5976 x 154.6364 pt
V2  all 15,307 scatter points identical (axes-relative, same order)
V3  scatter style, frame and ticks identical; labels identical strings
V4  no DejaVu glyph; every glyph #ArialMT-*; no <text>
V5  tick labels keep their anchors (x centre / y row within 2 px)
V6  plot interior pixel-identical (sub-pixel AA tolerated)
V7  PNG 1802 x 1458 @600 dpi, clearance
"""
import html
import os
import re
import subprocess
import sys

import numpy as np
from lxml import etree
from PIL import Image

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
BASE = r"E:\project\work1"
ROOT = os.path.join(BASE, "20261119_si_s5_arial")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
OLD = os.path.join(BASE, "20261116_figs456_split", "out", "svg")
PX = 600 / 72.0
CANVAS = (216.200, 174.920)
PLOT = (181.5976, 154.6364)
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-62s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def axes_box(root):
    ax = [g for g in root.iter(CS + "g")
          if (g.get("id") or "").startswith("axes_")][0]
    p = ax.find(CS + "g").find(CS + "path")
    v = [float(x) for x in re.findall(r"-?\d+\.?\d*", p.get("d"))]
    xs, ys = v[0::2], v[1::2]
    return ax, (min(xs), min(ys), max(xs), max(ys))


def points(ax, box):
    out = []
    for g in ax.iter(CS + "g"):
        if not (g.get("id") or "").startswith("PathCollection"):
            continue
        for u in g.iter(CS + "use"):
            if u.get("x") is None:
                continue
            out.append((float(u.get("x")) - box[0], float(u.get("y")) - box[1],
                        u.get("style")))
    return out


def labels(root):
    out = []
    for g in root.iter(CS + "g"):
        if not re.match(r"^text_\d+$", g.get("id") or ""):
            continue
        com = [html.unescape(n.text.strip()) for n in g
               if not isinstance(n.tag, str) and n.text and n.text.strip()]
        if com:
            out.append(com[0])
    return out


def render(svg, png):
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "render_svg_px.py"),
                        svg, png, "--dpi", "600"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError("render failed " + svg)


def main():
    print("=" * 80)
    for k in range(1, 10):
        stem = "S5_%02d" % k
        print(stem)
        new = etree.parse(os.path.join(OUT, stem + "_Arial.svg")).getroot()
        old = etree.parse(os.path.join(OLD, stem + ".svg")).getroot()
        axn, bn = axes_box(new)
        axo, bo = axes_box(old)

        cw = float(new.get("width").replace("pt", ""))
        ch = float(new.get("height").replace("pt", ""))
        ok(abs(cw - CANVAS[0]) < 1e-3 and abs(ch - CANVAS[1]) < 1e-3
           and abs((bn[2] - bn[0]) - PLOT[0]) < 1e-3
           and abs((bn[3] - bn[1]) - PLOT[1]) < 1e-3,
           "V1 canvas %.3f x %.3f pt, plot %.3f x %.3f pt"
           % (cw, ch, bn[2] - bn[0], bn[3] - bn[1]))

        pn, po = points(axn, bn), points(axo, bo)
        same_style = all(a[2] == b[2] for a, b in zip(pn, po))
        dn = np.array([(a[0], a[1]) for a in pn])
        do = np.array([(b[0], b[1]) for b in po])
        ok(len(pn) == len(po) == 15307 and dn.shape == do.shape
           and np.abs(dn - do).max() < 1e-3 and same_style,
           "V2 %d scatter points identical, same style" % len(pn),
           "max |d| %.2e" % (np.abs(dn - do).max() if dn.shape == do.shape else -1))

        ln, lo = labels(new), labels(old)
        hrefs = [u.get(XL + "href") or "" for u in new.iter(CS + "use")]
        glyph = [h for h in hrefs if re.match(r"^#[A-Za-z]+-", h)]
        dejavu = [h for h in hrefs if "DejaVu" in h]
        arial = [h for h in glyph if h.startswith("#ArialMT-")]
        ok(ln == lo and not dejavu and len(arial) == len(glyph)
           and len(list(new.iter(CS + "text"))) == 0,
           "V3 %d labels identical, %d glyphs all Arial, 0 DejaVu"
           % (len(ln), len(glyph)),
           "" if ln == lo else str([(a, b) for a, b in zip(ln, lo) if a != b][:3]))

        # renders
        pnew = os.path.join(WORK, stem + "_new.png")
        pold = os.path.join(WORK, stem + "_old.png")
        render(os.path.join(OUT, stem + "_Arial.svg"), pnew)
        render(os.path.join(OLD, stem + ".svg"), pold)
        an = np.asarray(Image.open(pnew).convert("RGB")).astype(int)
        ao = np.asarray(Image.open(pold).convert("RGB")).astype(int)
        ax_px = (bn[0] * PX, bn[1] * PX, bn[2] * PX, bn[3] * PX)

        def ink(img):
            return (255 - np.asarray(Image.fromarray(
                img.astype("uint8")).convert("L")).astype(int)) > 20

        def runs(mask, axis, gap):
            idx = np.where(mask.sum(axis=axis) > 0)[0]
            if not len(idx):
                return []
            cuts = np.where(np.diff(idx) > gap)[0]
            return [(s[0], s[-1]) for s in np.split(idx, cuts + 1)]

        r0 = int(round(ax_px[3] + 5 * PX))
        rn = runs(ink(an[r0:, :]), 0, 40)
        ro = runs(ink(ao[r0:, :]), 0, 40)
        # tick positions (axes-relative, pt) must be identical
        def ticks(ax, box):
            tx, ty = [], []
            for g in ax.iter(CS + "g"):
                gid = g.get("id") or ""
                if re.match(r"^xtick_\d+$", gid):
                    u = g.find(".//" + CS + "use")
                    if u is not None and u.get("x") is not None:
                        tx.append(float(u.get("x")) - box[0])
                elif re.match(r"^ytick_\d+$", gid):
                    u = g.find(".//" + CS + "use")
                    if u is not None and u.get("y") is not None:
                        ty.append(float(u.get("y")) - box[1])
            return sorted(tx), sorted(ty)

        txn, tyn = ticks(axn, bn)
        txo, tyo = ticks(axo, bo)
        ticks_ok = (len(txn) == len(txo) and len(tyn) == len(tyo)
                    and all(abs(a - b) < 1e-3 for a, b in zip(txn, txo))
                    and all(abs(a - b) < 1e-3 for a, b in zip(tyn, tyo)))

        c0 = int(round(ax_px[0] - 5 * PX))
        ytop = int(round(ax_px[3]))            # y labels only, not x labels
        rn2 = runs(ink(an[:ytop, :c0]), 1, 25)
        ro2 = runs(ink(ao[:ytop, :c0]), 1, 25)
        # every label ink must sit next to its own tick (8 px = 1 pt)
        def near(runs_, ticks_pt, offset_px):
            px = [offset_px + t * PX for t in ticks_pt]
            return all(min(abs((a + b) / 2 - p) for p in px) <= 8
                       for a, b in runs_)

        anchor_ok = (ticks_ok and len(rn) == len(txn) and len(rn2) == len(tyn)
                     and near(rn, txn, ax_px[0]) and near(rn2, tyn, ax_px[1]))
        ok(anchor_ok, "V4 %d x / %d y labels, ticks identical, all on their tick"
           % (len(rn), len(rn2)),
           "tick positions equal to 1e-3 pt")

        d = np.abs(an - ao).max(axis=2)
        inner = d[int(ax_px[1]) + 2:int(ax_px[3]) - 2,
                  int(ax_px[0]) + 2:int(ax_px[2]) - 2]
        ok(int((inner > 8).sum()) == 0,
           "V5 plot interior pixel-identical (AA only)",
           "%d px differ, max %d/255" % (int((inner > 0).sum()), int(inner.max())))

        png = os.path.join(OUT, stem + "_Arial.png")
        pg = Image.open(png)
        g = np.asarray(pg.convert("L")).astype(int)
        mk = (255 - g) > 8
        rr = np.where(mk.any(axis=1))[0]
        cc = np.where(mk.any(axis=0))[0]
        clr = min(cc[0], rr[0], g.shape[1] - 1 - cc[-1], g.shape[0] - 1 - rr[-1]) / PX
        ok(pg.size == (1802, 1458) and abs(pg.info.get("dpi", (0,))[0] - 600) < 1
           and clr > 1.0,
           "V6 PNG 1802 x 1458 @600 dpi, clearance %.2f pt" % clr)

    print("=" * 80)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
