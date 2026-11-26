"""
Sensitivity - Uncertainty Coupling Analysis
============================================
J-V sensitivity vs VAE inversion uncertainty
"""

import numpy as np
import matplotlib.pyplot as plt


# =====================================================
# 输出路径
# =====================================================

OUTPUT = "/home/student2/result-9D-AE-interface-lifetimes-2/compare"


# =====================================================
# 参数名称
# 保持VAE顺序
# =====================================================

PARAM_NAMES = [
    "mu_n",
    "mu_p",
    "tau_n",
    "tau_p",
    "Nc",
    "Nv",
    "tau_ETL",
    "tau_HTL",
    "rad_c"
]


# =====================================================
# J-V sensitivity
# 来自 parameter_JV_sensitivity_score
# =====================================================

sensitivity = np.array([

    0.259256,   # mu_n
    0.258027,   # mu_p
    0.146627,   # tau_p
    0.139511,   # tau_n
    0.125126,   # Nc
    0.136556,   # Nv
    0.015462,   # tau_ETL
    0.026015,   # tau_HTL
    0.032587    # rad_c

])


# =====================================================
# VAE uncertainty
# 来自v6 evaluation
# =====================================================

uncertainty = np.array([

    0.28691,   # mu_n
    0.27861,   # mu_p
    0.29902,   # tau_n
    0.30420,   # tau_p
    0.25408,   # Nc
    0.26904,   # Nv
    0.48999,   # tau_ETL
    0.43659,   # tau_HTL
    0.48748    # rad_c

])


# =====================================================
# Min-Max normalization
# =====================================================
'''
sens_norm = (
    sensitivity - sensitivity.min()
) / (
    sensitivity.max() - sensitivity.min()
)


unc_norm = (
    uncertainty - uncertainty.min()
) / (
    uncertainty.max() - uncertainty.min()
)
'''

sens_norm = sensitivity / sensitivity.max()

unc_norm = uncertainty / uncertainty.max()


# =====================================================
# 绘图
# =====================================================

x = np.arange(len(PARAM_NAMES))

width = 0.35


plt.figure(figsize=(10,5))


plt.bar(
    x-width/2,
    sens_norm,
    width,
    label="J-V Sensitivity"
)


plt.bar(
    x+width/2,
    unc_norm,
    width,
    label="VAE Uncertainty"
)



plt.xticks(
    x,
    PARAM_NAMES,
    rotation=45,
    ha="right"
)


plt.ylabel(
    "Normalized value"
)


plt.title(
    "Relationship between J-V Sensitivity and VAE Prediction Uncertainty"
)


plt.legend()


plt.grid(
    axis="y",
    alpha=0.3
)


plt.tight_layout()


plt.savefig(
    OUTPUT+"/fig_sensitivity_vs_uncertainty.png",
    dpi=300,
    bbox_inches="tight"
)


plt.show()



# =====================================================
# 输出排序
# =====================================================

print("\n===== Parameter Identifiability Ranking =====")


score = sens_norm - unc_norm


rank = np.argsort(score)[::-1]


for i in rank:

    print(
        f"{PARAM_NAMES[i]:10s} "
        f"Sensitivity={sensitivity[i]:.4f} "
        f"Uncertainty={uncertainty[i]:.4f}"
    )


print("\nFigure saved.")