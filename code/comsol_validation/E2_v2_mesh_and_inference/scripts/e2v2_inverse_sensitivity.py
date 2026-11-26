# -*- coding: utf-8 -*-
"""
e2v2_inverse_sensitivity.py -- P0 E2-v2: does mesh / tolerance change the FROZEN
model's INVERSE predictions?

Every COMSOL curve (old 48 + v2 fine 18 = 66 rows, 6 reps x 11 configs) is fed
through the frozen path exactly as the published evaluation does:
    Jphys (mA/cm2) --per-column MinMax--> J_norm
    z_mean = encoder(J_norm)[0]            (NO latent re-sampling)
    mu, sigma = param_head(z_mean); sigma = clip(softplus+0.01, 0.01, 1)
Comparisons are made in normalized log10 units (mu, sigma); because both mu and
sigma are additive-linear under the MinMax transform, z-scores and containment
are identical in normalized vs log10-physical units.  We also report mu in
log10 decades (norm_to_log10) for physical readability.

Pre-registered criterion (execution_plan.md): a curve is INVERSE-SENSITIVE to a
mesh/tolerance change if |d_mu| > 0.10 * sigma_curve  for any of the 9 params,
where sigma_curve is the model's own predictive sigma on the perturbed curve.

Window-substitution (attribution): for each rep the ref (m=1) and finest
(m=0.25) curves are recombined at the fixed V=1.0 boundary and at Voc_t, and
each recombination is passed through inference.  If the prediction tracks which
curve supplied the >1 V segment, the frozen model's inverse read is driven by
the not-mesh-converged >1 V region; if it tracks the <=1 V / gen0 segment, the
mesh-converged region dominates.

Outputs (outputs/):
  e2v2_inverse_perrow.csv                 per-row latent + per-param mu,sigma
  e2v2_inverse_mesh_sensitivity.csv       per (rep,param,row): d_mu vs its ref,
                                          z = d_mu/sigma, mesh_sensitive flag
  e2v2_inverse_window_substitution.csv    per (rep, config): mu and d vs each parent
  (console) headline counts over the fine chain and the tol chain.
"""
import os, sys, glob, re
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_tools"))
import v2lib
from v2lib import PARAM_NAMES, norm_to_log10, Jphys_to_Jnorm, V
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import infer_frozen

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = r"E:\project\work1"
OLD_CUR = os.path.join(BASE, "supplementary_validation", "E2", "outputs", "curves")
V2_CUR = os.path.join(TASK, "outputs", "curves")
OUTDIR = os.path.join(TASK, "outputs")
os.makedirs(OUTDIR, exist_ok=True)
SENS_Z = 0.10                       # pre-registered 0.1 predictive-sigma threshold

def load_rows(curdir):
    out = []
    for f in sorted(glob.glob(os.path.join(curdir, "row_*.csv"))):
        with open(f) as fh:
            hdr = fh.readline().strip().lstrip("# ").strip()
            meta = dict(re.findall(r"(\w+)=([^,]+)", hdr))
            body = [float(x) for x in fh.read().split()]
        if meta.get("status", "ok") != "ok" or len(body) != 131:
            continue
        out.append(dict(rowid=int(meta["rowid"]), test_index=int(meta["test_index"]),
                        level_type=meta.get("level_type", ""), level=meta.get("level", ""),
                        mesh=float(meta.get("mesh_size_factor", 1.0)),
                        stol=float(meta.get("stol", 1e-6)),
                        nelem=int(meta.get("nelem", -1)),
                        J=np.asarray(body) * v2lib.AM2))
    return pd.DataFrame(out)

def infer(JmA):
    """frozen inference on one mA/cm2 curve -> (z_mean, mu, sigma) normalized."""
    Jn = Jphys_to_Jnorm(np.asarray(JmA, np.float64)[None, :])
    p = infer_frozen.predict(np.asarray(Jn, np.float32))
    return p["z_mean"][0], p["mu"][0], p["sigma"][0]

