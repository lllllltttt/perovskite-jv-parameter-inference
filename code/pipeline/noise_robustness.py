"""
VAE v6 - J-V input noise robustness analysis (frozen model, test set)
====================================================================

Question: when the input J-V carries realistic measurement perturbations,
how do the VAE's parameter point prediction, predictive uncertainty, and
calibration change?

Constraints honored:
  * no retraining, no model modification, no COMSOL
  * frozen encoder + param_head; sigma = clip(softplus(raw)+0.01, 0.01, 1.0)
  * noise added in PHYSICAL current space, then renormalized with the exact
    original per-column MinMax recovered from (J_test_raw, J_test)
  * N_MC = 30 independent realizations per level, fixed seeds; metrics = mean +/- SD

Noise model (type 1, random current):
    J_noisy(V) = J_clean(V) + eps(V),  eps ~ Normal(0, sigma_noise)
    sigma_noise = noise_level * |Jsc|     (per-curve constant)
  * |Jsc| (short-circuit current) is used as the physical current scale because
    per-curve max|J| is dominated by the reverse-bias dark tail (up to ~6.4 A/cm2,
    a numerical artifact), and a fixed instrument scale would over-noise
    low-Jsc devices. Constant-per-curve noise does NOT vanish near J=0.

Outputs (noise_robustness/):
  noise_metrics_all.csv, noise_parameter_summary.csv, noise_uncertainty_summary.csv,
  noise_calibration_summary.csv, noise_robustness_summary.txt,
  noise_robustness.png, noise_robustness_parameter_heatmap.png, config.json
"""
import os
import json
import numpy as np
import pandas as pd
import scipy.stats as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

BASE = r"E:\project\work1"
NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
MODEL_DIR = os.path.join(BASE, "data", "vae-v6", "vae-v6")
OUT = os.path.join(BASE, "noise_robustness")
os.makedirs(OUT, exist_ok=True)

INPUT_DIM = 131
N_PARAM = 9
PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]
NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}
SIGMA_MIN, SIGMA_MAX = 0.01, 1.0
NOISE_LEVELS = [0.0, 0.002, 0.005, 0.01, 0.02]
LEVEL_LABELS = ["0%", "0.2%", "0.5%", "1.0%", "2.0%"]
N_MC = 30
SEED_BASE = 20260823

# ---------------------------------------------------------------- model / data
class Sampling(layers.Layer):
    def call(self, inputs):
        z_mean, z_log_var = inputs
        eps = tf.random.normal(shape=tf.shape(z_mean))
        return z_mean + tf.exp(0.5 * z_log_var) * eps


def sigma_fixed(raw):
    s = tf.nn.softplus(raw).numpy() + SIGMA_MIN
    return np.clip(s, SIGMA_MIN, SIGMA_MAX)


data = np.load(NPZ, allow_pickle=True)
J_test = data["J_test"].astype(np.float64)         # normalized
Jraw = data["J_test_raw"].astype(np.float64)        # physical mA/cm2
P_test = data["params_test"].astype(np.float64)     # normalized log params
Vgrid = np.linspace(0.0, 1.3, INPUT_DIM)

# recover exact per-column MinMax affine: norm = a*raw + b
a = np.zeros(INPUT_DIM); b = np.zeros(INPUT_DIM)
for c in range(INPUT_DIM):
    m = np.polyfit(Jraw[:, c], J_test[:, c], 1)
    a[c], b[c] = m
assert np.abs(a[None, :] * Jraw + b[None, :] - J_test).max() < 1e-6, "J transform not exactly affine"

encoder = keras.models.load_model(os.path.join(MODEL_DIR, "encoder.h5"),
                                  custom_objects={"Sampling": Sampling})
param_head = keras.models.load_model(os.path.join(MODEL_DIR, "param_head.h5"))


def infer(Jn):
    """frozen inference: z_mean point prediction, no latent sampling"""
    z_mean, _, _ = encoder.predict(Jn.astype(np.float32), verbose=0)
    mu, sraw = param_head.predict(z_mean, verbose=0)
    return mu.astype(np.float64), sigma_fixed(sraw), z_mean


