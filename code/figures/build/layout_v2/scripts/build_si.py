# -*- coding: utf-8 -*-
"""
build_si.py — sync the current Supplementary Information to the corrected
nearest-neighbour pair set and to the finalised five-figure set.
========================================================================

Reads  E:\\project\\work1\\20260929_si_provenance_wording\\
       Supplementary_Information_provenance_wording_20260929.docx   (read-only)

Writes <delivery>\\si\\Supplementary_Information_synced.docx
       <delivery>\\si\\SI_edit_log.csv

The source file is never modified. Every edit below is guarded: the script
asserts that the text it is about to replace is still there, in exactly one
run, before touching it, and aborts without writing if any guard fails. That
is the same discipline the manuscript build used, and it is what makes the
edit log trustworthy.

WHAT CHANGES, AND WHY
---------------------
1. The Table S6 block (SI paragraphs 18-26 and table blocks 6-10) is
   recomputed on the corrected undirected nearest-neighbour pair set
   (11,245 edges) instead of the archived `i < NN(i)` subset (7,666). The
   metric, the parameter distance, the tier rule, the random baseline and
   the ambiguity definitions are unchanged; only the pair set moves.

2. Table S10 (block 29) and its caption (paragraph 64) carry the corrected
   numbers per metric M1-M6, and the T10.1 caption gains the
   non-monotonicity caveat the corrected table makes visible (M2's
   closest-0.1% median exceeds its closest-0.1%-1% median; this was already
   true of the archived numbers and is reported as it stands).

3. The unit name is unified to "log₁₀ units" at all 20 SI occurrences, as the
   mentor requested. This is a house-style unification, not a scientific
   correction: a physical log₁₀ width is not by itself a factor-of-ten span,
   but the point here is only that the SI should use one unit word
   throughout. Each occurrence was read in context before it was changed; the
   one occurrence in the main text ("over the past decade") is a period of
   time and is not in this file.

4. Two cross-references to the nine-parameter parities are repointed from
   "Fig. 2a" to the new "Fig. S6", because that grid has left Figure 2.

5. Two new SI figures are appended: Fig. S6 (nine individual-parameter
   parity panels, moved out of main Figure 2) and Fig. S7 (full-range ECDF
   of the six paired coordinates against the random-pair baseline). Both are
   placed at 6.00 in wide, matching the seven existing SI figures, and use
   the existing "Captioned Figure" / "First Paragraph" style pair.

Read-only on the frozen project; writes only inside this delivery directory.
"""
import copy
import csv
import os
import shutil
import sys

import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_v2 as L                                          # noqa: E402

OUT = os.path.dirname(HERE)

SRC = (r"E:\project\work1\20260929_si_provenance_wording"
       r"\Supplementary_Information_provenance_wording_20260929.docx")
SI_DIR = os.path.join(OUT, "si")
DST = os.path.join(SI_DIR, "Supplementary_Information_synced.docx")
FIGDIR = os.path.join(OUT, "figures")
LOG = os.path.join(SI_DIR, "SI_edit_log.csv")

SI_FIG_WIDTH_IN = 6.00          # matches the seven existing SI figures

_T = qn("w:t")
_M = qn("m:t")

LOG_ROWS = []


def record(block, kind, target, description, before, after):
    LOG_ROWS.append(dict(block=block, kind=kind, target=target,
                         description=description, before=before, after=after))


# --------------------------------------------------------------- text access --
def ptext(p):
    """What the paragraph displays: w:t and m:t in document order."""
    return "".join((n.text or "") for n in p._p.iter() if n.tag in (_T, _M))


def wt(p):
    return "".join((n.text or "") for n in p._p.iter(_T))


def mtext(p):
    return "".join((n.text or "") for n in p._p.iter(_M))


def all_paras(container):
    """Every paragraph of a cell, including nested tables (none here)."""
    out = list(container.paragraphs)
    for t in container.tables:
        for row in t.rows:
            for c in row.cells:
                out.extend(all_paras(c))
    return out


# ------------------------------------------------------------------- editing --
def repl_run(p, old, new, where=""):
    """Replace `old` inside the ONE w:t run that contains it.

    Refuses to act when the match is absent or spans runs: a cross-run match
    would have to be spread over several rPr contexts, and the figure-1 round
    showed how quietly that goes wrong. Every target in this file was checked
    to sit inside a single run before the script was written.
    """
    hits = [r for r in p._p.iter(_T) if old in (r.text or "")]
    if len(hits) != 1:
        raise SystemExit("repl_run: %s expected 1 run containing %r, found %d"
                         % (where or ptext(p)[:40], old, len(hits)))
    r = hits[0]
    before = r.text
    r.text = r.text.replace(old, new, 1)
    return before, r.text


def repl_math(p, old, new, where=""):
    """Replace the text of the ONE m:t node equal to `old`.

    OMML is one node per symbol group here, so `n=77` is three nodes
    ("n", "=", "77") and only the value node is touched.
    """
    hits = [r for r in p._p.iter(_M) if (r.text or "") == old]
    if len(hits) != 1:
        raise SystemExit("repl_math: %s expected 1 m:t == %r, found %d"
                         % (where or ptext(p)[:40], old, len(hits)))
    hits[0].text = new
    return old, new


def set_cell(cell, text):
    """Replace a cell's whole content with `text`, in one run.

    Used where the archived cell carries an OMML p-value that must go: the
    p-value is not editable text, it is a math object, so the cell is rebuilt
    around the first run's rPr. The first run's formatting is the cell's own.
    """
    ps = cell.paragraphs
    p = ps[0]
    runs = p._p.findall(qn("w:r"))
    rpr = None
    if runs:
        rpr = runs[0].find(qn("w:rPr"))
    for child in list(p._p):
        if child.tag != qn("w:pPr"):
            p._p.remove(child)
    new_r = p._p.makeelement(qn("w:r"), {})
    if rpr is not None:
        new_r.append(copy.deepcopy(rpr))
    t = new_r.makeelement(qn("w:t"), {})
    t.text = text
    t.set(qn("xml:space"), "preserve")
    new_r.append(t)
    p._p.append(new_r)


def set_cell_text_only(cell, text):
    """Replace a cell's text when it is already a single run of plain text."""
    old = [t.text for t in cell.paragraphs[0]._p.iter(_T)]
    if len(old) != 1:
        raise SystemExit("set_cell_text_only: cell has %d runs, not 1: %r"
                         % (len(old), old))
    cell.paragraphs[0]._p.iter(_T).__next__().text = text
    return old[0], text


def swap_cell_blocks(ca, cb):
    """Swap the content (everything but pPr) of two cells.

    Needed once: on the corrected pair set the fourth and fifth ranks of the
    Table S6.4 ambiguity ranking exchange places, and the parameter column is
    OMML, so the two cells are exchanged wholesale rather than rebuilt.
    """
    pa, pb = ca.paragraphs[0]._p, cb.paragraphs[0]._p
    ka = [c for c in pa if c.tag != qn("w:pPr")]
    kb = [c for c in pb if c.tag != qn("w:pPr")]
    for c in ka:
        pa.remove(c)
    for c in kb:
        pb.remove(c)
    for c in kb:
        pa.append(c)
    for c in ka:
        pb.append(c)


