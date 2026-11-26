# -*- coding: utf-8 -*-
"""
cross_reference_map.py -- every figure/table reference in the two delivered
Word files, with the paragraph it sits in, the section it falls under, and
whether the thing it names actually exists in this delivery.

    python scripts/cross_reference_map.py

Reads the BUILT files (manuscript/*_integrated.docx, si/*_synced.docx), not the
sources: the map must describe what the reader is handed.

Resolution rules
  Fig./Figure 1-5     -> figures/Figure<N>.{pdf,svg,png}
  Fig./Figure S1-S7   -> the SI image paragraphs, in order (caption = number)
  Table S*            -> a caption paragraph in the SI starting "Table S..."
  Table 1             -> a caption paragraph in the manuscript starting
                         "Table 1."  (the only main-text table)
A reference that cannot be resolved is written with status=UNRESOLVED and the
script exits non-zero, so a broken link cannot pass silently.
"""
import csv
import os
import re
import sys

from docx import Document
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
MS = os.path.join(OUT, "manuscript", "Manuscript_20261002_Working_integrated.docx")
SI = os.path.join(OUT, "si", "Supplementary_Information_synced.docx")
FIGDIR = os.path.join(OUT, "figures")
CSV_OUT = os.path.join(OUT, "report", "cross_reference_map.csv")

W, M = qn("w:t"), qn("m:t")
TOKEN = re.compile(r"(?:Figs?\.|Figures?)\s*S?\d+[a-h]?|Tables?\s*S?\d+[a-z]?")


def ptext(p):
    return "".join((n.text or "") for n in p._p.iter() if n.tag in (W, M))


def walk(path, label):
    """Yield (paragraph index, section, text, has_inline_image)."""
    doc = Document(path)
    section = "(front matter)"
    for i, p in enumerate(doc.paragraphs):
        t = ptext(p)
        if p.style.name.startswith("Heading") or p.style.name.startswith("Title"):
            section = t.strip() or section
        img = bool(p._p.findall(".//" + qn("wp:inline")))
        yield i, section, t, img


def si_contents():
    """The figures and tables the SI defines, by the number it gives them."""
    figs, tbls = {}, {}
    order = 0
    for i, _sec, t, img in walk(SI, "SI"):
        if img:
            order += 1
        m = re.match(r"Figure\s+(S\d+)\.", t.strip())
        if m:
            figs[m.group(1)] = i
        m = re.match(r"Table\s+(S\d+[a-z]?)[.\s]", t.strip() + " ")
        if m:
            tbls[m.group(1)] = i
    return figs, tbls, order


def ms_contents():
    """Main-text table captions. The manuscript's Table 1 caption is a Heading 2
    reading "Table 1 Target parameters and sampling ranges" -- no period after
    the number, which is why the separator class below covers space too."""
    tbls = {}
    for i, _sec, t, _img in walk(MS, "MS"):
        m = re.match(r"Table\s+(\d+[a-z]?)[.\s]", t.strip() + " ")
        if m:
            tbls[m.group(1)] = i
    return tbls


def resolve(ref, ms_tables, si_figs, si_tables):
    """-> (kind, target, definition location, status)"""
    r = ref.replace("Figs.", "Fig.").replace("Figures", "Figure")
    r = r.replace("Tables", "Table").replace("Fig. ", "Figure ")
    num = re.search(r"(S?\d+[a-h]?)", r).group(1)
    is_table = r.startswith("Table")

    if is_table:
        if num.startswith("S"):
            if num in si_tables:
                return ("SI table", "Table " + num,
                        "SI paragraph %d" % si_tables[num], "ok")
            return ("SI table", "Table " + num, "-", "UNRESOLVED")
        if num in ms_tables:
            return ("main table", "Table " + num,
                    "manuscript paragraph %d" % ms_tables[num], "ok")
        return ("main table", "Table " + num, "-", "UNRESOLVED")

    if num.startswith("S"):
        if num in si_figs:
            return ("SI figure", "Figure " + num,
                    "SI paragraph %d" % si_figs[num], "ok")
        return ("SI figure", "Figure " + num, "-", "UNRESOLVED")

    # "Fig. 2g" names panel g of figure 2: the file is Figure2.png either way.
    stem = re.match(r"\d+", num).group(0)
    png = os.path.join(FIGDIR, "Figure%s.png" % stem)
    if os.path.exists(png):
        return ("main figure", "Figure " + num, "figures/Figure%s.*" % stem, "ok")
    return ("main figure", "Figure " + num, "-", "UNRESOLVED")


def main():
    si_figs, si_tables, si_img_count = si_contents()
    ms_tables = ms_contents()
    print("definitions: %d SI figures (%d image paragraphs), %d SI tables, "
          "%d main table(s)" % (len(si_figs), si_img_count, len(si_tables),
                                len(ms_tables)))
    print("  SI figures: %s" % ", ".join(sorted(si_figs)))
    print("  main tables: %s" % ", ".join(sorted(ms_tables)))

    rows, bad = [], []
    for path, label in ((MS, "manuscript"), (SI, "SI")):
        for i, section, t, _img in walk(path, label):
            for m in TOKEN.finditer(t):
                ref = m.group(0).strip()
                kind, target, where, status = resolve(ref, ms_tables,
                                                      si_figs, si_tables)
                ctx = " ".join(t[max(0, m.start() - 45):m.end() + 45].split())
                rows.append({
                    "source": label,
                    "paragraph": i,
                    "section": section[:70],
                    "reference": ref,
                    "resolves_to": target,
                    "target_kind": kind,
                    "defined_at": where,
                    "context": ctx,
                    "status": status,
                })
                if status != "ok":
                    bad.append("%s p%d: %s" % (label, i, ref))

    os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
    with open(CSV_OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "paragraph", "section",
                                           "reference", "resolves_to",
                                           "target_kind", "defined_at",
                                           "context", "status"])
        w.writeheader()
        w.writerows(rows)

    n_ms = sum(1 for r in rows if r["source"] == "manuscript")
    n_si = len(rows) - n_ms
    print("\nwrote %s" % CSV_OUT)
    print("  %d references (%d in the manuscript, %d in the SI), %d unresolved"
          % (len(rows), n_ms, n_si, len(bad)))
    for b in bad:
        print("  UNRESOLVED %s" % b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
