# -*- coding: utf-8 -*-
"""Re-issue S6_01 ... S6_09 with a complete, uniform tick-label set.

Figure S6 was drawn with shared axes: only the outer panels carry tick
numbers, so the left column showed 0.5/1.0 on one panel, 0.5 on another and
0.0/0.5 on the third, and the bottom row only 0.0/0.5 or 0.5/1.0.  Every panel
keeps three x ticks and three y ticks at 0.0 / 0.5 / 1.0, so the labels are
simply completed here - positions come from the existing tick marks, offsets
from an existing labelled tick, so nothing moves.

Everything else - data, spines, tick marks, axis ranges, colours, the identity
line - is untouched; the nine panels keep the same canvas as before.
"""
import io
import json
import os
import re
import sys

from lxml import etree
import numpy as np
from PIL import Image

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import split_s456 as S      # noqa: E402

CS = "{http://www.w3.org/2000/svg}"
OUT = "out"
FIG = "FigureS6.svg"
LABELS = ["0.0", "0.5", "1.0"]
STYLE = ("font-size: 7.5px; font-family: 'Arial', 'DejaVu Sans', sans-serif; "
         "text-anchor: %s; fill: #1a1a1a")


def tick_groups(ax, kind):
    """tick groups of one kind, ordered bottom/left first."""
    out = []
    for c in ax:
        if not (c.get("id") or "").startswith("matplotlib.axis_"):
            continue
        for g in c:
            if not (g.get("id") or "").startswith(kind + "tick_"):
                continue
            u = next(g.iter(CS + "use"), None)
            if u is None:
                continue
            out.append((g, float(u.get("x")), float(u.get("y"))))
    return out


def unify(ax, want_x, want_y):
    """Complete the tick labels on the axes that carry them.

    The figure uses shared axes: x numbers only on the bottom row, y numbers
    only on the left column (the bottom-left panel therefore has both).  Every
    labelled axis must show all three ticks 0.0 / 0.5 / 1.0.
    """
    added = 0
    # x ticks: left to right
    xs = sorted(tick_groups(ax, "x"), key=lambda t: t[1])
    assert len(xs) == 3, (ax.get("id"), len(xs))
    for i, (g, tx, ty) in enumerate(xs):
        lab = LABELS[i]
        t = next(g.iter(CS + "text"), None)
        if not want_x:
            if t is not None:
                t.getparent().getparent().remove(t.getparent())
            continue
        if t is None:
            grp = etree.SubElement(g, CS + "g")
            grp.set("id", "uniform_x_%s_%d" % (ax.get("id"), i))
            t = etree.SubElement(grp, CS + "text")
            added += 1
        t.set("style", STYLE % "middle")
        t.set("x", "%.4f" % tx)
        t.set("y", "%.4f" % (ty + 11.868359))
        t.set("transform", "rotate(-0 %.4f %.4f)" % (tx, ty + 11.868359))
        t.text = lab
    # y ticks: bottom to top
    ys = sorted(tick_groups(ax, "y"), key=lambda t: -t[2])
    assert len(ys) == 3, (ax.get("id"), len(ys))
    for i, (g, tx, ty) in enumerate(ys):
        lab = LABELS[i]
        t = next(g.iter(CS + "text"), None)
        if not want_y:
            if t is not None:
                t.getparent().getparent().remove(t.getparent())
            continue
        if t is None:
            grp = etree.SubElement(g, CS + "g")
            grp.set("id", "uniform_y_%s_%d" % (ax.get("id"), i))
            t = etree.SubElement(grp, CS + "text")
            added += 1
        t.set("style", STYLE % "end")
        t.set("x", "%.4f" % (tx - 6.5))
        t.set("y", "%.4f" % (ty + 2.684179))
        t.set("transform", "rotate(-0 %.4f %.4f)" % (tx - 6.5, ty + 2.684179))
        t.text = lab
    return added