# ------------------------------------------------------------------ edit map --
# Paragraph edits: (index, old, new, description). All inside one w:t run.
PARA_TEXT_EDITS = [
    (9, "decades)", "units)",
     "按导师要求统一为 log₁₀ units（原文写作 'decades'）"),
    (16, "(Fig. 2a)", "(Fig. S6)",
     "cross-reference: the nine-parameter parities have left Figure 2"),
    (19,
     "7,666 retained nearest-neighbor pairs, formed by pairing every test "
     "curve with its nearest other curve and keeping only pairs with i < j; "
     "this rule is not the set of all unique undirected edges, and samples "
     "may recur (the set contains 12,487 distinct samples, 2,497 of which "
     "appear more than once)",
     "11,245 undirected nearest-neighbor edges, formed by pairing every test "
     "curve with its nearest other curve, mapping each relation to its "
     "unordered pair and deduplicating; the corrected set covers all 15,307 "
     "test curves, and a curve may participate in more than one edge (5,859 "
     "do, the maximum being 5)",
     "Table S6 rule: the corrected dedup keeps every edge, not only i < NN(i)"),
    (23, None, None,
     "T6.4 caption: closest-1% tier size 77 -> 112 (OMML value node)"),
    (24, "0.1337", "0.1407",
     "tier prose: closest-0.5% median (pair count is an OMML node, edited "
     "separately)"),
    (24, "0.1021", "0.1041",
     "tier prose: closest-0.1% median (pair count is an OMML node, edited "
     "separately)"),
    # "in physical log10 parameter coordinates" already names the space, so the
    # unit tag is dropped rather than swapped: "(in log10 units)" after it
    # would read "physical log10 ... (in log10 units)", saying it twice.
    (48, " (unit: decades)", "",
     "按导师要求统一为 log₁₀ units：删除重复的单位标签"),
    (51, " (unit: decades)", "",
     "按导师要求统一为 log₁₀ units：删除重复的单位标签"),
    (64, "(0.200\u20130.219)", "(0.202\u20130.222)",
     "Table S10 caption: nearest-neighbour median range"),
    (64, "0.144 (M1) to 0.182 (M2)", "0.145 (M1) to 0.189 (M2)",
     "Table S10 caption: closest-1% median range"),
    (68, "0.20\u20130.21 decades;", "0.20\u20130.21 log\u2081\u2080 units;",
     "按导师要求统一为 log₁₀ units；数值本身不变"),
    (83, " (decades)", "",
     "按导师要求统一为 log₁₀ units：删除重复的单位标签"),
    (83, "before conversion to decades)", "before conversion to log\u2081\u2080 units)",
     "按导师要求统一为 log₁₀ units"),
    (83, "decades. A physical-decade width equals",
     "units. A width in physical log\u2081\u2080 units equals",
     "按导师要求统一为 log₁₀ units；名词一处保留其前面的 'physical "
     "log₁₀'，形容词一处改写"),
    (85, "decades. The MAE is computed", "units. The MAE is computed",
     "按导师要求统一为 log₁₀ units（前文已有 'in log₁₀'）"),
    (85, "(unit: decades), not on the", "(in log\u2081\u2080 units), not on the",
     "按导师要求统一为 log₁₀ units"),
    (85, "of Fig. 2a, whereas", "of Fig. S6, whereas",
     "cross-reference: nine-parameter parities"),
    (89, "decades, and a normalized width", "units, and a normalized width",
     "按导师要求统一为 log₁₀ units（前文已有 'in physical log₁₀'）"),
    (89, "range gives the corresponding physical-decade width.",
     "range gives the corresponding width in physical log\u2081\u2080 units.",
     "按导师要求统一为 log₁₀ units（形容词用法改写）"),
    (91, " (decades), formed from", ", formed from",
     "按导师要求统一为 log₁₀ units：删除重复的单位标签"),
    (91, "before conversion to decades.", "before conversion to log\u2081\u2080 units.",
     "按导师要求统一为 log₁₀ units"),
    (91, "decades, so their coverages", "units, so their coverages",
     "按导师要求统一为 log₁₀ units（前文已有 'in common physical log₁₀'）"),
    (93, "expressed in decades.", "expressed in log\u2081\u2080 units.",
     "按导师要求统一为 log₁₀ units"),
    (93, "also in decades.", "also in log\u2081\u2080 units.",
     "按导师要求统一为 log₁₀ units"),
    (94, "decades.", "units.", "按导师要求统一为 log₁₀ units（前文已有 'in physical log₁₀'）"),
    # ---- v2 targeted patch: wording and pointers -------------------------
    (18,
     "distance tiers, and all five representative collision cases.",
     "distance tiers, the two curve pairs of the main-text Fig. 3 (T6.7), and "
     "five archived supplementary collision cases (T6.6).",
     "Table S6 lead: name the new T6.7 subsection and mark the archived five "
     "cases as supplementary, so the lead cannot be read as calling them the "
     "main-figure cases"),
    (25, "T6.5. Compensation directions (",
     "T6.5. Same-sign parameter differences (",
     "T6.5 title: the table counts same-sign differences; it does not by "
     "itself establish a compensation mechanism"),
    (30, "Case D — bulk transport / recombination compensation (pair",
     "Case D — bulk transport and recombination parameter differences (pair",
     "T6.6 case D title: describe the difference pattern rather than name a "
     "mechanism"),
    (31, "Case E — paired-parameter compensation (pair",
     "Case E — paired-parameter differences (pair",
     "T6.6 case E title: same; this pair is also Fig. 3(a), see T6.7"),
]

# OMML value edits: (paragraph index, old m:t text, new m:t text, description)
PARA_MATH_EDITS = [
    (23, "77", "112", "T6.4 caption tier size"),
    (24, "38", "56", "closest-0.5% tier size"),
    (24, "8", "11", "closest-0.1% tier size"),
]

