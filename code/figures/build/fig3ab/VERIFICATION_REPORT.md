# Verification report — Fig. 3(a)/(b), shared Y axes (2026-11-12)

Supervisor's instruction: *"a, b 统一 Y 轴，只在 a 保留 Y 轴标题、刻度值及图例，b 不再重复显示。"*

Everything below is read from the build script and the CSV data — not from a
screenshot. Numbers are the ones written by `scripts/fig3ab_rebuild.py`
(`qa/qa_fig3ab.json`) and `scripts/verify_fig3ab.py` (`qa/verify_fig3ab.json`),
which read the exported PDFs, PNGs and SVGs back from disk.

---

## 1. Audit before the change (the four requested checks)

### 1.1 Upper (J–V) axis

| item | (a) | (b) | equal |
|---|---|---|---|
| ylim | −11.2 … 32.0 | −11.2 … 32.0 | yes |
| yticks | −10, 0, 10, 20 | −10, 0, 10, 20 | yes |
| scale | linear | linear | yes |
| tick marks | 3.0 pt, outward | 3.0 pt, outward | yes |

### 1.2 Lower (residual) axis

| item | (a) | (b) | equal |
|---|---|---|---|
| ylim | −7.1316 … 7.1316 | −7.1316 … 7.1316 | yes |
| yticks | −5, 0, 5 | −5, 0, 5 | yes |
| scale | linear | linear | yes |
| tick marks | 3.0 pt, outward | 3.0 pt, outward | yes |

### 1.3 Plot rectangles, heights, ratio and separator

| item | (a) | (b) |
|---|---|---|
| canvas | 3.30 × 2.70 in | 3.30 × 2.70 in |
| J–V axes box | x 0.62, y 1.04, w 2.62, h 1.48 in | identical |
| residual axes box | x 0.62, y 0.42, w 2.62, h 0.62 in | identical |
| upper : lower height ratio | 1.48 : 0.62 = 2.387 | identical |
| separator (J bottom = residual top) | y = 1.04 in | identical |

### 1.4 Against the data (not the screenshot)

| quantity | (a) | (b) | union the shared scale must hold |
|---|---|---|---|
| J min | −10.1387 (at 1.30 V) | −4.5756 (at 1.30 V) | −10.1387 |
| J max | 24.0949 (at 0.00 V) | 24.0907 (at 0.00 V) | 24.0949 |
| residual min | −0.0093 | −0.0030 | −0.0093 |
| residual max | 5.2827 (at 1.30 V) | 3.1241 (at 1.30 V) | 5.2827 |
| n points per curve | 131 | 131 | — |

**Conclusion of the audit:** the two panels already used one and the same
specification for both Y axes. Per instruction 二.1 the ranges and the tick
positions are therefore left untouched — nothing was re-scaled.

---

## 2. What was changed

Only subtractive, and only in (b):

* removed: the four upper Y tick numbers (−10, 0, 10, 20), the three lower Y
  tick numbers (−5, 0, 5), and the `Curve i` / `Curve j` legend;
* kept in (b): all seven Y tick **marks** (3.0 pt, outward), all spines, the
  dashed y = 0 line, both x tick numbers and both curves.

The axes are created with explicit `add_axes` rectangles and no layout engine
is involved, so removing text cannot widen or move a plot area — which is
confirmed independently in §3 and §4 below.

