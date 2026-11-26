# -*- coding: utf-8 -*-
"""
fig3_case_analysis.py — corrected nine-parameter case analysis for Figure 3(d).
================================================================================
Fixes and verifies the defect the review found in fig3_sketch.py panel (d):

  BUG (v1):  vals[q] = abs(np.log10(L[i, q] / L[j, q]))   with L = log10(raw)
             i.e. log10 of a ratio OF LOGARITHMS. Not a log-ratio.
  FIX (v2):  vals[q] = abs(L[i, q] - L[j, q]) = |log10(theta_i / theta_j)|

  BUG (v1):  bars plotted param 0..8 against tick labels param 8..0, so eight
             of the nine labels sat against the wrong parameter.
  FIX (v2):  value and label are taken from the same index.

Verification performed here (all against the raw physical parameters, not
against any intermediate):
  1. |L_i - L_j| vs |log10(theta_i/theta_j)| computed straight from raw values.
  2. all 18 parameter differences (2 cases x 9) listed individually.
  3. the corrected single-parameter differences are reconciled with the paired
     coordinate differences a and r by exact algebraic identity.
  4. physical-current residual J_j - J_i, its RMSE and max|dJ|, in mA cm^-2.

Read-only on the frozen project; writes only inside this v2 directory.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_v2 as L
import figstyle as st

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")
os.makedirs(DATADIR, exist_ok=True)

# test index -> global Sample_ID, from the frozen working copy whose idx_test
# reproduces params_test_raw / J_test_raw bit-exactly (checked below).
SID_NPZ = os.path.join(L.BASE, "supplementary_validation_v4", "T2_control",
                       "_data_physical.npz")


def sample_ids(test_indices):
    z = np.load(SID_NPZ, allow_pickle=True)
    d = np.load(L.DATA_NPZ)
    f = np.load(L.FROZEN_NPZ)
    idx = z["idx_test"]
    # the mapping is only trustworthy if it reproduces the frozen arrays exactly
    assert np.array_equal(z["params_phys"][idx], f["params_test_raw"]), \
        "idx_test does not reproduce params_test_raw"
    assert np.array_equal(z["J_phys"][idx], f["J_test_raw"]), \
        "idx_test does not reproduce J_test_raw"
    sid = z["Sample_ID"]
    return {int(t): int(sid[idx[t]]) for t in test_indices}


def main():
    F = L.load_frozen()
    Lg, raw, J, V = F["L"], F["raw"], F["J"], F["V"]

    # ---- random-pair baseline medians, recomputed here with seed 42 --------
    ra, rb = L.random_pairs(len(Lg))
    R = {}
    Ca = L.coordinates(Lg)
    for cid, fam, p, q in L.COORDS:
        col = L.COORD_IDS.index(cid)
        R[cid] = float(np.median(np.abs(Ca[ra, col] - Ca[rb, col])))
    dJ_rand = np.sqrt(np.mean((F["Jn"][ra] - F["Jn"][rb]) ** 2, axis=1))
    R["dJ_rmse"] = float(np.median(dJ_rand))

    unit_df = L.verify_units(raw)
    unit_df.to_csv(os.path.join(DATADIR, "unit_basis_check.csv"), index=False)
    print("[units] all nine columns lie inside their Table 1 sampling bounds:",
          bool(unit_df["inside_bounds"].all()))

    tids = [t for _tag, i, j, _w in L.CASES for t in (i, j)]
    SID = sample_ids(tids)

    # ======================================================================
    # 1-2. nine parameters per case, corrected values, verification
    # ======================================================================
    prows, crows = [], []
    for tag, i, j, why in L.CASES:
        dL = Lg[i] - Lg[j]                     # signed, per parameter
        for q, name in enumerate(L.PARAM_NAMES):
            theta_i, theta_j = raw[i, q], raw[j, q]
            # (1) independent recomputation straight from the raw values
            direct = abs(np.log10(theta_i / theta_j))
            fixed = abs(dL[q])
            v1_err = abs(np.log10(Lg[i, q] / Lg[j, q]))   # the v1 defect
            prows.append(dict(
                case=tag, selection=why,
                test_index_i=i, test_index_j=j,
                sample_id_i=SID[i], sample_id_j=SID[j],
                parameter=name, unit=L.PARAM_UNITS_PLAIN[q],
                theta_i=theta_i, theta_j=theta_j,
                log10_theta_i=Lg[i, q], log10_theta_j=Lg[j, q],
                signed_delta_log10=dL[q],
                abs_delta_log10=fixed,
                abs_log10_ratio_direct=direct,
                abs_diff=fixed - direct,
                v1_erroneous_value=v1_err,
                v1_ratio_to_correct=(v1_err / fixed) if fixed else np.nan))
        # (3) reconcile with the paired coordinates: exact identities
        rows = []
        for fam, p, q in (("mobility", 0, 1), ("lifetime", 2, 3), ("DOS", 4, 5)):
            da = 0.5 * (dL[p] + dL[q])
            dr = dL[p] - dL[q]
            rows.append((fam, dL[p], dL[q], da, dr))
            crows.append(dict(
                case=tag, family=fam,
                test_index_i=i, test_index_j=j,
                coord_a_i=0.5 * (Lg[i, p] + Lg[i, q]),
                coord_a_j=0.5 * (Lg[j, p] + Lg[j, q]),
                coord_r_i=Lg[i, p] - Lg[i, q],
                coord_r_j=Lg[j, p] - Lg[j, q],
                delta_a=da, delta_r=dr,
                absd_a=abs(da), absd_r=abs(dr),
                norm_absd_a=abs(da) / R["a_" + {"mobility": "mu", "lifetime": "tau", "DOS": "D"}[fam]],
                norm_absd_r=abs(dr) / R["r_" + {"mobility": "mu", "lifetime": "tau", "DOS": "D"}[fam]]))
        for fam, dl_p, dl_q, da, dr in rows:
            assert abs(dr - (dl_p - dl_q)) < 1e-12
            assert abs(da - 0.5 * (dl_p + dl_q)) < 1e-12

    P = pd.DataFrame(prows)
    C = pd.DataFrame(crows)

    # (2) the 18 differences, printed one by one
    print("\n" + "=" * 96)
    print("all 18 parameter differences (2 cases x 9 parameters), corrected")
    print("=" * 96)
    for tag, i, j, _why in L.CASES:
        sub = P[P["case"] == tag]
        print("\n  %s  test index %d / %d  (Sample_ID %d / %d)"
              % (tag, i, j, SID[i], SID[j]))
        print("  %-12s %-14s %11s %11s %11s %11s"
              % ("parameter", "unit", "log10_i", "log10_j",
                 "|dlog10|", "v1_wrong"))
        for _, r in sub.iterrows():
            print("  %-12s %-14s %11.5f %11.5f %11.5f %11.5f"
                  % (r["parameter"], r["unit"], r["log10_theta_i"],
                     r["log10_theta_j"], r["abs_delta_log10"],
                     r["v1_erroneous_value"]))
    print("\n  max |direct - corrected| over all 18: %.3e"
          % P["abs_diff"].abs().max())
    assert P["abs_diff"].abs().max() < 1e-12

    print("\n  v1 defect magnitude (v1_wrong / corrected), per case:")
    for tag, _i, _j, _w in L.CASES:
        s = P[P["case"] == tag]
        print("     %s: ratio %.2f .. %.2f  (median %.2f)"
              % (tag, s["v1_ratio_to_correct"].min(),
                 s["v1_ratio_to_correct"].max(),
                 s["v1_ratio_to_correct"].median()))
        print("        argmax parameter: v1 -> %s | corrected -> %s"
              % (s.loc[s["v1_erroneous_value"].idxmax(), "parameter"],
                 s.loc[s["abs_delta_log10"].idxmax(), "parameter"]))

    print("\n  reconciliation with paired coordinates (exact identity):")
    for _, r in C.iterrows():
        print("     %s %-9s  d_a=%+.6f  d_r=%+.6f  |d_a|=%.4f |d_r|=%.4f"
              "   norm |d_a|=%.3f |d_r|=%.3f"
              % (r["case"], r["family"], r["delta_a"], r["delta_r"],
                 r["absd_a"], r["absd_r"], r["norm_absd_a"], r["norm_absd_r"]))

    # ======================================================================
    # 4. physical current residual, J_j - J_i, mA cm^-2
    # ======================================================================
    print("\n" + "=" * 96)
    print("physical current residual  dJ = J_j - J_i   (mA cm^-2)")
    print("=" * 96)
    curve_frames, srows = [], []
    for tag, i, j, why in L.CASES:
        dJ = J[j] - J[i]
        rmse = float(np.sqrt(np.mean(dJ ** 2)))
        mx = float(np.abs(dJ).max())
        k = int(np.argmax(np.abs(dJ)))
        curve_frames.append(pd.DataFrame(dict(
            case=tag, test_index_i=i, test_index_j=j,
            sample_id_i=SID[i], sample_id_j=SID[j],
            voltage_V=V, J_i_mA_cm2=J[i], J_j_mA_cm2=J[j],
            residual_Jj_minus_Ji_mA_cm2=dJ)))
        srows.append(dict(case=tag, test_index_i=i, test_index_j=j,
                          sample_id_i=SID[i], sample_id_j=SID[j],
                          selection=why,
                          dJ_rmse_normalized=float(
                              np.sqrt(np.mean((F["Jn"][i] - F["Jn"][j]) ** 2))),
                          physical_rmse_mA_cm2=rmse,
                          max_abs_dJ_mA_cm2=mx,
                          max_abs_dJ_at_V=float(V[k]),
                          J_i_at_0V=float(J[i, 0]), J_j_at_0V=float(J[j, 0]),
                          J_i_min=float(J[i].min()), J_j_min=float(J[j].min()),
                          J_i_max=float(J[i].max()), J_j_max=float(J[j].max()),
                          residual_at_0V=float(dJ[0]),
                          residual_at_max_V=float(dJ[-1])))
        print("  %s  i=%d j=%d (Sample_ID %d / %d)"
              % (tag, i, j, SID[i], SID[j]))
        print("     RMSE = %.4f mA cm^-2   max|dJ| = %.4f mA cm^-2 at V = %.2f V"
              % (rmse, mx, V[k]))
        print("     J_i: %.3f .. %.3f    J_j: %.3f .. %.3f  mA cm^-2"
              % (J[i].min(), J[i].max(), J[j].min(), J[j].max()))
        print("     residual at V=0: %+.4f   at V=1.30: %+.4f  mA cm^-2"
              % (dJ[0], dJ[-1]))
    S = pd.DataFrame(srows)

    # ---- other parameters change simultaneously ---------------------------
    print("\n  how many of the nine parameters differ in each case "
          "(|dlog10| > 0.01):")
    for tag, _i, _j, _w in L.CASES:
        s = P[P["case"] == tag]
        n = int((s["abs_delta_log10"] > 0.01).sum())
        print("     %s: %d of 9   (largest |dlog10| = %.3f on %s)"
              % (tag, n, s["abs_delta_log10"].max(),
                 s.loc[s["abs_delta_log10"].idxmax(), "parameter"]))

    # ---- write ------------------------------------------------------------
    P.to_csv(os.path.join(DATADIR, "fig3_case_parameters.csv"), index=False)
    C.to_csv(os.path.join(DATADIR, "fig3_case_coordinates.csv"), index=False)
    pd.concat(curve_frames, ignore_index=True).to_csv(
        os.path.join(DATADIR, "fig3_case_curves.csv"), index=False)
    S.to_csv(os.path.join(DATADIR, "fig3_case_summary.csv"), index=False)
    P[["case", "parameter", "unit", "theta_i", "theta_j",
       "log10_theta_i", "log10_theta_j", "abs_delta_log10",
       "abs_log10_ratio_direct", "abs_diff", "v1_erroneous_value"]].to_csv(
        os.path.join(DATADIR, "fig3_case_parameter_check.csv"), index=False)
    print("\nwrote: fig3_case_parameters.csv, fig3_case_coordinates.csv,")
    print("       fig3_case_curves.csv, fig3_case_summary.csv,")
    print("       fig3_case_parameter_check.csv, unit_basis_check.csv")


if __name__ == "__main__":
    main()
