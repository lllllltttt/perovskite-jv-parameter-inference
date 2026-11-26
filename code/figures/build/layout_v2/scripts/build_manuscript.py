# -*- coding: utf-8 -*-
"""
build_manuscript.py — assemble the finalised five figures into the mentor's
current manuscript and apply the text edits that this round makes necessary.

    python scripts/build_manuscript.py

Input  (read only, never written):
    E:\\project\\work1\\20261006\\Manuscript_20261002_Working.docx
    figures/Figure{1..5}.png            the 600 dpi renders of this round

Output:
    manuscript/Manuscript_20261002_Working_integrated.docx
    manuscript/Manuscript_edit_log.csv  one row per applied edit

WHAT THIS SCRIPT DOES, AND WHY IT IS SPLIT THIS WAY
---------------------------------------------------
Twelve blocks change. Five of them are pictures: [014], [034] and [041] already
hold an inline image and the image is swapped; [021] and [027] hold a coloured
"INSERTION" placeholder and the placeholder paragraph *becomes* the picture.
Seven are text: [018], [024], [025], [028], [035], [042] and [076]. Two more
([030], [032]) keep their text exactly and only lose the paragraph-wide
`w:vertAlign="superscript"` run property that was rendering all of their runs,
literal superscript glyphs included, at about 7 pt instead of the 11 pt body
size. Paragraphs
[086] (the data-and-code availability query) and the reference list are
deliberately untouched -- [086] asks the author for a repository that this round
has no authority to invent, and the references are outside the round's scope.

Two different run strategies are used, on purpose:

  * Uniform paragraphs ([018], [024], [025], [028], [076]) are collapsed into a
    single run that inherits the first existing run's properties verbatim. That
    keeps the document's own font, language and eastAsia hints exactly as they
    were; a paragraph whose runs differ only in where Word happened to break
    them gains nothing from being rebuilt run by run.

  * Formatted paragraphs ([035], [042]) are rebuilt from an explicit run list,
    because their formatting is load-bearing: the bold "Figure 4." lead, and the
    decoder / target / COMSOL subscripts that the caption's meaning depends on.
    The run properties are cloned from the paragraph's own runs and the extra
    children are inserted in schema order (CT_RPr has a required child order;
    appending <w:b/> after <w:color/> is invalid and Word will repair the file).

Every edit is recorded in Manuscript_edit_log.csv with the paragraph index, the
kind of edit and the character count before and after, so that a later reader
can show what moved without diffing two Word files by eye.
"""
import copy
import csv
import os
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = r"E:\project\work1\20261006\Manuscript_20261002_Working.docx"
DST_DIR = os.path.join(OUT, "manuscript")
DST = os.path.join(DST_DIR, "Manuscript_20261002_Working_integrated.docx")
FIGDIR = os.path.join(OUT, "figures")

FIG_WIDTH_IN = 6.80      # = the manuscript text column (8.5 - 0.85 - 0.85 in)

# Which paragraph gets which figure. The three indices that already carry an
# inline image get that image replaced; the two that carry a placeholder get the
# placeholder deleted and the picture put in its place.
FIG_EDITS = [
    (14, "Figure1.png", "replace inline image"),
    (21, "Figure2.png", "replace [FIGURE 2 INSERTION] placeholder"),
    (27, "Figure3.png", "replace [FIGURE 3 INSERTION] placeholder"),
    (34, "Figure4.png", "replace inline image"),
    (41, "Figure5.png", "replace inline image"),
]

# CT_RPr child order, ECMA-376. Inserting a child at the wrong position makes
# the part schema-invalid; Word then "repairs" the file on open, which is a
# silent edit of our own delivery.
_RPR_ORDER = [
    "w:rStyle", "w:rFonts", "w:b", "w:bCs", "w:i", "w:iCs", "w:caps",
    "w:smallCaps", "w:strike", "w:dstrike", "w:outline", "w:shadow",
    "w:emboss", "w:imprint", "w:noProof", "w:snapToGrid", "w:vanish",
    "w:webHidden", "w:color", "w:spacing", "w:w", "w:kern", "w:position",
    "w:sz", "w:szCs", "w:highlight", "w:u", "w:effect", "w:bdr", "w:shd",
    "w:fitText", "w:vertAlign", "w:rtl", "w:cs", "w:em", "w:lang",
    "w:eastAsianLayout", "w:specVanish", "w:oMath",
]

