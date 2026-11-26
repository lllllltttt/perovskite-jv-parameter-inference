# 逐图检查表（Figure 1–5 / S1–S11）

底稿：`Manuscript_20261125_final_figures_text_corrected.docx`、
`Supplementary_Information_20261125_final_figures_text_corrected.docx`（2026-11-25，未改动）
图源：`finalfig/正文_fig.pptx`、`finalfig/SI_fig.pptx` 及其引用的原始 SVG；原始素材目录见“图源”列。
判定“有效分辨率”时按 **最终插入尺寸**（正文 6.8 in / SI 6.27 in 宽）折算。

| 图 | 原问题（实测） | 处理 | 是否含栅格层 | 最终有效分辨率 | Word 导出 PDF 检查 |
|---|---|---|---|---|---|
| **Figure 1** | 导出 SVG 无 `<image>`，本身即纯矢量；Word 里另存的 PNG 仅 301 dpi | 仅重出 600 dpi PNG 回退图 | 否 | 全矢量 | 全矢量，0 幅位图 ✔ |
| **Figure 2** | 6 子图内嵌 263×280 JPEG（≈65 dpi）、2 色条 68×280 JPEG（≈79 dpi） | 换成 `20261109_fig2_final_D_assets` 的 6 个面板 SVG + 2 个色条 SVG，按原变换原位嵌入 | 散点层保留 900→1070 dpi 栅格 | 散点 1068 dpi；文字/轴/柱图矢量 | 1068 dpi，文字矢量 ✔（原 138 dpi） |
| **Figure 3** | 3 幅面板内嵌 339×278 JPEG（68 dpi）；(c)(d) 图例色块比文字低 ≈0.96–1.04 pt | 换 `Fig3b/3c/3d.svg`（原始矢量），图框按原 clip 还原；**本轮再修 (c)(d) 图例**：色块按文字字形（cap 高）光学中心上移 | 否 | 全矢量 | 0 幅位图，全矢量 ✔（原 68 dpi） |
| **Figure 4** | 7 幅面板 161–250 px JPEG（62–84 dpi） | 换 `Fig4a/b`、`Fig4d_clean_half`、`Fig4e_{Jsc,PCE,FF_pp,Voc}.svg`；`fill-opacity` 由 Chromium 正确渲染 | 否 | 全矢量 | 0 幅位图，全矢量 ✔（原 62–84 dpi） |
| **Figure 5** | 5 幅面板 282–329 px JPEG（78–134 dpi） | 换 `Fig5a–e.svg` | 否 | 全矢量 | 0 幅位图，全矢量 ✔（原 78–134 dpi） |
| **Figure S1** | 2 幅位图：511×511 相关矩阵 + 30×511 色条，均为源面板 SVG 内嵌的 100 dpi 栅格 | **未改**（源即如此；矩阵为 9×9 实色块、色条为平滑渐变，放大无可见差异） | 是（源内嵌） | 209 dpi | 209 dpi，其余矢量（同底稿） |
| **Figure S2** | 无位图 | 未改 | 否 | 全矢量 | 全矢量 ✔ |
| **Figure S3** | 无位图 | 未改 | 否 | 全矢量 | 全矢量 ✔ |
| **Figure S4** | 2 处碎片位图（96×4、96×16，≈141 dpi） | 换成原始面板 `image69.svg` 矢量输出 | 否（矢量源） | 全矢量 | ⚠ Word 仍把面板内 2 个元素栅格化成 66×4 / 66×12（96 dpi） |
| **Figure S5** | 336 个柱条碎片位图（6–8 px，≈131 dpi） | 换成 9 个原始面板 SVG（柱条全矢量） | 否（矢量源） | 全矢量 | ⚠ Word 仍把柱条栅格化成 6–7 px（96 dpi） |
| **Figure S6** | docx 内只有 1180×1078 PNG（188 dpi），没有 SVG（矢量版 64 MB） | 由 `SI6.svg` 重出 600 dpi PNG（3762×3439）替换 | 整幅为栅格 | 600 dpi | 600 dpi ✔（原 188 dpi） |
| **Figure S7** | 9 个散点层内嵌 285×259 PNG（104 dpi） | 换 9 个原始面板 SVG（散点 600 dpi 栅格 + 矢量轴） | 散点层栅格 | 655 dpi | 655 dpi ✔（原 104 dpi） |
| **Figure S8** | 1 幅面板 239×189 PNG（108 dpi），PPT 中该面板无 SVG | **本轮已修**：该面板 = ECDF 的 rμ 子图，取自 `20261116_figs7_split/out/svg/S7b.svg`（旧编号 S7b，由 `20261024_final_figures_svg/si/FigureS7.svg` 拆出，含 11,245 对与 199,985 随机的两条 ECDF），补回原图的图例后按原矩形嵌入 | 否 | 全矢量 | 0 幅位图，全矢量 ✔（原 124 dpi） |
| **Figure S9** | 无位图 | 未改 | 否 | 全矢量 | 全矢量 ✔ |
| **Figure S10** | 无位图 | 未改 | 否 | 全矢量 | 全矢量 ✔ |
| **Figure S11** | 无位图 | 未改 | 否 | 全矢量 | 全矢量 ✔ |

## 说明

- “原问题”列的分辨率按 **导出 SVG 内嵌位图 ÷ 最终显示尺寸** 实测，不是看 DPI 元数据。
- Word 导出 PDF 时对**位图**统一压到 ~200 dpi（本底稿实测 130–200 dpi），对
  **部分矢量元素**（S4/S5 里的实心矩形块）会自行栅格化成 6–16 px 小图。
  前者已用 PyMuPDF 原位换回全分辨率（Fig 2 / S6 / S7 均已恢复）；后者是 Word 渲染器的行为，
  **SVG 与独立 PDF 中这些元素是矢量的**，只有 Word 导出的 PDF 会退化。
- Figure S1、S8 为“源即低清”，未做任何放大/锐化/改 DPI 处理。
- 全部 16 图的 `svg` 内部位图均逐个解码核对过实际像素尺寸（见 README 的“位图清单”）。
