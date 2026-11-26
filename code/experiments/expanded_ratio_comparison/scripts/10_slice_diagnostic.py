# -*- coding: utf-8 -*-
"""Auxiliary diagnostic (post-hoc, same predictions, no retraining).

On the common expanded-range test, score both models only on the rows whose
matching ratio coordinate lies inside the old 0.2-5 window.  This separates
"the expanded model is worse because it must extrapolate to extreme ratios"
from "the expanded model is worse everywhere".

No Skill/R2 is reported here: the slice has its own variance and a training
baseline for the slice would have to be re-derived, so raw RMSE and MAE are the
honest quantities.  Everything is recomputed from out/predictions.
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED = os.path.join(ROOT, "out", "predictions")
MET = os.path.join(ROOT, "out", "metrics")
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
PAIR = {"a_mu": ("mu_n", "mu_p"), "r_mu": ("mu_n", "mu_p"),
        "a_tau": ("tau_n", "tau_p"), "r_tau": ("tau_n", "tau_p"),
        "a_D": ("Nc", "Nv"), "r_D": ("Nc", "Nv")}
LO, HI = 0.2, 5.0

with open(os.path.join(ROOT, "config", "experiment_config.json"),
          encoding="utf-8") as f:
    SEEDS = json.load(f)["design"]["training_seeds"]

rows = []
for c in COORDS:
    n, lo_n = None, None
    for model_arm in ("original", "expanded"):
        for seed in SEEDS:
            df = pd.read_csv(os.path.join(
                PRED, "pred_%s_%d__on_expanded.csv" % (model_arm, seed)))
            a, b = PAIR[c]
            q = (10 ** df["true_log10_" + a]) / (10 ** df["true_log10_" + b])
            m = (q >= LO) & (q <= HI)
            err = df.loc[m, "pred_" + c] - df.loc[m, "true_" + c]
            rows.append({"subset": "q in [0.2,5] on expanded test",
                         "coordinate": c, "model_arm": model_arm,
                         "seed": seed, "n": int(m.sum()),
                         "rmse": float(np.sqrt(np.mean(err ** 2))),
                         "mae": float(np.mean(np.abs(err)))})

D = pd.DataFrame(rows)
S = (D.groupby(["subset", "coordinate", "model_arm"])
     .agg(n=("n", "first"), rmse_mean=("rmse", "mean"),
          rmse_sd=("rmse", "std"), mae_mean=("mae", "mean"),
          mae_sd=("mae", "std"), n_seeds=("seed", "nunique"))
     .reset_index())
S.to_csv(os.path.join(MET, "diagnostic_overlap_slice.csv"), index=False)
D.to_csv(os.path.join(MET, "diagnostic_overlap_slice_perseed.csv"), index=False)

print(S.to_string(index=False, float_format=lambda v: "%.4f" % v))