Jsc = np.abs(Jraw[:, 0])


def add_current_noise(J_phys, level, rng):
    """constant-per-curve Gaussian noise in physical current space."""
    s = level * np.abs(J_phys[:, [0]])          # sigma_noise = level * |Jsc|
    return J_phys + rng.normal(0.0, s, size=J_phys.shape)


# ---------------------------------------------------------------- metric helpers
def point_metrics(mu):
    err = np.abs(P_test - mu)
    r = np.array([st.pearsonr(P_test[:, p], mu[:, p])[0] for p in range(N_PARAM)])
    mae = err.mean(axis=0)
    rmse = np.sqrt(np.mean((P_test - mu) ** 2, axis=0))
    return r, mae, rmse, err


def spearman_sig(sig, err):
    return np.array([st.spearmanr(sig[:, p], err[:, p])[0] for p in range(N_PARAM)])


def calibration(mu, sig):
    emp = np.zeros((N_PARAM, len(NOMINAL)))
    wm = np.zeros((N_PARAM, len(NOMINAL)))
    wmed = np.zeros((N_PARAM, len(NOMINAL)))
    for j, lvl in enumerate(NOMINAL):
        zz = NOMINAL[lvl]
        lo = mu - zz * sig; hi = mu + zz * sig
        emp[:, j] = np.mean((P_test >= lo) & (P_test <= hi), axis=0)
        w = 2 * zz * sig
        wm[:, j] = w.mean(axis=0); wmed[:, j] = np.median(w, axis=0)
    return emp, wm, wmed


def sigma_stats(sig):
    return np.array([sig.mean(axis=0), np.median(sig, axis=0),
                     np.percentile(sig, 25, axis=0), np.percentile(sig, 75, axis=0)])


# ---------------------------------------------------------------- clean baseline
print("[clean] running baseline ...")
mu0, sig0, _ = infer(J_test)
r0, mae0, rmse0, err0 = point_metrics(mu0)
sp0 = spearman_sig(sig0, err0)
cal0_emp, cal0_wm, cal0_wmed = calibration(mu0, sig0)
ss0 = sigma_stats(sig0)     # rows: mean, median, q25, q75

# ---------------------------------------------------------------- random-noise MC
# per level, per param: r, mae, rmse, spearman; per level per param: sigma stats;
# per level: empirical coverage / widths; per level: J-V perturbation
metrics = {}   # lvl -> dict of arrays over MC: r(NMC,9), mae(NMC,9), rmse(NMC,9), sp(NMC,9), ss(NMC,4,9)
cal = {}       # lvl -> emp(NMC,9,4), wm(NMC,9,4), wmed(NMC,9,4)
jvp = {}       # lvl -> rmse_curve, mae_curve, max_curve (flattened over MC)
hv = {}        # lvl -> hv-region per-curve rmse (flattened over MC)
hv_exp = {}    # lvl -> exploratory per-param Pearson(hv_pert, |err| increase), mc=0
oob_frac = {}  # lvl -> fraction of normalized inputs outside [0,1]