# Table cell edits: (table block, row, col, old text, new text, description)
CELL_EDITS = [
    # ---- Table S6.1 (block 6): d_J distribution -------------------------
    (6, 1, 1, "7666", "11245", "T6.1 count"),
    (6, 2, 1, "0.00395", "0.004236", "T6.1 mean"),
    (6, 3, 1, "0.00513", "0.005811", "T6.1 std"),
    (6, 4, 1, "0.00004", "0.000040", "T6.1 min"),
    (6, 5, 1, "0.00128", "0.001365", "T6.1 25%"),
    (6, 6, 1, "0.00267", "0.002862", "T6.1 50%"),
    (6, 7, 1, "0.00483", "0.005165", "T6.1 75%"),
    (6, 8, 1, "0.00791", "0.008278", "T6.1 90%"),
    (6, 9, 1, "0.02500", "0.026912", "T6.1 99%"),
    (6, 10, 1, "0.11523", "0.173429", "T6.1 max"),
    # ---- Table S6.2 (block 7): d_Theta distribution ---------------------
    (7, 1, 1, "7666", "11245", "T6.2 count"),
    (7, 2, 1, "0.2089", "0.210959", "T6.2 mean"),
    (7, 3, 1, "0.0841", "0.084251", "T6.2 std"),
    (7, 4, 1, "0.0330", "0.019512", "T6.2 min"),
    (7, 5, 1, "0.1464", "0.147911", "T6.2 25%"),
    (7, 6, 1, "0.1999", "0.202068", "T6.2 50%"),
    (7, 7, 1, "0.2636", "0.266259", "T6.2 75%"),
    (7, 8, 1, "0.3218", "0.324668", "T6.2 90%"),
    (7, 9, 1, "0.4329", "0.434120", "T6.2 99%"),
    (7, 10, 1, "0.6053", "0.617473", "T6.2 max"),
    # ---- Table S6.3 (block 8): coupling --------------------------------
    # (rows 1 and 2 carry OMML p-values and are rebuilt -- see CELL_REBUILD)
    (8, 4, 1, "0.200", "0.202", "T6.3 nearest-neighbour dTheta median"),
    (8, 6, 1, "0.00267", "0.00286", "T6.3 nearest-neighbour dJ median"),
    # ---- Table S6.4 (block 9): closest-1% ambiguity ranking -------------
    (9, 1, 2, "0.1536", "0.1567", "T6.4 rank 1 tau_ETL median"),
    (9, 1, 3, "0.1773", "0.1761", "T6.4 rank 1 mean"),
    (9, 1, 4, "0.3714", "0.3700", "T6.4 rank 1 p90"),
    (9, 2, 2, "0.1177", "0.1154", "T6.4 rank 2 mu_n median"),
    (9, 2, 3, "0.1289", "0.1313", "T6.4 rank 2 mean"),
    (9, 2, 4, "0.2458", "0.2603", "T6.4 rank 2 p90"),
    (9, 3, 2, "0.1011", "0.1060", "T6.4 rank 3 tau_HTL median"),
    (9, 3, 3, "0.1244", "0.1320", "T6.4 rank 3 mean"),
    (9, 3, 4, "0.2803", "0.3016", "T6.4 rank 3 p90"),
    (9, 4, 2, "0.1006", "0.0916", "T6.4 rank 4 (now rrad) median"),
    (9, 4, 3, "0.1255", "0.1472", "T6.4 rank 4 mean"),
    (9, 4, 4, "0.2759", "0.3575", "T6.4 rank 4 p90"),
    (9, 5, 2, "0.0885", "0.0913", "T6.4 rank 5 (now tau_n) median"),
    (9, 5, 3, "0.1453", "0.1216", "T6.4 rank 5 mean"),
    (9, 5, 4, "0.3668", "0.2939", "T6.4 rank 5 p90"),
    (9, 6, 2, "0.0866", "0.0866", "T6.4 rank 6 tau_p median (unchanged)"),
    (9, 6, 3, "0.1246", "0.1218", "T6.4 rank 6 mean"),
    (9, 6, 4, "0.2655", "0.2656", "T6.4 rank 6 p90"),
    (9, 7, 2, "0.0727", "0.0712", "T6.4 rank 7 mu_p median"),
    (9, 7, 3, "0.0953", "0.0960", "T6.4 rank 7 mean"),
    (9, 7, 4, "0.2066", "0.2228", "T6.4 rank 7 p90"),
    (9, 8, 2, "0.0596", "0.0584", "T6.4 rank 8 Nv median"),
    (9, 8, 3, "0.0845", "0.0810", "T6.4 rank 8 mean"),
    (9, 8, 4, "0.1874", "0.1862", "T6.4 rank 8 p90"),
    (9, 9, 2, "0.0520", "0.0500", "T6.4 rank 9 Nc median"),
    (9, 9, 3, "0.0680", "0.0663", "T6.4 rank 9 mean"),
    (9, 9, 4, "0.1512", "0.1485", "T6.4 rank 9 p90"),
    # ---- Table S6.5 (block 10): compensation directions -----------------
    (10, 1, 1, "0.62", "0.72", "T6.5 mu_n vs mu_p"),
    (10, 2, 1, "0.88", "0.87", "T6.5 tau_n vs tau_p"),
    (10, 3, 1, "0.50", "0.60", "T6.5 Nc vs Nv"),
    (10, 4, 1, "0.25", "0.51", "T6.5 tau_n vs tau_ETL"),
    (10, 5, 1, "0.25", "0.46", "T6.5 tau_n vs tau_HTL"),
    (10, 6, 1, "0.38", "0.46", "T6.5 rrad vs tau_n"),
    (10, 7, 1, "0.25", "0.42", "T6.5 rrad vs tau_ETL"),
    # ---- Table S10 (block 29) -------------------------------------------
    (29, 1, 1, "7666", "11245", "T10.1 M1 pairs"),
    (29, 1, 2, "0.1999", "0.2021", "T10.1 M1 all-NN median"),
    (29, 1, 4, "0.1443", "0.1452", "T10.1 M1 closest 1%"),
    (29, 1, 5, "0.1337", "0.1407", "T10.1 M1 closest 0.5%"),
    (29, 1, 6, "0.1021", "0.1041", "T10.1 M1 closest 0.1%"),
    (29, 1, 7, "0.158", "0.154", "T10.1 M1 Spearman"),
    (29, 2, 1, "7635", "11060", "T10.1 M2 pairs"),
    (29, 2, 2, "0.2165", "0.2194", "T10.1 M2 all-NN median"),
    (29, 2, 4, "0.1816", "0.1885", "T10.1 M2 closest 1%"),
    (29, 2, 5, "0.1855", "0.1812", "T10.1 M2 closest 0.5%"),
    (29, 2, 6, "0.1898", "0.2125", "T10.1 M2 closest 0.1%"),
    (29, 2, 7, "0.084", "0.082", "T10.1 M2 Spearman"),
    (29, 3, 1, "7638", "11104", "T10.1 M3 pairs"),
    (29, 3, 2, "0.2164", "0.2191", "T10.1 M3 all-NN median"),
    (29, 3, 4, "0.1679", "0.1808", "T10.1 M3 closest 1%"),
    (29, 3, 6, "0.1506", "0.1502", "T10.1 M3 closest 0.1%"),
    (29, 3, 7, "0.098", "0.092", "T10.1 M3 Spearman"),
    (29, 4, 1, "7666", "11208", "T10.1 M4 pairs"),
    (29, 4, 2, "0.2072", "0.2092", "T10.1 M4 all-NN median"),
    (29, 4, 4, "0.1520", "0.1509", "T10.1 M4 closest 1%"),
    (29, 4, 5, "0.1505", "0.1532", "T10.1 M4 closest 0.5%"),
    (29, 4, 6, "0.1263", "0.1133", "T10.1 M4 closest 0.1%"),
    (29, 4, 7, "0.148", "0.142", "T10.1 M4 Spearman"),
    (29, 5, 1, "7670", "11212", "T10.1 M5 pairs"),
    (29, 5, 2, "0.2073", "0.2094", "T10.1 M5 all-NN median"),
    (29, 5, 4, "0.1520", "0.1509", "T10.1 M5 closest 1%"),
    (29, 5, 5, "0.1505", "0.1532", "T10.1 M5 closest 0.5%"),
    (29, 5, 6, "0.1263", "0.1133", "T10.1 M5 closest 0.1%"),
    (29, 5, 7, "0.183", "0.170", "T10.1 M5 Spearman"),
    (29, 6, 1, "7691", "11036", "T10.1 M6 pairs"),
    (29, 6, 2, "0.2190", "0.2220", "T10.1 M6 all-NN median"),
    (29, 6, 4, "0.1686", "0.1838", "T10.1 M6 closest 1%"),
    (29, 6, 5, "0.1592", "0.1589", "T10.1 M6 closest 0.5%"),
    (29, 6, 6, "0.1633", "0.1595", "T10.1 M6 closest 0.1%"),
    # ---- Table S10 tiers, M1 only (block 30) ----------------------------
    (30, 1, 1, "767", "1124", "T10.2 closest 10% pairs"),
    (30, 1, 2, "0.000420", "0.000447", "T10.2 closest 10% median dJ"),
    (30, 1, 3, "0.1683", "0.1729", "T10.2 closest 10% median dTheta"),
    (30, 2, 1, "383", "562", "T10.2 closest 5% pairs"),
    (30, 2, 2, "0.000291", "0.000320", "T10.2 closest 5% median dJ"),
    (30, 2, 3, "0.1554", "0.1665", "T10.2 closest 5% median dTheta"),
    (30, 3, 1, "77", "112", "T10.2 closest 1% pairs"),
    (30, 3, 2, "0.000153", "0.000171", "T10.2 closest 1% median dJ"),
    (30, 3, 3, "0.1443", "0.1452", "T10.2 closest 1% median dTheta"),
    (30, 4, 1, "38", "56", "T10.2 closest 0.5% pairs"),
    (30, 4, 2, "0.000118", "0.000133", "T10.2 closest 0.5% median dJ"),
    (30, 4, 3, "0.1337", "0.1407", "T10.2 closest 0.5% median dTheta"),
    (30, 5, 1, "8", "11", "T10.2 closest 0.1% pairs"),
    (30, 5, 2, "0.000079", "0.000090", "T10.2 closest 0.1% median dJ"),
    (30, 5, 3, "0.1021", "0.1041", "T10.2 closest 0.1% median dTheta"),
    (30, 6, 1, "7666", "11245", "T10.2 all NN pairs"),
    (30, 6, 2, "0.002668", "0.002862", "T10.2 all NN median dJ"),
    (30, 6, 3, "0.1999", "0.2021", "T10.2 all NN median dTheta"),
    # ---- table headers carrying the unit name ---------------------------
    (27, 0, 6, " decades)", " units)",
     "按导师要求统一为 log₁₀ units：T8.2b 表头"),
    (31, 0, 2, "Median absolute log-error (decades)",
     "Median absolute log-error (log\u2081\u2080 units)",
     "按导师要求统一为 log₁₀ units：T11.1 表头"),
    (38, 0, 3, "Interval width (dec)",
     "Interval width (log\u2081\u2080 units)",
     "Table S17b header: the same unit name, abbreviated rather than "
     "spelled out; its own caption two paragraphs above already says "
     "'physical log10 units'"),
]

