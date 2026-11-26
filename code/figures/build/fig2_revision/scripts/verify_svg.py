# -*- coding: utf-8 -*-
"""verify_svg.py -- what was and was not verified for Figure2_editable.svg.

Checked here
------------
1. structure: every math label is ONE <text>; no per-character x lists remain;
   no glyph was turned into a <path>; the path/use counts are unchanged.
2. rendering: the raw matplotlib SVG and the rebuilt one are both rendered by
   the same browser engine (Edge, headless) and compared. Any label that moved
   or reflowed shows up as a mismatch; the report gives the ink extent of the
   text bands in both renders.

NOT checked here: behaviour inside Adobe Illustrator itself. Illustrator is not
installed on this machine, so nothing is claimed about it beyond the structure
of the file (live <text> with inline <tspan> runs, standard font attributes).
"""
import os
import re
import subprocess

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
RAW = os.path.join(OUT, "figures", "Figure2_revision_raw.svg")
EDIT = os.path.join(OUT, "figures", "Figure2_editable.svg")
WORK = os.path.join(OUT, "work")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
REPORT = os.path.join(WORK, "svg_verification.txt")

# The screenshot is 2x device pixels of a 4/3 px-per-pt layout, i.e. 192 px
# per inch of the 6.8 x 7.26 in figure. Bands are given in inches and converted
# here so they stay right if the layout is retuned.
PPI = 192.0
BANDS_IN = {
    "row-1 group label": (0.06, 0.28, 0.30, 6.60),
    "row-1 column names": (0.38, 0.64, 0.35, 6.60),
    "row-1 x labels":    (2.80, 2.95, 0.30, 6.60),
    "row-2 group label": (3.02, 3.24, 0.30, 6.60),
    "rho (a1)":          (2.36, 2.50, 1.60, 2.26),
    "shared legend":     (5.55, 5.76, 1.20, 5.60),
    "bar values (c)":    (5.95, 6.35, 0.30, 3.30),
    "bar categories":    (7.12, 7.22, 0.30, 6.60),
}
BANDS = {k: (int(a * PPI), int(b * PPI), int(c * PPI), int(d * PPI))
         for k, (a, b, c, d) in BANDS_IN.items()}


def render(svg, png):
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=800,800",
                    "--screenshot=" + png, "file:///" + svg.replace("\\", "/")],
                   check=True, capture_output=True)
    return Image.open(png).convert("L")


def ink(img, r0, r1, c0, c1, thr=200):
    sub = np.asarray(img, int)[r0:r1, c0:c1]
    cols = np.where((sub < thr).any(0))[0]
    rows = np.where((sub < thr).any(1))[0]
    if not len(cols):
        return None
    return (c0 + int(cols.min()), c0 + int(cols.max()),
            r0 + int(rows.min()), r0 + int(rows.max()))


def main():
    raw_txt = open(RAW, encoding="utf-8").read()
    ed_txt = open(EDIT, encoding="utf-8").read()

    n_text = len(re.findall(r"<text\b", ed_txt))
    n_math_groups = raw_txt.count('transform="translate(') - 0
    per_char = len(re.findall(r'<tspan[^>]*x="[^"]*\s[^"]*"', ed_txt))
    paths_raw = len(re.findall(r"<path\b", raw_txt))
    paths_ed = len(re.findall(r"<path\b", ed_txt))
    use_raw = len(re.findall(r"<use\b", raw_txt))
    use_ed = len(re.findall(r"<use\b", ed_txt))
    img_raw = len(re.findall(r"<image\b", raw_txt))
    img_ed = len(re.findall(r"<image\b", ed_txt))

    a = render(RAW, os.path.join(WORK, "verify_raw.png"))
    b = render(EDIT, os.path.join(WORK, "verify_edit.png"))

    lines = []
    lines.append("Figure2_editable.svg -- verification\n")
    lines.append("structure")
    lines.append("  <text> elements            : %d" % n_text)
    lines.append("  math groups in raw svg     : %d" % n_math_groups)
    lines.append("  per-character x lists      : %d   (must be 0)" % per_char)
    lines.append("  <path>  raw / editable     : %d / %d   (equal => no text "
                 "was converted to outlines)" % (paths_raw, paths_ed))
    lines.append("  <use>   raw / editable     : %d / %d" % (use_raw, use_ed))
    lines.append("  <image> raw / editable     : %d / %d   (rasterised "
                 "scatter, unchanged)" % (img_raw, img_ed))
    lines.append("")
    lines.append("browser render (Edge 2x), ink extent per text band")
    lines.append("  %-20s %-26s %s" % ("band", "raw  (x0,x1,y0,y1)",
                                         "editable"))
    worst = 0.0
    for name, (r0, r1, c0, c1) in BANDS.items():
        ea, eb = ink(a, r0, r1, c0, c1), ink(b, r0, r1, c0, c1)
        if ea and eb:
            d = max(abs(ea[i] - eb[i]) for i in range(4))
            worst = max(worst, d)
            lines.append("  %-20s %-26s %s   max edge delta %d px"
                         % (name, str(ea), str(eb), d))
        else:
            lines.append("  %-20s %-26s %s" % (name, str(ea), str(eb)))
    lines.append("")
    lines.append("  largest edge delta over the sampled bands: %d px "
                 "(2x screenshot = %.2f pt)" % (worst, worst / 2.0 * 0.75))
    lines.append("")
    lines.append("Not verified: opening the file in Adobe Illustrator. "
                 "Illustrator is not available on this machine; the deliverable "
                 "is live text in the SVG sense (one <text> per logical label, "
                 "inline <tspan> runs, plain font attributes), not a "
                 "proof of Illustrator behaviour.")
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
