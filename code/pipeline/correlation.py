"""
Parameter Correlation Analysis
==============================
输入:
    JV_database_9D_interface_lifetimes.csv

输出:
    parameter_correlation_matrix.png
    parameter_correlation.csv

用途:
    分析9个物理参数之间是否存在耦合
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# =====================================================
# 路径
# =====================================================

CSV_PATH = r"/home/student2/result-csv/JV_database_9D_interface_lifetimes-2.csv"

OUTPUT_DIR = r"/home/student2/result-9D-AE-interface-lifetimes-2/correlation"

os.makedirs(OUTPUT_DIR, exist_ok=True)



# =====================================================
# 参数列表
# =====================================================

PARAM_COLS = [
    "mu_n_pvk",
    "mu_p_pvk",
    "tau_n_pvk",
    "tau_p_pvk",
    "Nc_eff_pvk",
    "Nv_eff_pvk",
    "tau_ETL",
    "tau_HTL",
    "rad_c",
]


# =====================================================
# 读取数据
# =====================================================

df = pd.read_csv(CSV_PATH)

params = df[PARAM_COLS]


print("Dataset:")
print(params.shape)


# =====================================================
# Pearson相关矩阵
# =====================================================

corr = params.corr(method="pearson")


print("\n===== Pearson Correlation =====")
print(corr.round(3))


# 保存csv

corr.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "parameter_correlation.csv"
    )
)


# =====================================================
# 热力图
# =====================================================

plt.figure(figsize=(10,8))

sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    square=True,
    linewidths=0.5
)


plt.title(
    "Pearson Correlation Matrix of 9 Physical Parameters",
    fontsize=14
)

plt.tight_layout()


save_path = os.path.join(
    OUTPUT_DIR,
    "parameter_correlation_matrix.png"
)

plt.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


print("\nSaved:")
print(save_path)



# =====================================================
# 输出高度相关参数
# =====================================================

print("\n===== High Correlation Pairs =====")

threshold = 0.7

for i in range(len(PARAM_COLS)):
    for j in range(i+1,len(PARAM_COLS)):

        value = corr.iloc[i,j]

        if abs(value) >= threshold:

            print(
                f"{PARAM_COLS[i]:15s} "
                f"<--> "
                f"{PARAM_COLS[j]:15s}"
                f" : {value:.3f}"
            )


print("\nDone.")