# T1-A（v4 §三）E2 网格收敛 + 冻结反演相邻偏移链 —— 纯后处理复核

任务区：`supplementary_validation_v4/T1A_E2/`。**本轮 0 次新增 COMSOL 求解；冻结文件与
v1–v3 任何输出均未改动。** 全部输入只读，全部新产物在本目录 `outputs/tables/` 与 `scripts/`。

复跑：`python scripts/t1a_forward_fixedref.py`（A 块），`python scripts/t1a_inverse_adjacent.py`（B 块）。
python = `D:\PythonProject\.venv\Scripts\python.exe`。运行输出已追加 `run.log`。

---

## 1. 输入（全部只读）

| 用途 | 路径 |
|---|---|
| m=1 真实参考曲线（物理 mA/cm²） | `E:\project\work1\data\dataset_normalized.npz` → `J_test_raw[test_index]`；test_index = {3741, 5808, 7693, 8874, 14179, 14912}（npz 测试集行号 = DB CSV 行序 = split 后 test 索引） |
| v3 细档 m0.18/m0.125 曲线（A/m²，×0.1→mA/cm²） | `E:\project\work1\supplementary_validation_v3\E2_finemesh\outputs\curves\row_00200..00211.csv`（清单 `...\inputs\e2v3_finemesh_manifest.csv`） |
| v2 归档细档 m0.35/m0.25 曲线 | `E:\project\work1\supplementary_validation_v2\E2_mesh_and_inference\outputs\curves\row_00100..00117.csv`（按首行 `# rowid=.. test_index=.. level=..` 匹配） |
| 冻结分析脚本（口径必读） | `E:\project\work1\supplementary_validation_v3\E2_finemesh\scripts\e2v3_mesh_convergence.py` |
| 冻结基线（重算对照） | `...\E2_finemesh\outputs\tables\e2v3_finemesh_convergence_verdict.csv`、`e2v3_finemesh_adjacent_delta.csv`、`e2v3_finemesh_inverse_adjacent.csv` |
| 冻结反演记录 | `E:\project\work1\supplementary_validation_v3\E2_inverse_repair\outputs\tables\e2v3_config.json`、`e2v3_inverse_perrow.csv`（78 行）、`e2v3_inverse_mesh_sensitivity.csv`（432 行）、`e2v3_fine_chain_perparam.csv`（9 行）及该目录 `README.md` |
| 共享库（未改写） | `E:\project\work1\supplementary_validation_v3\_tools\v2lib.py`（V=linspace(0,1.3,131)、AM2=0.1、device_metrics、window_masks、rmse_windows） |

---

## 2. 方法

### A. 前向三窗固定参考重算

- **相邻档对**：m0.35→m0.25、m0.25→m0.18、m0.18→m0.125（同参数、同 stol=1e-6，仅网格不同；不混参考类型）。
- **device 差**（网格自身指标，`voc_mode='interp'`）：
  `dVoc_mV=(Voc_f−Voc_c)·1000`；`dJsc_pct=|Jsc_f−Jsc_c|/|Jsc_c|·100`；`dPmax_pct=|Pmax_f−Pmax_c|/|Pmax_c|·100`。
- **曲线段 RMSE（相邻两曲线，mA/cm²）**：`rmse_win = sqrt(mean_{win}((J_c−J_f)²))`。
- **>1 V 相对误差分母（脚本原定义）**：`denom_gt1 = mean_{V>1}|(J_c+J_f)/2|`，`rel_gt1_pct = rmse_gt1/denom_gt1·100`——这是**整段聚合相对残差**，不是逐点 <1%。
- **固定参考掩码（T1A 修复口径）**：每代表用 m=1 真实曲线的 `voc_ref/vmp_ref`（`device_metrics(J_test_raw, 'interp')`）
  生成 `window_masks(voc_ref, vmp_ref, mpp_half=0.05)`：le1 = V≤1；gen0 = V≤voc_ref；gt1 = V>1；
  gtvoc = V>voc_ref；mpp = |V−vmp_ref|≤0.05；full = 全部 131 点。所有档对/档级共用同一掩码，
  而不是各网格自己的 Voc/Vmp。