Nothing else was touched: same sample pairs (test indices 2890/5067 and
500/4560), same CSV rows, same residual direction (J_j − J_i, asserted to
< 1e-12), same colours (#4C72B0 solid / #DD8452 dashed), same line widths
1.3 / 1.2 / 1.1 pt, same dash pattern (4.0, 2.0).

---

## 3. Final axis values and clipping

### 3.1 Scales after the change

| | upper J–V axis | lower residual axis |
|---|---|---|
| ylim (both panels) | −11.2 … 32.0 | −7.1316 … 7.1316 |
| yticks (both panels) | −10, 0, 10, 20 | −5, 0, 5 |
| xlim / xticks (both) | 0.0 … 1.32 / 0, 0.5, 1 | same |

Y tick-mark positions coincide between (a) and (b) to **0.0 px** (measured
after rendering, `checks.shared_y.max_tick_mark_position_delta_px`).

### 3.2 Head-room, in points (no curve is clipped)

| panel | J bottom | J top | residual bottom | residual top |
|---|---|---|---|---|
| (a) | 2.62 | 19.50 | 22.29 | 5.79 |
| (b) | 16.34 | 19.51 | 22.31 | 12.54 |

All eight margins are positive; the smallest is 2.62 pt (panel (a), the
blue curve at 1.30 V against −11.2). That margin is the accepted 2026-11-11
geometry and was deliberately not altered. The large top head-room
(19.5 pt) is the space the legend occupies in (a); (b) keeps it so that the
two panels stay in register.

`checks.no_clipping` asserts every margin > 2 pt for both panels.

---

## 4. Alignment proof (a vs b)

### 4.1 Vector geometry, read back from the PDFs

Identical object-for-object between `Fig3a.pdf` and `Fig3b.pdf`
(`vector_frame.identical = true`). Coordinates in pt, origin bottom-left;
page 237.6 × 194.4 pt = 3.30 × 2.70 in.

| element | (a) | (b) |
|---|---|---|
| left spine | x = 44.64, y 30.24–74.88 and 74.88–181.44 | identical |
| right spine | x = 233.28, y 30.24–74.88 and 74.88–181.44 | identical |
| J–V top frame | y = 181.44, x 44.64–233.28 | identical |
| separator | y = 74.88, x 44.64–233.28 | identical |
| residual bottom | y = 30.24, x 44.64–233.28 | identical |
| residual y = 0 dashed line | y = 52.56, x 44.64–233.28 | identical |

### 4.2 Raster geometry, 600 dpi PNG / PDF render

Rows in the 1980 × 1620 px image that are > 80 % dark across the plot width
(the three frame lines):

| | row 1 | row 2 | row 3 |
|---|---|---|---|
| (a) | 107.5 px | 995.5 px | 1367.5 px |
| (b) | 107.5 px | 995.5 px | 1367.5 px |

i.e. J–V top = 2.520 in, separator = 1.040 in, residual bottom = 0.420 in
from the bottom of the canvas, in both files.

### 4.3 Text actually present in each PDF

| | (a) | (b) |
|---|---|---|
| Y tick numbers | −10, 0, 10, 20, −5, 5 | **none** |
| legend | Curve i, Curve j | **none** |
| x tick numbers | 0, 0.5, 1 | 0, 0.5, 1 |

The three x tick numbers sit at exactly the same PDF boxes in both files
(e.g. "0" at x 42.69–46.59 pt, y 168.33–176.16 pt), so the x axis did not
move either.

### 4.4 Pixel diff against the accepted 2026-11-11 exports

| file | differing pixels (> 8/255 at 600 dpi) | where |
|---|---|---|
| Fig3a | **0** | — (panel (a) is unchanged) |
| Fig3b | 11 736 = 0.366 % of the canvas | 5 501 in the left label margin, 6 235 in the legend box, **0 anywhere else** |

So in (b) the only ink that disappeared is the tick numbers and the legend;
no curve, tick mark, spine or dashed line changed by a single pixel. The
`Fig3a.png` file is even byte-identical to the previous delivery
(md5 `c8253bffb5d4c14df878dee416b7d135`); the PDF/SVG differ only in their
creation timestamp and auto-generated element ids.

---

## 5. Deliverables

| file | content |
|---|---|
| `figures/Fig3a.pdf` / `.png` / `.svg` | panel (a), vector + 600 dpi (1980 × 1620) |
| `figures/Fig3b.pdf` / `.png` / `.svg` | panel (b), same canvas |
| `preview/Fig3ab_preview.pdf` / `.png` | 6.82 × 3.10 in, (a) and (b) 0.10 in apart, with the PowerPoint titles drawn for checking only |
| `qa/alignment_overlay.png` / `.pdf` | both panels with the three frame rows and both spines drawn as guides |
| `qa/diff_b_vs_2026_11_11.png` | every pixel (b) lost, painted red |
| `qa/crops/` | left-edge crops of (a) and (b), upper-right corner comparison |
| `qa/qa_fig3ab.json`, `qa/verify_fig3ab.json` | all measurements above |
| `labels_and_caption.txt` | axis titles, do/don't-add notes and the caption sentence |

Assembly in PowerPoint: place both files at 100 % (3.30 × 2.70 in) with their
canvas edges adjacent. Because both carry the same 0.62 in left margin
whether or not numbers are drawn in it, all five horizontal edges coincide.

---

## 6. Caption sentence (English)

> Panels (a) and (b) share the same vertical scales, for both the J–V curves
> and the residuals, and the Curve i / Curve j legend in (a) applies to both
> panels.

(shorter: *"(a, b) share the J–V and residual ordinate scales; the legend in
(a) applies to both panels."*)

---

## 7. Not touched

Fig. 3(c), Fig. 3(d), Fig. 4, Fig. 5, the Word manuscript and the SI. No model
was re-run, no sample was re-selected, no data value was recomputed; the two
CSVs in `data_used/` are byte-identical to the 2026-11-11 package
(md5 `525c0d6b…` and `26458467…`). The original 2026-11-11 directory is
untouched.
