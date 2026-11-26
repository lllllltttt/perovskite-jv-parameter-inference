"""
前向验证画图脚本 v3 — 9参数版
====================
改动：
  - 参数从6个扩展到9个（tau_ETL, tau_HTL, rad_c）
  - 电压点数 121 → 131（0~1.3V）
  - y轴统一截断到 [-200, 25] mA/cm²
  - 图尺寸放大，子图间距优化
  - 线条样式、颜色、图例重新设计
  - 标题和标注字体统一
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.io import loadmat
from sklearn.metrics import r2_score

# =====================================================
# 全局字体设置
# =====================================================
mpl.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        10,
    "axes.titlesize":   10,
    "axes.labelsize":   10,
    "legend.fontsize":  8.5,
    "xtick.labelsize":  9,
    "ytick.labelsize":  9,
    "axes.linewidth":   1.0,
    "grid.alpha":       0.3,
    "grid.linewidth":   0.6,
})

# =====================================================
# 路径配置
# =====================================================
NPZ_PATH     = "/home/student2/result-9D-AE-interface-lifetimes-2/forward_validation2/selected_samples.npz"
TRUE_MAT_DIR = "/home/student2/result-9D-AE-interface-lifetimes-2/forward_validation2/comsol_true/"
PRED_MAT_DIR = "/home/student2/result-9D-AE-interface-lifetimes-2/forward_validation2/comsol_pred/"
OUTPUT_DIR   = "/home/student2/result-9D-AE-interface-lifetimes-2/forward_validation2/"

# =====================================================
# 9个参数（完整参数集）
# =====================================================
PARAM_NAMES = [
    "mu_n_pvk", "mu_p_pvk",
    "tau_n_pvk", "tau_p_pvk",
    "Nc_eff_pvk", "Nv_eff_pvk",
    "tau_ETL",           # 钙钛矿/C60 界面寿命
    "tau_HTL",           # NiOx/钙钛矿 界面寿命
    "rad_c",             # 辐射复合系数
]

PARAM_LABELS = [
    r"$\mu_n$", r"$\mu_p$",
    r"$\tau_n$", r"$\tau_p$",
    r"$N_c$", r"$N_v$",
    r"$\tau_{ETL}$", r"$\tau_{HTL}$",
    r"$k_{rad}$",
]

Y_MIN, Y_MAX = -200, 25

# =====================================================
# 加载数据
# =====================================================
print("Loading data...")
data = np.load(NPZ_PATH, allow_pickle=True)

selected_idx     = data["selected_idx"]
J_raw_selected   = data["J_raw_selected"]          # (n, 131)
params_true_phys = data["params_true_phys"]        # (n, 9)
params_pred_phys = data["params_pred_phys"]        # (n, 9)
log_err_selected = data["log_err_selected"]        # (n, 9)

# 电压范围 0~1.3V, 131点
V = np.linspace(0, 1.3, 131)

print(f"Loaded {len(selected_idx)} samples, {J_raw_selected.shape[1]} voltage points")

# =====================================================
# 加载COMSOL结果
# =====================================================
def load_comsol_mat(mat_dir, sample_id):
    fname = os.path.join(mat_dir, f"validation_sample_{sample_id:05d}.mat")
    if not os.path.exists(fname):
        print(f"  [WARNING] Not found: {fname}")
        return None
    d = loadmat(fname)
    J = np.squeeze(d["J"]) * 0.1   # A/m² → mA/cm²
    return J[:131]                 # 取前131点（0~1.3V）

J_true_comsol, J_pred_comsol = [], []
for idx in selected_idx:
    J_true_comsol.append(load_comsol_mat(TRUE_MAT_DIR, idx))
    J_pred_comsol.append(load_comsol_mat(PRED_MAT_DIR, idx))

# =====================================================
# 计算R²
# =====================================================
r2_true_list, r2_pred_list = [], []
for i in range(len(selected_idx)):
    r2_true_list.append(
        r2_score(J_raw_selected[i], J_true_comsol[i])
        if J_true_comsol[i] is not None else np.nan
    )
    r2_pred_list.append(
        r2_score(J_raw_selected[i], J_pred_comsol[i])
        if J_pred_comsol[i] is not None else np.nan
    )

# =====================================================
# 画图
# =====================================================
n = len(selected_idx)
fig, axes = plt.subplots(1, n, figsize=(3.8 * n, 5.0),
                         sharey=True,
                         gridspec_kw={"wspace": 0.08})

# 配色
C_ORIG = "#999999"
C_TRUE = "#2196F3"
C_PRED = "#E53935"

for i, (ax, idx) in enumerate(zip(axes, selected_idx)):

    # --- 原始曲线 ---
    ax.plot(V, J_raw_selected[i],
            color=C_ORIG, linewidth=2.0, zorder=4,
            label="Original")

    # --- 真实参数重仿真 ---
    if J_true_comsol[i] is not None:
        ax.plot(V, J_true_comsol[i],
                color=C_TRUE, linewidth=1.8,
                linestyle="--", zorder=3,
                label=f"True params ($R^2$={r2_true_list[i]:.4f})")

    # --- 预测参数重仿真 ---
    if J_pred_comsol[i] is not None:
        ax.plot(V, J_pred_comsol[i],
                color=C_PRED, linewidth=1.8,
                linestyle="-.", zorder=3,
                label=f"Pred params ($R^2$={r2_pred_list[i]:.4f})")

    # --- 零线 ---
    ax.axhline(0, color="gray", linewidth=0.7, linestyle=":", zorder=1)

    # --- 轴范围 ---
    ax.set_xlim(0, 1.3)
    ax.set_ylim(Y_MIN, Y_MAX)

    # --- 最大误差参数标注 ---
    worst_i    = log_err_selected[i].argmax()
    worst_label = PARAM_LABELS[worst_i]
    worst_val   = log_err_selected[i, worst_i]

    ax.set_title(
        f"Sample {idx}\n"
        f"max $\\Delta\\log_{{10}}$={worst_val:.3f} ({worst_label})",
        pad=6
    )

    ax.set_xlabel("Voltage (V)")
    if i == 0:
        ax.set_ylabel(r"$J$ (mA cm$^{-2}$)")

    ax.legend(loc="lower left", framealpha=0.85,
              edgecolor="#cccccc", handlelength=1.8)
    ax.grid(True)

    # 右侧和顶部边框去掉
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle(
    "Forward Validation: VAE Parameter Extraction → COMSOL Re-simulation",
    fontsize=12, fontweight="bold", y=1.02
)

plot_path = f"{OUTPUT_DIR}/forward_validation_plot_v3.png"
plt.savefig(plot_path, dpi=180, bbox_inches="tight")
print(f"Plot saved: {plot_path}")
print("Done.")