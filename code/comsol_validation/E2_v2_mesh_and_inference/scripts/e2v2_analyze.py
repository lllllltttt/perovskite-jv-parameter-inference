# -*- coding: utf-8 -*-
"""
e2v2_analyze.py -- windowed mesh/tolerance convergence tables for E2-v2.

Ingests E2 curve rows (old 48-row manifest under supplementary_validation/E2,
plus, when present, v2 fine-mesh rows under this task's outputs) and writes:

  e2v2_mesh_windowed_rmse.csv  per-row windowed RMSE vs 3 references:
                               (a) frozen m=1 ref row, (b) adjacent-finer mesh,
                               (c) finest mesh present; + vs-target DB curve.
                               windows full/le1/gt1/gen0/gtvoc/mpp, n per window.
  e2v2_device_metrics.csv      per-row Jsc/Voc/Vmp/Pmax/FF/PCE (interp Voc),
                               dX and dX% vs the sample's ref (m=1) row.
  e2v2_rel_gt1.csv             >1 V window in *relative* |dJ|/|J_ref| quantiles
                               (absolute RMSE there is dominated by the steep
                               high-|J| region; NOT used for convergence).

Window rules come from the TARGET curve (voc interp / vmp discrete), shared by
every row of a sample -> all curves compared on identical point sets.
COMSOL curves are A/m2 (x0.1 -> mA/cm2); target curves are mA/cm2 (npz).
Run again after the v2 fine-mesh solves exist: they are picked up automatically.
"""
import os, sys, glob, re
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_tools"))
import v2lib
from v2lib import device_metrics, window_masks, V, AM2

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = r"E:\project\work1"
OLD_CUR = os.path.join(BASE, "supplementary_validation", "E2", "outputs", "curves")
V2_CUR = os.path.join(TASK, "outputs", "curves")
OUTDIR = os.path.join(TASK, "outputs")
os.makedirs(OUTDIR, exist_ok=True)
WINDOWS = ["full", "le1", "gt1", "gen0", "gtvoc", "mpp"]

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
                        elapsed=float(meta.get("elapsed_s", np.nan)),
                        J=np.asarray(body) * AM2))
    return pd.DataFrame(out)

