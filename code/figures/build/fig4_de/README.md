# Figure 4 (d) and (e) standalone panels — 2026-11-10

Five net images for the lower half of the manuscript's Figure 4, redrawn from
the plotting script and the frozen per-sample data that the manuscript figure
itself reads. No value was traced from the screenshot, nothing was predicted
again, and COMSOL was not re-run. **(a)–(c) are untouched from the separate
`20261110_fig4_standalone` delivery, and neither the manuscript Word file nor
the SI was modified.**

## Deliverables

| File | What it is |
| --- | --- |
| `figures/Fig4d.{png,pdf,svg}` | three voltage windows, log axis, 2.600 × 2.200 in |
| `figures/Fig4e_Jsc.{png,pdf,svg}` | \|ΔJ_sc\|, mA cm⁻², 1.680 × 1.000 in |
| `figures/Fig4e_Voc.{png,pdf,svg}` | \|ΔV_oc\|, V |
| `figures/Fig4e_FF.{png,pdf,svg}` | \|ΔFF\|, dimensionless |
| `figures/Fig4e_FF_pp.{png,pdf,svg}` | the same panel in percentage points — see below |
| `figures/Fig4e_PCE.{png,pdf,svg}` | \|ΔPCE\|, pp |
| `preview/Fig4de_preview.{png,pdf}` | proof assembly, 6.80 × 2.84 in, the only file that carries text |
| `labels_and_caption.txt` | copy-paste text for PowerPoint, plus the caption paragraph |
| `data_used/Figure4d_per_sample.csv` | 135 rows: window, RMSE (mA cm⁻²) |
| `data_used/Figure4e_per_sample.csv` | 177 rows: metric, absolute deviation |
| `data_used/Figure4de_box_stats.csv` | quartiles, whisker ends, median, min/max, n |
| `qa/` | print-scale crops used for the visual check |

PNG 600 dpi · PDF with subset Arial TrueType (Type 42 semantics, `Identity-H`) ·
SVG with live `<text>`, no raster.

## Provenance

* `fig4_forward.collect()` of
  `20261006/manuscript_figures_SI_integrated_v2_layout_final/scripts` is
  imported and called, so the archived pins are re-asserted before anything is
  drawn: case order, cycle gaps, and the RMSE / device-metric medians.
* (d): per-sample `rmse_full`, `rmse_0to1V`, `rmse_gt1V` from
  `forward_validation_unbiased/forward_metrics_per_sample.csv` — the columns the
  manuscript panel plots.
* (e): the same per-sample device metrics as the manuscript panel,
  \|predicted − target\|, with V_oc at the first downward zero crossing.
* Style module `figstyle.py` of the same package: Arial, Okabe–Ito colours,
  0.8 pt spines, 3 pt outward ticks, 7.5 pt tick numbers.

## Verification of the checked numbers

| Check | Source value | Figure |
| --- | --- | --- |
| (d) medians | 2.692631 / 0.455349 / 5.191600 mA cm⁻² | same |
| (d) n | 45 per window | same |
| (e) medians | 0.111897 (n = 45) / 0.022439 / 0.015533 / 0.471401 | same |
| (e) n | 45, 44, 44, 44 | same |

FF is a fraction (median 0.0155) and the PCE deviation is already in
percentage points (median 0.4714); neither is multiplied by 100.

## Design decisions

1. **(d) log axis without pre-logging.** The data stay linear and the axis does
   the work: `set_yscale("log")` plus a `FixedLocator` at 0.01/0.1/1/10/100
   with plain-decimal labels, and `NullFormatter` on the minor ticks, so the
   five labelled decades are evenly spaced and nothing else is numbered.
2. **(d) limits.** 0.01–200. The >1.0 V group reaches 113.34 mA cm⁻², so a top
   of 100 would clip or crowd it; 200 keeps the 100 tick mid-axis. The bottom
   0.01 is just below the smallest RMSE (0.0163).
3. **Box statistics unchanged** from the manuscript call: quartiles at the 25th
   and 75th percentile, median line, whiskers at the most extreme sample within
   1.5 × IQR, `showfliers=False`. Raw points are therefore the only dots — the
   boxplot draws no second symbol for far samples.
