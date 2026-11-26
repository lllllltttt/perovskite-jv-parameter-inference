# -*- coding: utf-8 -*-
"""
verify_si.py — read the built SI back and assert every intended value.

    python scripts/verify_si.py

build_si.py guards its inputs; this script checks its OUTPUT. It re-opens
si/Supplementary_Information_synced.docx and, independently of the edit list,
tests what a reader would test:

  1. every Table S6 / S10 cell that this round touched holds the value
     recomputed from the frozen sources (the v2 rows of T6.7-T6.9 are compared
     cell by cell against the CSVs in data_used/ that the tables were built
     from, so the document and the delivered data cannot drift apart);
  2. the factor column of T6.7a/6.7c really is 10^|Delta log10 theta| and not
     the exponential of a rescaled difference;
  3. the two Figure 3 cases are findable: both zero-based test-index pairs and
     both database Sample_ID pairs appear in T6.7 and in the case files;
  4. the tier table carries this round's counts and the six baselines;
  5. the case titles no longer present same-sign differences as evidence of a
     compensation mechanism, and the word does not appear in the SI at all;
  6. no "decade" survives anywhere in the file, in a paragraph or a table;
  7. the two cross-references say Fig. S6, and the withdrawn p-values are gone
     including as OMML math objects, which a text search cannot see;
  8. both added figures are present, at the width the other SI figures use,
     each followed by its caption;
  9. the paragraph and table counts moved only by what this round added.

Table lookup is by LABEL, not by position. build_si.py splices eight new tables
into the middle of S6, so every positional index after them shifts; three
hard-coded indices in the previous revision of this script silently pointed at
different tables after the splice (the archived Table S10 pair moved from 29/30
to 37/38). A label cannot drift that way, and a missing label is a hard error
rather than a comparison against the wrong table.
"""
import os
import sys

import pandas as pd
from docx import Document
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = (r"E:\project\work1\20260929_si_provenance_wording"
       r"\Supplementary_Information_provenance_wording_20260929.docx")
DST = os.path.join(OUT, "si", "Supplementary_Information_synced.docx")
DATADIR = os.path.join(OUT, "data_used")

W, M = qn("w:t"), qn("m:t")
FAIL = []

# paragraphs added by build_si.py relative to SRC: 6 in the first integration
# round (two figure spacers, two images, two captions) + 11 in this round
N_NEW_PARAS = 17
N_NEW_TABLES = 8


def ptext(p):
    return "".join((n.text or "") for n in p._p.iter() if n.tag in (W, M))


def wt(p):
    return "".join((n.text or "") for n in p._p.iter(W))


def cell_text(c):
    return "".join((n.text or "") for n in c._tc.iter() if n.tag in (W, M))


def check(cond, msg):
    print("%-4s %s" % ("ok" if cond else "FAIL", msg))
    if not cond:
        FAIL.append(msg)


def num(s):
    """Parse a displayed number, tolerating the minus sign Word may emit."""
    return float(s.strip().replace("\u2212", "-").replace(",", ""))


# ---------------------------------------------------------------- lookup ----