for li, lvl in enumerate(NOISE_LEVELS):
    if lvl == 0.0:
        metrics[lvl] = dict(r=np.full((1, 9), r0), mae=np.full((1, 9), mae0),
                            rmse=np.full((1, 9), rmse0), sp=np.full((1, 9), sp0),
                            ss=ss0[None, :, :])
        cal[lvl] = (cal0_emp[None, :, :], cal0_wm[None, :, :], cal0_wmed[None, :, :])
        jvp[lvl] = (np.zeros(1), np.zeros(1), np.zeros(1))
        hv[lvl] = np.zeros(1)
        hv_exp[lvl] = np.zeros(N_PARAM)
        oob_frac[lvl] = 0.0
        print(f"[level {LEVEL_LABELS[li]}] baseline")
        continue

    rs = np.zeros((N_MC, N_PARAM)); maes = np.zeros((N_MC, N_PARAM))
    rms = np.zeros((N_MC, N_PARAM)); sps = np.zeros((N_MC, N_PARAM))
    sss = np.zeros((N_MC, 4, N_PARAM))
    e_arr = np.zeros((N_MC, N_PARAM, 4)); wm_arr = np.zeros((N_MC, N_PARAM, 4)); wmd_arr = np.zeros((N_MC, N_PARAM, 4))
    rm_curve = []; ma_curve = []; mx_curve = []; hv_curve = []
    oob = 0.0
    for mc in range(N_MC):
        rng = np.random.default_rng(SEED_BASE + li * 10000 + mc)
        Jr = add_current_noise(Jraw, lvl, rng)
        Jn = a[None, :] * Jr + b[None, :]
        oob += float(np.mean((Jn < 0) | (Jn > 1)))
        mu, sig, _ = infer(Jn)
        r, mae, rmse, err = point_metrics(mu)
        rs[mc] = r; maes[mc] = mae; rms[mc] = rmse
        sps[mc] = spearman_sig(sig, err)
        sss[mc] = sigma_stats(sig)
        emp, wm, wmd = calibration(mu, sig)
        e_arr[mc] = emp; wm_arr[mc] = wm; wmd_arr[mc] = wmd
        dj = Jr - Jraw
        rm_curve.append(np.sqrt(np.mean(dj ** 2, axis=1)))
        ma_curve.append(np.mean(np.abs(dj), axis=1))
        mx_curve.append(np.max(np.abs(dj), axis=1))
        hv_curve.append(np.sqrt(np.mean(dj[:, Vgrid > 0.8] ** 2, axis=1)))
        if mc == 0:
            # exploratory (observational) attribution: HV-region perturb vs |error| increase
            d_err = np.abs(err) - err0
            hv_p = np.sqrt(np.mean(dj[:, Vgrid > 0.8] ** 2, axis=1))
            hv_exp[lvl] = np.array([st.pearsonr(hv_p, d_err[:, p])[0] for p in range(N_PARAM)])
    metrics[lvl] = dict(r=rs, mae=maes, rmse=rms, sp=sps, ss=sss)
    cal[lvl] = (e_arr, wm_arr, wmd_arr)
    jvp[lvl] = (np.concatenate(rm_curve), np.concatenate(ma_curve), np.concatenate(mx_curve))
    hv[lvl] = np.concatenate(hv_curve)
    oob_frac[lvl] = oob / N_MC
    print(f"[level {LEVEL_LABELS[li]}] done (MC={N_MC}, oob_frac={oob_frac[lvl]:.2e})")

# ---------------------------------------------------------------- systematic perturbations
sys_rows = []
# A. current scale error: J*(1+delta)
for delta in [-0.010, -0.005, -0.002, 0.002, 0.005, 0.010]:
    Jr = Jraw * (1.0 + delta)
    mu, _, _ = infer(a[None, :] * Jr + b[None, :])
    r, mae, rmse, _ = point_metrics(mu)
    sys_rows.append(dict(kind="scale", value=delta, r_mean=r.mean(), r_min=r.min(),
                         mae_mean=mae.mean(), rmse_mean=rmse.mean()))
# B. voltage offset: J_recorded(V) = J_clean(V - Voff); interp on original grid
for voff_mv in [-5, -2, -1, 1, 2, 5]:
    off = voff_mv / 1000.0
    Jr = np.array([np.interp(Vgrid - off, Vgrid, row) for row in Jraw])
    mu, _, _ = infer(a[None, :] * Jr + b[None, :])
    r, mae, rmse, _ = point_metrics(mu)
    sys_rows.append(dict(kind="voltage_offset", value=voff_mv, r_mean=r.mean(), r_min=r.min(),
                         mae_mean=mae.mean(), rmse_mean=rmse.mean()))
sys_df = pd.DataFrame(sys_rows)

