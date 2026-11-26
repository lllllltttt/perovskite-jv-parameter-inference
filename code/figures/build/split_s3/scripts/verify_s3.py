# -*- coding: utf-8 -*-
"""Verification for the three Figure S3 blocks.

A  wording      : only numeric tick labels remain (no letters, no legends)
B/C data       : every surviving element identical to the source vector, and
                 identical counts of path / use / rect (data shapes intact)
D  ticks        : identical tick marks; numeric labels identical; the
                 categorical labels removed but their tick marks kept
E  no collateral: 600-dpi difference against the untouched source is confined
                 to the ink of exactly the elements that were deleted
F  margins      : all ink inside the canvas with clearance
G  inset        : the a5 inset axes and its curves survived
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
import split_s3 as S3     # noqa: E402  same deletion rules as the builder

CS = "{http://www.w3.org/2000/svg}"
OUT = "out"
NUM = re.compile(r"^[−\-]?\d+(\.\d+)?$")
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
        attrs = tuple(sorted((k, v) for k, v in x.attrib.items()
                             if k not in ("id", "font-family", "font-size")))
        return "<%s %s>%s</%s>" % (x.tag, attrs, "".join(rec(c) for c in x), x.tag)
    return rec(e)


def count_kinds(root):
    out = {}
    for e in root.iter():
        if isinstance(e.tag, str):
            k = e.tag.split("}")[1]
            out[k] = out.get(k, 0) + 1
    return out


def main():
    meta = json.load(open(os.path.join(OUT, "work", "meta.json"), encoding="utf-8"))
    by = {m["name"]: m for m in meta["pieces"]}

    print("=" * 78)
    print("A  wording: only numeric tick labels remain")
    print("=" * 78)
    for m in meta["pieces"]:
        root = etree.parse(m["svg"]).getroot()
        texts = [txt(t) for t in root.iter(CS + "text")]
        bad = [s for s in texts if not NUM.match(s)]
        ok(not bad, "%-4s %3d numeric labels, %d non-numeric"
           % (m["name"], len(texts), len(bad)), str(bad[:4]) if bad else "")

    print("\n" + "=" * 78)
    print("B/C  data and retained artwork identical to the source")
    print("=" * 78)
    for m in meta["pieces"]:
        src = etree.parse(os.path.join(S3.BASE, m["source"] + ".svg")).getroot()
        fig0 = src.find(".//" + CS + "g[@id='figure_1']")
        exp = etree.fromstring(etree.tostring(fig0))
        S3.cut(exp)
        S3.font_fix(exp)
        got = etree.parse(m["svg"]).getroot().find(CS + "g")[0]
        k0, k1 = count_kinds(exp), count_kinds(got)
        same = all(k1.get(k, 0) == v for k, v in k0.items())
        ok(canon(exp) == canon(got) and same,
           "%-4s %d elements identical (path %d, use %d, rect %d)"
           % (m["name"], sum(1 for _ in exp.iter()), k1.get("path", 0),
              k1.get("use", 0), k1.get("rect", 0)))

    print("\n" + "=" * 78)
    print("D  ticks: marks identical, numeric labels identical, categories gone")
    print("=" * 78)
    for m in meta["pieces"]:
        src = etree.parse(os.path.join(S3.BASE, m["source"] + ".svg")).getroot()
        got = etree.parse(m["svg"]).getroot()

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
        d0, d1 = ticks(src), ticks(got)
        bad, ncat = [], 0
        for gid, (pos, lab) in d0.items():
            if gid not in d1:
                bad.append((gid, "missing"))
                continue
            pos1, lab1 = d1[gid]
            if pos != pos1:
                bad.append((gid, "mark moved"))
            if lab is None or NUM.match(lab):
                if lab1 != lab:
                    bad.append((gid, "label changed", lab, lab1))
            else:
                ncat += 1
                if lab1 is not None:
                    bad.append((gid, "categorical kept", lab1))
        ok(not bad, "%-4s %d tick groups identical, %d categorical labels removed"
           % (m["name"], len(d0), ncat), str(bad[:3]))

    print("\n" + "=" * 78)
    print("E  difference against the untouched source is only the deleted ink")
    print("=" * 78)
    for m in meta["pieces"]:
        src = etree.parse(os.path.join(S3.BASE, m["source"] + ".svg")).getroot()
        idmap = {e.get("id"): e for e in src.iter() if e.get("id")}
        order = {i: k for k, i in enumerate(idmap)}
        fig0 = src.find(".//" + CS + "g[@id='figure_1']")
        win = tuple(m["win"])

        ref = etree.fromstring(etree.tostring(fig0))
        S3.font_fix(ref)
        rp = S3.build([ref], win, idmap, order,
                      os.path.join(OUT, "work", m["name"] + "_ref.svg"))
        S3.render(rp, os.path.join(OUT, "work", m["name"] + "_ref.png"), 600)

        probe = etree.fromstring(etree.tostring(fig0))
        removed = S3.cut(probe)
        maskdoc = etree.Element(CS + "svg",
                                nsmap={None: "http://www.w3.org/2000/svg",
                                       "xlink": "http://www.w3.org/1999/xlink"})
        maskdoc.set("width", "%.4f" % (win[2] * 96 / 72))
        maskdoc.set("height", "%.4f" % (win[3] * 96 / 72))
        maskdoc.set("viewBox", "%.4f %.4f %.4f %.4f" % win)
        g = etree.SubElement(maskdoc, CS + "g")
        for _lbl, el in removed:
            g.append(etree.fromstring(etree.tostring(el)))
        mp = S3.build([g], win, idmap, order,
                      os.path.join(OUT, "work", m["name"] + "_mask.svg"))
        S3.render(mp, os.path.join(OUT, "work", m["name"] + "_mask.png"), 600)

        a = np.asarray(Image.open(os.path.join(OUT, "png", m["name"] +
                                               "_600dpi.png")).convert("L")).astype(int)
        b = np.asarray(Image.open(os.path.join(OUT, "work", m["name"] +
                                               "_ref.png")).convert("L")).astype(int)
        mask = ((255 - np.asarray(Image.open(os.path.join(
            OUT, "work", m["name"] + "_mask.png")).convert("L")).astype(int)) > 8)
        for _ in range(6):
            d = mask.copy()
            d[1:, :] |= mask[:-1, :]
            d[:-1, :] |= mask[1:, :]
            d[:, 1:] |= mask[:, :-1]
            d[:, :-1] |= mask[:, 1:]
            mask = d
        if b.shape != a.shape:
            b = np.asarray(Image.fromarray(b.astype(np.uint8))
                           .resize(a.shape[::-1], Image.LANCZOS)).astype(int)
        diff = np.abs(a - b) > 40
        outside = int((diff & ~mask).sum())
        ok(outside == 0, "%-4s %d px differ, all inside the deleted ink"
           % (m["name"], int((diff & mask).sum())), "outside=%d" % outside)

    print("\n" + "=" * 78)
    print("F  margins: every block inside its canvas")
    print("=" * 78)
    for m in meta["pieces"]:
        im = np.asarray(Image.open(os.path.join(OUT, "png", m["name"] +
                                                 "_600dpi.png")).convert("L")).astype(int)
        mk = (255 - im) > 8
        rows = np.where(mk.any(axis=1))[0]
        cols = np.where(mk.any(axis=0))[0]
        clear = min(cols[0], rows[0], im.shape[1] - 1 - cols[-1],
                    im.shape[0] - 1 - rows[-1]) / (600 / 72.0)
        ok(clear > 1.0, "%-4s clearance %.2f pt" % (m["name"], clear))

    print("\n" + "=" * 78)
    print("G  the a5 inset survived")
    print("=" * 78)
    root = etree.parse(by["S3a"]["svg"]).getroot()
    ids = {g.get("id") for g in root.iter(CS + "g")}
    n_axes = len([i for i in ids if i and i.startswith("axes_")])
    ok(n_axes >= 7, "S3a keeps %d axes groups (6 panels + inset)" % n_axes)

    print("\n" + "=" * 78)
    print("RESULT: %s   (%d failures)" % ("ALL PASS" if not FAIL else "FAIL",
                                          len(FAIL)))
    print("=" * 78)
    for f in FAIL:
        print("  FAILED:", f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
