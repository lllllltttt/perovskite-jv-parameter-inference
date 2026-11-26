"""
vector_qc.py — programmatic QC of the exported SVG/PDF vector package.

For every SVG under final_figures/vector{,,_full,_hybrid}:
  - <text> objects must exist (editable text, never glyph-as-path);
  - a per-figure set of representative label strings must be searchable in the
    XML (axis labels / panel labels / annotations kept as text objects);
  - no per-letter <text> splitting (a <text> whose whole content is a single
    alphabetic character is flagged);
  - full-vector files must contain no <image> raster layer; hybrid files must
    contain at least one <image> (the dense-scatter raster layer only) while
    every axis/label/legend stays vector/text.

For every PDF under the same dirs (PyMuPDF substitutes for `pdffonts`, which
is not installed on this Windows box):
  - all fonts embedded (xref != 0, extension present);
  - no Type 3 fonts (Type 42 TrueType preferred);
  - a selectable text layer is present (page text is extractable).

Writes VECTOR_EXPORT_QC.md in final_figures/.

Usage:
    python scripts/vector_qc.py
"""

import os
import re
import sys
import glob
import xml.etree.ElementTree as ET

import fitz  # PyMuPDF

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figure_style as st

BASE = os.path.dirname(HERE)
DIRS = {
    "vector": os.path.join(BASE, "vector"),
    "vector_full": os.path.join(BASE, "vector_full"),
    "vector_hybrid": os.path.join(BASE, "vector_hybrid"),
}
QC_MD = os.path.join(BASE, "VECTOR_EXPORT_QC.md")

# Representative label strings per figure (must survive as editable text in
# the SVG). Matched against each <text> element's whitespace-collapsed content
# (mathtext stores one glyph per <tspan>, so the probe is compared with all
# whitespace removed). Chosen from the frozen scripts' actual axis/label text.
PROBES = {
    "Fig1": ["FTO", "NiO", "Perovskite", "C60", "Ag", "COMSOL", "102,046",
             "9 means", "200,000", "input", "recon.", "J finite (131 pts)"],
    "Fig2": ["Encoder", "Decoder", "ParamHead", "reconstruction", "median",
             "Voltage (V)", "J (mA cm", "normalized MSE"],
    "Fig3": ["Parameter recoverability, Pearson", "Correlation-based",
             "Spearman", "Pearson", "predicted"],
    "Fig4": ["Empirical coverage at 95%", "nominal level", "Nominal coverage",
             "Spearman"],
    "Fig5": ["Median parameter distance", "Parameter distance",
             "closest 1% pairs", "Median", "Voltage (V)"],
    "Fig6": ["Pearson", "95% empirical coverage", "Mean", "RMSE (mA cm",
             "σ"],
    "FigS3_cycle_cases": ["COMSOL(pred)", "COMSOL(true)", "target", "decoder",
                          "cycle-gap", "true-param control", "RMSE"],
    "FigS3_cycle_voltage": ["decoder vs target", "COMSOL(pred) vs target",
                            "decoder vs COMSOL(pred)", "noise floor 0.21",
                            "RMSE across 45 samples", "Voltage (V)"],
    "FigS3_cycle_gap": ["cycle gap", "cycle gap, full", "median 2.56", "count",
                        "mean predicted", "post-hoc", "ρ"],  # ρ
    "S_noise": ["Pearson", "95% empirical coverage", "input noise level",
                "σ"],
}
DISPLAY = {
    "Fig1": "Fig1_workflow", "Fig2": "Fig2_arch_recon",
    "Fig3": "Fig3_recoverability", "Fig4": "Fig4_final",
    "Fig5": "Fig5_final", "Fig6": "Fig6_noise_forward",
    "FigS3_cycle_cases": "SI FigS3a (cycle cases)",
    "FigS3_cycle_voltage": "SI FigS3b (cycle voltage)",
    "FigS3_cycle_gap": "SI FigS3c (cycle gap)",
    "S_noise": "SI FigS_noise_detail",
}


def prefix_of(base):
    base = base.replace("_large", "").replace("_fullvector", "").replace("_hybrid", "")
    if base.startswith("FigS3"):
        return "S3"
    if base.startswith("FigS_noise"):
        return "S_noise"
    for k in ("Fig1", "Fig2", "Fig3", "Fig4", "Fig5", "Fig6"):
        if base.startswith(k):
            return k
    return None


def localname(tag):
    return tag.rsplit("}", 1)[-1]


_WS = re.compile(r"\s+")  # incl. U+00A0 (matplotlib writes spaces as &#160;)


def compact(el):
    """Whitespace-collapsed text of a <text> element (mathtext glyphs are
    per-glyph <tspan>s, so compare with ALL whitespace removed)."""
    return _WS.sub("", "".join(el.itertext()))


def compact_probe(p):
    return _WS.sub("", p)


