"""
e2_design.py  (E2: mesh & tolerance convergence -- manifest builder)

Selects ~6 representative physical operating points (true frozen test samples,
re-used from the E1 12-sample cohort so results tie across tasks) and builds the
COMSOL job manifest for a controlled mesh-resolution x solver-tolerance
convergence study of the FROZEN 1D drift-diffusion model.

Each (sample, level) row is a full 131-pt J-V forward solve (V = 0:0.01:1.3 V).

Group selection (deterministic, all from the E1 cohort, no new samples):
    g1 median_PCE      closest to the cohort median PCE      (nominal operating point)
    g2 high_mobility   max common-scale log10(mobility)      (a_mu)
    g3 low_mobility    min a_mu
    g4 long_lifetime   max a_tau
    g5 asym_lifetime   max |r_tau|  (electron/hole lifetime asymmetry)
    g6 high_recomb     max rad_c   (bimolecular recombination coefficient)
Greedy selection over unchosen cohort members (ties -> next ranked) so the 6
groups are always distinct and traceable.

Levels per sample (8 solves):
    ref : mesh size factor m=1 (frozen) AND solver stol=1e-6 (frozen)  [runAll reference]
    mesh: mesh element-size factor m in {2.00, 1.41, 0.71, 0.50}  (stol frozen)
          m>1 coarser / m<1 finer; nominal relative density d = 1/m.
    tol : stationary relative tolerance stol in {1e-4, 1e-5, 1e-7}  (mesh frozen)
Mesh control scales hmax & hmin of BOTH the default `size` and the vertex
`size1` features of mesh1 by m; the mesh is rebuilt with model.mesh('mesh1').run
before each solve.  Tolerance is set on sol1's Stationary feature (`s1`, p:stol).
Level 0 of every sample is the shared frozen-config reference (m=1, stol=1e-6).

The worker also performs one model.study('std1').run solve (the E1/archive code
path) for its first sample when qc=1, so the runAll route can be validated
against the proven study.run route on identical frozen settings.

Writes (E2/inputs/): e2_cohort.csv (6 chosen + selection rationale),
e2_manifest.csv (48 rows), e2_meta.json.
"""
import os, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
E2 = os.path.dirname(HERE)
E1 = os.path.dirname(os.path.dirname(HERE)) and os.path.join(os.path.dirname(os.path.dirname(HERE)), "E1")
BASE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # E:\project\work1
INPUTS = os.path.join(E2, "inputs"); os.makedirs(INPUTS, exist_ok=True)

COH = pd.read_csv(os.path.join(E1, "inputs", "e1_cohort.csv"))
MAN = pd.read_csv(os.path.join(E1, "inputs", "e1_manifest.csv"))
BAS = MAN[MAN.design == "baseline"].copy()          # 12 true-parameter rows

MESH_FACTORS = [2.00, 1.41, 0.71, 0.50]             # element-size factor m (1.0 = frozen = ref)
TOL_LEVELS = [1e-4, 1e-5, 1e-7]                     # stol (1e-6 = frozen = ref)
STOL_FROZEN = 1e-6

PARAM9 = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]


def choose_groups():
    c = COH.sort_values("test_index").reset_index(drop=True)
    # rad_c per sample (physical) from E1 baseline manifest
    rc = BAS.set_index("test_index").loc[c.test_index, "rad_c"].values
    c = c.assign(rad_c=rc, _abs_r_tau=c.r_tau.abs())
    r = c.set_index("test_index")
    pick = {}
    def best(fn, exclude):
        sub = c[~c.test_index.isin(exclude)].copy()
        if sub.empty:
            return None
        return int(sub.sort_values(fn, ascending=False).test_index.iloc[0])

    # g1 nominal = closest to cohort median PCE
    med = float(c.pce.median())
    c["_dmed"] = (c.pce - med).abs()
    pick["g1_median_PCE"] = int(c.sort_values("_dmed").test_index.iloc[0])
    done = [pick["g1_median_PCE"]]
    for key, col, asc in [("g2_high_mobility", "a_mu", False),
                          ("g3_low_mobility", "a_mu", True),
                          ("g4_long_lifetime", "a_tau", False),
                          ("g5_asym_lifetime", "_abs_r_tau", False),
                          ("g6_high_recomb", "rad_c", False)]:
        sub = c[~c.test_index.isin(done)].sort_values(col, ascending=asc)
        sid = int(sub.test_index.iloc[0])
        pick[key] = sid
        done.append(sid)
    rows = []
    for key, sid in pick.items():
        cc = r.loc[sid]
        rows.append(dict(test_index=int(sid), group_id=key,
                         pce=float(cc.pce), a_mu=float(cc.a_mu), a_tau=float(cc.a_tau),
                         r_tau=float(cc.r_tau), rad_c=float(cc.rad_c)))
    return pd.DataFrame(rows)


def build_manifest(g):
    rows = []
    for _, gv in g.iterrows():
        sid = int(gv.test_index)
        p = BAS[BAS.test_index == sid].iloc[0]           # 9 physical params
        base = dict(test_index=sid, group_id=gv.group_id, pce=float(gv.pce))
        # shared frozen-config reference (m=1, stol frozen)
        rows.append(dict(base, level_type="ref", level="ref",
                         mesh_size_factor=1.0, stol=STOL_FROZEN, **phys(p)))
        for m in MESH_FACTORS:
            rows.append(dict(base, level_type="mesh", level=f"m{m:.2f}",
                             mesh_size_factor=float(m), stol=STOL_FROZEN, **phys(p)))
        for st in TOL_LEVELS:
            rows.append(dict(base, level_type="tol", level=f"stol{st:g}",
                             mesh_size_factor=1.0, stol=float(st), **phys(p)))
    df = pd.DataFrame(rows)
    df.insert(0, "rowid", np.arange(len(df)))            # unique, file order 0..47
    df = df[["rowid", "test_index", "group_id", "pce", "level_type", "level",
             "mesh_size_factor", "stol"] + PARAM9]
    df["run"] = 1
    return df


def phys(p):
    return {k: float(p[k]) for k in PARAM9}


def main():
    g = choose_groups()
    # drop the temporary _dmed column if present on a copy (choose_groups used a local df)
    g.to_csv(os.path.join(INPUTS, "e2_cohort.csv"), index=False)
    mf = build_manifest(g)
    mf.to_csv(os.path.join(INPUTS, "e2_manifest.csv"), index=False)
    json.dump(dict(n_groups=len(g), mesh_size_factors=MESH_FACTORS,
                   tol_levels=TOL_LEVELS, stol_frozen=STOL_FROZEN,
                   solves_per_sample=1 + len(MESH_FACTORS) + len(TOL_LEVELS),
                   total_solves=int(len(mf))),
              open(os.path.join(INPUTS, "e2_meta.json"), "w"), indent=2)
    print(g.to_string(index=False))
    print("\nmanifest rows:", len(mf))
    print(mf.groupby(["group_id", "level_type"]).size().to_string())


if __name__ == "__main__":
    main()