# CT_PPr child order, ECMA-376. Same reason as _RPR_ORDER: a pPr whose children
# are out of order is schema-invalid and Word rewrites it on open.
_PPR_ORDER = [
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
    "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
    "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap",
    "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
]

LOG = []


# ------------------------------------------------------------- xml helpers --
def _ensure_child_at(parent, tag, order):
    el = parent.find(qn(tag))
    if el is not None:
        return el
    el = OxmlElement(tag)
    rank = order.index(tag)
    pos = len(parent)
    for k, child in enumerate(parent):
        full = "w:" + child.tag.split("}")[-1]
        if full in order and order.index(full) > rank:
            pos = k
            break
    parent.insert(pos, el)
    return el


def _ensure_child(rpr, tag):
    return _ensure_child_at(rpr, tag, _RPR_ORDER)


def _drop(rpr, *tags):
    for tag in tags:
        for el in rpr.findall(qn(tag)):
            rpr.remove(el)


def clear_runs(p):
    """Remove every w:r child, leaving the paragraph properties in place."""
    for r in list(p._p.findall(qn("w:r"))):
        p._p.remove(r)


def _rpr_of(p, idx=0):
    rs = p.runs
    if idx < len(rs):
        el = rs[idx]._r.find(qn("w:rPr"))
        if el is not None:
            return copy.deepcopy(el)
    return None


def _mk_run(p, text, rpr=None, bold=None, sub=False, unmark=False,
            no_proof=False):
    """Append a run built from `rpr` with the requested overrides."""
    r = OxmlElement("w:r")
    rp = copy.deepcopy(rpr) if rpr is not None else None
    if rp is None and (bold or sub or no_proof or unmark):
        rp = OxmlElement("w:rPr")
    if rp is not None:
        if unmark:
            # the INSERTION placeholders were coloured + highlighted; the run
            # properties are inherited, so the marks have to be stripped or the
            # rewritten paragraph arrives in orange on yellow.
            _drop(rp, "w:highlight", "w:color")
        if bold is True:
            _ensure_child(rp, "w:b")
        elif bold is False:
            _drop(rp, "w:b")
        if sub:
            _ensure_child(rp, "w:vertAlign").set(qn("w:val"), "subscript")
        if no_proof:
            _ensure_child(rp, "w:noProof")
        r.append(rp)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    p._p.append(r)
    return r


def collapse(p, text, unmark=False):
    """Put `text` in the first run, drop the rest. Formatting is preserved."""
    rpr = _rpr_of(p)
    clear_runs(p)
    _mk_run(p, text, rpr, unmark=unmark)


def all_superscript(p):
    """True when the paragraph has runs and every one of them is superscript."""
    rs = p.runs
    if not rs:
        return False
    for r in rs:
        rp = r._r.find(qn("w:rPr"))
        if rp is None:
            return False
        v = rp.find(qn("w:vertAlign"))
        if v is None or v.get(qn("w:val")) != "superscript":
            return False
    return True