- 判据（与冻结脚本 CR 常量一致）：dVoc≤2 mV、dJsc≤0.05%、dPmax≤0.1%、le1 RMSE≤0.1（tight≤0.05）、
  >1 V 相对 max≤1%（名义）。

### B. 冻结反演相邻偏移链

- 9 参数顺序沿用 v2lib `PARAM_NAMES` = mu_n, mu_p, tau_n, tau_p, Nc, Nv, tau_ETL, tau_HTL, rad_c。
- `σ_ref(t,p)` = 代表 t 的 **m=1 冻结参考曲线** 在参数 p 上的预测 σ（norm 空间，perrow `sig_<p>` 的 ref 行）。
- 每个 (代表,档,参数) 的 `z_ref = (μ_norm(档)−μ_norm(ref))/σ_ref`（ref 自身 z_ref≡0）。
  从 `e2v3_inverse_perrow.csv` 独立重建；与 `e2v3_inverse_mesh_sensitivity.csv` 的 432 格 z_ref 交叉核对
  max|diff|=3.6e-15（位一致）。
- 相邻链 `ref→m0.35 → m0.25 → m0.18 → m0.125`，`Δz_ref(相邻) = z_ref(f)−z_ref(c) = dμ_norm/σ_ref`；
  每对 54 格 = 6 代表 × 9 参数。**"最大偏移"一律指跨 54 格（或每参数×6 代表）的最大值，不是单一样本点。**
- 细链每参数最大 `|z_ref|`（24 格 = 6 代表 × 4 细档，vs m=1 ref）与 `e2v3_fine_chain_perparam.csv` 对照。

---

## 3. 数字结论

### A1. 冻结 verdict 重现（自检基线）—— 三对全 PASS

`outputs/tables/t1a_baseline_verdict_repro.csv` 逐项与 `e2v3_finemesh_convergence_verdict.csv` 比对
（容差 1e-9），`ALL_PASS=True` 于三档对；判据 PASS/FAIL 与冻结完全一致。

| 档对 | max\|dVoc\| mV | max\|dJsc\| % | max\|dPmax\| % | max ≤1V RMSE mA/cm² | >1V 相对中位/最大 % | 生成窗判据 |
|---|---|---|---|---|---|---|
| m0.35→m0.25 | 0.629156 | 0.00261 | 0.00443 | 0.001956 | 2.247 / 2.503 | 过（>1V≤1% 否） |
| m0.25→m0.18 | 0.394972 | 0.00155 | 0.00308 | 0.001548 | 1.435 / 1.591 | 过（>1V≤1% 否） |
| m0.18→m0.125 | 0.218829 | 0.00104 | 0.002088 | 0.000989 | 0.786 / 0.866 | 过；>1V 相对 **≤1%（是）** |

（>1 V 绝对 RMSE 最后档：中位 0.4738、最大 2.9139 mA/cm²；绝对 tight 收敛**未**建立——如实保留。）

### A2. 固定参考掩码重算

`outputs/tables/t1a_window_rmse_fixedref.csv`（行=代表×档对），`t1a_device_delta_fixedref.csv`（device 差表）。

- 5/6 代表的 voc_ref>1（3741=1.0415、7693=1.0145、8874=1.1501、14179=1.1417、14912=1.1914；仅 5808=0.9902<1）。
  因此对高 voc_ref 代表，**固定 gen0 窗延伸到 >1 V 的近 Voc 区**，其相邻 RMSE 明显大于 ≤1 V 窗 RMSE。
- 最后档（m0.18→m0.125）gen0 窗 max = **0.002550 mA/cm²**（代表 14912）——见 §4 R3。
- mpp 窗相邻 RMSE 全部 ≤6.4e-4 mA/cm²；gtvoc 窗即读尾，量级与 gt1 相近或更大。

