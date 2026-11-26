# Figure 5 — five standalone panels and an assembled preview (2026-11-10)

Rework of the manuscript's Figure 5 for PowerPoint assembly, in the same way as
the Figure 4 delivery: I draw and export the panels, the author assembles them
and adds the panel letters, the panel titles and the axis names as text boxes.

No number was retrained, re-predicted or read from a screenshot. The arrays
come from `fig5_intervals.load()` of the manuscript package, which re-asserts
every archived pin (the S15/S17/S17b tables and the noise-robustness CSVs) be-
fore returning them, so the plotted values are the ones the manuscript's own
Figure 5 plots. **The manuscript's Figure 5 files, the Word text and the SI are
untouched.**

## Deliverables

| File | What it is |
| --- | --- |
| `figures/Fig5a.{png,pdf,svg}` | marginal coverage vs nominal level, 2.00 × 1.75 in |
| `figures/Fig5b.{png,pdf,svg}` | 95 % interval score dot plot, 2.00 × 1.75 in |
| `figures/Fig5c.{png,pdf,svg}` | correlation vs noise, 2.00 × 1.50 in |
| `figures/Fig5d.{png,pdf,svg}` | 95 % coverage vs noise, 2.00 × 1.50 in |
| `figures/Fig5e.{png,pdf,svg}` | % change of mean σ_θ vs noise, 2.00 × 1.50 in |
| `legends/Fig5_param_legend.{png,pdf,svg}` | the shared nine-parameter key, uncropped |
| `legends/Fig5b_marker_legend.{png,pdf,svg}` | the (b) three-symbol key, uncropped |
| `legends/Fig5_color_map.{png,pdf,svg}` | marker / colour / family table |
| `preview/Fig5_preview.{png,pdf}` | 6.80 × 4.70 in lettered assembly — the only files that carry text |
| `labels_and_caption.txt` | copy-paste axis names, units, subscript notes, caption |
| `data_used/Figure5_plotting_values.csv` | every plotted number, long format |
| `data_used/Figure5_color_map.csv` | the colour/marker mapping |
| `qa/crop_*.png` | print-scale crops used for the visual checks |

PNG 600 dpi · PDF TrueType Arial (Type 42) · SVG with live `<text>`, no raster.

## What the original draws (verified before redrawing)

* **(a)** plots all nine parameters individually — there is no aggregate or
  mean curve in the source (`for i in range(9)` over `cov[9, 4]`), so nothing
  was split or merged.
* **(b)** shows three symbols: the open circle is the fixed training-quantile
  baseline, the filled dot the model's interval, and the orange ring is the
  frozen `raw_worse_than_prior` flag — true for **τ_ETL and r_rad only**.
  "Worse" means the model's 95 % interval score is not lower than the
  baseline's; the score is in physical log₁₀ units and lower is better.
* **(c–e)** use the five measured noise levels 0, 0.2, 0.5, 1 and 2 % of each
  curve's |J_sc|, added at all 131 voltage points and averaged over 30
  realizations. (e) is 100 × [σ_θ(noisy)/σ_θ(clean) − 1], a percentage of the
  clean-input value, **not** percentage points.

## Design decisions

1. **One palette, two chart families.** (a),(c),(d),(e) share a four-family,
   two-shade code — μ_n/μ_p blue `#004488`/`#6BA0D2`, τ_n/τ_p orange
   `#A85400`/`#D08F45`, N_c/N_v teal-green `#06695A`/`#55AE9C`,
   τ_ETL/τ_HTL purple `#5B2C83`/`#A98BC9`, r_rad grey `#333333` — with the
   dark member a filled circle and the light member a filled square, in every
   panel. Panel (b) keeps its semantic grey/blue/orange code.
2. **The key appears once.** Nine entries, two columns, inside (e) at the
   lower left, each family pair on one row and r_rad alone on the last row.
   Matplotlib fills a two-column legend column by column, so the handle order
   is `[μ_n, τ_n, N_c, τ_ETL, r_rad | μ_p, τ_p, N_v, τ_HTL]`. The nearest
   marker keeps **5.8 pt** of clearance (measured), so the key covers no
   curve; (a)'s empty lower-right corner was the fallback and was not needed.
