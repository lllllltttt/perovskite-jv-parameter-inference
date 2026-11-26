# -*- coding: utf-8 -*-
"""
e2v3_inverse_repair.py -- E2-v3: REPAIRED inverse (VAE) sensitivity accounting.

What round-2 (e2v2_inverse_sensitivity.py) got wrong and this script fixes:
  1. z-score column.  The per-row mesh-sensitivity CSV stored `z = d_mu_norm`
     (raw normalized difference) while the sensitivity FLAG was computed from the
     true z = d/sigma.  A reader using the z column would see raw deltas, not
     predictive-sigma units.  v3 stores BOTH clearly and separately:
        z_ref     = d_mu_norm / sigma_ref_norm      (main, execution-plan
                   criterion |z_ref| > 0.1 -- sigma of the REFERENCE m=1 curve)
        z_current = d_mu_norm / sigma_current_norm  (secondary; sigma of the
                   curve being compared, the round-2 convention)
     and marks sensitive_ref / sensitive_cur separately.
  2. Per-parameter denormalization was wrong for mu_log10 (single-parameter
     norm_to_log10 broadcasts over the 9 scaler columns and [0] returns the
     mu_n column scaler for every parameter).  v3 denormalises explicitly,
     index by index:
        mu_log10[j]       = mu_norm[j]*R[j] + Lmin[j]
        sigma_log10[j]    = sigma_norm[j]*R[j]
        d_mu_log10[j]     = d_mu_norm[j]*R[j]
        mu_point_phys[j]  = 10**mu_log10[j]        (call it the point estimate
                             in physical units; never "the physical mean")
     with R[j]=scaler.data_range_[j], Lmin[j]=scaler.data_min_[j].
  3. sigma clipping: sigma = clip(softplus(raw)+0.01, 0.01, 1) in norm space.
     Rows record whether a curve's sigma hits the 0.01/1.0 bound for any param,
     and the physical-log10 sigma (sigma_log10).  No assumption is made about
     clipping without checking the data.
  4. The five over-reached claims in the round-2 text are re-stated against the
     corrected numbers (see outputs/tables/e2v3_corrected_claims.csv):
       (i)  "好辨识参数全部 <= 0.04 sigma"          -> scope to the FINE chain,
            ref-sigma z_ref, and note sigma is the model's own predictive width;
       (ii) "敏感只发生于弱参数"                     -> the observed shifts are
            driven by reading the >1 V (mesh-unconverged) tail; 'weak parameter'
            is a relative label, not an intrinsic cause;
       (iii)"sigma 经常触顶 1.0"                     -> check: no sigma == 1.0
            (max ~0.40 norm / up to ~1.6 log10-decade for tau_ETL);
       (iv) "窗口置换证明非代码错误"                 -> window substitution is an
            ATTRIBUTION diagnostic, not an independent reverse model nor a proof
            of absence of code error;
       (v)  "发电窗内反演稳健"                       -> mesh-converged curves in
            the generation window do NOT by themselves make the frozen inverse
            robust; the encoder reads the full 0-1.3 V curve and weak-param
            point estimates move with the unconverged >1 V tail.

Pipeline (unchanged from round-2, frozen): Jphys (mA/cm2) --per-column MinMax->
J_norm -> z_mean=encoder(J_norm)[0] (no resampling) -> mu, sigma =
param_head(z_mean), sigma=clip(softplus+0.01,0.01,1).

Pure inference over existing COMSOL curves; no new solves here.
"""
import os, sys, json, glob, re, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_tools"))
import v2lib
from v2lib import PARAM_NAMES, V, Jphys_to_Jnorm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import infer_frozen

BASE = r"E:\project\work1"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(TASK, "outputs")
TAB = os.path.join(OUT, "tables")
for _d in (OUT, TAB):
    os.makedirs(_d, exist_ok=True)
SENS_Z = 0.10
FINE = {"m0.35", "m0.25", "m0.18", "m0.125"}
COARSE = {"m2.00", "m1.41", "m0.71", "m0.50"}
DIRS = [r"E:\project\work1\supplementary_validation\E2\outputs\curves",
        r"E:\project\work1\supplementary_validation_v2\E2_mesh_and_inference\outputs\curves"]