### B. 反演相邻链 —— 全部命中冻结值

`outputs/tables/t1a_inverse_chain_summary.csv`（每对 54 格，n_cells=54，全部有效）：

| 档对 | max\|Δz_ref\| | 中位\|Δz_ref\| | >0.1σ / 54 | 与冻结 |
|---|---|---|---|---|
| ref(m=1)→m0.35 | 0.643453 | 0.103569 | **28** | 一致 |
| m0.35→m0.25 | 0.062024 | 0.006517 | 0 | 一致 |
| m0.25→m0.18 | 0.039252 | 0.004985 | 0 | 一致 |
| m0.18→m0.125 | 0.020972 | 0.002854 | 0 | 一致 |

**0.062→0.039→0.021σ_ref 单调递减、细-细每级 0/54 >0.1σ 完全复现**；全部“网格敏感”集中在单一
ref→m0.35 粗-细第一步（28/54，max 0.643σ_ref）。细链内收敛；相对 m=1 粗参考的 0.3–0.7σ_ref 偏移是
**粗参考偏移**，不是细网格持续不收敛（语义沿用 v3 并入段，未改写）。

每参数×相邻对 的 max|Δz_ref|：`outputs/tables/t1a_inverse_adjacent_recompute.csv`（36 行；每格 6 代表有效）。
每参数细链 max|z_ref|（24 格）：`outputs/tables/t1a_inverse_perparam_recompute.csv`，与
`e2v3_fine_chain_perparam.csv` 逐参数一致（abs_diff≤1e-15）：rad_c 0.765701、mu_p 0.608927、
mu_n 0.505551、tau_HTL 0.471000、Nv 0.454910、tau_ETL 0.403681、Nc 0.344863、tau_n 0.327019、tau_p 0.307764。

---

## 4. 量值核对表（逐行结论）

`outputs/tables/t1a_magnitude_trace.csv`；六项参考量全部按“最贴切定义”命中：

| 参考量 | 规格值 | 最贴切定义（档对,窗/统计） | 重算值 | 命中 |
|---|---|---|---|---|
| R1 max\|ΔVoc\| | ≈0.219 mV | m0.18→m0.125，6 代表 max（自网格指标） | 0.218829 mV | 命中 |
| R2 max\|ΔPmax\| | ≈0.0021% | m0.18→m0.125，6 代表 max（相对 Pmax） | 0.002088% | 命中 |
| R3 固定产生窗 max RMSE | ≈0.00255 mA/cm² | **m0.18→m0.125 × gen0 固定窗（V≤voc_ref），6 代表 max = 代表 14912** | 0.002550 mA/cm² | 命中 |
| R4a >1V 相对中位 | ≈0.786% | m0.18→m0.125，中位；分母=mean_{V>1}\|(Ja+Jb)/2\| | 0.786229% | 命中 |
| R4b >1V 相对最大 | ≈0.866% | 同定义，最大（代表 5808） | 0.866205% | 命中 |
| R5a >1V 绝对 RMSE 中位 | ≈0.474 mA/cm² | m0.18→m0.125，中位 | 0.473823 mA/cm² | 命中 |
| R5b >1V 绝对 RMSE 最大 | ≈2.914 mA/cm² | m0.18→m0.125，最大（代表 7693） | 2.913862 mA/cm² | 命中 |

**R3 备注（表述来源）**：同一“gen0 窗 RMSE”在其它定义下**不**等于 0.00255——
m0.35→m0.25 gen0 max = 0.00741（代表 14912）、全档对 full 窗 max = 4.05、全档对 le1 窗 max = 0.001956、
各档级对 m=1 真实曲线 gen0 窗 max = 0.123（模型-真实差异，量级完全不同）。因此 R3 的 0.00255 只有在
“**最细档对 m0.18→m0.125、固定 gen0 窗（V≤voc_ref）、跨代表 max**”这一读法下成立（落在代表 14912）；
若原文想表达 ≤1 V 窗或 vs 真实曲线，则应为 0.001956 或 0.123。已如实标注。

