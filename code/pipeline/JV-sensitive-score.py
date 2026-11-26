"""
Parameter-JV Sensitivity Score
==============================
计算每个物理参数对J-V曲线整体的敏感性

S_i = mean(|corr(parameter_i, J(V))|)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =====================================================
# 路径
# =====================================================
CSV_PATH = r"/home/student2/result-csv/JV_database_9D_interface_lifetimes-2.csv"

OUTPUT_PATH = r"/home/student2/result-csv/parameter_JV_sensitivity_score-2.csv"

FIG_PATH = r"/home/student2/result-csv/parameter_JV_sensitivity_score-2.png"


# =====================================================
# 参数
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

J_COLS = [
    c for c in df.columns
    if c.startswith("J_")
]


print("Dataset:", df.shape)
print("J points:", len(J_COLS))


# =====================================================
# 计算相关矩阵
# =====================================================

corr_matrix = np.zeros(
    (len(PARAM_COLS), len(J_COLS))
)


for i, param in enumerate(PARAM_COLS):

    print(f"Processing {param}")

    for j, J in enumerate(J_COLS):

        corr_matrix[i,j] = df[param].corr(df[J])


# =====================================================
# 敏感性指标
# =====================================================

sensitivity_score = np.mean(
    np.abs(corr_matrix),
    axis=1
)


result = pd.DataFrame({

    "Parameter": PARAM_COLS,

    "Sensitivity_score": sensitivity_score

})


# 排序
result = result.sort_values(
    "Sensitivity_score",
    ascending=False
)


print("\n===== Parameter Sensitivity =====")
print(result)


result.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nSaved:", OUTPUT_PATH)



# =====================================================
# 绘图
# =====================================================

plt.figure(
    figsize=(9,5)
)


sns.barplot(
    data=result,
    x="Parameter",
    y="Sensitivity_score"
)


plt.ylabel(
    "Mean |Pearson correlation|"
)

plt.xlabel(
    "Physical parameter"
)


plt.title(
    "Global Parameter-JV Sensitivity"
)


plt.xticks(
    rotation=45,
    ha="right"
)


plt.tight_layout()


plt.savefig(
    FIG_PATH,
    dpi=300,
    bbox_inches="tight"
)


plt.show()


print("Figure saved:", FIG_PATH)