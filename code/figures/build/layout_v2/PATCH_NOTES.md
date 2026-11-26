# PATCH_NOTES — 定向修补（v2）

日期：2026-10-06 · 交付根目录：`E:\project\work1\20261006\manuscript_figures_SI_integrated_v2\`
来源：v1 交付 `E:\project\work1\20261006\manuscript_figures_SI_integrated\`（**未覆盖，原件未改动**）

本文件按委托的九节逐条对应。所有定位按**段落内容**而非页码完成；页码只用于交付后的
目视复核。

---

## 一 范围

只做了委托列出的九类事项。**未做**：不重训、不预测、不拟合 scaler、不跑 COMSOL；
不改数据、配对规则、随机基线、案例选择或统计定义；不新增显著性检验、bootstrap 或
研究分析；不整体重写正文；不重排五图结构；不恢复 S19。**数据共享 AUTHOR QUERY 保留**
（正文 P086）。

Figures 1、2、4、5 未重绘、未重导出。Figure 4 只改图注文字（第三节）。

规模变化：

| | v1 | v2 |
|---|---|---|
| 正文 | 18 页 / 7,016 词 | **18 页 / 7,016 词**（未回流） |
| SI | 44 页 / 9,789 词 / 42 表 | **50 页 / 11,334 词 / 50 表**（新增 S6 小节为实质内容） |
| 交叉引用 | 119 条 | **127 条（正文 57 / SI 70），0 条未解析** |

---

## 二 Figure 3 图注 (d)

**改**：原文 "the nine inferred parameters" → **"the nine ground-truth simulation
parameters"**。理由如委托所述：这里比较的是两条**模拟**曲线各自真实的生成参数，
不是模型输出，写成 inferred 会把"真值之间的差"说成"反演误差"。

**保留**：恒等式 `|log₁₀(θᵢ/θⱼ)| = |log₁₀θᵢ − log₁₀θⱼ|` 原样保留；"in physical
log₁₀ units" 的物理 log₁₀ 坐标含义保留。

**未做全局替换**：只改了这一处。检查过全文其余 "inferred parameter(s)" 的用法
（如 P030 "the inferred parameter combinations"、P032 "one inferred curve"、
Figure 4 图注 "inferred parameter combinations"）——那些讲的确实是反演结果，保持
原样。SI 本轮新增文字里也没有把这个参数组描述成预测误差或反演参数差。

---

## 三 Figure 4 图注

**改**：`Case (c) reaches large reverse-bias currents` →
**`Case (c) reaches large negative current densities at high forward bias`**，
其后接委托给出的可选句：**`The inset enlarges the 0–1.0 V region while the main panel
retains the full voltage and current ranges; the inset axis is labelled in mA cm⁻².`**

**删/改误导措辞**：v1 图注里的 "shared vertical scale" 已不存在。该图三个面板各有
独立的纵轴（面板 (c) 到 −1500 mA cm⁻²，面板 (b) 到 −60），说"共用纵轴"是错的。
替换为 **`Panels have independent vertical scales`**，与图中实际刻度一致。

**未做**：曲线、数据、轴范围、案例均未改动；Figure 4 **未重绘、未重导出**。

---

## 四 SI 中新增 Figure 3 两个案例的数值依据

正文引用 "Table S6, T6.7"，而 v1 的 S6 主体仍是旧的五个案例、且没有 500/4560 记录。
本轮在 Table S6 下新增 **T6.7** 小节（**T6.7 lead + 选例规则 + 两案例各自的参数表与
坐标表，共 3 段 + 4 表**）。

内容（每个案例两张紧凑表，避免过宽）：

- **零基 test index**：case (a) 2890 / 5067；case (b) 500 / 4560。
- **可核验的数据库 Sample_ID**：(a) 141475 / 71905；(b) 37892 / 87198。
- **九个参数的名称、单位、两个成员各自的物理值**（T6.7a / T6.7c）。
- **`|Δlog₁₀θ|`** 与 **Factor** 列。
- **六个配对坐标**：三个共同尺度 `a` 与三个对数比 `r` 的两成员值与差（T6.7b / T6.7d），
  末列为 `|Δ| / baseline`。
- **必要的曲线距离与物理电流残差指标，带单位**（两案例各自的 lead 段给出）：
  131 点上的归一化 RMSE `d_J` = **1.950e−4**（a）/ **1.958e−4**（b）；物理 J–V RMSE =
  **0.713** / **0.532 mA cm⁻²**；`max|ΔJ|` = **5.283** / **3.124 mA cm⁻²**，均发生在
  V = 1.30 V，并注明 ΔJ = J_j − J_i。

**倍数规则（硬性）**：Factor 列**只**由 `10^|Δlog₁₀θ|` 生成，代码里只有一个地方
成形（`si_table_s6_new.coerce_factor()`），即"两值中较大者除以较小者"。SI 正文明确
写出 "No factor in this subsection is formed from baseline-normalized or otherwise
rescaled parameter differences."，并由 `verify_si.py` 对全部 18 行断言
`factor == 10**abs_dlog10`。正文引用的 **×443** 与 **×35** 分别对应 T6.7a 的
τ_p_pvk（442.9）与 T6.7c 的 τ_HTL（35.0）。

**旧五案例的处理**：保留，但在 **T6.6** 标题中明确标为
"Representative collision cases … five archived supplementary collision cases"，
并在 lead 中点明它们**不是** Fig. 3 画的那两对（"they are not the pairs drawn in the
main-text Fig. 3, which are tabulated separately in T6.7"）。新小节编号接在既有的
S6 内容之后（T6.6 → T6.7 → T6.8 → T6.9）。正文引用已改为指向该小节。

**数据来源**：`data_used\fig3_case_parameters.csv`、`fig3_case_coordinates.csv`、
`fig3_case_summary.csv` 及 `si_table_s6_7_figure_cases.csv` /
`si_table_s6_7_figure_case_coordinates.csv`（全源精度；表中按显示需要合理取整）。

---

## 五 配对坐标分档表

正文 p6（P025）说百分位子集在 Table S6，v1 的 SI 并未完整给出六坐标的分档比较。
本轮新增 **T6.8（T6.8a 迁移率 / T6.8b 体寿命 / T6.8c 态密度，共 3 表）** 与
**T6.9（随机基线表，1 表）**。

覆盖 Methods 已声明的全部集合：**all、closest 10%、5%、1%、0.5%、0.1%**。每列给出
pair 数、distinct test-sample 数，以及每个坐标的**基线归一化**中位差与四分位距。

**校验点（全部从源文件读出，无一处手写估计）**：

- all = **11,245** pairs / **15,307** distinct samples
- closest 1% = **112**；closest 0.5% = **56**；closest 0.1% = **11**
- distinct samples：15,307 / 1,673 / 876 / 196 / 99 / 21

**归一化是显示换算，不是新分析**：源文件 `si_table_s6_8_tiers.csv` 存的**已经是**
原始坐标差除以同一坐标的随机基线中位数。这一点由独立重算证实（例：`a_mu` 全集的
原始中位差 0.310834 ÷ 基线 0.880111 = 0.353176，与表中存储值逐位相同）。T6.9 列出
六个随机基线中位数及其物理 log₁₀ 坐标定义，使归一化值可溯源。

**措辞约束（已写入 SI）**：四分位距描述的是**配对差的分布，不是置信区间**；配对数
共享样本，**不是独立观测**；**不报告任何 p 值**；接近基线中位数的档位只作为数值报告，
不写成统计上"不可区分"或"无信息"。

正文的表指针已同步为 **"Table S6 (T6.8)"**，指向的表确实承载该主张。

---

## 六 Figure 3 图内文字与选例规则

**保留**：两个案例、四面板结构、全部曲线、数值与误差范围。面板 (c) 的 all-pairs
范围（11,245 对）不变。

**移出图外的纯交接信息**：图内原有的数据库 Sample_ID 与 "database IDs, mapping
verified" 一类说明属于交接信息，不是图的内容——同一对曲线在图内已由 test index
唯一标识，而 index 与 Sample_ID 都在新增的 SI T6.7 与
`data_used\fig3_case_summary.csv` 中。同时删去三行只是重述图注的长文字。图内现在
保留：清晰的 test index、关键坐标信息、物理残差及其单位，以及两行必须留在图面上的
限制说明。

**图注重写**：原图注称 "titles give … indices"，但数字实际出现在图例/标注里，与
最终图像不符。已按图的真实版面改为与位置无关的
**"Cases are identified by zero-based test indices; …"**。

**选例规则（已写入 Methods，并核对过脚本）**：
从修正后的 closest-1% 集合（n = 112）出发，取**绝对迁移率对数比差**最大的那一对为
case (a)；再在**去掉该对之后**的同一档里，取**绝对体寿命对数比差**最大的那一对为
case (b)。已核对 `lib_v2.select_figure_cases()`：脚本按**原始**坐标差排序，因此 SI
中如实写出 "Both were ranked on the raw coordinate differences; dividing a
coordinate by its own fixed positive baseline rescales those differences without
changing their order, so ranking the baseline-normalized differences selects the
same two pairs."。**并列处理**按实际实现记录：`np.argsort(kind="stable")` 沿升序
`d_J` 排序、`argmax` 取首个最大值，即"取升序距离排序中靠前的那一对"。
实测统计量：|Δr_mu| = 1.354456（case a）、|Δr_tau| = 1.266201（case b）；全集
最大 |Δr_mu| = 1.361187 属于 pair 3396 / 13213，**未被画入**（已写入 SI，用来说明
档位限制确实在起作用）。

**图注指向**：图注简短指向 Methods 中的该规则，并保留 "extreme cases chosen by
rule, not random typical cases" 的限制。

**未做**：未换案例、未为版面删数据、未改面板 (c) 的 all-pairs 范围。

**重导出**：Figure 3 重新导出并换入 Word：`figures\Figure3.{png,pdf,svg}` 与
`Figure3_large.{png,pdf,svg}`，脚本为 `scripts\fig3_neighbour.py`。中排
`height_ratios` 由 `[1.150, 0.955, 0.895]` 重平衡为 `[1.300, 0.700, 0.995]`，
以适配缩短后的标注块（复核：标注块距 (c)/(d) 行 +30.5 px（journal）/ +82.5 px
（large）；(c) 标签出框 0.0 px）。

---

## 七 SI 中 "compensation" 措辞

在相关的 Table S6 小节/案例标题中：

| v1 | v2 |
|---|---|
| `Compensation directions` | **`Same-sign parameter differences`** |
| `paired-parameter compensation` | **`Paired-parameter differences`** |
| `bulk transport / recombination compensation` | **`bulk transport and recombination parameter differences`** |

**所有数值保留。** 同号比例与案例差本身不足以验证某种补偿机制，标题不再这样暗示。
正文讨论中作为**可能解释**明确提出的 "compensating parameter changes" 一类正当用法
保留（正文 P002 / P040 / P045 三处，均为物理描述，非机制论证）。

**未做机械全局替换**：逐条读取上下文后改的。复核结果：整个 SI 中 "compensat*"
出现次数为 **0**（由 `verify_si.py` 断言）。

---

## 八 排版修补

### 8.1 两个 7 pt 段落

v1 第 8 页有**两段** 7 pt 正文：一段以 "Physical back-substitution evaluates…" 开头，
一段以 "Selected device metrics remain close…" 开头。两者整段异常的真实机制是：
**该段每一个 run 都带 `w:vertAlign="superscript"`**，Word 因此把整段按上标比例
（约 58–65%）排版，文件里**没有任何 `w:sz`**。

**已恢复为 11 pt**，做法是**只**移除段级/运行级的 `w:vertAlign`，段落样式不动，因此
文字与其邻居同字号同风格。

- `Normal` 样式 rPr 只有 `rFonts eastAsia="Times New Roman"` 与 `color 000000`；
  `docDefaults` 设 `w:sz=22`（11 pt）——所以去掉 vertAlign 即回到 11 pt。
- **上标/下标格式未被压成正文大小**：这些上标是文本里的**字面 Unicode 字符**
  （⁻⁷、⁻²、×、10），不是格式，去掉 vertAlign 后仍按上标字形显示。渲染件复核：
  两段现为 11.04 pt（v1：6.96 pt 正文 + 5.52 pt 上标）。
- 代码在改动前有前置断言：**只有整段每个 run 都是上标时**才允许剥离，混合段落会被
  拒绝（`build_manuscript.py` 的 `all_superscript()` 守卫），避免误删有含义的上标。
- 全文只有这两段是纯上标段。

**版面回流被允许**：正文仍为 18 页，未强行凑页。

### 8.2 SI Table S5 表头

`Recoverability` 曾在 `Recoverabilit / y` 处断开。修法是**调列宽**，不是删字：
原来六列均分 1320 twips，该列只有 55.2 pt 内容宽，而 "Recoverability" 一词在 12 pt
Times New Roman 下需要 70.6 pt。改为 `[1280, 1120, 1060, 1320, 1300, 1840]`
（仍合计 7920 twips）：从两个公式列各取 200 twips 补给末列，另从参数列调整，使
"Parameter"（48.5 pt）也不会改成断在中间。

第一次尝试 `[1000,1320,1320,1320,1320,1640]` 把断词从末列搬到了首列
（`Paramete / r`），是**渲染出来读页面**时发现的，随后用 PIL 实测真实表头字串宽度
重新解算。**数值未改**；表注无需同步（表注未提及列宽）。渲染复核：`Parameter`、
`Rank (raw)`、`Rank (log)`、`Recoverability r` 均在单行内。

### 8.3 图前后留白

未处理。未为了减少留白缩小整图，未固定页数，未把每条图注绑成一个不可拆分的巨块。

---

## 九 验收与交付

自动检查 `scripts\verify_si.py`（**115 项，全部 PASS，0 FAIL**），覆盖：

- 两个图注错误都已改（"ground-truth simulation parameters" 在、v1 措辞不在；
  "large negative current densities at high forward bias" 在、"shared vertical
  scale" 不在）。
- **两个新案例在 SI 中找得到**：test index 对与 Sample_ID 对都出现在 T6.7 lead 及
  案例 CSV 中；两张参数表与两张坐标表**逐格**对回 CSV。
- **分档表完整且与冻结 CSV 一致**：三张 T6.8 表的计数、中位数、四分位距全部对回
  `si_table_s6_8_tiers.csv`；四个校验点 11,245 / 112 / 56 / 11 命中。
- **Figure 3 图像 / 图注 / Methods / SI 四处对案例与集合的说法一致**：图注指向
  Methods 的哪一节，就用脚本打开那一节读，确认它真的写了选例规则（不是只检查编号
  存在）；正文引用的 ×443 / ×35 分别对回 T6.7a 的 τ_p_pvk 与 T6.7c 的 τ_HTL。
- 两段 7 pt 已恢复（段落内不再有段级 vertAlign）。
- S5 表头不再断在词中。
- 新表无截断、无溢出、单位无误。
- 未新增任何不支持的机制或显著性主张；SI 中 "compensat*" 为 0。
- **数据共享 AUTHOR QUERY 仍在**（正文 P086）。
- **S19 未恢复**（正文中 "S19" 出现 0 次）。

四个验收脚本全部 PASS：`qa_layout.py`、`figure_font_audit.py`（17.27 cm 下最小图内
字号 7.0 pt ≥ 6 pt 底线）、`svg_pdf_audit.py`、`cross_reference_map.py`
（127 条，0 未解析）。

**实际渲染件目视**（不是用脚本成功代替目视）：

| 看的地方 | 结果 |
|---|---|
| 正文 Figure 3 页（p7） | 新图 + 改正后的图注；(d) 为 ground-truth 措辞；图内无交接信息 |
| 正文 Figure 4 图注页（p9） | 改正句子就位；图中三面板确为独立纵轴 |
| 正文原 p8 两段及其邻居（p8） | 两段均为正文大小，上标仍为上标字形 |
| 正文 Methods 页（p15） | "Curve similarity and parameter ambiguity" 下确有完整选例规则 |
| SI p5（S5 表） | `Parameter` / `Recoverability r` 均单行 |
| SI p6、p10–p16（S6 新旧小节及邻居） | T6.7/T6.8/T6.9 完整，无截断、无溢出、单位清楚 |

**两份 PDF 都已 `restore_hd.py` 换回高清位图流**（Word 导出会把位图压到 200 ppi；
换回后文字与版面逐字节相同，仅位图分辨率不同）：正文 1.46 MB → 5.90 MB；SI
2.25 MB → 15.61 MB。

---

## 本轮的诚实说明（未完成项 / 已知副作用）

1. **P030 出现新的断行副作用（已报告，未擅自修改文本）。** 恢复到 11 pt 后该段变长，
   现在断为 `…1.19 × 10⁻⁷ mA cm⁻` / `², confirming…`，即上标 `²` 被孤立到下一行行首。
   v1 在 6.96 pt 下没有这个断法。这是恢复字号的**必然副作用**，不是新缺陷。
   若要消除，最小改法是在 `⁻` 与 `²` 之间插入一个 word joiner（U+2060）——那是一处
   不可见字符改动，会动到导师的文本，**因此留给导师决定**，本轮不擅自插入。

2. **SI 由 44 页增至 50 页**。新增的 T6.7–T6.9 是委托要求的实质内容（两案例全参数
   表 + 分档表 + 基线表，共 8 张表 / 11 段），页面增加是内容增加的结果，不是版面
   松动。T6.9 的表在 p15/p16 之间**带重复表头**跨页，两页都完整可读。

3. **正文图注中 "Methods (Curve similarity and parameter ambiguity)" 的写法**：查找
   后未发现稿内既有"引用 Methods 子节"的成文体例（既有的交叉引用都是图表编号），
   因此按委托要求把节名完整写出，而不是只写编号。

4. **本轮构建过程中发现并已修正的一处自身缺陷**：新增 S6 小节的插入锚点原先取
   `doc.tables[15]`，而那是 **case E 的参数表本身**（不是 S6 块的末元素），结果新小节
   被插到 case E 的 lead 与其表格**之间**，把那张表孤立到 T6.9 之后，在渲染件上表现为
   p15 出现一张无标题的表。已改为按文本定位 "Table S7." 前的空段落作为锚点，并在构建
   时断言 "case E 的 lead 后面紧跟它自己的表"。交付件中此问题已不存在。

5. **术语统一的措辞**：日志与报告一律写成"**按导师要求统一为 log₁₀ units**"，
   未把它描述成普遍的科学纠错（`report\QA.md` §2.4 与中文要点已同步改）。

6. **未做的事**：未重训、未预测、未拟合 scaler、未跑 COMSOL；未改原始数据与冻结模型；
   未对正文做整篇语言润色。Figures 1、2、4、5 未重新生成（本轮三个审计脚本会重跑
   全部图形，但 **PNG 逐字节不变**，因此 Word 中嵌入的图仍与 `figures\` 一致；
   变化的只有 PDF/SVG 的生成时间戳与随机 id）。
