# -*- coding: utf-8 -*-
"""
EXP1 figures (spec phase N/O): EXP1_FigA-F.
Reads results/per_seed_metrics.csv and results/multiseed_summary.csv.
Categorical palette = Okabe-Ito (colorblind-safe) in fixed family order.
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, os.environ.get("EXP1_RESULTS_DIR", "results"))
FIG = os.path.join(HERE, os.environ.get("EXP1_FIGURES_DIR", "figures"))
os.makedirs(FIG, exist_ok=True)

PARAMS = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c", "ALL"]
MODELS = ["vae", "det_ae", "mlp"]
OKABE = {"vae": "#0072B2", "det_ae": "#E69F00", "mlp": "#009E73"}
MODEL_LABEL = {"vae": "VAE-Gaussian", "det_ae": "Det-AE-Gaussian", "mlp": "Direct-MLP-Gaussian"}

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
})

# ---- load multiseed summary ----
summ = {}
with open(os.path.join(RES, "multiseed_summary.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        summ[(r["model"], r["parameter"])] = r


def ms(model, param, col):
    return float(summ[(model, param)][col + "_mean"]), float(summ[(model, param)][col + "_sd"])


def group_bars(figpath, col, ylabel, title, ymin=None, ymax=None, ref=None, ref_kw=None):
    """Grouped bar (mean) + SD error cap; x = 9 params + ALL; 3 families."""
    fig, ax = plt.subplots(figsize=(9.2, 3.4), dpi=150)
    n = len(PARAMS); width = 0.26
    x = np.arange(n)
    for j, model in enumerate(MODELS):
        means = [ms(model, p, col)[0] for p in PARAMS]
        sds = [ms(model, p, col)[1] for p in PARAMS]
        ax.bar(x + (j - 1) * width, means, width, color=OKABE[model],
               edgecolor=OKABE[model], linewidth=0.5,
               label=MODEL_LABEL[model], zorder=3)
        ax.errorbar(x + (j - 1) * width, means, yerr=sds, fmt="none",
                    ecolor="#333333", elinewidth=0.8, capsize=2, zorder=4)
    if ref is not None:
        ax.axhline(ref, color="#B00000", ls="--", lw=1.0, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(PARAMS, rotation=40, ha="right")
    ax.set_ylabel(ylabel); ax.set_title(title)
    if ymin is not None: ax.set_ylim(ymin, ymax)
    ax.legend(frameon=False, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, 1.14), handlelength=1.0, handletextpad=0.5)
    fig.tight_layout()
    fig.savefig(figpath, bbox_inches="tight")
    plt.close(fig)


# ---- Fig A: per-parameter Pearson r, mean+/-SD ----
group_bars(os.path.join(FIG, "EXP1_FigA_pearson_r.png"),
           "pearson_r", "Pearson r (mean $\\pm$ SD, 5 seeds)",
           "EXP1 Fig A — Recoverability $r$ per parameter (leakage-free, matched baselines)",
           ymin=0.0, ymax=1.0)

# ---- Fig B: MAE in decades ----
group_bars(os.path.join(FIG, "EXP1_FigB_mae_decades.png"),
           "mae_decades", "MAE (decades, mean $\\pm$ SD)",
           "EXP1 Fig B — Parameter error in decades",
           ymin=0.0)

# ---- Fig C: 95% coverage + 0.95 reference ----
group_bars(os.path.join(FIG, "EXP1_FigC_coverage_95.png"),
           "coverage_95", "95% Gaussian coverage (mean $\\pm$ SD)",
           "EXP1 Fig C — Calibration of predictive uncertainty",
           ymin=0.80, ymax=1.0,
           ref=0.95, ref_kw={"label": "nominal 0.95"})

# ---- Fig D: Gaussian test NLL ----
group_bars(os.path.join(FIG, "EXP1_FigD_nll.png"),
           "gaussian_nll", "Gaussian NLL (mean $\\pm$ SD)",
           "EXP1 Fig D — Gaussian negative log-likelihood on test",
           ymin=0.0)

# ---- Fig E: sigma-error Spearman ----
group_bars(os.path.join(FIG, "EXP1_FigE_spearman_sigma.png"),
           "spearman_sigma_error", "Spearman $\\rho(\\sigma,|e|)$ (mean $\\pm$ SD)",
           "EXP1 Fig E — Uncertainty calibration: does $\\sigma$ track absolute error?",
           ymin=0.0)

# ---- Fig F: frozen VAE-v6 (single) vs leakage-free VAE (mean+/-SD, 5 seeds) ----
REF_R = {"mu_n": 0.9063, "mu_p": 0.9194, "tau_n": 0.8783, "tau_p": 0.8808,
         "Nc": 0.9090, "Nv": 0.8956, "tau_ETL": 0.5936, "tau_HTL": 0.7199, "rad_c": 0.5592}
PARAMS9 = PARAMS[:-1]
fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=150)
x = np.arange(len(PARAMS9))
free = [REF_R[p] for p in PARAMS9]
lf = [ms("vae", p, "pearson_r")[0] for p in PARAMS9]
lf_sd = [ms("vae", p, "pearson_r")[1] for p in PARAMS9]
ax.plot(x, free, "s", color="#555555", ms=6, mec="#222222", mew=0.8,
        label="frozen VAE-v6 (full-data scaler)", zorder=3)
ax.errorbar(x, lf, yerr=lf_sd, fmt="o", color=OKABE["vae"], ms=5.5,
            ecolor="#333333", elinewidth=0.9, capsize=3,
            label="leakage-free VAE (5 seeds, mean$\\pm$SD)", zorder=4)
for i in range(len(PARAMS9)):
    ax.plot([x[i], x[i]], [free[i], lf[i]], color="#cccccc", lw=0.7, zorder=1)
ax.axhline(np.mean(free), color="#B00000", ls=":", lw=1.0)
ax.annotate("frozen mean $\\bar{r}$=%.3f" % np.mean(free),
            xy=(0.02, np.mean(free) + 0.012), fontsize=8, color="#B00000")
ax.set_xticks(x); ax.set_xticklabels(PARAMS9, rotation=40, ha="right")
ax.set_ylabel("Pearson r")
ax.set_ylim(0.0, 1.02)
ax.set_title("EXP1 Fig F — Preprocessing leakage effect on VAE recoverability")
ax.legend(frameon=False, loc="lower right", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "EXP1_FigF_frozen_vs_leakagefree.png"), bbox_inches="tight")
plt.close(fig)

print("figures written to", FIG)
