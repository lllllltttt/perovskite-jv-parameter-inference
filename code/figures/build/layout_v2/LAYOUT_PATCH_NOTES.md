# 局部排版修补 — 正文单位断行 + SI 两处表格分页

日期：2026-10-07 · 交付根目录：`E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final\`
底稿：`E:\project\work1\20261006\manuscript_figures_SI_integrated_v2\`（**未覆盖**，只读）

本轮**只做三件事**：正文一处单位断行、SI 一张表的行跨页拆分、SI 一张表的孤立表头。
没有改动科学内容、数据、图片、统计方法、参考文献；没有重跑模型、统计或绘图；
没有重排全稿；没有覆盖任何输入文件。验收一律以**最终导出 PDF 的实际渲染**为准，
不以 DOCX 里"已加入某字符"或"已设置 cantSplit"为准。

---

## 一、正文 p8：`cm⁻²` 不再断开

**现象**（v2 PDF p8 首段）：
`... with a median RMSE of 1.19 × 10⁻⁷ mA cm⁻` / 换行 / `², confirming ...`
负二次方的 `²` 单独落到下一行行首。

**修法**：在 `cm` 与上标负号之间、负号与 `²` 之间各插入一个
**U+FEFF ZERO WIDTH NO-BREAK SPACE**（零宽不换行空格），使整个 `cm⁻²` 成为一个
不可断行的单位。正文 11 pt、负二次方上标、原句文字与数值 `1.19 × 10⁻⁷` 全部保留；
没有整段缩字号，没有改成普通基线的 `cm-2`。

**关键发现 — 上一轮为什么没修好**：先前用的是 **U+2060 WORD JOINER，Word 不认**。
用一个与真实版式等宽的对照实验（同一段文字、四种写法、逐一导出 PDF）可以复现：

| 写法 | 结果 |
|---|---|
| 原样 `cm⁻²` | `cm⁻` \| `²,` — 复现故障 |
| U+2060 ×2 | 仍然在 `⁻` 后断行 — **Word 忽略 U+2060** |
| U+2060（仅负号后） | 仍然断行 |
| **U+FEFF ×2** | `mA` \| `cm⁻²,` — **整块下移，不再断开** |

**最终 PDF 实测**（不是断言）：

- 全文 `U+207B` 与 `U+00B2` 之间发生换行的次数：v2 = **1**，最终 = **0**。
- p8 目标行实际渲染为 `... mA` ⏎ `cm⁻², confirming consistency of the parameter transfer`。
- 字距（同一行内字符包围盒）：`⁻`→`²` 的间隙 v2 = **−489.8 pt**（换行回行首），
  最终 = **+0.067 pt**（紧邻，无可见空隙）。
- 字号实测 **11.04 pt**（即 11 pt），与改前一致。
- U+FEFF 在 PDF 中**不产生任何字形**，拷贝出的文本仍是 `cm⁻²`。
- 全文另有 22 处 `⁻²`，改前改后都完好，未做改动。

---

## 二、SI：T6.8b 的行不再跨页拆开

**现象**（v2 SI）：p14 页底是 `median` 加六个统计数值，p15 页首是该行标签剩下的
`|Δa| / bₐ` —— 同一表格行被页边界劈成两半。

**修法**：对 **T6.8a / T6.8b / T6.8c** 三张表的**全部数据行**写入
`<w:cantSplit/>`（即关闭 Word 的"允许跨页断行"）。v2 中这三张表**没有任何一行**
带过这个属性（实测 `cantSplit before=0`）。
`<w:tblHeader/>` 原样保留 —— 表格照常跨页、表头照常重复，
**没有**把长表强行绑到一页。

**最终 PDF 实测**：

- 四组统计标签（`median |Δa| / bₐ`、`IQR |Δa| / bₐ`、`median |Δr| / bᵣ`、
  `IQR |Δr| / bᵣ`）在三张表中共 12 处，**12/12 标签与其六个数值同页完整**；
  v2 为 11/12（缺的正是 T6.8b 的 `median |Δa| / bₐ`）。
- 没有任何一页以裸露的标签片段（`median`、`Distinct`、`curves` …）结尾。
- p15 页首实际渲染为：重复表头 `Statistic | all | 10% | 5% | 1% | 0.5% | 0.1%`
  紧跟完整的 `median |Δa| / bₐ | 0.312 | 0.454 | 0.411 | 0.322 | 0.354 | 0.118`。

---

## 三、SI：T6.9 不再有孤立表头

**现象**（v2 SI）：T6.9 的表头行留在 p15 页底，六行数据全部落到 p16。

**修法**：在 T6.9 **表头行**各单元格段落的 `pPr` 上写入 `<w:keepNext/>`
（"与下段同页"），表头因此必须与紧随其后的**第一条数据行**同页。
同样对该表数据行加了 `cantSplit`。表头重复（`tblHeader`）保留，字号未缩小。

**最终 PDF 实测**：

- 承载 T6.9 表头的页面：p16；该页同时含第一条数据行 `a, mobility` —— **孤立表头 0 个**（v2 为 1 个，在 p15）。
- T6.9 **表题仍留在 p15 页底**。这是刻意的选择：若把表题一并下推，p15 页底会空出
  约 210 pt（7 cm），属于明显的异常留白；只下推表头行时 p15 页底留白约 37.6 pt。

---

## 四、导出与验收

从**修改后的 DOCX** 重新用 Word 导出两份 PDF，再按本包既有流程跑
`scripts\restore_hd.py` 把位图换回高清流（Word 导出会把位图压到 200 ppi）。

| | v2 | 本轮 | 说明 |
|---|---|---|---|
| 正文页数 | 18 | **18** | 未变 |
| SI 页数 | 50 | **50** | 未变 |
| 正文文字有变化的页 | — | **仅 p8** | 逐页比对 |
| SI 文字有变化的页 | — | **仅 p14、p15** | 逐页比对（p16 及以后逐字未变） |
| `restore_hd` 换回高清位图 | — | 正文 **5** 张 / SI **9** 张 | 换图后 `text : IDENTICAL` |

**内容等价性（token 级，非目视）**：

- 正文：v2 分词为 `cm⁻` + `²,`，最终为 `cm⁻²,`，**除此之外全文 token 完全一致**。
- SI：最终比 v2 **正好少一份 T6.9 表头行的重复拷贝**（`Coordinate / Definition / in /
  physical / log₁₀ / values / Random-pair / median / |Δ|` 各少 1），
  **除此之外全文 token 完全一致** —— 那是页边界移到表头之后不再需要的重复表头。

**相邻页几何（最终 PDF 实测，`verify_layout_patch.py` 第 4 项）**：

| 页 | 出界文本 | 文本重叠 | 页底留白 |
|---|---|---|---|
| 正文 p8 | 0 | 0 | 与 v2 相同 |
| SI p14 | 0 | 0 | 10.9 → **35.2 pt** |
| SI p15 | 0 | 0 | 19.0 → **37.6 pt** |
| SI p16 | 0 | 0 | 15.7 pt（**未变**） |

p14 / p15 页底多出的 1.2–1.3 cm 是"行不许拆、表头不许孤立"的**直接且不可避免的代价**：
被拆开的行整体下移一行、孤立表头下移一行。两页仍然都是满页（正文区高约 745 pt），
不构成异常留白；p16 及以后完全未受影响，没有新增遮挡、截断或空洞。

**验收脚本**：`scripts\verify_layout_patch.py <manuscript.pdf> <si.pdf>`，
对**最终交付的 PDF** 逐项判定，四项全过；日志见 `report\LAYOUT_PATCH_QA.log`。
`RESULT: PASS — all four checks`。

---

## 五、交付物

```
manuscript\Manuscript_20261002_Working_integrated.docx / .pdf   正文（18 页）
si\Supplementary_Information_synced.docx / .pdf                 SI（50 页）
render_checks\   三处修复位置的最终 PDF 渲染截图（另附 v2 对照，见下）
LAYOUT_PATCH_NOTES.md      本文件
report\LAYOUT_PATCH_QA.log 验收脚本输出
scripts\patch_manuscript_unit.py / patch_si_tables.py / verify_layout_patch.py
```

截图（300 dpi 直接由最终 PDF 渲染）：

| 文件 | 内容 |
|---|---|
| `01_manuscript_p8_unit_BEFORE_vs_AFTER.png` | 正文 p8 目标段，上=v2，下=最终 |
| `02_si_p15_top_T68b_row_BEFORE_vs_AFTER.png` | SI p15 页首，上=v2（孤立续行），下=最终（整行） |
| `03a_si_p15_bottom_T69_orphan_header_BEFORE_vs_AFTER.png` | SI p15 页底，上=v2（孤立表头），下=最终（无表头） |
| `03_si_p16_top_T69_header_rows_BEFORE_vs_AFTER.png` | SI p16 页首：表头与第一条数据行同页 |
| `02_si_p14_bottom_T68a_end_*.png` | 佐证：p14 页底以完整行结束 |

v2 原样对照图在 `render_checks\before_v2\`。

**校验和（sha256 前 16 位）**

| 文件 | 输入 v2 | 本轮交付 |
|---|---|---|
| 正文 docx | `04f9acaba355694d` | `d439f4d9b955d67f` |
| 正文 pdf | `3412ab151ec598dd` | `65a0578a15a74c6c` |
| SI docx | `2c84cc9969e47f84` | `80cb49027d12aa69` |
| SI pdf | `b488c9c7291d4d96` | `b896a1819d8d6b03` |

交付目录里的 PDF 就是跑完四项验收的**同一份文件**（截图与校验和均由该文件生成）。

---

## 六、没有做的事

- 没有动科学内容、数据、图片、统计方法、参考文献。
- 没有重跑模型、统计或绘图；`figures\`、`data_used\` 与 v2 逐字节相同。
- 没有把 T6.9 表题一并下推（会留下约 7 cm 异常留白）；没有把长表绑到一页。
- 没有缩小任何字号，没有把单位改成普通基线写法。
- 没有顺手修改正文里另外 22 处 `⁻²`（改前改后都完好，不在范围内）。
- 没有覆盖 `manuscript_figures_SI_integrated_v2\` 下的任何文件。

## 七、复现

解释器 `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`，
环境变量 `PYTHONIOENCODING=utf-8`。

```
python scripts\patch_manuscript_unit.py <pkg>\manuscript\...integrated.docx
python scripts\patch_si_tables.py       <pkg>\si\..._synced.docx
powershell -File scripts\render.ps1 -Docx <pkg>\manuscript\...integrated.docx
powershell -File scripts\render.ps1 -Docx <pkg>\si\..._synced.docx
python scripts\restore_hd.py <pkg>\manuscript\...integrated.docx
python scripts\restore_hd.py <pkg>\si\..._synced.docx
python scripts\verify_layout_patch.py <pkg>\manuscript\...integrated.pdf <pkg>\si\..._synced.pdf
```

两个 `patch_*.py` 都是幂等的守卫式脚本：找不到目标会直接断言失败，不会静默跳过。
`restore_hd.py` 必须在**每次**重新导出 PDF 之后再跑一次。
