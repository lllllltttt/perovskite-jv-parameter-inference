# Figure 4 (a)–(c) standalone panels — 2026-11-10

Three independently assembleable panels for the first part of Figure 4, plus a
1×3 proof, built from the plotting script and source data of the Figure 4 that
is currently in the manuscript. No screenshot was traced, no case was
re-selected, and neither the model nor COMSOL was re-run. **(d), (e), the
manuscript Word file and the SI were not touched.**

## Deliverables

| File | What it is |
| --- | --- |
| `figures/Fig4a.{png,pdf,svg}` | case 12058, lowest cycle gap — legend inside its main panel |
| `figures/Fig4b.{png,pdf,svg}` | case 595, median cycle gap |
| `figures/Fig4c.{png,pdf,svg}` | case 14499, highest cycle gap — keeps the 0–1.0 V inset |
| `figures/Fig4abc_preview_1x3.{png,pdf,svg}` | proof row at exactly 6.80 in, with the two titles the author adds at the left |
| `labels.txt` | the three panel titles, plus the two shared y-axis titles |
| `caption_draft.txt` | English caption draft for (a)–(c) only |
| `data_used/Figure4ac_plotting_values.csv` | per-case d_gap / d_dec / d_COM, y limits, tick values |
| `data_used/Figure4ac_curves.csv` | 131 rows: V and target / decoder / COMSOL / both residuals per case |
| `qa/geometry.json`, `qa/*.png` | measured geometry, and print-scale crops of the legend, inset and tail |

PNG is 900 dpi, PDF is Type-42 text, SVG keeps live text (no raster, no
text-as-path). Each panel file is 2.1267 × 2.1100 in.

## Provenance

* Plotting code inherited from
  `20261006/manuscript_figures_SI_integrated_v2_layout_final/scripts/fig4_forward.py`
  — `collect()` is imported and called, so every archived pin is re-asserted
  before a single stroke is drawn: case order 12058 / 595 / 14499, cycle gaps
  0.267519 / 2.562703 / 54.104513 mA cm⁻², RMSE medians, device-metric medians.
* Data: the frozen `final_figures/scripts/_frozen_preds.npz`, `J_scaler.pkl`
  and the per-sample COMSOL forward results — the same files the manuscript
  figure reads. No re-selection: the three cases come from the archive.
* Style: `figstyle.py` of the same package (Arial, Okabe–Ito colours, 0.8 pt
  spines, outward 3 pt ticks).
* Resampled numbers in the caption were read back from the plotted arrays:
  at 1.0 V in case (c) target 11.559, decoder 11.664, COMSOL 19.010 mA cm⁻².

## Geometry

* Canvas 2.1267 × 2.1100 in for all three; axes rectangles are identical
  fractions of that canvas (main y 0.384–0.597, residual 0.133–0.251,
  x 0.188–0.798), so after pasting, the top borders, the main/residual
  dividers and the bottom borders lie on the same three lines — verified in
  the exported PDFs, not only in the figure model.
* 0.42 in left gutter + three panels with zero gap = exactly 6.80 in, the
  manuscript column width. No panel is resized for its legend or inset.
* Main/residual height ratio 1.26 : 0.53; voltage 0–1.3 V with ticks
  0.0/0.5/1.0 printed only on the residual strips; no "Voltage (V)" title and
  no in-panel y-axis title (the author adds both once, at the left of the row).
* Residual: ΔJ = J_method − J_target, signed, never absolute. Limits ±1.30·rmax
  per case, ticks at −rmax / 0 / +rmax formatted `%.3g` — the manuscript
  figure's own residual convention, so the strips read the same way.

## Deliberate differences from the manuscript's Figure 4 (a)–(c)

1. **No in-panel numbers.** The d_gap / d_dec / d_COM block belongs in the
   caption now, so the 0.30 R band the manuscript reserved above the curves
   for that text is empty here and would shrink every curve inside its frame.
   Headroom was trimmed to 0.12 R; the minimum side (0.08 R below the lowest
   data point) is untouched, so no tail is cut. Case (c)'s axis still reaches
   −1847 mA cm⁻² for data that bottom out at −1709.
2. **(c)'s inset was moved up by 0.087 of the axes height** (0.048 → 0.135)
   and shortened to keep its top edge where the manuscript has it. In the
   manuscript the inset's x tick numbers 0.0/0.5/1.0 fall outside the axes
   box and are clipped; here they are complete, with 3.15 pt clearance above
   the divider, and its y tick numbers clear the main left spine by 5.16 pt.
   The 0–1.0 V window, the independent ticks and the in-inset unit are
   unchanged.
3. **Tick locator** `MaxNLocator(nbins=5)` replaces the default, which on the
   shorter standalone axes collapsed (c) to 0 / −1000 only.

## Verification

`python -I scripts/qa_fig4_abc.py` — **88 checks, 0 failures**:

* data: 131 points, 0–1.3 V; archived case order; each cycle gap reproduced to
  1e-9 from the plotted arrays; residual sign proved from the arrays;
* files: presence, 900 dpi, canvas size, single-page PDFs, common page size,
  SVG live text / no raster / no test-index title / no d_gap / no
  "Voltage (V)";
* alignment: the three border lines and the two spine lines are at identical
  coordinates in all three PDFs;
* (a): legend inside its axes and 0 curve samples under its box;
* (c): inset tick numbers clear the divider and the main spine, main axis
  keeps the full tail;
* caption: every number appears, and the 1.0 V triple matches the plotted data.

Visual check at the actual 6.80 in width (`qa/preview_actual_width_200dpi.png`
and the 600 dpi crops): legend legible and clear of the curves, (c) tail and
inset both readable, three residual strips aligned.

## Reproduce

```
python -I scripts/fig4_abc_standalone.py     # writes figures/, labels, caption, data_used/, qa/geometry.json
python -I scripts/qa_fig4_abc.py             # 88 checks
python -I scripts/render_printscale.py       # print-scale crops + 6.80 in proof
```

## Left to the author

Panel titles and the two left-hand axis titles are in `labels.txt`; the caption
draft is meant to be merged with the existing Fig. 4 caption for (d)/(e).
