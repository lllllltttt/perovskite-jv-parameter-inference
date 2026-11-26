# -*- coding: utf-8 -*-
"""Emit the numbers quoted in RESULTS.md, straight from the metric tables."""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MET = os.path.join(ROOT, "out", "metrics")
COORDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]


def ms(S, test_arm, model_arm, family, q, metric):
    r = S[(S["test_arm"] == test_arm) & (S["model_arm"] == model_arm) &
          (S["family"] == family) & (S["quantity"] == q) &
          (S["metric"] == metric)]
    return float(r["mean"].iloc[0]), float(r["sd"].iloc[0])


def main():
    S = pd.read_csv(os.path.join(MET, "summary_mean_sd.csv"))
    P = pd.read_csv(os.path.join(MET, "paired_difference_summary.csv"))
    B = pd.read_csv(os.path.join(MET, "table_B_common_tests.csv"))

    print("\n=== TABLE A (own distribution), coordinates ===")
    for c in COORDS:
        for m in ("skill_mse", "rmse", "mae", "pearson", "r2_test"):
            a = ms(S, "original", "original", "coordinate", c, m)
            b = ms(S, "expanded", "expanded", "coordinate", c, m)
            print("%-6s %-12s orig %8.4f ± %.4f | exp %8.4f ± %.4f"
                  % (c, m, a[0], a[1], b[0], b[1]))

    print("\n=== TABLE A, nine parameters (skill/rmse) ===")
    for q in sorted(S[S["family"] == "parameter"]["quantity"].unique()):
        for m in ("skill_mse", "rmse"):
            a = ms(S, "original", "original", "parameter", q, m)
            b = ms(S, "expanded", "expanded", "parameter", q, m)
            print("%-12s %-10s orig %8.4f ± %.4f | exp %8.4f ± %.4f"
                  % (q, m, a[0], a[1], b[0], b[1]))

    print("\n=== TABLE B paired differences (expanded - original) ===")
    for t in ("original", "expanded"):
        for fam in ("coordinate", "parameter"):
            sub = P[(P["test_arm"] == t) & (P["family"] == fam)]
            for q in sub["quantity"].unique():
                r = sub[(sub["quantity"] == q) &
                        (sub["metric"] == "skill_mse")]
                d = float(r["mean_diff"].iloc[0])
                sd = float(r["sd_diff"].iloc[0])
                pos = int(r["n_positive"].iloc[0])
                neg = int(r["n_negative"].iloc[0])
                print("%-8s %-5s %-12s dSkill %+7.4f (sd %.4f) +%d/-%d"
                      % (t, fam[:3], q, d, sd, pos, neg))

    print("\n=== TABLE B raw values on the common tests ===")
    for t in ("original", "expanded"):
        print("-- common %s test --" % t)
        for c in COORDS:
            g = B[(B["test_arm"] == t) & (B["family"] == "coordinate") &
                  (B["quantity"] == c)]
            for ma in ("original", "expanded"):
                h = g[g["model_arm"] == ma]
                print("%-6s %-8s skill %7.4f±%.4f  rmse %7.4f  mae %7.4f  "
                      "baseMSE %8.4f"
                      % (c, ma, h["skill_mse"].mean(), h["skill_mse"].std(ddof=1),
                         h["rmse"].mean(), h["mae"].mean(),
                         (h["sse_train_mean"] / h["n"]).mean()))

    print("\n=== per-seed spread (min..max) of Skill, coordinates ===")
    for t, ma in (("original", "original"), ("expanded", "expanded")):
        for c in COORDS:
            for m in ("skill_mse",):
                r = S[(S["test_arm"] == t) & (S["model_arm"] == ma) &
                      (S["family"] == "coordinate") & (S["quantity"] == c) &
                      (S["metric"] == m)].iloc[0]
                print("%-8s %-6s %-10s %7.4f .. %7.4f (mean %.4f)"
                      % (t, c, m, r["min"], r["max"], r["mean"]))


if __name__ == "__main__":
    main()
