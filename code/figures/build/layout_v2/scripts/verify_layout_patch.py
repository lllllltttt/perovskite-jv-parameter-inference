# -*- coding: utf-8 -*-
"""verify_layout_patch.py — acceptance gate for the three layout repairs.

Run against the DELIVERED PDFs (after restore_hd.py), never against the DOCX and
never against the plain Word render:

    python scripts/verify_layout_patch.py <manuscript.pdf> <si.pdf>

Checks, each on the rendered page and not on a DOCX property:

  1  the unit cm^-2 is never split: no line break may fall between U+207B and
     U+00B2 anywhere in the manuscript;
  2  every statistic label of T6.8a-c is intact on ONE page together with the
     six values that belong to it;
  3  the T6.9 header row never appears on a page that does not also carry its
     first data row;
  4  on the affected pages, no text lies outside the printable area and no two
     text blocks overlap.

Exit status is non-zero if any check fails.
"""
import re, sys, pymupdf

FAIL = []

def pages(path):
    d = pymupdf.open(path)
    return d, [re.sub(r"[ \t]+", " ", p.get_text()) for p in d]

def check1(ms_pdf):
    d, pg = pages(ms_pdf)
    allt = "\n".join(pg)
    split = [m.start() for m in re.finditer(r"\u207b\s*\n\s*\u00b2", allt)]
    intact = allt.count("\u207b\u00b2")
    print("  [1] unit cm^-2 split across a line : %d   (intact occurrences: %d)"
          % (len(split), intact))
    for i in split:
        print("      !! %r" % allt[max(0, i-60):i+30])
    if split:
        FAIL.append("check1: %d split unit(s)" % len(split))
    for n, t in enumerate(pg):
        if "1.19 \u00d7 10" in t:
            i = t.find("1.19 \u00d7 10")
            print("      p%d: %r" % (n+1, t[i:i+68]))

def check2(si_pdf):
    d, pg = pages(si_pdf)
    labels = ["median |\u0394a| / ba", "IQR |\u0394a| / ba",
              "median |\u0394r| / br", "IQR |\u0394r| / br"]
    for lab in labels:
        found = []
        for i, t in enumerate(pg):
            g = re.sub(r"\s+", " ", t)
            for m in re.finditer(re.escape(lab), g):
                tail = g[m.end():m.end()+130]
                found.append((i+1, len(re.findall(r"-?\d[\d.,\u2013]*", tail))))
        state = "ok" if len(found) == 3 and all(n >= 6 for _, n in found) else "FAIL"
        print("  [2] %-18s intact on one page: %d/3 %s %s"
              % (lab, len(found), found, "" if state == "ok" else "<-- "+state))
        if state != "ok":
            FAIL.append("check2: %s" % lab)
    for i, t in enumerate(pg):
        lines = [l.strip() for l in t.split("\n") if l.strip()]
        if lines and lines[-1] in ("median", "Distinct", "curves", "IQR |\u0394a| /", "IQR |\u0394r| /"):
            print("      !! page %d ends on a bare label fragment %r" % (i+1, lines[-1]))
            FAIL.append("check2: page %d ends mid-row" % (i+1))

def check3(si_pdf):
    d, pg = pages(si_pdf)
    orphan = 0
    for i, t in enumerate(pg):
        g = re.sub(r"\s+", " ", t)
        if "Random-pair median |\u0394|" not in g:
            continue
        first = "a, mobility" in g
        print("  [3] page %d carries the T6.9 header; first data row present: %s"
              % (i+1, first))
        if not first:
            orphan += 1
    print("      orphaned T6.9 header rows: %d" % orphan)
    if orphan:
        FAIL.append("check3: %d orphan header(s)" % orphan)

def check4(pdf, tag, pagenos):
    d = pymupdf.open(pdf)
    for pno in pagenos:
        p = d[pno-1]
        W, H = p.rect.width, p.rect.height
        blocks = [b for b in p.get_text("blocks") if b[4].strip()]
        out = [b for b in blocks if b[0] < 20 or b[2] > W-20 or b[1] < 20 or b[3] > H-20]
        ov = 0
        for i in range(len(blocks)):
            for j in range(i+1, len(blocks)):
                a, b = blocks[i], blocks[j]
                if min(a[2], b[2]) - max(a[0], b[0]) > 2 and min(a[3], b[3]) - max(a[1], b[1]) > 2:
                    ov += 1
        lowest = max([b[3] for b in blocks], default=0)
        print("  [4] %s p%-2d outside=%-2d overlaps=%-2d lowest-text y1=%6.1f bottom gap=%5.1f pt"
              % (tag, pno, len(out), ov, lowest, H-72-lowest))
        if out or ov:
            FAIL.append("check4: %s p%d" % (tag, pno))

ms_pdf, si_pdf = sys.argv[1], sys.argv[2]
print("=" * 72); print("check 1 — manuscript, the unit cm^-2");        check1(ms_pdf)
print("=" * 72); print("check 2 — SI, T6.8a-c rows must not straddle a page"); check2(si_pdf)
print("=" * 72); print("check 3 — SI, T6.9 header must not be orphaned");      check3(si_pdf)
print("=" * 72); print("check 4 — affected + adjacent pages: clipping / overlap")
check4(ms_pdf, "MS", [8]); check4(si_pdf, "SI", [14, 15, 16])
print("=" * 72)
if FAIL:
    print("RESULT: FAIL"); [print("   -", f) for f in FAIL]; sys.exit(1)
print("RESULT: PASS — all four checks")
