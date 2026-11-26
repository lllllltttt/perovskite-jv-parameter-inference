# 正文 Figure 1–5 / SI S1–S11 图片清晰度修复（2026-11-25）

## 1. 底稿与图源

| 用途 | 路径 |
|---|---|
| 正文底稿 | `20261125_integration/deliverables/Manuscript_20261125_final_figures_text_corrected.docx` |
| SI 底稿 | `20261125_integration/deliverables/Supplementary_Information_20261125_final_figures_text_corrected.docx` |
| 正文图 PPT | `20261125_integration/finalfig/正文/正文_fig.pptx`（5 页 = Fig 1–5） |
| SI 图 PPT | `20261125_integration/finalfig/SI/SI_fig.pptx`（11 页 = S1–S11） |
| 导出的组合 SVG | `finalfig/正文/图片1–5.svg`、`finalfig/SI/SI1–11.svg`（以及 Word 内另存的同内容副本） |
| 原始面板矢量 | `20261109_fig2_final_D_assets`、`20261110_fig4*`、`20261110_fig5_standalone`、`20261111_fig345_standalone_revision`、`20261112_fig3ab_shared_yaxis`、`20261112_fig4d_*`、`finalfig/SI_fig.pptx` 内嵌 SVG |

两张底稿**未改动**；原文件均保留。

## 2. 病根（实测）

PowerPoint「另存为图片 → SVG」把**每一张被摆放的位图**重采样成很小的一张 JPEG：

- Figure 2：6 子图 2100×2235 → **263×280 JPEG**，2 色条 540×2235 → **68×280 JPEG**（约 1/8，≈65–79 dpi）；
- Figure 3：1980×1620 → **339×278**（68 dpi）；
- Figure 4：1560×1464 → 250×234、1913×1899 → 206×204、1008×600 → 161×96（62–84 dpi）；
- Figure 5：1200×900 → 329×247 / 282×248（78–134 dpi）；
- S7：600 dpi 散点层 → 285×259（104 dpi）；S5：直方图柱条被拆成 336 张 6–8 px 小图（131 dpi）；
- S6：64 MB 矢量 SVG 无法进 Word，文档里只有 1180×1078 PNG（188 dpi）。

矢量部分（标题、轴名、ρ、(c)(d) 柱图等）**没有**损失。
见 `CHECKLIST.md` 逐图明细。

## 3. 做法

1. 以导出 SVG 为版式底稿，**矢量内容逐字节保留**；
2. 把每个降采样 `<image>` 换成 PPT/素材目录里的**原始面板 SVG**，按原 `matrix()` 链
   （含 1.00427 类微拉伸、`srcRect` 裁剪对应的图框）原位嵌入 → 面板恢复为矢量文字 +
   900 dpi 散点栅格；
3. S4/S5/S7 这类“整页=若干面板图片、无 PPT 文字”的图，用**坐标轴矩形对齐**把面板 SVG
   放回原位（面板自带白底覆盖掉残留碎片）；
4. S6 由 64 MB 矢量 SVG 重出 600 dpi PNG（Word 不能吃这个尺寸的 SVG）；
5. Word 导出 PDF 后，用 PyMuPDF `replace_image` 把 Word 压到 ~200 dpi 的位图换回原生栅格
   （`word-pdf-200ppi-restore` 的同一套办法）。

**没有**使用截图、放大、锐化、AI 超分或只改 DPI 元数据。

## 4. 交付物

```
highres_20261125/
├─ deliverables/
│  ├─ Manuscript_20261125_highres.docx / .pdf            (19 页)
│  └─ Supplementary_Information_20261125_highres.docx / .pdf (69 页)
├─ figures/      16 幅：<Figure>.svg / .pdf / .png(600 dpi)
├─ scripts/      全部生成与校验脚本
├─ CHECKLIST.md  逐图检查表
└─ README.md
```

- 正文图 6.80 in 宽，SI 图 6.27 in 宽（与 docx `wp:extent` 一致）；
- PNG 均为 600 dpi 白底（Figure 2 = 4080×3641，S6 = 3762×3439 …），尺寸见 `figs/figure_sizes.json`。

## 5. 最终 SVG 内部位图清单（逐个解码实测，不看扩展名）

| 图 | 位图数 | 实际像素 | 最小有效分辨率 |
|---|---|---|---|
| Figure 1 / 3 / 4 / 5 | 0 | 纯矢量 | — |
| Figure 2 | 8 | 1329×1444、1007×1543、1449×1457、1201×1062、1204×1300、1205×1225、77×1080×2 | **865 dpi**（散点 1067） |
| Figure S1 | 2 | 511×511、30×511 | 201 dpi（源即 100 dpi 栅格） |
| Figure S2/S3/S4/S5/S6/S9/S10/S11 | 0 | 纯矢量 | — |
| Figure S7 | 9 | 1138×1035 … 1141×1056 | **653 dpi** |
| Figure S8 | 1 | 239×189 | 108 dpi（源即低清，未修） |

## 6. 校验

- 两份 PDF 与底稿 PDF **逐页文字完全一致**（19/19、69/69 页，0 页差异），页数相同，
  caption 与图同页，编号连续。
- 正文 Fig 3/4/5 的 PDF 页面里**没有任何位图**（`get_images` 返回 0）。
- Fig 2 页面位图 1068 dpi、S7 655 dpi、S6 600 dpi。
- 图与底稿的位置、纵横比、插入尺寸不变（`wp:extent` 未改）。