---

## 5. 与旧口径的差异

- **e2v3_mesh_convergence.py 旧口径**只对相邻档对用了 V≤1 / V>1 两个**固定电压**窗 + 网格自身 device 差，
  没有 gen0/gtvoc/mpp 窗，也没有用 m=1 voc_ref/vmp_ref 做掩码。T1A 固定参考重算新增了这些窗；
  gen0 固定窗对 voc_ref>1 的代表会纳入 >1 V 的近 Voc 点，因而相邻 RMSE 比 ≤1 V 窗大（R3 即此现象）。
- device 相对误差（dJsc%、dPmax%）与**窗内 RMSE 相对误差**（>1 V 相对残差）是两回事：前者是器件指标
  的相邻相对差（≤0.005% 量级），后者是 >1 V 段残差对段内平均幅度的比值（0.8–2.5% 量级），报告中分列。
- 反演：冻结表 `e2v3_fine_chain_perparam.csv` 的 per-param max|z_ref| 是 **24 格跨样本/网格最大**；
  T1A 保留同一口径并在 README 明示，不写成单点值。细链相邻偏移是 **coarse→fine 累积链式偏移**的逐级
  差分（0.062→0.039→0.021），**不是**“从 m=1 一步到达细解”；m=1→m0.35 的 0.64σ_ref 一步才是粗-细主跳。

---

## 6. 表述纪律（落地到本任务所有表/README）

1. **>1 V 相对误差是整段归一化统计**：`rmse_gt1 / mean_{V>1}|(J_c+J_f)/2|`，绝不写成“每点 <1%”。
2. >1 V 绝对 RMSE 单位 mA/cm²（中位 0.474 / 最大 2.914，最后档）。
3. device 相对误差与 window 相对误差分开表述（见 §5）。
4. 每参数最大偏移都注明“**跨样本/网格最大值**”（24 格或 54 格/6 代表），不指单一样本。
5. coarse→fine 链式偏移不表述为“一步同时到达”。
6. **细链稳定 ≠ 细网格上的反演准确/覆盖**：v3 已记录“>0.1σ 判据依赖模型自身 σ 宽窄”、反演主要经
   >Voc/>1 V 尾随读取等限制；本任务不改写这些结论。

---

## 7. 未决项

- R3“固定产生窗最大 RMSE≈0.00255”的口径依赖“最细档对 × gen0 固定窗”的读法才成立；若源头指 ≤1 V 窗
  或“对 m=1 真实曲线”，则对应 0.001956 / 0.123 mA/cm²，需在引用时澄清（见 §4）。
- 固定 gen0 窗对 voc_ref>1 的 5/6 代表覆盖到 >1 V 近 Voc 区，该区绝对收敛未完全建立（v3 已记录），
  gen0 窗 RMSE 因而比 ≤1 V 窗大；这是口径事实，不是新发现的网格失败。
- 6 代表仅为 E2 冻结子集，未扩到全测试集（v3 已声明代表性有限）。
- 反演每格 σ_ref 语义 = m=1 冻结参考的预测 σ；“0.1σ”判据对宽 σ 参数更不易触发（v3 未决项，未在本轮重开）。

---

## 8. 交付文件

`scripts/t1a_forward_fixedref.py`、`scripts/t1a_inverse_adjacent.py`（可复跑，只读输入）；
`outputs/tables/`：
`t1a_baseline_adjacent_delta.csv`、`t1a_baseline_pair_aggregates.csv`、`t1a_baseline_verdict_repro.csv`、
`t1a_window_rmse_fixedref.csv`、`t1a_device_delta_fixedref.csv`、`t1a_gen0_vs_true.csv`、
`t1a_magnitude_trace.csv`、`t1a_inverse_adjacent_recompute.csv`、`t1a_inverse_chain_summary.csv`、
`t1a_inverse_perparam_recompute.csv`；`run.log`。

**声明：本轮 0 次新增 COMSOL 求解；冻结文件与 v1–v3 输出未改。**