# Cells rebuilt from scratch (the archived value carries an OMML p-value)
CELL_REBUILD = [
    (8, 1, 1, "0.158", "0.154",
     "T6.3 Spearman: value corrected and the OMML p-value withdrawn"),
    (8, 2, 1, "0.079", "0.073",
     "T6.3 Pearson: value corrected and the OMML p-value withdrawn"),
]

# Column rebalances: (table block, [six/five/... gridCol widths], description).
# The widths are proportions, not absolutes -- the table style is tblW="auto"
# and the grid sums to 7920 twips, exactly as every other table in this file, so
# the rendered total width is unchanged and only the share of each column moves.
GRID_EDITS = [
    # Table S5, last header cell: "Recoverability" + an inline OMML r. At the
    # original uniform 1320 twips the column offered 55.2 pt of content box and
    # Word broke the word mid-way as "Recoverabilit / y" (the word alone needs
    # 70.6 pt at 12 pt Times New Roman). The width comes from the two equation
    # columns, whose headers are OMML symbols about 18 pt wide and whose data
    # are 6-character numbers (36 pt); they keep 45.2 pt and 42.2 pt of content
    # box, which is ample. The first column goes the other way: at the narrower
    # width it would have broken "Parameter" (48.5 pt), so it is set to 53.2 pt.
    # Every other header stays on one line: "Rank (raw)" 54.1 pt against 55.2,
    # "Rank (log)" 51.6 pt against 54.2, "Recoverability r" 77.9 pt against
    # 81.2. Values and formatting untouched.
    (5, [1280, 1120, 1060, 1320, 1300, 1840],
     "Table S5 header: 'Recoverability r' was broken mid-word as "
     "'Recoverabilit / y' at the uniform 1320-twip grid (55.2 pt of content "
     "box for a 70.6 pt word). 440 twips move from the two equation columns "
     "to the last one, and 280 more to the parameter column so that "
     "'Parameter' cannot break instead; the grid still sums to 7920. Values "
     "untouched."),
]

# The one structural change inside a table: ranks 4 and 5 exchange artists
SWAP_CELLS = [(9, 4, 1, 9, 5, 1,
               "T6.4: on the corrected set rrad ranks 4 and tau_n ranks 5 "
               "(the parameter cells are OMML, so they are exchanged whole)")]

# Paragraphs whose text is appended to (not replaced)
APPEND_EDITS = [
    (26,
     " These five cases are archived supplementary cases. They are not the "
     "pairs drawn in the main-text Fig. 3, which are tabulated separately in "
     "T6.7; case E happens to be the same pair as Fig. 3(a) and is given "
     "there in physical units.",
     "T6.6 lead: mark the archived five as supplementary so they are not read "
     "as the main-figure cases"),
    (65,
     " The distance-tier medians are reported as they stand. They do not "
     "fall monotonically with tier tightness for every metric: under M2 the "
     "closest-0.1% median (0.2125) exceeds the closest-1% median (0.1885). "
     "No monotone trend is assumed and no value is adjusted to produce one.",
     "T10.1 caption: the corrected table makes a non-monotonicity visible "
     "that the archived numbers also had; the text must not imply otherwise"),
]

# New SI figures: (stem, figure number, caption as (text, subscript) parts)
#
# S6's caption names nine parameter symbols, six of which take a subscript.
# Four of those subscripts cannot be spelled with Unicode subscript glyphs at
# all (there is no subscript c, no subscript capital, no subscript d), and a
# caption that mixes Unicode subscripts with flat letters -- "mu_n/mu_p" next
# to "Nc/Nv" -- reads as two different conventions in the same parenthesis. So
# every symbol in the caption is set the way the SI's own table headers set
# theirs: an ordinary run plus a run carrying w:vertAlign val="subscript".
# Plain runs are whole phrases, so a text search still finds the sentence.
S6_CAP = [
    ("Figure S6. Predicted versus true values of the nine individual "
     "parameters on the 15,307-curve test set, in the min\u2013max-normalized "
     "log\u2081\u2080 coordinates of the frozen scaler. Each panel is one "
     "parameter; the dashed line is the identity and \u03c1 is the Pearson "
     "correlation, annotated in every panel. These are the single-parameter "
     "parities that the coordinate analysis of Fig. 2 and Table S11 "
     "aggregates into shared-scale and log-ratio coordinates: the three bulk "
     "pairs (\u03bc", 0),
    ("n", 1), ("/\u03bc", 0), ("p", 1),
    (", \u03c4", 0), ("n", 1), ("/\u03c4", 0), ("p", 1),
    (", N", 0), ("c", 1), ("/N", 0), ("v", 1),
    (") and the three directly sampled parameters (\u03c4", 0),
    ("ETL", 1), (", \u03c4", 0), ("HTL", 1), (", r", 0), ("rad", 1),
    ("). The values are the frozen evaluation arrays of the main model and "
     "are not recomputed here; the per-parameter Pearson correlations agree "
     "with those reported for the original test set in Table S14.", 0),
]

