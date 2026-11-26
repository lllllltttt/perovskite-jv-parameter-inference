# v4 · T2 配对训练对照 protocol（先于一切 T2 训练锁定）

- 依据：v4 规范 §四（T2）。目的：量化「数据驱动预处理在切分前用全量(含 test)拟合」这一构造性来源
  （T0 P1/P2）对模型性能/不确定性的影响。**一个预定的配对训练**：同一网络/损失/种子/批次序，
  仅预处理不同。冻结历史 checkpoint 只作参照列，不覆盖、不重训。
- 本 protocol 先行锁定后，任何实现不得因 test 表现改任何一行下列条目；偏差只允许**记录并说明**。

## 0. 总边界
- 0 次新增 COMSOL 求解；0 次新 DB 生成；无真实器件实验；无超参搜索；无数据切分/样本过滤改动
  （train/val/test = 冻结 70/15/15，random_state=42，见 `v4/source_inventory`）。
- 冻结历史 vae-v6（encoder/decoder/param_head .h5、scaler pkl、npz）全部只读。
- 产出目录：`v4/T2_control/`（runs/L_seed<S>、runs/T_seed<S>、tables、figures 可选）。

## 1. 两分支与第三列
| 列 | 预处理（数据驱动部分） | 网络/损失/优化 | 训练数据 | 说明 |
|---|---|---|---|---|
| Historical (冻结，**参照列，不重训**) | 全量(含test) scaler（npz/pkl） | 冻结 .h5 | — | 仅推理 test，列在比较表里作 A 的端点 |
| Branch L = legacy | **原冻结规则逐字复刻**：log10 全参数+MinMax 拟合于**切分前全量**（含 val+test）；训练即在 npz 缩放数组上 | 与冻结相同（复刻 VAE-v6.py） | npz 的 J_train/params_train | 重训（种子固定，见 §4）；批次序与冻结历史不同（历史无 seed，不可逐位复现）→ 记录 |
| Branch T = train-only | **所有数据驱动预处理只 fit train**：log10 掩码与 MinMax 的 data_min/max 均取自 idx_train 子集；val/test 仅 transform | 与冻结相同 | train-only 缩放的 J/params | 与 L 同一 S0、同一 init、同一批次序，仅预处理不同 |

- 比较结构（严格区分两个增量）：
  - **A: Historical → L** = 冻结 checkpoint 与「按原始(泄漏)规则、种子固定的重训」之差 = 复现/重训差
    （含历史批次序不可复现导致的随机性；不解读为逐位一致或“重训失败”）。
  - **B: L → T** = 只把预处理改为 train-only 的差 = **本 control 的目标量**（在同一 init/批次序下，
    因果可归于预处理）。
  - 报告 A、B 分开；不预设 B 方向/大小。

## 2. 网络 / 损失 / 优化 / 训练（逐字复刻 VAE-v6.py，语义优先）
- 架构：enc `J(131) → Dense128 relu → Dense64 relu → z9(+z_log_var)`；dec `9 → 64/128 relu → 131 sigmoid`；
  param head `9 → 64 relu → 32 relu → [mu9, sigma_raw9]`；σ=clip(softplus(sigma_raw)+0.01, 0.01, 1)（norm 空间）。
- 损失 = MSE_recon + 0.001·KL + 1.0·GaussianNLL(9 参数，sum)；负号/符号以 VAE-v6.py 为准。
- 优化器 Adam lr 1e-3；batch 64；epochs ≤ 1000（与冻结一致，不因 test 提前/延后）。
- 回调（复刻）：EarlyStopping(monitor='val_param_loss', patience=50, restore_best_weights=True)、
  ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=15, min_lr=1e-6)、
  ModelCheckpoint(best.weights.h5, monitor='val_loss')。
- **验证 checkpoint 规则（预先固定，唯一）**：正式指标取自 early-stop 恢复权重
  （= val_param_loss 最优历元后的恢复态），与冻结 .h5 的保存语义一致（冻结 .h5 为训练结束保存态，
  早停恢复后）。test **绝不**参与任何选择。
- 若 Keras 3 / TF 2.21 与冻结脚本原始 Keras 2 语义有差异（API 级），做**语义等价的适配**并在
  `runs/*/deviations.md` 逐条记录；不改超参/结构。

## 3. 数据与预处理（Branch L / T 具体化）
输入：`_data_physical.npz`（T0 产物：Sample_ID/params_phys/params_log/J_phys/idx_train,val,test/log_mask）
与冻结 `dataset_normalized.npz`、两个 scaler pkl。
- **Branch L**：训练/验证直接取冻结 npz 的 J_train/params_train/J_val/params_val（= 全量 scaler 变换后）。
  test 缩放用于推理（与冻结相同坐标）。