def desup(p):
    """Drop w:vertAlign from every run of a wholly-superscript paragraph.

    Two paragraphs in the source (the "Physical back-substitution ..." and
    "Selected device metrics ..." paragraphs on the back-substitution page) have
    w:vertAlign val="superscript" on *every* run and no w:sz anywhere. Word
    applies the superscript size factor to the whole paragraph, so both render
    at about 7 pt against the 11 pt body text around them.

    Removing the vertAlign is the whole fix, and it is a run-level fix only:
      * the document's `Normal` style rPr carries no w:sz (only w:rFonts and
        w:color), and docDefaults set w:sz to 22 half-points, so a run with no
        vertAlign and no sz renders at the 11 pt body size; and
      * the superscripts that carry meaning in these paragraphs are literal
        Unicode glyphs inside the text (⁻⁷, ⁻², ×, 10), not formatting, so they
        keep rendering as superscripts of their own accord.

    Nothing is forced to body size: only the paragraph-wide vertAlign is
    removed. The paragraph style is left alone, so the text matches its
    neighbours.
    """
    n = 0
    for r in p.runs:
        rp = r._r.find(qn("w:rPr"))
        if rp is None:
            continue
        for v in rp.findall(qn("w:vertAlign")):
            rp.remove(v)
            n += 1
    ppr = p._p.find(qn("w:pPr"))
    if ppr is not None:
        mr = ppr.find(qn("w:rPr"))
        if mr is not None:
            for v in mr.findall(qn("w:vertAlign")):
                mr.remove(v)
                n += 1
    return n


def rich(p, parts):
    """Rebuild the paragraph from [(text, flags), ...].

    flags: a string of 'B' (bold), 'S' (subscript), lowercase = plain.
    The clone template is taken per-flag from an existing run so that the
    rebuilt paragraph inherits the document's real fonts rather than the
    python-docx default.
    """
    plain, bold = _rpr_of(p), None
    for r in p.runs:
        rp = r._r.find(qn("w:rPr"))
        if rp is not None and rp.find(qn("w:b")) is not None:
            bold = copy.deepcopy(rp)
            break
    clear_runs(p)
    # Inline OMML hangs directly off w:p, not inside a w:r, so clear_runs
    # leaves it standing. The rebuilt text spells its own symbols, so a
    # survivor is pure duplication -- and because the new runs are appended
    # after it, it is stranded at the head of the paragraph, where it renders
    # as a stray glyph cluster in front of the caption's first word. The
    # display equations rich() never touches are separate paragraphs.
    for tag in ("m:oMath", "m:oMathPara"):
        for el in list(p._p.findall(qn(tag))):
            p._p.remove(el)
    for text, flags in parts:
        _mk_run(p, text, bold if "B" in flags else plain,
                bold=("B" in flags), sub=("S" in flags))


# ---------------------------------------------------------------- pictures --
def set_pic_paragraph(p, path, width_in):
    """Turn a paragraph into a centred figure paragraph holding one picture.

    keepNext + the 200/80 pt spacing reproduce the pattern the existing image
    paragraphs already use, so the inserted figures space like the ones around
    them. jc=center rather than the old jc=both: at the full text-column width
    the two are identical, and at any other width centring is what a figure
    wants.
    """
    for r in list(p._p.findall(qn("w:r"))):
        p._p.remove(r)
    for tag in ("w:pPr", "w:rPr"):                       # paragraph-mark marks
        el = p._p.find(qn("w:pPr"))
        if el is None:
            continue
        if tag == "w:rPr":
            inner = el.find(qn("w:rPr"))
            if inner is not None:
                _drop(inner, "w:highlight", "w:color")
        else:
            for old in el.findall(qn("w:keepNext")):
                el.remove(old)
            for old in el.findall(qn("w:spacing")):
                el.remove(old)
            for old in el.findall(qn("w:jc")):
                el.remove(old)
            _ensure_child_at(el, "w:keepNext", _PPR_ORDER)
            sp = _ensure_child_at(el, "w:spacing", _PPR_ORDER)
            sp.set(qn("w:before"), "200")
            sp.set(qn("w:after"), "80")
            jc = _ensure_child_at(el, "w:jc", _PPR_ORDER)
            jc.set(qn("w:val"), "center")
    run = p.add_run()
    run.add_picture(path, width=Inches(width_in))
    rp = run._r.find(qn("w:rPr"))
    if rp is None:
        rp = OxmlElement("w:rPr")
        run._r.insert(0, rp)
    _ensure_child(rp, "w:noProof")
    return run


