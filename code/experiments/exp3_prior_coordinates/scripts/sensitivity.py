# -*- coding: utf-8 -*-
"""
EXP3 §12 — coordinate sensitivity to the J-V observable.

S_i = mean over the 131 voltages of |Pearson(coordinate_i, J(V))|
using the PHYSICAL J-V values of the same test set (frozen J_test_raw).
Coordinates are the TRUE log10-physical coordinates.

Output: results/coordinate_sensitivity.csv  (coordinate, sensitivity_S, recoverability_r)
Descriptive only — no significance claim with six points.
"""
import os, sys, csv
import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp3_lib import (EXP3, COORDS, coords_from_log10, frozen_test,
                      frozen_norm_to_log10)

RES = os.path.join(EXP3, "results")

t = frozen_test()
J_phys = t["J_test_raw"]                 # (15307, 131) physical mA/cm^2
L_true = frozen_norm_to_log10(t["params_test"])
C_true = coords_from_log10(L_true)       # (15307, 6)

rows = []
for ci, cname in enumerate(COORDS):
    coord = C_true[:, ci]
    s = np.mean([abs(pearsonr(coord, J_phys[:, v])[0]) for v in range(J_phys.shape[1])])
    rows.append((cname, s))
    print("%-5s  S = %.4f" % (cname, s))

with open(os.path.join(RES, "coordinate_sensitivity.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["coordinate", "sensitivity_S", "recoverability_r"])
    # read recoverability_r from the CSV we already produced
    with open(os.path.join(RES, "frozen_coordinate_recoverability.csv"), newline="") as fc:
        rd = {r["coordinate"]: float(r["pearson_r"]) for r in csv.DictReader(fc)}
    for cname, s in rows:
        w.writerow([cname, "%.6f" % s, "%.6f" % rd[cname]])
        print("  recoverability r = %.4f" % rd[cname])
print("saved coordinate_sensitivity.csv")
