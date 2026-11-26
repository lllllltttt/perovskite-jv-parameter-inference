# -*- coding: utf-8 -*-
"""Structural checks for the final Figure 2 assets."""
import json
import os
import re
import sys

import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
QA = os.path.join(OUT, "qa")

P = 1.7633333333333333
ML, MR, MB, MT = 0.50, 0.07, 0.42, 0.30
WF, HF = P + ML + MR, P + MB + MT
LEFT_PT, TOP_PT = ML * 72.0, MT * 72.0
SIDE_PT = P * 72.0
CB_W, CB_H = 0.60, 1.20

MINUS = "−"


def fmt(v, f):
    if f == "%d":
        s = "%d" % int(round(v))
    else:
        s = "%.1f" % v
    return s.replace("-", MINUS)


def check_pdf(path, rec):
    doc = pymupdf.open(path)
    assert doc.page_count == 1
    pg = doc[0]
    pw, ph = pg.rect.width, pg.rect.height
    out = dict(page_pt=[round(pw, 2), round(ph, 2)])

    diag, vs, hs = [], [], []
    for d in pg.get_drawings():
        for it in d["items"]:
            if it[0] != "l":
                continue
            p0, p1 = it[1], it[2]
            if abs(p0.x - p1.x) > 1 and abs(p0.y - p1.y) > 1:
                diag.append((p0, p1))
            elif abs(p0.x - p1.x) < 0.01 and abs(p0.y - p1.y) > 1:
                vs.append((p0.x, abs(p0.y - p1.y)))
            elif abs(p0.y - p1.y) < 0.01 and abs(p0.x - p1.x) > 1:
                hs.append((p0.y, abs(p0.x - p1.x)))
    frames = sorted({round(l, 2) for _, l in vs + hs if l > 100})
    out["frame_len_pt"] = frames
    out["n_diag"] = len(diag)

    assert len(diag) == 1, len(diag)
    p0, p1 = diag[0]
    dx, dy = abs(p0.x - p1.x), abs(p0.y - p1.y)
    corners = sorted([(round(p0.x, 2), round(p0.y, 2)),
                      (round(p1.x, 2), round(p1.y, 2))])
    out["diag_dxdy"] = [round(dx, 3), round(dy, 3)]
    out["diag_corners"] = corners
    assert abs(dx - SIDE_PT) < 0.01 and abs(dy - SIDE_PT) < 0.01
    assert abs(dx - dy) < 1e-3
    assert corners == sorted([(round(LEFT_PT, 2), round(TOP_PT + SIDE_PT, 2)),
                              (round(LEFT_PT + SIDE_PT, 2), round(TOP_PT, 2))])

    spans = []
    for block in pg.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                if sp["text"].strip():
                    spans.append(sp)
    bad = []
    for sp in spans:
        x0, y0, x1, y1 = sp["bbox"]
        if x0 < -0.01 or y0 < -0.01 or x1 > pw + 0.01 or y1 > ph + 0.01:
            bad.append(sp["text"].replace(MINUS, "-"))
    expected = set(fmt(v, rec["fmt"]) for v in rec["xticks"]) | \
        set(fmt(v, rec["fmt"]) for v in rec["yticks"])
    got = [sp["text"].replace(MINUS, "-") for sp in spans]
    exp = set(s.replace(MINUS, "-") for s in expected)
    out["n_spans"] = len(spans)
    out["text_ok"] = set(got) == exp
    out["text_extra"] = sorted(set(got) - exp)
    out["text_missing"] = sorted(exp - set(got))
    out["n_outside"] = len(bad)
    out["outside"] = bad
    out["n_images"] = len(pg.get_images(full=True))
    fonts = pg.get_fonts(full=True)
    out["fonts"] = sorted({f[3] for f in fonts})
    doc.close()
    return out


def check_svg(path, rec):
    s = open(path, encoding="utf-8").read()
    texts = [re.sub(r"<[^>]+>", "", t) for t in
             re.findall(r"<text\b[^>]*>(.*?)</text>", s, re.S)]
    expected = set(fmt(v, rec["fmt"]) for v in rec["xticks"]) | \
        set(fmt(v, rec["fmt"]) for v in rec["yticks"])
    return dict(n_text=len(texts), n_image=len(re.findall(r"<image\b", s)),
                n_path=len(re.findall(r"<path\b", s)),
                text_set_equal=set(texts) == expected,
                extra=sorted(set(texts) - expected),
                missing=sorted(expected - set(texts)),
                per_char_x=len(re.findall(r'<tspan[^>]*\bx="[^"]*\s[^"]*"', s)))


def main():
    qa = json.load(open(os.path.join(QA, "qa_report.json"), encoding="utf-8"))
    res = {"panels": {}, "colorbars": {}, "preview": {}}
    for rec in qa["panels"]:
        name = "%s_%s" % (rec["id"], rec["title"].replace(" ", "_"))
        stem = os.path.join(OUT, "panels", name)
        im = Image.open(stem + ".png")
        assert im.size == (2100, 2235), im.size
        assert im.mode == "RGB"
        assert im.getpixel((5, 5)) == (255, 255, 255)
        pdf = check_pdf(stem + ".pdf", rec)
        svg = check_svg(stem + ".svg", rec)
        assert pdf["n_outside"] == 0 and pdf["text_ok"]
        assert svg["text_set_equal"]
        res["panels"][rec["id"]] = dict(png=list(im.size), pdf=pdf, svg=svg)

    for rec in qa["colorbars"]:
        stem = os.path.join(OUT, "colorbars", rec["name"])
        im = Image.open(stem + ".png")
        assert im.size == (540, 2235), im.size
        assert im.mode == "RGB"
        doc = pymupdf.open(stem + ".pdf")
        pg = doc[0]
        texts = [sp["text"].strip() for b in pg.get_text("dict")["blocks"]
                 for l in b.get("lines", []) for sp in l.get("spans", [])
                 if sp["text"].strip()]
        out = dict(page_pt=[round(pg.rect.width, 2), round(pg.rect.height, 2)],
                   texts=texts, n_images=len(pg.get_images(full=True)))
        assert set(texts) == set(["1", "2", "5", "10", "20", "Samples per bin"])
        s = open(stem + ".svg", encoding="utf-8").read()
        out["svg_text"] = len(re.findall(r"<text\b", s))
        doc.close()
        res["colorbars"][rec["name"]] = out

    prev = Image.open(os.path.join(OUT, "preview",
                                   "Figure2_assembly_preview.png"))
    res["preview"] = dict(png=list(prev.size))
    with open(os.path.join(QA, "structural_checks.json"), "w",
              encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)

    for pid, r in res["panels"].items():
        print(pid, r["pdf"]["frame_len_pt"], r["pdf"]["diag_dxdy"],
              r["pdf"]["n_spans"], r["pdf"]["n_outside"], r["svg"]["n_text"],
              r["svg"]["n_image"], r["pdf"]["fonts"])
    for name, r in res["colorbars"].items():
        print(name, r["page_pt"], r["texts"], r["n_images"], r["svg_text"])
    print("preview", res["preview"]["png"])


if __name__ == "__main__":
    main()