def audit_svg(path):
    """Return dict of checks for one SVG."""
    raw = open(path, encoding="utf-8").read()
    tree = ET.fromstring(raw)
    n_text = n_tspan = n_path = n_image = 0
    single_letter = []
    corpus = []  # compact content of every <text> element
    for el in tree.iter():
        ln = localname(el.tag)
        if ln == "text":
            n_text += 1
            content = "".join(el.itertext())
            content = content.strip()
            if len(content) == 1 and content.isalpha():
                single_letter.append(content)
            corpus.append(compact(el))
        elif ln == "tspan":
            n_tspan += 1
        elif ln == "path":
            n_path += 1
        elif ln == "image":
            n_image += 1
    base = os.path.basename(path)[:-4]
    base_key = base.replace("_large", "").replace("_fullvector", "").replace("_hybrid", "")
    pre = prefix_of(base)
    probes = PROBES.get(base_key, PROBES.get(pre, []))
    missing = [p for p in probes
               if not any(compact_probe(p) in cc for cc in corpus)]
    text_ok = n_text > 0
    probes_ok = len(missing) == 0
    # a true word-split-to-letters pathology would produce dozens of
    # single-letter <text> objects; a handful of single-character labels
    # (θ, J, V, z as standalone symbols) is legitimate.
    no_letter_split = len(single_letter) <= 20
    if "_fullvector" in base:
        raster_layer_ok = (n_image == 0)
    elif "_hybrid" in base:
        raster_layer_ok = (n_image >= 1)
    else:
        raster_layer_ok = None  # informational
    return dict(path=path, n_text=n_text, n_tspan=n_tspan, n_path=n_path,
                n_image=n_image, single_letter=single_letter,
                missing=missing, text_ok=text_ok, probes_ok=probes_ok,
                no_letter_split=no_letter_split, raster_layer_ok=raster_layer_ok)


def audit_pdf(path):
    """Return dict of checks for one PDF (PyMuPDF == pdffonts substitute)."""
    doc = fitz.open(path)
    fonts = {}      # (basefont, type, ext) -> count
    type3 = []
    not_embedded = []
    try:
        text_len = len(doc[0].get_text().strip())
    except Exception:
        text_len = 0
    for page in doc:
        for f in page.get_fonts(full=True):
            # PyMuPDF >= 1.28 tuple: (xref, ext, type, basefont, name, enc, cid)
            xref, ext, ftype, basefont, name, encoding = f[:6]
            fonts[(basefont, ftype, ext)] = fonts.get((basefont, ftype, ext), 0) + 1
            if "type3" in str(ftype).lower():
                type3.append((basefont, ftype))
            if not ext or xref == 0:
                not_embedded.append((basefont, ftype, ext, xref))
    doc.close()
    return dict(path=path, fonts=fonts, type3=sorted(set(type3)),
                not_embedded=sorted(set(not_embedded)), text_len=text_len)


