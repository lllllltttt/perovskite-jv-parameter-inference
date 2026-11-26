"""Read-only probe of the frozen Figure 4 (a-c) data."""
import os, sys, glob, re, pickle
import numpy as np
import pandas as pd
from scipy.io import loadmat

BASE = r"E:\project\work1"
sys.path.insert(0, os.path.join(BASE, "20261006",
                "manuscript_figures_SI_integrated_v2_layout_final", "scripts"))
import figstyle as st

NPZ = st.NPZ
J_SCALER = os.path.join(BASE, "data", "J_scaler.pkl")
DC_CSV = os.path.join(BASE, "decoder_comsol_audit",
                      "decoder_comsol_metrics_per_sample.csv")
FW_DIR = os.path.join(BASE, "forward_validation_unbiased")
FW_PRED = os.path.join(FW_DIR, "comsol_pred")
FW_TRUE = os.path.join(FW_DIR, "comsol_true")


def load_mat_J(path):
    dd = loadmat(path, squeeze_me=True)
    J = np.asarray(dd["J"], dtype=np.float64)
    if J.ndim == 2:
        J = J[:, 0]
    return J * 0.1


d = np.load(NPZ, allow_pickle=True)
V = d["V_GRID"]
Jraw = d["J_test_raw"]
with open(J_SCALER, "rb") as f:
    js = pickle.load(f)
recon = js.inverse_transform(d["recon_test"])

print("V_GRID:", V.shape, V[0], V[-1], "dtype", V.dtype)
print("J_test_raw:", Jraw.shape, "recon:", recon.shape)

for sid in (12058, 595, 14499):
    Jt = Jraw[sid]
    Jp = load_mat_J(os.path.join(FW_PRED, "Sample_%05d_pred.mat" % sid))
    Jd = recon[sid]
    d_dec = Jd - Jt
    d_com = Jp - Jt
    d_rev = Jt - Jd
    print("\ncase", sid)
    print("  target min/max %.6f %.6f" % (Jt.min(), Jt.max()))
    print("  dec    min/max %.6f %.6f" % (Jd.min(), Jd.max()))
    print("  comsol min/max %.6f %.6f" % (Jp.min(), Jp.max()))
    print("  rmse full dec %.6f  com %.6f  gap %.6f" %
          (np.sqrt(np.mean(d_dec**2)), np.sqrt(np.mean(d_com**2)),
           np.sqrt(np.mean((Jp - Jd) ** 2))))
    print("  rmse 0-1V dec %.6f com %.6f" %
          (np.sqrt(np.mean(d_dec[V <= 1.0] ** 2)),
           np.sqrt(np.mean(d_com[V <= 1.0] ** 2))))
    print("  rmse >1V  dec %.6f com %.6f" %
          (np.sqrt(np.mean(d_dec[V > 1.0] ** 2)),
           np.sqrt(np.mean(d_com[V > 1.0] ** 2))))
    print("  max|d_dec| %.6f  max|d_com| %.6f" %
          (np.abs(d_dec).max(), np.abs(d_com).max()))
    i1 = int(np.argmin(np.abs(V - 1.0)))
    print("  at V=%.4f: target %.4f dec %.4f comsol %.4f" %
          (V[i1], Jt[i1], Jd[i1], Jp[i1]))
    print("  diff d_rev vs -d_dec max %.2e" % np.max(np.abs(d_rev + d_dec)))
    print("  sign test: n(d_dec>0)=%d n(d_dec<0)=%d" %
          ((d_dec > 0).sum(), (d_dec < 0).sum()))

df = pd.read_csv(DC_CSV)
print("\naudit csv cols:", list(df.columns))
sel = df[df.sample_id.isin([12058, 595, 14499])]
print(sel.to_string(index=False))
print("\ncycle_gap ranks:", sel["cycle_gap"].values)
print("order-based cases:",
      [int(df.iloc[np.argsort(df.cycle_gap.values)[int(q * 44)]]["sample_id"])
       for q in (0.0, 0.5, 1.0)])
print("median cycle_gap %.6f" % df.cycle_gap.median())
print("min/max cycle_gap %.6f %.6f" % (df.cycle_gap.min(), df.cycle_gap.max()))

# V window used by inset
op = (V >= 0.0) & (V <= 1.0)
print("\ninset window points:", op.sum(), "V range", V[op][0], V[op][-1])
for sid in (14499,):
    Jt = Jraw[sid]; Jp = load_mat_J(os.path.join(FW_PRED, "Sample_%05d_pred.mat" % sid))
    Jd = recon[sid]
    print("  inset y range: %.4f .. %.4f" %
          (min(Jt[op].min(), Jd[op].min(), Jp[op].min()),
           max(Jt[op].max(), Jd[op].max(), Jp[op].max())))
