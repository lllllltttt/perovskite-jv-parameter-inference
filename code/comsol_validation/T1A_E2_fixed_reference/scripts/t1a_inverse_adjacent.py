# -*- coding: utf-8 -*-
"""
t1a_inverse_adjacent.py -- v4 T1-A (E2) frozen-inversion adjacent-offset re-check.

Pure post-processing of the frozen inverse tables of E2_inverse_repair (and the
E2_finemesh inverse-adjacent companion table).  NO new COMSOL solve, no writes to
work1 frozen or v1-v3 outputs.  Read-only inputs:
  - e2v3_inverse_perrow.csv            (78 rows; per curve/ref inverse point estimate)
  - e2v3_inverse_mesh_sensitivity.csv  (432 rows; z_ref per level & param)
  - e2v3_fine_chain_perparam.csv       (frozen per-param max |z_ref| over fine chain)
  - e2v3_finemesh_inverse_adjacent.csv (frozen adjacent z_adj reference, 216 rows)

Definitions (same sigma-ref semantics as E2_inverse_repair / E2_finemesh):
  For representative t and parameter j:
    sigma_ref(t,j) = predictive sigma (norm space) of the frozen m=1 reference curve.
    z_ref(level,t,j) = (mu_norm(level,t,j) - mu_norm(ref,t,j)) / sigma_ref(t,j)
  Adjacent z-drift over a pair (c -> f) = z_ref(f) - z_ref(c) = d_mu_norm(c->f)/sigma_ref.
  Reported maxima are ACROSS the 6 reps x 9 params grid (=54 cells/pair), per pair,
  or per (pair,param) over the 6 reps.  Fine chain = {m0.35,m0.25,m0.18,m0.125}.

The claim being verified: fine-chain adjacent drift 0.062 -> 0.039 -> 0.021 sigma_ref
(monotone down, 0/54 cells > 0.1 sigma per fine-fine step); the 0.3-0.7 sigma_ref
"sensitivity" vs the frozen m=1 ref is concentrated in the single ref->m0.35 step.
Also checked: per-param fine-chain max |z_ref| vs e2v3_fine_chain_perparam.csv.
"""
import os, sys
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\project\work1\supplementary_validation_v3\_tools")
import v2lib
from v2lib import PARAM_NAMES

OUT = r"E:\project\work1\supplementary_validation_v4\T1A_E2\outputs\tables"
os.makedirs(OUT, exist_ok=True)
DIR = r"E:\project\work1\supplementary_validation_v3\E2_inverse_repair\outputs\tables"
ADJ = (r"E:\project\work1\supplementary_validation_v3\E2_finemesh\outputs\tables"
       r"\e2v3_finemesh_inverse_adjacent.csv")
REPS = [3741, 5808, 7693, 8874, 14179, 14912]
FINE = ["m0.35", "m0.25", "m0.18", "m0.125"]
PAIRS = [("ref", "m0.35"), ("m0.35", "m0.25"), ("m0.25", "m0.18"), ("m0.18", "m0.125")]
TOL = 1e-9

# ---------------------------------------------------------------------------
# 1. reconstruct per (rep, level, param) mu_norm and sigma_ref from perrow
# ---------------------------------------------------------------------------
per = pd.read_csv(os.path.join(DIR, "e2v3_inverse_perrow.csv"), low_memory=False)
assert len(per) == 78
mu_cols = ["mu_" + p for p in PARAM_NAMES]
sig_cols = ["sig_" + p for p in PARAM_NAMES]

recs = []
for ti, g in per.groupby("test_index"):
    rref = g[g.level == "ref"].iloc[0]
    sig_ref = {p: float(rref["sig_" + p]) for p in PARAM_NAMES}
    muref = {p: float(rref["mu_" + p]) for p in PARAM_NAMES}
    for _, row in g.iterrows():
        lv = row["level"]
        for p in PARAM_NAMES:
            mu = float(row["mu_" + p])
            s = sig_ref[p]
            if not np.isfinite(s) or s <= 0:
                z = np.nan
            else:
                z = (mu - muref[p]) / s
            recs.append(dict(test_index=int(ti), level=lv, param=p,
                             mu_norm=mu, sigma_ref=s,
                             z_ref=z, d_mu_norm=mu - muref[p]))
zr = pd.DataFrame(recs)                       # 78*9 = 702 rows
# sanity: ref row must have z_ref == 0 for every rep/param
assert np.isclose(zr[zr.level == "ref"]["z_ref"], 0.0).all()

# cross-check against the frozen mesh_sensitivity z_ref (fine + coarse levels)
ms = pd.read_csv(os.path.join(DIR, "e2v3_inverse_mesh_sensitivity.csv"),
                 low_memory=False)
