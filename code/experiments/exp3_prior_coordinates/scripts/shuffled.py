# -*- coding: utf-8 -*-
"""
EXP3 §11 — shuffled-J pairing null control (sanity check only).

Permute the association between predicted and true test samples (same frozen
predictions, true targets randomly re-paired), seed 20260826, 100 permutations.
For each transformed coordinate report the null distribution of Pearson r.
A genuine sample-wise predictive association should sit far from this null.

Output: results/shuffled_pairing_null.csv
(columns: perm, a_mu, r_mu, a_tau, r_tau, a_D, r_D) + summary stats
"""
import os, sys, csv
import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp3_lib import (EXP3, COORDS, coords_from_log10, frozen_test,
                      frozen_norm_to_log10, frozen_pred_log10)

RES = os.path.join(EXP3, "results")
SEED = 20260826
N_PERM = 100

true_L = frozen_norm_to_log10(frozen_test()["params_test"])
pred_L = frozen_pred_log10()
C_true = coords_from_log10(true_L)
C_pred = coords_from_log10(pred_L)
N = true_L.shape[0]

rng = np.random.default_rng(SEED)
perms = np.zeros((N_PERM, 6))
for i in range(N_PERM):
    idx = rng.permutation(N)
    for ci in range(6):
        perms[i, ci] = pearsonr(C_true[:, ci], C_pred[idx, ci])[0]

# summary
print("shuffled-J null distribution of Pearson r (mean +/- SD):")
with open(os.path.join(RES, "shuffled_pairing_null.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["perm"] + COORDS)
    for i in range(N_PERM):
        w.writerow([i] + ["%.6f" % v for v in perms[i]])
    # append summary rows
    w.writerow(["summary_mean"] + ["%.6f" % perms[:, ci].mean() for ci in range(6)])
    w.writerow(["summary_sd"] + ["%.6f" % perms[:, ci].std() for ci in range(6)])
    w.writerow(["summary_p95"] + ["%.6f" % np.percentile(perms[:, ci], 95) for ci in range(6)])

print("null mean:  ", ["%.4f" % perms[:, ci].mean() for ci in range(6)])
print("null sd:    ", ["%.4f" % perms[:, ci].std() for ci in range(6)])
print("null p95:   ", ["%.4f" % np.percentile(perms[:, ci], 95) for ci in range(6)])
# observed
obs = [pearsonr(C_true[:, ci], C_pred[:, ci])[0] for ci in range(6)]
print("observed r: ", ["%.4f" % o for o in obs])
print("saved shuffled_pairing_null.csv")
