# -*- coding: utf-8 -*-
"""Summarise the 1,000 random-subset replicates.

The 2.5th/97.5th percentiles are *descriptive resampling percentile ranges*
across subset replicates.  They are not confidence intervals and not a
bootstrap CI for the original 15,307-curve statistic.
"""
import json
import os

import numpy as np
import pandas as pd

BASE = r"E:\project\work1"
STAB = os.path.join(BASE, "20261019_NN_stability", "out", "stability")
REP = os.path.join(BASE, "20261019_NN_stability", "out", "reproduction")
OUT = STAB

COORD_IDS = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
FAMILIES = [("mobility", "a_mu", "r_mu"),
            ("lifetime", "a_tau", "r_tau"),
            ("DOS", "a_D", "r_D")]
SETS = [("all", "all corrected pairs"),
        ("t10", "closest 10%"), ("t5", "closest 5%"),
        ("t1", "closest 1%"), ("t05", "closest 0.5%"),
        ("t01", "closest 0.1%")]


def q(x, p):
    return float(np.percentile(np.asarray(x, float), p))


def main():
    df = pd.read_csv(os.path.join(STAB, "per_replicate.csv"))
    assert df["rep"].tolist() == list(range(1, len(df) + 1)), "non-consecutive reps"
    n_reps = len(df)
    s6 = pd.read_csv(os.path.join(REP, "s6_reproduced.csv")).set_index("set")
    rb = pd.read_csv(os.path.join(REP, "random_baseline_check.csv")).set_index(
        "coordinate")
    with open(os.path.join(REP, "reproduction_check.json"), encoding="utf-8") as fh:
        paircheck = json.load(fh)["pair_set"]

    orig = {}
    orig["n_unique"] = 15307
    orig["n_pairs"] = 11245
    orig["n_directed"] = paircheck["directed_links"]
    orig["n_mutual"] = paircheck["mutual_nearest_pairs"]
    for tag, s6tag in SETS:
        r = s6.loc[s6tag]
        orig["n_" + tag] = int(r["n_pairs"])
        orig["median_dJ_" + tag] = float(r["median_dJ"])
        for cid in COORD_IDS:
            orig["absd_%s_%s" % (tag, cid)] = float(r["median_absd_" + cid])
            orig["norm_%s_%s" % (tag, cid)] = float(r["median_norm_" + cid])
    orig["distinct_all"] = int(s6.loc["all corrected pairs", "distinct_samples"])
    orig["multi_all"] = int(s6.loc["all corrected pairs",
                                   "samples_in_multiple_pairs"])
    orig["max_all"] = int(s6.loc["all corrected pairs", "max_pairs_per_sample"])
    orig["distinct_t01"] = int(s6.loc["closest 0.1%", "distinct_samples"])
    orig["multi_t01"] = int(s6.loc["closest 0.1%",
                                   "samples_in_multiple_pairs"])
    orig["max_t01"] = int(s6.loc["closest 0.1%", "max_pairs_per_sample"])
    for cid in COORD_IDS:
        orig["rand_" + cid] = float(rb.loc[cid, "median_absd_random"])

    order = ["n_unique", "n_pairs", "n_directed", "n_mutual",
             "distinct_all", "multi_all", "max_all",
             "distinct_t01", "multi_t01", "max_t01"]
    order += ["n_" + tag for tag, _ in SETS if tag != "all"]
    order += ["rand_" + cid for cid in COORD_IDS]
    for tag, _ in SETS:
        order += ["median_dJ_" + tag]
        order += ["absd_%s_%s" % (tag, cid) for cid in COORD_IDS]
        order += ["norm_%s_%s" % (tag, cid) for cid in COORD_IDS]

    rows = []
    for k in order:
        x = df[k].values
        rows.append(dict(quantity=k,
                         original=orig.get(k, np.nan),
                         rep_median=float(np.median(x)),
                         p2_5=q(x, 2.5),
                         p97_5=q(x, 97.5),
                         rep_min=float(np.min(x)),
                         rep_max=float(np.max(x)),
                         n_reps=n_reps))
    summary = pd.DataFrame(rows)
    summary.to_csv(os.path.join(OUT, "summary.csv"), index=False)

    # ----------------------------------------- first 500 vs all 1000 --------
    cmp_rows = []
    half = df.iloc[:500]
    for k in order:
        x5, xa = half[k].values, df[k].values
        cmp_rows.append(dict(
            quantity=k,
            n_reps_first500=len(x5), median_first500=float(np.median(x5)),
            p2_5_first500=q(x5, 2.5), p97_5_first500=q(x5, 97.5),
            n_reps_all=len(xa), median_all=float(np.median(xa)),
            p2_5_all=q(xa, 2.5), p97_5_all=q(xa, 97.5),
            d_median=float(np.median(xa) - np.median(x5)),
            d_p2_5=q(xa, 2.5) - q(x5, 2.5),
            d_p97_5=q(xa, 97.5) - q(x5, 97.5)))
    pd.DataFrame(cmp_rows).to_csv(
        os.path.join(OUT, "first500_vs_all1000.csv"), index=False)

    # --------------------------------------------- family interpretation ----
    irows = []
    for tag, s6tag in SETS:
        for fam, ca, cr in FAMILIES:
            a = df["norm_%s_%s" % (tag, ca)].values
            r = df["norm_%s_%s" % (tag, cr)].values
            diff = a - r
            irows.append(dict(
                pair_set=tag, family=fam,
                original_norm_a=orig["norm_%s_%s" % (tag, ca)],
                original_norm_r=orig["norm_%s_%s" % (tag, cr)],
                rep_median_norm_a=float(np.median(a)),
                rep_median_norm_r=float(np.median(r)),
                rep_median_a_minus_r=float(np.median(diff)),
                a_minus_r_p2_5=q(diff, 2.5),
                a_minus_r_p97_5=q(diff, 97.5),
                frac_reps_a_lt_r=float(np.mean(a < r)),
                n_reps=n_reps))
    pd.DataFrame(irows).to_csv(os.path.join(OUT, "interpretation_by_family.csv"),
                               index=False)

    all_rows = []
    for tag, _ in SETS:
        ok = np.ones(n_reps, dtype=bool)
        for fam, ca, cr in FAMILIES:
            ok &= (df["norm_%s_%s" % (tag, ca)].values
                   < df["norm_%s_%s" % (tag, cr)].values)
        all_rows.append(dict(pair_set=tag,
                             frac_reps_all_three_a_lt_r=float(np.mean(ok)),
                             n_reps=n_reps))
    pd.DataFrame(all_rows).to_csv(
        os.path.join(OUT, "interpretation_all_three.csv"), index=False)

    # ------------------------------------------- closest 0.1% volatility ----
    vrows = []
    for k in ["n_t01", "distinct_t01", "multi_t01", "max_t01"] + \
             ["norm_t01_" + c for c in COORD_IDS]:
        x = df[k].values
        vrows.append(dict(quantity=k, original=orig.get(k, np.nan),
                          median=float(np.median(x)), p2_5=q(x, 2.5),
                          p97_5=q(x, 97.5), minimum=float(np.min(x)),
                          maximum=float(np.max(x)), n_reps=n_reps))
    pd.DataFrame(vrows).to_csv(os.path.join(OUT, "closest01_volatility.csv"),
                               index=False)

    meta = dict(n_reps=n_reps, seed_base=20261019,
                random_pair_seed=42,
                analysis="random-subset stability analysis with duplicate collapse",
                percentile_note=("2.5th/97.5th percentiles are descriptive "
                                 "resampling percentile ranges, not confidence "
                                 "intervals"))
    with open(os.path.join(OUT, "summary_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(summary.to_string(index=False))
    print("\nfirst-500 vs all-1000 max |d median|: %.6g"
          % np.max(np.abs(pd.DataFrame(cmp_rows)["d_median"])))
    print("all-three a<r by set:")
    print(pd.DataFrame(all_rows).to_string(index=False))


if __name__ == "__main__":
    main()
