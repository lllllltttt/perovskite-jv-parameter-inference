# Figure 2 修订说明（PATCH_NOTES）

日期：2026-11-08
目录：`E:\project\work1\20261108_fig2_supervisor_revision`
底稿：`20261006\manuscript_figures_SI_integrated_v2_layout_final`（原始文件未改动，本目录为新建）

本轮按要求**只做 Figure 2**：不改正文、不改 SI、不动 Figure 3。

---

## 一、导师四条意见的落实位置

| 导师意见 | 落实 | 位置/文件 |
|---|---|---|
| ① 公式按“第二页”写，复用已有符号、上下标与单位 | 两组组名直接写完整公式：`Shared scale a = (log₁₀ pₙ + log₁₀ pₚ)/2`、`Electron–hole log-ratio r = log₁₀(pₙ/pₚ)`；分母为 pₚ；DOS 用 N_c、N_v；每列标题下加一行成对参数与单位 `μₙ, μₚ (m² V⁻¹ s⁻¹)` / `τₙ, τₚ (s)` / `N_c, N_v (m⁻³)` | `scripts/fig2_build.py`（组名与列单位行）；图内顶部与中部的组名行 |
| ② 六个散点改名 a1/a2/a3、b1/b2/b3，编号位置、轴名 | 上排 (a1)(a2)(a3)=共享标度，下排 (b1)(b2)(b3)=电子–空穴对数比；编号在**每个框左上角外侧**；列标题只写一次；轴名简化为 `True a / Predicted a`、`True r / Predicted r`；旧的“蓝色；面板 a–c”提示已删除 | 同上；`figures/Figure2_revision.png` |
| ③ 原 (g)(h) 合成一行两列并共享图例 | 新 (c) Pearson 相关、新 (d) MAE 降幅（相对**训练集中位数**基线）；两框等高、各自 y 轴、柱从 0 起；**一处共享图例**放在下方块内、两个柱图之上，不压柱顶数值，也不必把 (c) 的纵轴抬到 1.3（现为 0–1.05） | 同上，`_legend()` |
| ④ 蓝橙配色疲劳 | 改为 Seaborn deep 前两色：共享标度 `#4C72B0 (76,114,176)`、对数比 `#DD8452 (221,132,82)`；散点、柱、图例三处含义固定 | 同上，`C_A / C_R` |

## 二、Figure 3 / SI 是否随之改动

- **Figure 3：本轮未改**（按要求先只做 Figure 2）。前期已查明它只有 (c) 面板用颜色区分 a 与 r（(a)(b) 区分曲线 i/j、(d) 区分 pair (a)/(b)，语义不同）；若日后要同步，只改 (c) 的两色即可，`scripts/fig3_color_sync.py` 已备好但**未纳入本次交付**。
- **SI：未动**。核查过 SI 只有一处提到“the coordinate analysis of Fig. 2 and Table S11”，不带子面板字母，正文/图号改动不会造成断链。

## 三、最终检查结果

| 检查项 | 结果 |
|---|---|
| 画布 | 6.80 × 7.26 in = **172.7 × 184.3 mm**（旧图 172.72 × 187.16 mm，高度略减） |
| 单幅散点框 | 1.763 in 正方形 = 44.8 mm，六框等宽等高、按列对齐 |
| 对角线 | 每框 x、y 同为同一范围、同一刻度集，框为正方形 → y=x 为真 45° |
| 最小字号 | 7 pt ≥ 6.71 pt（0.3886 pt/cm × 17.27 cm 下限） |
| 12 个存档数值 | 全部由冻结数据重算并断言到 5e-7：ρ 0.925/0.882/0.925、0.429/0.352/0.266；MAE 降幅 68.1/61.3/66.3 %、8.4/2.7/0.8 % |
| 散点与柱状一致性 | 两处 ρ 取自同一 dict，逐项相同 |
| 0.8% 柱 | 真实高度保留（非最小值截断），柱顶数值可读 |
| 图例 | 一处，位于下方块内、两柱图正上方；不压柱顶数值 |
| 出界裁剪 | PNG 四边 3 px 内无墨迹，无文字被裁 |
| 刻度负号 | 使用排版减号 U+2212（非 ASCII 连字符），与公式内减号同字形 |
| 配色来源 | Seaborn `SEABORN_PALETTES["deep"]`，`https://github.com/mwaskom/seaborn/blob/master/seaborn/palettes.py` |

