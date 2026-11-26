"""
Step 01: Data Exploration & Normalization
=========================================
输入: JV_database_9D.csv（有效样本，9个物理参数）
      参数列: mu_n_pvk, mu_p_pvk, tau_n_pvk, tau_p_pvk,
              Nc_eff_pvk, Nv_eff_pvk, tau_ETL, tau_HTL, rad_c
输出:
  - dataset_normalized.npz   训练用归一化数据
  - param_scaler.pkl         参数归一化器（推理时反归一化用）
  - J_scaler.pkl             J-V曲线归一化器
  - 01_exploration.png       数据分布可视化
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# =====================================================
# 路径配置（请根据实际情况修改）
# =====================================================
CSV_PATH   = r"/home/student2/result-csv/JV_database_9D_interface_lifetimes-2.csv"  # ← 更新为实际文件名
OUTPUT_DIR = r"/home/student2/result-9D-AE-interface-lifetimes-2"                  # ← 新输出目录

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================
# 读取数据
# =====================================================
df = pd.read_csv(CSV_PATH)
print(f"Dataset shape: {df.shape}")

# 更新后的参数列名（界面缺陷替换为界面寿命）
PARAM_COLS = [
    "mu_n_pvk", "mu_p_pvk",
    "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk",
    "tau_ETL",        # 取代 Nt_ETL_PVK
    "tau_HTL",        # 取代 Nt_HTL_PVK
    "rad_c",
]
J_COLS = [c for c in df.columns if c.startswith("J_")]

params = df[PARAM_COLS].values   # (N, 9)
J      = df[J_COLS].values       # (N, 131)

print(f"Params shape: {params.shape}")
print(f"J-V shape:    {J.shape}")

# =====================================================
# 基本统计
# =====================================================
print("\n--- Parameter statistics ---")
param_df = pd.DataFrame(params, columns=PARAM_COLS)
print(param_df.describe().round(4))

print("\n--- J-V statistics (mA/cm²) ---")
print(f"  J_sc range:  [{J[:, 0].min():.2f}, {J[:, 0].max():.2f}] mA/cm²")
print(f"  J_oc range:  [{J[:, -1].min():.2f}, {J[:, -1].max():.2f}] mA/cm²")
print(f"  Global min:  {J.min():.2f}")
print(f"  Global max:  {J.max():.2f}")

# =====================================================
# 可视化（9个参数 + 1个J-V图 = 10个子图，2×5布局）
# =====================================================
fig, axes = plt.subplots(2, 5, figsize=(20, 8))
axes = axes.flatten()

for i, col in enumerate(PARAM_COLS):
    vals = params[:, i]
    if vals.min() > 0 and (vals.max() / vals.min()) > 100:
        axes[i].hist(np.log10(vals), bins=50, color="#4C72B0", alpha=0.8)
        axes[i].set_xlabel(f"log10({col})")
    else:
        axes[i].hist(vals, bins=50, color="#4C72B0", alpha=0.8)
        axes[i].set_xlabel(col)
    axes[i].set_ylabel("Count")
    axes[i].set_title(col, fontsize=9)

# 随机100条J-V曲线
V = np.linspace(0, 1.3, 131)
idx = np.random.choice(len(J), 100, replace=False)
for j_curve in J[idx]:
    axes[9].plot(V, j_curve, alpha=0.1, color="#4C72B0", linewidth=0.8)
axes[9].set_xlabel("Voltage (V)")
axes[9].set_ylabel("J (mA/cm²)")
axes[9].set_title("100 random J-V curves")
axes[9].axhline(0, color='k', linewidth=0.5)

plt.tight_layout()
save_path = f"{OUTPUT_DIR}/01_exploration.png"
plt.savefig(save_path, dpi=150)
print(f"\nPlot saved: {save_path}")

# =====================================================
# 归一化
# =====================================================
print("\n--- Normalization ---")

log_transform_mask = []
for i, col in enumerate(PARAM_COLS):
    vals = params[:, i]
    need_log = (vals.min() > 0) and ((vals.max() / vals.min()) > 100)
    log_transform_mask.append(need_log)
    print(f"  {col}: log_transform={need_log}  "
          f"range=[{vals.min():.3e}, {vals.max():.3e}]")

log_transform_mask = np.array(log_transform_mask)

params_transformed = params.copy().astype(float)
params_transformed[:, log_transform_mask] = np.log10(
    params[:, log_transform_mask]
)

param_scaler  = MinMaxScaler()
params_scaled = param_scaler.fit_transform(params_transformed)

J_scaler = MinMaxScaler()
J_scaled  = J_scaler.fit_transform(J)

print(f"\nParams scaled range: [{params_scaled.min():.3f}, {params_scaled.max():.3f}]")
print(f"J scaled range:      [{J_scaled.min():.3f}, {J_scaled.max():.3f}]")
print(f"J global min: {J.min():.2f}")
print(f"J[:, -1].mean(): {J[:, -1].mean():.2f}")

# =====================================================
# 划分数据集  70% train / 15% val / 15% test
# =====================================================
N       = len(params_scaled)
idx_all = np.arange(N)

idx_train, idx_temp = train_test_split(idx_all, test_size=0.30, random_state=42)
idx_val,   idx_test = train_test_split(idx_temp, test_size=0.50, random_state=42)

print(f"\nSplit: train={len(idx_train)}, val={len(idx_val)}, test={len(idx_test)}")

# =====================================================
# 保存
# =====================================================
npz_path = f"{OUTPUT_DIR}/dataset_normalized.npz"
np.savez(
    npz_path,
    J_train           = J_scaled[idx_train],
    J_val             = J_scaled[idx_val],
    J_test            = J_scaled[idx_test],
    params_train      = params_scaled[idx_train],
    params_val        = params_scaled[idx_val],
    params_test       = params_scaled[idx_test],
    J_test_raw        = J[idx_test],
    params_test_raw   = params[idx_test],
    log_transform_mask = log_transform_mask,
    param_names       = np.array(PARAM_COLS),
)

with open(f"{OUTPUT_DIR}/param_scaler.pkl", "wb") as f:
    pickle.dump({"scaler": param_scaler, "log_mask": log_transform_mask}, f)
with open(f"{OUTPUT_DIR}/J_scaler.pkl", "wb") as f:
    pickle.dump(J_scaler, f)

print(f"\nSaved: {npz_path}")
print(f"Saved: {OUTPUT_DIR}/param_scaler.pkl")
print(f"Saved: {OUTPUT_DIR}/J_scaler.pkl")
print("\nDone. Next step: 02_train_AE.py")

# =====================================================
# 计算并打印 Voc 统计（仅作参考）
# =====================================================
V = np.linspace(0, 1.3, 131)
Voc = np.zeros(len(J))

for n, j_curve in enumerate(J):
    # 找到 J 穿过 0 的位置
    idx = np.where(np.diff(np.sign(j_curve)))[0]
    if len(idx) == 0:
        Voc[n] = np.nan
        continue
    i = idx[0]
    Voc[n] = np.interp(
        0,
        [j_curve[i], j_curve[i + 1]],
        [V[i], V[i + 1]]
    )
print("\nVoc statistics (percentiles):")
print(np.percentile(Voc[~np.isnan(Voc)], [50, 90, 95, 99, 100]))