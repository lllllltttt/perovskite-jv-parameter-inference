# -*- coding: utf-8 -*-
"""
e2v3_mesh_convergence.py -- E2-v3 task #4 FORWARD mesh-convergence analysis.

Questions (section 4 of the v3 plan), answered on the NEW m=0.18 / m=0.125 solves
plus the existing m=0.35 / m=0.25 fine curves for the SAME six reps, all stol=1e-6:
  1. Do the device metrics (Voc / Jsc / Pmax / FF / PCE) converge between adjacent
     refinement grades m0.25->m0.18->m0.125?
     criteria: |dV_oc|<=2 mV ; |dJsc|<=0.05% ; |dPmax|<=0.1%  (relative, adjacent).
  2. Does the <=1 V (generation) curve segment converge between adjacent grades?
     criterion: adjacent-segment RMSE <= 0.05-0.1 mA/cm2.
  3. Does the >1 V (>Voc) segment converge?
     reported as RMSE + RMSE/denominator + quantiles (denominator explicitly given);
     absolute tolerance does NOT apply to this segment.
  4. Overall forward verdict for the fine chain; if the LAST two grades fail any
     criterion, that quantity is reported as "convergence not established within
     this round's budget" (NOT "all meshes fail", no extra solves, no retrain).
All three curve families (mesh grades) share the SAME physical params and solver
tolerance; only the mesh differs (three reference types are never mixed here).
"""
import os, glob, re, json
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_tools"))
import v2lib
from v2lib import V, device_metrics

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(TASK, "outputs"); TAB = os.path.join(OUT, "tables")
FIG  = os.path.join(OUT, "figures"); PROV = os.path.join(TASK, "_work")
for _d in (OUT, TAB, FIG, PROV):
    os.makedirs(_d, exist_ok=True)

V2D = r"E:\project\work1\supplementary_validation_v2\E2_mesh_and_inference\outputs\curves"
V3D = r"E:\project\work1\supplementary_validation_v3\E2_finemesh\outputs\curves"
NPZ = r"E:\project\work1\data\dataset_normalized.npz"

# criteria (section 4)
CR = dict(dVoc_mV=2.0, dJsc_pct=0.05, dPmax_pct=0.10, rmse_le1=0.10, rmse_le1_tight=0.05)

def load_curves(curdir):
    rows = []
    for f in sorted(glob.glob(os.path.join(curdir, "row_*.csv"))):
        with open(f, encoding="utf-8", errors="replace") as fh:
            hdr = fh.readline().strip().lstrip("# ").strip()
            body = fh.read().split()
        meta = dict(re.findall(r"(\w+)=([^,]+)", hdr))
        if meta.get("status", "ok") != "ok" or len(body) != len(V):
            continue
        rows.append(dict(rowid=int(meta["rowid"]), test_index=int(meta["test_index"]),
                         level=meta.get("level", ""),
                         mesh=float(meta.get("mesh_size_factor", 1.0)),
                         stol=float(meta.get("stol", 1e-6)),
                         nelem=int(meta.get("nelem", -1)),
                         J=np.asarray(body, np.float64) * v2lib.AM2))  # -> mA/cm2
    return pd.DataFrame(rows)

fine = pd.concat([load_curves(V2D), load_curves(V3D)])
# keep only the four fine grades at stol=1e-6 (mesh-only, one reference type)
fine = fine[(np.isclose(fine.stol, 1e-6)) & (fine.level.isin(
    ["m0.35", "m0.25", "m0.18", "m0.125"]))].copy()
print("fine curves loaded: %d  (6 reps x 4 grades expected)" % len(fine))
assert fine.groupby("test_index")["level"].nunique().eq(4).all()

npz = np.load(NPZ, allow_pickle=True)

def dm(J):
    return device_metrics(np.asarray(J, np.float64), voc_mode="interp")

