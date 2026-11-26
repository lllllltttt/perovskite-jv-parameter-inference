import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


CSV_PATH = "/home/student2/result-csv/JV_database_9D_interface_lifetimes-2.csv"


PARAM_COLS=[
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


df=pd.read_csv(CSV_PATH)


J_cols=[c for c in df.columns if c.startswith("J_")]


result=np.zeros((len(PARAM_COLS),len(J_cols)))


for i,p in enumerate(PARAM_COLS):
    for j,J in enumerate(J_cols):
        result[i,j]=df[p].corr(df[J])


plt.figure(figsize=(16,6))

sns.heatmap(
    result,
    cmap="coolwarm",
    center=0,
    xticklabels=False,
    yticklabels=PARAM_COLS
)

plt.xlabel("Voltage points")
plt.ylabel("Physical parameters")
plt.title("Parameter-JV Sensitivity Correlation")

plt.tight_layout()

plt.savefig(
    "parameter_JV_correlation.png",
    dpi=300
)

plt.show()