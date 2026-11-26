"""
PSC Parameter LHS Sampling — v5 (9D with Interface Lifetimes)
================================================================
更新内容：
  - 将原先的两个界面缺陷密度（Nt_ETL_PVK, Nt_HTL_PVK）替换为
    两个界面层的 SRH 寿命（tau_interface_ETL, tau_interface_HTL）。
  - 范围：1e-12 ~ 1e-8 秒（覆盖从极弱复合到极强复合的敏感区）。
  - 采用独立对数空间采样，完美解耦顶/底界面的复合强度。
  - 其他参数保持不变：迁移率（μ_avg, μ_ratio）、体寿命（τ_avg, τ_ratio）、
    有效态密度（DOS_avg, DOS_ratio）、辐射复合系数（rad_c）。
"""

import numpy as np
import pandas as pd
from scipy.stats import qmc

# ==========================================================
# 采样总数
# ==========================================================
N = 200000

# ==========================================================
# Parameter Space v5（9维独立空间）
# ==========================================================
params = {
    # 迁移率
    "mu_avg":     (1e-6,  1e-3),
    "mu_ratio":   (0.2,   5.0),

    # 体相载流子寿命
    "tau_avg":    (1e-9,  1e-2),
    "tau_ratio":  (0.2,   5.0),

    # 有效态密度
    "DOS_avg":    (1e22,  1e26),
    "DOS_ratio":  (0.2,   5.0),

    # 界面复合：使用 SRH 寿命作为集总参数（取代复杂的陷阱密度）
    "tau_interface_ETL": (1e-12, 1e-8),   # 钙钛矿/C60 界面
    "tau_interface_HTL": (1e-14, 1e-10),   # NiOx/钙钛矿 界面

    # 辐射复合系数
    "rad_c":      (1e-12, 1e-9),
}

# ==========================================================
# 对数空间采样的参数名单（所有跨数量级参数）
# ==========================================================
log_params = ["mu_avg", "tau_avg", "DOS_avg",
              "tau_interface_ETL", "tau_interface_HTL", "rad_c"]

# ==========================================================
# Latin Hypercube Sampling（9维）
# ==========================================================
n_dim    = len(params)
sampler  = qmc.LatinHypercube(d=n_dim, seed=42)
lhs_unit = sampler.random(n=N)

print(f"LHS dimensions: {n_dim}D")
print(f"Total samples:  {N}")

# ==========================================================
# 转换到物理空间
# ==========================================================
data = {}
for i, (name, bounds) in enumerate(params.items()):
    low, high = bounds
    u = lhs_unit[:, i]
    if name in log_params:
        values = 10 ** (np.log10(low) + u * (np.log10(high) - np.log10(low)))
    else:
        values = low + u * (high - low)
    data[name] = values

# ==========================================================
# 重建 COMSOL 输入所需的物理参数
# ==========================================================

# 1. 迁移率
mu_n = data["mu_avg"] * np.sqrt(data["mu_ratio"])
mu_p = data["mu_avg"] / np.sqrt(data["mu_ratio"])

# 2. 体相载流子寿命
tau_n = data["tau_avg"] * np.sqrt(data["tau_ratio"])
tau_p = data["tau_avg"] / np.sqrt(data["tau_ratio"])

# 3. 有效态密度
Nc = data["DOS_avg"] * np.sqrt(data["DOS_ratio"])
Nv = data["DOS_avg"] / np.sqrt(data["DOS_ratio"])

# 4. 界面复合寿命（直接取自 LHS 采样值）
tau_interface_ETL = data["tau_interface_ETL"]
tau_interface_HTL = data["tau_interface_HTL"]

# 5. 辐射复合系数
rad_c = data["rad_c"]

# ==========================================================
# 构建并存储 DataFrame
# ==========================================================
df = pd.DataFrame({
    "Sample_ID": np.arange(1, N + 1),

    # ---- 原始 LHS 采样变量（用于神经网络 Label） ----
    "mu_avg":                data["mu_avg"],
    "mu_ratio":              data["mu_ratio"],
    "tau_avg":               data["tau_avg"],
    "tau_ratio":             data["tau_ratio"],
    "DOS_avg":               data["DOS_avg"],
    "DOS_ratio":             data["DOS_ratio"],
    "tau_interface_ETL":     tau_interface_ETL,
    "tau_interface_HTL":     tau_interface_HTL,
    "rad_c":                 rad_c,

    # ---- COMSOL 实际输入物理参数（共 9 个输入项） ----
    "mu_n_pvk":              mu_n,
    "mu_p_pvk":              mu_p,
    "tau_n_pvk":             tau_n,
    "tau_p_pvk":             tau_p,
    "Nc_eff_pvk":            Nc,
    "Nv_eff_pvk":            Nv,
    "tau_interface_ETL_in":  tau_interface_ETL,   # 直接传给 COMSOL 的 ETL 界面寿命
    "tau_interface_HTL_in":  tau_interface_HTL,   # 直接传给 COMSOL 的 HTL 界面寿命
    "rad_c_in":              rad_c,
})

# ==========================================================
# 保存文件（科学计数法输出）
# ==========================================================
filename = f"PSC_LHS_9D_interface_lifetimes_{N}_3.csv"
df.to_csv(filename, index=False, float_format='%.6e')

# ==========================================================
# 统计与边界输出验证
# ==========================================================
print("\n" + "=" * 60)
print(f"PSC LHS Sampling v5（界面寿命版，{N}条）")
print("=" * 60)

print(f"\nShape: {df.shape}")
print(f"Saved: {filename}")

print("\n--- 最终生成的 COMSOL 实际参数边界范围 ---")
comsol_cols = {
    "mu_n_pvk":              "迁移率（电子）       cm²/V/s (或 m²/V/s)",
    "mu_p_pvk":              "迁移率（空穴）       cm²/V/s (或 m²/V/s)",
    "tau_n_pvk":             "体寿命（电子）       s",
    "tau_p_pvk":             "体寿命（空穴）       s",
    "Nc_eff_pvk":            "有效态密度（导带）   cm⁻³ (或 m⁻³)",
    "Nv_eff_pvk":            "有效态密度（价带）   cm⁻³ (或 m⁻³)",
    "tau_interface_ETL_in":  "ETL界面SRH寿命      s (1e-12~1e-8)",
    "tau_interface_HTL_in":  "HTL界面SRH寿命      s (1e-12~1e-8)",
    "rad_c_in":              "辐射复合系数         cm³/s (或 m³/s)",
}
for col, desc in comsol_cols.items():
    v = df[col].values
    print(f"  {col:20s} [{v.min():.3e}, {v.max():.3e}]  {desc}")

print("\n--- 架构状态确认 ---")
print("  [√] 参数替换: 界面缺陷密度 → 界面SRH寿命（集总参数）")
print("  [√] 物理透明: 两个界面寿命独立采样，完全解耦")
print("  [√] 敏感区间: 1e-12~1e-8 s 覆盖复合从极弱到极强的完整过渡")
print("  [√] 逆向友好: 单一参数控制单一界面复合，AE 辨识度极大提升")
print("=" * 60)