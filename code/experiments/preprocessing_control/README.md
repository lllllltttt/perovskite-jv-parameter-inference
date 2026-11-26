# v4 T2 · 预处理配对训练对照（train-only scaler）

**状态：已执行且通过（在冻结架构上的单种子配对对照）。**
Protocol：`T2_control/protocol.md`（数据划分/架构/损失/种子/批次序/预算/验证选点/评估规则在分支间固定）。复刻偏差：`T2_control/deviations.md`（D1–D6，均语义等价或已记录）。

## 目的（与 manuscript §2.4 / Data&Code 声明对接）

投稿稿声明：*“both normalization scalers were fitted on all retained samples before the split — a
train-only-scaler re-run moves mean Pearson by ≲0.02 … reproduces the recoverability hierarchy and all
group conclusions exactly”*。T2 用**最小配对控制**直接复检该量级：

- **Branch L（legacy）** = 冻结预处理原规则重训：scaler 拟合于全部 102,046 保留样本（含 test）→ 切分 → 训练。
- **Branch T（train-only）** = scaler 仅拟合于 idx_train（log10 判定 + MinMax 均只在 train 上 fit）；val/test 只做变换。
- L 与 T 的其它一切相同：同一数据划分、同一架构/损失/优化器、**同一种子**（S0=20260823）与**同一固定批次序**、同一 max-budget 1000 epochs、同一验证选点规则（EarlyStopping val_param_loss pat50 restore_best，仅作权重选点）。
- 增量定义：**A = Historical(frozen)→L**；**B = L→T**（B 即 scaler 泄漏效应的单种子净估计）。Historical 冻结检查点仅作参考列，不覆盖。

## 运行

| branch | epochs | best val_param_loss idx | val_param_loss min | wall | artifacts |
|---|---|---|---|---|---|
| L | 1000（预算满；val 持续改善至 idx988，未触发早停） | 988 | −15.2741 | 1532.7 s (1.53 s/ep) | `runs/L_seed20260823/{encoder,decoder,param_head}.keras` + history/meta/scaler_meta |
| T | 1000（同上，idx977） | 977 | — | 1548.1 s (1.55 s/ep) | `runs/T_seed20260823/…` |

冻结参考（v3 只读）：688 epochs、val_loss argmin≈637（history.pkl）。L/T 属本 protocol 的确定性子种子运行；与冻结相比叠加 D1–D5 与固定种子随机性，A 不解读为逐位复现。

## 评估（`scripts/t2_eval.py`，只读）

- 在**物理 log10 参数空间 / J 以 mA·cm⁻²** 上比较（协议 §5）；σ_ref 保持 m=1 定义。
- Interval 主口径 **RAW**（sig_norm·prange）；先验 = **train-empirical log10 高斯**（L/T 共用）。
- Scalers 为 sklearn 对象（Historical/L = 冻结 pkl；T = train-only refit，确定性，与 t2_train 相同）。
- 输出 `tables/preprocessing_control_metrics.csv`（40 行：H/L/T + Prior 各 9 参数 + POOLED9）、`tables/J_recon_summary.csv`、`tables/control_per_sample.csv`（15307 行）。

## 结果（test 15307）

| 量（9 参均值，log10） | Historical | L | T | A(L−H) | **B(T−L)** |
|---|---|---|---|---|---|
| mean Pearson | **0.8069** | 0.8052 | 0.8014 | −0.0017 | **−0.0038** |
| mean cov@95% | 0.9574 | 0.9571 | 0.9580 | −0.0003 | +0.0009 |
| MAE | 0.4836 | 0.4868 | 0.4928 | +0.003 | +0.006 |
| RMSE | 0.6389 | 0.6448 | 0.6513 | +0.006 | +0.007 |
| pooled RMSE | 0.7001 | 0.7042 | 0.7121 | +0.004 | +0.008 |

- **分级/群序**：三模型均维持 bulk(mu/tau/DOS 0.87–0.92) > τ_HTL(0.71–0.72) > τ_ETL(0.59–0.61) > rad_c(0.56–0.57)；per-param |Δ|≤0.019，最大单参漂移 tau_ETL(T−L −0.019)。
- **校准**：cov95 各参区间 H 0.9464–0.9692 / L 0.9451–0.9701 / T 0.9480–0.9710 —— 名义水平附近，train-only 不显著改变校准。
- **J recon**（decoder，mA·cm⁻² 行 RMSE 中位）：full 1.66/1.76/1.55；0–1.0 V 0.067/0.065/0.056；>1 V 3.46/3.68/3.23；gen0 0.219/0.227/0.187。
- Prior(train-empirical) pooled RMSE 1.268 → 模型远优于先验，宽度收窄保留。

## 对投稿声明的检验（同步进 submission_candidate，见 claim_sync_matrix）

- **B |ΔmeanPear| = 0.004 ≤ 0.02** → 投稿“≲0.02”量级**成立**（并更小）；已在候选副本 Data&Code/(ii) 与 §2.4 补实测值 0.805→0.801（Δ≈0.004）。
- 分级与群结论、近似校准在 L 与 T 间**均复现** → 该选择不改变任何定性结论（覆盖/宽度仍为固定 test 分布描述，见 §3.2 Boundary）。
- 无预设结论、无 test 真值裁剪、未反向扩 train scaler、未因 test 差改 σ bounds/loss/epochs；全部按 protocol。

**遗留/边界**：单种子（S0）单次；未做多种子。冻结架构 L 已接近 Historical（meanPear −0.0017），说明本机复刻 + 固定种子在该精度下可复现冻结行为量级。
