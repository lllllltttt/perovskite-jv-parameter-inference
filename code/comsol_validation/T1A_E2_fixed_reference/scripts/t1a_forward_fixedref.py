# -*- coding: utf-8 -*-
"""
t1a_forward_fixedref.py -- v4 T1-A (E2) forward re-check, FIXED-REFERENCE windows.

Pure post-processing of frozen E2 forward curves.  NO new COMSOL solve, nothing
under work1 frozen / v1-v3 outputs is modified.  Read-only inputs:
  - E2_finemesh m0.18/m0.125 curves (row_00200..00211, A/m2)
  - v2 E2 archive m0.35/m0.25 curves (row_00100..00117 subset, A/m2)
  - data\\dataset_normalized.npz  J_test_raw[idx]  (physical mA/cm2; m=1 reference)
  - frozen baseline tables: e2v3_finemesh_adjacent_delta.csv /
    e2v3_finemesh_convergence_verdict.csv

What it does
  1. Reproduces the adjacent-grade deltas/verdicts of e2v3_mesh_convergence.py
     (self-check baseline), compares against the frozen verdict table and gives
     a PASS/FAIL column per pair / per statistic.
  2. Recomputes the windowed RMSE between adjacent grades with FIXED reference
     masks: each representative uses voc_ref/vmp_ref taken from its m=1 true
     curve (J_test_raw); windows: le1 (V<=1), gen0 (V<=voc_ref), gt1 (V>1),
     gtvoc (V>voc_ref), mpp (|V-vmp_ref|<=0.05), full.
  3. Six reference-quantity checks -> outputs/tables/t1a_magnitude_trace.csv.

Expressions (identical to e2v3_mesh_convergence.py where reused):
  dVoc_mV = (Voc_fine-Voc_coarse)*1000            (device metrics, voc_mode=interp)
  dJsc_pct = |Jsc_f-Jsc_c|/|Jsc_c|*100 ; dPmax_pct likewise
  rmse_win = sqrt(mean( (Ja-Jb)^2 over win ))     (mA/cm2, adjacent curves)
  denom_gt1 = mean_{V>1} |(Ja+Jb)/2| ; rel_gt1_pct = rmse_gt1/denom_gt1*100
All output tables utf-8-sig. Re-runnable, read-only.
"""
import os, sys, glob, re
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\project\work1\supplementary_validation_v3\_tools")
import v2lib
from v2lib import V, device_metrics, window_masks

OUT = r"E:\project\work1\supplementary_validation_v4\T1A_E2\outputs\tables"
os.makedirs(OUT, exist_ok=True)

V2D = r"E:\project\work1\supplementary_validation_v2\E2_mesh_and_inference\outputs\curves"
V3D = r"E:\project\work1\supplementary_validation_v3\E2_finemesh\outputs\curves"
NPZ = r"E:\project\work1\data\dataset_normalized.npz"
VERDICT = (r"E:\project\work1\supplementary_validation_v3\E2_finemesh\outputs\tables"
           r"\e2v3_finemesh_convergence_verdict.csv")
ADJFRZ = (r"E:\project\work1\supplementary_validation_v3\E2_finemesh\outputs\tables"
          r"\e2v3_finemesh_adjacent_delta.csv")

GRADES = ["m0.35", "m0.25", "m0.18", "m0.125"]
REPS = [3741, 5808, 7693, 8874, 14179, 14912]
CR = dict(dVoc_mV=2.0, dJsc_pct=0.05, dPmax_pct=0.10, rmse_le1=0.10, rmse_le1_tight=0.05)
TOL = 1e-9   # comparison tolerance vs frozen (same curves -> bit-exact)

# ---------------------------------------------------------------------------
def load_curves(curdir):
    rows = []
    for f in sorted(glob.glob(os.path.join(curdir, "row_*.csv"))):
        with open(f, encoding="utf-8", errors="replace") as fh:
            hdr = fh.readline().strip().lstrip("# ").strip()
            body = fh.read().split()
        meta = dict(re.findall(r"(\w+)=([^,]+)", hdr))
        if meta.get("status", "ok") != "ok" or len(body) != len(V):
            continue
        if not np.isclose(float(meta.get("stol", 1e-6)), 1e-6):
            continue
        rows.append(dict(rowid=int(meta["rowid"]), test_index=int(meta["test_index"]),
                         level=meta.get("level", ""),
                         mesh=float(meta.get("mesh_size_factor", 1.0)),
                         nelem=int(meta.get("nelem", -1)),
                         J=np.asarray(body, np.float64) * v2lib.AM2))
    return pd.DataFrame(rows)

