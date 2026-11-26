# A1_interval_repair — 第三轮：scaler 来源实证改标签 + 宽度图排序修复 + raw/clip/prior 与 mean/median 分开报告

脚本 `scripts/a1v3_interval_repair.py` + 独立复核 `scripts/a1v3_qc.py`。**纯后处理**（冻结
test 集上重放冻结 scaler/encoder/param_head，无重训、无新求解、无再校准）。v2 A1 目录只读。

## 执行状态
- 冻结推理在 n=15307 测试集上完成；预测 mu/sigma 与 v2 存储数组 **逐位一致**（QC q10：
  max|Δmu|=0、max|Δσ|=0）——本轮只改标签、排序与分析口径，未改任何预测。
- 表格/图/npz 全部写入本目录 `outputs/`；QC 18/18 通过（`outputs/qc/a1v3_qc.csv`）。

## 数据检查状态（scaler 拟合来源，实证而非背书）
对冻结 `param_scaler.pkl` 的 `data_min_/data_range_` 与冻结 `dataset_normalized.npz` 三分区
(train 71432 / val 15307 / test 15307) 逐列比对（`outputs/tables/a1v3_scaler_fit_source.csv`）：
**每个参数的 scaler 极值都由某个分区实际达到**，且分布跨 train/val/test 三区：

| param | scaler 低边所在分区 | scaler 高边所在分区 |
|---|---|---|
| mu_n | train | **test** |
| mu_p | val | val+test |
| tau_n | val | train |
| tau_p | **test** | train |
| **Nc** | **test**（≠train） | train+val |
| Nv | train | train |
| tau_ETL / tau_HTL / rad_c | train+val+test（声明盒边界） | … |

Nc 一列即证伪 v2 的 “train scaler 包络”：scaler 低边 log10=22.6665 = **test** 分区最小值
(train 分区最小值 22.7664 显著更高)；规范化后 test 达到 0、train 停在 0.0271（QC q7a/b）。
结论：`MinMaxScaler` 在切分前拟在**完整保留集（102046 行）**上 → **[0,1] 包络 = 全保留集
(含 test) 经验 min/max 包络**，非 train-only。冻结 scaler 未改动。

**结构性后果（本 README 显式声明）**：test 真值全部落在 [0,1]（true_oor_frac=0）是**构造使然**
（scaler 见过了 test），因此 `cov_raw == cov_clip` 严格成立但**不构成**“模型区间不越包络”的独立
证据；它只反映裁剪去掉了没有真值所在的包络外高斯质量。

## 科学判据状态（修正后）
1. **覆盖**（clip==raw，数学必然；median over 9 params）：0.474 / 0.797 / 0.907 / 0.958
   （名义 0.50/0.80/0.90/0.95），模型与 train 分区边缘先验（实测 cov 0.950/0.951/0.954…@0.95）
   都在名义附近——宽度比较是**同名义水平**下进行。
2. **宽度比（model/prior，同名义水平）**：
   - clip 中位比，9 param 中位：0.391 / 0.469 / 0.530 / 0.582（0.50→0.95）；
   - raw 中位比中位：0.391 / 0.470 / 0.536 / 0.603。均值口径同列（`a1v3_model_vs_prior.csv`）。
   - @0.95 逐参数 clip-中位比 = mu_n 0.425、mu_p 0.391、tau_n 0.582、tau_p 0.614、Nc 0.404、
     Nv 0.454、**tau_ETL 0.868、tau_HTL 0.768、rad_c 0.900**。
   - 主结论**维持**：模型区间在每个名义水平都明显窄于先验且覆盖不塌。
3. **soft 参数 @0.95 必须同时给 raw/clip/prior 三数**（否则是误导）：
   | param | raw 中位宽(dec) | clip 中位宽(dec) | prior 宽(dec) | clip/prior | raw/prior | raw 宽度≥整包络比例 | 裁剪率 |
   |---|---|---|---|---|---|---|---|
   | tau_ETL | 3.596 | 3.304 | 3.808 | 0.868 | 0.944 | 0.379 | 0.788 |
   | tau_HTL | 3.146 | 2.930 | 3.816 | 0.768 | 0.824 | 0.160 | 0.675 |
   | rad_c | 2.750 | 2.567 | 2.853 | 0.900 | 0.964 | 0.413 | 0.762 |
   即“soft 窄于先验”只对**裁剪（rectified）区间**成立；对约 16–41% 行的**原始高斯** 95% 区间，
   宽度已达/超过整包络（无包络内分辨力），必须靠裁剪才产生可用区间。且**没有任何参数的 σ 触顶
   1.0**（`a1v3_sigma_clip_stats.csv`：frac_at_ceiling1=0 全部），v2 “σ 常触顶 1.0=整包络宽”的说法
   不成立——大宽度来自 σ 中等偏大（soft 参数 med σ≈0.20–0.23 norm）与窄包络共同作用。
4. **mean vs median**：每个宽度/评分同时给均值与中位数（表列 `*_mean/_med`）；本 README 引用
   处均注明所用统计量，不以中位数单点代替分布。
5. **条件（分组）校准**：仍为 **诊断用**（`diag_only=True`），不作为边际覆盖之外的独立声明。

## 修复清单（相对 v2）
| # | v2 问题 | v3 处置 | 证据 |
|---|---|---|---|
| A1-1 | “[0,1]=train scaler 包络”标签错误 | 实证→“全保留集(含 test)经验 min/max 包络，切分前拟合”；meta/npz/图/注释全部改 | `a1v3_scaler_fit_source.csv`，QC q7a–e |
| A1-2 | 宽度图按 `sort_values("param")`（字母序）对位 PARAM_NAMES 刻度 → **数据错位 9/9** | 显式 `set_index('param').loc[PARAM_NAMES]` 重排 + 输出 x↔label↔data 对照表 | `a1v3_width_fig_correspondence.csv`，QC q8a–c |
| A1-3 | 只报中位宽度 | 宽度/评分同时给 mean & median，声明注明统计量 | 表列 `*_mean/_med` |
| A1-4 | soft 参数“窄于先验”只给 clip 数 | 补 raw 数：raw/prior>clip/prior，且 16–41% raw 区间宽≥整包络；σ 触顶率=0 | 上表 + `a1v3_sigma_clip_stats.csv` |
| A1-5 | “σ 常触顶 1.0”表述（若出现在 A1 文本） | 实测 frac_at_ceiling1=0 | `a1v3_sigma_clip_stats.csv` |
| A1-6 | 条件分组校准口径 | 维持 diag-only | `a1v3_grouped_calibration.csv` |

## 支持结论
- 覆盖：模型区间各名义水平实测覆盖贴近名义（0.474…0.958），未系统性欠覆盖。
- 效率：同名义水平下模型区间中位宽度为先验的 0.39–0.90（逐参数@0.95），soft 参数需读 clip
  口径（raw 高斯对 16–41% 行不具包络内分辨力）。
- scaler 经验范围标签修正为“完整保留集（含 test）”，并把 cov_raw==cov_clip 与 true_oor=0
  重新定性为构造性结果，不再作为独立在包络证据。

## 未解决问题（入 final_review/unresolved_items）
- 冻结 J_scaler 与 param_scaler 均含 test（已知泄漏）：本表覆盖/宽度是**在冻结 test 分布上**的
  描述，不构成外推泛化声明；泄漏已在 round-2 记录，未在此修复（不动冻结 scaler）。
- “soft/好辨识参数”仍为相对标签；对区间宽度的解读依赖模型自身 σ，未作绝对类别划分。
- 分组校准覆盖偏离（若有）只作诊断提示，未在本轮展开其物理解释。
