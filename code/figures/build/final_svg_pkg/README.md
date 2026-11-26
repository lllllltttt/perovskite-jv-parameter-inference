# 最终版图片 SVG 汇总（2026-10-24）

对应最终稿：正文 `20261022_expanded_ratio_manuscript_integration_final/manuscript/Manuscript_20261022_expanded_ratio_integrated_final.docx`
与 SI `.../si/Supplementary_Information_20261022_expanded_ratio_integrated_final.docx`。

本目录把所有 **最终版图片的矢量源文件** 集中到一处，并按正文/SI 的图号统一重命名。
所有文件都是从原目录 **逐字节复制**（SHA-256 一致），未做任何重新导出、压缩或编辑。

## 目录结构

```
main/     正文主图 Figure 1–5（含 _large 放大版）
si/       SI 图 Figure S1、S2、S3a、S3b、S3c、S4–S10（S6/S7 含 _large）
MANIFEST.csv    每张图的图号、字节数、SVG 尺寸、viewBox、SHA-256、源文件路径
SHA256SUMS.txt  校验和（可用 `sha256sum -c` 复核）
build_manifest.py  生成并校验 MANIFEST 的脚本
```

## 与最终稿的对应关系

正文最终 docx 内嵌 5 张位图，其字节数与下表中的 PNG 逐一相等，因此下表 SVG 就是最终稿的源矢量：

| 最终图号 | 本目录 SVG | 源目录（相对 `E:\project\work1`） |
|---|---|---|
| Figure 1 | `main/Figure1.svg`、`Figure1_large.svg` | `20261006\Figure1_simplified_layout\` |
| Figure 2–5 | `main/Figure2.svg` … `Figure5.svg`（各含 `_large`） | `20261006\manuscript_figures_SI_integrated_v2_layout_final\figures\` |
| Figure S1 | `si/FigureS1.svg` | `final_figures\SI_final_review\FigS1_parameter_distributions_correlations.svg` |
| Figure S2 | `si/FigureS2.svg` | `final_figures\SI_final_review\FigS2_sensitivity_recoverability.svg` |
| Figure S3a | `si/FigureS3a.svg` | `20260929_si_rg_sync\figures\FigS3_cycle_cases.svg` |
| Figure S3b | `si/FigureS3b.svg` | `final_figures\SI_final_review\FigS3_cycle_voltage.svg` |
| Figure S3c | `si/FigureS3c.svg` | `20260929_si_rg_sync\figures\FigS3_cycle_gap_RG.svg` |
| Figure S4 | `si/FigureS4.svg` | `final_figures\SI_final_review\FigS4_fixed_sigma_distribution.svg` |
| Figure S5 | `si/FigureS5.svg` | `final_figures\SI_final_review\FigS5_fixed_uncertainty_error_3x3_polish.svg` |
| Figure S6 | `si/FigureS6.svg`、`_large.svg` | `20261006\manuscript_figures_SI_integrated_v2_layout_final\figures\FigureS6_nineparam*.svg` |
| Figure S7 | `si/FigureS7.svg`、`_large.svg` | 同上 `FigureS7_ecdf*.svg` |
| Figure S8–S10 | `si/FigureS8.svg` … `FigureS10.svg` | `20261022_expanded_ratio_report_final_v2\figures\fig01/02/03_*.svg` |

## 使用注意

1. **最终正文只有 5 张主图，没有 Figure 6**。旧包里的 `Figure6.svg` 已废弃，未收录。
2. **S3a、S3c 用的是 2026-09-29 RG 同步后的版本**（`20260929_si_rg_sync`）。`submission_package\figures\` 里的同名文件是 8-30 旧版，不要用。
3. **S8–S10 的 SVG 只存在于报告目录** `20261022_expanded_ratio_report_final_v2\figures\`；10-22 整合交付包里只有 docx/pdf，没有单独图文件。
4. `_large` 版本只原始产出过 Figure 1、S6、S7 三张，其余图没有 large 变体，不是本目录遗漏。
5. 文字形态不一致，投稿前如需统一请留意：Figure 1、S4、S5、S8、S9、S10 的 `svg.fonttype='path'`（文字已转轮廓，任何机器渲染一致）；Figure 2–5、S3a、S3c、S6、S7 保留活字，字体栈为 Arial → DejaVu Sans 回退。

## 已做的校验

- 24 个文件全部与原文件 SHA-256 逐字节一致（见 `MANIFEST.csv` 的 `source_match` 列）。
- 24 个文件全部可被 XML 解析，根元素为 `<svg>`，`width`/`height`/`viewBox` 齐备且自洽（单位 pt）。
- 用 MuPDF 以 72 dpi 逐张渲染，全部成功且非空白（墨迹占比 4.4%–48.7%），无损坏文件。

## 未收录

PNG 与 PDF 版本不在本目录（本次只汇总 SVG）。最终稿实际内嵌的是 PNG；若需要 PDF 或高分辨率位图，按上表源目录取同名 `.pdf` / `.png`。
