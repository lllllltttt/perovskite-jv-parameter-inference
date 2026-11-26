# VECTOR_EXPORT_QC — editable-text SVG + vector PDF package

Date: 2026-08-24 · Scope: frozen main figures Fig1–Fig6 + SI S3 + SI
S_noise, journal + large variants. No scientific data touched; figures
re-rendered verbatim from the frozen scripts (see `scripts/vector_export.py`).

## Export settings (confirmed present in frozen `figure_style.py`)

| Setting | Value |
|---|---|
| `svg.fonttype` | `none` — SVG text written as `<text>/<tspan>`, never glyph paths |
| `pdf.fonttype` | `42` — TrueType (Type 42) embedded text in PDFs |
| `ps.fonttype` | `42` |
| `text.usetex` | `False` (matplotlib default; set explicitly in the driver) |
| `mathtext.fontset` | `dejavusans` (unchanged from frozen rendering) |
| primary font | **Arial** — resolved to `C:\Windows\Fonts\arial.ttf` (present, not faked) |
| mathtext glyphs | DejaVu Sans via the matplotlib mathtext fontset (frozen rendering; not a second design font) |
| save | SVG/PDF written directly from the matplotlib figure object; `bbox_inches=tight`; rasterized layers (hybrid only) at 600 dpi |

## PDF inspection

`pdffonts` is not installed on this Windows box; **PyMuPDF** is used as
the equivalent inspector (per-page font table: xref/ext/type/basefont +
embedded check). All PDFs verified: fonts embedded, no Type 3, text
layer selectable/extractable.

## Per-file results

| File | SVG `<text>` | text editable | PDF font(s) | raster layer | PASS |
|---|---|---|---|---|---|
| Fig1_workflow | 74 | yes (12/12 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), Arial-Italic [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig1_workflow_large | 74 | yes (12/12 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), Arial-Italic [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig2_arch_recon | 62 | yes (8/8 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Bold [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), STIXNonUnicode-Italic [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig2_arch_recon_large | 62 | yes (8/8 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Bold [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), STIXNonUnicode-Italic [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig3_recoverability | 67 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | hybrid scatter (9 image) | PASS |
| Fig3_recoverability_fullvector | 67 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none (full vector) | PASS |
| Fig3_recoverability_hybrid | 67 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | dense-scatter raster layer only | PASS |
| Fig3_recoverability_large | 68 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | hybrid scatter (9 image) | PASS |
| Fig3_recoverability_large_fullvector | 68 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none (full vector) | PASS |
| Fig3_recoverability_large_hybrid | 68 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | dense-scatter raster layer only | PASS |
| Fig4_final | 54 | yes (4/4 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig4_final_large | 54 | yes (4/4 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig5_final | 96 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | hybrid scatter (1 image) | PASS |
| Fig5_final_fullvector | 96 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none (full vector) | PASS |
| Fig5_final_hybrid | 96 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | dense-scatter raster layer only | PASS |
| Fig5_final_large | 100 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | hybrid scatter (1 image) | PASS |
| Fig5_final_large_fullvector | 100 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none (full vector) | PASS |
| Fig5_final_large_hybrid | 100 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | dense-scatter raster layer only | PASS |
| Fig6_noise_forward | 77 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none | PASS |
| Fig6_noise_forward_large | 84 | yes (5/5 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none | PASS |
| FigS3_cycle_cases | 76 | yes (7/7 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf) | none | PASS |
| FigS3_cycle_gap | 55 | yes (7/7 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf), DejaVuSansDisplay [TrueType(Type42)/CID](ttf) | none | PASS |
| FigS3_cycle_voltage | 19 | yes (6/6 probes) | Arial [TrueType(Type42)/CID](ttf), DejaVuSans [TrueType(Type42)/CID](ttf) | none | PASS |
| FigS_noise_detail | 48 | yes (4/4 probes) | Arial [TrueType(Type42)/CID](ttf), Arial-Bold [TrueType(Type42)/CID](ttf), DejaVuSans-Oblique [TrueType(Type42)/CID](ttf) | none | PASS |

## Mathtext note

Mathtext expressions (e.g. `$|\Delta J_{sc}|$`, `$S_{\log}$`, `$\mu_n$`)
are written by the SVG backend as ONE `<text>` element holding per-glyph
`<tspan>` runs — the accepted 'one text object / tspan group' form, not
per-glyph `<path>`s. The LaTeX source is even kept as an XML comment
(`<!-- $...$ -->`) above each element. Editing an axis label in
Illustrator/Inkscape selects the whole label; subscript runs are
adjustable in place. **No `_editabletext.svg` fallback is required**
(mathtext never degrades to paths under `svg.fonttype='none'`).

## Verdict

SVG audited: 24 · PDF audited: 24 · FAILING files: 0

**VECTOR/PDF EXPORT READY — YES**
