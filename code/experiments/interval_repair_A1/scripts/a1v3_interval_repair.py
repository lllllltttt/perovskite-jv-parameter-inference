# -*- coding: utf-8 -*-
"""
a1v3_interval_repair.py -- A1-v3: interval scoring + width analysis, HONEST labels.

Third-round directed repairs over round-2 A1 (v2 file is frozen/read-only):
  (1) SCALER-FIT SOURCE.  Round-2 labelled the normalized [0,1] envelope as the
      "TRAIN scaler envelope" (a1v2_meta.json scaler_fit, v2lib.param_scaler
      docstring, figure/comments).  Pre-process evidence + a direct partition
      check show the MinMaxScaler was fit on the FULL retained set
      (train 71432 + val 15307 + test 15307 = 102046) BEFORE the split.  This
      script re-derives that from the frozen npz + scaler (no code archaeology)
      and relabels everything.  The frozen scaler is NOT changed.
      Structural consequence, stated explicitly: test truth being inside [0,1]
      (true_oor_frac = 0) is BY CONSTRUCTION (the scaler saw the test set), so
      cov_raw == cov_clip is exact but is NOT independent evidence that the model
      stays inside the envelope.
  (2) WIDTH-FIGURE SORT BUG.  Round-2 sorted the width bars by parameter name
      alphabetically (sort_values("param")) while placing them at x positions
      labelled by PARAM_NAMES (canonical mu_n,mu_p,tau_n,...) -> data misaligned
      to labels.  Fixed by explicit re-index to PARAM_NAMES; an x-pos/label/data
      correspondence table is exported and asserted by the QC script.
  (3) MEAN vs MEDIAN.  Round-2 headline width ratios used medians only.  Here
      every width/score is reported as BOTH mean and median; claims state which.
  (4) RAW / CLIPPED / PRIOR kept separate.  Round-2 already separated raw
      Gaussian and clipped intervals.  This adds, per parameter, the raw width
      vs full-envelope width (a raw Gaussian can be WIDER than the whole [0,1]
      envelope for soft params) and the fraction of raw intervals that strictly
      contain or superset the envelope.
  (5) SOFT PARAMS @0.95 (tau_ETL / tau_HTL / rad_c): give raw AND clipped AND
      prior widths side by side, plus the sigma-at-ceiling / sigma-at-floor
      fractions, so "narrower than prior" is stated for the rectified interval
      and NOT for the raw Gaussian where it does not hold.
  (6) Conditional (grouped) calibration stays DIAGNOSTIC-ONLY, as in round 2.

Pure post-processing: frozen predictions replayed on the frozen scaler/encoder/
param_head over the frozen normalized test set.  No retraining, no recalibration,
no COMSOL.  Outputs under supplementary_validation_v3/A1_interval_repair/.
"""
import os, json, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "_tools"))
import v2lib
from v2lib import PARAM_NAMES, interval_score

A1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(A1, "outputs", "tables"); os.makedirs(TAB, exist_ok=True)
FIG = os.path.join(A1, "figures"); os.makedirs(FIG, exist_ok=True)
DAT = os.path.join(A1, "outputs", "data"); os.makedirs(DAT, exist_ok=True)
QCO = os.path.join(A1, "outputs", "qc"); os.makedirs(QCO, exist_ok=True)

LEV = [0.50, 0.80, 0.90, 0.95]
P = len(PARAM_NAMES)
EPS = 1e-9


def _wilson(ins, n, z=1.959963984540054):
    if n == 0:
        return (np.nan, np.nan)
    p = ins / n
    denom = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (cen - half, cen + half)


def hand_check_interval_score():
    val = interval_score(np.array([0.2]), np.array([0.6]), np.array([0.9]), 0.95)
    assert abs(val[0] - 12.4) < 1e-12, val
    v2 = interval_score(np.array([0.2]), np.array([0.6]), np.array([0.4]), 0.95)
    assert abs(v2[0] - 0.4) < 1e-12
    v3 = interval_score(np.array([0.2]), np.array([0.6]), np.array([0.1]), 0.95)
    assert abs(v3[0] - 0.4 - 40 * 0.1) < 1e-12
    v4 = interval_score(np.array([0.2]), np.array([0.6]), np.array([0.9]), 0.50)
    assert abs(v4[0] - 0.4 - 4 * 0.3) < 1e-12
    print("hand-check interval score OK (40 at c=0.95, 4 at c=0.50)")
    return True


