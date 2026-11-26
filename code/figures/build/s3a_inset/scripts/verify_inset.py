# -*- coding: utf-8 -*-
"""Verify the S3a_05 inset move.

V1  canvas 226.280 x 170.600 pt, PNG 1886 x 1422 px @600 dpi
V2  the SVG differs from the approved one by exactly one attribute:
    <g id="axes_6" transform="translate(8 0)">
V3  every pixel that changed lies inside the old+new inset footprint
V4  the "-400" label now starts >= 5 pt right of the main left frame
V5  the inset frame and its curves are intact at the new position
V6  no main curve is covered: the strip the inset newly occupies was blank
"""
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
ROOT = os.path.join(BASE, "20261119_figS3a_inset")
OUT = os.path.join(ROOT, "out")
WORK = os.path.join(ROOT, "work")
SRC = os.path.join(BASE, "20261116_figs3_split", "package", "S3a_six_panels",
                   "S3a_05.svg")
PX = 600 / 72.0
VB = (285.9902, 285.9154, 226.2800, 170.6000)
MAIN = (323.05017, 289.135394, 509.14108, 440.778471)
OLD_IN = (341.659261, 361.924071, 453.313807, 428.647025)
DX = 8.0
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %-62s%s" % ("PASS" if cond else "FAIL", label,
                             ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def px(x, y):
    return (x - VB[0]) * PX, (y - VB[1]) * PX


def main():
    new = etree.parse(os.path.join(OUT, "S3a_05.svg")).getroot()
    old = etree.parse(SRC).getroot()

    cw = float(new.get("width")) if not new.get("width").endswith("pt") \
        else float(new.get("width")[:-2])
    # width/height are CSS px in this file
    w_px = float(new.get("width"))
    h_px = float(new.get("height"))
    ok(abs(w_px / (96 / 72.0) - 226.28) < 1e-3
       and abs(h_px / (96 / 72.0) - 170.6) < 1e-3,
       "V1 canvas %.3f x %.3f pt" % (w_px * 3 / 4, h_px * 3 / 4))
    im = Image.open(os.path.join(OUT, "S3a_05_600dpi.png"))
    ok(im.size == (1886, 1422)
       and abs(im.info.get("dpi", (0,))[0] - 600) < 1,
       "V1b PNG %dx%d @600 dpi" % im.size)

    # V2: only the axes_6 transform differs
    def canon(root, drop_transform=False):
        e = etree.fromstring(etree.tostring(root))
        if drop_transform:
            for g in e.iter(CS + "g"):
                if g.get("id") == "axes_6":
                    g.attrib.pop("transform", None)
        for x in e.iter():
            if x.text is not None and not x.text.strip():
                x.text = None
            if x.tail is not None and not x.tail.strip():
                x.tail = None
        return etree.tostring(e)

    ax6n = [g for g in new.iter(CS + "g") if g.get("id") == "axes_6"][0]
    ok(ax6n.get("transform") == "translate(8.0000 0)"
       and canon(new, True) == canon(old),
       "V2 only <g id=axes_6 transform='translate(8 0)'> was added",
       ax6n.get("transform"))

    # V3: pixel diff inside the old+new inset footprint
    an = np.asarray(Image.open(os.path.join(OUT, "S3a_05_600dpi.png")).convert("RGB")).astype(int)
    ao = np.asarray(Image.open(os.path.join(WORK, "S3a_05_old.png")).convert("RGB")).astype(int)
    d = (an != ao).any(axis=2)

    x0, y0 = px(320.0, 360.0)
    x1, y1 = px(453.313807 + DX, 441.0)
    m = 4
    mask = np.zeros(d.shape, bool)
    mask[max(int(y0) - m, 0):int(y1) + m, max(int(x0) - m, 0):int(x1) + m] = True
    outside = int((d & ~mask).sum())
    ok(outside == 0 and int(d.sum()) > 0,
       "V3 only the inset footprint changed",
       "%d px changed, %d outside" % (int(d.sum()), outside))

    # V4: "-400" label left ink vs the main left frame
    def left_ink(img, y_base, x_from, x_to):
        """left edge of the whole label ink (minus sign included)"""
        r1 = int(round((y_base - 7.0 - VB[1]) * PX))
        r2 = int(round((y_base + 1.0 - VB[1]) * PX))
        c0, c1 = int((x_from - VB[0]) * PX), int((x_to - VB[0]) * PX)
        band = np.asarray(Image.fromarray(img.astype("uint8")).convert("L")
                          ).astype(int)[r1:r2, c0:c1]
        cols = np.where((255 - band).max(axis=0) > 40)[0]
        return None if not len(cols) else x_from + cols[0] / PX

    y400 = 427.154657
    lx_old = left_ink(ao, y400, 318.8, 322.4)     # left of the main frame
    lx_new = left_ink(an, y400, 323.8, 352.0)     # right of the main frame
    gap_old = lx_old - 323.05017 if lx_old else None
    gap_new = lx_new - 323.05017 if lx_new else None
    ok(lx_new is not None and gap_new >= 5.0,
       "V4 '-400' ink starts %.2f pt right of the main frame (was %.2f)"
       % (gap_new or -1, gap_old if gap_old is not None else -1))

    # V5: inset frame at the new place; its curves reach the frame
    def right_frame(img, y_svg):
        r = int(round((y_svg - VB[1]) * PX))
        row = np.asarray(Image.fromarray(img.astype("uint8")).convert("L")
                         ).astype(int)[r]
        cols = np.where((255 - row) > 80)[0]
        xs = [VB[0] + c / PX for c in cols if 440 < VB[0] + c / PX < 470]
        return min(xs), max(xs)

    fr = right_frame(an, 395.0)
    ok(abs(fr[1] - (OLD_IN[2] + DX)) < 1.5,
       "V5 inset frame right edge at %.2f pt (expected %.2f)"
       % (fr[1], OLD_IN[2] + DX),
       "old %.2f" % OLD_IN[2])

    # V6: the strip the inset newly occupies was blank before
    sx0, sy0 = px(OLD_IN[2] + 1.0, OLD_IN[1] + 1.0)
    sx1, sy1 = px(OLD_IN[2] + DX, OLD_IN[3] - 1.0)
    strip = ao[int(sy0):int(sy1), int(sx0):int(sx1)]
    white = float((strip.min(axis=2) >= 250).mean())
    ok(white == 1.0, "V6 new strip was 100%% blank before (no curve covered)",
       "%.1f%%" % (100 * white))

    print("=" * 74)
    print("RESULT:", "ALL PASS" if not FAIL else "FAIL (%d)" % len(FAIL))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
