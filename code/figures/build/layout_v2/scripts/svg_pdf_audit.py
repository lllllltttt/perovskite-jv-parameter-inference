# -*- coding: utf-8 -*-
"""Vector-format audit for the delivered figures: PDF raster dpi, SVG text.

    python scripts/svg_pdf_audit.py

The PNG renders are checked by qa_layout.py and figure_font_audit.py, which
re-measure the live matplotlib canvases. Those say nothing about the two vector
formats, and the two vector formats are what carry the figure into production:
the PDF is what a journal places, the SVG is what an editor opens.

Three checks, all on the saved files rather than on the live figure.

1. PDF raster resolution. Figure 2 (six parity panels) and Figure S6 (nine
   parameter panels) each draw 15,307 points per panel with
   `rasterized=True`: a vector equivalent would be tens of megabytes that no
   journal would take. Every other artist in every figure is vector. So the
   rasterised collections are the only raster content in the package, and
   their resolution is a real quality property that nothing else checks --
   a 100 dpi cloud stretched over a 1.9 in panel sits in exactly the right
   place at exactly the right size and is simply soft. Measured, and the
   reason figstyle.save_fig now forwards `dpi` to the PDF as well as to the
   PNG.

2. PDF font embedding. Every font listed on the page is embedded (a subset
   prefix like "EGWXSV+" in the font name), so the page renders identically
   on a machine that does not have the fonts. This is the format's own
   answer to font substitution, and it is checkable.

3. SVG text. Text is emitted as <text>/<tspan> rather than as outlines, so
   the file stays editable (`svg.fonttype = "none"` in figstyle.py). Every
   declaration is one of the families the project means to use, and no
   <text> anchor lands outside the viewBox, where a viewer would clip it.
   The anchor test accumulates the <g transform="..."> chain instead of
   reading the raw x/y attributes: matplotlib writes x/y in the LOCAL frame
   of the enclosing group, so the raw values of a rotated y-axis label are
   meaningless on their own and a naive test reports dozens of false hits.

Fonts that legitimately appear and are NOT a substitution problem:
  Arial / Arial-BoldMT  -- the authoring font (figstyle.py).
  DejaVu Sans           -- matplotlib's mathtext fontset (`mathtext.fontset`
                           = "dejavusans"), and the declared fallback for
                           Arial.
  DejaVu Sans Display   -- matplotlib's display-size DejaVu, chosen
                           automatically for large mathtext.
  DejaVu Sans Oblique   -- italic mathtext.
  STIXSizeOneSym        -- matplotlib's growing-delimiter font, used by
                           mathtext for tall parentheses/brackets.
All of them ship with matplotlib and all of them are EMBEDDED in the PDFs. In
the SVG they are named, not embedded, so a viewer must have Arial and DejaVu
Sans, or it will substitute for those glyphs and only those. The PNG and the
PDF are the two deliverables that are safe on any machine; the SVG is the one
that assumes a normal desktop font set.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FIGDIR = os.path.join(OUT, "figures")

NOMINAL = {"": 7.09, "_large": 9.50}
# bbox_inches="tight" trims to the content and pads 0.1 in, so the delivered
# page is the designed width minus however much margin the layout left. The
# check below is a bound, not an equality: the page may never be WIDER than
# the designed column (that would overflow the journal column), and it may not
# be trimmed away to something much narrower than designed.
TRIM_MAX = 0.55
# ...and it may be WIDER than designed, because tight-bbox keeps whatever
# sticks out past the canvas edge: a rotated y-axis label or a panel tag set
# just outside its axes makes the page up to 0.1 in wider than the nominal
# width (measured: Figure 1 7.19 in, Figure 2 7.13 in). That is a 1.4% overrun
# on a column the publisher scales to fit, not an overflow, so the bound is
# 0.20 in -- wide enough to allow it, narrow enough to catch a real mistake
# such as a figure built at the wrong size.
OVER_MAX = 0.20

MIN_RASTER_DPI = 300.0        # the floor a journal applies to raster content
RASTER_FIGURES = ("Figure2", "FigureS6_nineparam")

ALLOWED_FAMILIES = {
    "'Arial'",
    "'DejaVu Sans'",
    "'DejaVu Sans Display'",
    "'DejaVu Sans Oblique'",
    "'STIXSizeOneSym'",
    "'Arial', 'DejaVu Sans', sans-serif",
}


# --------------------------------------------------------------------- pdf --
def check_pdf(path):
    import fitz

    doc = fitz.open(path)
    page = doc[0]
    problems = []

    fonts = page.get_fonts(full=True)
    if not fonts:
        problems.append("no fonts listed")
    for f in fonts:
        if not f[1]:
            problems.append("font not embedded: %s" % f[3])

    w_in = page.rect.width / 72.0
    stem = os.path.basename(path)[:-4]
    variant = "_large" if stem.endswith("_large") else ""
    want = NOMINAL[variant]
    if w_in > want + OVER_MAX:
        problems.append("page %.2f in is wider than the designed %.2f in"
                        % (w_in, want))
    if w_in < want - TRIM_MAX:
        problems.append("page %.2f in is %.2f in narrower than designed"
                        % (w_in, want - w_in))

    fams = sorted({f[3].split("+")[-1] for f in fonts})

    n_img = 0
    worst = None
    for img in page.get_images(full=True):
        rects = page.get_image_rects(img[0])
        if not rects:
            continue
        n_img += 1
        r = max(rects, key=lambda q: q.width)
        dpi = img[2] / (r.width / 72.0)
        if worst is None or dpi < worst[0]:
            worst = (dpi, img[2], img[3], r.width / 72.0)

    if n_img and worst[0] < MIN_RASTER_DPI - 1:
        problems.append("raster content at %.0f dpi, below the %.0f dpi floor "
                        "(softest: %d x %d px over %.2f in)"
                        % (worst[0], MIN_RASTER_DPI, worst[1], worst[2],
                           worst[3]))
    if n_img and not stem.startswith(RASTER_FIGURES):
        problems.append("%d raster image(s) in a figure that draws none"
                        % n_img)

    doc.close()

    kind = "vector only" if not n_img else (
        "%d raster panel(s), lowest %.0f dpi" % (n_img, worst[0]))
    return ("%.2f in wide | %s | %d font(s) embedded: %s"
            % (w_in, kind, len(fonts), ", ".join(fams))), problems


# --------------------------------------------------------------------- svg --
_NUM = r"[-+]?[\d.]+(?:[eE][-+]?\d+)?"


def _mat_mul(a, b):
    return (a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1],
            a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
            a[0] * b[4] + a[2] * b[5] + a[4],
            a[1] * b[4] + a[3] * b[5] + a[5])


def _parse_transform(s):
    import math
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s):
        v = [float(t) for t in re.findall(_NUM, args)]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "scale":
            sx = v[0]
            sy = v[1] if len(v) > 1 else sx
            t = (sx, 0, 0, sy, 0, 0)
        elif name == "rotate":
            a = math.radians(v[0])
            c, s_ = math.cos(a), math.sin(a)
            t = (c, s_, -s_, c, 0, 0)
            if len(v) == 3:                       # rotate(a cx cy)
                cx, cy = v[1], v[2]
                t = _mat_mul((1, 0, 0, 1, cx, cy),
                             _mat_mul(t, (1, 0, 0, 1, -cx, -cy)))
        elif name == "matrix":
            t = tuple(v[:6])
        else:
            continue
        m = _mat_mul(m, t)
    return m


def _apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def check_svg(path):
    s = open(path, encoding="utf-8").read()
    problems = []

    if not re.search(r"<text\b", s):
        problems.append("no <text> elements: labels were converted to paths, "
                        "so the SVG is no longer editable")

    fams = set()
    for m in re.finditer(r"font-family:\s*([;\"])?\s*([^;\"]+)", s):
        fams.add(m.group(2).strip().replace("  ", " "))
    unknown = {f for f in fams if f not in ALLOWED_FAMILIES}
    if unknown:
        problems.append("undeclared font-family: %s"
                        % ", ".join(sorted(unknown)))

    vb = re.search(r'viewBox="(%s)\s+(%s)\s+(%s)\s+(%s)"' % ((_NUM,) * 4), s)
    if not vb:
        problems.append("no viewBox")
        return "no viewBox", problems
    x0, y0, vw, vh = (float(v) for v in vb.groups())

    # walk the tree, accumulating the transform of every <g>, and test each
    # <text>/<tspan> anchor in viewBox coordinates
    stack = [(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)]
    pos = 0
    outside = []
    n_text = n_tspan = 0
    for m in re.finditer(r"<(/?)(\w+)([^>]*?)(/?)>", s):
        closing, tag, attrs, selfclose = m.groups()
        if closing:
            if stack:
                stack.pop()
            continue
        ctm = stack[-1]
        tm = re.search(r'transform="([^"]*)"', attrs)
        if tm:
            ctm = _mat_mul(ctm, _parse_transform(tm.group(1)))
        if tag in ("text", "tspan"):
            xm = re.search(r'\sx="(%s)"' % _NUM, attrs)
            ym = re.search(r'\sy="(%s)"' % _NUM, attrs)
            if xm and ym:
                px, py = _apply(ctm, float(xm.group(1)), float(ym.group(1)))
                if not (x0 - 1.5 <= px <= x0 + vw + 1.5
                        and y0 - 1.5 <= py <= y0 + vh + 1.5):
                    outside.append((tag, round(px, 1), round(py, 1)))
            if tag == "text":
                n_text += 1
            else:
                n_tspan += 1
        if not selfclose:
            stack.append(ctm)

    if outside:
        problems.append("%d text anchor(s) outside the viewBox, e.g. %s"
                        % (len(outside), outside[:4]))

    inl = len(re.findall(r"<image\b", s))
    return ("%d <text>, %d <tspan>, %d font-family decl, %d inline raster, "
            "viewBox %.0f x %.0f" % (n_text, n_tspan, len(fams), inl, vw, vh)), \
        problems


def main():
    bad = 0
    for kind, fn, chk in (("PDF", "*.pdf", check_pdf),
                          ("SVG", "*.svg", check_svg)):
        print("=" * 100)
        print(kind)
        print("=" * 100)
        for p in sorted(glob.glob(os.path.join(FIGDIR, fn))):
            summary, problems = chk(p)
            print("%-28s %s" % (os.path.basename(p), summary))
            for pr in problems:
                print("%-28s   !! %s" % ("", pr))
            bad += len(problems)
    print("\n%s" % ("svg_pdf_audit: PASS" if not bad
                    else "svg_pdf_audit: FAIL (%d problem(s))" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
