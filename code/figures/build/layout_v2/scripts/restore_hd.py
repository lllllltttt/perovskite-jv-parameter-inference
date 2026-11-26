# -*- coding: utf-8 -*-
"""
restore_hd.py — undo Word's 200 ppi bitmap cap on a rendered PDF.

    python scripts/restore_hd.py <file.docx> [<file.pdf>]

Word's PDF export always downsamples bitmaps to 200 ppi and there is no
switch for it. Every figure in this delivery is a 600 dpi or vector-quality
render, so the plain export silently destroys exactly the content the round
was spent producing: a Figure 2 panel arrives as a soft 200 ppi cloud in the
right place at the right size, which no geometry check can see.

The fix is post-export and format-level: each image stream in the PDF is
matched back to the HD original carried inside the DOCX, then swapped in place
with Page.replace_image. Placement, pagination and every text run are
untouched -- the page objects are not re-laid-out.

The match is by DOCUMENT ORDER, not by aspect ratio. python-docx appends new
media parts without removing the ones already in the package, so a rebuilt
manuscript carries both its old figures and the new ones, and an old Figure 4
and a new Figure 4 have identical pixel dimensions. Aspect ratio cannot tell
them apart; it silently picks whichever sorts first. The order in which the
document references its images is unambiguous, so that is what is used here,
with the aspect ratio kept only as an assertion that the pairing is sane.

Must be re-run after EVERY render: Word re-caps the bitmaps each time.
"""
import hashlib
import os
import re
import struct
import sys
import zipfile

import pymupdf
from docx import Document
from docx.oxml.ns import qn

WORK = os.path.dirname(os.path.abspath(__file__))
# pymupdf 1.24 spells the module `fitz`; 1.25+ prefers `pymupdf`. The older
# name is still importable, and the wording round used it, so fall back.
if pymupdf.__name__ == "pymupdf" and not hasattr(pymupdf, "open"):
    import fitz as pymupdf                                   # noqa: F401

MIN_SIDE = 900          # below this a bitmap is a logo/rule, not a figure
ASPECT_TOL = 0.02


def png_size(d):
    return struct.unpack(">II", d[16:24])


def referenced_in_order(docx):
    """The media parts the document actually draws, in document order."""
    z = zipfile.ZipFile(docx)
    rels = z.read("word/_rels/document.xml.rels").decode("utf8")
    target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
    part = {}
    for n in z.namelist():
        if n.startswith("word/media/"):
            part["media/" + n.rsplit("/", 1)[-1]] = n
    out = []
    for blip in Document(docx).element.body.iter(qn("a:blip")):
        tgt = target.get(blip.get(qn("r:embed")))
        if tgt in part and part[tgt] not in out:
            out.append(part[tgt])
    return z, out


def restore(docx, pdf):
    assert os.path.exists(pdf), "render the DOCX to PDF first"

    z, order = referenced_in_order(docx)
    src, orphan = {}, {}
    for n in sorted(x for x in z.namelist() if x.startswith("word/media/")):
        d = z.read(n)
        sw, sh = png_size(d)
        (src if n in order else orphan).__setitem__(n, (sw, sh, d))
    print("== docx media parts: %d referenced, %d orphaned =="
          % (len(src), len(orphan)))
    for n in order:
        sw, sh, d = src[n]
        print("  %-12s %5dx%-5d %11s bytes"
              % (n.rsplit("/", 1)[-1], sw, sh, "{:,}".format(len(d))))
    for n, (sw, sh, d) in sorted(orphan.items()):
        print("  (orphan) %-6s %5dx%-5d %11s bytes -- not drawn, ignored"
              % (n.rsplit("/", 1)[-1], sw, sh, "{:,}".format(len(d))))

    before_sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    before_size = os.path.getsize(pdf)
    doc = pymupdf.open(pdf)
    pages0 = doc.page_count
    text0 = "\n".join(doc[i].get_text() for i in range(doc.page_count))

    placements = []
    for pno in range(doc.page_count):
        for info in doc[pno].get_images(full=True):
            pix = pymupdf.Pixmap(doc, info[0])
            if pix.width < MIN_SIDE and pix.height < MIN_SIDE:
                continue
            placements.append((pno + 1, info[0], pix.width, pix.height))

    print("\n== mapping (document order) ==")
    drawn = [n for n in order
             if src[n][0] >= MIN_SIDE or src[n][1] >= MIN_SIDE]
    assert len(drawn) == len(placements), \
        "%d referenced figures >=%d px but %d bitmaps in the PDF" \
        % (len(drawn), MIN_SIDE, len(placements))
    plan = []
    for (pno, xref, w, h), n in zip(placements, drawn):
        sw, sh, _d = src[n]
        gap = abs(sw / float(sh) - w / float(h))
        assert gap < ASPECT_TOL, \
            "pairing out of step at page %d: PDF %dx%d vs DOCX %s %dx%d" \
            % (pno, w, h, n, sw, sh)
        print("  p%-3d xref %-5d %5dx%-5d -> %-12s %5dx%-5d (aspect gap %.4f)"
              % (pno, xref, w, h, n.rsplit("/", 1)[-1], sw, sh, gap))
        plan.append((pno, xref, n))

    assert placements, "nothing >=900 px - Word already kept the originals?"

    print("\n== replacing streams ==")
    tmp_png = os.path.join(WORK, "_hd_tmp.png")
    for pno, xref, name in plan:
        with open(tmp_png, "wb") as f:
            f.write(src[name][2])
        doc[pno - 1].replace_image(xref, filename=tmp_png)
    os.remove(tmp_png)

    print("== pruning undrawn aliases ==")
    pruned = 0
    for pno in range(doc.page_count):
        page = doc[pno]
        kind, val = doc.xref_get_key(page.xref, "Resources/XObject")
        if kind != "dict" or val is None:
            continue
        names = re.findall(r"/(\w+)\s+\d+ 0 R", val)
        drawn = set(re.findall(r"/(\w+)\s+Do\b",
                               page.read_contents().decode("latin-1")))
        for nm in names:
            if nm.startswith("fzImg") and nm not in drawn:
                doc.xref_set_key(page.xref, "Resources/XObject/%s" % nm,
                                 "null")
                pruned += 1
    print("  pruned %d alias entries" % pruned)

    tmp = pdf + ".tmp"
    doc.save(tmp, garbage=4, deflate=True, clean=True)
    doc.close()
    os.replace(tmp, pdf)

    print("\n== result ==")
    doc = pymupdf.open(pdf)
    text1 = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    print("  pages   : %d -> %d" % (pages0, doc.page_count))
    print("  bytes   : %s -> %s" % ("{:,}".format(before_size),
                                    "{:,}".format(os.path.getsize(pdf))))
    print("  text    : %s" % ("IDENTICAL to the plain render"
                              if text0 == text1 else "CHANGED !!"))
    print("  sha256  : %s\n         -> %s"
          % (before_sha, hashlib.sha256(open(pdf, "rb").read()).hexdigest()))

    print("\n== bitmaps >=900 px on a side (after restore) ==")
    n_big = 0
    for pno in range(doc.page_count):
        for info in doc[pno].get_images(full=True):
            pix = pymupdf.Pixmap(doc, info[0])
            if pix.width >= MIN_SIDE or pix.height >= MIN_SIDE:
                n_big += 1
                print("  p%-3d xref %-5d %5d x %-5d"
                      % (pno + 1, info[0], pix.width, pix.height))
    print("  total: %d" % n_big)
    doc.close()
    return 0 if text0 == text1 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    docx = sys.argv[1]
    pdf = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(docx)[0] + ".pdf"
    sys.exit(restore(docx, pdf))