## 四、可编辑 SVG（`figures/Figure2_editable.svg`）

做法：matplotlib 导出 SVG 时会把每个数学串拆成**逐字定点**的 `<tspan>`（3.10 更是一字一个 tspan），这正是之前“点进去是一堆碎字、改一个词就散架”的原因。`scripts/svg_textify.py` 按绘图时记下的 25 条标签登记表，把每一条**整体重建成一个 `<text>`**，上下标用行内 `<tspan>` 的 `font-size + dy` 表达，普通标题/刻度/数值本来就是单个 `<text>`，并把 CSS 简写展开成 `font-family` / `font-size` / `font-weight` 属性。

结构校验（`work/svg_verification.txt`）：
- `<text>` 125 个；逐字 x 列表 **0** 个；
- `<path>` 65/65、`<use>` 68/68，与原始 SVG 相同 → **没有任何文字被转成轮廓**；
- 6 个 600 dpi 散点栅格图片原样保留（密集散点局部栅格化，轴/文字/图例为矢量文字）。

浏览器渲染比对（Edge headless，原始 SVG vs 可编辑 SVG，同一引擎分别栅格化）：8 个文字带中 7 个边缘差 ≤ 3 px（2× 截图），仅顶部组名公式因去掉逐字定位后按字体自然排布而**变窄 11 px ≈ 4.1 pt**（约 1.5%），文字基线、锚点、旋转均无位移。

**诚实说明**：本机**没有 Adobe Illustrator**，因此没有、也不能声称“在 AI 里测过”。已验证的是：文件里是真正的活文字（每条逻辑标签一个 text 对象、行内 tspan、无轮廓化、无逐字拆分），并且用浏览器引擎渲染与原始 SVG 逐像素对齐。

## 五、还需要作者手工做的事

1. 如需装进正文：替换 Fig. 2 图片（按 172.7 mm 宽）、改写图注为 (a1–a3)/(b1–b3)/(c)/(d)、把正文 “Fig. 2g” 改为 “Fig. 2c”、“Fig. 2h” 改为 “Fig. 2d”。**注意新 2c 是 Pearson 柱状图，旧 2c 是 DOS 散点（现为 a3），不能全局机械替换。**（本轮按指示未做）
2. 在 Illustrator 里打开 `Figure2_editable.svg` 后，建议先确认 Arial 已装（文件里写的是 Arial，不是替代字体）；如需送审，另存为 PDF 时勾选“保留编辑能力”即可，送审请用 `Figure2_revision.pdf`。
3. 图注里若要提配色，只写“蓝色为共享标度、橙色为对数比”，**不要**写成期刊指定色板（本图用的是 Seaborn deep 前两色）。

## 六、文件清单

```
figures/Figure2_revision.pdf      送审用矢量 PDF（172.7 × 184.3 mm）
figures/Figure2_revision.png      600 dpi 位图（4080 × 4353 px）
figures/Figure2_editable.svg      可编辑母版（活文字）
figures/Figure2_revision_raw.svg  机器原始输出（对照用，勿投）
figures/panels/Figure2_panel_{a1,a2,a3,b1,b2,b3}.{png,pdf,svg}
                                  六张无标题单幅散点图（仅散点+框+刻度+刻度数字+y=x 虚线）
data_used/fig2_coordinates.csv    15307 条测试曲线的 12 个坐标
data_used/fig2_metrics.csv        ρ 与 MAE 降幅（含基线）明细
scripts/fig2_data.py              从冻结 npz 重建坐标并断言 12 个存档值
scripts/fig2_build.py             整图拼装（布局、文字、图例）
scripts/svg_textify.py            SVG 文字化（25 条标签重建为单一 <text>）
scripts/fig2_panels.py            六张单幅面板
scripts/verify_svg.py             SVG 结构与浏览器渲染核验
work/svg_verification.txt         上述核验报告
work/textify_report.txt           标签重建明细
```