# ---------------------------------------------------------------- robustness ranking (1% noise)
r1 = metrics[0.01]["r"].mean(axis=0)
mae1 = metrics[0.01]["mae"].mean(axis=0)
R_i = (r0 - r1) / np.abs(r0)
mae_inc = (mae1 - mae0) / mae0
rank_order = np.argsort(R_i)[::-1]  # most degradation first

# ---------------------------------------------------------------- CSVs
rows_all = []
for lvl in NOISE_LEVELS:
    m = metrics[lvl]
    for p in range(N_PARAM):
        r_m, r_s = m["r"][:, p].mean(), m["r"][:, p].std()
        ma_m, ma_s = m["mae"][:, p].mean(), m["mae"][:, p].std()
        rm_m, rm_s = m["rmse"][:, p].mean(), m["rmse"][:, p].std()
        rows_all.append(dict(parameter=PARAM_NAMES[p], noise=LEVEL_LABELS[NOISE_LEVELS.index(lvl)],
                             r_mean=r_m, r_sd=r_s, mae_mean=ma_m, mae_sd=ma_s,
                             rmse_mean=rm_m, rmse_sd=rm_s,
                             delta_r=r_m - r0[p], delta_mae=ma_m - mae0[p], delta_rmse=rm_m - rmse0[p]))
df_metrics = pd.DataFrame(rows_all)
df_metrics.to_csv(os.path.join(OUT, "noise_metrics_all.csv"), index=False)

rows_unc = []
for lvl in NOISE_LEVELS:
    m = metrics[lvl]; s = m["ss"]
    for p in range(N_PARAM):
        rows_unc.append(dict(parameter=PARAM_NAMES[p], noise=LEVEL_LABELS[NOISE_LEVELS.index(lvl)],
                             sigma_mean=s[:, 0, p].mean(), sigma_mean_sd=s[:, 0, p].std(),
                             sigma_median=s[:, 1, p].mean(), sigma_q25=s[:, 2, p].mean(),
                             sigma_q75=s[:, 3, p].mean(),
                             spearman_mean=m["sp"][:, p].mean(), spearman_sd=m["sp"][:, p].std()))
df_unc = pd.DataFrame(rows_unc)
df_unc.to_csv(os.path.join(OUT, "noise_uncertainty_summary.csv"), index=False)

rows_param = []
for lvl in NOISE_LEVELS:
    m = metrics[lvl]; s = m["ss"]
    for p in range(N_PARAM):
        rows_param.append(dict(parameter=PARAM_NAMES[p], noise=LEVEL_LABELS[NOISE_LEVELS.index(lvl)],
                               pearson_degradation_R=(r0[p] - m["r"][:, p].mean()) / abs(r0[p]),
                               mae_increase=(m["mae"][:, p].mean() - mae0[p]) / mae0[p],
                               sigma_mean=s[:, 0, p].mean(), sigma_q25=s[:, 2, p].mean(),
                               sigma_q75=s[:, 3, p].mean(),
                               spearman_mean=m["sp"][:, p].mean(), spearman_sd=m["sp"][:, p].std()))
df_param = pd.DataFrame(rows_param)
df_param.to_csv(os.path.join(OUT, "noise_parameter_summary.csv"), index=False)

rows_cal = []
for lvl in NOISE_LEVELS:
    e_arr, wm_arr, wmd_arr = cal[lvl]
    for p in range(N_PARAM):
        for j, nvl in enumerate(NOMINAL):
            rows_cal.append(dict(parameter=PARAM_NAMES[p], noise=LEVEL_LABELS[NOISE_LEVELS.index(lvl)],
                                 nominal=nvl, coverage_mean=e_arr[:, p, j].mean(),
                                 coverage_sd=e_arr[:, p, j].std(),
                                 width_mean=wm_arr[:, p, j].mean(),
                                 width_median=wmd_arr[:, p, j].mean()))
df_cal = pd.DataFrame(rows_cal)
df_cal.to_csv(os.path.join(OUT, "noise_calibration_summary.csv"), index=False)

