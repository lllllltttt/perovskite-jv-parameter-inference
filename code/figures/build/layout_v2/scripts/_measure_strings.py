# -*- coding: utf-8 -*-
"""Dev helper (not delivered): rendered width of a candidate label at a given
point size, on the same renderer the figures are drawn with. Used to size
strings against the layout slot they have to fit in (a Figure 1 panel-(c)
column is 0.322 x the panel width; a Figure 1 panel-(b) strip line must fit
0.992 of the panel width) instead of estimating characters x 0.5 em.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# figstyle must be imported FIRST: it is what selects Arial over matplotlib's
# DejaVu Sans default, and Arial is ~6% narrower. Measuring without it reports
# widths that do not occur in any delivered figure.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle as st  # noqa: E402,F401

STRINGS = [
    "0.01 nm", "Density of states", "Bulk lifetime", "Perovskite",
    "Nine inference targets", "paired electron–hole parameters",
    "generation variables  (Latin hypercube)",
    "log-uniform, inside each pair's range",
    "one shared $g$ and one $q$ per electron–hole pair",
    "$g$ and $q$ are the generation variables;",
    "directly sampled parameters", "schematic, not to scale",
    "FTO and Ag: contacts,",
    # --- Figure 1 panel (b) head/decoder box candidates ---------------------
    "Gaussian parameter head",
    "9 means $\\mu_\\theta$   +   9 scales $\\sigma_\\theta$",
    "9 means $\\mu_\\theta$ + 9 scales $\\sigma_\\theta$",
    "9 means, 9 scales, normalized $\\log_{10}$",
    "in normalized log$_{10}$ space",
    "reconstructs the J–V curve from $z$",
    "reconstructs the J–V curve",
    "reconstructs a J–V curve",
    "from $z$",
    "Encoder", "Decoder", "parameter vector", "normalized log$_{10}$",
    # panel (b) archive strip, current
    "archived data:  200,000 Latin-hypercube draws  $\\rightarrow$  "
    "102,046 retained curves  (51.0%)",
    "fixed split:  train 71,432   $\\cdot$   validation 15,307   "
    "$\\cdot$   test 15,307     normalization fitted on the retained set",
    # candidates
    "archived data:  200,000 Latin-hypercube draws",
    "$\\rightarrow$  102,046 retained curves  (51.0%)",
    "fixed split:  train 71,432   $\\cdot$   validation 15,307   "
    "$\\cdot$   test 15,307",
    "normalization fitted on the retained set",
    "archived data:  200,000 draws  $\\rightarrow$  102,046 retained (51.0%)",
    "fixed split:  71,432 train  $\\cdot$  15,307 validation  "
    "$\\cdot$  15,307 test",
    # panel (a) parameter column
    "generation variables  (Latin hypercube, 200,000 draws)",
    "generation variables  (Latin hypercube)",
    "generation variables",
    "(Latin hypercube, 200,000 draws)",
    "Density of states",
    "$\\mu_n,\\ \\mu_p$",
    "$N_c,\\ N_v$",
    "$\\tau_n,\\ \\tau_p$",
    # panel (b) J-V input captions
    "131 currents", "131 points", "J–V input", "0 – 1.3 V",
    # panel (c) middle column
    "$\\mu_\\theta$  $\\rightarrow$  inverse scaling  "
    "$\\rightarrow$  $10^{x}$",
    "$\\mu_\\theta$  $\\rightarrow$  inverse scaling",
    "$\\rightarrow$  $10^{x}$",
    "$\\hat{\\theta}$   (physical units)",
    "the decoder curve is not used here",
    "•  coordinate prediction correlation",
    "reported as",
    "compared with",
    "fixed constant, computed from the",
    "training-median baseline",
    "$\\mu_\\theta \\pm z_{1-\\alpha/2}\\,\\sigma_\\theta$",
    "1  Recovery of paired",
    "Figure 2g, 2h   $\\cdot$   Table S11",
]


def main():
    pt = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
    fig = plt.figure(figsize=(7.09, 2.0), dpi=100)
    r = fig.canvas.get_renderer()
    print("point size %.1f pt; canvas width 709 px = 7.09 in\n" % pt)
    for s in STRINGS:
        t = fig.text(0.5, 0.5, s, fontsize=pt)
        bb = t.get_window_extent(renderer=r)
        t.remove()
        print("   %7.1f px %7.1f pt   %r" % (bb.width, bb.width * 72 / 100.0, s))
    plt.close(fig)


if __name__ == "__main__":
    main()
