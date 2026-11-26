# Pre-check 审计报告（Audit A–D）

**日期**：2026-09-07
**范围**：`E:\project\work1` 已冻结主稿/SI/模型的只读核查（不修改任何冻结文件）。
**执行方式**：全部结论基于本机 frozen 数据 + 一次真实 COMSOL LiveLink 求解（server @2039）。
**运行环境**：COMSOL 6.3 + MATLAB R2024b；Python `anaconda3/envs/pytorch-2.60-gpu`。

所有新产物写入 `supplementary_validation/audit/`：
脚本 `auditA_mapping_AB.py`、`auditD_coordinates.py`、`auditC_live_probe.m`；数据 `auditA_sample_mapping.csv`、`auditB_param_metric.csv`、`auditD_sq_summary.csv`、`auditD_declared_box.csv`、`auditD_sq_distributions.png`；运行记录 `_work/*.log|txt` 与 `auditC_log.txt`、`dmodel.xml`（从冻结 .mph 解出的模型 XML）。

---

## 0. 结论总表

| 审计 | 核查对象 | 结论 | 是否物理/数据错误 | 需要的文字修订 |
|---|---|---|---|---|
| **A** | Fig. S3 (c)/(f) “#595” vs Table S8 #595 | **非阵列错位、非版本混用**：c、f 两图共用同一 target 阵列（npz test index 595），f 为同一样品的 true-control 叠图 | 否 | 无需（可加一句注释说明 c/f 共用 #595 是设计，f 为 true-control） |
| **B** | Table S8 “Param log10-RMSE”；Voc 提取 | Param RMSE = **raw log10 空间 RMSE（decades）**，非归一化。存储 Voc = **网格节点值（首 J≤0 格点）**，不是线性插值 | 否（数值本身自洽） | SI §406 措辞；主稿 §2.11 (L145) 措辞；DOC 与 frozen CSV 的提取器不一致需澄清 |
| **C** | 电极位置/命名（Ag、FTO 接线） | 模型里 **Ag(term1,V0=0) 在 x=530 nm（SnO2 背电极侧）、FTO(term2,V_app) 在 x=0 nm（HTL 前侧）**；SI S9.4 文字把两者空间归属**写反** | **命名级，不影响物理**（两接触同为理想欧姆 Richardson，仅 V0/term 号不同；可精确复现 DB） | SI S9.4 (L492) 空间归属需改正 |
| **D** | θ_n=s√q / θ_p=s/√q；a/r 定义；Table S11 指标 | 构造式成立；a=log10 s、r=log10 q 与代码一致；q∈[0.2,5] 线性、s log-均匀；DB-2 几乎 100% 落在 Table 1 声明盒内；DOS 低端因物理筛选缺失 | 否 | “Skill_RMSE”为 MSE-skill（R² 式），非 RMSE 比——措辞建议点明 |

未发现任何需要重算 45 样本聚合值的阵列/版本问题。所有“错误”都落在**文档措辞层**，不进入数值结论。

---

## 1. Audit A —— Sample 映射链（#595 → target → 真值 → 预测 → COMSOL → 图）

### 1.1 问题
SI Fig. S3a 的 (c) 与 (f) 两格都标 “#595”，但被认为 target Jsc 不同；Table S8 里 #595 的 Jsc_t = 3.1697。需判定：图注编号错误 / 阵列错位 / 版本混用，并追全链条。

### 1.2 关键事实（只读重算，脚本 `auditA_mapping_AB.py`）
- **标识符体系**：npz test array 下标（0–15306，test 切分内）≠ DB-2 CSV 行号 ≠ LHS `Sample_ID`（三个体系）。审计用 9 参 17 位精确匹配将三者一一对应。
- **45 样本队列**全部**唯一** 1:1 映射到 DB-2（45/45，`n_db_cand==1`），无歧义。
- **#595**：npz test index **595** ↔ DB-2 **row 60145（0-based）** ↔ LHS **`Sample_ID 117995`**。
  - target Jsc = **3.169725 mA cm⁻²**（= Table S8 行 595 的 3.1697）
  - Voc(网格) = 1.01 V；FF = 0.26104；PCE = 0.83570
  - stored param_log10_rmse = 0.458088（= Table S8 0.4581）