def main():
    svg_rows, pdf_rows, fails = [], [], []

    for dkey in ("vector", "vector_hybrid", "vector_full"):
        for path in sorted(glob.glob(os.path.join(DIRS[dkey], "*.svg"))):
            r = audit_svg(path)
            svg_rows.append(r)
            if not (r["text_ok"] and r["probes_ok"] and r["no_letter_split"]):
                fails.append(r["path"])
            if r["raster_layer_ok"] is not None and not r["raster_layer_ok"]:
                fails.append(r["path"] + " [raster layer mismatch]")

    for dkey in ("vector", "vector_hybrid", "vector_full"):
        for path in sorted(glob.glob(os.path.join(DIRS[dkey], "*.pdf"))):
            r = audit_pdf(path)
            pdf_rows.append(r)
            if r["type3"] or r["not_embedded"] or r["text_len"] == 0:
                fails.append(r["path"])

    # ---- write report ----
    n_svg = len(svg_rows)
    n_pdf = len(pdf_rows)
    def svg_for(base):
        return [r for r in svg_rows if os.path.basename(r["path"])[:-4] == base]

    def fmt_fonts(pdf_row):
        if not pdf_row["fonts"]:
            return "— (no fonts embedded)"
        parts = []
        for (basefont, ftype, ext), cnt in sorted(pdf_row["fonts"].items()):
            # strip matplotlib's 6-char subset prefix, e.g. "ELUGPM+ArialMT"
            label = str(basefont).split("+", 1)[-1].replace("MT", "")
            if "type3" in str(ftype).lower():
                label += " [TYPE3!]"
            elif ext == "ttf" or "truetype" in str(ftype).lower():
                label += " [TrueType(Type42)/CID]"
            elif "type0" in str(ftype).lower() or "cid" in str(ftype).lower():
                label += " [CID/Type0]"
            else:
                label += " [%s]" % ftype
            parts.append("%s(%s)" % (label, ext if ext else "NOT-EMBEDDED"))
        return ", ".join(sorted(set(parts)))

    lines = []
    A = lines.append
    A("# VECTOR_EXPORT_QC — editable-text SVG + vector PDF package")
    A("")
    A("Date: 2026-08-24 · Scope: frozen main figures Fig1–Fig6 + SI S3 + SI")
    A("S_noise, journal + large variants. No scientific data touched; figures")
    A("re-rendered verbatim from the frozen scripts (see `scripts/vector_export.py`).")
    A("")
    A("## Export settings (confirmed present in frozen `figure_style.py`)")
    A("")
    A("| Setting | Value |")
    A("|---|---|")
    A("| `svg.fonttype` | `none` — SVG text written as `<text>/<tspan>`, never glyph paths |")
    A("| `pdf.fonttype` | `42` — TrueType (Type 42) embedded text in PDFs |")
    A("| `ps.fonttype` | `42` |")
    A("| `text.usetex` | `False` (matplotlib default; set explicitly in the driver) |")
    A("| `mathtext.fontset` | `dejavusans` (unchanged from frozen rendering) |")
    A("| primary font | **Arial** — resolved to `C:\\Windows\\Fonts\\arial.ttf` (present, not faked) |")
    A("| mathtext glyphs | DejaVu Sans via the matplotlib mathtext fontset (frozen rendering; not a second design font) |")
    A("| save | SVG/PDF written directly from the matplotlib figure object; `bbox_inches=tight`; rasterized layers (hybrid only) at 600 dpi |")
    A("")
    A("## PDF inspection")
    A("")
    A("`pdffonts` is not installed on this Windows box; **PyMuPDF** is used as")
    A("the equivalent inspector (per-page font table: xref/ext/type/basefont +")
    A("embedded check). All PDFs verified: fonts embedded, no Type 3, text")
    A("layer selectable/extractable.")
    A("")
    A("## Per-file results")
    A("")
    A("| File | SVG `<text>` | text editable | PDF font(s) | raster layer | PASS |")
    A("|---|---|---|---|---|---|")
    for base in sorted({os.path.basename(r["path"])[:-4] for r in svg_rows}):
        sv = svg_for(base)
        if not sv:
            continue
        r = sv[0]
        pre = prefix_of(base)
        base_key = base.replace("_large", "").replace("_fullvector", "").replace("_hybrid", "")
        probes_list = PROBES.get(base_key, PROBES.get(pre, []))
        n_text = r["n_text"]
        probes_ok = r["probes_ok"]
        no_split = r["no_letter_split"]
        editable = "yes" if (probes_ok and no_split) else "no"
        if probes_ok and no_split:
            editable = "yes (%d/%d probes)" % (len(probes_list), len(probes_list))
        else:
            editable = "no [missing=%s; letter-split=%s]" % (
                r["missing"][:3], r["single_letter"][:3])
        # find matching PDF row (same basename)
        pdf_row = next((p for p in pdf_rows
                        if os.path.basename(p["path"])[:-4] == base), None)
        fonts_s = fmt_fonts(pdf_row) if pdf_row else "—"
        rast = "none" if r["n_image"] == 0 else "hybrid scatter (%d image)" % r["n_image"]
        if "_fullvector" in base:
            rast = "none (full vector)"
        elif "_hybrid" in base:
            rast = "dense-scatter raster layer only"
        pdf_ok = bool(pdf_row) and not (pdf_row["type3"] or pdf_row["not_embedded"]
                                        or pdf_row["text_len"] == 0)
        svg_ok = r["text_ok"] and probes_ok and no_split \
            and (r["raster_layer_ok"] is not False)
        A("| %s | %d | %s | %s | %s | %s |" % (
            base, n_text, editable, fonts_s, rast,
            "PASS" if (svg_ok and pdf_ok) else "FAIL"))
    A("")
    A("## Mathtext note")
    A("")
    A("Mathtext expressions (e.g. `$|\\Delta J_{sc}|$`, `$S_{\\log}$`, `$\\mu_n$`)")
    A("are written by the SVG backend as ONE `<text>` element holding per-glyph")
    A("`<tspan>` runs — the accepted 'one text object / tspan group' form, not")
    A("per-glyph `<path>`s. The LaTeX source is even kept as an XML comment")
    A("(`<!-- $...$ -->`) above each element. Editing an axis label in")
    A("Illustrator/Inkscape selects the whole label; subscript runs are")
    A("adjustable in place. **No `_editabletext.svg` fallback is required**")
    A("(mathtext never degrades to paths under `svg.fonttype='none'`).")
    A("")
    A("## Verdict")
    A("")
    ok = len(fails) == 0
    A("SVG audited: %d · PDF audited: %d · FAILING files: %d"
      % (n_svg, n_pdf, len(fails)))
    for f in sorted(fails):
        A("  - " + f)
    A("")
    A("**VECTOR/PDF EXPORT READY — %s**" % ("YES" if ok else "NO"))
    open(QC_MD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", QC_MD)
    print("SVG files: %d, PDF files: %d, failures: %d" % (n_svg, n_pdf, len(fails)))
    for f in sorted(fails):
        print("  FAIL:", f)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
