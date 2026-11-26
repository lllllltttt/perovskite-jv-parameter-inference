# -*- coding: utf-8 -*-
"""Figure S3 (SI) -> three standalone panels S3a / S3b / S3c.

Where it comes from
  SI.pptx embeds Figure S3 across three slides (not one): the embedded SVG on
  each slide is a re-export of the original matplotlib file, with the same
  viewBox to 1e-5 pt.  The originals are used as the source:
    FigureS3a.svg  <- SI slide 3  (panels a1-a6, J-V cycle cases)
    FigureS3b.svg  <- SI slide 4  (RMS vs voltage)
    FigureS3c.svg  <- SI slide 5  (panels c1-c4, cycle-gap distributions)

Deleted (the user re-adds them in PowerPoint)
  panel letters (a1)...(a6), (c1)...(c4);
  panel titles / subtitles ("cycle-gap lowest # 12058", "cg = 0.27 mA cm-2",
  "rRMSE = ...", "true-param control # 595", "zoom: 0-1.2 V", "median 2.56",
  "0.47" / "5.30", "rho = ... (p = ...)", "noise floor = 0.21 mA cm-2");
  axis titles and units ("J (mA cm-2)", "V (V)", "Voltage (V)",
  "RMSE across 45 samples (mA cm-2)", "count", ...);
  the legends (S3a figure-level legend_1, S3b in-axes legend_1);
  the categorical tick words ("0-1.0 V", ">1.0 V") - tick marks stay.

Kept verbatim
  every curve / line / marker collection / patch (including the inset axes of
  a5 and the dashed reference lines), the spines, the tick marks, and every
  numeric tick label.
"""
import io
import json
import os
import re
import subprocess
import sys

from lxml import etree
import numpy as np
from PIL import Image

