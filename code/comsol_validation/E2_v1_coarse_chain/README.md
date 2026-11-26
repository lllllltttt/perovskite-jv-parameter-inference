# E2 — 网格 × 容差收敛（状态：**已运行**）

**日期**：2026-09-07 · **目录**：`supplementary_validation/E2/`
**冻结模型**：`matlab&mph/1D_PSC_wen.mph`（只读）。**求解**：COMSOL 6.3 + MATLAB R2024b，
4 路 server（2041–2044）；48 行分 4 chunk 并行，每行重建 mesh 后 `model.sol('sol1').runAll`
（先 `s1.stol` 重设），输出 0–1.3 V / 131 点 J–V。**脚本**：`e2_design.py`、`e2_comsol_batch.m`
（worker）、`run_e2.sh`（launcher）、`e2_analyze.py`（结果）、`e2_smoke.m`/`e2_probe.m`（路径验证）。

**目的**：对 E1/前向实验用的数值配置做量化收敛检验：固定模型参数，扫
**网格单元尺寸因子 m ∈ {0.50, 0.71, 1.00, 1.41, 2.00}**（把 mesh1 两个 Size 特性的 hmax/hmin
同乘 m 后重建；m=1 即冻结默认 112 单元）与
**稳态相对容差 stol ∈ {1e-4, 1e-5, 1e-7}**（冻结为 1e-6），报告单元数/耗时与
**相对冻结配置（m=1, stol=1e-6, runAll）的数值误差**，并比较其与 E1 前向响应差的量级。
6 组样本 = E1 cohort 内 6 个代表（g1 中位 PCE=5808、g2 高迁移率=3741、g3 低迁移率=14912、
g4 长寿命=7693、g5 非对称寿命=8874、g6 高复合=14179）；每样本 8 行 = ref(1) + mesh(4) + tol(3)。

---

## 1. 质量与复现

* 48/48 行成功（`e2_failures` 空）；每行 `nelem`/`nvtx` 由 `mphmeshstats` 实测写入。
* 单元数随 m 单调：m 0.50/0.71/1.00/1.41/2.00 → nelem 195/146/**112**/87/68（nvtx=7 恒）。
* **runAll 与 study.run 同路径 QC**：对样本 5808 同时用 `sol1.runAll` 与 `study('std1').run`
  求解同一参数，两曲线与 E1 归档基线三者一致到 **≤1e-7 mA/cm²**（QC 表
  `e2_qc_runall_vs_studyrun.csv`；输出舍入显示 0.0）。→ E2 的 runAll 路线与 E1/归档完全等价。
* 网格基值由 `getDouble` 从模型实测（6.89/1.06、3.55/0.53 nm 量级；`feat.get('hmax')` 在
  LiveLink 6.3 会抛异常，见 `e2_probe.m`，已用 `getDouble` 修正并单行 smoke 验证）。

## 2. 结果 A — 容差收敛（stol 1e-4…1e-7，固定 m=1）

全窗/各窗曲线误差（相对 stol=1e-6 的 ref）在全部 6 组上 **≤ 2.3e-5 mA/cm²**；设备指标差
dPmax ≤ 1e-4%、dVoc < 1e-3 mV。→ 冻结 stol=1e-6 完全收敛；即便放到 1e-4 指标也无差别。
数值误差(容差腿)比 E1 任意响应通道小 4–7 个量级。

## 3. 结果 B — 网格收敛（m 0.50–2.00，即 195→68 单元跨冻结 112）

| test_index | 组 | ref Pmax (mW/cm²) | m0.50 gen-rmse | m2.00 gen-rmse | 全窗 rmse@m2.00 | dJsc% @m2.00 | dVoc(mV) @m2.00 | dPmax% @m2.00 |
|---|---|---|---|---|---|---|---|---|
| 3741 | g2 高迁移率 | 19.21 | 0.047 | 0.190 | 219.1 | 0.0022 | −2.75 | −0.101 |
| 5808 | g1 中位 PCE | 16.19 | 0.009 | 0.040 | 59.1 | 0.0278 | −1.84 | +0.028 |
| 14912 | g3 低迁移率 | 18.47 | 0.093 | 0.443 | 5.4 | 0.0048 | −17.0 | −0.003 |
| 7693 | g4 长寿命 | 16.73 | 0.029 | 0.121 | 209.6 | 0.0071 | −2.49 | −0.040 |
| 8874 | g5 非对称寿命 | 6.21 | 0.004 | 0.016 | 0.98 | −0.076 | −5.01 | −0.157 |
| 14179 | g6 高复合 | 11.02 | 0.004 | 0.015 | 1.70 | −0.029 | −2.07 | −0.095 |