## 7. 未解决项（如实列出）

1. **Figure S8**：唯一未修的一幅。该面板在 PPT 里是 239×189 PNG（108 dpi），
   在 `20261116_figs8_split`、`20261117_si_s4_s5_s8`、`20261119_si_s8_arial`
   中都没有匹配到对应的矢量源；按规则不放大、不重画，保持原样。
2. **Figure S1**：相关矩阵与色条的栅格是**源面板 SVG 自带**的 100 dpi 位图，
   源即如此；显示 201 dpi。9×9 实色块 + 平滑色条，放大看不出差别。
3. **S4 / S5 的 Word PDF**：SVG 里柱条/碎片已是矢量，但 Word 的 PDF 导出器仍会把
   这些实心矩形自行栅格化成 6–16 px 小图（96 dpi）。同一幅图的独立 PDF（`figures/`）
   是纯矢量。这是 Word 渲染器的行为，无法通过换图消除。
4. **Word PDF 的位图上限**：Word 导出 PDF 时把位图压到 ~200 dpi；本文档已用
   `replace_image` 换回原生分辨率，但若用户再次用 Word 重新导出，会重新被压到 200 dpi。

## 8. 本轮定点修复（2026-11-25 v2）

只动两处，其余图与正文未碰；上一版整包保存在 `archive_v1/`。

1. **Figure 3(c)(d) 图例对齐**：色块原比文字低 ≈0.96 pt（(c) 第二行 1.04 pt）。
   按文字可见字形（cap 高）的光学中心重排色块：`fix_legend.py` 读每行的
   `translate_y + tspan y` 得基线，目标中心 = 基线 − 0.358 em（Arial cap 高 0.716 em），
   色块高 4.9 pt 保持不变。(c) 两行 18.898 / 27.351，(d) 两行 18.998 / 27.748；
   色块尺寸、行距、色块—文字 2.8 pt 间距、字号配色与位置均未变。
2. **Figure S8(d)**：原 239×189 PNG（108 dpi）换成矢量。该面板是 ECDF 的
   rμ（mobility）子图 = `20261116_figs7_split/out/svg/S7b.svg`；
   原图例（random pairs / nearest-neighbour pairs）按冻结图里的位置补回，
   曲线、坐标范围、刻度、虚线、配色全部沿用原矢量，未重算数据。

校验（v2）：

| 项 | 结果 |
|---|---|
| 两份 PDF 与底稿逐页文字 | 19/19、69/69 页 **0 页差异** |
| Figure 3 渲染与上一版 | 平均差 0.034/255，差异仅落在图例色块带（x 1253–3776, y 1903–2031） |
| Figure 3 色块中心 vs 文字光学中心 | (c) 两行 −0.06 pt 内；(d) 两行 −0.06 pt 内（600 dpi 下 ≤1 px） |
| Figure S8 与上一版 | 差异仅限 (d) 面板；轴标签包围盒逐像素相同（1658–2571 / 2380–2409） |
| S8 页位图数 | Word PDF 第 55 页 `get_images` = **0** |
| PDF 图像替换（p5/p49/p54/S6） | 尺寸/位置/纵横比不变，SMask 保留（透明度未丢） |
| 页数 | 19 / 69，与底稿一致 |

## 9. v3：S8(d) 图例线—文字对齐（2026-11-25）

上一版 (d) 的图例线段没压在文字上：灰线比 “random pairs” 的字形中心高约 3 px、橙线比
“nearest-neighbour pairs” 偏低约 1 px（两条线是我按冻结位图逐像素量的，本身不一致）。
现改为与 Figure 3 相同的规则：**线段中心 = 文字基线 − 0.358 em（Arial cap 高的一半）**，
两条线各自对自己的行，行距、线段长度、字号、配色、图例位置均不变。

校验：最终 PDF 第 55 页 600 dpi 下，灰线中心与该行字形中心差 0.36 pt（<1 px），
橙线同规则；该页位图数仍为 0；SI PDF 与底稿逐页文字 0 页差异、69 页不变。

## 10. v4：S8(d) 图例改为整体复用 (a) 的图例（2026-11-25）

上一版 (d) 的图例是手绘的（自排文字 + 两条线段），字号/间距与 (a) 不一致。
本版改为**整组复用 (a) 的图例几何**：

- 取 `S7a.svg`（ECDF 的 aμ 面板）里的 `<g id="legend_1">`——包含白色底框、两条样例线
  和全部文字轮廓路径（class="glyphs"），**原样平移**到 (d) 的坐标系
  （`translate(165.906 0)`，即两面板 viewBox 原点之差 = 坐标轴原点之差）；
- 仅把第二条样例线的 `#0072b2` 改成 `#d55e00`；灰线 #9a9a9a、线宽 1.3/1.6、
  文字轮廓、字号、行距、线段长度、线段—文字间距、相对坐标轴右下角的留白全部来自 (a)；
- 未改面板尺寸、数据、曲线、坐标轴、刻度或其他文字；图例仍是矢量。

校验（最终 SI PDF 第 55 页，600 dpi）：(a)(d) 两行文字墨迹高度均 59 px、
“random pairs”宽度均 516–517 px；两条样例线长度、右侧与底部留白一致；
并排预览见 `figures/FigureS8_legend_compare.png`。
