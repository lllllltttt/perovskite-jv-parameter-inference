# -*- coding: utf-8 -*-
"""
EXP3 Phase 0 — reproduce the frozen Stage-I VAE-v6 test predictions
(Table 2 Pearson values, N = 15307). STOP if they cannot be reproduced.

Inference-only: forward pass through the frozen encoder + ParamHead at z_mean.
Writes FROZEN_PREDICTION_REPRODUCTION_CHECK.md in the EXP3 root.
"""
import os, sys, csv
import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp3_lib import (BASE, EXP3, PARAM_NAMES, frozen_test, frozen_norm_to_log10,
                      frozen_pred_log10)

OUT = os.path.join(EXP3, "FROZEN_PREDICTION_REPRODUCTION_CHECK.md")
L = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)

# reference from the frozen evaluation (evaluation_fixed/parameter_metrics.csv)
# column names in that file: mu_n_pvk ... Nc_eff_pvk/Nv_eff_pvk, tau_ETL, ...
_NAME_MAP = {"mu_n_pvk": "mu_n", "mu_p_pvk": "mu_p", "tau_n_pvk": "tau_n",
             "tau_p_pvk": "tau_p", "Nc_eff_pvk": "Nc", "Nv_eff_pvk": "Nv"}
REF = {}
with open(os.path.join(BASE, "evaluation_fixed", "parameter_metrics.csv"), newline="") as f:
    for r in csv.DictReader(f):
        key = _NAME_MAP.get(r["parameter"], r["parameter"])
        REF[key] = {"pearson": float(r["pearson_r"]), "mae": float(r["mae"]), "rmse": float(r["rmse"])}

P("# FROZEN PREDICTION REPRODUCTION CHECK (EXP3 Phase 0)")
P("")
P("Frozen Stage-I VAE-v6 z_mean point evaluation on the frozen test set.")
P("Reference: `evaluation_fixed/parameter_metrics.csv` (frozen evaluation pipeline).")
P("")

t = frozen_test()
P("Test N = %d  (required 15307) -> %s" % (t["params_test"].shape[0],
                                            "PASS" if t["params_test"].shape[0] == 15307 else "FAIL"))
P("")

pred_log10 = frozen_pred_log10()           # (N,9) log10 physical
true_log10 = frozen_norm_to_log10(t["params_test"])   # (N,9) log10 physical

# Pearson in log10 physical space == Pearson in normalized space (affine), and
# matches the frozen Table 2 values exactly.
P("| param | frozen ref | reproduced (log10 phys) | diff |")
P("|---|---|---|---|")
ok_all = True
pearson_list = []
for j, name in enumerate(PARAM_NAMES):
    r = pearsonr(true_log10[:, j], pred_log10[:, j])[0]
    pearson_list.append(r)
    ref = REF[name]["pearson"]
    d = abs(r - ref)
    ok = d < 1e-3
    ok_all &= ok
    P("| %-8s | %.4f | %.4f | %+.5f | %s |" % (name, ref, r, r - ref, "PASS" if ok else "FAIL"))
mean_r = float(np.mean(pearson_list))
mean_ref = float(np.mean([REF[n]["pearson"] for n in PARAM_NAMES]))
P("| **mean** | **%.4f** | **%.4f** | %+.5f | %s |" % (mean_ref, mean_r, mean_r - mean_ref,
                                                       "PASS" if abs(mean_r - mean_ref) < 1e-3 else "FAIL"))

P("")
P("## Spec reproduction targets")
P("")
targets = {"mu_n": 0.906, "mu_p": 0.919, "tau_n": 0.878, "tau_p": 0.881, "Nc": 0.909,
           "Nv": 0.896, "tau_ETL": 0.594, "tau_HTL": 0.720, "rad_c": 0.559}
P("| param | target | reproduced | ok |")
P("|---|---|---|---|")
for name, tg in targets.items():
    j = PARAM_NAMES.index(name)
    ok = abs(pearson_list[j] - tg) < 0.0015
    ok_all &= ok
    P("| %-8s | %.3f | %.4f | %s |" % (name, tg, pearson_list[j], "PASS" if ok else "FAIL"))
P("| **mean** | **0.807** | **%.4f** | %s |" % (mean_r, "PASS" if abs(mean_r - 0.807) < 0.001 else "FAIL"))

# inverse reconstruction QC (average, ratio) -> original paired log params
from exp3_lib import coords_from_log10, log10_from_coords
C_true = coords_from_log10(true_log10)
rec = log10_from_coords(C_true)
# rec has 6 cols (paired); compare to the 6 paired cols of true_log10
max_rec = np.abs(rec - true_log10[:, :6]).max()
P("")
P("## Inverse reconstruction QC ((a,r) -> paired log params)")
P("max |reconstructed - original| over the 6 paired log10 parameters = %.3e -> %s"
  % (max_rec, "PASS" if max_rec < 1e-9 else "FAIL"))
ok_all &= max_rec < 1e-9

P("")
P("## Verdict")
P("")
if ok_all:
    P("**PASS — frozen predictions reproduced (all |Δ| < 0.0015). Proceeding to the "
      "prior-coordinate analysis.**")
else:
    P("**FAIL — STOP. Do not continue with reconstructed or approximate predictions.**")
print("exit ok_all =", ok_all)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("saved:", OUT)