# -------------------------------------------------------------- the texts ---
T018 = (
    "The paired-coordinate distinction qualifies the strong correlations "
    "obtained for the six bulk parameters individually, which range from 0.878 "
    "to 0.919. The three remaining parameters have lower correlations: 0.594 "
    "for the ETL-side interfacial lifetime, 0.720 for the HTL-side interfacial "
    "lifetime, and 0.559 for the radiative coefficient (Fig. S6). Absolute "
    "errors also remain appreciable: the electron and hole bulk-lifetime MAEs "
    "are 0.70 and 0.71 in physical log₁₀ units (Table S16), corresponding to "
    "geometric mean multiplicative error factors of approximately five. "
    "Individual-parameter correlation therefore describes only part of the "
    "accuracy relevant to device interpretation."
)

T024 = (
    "The simulated dataset contains similar J–V responses with markedly "
    "different parameter combinations. The two representative pairs in Fig. 3 "
    "were selected from the closest 1% of corrected undirected pairs (n = 112) "
    "as the extreme members of the mobility and bulk-lifetime log-ratio "
    "coordinates; within them the largest single-parameter differences are a "
    "factor of 443 in the hole bulk lifetime and a factor of 35 in the HTL-side "
    "interfacial lifetime (Table S6, T6.7). Other parameters also differ within "
    "these "
    "pairs, so the examples describe variation among combinations of "
    "parameters. Their similarity in normalized current coordinates motivates "
    "examining shared-scale and log-ratio differences directly across "
    "neighbouring curves."
)

T025 = (
    "Across the test set, the corrected rule yields 11,245 unique undirected "
    "nearest-neighbour pairs. They cover all 15,307 test curves, and 5,859 "
    "curves appear in more than one pair, so the pairs are not independent "
    "observations. Each coordinate difference is normalized by the median "
    "absolute difference of the same coordinate among random pairs. Over all "
    "11,245 pairs, the median normalized differences are 0.353, 0.312 and 0.404 "
    "for the shared scales of mobility, bulk lifetime and density of states, "
    "compared with 0.810, 0.861 and 0.944 for the corresponding log-ratios "
    "(Fig. 3c). Under this distance metric and simulated sampling distribution, "
    "the shared-scale difference therefore shrinks substantially more than the "
    "log-ratio difference. Percentile subsets of the same pairs are reported in "
    "Table S6 (T6.8), and the full distribution of each coordinate against its "
    "random-pair baseline is shown in Fig. S7. These comparisons are "
    "descriptive: they do not show that the electron–hole ratio carries no "
    "information, and they do not establish non-uniqueness or a universal "
    "identifiability limit."
)

T028 = [
    ("Figure 3. Parameter variation among neighbouring J–V curves. ", ""),
    ("(a, b) The two representative simulated curve pairs, one selected on the "
     "mobility and one on the bulk-lifetime log-ratio coordinate: the J–V "
     "curves of both members, with the pointwise difference between their "
     "physical current densities, ΔJ, in mA cm⁻², in the strip below each "
     "panel. Both pairs are deliberately extreme members of the closest 1% of "
     "corrected undirected pairs (n = 112), chosen by the stated rule rather "
     "than drawn at random. Cases are identified by zero-based test indices; "
     "the selection rule is given in Methods (Curve similarity and parameter "
     "ambiguity). ", ""),
    ("(c) Median absolute coordinate difference over all 11,245 corrected "
     "undirected pairs, normalized by the median absolute difference of the "
     "same coordinate among random pairs, for the shared scale and the "
     "log-ratio of mobility, bulk lifetime and density of states; whiskers give "
     "the interquartile range and the dashed line at one is the random-pair "
     "median. ", ""),
    ("(d) Absolute differences |log₁₀(θ", ""), ("i", "S"), ("/θ", ""), ("j", "S"),
    (")| = |log₁₀θ", ""), ("i", "S"), (" − log₁₀θ", ""), ("j", "S"),
    ("| of the nine ground-truth simulation parameters for the same two pairs, "
     "in physical log₁₀ units, so that the individual parameters behind the "
     "coordinate separations are visible. Neighbours are selected using the "
     "primary "
     "normalized-current distance, and directed pairs are converted to unique "
     "undirected pairs. Panel (c) is descriptive: the tier pairs share samples, "
     "so no p-value and no confidence interval is reported, and neither the "
     "aggregate summaries nor the two examples establish that these responses "
     "are experimentally indistinguishable.", ""),
]

