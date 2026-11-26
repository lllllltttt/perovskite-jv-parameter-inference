# -*- coding: utf-8 -*-
"""fig3_color_sync.py -- bring Figure 3's a/r colours in line with Figure 2.

Judgement (recorded in PATCH_NOTES as well)
-------------------------------------------
Figure 3 uses one blue and one orange for two different things:

  * panel (c) -- the only place in Figure 3 where colour means "shared scale a"
    vs "electron-hole log-ratio r", i.e. the same meaning as everywhere in the
    new Figure 2. Its legend says exactly that.
  * panels (a), (b) -- the same two hex values distinguish curve i from curve j
    within one case, and panel (d) uses them for pair (a) vs pair (b). Those are
    different objects; recolouring them would rewrite a meaning the reader has
    already been taught, so they keep their colours.

Therefore only panel (c)'s two bar colours (and the two legend swatches that
belong to them) are switched to Seaborn deep[0]/deep[1] (#4C72B0 / #DD8452).
Nothing else about Figure 3 is touched: same script, same data, same layout, so
every other pixel is unchanged by construction.

The original Figure 3 is read-only; this writes a new copy into the revision
directory.
"""
import os
import shutil
import sys

SRC_SCRIPTS = (r"E:\project\work1\20261006"
               r"\manuscript_figures_SI_integrated_v2_layout_final\scripts")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
RAWOUT = os.path.join(OUT, "figures", "fig3_sync")
FIGDIR = os.path.join(OUT, "figures")

sys.path.insert(0, SRC_SCRIPTS)

import fig3_neighbour as f3          # noqa: E402  (module-level CSVs are read)

C_A = "#4C72B0"      # seaborn deep[0]
C_R = "#DD8452"      # seaborn deep[1]


def main():
    os.makedirs(RAWOUT, exist_ok=True)
    print("original a/r colours:", f3.C_SHARED, f3.C_RATIO)
    print("panel (a)/(b)/(d) colours (kept):", f3.C_CURVE1, f3.C_CURVE2)
    f3.C_SHARED, f3.C_RATIO = C_A, C_R
    f3.FIGDIR = RAWOUT
    f3.build("journal")
    f3.build("large")
    for ext in ("png", "pdf", "svg"):
        src = os.path.join(RAWOUT, "Figure3." + ext)
        dst = os.path.join(FIGDIR, "Figure3_synced." + ext)
        shutil.copyfile(src, dst)
        print("wrote", dst)


if __name__ == "__main__":
    main()