S7_CAP = [
    ("Figure S7. Empirical cumulative distributions of the six paired "
     "coordinates over the corrected undirected nearest-neighbour pair set "
     "(11,245 pairs) and over the random-pair baseline (199,985 pairs, seed "
     "42). One panel per coordinate: the shared scale a and the electron\u2013"
     "hole log-ratio r for mobility, bulk lifetime and density of states; "
     "blue is the shared scale, orange the log-ratio and grey the random "
     "pairs. The x axis is the absolute coordinate difference divided by the "
     "median absolute difference of the same coordinate among random pairs, "
     "so the dotted line at one is the random-pair median. Every value of "
     "both sets is plotted, without truncation and without dropped points, "
     "and each panel spans the full range of its own two groups. The "
     "comparison is descriptive.", 0),
]

SI_FIGURES = [("FigureS6_nineparam", "Figure S6", S6_CAP),
              ("FigureS7_ecdf", "Figure S7", S7_CAP)]


# ==========================================================================
# v2 targeted patch: the new Table S6 subsections T6.7-T6.9
# ==========================================================================
# They are inserted immediately after the archived case-E table, so they sit
# inside the S6 block that the manuscript cites. Numbering continues the
# block's own T6.1-T6.6 scheme.
#
# Every number below is taken from si_table_s6_new.tables(), which recomputes
# them from the frozen arrays and asserts them against the tables the figure
# round already delivered -- nothing here is transcribed by hand.

S6_T67_LEAD = (
    "T6.7. The two curve pairs drawn in the main-text Fig. 3, in physical "
    "values. Case (a): zero-based test indices 2890 / 5067, database Sample_ID "
    "141475 / 71905. Case (b): zero-based test indices 500 / 4560, Sample_ID "
    "37892 / 87198. The indices are positions in the frozen test array; the "
    "Sample_ID values identify the same two curves in the source database. The "
    "two tables per case give the nine parameters in physical units and the "
    "six paired coordinates in physical log₁₀ units, where the "
    "shared scale a = (log₁₀θₙ + log₁₀"
    "θₚ)/2 is the logarithm of the geometric mean of the two carrier "
    "parameters of a family and r = log₁₀(θₙ/θₚ) "
    "is their difference in log₁₀. The per-parameter difference in the two "
    "parameter tables is the absolute difference of the two physical "
    "log₁₀ values, |Δlog₁₀θ| = |log₁₀θᵢ − log₁₀θⱼ| = |log₁₀(θᵢ/θⱼ)|, and the "
    "factor column is 10^|Δlog₁₀θ|, that is the larger of the two physical "
    "values divided by the smaller. No factor in this subsection is formed "
    "from baseline-normalized or otherwise rescaled parameter differences. "
    "The same values at full source "
    "precision are in si_table_s6_7_figure_cases.csv and "
    "si_table_s6_7_figure_case_coordinates.csv."
)

S6_T67_RULE = (
    "Selection rule, applied to the corrected undirected pair set. Restrict "
    "to the closest 1%% of pairs by ascending d_J (n = %(tier)d of "
    "%(total)s pairs); take the pair with the largest absolute mobility "
    "log-ratio difference |Δr| as case (a); then, from the same tier with "
    "case (a)'s pair removed, take the pair with the largest absolute "
    "bulk-lifetime log-ratio difference |Δr| as case (b). The measured "
    "values are |Δr| = %(a).6f for case (a) and |Δr| = %(b).6f for "
    "case (b). Both picks are also the largest in the same tier when the "
    "coordinate is normalized by its random-pair baseline (T6.9), because "
    "dividing a coordinate by one fixed positive constant does not change the "
    "ordering. Ties would be broken by position in the tier ordering, that is "
    "by smaller d_J first. The tier restriction is load-bearing: the "
    "largest |Δr| for mobility over all %(total)s corrected pairs is "
    "%(gm).6f and belongs to pair %(gp)s, which is not drawn in Fig. 3."
)

S6_T67_COORD_LEAD = (
    "T6.7%(sub)s. Paired coordinates of case %(tag)s in physical "
    "log₁₀ units. The last column divides |Δ| by the "
    "random-pair median of the same coordinate (T6.9). Differences of "
    "log₁₀ values do not depend on the unit basis of the parameters, "
    "so only the absolute values of a do."
)

S6_T68_LEAD = (
    "T6.8. Distance-tier comparison of the six paired coordinates. Columns "
    "after the first give all corrected undirected pairs and then the closest "
    "10%%, 5%%, 1%%, 0.5%% and 0.1%% of those pairs, taken in ascending "
    "d_J. Column headers give the tier as the fraction of all corrected pairs "
    "it holds. The tier sizes are %(sizes)s pairs, so the three smallest sets "
    "hold 112, 56 and 11 pairs and their medians are correspondingly less "
    "stable. \"Pairs\" counts the curve pairs in a set and \"Distinct curves\" "
    "the test curves that appear in it; values are absolute coordinate "
    "differences divided by the "
    "random-pair median of the same coordinate (T6.9), so one is the "
    "random-pair level. The interquartile range describes the spread of the "
    "paired differences within the set and is not a confidence interval; pairs "
    "share test curves, so they are not independent observations, and no "
    "p-value is reported for any set. Dividing a coordinate by a fixed "
    "positive baseline changes the scale of the numbers but not their "
    "ordering, so the raw differences rank the sets in the same order. A "
    "median close to the random-pair level is reported as a value, and nothing "
    "further is inferred from it."
)

S6_T69_LEAD = (
    "T6.9. Random-pair baselines of the six paired coordinates. Each value is "
    "the median absolute difference of that coordinate over the random-pair "
    "baseline used throughout this work: 200,000 ordered index pairs drawn "
    "uniformly from the 15,307 test curves with numpy.random.default_rng(42), "
    "self-pairs dropped, 199,985 retained. These six constants normalize the "
    "coordinate differences in T6.7 and T6.8, in Fig. 3c and in Fig. S7. "
    "Differences of physical log₁₀ values are independent of the "
    "unit basis of the underlying parameters, so the baselines are too."
)

S6_T68_SUB = {"mobility": "T6.8a. Mobility coordinates.",
              "lifetime": "T6.8b. Bulk-lifetime coordinates.",
              "DOS": "T6.8c. Density-of-states coordinates."}

