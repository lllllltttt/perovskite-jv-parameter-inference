# Verification report — Fig. 4(d), text-free panel, half of the previous right extension
## 2026-11-12

Request: the previous increase of the right-hand blank was too large; set

```
new right end = original right end + 0.5 x (previous right end - original)
```

keep the left end, the canvas and the plot rectangle, do not squeeze the
image, and export the same text-free panel for PowerPoint assembly (only the
five y tick numbers drawn; tick marks and spines kept; no titles, units,
category names, n note or median numbers).

All numbers below are read back from the delivered PDF and the 600 dpi PNG
(`qa/qa_fig4d_half.json`, `qa/verify_fig4d_half.json`).

---

## 1. xlim, three versions side by side

| | original (2026-11-11) | previous export | **this file** |
|---|---|---|---|
| xlim | −0.55 … 2.55 | −0.55 … 2.90 | **−0.55 … 2.725** |
| right end | 2.55 | 2.90 | 2.725 = 2.55 + 0.5 × (2.90 − 2.55) |
| left end | −0.55 | −0.55 | −0.55 (**unchanged**) |
| visible span | 3.10 units | 3.45 units | 3.275 units |
| pt per unit | 51.93 | 46.66 | 49.15 |
| box width on paper | 25.96 pt | 23.33 pt | 24.58 pt |
| right blank, box 3 edge → frame | 15.58 pt | 30.33 pt | **23.35 pt** |
| text typed 2 pt from the box leaves | 0.6 pt | 15.4 pt | **8.4 pt** |

The box positions are untouched (x = 0, 1, 2; half-width 0.25); the canvas
(2.60 × 2.44 in) and the plot rectangle (0.30428, 0.34, 2.23572, 2.05 in) are
unchanged, so the panel is not compressed — only its visible x window is a
little wider than the original.

---

## 2. The blank the number will live in

Measured on the 600 dpi raster: the band from x = 2.25 + 0.5 pt to the frame
− 0.5 pt is **22.32 pt wide and completely empty** — darkest pixel 255/255,
zero pixels below 245 (i.e. 23.35 pt of blank edge to edge). No dot, whisker
or spine reaches into it; the right-most dot centre is x = 2.13.

With 7 pt Arial the string "5.19" is 12.96 pt wide: placed 2 pt from the box
it spans 2.244 … 2.424 in, and the right frame is at 2.540 in.

---

## 3. Text actually present

The PDF contains exactly five words: `0.01`, `0.1`, `1`, `10`, `100`.

| element | state |
|---|---|
| y tick numbers | present (the five above) |
| y / x tick marks | present; x marks are 3 pt vertical segments at x = 48.94 / 98.09 / 147.24 pt = data x = 0 / 1 / 2 (spacing 49.15 pt = one data unit) |
| four spines | present: x = 21.91 / 182.88 pt, y 3.60 / 151.20 pt (top origin); page 187.2 × 175.68 pt = 2.60 × 2.44 in |
| x category names | absent |
| medians 2.69 / 0.455 / 5.19 | absent |
| axis titles, units, (d), n note | absent (never baked in) |
| boxes, whiskers, median lines, dots | present, 45 dots per group |

---

## 4. Nothing else changed

* Box statistics identical to the accepted 2026-11-11 panel, < 1e-9 on all
  eight quantities of all three groups (n = 45, medians 2.692631 / 0.455349 /
  5.191600; full table in `qa/qa_fig4d_half.json`).
* Dot positions: same seeds (2026 / 2027 / 2028) and the same draw
  `uniform(-0.13, 0.13, 45)`, asserted element-wise before drawing.
* ylim 0.01 … 200 log, y ticks 0.01 / 0.1 / 1 / 10 / 100, Okabe–Ito colours
  0 / 2 / 3, alphas 0.22 (box) and 0.45 (dots), line widths 0.6 / 1.0 / 0.7 pt
  — unchanged.

---

## 5. Fitting "5.19" by hand

`preview/Fig4d_clean_half_preview.png` shows the delivered file (left) and the
same file with a grey 7 pt "5.19" placed 2 pt right of box 3, centred on the
median line (right; marked DEMO ONLY — not in the deliverable). The red dashed
guides mark the box edge and the right frame.

Exact positions (from the image's lower-left corner), left-aligned text boxes,
centre y on the coloured median line:

| text | left edge x | centre y |
|---|---|---|
| 2.69 | 0.878 in | 1.498 in |
| 0.455 | 1.561 in | 1.130 in |
| 5.19 | 2.244 in | 1.634 in |

x tick marks for the category names: 0.680 / 1.362 / 2.045 in.

---

## 6. Deliverables

| file | content |
|---|---|
| `figures/Fig4d_clean_half.pdf` | vector PDF, Type-42 embedded Arial, 2.60 × 2.44 in |
| `figures/Fig4d_clean_half.png` | 600 dpi, 1560 × 1464 px, white background |
| `figures/Fig4d_clean_half.svg` | editable SVG (only the five y tick numbers as text) |
| `preview/Fig4d_clean_half_preview.png` | as delivered + PPT typing demo with the measured blanks |
| `qa/qa_fig4d_half.json`, `qa/verify_fig4d_half.json` | every number above |
| `data_used/Figure4d_per_sample.csv` | 135 per-sample values, md5 identical to the accepted copy |
| `labels_and_caption.txt` | what is in the image, what to add in PPT and where |

---

## 7. Not touched

Fig. 4(e), Fig. 3, Fig. 5, the Word manuscript and the SI. No model re-run, no
sample re-selected, no value recomputed (`fig4_forward.collect()` re-asserts
every archived pin). The 2026-11-11 directory and both earlier 2026-11-12
directories are untouched.
