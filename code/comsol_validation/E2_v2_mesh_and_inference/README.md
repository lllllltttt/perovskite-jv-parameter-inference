# E2-v2 — 网格×容差对冻结模型**正演曲线与反演推断**的影响（状态：**已运行**）

**日期**：2026-09-07 · 目录：`supplementary_validation_v2/E2_mesh_and_inference/`
**对象**：复核「换网格会不会改变冻结 VAE 的反演预测」这一 P0 问题。只读输入与冻结 hash 见
`job_manifest.md` §1；所有新曲线/表/图都在本目录，未触碰冻结模型/DB/旧包。

---

## 0. 结论条目（状态标记）

| 条目 | 状态 |
|---|---|
| 旧 48 条曲线窗口化重析（正确的 le1/gt1/gen0/… 窗） | 已执行 → 复核 round-1 数字 |
| 细网格 m=0.35/0.25 在**同一 6 个代表**上的新求解 | 已执行（18/18 ok） |
| 细网格上的容差重检（m=0.25, stol 1e-7 vs 1e-6） | 已执行 |
| 每条曲线经冻结 scaler+encoder+param_head（z_mean，不重采样）反演 | 已执行（66 条） |
| >1 V 与 ≤1 V 段互换的窗归因（window-substitution） | 已执行 |
| 网格/求解器设置存档 | 已执行（基值来自 round-1 `getDouble` 探针；每行头记 m/stol/nelem/nvtx） |
| 各**薄层**单元数 | 部分——仅全局 edg 单元数 nelem；逐层拆分未在本次运行记录（见 §7 遗留） |
| 是否需要 m=0.18/0.125 更细网格 | 未执行（判定不需要，见 §6） |

**一句话结论（对 P0）**：≤1 V/发电窗物理信息对网格**稳健**——细网格（m=0.35/0.25）下全部 6 个
代表的设备指标与冻结 m=1 相差 |dJsc|≤0.031%、|dPmax|≤0.054%、|dVoc|≤1.9 mV（唯一例外 14912 的
Voc_t≈1.19 V 位于 >1 V 非收敛带，dVoc +8.2 mV 本身是 >1 V 伪迹）；反演对**好辨识参数**
（mu_n/mu_p/Nc/Nv/tau_HTL）最多移动 ≤0.04σ，但对**弱辨识参数**（rad_c/tau_ETL/tau_n/tau_p）移动
可达 0.10–0.16σ（log10 至多 ~0.3–0.5 decade）；**窗互换证明该弱参数敏感性完全由 >1 V 尾巴驱动**
（换入哪一段 >1 V，预测就贴向哪个母体），而 ≤1 V/gen0 段无法区分网格。求解器容差在 m=1 与 m=0.25
上都对正演指标（≤1e-6% Pmax、≤1e-8 V）与反演预测（0/6 条曲线敏感）**毫无影响**。

---

## 1. 冻结输入与新增求解

- 冻结输入（只读，md5 见 `job_manifest.md`）：`1D_PSC_wen.mph`、`dataset_normalized.npz`、
  `J_scaler.pkl`、`param_scaler.pkl`、`vae-v6/{encoder,param_head}.h5`、旧 `E2/inputs/e2_manifest.csv`。
- 新增 COMSOL 求解 **18 条**（远低于 350 上限）：6 代表 × { m=0.35 stol1e-6, m=0.25 stol1e-6,
  m=0.25 **stol1e-7** }。行号 rowid 100–117。
- 求解：复制 round-1 冻结 worker 逻辑（`e2v2_comsol_batch.m`，读后不改冻结），mesh Size 双特性
  `size/size1` 的 hmax/hmin 经 `getDouble` 读冻结基值后同乘 m 重建，`sol('sol1').feature('s1').stol`
  重设后 `sol1.runAll`；4 server(2041–2044)+4 MATLAB，launcher 以 `wait` 收尾。
- 网格单元数：m=0.35 → **nelem 269**、m=0.25 → **nelem 367**（旧 m 链 2.0/1.41/1.00/0.71/0.50 →
  68/87/112/146/195）。nvtx=7 恒定。18/18 行 `status ok`（`_work/logs/e2v2_full_{0..3}.log`），
  单行耗时 22–49 s。

## 2. 正演收敛（窗口化，相对冻结 m=1 曲线）

窗由**目标**曲线（npz）定（Voc 插值/离散 Vmp），同一样本所有行共用同一组点。
表 `outputs/e2v2_mesh_windowed_rmse.csv`、`e2v2_device_metrics.csv`。

| test_index (Sample_ID) | m | nelem | gen0 RMSE | >1 V RMSE | 全窗 RMSE | vs_target 全窗 |
|---|---|---|---|---|---|---|
| 3741 (131019) | 0.25 | 367 | 0.060 | 126.5 | 60.6 | 60.6 |
| 5808 (87146) | 0.25 | 367 | 0.012 | 40.2 | 19.2 | 19.2 |
| 7693 (23756) | 0.25 | 367 | 0.037 | 128.4 | 61.5 | 61.5 |
| 8874 (138740) | 0.25 | 367 | 0.006 | 0.53 | 0.26 | 0.26 |
| 14179 (180278) | 0.25 | 367 | 0.005 | 0.98 | 0.47 | 0.47 |
| 14912 (65444) | 0.25 | 367 | 0.115 | 2.61 | 1.25 | 1.25 |