def main():
    npz = np.load(os.path.join(BASE, "data", "dataset_normalized.npz"), allow_pickle=True)
    rows = pd.concat([load_rows(OLD_CUR), load_rows(V2_CUR)], ignore_index=True)
    print("curve rows loaded: %d (old 48 + v2 fine 18 = 66 expected)" % len(rows))

    # ---------- 1. per-row inference ----------
    recs = []
    for _, r in rows.iterrows():
        z, mu, sg = infer(r.J)
        recs.append(dict(rowid=int(r.rowid), test_index=int(r.test_index),
                         level_type=r.level_type, level=r.level,
                         mesh=r.mesh, stol=r.stol, nelem=int(r.nelem),
                         dzmax=float(np.max(np.abs(z)))))
        for k in range(9):
            recs[-1]["z%d" % k] = float(z[k])
        for j, nm in enumerate(PARAM_NAMES):
            recs[-1]["mu_" + nm] = float(mu[j])
            recs[-1]["sig_" + nm] = float(sg[j])
    pr = pd.DataFrame(recs)
    pr.to_csv(os.path.join(OUTDIR, "e2v2_inverse_perrow.csv"), index=False)

    # ---------- 2. mesh/tol sensitivity vs each sample's ref (m=1, stol 1e-6) ----------
    sens_rows = []
    for ti, g in pr.groupby("test_index"):
        g = g.reset_index(drop=True)
        iref = int(np.flatnonzero((g.level_type == "ref")).tolist()[0])  # ref row present
        ref = g.iloc[iref]
        for i, r in g.iterrows():
            for j, nm in enumerate(PARAM_NAMES):
                d = r["mu_" + nm] - ref["mu_" + nm]
                z = d / r["sig_" + nm]
                sens_rows.append(dict(test_index=int(ti), rowid=int(r.rowid),
                                      level_type=r.level_type, level=r.level,
                                      mesh=r.mesh, stol=r.stol, nelem=int(r.nelem),
                                      param=nm, mu_log10=float(norm_to_log10(np.array([r["mu_"+nm]]))[0]),
                                      d_mu_norm=float(d), d_mu_log10=float(d * v2lib.param_scaler().data_range_[j]),
                                      sig_norm=float(r["sig_" + nm]),
                                      z=d, mesh_sensitive=bool(abs(z) > SENS_Z)))
    sen = pd.DataFrame(sens_rows)
    sen.to_csv(os.path.join(OUTDIR, "e2v2_inverse_mesh_sensitivity.csv"), index=False)

    # ---------- 2b. direct tolerance-pair comparison (same mesh, stol tight vs base)
    # For the recheck to be about TOLERANCE, both curves must share a mesh:
    #   m=1    : stol 1e-4 / 1e-5 / 1e-7   vs  stol 1e-6 (the ref base)
    #   m=0.25 : stol 1e-7                vs  stol 1e-6
    tol_rows = []
    for ti, g in pr.groupby("test_index"):
        g = g.reset_index(drop=True)
        for (msh, stol_a, stol_b) in [(1.0, 1e-4, 1e-6), (1.0, 1e-5, 1e-6),
                                      (1.0, 1e-7, 1e-6), (0.25, 1e-7, 1e-6)]:
            sel_a = g[(np.isclose(g.mesh, msh)) & (np.isclose(g.stol, stol_a))]
            sel_b = g[(np.isclose(g.mesh, msh)) & (np.isclose(g.stol, stol_b))]
            if len(sel_a) != 1 or len(sel_b) != 1:
                continue
            a, b = sel_a.iloc[0], sel_b.iloc[0]
            for j, nm in enumerate(PARAM_NAMES):
                d = a["mu_" + nm] - b["mu_" + nm]
                z = d / a["sig_" + nm]
                tol_rows.append(dict(test_index=int(ti), mesh=msh, stol_tight=stol_a,
                                     stol_base=stol_b, nelem=int(a.nelem), param=nm,
                                     d_mu_norm=float(d),
                                     d_mu_log10=float(d * v2lib.param_scaler().data_range_[j]),
                                     sig_norm=float(a["sig_" + nm]), z=float(z),
                                     tol_sensitive=bool(abs(z) > SENS_Z)))
    tol = pd.DataFrame(tol_rows)
    tol.to_csv(os.path.join(OUTDIR, "e2v2_inverse_tolpair.csv"), index=False)

    # ---------- 3. headline counts ----------
    print("\nPre-registered criterion |d_mu| > %.2f*sig -> INVERSE-SENSITIVE" % SENS_Z)
    for grpname, sel in [("FINE chain (m0.35/0.25 @1e-6) vs m=1 ref", sen.level.isin(["m0.35", "m0.25"]) & (sen.stol == 1e-6)),
                          ("COARSE chain (m2.0/1.41/0.71/0.5 @1e-6) vs m=1 ref", sen.level.isin(["m2.00", "m1.41", "m0.71", "m0.50"]) & (sen.stol == 1e-6))]:
        s = sen[sel]
        if len(s) == 0:
            continue
        percell = s.groupby(["test_index", "rowid"]).mesh_sensitive.any()
        print("  %-48s cells %4d  sensitive-cells %3d  sensitive-curves %2d/%d"
              % (grpname, len(s), int(s.mesh_sensitive.sum()), int(percell.sum()), int(len(percell))))
    # direct same-mesh tolerance pairs
    for (msh, stA), g in tol.groupby(["mesh", "stol_tight"]):
        g = g.reset_index(drop=True)
        percell = g.groupby("test_index").tol_sensitive.any()
        print("  TOL pair m=%-4s stol %.0e vs %.0e : cells %3d  sensitive-cells %3d  sensitive-curves %2d/6"
              % (msh, stA, g.stol_base.iloc[0], len(g), int(g.tol_sensitive.sum()), int(percell.sum())))
    # per-param worst |z| over the fine chain
    fine = sen[(sen.level.isin(["m0.35", "m0.25"])) & (sen.stol == 1e-6)]
    worst = fine.groupby("param").apply(lambda d: pd.Series(
        dict(max_abs_z=float(d.z.abs().max()), mean_abs_z=float(d.z.abs().mean()),
             max_d_mu_log10=float(d.d_mu_log10.abs().max())), index=["max_abs_z", "mean_abs_z", "max_d_mu_log10"]),
        include_groups=False)
    print("\nfine-chain |d_mu| vs ref (worst over 6 reps x 2 meshes):")
    print(worst.round(4).to_string())
    print("param sigma_norm is per-curve; a |z|=0.1 corresponds to mu shifting")
    print("by 1/10 of the model's own predictive sigma.")

    # ---------- 4. window substitution ----------
    sub_rows = []
    for ti, g in pr.groupby("test_index"):
        g = g.reset_index(drop=True)
        ref = g.iloc[int(np.flatnonzero(g.level_type.values == "ref")[0])]
        Jref = rows.loc[rows.rowid == ref.rowid, "J"].iloc[0]
        # finest default-tol curve = smallest mesh among (level_type mesh/ref, stol 1e-6)
        df = g[(g.stol == 1e-6) & (g.level_type.isin(["ref", "mesh"]))].sort_values("mesh")
        fr = df.iloc[0]
        Jf = rows.loc[rows.rowid == fr.rowid, "J"].iloc[0]
        # build mixes at fixed V boundaries
        mask_le1 = V <= 1.0
        voc = np.nan if False else None
        mixes = {
            "full_ref_gt1__fine_le1": np.where(mask_le1, Jf, Jref),     # fine <=1V, ref >1V
            "full_fine_gt1__ref_le1": np.where(mask_le1, Jref, Jf),     # ref <=1V, fine >1V
        }
        # true Voc boundary from the target curve
        import v2lib as V2
        voc_t = V2.device_metrics(npz["J_test_raw"][ti].astype(np.float64), voc_mode="interp")["Voc"]
        mixes["ref_gtVoc__fine_gen0"] = np.where(V <= voc_t, Jf, Jref)
        mixes["fine_gtVoc__ref_gen0"] = np.where(V <= voc_t, Jref, Jf)
        ref_z = np.array([ref["z%d" % k] for k in range(9)])
        for nm, Jmix in mixes.items():
            z, mu, sg = infer(Jmix)
            rec = dict(test_index=int(ti), config=nm,
                       dz_from_ref=float(np.max(np.abs(z - ref_z))))
            # track which parent the mu follows (closer to full-ref or full-fine?)
            ref_mu = np.array([ref["mu_" + p] for p in PARAM_NAMES])
            fin_mu = np.array([fr["mu_" + p] for p in PARAM_NAMES])
            rec["d_mu_vs_ref"] = float(np.max(np.abs(mu - ref_mu)))
            rec["d_mu_vs_fine"] = float(np.max(np.abs(mu - fin_mu)))
            rec["follows"] = "ref" if rec["d_mu_vs_ref"] < rec["d_mu_vs_fine"] else "fine"
            for j, p in enumerate(PARAM_NAMES):
                rec["mu_" + p] = float(mu[j])
                rec["sig_" + p] = float(sg[j])
            sub_rows.append(rec)
    sub = pd.DataFrame(sub_rows)
    sub.to_csv(os.path.join(OUTDIR, "e2v2_inverse_window_substitution.csv"), index=False)
    print("\nwindow-substitution attribution (max over 9 params, normalized units):")
    piv = sub.pivot_table(index="config", columns="test_index",
                          values=["d_mu_vs_ref", "d_mu_vs_fine"], aggfunc="first")
    print(piv.round(4).to_string())
    print("\nsaved: e2v2_inverse_perrow.csv / e2v2_inverse_mesh_sensitivity.csv /",
          "e2v2_inverse_window_substitution.csv ->", OUTDIR)

if __name__ == "__main__":
    main()
