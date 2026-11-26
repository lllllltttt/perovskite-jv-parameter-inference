# Figure 2 final scatter assets (D density style)

Date: 2026-11-09
Scope: **assets only**. Six standalone scatter panels, two standalone colour
keys and one assembly preview, for manual assembly in PowerPoint /
Illustrator. The manuscript, the SI, the official Figure 2, the two bar
panels and the earlier D trial (`20261109_fig2_b3_trial_D`) are untouched.

## What is delivered

| file | content |
|---|---|
| `panels/a1_Mobility.*` | a1 Mobility, blue, True/Predicted a |
| `panels/a2_Bulk_lifetime.*` | a2 Bulk lifetime, blue |
| `panels/a3_Density_of_states.*` | a3 Density of states, blue |
| `panels/b1_Mobility.*` | b1 Mobility, orange, True/Predicted r |
| `panels/b2_Bulk_lifetime.*` | b2 Bulk lifetime, orange |
| `panels/b3_Density_of_states.*` | b3 Density of states, orange |
| `colorbars/Colorbar_shared_scale_blue.*` | shared blue count key, 1 … 23 |
| `colorbars/Colorbar_log_ratio_orange.*` | shared orange count key, 1 … 31 |
| `preview/Figure2_assembly_preview.png` | two rows assembled, all annotation |
| `labels.txt` | copy-ready id, title, unit, axis names and rho |
| `checklist.csv` | xlim, ylim, ticks, n plotted, n outside, bin box |

Each of the six panels and both colour keys exists as **PNG, PDF and SVG**.
The panels contain only the scatter, the y = x guide, the frame, tick marks
and tick numbers. No panel letter, title, unit, axis name, rho or legend is
inside a panel; none of the six panels carries its own colour bar.

## Canvas and geometry (identical for all six panels)

- canvas **2.3333 x 2.4833 in = 59.27 x 63.08 mm**;
- square plot box **1.7633 in = 44.79 mm = 126.96 pt**, at a fixed position
  (0.50 in left, 0.42 in bottom, 0.30 in top, 0.07 in right);
- 7 pt tick numbers, 7 pt ticks, 0.7 pt frame; no tight crop, so the six
  canvases register exactly when dropped into PPT at the same size.
- The left/bottom margins are sized for a typographic minus plus two-digit
  tick numbers.

## Coordinates: true equal aspect in every panel

Display limits are the joint true/predicted extremes with **2 % of the joint
span left at each end**; the same pair is used for x and y. Limits are *not*
rounded out to the tick grid, so the outermost tick can sit inside the frame
and no axis is widened just to land a tick on the border. Ticks are identical
on both axes (same positions, same interval, same format).
`ax.set_aspect("equal", adjustable="box")` keeps the box square, so the guide
runs exactly from the lower-left to the upper-right corner (verified in the
PDF: dx = dy = 126.96 pt).

| panel | xlim = ylim | major ticks (step) | n plotted | outside |
|---|---|---|---|---|
| a1 Mobility | −6.4524 … −1.6457 | −6, −5, −4, −3, −2 (1) | 15,307 | 0 |
| a2 Bulk lifetime | −9.6102 … −1.8506 | −9 … −2 (1) | 15,307 | 0 |
| a3 Density of states | 22.7704 … 26.5877 | 23, 24, 25, 26 (1) | 15,307 | 0 |
| b1 Mobility | −0.7359 … 1.1344 | −0.5, 0.0, 0.5, 1.0 (0.5) | 15,307 | 0 |
| b2 Bulk lifetime | −0.7359 … 1.1344 | −0.5, 0.0, 0.5, 1.0 (0.5) | 15,307 | 0 |
| b3 Density of states | −0.7359 … 1.1344 | −0.5, 0.0, 0.5, 1.0 (0.5) | 15,307 | 0 |

The three orange panels share one range and one tick set, pooled over the six
value sets of b1–b3: the combined minimum is the DOS true r (−0.6999) and the
combined maximum is the bulk-lifetime predicted r (+1.0984). Blue panels each
have their own range. No percentile clipping; the
predicted extremes set the limits where they exceed the true range.

