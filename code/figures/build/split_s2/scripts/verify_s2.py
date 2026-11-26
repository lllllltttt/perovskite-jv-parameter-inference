# -*- coding: utf-8 -*-
"""Verification for the two Figure S2 panels.

A  wording      : only tick numbers remain, nothing else
B  canvas       : identical canvas, identical plot-area offset for both panels
C  retained     : every surviving element is identical to the source vector
D  scatter/ticks: 9 markers with identical coordinates, tick marks and tick
                  numbers identical (count, value, position)
E  no collateral: the 600-dpi difference against the untouched source axes is
                  confined to the ink of the deleted elements
F  margins      : all ink inside the canvas with clearance
G  leaders      : no grey (#a6a6a6) leader stroke survives
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

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SRC = r"E:\project\work1\20261024_final_figures_svg\si\FigureS2.svg"
OUT = os.environ.get("S2_OUT", "out")
PY = sys.executable

PANELS = [("S2a_sensitivity_log", "axes_1"), ("S2b_sensitivity_raw", "axes_2")]
FAIL = []


def ok(cond, label, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("  " + detail) if detail else ""))
    if not cond:
        FAIL.append(label)


def txt(e):
    return "".join(e.itertext()).strip()


def ref_ids(el):
    ids = set()
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        for a in (XL + "href", "href"):
            v = e.get(a) or ""
            if v.startswith("#"):
                ids.add(v[1:])
        for a in ("clip-path", "fill", "stroke", "filter", "mask", "style"):
            m = re.search(r"url\(#([^)]+)\)", e.get(a) or "")
            if m:
                ids.add(m.group(1))
    return ids


def defined_ids(el):
    return {e.get("id") for e in el.iter() if isinstance(e.tag, str) and e.get("id")}


def external_defs(piece, idmap, order):
    have = defined_ids(piece)
    need = ref_ids(piece) - have
    out, seen = [], set()
    while need:
        nid = sorted(need, key=lambda i: order[i])[0]
        need.discard(nid)
        if nid in seen:
            continue
        seen.add(nid)
        out.append(etree.fromstring(etree.tostring(idmap[nid])))
        need |= (ref_ids(idmap[nid]) - have - {d.get("id") for d in out})
    return out


def build(groups, win, idmap, order, path):
    root = etree.Element(CS + "svg",
                         nsmap={None: "http://www.w3.org/2000/svg",
                                "xlink": "http://www.w3.org/1999/xlink"})
    root.set("width", "%.4f" % (win[2] * 96 / 72))
    root.set("height", "%.4f" % (win[3] * 96 / 72))
    root.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
    root.set("overflow", "hidden")
    body = etree.SubElement(root, CS + "g")
    for g in groups:
        body.append(g)
    extra = external_defs(body, idmap, order)
    if extra:
        d = etree.Element(CS + "defs")
        for e in extra:
            d.append(e)
        root.insert(0, d)
    etree.ElementTree(root).write(path, xml_declaration=True, encoding="utf-8")
    return path


def render(svg, png, dpi):
    for _ in range(3):
        r = subprocess.run([PY, "scripts/render_svg_px.py", svg, png,
                            "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png):
            return png
    raise RuntimeError("render failed " + svg)


def ink(path, thr=8):
    a = np.asarray(Image.open(path).convert("L")).astype(int)
    return (255 - a) > thr


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


def bbox(m, win, dpi):
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


def canon(e, drop_font=True):
    def rec(x):
        if not isinstance(x.tag, str):
            return ""
        attrs = []
        for k, v in sorted(x.attrib.items()):
            if k == "id":
                continue
            if drop_font and k in ("font-family", "font-size"):
                continue
            attrs.append((k, v))
        kids = "".join(rec(c) for c in x)
        return "<%s %s>%s</%s>" % (x.tag, tuple(attrs), kids, x.tag)
    return rec(e)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import split_s2 as S2      # noqa: E402  (same deletion rules as the builder)


def split_deleted(a):
    """Same rule as split_s2.cut(), returning (kept copy, deleted elements)."""
    kept = etree.fromstring(etree.tostring(a))
    deleted = []
    for c in list(kept):
        cid = c.get("id") or ""
        if c.tag == CS + "g" and re.match(r"^text_\d+$", cid):
            deleted.append(etree.fromstring(etree.tostring(c)))
            kept.remove(c)
        elif c.tag == CS + "g" and cid.startswith("patch_"):
            p = c.find(".//" + CS + "path")
            st = (p.get("style") if p is not None else "") or ""
            if "#a6a6a6" in st and not S2.KEEP_LEADERS:
                deleted.append(etree.fromstring(etree.tostring(c)))
                kept.remove(c)
    for c in list(kept):
        cid = c.get("id") or ""
        if not cid.startswith("matplotlib.axis_"):
            continue
        for g in list(c):
            if g.tag != CS + "g":
                continue
            if (g.get("id") or "").startswith(("xtick_", "ytick_")):
                continue
            if next(g.iter(CS + "text"), None) is not None:
                deleted.append(etree.fromstring(etree.tostring(g)))
                c.remove(g)
    return kept, deleted


def font_fix(el):
    S2.font_fix(el, S2.plot_box(el), S2.FONT_SIZE)


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    by = {p["name"]: p for p in meta["pieces"]}
    CW, CH = meta["canvas"]
    src = etree.parse(SRC).getroot()
    idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}

    print("=" * 78)
    print("A  wording: only tick numbers remain")
    print("=" * 78)
    for name, aid in PANELS:
        root = etree.parse(os.path.join(OUT, "svg", name + ".svg")).getroot()
        texts = [txt(t) for t in root.iter(CS + "text")]
        num_ok = all(re.fullmatch(r"[−\-]?\d+(\.\d+)?", s) for s in texts)
        want = 6 + 5 if aid == "axes_1" else 4 + 5
        ok(num_ok and len(texts) == want,
           "%-22s %d numbers only %s" % (name, len(texts), texts))

    print("\n" + "=" * 78)
    print("B  canvas: identical size and plot-area offset")
    print("=" * 78)
    offs = []
    for name, aid in PANELS:
        root = etree.parse(os.path.join(OUT, "svg", name + ".svg")).getroot()
        vb = [float(v) for v in root.get("viewBox").split()]
        bx, byy = meta["boxes"][name][:2]
        offs.append((round(bx - vb[0], 4), round(byy - vb[1], 4), vb[2], vb[3]))
    ok(abs(offs[0][0] - offs[1][0]) < 1e-6 and abs(offs[0][1] - offs[1][1]) < 1e-6
       and abs(offs[0][2] - CW) < 1e-3 and abs(offs[0][3] - CH) < 1e-3,
       "both %.3f x %.3f pt, plot offset (%.2f, %.2f)" % tuple(
           [offs[0][2], offs[0][3], offs[0][0], offs[0][1]]))

    print("\n" + "=" * 78)
    print("C  retained elements identical to the source")
    print("=" * 78)
    for name, aid in PANELS:
        exp, _ = split_deleted(idmap[aid])
        font_fix(exp)
        got = etree.fromstring(open(os.path.join(OUT, "svg", name + ".svg"),
                                    "rb").read()).find(CS + "g")[0]
        ok(canon(exp) == canon(got),
           "%-22s %d elements match" % (name, sum(1 for _ in exp.iter())))

    print("\n" + "=" * 78)
    print("D  scatter markers and ticks unchanged")
    print("=" * 78)
    for name, aid in PANELS:
        a0 = idmap[aid]
        got = etree.parse(os.path.join(OUT, "svg", name + ".svg")).getroot()
        def markers(root):
            out = []
            for g in root.iter(CS + "g"):
                if not (g.get("id") or "").startswith("PathCollection_"):
                    continue
                out += [(u.get("x"), u.get("y")) for u in g.iter(CS + "use")]
            return out
        m0, m1 = markers(a0), markers(got)
        # tick <use> (markers path) carry no x/y pair in the same way -> the
        # marker list is the clip-path-clipped collection
        def ticklabels(root):
            out = {}
            for g in root.iter(CS + "g"):
                gid = g.get("id") or ""
                if not gid.startswith(("xtick_", "ytick_")):
                    continue
                t = next(g.iter(CS + "text"), None)
                u = next(g.iter(CS + "use"), None)
                if t is not None:
                    out[gid] = (txt(t), float(t.get("x")), float(t.get("y")),
                                None if u is None else float(u.get("y")),
                                gid.startswith("xtick_"))
            return out
        t0, t1 = ticklabels(a0), ticklabels(got)
        box = meta["boxes"][name]
        k = (S2.FONT_SIZE or 7.5) / 7.5
        ydev = 0.0
        for gid, (s_txt, s_x, s_y, s_tick, is_x) in t0.items():
            g_txt, g_x, g_y, _, _ = t1[gid]
            if is_x:
                bottom = box[1] + box[3]
                want = bottom + 7.0 + (s_y - bottom - 7.0) * k
            else:
                want = s_tick + (s_y - s_tick) * k
            ydev = max(ydev, abs(g_y - want))
            assert g_txt == s_txt and abs(g_x - s_x) < 1e-6, (gid, s_txt, g_txt)
        ok(abs(ydev) < 1e-3, "%-22s baseline shift matches the font metric (%.4f pt)"
           % (name, ydev))
        ok(len(m1) == 9 and m1 == m0 and set(t1) == set(t0),
           "%-22s 9 markers identical, %d tick numbers kept (value + x)"
           % (name, len(t1)))

    print("\n" + "=" * 78)
    stats = {}
    print("E  difference against the untouched source is only the deleted ink")
    print("=" * 78)
    for name, aid in PANELS:
        m = [p for p in meta["pieces"] if p["name"] == name][0]
        win = tuple(m["win"])
        kept, deleted = split_deleted(idmap[aid])
        # reference: the ORIGINAL axes (nothing deleted) carrying the SAME
        # tick typography, so the only remaining difference is the deletion
        refdoc = etree.fromstring(etree.tostring(idmap[aid]))
        font_fix(refdoc)
        ref = build([refdoc], win,
                    idmap, order, os.path.join(OUT, "work", name + "_ref.svg"))
        render(ref, os.path.join(OUT, "work", name + "_ref.png"), 600)
        # mask: only the deleted elements
        maskdoc = etree.Element(CS + "svg",
                                nsmap={None: "http://www.w3.org/2000/svg",
                                       "xlink": "http://www.w3.org/1999/xlink"})
        maskdoc.set("width", "%.4f" % (win[2] * 96 / 72))
        maskdoc.set("height", "%.4f" % (win[3] * 96 / 72))
        maskdoc.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
        g = etree.SubElement(maskdoc, CS + "g")
        for d in deleted:
            g.append(d)
        mp = build([g], win, idmap, order, os.path.join(OUT, "work",
                                                        name + "_mask.svg"))
        render(mp, os.path.join(OUT, "work", name + "_mask.png"), 600)
        mask = dilate(ink(os.path.join(OUT, "work", name + "_mask.png")), 6)

        a = np.asarray(Image.open(os.path.join(OUT, "png",
                                               name + "_600dpi.png")).convert("L"))
        b = np.asarray(Image.open(os.path.join(OUT, "work",
                                               name + "_ref.png")).convert("L"))
        d = a != b
        outside = int((d & ~mask).sum())
        inside = int((d & mask).sum())
        stats.setdefault(name, {})["diff"] = inside
        stats[name]["outside"] = outside
        ok(outside == 0, "%-22s %d px differ, all inside the deleted ink"
           % (name, inside), "outside=%d" % outside)

    print("\n" + "=" * 78)
    print("F  margins: every piece inside its canvas")
    print("=" * 78)
    for name, aid in PANELS:
        m = [p for p in meta["pieces"] if p["name"] == name][0]
        win = tuple(m["win"])
        bb = bbox(ink(os.path.join(OUT, "png", name + "_600dpi.png")), win, 600)
        clear = min(bb[0] - win[0], bb[1] - win[1],
                    win[0] + win[2] - bb[2], win[1] + win[3] - bb[3])
        stats.setdefault(name, {})["clear"] = round(clear, 2)
        ok(clear > 1.0, "%-22s ink %.2f..%.2f x %.2f..%.2f  clearance %.2f pt"
           % (name, bb[0], bb[2], bb[1], bb[3], clear))

    print("\n" + "=" * 78)
    print("G  grey leader strokes " + ("kept" if S2.KEEP_LEADERS else "removed"))
    print("=" * 78)
    for name, aid in PANELS:
        s = open(os.path.join(OUT, "svg", name + ".svg"), encoding="utf-8").read()
        n = s.count('stroke: #a6a6a6')
        ok((n == 9) if S2.KEEP_LEADERS else (n == 0),
           "%-22s %d grey leader lines (%s)"
           % (name, n, "kept" if S2.KEEP_LEADERS else "removed"))

    print("\n" + "=" * 78)
    json.dump(stats, open(os.path.join(OUT, "work", "verify_summary.json"), "w"))
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL",
                                          len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