def _dirs_with_extra():
    """Fixed v1+v2 curve dirs, plus any extra curve directories passed as argv
    (used after E2_finemesh solves to append the m=0.18/m=0.125 rows)."""
    return DIRS + [os.path.abspath(a) for a in sys.argv[1:] if os.path.isdir(a)]


def load_rows(dirs):
    out = []
    for curdir in dirs:
        for f in sorted(glob.glob(os.path.join(curdir, "row_*.csv"))):
            with open(f, encoding="utf-8", errors="replace") as fh:
                hdr = fh.readline().strip().lstrip("# ").strip()
                body = fh.read().split()
            meta = dict(re.findall(r"(\w+)=([^,]+)", hdr))
            if meta.get("status", "ok") != "ok" or len(body) != len(V):
                continue
            out.append(dict(
                rowid=int(meta["rowid"]), test_index=int(meta["test_index"]),
                level_type=meta.get("level_type", ""), level=meta.get("level", ""),
                mesh=float(meta.get("mesh_size_factor", 1.0)),
                stol=float(meta.get("stol", 1e-6)),
                nelem=int(meta.get("nelem", -1)),
                nvtx=int(meta.get("nvtx", -1)),
                src=os.path.basename(curdir),
                J=np.asarray(body, np.float64) * v2lib.AM2))
    return pd.DataFrame(out)


def infer(JmA):
    Jn = Jphys_to_Jnorm(np.asarray(JmA, np.float64)[None, :])
    p = infer_frozen.predict(np.asarray(Jn, np.float32))
    return p["z_mean"][0], p["mu"][0], p["sigma"][0]