The 2 % margin is 2.44 pt on the 126.96 pt frame, larger than the 0.71 pt
marker radius, so the outermost markers clear the frame by 1.73 pt. This is
asserted per panel (`edge_clearance_pt` in `qa_report.json` / `checklist.csv`)
and checked on 1200 dpi renders of the extreme points.

## Density colouring: bin edges are independent of display edges

150 x 150 histogram cells, count -> colour, original point positions, s =
1.6 pt², alpha = 1.0, no marker edge, sparse points drawn first (stable sort
by count). No hexbin, no smoothing.

- **b3 reuses the reviewed D binning exactly**: x −0.75 … 0.75, y −0.75 …
  0.94, 150 x 150; max cell 31, 3,775 occupied cells (both match the D
  delivery). Its per-point counts are unchanged even though the display
  range is now the pooled −0.8 … 1.2.
- The other five panels use the same recipe: x over true ± 0.05, y over
  joint ± 0.05, 150 x 150. The exact bin boxes are listed in
  `checklist.csv`; they are not tied to the display limits.
- **One count->colour mapping per colour.** Blue: LogNorm 1 … 23 (max count
  23 in a2; a1 reaches 14, a3 22). Orange: LogNorm 1 … 31 (max 31 in b3;
  b1 22, b2 25). Neither row is stretched per panel; a panel whose busiest
  cell is lower therefore stays lighter, by design.
- Ramps (monotonic light -> panel hue -> dark):
  blue `#AFC3DF -> #86A3CE -> #4C72B0 -> #36578C -> #1F3560`,
  orange `#F1B285 -> #E79A66 -> #DD8452 -> #C66733 -> #9C3D0B`.
- Both colour keys are generated from the same cmap and norm the panels use:
  1.20 x 0.085 in bar, 7 pt ticks (1, 2, 5, 10, 20), 7.5 pt rotated
  "Samples per bin", identical geometry and font sizes for both.

## Export formats

- PNG: white background, RGB (no alpha), **900 dpi native**, 2100 x 2235 px
  for every panel (44.79 mm box at paper scale); colour keys 540 x 2235 px.
- PDF: single page 168 x 178.8 pt (2.333 x 2.483 in); frame, ticks, tick
  numbers and colour-key text are vector (Arial embedded, Type 42); the
  15,307-point cloud is a 900 dpi raster layer, as in the reviewed D panel.
- SVG: live `<text>` elements (editable in Illustrator), vector axes/ticks,
  the point cloud as one embedded image; page size in pt.

## Preview

`preview/Figure2_assembly_preview.png` (600 dpi, 4392 x 3223 px,
185.93 x 136.47 mm): top row a1–a3 + blue key, bottom row b1–b3 + orange key,
with panel letters, column titles, row definitions, axis names and rho.
Units are not repeated in the preview; they are in `labels.txt`.

## Checks performed

- Every panel: 15,307 samples, 0 outside the displayed ranges (asserted
  against the limits, not eyeballed); all points inside the bin boxes
  (`H.sum() == n`, `counts.min() >= 1`).
- PDF: frame 126.96 pt in all six, identical position; the y = x line spans
  the full frame (dx = dy = 126.96 pt, 45°); tick text is exactly the
  expected set and none of it leaves the page.
- SVG: same text elements as the PDF tick sets, one image, no per-character
  text splitting; rendered in Edge and compared with the PDF.
- b3's counts asserted equal to the delivered D (max 31, 3,775 occupied).
- PNG: 2100 x 2235 px, RGB, 900 dpi, white corners.
- Visually opened: exported PNG crops at 900 dpi (minus signs intact, nothing
  clipped), PDF renders at 300 dpi for a1/a2/a3/b1/b2/b3 and both colour
  keys, and the assembly preview.

## Notes

- The vertical hard edge at the right of the clouds (true a ≈ −3.0 / −2.0 /
  26.0, true r ≈ 0.70) is the true-value range of the frozen test set, not
  clipping: the predicted values continue beyond it and the display limits
  sit well outside.
- b3 keeps the reviewed D colours even though its axes are now the pooled
  orange range; this is required so its per-point counts do not change.
