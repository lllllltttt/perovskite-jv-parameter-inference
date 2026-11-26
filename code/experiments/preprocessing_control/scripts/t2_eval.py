"""v4 T2 evaluation (protocol.md §5): physical-log10 parameter + mA/cm2 J metrics
for Historical(frozen) / Branch L / Branch T, shared train-empirical log10 prior
reference, and increments A(L-Hist), B(T-L). Read-only on frozen & runs.
Scalers are sklearn objects: Historical & L = frozen full-fit pkl; T = train-only
refit from _data_physical.npz (deterministic, identical to t2_train). Outputs
tables/preprocessing_control_metrics.csv and tables/control_per_sample.csv."""
import os, sys, csv, pickle
import numpy as np
import tensorflow as tf
from scipy.stats import norm, pearsonr, spearmanr
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from sklearn.preprocessing import MinMaxScaler
# register t2_model.Sampling etc. so Keras can deserialize the .keras encoder graphs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_model as M
FROZ_CUSTOM = {"Sampling": M.Sampling}  # frozen Keras-2 .h5 encoder stores a custom 'Sampling' layer

RUNS = r"E:\project\work1\supplementary_validation_v4\T2_control\runs"
OUTT = r"E:\project\work1\supplementary_validation_v4\T2_control\tables"
os.makedirs(OUTT, exist_ok=True)
FROZ = r"E:\project\work1\data\vae-v6\vae-v6"
ROOT = r"E:\project\work1"
PARAM_NAMES = ["mu_n_pvk","mu_p_pvk","tau_n_pvk","tau_p_pvk",
               "Nc_eff_pvk","Nv_eff_pvk","tau_ETL","tau_HTL","rad_c"]
LEVELS = [0.50, 0.80, 0.90, 0.95]
V = np.linspace(0.0, 1.3, 131)
n = 9

d = np.load(os.path.join(ROOT, r"data\dataset_normalized.npz"), allow_pickle=True)
p = np.load(r"E:\project\work1\supplementary_validation_v4\T2_control\_data_physical.npz", allow_pickle=True)
J_true = d["J_test_raw"]                      # mA/cm2 (15307,131)
par_true = d["params_test_raw"]
idx_tr, idx_va, idx_te = p["idx_train"], p["idx_val"], p["idx_test"]
sid_test = p["Sample_ID"][idx_te]
par_log_true = np.log10(par_true)

def softplus(x): return np.log1p(np.exp(np.clip(x, -50, 50)))
def sigma_from_raw(raw): return np.clip(softplus(raw) + 0.01, 0.01, 1.0)

# ---- scaler objects ----
def build_full_scaler():
    param_pkl = pickle.load(open(os.path.join(ROOT, r"data\param_scaler.pkl"), "rb"))
    J = pickle.load(open(os.path.join(ROOT, r"data\J_scaler.pkl"), "rb"))
    return dict(param=param_pkl, J=J, scope="L/full")

phys_par = p["params_phys"]; phys_J = p["J_phys"]
def build_T_scaler():
    pt = phys_par[idx_tr]
    colmin = pt.min(0); colmax = pt.max(0)
    mask = (colmin > 0) & (colmax / np.maximum(colmin, 1e-300) > 100.0)
    X = np.where(mask, np.log10(pt), pt)
    psT = MinMaxScaler().fit(X)
    jsT = MinMaxScaler().fit(phys_J[idx_tr])
    return dict(param=dict(scaler=psT, log_mask=mask), J=jsT, scope="T/train-only")

def phys_param_to_log_norm(phys, sc):
    mask = np.asarray(sc["param"]["log_mask"], bool)
    x = np.where(mask, np.log10(phys), phys)
    return sc["param"]["scaler"].transform(x)

def inv_mu_to_log10(mu_norm, sc):
    # returns predicted log10 physical per parameter (decades)
    mask = np.asarray(sc["param"]["log_mask"], bool)
    inv = sc["param"]["scaler"].inverse_transform(mu_norm)
    out = np.where(mask, inv, np.log10(np.maximum(inv, 1e-30)))
    return out, mask

def model_pred(runname):
    enc = tf.keras.models.load_model(runname)
    return enc

registry = []
reg = []
for name, base in [("Historical", FROZ), ("L", os.path.join(RUNS, "L_seed20260823"))]:
    # Historical .h5 (Keras2) and L/T .keras both embed the custom 'Sampling' layer;
    # every load needs custom_objects so Keras can resolve it.
    kw = dict(custom_objects=FROZ_CUSTOM)
    enc = tf.keras.models.load_model(os.path.join(base, "encoder.keras" if name=="L" else "encoder.h5"), **kw)
    dec = tf.keras.models.load_model(os.path.join(base, "decoder.keras" if name=="L" else "decoder.h5"), **kw)
    head = tf.keras.models.load_model(os.path.join(base, "param_head.keras" if name=="L" else "param_head.h5"), **kw)
    sc = build_full_scaler()
    reg.append((name, enc, dec, head, sc))