4. **Box and points.** Translucent box fill (α = 0.22 of the group colour),
   black edge, black 1.0 pt median, black 0.7 pt whiskers and caps; points
   drawn 2.2 pt at α = 0.45 in the group colour, z-order above the box, jitter
   ±0.13 only (fixed seed, so the layout reproduces exactly).
5. **(e) axes.** Linear, from zero, independent per metric; the 1/2/2.5/4/5
   tick ladder picks a round step so that the labels are 3–5 equidistant
   numbers and the top tick is never below the largest sample. Matplotlib's
   `MaxNLocator` was rejected: it produced 0.8-wide (Jsc) and 0.6-wide (PCE)
   steps whose top tick fell below the data.
6. **No in-panel text.** (d) keeps its three category tick marks but no
   category names; (e) has no x numbers at all. Panel letters, metric names,
   units, n and medians are all in `labels_and_caption.txt`, because the author
   adds them as PowerPoint text boxes.
7. **One canvas per panel, exact print size.** Each file is drawn at its final
   inches (1 figure pt = 1 printed pt) with an explicit axes rectangle and no
   tight bbox. The four (e) canvases are identical and the left margin is one
   measured value for the widest tick column of all four ("0.00" and "0.12"),
   so the four frames land on the same pixels — PPT cannot misalign them.

## Verification

`python -I scripts/qa_fig4de.py` — **165 checks, 0 failed**:

* the six checked numbers above, read back from the plotted arrays;
* box statistics equal `matplotlib.cbook.boxplot_stats` (Q1/Q3, 1.5 IQR);
* every sample inside the axes in all five panels; the axis top above the
  maximum; zero flier markers; points' z-order above the boxes;
* (d): scale is log, ticks exactly 0.01/0.1/1/10/100 with decimal labels, no
  minor labels, no grid, three empty category ticks;
* (e): four axes rectangles and four frames identical to 1e-6 / 0.001 px,
  three or more equidistant ticks, y from zero, no x numbers, no grid;
* no text outside any net canvas; SVG live text with no baked-in label, unit
  or caption string; file sizes, dpi, page size; the text list contains every
  required phrase and never calls the whiskers a confidence interval.

Visual check at the real display size (`qa/preview_200.png`, and 600–700 dpi
crops of the (d) bottom band, the (e) 2 × 2 block and the top of the >1.0 V
group): no clipped point, points readable through the box, 7.5 pt numbers
legible, four (e) frames aligned.

## Variant: |ΔFF| in percentage points

`figures/Fig4e_FF_pp.{png,pdf,svg}` is the bottom-left panel with the fill-factor
deviation expressed in pp, for the case where the figure should read 0–8 rather
than 0.00–0.08. Built by `scripts/fig4e_ff_pp.py` from the same frozen values:
the deviation is multiplied by 100 exactly once (never divided by the true FF)
and the axis is scaled with it, so the panel is a drop-in replacement — same
1.680 × 1.000 in canvas, same axes rectangle to 1e-12, same 44 points at the
same jitter x, and the same box/whisker geometry scaled by 100 (relative
positions inside the frame are unchanged to 1e-12). Ticks are 0, 2, 4, 6, 8 and
the axis top is 8.16; the median is 1.5533 pp and the largest sample 6.4926 pp,
neither clipped. The old `Fig4e_FF.*` files are untouched.

`python -I scripts/qa_fig4e_ff_pp.py` — **40 checks, 0 failed**.

## Reproduce

```
python -I scripts/fig4de_standalone.py     # figures/, preview/, data_used/
python -I scripts/qa_fig4de.py             # 165 checks
python -I scripts/fig4e_ff_pp.py           # figures/Fig4e_FF_pp.*
python -I scripts/qa_fig4e_ff_pp.py        # 40 checks
```

## Left to the author

The panel letters, both axis titles, the three window names, the four metric
names, the units, n and the medians are in `labels_and_caption.txt`, together
with the English caption paragraph to append to Figure 4.
