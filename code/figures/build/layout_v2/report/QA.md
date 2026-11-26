# QA — findings, adjudications and residual state

Round date: **2026-10-06** · delivery root `E:\project\work1\20261006\manuscript_figures_SI_integrated\`

> 本文件是 **v1** 那轮的判定记录。**v2 定向修补**见上一级目录的 `PATCH_NOTES.md`。
> v2 使下列 v1 数字失效，阅读 §6 时请以下列值为准：交叉引用 **127 条（正文 57 /
> SI 70）**；`verify_si.py` 现为 **115 项**（已改为按**标签**而非位置查表，并新增
> T6.7–T6.9 逐格对回冻结 CSV 与跨文档内容核对）；SI 由 44 页变为 **50 页 / 50 表**；
> 正文仍 18 页。§2.4 与 §2.10 的单位措辞已按导师要求改写为体例统一（见下）。

## 中文要点

本轮共处理三类事项：**必须跟着改正的数值/引用**、**制图与版面上的实际缺陷**、**看错了、经复核不成立的假警报**。以下是定论。

- 修正的统计事实：配对集 7,666 → 11,245；五档 tier 规模随之变化；表 T6.3 的 Spearman/Pearson 值与 p 值处理；T6.4 两个参数名次互换；T6.5 七个同号比例按标题所指的那一档重算；四个代表性算例在新规则下**全部存活**。
- 单位口径：**按导师要求统一为 log₁₀ units**（体例统一，不是科学纠错）——SI 中约二十处 "decade"/"(unit: decades)"/"physical-decade" 全部改为同一个单位词，并清掉四处替换后残留的冗余标注；无数字变动。
- 撤下的统计量：配对 Wilcoxon 符号秩检验与逐对百分位 bootstrap 的 p 值在正文与相关表中一律不再出现（SI 表 S13 与图 S3 不属撤下范围，未动）。
- 制图缺陷并已修：Figure 1 图内字号触底线、文字出框；Figure 3 标注行失衡；Figure 4 轴端幽灵刻度、inset 标题错位；Figure S7 图例过宽/半透明框/刻度、页脚四行重排、面板标签 a_N/r_N → a_D/r_D；600 dpi 栅格化。
- 装配缺陷并已修：`rich()` 遗留的孤立行内公式；SI 表 T17b 表头 "(dec)"；新增 Figure S6 图注的下标排版；T10.1 追加句被强制 Arial（导致 SI 由 45 页回流为 44 页）；`restore_hd.py` 的旧图错配。
- **经复核不成立、不得当作发现**：Figure S3 标注"被裁切"（300 dpi 裁图证明完好）；r 的符号约定与正文冲突（源文件与成果件都写 log₁₀(pₙ/pₚ)，是低分辨率误读）。
- 图内像素与两份 PDF 中嵌入的位图**逐像素相同**（用 PIL/numpy 比 RGB 数组，不是比字节流）。

---

## 1. What was inspected, and how

| surface | method |
|---|---|
| SI, all 44 pages | full-page rasters in `qa\pages\`, read page by page; `qa\pages_small\` is the same set at lower resolution for skimming |
| Manuscript, all 18 pages | same |
| Each figure standalone | `qa_render\preview_*.png` at full size, plus targeted crops (`crop_p8_top.png`, `crop_p11_cap.png`, `crop_si_p41_c34.png`) |
| Each figure inside the exported PDF | rasterized out of the PDF at 300 dpi and compared pixel-wise to `figures\*.png` |
| Text that Word hides from `Paragraph.text` | `docx_dump.py` walks `w:t` **and** `m:t`; every OMML-bearing cell was read as its concatenated `m:t` string |
| Fonts actually embedded | `svg_pdf_audit.py` font inventory over the PDF and the SVG text bounds |

Two limits are worth stating plainly. First, a raster inspection cannot prove
absence of a defect: a claim of the form "nothing is clipped anywhere" is not
supported by looking at pages. What is supported is "these specific things, at
these resolutions, read correctly". Second, `Paragraph.text` is empty for
inline equations, so no text search over a Word file is evidence that a symbol
is absent — the OMML was read directly.

## 2. Statistical and numerical adjudications

### 2.1 The pair set — 7,666 → 11,245
The archived rule kept a directed nearest-neighbour relation only when
`i < NN(i)`, which silently drops every relation whose partner has the lower
index. The mentor's rule maps each directed link to its unordered pair
`(min(i,j), max(i,j))` and takes the unique set: 11,245 undirected edges
covering all 15,307 test curves, with 5,859 samples in more than one edge (max
5). The corrected set is a strict superset of the archived one, so no archived
pair was lost — only added. Every SI and manuscript count that depended on the
old rule was updated (e.g. Table 6.1's 7,666 → 11,245, Table S6.2's count and
its ten summary statistics).

### 2.2 Tier sizes
`tier_k = max(1, int(round(n_pairs × frac)))` on the corrected set:
**1,124 / 562 / 112 / 56 / 11** (10 % / 5 % / 1 % / 0.5 % / 0.1 %). The archived
sizes were 766 / 383 / 77 / 38 / 8. Three of these live in OMML nodes rather
than in text (the Table 6.4 caption and two tier prose counts), which is why
they are logged as `math` edits rather than `cell` edits. The tier medians in
the prose moved accordingly (closest-0.5 %: 0.1337 → 0.1407; closest-0.1 %:
0.1021 → 0.1041).

### 2.3 Normalised medians
Over the 11,245 corrected pairs, with each axis normalised by its random-pair
baseline: mobility 0.353 (a) / 0.810 (r); lifetime 0.312 / 0.861; DOS 0.404 /
0.944. The qualitative ordering is unchanged from the archived numbers — the
shared-scale coordinate carries the recoverable signal, the ratio coordinate
carries much less — so the round's conclusions do not depend on the correction.

### 2.4 Unit wording unified to "log₁₀ units" — house style, at the mentor's request
按导师要求统一为 log₁₀ units。这是**体例统一**，不是科学纠错：本文件不再主张
"decade 是错词"。归档 SI 在约二十处用 "decade" / `(unit: decades)` /
"physical-decade" 来指物理 log₁₀ 宽度，导师要求全文改用同一个单位词
**log₁₀ units**。改动是逐句读取上下文后按句法改写的，不是机械替换：句内已经出现
"physical log₁₀" 的地方改名词短语，形容词形式单独改写（`text` 编辑见段落 9、48、
51、68、83 ×3、85 ×3、89 ×2、91 ×3、93 ×2、94；每处的 before/after 在 SI
edit log 中）。**没有任何数字变动。** 逐页复核时发现其中四处替换后留下了冗余标注
（`parameter coordinates (unit: decades)` 出现在已经点明单位的短语之后），这四处直接
删除而不是改写。

有一处是靠读第 34 页而不是靠检索才发现的：Table S17b 表头仍写
**`Interval width (dec)`**，而它上方两段的图注已写 "physical log₁₀ units"，同一族的
Tables S17/T27/T31 表头此前已经统一。已改为 **`Interval width (log₁₀ units)`**
（CELL_EDITS block 38；已在 pp. 34–35 渲染件上核对）。

**Why:** 导师的用词偏好；同一份 SI 里出现两种单位词只是体例不一致。
**How to apply:** 以后遇到类似要求，日志与报告一律写成"按导师要求统一为 X"，
不要把体例统一描述成普遍的科学纠错。

### 2.5 Withdrawn statistics
The paired Wilcoxon signed-rank test and the per-pair percentile bootstrap were
withdrawn before this round; nothing here reintroduces them. Concretely:

- **Table 6.3** carried a value and an OMML p-value per row. Both rows are
  rebuilt from scratch (`cell-rebuild`), because a cell that holds an equation
  cannot be edited run by run: Spearman **0.158 → 0.154**, Pearson **0.079 →
  0.073**, and the p-value node is removed from each. Read back out of the
  delivered SI, the two rows are now `Spearman(dJ, dΘ) | 0.154` and
  `Pearson(dJ, dΘ) | 0.073` with no third column and no parenthetical — the
  table is a two-column value table, which is why removing the node was a cell
  rebuild rather than a deletion.
- **SI Table S13 and SI Figure S3 are not part of that withdrawal** and were not
  touched; Figure S3's caption still cites W = 231, p = 9.01 × 10⁻⁴, which is a
  different test on a different quantity and remains as the author had it.

### 2.6 Table 6.4 — two ranks exchange places
On the corrected pair set r_rad ranks 4 and τ_n ranks 5 (the archived ordering
was the other way round). Both cells are OMML, so they are exchanged wholesale
rather than re-typed (`cell-swap`), which keeps the archived glyph runs and
their formatting intact.

### 2.7 Table 6.5 was printing the wrong tier
The seven same-sign fractions printed in the archived SI
(0.62 / 0.88 / 0.50 / 0.25 / 0.25 / 0.38 / 0.25) sit under a caption naming the
**closest-1 %** tier, whose archived size is n = 77 — but none of the seven is
k/77 for any integer k, and all seven *are* exact multiples of 1/8. The rows
therefore came from the n = 8 closest-0.1 % tier. This was adjudicated by
arithmetic, not assumption (`scripts\_verify_t65.py` recomputes the fraction on
every candidate pair set and prints the one that reproduces the archived rows),
and the table is now computed on the tier its caption names — n = 112 on the
corrected set. New values: 0.72 / 0.87 / 0.60 / 0.51 / 0.46 / 0.46 / 0.42.

This is a pair-set effect, not a physics change: every one of the seven moved
because the tier it is measured on moved from 8 pairs to 112, and the sign
pattern among the seven is preserved.

### 2.8 The four archived representative cases all survive
The archived Figure 4 cases were selected as the 0 / 0.5 / 1.0 percentiles of
the 45-sample forward-validation cohort's cycle gap — that selection is
inherited and was **not** re-made. Test indices 12058 / 595 / 14499 (database
Sample_IDs 52446 / 117995 / 154812) reproduce from the frozen audit CSV to
within the archived tolerances, and the cycle gaps recomputed from the frozen
curves match the archived values (0.2675 / 2.5627 / 54.1045 mA cm⁻²). The
corrected pair rule does not touch this cohort.

### 2.9 Figure 2 — two panels that both read 0.925
Panel (a) mobility ρ = **0.925047** and panel (c) DOS ρ = **0.924758**. Both
are printed to three decimals and therefore both read 0.925. This is not a
duplication defect and no value was adjusted: the two correlations genuinely
differ by 0.00029. Flagged here so that the coincidence is not mistaken for a
copy-paste error during review, and so that any later decision to print more
decimals is a deliberate one.

### 2.10 Unit basis
`data_used\unit_basis_check.csv` records the check that the two log₁₀
quantities used side by side are on the declared basis: `param_log10_rmse` is a
difference of physical log₁₀ values while `mean_pred_sigma` is a normalised
log₁₀ quantity. **这是两种不同的坐标口径，不是单位的对错**：SI 的措辞没有描述
清楚这一点，主文的措辞则是对的，所以只改了 SI 一侧（见 §2.4）。没有任何数字
变动，`unit_basis_check.csv` 里的数值不变。

## 3. Figure-level findings

| figure | finding | resolution |
|---|---|---|
| Figure 1 | in-figure fonts sat at the legibility floor for the 17.27 cm display width, and several strings had been drawn outside their box | internal type re-tuned; the out-of-box strings moved inside their containers |
| Figure 1 | the parameter-vector glyph had been drawn as a J–V curve in an earlier round | replaced by the glyph (fixed before this round, verified here) |
| Figure 2 | SVG/PDF text-bound audit found strings on the canvas edge | margin re-tuned; `svg_pdf_audit.py` now PASS |
| Figure 3 | the annotation row was unbalanced once the corrected pair set changed the tier sizes | row rebalanced |
| Figure 4 | a phantom tick appeared at the end of the axis (a Matplotlib auto-locator artifact) | filtered |
| Figure 4 | the inset caption sat where it competed with the inset's own axis labels | relocated |
| Figure 4 | panel (c)'s 0–1.0 V operating window was compressed into the top 5 % of a 2000 mA cm⁻² axis | inset added at 0.812 × 0.556 of the axes (the first attempt at 0.6 × 0.45 left ~5 pt tick numbers and merged the curves — visible in the first render, replaced) |
| Figure 4 | **inset value discrepancy, recorded not smoothed**: at V = 1.00 V for test index 14499 the stored target is **11.559**, the decoder reconstruction **11.664** and the COMSOL forward simulation **19.010 mA cm⁻²**. The decoder tracks the stored curve closely at this bias while the forward simulation departs from it — which is exactly the cycle gap this panel is about (the case is the cohort's highest, gap 54.10 mA cm⁻²). No value was adjusted; the panel shows the three curves as they are | left as data |
| Figure 5 | the (e) caption said "scale" where the quantity plotted is σ_θ | corrected, and a note added that the 0 % point is the noise-free reference and carries no bar |
| Figure S6 | **new** — nine-parameter comparison, appended at the same 6.00 in width as the seven existing SI figures | caption emitted as 19 runs so that the nine subscripts are real subscript runs |
| Figure S7 | **new** — ECDF figure; legend too wide, frame transparent, ticks too dense, footer wrapped to four lines | legend narrowed, frame made opaque, `MultipleLocator(1.0)` |
| Figure S7 | panels (e)/(f) were labelled a_N / r_N while SI Tables S11 and S14 define **a_D / r_D** for the DOS coordinate | corrected; the figure regenerated; only this figure differs in the SI media |

Rasterization: every figure is rasterized at **600 dpi** into its `.png`. An
earlier setting produced visibly soft text at the print size; 600 dpi is what
removed it. The `_large` variants are the same drawing on a wider canvas, for
the author's own re-use — they are not what is embedded in the documents.

## 4. Defects found in the build itself (and fixed)

These were found by looking at rendered pages, not by any script — each one is
invisible to the automated checks above.

1. **Stranded inline OMML.** `rich()` rebuilds a paragraph by clearing its runs
   and writing new ones. Inline `m:oMath` hangs directly off `w:p`, not inside a
   `w:r`, so `clear_runs()` left it standing while the new runs were appended
   *after* it — the equation ended up marooned at the head of the caption,
   rendering as a stray glyph cluster in front of the first word. Fixed by
   removing `m:oMath` / `m:oMathPara` children (display equations, which are
   their own paragraphs and which `rich()` never touches, are unaffected).
2. **Four mangled unit phrasings** left behind by the automated unit sweep —
   redundant `(unit: …)` tags after phrases that already named the unit. Cut.
3. **Stale-figure mis-mapping in `restore_hd.py`.** python-docx appends new
   media parts without removing the old ones, so a rebuilt document carries
   both, and an old Figure 4 and a new Figure 4 have identical pixel
   dimensions — aspect ratio cannot tell them apart and silently picks
   whichever sorts first. The mapping is now by **document order**, with the
   aspect ratio kept as an assertion that the pairing is sane. A wrong pairing
   here is invisible in every geometry check and would have shipped a stale
   figure inside a correct layout.
4. **`Interval width (dec)`** — see §2.4.
5. **Arial inside a serif caption.** The appended T10.1 sentence was written
   with `run.font.name = "Arial"`. The paragraph's other runs carry no `rFonts`
   and inherit from "Body Text", so naming Arial put a sans-serif sentence
   inside an otherwise serif caption — the only ArialMT span in the whole SI.
   Removing the line let the sentence inherit correctly, and the reflow took the
   SI from **45 to 44 pages**; the pagination was re-inspected after the change.
6. **Figure S6 caption subscripts.** The caption's symbols include four
   subscripts with no Unicode glyph ((n),(p) in μ, τ and N_c/N_v, ETL/HTL,
   r_rad). Emitted as real subscript runs using Word's own `vertAlign`
   convention, which the SI already uses in 18 table headers, rather than as
   lookalike characters.
7. **Two cross-references** pointed at Figure 2 for the nine-parameter parities,
   which have since moved out of Figure 2: SI paragraphs 16 and 85 now cite
   **Fig. S6**.

## 5. False positives — investigated, dismissed, and not to be reported as findings

1. **"Figure S3's annotations are clipped."** They are not. A 300 dpi crop of
   the relevant region reads cleanly: "ρ = 0.03 (p = 0.80)" and "ρ = 0.12
   (p = 0.44)". Nothing was changed. The impression came from a low-resolution
   page raster.
2. **"The SI defines r = log₁₀(pₚ/pₙ) while the manuscript defines
   r = log₁₀(pₙ/pₚ)."** There is no conflict. A 95 dpi render of SI page 24
   appeared to show the inverted form; programmatic extraction of the actual
   characters shows **both** the source and the built SI read
   `log₁₀(pₙ/pₚ)` (codepoints U+2081, U+2080, U+2099, U+209A — the subscripts
   are subscript *n* then *p*). It was a misread of a low-resolution glyph.
   **Nothing was changed, and this must not appear as a finding** — recording it
   would send the author looking for a defect that does not exist.
3. **Byte-hash mismatch between a PDF image stream and its figure PNG.**
   PyMuPDF re-encodes on extraction, so the stream hash cannot match the source
   file even when the images are identical. Re-checked with PIL/numpy RGB array
   comparison: identical for SI pp. 43/44 and manuscript pp. 3/5/7/9/11.

## 6. Verification summary

| check | result |
|---|---|
| `verify_si.py` | PASS — **115 checks, 0 FAIL** (v2). Table lookup is by label, not position; T6.7–T6.9 are compared cell by cell against the frozen CSVs in `data_used\`; the Figure 3 caption → Methods pointer and the two Table S6 pointers are checked for **content**, not just for a resolvable number |
| `figure_font_audit.py` | PASS — no in-figure string below the 6 pt floor at 17.27 cm |
| `svg_pdf_audit.py` | PASS — no SVG text outside its canvas, no font substitution in the PDF |
| `qa_layout.py` | PASS — no overlap or clipping detected among the drawn objects |
| `cross_reference_map.py` | **127 references, 0 unresolved** (57 manuscript / 70 SI) after the v2 patch; the script exits non-zero on any broken reference |
| Figure media vs. delivered PDFs | pixel-identical (RGB array comparison) |
| Figure pipeline determinism | Figures 1–5 and S6 reproduce byte-for-byte; only FigureS7 was regenerated this round |
| Manuscript diff vs. source | 103 paragraphs: 9 with changed text, 3 with a changed inline image only, 0 with changed `w:pPr` outside those |
| Font inventory, manuscript PDF | TimesNewRomanPSMT / -BoldMT, CambriaMath, SimSun (50 chars), SansSerifCollection (1 char) |
| Font inventory, SI PDF | TimesNewRomanPSMT, TimesNewRomanPS-BoldMT / -ItalicMT, CambriaMath, Consolas, Aptos Display Bold, ArialMT (2 chars) |

On the last line: the two ArialMT characters on SI page 14 are **invisible
spaces**, and no Arial reference exists anywhere in either DOCX — document,
styles, headers, footers and numbering were all searched. It is a Word export
artifact with no visible effect, listed for completeness only.

## 7. Pre-existing conditions, left as they are — the author's call

None of these were introduced by this round; each is inherited from the
sources. They are recorded so that a reviewer who notices them knows they were
seen and deliberately not "fixed" inside a figure-and-SI round.

1. **Manuscript p. 8 carries a paragraph set at 7.0 pt** amid 11 pt body text
   ("Physical back-substitution evaluates the inferred parameter
   combinations…"). It is the mentor's own formatting: the paragraph exists
   unchanged in `Manuscript_20261002_Working.docx` (paragraph 30, style
   `Normal`, runs carrying no explicit size), so the small size comes from the
   source document's own style definitions. If it is meant to be a note, it is
   a note; if it is a stray, it is the author's to change.
2. **Manuscript pp. 4 / 6 / 8 / 10 have large blank lower halves.** The figure
   plus its caption are an atomic block occupying 85–96 % of a page, so the
   next paragraph cannot start on that page. Making the pages fuller would mean
   shrinking figures below readable size, which section 六 of the brief
   forbids. Page count is 18 as delivered.
3. **SI Table S5's header wraps as "Recoverabilit / y"** — the column is too
   narrow for the word. Cosmetic; left alone rather than re-laying-out a table
   that is otherwise correct.
4. **Figure 5's panel citations — checked this round, no action needed.** An
   earlier round flagged two Figure 5 citations in the manuscript as possibly
   wrong after the figure was reassembled. They are not. The manuscript cites
   Fig. 5a (coverage), 5b (interval score) and 5c–e (noise effect), and panels
   (a)–(e) of the delivered Figure 5 are coverage, interval score, ρ, coverage
   under noise and the change in mean σ_θ respectively, in that order — so each
   citation points at what it says it points at. The Figure 5 caption in the
   manuscript names the same five panels in the same order. The earlier flag is
   closed; only if the author later reorders the panels would this need to be
   revisited.

## 8. What is still open

- The author's decisions listed in §7 — none blocks the delivery.
- The SI's own copy of the corrected Table S6 family is now consistent with the
  manuscript, but the archived `20260929_si_rg_sync` tree is superseded; the
  live base is `20260929_si_provenance_wording`, which is what this round used.
- Nothing in this delivery has been through a native-speaker language edit; the
  English of the inserted captions and sentences is the round's own.