mkey = ms[["test_index", "level", "param", "z_ref"]].rename(columns={"z_ref": "z_ref_frozen"})
chk = pd.merge(zr, mkey, on=["test_index", "level", "param"], how="inner")
chk["diff"] = (chk["z_ref"] - chk["z_ref_frozen"]).abs()
print("mesh_sensitivity z_ref cross-check: %d cells, max |diff| = %.3e"
      % (len(chk), chk["diff"].max()))
assert chk["diff"].max() <= TOL * 10

# ---------------------------------------------------------------------------
# 2. adjacent z-drift per pair and per (pair,param)
# ---------------------------------------------------------------------------
frozen_adj = pd.read_csv(ADJ)
frozen_adj["pair"] = frozen_adj["coarse"] + "->" + frozen_adj["fine"]

rowz = []
for c, f_ in PAIRS:
    zc = zr[zr.level == c].set_index(["test_index", "param"])["z_ref"]
    zf = zr[zr.level == f_].set_index(["test_index", "param"])["z_ref"]
    dz = (zf - zc).dropna()                      # per (rep,param)
    for p in PARAM_NAMES:
        sub = dz[dz.index.get_level_values("param") == p]
        rowz.append(dict(pair="%s->%s" % (c, f_), param=p,
                         n_reps=int(sub.shape[0]),
                         max_abs_dz_ref=float(sub.abs().max())))
rec_df = pd.DataFrame(rowz)
rec_df.to_csv(os.path.join(OUT, "t1a_inverse_adjacent_recompute.csv"),
              index=False, encoding="utf-8-sig")

# pair-level aggregates (across all 54 cells) + frozen comparison
summ = []
for c, f_ in PAIRS:
    zc = zr[zr.level == c].set_index(["test_index", "param"])["z_ref"]
    zf = zr[zr.level == f_].set_index(["test_index", "param"])["z_ref"]
    dz = (zf - zc).dropna()
    frz = frozen_adj[frozen_adj.pair == ("%s->%s" % (c, f_))]
    frz_dz = frz.set_index(["test_index", "param"])["z_adj"].abs() \
        if len(frz) else pd.Series(dtype=float)
    frz_dz = frz_dz.dropna()
    summ.append(dict(pair="%s->%s" % (c, f_), n_cells=int(dz.shape[0]),
                     max_abs_dz_ref=float(dz.abs().max()),
                     med_abs_dz_ref=float(dz.abs().median()),
                     n_gt_01=int((dz.abs() > 0.1).sum()),
                     frozen_max=float(frz_dz.max()) if len(frz_dz) else np.nan,
                     frozen_med=float(frz_dz.median()) if len(frz_dz) else np.nan,
                     frozen_n_gt_01=int((frz_dz > 0.1).sum()) if len(frz_dz) else -1,
                     max_ok=abs(dz.abs().max() - float(frz_dz.max())) <= TOL
                     if len(frz_dz) else False,
                     n_gt01_ok=(int((dz.abs() > 0.1).sum())
                                == int((frz_dz > 0.1).sum())) if len(frz_dz) else False))
sum_df = pd.DataFrame(summ)
sum_df.to_csv(os.path.join(OUT, "t1a_inverse_chain_summary.csv"),
              index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 3. per-param fine-chain max |z_ref| vs e2v3_fine_chain_perparam.csv
# ---------------------------------------------------------------------------
pp = pd.read_csv(os.path.join(DIR, "e2v3_fine_chain_perparam.csv"))
fc = zr[zr.level.isin(FINE)]
got = fc.groupby("param")["z_ref"].agg(lambda s: s.abs().max()).rename("recomp_max_abs_z_ref")
cmp = pp.set_index("param")
outp = []
for p in pp["param"]:
    frz = float(cmp.loc[p, "max_abs_z_ref"])
    mine = float(got[p])
    outp.append(dict(param=p, n_cells=int((fc["param"] == p).sum()),
                     recomp_max_abs_z_ref=mine, frozen_max_abs_z_ref=frz,
                     abs_diff=abs(mine - frz),
                     ok=abs(mine - frz) <= TOL * max(1.0, abs(frz))))
pp_df = pd.DataFrame(outp)
pp_df.to_csv(os.path.join(OUT, "t1a_inverse_perparam_recompute.csv"),
             index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
print("pair-level summary (recomputed vs frozen):")
print(sum_df.to_string(index=False))
print("\nper-param fine-chain max |z_ref| compare:")
print(pp_df.to_string(index=False))
print("\nadjacent recompute table written to t1a_inverse_adjacent_recompute.csv "
      "(%d rows)" % len(rec_df))