T035 = [
    ("Figure 4. ", "B"),
    ("Physical response of inferred parameter combinations. (a–c) Target "
     "curves, decoder reconstructions and COMSOL responses for the cases with "
     "the lowest, median and highest cycle gap in the 45-sample cohort; titles "
     "give zero-based test indices. Panels have independent vertical scales; "
     "the strips below give the pointwise residuals ΔJ = J", ""),
    ("decoder", "S"), (" − J", ""), ("target", "S"), (" and ΔJ = J", ""),
    ("COMSOL", "S"), (" − J", ""), ("target", "S"),
    (" in mA cm⁻². d", ""), ("dec", "S"), (" and d", ""), ("COM", "S"),
    (" are target-relative current RMSEs; d", ""), ("gap", "S"),
    (" is the RMSE between the decoder and COMSOL curves. Case (c) reaches "
     "large negative current densities at high forward bias. The inset enlarges "
     "the 0–1.0 V region while the main panel retains the full voltage and "
     "current ranges; the inset axis is labelled in mA cm⁻². "
     "Within that window the decoder follows the target "
     "closely, whereas the COMSOL response obtained from the same inferred "
     "vector departs as the bias approaches 1.0 V, reaching 19.0 mA cm⁻² "
     "against a target of 11.6 mA cm⁻² at 1.0 V. ", ""),
    ("(d) Current RMSE of the back-substitution over the full sweep, 0–1.0 V "
     "and >1.0 V (n = 45), on a logarithmic axis. (e) Absolute deviations from "
     "the target in short-circuit current density, open-circuit voltage, fill "
     "factor and power conversion efficiency (PCE), extracted under the same "
     "rules for target and predicted curves, with V", ""), ("oc", "S"),
    (" interpolated at the first downward zero crossing. Units: mA cm⁻², V, "
     "dimensionless (fill factor), percentage points (pp) for PCE. "
     "Short-circuit current uses all 45 cases and the other three metrics 44, "
     "because one predicted curve has no downward zero crossing within the "
     "sweep.", ""),
]

T042 = [
    ("Figure 5. ", "B"),
    ("Predictive intervals and the effect of current noise. (a) Empirical "
     "marginal coverage at nominal levels of 50%, 80%, 90% and 95% (dashed "
     "line), for the test curves (n = 15,307). (b) Mean 95% interval score in "
     "physical log₁₀ units for the model and for fixed training-quantile "
     "intervals, one row per parameter; lower is better. Model interval "
     "endpoints are not clipped, and the baseline is fixed from the training "
     "partition alone. An extra symbol marks parameters that do not improve on "
     "the baseline. (c–e) Independent Gaussian noise with a standard deviation "
     "equal to 0%, 0.2%, 0.5%, 1% or 2% of each curve’s |J", ""), ("sc", "S"),
    ("| is added at each of the 131 voltage points; the 0% entry repeats the "
     "noise-free input and is the reference for the relative changes in (e). "
     "The network and normalizations remain fixed at their noise-free values, "
     "and each statistic is averaged over 30 noise realizations, one curve per "
     "parameter. (c) Pearson correlation ρ. (d) Empirical 95% coverage. "
     "(e) Percentage change in the test-set mean predicted standard deviation "
     "σ", ""), ("θ", "S"),
    (" relative to the noise-free input, 100 × [σ", ""), ("θ", "S"),
    ("(noisy)/σ", ""), ("θ", "S"),
    ("(noise-free) − 1], in normalized log₁₀ coordinates.", ""),
]