3. **(a) is a percent axis.** Ticks 50–100, the four measured levels at their
   true positions (50, 80, 90, 95) with room to the right of the 95 points,
   and the ideal line is **y = x/100** over the whole frame (checked to 1e-12
   in the QA). No point was moved.
4. **(c)(d)(e) share one x axis**: same limits, same ticks 0 / 0.5 / 1.0 /
   1.5 / 2.0, and the five measured levels at their true positions — the 0.2 %
   case sits between 0 and 0.5, and 1.5 is a tick with no data.
5. **Equal plot areas for (c)(d)(e).** One left margin is measured for the
   widest tick column of the three and applied to all three, so the axes
   rectangles and the frame pixels are identical and the three images line up
   in PowerPoint without nudging.
6. **A reserved gutter for the y title.** Every canvas keeps 0.20 in of white
   on the left; the tick numbers start after it. The PowerPoint y title sits
   on that gutter, which is why the frame does not move when the text is added.
7. **Nothing else is baked in.** No panel letters, no panel titles, no axis
   titles, no caption. The only in-figure text is the tick numbers, the (e)
   key, the (b) legend words and the nine parameter names of (b) (the y axis of
   a dot plot).
8. **Canvas, not bbox.** Each panel is drawn at its final inches
   (1 figure pt = 1 printed pt) with an explicit `add_axes` rectangle and no
   `bbox_inches="tight"`, so PNG, PDF and SVG are the same size and nothing is
   rescaled on the way into PowerPoint.

## Verification

`python -I scripts/qa_fig5.py` — **160 checks, 0 failed**:

* provenance: the plotted arrays equal the archived lists (the two interval-
  score lists agree to their 6-dp archive precision, max 1.3e-6), 9 × 4 and
  9 × 5 shapes, the worse flag exactly on τ_ETL and r_rad, the 0 % column
  exactly zero;
* file set, canvas size, 600 dpi, PDF page size, embedded Arial, SVG live text
  and no raster;
* SVG text content: (a) exactly twelve tick numbers, (c–e) the five x labels
  and their y labels, (b) the four x numbers plus the nine parameter names,
  and **no** panel letter, axis name or caption word in any net panel;
* geometry: (c)(d)(e) identical axes rectangles to 1e-12 and identical frame
  pixels, data at the true positions, nothing at 1.5, reference lines at
  y = x/100, 0.95 and 0, no marker outside a frame, no grid, no text below
  6.5 pt, no text outside a canvas;
* both keys: the right entries, two columns, pair-per-row, no marker inside
  either box, 5.8 pt and 15.9 pt nearest-marker clearance;
* the data tables and the text list.

`python -I scripts/qa_crops.py` writes the print-scale crops used for the three
visual checks: `crop_e_key.png` (key vs curves), `crop_a_families.png` and
`crop_a_50.png` (dark/light pairs), `crop_a_9095.png`, `crop_c_0_02.png`,
`crop_d_0_02.png` (0 vs 0.2 % still separate). At 90 % and 95 % the nine (a)
curves span only 0.022 of coverage ≈ 4 pt of print height, i.e. barely more
than one marker, so they necessarily overlap there; at 50 % they spread over
14 pt and read separately. That is the data, not the drawing.

## Reproduce

```
set SRC=20261006\manuscript_figures_SI_integrated_v2_layout_final\scripts
python -I scripts/fig5_standalone.py    # figures/, legends/, preview/, data_used/
python -I scripts/qa_fig5.py            # 160 checks
python -I scripts/qa_crops.py           # qa/crop_*.png
```

## Left to the author

The panel letters, the three axis titles, the (e) y title and the caption are
in `labels_and_caption.txt`, each written out for the panel it belongs to,
including the subscript notes for J_sc, σ_θ, r_rad, τ_ETL and τ_HTL.
