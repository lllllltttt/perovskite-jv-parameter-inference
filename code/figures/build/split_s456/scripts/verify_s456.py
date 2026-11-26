# -*- coding: utf-8 -*-
"""Verification for the 27 panels of Figure S4 / S5 / S6.

A  wording    : no non-tick text group survives (titles, axis titles, notes,
                figure title all gone); only tick labels remain
B  canvas     : within one figure all nine panels share canvas and plot offset
C  content    : each axes subtree is element-equal to the source subtree
D  ticks      : identical tick groups, identical tick labels and positions
E  pixel      : each piece renders pixel-identically to the same window cut
                out of the source figure (so no data, no clip, no spine moved)
F  margins    : all ink inside the canvas
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
import split_s456 as S      # noqa: E402

CS = "{http://www.w3.org/2000/svg}"
OUT = "out"
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def cut_axes(a):
    """Same deletions the builder applies, on a copy of one axes subtree."""
    a = etree.fromstring(etree.tostring(a))
    for c in list(a):
        if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
            a.remove(c)
    for c in list(a):
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag == CS + "g" and re.match(r"^text_\d+$", g.get("id") or ""):
                c.remove(g)
    return a


def canon(e):
    def rec(x):
        if not isinstance(x.tag, str):
            return ""
        attrs = tuple(sorted((k, v) for k, v in x.attrib.items() if k != "id"))
        return "<%s %s>%s</%s>" % (x.tag, attrs, "".join(rec(c) for c in x), x.tag)
    return rec(e)


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))

    for tag in ("S4", "S5", "S6"):
        m = meta[tag]
        src = etree.parse(os.path.join(S.BASE, m["source"])).getroot()
        idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
        order = {i: k for k, i in enumerate(idmap)}

        print("=" * 78)
        print("%s  (plot %.3f x %.3f pt, canvas %.3f x %.3f)" % (
            tag, m["plot"][0], m["plot"][1], m["canvas"][0], m["canvas"][1]))
        print("=" * 78)

        # A + C + D
        for p in m["pieces"]:
            root = etree.parse(p["svg"]).getroot()
            body = root.find(CS + "g")[0]

            stray = []
            for g in body.iter(CS + "g"):
                gid = g.get("id") or ""
                if not re.match(r"^text_\d+$", gid):
                    continue
                chain, q = [], g.getparent()
                while q is not None:
                    chain.append(q.get("id") or "")
                    q = q.getparent()
                if not any(c.startswith(("xtick_", "ytick_")) for c in chain):
                    stray.append(gid)
            ok(not stray, "%-6s no non-tick text left%s"
               % (p["name"], "" if not stray else " " + str(stray[:4])))

            exp = cut_axes(idmap[p["axes"]])
            ok(canon(exp) == canon(body), "%-6s %d elements identical to the source"
               % (p["name"], sum(1 for _ in exp.iter())))

        # B: canvas + offset identical across the nine
        offs = []
        for p in m["pieces"]:
            vb = [float(v) for v in etree.parse(p["svg"]).getroot()
                  .get("viewBox").split()]
            ax = idmap[p["axes"]]
            cl = [i for i in S.ref_ids(ax) if i in idmap and
                  idmap[i].tag == CS + "clipPath"]
            rect = idmap[cl[0]].find(CS + "rect")
            bx = [float(rect.get(k)) for k in ("x", "y", "width", "height")]
            offs.append((round(bx[0] - vb[0], 4), round(bx[1] - vb[1], 4),
                         vb[2], vb[3], bx[2], bx[3]))
        dev = max(max(abs(a[i] - b[i]) for i in range(6)) for a in offs for b in offs)
        ok(dev < 0.005, "%s canvas %.3f x %.3f, plot %.3f x %.3f, max dev %.4f"
           % ("all nine:", offs[0][2], offs[0][3], offs[0][4], offs[0][5], dev))

        # E: pixel identity against the source in the same window
        for p in m["pieces"]:
            win = tuple(p["win"])
            ref = etree.fromstring(etree.tostring(src.find(".//" + CS +
                                                          "g[@id='figure_1']")))
            if tag == "S6":
                a10 = ref.find(".//" + CS + "g[@id='axes_10']")
                if a10 is not None:
                    a10.getparent().remove(a10)
            S.cut(ref)
            rp = S.build([ref], win, idmap, order,
                         os.path.join(OUT, "work", p["name"] + "_ref.svg"))
            S.render(rp, os.path.join(OUT, "work", p["name"] + "_ref.png"), 600)
            a = np.asarray(Image.open(p["png"]).convert("L")).astype(int)
            b = np.asarray(Image.open(os.path.join(OUT, "work", p["name"] +
                                                   "_ref.png")).convert("L")).astype(int)
            d = int((a != b).sum()) if a.shape == b.shape else -1
            ok(d == 0, "%-6s %d differing pixels vs the source window"
               % (p["name"], d))

        # F: margins
        for p in m["pieces"]:
            im = np.asarray(Image.open(p["png"]).convert("L")).astype(int)
            mk = (255 - im) > 8
            rows = np.where(mk.any(axis=1))[0]
            cols = np.where(mk.any(axis=0))[0]
            clear = min(cols[0], rows[0], im.shape[1] - 1 - cols[-1],
                        im.shape[0] - 1 - rows[-1]) / (600 / 72.0)
            ok(clear > 1.0, "%-6s clearance %.2f pt" % (p["name"], clear))

    print("\n" + "=" * 78)
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL",
                                          len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
