# -*- coding: utf-8 -*-
"""
Phase P/Q analysis: model-outcome classification and preprocessing-leakage
effect sizing, from results/per_seed_metrics.csv + multiseed_summary.csv.
Writes results/PQ_analysis.md (descriptive; n=5 seeds per family).
"""
import os, csv, json
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, os.environ.get("EXP1_RESULTS_DIR", "results"))
PARAMS9 = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
MODELS = ["vae", "det_ae", "mlp"]
SEEDS = [20260824, 20260825, 20260826, 20260827, 20260828]

# Frozen VAE-v6 reference (full-data scaler), phase0 repro
FROZEN_R = np.array([0.9063, 0.9194, 0.8783, 0.8808, 0.9090, 0.8956, 0.5936, 0.7199, 0.5592])
FROZEN_MEAN = 0.8069

rows = []
with open(os.path.join(RES, "per_seed_metrics.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

def all_r(model):
    """per-seed mean Pearson r (the 'ALL' rows), in SEEDS order."""
    out = []
    for seed in SEEDS:
        for r in rows:
            if r["model"] == model and r["parameter"] == "ALL" and int(r["seed"]) == seed:
                out.append(float(r["pearson_r"]))
    return np.array(out)

def per_param_r(model):
    """dict param -> per-seed r array."""
    d = {p: [] for p in PARAMS9}
    for seed in SEEDS:
        for r in rows:
            if r["model"] == model and r["parameter"] in d and int(r["seed"]) == seed:
                d[r["parameter"]].append(float(r["pearson_r"]))
    return {p: np.array(v) for p, v in d.items()}

O = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); O.append(s)

P("# EXP1 Phase P/Q — model-outcome & leakage-effect analysis")
P("")
P("Frozen VAE-v6 reference (full-data scaling): per-param r = %s, mean = %.4f" % (
    ", ".join("%.3f" % v for v in FROZEN_R), FROZEN_MEAN))
P("")

R = {m: all_r(m) for m in MODELS}
P("## Per-seed mean Pearson r (across 9 parameters), test cohort")
P("%-8s %10s %8s %10s" % ("model", "mean_r", "sd_r", "min..max"))
for m in MODELS:
    P("%-8s %10.4f %8.4f %10.4f..%.4f" % (m, R[m].mean(), R[m].std(ddof=1), R[m].min(), R[m].max()))

P("")
P("## Phase P — outcome classification (descriptive; n=5 seeds/family)")
pair = {}
for a, b in [("vae", "det_ae"), ("vae", "mlp"), ("det_ae", "mlp")]:
    d = R[a] - R[b]
    w, pval = stats.wilcoxon(d) if not np.all(d == 0) else (float("nan"), 1.0)
    t, pvalt = stats.ttest_rel(R[a], R[b])
    pair[(a, b)] = dict(delta_mean=d.mean(), wilcoxon_p=pval, paired_t_p=pvalt)
    P("%s - %s: delta_mean_r = %+.4f  (Wilcoxon p=%.3f, paired-t p=%.3f)" %
      (a, b, d.mean(), pval, pvalt))

# Effect-size vs deterministic baselines (VAE advantage)
P("")
best_det = max(pair[("vae", "det_ae")]["delta_mean"], pair[("vae", "mlp")]["delta_mean"])
P("VAE vs best deterministic baseline: delta_mean_r = %+.4f" % best_det)
if pair[("vae", "det_ae")]["delta_mean"] > 0 and pair[("vae", "mlp")]["delta_mean"] > 0:
    if min(pair[("vae", "det_ae")]["delta_mean"], pair[("vae", "mlp")]["delta_mean"]) > 0.02:
        verdict = "A (VAE outperforms both matched deterministic baselines)"
    else:
        verdict = "B (VAE probabilistic advantage only — deterministic AE within ~0.02 of VAE)"
elif min(pair[("vae", "det_ae")]["delta_mean"], pair[("vae", "mlp")]["delta_mean"]) > -0.02 and \
     max(pair[("vae", "det_ae")]["delta_mean"], pair[("vae", "mlp")]["delta_mean"]) <= 0.02:
    verdict = "C (architectures comparable — framework remains the contribution)"
elif pair[("vae", "det_ae")]["delta_mean"] < -0.02 and pair[("vae", "mlp")]["delta_mean"] < -0.02:
    verdict = "D (deterministic baselines outperform VAE — reframe architectural claims)"
else:
    verdict = "mixed (VAE wins on one baseline, loses on the other)"
P("VERDICT: %s" % verdict)

P("")
P("## Phase Q — preprocessing-leakage effect (frozen vs leakage-free VAE)")
pr = per_param_r("vae")
deltas = {}
for i, p in enumerate(PARAMS9):
    d = pr[p].mean() - FROZEN_R[i]
    deltas[p] = d
    P("%-8s frozen %.4f -> lf-mean %.4f  delta %+.4f" % (p, FROZEN_R[i], pr[p].mean(), d))
overall = R["vae"].mean() - FROZEN_MEAN
P("")
P("overall delta_mean_r = %+.4f  (leakage-free mean %.4f vs frozen %.4f)" %
  (overall, R["vae"].mean(), FROZEN_MEAN))
ad = np.abs(overall)
if ad < 0.01:
    leak = "NEGLIGIBLE"
elif ad < 0.05:
    leak = "SMALL"
elif ad < 0.15:
    leak = "MODERATE"
else:
    leak = "MATERIAL"
P("LEAKAGE-EFFECT CLASSIFICATION (overall mean |delta_r|): %s" % leak)
worst_p = max(deltas, key=lambda k: abs(deltas[k]))
P("largest single-parameter delta: %s %+.4f" % (worst_p, deltas[worst_p]))

with open(os.path.join(RES, "PQ_analysis.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(O) + "\n")
print("\nwrote", os.path.join(RES, "PQ_analysis.md"))