recs = []
for _, r in fine.iterrows():
    d = dm(r.J)
    Jt = npz["J_test_raw"][r.test_index].astype(np.float64)
    le1 = V <= 1.0
    rmse_full = float(np.sqrt(np.mean((r.J - Jt) ** 2)))
    rmse_le1 = float(np.sqrt(np.mean((r.J[le1] - Jt[le1]) ** 2)))
    gt1 = ~le1
    rmse_gt1 = float(np.sqrt(np.mean((r.J[gt1] - Jt[gt1]) ** 2)))
    recs.append(dict(test_index=int(r.test_index), level=r.level, mesh=r.mesh,
                     nelem=int(r.nelem), rowid=int(r.rowid),
                     Jsc=d["Jsc"], Voc=d["Voc"], Vmp=d["Vmp"], Pmax=d["Pmax"],
                     FF=d["FF"], PCE=d["PCE"],
                     rmse_full=rmse_full, rmse_le1=rmse_le1, rmse_gt1=rmse_gt1,
                     mean_abs_J_gt1=float(np.mean(np.abs(r.J[gt1]))),
                     Jt_voc=dm(Jt)["Voc"]))
cur = pd.DataFrame(recs)
cur.to_csv(os.path.join(TAB, "e2v3_finemesh_curve_metrics.csv"), index=False)

# ---------------- adjacent-grade deltas ------------------------------------
order = ["m0.35", "m0.25", "m0.18", "m0.125"]
pairs = [(order[i], order[i + 1]) for i in range(len(order) - 1)]
adj = []
for ti, g in cur.groupby("test_index"):
    g = g.set_index("level")
    for c, f_ in pairs:
        a, b = g.loc[c], g.loc[f_]
        # device-metric deltas (relative for Jsc/Pmax, absolute for Voc)
        dVoc = (b.Voc - a.Voc) * 1000.0                      # mV
        dJsc_pct = abs(b.Jsc - a.Jsc) / max(abs(a.Jsc), 1e-12) * 100.0
        dPmax_pct = abs(b.Pmax - a.Pmax) / max(abs(a.Pmax), 1e-12) * 100.0
        dFF = abs(b.FF - a.FF)
        # curve deltas between the two adjacent curves (same params; mesh only)
        Ja = fine[(fine.test_index == ti) & (fine.level == c)].J.iloc[0]
        Jb = fine[(fine.test_index == ti) & (fine.level == f_)].J.iloc[0]
        le1 = V <= 1.0
        rmse_le1 = float(np.sqrt(np.mean((Ja[le1] - Jb[le1]) ** 2)))
        rmse_gt1 = float(np.sqrt(np.mean((Ja[~le1] - Jb[~le1]) ** 2)))
        denom_gt1 = float(np.mean(np.abs((Ja[~le1] + Jb[~le1]) / 2.0)))
        rel_gt1 = rmse_gt1 / max(denom_gt1, 1e-12) * 100.0
        adj.append(dict(test_index=int(ti), coarse=c, fine=f_,
                        dVoc_mV=float(dVoc), dJsc_pct=float(dJsc_pct),
                        dPmax_pct=float(dPmax_pct), dFF=float(dFF),
                        rmse_le1=rmse_le1, rmse_gt1=rmse_gt1,
                        denom_gt1=denom_gt1, rel_gt1_pct=float(rel_gt1)))
ad = pd.DataFrame(adj)
ad.to_csv(os.path.join(TAB, "e2v3_finemesh_adjacent_delta.csv"), index=False)

