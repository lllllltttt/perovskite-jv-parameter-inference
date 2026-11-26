# -*- coding: utf-8 -*-
"""Verification for out_ticks/ (tick marks and tick numbers kept)."""
import io
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image
from lxml import etree

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SRC = "work/slide1_image2.svg"
META = json.load(open("out_ticks/work/ticks_meta.json", encoding="utf-8"))
PY = sys.executable
S = 600 / 72.0
FAIL = []


def ref_ids(el):
    ids = set()
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        for a in (XL + "href", "href"):
            v = e.get(a) or ""
            if v.startswith("#"):
                ids.add(v[1:])
        for a in ("clip-path", "fill", "stroke", "filter", "mask"):
            m = __import__("re").search(r"url\(#([^)]+)\)", e.get(a) or "")
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
        el = idmap[nid]
        out.append(etree.fromstring(etree.tostring(el)))
        need |= (ref_ids(el) - have - {d.get("id") for d in out})
    return out


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        FAIL.append(msg)


def byid(root, gid):
    for e in root.iter():
        if isinstance(e.tag, str) and e.get("id") == gid:
            return e
    raise KeyError(gid)


def canon(e, drop_font=True):
    a = dict(e.attrib)
    if drop_font:
        a.pop("font-family", None)
        a.pop("font-size", None)
    kids = [canon(c, drop_font) for c in e if isinstance(c.tag, str)]
    return (e.tag, tuple(sorted(a.items())), (e.text or "").strip(), tuple(kids))


