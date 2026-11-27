# -*- coding: utf-8 -*-
"""Reproduce the source-provenance checks in docs/SOURCE_VERIFICATION.md.

    python code/verify_source_provenance.py \
        --design PSC_LHS_9D_interface_lifetimes_300000_5.csv \
        --retained JV_database_9D_interface_lifetimes-3.csv
    python code/verify_source_provenance.py \
        --design PSC_LHS_9D_interface_lifetimes_200000_3.csv \
        --retained JV_database_9D_interface_lifetimes-2.csv

Checks performed
  1. Sample_ID is 1..n, unique and increasing (design file);
  2. the nine constructed parameters are finite and positive (design file);
  3. every retained Sample_ID has a design row (inner join count);
  4. every retained value equals the design value rounded to three significant
     digits, with the mismatch count and the maximum relative difference
     reported.  Ties at the fourth digit are reported but do not fail: the CSV
     writer rounded half up, ``numpy.round`` rounds half to even.

Exit code 0 when checks 1-3 pass and check 4 shows every value within half of
the last stored digit (relative 5e-3).
"""
import argparse
import sys

import numpy as np
import pandas as pd

PARAMS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
          "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
# older design files name the interface lifetimes differently
ALIASES = {"tau_ETL": ("tau_ETL", "tau_interface_ETL"),
           "tau_HTL": ("tau_HTL", "tau_interface_HTL")}


def sig3(x):
    x = np.asarray(x, float)
    e = np.floor(np.log10(x)) - 2
    return np.round(x / 10.0 ** e) * 10.0 ** e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--retained", required=True)
    a = ap.parse_args()

    d = pd.read_csv(a.design)
    fails = []

    sid = d["Sample_ID"].to_numpy()
    ok_id = (len(np.unique(sid)) == len(sid) and sid.min() == 1
             and sid.max() == len(sid) and np.all(np.diff(sid) > 0))
    print(f"design rows {len(d)}, columns {len(d.columns)}")
    print(f"Sample_ID 1..n, unique, increasing: {ok_id}")
    if not ok_id:
        fails.append("Sample_ID sequence")

    cols = {}
    for p in PARAMS:
        name = next((c for c in ALIASES.get(p, (p,)) if c in d.columns), None)
        if name is None:
            print(f"  {p}: column missing in the design file")
            fails.append(f"missing column {p}")
            continue
        cols[p] = name

    print("\nconstructed parameters (design file):")
    for p, name in cols.items():
        v = d[name].to_numpy(float)
        finite = bool(np.all(np.isfinite(v)))
        pos = bool(np.all(v > 0))
        print(f"  {p:12s} finite={finite} positive={pos} "
              f"min={v.min():.4e} max={v.max():.4e}")
        if not (finite and pos):
            fails.append(f"{p} not finite/positive")

    r = pd.read_csv(a.retained, usecols=["Sample_ID"] + PARAMS)
    print(f"\nretained rows {len(r)}")
    dd = d[["Sample_ID"] + [cols[p] for p in PARAMS]].rename(
        columns={cols[p]: p for p in PARAMS})
    m = r.merge(dd, on="Sample_ID", how="left", suffixes=("_ret", "_des"))
    missing = int(m[[p + "_des" for p in PARAMS]].isna().any(axis=1).sum())
    print(f"joined {len(m)} of {len(r)}; rows without a design match: {missing}")
    if missing:
        fails.append(f"{missing} retained rows without a design row")

    print(f"\n{'param':12s} {'max rel':>10s} {'<5e-3':>8s} {'sig3-exact':>11s}")
    for p in PARAMS:
        x = m[p + "_ret"].to_numpy(float)
        y = m[p + "_des"].to_numpy(float)
        good = np.isfinite(x) & np.isfinite(y)
        rel = np.abs(x[good] - y[good]) / np.abs(y[good])
        exact = int(np.isclose(sig3(y[good]), x[good], rtol=1e-12, atol=0).sum())
        within = int((rel <= 5e-3).sum())
        print(f"{p:12s} {rel.max():10.2e} {within:>5d}/{len(rel):<3d} "
              f"{exact:>6d}/{len(rel):<3d}")
        if within != len(rel):
            fails.append(f"{p}: {len(rel) - within} values outside 3-s.f. rounding")

    if fails:
        print("\nFAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("\nPASS: every retained row matches the design table to three "
          "significant digits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
