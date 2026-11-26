"""
auditD_coordinates.py  (Audit D: common-scale/ratio coordinate construction)

Read-only check of the sampling-prior -> retained-database coordinate chain:
  * theta_n = s*sqrt(q), theta_p = s/sqrt(q) construction (log10 linear pair),
    with s = geometric mean (common scale) and q = asymmetry ratio,
  * s,q extents/units in the raw retained LHS prior file (script/...200000_3.csv,
    the only raw sample draw stored locally) vs. the physically retained
    DB-2 (data/JV_database_9D_interface_lifetimes-2.csv, N=102,046),
  * how far the retained DB-2 lies inside the prior box (per-coordinate).

Outputs (this folder): auditD_coordinates_summary.csv, auditD_sq_distributions.png
No file is modified.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
LHSF = os.path.join(BASE, "script", "PSC_LHS_9D_interface_lifetimes_200000_3.csv")
DB2F = os.path.join(BASE, "data", "JV_database_9D_interface_lifetimes-2.csv")
OUT = HERE

# DB-2 (retained) column names (tau_ETL/tau_HTL = PVK|C60 / HTL|PVK slab lifetimes)
PHYS_DB2 = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
            "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
# raw LHS file column names (interface lifetimes stored as tau_interface_ETL/HTL)
PHYS_LHS = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
            "Nc_eff_pvk", "Nv_eff_pvk", "tau_interface_ETL", "tau_interface_HTL", "rad_c"]
# (electron idx, hole idx) for the three paired bulk families
PAIRS = [("mu_n_pvk", "mu_p_pvk"), ("tau_n_pvk", "tau_p_pvk"),
         ("Nc_eff_pvk", "Nv_eff_pvk")]


def s_q(df):
    out = {}
    for i, (en, hp) in enumerate(PAIRS):
        e = df[en].to_numpy(float); h = df[hp].to_numpy(float)
        s = np.sqrt(e * h)                       # common scale (geometric mean)
        q = e / h                                # asymmetry ratio (electron/hole)
        out[f"s_{i}"] = s; out[f"q_{i}"] = q
    return out


def stats(x):
    x = np.asarray(x, float)
    return dict(min=float(x.min()), max=float(x.max()),
                p1=float(np.percentile(x, 1)), p50=float(np.percentile(x, 50)),
                p99=float(np.percentile(x, 99)),
                mean=float(x.mean()), std=float(x.std()))


def main():
    lhs = pd.read_csv(LHSF)
    db2 = pd.read_csv(DB2F)
    print(f"LHS prior rows: {len(lhs)}   DB-2 retained rows: {len(db2)}")

    # ---- (1) is DB-2 a subset of the stored LHS draw? (exact 9-param vector)
    lk = set()
    for _, r in lhs[PHYS_LHS].iterrows():
        lk.add(",".join("%.17g" % v for v in r.to_numpy(float)))
    hit = 0; miss_geo = []
    for _, r in db2[PHYS_DB2].iterrows():
        k = ",".join("%.17g" % v for v in r.to_numpy(float))
        if k in lk: hit += 1
    print(f"DB-2 rows exactly matching stored LHS draw: {hit} / {len(db2)}")

    # ---- (2) per-physical-parameter extents: prior bounds vs DB-2
    rows = []
    for c, cl in zip(PHYS_DB2, PHYS_LHS):
        rows.append(dict(quantity=c, domain="physical",
                         prior_min=float(lhs[cl].min()), prior_max=float(lhs[cl].max()),
                         db2_min=float(db2[c].min()), db2_max=float(db2[c].max())))
    # ---- (3) per-parameter extents vs the DECLARED (constructed) Table-1 box
    # Table 1 ranges (consumed units): the six bulk params are constructed
    #   mu in [4.5e-7, 2.2e-3] m2/V/s ; tau in [4.5e-10, 2.2e-2] s ;
    #   DOS in [4.5e21, 2.2e26] m-3  (= latent_avg/sqrt5 .. latent_avg*sqrt5) ;
    #   tau_ETL [1e-12,1e-8] s ; tau_HTL [1e-14,1e-10] s ; rad_c [1e-12,1e-9] cm3/s.
    DECLARED = {
        "mu_n_pvk":  (4.5e-7, 2.2e-3),  "mu_p_pvk": (4.5e-7, 2.2e-3),
        "tau_n_pvk": (4.5e-10, 2.2e-2), "tau_p_pvk": (4.5e-10, 2.2e-2),
        "Nc_eff_pvk": (4.5e21, 2.2e26), "Nv_eff_pvk": (4.5e21, 2.2e26),
        "tau_ETL":   (1e-12, 1e-8),     "tau_HTL":  (1e-14, 1e-10),
        "rad_c":     (1e-12, 1e-9),
    }
    rows = []
    for c in PHYS_DB2:
        lo, hi = DECLARED[c]
        x = db2[c].to_numpy(float)
        frac_in = float(((x >= lo) & (x <= hi)).mean())
        # fraction sitting essentially on a declared edge (rel 1e-6 of log10 width)
        logw = np.log10(hi) - np.log10(lo)
        tol = 1e-6 * logw
        dl = np.abs(np.log10(x) - np.log10(lo))
        at_lo = float((dl < tol).mean())
        rows.append(dict(quantity=c,
                         declared_lo=lo, declared_hi=hi,
                         db2_min=float(x.min()), db2_max=float(x.max()),
                         frac_inside=frac_in, frac_at_low_edge=at_lo))
    rdf = pd.DataFrame(rows)
    rdf.to_csv(os.path.join(OUT, "auditD_declared_box.csv"), index=False)
    print(rdf.to_string(index=False))

    # ---- (4) s,q stats (in log10 decades for s; q linear + log10)
    sl = s_q(lhs); sd = s_q(db2)
    names = {0: "mobility", 1: "lifetime", 2: "DOS"}
    rows2 = []
    for i in range(3):
        for tag, d in (("prior", sl), ("DB2", sd)):
            s = d[f"s_{i}"]; q = d[f"q_{i}"]
            rows2.append(dict(pair=names[i], source=tag, coord="s_common",
                              min=float(s.min()), max=float(s.max()),
                              log10min=float(np.log10(s.min())), log10max=float(np.log10(s.max())),
                              log10p50=float(np.median(np.log10(s)))))
            rows2.append(dict(pair=names[i], source=tag, coord="q_ratio",
                              min=float(q.min()), max=float(q.max()),
                              log10min=float(np.log10(q.min())), log10max=float(np.log10(q.max())),
                              log10p50=float(np.median(np.log10(q)))))
    sdf = pd.DataFrame(rows2)
    sdf.to_csv(os.path.join(OUT, "auditD_sq_summary.csv"), index=False)
    print(sdf.to_string(index=False))

    # ---- (4) retained coverage fraction per coordinate (DB-2 inside prior box)
    # compute prior empirical percentiles of s,q and DB-2 percentiles
    print("\nDB-2 coordinate percentiles (log10 s ; log10 q):")
    for i in range(3):
        ps = np.log10(sl[f"s_{i}"]); pdq = np.log10(sd[f"s_{i}"])
        pr = np.log10(sl[f"q_{i}"]); pdr = np.log10(sd[f"q_{i}"])
        print(f"  {names[i]:8s} log10s prior[{np.percentile(ps,1):.2f},{np.percentile(ps,99):.2f}] "
              f"DB2[{np.percentile(pdq,1):.2f},{np.percentile(pdq,99):.2f}]  | "
              f"log10q prior[{np.percentile(pr,1):.2f},{np.percentile(pr,99):.2f}] "
              f"DB2[{np.percentile(pdr,1):.2f},{np.percentile(pdr,99):.2f}]")

    # ---- (5) quick distribution figure (overlay prior vs DB-2)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 3, figsize=(12, 6))
    for i in range(3):
        ax = axs[0, i]
        ax.hist(np.log10(sl[f"s_{i}"]), bins=60, alpha=0.55, label="prior (LHS draw)", color="#0072B2")
        ax.hist(np.log10(sd[f"s_{i}"]), bins=60, alpha=0.55, label="DB-2 retained", color="#E69F00")
        ax.set_title(f"{names[i]}: log10 common scale s")
        ax.legend(fontsize=7)
        ax = axs[1, i]
        ax.hist(np.log10(sl[f"q_{i}"]), bins=60, alpha=0.55, label="prior (LHS draw)", color="#0072B2")
        ax.hist(np.log10(sd[f"q_{i}"]), bins=60, alpha=0.55, label="DB-2 retained", color="#E69F00")
        ax.set_title(f"{names[i]}: log10 ratio q")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "auditD_sq_distributions.png"), dpi=150)
    print("\nwrote", os.path.join(OUT, "auditD_sq_distributions.png"))


if __name__ == "__main__":
    main()