sys_df.to_csv(os.path.join(OUT, "noise_systematic_perturbation.csv"), index=False)

with open(os.path.join(OUT, "config.json"), "w") as f:
    json.dump(dict(model_dir=MODEL_DIR, npz=NPZ, n_mc=N_MC, seed_base=SEED_BASE,
                   noise_levels=NOISE_LEVELS, noise_scale="level*|Jsc| per-curve constant",
                   sigma_convention="clip(softplus(raw)+0.01,0.01,1.0)",
                   j_renorm="exact per-column MinMax recovered from (J_test_raw,J_test)",
                   test_size=int(len(Jraw))), f, indent=2)

# ---------------------------------------------------------------- summary text
L = []
L.append("VAE v6 - J-V INPUT NOISE ROBUSTNESS ANALYSIS (frozen model, test set)")
L.append("=" * 70)
L.append("sigma convention : clip(softplus(raw)+0.01, 0.01, 1.0)  [fixed P0]")
L.append("noise model      : J_noisy(V)=J(V)+eps, eps~N(0, sigma), sigma = level * |Jsc| (constant per curve)")
L.append("noise levels     : " + ", ".join(LEVEL_LABELS) + "   (2.0% = stress test)")
L.append(f"MC realizations  : {N_MC} per level, seeds {SEED_BASE} + level*10000 + mc")
L.append(f"test set         : N={len(Jraw)}, J-dim={INPUT_DIM}, params in normalized log space")
L.append("")

L.append("=== 1. POINT PREDICTION (Pearson r, mean over MC) ===")
hdr = "param        " + "".join(["%9s" % s for s in LEVEL_LABELS])
L.append(hdr)
for p in range(N_PARAM):
    row = "%-12s " % SHORT[p]
    for lvl in NOISE_LEVELS:
        row += "%8.3f " % metrics[lvl]["r"][:, p].mean()
    L.append(row)
L.append("")

L.append("=== 2. POINT PREDICTION (MAE, mean over MC) ===")
L.append(hdr)
for p in range(N_PARAM):
    row = "%-12s " % SHORT[p]
    for lvl in NOISE_LEVELS:
        row += "%8.4f " % metrics[lvl]["mae"][:, p].mean()
    L.append(row)
L.append("")

L.append("=== 3. PREDICTED SIGMA (mean over MC) ===")
L.append(hdr)
for p in range(N_PARAM):
    row = "%-12s " % SHORT[p]
    for lvl in NOISE_LEVELS:
        row += "%8.4f " % metrics[lvl]["ss"][:, 0, p].mean()
    L.append(row)
L.append("")

L.append("=== 4. SPEARMAN(sigma, |error|) (mean over MC) ===")
L.append(hdr)
for p in range(N_PARAM):
    row = "%-12s " % SHORT[p]
    for lvl in NOISE_LEVELS:
        row += "%8.3f " % metrics[lvl]["sp"][:, p].mean()
    L.append(row)
L.append("")

L.append("=== 5. CALIBRATION: empirical coverage at nominal 95% (mean over MC) ===")
L.append(hdr)
for p in range(N_PARAM):
    row = "%-12s " % SHORT[p]
    for lvl in NOISE_LEVELS:
        row += "%8.3f " % cal[lvl][0][:, p, list(NOMINAL).index(0.95)].mean()
    L.append(row)
L.append("")

L.append("=== 6. INPUT PERTURBATION (physical mA/cm2, across all MC curves) ===")
for lvl in NOISE_LEVELS:
    if lvl == 0.0:
        L.append("  0%   : (none)")
        continue
    rmv, mav, mxv = jvp[lvl]
    hv_v = hv[lvl]
    L.append(f"  {LEVEL_LABELS[NOISE_LEVELS.index(lvl)]:<5}: J-V RMSE mean={rmv.mean():.4f} median={np.median(rmv):.4f} | "
             f"MAE mean={mav.mean():.4f} | max|d| mean={mxv.mean():.3f} | "
             f"HV(V>0.8V) RMSE mean={hv_v.mean():.4f}")
