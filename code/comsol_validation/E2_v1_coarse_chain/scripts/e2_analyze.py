"""
e2_analyze.py  (E2: mesh & tolerance convergence -- results)

Reads E2 row_%05d.csv curves + e2_manifest.csv, computes per-level device
metrics and full-window curve errors relative to each sample's frozen-config
reference (m=1, stol=1e-6, runAll), verifies the runAll-vs-study.run QC curve,
and writes convergence tables + figures.

Outputs (E2/outputs/tables/): e2_qc_runall_vs_studyrun.csv,
e2_mesh_levels.csv, e2_tol_levels.csv, e2_numerical_error_summary.csv
Figures (E2/figures/): e2_mesh_convergence.png, e2_tol_convergence.png,
e2_numerical_error.png
"""
import os, glob, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
E2 = os.path.dirname(HERE)
E1 = os.path.join(os.path.dirname(E2), "E1")
BASE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TAB = os.path.join(E2, "outputs", "tables"); os.makedirs(TAB, exist_ok=True)
FIG = os.path.join(E2, "figures"); os.makedirs(FIG, exist_ok=True)
CUR = os.path.join(E2, "outputs", "curves"); os.makedirs(CUR, exist_ok=True)
CUR1 = os.path.join(E1, "outputs", "curves")

V = np.linspace(0.0, 1.3, 131)
AM2 = 0.1                                # A/m2 -> mA/cm2


def read_row(path):
    """Parse a worker curve file -> dict(meta, J_mAcm2)."""
    with open(path) as f:
        head = f.readline().lstrip("#").strip()
    meta = dict(kv.split("=", 1) for kv in head.split(","))
    J = np.loadtxt(path, comments="#")
    J = np.atleast_1d(J).astype(float)
    meta["status"] = meta.get("status", "ok")
    return meta, J * AM2 if len(J) == 131 else J


def device_metrics(J):
    jsc = abs(J[0])
    s = np.diff(np.sign(J)); k = np.where(s)[0]
    if len(k):
        k = k[0]
        voc = V[k] - J[k] * (V[k + 1] - V[k]) / (J[k + 1] - J[k])
    else:
        voc = np.nan
    p = np.where(J * V > 0, J * V, np.nan)
    pmax = np.nanmax(p) if np.isfinite(np.nanmax(p)) else np.nan
    ff = pmax / (jsc * voc) if (np.isfinite(voc) and voc > 0 and jsc > 0 and np.isfinite(pmax)) else np.nan
    return dict(Jsc=jsc, Voc=voc, Pmax=pmax, FF=ff)