def label_tables(doc):
    """[(label, table)] for every table, labelled by the nearest preceding
    non-empty paragraph. The label paragraphs in this SI are the T6.x / T7.x /
    T10.x leads and the "Case (a)."/"Case (b)." leads."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    out, last = [], ""
    for ch in doc.element.body.iterchildren():
        tag = ch.tag.split("}")[1]
        if tag == "p":
            s = ptext(Paragraph(ch, doc)).strip()
            if s:
                last = s
        elif tag == "tbl":
            out.append((last, Table(ch, doc)))
    return out


_TABLES = None


def tbl(doc, prefix, nth=0):
    """The nth table whose label paragraph starts with `prefix`."""
    global _TABLES
    if _TABLES is None:
        _TABLES = label_tables(doc)
    hits = [t for lab, t in _TABLES if lab.startswith(prefix)]
    if len(hits) <= nth:
        raise SystemExit("no table labelled %r (#%d); labels seen: %s"
                         % (prefix, nth,
                            "; ".join(sorted({lab[:34] for lab, _ in _TABLES
                                              if lab}))[:400]))
    return hits[nth]


# --------------------------------------------------- archived expectations --

EXPECT = [
    # (label prefix, column indices to read, {row: expected strings})
    ("T6.1.", [1], {1: ("11245",), 2: ("0.004236",), 3: ("0.005811",),
                    4: ("0.000040",), 5: ("0.001365",), 6: ("0.002862",),
                    7: ("0.005165",), 8: ("0.008278",), 9: ("0.026912",),
                    10: ("0.173429",)}),
    ("T6.2.", [1], {1: ("11245",), 2: ("0.210959",), 3: ("0.084251",),
                    4: ("0.019512",), 5: ("0.147911",), 6: ("0.202068",),
                    7: ("0.266259",), 8: ("0.324668",), 9: ("0.434120",),
                    10: ("0.617473",)}),
    ("T6.3.", [1], {1: ("0.154",), 2: ("0.073",), 3: ("0.349",),
                    4: ("0.202",), 5: ("0.117",), 6: ("0.00286",)}),
    ("T6.4.", [2, 3, 4], {1: ("0.1567", "0.1761", "0.3700"),
                          2: ("0.1154", "0.1313", "0.2603"),
                          3: ("0.1060", "0.1320", "0.3016"),
                          4: ("0.0916", "0.1472", "0.3575"),
                          5: ("0.0913", "0.1216", "0.2939"),
                          6: ("0.0866", "0.1218", "0.2656"),
                          7: ("0.0712", "0.0960", "0.2228"),
                          8: ("0.0584", "0.0810", "0.1862"),
                          9: ("0.0500", "0.0663", "0.1485")}),
    ("T6.5.", [1], {1: ("0.72",), 2: ("0.87",), 3: ("0.60",), 4: ("0.51",),
                    5: ("0.46",), 6: ("0.46",), 7: ("0.42",)}),
    ("T10.1.", [1, 2, 4, 5, 6, 7],
     {1: ("11245", "0.2021", "0.1452", "0.1407", "0.1041", "0.154"),
      2: ("11060", "0.2194", "0.1885", "0.1812", "0.2125", "0.082"),
      3: ("11104", "0.2191", "0.1808", "0.1564", "0.1502", "0.092"),
      4: ("11208", "0.2092", "0.1509", "0.1532", "0.1133", "0.142"),
      5: ("11212", "0.2094", "0.1509", "0.1532", "0.1133", "0.170"),
      6: ("11036", "0.2220", "0.1838", "0.1589", "0.1595", "\u2014")}),
    ("T10.2.", [1, 2, 3],
     {1: ("1124", "0.000447", "0.1729"), 2: ("562", "0.000320", "0.1665"),
      3: ("112", "0.000171", "0.1452"), 4: ("56", "0.000133", "0.1407"),
      5: ("11", "0.000090", "0.1041"), 6: ("11245", "0.002862", "0.2021")}),
]


def check_displayed(doc):
    for label, cols, rows in EXPECT:
        tb = tbl(doc, label)
        for ri, want in rows.items():
            got = tuple(wt(tb.rows[ri].cells[c].paragraphs[0]).strip()
                        for c in cols)
            check(got == want, "%s r%d = %s" % (label, ri, " / ".join(got)))


# ------------------------------------------- this round's new S6 content ----

def check_case_tables(doc):
    """T6.7a/6.7c parameter tables and T6.7b/6.7d coordinate tables must match
    data_used/si_table_s6_7_figure_case_*.csv exactly (to display rounding)."""
    pc = pd.read_csv(os.path.join(DATADIR, "si_table_s6_7_figure_cases.csv"))
    cc = pd.read_csv(os.path.join(DATADIR,
                                  "si_table_s6_7_figure_case_coordinates.csv"))

    # the identity the SI states: the factor is 10^|Delta log10 theta|
    bad = pc[abs(pc["factor"] - 10.0 ** pc["abs_dlog10"]) > 1e-9]
    check(len(bad) == 0,
          "T6.7 factor column = 10^|Dlog10| in all %d rows (never exp of a "
          "rescaled difference)" % len(pc))
    bad = pc[abs(pc["abs_dlog10"] - pc["abs_log10_ratio"]) > 1e-12]
    check(len(bad) == 0,
          "T6.7 |Dlog10 theta| equals |log10(theta_i/theta_j)| in all rows")

    cases = [("Case (a).", "(a)", "2890", "5067", "141475", "71905"),
             ("Case (b).", "(b)", "500", "4560", "37892", "87198")]
    for lead, tag, ii, jj, si, sj in cases:
        sub = pc[pc["case"] == tag].reset_index(drop=True)
        tb = tbl(doc, lead)
        ok = True
        for k, r in sub.iterrows():
            row = tb.rows[k + 1]
            got = [num(wt(row.cells[2].paragraphs[0])),
                   num(wt(row.cells[3].paragraphs[0])),
                   num(wt(row.cells[4].paragraphs[0])),
                   num(wt(row.cells[5].paragraphs[0]))]
            ok &= abs(got[0] - r["theta_i"]) <= 2e-3 * abs(r["theta_i"])
            ok &= abs(got[1] - r["theta_j"]) <= 2e-3 * abs(r["theta_j"])
            ok &= abs(got[2] - r["abs_dlog10"]) <= 5e-4
            ok &= abs(got[3] - r["factor"]) <= 5e-3 * r["factor"]
        check(ok, "%s parameter table matches the case CSV "
                  "(9 params, factors %s)"
                  % (tag, ", ".join("%.4g" % v for v in sub["factor"])))
        # the lead paragraph identifies the case by index and by Sample_ID
        lead_txt = [lab for lab, t in label_tables(doc)
                    if lab.startswith(lead)][0]
        check(ii in lead_txt and jj in lead_txt and si in lead_txt
              and sj in lead_txt,
              "%s lead gives test indices %s/%s and Sample_ID %s/%s"
              % (tag, ii, jj, si, sj))

        coord = cc[cc["case"] == tag].reset_index(drop=True)
        ctb = tbl(doc, "T6.7b." if tag == "(a)" else "T6.7d.")
        ok = True
        for k, r in coord.iterrows():
            row = ctb.rows[k + 1]
            got = [num(wt(row.cells[2].paragraphs[0])),
                   num(wt(row.cells[3].paragraphs[0])),
                   num(wt(row.cells[4].paragraphs[0])),
                   num(wt(row.cells[5].paragraphs[0]))]
            ok &= abs(got[0] - r["value_i"]) <= 5e-4
            ok &= abs(got[1] - r["value_j"]) <= 5e-4
            ok &= abs(got[2] - r["absd"]) <= 5e-4
            ok &= abs(got[3] - r["absd_normalized"]) <= 5e-4
        check(ok, "%s coordinate table matches the case CSV "
                  "(6 coordinates, |D|/baseline)" % tag)

    # the rule the two picks come from, and the fact that the tier is doing work
    txt = " ".join(ptext(p) for p in doc.paragraphs)
    check("1.354456" in txt and "1.266201" in txt,
          "T6.7 states both selection statistics |Dr| = 1.354456 / 1.266201")
    check("1.361187" in txt and "3396" in txt and "13213" in txt,
          "T6.7 states that the global |Dr_mu| maximum is a different pair "
          "(3396/13213), so the tier restriction is load-bearing")


def check_tier_table(doc):
    """T6.8a/b/c must match data_used/si_table_s6_8_tiers.csv, including the
    four counts the brief fixes."""
    t = pd.read_csv(os.path.join(DATADIR, "si_table_s6_8_tiers.csv"))
    order = ["all", "closest 10%", "closest 5%", "closest 1%",
             "closest 0.5%", "closest 0.1%"]
    t = t.set_index("set").loc[order].reset_index()

    want_pairs = [11245, 1124, 562, 112, 56, 11]
    want_curves = [15307, 1673, 876, 196, 99, 21]
    check(list(t["n_pairs"]) == want_pairs,
          "tier pair counts = %s" % ", ".join(str(v) for v in t["n_pairs"]))
    check(list(t["distinct_samples"]) == want_curves,
          "tier distinct-curve counts = %s"
          % ", ".join(str(v) for v in t["distinct_samples"]))
    check(list(t["n_pairs"]) == want_pairs
          and t["n_pairs"].iloc[0] == 11245 and t["n_pairs"].iloc[3] == 112
          and t["n_pairs"].iloc[4] == 56 and t["n_pairs"].iloc[5] == 11,
          "the four checkpoints hold: all 11,245 / 1% 112 / 0.5% 56 / 0.1% 11")

    fams = [("T6.8a.", "mobility", ["a_mu", "r_mu"]),
            ("T6.8b.", "bulk-lifetime", ["a_tau", "r_tau"]),
            ("T6.8c.", "density-of-states", ["a_D", "r_D"])]
    for lead, fam, cols in fams:
        tb = tbl(doc, lead)
        # rows: 0 header, 1 Pairs, 2 Distinct curves, then (median, IQR) for a
        # and (median, IQR) for r. The IQR cell is one string "q25<endash>q75".
        ok = True
        for ci, cid in enumerate(cols):
            for ti in range(6):
                got_pairs = int(num(wt(tb.rows[1].cells[ti + 1].paragraphs[0])))
                got_curves = int(num(wt(tb.rows[2].cells[ti + 1].paragraphs[0])))
                got_med = num(wt(tb.rows[3 + 2 * ci].cells[ti + 1].paragraphs[0]))
                lo, hi = wt(tb.rows[4 + 2 * ci].cells[ti + 1].paragraphs[0]) \
                    .split("–")
                ok &= got_pairs == t["n_pairs"].iloc[ti]
                ok &= got_curves == t["distinct_samples"].iloc[ti]
                ok &= abs(got_med - t["med_%s" % cid].iloc[ti]) <= 5e-4
                ok &= abs(num(lo) - t["q25_%s" % cid].iloc[ti]) <= 5e-4
                ok &= abs(num(hi) - t["q75_%s" % cid].iloc[ti]) <= 5e-4
        check(ok, "T6.8 %s table matches the tier CSV "
                  "(counts, medians, IQRs, all six sets)" % fam)

    # the two restrictions the brief requires to be stated, and no p-value
    body = " ".join(ptext(p) for p in doc.paragraphs
                    if ptext(p).startswith("T6.8."))
    check("not a confidence interval" in body,
          "T6.8 states the interquartile range is not a confidence interval")
    check("not independent observations" in body,
          "T6.8 states the pairs are not independent observations")
    check("no p-value" in body.lower().replace("p-value is reported", "p-value"),
          "T6.8 states no p-value is reported")


def check_baselines(doc):
    b = pd.read_csv(os.path.join(DATADIR, "si_table_s6_9_baselines.csv"))
    order = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
    b = b.set_index("coordinate").loc[order].reset_index()
    tb = tbl(doc, "T6.9.")
    ok = True
    for k, r in b.iterrows():
        got = num(wt(tb.rows[k + 1].cells[2].paragraphs[0]))
        ok &= abs(got - r["median_absd_random"]) <= 5e-5
    check(ok, "T6.9 lists the six random-baseline medians "
              "(%s)" % ", ".join("%.4f" % v for v in b["median_absd_random"]))
    txt = " ".join(ptext(p) for p in doc.paragraphs if ptext(p).startswith("T6.9."))
    check("199,985" in txt and "200,000" in txt and "42" in txt,
          "T6.9 states the baseline construction (200,000 drawn, 199,985 kept, "
          "seed 42)")
    check("log10" in txt.lower() or "log\u2081\u2080" in txt,
          "T6.9 gives the physical log10 definition of each coordinate")


def check_case_e_adjacency(doc):
    """Regression guard: the fixed S6 insertion anchor must leave case E's lead
    immediately followed by case E's own value table. The earlier anchor
    (doc.tables[15], which IS that table) spliced 19 elements between them and
    stranded the table on the T6.9 page."""
    kids = list(doc.element.body.iterchildren())
    from docx.text.paragraph import Paragraph
    for n, ch in enumerate(kids):
        if ch.tag != qn("w:p"):
            continue
        if not ptext(Paragraph(ch, doc)).startswith("Case E "):
            continue
        nxt = kids[n + 1] if n + 1 < len(kids) else None
        check(nxt is not None and nxt.tag == qn("w:tbl"),
              "case E's lead paragraph is followed directly by its value table")
        return
    check(False, "case E lead paragraph not found")


def check_wording(doc):
    """Section 7: same-sign fractions are not evidence of a mechanism."""
    allp = " ".join(ptext(p) for p in doc.paragraphs)
    check("Same-sign parameter differences" in allp,
          "T6.5 title reads 'Same-sign parameter differences'")
    check("paired-parameter compensation" not in allp,
          "no 'paired-parameter compensation' left in the SI")
    check("compensation directions" not in allp.lower(),
          "no 'compensation directions' left in the SI")
    low = allp.lower()
    check("compensat" not in low,
          "the word 'compensation' does not appear anywhere in the SI "
          "(values kept, mechanism claim removed)")


MS = os.path.join(OUT, "manuscript", "Manuscript_20261002_Working_integrated.docx")


def check_manuscript_content_match(doc):
    """Content match, not number match.

    Every pointer this round introduced is followed to its target and the
    target is read: the Figure 3 caption sends the reader to a Methods section
    for the selection rule, so that section must state it; the two Table S6
    pointers must land on the subsections that carry the case tables and the
    tier table; and the two factors the Results quote must be the factors the
    SI case table displays. A number that resolves to the wrong content is the
    failure mode this check exists for.
    """
    ms = Document(MS)
    body = [ptext(p) for p in ms.paragraphs]

    cap = body[28]
    check("Cases are identified by zero-based test indices" in cap,
          "Fig. 3 caption identifies cases by zero-based test indices")
    check("nine ground-truth simulation parameters" in cap,
          "Fig. 3(d) caption says ground-truth simulation parameters")
    check("nine inferred parameters" not in " ".join(body),
          "no 'nine inferred parameters' left in the manuscript")

    target = "Methods (Curve similarity and parameter ambiguity)"
    check(target in cap, "Fig. 3 caption names its Methods target")
    head = [i for i, t in enumerate(body)
            if t.strip() == "Curve similarity and parameter ambiguity"]
    check(bool(head), "that Methods heading exists in the manuscript")
    if head:
        sec = body[head[0] + 1]
        check("the largest absolute mobility log-ratio difference" in sec
              and "the largest absolute bulk-lifetime log-ratio difference"
              in sec,
              "the cited Methods section actually states the Figure 3 "
              "selection rule")
        check("closest 1% subset (n = 112)" in sec,
              "the cited Methods section states the tier the rule runs on")
        check("without changing their order" in sec,
              "the cited Methods section states that the baseline is a fixed "
              "positive divisor and cannot reorder the pairs")

    check("Table S6, T6.7" in body[24],
          "Results point the case values at Table S6, T6.7")
    check("Table S6 (T6.8)" in body[25],
          "Results point the percentile subsets at Table S6 (T6.8)")

    # the quoted factors must be the factors T6.7a and T6.7c display
    pc = pd.read_csv(os.path.join(DATADIR, "si_table_s6_7_figure_cases.csv"))
    fa = pc[(pc["case"] == "(a)") & (pc["parameter"] == "tau_p_pvk")]
    fb = pc[(pc["case"] == "(b)") & (pc["parameter"] == "tau_HTL")]
    check("a factor of 443" in body[24]
          and round(float(fa["factor"].iloc[0])) == 443,
          "Results 'factor of 443' = T6.7a tau_p factor (%.1f)"
          % fa["factor"].iloc[0])
    check("a factor of 35" in body[24]
          and round(float(fb["factor"].iloc[0])) == 35,
          "Results 'factor of 35' = T6.7c tau_HTL factor (%.1f)"
          % fb["factor"].iloc[0])

    # T6.8 must carry the sets the Methods declares
    t = pd.read_csv(os.path.join(DATADIR, "si_table_s6_8_tiers.csv"))
    dec = body[head[0] + 1] if head else ""
    check("for f = 10%, 5%, 1%, 0.5% and 0.1%" in dec,
          "Methods declares the five percentile subsets T6.8 tabulates")
    check(list(t["set"]) == ["all", "closest 10%", "closest 5%", "closest 1%",
                             "closest 0.5%", "closest 0.1%"],
          "T6.8 tabulates exactly those sets plus the full set")

    # withdrawn / forbidden content must not have come back
    check("S19" not in " ".join(body), "S19 is not restored in the manuscript")
    check(any("AUTHOR QUERY" in t for t in body),
          "the data-sharing AUTHOR QUERY is still present")
    check("shared vertical scale" not in " ".join(body),
          "the Figure 4 'shared vertical scale' wording is gone")
    check("large negative current densities at high forward bias" in body[35],
          "the Figure 4 caption states the corrected case (c) wording")


def main():
    src = Document(SRC)
    doc = Document(DST)

    check(os.path.getsize(DST) > 1000000,
          "output DOCX exists and is non-trivial (%d bytes)"
          % os.path.getsize(DST))
    check(len(doc.paragraphs) == len(src.paragraphs) + N_NEW_PARAS,
          "paragraph count %d = %d + %d added"
          % (len(doc.paragraphs), len(src.paragraphs), N_NEW_PARAS))
    check(len(doc.tables) == len(src.tables) + N_NEW_TABLES,
          "table count %d = %d + %d added"
          % (len(doc.tables), len(src.tables), N_NEW_TABLES))

    check_displayed(doc)
    check_case_tables(doc)
    check_tier_table(doc)
    check_baselines(doc)
    check_case_e_adjacency(doc)
    check_wording(doc)
    check_manuscript_content_match(doc)

    # the parameter column of T6.4 must still read the symbols, in the new order
    sym = []
    t64 = tbl(doc, "T6.4.")
    for ri in range(1, 10):
        c = t64.rows[ri].cells[1]
        sym.append("".join((n.text or "") for n in c.paragraphs[0]._p.iter(M)))
    order = [s.replace("\u03c4", "tau").replace("\u03bc", "mu") for s in sym]
    check(order == ["tauETL", "mun", "tauHTL", "rrad", "taun", "taup",
                    "mup", "Nv", "Nc"],
          "T6.4 parameter column order = %s" % ", ".join(order))

    # every paragraph and cell scanned for the withdrawn unit name
    hits = [i for i, p in enumerate(doc.paragraphs)
            if "decade" in ptext(p).lower()]
    for ti, tb in enumerate(doc.tables):
        for row in tb.rows:
            for c in row.cells:
                if "decade" in cell_text(c).lower():
                    hits.append("T%d" % ti)
    check(not hits, "no 'decade' anywhere (%d hits)" % len(hits))

    # withdrawn p-values: the string AND the OMML nodes
    t63 = tbl(doc, "T6.3.")
    check("p=" not in ptext(t63.rows[1].cells[1].paragraphs[0])
          and not list(t63.rows[1].cells[1].paragraphs[0]._p.iter(M))
          and not list(t63.rows[2].cells[1].paragraphs[0]._p.iter(M)),
          "T6.3 p-values removed as text and as OMML")

    # cross-references
    p16 = [i for i, p in enumerate(doc.paragraphs)
           if ptext(p).startswith("Table S5.")][0]
    p85 = [i for i, p in enumerate(doc.paragraphs)
           if ptext(p).startswith("Table S16.")][0]
    check("(Fig. S6)" in ptext(doc.paragraphs[p16]),
          "Table S5 caption cites Fig. S6")
    check("of Fig. S6," in ptext(doc.paragraphs[p85]),
          "Table S16 caption cites Fig. S6")
    check("Fig. 2a" not in ptext(doc.paragraphs[p16])
          + ptext(doc.paragraphs[p85]),
          "neither caption still cites Fig. 2a")

    # the S6 lead must send the reader to the subsection that holds the cases
    lead = [ptext(p) for p in doc.paragraphs
            if ptext(p).startswith("Table S6.")][0]
    check("T6.7" in lead and "T6.6" in lead,
          "Table S6 caption names T6.7 (main-text Fig. 3 pairs) and T6.6 "
          "(archived supplementary cases)")

    # appended figures: order, width, caption, keep-with-next
    EMU_IN = 914400
    img = [p for p in doc.paragraphs[-6:]
           if p._p.findall(".//" + qn("wp:inline"))]
    caps = [p for p in doc.paragraphs[-6:]
            if ptext(p).strip().startswith("Figure S")]
    check(len(img) == 2 and len(caps) == 2,
          "the last six paragraphs carry 2 images + 2 captions")
    widths = []
    for p in img:
        ext = p._p.findall(".//" + qn("wp:extent"))
        widths.append(int(ext[0].get("cx")) / EMU_IN)
    check(all(abs(w - 6.00) < 1e-6 for w in widths),
          "both added figures are 6.00 in wide (%s)"
          % ", ".join("%.2f" % w for w in widths))
    check(all(p.paragraph_format.keep_with_next for p in img),
          "both image paragraphs keep with the caption")
    check([ptext(c).split(".")[0] for c in caps] == ["Figure S6", "Figure S7"],
          "captions are Figure S6 then Figure S7")
    check("11,245" in ptext(caps[1]) and "199,985" in ptext(caps[1]),
          "Figure S7 caption carries both pair counts")

    # the seven pre-existing SI images keep their width
    old_w = []
    for p in doc.paragraphs[:-6]:
        for e in p._p.findall(".//" + qn("wp:extent")):
            old_w.append(int(e.get("cx")) / EMU_IN)
    check(len(old_w) == 7 and all(abs(w - 6.00) < 1e-6 for w in old_w),
          "the seven pre-existing SI figures are untouched at 6.00 in")

    print("\n%s" % ("verify_si: PASS" if not FAIL
                    else "verify_si: FAIL (%d)" % len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
