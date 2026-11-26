"""
Paper Figures for Physics-informed VAE
9D interface lifetime dataset

Generate:
Fig2: J-V reconstruction
Fig3: Parameter identifiability
Fig4: Uncertainty quantification
Fig5: Uncertainty calibration

No retraining required.
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import pickle

from scipy.stats import pearsonr


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# =====================================================
# Path
# =====================================================

DATA_PATH = "/home/student2/result-9D-AE-interface-lifetimes-2/dataset_normalized.npz"

MODEL_DIR = "/home/student2/result-9D-AE-interface-lifetimes-2/VAE_v6"

FIG_DIR = os.path.join(
    MODEL_DIR,
    "Paper_Figures"
)

os.makedirs(
    FIG_DIR,
    exist_ok=True
)



# =====================================================
# Parameters
# =====================================================

PARAM_NAMES = [

    "mu_n_pvk",
    "mu_p_pvk",
    "tau_n_pvk",
    "tau_p_pvk",
    "Nc_eff_pvk",
    "Nv_eff_pvk",
    "tau_ETL",
    "tau_HTL",
    "rad_c"

]


SHORT_NAMES=[

    r"$\mu_n$",
    r"$\mu_p$",
    r"$\tau_n$",
    r"$\tau_p$",
    r"$N_c$",
    r"$N_v$",
    r"$\tau_{ETL}$",
    r"$\tau_{HTL}$",
    "rad_c"

]


N_PARAM=9



# =====================================================
# Sampling layer
# =====================================================


class Sampling(layers.Layer):

    def call(self,inputs):

        z_mean,z_log_var=inputs

        eps=tf.random.normal(
            shape=tf.shape(z_mean)
        )

        return (
            z_mean+
            tf.exp(0.5*z_log_var)*eps
        )



# =====================================================
# Load data
# =====================================================


data=np.load(
    DATA_PATH,
    allow_pickle=True
)


J_test=data["J_test"].astype(np.float32)

params_test=data["params_test"].astype(np.float32)



print(
    "Test:",
    J_test.shape,
    params_test.shape
)



# =====================================================
# Load models
# =====================================================


encoder=keras.models.load_model(
    f"{MODEL_DIR}/encoder.h5",
    custom_objects={
        "Sampling":Sampling
    }
)


decoder=keras.models.load_model(
    f"{MODEL_DIR}/decoder.h5"
)


param_head=keras.models.load_model(
    f"{MODEL_DIR}/param_head.h5"
)


print("Models loaded")



# =====================================================
# Prediction
# =====================================================


z_mean,z_log_var,z=encoder.predict(
    J_test,
    verbose=0
)


recon=decoder.predict(
    z_mean,
    verbose=0
)


param_mu,param_log_var=param_head.predict(
    z_mean,
    verbose=0
)


param_sigma=np.exp(
    0.5*param_log_var
)



# =====================================================
# Calculate metrics
# =====================================================


pearson=[]

for i in range(N_PARAM):

    r,_=pearsonr(
        params_test[:,i],
        param_mu[:,i]
    )

    pearson.append(r)



coverage=[]

for i in range(N_PARAM):

    lower=(
        param_mu[:,i]
        -
        1.96*param_sigma[:,i]
    )

    upper=(
        param_mu[:,i]
        +
        1.96*param_sigma[:,i]
    )


    c=np.mean(
        (
            params_test[:,i]>=lower
        )
        &
        (
            params_test[:,i]<=upper
        )
    )

    coverage.append(c)



print("Pearson")

for n,r in zip(PARAM_NAMES,pearson):

    print(n,r)



print("Coverage")

for n,c in zip(PARAM_NAMES,coverage):

    print(n,c)



# =====================================================
# Global style
# =====================================================


plt.rcParams.update({

    "font.size":12,
    "axes.linewidth":1.2

})



# =====================================================
# Figure 2
# J-V reconstruction
# =====================================================


plt.figure(
    figsize=(6,4)
)


V=np.linspace(
    0,
    1.3,
    131
)


idx=np.random.choice(
    len(J_test),
    6,
    replace=False
)


for i in idx:

    plt.plot(
        V,
        J_test[i],
        linewidth=1.5
    )


    plt.plot(
        V,
        recon[i],
        linestyle="--",
        linewidth=1.2
    )


plt.xlabel(
    "Voltage (V)"
)

plt.ylabel(
    "Normalized current density"
)


plt.title(
    "J-V reconstruction"
)


plt.tight_layout()


plt.savefig(
    f"{FIG_DIR}/Fig2_JV_reconstruction.png",
    dpi=600
)


plt.close()



# =====================================================
# Figure 3
# Parameter identifiability
# =====================================================


plt.figure(
    figsize=(7,4)
)


bars=plt.bar(
    range(N_PARAM),
    pearson
)


plt.xticks(
    range(N_PARAM),
    SHORT_NAMES
)


plt.ylabel(
    "Pearson r"
)


plt.ylim(
    0,
    1
)


plt.axhline(
    0.8,
    linestyle="--",
    linewidth=1
)


plt.title(
    "Parameter identifiability"
)


plt.tight_layout()


plt.savefig(
    f"{FIG_DIR}/Fig3_parameter_identification.png",
    dpi=600
)


plt.close()



# =====================================================
# Figure 4
# uncertainty
# =====================================================


mean_sigma=np.mean(
    param_sigma,
    axis=0
)



plt.figure(
    figsize=(7,4)
)


plt.bar(
    range(N_PARAM),
    mean_sigma
)


plt.xticks(
    range(N_PARAM),
    SHORT_NAMES
)


plt.ylabel(
    r"Predicted uncertainty $\sigma$"
)


plt.title(
    "Parameter uncertainty estimation"
)


plt.tight_layout()


plt.savefig(
    f"{FIG_DIR}/Fig4_uncertainty.png",
    dpi=600
)


plt.close()



# =====================================================
# Figure 5
# Calibration
# =====================================================


plt.figure(
    figsize=(7,4)
)


plt.bar(
    range(N_PARAM),
    np.array(coverage)*100
)


plt.axhline(
    95,
    linestyle="--",
    linewidth=1
)


plt.xticks(
    range(N_PARAM),
    SHORT_NAMES
)


plt.ylabel(
    "Coverage (%)"
)


plt.ylim(
    80,
    105
)


plt.title(
    "95% uncertainty interval calibration"
)


plt.tight_layout()


plt.savefig(
    f"{FIG_DIR}/Fig5_calibration.png",
    dpi=600
)

# =====================================================
# 追加：计算 R² 并绘制专用柱状图
# =====================================================

print("\n===== Calculating R² Scores =====")

r2_scores = []
for i in range(N_PARAM):
    y_true = params_test[:, i]
    y_pred = param_mu[:, i]
    y_mean = np.mean(y_true)

    # 总平方和 (TSS)
    tss = np.sum((y_true - y_mean) ** 2)
    # 残差平方和 (RSS)
    rss = np.sum((y_true - y_pred) ** 2)

    # 防止分母为 0
    r2 = 1 - (rss / tss) if tss > 1e-12 else 0.0
    r2_scores.append(r2)

    print(f"{PARAM_NAMES[i]}: R² = {r2:.4f}")

# -----------------------------------------------------
# 绘制 R² 专用柱状图（与 Fig3 风格统一）
# -----------------------------------------------------
plt.figure(figsize=(7, 4))

bars = plt.bar(
    range(N_PARAM),
    r2_scores,
    color='#1f77b4',  # 稳重的绿色，区别于 Pearson 的蓝色
    edgecolor='black',
    linewidth=1.2
)

# 参考线（0.8 阈值，与 Fig3 保持一致）
plt.axhline(0.8, linestyle='--', linewidth=1.5, color='gray', alpha=0.8)

# 坐标轴标签
plt.xticks(range(N_PARAM), SHORT_NAMES)
plt.ylabel('R² Score', fontsize=12)
plt.ylim(0, 1.05)  # 留出空间给数值标签

# 【重点】在每个柱子上方显示精确 R² 数值（保留 3 位小数，更严谨）
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2.,
        height + 0.02,
        f'{height:.3f}',  # 用 3 位小数，让审稿人看到细微差异
        ha='center',
        va='bottom',
        fontsize=9,
        rotation=0
    )

plt.title('Parameter prediction accuracy (R²)', fontsize=13)
plt.tight_layout()

# 保存（建议用新文件名，避免覆盖原来的 Fig3）
plt.savefig(f"{FIG_DIR}/Fig6_R2_accuracy.png", dpi=600)
plt.close()

print(f"\nR² figure saved to: {FIG_DIR}/Fig6_R2_accuracy.png")

plt.close()



print("\nAll paper figures saved:")
print(FIG_DIR)