（RMSE 单位 mA/cm²，相对各自 m=1 冻结曲线；`vs_target`=相对 npz 目标曲线。）
要点：
- **m=1 全窗 vs_target RMSE = 0.000** → DB 的目标 J–V 本身就是冻结 m=1 网格的解；换任何网格都只会
  “偏离”训练数据。
- **≤1 V/发电窗收敛**：最细两档相邻差 ≤0.007 mA/cm²（gen0），各样本 m0.25 vs m=1 的 gen0 RMSE
  ≤0.115（绝对量 ≪ Jsc~20 mA/cm² 的 1%）。两档细网格之间已到数值收敛。
- **>1 V 未收敛**：3741/5808/7693 在 m0.25 的 >1 V RMSE 达 40–128 mA/cm² 且随加密不趋于定值
  （m=1 本身不是该区收敛解——DB 只是恰好生成在 m=1）。8874/14179/14912 的 >1 V 差较小（0.5–2.6）。

### 设备指标（预注册阈值 |dPmax|≤0.1%、|dVoc|≤2 mV、|dJsc|≤0.05%，对 m0.25）
| rep | dJsc% | dVoc (mV) | dPmax% | 判定 |
|---|---|---|---|---|
| 3741 | −0.0009 | +0.9 | +0.030 | 通过 |
| 5808 | −0.0097 | +0.6 | −0.008 | 通过 |
| 7693 | −0.0031 | +0.9 | +0.014 | 通过 |
| 8874 | +0.031 | +1.9 | +0.054 | 通过 |
| 14179 | +0.012 | +0.8 | +0.033 | 通过 |
| 14912 | −0.0015 | **+8.2** | +0.002 | **dVoc 不通过** |

14912 例外原因：其 Voc_t≈1.1996 V > 1 V，插值点位于 >1 V 非收敛带（该带 m0.25 vs m=1 的逐点差即
~0.1 mA/cm²、Voc 斜率陡），故 +8.2 mV 是 **>1 V 伪迹**而非 ≤1 V 物理区不稳健；14912 在 ≤1 V 窗的
m0.25 vs m=1 RMSE 仅 0.007 mA/cm²。

### 容差（同网格直接配对）
- m=1：stol 1e-4/1e-5/1e-7 vs 冻结 1e-6 → 全部指标 ~1e-9–1e-6 位一致（复核 round-1）。
- **m=0.25：stol 1e-7 vs 1e-6** → dJsc ≤1e-6%、dVoc ≤1.5e-8 V、dPmax ≤1e-6% → 细网格上容差同样收敛。

## 3. 反演敏感性（每条曲线过冻结 VAE）

冻结路径：Jphys(mA/cm²) → 逐列 MinMax `Jphys_to_Jnorm` → `encoder(J_norm)` 取 **z_mean**（不重采样）
→ `param_head(z_mean)` → μ、σ=clip(softplus+0.01, 0.01, 1)，在归一化 log10 空间比较（z 分数与
log10 空间的换算差仅线性，等价的）。判据（预注册）：`|Δμ| > 0.10 σ_curve` → 该曲线对网格/容差
**反演敏感**。表 `e2v2_inverse_perrow.csv`、`e2v2_inverse_mesh_sensitivity.csv`、
`e2v2_inverse_tolpair.csv`。

| 比较 | 敏感 cell / total | 敏感曲线 |
|---|---|---|
| 细链 m0.35/0.25 vs m=1（6×2 曲线） | 59/108 | **10/12** |
| 粗链 m2.0–0.50 vs m=1 | 101/216 | 20/24 |
| 容差 m=1 stol1e-7/1e-5/1e-4 vs 1e-6 | 0/162 | **0/6** |
| 容差 **m=0.25 stol1e-7 vs 1e-6** | 0/54 | **0/6** |

按参数（细链最坏，12 条曲线取 max）：好辨识参数 max|z|——Nc 0.039、Nv 0.038、mu_n 0.027、
mu_p 0.035、tau_HTL 0.022 → **全部 ≤0.04σ，不敏感**；弱辨识参数——rad_c 0.159、tau_ETL 0.082、
tau_n 0.063、tau_p 0.052，其 log10 μ 最坏位移 0.48/0.33/0.48/0.40 decade。**注意**：rad_c/tau_ETL 的
σ 常触顶 1.0（=整个先验宽 3 decade），故 0.1σ 判据对它们偏宽；log10-decade 位移是更严的观察口径。

## 4. 窗归因（window-substitution）：敏感性来自 >1 V 尾巴