def main():
    npz = np.load(os.path.join(BASE, "data", "dataset_normalized.npz"), allow_pickle=True)
    JT = npz["J_test_raw"].astype(np.float64)
    old = load_rows(OLD_CUR)
    v2 = load_rows(V2_CUR)
    rows = pd.concat([old, v2], ignore_index=True)
    print("old E2 curves parsed: %d ; v2 fine-mesh curves present: %d ; total %d"
          % (len(old), len(v2), len(rows)))
    if len(rows) == 0:
        print("no curves; nothing to do"); return

    # target masks per sample (single shared reference)
    ref_row = rows[rows.level_type == "ref"].sort_values("test_index").reset_index(drop=True)
    tab_rows = []
    for _, r in rows.iterrows():
        voc_t = device_metrics(JT[r.test_index], voc_mode="interp")["Voc"]
        vmp_t = device_metrics(JT[r.test_index], voc_mode="interp")["Vmp"]
        msk = window_masks(voc_t, vmp_t)
        rec = dict(rowid=int(r.rowid), test_index=int(r.test_index), level_type=r.level_type,
                   level=r.level, mesh=r.mesh, stol=r.stol, nelem=int(r.nelem),
                   elapsed=float(r.elapsed))
        for nm in WINDOWS:
            rec["n_" + nm] = int(msk[nm].sum())
        # vs target DB curve (COMSOL reproduction context; Audits C/D already ~1e-6)
        rw = {}
        for nm in WINDOWS:
            m = msk[nm]
            if m.sum():
                d = JT[r.test_index][m] - r.J[m]
                rw["vs_target_rmse_" + nm] = float(np.sqrt(np.mean(d * d)))
        rec.update(rw)
        tab_rows.append(rec)
    tab = pd.DataFrame(tab_rows)

    # device metrics per row + diffs vs sample ref
    dm_rows = []
    refM = ref_row.set_index("test_index")
    for _, r in rows.iterrows():
        d0 = device_metrics(refM.loc[r.test_index, "J"], voc_mode="interp") if r.test_index in refM.index else {}
        d = device_metrics(r.J, voc_mode="interp")
        rec = dict(test_index=int(r.test_index), rowid=int(r.rowid), level_type=r.level_type,
                   level=r.level, mesh=r.mesh, stol=r.stol, nelem=int(r.nelem))
        for c in ["Jsc", "Voc", "Vmp", "Pmax", "FF", "PCE"]:
            v, v0 = d[c], d0.get(c, np.nan)
            rec[c] = v
            rec["d" + c] = v - v0
            rec["d" + c + "_pct"] = (v - v0) / v0 * 100.0 if (np.isfinite(v0) and v0 != 0) else np.nan
        dm_rows.append(rec)
    dm = pd.DataFrame(dm_rows)

    # ---- mesh-difference windows (default-tol ref+mesh chains only) ----
    # build, per sample, the sorted chain of (m, J) at default tol
    mesh_default = rows[(rows.level_type == "ref") | (rows.level_type == "mesh")]
    mesh_default = mesh_default[np.isclose(mesh_default.stol, 1e-6)]
    chains = {ti: g.sort_values("mesh") for ti, g in mesh_default.groupby("test_index")}
    for nm in WINDOWS:
        tab["vs_ref_rmse_" + nm] = np.nan
        tab["vs_adj_rmse_" + nm] = np.nan
        tab["vs_finest_rmse_" + nm] = np.nan
    for ti, ch in chains.items():          # ch sorted by mesh ASCENDING
        voc_t = device_metrics(JT[ti], voc_mode="interp")["Voc"]
        vmp_t = device_metrics(JT[ti], voc_mode="interp")["Vmp"]
        msk = window_masks(voc_t, vmp_t)
        ch = ch.reset_index(drop=True)
        iref = int(np.flatnonzero(ch.level_type.values == "ref")[0])   # frozen m=1
        Jref = ch.J.iloc[iref]
        Jfin = ch.J.iloc[0]                 # smallest mesh = finest
        for i, (_, r) in enumerate(ch.iterrows()):
            sel = tab.rowid == r.rowid
            for nm in WINDOWS:
                m = msk[nm]
                if m.sum() == 0:
                    continue
                tab.loc[sel, "vs_ref_rmse_" + nm] = np.sqrt(np.mean((r.J[m] - Jref[m]) ** 2))
                tab.loc[sel, "vs_finest_rmse_" + nm] = np.sqrt(np.mean((r.J[m] - Jfin[m]) ** 2))
                if i > 0:                    # adjacent FINER mesh = next lower mesh index
                    jn = ch.J.iloc[i - 1]
                    tab.loc[sel, "vs_adj_rmse_" + nm] = np.sqrt(np.mean((r.J[m] - jn[m]) ** 2))
    # ---- relative >1V error vs frozen ref (m=1) ----
    rel_rows = []
    for ti, ch in chains.items():
        ch = ch.reset_index(drop=True)
        iref = int(np.flatnonzero(ch.level_type.values == "ref")[0])
        J0 = ch.J.iloc[iref]
        gt = V > 1.0
        denom = np.abs(J0[gt]); sel = denom > 1e-6
        for _, r in ch.iterrows():
            d = np.abs(r.J[gt][sel] - J0[gt][sel]) / denom[sel]
            rel_rows.append(dict(test_index=int(ti), rowid=int(r.rowid), level_type=r.level_type,
                                 level=r.level, mesh=r.mesh, stol=r.stol, nelem=int(r.nelem),
                                 rel_gt1_med=float(np.median(d)), rel_gt1_p90=float(np.quantile(d, 0.90)),
                                 rel_gt1_p99=float(np.quantile(d, 0.99)), rel_gt1_max=float(np.max(d))))
    rel = pd.DataFrame(rel_rows)

    tab.to_csv(os.path.join(OUTDIR, "e2v2_mesh_windowed_rmse.csv"), index=False)
    dm.to_csv(os.path.join(OUTDIR, "e2v2_device_metrics.csv"), index=False)
    rel.to_csv(os.path.join(OUTDIR, "e2v2_rel_gt1.csv"), index=False)
    # per-sample mesh summary (default tol chain)
    chsum = tab[tab.level_type.isin(["ref", "mesh"])].sort_values(["test_index", "mesh"])
    cols = ["test_index", "level_type", "level", "mesh", "nelem",
            "vs_ref_rmse_gen0", "vs_ref_rmse_le1", "vs_ref_rmse_gt1", "vs_ref_rmse_full",
            "vs_finest_rmse_gen0", "vs_adj_rmse_gen0", "vs_target_rmse_full"]
    cols = [c for c in cols if c in chsum.columns]
    print(chsum[cols].round(5).to_string(index=False))
    print("\nsaved: e2v2_mesh_windowed_rmse.csv / e2v2_device_metrics.csv / e2v2_rel_gt1.csv ->", OUTDIR)

if __name__ == "__main__":
    main()