name = "T"; base = os.path.join(RUNS, "T_seed20260823")
enc = tf.keras.models.load_model(os.path.join(base, "encoder.keras"), custom_objects=FROZ_CUSTOM)
dec = tf.keras.models.load_model(os.path.join(base, "decoder.keras"), custom_objects=FROZ_CUSTOM)
head = tf.keras.models.load_model(os.path.join(base, "param_head.keras"), custom_objects=FROZ_CUSTOM)
reg.append((name, enc, dec, head, build_T_scaler()))

# shared prior: train-empirical log10 Gaussian
prior_mu = np.log10(phys_par[idx_tr]).mean(0); prior_sig = np.log10(phys_par[idx_tr]).std(0)

def voc_interp(Jc):
    i = np.argmax(Jc); tail = Jc[i:]
    sel = np.where(tail <= 0.0)[0]
    if len(sel) == 0: return 1.3
    k = i + sel[0]
    if k == 0: return V[0]
    if Jc[k] == Jc[k-1]: return V[k]
    return V[k-1] + (V[k]-V[k-1]) * (0.0 - Jc[k-1]) / (Jc[k]-Jc[k-1])

def win_rmse(a, b, mask):
    e = a[mask] - b[mask]
    return float(np.sqrt(np.mean(e*e))) if e.size else np.nan

zL = {lv: norm.ppf(0.5 + lv/2) for lv in LEVELS}

def stats_for(mu_log10, sig_log10):
    """per-param dict + pooled; mu_log10/sig_log10 (ntest,n)"""
    err = np.abs(par_log_true - mu_log10)
    per = {}
    for j in range(n):
        e = par_log_true[:, j] - mu_log10[:, j]
        per[j] = dict(mae=float(np.mean(np.abs(e))), rmse=float(np.sqrt(np.mean(e*e))),
                      pearson=float(pearsonr(par_log_true[:, j], mu_log10[:, j])[0]),
                      rho_rank=float(spearmanr(par_log_true[:, j], mu_log10[:, j]).statistic),
                      sig_err_spearman=float(spearmanr(sig_log10[:, j], err[:, j]).statistic))
        for lv in LEVELS:
            z = zL[lv]; lo = mu_log10[:, j]-z*sig_log10[:, j]; hi = mu_log10[:, j]+z*sig_log10[:, j]
            w = hi-lo
            sc_ = w + (2/(1-lv))*np.maximum(lo-par_log_true[:, j], 0) + (2/(1-lv))*np.maximum(par_log_true[:, j]-hi, 0)
            per[j][f"cov_{lv:.2f}"] = float(np.mean((par_log_true[:, j] >= lo) & (par_log_true[:, j] <= hi)))
            per[j][f"wmean_{lv:.2f}"] = float(np.mean(w)); per[j][f"wmed_{lv:.2f}"] = float(np.median(w))
            per[j][f"is_{lv:.2f}"] = float(np.mean(sc_))
    # pooled
    pooled = dict(param="POOLED9")
    for lv in LEVELS:
        z = zL[lv]; lo = mu_log10-z*sig_log10; hi = mu_log10+z*sig_log10
        pooled[f"cov_{lv:.2f}"] = float(np.mean((par_log_true >= lo) & (par_log_true <= hi)))
        pooled[f"wmean_{lv:.2f}"] = float(np.mean(hi-lo))
        pooled[f"wmed_{lv:.2f}"] = float(np.median(hi-lo))
        sc_ = (hi-lo) + (2/(1-lv))*np.maximum(lo-par_log_true,0) + (2/(1-lv))*np.maximum(par_log_true-hi,0)
        pooled[f"is_{lv:.2f}"] = float(np.mean(sc_))
    pooled["mae"] = float(np.mean(err)); pooled["rmse"] = float(np.sqrt(np.mean((par_log_true-mu_log10)**2)))
    return per, pooled