def scaler_fit_source():
    """Empirical proof of WHERE the frozen scaler's min/max come from.
    Returns rows: per param, the partition(s) attaining the scaler log10 edge."""
    sc = v2lib.param_scaler()
    R = np.asarray(sc.data_range_, np.float64)
    Lmin = np.asarray(sc.data_min_, np.float64)
    d = v2lib.load_npz()
    parts = {}
    for nm in ("params_train", "params_val", "params_test"):
        X = d[nm].astype(np.float64)
        parts[nm] = (X.min(0), X.max(0))          # normalized per column
    rows = []
    for j in range(P):
        # normalized 0 -> Lmin[j]; 1 -> Lmin[j]+R[j]
        at_min = [nm for nm, (lo, _) in parts.items()
                  if abs(float(lo[j])) < 1e-9]
        at_max = [nm for nm, (_, hi) in parts.items()
                  if abs(float(hi[j]) - 1.0) < 1e-9]
        rows.append(dict(param=PARAM_NAMES[j],
                         scaler_lo_log10=float(Lmin[j]),
                         scaler_hi_log10=float(Lmin[j] + R[j]),
                         partition_at_min="+".join(at_min) or "none",
                         partition_at_max="+".join(at_max) or "none",
                         norm_min_over_all=0.0,
                         norm_max_over_all=1.0))
    full = pd.DataFrame(rows)
    n_all = int(d["params_train"].shape[0] + d["params_val"].shape[0]
                + d["params_test"].shape[0])
    return full, n_all


