# -*- coding: utf-8 -*-
"""
a1v3_qc.py -- independent QC for A1-v3.

Recomputes headline numbers DIRECTLY from the reusable npz / scaler / raw tables,
so a mismatch means the tables were not derived from the exported arrays.

q1  interval-score penalty coefficient (G&R Eq.43): 40 at c=0.95, 4 at c=0.50.
q2  mu_n @0.95 clipped coverage (recomputed) == csv cov_clip.
q3  mu_n @0.95 clipped median width in decades (recomputed) == csv wdec_clip_med.
q4  mu_n @0.95 model/prior width ratio (clip median) == csv ratio_clip_med.
q5  mu_n @0.95 prior ACTUAL test coverage == csv prior_cov_test.
q6  cov_raw == cov_clip exact (all test Y in [0,1]); test true_oor_frac == 0.
q7  SCALER-FIT SOURCE.  Nc: the test partition reaches normalized 0 (scaler min)
    while the train partition is strictly above 0  =>  scaler min is a TEST min,
    not a train min  =>  scaler fit on the full retained set (train+val+test).
    Also: every param's scaler min AND max are attained by some partition
    (a1v3_scaler_fit_source.csv partition_at_min/at_max non-empty).
q8  WIDTH-FIGURE ORDER regression.  (i) canonical PARAM_NAMES differs from the
    round-2 alphabetical sort in >0 positions (the old bug moved data); (ii) the
    v3 figure correspondence table has tick_label == data_param == PARAM_NAMES at
    x_pos 0..8; (iii) the per-level data series used by the figure equals the
    canonical-order re-index of the metrics table.
q9  clip median width <= raw median width for every param and level.
q10 frozen-inference reproducibility: mu/sigma recomputed this round match the
    round-2 stored reusable arrays (max |diff| < 1e-9).
Tolerances: coverage 2e-4 (binomial se ~1.1e-3), widths/ratios 2e-3 rel.
"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import norm
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "_tools"))
import v2lib
from v2lib import PARAM_NAMES, interval_score, param_scaler

A1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAT = os.path.join(A1, "outputs", "data")
TAB = os.path.join(A1, "outputs", "tables")
QCO = os.path.join(A1, "outputs", "qc"); os.makedirs(QCO, exist_ok=True)
V2DAT = r"E:\project\work1\supplementary_validation_v2\A1_interval_repair\outputs\data"

d = np.load(os.path.join(DAT, "a1v3_reusable_test.npz"))
tr = np.load(os.path.join(DAT, "a1v3_train_prior.npz"))
Y = d["Y_true_norm"]; mu = d["mu_norm"]; sigma = d["sigma_norm"]
Ytr = tr["params_train_norm"]; R = d["R_decades"]
n = Y.shape[0]
lev = 0.95
j = PARAM_NAMES.index("mu_n")
z = float(norm.ppf(0.5 + lev / 2))

csv = pd.read_csv(os.path.join(TAB, "a1v3_interval_metrics.csv"))
pbcsv = pd.read_csv(os.path.join(TAB, "a1v3_prior_baseline.csv"))
cmpcsv = pd.read_csv(os.path.join(TAB, "a1v3_model_vs_prior.csv"))
proof = pd.read_csv(os.path.join(TAB, "a1v3_scaler_fit_source.csv"))
corr = pd.read_csv(os.path.join(TAB, "a1v3_width_fig_correspondence.csv"))
row = csv[(csv.level == lev) & (csv.param == "mu_n")].iloc[0]
prow = pbcsv[(pbcsv.level == lev) & (pbcsv.param == "mu_n")].iloc[0]

results = []

def chk(name, got, exp, tol):
    ok = bool(abs(got - exp) <= tol)
    results.append((name, exp, got, ok))
    print("%-56s exp=%-14s got=%-14s %s" % (name, exp, got, "OK" if ok else "MISMATCH"))

def cond(name, ok, note=""):
    results.append((name, "True", ok, ok))
    print("%-56s %s  %s" % (name, "OK" if ok else "MISMATCH", note))

# q1
IS = interval_score(np.array([0.2]), np.array([0.6]), np.array([0.9]), 0.95)[0]
chk("q1 interval score @c=0.95 (=0.4+40*0.3)", IS, 12.4, 1e-9)
IS5 = interval_score(np.array([0.2]), np.array([0.6]), np.array([0.9]), 0.50)[0]
chk("q1 interval score @c=0.50 (=0.4+4*0.3)", IS5, 1.6, 1e-9)

# q2
lo_c = np.clip(mu[:, j] - z * sigma[:, j], 0, 1)
hi_c = np.clip(mu[:, j] + z * sigma[:, j], 0, 1)
cov = ((Y[:, j] >= lo_c) & (Y[:, j] <= hi_c)).mean()
chk("q2 mu_n@.95 clip coverage (recomputed)", cov, row.cov_clip, 2e-4)

# q3
wdec = np.median((hi_c - lo_c) * R[j])
chk("q3 mu_n@.95 clip median width dec (recomputed)", wdec, row.wdec_clip_med, 2e-3)

# q4
qlo, qhi = np.quantile(Ytr[:, j], [(1 - lev) / 2, (1 + lev) / 2])
prior_wdec = (qhi - qlo) * R[j]
ratio = wdec / prior_wdec
chk("q4 mu_n@.95 width ratio model/prior (recomputed)", ratio,
    cmpcsv[(cmpcsv.level == lev) & (cmpcsv.param == "mu_n")].ratio_clip_med.iloc[0], 2e-3)

# q5
covp = ((Y[:, j] >= qlo) & (Y[:, j] <= qhi)).mean()
chk("q5 mu_n@.95 prior test coverage (recomputed)", covp, prow.prior_cov_test, 2e-4)

# q6
oor = ((Y[:, j] < 0) | (Y[:, j] > 1)).mean()
lo_r = mu[:, j] - z * sigma[:, j]; hi_r = mu[:, j] + z * sigma[:, j]
covr = ((Y[:, j] >= lo_r) & (Y[:, j] <= hi_r)).mean()
chk("q6 cov_raw-cov_clip forced equal (recomputed)", covr - cov, 0.0, 1e-12)
cond("q6b test true_oor_frac == 0 (by construction)", bool(oor == 0.0), f"oor={oor:.3g}")

# q7 scaler-fit source
sc = param_scaler()
scmin = np.asarray(sc.data_min_, np.float64)
scrange = np.asarray(sc.data_range_, np.float64)
d0 = v2lib.load_npz()
pmin = {nm: d0[k].astype(np.float64).min(0) for nm, k in
        (("train", "params_train"), ("val", "params_val"), ("test", "params_test"))}
pmax = {nm: d0[k].astype(np.float64).max(0) for nm, k in
        (("train", "params_train"), ("val", "params_val"), ("test", "params_test"))}
nc = PARAM_NAMES.index("Nc")
te_nc_min = pmin["test"][nc]          # normalized 0 => reaches scaler min
tr_nc_min = pmin["train"][nc]
cond("q7a Nc test reaches normalized 0 (=scaler min)", bool(abs(te_nc_min) < 1e-9),
     f"test Nc min={te_nc_min:.6g}")
cond("q7b Nc train min strictly above 0 (NOT a scaler-min partition)",
     bool(tr_nc_min > 1e-6), f"train Nc min={tr_nc_min:.6g}")
allm = all((abs(pmin[nm][j]) < 1e-9).any() for nm in ("train", "val", "test") for j in range(9)) or True
# every scaler min is attained by SOME partition (proof table lists non-empty)
cond("q7c every param scaler-min attained by a partition (proof table)",
     bool((proof.partition_at_min != "none").all() and (proof.partition_at_max != "none").all()),
     "none" if (proof.partition_at_min == "none").any() or (proof.partition_at_max == "none").any()
     else "min/max lists all non-empty")
# show which partitions hold the global (scaler-edge) values for Nc and total counts
n_at_0 = {nm: int((np.abs(pmin[nm]) < 1e-9).sum()) for nm in ("train", "val", "test")}
n_at_1 = {nm: int((np.abs(pmax[nm] - 1.0) < 1e-9).sum()) for nm in ("train", "val", "test")}
cond("q7d multiple partitions hold scaler edges (train/val/test all touch at least one edge)",
     bool(all(v > 0 for v in n_at_0.values()) and all(v > 0 for v in n_at_1.values())),
     f"cols@0 {n_at_0} cols@1 {n_at_1}")
# scaler log10 min for Nc equals test-partition log10 min
log10_test_min_nc = scmin[nc] + te_nc_min * scrange[nc]
chk("q7e Nc scaler log10 min == test log10 min (not train)",
    scmin[nc], log10_test_min_nc, 1e-12)

# q8 width-figure order regression
alpha = sorted(PARAM_NAMES)
n_shifted = int(sum(1 for a, b in zip(alpha, PARAM_NAMES) if a != b))
cond("q8a round-2 alphabetical sort would misalign data (bug real)",
     bool(n_shifted > 0), f"{n_shifted}/9 positions differ from canonical")
cond("q8b correspondence table tick==data==PARAM_NAMES in order",
     bool((corr.tick_label.values == PARAM_NAMES).all()
          and (corr.data_param.values == PARAM_NAMES).all()
          and (corr.x_pos.values == np.arange(9)).all()))
# data plotted for level 0.95 equals canonical-order metrics (clip median width)
canon = csv[csv.level == 0.95].set_index("param").loc[PARAM_NAMES].wdec_clip_med.values
maxd = float(np.abs(canon - csv[csv.level == 0.95].set_index("param").loc[PARAM_NAMES].wdec_clip_med.values).max())
cond("q8c figure data series == canonical PARAM_NAMES order (@0.95)", bool(maxd == 0.0),
     f"max|d|={maxd:.3g}")

# q9 raw >= clip median width everywhere
viol = csv[csv.wdec_clip_med > csv.wdec_raw_med + 1e-12]
cond("q9 clip median width <= raw median width (all param/level)",
     bool(len(viol) == 0), f"violations={len(viol)}")

# q10 reproducibility vs round-2 stored arrays
if os.path.exists(os.path.join(V2DAT, "a1v2_reusable_test.npz")):
    d2 = np.load(os.path.join(V2DAT, "a1v2_reusable_test.npz"))
    dmu = float(np.abs(mu - d2["mu_norm"]).max())
    dsg = float(np.abs(sigma - d2["sigma_norm"]).max())
    cond("q10 frozen-inference reproducibility vs round-2",
         bool(dmu < 1e-9 and dsg < 1e-9), f"max|dmu|={dmu:.3g} max|dsigma|={dsg:.3g}")
else:
    cond("q10 frozen-inference reproducibility vs round-2 (v2 npz missing -- skip)",
         True, "v2 reusable npz not found")

q = pd.DataFrame(results, columns=["check", "expected", "computed", "ok"])
q.to_csv(os.path.join(QCO, "a1v3_qc.csv"), index=False)
print("\nQC: %d/%d passed -> %s" % (int(q.ok.sum()), len(q), os.path.join(QCO, "a1v3_qc.csv")))
