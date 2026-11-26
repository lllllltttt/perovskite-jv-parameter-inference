"""
vector_export.py — editable-text SVG + vector PDF export of the frozen
FINAL figure package (Fig1–Fig6, SI S3, SI S_noise), journal + large.

Export settings (VECTOR_AND_PDF_EXPORT) are already present in the frozen
style module `figure_style.py`, which every plotting script imports — this
driver *confirms* rather than re-adds them:

    svg.fonttype  = 'none'      -> <text>/<tspan> objects in SVG, never glyph paths
    pdf.fonttype  = 42          -> TrueType (Type 42) embedded text in PDFs
    ps.fonttype   = 42          -> (PostScript, unused here but kept for parity)
    font.family   = Arial       -> resolves to C:\\Windows\\Fonts\\arial.ttf (verified)
    mathtext.fontset = 'dejavusans'  -> mathtext stays editable text in SVG
    text.usetex   = False       -> (matplotlib default; set explicitly below)

Strategy: this driver does NOT edit any frozen plotting script. It runs each
frozen entry point unchanged while `figure_style.save_fig` is patched by an
export recorder, so the frozen PNG/PDF files under Fig1..SI/ are never
rewritten; all export artifacts are written under
`final_figures/vector{,_full,_hybrid}/`:

  vector/          every figure:  <stem>.svg (editable text) + <stem>.pdf
                                  (vector, Type-42 text) + <stem>.png (copy of
                                  the frozen 600-dpi PNG, byte-identical).
  vector_full/     only figures containing rasterized artists (Fig3 parity
                   scatter 15,307 samples; Fig5 collision scatter 7,666 pairs):
                   <stem>_fullvector.{svg,pdf} — dense scatter converted back
                   to vector paths (rasterized=False), everything else vector.
  vector_hybrid/   same figures: <stem>_hybrid.{svg,pdf} — the frozen as-is
                   build, where ONLY the dense scatter is a raster layer;
                   axes, labels, annotations, legends, reference lines stay
                   vector/text.

All SVG/PDF are saved directly from the matplotlib figure object
(no PNG-to-PDF, no whole-figure rasterization). bbox_inches='tight' matches
the frozen save settings. Rasterized layers (hybrid only) are rendered at
600 dpi so they stay crisp.

Usage:
    python scripts/vector_export.py
"""

import os
import sys
import shutil
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import figure_style as st
import matplotlib as mpl

# explicit (already the matplotlib default): no LaTeX pipeline, mathtext stays
# editable text objects in the SVG/PDF backends.
mpl.rcParams["text.usetex"] = False

BASE = os.path.dirname(HERE)  # final_figures/
VECTOR = os.path.join(BASE, "vector")
VFULL = os.path.join(BASE, "vector_full")
VHYB = os.path.join(BASE, "vector_hybrid")
for _d in (VECTOR, VFULL, VHYB):
    os.makedirs(_d, exist_ok=True)

LOG = []  # (basename, had_rasterized, n_rasterized_artists)


def _save_vector(fig, path):
    """Save one vector file (SVG or PDF) from the live figure object."""
    fmt = "pdf" if path.lower().endswith(".pdf") else "svg"
    fig.savefig(path, format=fmt, bbox_inches="tight", facecolor="white",
                dpi=600)  # dpi governs only embedded raster layers (hybrid)


def export_save(fig, out_stem, dpi=600, pdf=True, svg=False, transparent=False):
    """Recorder that replaces figure_style.save_fig during export runs.

    Same signature as figure_style.save_fig so every frozen script keeps
    working; writes export artifacts instead of (and never over) the frozen
    outputs.
    """
    base = os.path.basename(out_stem)
    written = []

    # 1) standard vector/ export: editable-text SVG + vector PDF + frozen PNG
    svg_p = os.path.join(VECTOR, base + ".svg")
    _save_vector(fig, svg_p)
    written.append(svg_p)
    if pdf:
        pdf_p = os.path.join(VECTOR, base + ".pdf")
        _save_vector(fig, pdf_p)
        written.append(pdf_p)
    png_src = out_stem + ".png"
    if os.path.exists(png_src):
        png_dst = os.path.join(VECTOR, base + ".png")
        shutil.copy2(png_src, png_dst)  # byte-identical to the frozen 600-dpi PNG
        written.append(png_dst)

    # 2) rasterized artists present? -> also full-vector + hybrid variants.
    #    (Frozen scripts: Fig3 parity scatter, Fig5 collision scatter.)
    rast = [a for a in fig.findobj()
            if hasattr(a, "get_rasterized") and a.get_rasterized()]
    if rast:
        # hybrid = the frozen as-is build (dense scatter raster layer only)
        for ext in (".svg", ".pdf"):
            if ext == ".pdf" and not pdf:
                continue
            p = os.path.join(VHYB, base + "_hybrid" + ext)
            _save_vector(fig, p)
            written.append(p)
        # full-vector = dense scatter demoted back to vector paths
        for a in rast:
            a.set_rasterized(False)
        for ext in (".svg", ".pdf"):
            if ext == ".pdf" and not pdf:
                continue
            p = os.path.join(VFULL, base + "_fullvector" + ext)
            _save_vector(fig, p)
            written.append(p)

    plt.close(fig)
    LOG.append((base, bool(rast), len(rast)))
    return written


# Patch the module attribute every script calls as `st.save_fig`.
st.save_fig = export_save


def main():
    import plot_Fig1_workflow as P1
    import plot_Fig2_arch_recon as P2
    import plot_Fig3_recoverability as P3
    import plot_Fig4_final as P4
    import plot_Fig5_final as P5
    import plot_Fig6_noise_forward as P6
    import plot_SI_S3_cycle_audit as PS3
    import plot_SI_noise_detail as PSD

    jobs = [
        ("Fig1", lambda: (P1.make_fig("journal"), P1.make_fig("large"))),
        ("Fig2", P2.main),
        ("Fig3", P3.main),
        ("Fig4", P4.main),
        ("Fig5", P5.main),
        ("Fig6", P6.main),
        ("SI S3 cycle audit", PS3.main),
        ("SI noise detail", PSD.main),
    ]
    for name, fn in jobs:
        try:
            fn()
            print("[ok] %s" % name)
        except Exception:
            print("[ERR] %s" % name)
            traceback.print_exc()

    plt.close("all")
    print("\nExported stems  (had_rasterized | #rasterized artists):")
    for base, r, n in LOG:
        print("  %-40s %-5s %d" % (base, r, n))
    print("total export records:", len(LOG))


if __name__ == "__main__":
    main()