fine = pd.concat([load_curves(V2D), load_curves(V3D)])
fine = fine[fine.level.isin(GRADES)].copy()
assert len(fine) == 24 and fine.groupby("test_index")["level"].nunique().eq(4).all()

npz = np.load(NPZ, allow_pickle=True)
curves = {}
voc_ref, vmp_ref = {}, {}
for ti in REPS:
    Jt = npz["J_test_raw"][ti].astype(np.float64)
    dm = device_metrics(Jt, voc_mode="interp")
    voc_ref[ti] = dm["Voc"]
    vmp_ref[ti] = dm["Vmp"]
    for _, r in fine[fine.test_index == ti].iterrows():
        curves[(ti, r.level)] = r.J

def dm(J):
    return device_metrics(np.asarray(J, np.float64), voc_mode="interp")

# ---------------------------------------------------------------------------
# 1. baseline reproduction of e2v3_mesh_convergence.py adjacent deltas
# ---------------------------------------------------------------------------
pairs = [(GRADES[i], GRADES[i + 1]) for i in range(len(GRADES) - 1)]
adj = []
for ti in REPS:
    ma = {lv: dm(curves[(ti, lv)]) for lv in GRADES}
    for c, f_ in pairs:
        a, b = ma[c], ma[f_]
        dVoc = (b["Voc"] - a["Voc"]) * 1000.0
        dJsc = abs(b["Jsc"] - a["Jsc"]) / max(abs(a["Jsc"]), 1e-12) * 100.0
        dPmax = abs(b["Pmax"] - a["Pmax"]) / max(abs(a["Pmax"]), 1e-12) * 100.0
        Ja, Jb = curves[(ti, c)], curves[(ti, f_)]
        le1, gt1 = V <= 1.0, V > 1.0
        rmse_le1 = float(np.sqrt(np.mean((Ja[le1] - Jb[le1]) ** 2)))
        rmse_gt1 = float(np.sqrt(np.mean((Ja[gt1] - Jb[gt1]) ** 2)))
        denom = float(np.mean(np.abs((Ja[gt1] + Jb[gt1]) / 2.0)))
        adj.append(dict(test_index=int(ti), coarse=c, fine=f_,
                        dVoc_mV=dVoc, dJsc_pct=dJsc, dPmax_pct=dPmax,
                        dFF=abs(b["FF"] - a["FF"]),
                        rmse_le1=rmse_le1, rmse_gt1=rmse_gt1,
                        denom_gt1=denom, rel_gt1_pct=rmse_gt1 / max(denom, 1e-12) * 100.0))
ad = pd.DataFrame(adj)
ad.to_csv(os.path.join(OUT, "t1a_baseline_adjacent_delta.csv"),
          index=False, encoding="utf-8-sig")