# gridCol widths in twips. Every table in this SI is 7920 twips wide, which is
# what the neighbouring S6 tables use (gridCols summing to 7920, tblW auto).
G_T67_PARAM = [1200, 1560, 1350, 1350, 1230, 1230]
G_T67_COORD = [1000, 2610, 1120, 1120, 1040, 1030]
G_T68_TIER = [1900, 1004, 1004, 1004, 1004, 1004, 1000]
G_T69_BASE = [1900, 4300, 1720]
# the tier table's column headers; the lead names the sets in full
TIER_COLS = ["all", "10%", "5%", "1%", "0.5%", "0.1%"]

# the two parameter symbols of each coordinate family, as (symbol, subscript)
COORD_SYMS = {"mobility": ("μ", "n", "μ", "p"),
              "lifetime": ("τ", "n", "τ", "p"),
              "DOS": ("N", "c", "N", "v")}


def _num(v, n=4):
    """Four significant digits, in the 'e' notation where that reads best."""
    v = float(v)
    a = abs(v)
    if a == 0.0:
        return "0"
    if 1e-3 <= a < 1e5:
        d = max(0, n - 1 - int(np.floor(np.log10(a))))
        return "%.*f" % (d, v)
    m, e = ("%.*e" % (n - 1, v)).split("e")
    return "%se%d" % (m, int(e))


def _factor(v):
    return ("%.2f" % v) if v < 10.0 else ("%.1f" % v)


def _rng(lo, hi):
    return "%.3f–%.3f" % (lo, hi)


def _p(doc, text):
    """A new body paragraph in the SI's own body style."""
    return doc.add_paragraph(text, style="Body Text")


def _coord_defn(fam, axis, symbol):
    """Parts for one coordinate definition.

    symbol=True gives the full statement used in the T6.9 baseline table
    ("a = (log10 mu_n + log10 mu_p) / 2"); symbol=False gives the form used in
    the T6.7 coordinate table, where the row already names the coordinate.
    """
    s1, b1, s2, b2 = COORD_SYMS[fam]
    if axis == "a":
        if symbol:
            return [("a = (log", ""), ("10", "sub"), (" ", ""), (s1, ""),
                    (b1, "sub"), (" + log", ""), ("10", "sub"), (" ", ""),
                    (s2, ""), (b2, "sub"), (") / 2", "")]
        return [("½(log", ""), ("10", "sub"), (" ", ""), (s1, ""),
                (b1, "sub"), (" + log", ""), ("10", "sub"), (" ", ""),
                (s2, ""), (b2, "sub"), (")", "")]
    if symbol:
        return [("r = log", ""), ("10", "sub"), (" (", ""), (s1, ""),
                (b1, "sub"), (" / ", ""), (s2, ""), (b2, "sub"), (")", "")]
    return [("log", ""), ("10", "sub"), (" (", ""), (s1, ""), (b1, "sub"),
            (" / ", ""), (s2, ""), (b2, "sub"), (")", "")]


def _cell(doc, cell, parts):
    """Fill one cell: parts is [(text, flag)] with flag '', 'sub' or 'sup'.

    A bare (text, flag) pair is accepted too, so a header row can be written
    as a plain tuple list without a second layer of brackets.
    """
    if isinstance(parts, tuple):
        parts = [parts]
    p = cell.paragraphs[0]
    p.style = doc.styles["Compact"]
    for text, flag in parts:
        r = p.add_run(text)
        if flag == "sub":
            r.font.subscript = True
        elif flag == "sup":
            r.font.superscript = True


def _new_table(doc, widths, rows_parts):
    """A full-width table in the SI's own 'Table' style, header row repeating."""
    t = doc.add_table(rows=len(rows_parts), cols=len(widths))
    t.style = doc.styles["Table"]
    grid = t._tbl.find(qn("w:tblGrid"))
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "on")
    trpr.append(th)
    for ri, row in enumerate(rows_parts):
        for ci, parts in enumerate(row):
            _cell(doc, t.rows[ri].cells[ci], parts)
    return t


def new_s6_elements(doc):
    """Build the T6.7-T6.9 paragraphs and eight tables, in reading order.

    Returns an ordered list of (kind, element, label): eleven paragraphs and
    eight tables. The caller inserts them after the archived case-E table and
    writes one log row per element. Every number comes from
    si_table_s6_new.tables(), which recomputes it from the frozen arrays and
    asserts it against the tables the figure round already delivered.
    """
    import si_table_s6_new as S6

    T = S6.tables()
    info, rb, tiers = T["info"], T["rb"], T["tiers"]
    out = []

    def para(text, label):
        out.append(("p", _p(doc, text), label))

    def table(widths, rows, label):
        out.append(("t", _new_table(doc, widths, rows), label))

    # -------------------------------------------------- T6.7 lead and rule
    para(S6_T67_LEAD, "T6.7 lead")
    para(S6_T67_RULE % dict(tier=info["tier_pairs"],
                            total="{:,}".format(info["n_pairs"]),
                            a=info["absd_r_mu"], b=info["absd_r_tau"],
                            gm=info["global_absd_r_mu"],
                            gp="%d / %d" % info["global_pair"]),
         "T6.7 selection rule")

    # ------------------------------------------------------------- two cases
    for k, ((tag, i, j, _why), (params, s, coords)) in enumerate(
            zip(L.CASES, T["cases"])):
        p_sub, c_sub = ("a", "b") if k == 0 else ("c", "d")
        para(
            "Case %s. Test indices %d / %d (zero-based positions in the frozen "
            "test array); database Sample_ID %d / %d. T6.7%s lists the nine "
            "parameters with their units and both members' physical values; "
            "T6.7%s gives the six paired coordinates. The last column of "
            "T6.7%s is the multiplicative factor 10^|Δlog₁₀"
            "θ|, which equals the larger of the two values divided by the "
            "smaller. Curve distance: normalized RMSE d_J = %s over the 131 "
            "voltage points; physical J–V RMSE = %.3f mA cm⁻²; "
            "maximum |ΔJ| = %.3f mA cm⁻² at V = %.2f V, with "
            "ΔJ = J_j − J_i."
            % (tag, i, j, s["sample_id_i"], s["sample_id_j"], p_sub, c_sub,
               p_sub, _num(s["dJ_rmse_normalized"]),
               s["physical_rmse_mA_cm2"], s["max_abs_dJ_mA_cm2"],
               s["max_abs_dJ_at_V"]),
            "T6.7 case %s lead" % tag)

        rows = [[("Parameter", ""), ("Unit", ""), ("Index %d" % i, ""),
                 ("Index %d" % j, ""), ("|Δlog₁₀θ|", ""),
                 ("Factor", "")]]
        for p in params:
            rows.append([S6.PARAM_LABEL_PARTS[p["parameter"]],
                         [(p["unit"], "")],
                         [(_num(p["theta_i"]), "")],
                         [(_num(p["theta_j"]), "")],
                         [("%.3f" % p["abs_dlog10"], "")],
                         [(_factor(p["factor"]), "")]])
        table(G_T67_PARAM, rows, "T6.7%s case %s parameters" % (p_sub, tag))

        para(S6_T67_COORD_LEAD % dict(sub=c_sub, tag=tag),
             "T6.7%s coordinate lead" % c_sub)
        rows = [[("Coordinate", ""), ("Definition", ""), ("Index %d" % i, ""),
                 ("Index %d" % j, ""), ("|Δ|", ""),
                 ("|Δ| / baseline", "")]]
        for c in coords:
            axis = "a" if c["coordinate"].startswith("a") else "r"
            rows.append([[(axis, "")],
                         _coord_defn(S6.COORD_FAMILY[c["coordinate"]], axis,
                                     False),
                         [("%+.3f" % c["value_i"], "")],
                         [("%+.3f" % c["value_j"], "")],
                         [("%.3f" % c["absd"], "")],
                         [("%.3f" % (c["absd"] / rb[c["coordinate"]]), "")]])
        table(G_T67_COORD, rows, "T6.7%s case %s coordinates" % (c_sub, tag))

    # ---------------------------------------------------------------- T6.8
    para(S6_T68_LEAD % dict(sizes=", ".join(
        "{:,}".format(int(v)) for v in tiers["n_pairs"])), "T6.8 lead")

    for fam, fam_label, a_id, r_id in S6.FAMILY_TABLES:
        para(S6_T68_SUB[fam], "T6.8 sub-lead: %s" % fam_label)
        rows = [[("Statistic", "")] + [(lab, "") for lab in TIER_COLS]]
        rows.append([("Pairs", "")] +
                    [("{:,}".format(int(v)), "") for v in tiers["n_pairs"]])
        rows.append([("Distinct curves", "")] +
                    [("{:,}".format(int(v)), "") for v in
                     tiers["distinct_samples"]])
        for word, cid in (("median", a_id), ("IQR", a_id),
                          ("median", r_id), ("IQR", r_id)):
            axis = "a" if cid.startswith("a") else "r"
            lab = [(word, ""), (" |Δ", ""), (axis, ""), ("| / b", ""),
                   (axis, "sub")]
            vals = []
            for n in range(len(S6.TIER_LABELS)):
                if word == "median":
                    vals.append([("%.3f" % tiers["med_" + cid].iloc[n], "")])
                else:
                    vals.append([(_rng(tiers["q25_" + cid].iloc[n],
                                       tiers["q75_" + cid].iloc[n]), "")])
            rows.append([lab] + vals)
        table(G_T68_TIER, rows, "T6.8 table: %s" % fam_label)

    # ---------------------------------------------------------------- T6.9
    para(S6_T69_LEAD, "T6.9 lead")
    rows = [[("Coordinate", ""),
             ("Definition in physical log₁₀ values", ""),
             ("Random-pair median |Δ|", "")]]
    for cid, fam, fam_label, _ratio in S6.COORD_ROWS:
        axis = "a" if cid.startswith("a") else "r"
        rows.append([[("%s, %s" % (axis, fam_label), "")],
                     _coord_defn(fam, axis, True),
                     [("%.4f" % rb[cid], "")]])
    table(G_T69_BASE, rows, "T6.9 baselines")

    return out