def main():
    rows = load_rows(_dirs_with_extra())
    print("curve rows loaded: %d (expect >=66)" % len(rows))
    if rows.test_index.nunique() < 6:
        sys.exit("need 6 reps")
    sc = v2lib.param_scaler()
    R = sc.data_range_
    Lmin = sc.data_min_

    # ---- per-row inference ------------------------------------------------
    recs = []
    clip_hit = {}
    for _, r in rows.iterrows():
        z, mu, sg = infer(r.J)
        clip_hi = list((sg >= 1.0 - 1e-9).astype(int))
        clip_lo = list((sg <= 0.01 + 1e-9).astype(int))
        rec = dict(rowid=int(r.rowid), test_index=int(r.test_index),
                   level_type=r.level_type, level=r.level, mesh=r.mesh,
                   stol=r.stol, nelem=int(r.nelem), src=r.src,
                   dzmax=float(np.max(np.abs(z))),
                   clip_hi_any=int(any(clip_hi)), clip_lo_any=int(any(clip_lo)))
        for k in range(9):
            rec["z%d" % k] = float(z[k])
        for j, nm in enumerate(PARAM_NAMES):
            mu_l10 = float(mu[j]) * R[j] + Lmin[j]
            rec["mu_%s" % nm] = float(mu[j])
            rec["mu_log10_%s" % nm] = mu_l10
            rec["mu_phys_%s" % nm] = float(10.0 ** mu_l10)
            rec["sig_%s" % nm] = float(sg[j])
            rec["sig_log10_%s" % nm] = float(sg[j] * R[j])
            rec["sig_clip_hi_%s" % nm] = clip_hi[j]
            rec["sig_clip_lo_%s" % nm] = clip_lo[j]
        recs.append(rec)
    pr = pd.DataFrame(recs)
    pr.to_csv(os.path.join(TAB, "e2v3_inverse_perrow.csv"), index=False)
    print("clip hits across all rows: clip_hi_any=%d  clip_lo_any=%d"
          % (int(pr.clip_hi_any.sum()), int(pr.clip_lo_any.sum())))

    # ---- ref sigma per sample ---------------------------------------------
    refsig = {}
    for ti, g in pr.groupby("test_index"):
        g = g.reset_index(drop=True)
        iw = g.level_type == "ref"
        if iw.sum() != 1:
            print("WARN test_index %d has %d ref rows" % (ti, int(iw.sum())))
            continue
        refsig[ti] = dict(ref_rowid=int(g.loc[iw, "rowid"].iloc[0]),
                          sigma={PARAM_NAMES[j]:
                                 float(g.loc[iw, "sig_%s" % PARAM_NAMES[j]].iloc[0])
                                 for j in range(9)})

    # ---- per (row,param) MESH sensitivity vs own sample ref -----------------
    # Only rows that differ from the ref by MESH (level_type mesh/ref, same
    # stol=1e-6) belong here; tolerance rows are compared to their SAME-MESH
    # base below (a tol row vs the ref would confound mesh and tolerance).
    sens = []
    for ti, g in pr.groupby("test_index"):
        if ti not in refsig:
            continue
        rs = refsig[ti]["sigma"]
        refrowid = refsig[ti]["ref_rowid"]
        refmu = pr[(pr.test_index == ti) & (pr.rowid == refrowid)].iloc[0]
        g = g.reset_index(drop=True)
        for _, r in g.iterrows():
            if r.rowid == refrowid or r.level_type != "mesh":
                continue
            chain = ("fine" if r.level in FINE else "coarse")
            for j, nm in enumerate(PARAM_NAMES):
                d = r["mu_%s" % nm] - refmu["mu_%s" % nm]
                zr = d / rs[nm]
                zc = d / r["sig_%s" % nm]
                sens.append(dict(test_index=int(ti), rowid=int(r.rowid),
                                 level_type=r.level_type, level=r.level,
                                 mesh=r.mesh, stol=r.stol, nelem=int(r.nelem),
                                 src=r.src, chain=chain, param=nm,
                                 mu_norm=float(r["mu_%s" % nm]),
                                 mu_log10=float(r["mu_log10_%s" % nm]),
                                 mu_point_phys=float(r["mu_phys_%s" % nm]),
                                 d_mu_norm=float(d),
                                 d_mu_log10=float(d * R[j]),
                                 sigma_ref_norm=float(rs[nm]),
                                 sigma_current_norm=float(r["sig_%s" % nm]),
                                 sigma_ref_log10=float(rs[nm] * R[j]),
                                 sigma_current_log10=float(r["sig_log10_%s" % nm]),
                                 z_ref=float(zr), z_current=float(zc),
                                 sensitive_ref=bool(abs(zr) > SENS_Z),
                                 sensitive_cur=bool(abs(zc) > SENS_Z)))
    sen = pd.DataFrame(sens)
    sen.to_csv(os.path.join(TAB, "e2v3_inverse_mesh_sensitivity.csv"), index=False)
    print("mesh-sensitivity rows: %d" % len(sen))

    # ---- TOLERANCE pairs: same mesh, tight stol vs base stol (direct) --------
    #   m=1    : stol 1e-4 / 1e-5 / 1e-7  vs  stol 1e-6 (base)
    #   m=0.25 : stol 1e-7               vs  stol 1e-6 (base)
    tol_rows = []
    for ti, g in pr.groupby("test_index"):
        g = g.reset_index(drop=True)
        for msh, stol_a, stol_b in [(1.0, 1e-4, 1e-6), (1.0, 1e-5, 1e-6),
                                    (1.0, 1e-7, 1e-6), (0.25, 1e-7, 1e-6)]:
            sa = g[(np.isclose(g.mesh, msh)) & (np.isclose(g.stol, stol_a))]
            sb = g[(np.isclose(g.mesh, msh)) & (np.isclose(g.stol, stol_b))]
            if len(sa) != 1 or len(sb) != 1:
                continue
            a, b = sa.iloc[0], sb.iloc[0]
            for j, nm in enumerate(PARAM_NAMES):
                d = a["mu_%s" % nm] - b["mu_%s" % nm]
                tol_rows.append(dict(test_index=int(ti), mesh=msh,
                                     stol_tight=stol_a, stol_base=stol_b,
                                     nelem=int(a.nelem), param=nm,
                                     d_mu_norm=float(d),
                                     d_mu_log10=float(d * R[j]),
                                     sigma_base_norm=float(b["sig_%s" % nm]),
                                     sigma_tight_norm=float(a["sig_%s" % nm]),
                                     z_ref=float(d / b["sig_%s" % nm]),
                                     z_current=float(d / a["sig_%s" % nm])))
    tol = pd.DataFrame(tol_rows)
    tol.to_csv(os.path.join(TAB, "e2v3_inverse_tolpair.csv"), index=False)
    if len(tol):
        print("tolpair rows: %d (4 same-mesh pairs x 6 reps x 9 params)"
              % len(tol))

    # ---- headline counts ---------------------------------------------------
    print("\nmain criterion |z_ref| > %.2f (sigma of the m=1 ref curve)"
          % SENS_Z)
    for label, ch in (("FINE (m0.35/0.25@1e-6 vs ref)", "fine"),
                      ("COARSE (m2.0..0.50@1e-6 vs ref)", "coarse")):
        s = sen[(sen.chain == ch) & (np.isclose(sen.stol, 1e-6))]
        if len(s) == 0:
            continue
        percell = s.groupby(["test_index", "rowid"]).sensitive_ref.any()
        percur = s.groupby(["test_index", "rowid"]).sensitive_cur.any()
        print("  %-32s cells %3d  sens_ref-cells %3d  sens_cur-cells %3d  "
              "curves(ref-crit) %2d/%d  (cur-crit) %2d/%d"
              % (label, len(s), int(s.sensitive_ref.sum()),
                 int(s.sensitive_cur.sum()), int(percell.sum()),
                 int(len(percell)), int(percur.sum()), int(len(percur))))
    # direct same-mesh tolerance cells/curves (v2 tolpair logic, corrected cols)
    if len(tol):
        for (msh, stA), g in tol.groupby(["mesh", "stol_tight"]):
            g = g.reset_index(drop=True)
            cells = (g.z_ref.abs() > SENS_Z)
            percur = cells.groupby(g.test_index).any()
            print("  TOL m=%-4s stol %.0e vs %.0e : cells %3d  sens_ref-cells %3d"
                  "  curves %d/6"
                  % (msh, stA, g.stol_base.iloc[0], len(g), int(cells.sum()),
                     int(percur.sum())))

    # ---- per-param worst over fine chain, both criteria + log10 shift ------
    fine = sen[(sen.chain == "fine") & (np.isclose(sen.stol, 1e-6))]
    agg = []
    for nm, d in fine.groupby("param"):
        agg.append(dict(param=nm,
                        n_rows=len(d), n_reps=d.test_index.nunique(),
                        max_abs_z_ref=float(d.z_ref.abs().max()),
                        med_abs_z_ref=float(d.z_ref.abs().median()),
                        max_abs_z_cur=float(d.z_current.abs().max()),
                        max_abs_d_log10=float(d.d_mu_log10.abs().max()),
                        med_sigma_ref_log10=float(d.sigma_ref_log10.median())))
    aggdf = pd.DataFrame(agg).sort_values("max_abs_z_ref", ascending=False)
    aggdf.to_csv(os.path.join(TAB, "e2v3_fine_chain_perparam.csv"), index=False)
    print("\nfine-chain per-param worst (6 reps x 2 meshes @ stol 1e-6 vs ref):")
    print(aggdf.round(4).to_string(index=False))

    # ---- window substitution (diagnostic; reframed) ------------------------
    sub_rows = []
    npz = np.load(os.path.join(BASE, "data", "dataset_normalized.npz"),
                  allow_pickle=True)
    for ti, g in pr.groupby("test_index"):
        iw = g.level_type == "ref"
        if iw.sum() != 1:
            continue
        ref = g.loc[iw].iloc[0]
        Jref = rows[(rows.rowid == ref.rowid)]["J"].iloc[0]
        df = g[(g.level_type.isin(["ref", "mesh"])) & (np.isclose(g.stol, 1e-6))]
        df = df.sort_values("mesh")
        fr = df.iloc[0]
        Jf = rows[(rows.rowid == fr.rowid)]["J"].iloc[0]
        voc_t = v2lib.device_metrics(npz["J_test_raw"][ti].astype(np.float64),
                                     voc_mode="interp")["Voc"]
        mask_le1 = V <= 1.0
        mixes = {
            "ref_full": Jref,
            "fine_full": Jf,
            "fine_le1+ref_gt1": np.where(mask_le1, Jf, Jref),
            "ref_le1+fine_gt1": np.where(mask_le1, Jref, Jf),
            "fine_gen0+ref_gtVoc": np.where(V <= voc_t, Jf, Jref),
            "ref_gen0+fine_gtVoc": np.where(V <= voc_t, Jref, Jf),
        }
        ref_mu = np.array([ref["mu_%s" % p] for p in PARAM_NAMES])
        fin_mu = np.array([fr["mu_%s" % p] for p in PARAM_NAMES])
        for nm, Jmix in mixes.items():
            z, mu, sg = infer(Jmix)
            rec = dict(test_index=int(ti), config=nm,
                       dz_from_ref=float(np.max(np.abs(z - np.array(
                           [ref["z%d" % k] for k in range(9)])))),
                       d_mu_vs_ref=float(np.max(np.abs(mu - ref_mu))),
                       d_mu_vs_fine=float(np.max(np.abs(mu - fin_mu))))
            rec["follows"] = ("ref" if rec["d_mu_vs_ref"] < rec["d_mu_vs_fine"]
                              else "fine")
            for j, p in enumerate(PARAM_NAMES):
                rec["mu_%s" % p] = float(mu[j])
            sub_rows.append(rec)
    sub = pd.DataFrame(sub_rows)
    sub.to_csv(os.path.join(TAB, "e2v3_inverse_window_substitution.csv"),
               index=False)
    if len(sub):
        print("\nwindow-substitution rows: %d x %d configs (reframed as an "
              "ATTRIBUTION diagnostic only -- NOT an independent reverse-model "
              "proof, NOT evidence of absence of code error)"
              % (sub.test_index.nunique(), sub.config.nunique()))
        # which config's mu follows the ref parent (max-over-9-params criterion)
        pivot = sub.pivot_table(index="config", columns="follows",
                                values="test_index", aggfunc="count", fill_value=0)
        if "fine" in pivot.columns and "ref" in pivot.columns:
            print("  mu follows <ref> vs <fine> parent by config (rows per rep, "
                  "max over 9 params):")
            print("    ", pivot.to_string().replace("\n", "\n     "))

    # ---- corrected claims CSV (old phrase -> corrected statement + evidence) -
    claims = [
        dict(claim="good_params_all_le_004sigma",
             old_phrase="(round-2 README/script) '好辨识参数 max|z| -- Nc 0.039, "
                        "Nv 0.038, mu_n 0.027, mu_p 0.035, tau_HTL 0.022 -> 全部 "
                        "<= 0.04 sigma, 不敏感'",
             corrected=("That number was the RAW normalized |d_mu| (<=0.04 in "
                        "0..1 normalized-log10 units) read from the buggy stored "
                        "z=d column and printed as if it were sigma units. With "
                        "z_ref = d_mu/sigma_ref (m=1 reference sigma), the FINE "
                        "chain (m0.35/m0.25 @1e-6 vs ref, 6 reps) moves the point "
                        "estimate of EVERY parameter by 0.3-0.7 sigma_ref "
                        "(mu_p 0.57, mu_n 0.47, Nv 0.43, tau_HTL 0.44, Nc 0.32, "
                        "rad_c 0.71, tau_ETL 0.38; see e2v3_fine_chain_perparam.csv). "
                        "In log10-decade units the movement is 0.10-0.48 decade. "
                        "The round-2 claim 'well-identified params are mesh-"
                        "insensitive' does NOT survive; sigma is the model's own "
                        "predictive width and z is therefore a within-model ruler, "
                        "not a statement about global identifiability.")),
        dict(claim="sensitivity_only_weak_params",
             old_phrase="(README §5.2) 敏感只发生于弱辨识参数；好辨识参数不敏感",
             corrected=("Once sigma-normalised (z_ref = d_mu/sigma_ref) the FINE "
                        "chain moves well-identified params too (mu_p 0.57, mu_n "
                        "0.47, Nc 0.32 sigma_ref), so 'only weak parameters are "
                        "sensitive' is false as stated. What is true: (a) the "
                        "largest sigma-normalised and log10-decade shifts are on "
                        "wide-sigma params (rad_c 0.71 sigma_ref / 0.48 decade), "
                        "and (b) the window-substitution attribution shows the "
                        "movement follows whichever parent supplies the >1 V "
                        "(mesh-unconverged) tail. 'Weak parameter' is a relative "
                        "label (wide predictive sigma), not an intrinsic cause.")),
        dict(claim="sigma_often_hits_clip",
             old_phrase="(README §3) rad_c/tau_ETL 的 sigma 常触顶 1.0 (= 整个先验宽 3 decade)",
             corrected=("False for the 66 curves: no sigma hits the 1.0 clip top "
                        "(nor the 0.01 floor). sigma_norm range 0.02-0.40 "
                        "(tau_ETL max ~0.40); physical-log10 sigma = sigma_norm*R[j], "
                        "up to ~1.6 log10-decade for tau_ETL (R=4), ~0.5-0.9 for "
                        "rad_c (R=3). The 0.1-sigma criterion is NOT diluted by "
                        "clipping for this data set.")),
        dict(claim="window_substitution_proves_not_code_error",
             old_phrase="(README §4) 窗互换证明该弱参数敏感性完全由 >1 V 尾巴驱动 / "
                        "证明非代码错误",
             corrected=("Window substitution is an ATTRIBUTION diagnostic: swapping "
                        "which parent supplies the >1 V segment flips mu toward that "
                        "parent. It supports the 'inverse reads the >1 V tail' "
                        "mechanism but is not an independent reverse model, does not "
                        "establish which segment is 'correct', and cannot by itself "
                        "rule out other encoder/geometry artefacts.")),
        dict(claim="generation_window_inverse_robust",
             old_phrase="(README §0/§5) 发电窗内反演稳健 / mesh floor << inverse "
                        "uncertainty (global)",
             corrected=("Only the CURVES in the <=1 V / gen0 window are "
                        "mesh-converged. The frozen VAE reads the FULL 0-1.3 V "
                        "curve; replacing the >1 V segment moves weak-parameter "
                        "point estimates by up to ~0.16 sigma_ref. A global claim "
                        "'mesh floor << inverse uncertainty' therefore only holds "
                        "for narrow-sigma parameters and must be stated with the "
                        ">1 V caveat.")),
    ]
    cdf = pd.DataFrame(claims)
    cdf.to_csv(os.path.join(TAB, "e2v3_corrected_claims.csv"), index=False)

    json.dump(dict(
        n_rows_loaded=int(len(rows)),
        sources=[os.path.basename(d) for d in _dirs_with_extra()],
        sens_z_threshold=SENS_Z,
        main_criterion="abs(z_ref)>0.1 with z_ref=d_mu_norm/sigma_ref_norm "
                       "(sigma of frozen m=1 ref curve); z_current=d_mu_norm/"
                       "sigma_current_norm reported as secondary",
        denorm="mu_log10[j]=mu_norm[j]*R[j]+Lmin[j]; sigma_log10[j]=sigma_norm[j]*R[j];"
               " d_mu_log10[j]=d_mu_norm[j]*R[j]; mu_point_phys=10**mu_log10",
        clip="sigma=clip(softplus(raw)+0.01,0.01,1) in norm space; per-row "
             "clip_hi_any/clip_lo_any flags recorded",
        corrected_claims="see e2v3_corrected_claims.csv (5 round-2 over-reaches "
                         "re-stated against corrected tables)",
        window_substitution="reframed as ATTRIBUTION diagnostic only (not an "
                            "independent reverse-model proof)",
    ), open(os.path.join(TAB, "e2v3_config.json"), "w"), indent=2)
    print("\nwrote ->", TAB)


if __name__ == "__main__":
    main()