L.append("  (typical |Jsc| ~ 23.7 mA/cm2; 1% => sigma ~ 0.24 mA/cm2)")
L.append(f"  normalized-input OOB fraction (outside [0,1]): "
          + ", ".join(f"{LEVEL_LABELS[i]}={oob_frac[lvl]:.1e}" for i, lvl in enumerate(NOISE_LEVELS)))
L.append("")

L.append("=== 7. HIGH-VOLTAGE (V>0.8 V) region, exploratory attribution at 1% (single MC, mc=0) ===")
L.append("  Pearson(hv-region perturb, |error| increase) per parameter:")
for p in range(N_PARAM):
    L.append("    %-12s %.3f" % (SHORT[p], hv_exp[0.01][p]))
L.append("  (observational only; not a causal claim)")
L.append("")

L.append("=== 8. ROBUSTNESS RANKING at 1% noise ===")
L.append("  R_i = [r(clean) - r(1%)] / |r(clean)|  (Pearson degradation; larger = less robust)")
L.append("  param       R_i     mae_increase")
for p in rank_order:
    L.append("  %-12s %+.4f  %+.3f" % (SHORT[p], R_i[p], mae_inc[p]))
L.append("")

L.append("=== 9. SYSTEMATIC PERTURBATIONS (deterministic) ===")
L.append("  A. current scale error J*(1+delta):")
L.append("     delta      r_mean    mae_mean")
for r_ in [x for x in sys_rows if x["kind"] == "scale"]:
    L.append("     %+5.1f%%    %.3f     %.4f" % (100 * r_["value"], r_["r_mean"], r_["mae_mean"]))
L.append("  B. voltage offset (J_recorded(V) = J(V - Voff), interp on grid):")
L.append("     Voff(mV)   r_mean    mae_mean")
for r_ in [x for x in sys_rows if x["kind"] == "voltage_offset"]:
    L.append("     %+5d      %.3f     %.4f" % (r_["value"], r_["r_mean"], r_["mae_mean"]))
L.append("")

L.append("=== 10. INTERPRETATION BOUNDARY ===")
L.append("  Model trained on clean synthetic J-V only. If sigma is insensitive or calibration")
L.append("  degrades under input noise, the correct reading is that the Gaussian head")
L.append("  characterizes conditional predictive uncertainty within the CLEAN simulation")
L.append("  domain, and does not explicitly model measurement-noise uncertainty.")
L.append("  The normalized-input attenuation due to the reverse-tail-dominated MinMax")
L.append("  scaling means physical 1% current noise maps to a much smaller perturbation")
L.append("  in the network's input space; this is a preprocessing property, not model gain.")

open(os.path.join(OUT, "noise_robustness_summary.txt"), "w", encoding="utf-8").write("\n".join(L))
for line in L:
    print(line)

# ---------------------------------------------------------------- figures
GROUP = {"mu_n": ("bulk transport", "#0072B2"), "mu_p": ("bulk transport", "#0072B2"),
         "tau_n": ("bulk recombination", "#009E73"), "tau_p": ("bulk recombination", "#009E73"),
         "Nc": ("DOS", "#E69F00"), "Nv": ("DOS", "#E69F00"),
         "tau_ETL": ("interface", "#D55E00"), "tau_HTL": ("interface", "#D55E00"),
         "rad_c": ("radiative", "#CC79A7")}
LINESTYLES = {"mu_n": "-", "mu_p": "--", "tau_n": "-", "tau_p": "--", "Nc": "-", "Nv": "--",
              "tau_ETL": "-", "tau_HTL": "--", "rad_c": "-"}
x = [0, 0.2, 0.5, 1.0, 2.0]

plt.rcParams.update({"font.size": 8.5, "font.family": "sans-serif", "axes.linewidth": 0.8,
                     "axes.grid": True, "grid.linewidth": 0.4, "grid.alpha": 0.4, "grid.color": "#cccccc"})

fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.8))
panels = [(axes[0, 0], "Pearson r vs input noise", "r"),
          (axes[0, 1], "MAE vs input noise", "mae"),
          (axes[1, 0], "mean predicted sigma vs noise", "sigma"),
          (axes[1, 1], "empirical 95% coverage vs noise", "cov95")]
for ax, title, key in panels:
    for p in range(N_PARAM):
        col = GROUP[SHORT[p]][1]
        ls = LINESTYLES[SHORT[p]]
        if key == "r":
            y = [metrics[lvl]["r"][:, p].mean() for lvl in NOISE_LEVELS]
            sd = [metrics[lvl]["r"][:, p].std() for lvl in NOISE_LEVELS]
        elif key == "mae":
            y = [metrics[lvl]["mae"][:, p].mean() for lvl in NOISE_LEVELS]
            sd = [metrics[lvl]["mae"][:, p].std() for lvl in NOISE_LEVELS]
        elif key == "sigma":
            y = [metrics[lvl]["ss"][:, 0, p].mean() for lvl in NOISE_LEVELS]
            sd = [metrics[lvl]["ss"][:, 0, p].std() for lvl in NOISE_LEVELS]
        else:
            y = [cal[lvl][0][:, p, list(NOMINAL).index(0.95)].mean() for lvl in NOISE_LEVELS]
            sd = [cal[lvl][0][:, p, list(NOMINAL).index(0.95)].std() for lvl in NOISE_LEVELS]
        ax.plot(x, y, color=col, ls=ls, marker="o", ms=3.5, lw=1.2,
                label="%s (%s)" % (SHORT[p], GROUP[SHORT[p]][0]))
        ax.fill_between(x, np.array(y) - np.array(sd), np.array(y) + np.array(sd),
                        color=col, alpha=0.10, lw=0)
    ax.set_xlabel("input current noise (% of $J_{sc}$)")
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(LEVEL_LABELS)
    if key == "cov95":
        ax.axhline(0.95, color="#555555", ls=":", lw=1.0)
    if key == "r":
        ax.set_ylim(0.45, 1.0)
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=6.5, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(os.path.join(OUT, "noise_robustness.png"), dpi=300)
plt.close(fig)

# heatmap: Pearson degradation R_i (clamped >=0) rows sorted by R at 1%
Rmat = np.zeros((N_PARAM, len(NOISE_LEVELS)))
for j, lvl in enumerate(NOISE_LEVELS):
    Rmat[:, j] = (r0 - metrics[lvl]["r"].mean(axis=0)) / np.abs(r0)
Rplot = np.clip(Rmat, 0, None) * 100.0
order = np.argsort(R_i)  # most robust first
fig, ax = plt.subplots(figsize=(5.6, 4.6))
im = ax.imshow(Rplot[order], cmap="Reds", aspect="auto", vmin=0, vmax=max(5, Rplot.max()))
ax.set_yticks(range(N_PARAM)); ax.set_yticklabels([SHORT[p] for p in order])
ax.set_xticks(range(len(NOISE_LEVELS))); ax.set_xticklabels(LEVEL_LABELS)
ax.set_xlabel("input current noise (% of $J_{sc}$)")
ax.set_ylabel("parameter (top = most robust)")
for r_ in range(N_PARAM):
    for c_ in range(len(NOISE_LEVELS)):
        v = Rplot[order[r_], c_]
        ax.text(c_, r_, ("%.1f" % v) if v > 0.05 else "0.0",
                ha="center", va="center", fontsize=7,
                color="#333333" if v < 45 else "white")
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cbar.set_label("Pearson degradation R$_i$ (%)", fontsize=8)
ax.set_title("Parameter robustness to J-V noise (relative Pearson loss)", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "noise_robustness_parameter_heatmap.png"), dpi=300)
plt.close(fig)

print("\n[saved] noise_robustness/ (7 required files + config.json + systematic CSV)")
print("done.")
