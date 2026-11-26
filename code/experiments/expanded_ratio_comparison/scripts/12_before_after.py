# -*- coding: utf-8 -*-
"""Before/after comparison of the v1 (buggy) and v2 (fixed) evaluation.

Reads the archived v1 metric table from out/metrics_v1/ and the v2 table from
out/metrics/, and writes

  before_after_metrics.csv     one row per model_arm/test_arm/seed/family/
                               quantity/metric with the v1 value, the v2 value
                               and their difference
  before_after_summary.csv     the same aggregated over the five seeds

The diagonal (model_arm == test_arm) must reproduce v1; the observed maximum
difference is reported and asserted below a strict tolerance.
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MET = os.path.join(ROOT, "out", "metrics")
V1 = os.path.join(ROOT, "out", "metrics_v1")
KEYS = ["test_arm", "model_arm", "seed", "family", "quantity"]
METRICS = ["pearson", "mae", "rmse", "r2_test", "skill_mse", "mae_reduction"]


def main():
    old = pd.read_csv(os.path.join(V1, "metrics_long.csv"))
    new = pd.read_csv(os.path.join(MET, "metrics_long.csv"))
    m = old[KEYS + METRICS].merge(new[KEYS + METRICS], on=KEYS,
                                  suffixes=("_v1", "_v2"))
    rows = []
    for r in m.itertuples(index=False):
        d = r._asdict()
        for c in METRICS:
            rows.append({
                "model_arm": d["model_arm"], "test_arm": d["test_arm"],
                "seed": d["seed"], "family": d["family"],
                "quantity": d["quantity"], "metric": c,
                "v1": d[c + "_v1"], "v2": d[c + "_v2"],
                "diff_v2_minus_v1": d[c + "_v2"] - d[c + "_v1"],
                "subset": ("diagonal" if d["model_arm"] == d["test_arm"]
                           else "cross"),
            })
    B = pd.DataFrame(rows)
    # stable column order
    B = B[["model_arm", "test_arm", "seed", "family", "quantity", "metric",
           "v1", "v2", "diff_v2_minus_v1", "subset"]]
    B.to_csv(os.path.join(MET, "before_after_metrics.csv"), index=False)

    S = (B.groupby(["subset", "model_arm", "test_arm", "family", "quantity",
                    "metric"], as_index=False)
         .agg(v1_mean=("v1", "mean"), v2_mean=("v2", "mean"),
              diff_mean=("diff_v2_minus_v1", "mean"),
              diff_sd=("diff_v2_minus_v1", "std"),
              n_seeds=("seed", "nunique")))
    S.to_csv(os.path.join(MET, "before_after_summary.csv"), index=False)

    diag = B[B.subset == "diagonal"]
    cross = B[B.subset == "cross"]
    dmax = float(diag.diff_v2_minus_v1.abs().max())
    print("diagonal rows:", len(diag), "max |v2 - v1| = %.3e" % dmax)
    print("cross rows:", len(cross), "max |v2 - v1| = %.3e"
          % float(cross.diff_v2_minus_v1.abs().max()))
    for t in ("original", "expanded"):
        g = cross[cross.test_arm == t]
        print("-- common %s test, mean over seeds --" % t)
        for c in ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]:
            for metric in ("skill_mse", "rmse"):
                h = g[(g.quantity == c) & (g.metric == metric)]
                if len(h):
                    print("  %-6s %-9s v1 %8.4f -> v2 %8.4f  (diff %+7.4f)"
                          % (c, metric, h.v1.mean(), h.v2.mean(),
                             h.diff_v2_minus_v1.mean()))
    if dmax > 1e-12:
        raise SystemExit("diagonal did not reproduce v1: %.3e" % dmax)


if __name__ == "__main__":
    main()