T076 = (
    "For each test curve i, the nearest other curve j was selected by RMSE over "
    "the 131 normalized current values, excluding self-matches. The search used "
    "a chunked minimum over the normalized current vectors, so distance ties "
    "are broken by the lowest test index. Each directed pair was converted to "
    "(min(i,j), max(i,j)), and duplicates were removed to form the unique "
    "undirected neighbour set. This converted 15,307 directed links into 11,245 "
    "unique undirected pairs covering all 15,307 test curves, of which 5,859 "
    "curves appear in more than one pair (at most five). For each bulk pair, "
    "absolute differences in the physical log₁₀ shared-scale coordinate a and "
    "log-ratio coordinate r were calculated. Each coordinate difference was "
    "normalized by the median absolute difference for that same coordinate "
    "among random pairs; those baselines were drawn with "
    "numpy.random.default_rng(42) by sampling 200,000 ordered index pairs "
    "uniformly and dropping self-pairs, which left 199,985 pairs. Raw "
    "differences were retained alongside these baseline-normalized values. "
    "Percentile subsets of the corrected pairs were taken in ascending "
    "nearest-neighbour distance with k = max(1, round(n_pairs × f)) for f = "
    "10%, 5%, 1%, 0.5% and 0.1%. The two pairs shown in Fig. 3 were taken from "
    "the closest 1% subset (n = 112): the pair with the largest absolute "
    "mobility log-ratio difference, and then, with that pair excluded, the "
    "pair with the largest absolute bulk-lifetime log-ratio difference. Both "
    "were ranked on the raw coordinate differences; dividing a coordinate by "
    "its own fixed positive baseline rescales those differences without "
    "changing their order, so ranking the baseline-normalized differences "
    "selects the same two pairs. Distance ties would be resolved by taking the "
    "earlier pair in the ascending-distance ordering. Pair membership may "
    "share samples, so the pairs are not independent observations, and no "
    "significance test or confidence interval is reported for the subset "
    "comparisons."
)

TEXT_EDITS = [
    (18, "collapse", T018, "name the three lower individual-parameter "
                          "correlations and cite Fig. S6"),
    (24, "collapse", T024, "replace the withdrawn 280-fold / 72-fold example "
                           "with the final pair selection rule and the "
                           "measured 443-fold / 35-fold differences"),
    (25, "collapse", T025, "resolve F3-RESULTS: verified pair counts, "
                           "baseline-normalised medians, permitted conclusion"),
    (28, "rich", T028, "resolve F3-CAPTION: per-panel Figure 3 caption"),
    (35, "rich", T035, "extend the Figure 4 caption with the panel (c) "
                       "0-1.0 V inset and its measured values"),
    (42, "rich", T042, "fix the Figure 5 caption: noise-free 0 point, no bar "
                       "in panel (e), and sigma_theta not 'scale'"),
    (76, "collapse", T076, "resolve F3-METHODS: back-fill the tie rule, the "
                           "seed-42 random baseline, the tier rounding and the "
                           "Figure 3 case-selection rule the caption points to"),
    # the two paragraphs that render at ~7 pt because every run carries
    # w:vertAlign="superscript"; the text is untouched, only the run property
    # that shrank the whole paragraph is dropped
    (30, "desup", None, "restore the 11 pt body size (drop the paragraph-wide "
                        "superscript run property; literal superscript glyphs "
                        "kept as they are)"),
    (32, "desup", None, "restore the 11 pt body size (drop the paragraph-wide "
                        "superscript run property; literal superscript glyphs "
                        "kept as they are)"),
]