- **Branch T**：
  1. params：对 params_phys[idx_train] 逐列，凡 `min>0 且 max/min>100` 取 log10（掩码判定**只用 train**），
     再 MinMax 拟合 train；val/test 用同一 log_mask+scaler transform。
  2. J：对 J_phys[idx_train]（单位 mA/cm²）MinMax 拟合 train（逐列 131）；val/test transform-only。
  3. 推理时把 test 的 mu/sigma/重建 J 用**本分支 scaler 逆变换**回物理 log10 参数与 mA/cm² J。
- 不裁剪 test 真值；不用 test 统计反扩 train scaler；不改 σ 界/损失/epochs 以迁就 test。
- **共同 prior（L/T 共用，来源注明）**：train-empirical 逐参数 log10 高斯，均/标准差取自
  params_log[idx_train]（物理 log10），作为区间比较的“prior 列”与性能参照（prior-mean 基线误差）。
  [0,1] 全数据包络**不是合法物理界**，不作 bound；如需提及 test 落入包络比例仅作描述。
- clip 规则单独报告：σ_norm ∈ [0.01,1]（两分支同，但各自 norm 空间）→ 物理 log10 σ = σ_norm·R_branch
  （R_branch = 该分支 fit scaler 的 log10 范围 = max−min over log10 train 或 full）。此差异是**性质**不是 bug，报告。

## 4. 随机性控制（"一对种子"）
- 种子 `S0 = 20260823`（沿用前向对照种子，单一种子对 L 与 T 共用）。
- 数据顺序：两份分支**共用同一固定全局置换**（np.random.default_rng(S0).permutation(len_train) 生成
  顺序后固定），按 batch 64 切；**不再 shuffle**（确定性）。记录：此为相对历史的**必要偏差**
  （历史无 seed shuffle 不可复现），使 L↔T 仅差预处理。
- 初始权重：构建模型前 `tf.random.set_seed(S0)`、`np.random.seed(S0)`，两分支 init 相同。
- 只跑这一对；**不自动多种子**。报告中注明单种子对的限定与“如需第二对以量化随机性可另跑”。

## 5. 评估（test，物理空间；与 §6 度量清单一致）
推理 = 官方约定：z_mean = encoder(J_norm)；param mu/sigma = head(z_mean)；重建 J = decoder(z_mean)。
- **主度量轴**：物理 log10 参数（decades）与 mA/cm² J；预测 μ、区间端点=μ±z·σ_phys_log10，
  σ_phys_log10 = σ_norm·R_branch（min 裁到 clip 下限对应物理值，记录）。
- 逐参数 p：Pearson r(真,μ)、log10 MAE、log10 RMSE；50/80/90/95% 名义层覆盖（raw 区间，
  端点用每样本 σ）；区间宽度 mean/median（decades）；每层平均区间分（Gneiting–Raftery，式同 A1）；
  |真−μ| 与 σ 的 Spearman（σ 是否随误差排序）；prior-mean 基线同表列出（性能 vs 共同 prior）。
- J：整条曲线与 ≤1V/>1V/[0,Voc_test] 窗的 RMSE/MAE（mA/cm²）；重建峰值区域误差。
- recovery ranking：test 内 逐参数 Spearman rho（μ vs 真，排序恢复）＋ 预测前 10% 命中率（可选项，
  若做须写明定义）。
- 输出：`runs/L_seed20260823/metrics_test.csv`、同 T、`tables/preprocessing_control_metrics.csv`
  （A/B 增量列）与逐样本长表 `tables/control_per_sample.csv`（挂 test_index+Sample_ID）。
- 覆盖/区间**主用 raw 物理 log10**；如列 [0,1] 缩放空间的覆盖须标注“描述性”。

## 6. 报告约定
- 状态词：已执行且通过 / 已执行发现限制 / 未执行 / 文件或环境阻断 / 待作者选择表述（按 v4 词汇）。
- 报告里 A、B 分行；若 B≈0 不写“无泄漏影响”，写“在该单种子对、该度量下未检出 B”。
- 训练日志、history.json、权重与 scaler 均入 runs/；冻结文件零改动。

## 7. 环境与偏差记录
TF 2.21.0 / Keras 3.14.1 / CPU（本机无 GPU；oneDNN on）。记录实际 epochs、最优历元、耗时；
若与冻结 history（688 epochs，val_param_loss argmin≈637）在正常范围内则列“复刻一致”，
软件栈差异记入 deviations。
