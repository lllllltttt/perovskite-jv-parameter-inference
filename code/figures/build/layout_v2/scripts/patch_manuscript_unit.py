# -*- coding: utf-8 -*-
"""Fix #1: keep the unit cm^-2 on one line in the main text (PDF p8, first paragraph).

Word ignores U+2060 WORD JOINER for line breaking but honours U+FEFF
ZERO WIDTH NO-BREAK SPACE (verified by A/B render test).  U+FEFF is written
between 'cm' and the superscript minus, and between the minus and the two,
so the whole unit is one unbreakable token.  No other character, font size,
run formatting or wording is touched.
"""
import hashlib, sys, docx
from docx.oxml.ns import qn

DOCX = sys.argv[1]
WJ = "\ufeff"
UNIT_OLD = "\u207b\u00b2"          # superscript minus + superscript two
PRE_OLD = "mA cm"

d = docx.Document(DOCX)
hits = []
for p in d.paragraphs:
    if "reproduced the stored curves" not in p.text:
        continue
    runs = p.runs
    for i, r in enumerate(runs):
        if r.text == UNIT_OLD:
            prev = runs[i-1] if i else None
            assert prev is not None and prev.text.endswith(PRE_OLD), \
                "unexpected run before the unit: %r" % (prev.text[-20:] if prev else None)
            before = (prev.text, r.text)
            prev.text = prev.text[:-len(PRE_OLD)] + "mA cm" + WJ
            r.text = "\u207b" + WJ + "\u00b2"
            hits.append((p.text[:60], before, (prev.text, r.text)))
            break

assert len(hits) == 1, "expected exactly one target paragraph, got %d" % len(hits)
for para, before, after in hits:
    print("paragraph :", para)
    print("  before  :", repr(before))
    print("  after   :", repr(after))

d.save(DOCX)
print("\nsaved:", DOCX)
print("sha256:", hashlib.sha256(open(DOCX,'rb').read()).hexdigest())