def main():
    assert hand_check_interval_score()
    from scipy.stats import norm
    Z = {a: float(norm.ppf(0.5 + a / 2.0)) for a in LEV}

    d = v2lib.load_npz()
    Y = d["params_test"].astype(np.float64)          # true normalized log10 (n,9)
    Ytr = d["params_train"].astype(np.float64)       # train-partition marginal
    Yphys = d["params_test_raw"].astype(np.float64)
    n, P = Y.shape
    sc = v2lib.param_scaler()
    R = np.asarray(sc.data_range_, np.float64)
    Lmin = np.asarray(sc.data_min_, np.float64)
    env_lo = Lmin
    env_hi = Lmin + R

    # ---- scaler-fit proof + honest envelope label --------------------------
    proof, n_all = scaler_fit_source()
    proof.to_csv(os.path.join(TAB, "a1v3_scaler_fit_source.csv"), index=False)
    ENV_LABEL = ("full retained set (train+val+test, n=%d) empirical min/max, "
                 "fit PRE-SPLIT on log10 params -- NOT train-only") % n_all
    print("scaler envelope =", ENV_LABEL)
    print(proof.to_string(index=False))

    # ---- frozen inference over the frozen test set -------------------------
    from infer_frozen import predict
    print("running frozen inference on test set (n=%d) ..." % n)
    pr = predict(d["J_test"].astype(np.float32))
    mu, sigma = pr["mu"], pr["sigma"]

    # sigma-at-clip statistics (per param, independent of level)
    sig = []
    for j in range(P):
        sig.append(dict(param=PARAM_NAMES[j],
                        frac_at_ceiling1=float(np.mean(np.isclose(sigma[:, j], 1.0, atol=EPS))),
                        frac_at_floor01=float(np.mean(np.isclose(sigma[:, j], 0.01, atol=EPS))),
                        med_sigma=float(np.median(sigma[:, j])),
                        mean_sigma=float(np.mean(sigma[:, j]))))
    pdsig = pd.DataFrame(sig)
    pdsig.to_csv(os.path.join(TAB, "a1v3_sigma_clip_stats.csv"), index=False)

    # ---- per-level, per-parameter metrics (raw | clipped | mean | median) --
    rows = []
    for a in LEV:
        zz = Z[a]
        lo_r = mu - zz * sigma
        hi_r = mu + zz * sigma                     # raw gaussian (may exceed [0,1])
        lo_c = np.clip(lo_r, 0.0, 1.0)
        hi_c = np.clip(hi_r, 0.0, 1.0)
        cov_r = ((Y >= lo_r) & (Y <= hi_r)).mean(axis=0)
        cov_c = ((Y >= lo_c) & (Y <= hi_c)).mean(axis=0)
        w_r = hi_r - lo_r
        w_c = hi_c - lo_c
        ydec = Y * R[None, :]
        isc_r = interval_score(lo_r * R[None, :], hi_r * R[None, :], ydec, a)
        isc_c = interval_score(lo_c * R[None, :], hi_c * R[None, :], ydec, a)
        for j in range(P):
            rows.append(dict(level=a, param=PARAM_NAMES[j], range_dec=float(R[j]),
                             cov_raw=float(cov_r[j]), cov_clip=float(cov_c[j]),
                             # raw width: mean & median, normalized & decades
                             wnorm_raw_mean=float(np.mean(w_r[:, j])),
                             wnorm_raw_med=float(np.median(w_r[:, j])),
                             wdec_raw_mean=float(np.mean(w_r[:, j]) * R[j]),
                             wdec_raw_med=float(np.median(w_r[:, j]) * R[j]),
                             wdec_raw_q10=float(np.percentile(w_r[:, j] * R[j], 10)),
                             wdec_raw_q90=float(np.percentile(w_r[:, j] * R[j], 90)),
                             # clipped width: mean & median
                             wnorm_clip_mean=float(np.mean(w_c[:, j])),
                             wnorm_clip_med=float(np.median(w_c[:, j])),
                             wdec_clip_mean=float(np.mean(w_c[:, j]) * R[j]),
                             wdec_clip_med=float(np.median(w_c[:, j]) * R[j]),
                             # scores: raw & clipped, mean & median (decade units)
                             is_dec_raw_mean=float(isc_r[:, j].mean()),
                             is_dec_raw_med=float(np.median(isc_r[:, j])),
                             is_dec_clip_mean=float(isc_c[:, j].mean()),
                             is_dec_clip_med=float(np.median(isc_c[:, j])),
                             # overhang / rectification indicators
                             frac_clipped=float(np.mean((lo_r[:, j] < 0) | (hi_r[:, j] > 1))),
                             frac_hi_clip=float(np.mean(hi_r[:, j] > 1.0)),
                             frac_lo_clip=float(np.mean(lo_r[:, j] < 0.0)),
                             frac_raw_wider_than_env=float(np.mean(w_r[:, j] >= 1.0 - EPS)),
                             frac_raw_superset_env=float(np.mean((lo_r[:, j] <= 0.0) & (hi_r[:, j] >= 1.0))),
                             mu_oor_frac=float(np.mean((mu[:, j] < 0) | (mu[:, j] > 1))),
                             true_oor_frac=float(np.mean((Y[:, j] < 0) | (Y[:, j] > 1)))))
    pm = pd.DataFrame(rows)
    pm.to_csv(os.path.join(TAB, "a1v3_interval_metrics.csv"), index=False)

    # ---- prior baseline (train-partition marginal), ACTUAL test coverage ----
    prs = []
    for a in LEV:
        zq = [(1 - a) / 2, (1 + a) / 2]
        qlo = np.quantile(Ytr, zq[0], axis=0)
        qhi = np.quantile(Ytr, zq[1], axis=0)
        wdec = np.clip(qhi - qlo, 0, None) * R
        cov = ((Y >= qlo[None, :]) & (Y <= qhi[None, :])).mean(axis=0)
        ydec = Y * R[None, :]
        isc = interval_score(qlo[None, :] * R[None, :], qhi[None, :] * R[None, :], ydec, a)
        for j in range(P):
            prs.append(dict(level=a, param=PARAM_NAMES[j],
                            prior_wdec=float(wdec[j]),
                            prior_is_dec_mean=float(isc[:, j].mean()),
                            prior_cov_test=float(cov[j])))
    pbase = pd.DataFrame(prs)
    pbase.to_csv(os.path.join(TAB, "a1v3_prior_baseline.csv"), index=False)

    # ---- model-vs-prior at the SAME nominal level --------------------------
    cmp_ = pm.merge(pbase, on=["level", "param"])
    cmp_["ratio_clip_med"] = cmp_.wdec_clip_med / cmp_.prior_wdec
    cmp_["ratio_clip_mean"] = cmp_.wdec_clip_mean / cmp_.prior_wdec
    cmp_["ratio_raw_med"] = cmp_.wdec_raw_med / cmp_.prior_wdec
    cmp_["ratio_raw_mean"] = cmp_.wdec_raw_mean / cmp_.prior_wdec
    cmp_["dcov_model_clip_minus_prior"] = cmp_.cov_clip - cmp_.prior_cov_test
    cmp_.to_csv(os.path.join(TAB, "a1v3_model_vs_prior.csv"), index=False)

    # ---- grouped (conditional) calibration -- DIAGNOSTIC ONLY -------------
    Jraw = d["J_test_raw"].astype(np.float64)
    Jsc = np.abs(Jraw[:, 0])
    pv = np.where(Jraw >= 0, Jraw * v2lib.V[None, :], np.nan)
    PCE = np.nanmax(pv, axis=1)

    def terc(x):
        q1, q2 = np.quantile(x, [1 / 3, 2 / 3])
        return np.digitize(x, [q1, q2])

    g_pce = terc(PCE)
    g_rows = []
    for a in LEV:
        zz = Z[a]
        lo_r = mu - zz * sigma
        hi_r = mu + zz * sigma
        lo_c = np.clip(lo_r, 0, 1)
        hi_c = np.clip(hi_r, 0, 1)
        ins_c = (Y >= lo_c) & (Y <= hi_c)
        ydec = Y * R[None, :]
        isc_c = interval_score(lo_c * R[None, :], hi_c * R[None, :], ydec, a)
        for j in range(P):
            g_sig = terc(sigma[:, j])
            g_y = terc(Y[:, j])
            for gname, gv in (("own_sigma", g_sig), ("PCE", g_pce), ("true_param", g_y)):
                for gi in range(3):
                    m = gv == gi
                    nn = int(m.sum())
                    if nn < 10:
                        continue
                    cov = float(ins_c[m, j].mean())
                    lo_ci, hi_ci = _wilson(int(ins_c[m, j].sum()), nn)
                    g_rows.append(dict(level=a, param=PARAM_NAMES[j],
                                       group=f"{gname}_terc{gi}", n=nn, cov=round(cov, 5),
                                       cov_ci_lo=round(lo_ci, 5), cov_ci_hi=round(hi_ci, 5),
                                       wdec_clip_med=float(np.median((hi_c[m, j] - lo_c[m, j]) * R[j])),
                                       is_dec_clip_med=float(np.median(isc_c[m, j])),
                                       diag_only=True))
        # merged-over-params diagnostic rows flagged diag_only
        for gname, gv in (("sigma_mean", terc(sigma.mean(axis=1))), ("PCE", g_pce)):
            for gi in range(3):
                m = gv == gi
                nn = int(m.sum())
                if nn < 10:
                    continue
                g_rows.append(dict(level=a, param="ALL9(merged)", group=f"{gname}_terc{gi}",
                                   n=nn, cov=round(float(ins_c[m].mean()), 5),
                                   cov_ci_lo=np.nan, cov_ci_hi=np.nan,
                                   wdec_clip_med=float(np.median((hi_c[m] - lo_c[m]).mean(axis=1) * R.mean())),
                                   is_dec_clip_med=float(np.median(
                                       interval_score(lo_c[m] * R[None, :], hi_c[m] * R[None, :],
                                                      (Y * R[None, :])[m], a).mean(axis=1))),
                                   diag_only=True))
    gdf = pd.DataFrame(g_rows)
    gdf.to_csv(os.path.join(TAB, "a1v3_grouped_calibration.csv"), index=False)

    # ---- summary numbers ---------------------------------------------------
    print("\n=== per-parameter coverage & width at each level (raw | clipped) ===")
    for a in LEV:
        sub = pm[pm.level == a]
        print("level %.2f  cov_raw[med %.3f] cov_clip[med %.3f] | "
              "wdec clip med-mean %.3f/%.3f | raw med-mean %.3f/%.3f" %
              (a, sub.cov_raw.median(), sub.cov_clip.median(),
               sub.wdec_clip_med.median(), sub.wdec_clip_mean.median(),
               sub.wdec_raw_med.median(), sub.wdec_raw_mean.median()))
    print("\n@0.95 model/prior width ratios per param (clip-med | clip-mean | raw-med | raw-mean):")
    c95 = cmp_[cmp_.level == 0.95].set_index("param").loc[PARAM_NAMES]
    print(c95[["ratio_clip_med", "ratio_clip_mean", "ratio_raw_med", "ratio_raw_mean"]]
          .round(3).to_string())
    print("\n@0.95 raw width vs envelope (frac_raw_superset_env) and sigma-clip rates:")
    p95 = pm[pm.level == 0.95].set_index("param").loc[PARAM_NAMES]
    show = pd.concat([p95[["wdec_raw_med", "wdec_clip_med", "range_dec",
                           "frac_raw_wider_than_env", "frac_clipped"]],
                      pdsig.set_index("param").loc[PARAM_NAMES][["frac_at_ceiling1",
                                                                 "frac_at_floor01"]]], axis=1)
    print(show.round(3).to_string())

    # ---- exports -----------------------------------------------------------
    cr = v2lib.test_index_to_sample_id()
    sid = v2lib.sample_ids()[cr]
    np.savez_compressed(
        os.path.join(DAT, "a1v3_reusable_test.npz"),
        test_index=np.arange(n), sample_id=sid.astype(np.int64),
        Y_true_norm=Y, Y_true_log10=v2lib.norm_to_log10(Y), Y_true_phys=Yphys,
        mu_norm=mu, sigma_norm=sigma,
        mu_log10=v2lib.norm_to_log10(mu),
        env_fullset_lo_log10=env_lo, env_fullset_hi_log10=env_hi,
        R_decades=R, levels=np.asarray(LEV))
    np.savez_compressed(os.path.join(DAT, "a1v3_train_prior.npz"),
                        params_train_norm=Ytr,
                        params_train_log10=v2lib.norm_to_log10(Ytr))
    json.dump(dict(n_test=int(n), n_retained_all=int(n_all), levels=LEV,
                   scaler_fit=ENV_LABEL,
                   scaler_fit_note=("fitted PRE-SPLIT on log10 params of the full retained "
                                    "set; test lies in [0,1] BY CONSTRUCTION -> cov_raw==cov_clip "
                                    "is exact but not independent evidence of in-envelope behaviour; "
                                    "frozen scaler unchanged"),
                   interval_score="Gneiting-Raftery Eq43: w + 2/(1-c)*(outside penalty)",
                   envelope_note="[0,1] = full-retained-set (train+val+test) empirical min/max, "
                                 "not the full generative support",
                   env_lo_log10=env_lo.tolist(), env_hi_log10=env_hi.tolist(),
                   R_decades=R.tolist()),
              open(os.path.join(TAB, "a1v3_meta.json"), "w"), indent=2, default=float)

    # ---- figures (width ordering FIXED to PARAM_NAMES) ----------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = np.arange(P)
    # explicit canonical ordering used for EVERY bar figure
    o = pm.set_index(["level", "param"]).loc[pd.MultiIndex.from_product([LEV, PARAM_NAMES])]
    opb = pbase.set_index(["level", "param"]).loc[pd.MultiIndex.from_product([LEV, PARAM_NAMES])]
    # x-pos <-> label <-> data-param correspondence (all levels share x order)
    corr = pd.DataFrame(dict(x_pos=x, tick_label=PARAM_NAMES, data_param=PARAM_NAMES))
    corr.to_csv(os.path.join(TAB, "a1v3_width_fig_correspondence.csv"), index=False)

    C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
    # 1) width at all 4 levels: raw-med hollow + clip-med solid + prior markers
    fig, ax = plt.subplots(figsize=(12, 5.6))
    wd = 0.20
    for i, a in enumerate(LEV):
        sub = o.loc[(a, slice(None))]
        prb = opb.loc[(a, slice(None))]
        off = (i - 1.5) * wd
        ax.bar(x + off, sub.wdec_clip_med.values, wd, color=C[i], alpha=0.95,
               label=f"model clipped level {a:.2f}")
        ax.plot(x + off, sub.wdec_raw_med.values, "o", ms=3, mfc="none",
                mec=C[i], label=f"model RAW-med level {a:.2f}")
        ax.plot(x + off, prb.prior_wdec.values, "k*", ms=6,
                label=f"prior level {a:.2f}")
    ax.set_xticks(x)
    ax.set_xticklabels(PARAM_NAMES, rotation=30, ha="right")
    ax.set_ylabel("interval width (log$_{10}$ decades)")
    ax.set_title("A1-v3 width per parameter: clipped(med) bars, RAW(med) open, prior(*); "
                 "x-order = PARAM_NAMES (sort bug fixed)")
    ax.legend(fontsize=6, ncol=4, loc="upper left")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "a1v3_width_comparison.png"), dpi=150)
    plt.close(fig)

    # 2) coverage raw vs clipped vs prior-actual vs nominal (4 levels x 9 params)
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.6), sharey=True)
    for ax_, a in zip(axs, LEV):
        sub = pm[pm.level == a].set_index("param").loc[PARAM_NAMES]
        pb = pbase[pbase.level == a].set_index("param").loc[PARAM_NAMES]
        ww = 0.26
        ax_.bar(x - ww, sub.cov_raw, ww, color="#56B4E9", label="model raw")
        ax_.bar(x, sub.cov_clip, ww, color="#0072B2", label="model clipped")
        ax_.bar(x + ww, pb.prior_cov_test, ww, color="#999999", label="prior (test)")
        ax_.axhline(a, ls="--", c="k", lw=1.1)
        ax_.set_xticks(x)
        ax_.set_xticklabels(PARAM_NAMES, rotation=90, fontsize=7)
        ax_.set_ylim(0.2, 1.02)
        ax_.set_title(f"nominal {a:.2f}")
        if a == LEV[0]:
            ax_.set_ylabel("empirical coverage")
            ax_.legend(fontsize=7)
    fig.suptitle("A1-v3 marginal coverage per parameter: raw & clipped intervals, "
                 "prior measured on test", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(FIG, "a1v3_coverage.png"), dpi=150)
    plt.close(fig)

    # 3) grouped calibration diagnostic (tau_n / tau_p @0.95) -- diag only
    for pp in ("tau_n", "tau_p"):
        gsub = gdf[(gdf["param"] == pp) & (gdf["level"] == 0.95)]
        fig, ax = plt.subplots(figsize=(9, 4.2))
        for gn in ("own_sigma_terc0", "own_sigma_terc1", "own_sigma_terc2",
                   "true_param_terc0", "true_param_terc1", "true_param_terc2"):
            g = gsub[gsub["group"] == gn]
            if not len(g):
                continue
            cv = float(g["cov"].iloc[0])
            cilo = float(g["cov_ci_lo"].iloc[0])
            cihi = float(g["cov_ci_hi"].iloc[0])
            ax.errorbar([gn], [cv], yerr=[[cv - cilo], [cihi - cv]], fmt="o", ms=6)
        ax.axhline(0.95, ls="--", c="k", lw=1)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right")
        ax.set_ylim(0.6, 1.05)
        ax.set_ylabel("coverage at nominal 0.95")
        ax.grid(alpha=0.3, axis="y")
        ax.set_title(f"A1-v3 conditional coverage (DIAGNOSTIC-ONLY), {pp} @95%")
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f"a1v3_grouped_{pp}.png"), dpi=150)
        plt.close(fig)

    print("\nwrote tables + figures + reusable npz under", A1)
    print("ENVELOPE LABEL:", ENV_LABEL)


if __name__ == "__main__":
    main()
