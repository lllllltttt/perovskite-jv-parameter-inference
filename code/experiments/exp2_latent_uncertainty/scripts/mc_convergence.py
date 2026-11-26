# -*- coding: utf-8 -*-
"""
MC convergence gate (EXP2 spec §5).

Fixed reproducible subset of 1,000 test samples (seed 20260825). For
M in {20, 50, 100, 200, 500}, estimate mu_total / V_latent / V_head /
V_total / f_latent / sigma_total and compare against the M=500 reference.

Nested draws: a single master epsilon block of 500 draws per subset sample
is drawn once; each smaller M uses its first M draws, so the comparison is
monotone and consistent.

Criterion (preferred): median relative error < 2% AND 95th-percentile
relative error < 5% for V_total and f_latent over principal nonzero cases.
If no smaller M passes -> select M=500.

Writes MC_CONVERGENCE.md.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import (EXP2, load_frozen_submodels, load_frozen_test,
                      encode_zstats, decompose_zs, N_PARAM)

OUT = os.path.join(EXP2, "MC_CONVERGENCE.md")
SUBSET_SEED = 20260825
EPS_SEED = 20260825
SUBSET_SIZE = 1000
M_VALUES = [20, 50, 100, 200, 500]
M_REF = 500
MED_THRESH = 0.02
Q95_THRESH = 0.05

lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)

# ---- subset selection (spec: seed 20260825) ----
rng_idx = np.random.default_rng(SUBSET_SEED)
idx = rng_idx.choice(15307, size=SUBSET_SIZE, replace=False)
idx.sort()

encoder, param_head = load_frozen_submodels()
J_test, params_test = load_frozen_test()
z_mean, z_log_var = encode_zstats(encoder, J_test[idx])
zm_s, zl_s = z_mean, z_log_var

rng = np.random.default_rng(EPS_SEED)
eps_master = rng.standard_normal((SUBSET_SIZE, M_REF, N_PARAM)).astype(np.float32)

# ---- decompose at each M ----
decomp = {}
for M in M_VALUES:
    eps = eps_master[:, :M, :]
    decomp[M] = decompose_zs(zm_s, zl_s, eps, param_head)

ref = decomp[M_REF]
Q = ["mu_total", "V_latent", "V_head", "V_total", "f_latent", "sigma_total"]

P("# MONTE-CARLO CONVERGENCE GATE")
P("")
P("Fixed subset: %d test samples (seed %d), nested draws (first M of a 500-draw master, seed %d)."
  % (SUBSET_SIZE, SUBSET_SEED, EPS_SEED))
P("Reference: M = %d.  Quantities compared: %s." % (M_REF, ", ".join(Q)))
P("")

def relerr(a, b):
    denom = np.maximum(np.abs(b), 1e-12)
    return np.abs(a - b) / denom

def abserr(a, b):
    return np.abs(a - b)

# ---- main table: V_total & f_latent rel err medians / q95 ----
P("## Convergence criterion (V_total, f_latent — principal nonzero cases)")
P("")
P("| M | med-relerr V_total | q95-relerr V_total | med-relerr f_latent | q95-relerr f_latent | pass |")
P("|---|---|---|---|---|---|")
selected = None
for M in M_VALUES[:-1]:
    vt = decomp[M]["V_total"]; vt_ref = ref["V_total"]
    fl = decomp[M]["f_latent"]; fl_ref = ref["f_latent"]
    # principal nonzero: keep pairs where reference magnitude is not ~zero
    nzv = np.abs(vt_ref) > 1e-6
    nzf = nzv  # f_latent meaningful only where total variance is nonzero
    e_vt = relerr(vt, vt_ref)[nzv]
    e_fl = relerr(fl, fl_ref)[nzf]
    med_vt = np.median(e_vt); q95_vt = np.percentile(e_vt, 95)
    med_fl = np.median(e_fl); q95_fl = np.percentile(e_fl, 95)
    ok = (med_vt < MED_THRESH and q95_vt < Q95_THRESH
          and med_fl < MED_THRESH and q95_fl < Q95_THRESH)
    P("| %d | %.4f | %.4f | %.4f | %.4f | %s |"
      % (M, med_vt, q95_vt, med_fl, q95_fl, "PASS" if ok else "-"))
    if selected is None and ok:
        selected = M
P("")
if selected is None:
    selected = M_REF
P("**Selected M = %d** (smallest passing, else M=500)." % selected)
P("")

# ---- per-quantity relative + absolute error table at selected M ----
P("## Per-quantity error at selected M = %d  (relative / absolute)" % selected)
P("")
P("| quantity | med-rel | q95-rel | med-abs | q95-abs | units of reference |")
P("|---|---|---|---|---|---|")
d = decomp[selected]
for q in Q:
    e_r = relerr(d[q], ref[q]); e_a = abserr(d[q], ref[q])
    med_r = np.median(e_r); q95_r = np.percentile(e_r, 95)
    med_a = np.median(e_a); q95_a = np.percentile(e_a, 95)
    med_ref = np.median(np.abs(ref[q]))
    P("| %-10s | %.4f | %.4f | %.2e | %.2e | ~%.2e |" % (q, med_r, q95_r, med_a, q95_a, med_ref))
P("")

# ---- absolute near-zero check ----
P("## Near-zero absolute check (quantities near zero should be judged by absolute error)")
P("")
for q in ["V_latent", "V_head"]:
    med_ref = np.median(np.abs(ref[q]))
    a = abserr(decomp[selected][q], ref[q])
    P("- %-10s median |ref| = %.3e ; median abs err = %.3e ; q95 abs err = %.3e"
      % (q, med_ref, np.median(a), np.percentile(a, 95)))
P("")

# ---- representative distribution of f_latent at selected M vs M=500 ----
P("## f_latent distribution (selected M vs M=500 reference)")
P("")
d = decomp[selected]
P("| | selected M=%d | M=500 |" % selected)
P("|---|---|---|")
for stat in ["mean", "median", "q25", "q75", "q90", "q95"]:
    fn = {"mean": np.mean, "median": np.median, "q25": lambda x: np.percentile(x, 25),
          "q75": lambda x: np.percentile(x, 75), "q90": lambda x: np.percentile(x, 90),
          "q95": lambda x: np.percentile(x, 95)}[stat]
    P("| %s | %.4f | %.4f |" % (stat, fn(d["f_latent"]), fn(ref["f_latent"])))
P("")

P("## Decision")
P("")
P("Selected M = **%d** for the full-test decomposition." % selected)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\nsaved:", OUT)