def main():
    src = etree.parse(os.path.join(S.BASE, FIG)).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    fig = etree.fromstring(etree.tostring(src.find(".//" + CS + "g[@id='figure_1']")))
    a10 = fig.find(".//" + CS + "g[@id='axes_10']")
    if a10 is not None:
        a10.getparent().remove(a10)
    S.cut(fig)

    panels = []
    for a in [g for g in fig.iter(CS + "g")
              if re.match(r"^axes_\d+$", g.get("id") or "")]:
        cl = [i for i in S.ref_ids(a) if i in idmap and idmap[i].tag == CS + "clipPath"]
        rect = idmap[cl[0]].find(CS + "rect")
        box = tuple(float(rect.get(k)) for k in ("x", "y", "width", "height"))
        panels.append((a, box))
    panels.sort(key=lambda p: (round(p[1][1], 1), round(p[1][0], 1)))
    assert len(panels) == 9

    n_added = 0
    for i, (a, _b) in enumerate(panels):
        row, col = divmod(i, 3)
        n_added += unify(a, want_x=(row == 2), want_y=(col == 0))
    print("  panels labelled: x on the bottom row, y on the left column; %d labels added"
          % n_added)

    # same margins as the delivered set: recompute, they must not have grown
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    m = meta["S6"]
    L, T, R, B = (m["margins"]["L"], m["margins"]["T"],
                  m["margins"]["R"], m["margins"]["B"])
    W0, H0 = m["plot"]
    PAD = m["margins"]["pad"]

    # re-measure the ink so a wider label can never be clipped
    geo = []
    for a, (x, y, w, h) in panels:
        win = (x - 60, y - 60, w + 120, h + 120)
        p = S.build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                    os.path.join(OUT, "work", "s6b_%s.svg" % a.get("id")))
        S.render(p, os.path.join(OUT, "work", "s6b_%s.png" % a.get("id")), 300)
        ib = S.ink_bbox(os.path.join(OUT, "work", "s6b_%s.png" % a.get("id")), win, 300)
        geo.append((x - ib[0], y - ib[1], ib[2] - (x + w), ib[3] - (y + h)))
    L2 = max(g[0] for g in geo); T2 = max(g[1] for g in geo)
    R2 = max(g[2] for g in geo); B2 = max(g[3] for g in geo)
    print("  margins now L%.2f T%.2f R%.2f B%.2f (was L%.2f T%.2f R%.2f B%.2f)"
          % (L2, T2, R2, B2, L, T, R, B))
    L, T, R, B = max(L, L2), max(T, T2), max(R, R2), max(B, B2)
    CW, CH = W0 + L + R + 2 * PAD, H0 + T + B + 2 * PAD
    print("  canvas %.3f x %.3f pt" % (CW, CH))

    for i, (a, (x, y, w, h)) in enumerate(panels, start=1):
        name = "S6_%02d" % i
        win = (round(x - L - PAD, 4), round(y - T - PAD, 4),
               round(CW, 4), round(CH, 4))
        svg = S.build([etree.fromstring(etree.tostring(a))], win, idmap, order,
                      os.path.join(OUT, "svg", name + ".svg"))
        png = os.path.join(OUT, "png", name + "_600dpi.png")
        S.render(svg, png, 600)
        for p in meta["S6"]["pieces"]:
            if p["name"] == name:
                p.update(svg=svg, png=png, win=win,
                         px=list(Image.open(png).size))
        print("    %-6s %8.3f x %8.3f pt  %dx%d px"
              % (name, win[2], win[3], *Image.open(png).size))

    # rebuild the 3x3 preview
    s = 600 / 72.0
    GUT = 10.0
    Wc, Hc = 3 * CW + 4 * GUT, 3 * CH + 4 * GUT
    canvas = Image.new("RGB", (int(round(Wc * s)), int(round(Hc * s))), "white")
    for i, p in enumerate(meta["S6"]["pieces"]):
        r, c = divmod(i, 3)
        canvas.paste(Image.open(p["png"]).convert("RGB"),
                     (int(round((GUT + c * (CW + GUT)) * s)),
                      int(round((GUT + r * (CH + GUT)) * s))))
    canvas.save(meta["S6"]["preview"])
    print("    preview %s" % meta["S6"]["preview"])

    meta["S6"]["canvas"] = [round(CW, 4), round(CH, 4)]
    meta["S6"]["margins"] = dict(L=L, T=T, R=R, B=B, pad=PAD)
    meta["S6"]["tick_unified"] = True
    json.dump(meta, open(os.path.join(OUT, "work", "meta.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