# ------------------------------------------------------------------- main ---
def main():
    os.makedirs(DST_DIR, exist_ok=True)
    doc = Document(SRC)
    paras = doc.paragraphs
    print("source: %s" % SRC)
    print("        %d paragraphs, %d tables" % (len(paras), len(doc.tables)))

    # guard: every index we are about to touch must still hold what we expect
    checks = [
        (14, ""), (34, ""), (41, ""),
        (21, "FIGURE 2 INSERTION"), (27, "FIGURE 3 INSERTION"),
        (18, "The paired-coordinate distinction qualifies"),
        (24, "The simulated dataset contains similar"),
        (25, "AUTHOR QUERY F3-RESULTS"),
        (28, "Figure 3. Parameter variation among"),
        (35, "Figure 4. Physical response"),
        (42, "Figure 5. Predictive intervals"),
        (76, "For each test curve"),
        (30, "Physical back-substitution evaluates"),
        (32, "Selected device metrics remain close"),
    ]
    for idx, needle in checks:
        got = paras[idx].text
        if needle and needle not in got:
            raise SystemExit("paragraph [%03d] does not hold %r; aborting "
                             "rather than editing the wrong block.\n  found: %r"
                             % (idx, needle, got[:120]))
    # the desup edit is only safe when *every* run is superscript: on a mixed
    # paragraph it would silently strip superscripts that carry meaning.
    for idx, mode, _payload, _why in TEXT_EDITS:
        if mode == "desup" and not all_superscript(paras[idx]):
            raise SystemExit("paragraph [%03d] is not wholly superscript; "
                             "refusing to strip its run properties" % idx)

    # ---- 1. the five figures -------------------------------------------
    for idx, fname, what in FIG_EDITS:
        path = os.path.join(FIGDIR, fname)
        if not os.path.exists(path):
            raise SystemExit("missing figure: %s" % path)
        before = len(paras[idx].text)
        set_pic_paragraph(paras[idx], path, FIG_WIDTH_IN)
        LOG.append(dict(paragraph=idx, kind="figure", target=fname,
                        description=what + " (%.2f in wide)" % FIG_WIDTH_IN,
                        chars_before=before, chars_after=0))
        print("  [%03d] figure  <- %s" % (idx, fname))

    # ---- 2. the seven text blocks --------------------------------------
    for idx, mode, payload, why in TEXT_EDITS:
        before = len(paras[idx].text)
        if mode == "collapse":
            collapse(paras[idx], payload, unmark=True)
        elif mode == "desup":
            n = desup(paras[idx])
            LOG.append(dict(paragraph=idx, kind="desup", target="",
                            description="%s (%d vertAlign removed)" % (why, n),
                            chars_before=before, chars_after=before))
            print("  [%03d] desup   %d vertAlign removed, %d chars unchanged "
                  "(%s)" % (idx, n, before, why))
            continue
        else:
            rich(paras[idx], payload)
        after = len(paras[idx].text)
        LOG.append(dict(paragraph=idx, kind="text", target="",
                        description=why, chars_before=before,
                        chars_after=after))
        print("  [%03d] text    %d -> %d chars  (%s)" % (idx, before, after,
                                                         why))

    doc.save(DST)
    print("wrote: %s  (%d bytes)" % (DST, os.path.getsize(DST)))

    # ---- 3. re-open the written file and check the cross-references by
    #         content, not by number. The Figure 3 caption sends the reader to
    #         "Methods (Curve similarity and parameter ambiguity)" for the
    #         selection rule, so that section has to actually state it; the two
    #         Table S6 pointers have to land on the subsections that carry the
    #         thing named. A matching number with the wrong content is exactly
    #         what this round is meant to prevent.
    chk = Document(DST)
    body = [p.text for p in chk.paragraphs]
    m76 = body[76]
    for needle in ("the pair with the largest absolute mobility log-ratio "
                   "difference",
                   "the largest absolute bulk-lifetime log-ratio difference",
                   "dividing a coordinate by its own fixed positive baseline"):
        if needle not in m76:
            raise SystemExit("Methods paragraph [076] no longer states the "
                             "Figure 3 selection rule (%r missing); the "
                             "Fig. 3 caption points there" % needle)
    if "Methods (Curve similarity and parameter ambiguity)" not in body[28]:
        raise SystemExit("the Figure 3 caption no longer names the Methods "
                         "section it points to")
    if "T6.7" not in body[24] or "T6.8" not in body[25]:
        raise SystemExit("a Table S6 pointer lost its subsection number")
    print("  xref content check: Fig. 3 caption -> Methods rule, "
          "Table S6 pointers -> T6.7 / T6.8  OK")

    with open(os.path.join(DST_DIR, "Manuscript_edit_log.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paragraph", "kind", "target",
                                           "description", "chars_before",
                                           "chars_after"])
        w.writeheader()
        w.writerows(LOG)
    print("wrote: manuscript/Manuscript_edit_log.csv (%d edits)" % len(LOG))


if __name__ == "__main__":
    sys.exit(main())