def add_caption(p, parts):
    """One run per part; a part flagged 1 becomes a real subscript run."""
    for text, sub in parts:
        r = p.add_run(text)
        if sub:
            r.font.subscript = True
    return "".join(t for t, _ in parts)


def apply_grid_edits(doc):
    """Column rebalances, applied and logged (values never touched)."""
    for ti, widths, desc in GRID_EDITS:
        cols = doc.tables[ti]._tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))
        before = ",".join(c.get(qn("w:w")) for c in cols)
        for c, w in zip(cols, widths):
            c.set(qn("w:w"), str(w))
        after = ",".join(c.get(qn("w:w")) for c in cols)
        record("table %d" % ti, "grid", "gridCol", desc, before, after)
        print("T%-3d grid  %s -> %s" % (ti, before, after))


def _para_text(el):
    return "".join(n.text or "" for n in el.iter(qn("w:t"))).strip()


def insert_new_s6(doc):
    """Place the T6.7-T6.9 paragraphs and tables at the end of the S6 block.

    The elements were built at the end of the body (that is what add_paragraph
    and add_table do); each is then moved, in order, in front of one anchor
    element. Building them all first and moving them afterwards keeps the
    document order exactly as new_s6_elements returned it.

    The anchor has to be the *end* of S6, i.e. the blank paragraph that closes
    the block just before "Table S7.". An earlier revision of this function
    anchored on `doc.tables[15]`, which is case E's **value** table rather than
    the last element of the block: the new subsections were then spliced in
    between case E's lead paragraph and its own table, and that table was left
    stranded on the far side of T6.9 -- it rendered caption-less on the T6.9
    page. The anchor is now found by text so the failure cannot recur, and the
    case-E lead/table pair is asserted to be adjacent afterwards.
    """
    root = doc.element.body
    ref = None
    for ch in root.iterchildren():
        if ch.tag != qn("w:p") or _para_text(ch)[:9] != "Table S7.":
            continue
        prev = ch.getprevious()
        # keep the blank separator line with the S7 block, so the new material
        # ends flush against case E's table rather than after a stray blank
        if (prev is not None and prev.tag == qn("w:p")
                and _para_text(prev) == ""):
            ref = prev
        else:
            ref = ch
        break
    if ref is None:
        raise SystemExit("cannot find the 'Table S7.' paragraph that closes "
                         "the S6 block; refusing to guess where the new S6 "
                         "subsections belong")
    els = new_s6_elements(doc)
    for kind, el, label in els:
        node = el._tbl if kind == "t" else el._p
        # ref is deliberately NOT advanced: every element is placed
        # immediately before the case-E table, so successive insertions land
        # in reading order. Advancing ref would reverse the whole block.
        ref.addprevious(node)
        if kind == "t":
            body = "table %dx%d, grid %s" % (
                len(el.rows), len(el.columns),
                ",".join(c.get(qn("w:w")) for c in
                         el._tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))))
        else:
            body = el.text
        record("S6 (new)", "insert-" + ("table" if kind == "t" else "para"),
               label, label, "", body)
        print("+ S6  %-38s %s" % (label, body[:60]))

    # the case-E lead paragraph must still be followed by case E's own table:
    # the previous anchor put 19 elements in between them.
    kids = list(root.iterchildren())
    for n, ch in enumerate(kids):
        if ch.tag != qn("w:p") or not _para_text(ch).startswith("Case E "):
            continue
        nxt = kids[n + 1] if n + 1 < len(kids) else None
        if nxt is None or nxt.tag != qn("w:tbl"):
            raise SystemExit("case E's lead paragraph is no longer followed by "
                             "its value table; the S6 insertion split them")
        break
    return len(els)


