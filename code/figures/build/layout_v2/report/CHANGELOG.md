# CHANGELOG — five-figure finalization, manuscript assembly, SI sync

Round date: **2026-10-06**
Delivery root: `E:\project\work1\20261006\manuscript_figures_SI_integrated\`

> 本文件记录的是 **v1**（五图定稿 + 正文装配 + SI 同步）。**v2 定向修补**逐条记在
> 交付根目录的 **`PATCH_NOTES.md`**（本目录的上一级）。v2 变更摘要：
>
> - 正文：Figure 3(d) 图注 "inferred" → **"ground-truth simulation parameters"**；
>   Figure 4 图注改 "large negative current densities at high forward bias" 并删去
>   误导的 "shared vertical scale"；Methods 补上 Figure 3 的**选例规则**（图注指向
>   它）；两段 7 pt 正文恢复为 11 pt（保留字面上标字形）。共 **14 处编辑**，仍为 18 页。
> - SI：新增 **T6.7**（Fig. 3 两个案例的全参数与配对坐标依据，含 Sample_ID 与
>   `10^|Δlog₁₀θ|` 倍数列）、**T6.8a/b/c**（六坐标分档表）、**T6.9**（六个随机基线）；
>   旧五案例保留并标为归档补充案例；"compensation" 类标题改为中性描述；Table S5
>   表头调列宽修复断词。**169 行编辑**，44 → **50 页**。
> - Figure 3 重导出并换入 Word（中排 height_ratios 重平衡）。Figures 1/2/4/5 未重绘。
> - 交叉引用 119 → **127 条**，0 未解析。`verify_si.py` **115 项 PASS**。
> - 术语统一按导师要求写为 "按导师要求统一为 log₁₀ units"，不再描述成科学纠错。

## 中文要点

本轮把五张主图定稿后装入导师最新正文，并把配套 SI 同步到同一数值与交叉引用体系，交付一套图文、数值、交叉引用一致的审阅稿。

- 正文：5 处插图（Figure 1–5）+ 7 处文字修改，共 12 处；18 页。
- SI：144 处修改（111 单元格 / 24 文字 / 3 公式 / 2 单元格重建 / 2 插图 / 1 单元格互换 / 1 追加）；44 页、9,789 词、42 表、9 图。
- 五张主图 + 2 张新增 SI 图（S6 九参数表图、S7 ECDF）均已定稿，各自给出 PNG / 高分辨率 PNG / PDF / SVG 六件套。
- 交叉引用：119 条（正文 56、SI 63），**0 条未解析**。
- 未做（越界）：不重训、不重预测、不重拟合 scaler、不跑 COMSOL；不改原始数据、冻结模型、划分、既定算例与统计定义；不新增显著性检验或研究分析；不重写导师的引言/讨论；不恢复 S19。
- 仍需作者决定的事项见 `QA.md` 第 7 节。

---

## 1. Inputs — read-only, not modified by this round

| role | path | size (B) | sha256 (first 16) |
|---|---|---|---|
| mentor manuscript (source) | `E:\project\work1\20261006\Manuscript_20261002_Working.docx` | 3,016,879 | `ca7aed66ca0535fe` |
| SI (source) | `E:\project\work1\20260929_si_provenance_wording\Supplementary_Information_provenance_wording_20260929.docx` | 6,524,368 | `4a16fcd06f62e7a1` |
| frozen model predictions | `E:\project\work1\final_figures\scripts\_frozen_preds.npz` | 39,742,950 | `ad156cd18c1933e8` |
| frozen J scaler | `E:\project\work1\data\J_scaler.pkl` | 5,738 | `3b82a2541bd77c59` |

The two SI sources of the previous rounds are superseded and are **not** used:
`20260929_si_rg_sync` and the `provenance_wording` file is the live base.

The frozen test split, the archived representative cases, the directed-link
dedup rule and every statistical definition are inherited unchanged. No
retraining, no re-prediction, no scaler refit, no COMSOL run was performed.

## 2. Outputs

| artifact | size (B) | sha256 (first 16) |
|---|---|---|
| `manuscript\Manuscript_20261002_Working_integrated.docx` | 8,563,284 | `3ec53987b86df4a3` |
| `manuscript\Manuscript_20261002_Working_integrated.pdf` | 5,986,638 | `edd947f6de153eb2` |
| `si\Supplementary_Information_synced.docx` | 13,421,959 | `c8bc0c75eeeea581` |
| `si\Supplementary_Information_synced.pdf` | 15,375,272 | `af50fdade0116a40` |

Manuscript: **18 pages**, 5 figures placed on pp. 3 / 5 / 7 / 9 / 11.
SI: **44 pages**, 9,789 words, 42 tables, 126 paragraphs, 9 images
(7 figure paragraphs; S6 on p43, S7 on p44).

Both PDFs are exported from the delivered DOCX by Word
(`ExportAsFixedFormat($pdf, 17)` = PDF/A-1a-compatible export path) and then
passed through `scripts/restore_hd.py`, because Word's exporter caps every
bitmap at 200 ppi with no switch. The restore swaps each image stream back to
the HD original in place; page count, text and layout are unchanged
(`restore_hd` asserts `text : IDENTICAL to the plain render`).

## 3. Figures

Seven figure stems, each delivered as `.png` (≈4200–4300 px wide),
`_large.png` (≈5500 px wide), `.pdf`, `_large.pdf`, `.svg`, `_large.svg` —
42 files, 55 MB, in `figures\`.

| stem | what this round finalized |
|---|---|
| `Figure1` | workflow schematic — internal font re-tuned to clear the legibility floor; text that had been drawn outside its box moved inside |
| `Figure2` | paired-coordinate paper figure — layout, annotation placement and palette closed; panel (a) ρ = 0.925047 and panel (c) ρ = 0.924758 are both shown as 0.925 by design |
| `Figure3` | neighbour-pair figure — annotation row rebalanced after the corrected pair set changed the tier sizes |
| `Figure4` | forward-validation figure — phantom tick at the axis end filtered; inset caption relocated; the (c) 0–1.0 V operating-region inset added |
| `Figure5` | interval figure — caption corrected ("scale" → σ_θ) and the noise-free 0 % reference point documented |
| `FigureS6_nineparam` | **new** — nine-parameter comparison table figure, appended as SI Figure S6 |
| `FigureS7_ecdf` | **new** — ECDF of the paired-coordinate statistics, appended as SI Figure S7; panel labels corrected to a_D / r_D to match SI Tables S11 and S14 |

The five main figures are rasterized at 600 dpi into `figures\*.png`; the
`_large` variants are the same drawings at a wider canvas for the author's own
re-use. Fonts inside every figure are ≥ 6 pt at the 17.27 cm display width,
which is the floor implied by `f_internal ≥ 0.3887 pt/cm × W_display`.

## 4. Manuscript — 12 edits (`manuscript\Manuscript_edit_log.csv`)

Five figure insertions, all 6.80 in wide:

| paragraph | edit |
|---|---|
| 14 | `Figure1.png` replaces the inline image (in place) |
| 21 | `Figure2.png` replaces the `[FIGURE 2 INSERTION]` placeholder |
| 27 | `Figure3.png` replaces the `[FIGURE 3 INSERTION]` placeholder |
| 34 | `Figure4.png` replaces the inline image (in place) |
| 41 | `Figure5.png` replaces the inline image (in place) |

Seven text edits:

| paragraph | edit | chars |
|---|---|---|
| 18 | name the three lower individual-parameter correlations and cite the SI figures | 612 → 683 |
| 24 | replace the withdrawn 280-fold / 72-fold example with the final pair statistics | 551 → 725 |
| 25 | F3-RESULTS: verified pair counts, baseline-normalised medians | 536 → 1,086 |
| 28 | F3-CAPTION: per-panel Figure 3 caption | 887 → 1,486 |
| 35 | Figure 4 caption: panel (c) 0–1.0 V inset and its metrics | 1,119 → 1,594 |
| 42 | Figure 5 caption: noise-free 0 point, no bar in panel (e), σ_θ | 1,123 → 1,155 |
| 76 | F3-METHODS: back-fill the tie rule, the seed-42 random baseline, the tier rule | 996 → 1,387 |

Diffed paragraph by paragraph against the source afterwards: of the 103
paragraphs, exactly 9 carry different text (the 7 text edits plus paragraphs 21
and 27, whose `[FIGURE n INSERTION]` placeholder text was consumed by the
image), and 3 (14, 34, 41) carry a different inline image with their text
unchanged. Every other paragraph is identical in text **and** in its `w:pPr`
formatting XML — the introduction, discussion and reference list are
untouched.

## 5. SI — 144 edits (`si\SI_edit_log.csv`)

| kind | n | what |
|---|---|---|
| `cell` | 111 | table cells whose value, unit name or label had to follow the corrected pair set and the corrected unit convention |
| `text` | 24 | caption and body sentences in the SI itself |
| `math` | 3 | OMML runs inside table cells (e.g. the T6.4 caption tier size 77 → 112) |
| `cell-rebuild` | 2 | cells that carry an equation and therefore cannot be edited run-by-run (T6.3 Spearman value corrected, its withdrawn p-value removed) |
| `figure` | 2 | new Figure S6 and Figure S7 appended |
| `cell-swap` | 1 | T6.4: on the corrected set r_rad ranks 4 and τ_n ranks 5, so the two cells exchange |
| `append` | 1 | T10.1 caption sentence explaining the non-monotonicity the corrected table now shows |

The seven originally existing SI figures are untouched in content; only their
numbering position relative to the two appended figures changed.

## 6. Reproducible scripts and light data

`scripts\` (33 Python files + `render.ps1`):

```
figstyle.py                 shared style: Okabe-Ito palette, font sizes, legibility floor
lib_v2.py                   corrected pair set, tier rule, normalised medians
build_all_figures.py        driver: runs every figure script in order
fig1_workflow.py  fig2_paired_recovery.py  fig3_neighbour.py
fig4_forward.py   fig5_intervals.py  figS6_nineparam.py  figs7_ecdf.py
si_table_s6_stats.py        the Table S6 / S10 statistics used by the figures
build_manuscript.py         manuscript assembly (source -> *_integrated.docx)
build_si.py                 SI sync (source -> *_synced.docx, 144 logged edits)
render.ps1                  Word -> PDF export
restore_hd.py               post-export: put the HD bitmaps back (Word caps at 200 ppi)
verify_si.py                six SI invariants
figure_font_audit.py        minimum in-figure font size
svg_pdf_audit.py            SVG text boundaries, font substitution, PDF font inventory
qa_layout.py                overlap / clipping / page-fill checks
cross_reference_map.py      builds report\cross_reference_map.csv, exits non-zero on a broken reference
docx_dump.py                paragraph/run/OMML dumper used for the visual-inspection follow-ups
superseded\                 two scripts kept for provenance only, not part of the pipeline
```

Reproduction order:

```
python scripts\build_all_figures.py
python scripts\build_manuscript.py
python scripts\build_si.py
powershell -File scripts\render.ps1
python scripts\restore_hd.py manuscript\..._integrated.docx
python scripts\restore_hd.py si\..._synced.docx
python scripts\verify_si.py ; python scripts\figure_font_audit.py
python scripts\svg_pdf_audit.py ; python scripts\qa_layout.py
python scripts\cross_reference_map.py
```

Interpreter: `D:\PythonProject\.venv\Scripts\python.exe`, with
`PYTHONIOENCODING=utf-8`.

`data_used\` — 37 files, 36 MB — is the light data actually read by the
figures and by the two new SI tables: the corrected pair tables, the random
baseline pairs (seed 42), the per-sample coordinate table, the nearest-neighbour
links, the six Table S6 exports, the eight Table S10 exports, the four
representative-case tables and `unit_basis_check.csv`. The frozen model, the
raw dataset and the COMSOL working directories are **not** copied here.

## 7. Verification performed this round

| check | result |
|---|---|
| `verify_si.py` | PASS (six invariants) |
| `figure_font_audit.py` | PASS — every in-figure string ≥ the 6 pt floor |
| `svg_pdf_audit.py` | PASS — no text outside its canvas, no substituted font |
| `qa_layout.py` | PASS |
| `cross_reference_map.py` | 119 references (56 manuscript / 63 SI), **0 unresolved** |
| SI page-by-page visual sweep | all 44 pages (`qa\pages\`) |
| Manuscript page-by-page visual sweep | all 18 pages |
| Figures inspected standalone + inside the exported PDFs | Figures 1–5, S6, S7 |
| Figure media vs. delivered PDFs | pixel-identical (PIL/numpy RGB comparison, not a byte hash of the stream) |
| Figure pipeline determinism | re-running `build_all_figures.py` reproduces Figures 1–5 and S6 byte-for-byte against the media inside the delivered DOCX; only FigureS7 was regenerated (its a_D/r_D label fix) |
| Manuscript diff against source | 103 paragraphs: 9 with changed text, 3 with a changed inline image only, 0 with a changed `w:pPr` outside those, 0 structural surprises |

## 8. Deliberately not done

No retraining, re-prediction, scaler refit or COMSOL launch. No change to the
raw data, the frozen model, the split, the archived cases or any statistical
definition. No value was adjusted to accommodate text. No significance test or
new analysis was introduced; the paired Wilcoxon signed-rank test and the
per-pair percentile bootstrap remain withdrawn, and SI Table S13 and Figure S3
(which are not part of that withdrawal) are untouched. Nothing was rewritten
in the mentor's introduction or discussion, no S19 content was restored, and no
data-sharing address, software version or server log was invented. No input
file was overwritten — every output lives under this delivery root.

## 9. Open items for the author

See `QA.md` §7. In short: the two Figure 2 panels that both round to 0.925, the
manuscript's own small-print paragraph on p8, the blank lower halves of
pp. 4/6/8/10 caused by figure+caption atomic blocks, and SI Table S5's header
wrapping as "Recoverabilit / y" are all inherited from the sources and were
left as they are unless the author wants them changed.
