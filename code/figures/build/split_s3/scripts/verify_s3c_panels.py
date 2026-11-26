# -*- coding: utf-8 -*-
"""Verification for S3c_01 ... S3c_04.

A  one panel per file : exactly one axes subtree (+ the defs it needs)
B  identical canvas  : same canvas size and same plot-area offset in all four
C  identical content : the axes subtree is element-equal to the one in S3c.svg
D  ticks             : same tick groups, same tick numbers, same positions
E  no collateral     : 600-dpi render is pixel-identical to the same window
                       cut out of the finished S3c.svg
F  margins           : all ink inside the canvas
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
import split_s3c_panels as S      # noqa: E402

CS = "{http://www.w3.org/2000/svg}"
OUT = "out_c_panels"
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def txt(e):
    return re.sub(r"\s+", " ", "".join(e.itertext()).replace("\xa0", " ")).strip()


def canon(e):
    def rec(x):
        if not isinstance(x.tag, str):
            return ""
        attrs = tuple(sorted((k, v) for k, v in x.attrib.items() if k != "id"))
        return "<%s %s>%s</%s>" % (x.tag, attrs, "".join(rec(c) for c in x), x.tag)
    return rec(e)


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    src = etree.parse(S.SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    CW, CH = meta["canvas"]

    print("=" * 78)
    print("A  one panel per file, nothing else")
    print("=" * 78)
    for m in meta["pieces"]:
        root = etree.parse(m["svg"]).getroot()
        axes = [g.get("id") for g in root.iter(CS + "g")
                if (g.get("id") or "").startswith("axes_")]
        texts = [txt(t) for t in root.iter(CS + "text")]
        ok(axes == [m["axes"]],
           "%-8s axes=%s, %d tick numbers" % (m["file"], axes, len(texts)))

    print("\n" + "=" * 78)
    print("B  identical canvas and identical plot-area offset")
    print("=" * 78)
    offs = []
    for m in meta["pieces"]:
        root = etree.parse(m["svg"]).getroot()
        vb = [float(v) for v in root.get("viewBox").split()]
        x, y, w, h = S.plot_box(etree.fromstring(etree.tostring(idmap[m["axes"]])))
        offs.append((round(x - vb[0], 4), round(y - vb[1], 4), vb[2], vb[3], w, h))
    dev = max(max(abs(a[i] - offs[0][i]) for i in range(6)) for a in offs)
    ok(dev < 0.005 and abs(offs[0][2] - CW) < 1e-3 and abs(offs[0][3] - CH) < 1e-3,
       "all four: canvas %.3f x %.3f pt, plot %.3f x %.3f at (%.2f, %.2f), dev %.4f"
       % (offs[0][2], offs[0][3], offs[0][4], offs[0][5], offs[0][0], offs[0][1], dev))

    print("\n" + "=" * 78)
    print("C  axes subtree identical to the one in S3c.svg")
    print("=" * 78)
    for m in meta["pieces"]:
        exp = idmap[m["axes"]]
        got = etree.parse(m["svg"]).getroot().find(CS + "g")[0]
        ok(canon(exp) == canon(got),
           "%-8s %d elements identical" % (m["file"], sum(1 for _ in exp.iter())))

    print("\n" + "=" * 78)
    print("D  tick groups and tick numbers preserved")
    print("=" * 78)
    for m in meta["pieces"]:
        def ticks(root):
            out = {}
            for g in root.iter(CS + "g"):
                gid = g.get("id") or ""
                if not gid.startswith(("xtick_", "ytick_")):
                    continue
                u = next(g.iter(CS + "use"), None)
                t = next(g.iter(CS + "text"), None)
                out[gid] = (None if u is None else (u.get("x"), u.get("y")),
                            None if t is None else txt(t))
            return out
        t0 = ticks(idmap[m["axes"]])
        t1 = ticks(etree.parse(m["svg"]).getroot())
        ok(t0 == t1, "%-8s %d tick groups, %d with numbers"
           % (m["file"], len(t1), sum(1 for v in t1.values() if v[1])))

    print("\n" + "=" * 78)
    print("E  pixel-identical to the same window of the finished S3c.svg")
    print("=" * 78)
    for m in meta["pieces"]:
        win = tuple(m["win"])
        ref = etree.fromstring(etree.tostring(src.find(CS + "g")))
        rp = S.build([ref], win, idmap, order,
                     os.path.join(OUT, "work", m["file"] + "_ref.svg"))
        S.render(rp, os.path.join(OUT, "work", m["file"] + "_ref.png"), 600)
        a = np.asarray(Image.open(m["png"]).convert("L")).astype(int)
        b = np.asarray(Image.open(os.path.join(OUT, "work",
                                               m["file"] + "_ref.png")).convert("L")).astype(int)
        d = int((a != b).sum()) if a.shape == b.shape else -1
        ok(d == 0, "%-8s %d differing pixels" % (m["file"], d))

    print("\n" + "=" * 78)
    print("F  margins: ink inside the canvas")
    print("=" * 78)
    for m in meta["pieces"]:
        im = np.asarray(Image.open(m["png"]).convert("L")).astype(int)
        mk = (255 - im) > 8
        rows = np.where(mk.any(axis=1))[0]
        cols = np.where(mk.any(axis=0))[0]
        clear = min(cols[0], rows[0], im.shape[1] - 1 - cols[-1],
                    im.shape[0] - 1 - rows[-1]) / (600 / 72.0)
        ok(clear > 1.0, "%-8s clearance %.2f pt" % (m["file"], clear))

    print("\n" + "=" * 78)
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL",
                                          len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
