# -*- coding: utf-8 -*-
"""Dev helper (not delivered): raise every sub-7.0 pt in-figure text size to the
project floor FS_ANNOT = 7.0 pt, so that the delivered figures satisfy

    f_internal >= 0.3886 pt/cm x W_display      (audit: scripts/figure_font_audit.py)

at the manuscript column width. Pure textual substitution on the figure
scripts; every replacement count is asserted so a silent partial edit cannot
pass. Layout consequences are checked afterwards by scripts/qa_layout.py and by
eye on the re-rendered files.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PLAN = {
    "fig2_paired_recovery.py": [
        ("fontsize=st.FS_ANNOT - 0.4", "fontsize=st.FS_ANNOT", 2),
        ("fontsize=st.FS_ANNOT - 0.5", "fontsize=st.FS_ANNOT", 4),
    ],
    "fig4_forward.py": [
        ("fontsize=6.8,", "fontsize=st.FS_ANNOT,", 1),
        ("fontsize=st.FS_ANNOT - 1.0, color=st.INK, pad=2.0",
         "fontsize=st.FS_ANNOT, color=st.INK, pad=2.0", 1),
    ],
    "figs7_ecdf.py": [
        ("fontsize=st.FS_ANNOT - 1.4", "fontsize=st.FS_ANNOT", 2),
        ("fontsize=st.FS_ANNOT - 1.0)", "fontsize=st.FS_ANNOT)", 1),
        ("fontsize=st.FS_ANNOT - 0.6)", "fontsize=st.FS_ANNOT)", 1),
        ("fontsize=st.FS_ANNOT - 1.2, color=st.MUTED",
         "fontsize=st.FS_ANNOT, color=st.MUTED", 1),
    ],
    "fig3_neighbour.py": [
        ("fontsize=st.FS_ANNOT - 1.0,", "fontsize=st.FS_ANNOT,", 2),
        ("fontsize=st.FS_ANNOT - 1.6, color=st.INK",
         "fontsize=st.FS_ANNOT, color=st.INK", 1),
        ("fontsize=st.FS_ANNOT - 0.8, color=st.INK",
         "fontsize=st.FS_ANNOT, color=st.INK", 1),
        ("fontsize=st.FS_ANNOT - 0.6, color=st.INK",
         "fontsize=st.FS_ANNOT, color=st.INK", 1),
        ("fontsize=st.FS_ANNOT - 0.6, color=st.MUTED",
         "fontsize=st.FS_ANNOT, color=st.MUTED", 1),
        ("fontsize=st.FS_ANNOT - 0.8)", "fontsize=st.FS_ANNOT)", 1),
        ("fontsize=st.FS_LEGEND - 1.2,", "fontsize=st.FS_ANNOT,", 1),
        ("fontsize=st.FS_ANNOT - 0.5)", "fontsize=st.FS_ANNOT)", 1),
        ("fontsize=st.FS_ANNOT - 1.2,", "fontsize=st.FS_ANNOT,", 1),
    ],
}


def main():
    for name, pairs in PLAN.items():
        path = os.path.join(HERE, name)
        s = io.open(path, encoding="utf-8").read()
        for a, b, n in pairs:
            c = s.count(a)
            assert c == n, (name, a, c, n)
            s = s.replace(a, b)
        io.open(path, "w", encoding="utf-8", newline="").write(s)
        print("patched %-28s %d substitution rules" % (name, len(pairs)))


if __name__ == "__main__":
    main()
