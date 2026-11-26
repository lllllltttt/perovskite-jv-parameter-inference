"""
auditA_mapping_AB.py  (Audit A + B: sample-chain mapping and metric definitions)

Reproduces, from frozen local data only:
  Audit A  - the Sample_ID chain for the 45-sample forward-validation cohort and
             the six Fig. S3a cycle-case panels
             (panel label "#595" -> npz test array index 595 -> DB-2 row ->
              original LHS Sample_ID -> target curve -> device metrics).
  Audit B  - the "Param log10-RMSE" definition (raw log10 vs min-max-normalized
             log10) and the Voc extraction method (grid-node vs linear interp).

No files are modified. Outputs are written to supplementary_validation/audit/.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
DBCSV = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-2.csv")
FWMET = os.path.join(BASE, "forward_validation_unbiased", "forward_metrics_per_sample.csv")
FWPAR = os.path.join(BASE, "forward_validation_unbiased", "param_error_posthoc.csv")
OUT = HERE

PARAM_COLS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
              "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]

z = np.load(NPZ, allow_pickle=True)
Jraw = z["J_test_raw"]                      # (15307, 131) physical mA/cm2
V = np.linspace(0.0, 1.3, 131)


def device_metrics_gridvoc(a):
    """Grid-node Voc = first grid point with J <= 0 (the archived recipe)."""
    jsc = float(np.abs(a[0]))
    neg = a <= 0
    if not neg.any():
        return jsc, np.nan, np.nan, np.nan
    k = int(np.argmax(neg))
    voc = float(V[k])
    p = a * V
    pm = float(np.nanmax(np.where(p > 0, p, np.nan)))
    ff = pm / (jsc * voc) if jsc * voc > 0 else np.nan
    return jsc, voc, ff, jsc * voc * ff


def device_metrics_interpvoc(a):
    """Linear-interpolated Voc (first +->- crossing, ascending bracket)."""
    jsc = float(np.abs(a[0]))
    d = np.diff(np.sign(a))
    idx = np.where(d < 0)[0]
    if len(idx) == 0:
        return jsc, np.nan, np.nan, np.nan
    k = int(idx[0])
    vk, vk1 = V[k], V[k + 1]
    jk, jk1 = float(a[k]), float(a[k + 1])
    voc = float(vk + (0.0 - jk) / (jk1 - jk) * (vk1 - vk))
    p = a * V
    pm = float(np.nanmax(np.where(p > 0, p, np.nan)))
    ff = pm / (jsc * voc) if jsc * voc > 0 else np.nan
    return jsc, voc, ff, jsc * voc * ff


def main():
    fw = pd.read_csv(FWMET)
    assert len(fw) == 45
    # ---- recover LHS Sample_ID by exact match of the 9 param columns ----
    db = pd.read_csv(DBCSV)
    dbf = db[PARAM_COLS].values
    lk = {}
    for i in range(len(db)):
        lk.setdefault(",".join("%.17g" % x for x in dbf[i]), []).append(i)

    rows = []
    for _, r in fw.iterrows():
        ti = int(r["test_index"])
        key = ",".join("%.17g" % x for x in z["params_test_raw"][ti])
        cand = lk.get(key, [])
        dbrow = cand[0] if len(cand) == 1 else (-1 if len(cand) == 0 else -2)
        lhs_id = db.iloc[dbrow]["Sample_ID"] if dbrow >= 0 else np.nan
        jg, vg, fg, pg = device_metrics_gridvoc(Jraw[ti])
        ji, vi, fi, pi = device_metrics_interpvoc(Jraw[ti])
        rows.append(dict(
            test_index=ti, n_db_cand=len(cand), db_row=dbrow, lhs_sample_id=lhs_id,
            Jsc_raw=Jraw[ti, 0],
            jsc_grid=round(jg, 6), voc_grid=round(vg, 6), ff_grid=round(fg, 6), pce_grid=round(pg, 6),
            voc_interp=round(vi, 6), ff_interp=round(fi, 6), pce_interp=round(pi, 6),
            stored_Jsc_t=r["Jsc_t"], stored_Voc_t=r["Voc_t"], stored_FF_t=r["FF_t"],
            stored_PCE_t=r["PCE_t"], stored_param_rmse=r["param_log10_rmse"],
        ))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "auditA_sample_mapping.csv"), index=False)

    # ---- checks ----
    n_uniq = (out["n_db_cand"] == 1).sum()
    print("cohort test-indices uniquely mapped to DB-2 row:", n_uniq, "/", len(out))
    # stored Jsc matches recomputed grid Jsc (abs) and raw?
    print("stored Jsc_t == raw Jsc (abs):", np.allclose(out.stored_Jsc_t, np.abs(out.Jsc_raw), atol=1e-6))
    print("stored Voc_t == grid-node voc:", np.allclose(out.stored_Voc_t, out.voc_grid, atol=1e-9))
    print("stored Voc_t == interp voc:", np.allclose(out.stored_Voc_t, out.voc_interp, atol=1e-9))
    print("max |stored_voc - interp|:", (out.stored_Voc_t - out.voc_interp).abs().max())
    print("max |stored_ff - interp_ff|:", (out.stored_FF_t - out.ff_interp).abs().max())
    print("stored PCE == grid PCE:", np.allclose(out.stored_PCE_t, out.pce_grid, atol=1e-9))

    # ---- Audit B: param RMSE definition for the six Fig-S3a samples ----
    fp = np.load(os.path.join(BASE, "final_figures", "scripts", "_frozen_preds.npz"), allow_pickle=True)
    pm = fp["param_mu"]; pt = fp["params_test"]; pph = fp["params_pred_phys"]
    praw = fp["params_test_raw"]
    fig_ids = [12058, 4077, 595, 695, 14499]
    b_rows = []
    for sid in fig_ids + [595]:
        raw = float(np.sqrt(np.mean((np.log10(pph[sid]) - np.log10(praw[sid])) ** 2)))
        norm = float(np.sqrt(np.mean((pm[sid] - pt[sid]) ** 2)))
        stored = float(out.loc[out.test_index == sid, "stored_param_rmse"].iloc[0])
        b_rows.append(dict(test_index=sid, raw_log10_rmse=raw, norm_log10_rmse=norm, stored=sid if False else stored,
                           equals_raw=np.isclose(raw, stored, atol=1e-9),
                           equals_norm=np.isclose(norm, stored, atol=1e-9)))
    bdf = pd.DataFrame(b_rows)
    bdf.to_csv(os.path.join(OUT, "auditB_param_metric.csv"), index=False)
    print(bdf.to_string(index=False))

    # ---- Audit A: the six Fig-S3a case rows ----
    print(out[out.test_index.isin(fig_ids + [595])].to_string(index=False))


if __name__ == "__main__":
    main()