把每条代表的 m=1(ref) 与 m=0.25(fine) 曲线在固定 V=1.0 及 Voc_t 处对切再组合，过同一冻结反演；
看 μ 贴向哪个母体。表 `e2v2_inverse_window_substitution.csv`、图 `e2v2_fig_window_substitution.png`。

| 组合（ti 3741，max-over-9-params Δμ） | d vs full-ref | d vs full-fine | 贴向 |
|---|---|---|---|
| fine ≤1 V + ref >1 V | 0.0019 | 0.1582 | **ref** |
| ref ≤1 V + **fine >1 V** | 0.1571 | 0.0015 | **fine** |

5808、7693 同型（0.083/0.084、0.115/0.116）；8874、14179、14912 两种组合对两个母体都 ≤0.04
（其正演 >1 V 本身几乎没动，预测自然不变）。→ **只要换入的那段 >1 V 来自哪个网格，反演 μ 就贴向
哪个网格；≤1 V/gen0 段（已收敛、物理区）完全无法区分 m=1 与 m=0.25。** 这是对“网格改变弱参数反演
预测”的机制性解释：VAE 在读 >1 V 高偏压尾巴，而该尾巴并非收敛解。

## 5. 对 P0 的回答（不夸大、不抹平）

1. **正演**：物理发电窗（≤1 V / ≤Voc_t）对 m=0.35/0.25 已收敛（相邻差 ≤0.007 mA/cm²）；>1 V 区在
   任何网格都未收敛，且 DB 训练曲线本身是 m=1 解 → “换网格是否会改变正演预测”在物理窗内=否、在
   >1 V 尾巴=是（但那里本无“真值”）。
2. **反演（冻结）**：好辨识参数（迁移率×2、DOS×2、tau_HTL）**不敏感**（≤0.04σ）；弱辨识参数
   （rad_c、tau_ETL、绝对 tau_n/tau_p）**敏感**（至多 ~0.16σ / ~0.5 decade），**机制=读 >1 V 尾巴**
   （§4 互换证明）。因此**任何声称“网格地板 ≪ 反演不确定度”的全局表述都需限定到物理窗与
   好辨识参数**；对弱参数在 >1 V 上的读数，细网格会系统性移动 VAE 的点估计。
3. **容差**：在 m=1 与 m=0.25 上对正演与反演都无影响（0/6 曲线敏感）。冻结 stol=1e-6 站得住。
4. 6 样本反演覆盖率**不能**当作全集校准（同 v1 边界）——本次仅回答网格敏感性，不做校准声明。

## 6. 为何不需要 m=0.18/0.125

计划里 (+0.18/0.125 as needed) 的触发条件是“≤1 V 尚未在两档细网格间收敛”。实测两档相邻差
≤0.007 mA/cm²（远低于设备指标阈值与 E1 响应地板），≤1 V 已收敛；>1 V 不随加密收敛且不承载物理
结论。再加密只会为“>1 V 仍不收敛”增加无效确认，故**不跑**（不浪费 350 上限内的求解预算）。

## 7. 遗留 / 未执行

- **各薄层单元数**：worker 只记全局 edg `nelem`/`nvtx`（nvtx=7=顶点类型数），未拆到 ETL/吸收层/HTL
  各薄层。基值 hmax/hmin 取自 round-1 `getDouble` 探针（size/size1 ≈ 6.89/1.06 与 3.55/0.53 nm
  量级，m 同乘；`e2_probe.m` 只读探针）。如需逐层计数，需一次 0-求解的 mesh 探针（读层几何+域单元
  统计），已记入 `unresolved_items.md` 作低成本跟进。
- 旧 E2 README 的“网格地板 ≪ E1 响应”只就**正演响应窗**成立；v2 新增的反演敏感性（§5.2）是原
  round-1 未覆盖的新发现，需并入复核报告。

## 8. 产物
- 输入：`inputs/e2v2_manifest.csv`(18)、`_work/chunks/e2v2_chunk_{0..3}.csv`
- 曲线：`outputs/curves/row_{00100..00117}.csv`（头含 rowid/test_index/level_type/level/mesh_size_factor/
  stol/status/elapsed_s/nelem/nvtx/unit）
- 表：`outputs/e2v2_mesh_windowed_rmse.csv`、`e2v2_device_metrics.csv`、`e2v2_rel_gt1.csv`、
  `e2v2_inverse_perrow.csv`、`e2v2_inverse_mesh_sensitivity.csv`、`e2v2_inverse_tolpair.csv`、
  `e2v2_inverse_window_substitution.csv`
- 图：`outputs/e2v2_fig_mesh_convergence.png`、`e2v2_fig_window_substitution.png`
- 脚本：`scripts/{e2v2_comsol_batch.m, run_e2v2.sh, e2v2_analyze.py, e2v2_inverse_sensitivity.py,
  e2v2_figures.py}`
- 运行记录：`_work/logs/{srvE2v2_*.log, e2v2_full_{0..3}.log(.out/.err)}`

**审阅状态**：数值结果程序化复算通过（18/18 ok；容差配对 0/6；窗归因方向干净）；人类审阅未开始。
