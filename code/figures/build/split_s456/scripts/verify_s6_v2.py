# -*- coding: utf-8 -*-
"""Verify the re-issued S6 panels.

Layout rule (shared axes, as in the source but completed):
  left column  -> y numbers only (0.0 / 0.5 / 1.0)
  bottom row   -> x numbers only (0.0 / 0.5 / 1.0)
  bottom-left  -> both
  all other panels -> tick marks but no numbers
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
WANT = {1: (False, True), 2: (False, False), 3: (False, False),
        4: (False, True), 5: (False, False), 6: (False, False),
        7: (True, True), 8: (True, False), 9: (True, False)}


def ok(c, l, d=""):
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("  " + d) if d else ""))
    if not c:
        FAIL.append(l)


def labels(root):
    xs, ys = [], []
    for g in root.iter(CS + "g"):
        gid = g.get("id") or ""
        if not gid.startswith(("xtick_", "ytick_")):
            continue
        t = next(g.iter(CS + "text"), None)
        s = "" if t is None else (t.text or "").strip()
        (xs if gid.startswith("xtick_") else ys).append(s)
    return [v for v in xs if v], [v for v in ys if v]


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"),
                          encoding="utf-8"))["S6"]
    src = etree.parse(os.path.join(S.BASE, meta["source"])).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    CW, CH = meta["canvas"]

    print("=" * 74)
    print("A  labels follow the shared-axis rule, each set complete")
    print("=" * 74)
    for k, p in enumerate(meta["pieces"], start=1):
        xs, ys = labels(etree.parse(p["svg"]).getroot())
        wx, wy = WANT[k]
        ok((sorted(xs) == ["0.0", "0.5", "1.0"]) if wx else (xs == []),
           "%-6s x = %-16s %s" % (p["name"], " ".join(xs) if xs else "—",
                                  "want 0.0/0.5/1.0" if wx else "want none"))
        ok((sorted(ys) == ["0.0", "0.5", "1.0"]) if wy else (ys == []),
           "%-6s y = %-16s %s" % (p["name"], " ".join(ys) if ys else "—",
                                  "want 0.0/0.5/1.0" if wy else "want none"))

    print("\n" + "=" * 74)
    print("B  identical canvas across the nine")
    print("=" * 74)
    offs = []
    for p in meta["pieces"]:
        vb = [float(v) for v in etree.parse(p["svg"]).getroot()
              .get("viewBox").split()]
        ax = idmap[p["axes"]]
        cl = [i for i in S.ref_ids(ax) if i in idmap and idmap[i].tag == CS + "clipPath"]
        rect = idmap[cl[0]].find(CS + "rect")
        bx = [float(rect.get(k)) for k in ("x", "y", "width", "height")]
        offs.append((round(bx[0] - vb[0], 4), round(bx[1] - vb[1], 4),
                     vb[2], vb[3], bx[2], bx[3]))
    dev = max(max(abs(a[i] - b[i]) for i in range(6)) for a in offs for b in offs)
    ok(dev < 0.005 and abs(offs[0][2] - CW) < 1e-3 and abs(offs[0][3] - CH) < 1e-3,
       "canvas %.3f x %.3f, plot %.3f x %.3f, max dev %.4f"
       % (offs[0][2], offs[0][3], offs[0][4], offs[0][5], dev))

    print("\n" + "=" * 74)
    print("C  where a label exists it sits at the original offset")
    print("=" * 74)
    for p in meta["pieces"]:
        off = []
        for g in etree.parse(p["svg"]).getroot().iter(CS + "g"):
            gid = g.get("id") or ""
            if not gid.startswith(("xtick_", "ytick_")):
                continue
            u = next(g.iter(CS + "use"), None)
            t = next(g.iter(CS + "text"), None)
            if u is None or t is None:
                continue
            off.append((gid.split("_")[0], round(float(t.get("x")) - float(u.get("x")), 3),
                        round(float(t.get("y")) - float(u.get("y")), 3)))
        dx = {o[1] for o in off if o[0] == "xtick"}
        dy = {o[2] for o in off if o[0] == "xtick"}
        ex = {o[1] for o in off if o[0] == "ytick"}
        ey = {o[2] for o in off if o[0] == "ytick"}
        good = (dx in ({0.0}, {-0.0}, set())) and len(dy) <= 1 and \
               (ex in ({-6.5}, set())) and len(ey) <= 1
        ok(good, "%-6s x offset %s/%s, y offset %s/%s"
           % (p["name"], dx, dy, ex, ey))

    print("\n" + "=" * 74)
    print("D  pixel check vs the source (only text ink may differ)")
    print("=" * 74)
    for p in meta["pieces"]:
        win = tuple(p["win"])
        ref = etree.fromstring(etree.tostring(src.find(".//" + CS + "g[@id='figure_1']")))
        a10 = ref.find(".//" + CS + "g[@id='axes_10']")
        if a10 is not None:
            a10.getparent().remove(a10)
        S.cut(ref)
        rp = S.build([ref], win, idmap, order,
                     os.path.join(OUT, "work", p["name"] + "_ref2.svg"))
        S.render(rp, os.path.join(OUT, "work", p["name"] + "_ref2.png"), 600)
        md = etree.Element(CS + "svg", nsmap={None: "http://www.w3.org/2000/svg",
                                              "xlink": "http://www.w3.org/1999/xlink"})
        md.set("width", "%.4f" % (win[2] * 96 / 72))
        md.set("height", "%.4f" % (win[3] * 96 / 72))
        md.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
        g = etree.SubElement(md, CS + "g")
        for root in (ref, etree.parse(p["svg"]).getroot()):
            for e in root.iter(CS + "g"):
                gid = e.get("id") or ""
                if gid.startswith(("xtick_", "ytick_")) or \
                   re.match(r"^text_\d+$", gid) or gid.startswith("uniform_"):
                    g.append(etree.fromstring(etree.tostring(e)))
        mp = S.build([g], win, idmap, order,
                     os.path.join(OUT, "work", p["name"] + "_mask2.svg"))
        S.render(mp, os.path.join(OUT, "work", p["name"] + "_mask2.png"), 600)
        mask = ((255 - np.asarray(Image.open(os.path.join(
            OUT, "work", p["name"] + "_mask2.png")).convert("L")).astype(int)) > 8)
        for _ in range(6):
            d = mask.copy()
            d[1:, :] |= mask[:-1, :]
            d[:-1, :] |= mask[1:, :]
            d[:, 1:] |= mask[:, :-1]
            d[:, :-1] |= mask[:, 1:]
            mask = d
        A = np.asarray(Image.open(p["png"]).convert("L")).astype(int)
        B = np.asarray(Image.open(os.path.join(OUT, "work", p["name"] +
                                               "_ref2.png")).convert("L")).astype(int)
        diff = np.abs(A - B) > 40
        ok(int((diff & ~mask).sum()) == 0,
           "%-6s %d px differ, all inside text ink" % (p["name"], int((diff & mask).sum())),
           "outside=%d" % int((diff & ~mask).sum()))

    print("\n" + "=" * 74)
    print("E  margins")
    print("=" * 74)
    for p in meta["pieces"]:
        im = np.asarray(Image.open(p["png"]).convert("L")).astype(int)
        mk = (255 - im) > 8
        rows = np.where(mk.any(axis=1))[0]
        cols = np.where(mk.any(axis=0))[0]
        clear = min(cols[0], rows[0], im.shape[1] - 1 - cols[-1],
                    im.shape[0] - 1 - rows[-1]) / (600 / 72)
        ok(clear > 1.0, "%-6s clearance %.2f pt" % (p["name"], clear))

    print("\nRESULT: %s (%d failures)" % ("ALL PASS" if not FAIL else "FAIL", len(FAIL)))
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


main()