def main():
    man = pd.read_csv(os.path.join(E2, "inputs", "e2_manifest.csv"))
    rows = []
    for p in sorted(glob.glob(os.path.join(CUR, "row_*.csv"))):
        meta, J = read_row(p)
        r = {k: meta.get(k) for k in ("rowid", "test_index", "level_type", "level",
                                      "mesh_size_factor", "stol", "status", "nelem", "elapsed_s")}
        r["rowid"] = int(r["rowid"]); r["test_index"] = int(r["test_index"])
        r["m"] = float(r["mesh_size_factor"]); r["stol"] = float(r["stol"])
        r["nelem"] = int(r["nelem"]) if r["nelem"] not in (None, "") else np.nan
        ok = r["status"] == "ok" and len(J) == 131
        r["ok"] = ok
        if ok:
            r.update(device_metrics(J))
            r["curve"] = J
        else:
            r.update(Jsc=np.nan, Voc=np.nan, Pmax=np.nan, FF=np.nan); r["curve"] = None
        rows.append(r)
    df = pd.DataFrame(rows)

    # reference per sample = runAll frozen-config row (level_type=='ref')
    refs = {}
    for _, r in df[df.level_type == "ref"].iterrows():
        if r["ok"]:
            refs[int(r.test_index)] = r

    # ---- QC: runAll ref vs study.run QC curve (E1/archive code path) -------
    e1bas = pd.read_csv(os.path.join(E1, "inputs", "e1_manifest.csv"))
    e1map = dict(zip(e1bas[e1bas.design == "baseline"].test_index,
                     e1bas[e1bas.design == "baseline"].rowid))
    qrows = []
    for qf in sorted(glob.glob(os.path.join(CUR, "qc_studyrun_*.csv"))):
        meta, Jq = read_row(qf)
        rid = int(meta["rowid"])
        mr = man[man.rowid == rid].iloc[0]
        ti = int(mr.test_index)
        # E1 baseline curve (study.run, same params) keyed by E1 baseline rowid
        bf = os.path.join(CUR1, "row_%05d.csv" % e1map[ti])
        if not os.path.exists(bf):
            continue
        _, J1 = read_row(bf)
        ref = refs[ti]["curve"] if ti in refs else None
        d_st = np.abs(Jq - J1)              # study.run(here) vs study.run(E1)
        d_rn = np.abs(Jq - ref) if ref is not None else None  # study.run vs runAll
        rec = dict(test_index=ti, n=len(Jq),
                   studyrun_vs_e1_max_mAcm2=float(d_st.max()),
                   studyrun_vs_e1_rmse_mAcm2=float(np.sqrt(np.mean(d_st ** 2))))
        if d_rn is not None:
            rec["studyrun_vs_runall_max_mAcm2"] = float(d_rn.max())
            rec["studyrun_vs_runall_rmse_mAcm2"] = float(np.sqrt(np.mean(d_rn ** 2)))
        # metric deltas study.run vs runAll ref
        mq = device_metrics(Jq); mr_ = device_metrics(ref)
        rec["dPmax_mWcm2"] = float(mq["Pmax"] - mr_["Pmax"])
        rec["dVoc_mV"] = float((mq["Voc"] - mr_["Voc"]) * 1e3)
        qrows.append(rec)
    qc = pd.DataFrame(qrows)
    qc.to_csv(os.path.join(TAB, "e2_qc_runall_vs_studyrun.csv"), index=False)
    if len(qc):
        print("=== runAll vs study.run QC ===")
        print(qc.round(6).to_string(index=False))

    # ---- per-level metrics vs sample reference -----------------------------
    out = []
    for _, r in df.iterrows():
        ti = int(r.test_index)
        if ti not in refs:
            continue
        rr = refs[ti]["curve"]
        rec = dict(rowid=int(r.rowid), test_index=ti, group_id=man[man.rowid == r.rowid].group_id.iloc[0],
                   level_type=r.level_type, level=r.level, m=r.m, stol=r.stol,
                   status=r.status, nelem=r.nelem, elapsed_s=r.elapsed_s)
        if r["ok"]:
            d = rr - r["curve"]
            rec["rmse_full_mAcm2"] = float(np.sqrt(np.mean(d ** 2)))
            rec["max_abs_mAcm2"] = float(np.max(np.abs(d)))
            rec["dJsc_pct"] = float(100 * (r.Jsc - refs[ti].Jsc) / refs[ti].Jsc)
            rec["dVoc_mV"] = float((r.Voc - refs[ti].Voc) * 1e3)
            rec["dFF"] = float(r.FF - refs[ti].FF)
            rec["dPmax_pct"] = float(100 * (r.Pmax - refs[ti].Pmax) / refs[ti].Pmax)
        else:
            for c in ("rmse_full_mAcm2", "max_abs_mAcm2", "dJsc_pct", "dVoc_mV", "dFF", "dPmax_pct"):
                rec[c] = np.nan
        out.append(rec)
    rdf = pd.DataFrame(out)
    mesh = rdf[rdf.level_type == "mesh"].copy()
    tol = rdf[rdf.level_type == "tol"].copy()
    refdf = rdf[rdf.level_type == "ref"].copy()
    mesh.to_csv(os.path.join(TAB, "e2_mesh_levels.csv"), index=False)
    tol.to_csv(os.path.join(TAB, "e2_tol_levels.csv"), index=False)

    # ---- numerical-error summary per sample --------------------------------
    summ = []
    for ti, g in rdf.groupby("test_index"):
        gm = mesh[mesh.test_index == ti].dropna(subset=["rmse_full_mAcm2"])
        gt = tol[tol.test_index == ti].dropna(subset=["rmse_full_mAcm2"])
        rec = dict(test_index=int(ti), group_id=man[man.test_index == ti].group_id.iloc[0],
                   ref_Pmax_mWcm2=float(refs[ti].Pmax), ref_nelem=int(refs[ti].nelem))
        def span(s):
            if len(s) == 0:
                return np.nan
            return float(np.max(s))       # max |delta| over levels (vs ref)
        # fine vs frozen (m=0.5), and coarsest-induced max deviation (m>=1)
        g_m = gm.set_index("level")
        rec["mesh_rmse_fine_mAcm2"] = float(g_m.loc["m0.50", "rmse_full_mAcm2"]) if "m0.50" in g_m.index else np.nan
        coarse = g_m.loc[[l for l in g_m.index if l in ("m2.00", "m1.41")]]
        rec["mesh_rmse_coarse_max_mAcm2"] = span(coarse.rmse_full_mAcm2) if len(coarse) else np.nan
        rec["mesh_dPmax_fine_pct"] = float(g_m.loc["m0.50", "dPmax_pct"]) if "m0.50" in g_m.index else np.nan
        rec["mesh_dPmax_coarse_max_pct"] = span(coarse.dPmax_pct) if len(coarse) else np.nan
        g_t = gt.set_index("level")
        rec["tol_rmse_max_mAcm2"] = span(g_t.rmse_full_mAcm2)
        rec["tol_dPmax_max_pct"] = span(g_t.dPmax_pct)
        rec["mesh_rmse_range_mAcm2"] = float(gm.rmse_full_mAcm2.max()) if len(gm) else np.nan
        rec["tol_rmse_range_mAcm2"] = float(gt.rmse_full_mAcm2.max()) if len(gt) else np.nan
        summ.append(rec)
    sm = pd.DataFrame(summ)
    sm.to_csv(os.path.join(TAB, "e2_numerical_error_summary.csv"), index=False)
    print("\n=== numerical error summary (vs frozen-config reference) ===")
    print(sm.round(6).to_string(index=False))

    json.dump(dict(ok_rows=int(df.ok.sum()), failed=int((~df.ok).sum()),
                   n_groups=sm.test_index.nunique(),
                   median_mesh_rmse_range=float(sm.mesh_rmse_range_mAcm2.median()),
                   median_tol_rmse_range=float(sm.tol_rmse_range_mAcm2.median())),
              open(os.path.join(TAB, "e2_meta.json"), "w"), indent=2)

    # ============================ FIGURES ===================================
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]

    gids = rdf.groupby("test_index").group_id.first()
    gids = gids[gids.index.isin(refdf.test_index)]
    sids = list(gids.index)
    labs = [gids[s] for s in sids]

    # mesh convergence: full-window RMSE-vs-ref (log y) over element count
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.2), sharex=False)
    for ax, s, lb in zip(axs.ravel(), sids, labs):
        g = mesh[mesh.test_index == s].dropna(subset=["rmse_full_mAcm2"]).sort_values("nelem")
        if len(g) == 0:
            ax.set_title(f"{lb} (sid {s}) -- failed"); continue
        ax.plot(g.nelem, g.rmse_full_mAcm2, "o-", color=C[0], lw=1.6, ms=5)
        ref_ne = refs[s].nelem
        ax.axvline(ref_ne, ls=":", c="k", lw=1)
        ax.set_yscale("log")
        ax.set_title(f"{lb} (sid {s}, ref Pmax {refs[s].Pmax:.2f})")
        ax.set_xlabel("edge elements")
        ax.grid(alpha=0.3, which="both")
        if ax in (axs[0, 0],):
            ax.set_ylabel("RMSE vs frozen ref (mA/cm$^2$)")
    fig.suptitle("E2 mesh convergence: full J-V RMSE vs the frozen-config (runAll) reference", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(FIG, "e2_mesh_convergence.png"), dpi=150)
    plt.close(fig)

    # tolerance convergence
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.2))
    for ax, s, lb in zip(axs.ravel(), sids, labs):
        g = tol[tol.test_index == s].dropna(subset=["rmse_full_mAcm2"]).sort_values("stol", ascending=False)
        if len(g) == 0:
            ax.set_title(f"{lb} (sid {s}) -- failed"); continue
        ax.semilogx(g.stol, g.rmse_full_mAcm2, "o-", color=C[1], lw=1.6, ms=5)
        ax.set_title(f"{lb} (sid {s})")
        ax.set_xlabel("stationary stol")
        ax.grid(alpha=0.3, which="both")
        if ax in (axs[0, 0],):
            ax.set_ylabel("RMSE vs frozen ref (mA/cm$^2$)")
    fig.suptitle("E2 solver-tolerance convergence: full J-V RMSE vs frozen stol=1e-6 reference", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(FIG, "e2_tol_convergence.png"), dpi=150)
    plt.close(fig)

    # aggregate numerical error bars
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    x = np.arange(len(sids))
    axs[0].errorbar(x, sm.set_index("test_index").loc[sids, "mesh_rmse_range_mAcm2"], fmt="o", color=C[0])
    axs[0].set_yscale("log"); axs[0].set_xticks(x); axs[0].set_xticklabels(labs, rotation=30, ha="right", fontsize=8)
    axs[0].set_ylabel("max mesh-induced |dJ| RMSE (mA/cm$^2$)")
    axs[0].set_title("Mesh-level numerical range (m = 0.5..2.0)")
    axs[1].errorbar(x, sm.set_index("test_index").loc[sids, "tol_rmse_range_mAcm2"], fmt="o", color=C[1])
    axs[1].set_yscale("log"); axs[1].set_xticks(x); axs[1].set_xticklabels(labs, rotation=30, ha="right", fontsize=8)
    axs[1].set_ylabel("max tol-induced |dJ| RMSE (mA/cm$^2$)")
    axs[1].set_title("Tolerance numerical range (stol = 1e-4..1e-7)")
    fig.suptitle("E2 numerical error scale per parameter group (vs frozen-config reference)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(FIG, "e2_numerical_error.png"), dpi=150)
    plt.close(fig)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
