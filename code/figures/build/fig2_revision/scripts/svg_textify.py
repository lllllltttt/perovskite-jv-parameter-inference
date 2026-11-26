# -*- coding: utf-8 -*-
"""svg_textify.py -- turn the matplotlib SVG into an Illustrator-editable master.

Why this exists
---------------
With ``svg.fonttype = 'none'`` matplotlib keeps the glyphs as text, but every
math string is emitted as a *group* holding several ``<tspan>`` runs, each
carrying one absolute x per character::

    <g transform="translate(47.16 13.68)">
      <text>
        <tspan x="0 5.67 10.40 ..." y="-0.81">Shared scale   = (log  + log )/2</tspan>
        <tspan x="54.34 93.66 133.88" y="-0.81">app</tspan>
        <tspan x="83.07 86.38 ..." y="1.73">1010</tspan>
        ...
      </text>
    </g>

In Illustrator that is a string of separately-positioned glyphs whose reading
order is scrambled; clicking into it gives fragments, and editing a word
destroys the line. This script rewrites every math label as ONE ``<text>``
element whose content is the logical string, with ordinary inline ``<tspan>``
runs for italics and for sub/superscripts (font-size + dy), no per-character
x lists and no outlines.

The label strings, colours, sizes, anchors and rotations come from the
registry that fig2_build.py wrote while drawing -- they are not re-parsed from
the SVG, so no information is lost in translation. What IS read from the SVG is
the baseline offset matplotlib applied to each math group (it places the group
origin at the bottom of the text box, not at the baseline).

Outputs
-------
figures/Figure2_editable.svg      the master for Illustrator
work/textify_report.txt           what was replaced, and the structural checks
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = os.path.join(OUT, "figures", "Figure2_revision_raw.svg")
DST = os.path.join(OUT, "figures", "Figure2_editable.svg")
REG = os.path.join(OUT, "work", "fig2_math_registry.json")
REPORT = os.path.join(OUT, "work", "textify_report.txt")

FONT = "Arial"
SUB_SCALE = 0.70        # mathtext shrink factor
SUB_DY = 0.2031         # figure-pt below the baseline, per pt of base size
SUP_DY = -0.697         # above the baseline

ANCHOR = {"left": "start", "center": "middle", "right": "end"}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def group_extent(s, start):
    """End index of the <g ...> element that starts at ``start``."""
    depth = 0
    for m in re.finditer(r"<g\b[^>]*>|</g>", s[start:]):
        if m.group(0) == "</g>":
            depth -= 1
            if depth == 0:
                return start + m.end()
        else:
            depth += 1
    raise ValueError("unbalanced <g> at %d" % start)


def tspan_rows(inner):
    """(font size, baseline y) for every tspan, in either matplotlib layout.

    matplotlib 3.9 writes one tspan per run with ``style="font: 8.5px 'Arial'"``
    and an x list; 3.10 writes one tspan per glyph with ``style="font-size:
    8.5px; ..."``. Both carry the baseline y that this script needs.
    """
    for m in re.finditer(r"<tspan\b([^>]*)>", inner):
        attrs = m.group(1)
        st = re.search(r'style="([^"]*)"', attrs)
        st = st.group(1) if st else ""
        fm = re.search(r"font:\s*(?:\d+\s+)?([\d.]+)px", st)
        if not fm:
            fm = re.search(r"font-size:\s*([\d.]+)px", st)
        ym = re.search(r'\by="([-\d.eE]+)"', attrs)
        if fm and ym:
            yield float(fm.group(1)), float(ym.group(1))


def main_baseline(inner):
    """Baseline offset matplotlib used for the main (largest) glyph run."""
    rows = list(tspan_rows(inner))
    if not rows:
        raise ValueError("no tspan rows found")
    big = max(r[0] for r in rows)
    ys = {y for size, y in rows if abs(size - big) < 1e-9}
    if len(ys) != 1:
        raise ValueError("ambiguous baseline: %r" % (ys,))
    return ys.pop()


def runs_to_svg(runs, size):
    """One logical label -> inline <tspan> content with no absolute positions."""
    groups, cur = [], None
    for kind, text in runs:
        if kind in ("sp", "sp2", "sp3"):
            text = {"sp": " ", "sp2": "  ", "sp3": "   "}[kind]
            ital, shift = False, 0
        elif kind == "i":
            ital, shift = True, 0
        elif kind == "r":
            ital, shift = False, 0
        elif kind == "op":
            text, ital, shift = text, False, 0
        elif kind in ("sub", "subi"):
            ital, shift = (kind == "subi"), 1
        elif kind in ("sup", "supi"):
            ital, shift = (kind == "supi"), -1
        else:
            raise ValueError(kind)
        if cur is not None and cur[0] == ital and cur[1] == shift:
            cur[2].append(text)
        else:
            cur = (ital, shift, [text])
            groups.append(cur)

    off_of = {0: 0.0, 1: SUB_DY * size, -1: SUP_DY * size}
    out, cur_off = [], 0.0
    for ital, shift, chunks in groups:
        text = "".join(chunks)
        if not text:
            continue
        target = off_of[shift]
        delta = target - cur_off
        tsize = size * (SUB_SCALE if shift else 1.0)
        attrs = []
        if abs(delta) > 1e-9:
            attrs.append('dy="%.4f"' % delta)
            cur_off = target
        if abs(tsize - size) > 1e-9:
            attrs.append('font-size="%.4g"' % tsize)
        if ital:
            attrs.append('font-style="italic"')
        body = esc(text)
        out.append("<tspan %s>%s</tspan>" % (" ".join(attrs), body)
                   if attrs else body)
    return "".join(out)


def main():
    svg = open(SRC, encoding="utf-8").read()
    reg = json.load(open(REG, encoding="utf-8"))["labels"]

    blocks = []
    for m in re.finditer(r'<g id="text_(\d+)">', svg):
        end = group_extent(svg, m.start())
        inner = svg[m.end():end]
        if 'transform="translate(' in inner:
            blocks.append((m.start(), end, inner))

    if len(blocks) != len(reg):
        raise SystemExit("math groups in svg = %d, registry = %d"
                         % (len(blocks), len(reg)))

    edits, log = [], []
    for (start, end, inner), lab in zip(blocks, reg):
        gid = re.search(r'<g id="(text_\d+)">', svg[start:end]).group(1)
        size = float(lab["size"])
        ty = float(re.search(r'transform="translate\(([-\d.eE]+) '
                             r'([-\d.eE]+)\)', inner).group(2))
        baseline = ty + main_baseline(inner)     # svg y grows downwards
        x = lab["ax"]
        roty = lab["rot"]
        attrs = ['x="%.4f"' % x, 'y="%.4f"' % baseline,
                 'font-family="%s"' % FONT, 'font-size="%.4g"' % size,
                 'fill="%s"' % lab["color"],
                 'text-anchor="%s"' % ANCHOR[lab["ha"]],
                 'xml:space="preserve"']
        if roty:
            attrs.append('transform="rotate(%.1f %.4f %.4f)"'
                         % (-roty, x, baseline))
        body = runs_to_svg(lab["runs"], size)
        new = ('<g id="%s">\n <text %s>%s</text>\n</g>'
               % (gid, " ".join(attrs), body))
        edits.append((start, end, new))
        log.append("%-8.2f %-8.2f %s" % (x, baseline,
                                         re.sub(r"<[^>]+>", "", body)))

    for start, end, new in reversed(edits):
        svg = svg[:start] + new + svg[end:]

    # tick labels and panel letters are already single <text> objects; only
    # unpack matplotlib's CSS style (fill + font shorthand + anchor) into plain
    # attributes so Illustrator shows them as ordinary text, and drop the no-op
    # rotate(-0 ...) transforms.
    def unpack_style(m):
        body = m.group(1)
        out, fam, size, weight = [], None, None, None
        for part in (p.strip() for p in body.split(";")):
            if not part:
                continue
            key, _, val = part.partition(":")
            key, val = key.strip(), val.strip()
            if key == "fill":
                out.append('fill="%s"' % val)
            elif key == "text-anchor":
                out.append('text-anchor="%s"' % val)
            elif key == "font":                      # matplotlib 3.9 shorthand
                mm = re.match(r"(?:(700)\s+)?([\d.]+)px\s*'([^']+)'", val)
                if not mm:
                    raise ValueError("unparsed font: %r" % val)
                weight, size, fam = mm.groups()
            elif key == "font-size":                 # matplotlib 3.10 longhand
                size = val.replace("px", "").strip()
            elif key == "font-family":
                fam = val.split(",")[0].strip().strip("'\"")
            elif key == "font-weight":
                weight = val
            else:
                out.append('style="%s:%s"' % (key, val))
        if fam:
            out.insert(0, 'font-family="%s"' % fam)
        if size:
            out.insert(1, 'font-size="%s"' % size)
        if weight:
            out.insert(2, 'font-weight="%s"' % weight)
        return " ".join(out)

    svg = re.sub(r'style="([^"]*\bfont[^"]*)"', unpack_style, svg)
    svg = re.sub(r'style="fill: ([^";]+)"', r'fill="\1"', svg)
    svg = re.sub(r' transform="rotate\(-0 [^"]+\)"', "", svg)

    open(DST, "w", encoding="utf-8").write(svg)

    # ---- structural checks on the delivered file ---------------------------
    txt = open(DST, encoding="utf-8").read()
    per_char = len(re.findall(r'<tspan[^>]*x="[^"]*\s[^"]*"', txt))
    n_text = len(re.findall(r"<text\b", txt))
    n_tspan = len(re.findall(r"<tspan\b", txt))
    # nothing was converted to outlines: the path count must be unchanged and
    # no glyph-path definitions may appear
    n_path = (len(re.findall(r"<path\b", txt)),
              len(re.findall(r"<path\b", open(SRC, encoding="utf-8").read())))
    leftover_groups = len(re.findall(r'<g id="text_\d+">', txt))
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("source : %s\n" % SRC)
        fh.write("output : %s\n\n" % DST)
        fh.write("math labels rewritten : %d\n" % len(edits))
        fh.write("<text> elements       : %d\n" % n_text)
        fh.write("<tspan> elements      : %d\n" % n_tspan)
        fh.write("per-character x lists : %d (must be 0)\n" % per_char)
        fh.write("<path> raw / out       : %d / %d (must be equal)\n" % n_path)
        fh.write("text groups kept      : %d\n" % leftover_groups)
        fh.write("\nlabel baselines and plain text:\n")
        fh.write("\n".join(log) + "\n")

    print("wrote", DST)
    print("math labels rewritten:", len(edits))
    print("<text> %d   <tspan> %d   per-char x lists %d"
          % (n_text, n_tspan, per_char))
    if per_char:
        raise SystemExit("per-character positioning survived")


if __name__ == "__main__":
    main()