（`gen-rmse` = 0→Voc_ref 窗口逐点 RMSE，mA/cm²；全表见 `e2_windowed_rmse.csv`、
`e2_mesh_levels.csv`。）

* **设备指标对网格稳定**：全网格范围 |dJsc| ≤ 0.08%、|dPmax| ≤ 0.16%、|dVoc| ≤ ~3 mV
  （唯一例外：g3 低迁移率样本 14912 在**最粗** m=2.00 时 dVoc −17 mV）。
* **发电窗/0–1V 内数值误差小**：各样本 gen-window 网格误差 ≤ 0.19 mA/cm²（中位 ≤0.05），
  0–1V ≤ 0.09 mA/cm² → 相对 E1 主要响应通道（a_mu/a_tau/a_D 的 gen-window 响应每 decade
  2.7–4.8 mA/cm²）小 ~25× 以上。
* **全窗(0–1.3V)绝对 RMSE 大但被 >1V 陡区主导**：rmse@m2.00 可达 59–219 mA/cm²，但
  逐点拆分显示 >1V 窗口贡献了几乎全部（m2.00 时 >1V rmse 123–458 mA/cm²；1V 以下 ≤0.09）。
  原因：高偏压区 |J| 达数百 mA/cm²，最粗网格对该大电流的高场抽取有 ~1% 的相对扰动 → 绝对
  差大；这不进入任何设备指标，也不进入 E1/A2 用的 0–1V/gen 窗口结论。

## 4. 对 E1 响应差的意义（“数值误差 ≪ E1 响应差”的量化）

* 容差腿：≤2e-5 mA/cm² ≪ E1 最小响应通道。
* 网格腿（在论文/本工作使用的指标与 0–1V/gen 窗口口径下）：≤ ~0.2 mA/cm²，比 E1 最强
  响应（gen-window ~2.7–4.8 mA/cm²/dec）小一个量级以上 → E1 的 a-vs-r 排序在数值上是稳健的。
* **边界（如实报告）**：(i) 若把比较窗放宽到 >1V 高偏压区，冻结 112 单元网格的**绝对电流**
  尚未网格收敛到 ~1%，该区全窗 RMSE 不能作为收敛判据——这与 A2 “>1V 窗信息量最低”互相印证；
  (ii) 最弱比值通道 r_tau 近零信号与网格 gen 窗数值地板(≤0.19)同量级，故 E1 中“r 近静默”
  的说法只在 ~0.2 mA/cm² 以上成立，语义上应读作“在数值分辨不出与 0 的区别”，而非“严格为 0”。
* 未发现需要改变 E1/E2/DB 数值结论的收敛问题；也不需要给冻结 DB 换网格（那会改动 100k 曲线，
  超出本任务范围，且新网格仍无“真值”锚点）。

## 5. 产物

* 输入：`inputs/e2_manifest.csv`(48)、`_work/chunks/e2_chunk_{0..3}.csv`
* 曲线：`outputs/curves/row_%05d.csv`(48, 含 nelem/nvtx/status 头) + `qc_studyrun_00000.csv`
* 表：`outputs/tables/e2_qc_runall_vs_studyrun.csv`, `e2_mesh_levels.csv`, `e2_tol_levels.csv`,
  `e2_numerical_error_summary.csv`, `e2_windowed_rmse.csv`, `e2_meta.json`
* 图：`figures/e2_mesh_convergence.png`, `e2_tol_convergence.png`, `e2_numerical_error.png`
* 运行/验证记录：`_work/logs/*.log`；`scripts/e2_probe.m`（API 探针）、`e2_smoke.m`
  （runAll-vs-study.run 单行验证，用于修正 `getDouble` 读取并确认 runAll 等价）。

**审阅状态**：数值结果程序化 QC 通过（48/48 ok、runAll≡study.run、网格/容差单调）；人类审阅未开始。