def render(svg, png, dpi):
    subprocess.run([PY, "scripts/render_svg_px.py", svg, png, "--dpi", str(dpi)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png


src = etree.parse(SRC).getroot()
removed = META["removed"]
ORDER = ["axes_%d" % (i + 1) for i in range(0, 9)]
for k, p in enumerate([p for p in META["pieces"] if not p["name"].startswith("S1b")]):
    p["axes"] = [ORDER[k]]
for p in META["pieces"]:
    if p["name"].startswith("S1b"):
        p["axes"] = ["axes_10", "axes_11"]
banned = ["Count", "Spearman", "Retained parameter", "Pairwise", "102,046",
          "log", "(a)", "(b)"]

print("== A  every piece: wording ==")
for p in META["pieces"]:
    name = p["name"]
    raw = open(p["svg"], encoding="utf-8").read()
    root = etree.parse(p["svg"]).getroot()
    texts = ["".join(t.itertext()).strip() for t in root.iter(CS + "text")]
    hits = [b for b in banned if b in raw]
    gone = [t for _, t in removed[name]]
    left = [t for t in gone if t and t in raw]
    n_use = sum(1 for _ in root.iter(CS + "use"))
    print("  %-18s texts=%-3d use=%-2d banned=%s leaked=%s"
          % (name, len(texts), n_use, hits or "-", left or "-"))
    check(not hits and not left, "%s: all explanatory wording gone" % name)
    if name.startswith("S1b"):
        check(len(texts) == 81 + 5, "%s: 81 in-cell numbers + 5 colour-bar numbers" % name)

print("\n== B  retained subtree identical to the source (minus deleted ids) ==")
for p in META["pieces"]:
    name = p["name"]
    root = etree.parse(p["svg"]).getroot()
    body = [g for g in root if g.tag == CS + "g"][0]
    got = [canon(g) for g in body]
    ids = {i for i, _ in removed[name]}
    want = []
    for srcid in p["axes"]:
        s = etree.fromstring(etree.tostring(byid(src, srcid)))
        for i in ids:
            try:
                e = byid(s, i)
            except KeyError:
                continue
            if e.getparent() is not None:
                e.getparent().remove(e)
        want.append(canon(s))
    n_el = sum(len(list(g.iter())) for g in body)
    check(got == want, "%s: %d elements identical apart from the deletions" % (name, n_el))

print("\n== C  tick marks: piece vs source ==")
for p in META["pieces"]:
    name = p["name"]
    root = etree.parse(p["svg"]).getroot()
    n_piece = sum(1 for _ in root.iter(CS + "use"))
    n_src = sum(sum(1 for _ in byid(src, i).iter(CS + "use")) for i in p["axes"])
    print("  %-18s use piece=%-2d source=%-2d" % (name, n_piece, n_src))
    check(n_piece == n_src, "%s: all %d tick-mark <use> kept" % (name, n_src))

print("\n== D  crop: 600 dpi render vs the source in the same window ==")
os.makedirs("out_ticks/work/verify", exist_ok=True)
margins = {}
for p in META["pieces"]:
    name, win = p["name"], tuple(p["win"])
    w, h = win[2], win[3]

    # reference: this piece's own axes, undeleted, rendered in the same window
    # (the whole document is not used: a neighbour panel's tick label bleeds a
    #  few points into the left margin of the bottom-right crop)
    g = etree.Element(CS + "svg", nsmap={None: "http://www.w3.org/2000/svg"})
    g.set("width", "%.4f" % (w * 96 / 72))
    g.set("height", "%.4f" % (h * 96 / 72))
    g.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
    body = etree.SubElement(g, CS + "g")
    for srcid in p["axes"]:
        e = etree.fromstring(etree.tostring(byid(src, srcid)))
        for tx in e.iter(CS + "text"):
            tx.set("font-family", "Arial")
            tx.set("font-size", "12")
        body.append(e)
    idmap = {e.get("id"): e for e in src.iter() if isinstance(e.tag, str) and e.get("id")}
    order = {i: k for k, i in enumerate(idmap)}
    extra = external_defs(body, idmap, order)      # markers live in axes_1's defs
    if extra:
        d = etree.Element(CS + "defs")
        for x in extra:
            d.append(x)
        g.insert(0, d)
    ref = "out_ticks/work/verify/%s_ref.svg" % name
    open(ref, "wb").write(etree.tostring(g, xml_declaration=True, encoding="utf-8"))

    # mask: renders of the groups this piece deleted, at their original place
    g = etree.Element(CS + "svg", nsmap={None: "http://www.w3.org/2000/svg"})
    g.set("width", "%.4f" % (w * 96 / 72))
    g.set("height", "%.4f" % (h * 96 / 72))
    g.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
    body = etree.SubElement(g, CS + "g")
    n_mask = 0
    for i, _ in removed[name]:
        e = etree.fromstring(etree.tostring(byid(src, i)))
        for tx in e.iter(CS + "text"):
            tx.set("font-family", "Arial")
            tx.set("font-size", "12")
        body.append(e)
        n_mask += 1
    mask = "out_ticks/work/verify/%s_mask.svg" % name
    open(mask, "wb").write(etree.tostring(g, xml_declaration=True, encoding="utf-8"))

    refp = render(ref, "out_ticks/work/verify/%s_ref.png" % name, 600)
    maskp = render(mask, "out_ticks/work/verify/%s_mask.png" % name, 600)

    mine = np.asarray(Image.open(p["png"]).convert("RGB")).astype(int)
    rf = np.asarray(Image.open(refp).convert("RGB")).astype(int)
    mk = np.asarray(Image.open(maskp).convert("RGB")).astype(int)
    assert mine.shape == rf.shape == mk.shape, (mine.shape, rf.shape, mk.shape)
    dm = ((255 - mk).max(axis=2) > 8).astype(np.uint8)
    d = dm.copy()
    for k in (-4, -3, -2, -1, 1, 2, 3, 4):
        d |= np.roll(dm, k, axis=0)
        d |= np.roll(dm, k, axis=1)
    diff = np.abs(mine - rf).max(axis=2)
    out = int((diff * (1 - d) > 0).sum())
    tot = int((diff > 0).sum())

    ink = (255 - mine).max(axis=2) > 8
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    mar = (cols[0] / S, (mine.shape[1] - 1 - cols[-1]) / S,
           rows[0] / S, (mine.shape[0] - 1 - rows[-1]) / S)
    margins[name] = mar
    print("  %-18s %dx%d  diff=%-6d outside-mask=%-5d  margins L%.2f R%.2f T%.2f B%.2f pt  (mask %d groups)"
          % (name, mine.shape[1], mine.shape[0], tot, out, *mar, n_mask))
    check(out == 0, "%s: nothing changed outside the deleted text" % name)
    check(min(mar) >= 1.4, "%s: no ink touches the crop edge (min %.2f pt)" % (name, min(mar)))

print("\n== E  PNG matches the SVG canvas ==")
for p in META["pieces"]:
    svg = etree.parse(p["svg"]).getroot()
    vb = [float(v) for v in svg.get("viewBox").split()]
    wpx, hpx = float(svg.get("width")), float(svg.get("height"))
    im = Image.open(p["png"])
    ok = (abs(wpx - vb[2] * 96 / 72) < 1e-3 and abs(hpx - vb[3] * 96 / 72) < 1e-3 and
          abs(im.size[0] - round(vb[2] * S)) <= 1 and abs(im.size[1] - round(vb[3] * S)) <= 1)
    check(ok, "%-18s %.3f x %.3f pt -> %dx%d px" % (p["name"], vb[2], vb[3], im.size[0], im.size[1]))

print("\n== F  nine histograms share one canvas and one plot position ==")
names9 = [p["name"] for p in META["pieces"] if not p["name"].startswith("S1b")]
szs = {(p["px"][0], p["px"][1]) for p in META["pieces"] if not p["name"].startswith("S1b")}
check(len(szs) == 1, "identical canvas: %s" % (szs,))

# plot-area position inside each piece = background patch rectangle - window
import re as _re
pos = {}
for p in META["pieces"]:
    if p["name"].startswith("S1b"):
        continue
    root = etree.parse(p["svg"]).getroot()
    a = byid(root, p["axes"][0])
    hit = None
    for c in a.iter(CS + "path"):
        d = c.get("d") or ""
        v = [float(x) for x in _re.findall(r"-?\d+\.?\d*", d)]
        if len(v) >= 8:
            xs, ys = v[0::2], v[1::2]
            if abs(max(xs) - min(xs) - 125.569) < .01 and abs(max(ys) - min(ys) - 115.162) < .01:
                hit = (min(xs) - p["win"][0], min(ys) - p["win"][1])
                break
    pos[p["name"]] = tuple(round(v, 4) for v in hit)
uniq = set(pos.values())
print("  plot-area offset inside the canvas: %s" % sorted(uniq))
ok = len(uniq) == 1 and abs(list(uniq)[0][0] - (36.36 + META["pad"])) < 1e-3 \
    and abs(list(uniq)[0][1] - (5.88 + META["pad"])) < 1e-3
check(ok, "all nine plot areas at the same offset %s pt" % (sorted(uniq),))
o = list(uniq)[0]
print("  canvas %.3f x %.3f pt, plot area %.3f x %.3f pt, margins L%.2f R%.2f T%.2f B%.2f"
      % (META["hist_win"][2], META["hist_win"][3], 125.569, 115.162,
         o[0], META["hist_win"][2] - o[0] - 125.569, o[1],
         META["hist_win"][3] - o[1] - 115.162))

print("\n%s" % ("ALL PASS" if not FAIL else "FAILURES (%d):\n  " % len(FAIL) + "\n  ".join(FAIL)))
