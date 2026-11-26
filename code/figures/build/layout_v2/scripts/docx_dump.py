# -*- coding: utf-8 -*-
"""Dump a DOCX body in document order: paragraph index, style, text, tables.

    python scripts/docx_dump.py <file.docx> [p|t|all] [lo] [hi] [width]

Paragraph indices are python-docx body-paragraph indices -- the same numbering
the sync checklist uses -- and TABLE blocks are numbered separately. Every
editing round in this project has needed this dump to locate a block and to
show, afterwards, that only the intended blocks moved.

WHY THE TEXT IS COLLECTED FROM THE XML AND NOT FROM Paragraph.text
------------------------------------------------------------------
Word equations are OMML (<m:oMath>), not runs, and python-docx cannot see
them: Paragraph.text silently reports a paragraph that is half equation as if
the equation were not there. The supplementary information is full of them, and
the phase-1 round lost time to a negative text search that was really a
limitation of the search. So every block here is read as the concatenation of
<w:t> and <m:t> in document order, which is what the file actually shows on the
page. The OMML body is one character per <m:t> run, so the join is the only way
to see a symbol whole.
"""
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

_MATH = qn("m:t")
_TEXT = qn("w:t")


def para_text(p):
    """Everything the paragraph displays: w:t and m:t, in document order."""
    out = []
    for node in p._p.iter():
        if node.tag == _TEXT or node.tag == _MATH:
            out.append(node.text or "")
    return "".join(out)


def cell_text(c):
    out = []
    for p in c.paragraphs:
        out.append(para_text(p))
    for t in c.tables:
        for row in t.rows:
            for cc in row.cells:
                out.append(cell_text(cc))
    return " ".join(out)


def iter_block_items(parent):
    for child in parent.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def main(path, mode="all", lo=0, hi=10 ** 9, width=110):
    doc = Document(path)
    pi = ti = 0
    for blk in iter_block_items(doc):
        if isinstance(blk, Paragraph):
            txt = para_text(blk).strip().replace("\n", " ")
            if mode in ("all", "p") and lo <= pi <= hi:
                print("[%03d] {%s} %s" % (pi, blk.style.name, txt[:width]))
            pi += 1
        else:
            if mode in ("all", "t") and lo <= ti <= hi:
                print(">>> TABLE %d  %dx%d" % (ti, len(blk.rows),
                                               len(blk.columns)))
                for ri, row in enumerate(blk.rows):
                    cells = [cell_text(c).strip().replace("\n", " ")
                             for c in row.cells]
                    print("    r%-3d | %s" % (ri, " | ".join(cells)[:width]))
            ti += 1
    print("--- %d paragraphs, %d tables" % (pi, ti))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1] if len(a) > 1 else "all",
         int(a[2]) if len(a) > 2 else 0,
         int(a[3]) if len(a) > 3 else 10 ** 9,
         int(a[4]) if len(a) > 4 else 110)