def main():
    if not os.path.exists(SRC):
        raise SystemExit("source SI not found: %s" % SRC)
    os.makedirs(SI_DIR, exist_ok=True)

    doc = Document(SRC)
    n_para0 = len(doc.paragraphs)
    n_tab0 = len(doc.tables)
    n_s6_base = len(doc.tables)
    print("source: %s" % SRC)
    print("        %d paragraphs, %d tables" % (n_para0, n_tab0))

    # ---------------------------------------------------------- guards -------
    # Every replacement's `old` must be present before anything is written.
    for idx, old, new, desc in PARA_TEXT_EDITS:
        if old is None:
            continue
        p = doc.paragraphs[idx]
        if old not in wt(p):
            raise SystemExit("guard failed: [%03d] does not contain %r"
                             % (idx, old[:60]))
    for idx, old, new, desc in PARA_MATH_EDITS:
        if old not in mtext(doc.paragraphs[idx]):
            raise SystemExit("guard failed: [%03d] has no m:t %r" % (idx, old))
    for ti, ri, ci, old, new, desc in CELL_EDITS:
        t = doc.tables[ti].rows[ri].cells[ci]
        if old not in wt(t.paragraphs[0]):
            raise SystemExit("guard failed: T%d r%d c%d has no %r (has %r)"
                             % (ti, ri, ci, old, wt(t.paragraphs[0])[:40]))
    for ti, ri, ci, old, new, desc in CELL_REBUILD:
        t = doc.tables[ti].rows[ri].cells[ci]
        if not wt(t.paragraphs[0]).startswith(old):
            raise SystemExit("guard failed: T%d r%d c%d has %r, expected %r"
                             % (ti, ri, ci, wt(t.paragraphs[0])[:30], old))
    for ti, widths, desc in GRID_EDITS:
        cols = doc.tables[ti]._tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))
        if len(cols) != len(widths):
            raise SystemExit("guard failed: table %d has %d gridCols, the "
                             "rebalance names %d" % (ti, len(cols), len(widths)))
        have = sum(int(c.get(qn("w:w"))) for c in cols)
        if have != sum(widths):
            raise SystemExit("guard failed: table %d grid sums to %d, the "
                             "rebalance sums to %d" % (ti, have, sum(widths)))
    print("guards: all %d targets present" %
          (len([e for e in PARA_TEXT_EDITS if e[1]]) + len(PARA_MATH_EDITS)
           + len(CELL_EDITS) + len(CELL_REBUILD) + len(GRID_EDITS)))

    # ---------------------------------------------------------- apply --------
    for idx, old, new, desc in PARA_TEXT_EDITS:
        if old is None:
            # recorded separately under PARA_MATH_EDITS
            continue
        p = doc.paragraphs[idx]
        b, a = repl_run(p, old, new, "[%03d]" % idx)
        record("para %d" % idx, "text", "run", desc, b, a)
        print("[%03d] text  %s" % (idx, desc[:70]))

    for idx, old, new, desc in PARA_MATH_EDITS:
        repl_math(doc.paragraphs[idx], old, new, "[%03d]" % idx)
        record("para %d" % idx, "math", "m:t", desc, old, new)
        print("[%03d] math  %s" % (idx, desc[:70]))

    for ti, ri, ci, old, new, desc in CELL_EDITS:
        cell = doc.tables[ti].rows[ri].cells[ci]
        # repl_run, not a whole-cell rewrite: the T8.2b header interleaves its
        # "log10" subscripts with plain runs, and only the last run may change.
        b, a = repl_run(cell.paragraphs[0], old, new,
                        "T%d r%d c%d" % (ti, ri, ci))
        record("table %d r%d c%d" % (ti, ri, ci), "cell", "%s -> %s"
               % (old, new), desc, old, new)
        print("T%-3d r%-2d c%-2d  %-30s %s" % (ti, ri, ci, desc[:30], new))

    for ti, ri, ci, old, new, desc in CELL_REBUILD:
        cell = doc.tables[ti].rows[ri].cells[ci]
        b = wt(cell.paragraphs[0])
        set_cell(cell, new)
        record("table %d r%d c%d" % (ti, ri, ci), "cell-rebuild",
               "cell", desc, b, new)
        print("T%-3d r%-2d c%-2d  rebuilt -> %s" % (ti, ri, ci, new))

    apply_grid_edits(doc)

    for ta, ra, ca, tb, rb, cb, desc in SWAP_CELLS:
        swap_cell_blocks(doc.tables[ta].rows[ra].cells[ca],
                         doc.tables[tb].rows[rb].cells[cb])
        record("table %d r%d c%d <-> r%d c%d" % (ta, ra, ca, rb, cb),
               "cell-swap", "omml cell", desc, "", "")
        print("T%d r%d c%d <-> r%d c%d  %s" % (ta, ra, ca, rb, cb, desc[:40]))

    for idx, extra, desc in APPEND_EDITS:
        p = doc.paragraphs[idx]
        before = ptext(p)
        # No font is set on purpose. The appended sentence must read as part
        # of the caption it extends, and that paragraph's runs carry no rFonts
        # of their own -- they inherit from the "Body Text" style, as the new
        # run then does. Naming a font here (Arial was tried) put a sans-serif
        # sentence inside an otherwise serif caption, visible in the PDF as
        # the only ArialMT span in the whole SI.
        run = p.add_run(extra)
        record("para %d" % idx, "append", "text", desc, before, ptext(p))
        print("[%03d] append %s" % (idx, desc[:70]))

    # ------------------------------------------- new Table S6 subsections ---
    # Inserted here, after every paragraph edit, so the paragraph indices the
    # edits above use are still the source document's own.
    assert len(doc.tables) == n_s6_base, \
        "a table was added before the S6 insertion; the case-E index is stale"
    n_new = insert_new_s6(doc)
    print("+ %d new S6 elements (11 paragraphs, 8 tables)" % n_new)

    # ------------------------------------------------------ new SI figures ---
    for stem, tag, caption in SI_FIGURES:
        caption_text = "".join(t for t, _ in caption)
        png = os.path.join(FIGDIR, stem + ".png")
        if not os.path.exists(png):
            raise SystemExit("new SI figure missing: %s" % png)
        doc.add_paragraph(style="Normal")                  # spacer, as S1-S5
        pic_p = doc.add_paragraph(style="Captioned Figure")
        pic_p.paragraph_format.keep_with_next = True
        pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = pic_p.add_run()
        run.add_picture(png, width=Inches(SI_FIG_WIDTH_IN))
        cap_p = doc.add_paragraph(style="First Paragraph")
        add_caption(cap_p, caption)
        record("appended", "figure", tag,
               "%s at %.2f in wide (matches the seven existing SI figures); "
               "caption %d chars in %d runs (%d subscripts)"
               % (stem, SI_FIG_WIDTH_IN, len(caption_text), len(caption),
                  sum(1 for _t, s in caption if s)),
               "", tag)
        print("+ %s  image %.2f in + caption (%d chars, %d runs)"
              % (tag, SI_FIG_WIDTH_IN, len(caption_text), len(caption)))

    doc.save(DST)
    print("\nwrote %s (%d bytes)" % (DST, os.path.getsize(DST)))
    print("        %d paragraphs (was %d), %d tables (was %d)"
          % (len(doc.paragraphs), n_para0, len(doc.tables), n_tab0))

    with open(LOG, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["block", "kind", "target",
                                           "description", "before", "after"])
        w.writeheader()
        for row in LOG_ROWS:
            w.writerow(row)
    print("wrote %s (%d rows)" % (LOG, len(LOG_ROWS)))


if __name__ == "__main__":
    main()