# ---------------- verdicts --------------------------------------------------
def grade(df, c_, f_, crit):
    g = df[(df.coarse == c_) & (df.fine == f_)]
    res = dict(pair="%s->%s" % (c_, f_), n=len(g),
               max_dVoc_mV=float(g.dVoc_mV.abs().max()),
               max_dJsc_pct=float(g.dJsc_pct.abs().max()),
               max_dPmax_pct=float(g.dPmax_pct.abs().max()),
               max_rmse_le1=float(g.rmse_le1.max()),
               med_rmse_le1=float(g.rmse_le1.median()),
               med_rmse_gt1=float(g.rmse_gt1.median()),
               max_rmse_gt1=float(g.rmse_gt1.max()),
               p25_rmse_gt1=float(g.rmse_gt1.quantile(.25)),
               p90_rmse_gt1=float(g.rmse_gt1.quantile(.90)),
               med_rel_gt1_pct=float(g.rel_gt1_pct.median()),
               max_rel_gt1_pct=float(g.rel_gt1_pct.max()))
    res["pass_dVoc"] = bool(res["max_dVoc_mV"] <= crit["dVoc_mV"])
    res["pass_dJsc"] = bool(res["max_dJsc_pct"] <= crit["dJsc_pct"])
    res["pass_dPmax"] = bool(res["max_dPmax_pct"] <= crit["dPmax_pct"])
    res["pass_le1"] = bool(res["max_rmse_le1"] <= crit["rmse_le1"])
    res["pass_le1_tight"] = bool(res["max_rmse_le1"] <= crit["rmse_le1_tight"])
    res["pass_all_generation"] = bool(res["pass_dVoc"] and res["pass_dJsc"]
                                      and res["pass_dPmax"] and res["pass_le1"])
    res["pass_gt1_rel"] = bool(res["max_rel_gt1_pct"] <= 1.0)  # 1% relative (nominal)
    return res

verdicts = pd.DataFrame([grade(ad, c_, f_, CR) for c_, f_ in pairs])
verdicts.to_csv(os.path.join(TAB, "e2v3_finemesh_convergence_verdict.csv"), index=False)

print("\n=== adjacent-grade convergence verdict (6 reps; criteria Voc<=2mV, "
      "Jsc<=0.05%, Pmax<=0.1%, le1 RMSE<=0.1) ===")
print(verdicts[["pair", "max_dVoc_mV", "max_dJsc_pct", "max_dPmax_pct",
                "max_rmse_le1", "med_rmse_gt1", "max_rmse_gt1", "med_rel_gt1_pct",
                "pass_all_generation", "pass_gt1_rel"]].round(4).to_string(index=False))

# --- last-two-grades statement (section-4 rule) ------------------------------
last = verdicts[verdicts.pair == "m0.18->m0.125"].iloc[0]
gen_ok = bool(last.pass_all_generation)
le1_ok = bool(last.pass_le1)
gt1_stat = "median |J| denom rel %.3f%% (max %.3f%%)" % (
    last.med_rel_gt1_pct, last.max_rel_gt1_pct)
gt1_ok = bool(last.pass_gt1_rel)
json.dump(dict(
    n_reps=6, grades=order,
    criteria=CR,
    last_two=dict(pair="m0.18->m0.125",
                  device_metrics_generation_window_converged=gen_ok,
                  max_dVoc_mV=last.max_dVoc_mV,
                  max_dJsc_pct=last.max_dJsc_pct,
                  max_dPmax_pct=last.max_dPmax_pct,
                  max_rmse_le1=last.max_rmse_le1,
                  gt1_segment=gt1_stat,
                  gt1_relative_1pct_converged=gt1_ok),
    forward_verdict=("device metrics + <=1V generation segment: converged within "
                     "budget at the last two grades" if (gen_ok and le1_ok) else
                     "generation-window criteria NOT all met at last two grades"),
    gt1_verdict=(">1 V segment: convergence NOT established within this round's "
                 "budget" if not gt1_ok else ">1 V segment within 1% rel at m0.125"),
), open(os.path.join(TAB, "e2v3_finemesh_convergence_meta.json"), "w"), indent=2)

# device-metric drift across the fine chain (per metric, coarse vs finest)
print("\n=== device metrics drift m0.35 -> m0.125 (median over 6 reps) ===")
piv = cur.pivot_table(index="test_index", columns="level",
                      values=["Voc", "Jsc", "Pmax", "FF"])
for met in ["Voc", "Jsc", "Pmax", "FF"]:
    drift = (piv[met]["m0.125"] - piv[met]["m0.35"]).abs()
    print("  %-4s |median drift| m0.35->m0.125 = %.5f  (max %.5f)"
          % (met, drift.median(), drift.max()))
print("\nwrote ->", TAB)