- **Fig. S3a 六格**（`final_figures/scripts/plot_SI_S3_cycle_audit.py` L222 断言）：
  `sid_list == [12058, 4077, 595, 695, 14499, 595]`。
  即 (c) 与 (f) **都是 npz test index 595**；(f) 是脚本 L179 `sid = df.loc[mid,…]` 选取的**中间样品**的 COMSOL-true 对照。
- 因此 (c)/(f) 底下的 target 阵列**逐点相同**（脚本 `np.array_equal` QC 也校验 target/decoder/COMSOL(pred)/COMSOL(true) 与 frozen 阵列一致）；两格视觉不同来自**叠图层不同**：
  - (c)：target + decoder 重建 + COMSOL(pred)（cycle-gap 展示，三条线分离）
  - (f)：target + COMSOL(true)（true-control，按构造与 target 重合）
- **Table S8 行 595 全部复核**：Jsc_t 3.1697 ✓、Voc_t 1.0100 ✓（=网格）、PCE_t 0.8357 ✓、param_rmse 0.4581 ✓；`rmse_full=4.5936`、`rmse_0to1V=0.4553`、`rmse_gt1V=9.5626`、`mean_sigma=0.1358` 为 frozen 记录值。

### 1.3 判定
- **不是阵列错位 / 版本混用**：c、f 共用同一 target（同一 Jsc 3.1697）。两格标同一 “#595” 是**有意设计**（f = 该 cycle 中样品的 true-control），不是编号错。
- 若成图中两格注释的 Jsc 数字不同，那只可能是**渲染/图注注释**问题（例如 f 格把 COMSOL(true) 的 Jsc 也打上去，二者按构造应相等），与底层数据无关。
- **无需修正旧图、无需重算 45 样本聚合**。建议补充一句图注说明“面板 (f) 为面板 (c) 同一样品 (#595) 的真参数对照”。

---

## 2. Audit B —— 指标定义（Param log10-RMSE；Voc 提取）

### 2.1 Param log10-RMSE = raw log10 空间（不是 min-max 归一化）
对 Fig. S3a 六个出现样品逐一重算两种定义并比对 frozen `stored_param_rmse`（`auditB_param_metric.csv`）：

| test_index | raw log10 RMSE | normalized RMSE | stored | equals_raw | equals_norm |
|---|---|---|---|---|---|
| 12058 | 0.716356 | 0.124938 | 0.716356 | **True** | False |
| 4077 | 1.065694 | 0.154440 | 1.065694 | **True** | False |
| 595 | 0.458088 | 0.140807 | 0.458088 | **True** | False |
| 695 | 0.721442 | 0.170966 | 0.721442 | **True** | False |
| 14499 | 1.112783 | 0.238576 | 1.112783 | **True** | False |

- **定义**：`RMSE = sqrt(mean((log10 θ_pred − log10 θ_true)²))`，单位 **decades**（预测与真值都在 raw log10 物理空间，未做任何 min-max 归一）。
- 队列范围 min 0.3889（#8438）… max 1.3591（#269），与“~0.3889–1.3591”一致。
- **SI 文字问题**：`Supplementary_Information_final_v2.md` L406 “param log10-RMSE is the RMSE of the predicted vs. true **normalized** log parameters”——应为 **raw log10（decades）**，去掉 “normalized”。

### 2.2 Voc = 网格节点值，不是线性插值
对 45 个队列样品用两种实现重算 target Voc 并比对 stored `Voc_t`：

| 检查 | 结果 |
|---|---|
| stored Voc_t == 网格节点 Voc（首 J≤0 格点） | **True**（45/45，max 偏差 2e-16 V） |
| stored Voc_t == 线性插值零交叉 | **False**（45/45 都不等） |
| max \|stored − interp\| | **0.0097 V**（即 1 个 0.01 V 步长内） |
| median \|stored − interp\| | **0.0040 V** |
| stored FF/PCE 一致于网格版本 | True（PCE=离散 max(V·J)，与 Voc 提取无关，两版本 PCE 完全相同） |

- 存储的 Voc 全部**恰好落在 0.01 V 网格**上（网格节点法 = 取第一个 J≤0 的格点电压，比真零交叉**偏高 ≤ 1 步**）。
- **代码与文档不一致（可复现性缺口）**：磁盘上的归档提取脚本 `script/forward_validation_postprocess.py` `observables()`（及 `forward_validation_unbiased.py` `device_observables()`）用的是 `np.interp` **线性插值**；但 frozen `forward_metrics_per_sample.csv`（→ SI Table S8）的数值是**网格节点法**。即“声称产出这些数”的脚本版本与 frozen 数值不匹配（CSV 生成于 2026-08-23 12:54，脚本 10:56；数值特征=网格法）。
- **主稿/SI 措辞**：`manuscript_stage1_submission_final_v2.md` §2.11 (L145) 与 `DEVICE_METRIC_EXTRACTION_VERIFICATION.md` 描述线性插值——与 frozen 数值所反映的网格节点法不符。
- **影响评估**：Jsc、PCE 不受影响；Voc 系统偏高 ≤ 9.7 mV；FF 相应偏低 ≤ 0.0054。target 与 sim 用的是**同一种**（网格）约定，故**差值是同一约定下的自洽量**（`dVoc` 中位数 0.030 V 等统计仍是同约定内部的），只是其“绝对值”≠ 线性插值约定下的值。A2 将用单一显式配方（线性插值 Voc + 离散最大功率点）对 target/sim **同时**重提取，量化其对 14/45、rho、设备指标差的影响。

---

## 3. Audit C —— 物理结构：电极在哪一侧？（一次真实 COMSOL 求解）

### 3.1 现场证据（`auditC_live_probe.m`，server @2039，MATLAB `-batch`；记录 `auditC_log.txt`）
**几何顶点 → x（nm）**（`getVertexCoord` 返回，模型长度单位 nm）：

| vertex | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| x (nm) | 0 | 20 | 20.01 | 490 | 490.01 | 510 | **530** |

对应层（SI S9.1）：HTL[0,20] | HTL·PVK 界面[20,20.01] | PVK[20.01,490] | PVK·C60 界面[490,490.01] | C60[490.01,510] | SnO2[510,530]。

**两个金属接触（physics `semi`）**——selection entities 与 V0/Terminal 均由**现场 API**读出：

| feature | 标签 | 选中顶点 | 顶点 x | 物理位置 | Terminal | 类型 | V0 |
|---|---|---|---|---|---|---|---|
| mc1 | **Ag** | {7} | **530 nm** | **SnO2/背电极侧** | 1 | Voltage | **0[V]** |
| mc2 | **FTO** | {1} | **0 nm** | **HTL/前电极侧** | 2 | Voltage | **V_app** |

两接触其余参数完全相同（模型自身 `dmodel.xml` 佐证，即 .mph 内嵌 XML）：`ContactType=ohmic`、`SpecifyUsing=richardsons`、`SpecifyBarrierHeight=ideal`、Φ_B=0.67 V、Φ=4.5 V、vsnin=21605 m/s、vspin=19006 m/s、A*_n=110 A/(K·cm)²、A*_p=90、`ContactResistance=0`。

**工具链验证**：将 `comsol_true_parameters.csv` 行 test_index=269 的真参数（含 rad_c×1e-6 的 cm³→m³ 换算，SI 单位串）赋给 frozen 模型并求解：耗时 15.6 s，J(0)=224.13123 A/m²（=22.4131 mA/cm²，与 DB 一致），与 frozen `Sample_00269_true.mat` 的 **RMSE=1.08e-6、max|Δ|=2.92e-6**（131 点）——用同一工具链精确复现数据库，证明电气配置与 DB 生成一致。

### 3.2 判定
- **模型实际**：接地/扫压的电极分配是 **Ag(0 V) 在 SnO2 侧、FTO(V_app) 在 HTL 侧**，是正常工作的电池取向，并能精确复现 DB。
- **SI S9.4（L492）把空间归属写反**：“‘Ag’ (terminal 1, V0 = 0 V) **at the HTL side**, ‘FTO’ (terminal 2, V0 = V_app) **at the SnO2 side**” —— 与模型相反。
- **性质**：两接触**电学上完全等价**（同为理想欧姆 Richardson，仅 V0/terminal 号不同），所以这是**命名/文字**层面的错位，**不是影响物理的接线错误**，也不会改变任何曲线/指标。
- **修订建议**：把 S9.4 改为 “Ag（terminal 1, V0=0 V）at the SnO2（back/electron）side；FTO（terminal 2, V0=V_app）at the HTL（front）side”（或按模型文字改为与几何一致），或删除空间归属、只保留 terminal/V0 描述。

---

## 4. Audit D —— 坐标构造与坐标级指标

### 4.1 θ_n=s√q / θ_p=s/√q 构造（成立）
- 配对构造（`script/LHS.py`，主稿 Table 1）：对 (μn,μp)、(τn,τp)、(Nc,Nv) 三对：
  θ_n = **s·√q**，θ_p = **s/√q**，其中 s = 共享几何平均（common scale）= √(θ_n θ_p)，q = 电子/空穴不对称比 = θ_n/θ_p。
- log10 下：log10 θ_n = a + r/2，log10 θ_p = a − r/2，其中 **a = log10 s = ½(log10 θ_n + log10 θ_p)**，**r = log10 q = log10 θ_n − log10 θ_p**。`reviewer_experiments/exp3_prior_coordinate_recoverability/scripts/exp3_lib.py::coords_from_log10`（L83–90）与之一致。
- **潜伏量范围/单位**：s（三对 avg）分别 log-均匀 μ_avg∈[1e-6,1e-3] m² V⁻¹ s⁻¹、τ_avg∈[1e-9,1e-2] s、D_avg∈[1e22,1e26] m⁻³；**q 线性**∈[0.2,5]（对应 ±√5 偏离）。Table 1 给出的是**构造后**盒：μ∈[4.5e-7,2.2e-3]、τ∈[4.5e-10,2.2e-2] s、DOS∈[4.5e21,2.2e26] m⁻³（= avg/sqrt5 … avg·sqrt5）。
- 直接采样量：τ_ETL∈[1e-12,1e-8] s、τ_HTL∈[1e-14,1e-10] s、rad_c∈[1e-12,1e-9] cm³ s⁻¹（COMSOL 内 ×1e-6 → m³/s）。

### 4.2 保留库 DB-2 相对声明盒的覆盖（`auditD_declared_box.csv`）
| 量 | 声明盒 | DB-2 min | DB-2 max | 盒内比例 |
|---|---|---|---|---|
| μn / μp | [4.5e-7, 2.2e-3] | 4.56e-7 / 4.52e-7 | 2.23e-3 / 2.11e-3 | ≥0.99998 |
| τn / τp | [4.5e-10, 2.2e-2] | 4.78e-10 / 4.48e-10 | 2.21e-2 / 2.04e-2 | ≥0.99999 |
| Nc / Nv | [4.5e21, 2.2e26] | **4.64e22** / 4.31e22 | 2.23e26 / 2.18e26 | ≥0.99996 |
| τ_ETL | [1e-12,1e-8] | **1.000e-12** | 1.000e-08 | 1.0 |
| τ_HTL | [1e-14,1e-10] | **1.000e-14** | 1.000e-10 | 1.0 |
| rad_c | [1e-12,1e-9] | **1.000e-12** | 1.000e-09 | 1.0 |

- DB-2 几乎 100% 落在 Table 1 声明盒内（仅 ~0.002% 行在**四舍五入后的上界**外一点，如 μn max 2.23e-3 vs 声明 2.2e-3=√5×1e-3 的舍入值）。
- **τ_ETL/τ_HTL/rad_c 精确触到声明下界**（min 恰好 1e-12/1e-14/1e-12），说明筛选未削去极慢界面复合/低辐射区——但这是“触及”声明盒而非越界。
- **物理筛选的保留效应**：Nc/Nv 的有效支撑**低端上移约 10×**（Nc min 4.64e22 vs 声明 4.5e21），即保留集中区整体移向高 DOS；log10 s_DOS 中位 prior 24.00 → DB2 24.97；log10 s_τ 中位 prior −5.50 → DB2 −5.94（偏短寿命）。这些是 51.0% 保留率（finite / Jsc>0 / ΔJ≤0.2 / 0–1.3V 零交叉）对边界的真实收缩，属**已文档化筛选的后果**，不是坐标构造问题。
- **可复现性注意**：本地归档的 200k LHS 文件（`PSC_LHS_9D_interface_lifetimes_200000_3.csv`）与 DB-2 **共享 0 条精确 9 参向量**——即归档文件**不是**生成 DB-2 的那个筛选前抽取（生成抽取未本地归档）。因此上表“prior”分布仅作范围级参考（同范围不同抽取），**无法精确复现 DB-2 的筛选前边际**。此为主稿 L80 “Of the 200,000 simulated curves, 102,046 retained” 的溯源局限，建议在 SI 数据可用性中注明 pre-retention draw 未归档。

### 4.3 Table S11 指标定义（`reviewer_experiments/exp3_prior_coordinate_recoverability/scripts/recoverability.py`）
- 坐标级预测目标：每对坐标的 **a（log10 共享尺度）与 r（log10 电子/空穴比）**；误差单位 decades。
- **Skill_RMSE = 1 − MSE_model / MSE_prior_mean**（prior-only 基线 = **训练子集**每个坐标的均值预测；`rmse_prior_mean²` 即该基线的 MSE）。
  - 注意：它**不是** 1 − RMSE_model/RMSE_prior（RMSE 比）——若按 RMSE 比，数值会更小（如 a_μ：1−RMSE_ratio ≈ 1−√(1−0.856)≈0.62，而表列 0.856）。SI T11 列名 “Skill_RMSE (vs prior-only predictor)” 建议加注“定义为 1 − MSE_model/MSE_prior（R² 式）”。
- **MAE reduction = 1 − MAE_model / MAE_prior_median**（基线 = 训练子集每坐标中位数）。
- prior-only 基线只使用训练子集（train_L=71,432 行），不在测试上重校——与 A1 的“prior baseline from training subset”一致，可复用。

---

## 5. 建议文字修订清单（不触碰 frozen 文件，仅列档）

| # | 位置 | 现状 | 建议 |
|---|---|---|---|
| B1 | `Supplementary_Information_final_v2.md` L406 | “Param log10-RMSE … **normalized** log parameters” | 改为 raw log10（decades），删除 normalized |
| B2 | `manuscript_stage1_submission_final_v2.md` §2.11 L145 | “V_oc … found by **linear interpolation**” | 注明 frozen 数值为**网格节点（首 J≤0 格点）**；若 A2 采用线性插值配方需统一重提取并在文中说明 |
| B3 | `DEVICE_METRIC_EXTRACTION_VERIFICATION.md` | 声称 np.interp 产出 Table S8 | 指出与 frozen 数值（网格法）不符的版本差异；补一条提取器版本澄清 |
| C1 | `Supplementary_Information_final_v2.md` L492 (S9.4) | “Ag … at the HTL side, FTO … at the SnO2 side” | 空间归属与模型相反 → 改为 Ag@SnO2 侧(0 V)、FTO@HTL 侧(V_app)，或仅保留 terminal/V0 描述 |
| A1* | Fig. S3a 图注（建议性） | (c)/(f) 均标 #595 | 加注“(f) = (c) 同一样品的真参数 COMSOL 对照” |
| D1 | SI 数据可用性（建议性） | — | 注明生成 DB-2 的 pre-retention 200k 抽取未本地归档（无法复现筛选前边际） |
| D2 | `Supplementary_Information_final_v2.md` L528/T11.1 | 列名 “Skill_RMSE” | 加注定义为 1 − MSE_model/MSE_prior（R² 式，非 RMSE 比） |

\* A1 编号与任务中的 A1 实验不同，此处表示“Audit A 第 1 条建议”，为避免混淆已在正文用“Audit-A 建议”。

---

## 6. 对 E1 / E2 / A1 / A2 的影响

- **E1**（common-scale vs ratio 可控扫描）：坐标已确证为 (a=log10 s, r=log10 q)，扫点可直接用“等 log10 s 步 / 等训练-SD 步”两套设计；12 个分层样品的定位沿用 Audit-A 的 npz-index ↔ LHS-Sample_ID 链，不用行号。
- **E2**（网格/容差收敛）：Audit-C 证明当前网格+默认容差能复现 DB 到 RMSE~1e-6（数值噪声远小于 E1 响应差），为 E2 提供基线；E2 用同款 COMSOL runner。
- **A1**（区间信息量/校准）：prior-only 基线的“训练子集边际”定义已在 Audit-D §4.3 确认（train_L），可直接用于构造等分区间与分数区间对比。
- **A2**（运行窗回代）：Audit-B §2.2 明确要做的重提取正是 A2 的核心交付——用**单一显式配方**（线性插值 Voc + 离散 MPP）重算 45 样本的 target/sim 指标，检验 dVoc/dFF/dPCE 与 rho=−0.183、p≈0.23、14/45（中位拆分）是否随 Voc 约定改变。
- **COMSOL 流程**：server 在 MATLAB 客户端断开后自动退出——每个 MATLAB `-batch` 前需重启 server（已在 E1/E2 驱动脚本中处理）。

---

## 7. 证据文件索引

| 证据 | 文件 |
|---|---|
| 45 样品映射 + 网格/插值 Voc + param RMSE | `auditA_sample_mapping.csv`；脚本 `auditA_mapping_AB.py`；stdout `_work/auditA_stdout.txt` |
| Param-RMSE 两定义对比 | `auditB_param_metric.csv` |
| FigS3a sid 断言 | `final_figures/scripts/plot_SI_S3_cycle_audit.py`（L179/L222 附近） |
| COMSOL 现场探针（顶点坐标、接触实体、V0/Terminal、269 复现） | `auditC_live_probe.m`；记录 `auditC_log.txt` |
| 模型内嵌接触参数 | `_work/dmodel.xml`（自 `matlab&mph/1D_PSC_wen.mph` 解出）；`_work/probe_props.log` |
| 坐标 s/q 分布 + 声明盒覆盖 | `auditD_sq_summary.csv`、`auditD_declared_box.csv`、`auditD_sq_distributions.png`；`_work/auditD_stdout.txt` |
| Table S11 公式来源 | `reviewer_experiments/exp3_prior_coordinate_recoverability/scripts/recoverability.py` L52–56 |

> 复核提示：本节所有“frozen 主稿/SI 行号”按 `manuscript_stage1_submission_final_v2.md` / `submission_package/Supplementary_Information_final_v2.md` 于 2026-09-07 实测读取；若行号在后续版本漂移，按关键字重定位。