res = {}
for name, enc, dec, head, sc in reg:
    Jn = sc["J"].transform(J_true).astype(np.float32)
    out = enc(Jn, training=False); z_mean = out[0] if isinstance(out, (list, tuple)) else out
    hm = head(z_mean, training=False); mu_n = hm[0]; raw = hm[1]
    sig_n = sigma_from_raw(raw.numpy() if hasattr(raw, "numpy") else raw)
    mu_n = mu_n.numpy() if hasattr(mu_n, "numpy") else mu_n
    rc = dec(z_mean, training=False); rc = rc.numpy() if hasattr(rc, "numpy") else rc
    mu_log10, mask = inv_mu_to_log10(mu_n, sc)
    pr = sc["param"]["scaler"].data_max_ - sc["param"]["scaler"].data_min_
    sig_log10 = sig_n * pr                     # mask all-True (asserted below)
    assert np.all(np.asarray(sc["param"]["log_mask"], bool)), "T2 eval assumes log_mask all-True (verified T0)"
    J_pred = sc["J"].inverse_transform(rc)
    res[name] = dict(mu=mu_log10, sig=sig_log10, J=J_pred)
    per, pooled = stats_for(mu_log10, sig_log10)
    res[name]["per"] = per; res[name]["pooled"] = pooled
    fr = np.sqrt(np.mean((J_pred-J_true)**2, axis=1))
    res[name]["Jfull"] = fr
    print(f"{name}: n_par_ok; J whole-curve RMSE mean={fr.mean():.4f} med={np.median(fr):.4f} mA/cm2; "
          f"pooled cov95={pooled['cov_0.95']:.4f}")

# prior as pseudo-model
PR = dict(mu=np.tile(prior_mu, (J_true.shape[0], 1)), sig=np.tile(prior_sig, (J_true.shape[0], 1)))
pr_per, pr_pooled = stats_for(PR["mu"], PR["sig"])

rows = []
def push_model(mname, per, pooled, kind="model"):
    for j, pn in enumerate(PARAM_NAMES):
        row = dict(model=mname, kind=kind, param=pn, **per[j]); rows.append(row)
    row = dict(model=mname, kind=kind, **pooled); rows.append(row)  # pooled already carries param="POOLED9"

for name in ["Historical", "L", "T"]:
    push_model(name, res[name]["per"], res[name]["pooled"])
push_model("Prior", pr_per, pr_pooled, kind="prior")

# ---- write main metrics table (per-param + pooled; one uniform schema) ----
metric_cols = (["model", "kind", "param", "pearson", "rho_rank", "sig_err_spearman",
                "mae", "rmse"] +
               [f"{s}_{lv:.2f}" for lv in LEVELS
                for s in ("cov", "wmean", "wmed", "is")])
with open(os.path.join(OUTT, "preprocessing_control_metrics.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=metric_cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
n_main = len(rows)

# ---- J reconstruction summary (mean/median/rmse-of-row-rmse per window) ----
with open(os.path.join(OUTT, "J_recon_summary.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["model", "window", "n", "mean_rowRMSE_mAcm2", "med_rowRMSE_mAcm2"])
    for name in ["Historical", "L", "T"]:
        Jp = res[name]["J"]
        full = np.sqrt(np.mean((Jp-J_true)**2, axis=1))
        le = np.array([win_rmse(Jp[i], J_true[i], V <= 1.0) for i in range(J_true.shape[0])])
        gt = np.array([win_rmse(Jp[i], J_true[i], V > 1.0) for i in range(J_true.shape[0])])
        gen = np.array([win_rmse(Jp[i], J_true[i], V <= voc_interp(J_true[i])) for i in range(J_true.shape[0])])
        for tag, arr in [("full", full), ("le1", le), ("gt1", gt), ("gen0", gen)]:
            w.writerow([name, tag, arr.size, float(arr.mean()), float(np.median(arr))])

# per-sample long table
with open(os.path.join(OUTT, "control_per_sample.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    hdr = ["test_index", "Sample_ID"] + [f"true_log10_{p}" for p in PARAM_NAMES]
    for name in ["Historical", "L", "T"]:
        hdr += [f"{name}_mu_{p}" for p in PARAM_NAMES] + [f"{name}_sig_{p}" for p in PARAM_NAMES]
        hdr += [f"{name}_Jrmse"]
    w.writerow(hdr)
    for i in range(J_true.shape[0]):
        r = [i, int(sid_test[i])] + [float(par_log_true[i, j]) for j in range(n)]
        for name in ["Historical", "L", "T"]:
            r += [float(res[name]["mu"][i, j]) for j in range(n)]
            r += [float(res[name]["sig"][i, j]) for j in range(n)]
            r += [float(np.sqrt(np.mean((res[name]["J"][i]-J_true[i])**2)))]
        w.writerow(r)
print("wrote preprocessing_control_metrics.csv (%d rows) + J_recon_summary.csv + control_per_sample.csv (%d rows)"
      % (n_main, J_true.shape[0]))