if (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CS = "{http://www.w3.org/2000/svg}"
XL = "{http://www.w3.org/1999/xlink}"
SVGNS = "http://www.w3.org/2000/svg"
XLNS = "http://www.w3.org/1999/xlink"

BASE = r"E:\project\work1\20261024_final_figures_svg\si"
OUT = "out"
PAD = 2.5
PX_PER_PT = 96.0 / 72.0
NUM = re.compile(r"^[−\-]?\d+(\.\d+)?$")
PY = sys.executable

BLOCKS = [("S3a", "FigureS3a"), ("S3b", "FigureS3b"), ("S3c", "FigureS3c")]


# ---------------------------------------------------------------- helpers --
def txt(e):
    return "".join(e.itertext()).strip()


def flat(g):
    s = "".join("".join(t.itertext()) for t in g.iter(CS + "text"))
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


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
    root = etree.Element(CS + "svg", nsmap={None: SVGNS, "xlink": XLNS})
    root.set("width", "%.4f" % (win[2] * PX_PER_PT))
    root.set("height", "%.4f" % (win[3] * PX_PER_PT))
    root.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
    root.set("stroke-linejoin", "round")
    root.set("overflow", "hidden")
    body = etree.SubElement(root, CS + "g")
    need = set()
    for g in groups:
        body.append(g)
        need |= ref_ids(g)
    extra = external_defs(body, idmap, order)
    if extra:
        d = etree.Element(CS + "defs")
        for e in extra:
            d.append(e)
        root.insert(0, d)
    with open(path, "wb") as f:
        f.write(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    return path


def render(svg, png, dpi):
    for _ in range(3):
        r = subprocess.run([PY, "scripts/render_svg_px.py", svg, png,
                            "--dpi", str(dpi)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(png):
            return png
    raise RuntimeError("render failed " + svg)


def ink_bbox(png, win, dpi, thr=8):
    a = np.asarray(Image.open(png).convert("L")).astype(int)
    m = (255 - a) > thr
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    s = dpi / 72.0
    return (win[0] + cols[0] / s, win[1] + rows[0] / s,
            win[0] + (cols[-1] + 1) / s, win[1] + (rows[-1] + 1) / s)


def font_fix(el):
    """Pin the face/size as attributes (PowerPoint ignores the CSS shorthand)."""
    for t in el.iter(CS + "text"):
        st = t.get("style") or ""
        m = re.search(r"([\d.]+)px", st)
        t.set("font-family", "Arial")
        t.set("font-size", "%g" % (float(m.group(1)) if m else 10.0))


# ------------------------------------------------------------ delete words --
def cut(fig):
    """Remove legends, wording and categorical tick words; keep tick numbers.

    Returns (description, element) pairs: the elements are deep copies taken
    before removal, so a caller can render exactly the deleted ink.
    """
    removed = []

    def take(el, label):
        removed.append((label, etree.fromstring(etree.tostring(el))))
        return el
    for g in list(fig.iter(CS + "g")):
        gid = g.get("id") or ""
        if gid.startswith("legend"):
            take(g, gid)
            g.getparent().remove(g)

    for a in [g for g in fig.iter(CS + "g")
              if (g.get("id") or "").startswith("axes_")]:
        for c in list(a):
            if c.tag == CS + "g" and re.match(r"^text_\d+$", c.get("id") or ""):
                take(c, c.get("id"))
                a.remove(c)
        for c in list(a):
            if not (c.get("id") or "").startswith("matplotlib.axis_"):
                continue
            for g in list(c):
                if g.tag != CS + "g":
                    continue
                gid = g.get("id") or ""
                if gid.startswith(("xtick_", "ytick_")):
                    for t in list(g.iter(CS + "text")):
                        s = re.sub(r"\s+", " ", "".join(t.itertext())
                                   .replace("\xa0", " ")).strip()
                        if not NUM.match(s):
                            take(t, gid + " " + s)
                            t.getparent().remove(t)
                elif next(g.iter(CS + "text"), None) is not None:
                    take(g, gid)
                    c.remove(g)
    return removed


def main():
    for d in ("svg", "png", "work"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    meta = []
    for tag, stem in BLOCKS:
        src = etree.parse(os.path.join(BASE, stem + ".svg")).getroot()
        idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
        order = {i: k for k, i in enumerate(idmap)}
        fig = src.find(".//" + CS + "g[@id='figure_1']")
        fig = etree.fromstring(etree.tostring(fig))
        removed = cut(fig)
        font_fix(fig)

        vb = [float(v) for v in src.get("viewBox").split()]
        win0 = (vb[0] - 30, vb[1] - 30, vb[2] + 60, vb[3] + 60)
        p = build([etree.fromstring(etree.tostring(fig))], win0, idmap, order,
                  os.path.join(OUT, "work", tag + "_probe.svg"))
        render(p, os.path.join(OUT, "work", tag + "_probe.png"), 300)
        ib = ink_bbox(os.path.join(OUT, "work", tag + "_probe.png"), win0, 300)
        win = (round(ib[0] - PAD, 4), round(ib[1] - PAD, 4),
               round(ib[2] - ib[0] + 2 * PAD, 4), round(ib[3] - ib[1] + 2 * PAD, 4))

        svg = build([fig], win, idmap, order,
                    os.path.join(OUT, "svg", tag + ".svg"))
        png = os.path.join(OUT, "png", tag + "_600dpi.png")
        render(svg, png, 600)
        px = Image.open(png).size
        meta.append(dict(name=tag, source=stem, svg=svg, png=png, win=win,
                         px=list(px), removed=[(lbl, flat(el)) for lbl, el in removed]))
        print("  %-4s %-12s %8.3f x %8.3f pt  %s px  removed %d"
              % (tag, stem, win[2], win[3], "%dx%d" % px, len(removed)))

    # ---- preview: original stacking order, a / b / c -------------------
    s = 600 / 72.0
    GUT = 12.0
    W = max(m["win"][2] for m in meta)
    H = sum(m["win"][3] for m in meta) + GUT * (len(meta) + 1)
    canvas = Image.new("RGB", (int(round(W * s)), int(round(H * s))), "white")
    y = GUT
    for m in meta:
        x = (W - m["win"][2]) / 2.0
        canvas.paste(Image.open(m["png"]).convert("RGB"),
                     (int(round(x * s)), int(round(y * s))))
        y += m["win"][3] + GUT
    prev = os.path.join(OUT, "preview", "FigureS3_split_preview_600dpi.png")
    os.makedirs(os.path.dirname(prev), exist_ok=True)
    canvas.save(prev)
    print("\n  preview %s  %dx%d px = %.1f x %.1f pt"
          % (prev, canvas.size[0], canvas.size[1], W, H))

    json.dump(dict(pieces=meta, preview=prev),
              open(os.path.join(OUT, "work", "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    for m in meta:
        print("\n  == %s removed (%d) ==" % (m["name"], len(m["removed"])))
        for i, t in m["removed"]:
            print("     %-10s %r" % (i, t))


if __name__ == "__main__":
    main()