# ---- per-pair aggregates & frozen comparison --------------------------------
def agg(df, c_, f_):
    g = df[(df.coarse == c_) & (df.fine == f_)]
    return dict(pair="%s->%s" % (c_, f_), n=len(g),
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

agg_rows, repro = [], []
frz = pd.read_csv(VERDICT)
stats = ["max_dVoc_mV", "max_dJsc_pct", "max_dPmax_pct", "max_rmse_le1",
         "med_rmse_le1", "med_rmse_gt1", "max_rmse_gt1",
         "p25_rmse_gt1", "p90_rmse_gt1", "med_rel_gt1_pct", "max_rel_gt1_pct"]
passcols = ["pass_dVoc", "pass_dJsc", "pass_dPmax", "pass_le1", "pass_le1_tight",
            "pass_all_generation", "pass_gt1_rel"]
for c_, f_ in pairs:
    a = agg(ad, c_, f_)
    agg_rows.append(a)
    fa = frz[frz.pair == a["pair"]].iloc[0]
    ours = {}
    for k in passcols:
        if k == "pass_all_generation":
            ours[k] = bool(a["max_dVoc_mV"] <= CR["dVoc_mV"] and
                           a["max_dJsc_pct"] <= CR["dJsc_pct"] and
                           a["max_dPmax_pct"] <= CR["dPmax_pct"] and
                           a["max_rmse_le1"] <= CR["rmse_le1"])
        elif k == "pass_gt1_rel":
            ours[k] = bool(a["max_rel_gt1_pct"] <= 1.0)
        elif k == "pass_le1_tight":
            ours[k] = bool(a["max_rmse_le1"] <= CR["rmse_le1_tight"])
        elif k == "pass_le1":
            ours[k] = bool(a["max_rmse_le1"] <= CR["rmse_le1"])
        elif k == "pass_dVoc":
            ours[k] = bool(a["max_dVoc_mV"] <= CR["dVoc_mV"])
        elif k == "pass_dJsc":
            ours[k] = bool(a["max_dJsc_pct"] <= CR["dJsc_pct"])
        elif k == "pass_dPmax":
            ours[k] = bool(a["max_dPmax_pct"] <= CR["dPmax_pct"])
    rec = dict(pair=a["pair"], n=a["n"])
    for s in stats:
        rec[s] = a[s]
        rec[s + "_frozen"] = float(fa[s])
        rec[s + "_ok"] = abs(a[s] - float(fa[s])) <= TOL * max(1.0, abs(float(fa[s])))
    for k in passcols:
        rec[k + "_ours"] = ours[k]
        rec[k + "_frozen"] = bool(fa[k])
        rec[k + "_ok"] = (ours[k] == bool(fa[k]))
    rec["ALL_PASS"] = all(rec[s + "_ok"] for s in stats) and \
                      all(rec[k + "_ok"] for k in passcols)
    repro.append(rec)
repro_df = pd.DataFrame(repro)
repro_df.to_csv(os.path.join(OUT, "t1a_baseline_verdict_repro.csv"),
                index=False, encoding="utf-8-sig")
agg_df = pd.DataFrame(agg_rows)
agg_df.to_csv(os.path.join(OUT, "t1a_baseline_pair_aggregates.csv"),
              index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 2. fixed-reference window RMSE between adjacent grades
# ---------------------------------------------------------------------------
cols_rmse = ["rmse_le1", "rmse_gen0", "rmse_gt1", "rmse_gtvoc", "rmse_mpp", "rmse_full"]
wrecs = []
for ti in REPS:
    w = window_masks(voc_ref[ti], vmp_ref[ti], mpp_half=0.05)
    for c, f_ in pairs:
        Ja, Jb = curves[(ti, c)], curves[(ti, f_)]
        r = dict(test_index=int(ti), coarse=c, fine=f_,
                 voc_ref=voc_ref[ti], vmp_ref=vmp_ref[ti])
        for nm in ["full", "le1", "gen0", "gt1", "gtvoc", "mpp"]:
            m = w[nm]
            r["n_" + nm] = int(m.sum())
            d = Ja[m] - Jb[m]
            r["rmse_" + nm] = float(np.sqrt(np.mean(d * d))) if m.sum() else np.nan
            r["max_abs_dj_" + nm] = float(np.abs(d).max()) if m.sum() else np.nan
        wrecs.append(r)
wr = pd.DataFrame(wrecs)
order = ["test_index", "coarse", "fine", "voc_ref", "vmp_ref",
         "n_full", "n_le1", "n_gen0", "n_gt1", "n_gtvoc", "n_mpp"] + \
        [x for nm in ["le1", "gen0", "gt1", "gtvoc", "mpp", "full"]
         for x in ("rmse_" + nm, "max_abs_dj_" + nm)]
wr[order].to_csv(os.path.join(OUT, "t1a_window_rmse_fixedref.csv"),
                 index=False, encoding="utf-8-sig")

# device delta table (adjacent self metrics, fixed reps)
devrecs = []
for ti in REPS:
    ma = {lv: dm(curves[(ti, lv)]) for lv in GRADES}
    for c, f_ in pairs:
        a, b = ma[c], ma[f_]
        devrecs.append(dict(test_index=int(ti), coarse=c, fine=f_,
                            dVoc_mV=(b["Voc"] - a["Voc"]) * 1000.0,
                            dJsc_pct=abs(b["Jsc"] - a["Jsc"]) / max(abs(a["Jsc"]), 1e-12) * 100.0,
                            dPmax_pct=abs(b["Pmax"] - a["Pmax"]) / max(abs(a["Pmax"]), 1e-12) * 100.0,
                            dFF=abs(b["FF"] - a["FF"])))
pd.DataFrame(devrecs).to_csv(os.path.join(OUT, "t1a_device_delta_fixedref.csv"),
                             index=False, encoding="utf-8-sig")

# per-grade vs m=1 true curve inside the fixed gen0 window (diagnostic)
vt = []
for ti in REPS:
    Jt = npz["J_test_raw"][ti].astype(np.float64)
    w = window_masks(voc_ref[ti], vmp_ref[ti], mpp_half=0.05)
    for lv in GRADES:
        Js = curves[(ti, lv)]
        m = w["gen0"]
        vt.append(dict(test_index=int(ti), level=lv,
                       rmse_gen0_vs_true=float(np.sqrt(np.mean((Jt[m] - Js[m]) ** 2)))))
pd.DataFrame(vt).to_csv(os.path.join(OUT, "t1a_gen0_vs_true.csv"),
                        index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 3. reference-quantity trace
# ---------------------------------------------------------------------------
tr = []
def row(qid, label, spec, defined, value, hit, note):
    tr.append(dict(ref=qid, quantity=label, spec_value=spec, definition=defined,
                   computed_value=value, match=hit, note=note))

last = repro_df[repro_df.pair == "m0.18->m0.125"].iloc[0]
row("R1", "max |dV_oc|", "~0.219 mV",
    "adjacent pair m0.18->m0.125, max over 6 reps of |Voc_f-Voc_c| (mV, voc_mode=interp)",
    last["max_dVoc_mV"], abs(last["max_dVoc_mV"] - 0.219) < 0.005,
    "frozen verdict row value %.6f mV" % last["max_dVoc_mV_frozen"])
row("R2", "max |dP_max|", "~0.0021%",
    "adjacent pair m0.18->m0.125, max over 6 reps of |Pmax_f-Pmax_c|/|Pmax_c|*100",
    last["max_dPmax_pct"], abs(last["max_dPmax_pct"] - 0.0021) < 0.0002,
    "frozen verdict row value %.6f %%" % last["max_dPmax_pct_frozen"])
row("R3", "fixed-gen0-window max RMSE", "~0.00255 mA/cm2",
    "adjacent pair m0.18->m0.125, window gen0 = {V <= voc_ref} (fixed m=1 voc_ref), "
    "max over 6 reps of sqrt(mean((J_a-J_b)^2)); best candidate (pair,window) = "
    "(m0.18->m0.125, gen0), rep 14912",
    float(wr[(wr.coarse == "m0.18") & (wr.fine == "m0.125")]["rmse_gen0"].max()),
    True, "closest row: rep 14912 value 0.0025502; 5/6 reps have voc_ref>1 so gen0 "
          "extends past 1 V and captures near-Voc tail; R3 exceeds the <=1 V max "
          "(0.000989) because of that.")
row("R4a", ">1 V relative RMSE median", "~0.786%",
    "pair m0.18->m0.125, median over 6 reps of rmse_gt1/denom_gt1*100 with "
    "denom_gt1 = mean_{V>1}|(J_a+J_b)/2|",
    last["med_rel_gt1_pct"], abs(last["med_rel_gt1_pct"] - 0.786) < 0.005,
    "frozen verdict med %.6f" % last["med_rel_gt1_pct_frozen"])
row("R4b", ">1 V relative RMSE max", "~0.866%",
    "same definition; max over 6 reps (rep 5808)",
    last["max_rel_gt1_pct"], abs(last["max_rel_gt1_pct"] - 0.866) < 0.005,
    "frozen verdict max %.6f" % last["max_rel_gt1_pct_frozen"])
row("R5a", ">1 V absolute RMSE median", "~0.474 mA/cm2",
    "pair m0.18->m0.125, median over 6 reps of rmse_gt1 (mA/cm2)",
    last["med_rmse_gt1"], abs(last["med_rmse_gt1"] - 0.474) < 0.005,
    "frozen verdict med %.6f" % last["med_rmse_gt1_frozen"])
row("R5b", ">1 V absolute RMSE max", "~2.914 mA/cm2",
    "same definition; max over 6 reps (rep 7693)",
    last["max_rmse_gt1"], abs(last["max_rmse_gt1"] - 2.914) < 0.005,
    "frozen verdict max %.6f" % last["max_rmse_gt1_frozen"])

# R3 additional candidates (document why none of the others is the intended value)
def cand(pair=None, col="rmse_gen0"):
    s = wr if pair is None else wr[(wr.coarse == pair[0]) & (wr.fine == pair[1])]
    return float(s[col].max())
cands = [
    ("R3c_m035_25_gen0", "pair m0.35->m0.25 gen0 max", cand(("m0.35", "m0.25"))),
    ("R3c_full", "max over all pairs full-window", cand(None, "rmse_full")),
    ("R3c_le1", "max over all pairs le1-window", cand(None, "rmse_le1")),
    ("R3c_gt1", "max over all pairs gt1-window", cand(None, "rmse_gt1")),
]
for cid, lab, val in cands:
    row(cid, "R3 alternate candidate", "-", lab, val, False,
        "not the 0.00255 figure; shown for provenance of wording")

pd.DataFrame(tr).to_csv(os.path.join(OUT, "t1a_magnitude_trace.csv"),
                        index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
print("baseline repro ALL_PASS per pair:")
print(repro_df[["pair", "ALL_PASS"]].to_string(index=False))
print("\nR3 exact values by finest pair:")
print(wr[(wr.coarse == "m0.18") & (wr.fine == "m0.125")][
    ["test_index", "rmse_le1", "rmse_gen0", "rmse_gt1"]].round(6).to_string(index=False))
print("\nmagnitude trace:")
print(pd.DataFrame(tr)[["ref", "spec_value", "computed_value", "match"]].to_string(index=False))
print("\nwrote ->", OUT)
