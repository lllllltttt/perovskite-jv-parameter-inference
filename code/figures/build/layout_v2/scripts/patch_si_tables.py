# -*- coding: utf-8 -*-
"""Fixes #2 and #3 in the SI.

#2  T6.8a-c: switch OFF "allow row to break across pages" (w:cantSplit) on every
    row, so a statistic label and its six values can never be split by a page
    break.  The tables still flow across pages and still repeat their header
    rows (w:tblHeader is untouched) -- nothing is pinned to one page.

#3  T6.9: the header row is pulled down to the first data row with w:keepNext on
    the paragraphs inside the header cells, so the header can no longer be left
    orphaned at the foot of a page.
"""
import hashlib, sys, docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCX = sys.argv[1]

TRPR_ORDER = ["cnfStyle","divId","gridBefore","gridAfter","wBefore","wAfter",
              "cantSplit","trHeight","tblHeader","tblCellSpacing","jc","hidden"]
PPR_ORDER  = ["pStyle","keepNext","keepLines","pageBreakBefore"]

def insert_ordered(parent, tag, order):
    """Insert <w:tag> into parent at its schema position."""
    el = OxmlElement('w:' + tag)
    idx = order.index(tag)
    for child in parent:
        name = child.tag.split('}')[1]
        if name in order and order.index(name) > idx:
            child.addprevious(el)
            return el
    parent.append(el)
    return el

def add_trPr(tr):
    trPr = tr.find(qn('w:trPr'))
    if trPr is None:
        trPr = OxmlElement('w:trPr')
        tr.insert(0, trPr)          # w:trPr is the first child of w:tr
    return trPr

def add_pPr(p):
    pPr = p.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr')
        p.insert(0, pPr)            # w:pPr is the first child of w:p
    return pPr

def prev_caption(body, tbl):
    p = tbl.getprevious()
    while p is not None and p.tag != qn('w:p'):
        p = p.getprevious()
    return "" if p is None else "".join(t.text or "" for t in p.iter(qn('w:t'))).strip()

def add_keepnext(tr):
    n = 0
    for tc in tr.findall(qn('w:tc')):
        for p in tc.findall(qn('w:p')):
            pPr = add_pPr(p)
            if pPr.find(qn('w:keepNext')) is None:
                insert_ordered(pPr, 'keepNext', PPR_ORDER)
                n += 1
    return n

d = docx.Document(DOCX)
body = d.element.body
tables = d.tables
assert len(tables) >= 24, "table map shifted: only %d tables" % len(tables)

EXPECT = {20: "T6.8a", 21: "T6.8b", 22: "T6.8c", 23: "T6.9"}
report = []
for idx, cap in EXPECT.items():
    t = tables[idx]
    caption = prev_caption(body, t._tbl)
    assert cap in caption, "table #%d caption is %r, expected %s" % (idx, caption[:60], cap)
    rows = t._tbl.findall(qn('w:tr'))
    before = sum(1 for tr in rows if (tr.find(qn('w:trPr')) is not None
                                      and tr.find(qn('w:trPr')).find(qn('w:cantSplit')) is not None))
    for tr in rows:
        add_ordered = add_trPr(tr)
        if add_ordered.find(qn('w:cantSplit')) is None:
            insert_ordered(add_ordered, 'cantSplit', TRPR_ORDER)
    hdr = rows[0].find(qn('w:trPr'))
    hdr_repeat = hdr is not None and hdr.find(qn('w:tblHeader')) is not None
    kn = add_keepnext(rows[0]) if cap == "T6.9" else 0
    report.append((idx, cap, len(rows), before, hdr_repeat, kn))

for idx, cap, nrows, before, hdr, kn in report:
    print("%-6s tbl#%-3d rows=%-3d cantSplit-before=%d  headerRepeat=%s  keepNext-added=%d"
          % (cap, idx, nrows, before, hdr, kn))

d.save(DOCX)
print("\nsaved:", DOCX)
print("sha256:", hashlib.sha256(open(DOCX,'rb').read()).hexdigest())
