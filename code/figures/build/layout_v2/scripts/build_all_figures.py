# -*- coding: utf-8 -*-
"""Rebuild every delivered figure, in one pass, in a fixed order.

    python scripts/build_all_figures.py

Writes, for each figure, the three formats the submission needs:

    figures/<Name>.pdf        vector, Type-42 embedded (pdf.fonttype 42)
    figures/<Name>.svg        editable vector (svg.fonttype "none")
    figures/<Name>.png        600 dpi raster (the "high-resolution PNG")

`<Name>` is the journal-size render (7.09 in wide, the authoring width the
legibility law is written against) or `<Name>_large` (9.50 in), which carries
the same artwork for slide or poster use.

The order matters only in that fig3_neighbour and figs7_ecdf read the tables
that si_table_s6_stats.py writes; run that first if data_used/ is empty.

Two gates must pass on the result and are run separately, because a build that
"worked" is not a layout that is right:

    python scripts/qa_layout.py            text past the canvas, text-on-text
    python scripts/figure_font_audit.py    smallest in-figure type, legibility
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SIZES = ("journal", "large")


def main():
    t0 = time.time()
    import fig1_workflow
    import fig2_paired_recovery
    import fig3_neighbour
    import fig4_forward
    import fig5_intervals
    import figS6_nineparam
    import figs7_ecdf

    for size in SIZES:
        print("\n===== size: %s =====" % size)
        fig1_workflow.build(size)
        coords, _ = fig2_paired_recovery.load()
        fig2_paired_recovery.build(size, coords)
        fig3_neighbour.build(size)
        fig4_forward.build(size)
        fig5_intervals.build(size)
        figS6_nineparam.build(size)
    figs7_ecdf.main()          # both sizes internally

    print("\nbuilt 14 renders in %.1f s; now run qa_layout.py and "
          "figure_font_audit.py" % (time.time() - t0))


if __name__ == "__main__":
    main()
