# -*- coding: utf-8 -*-
"""
si_table_s6_new.py — the data behind the two new Table S6 subsections.
=======================================================================

    python scripts/si_table_s6_new.py          write data_used/*.csv

build_si.py imports this module and calls tables() to *lay out* the same
numbers it writes here, so the delivered SI and the delivered CSV cannot
disagree, and neither can drift from Figure 3, which reads the same source
tables.

WHAT IS COMPUTED, AND FROM WHAT
-------------------------------
Nothing is re-simulated, re-predicted or re-fitted. Every number is read from
the frozen arrays and the corrected pair set, and each one is asserted against
the table the figure round already delivered:

    frozen arrays       params_test_raw, J_test_raw, J_test, V_GRID
                        (final_figures/scripts/_frozen_preds.npz)
    corrected pairs     data_used/fig3_pairs_v2.csv            11,245 rows
    random baseline     data_used/fig3_random_baseline_v2.csv  199,985 pairs
    cross-checks        data_used/fig3_case_parameters.csv,
                        fig3_case_coordinates.csv, fig3_case_summary.csv,
                        fig3_pair_summary_v2.csv

WHAT THE NEW SUBSECTIONS ARE
----------------------------
T6.7  the two curve pairs drawn in the main-text Fig. 3, in physical values:
      zero-based test indices, the database Sample_ID, the nine parameters
      with units and both members' values, |log10(theta_i) - log10(theta_j)|
      (which equals |log10(theta_i/theta_j)|), the factor 10^|Delta log10|,
      the six paired coordinates with both members' values and their
      differences, and the curve-distance and physical-current residuals.

      The factor column exists because the manuscript quotes "a factor of 443"
      and "a factor of 35": each is 10^|Delta log10| of one parameter, NOT the
      exponential of a difference of separately normalized parameters.
      coerce_factor() is the only place a factor is formed, and it is formed
      from the physical log10 difference.

T6.8  the distance-tier comparison of the six paired coordinates: pair counts,
      distinct test-curve counts, and the baseline-normalized median and
      interquartile range of each coordinate over all corrected pairs and over
      the five declared percentile subsets (10 / 5 / 1 / 0.5 / 0.1%).

T6.9  the six random-pair baseline medians and the physical log10 definition
      of each coordinate, so that every normalized value in T6.8 and in
      Fig. 3c is traceable to its own baseline.

No p-value is produced anywhere, and no uncertainty is attached to any tier
median: the pairs share curves, so they are not independent observations.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_v2 as L                                        # noqa: E402

OUT = os.path.dirname(HERE)
DATADIR = os.path.join(OUT, "data_used")

# Display label per parameter, subscript parts split out so the Word builder
# can set them as real subscripts: none of these takes a Unicode subscript
# glyph (there is no subscript c, no subscript capital, no subscript d).
PARAM_LABEL_PARTS = {
    "mu_n_pvk": [("μ", 0), ("n", 1)],
    "mu_p_pvk": [("μ", 0), ("p", 1)],
    "tau_n_pvk": [("τ", 0), ("n", 1)],
    "tau_p_pvk": [("τ", 0), ("p", 1)],
    "Nc_eff_pvk": [("N", 0), ("c", 1)],
    "Nv_eff_pvk": [("N", 0), ("v", 1)],
    "tau_ETL": [("τ", 0), ("ETL", 1)],
    "tau_HTL": [("τ", 0), ("HTL", 1)],
    "rad_c": [("r", 0), ("rad", 1)],
}
# Compact display units, same basis as lib_v2.PARAM_UNITS_PLAIN.
PARAM_UNITS_SHORT = {
    "mu_n_pvk": "m² V⁻¹ s⁻¹",
    "mu_p_pvk": "m² V⁻¹ s⁻¹",
    "tau_n_pvk": "s", "tau_p_pvk": "s",
    "Nc_eff_pvk": "m⁻³", "Nv_eff_pvk": "m⁻³",
    "tau_ETL": "s", "tau_HTL": "s",
    "rad_c": "cm³ s⁻¹",
}
# Coordinate rows: (id, family key, family label, ratio-symbol parts).
COORD_ROWS = [
    ("a_mu", "mobility", "mobility", [("μ", 0), ("n", 1), ("/", 0), ("μ", 0), ("p", 1)]),
    ("r_mu", "mobility", "mobility", [("μ", 0), ("n", 1), ("/", 0), ("μ", 0), ("p", 1)]),
    ("a_tau", "lifetime", "bulk lifetime", [("τ", 0), ("n", 1), ("/", 0), ("τ", 0), ("p", 1)]),
    ("r_tau", "lifetime", "bulk lifetime", [("τ", 0), ("n", 1), ("/", 0), ("τ", 0), ("p", 1)]),
    ("a_D", "DOS", "density of states", [("N", 0), ("c", 1), ("/N", 0), ("v", 1)]),
    ("r_D", "DOS", "density of states", [("N", 0), ("c", 1), ("/N", 0), ("v", 1)]),
]
COORD_FAMILY = dict((c[0], c[1]) for c in COORD_ROWS)
FAMILY_TABLES = [("mobility", "mobility", "a_mu", "r_mu"),
                 ("lifetime", "bulk lifetime", "a_tau", "r_tau"),
                 ("DOS", "density of states", "a_D", "r_D")]
TIER_LABELS = [("all", None), ("closest 10%", 0.10), ("closest 5%", 0.05),
               ("closest 1%", 0.01), ("closest 0.5%", 0.005),
               ("closest 0.1%", 0.001)]


def sig(x, n=4):
    """`n` significant digits, in the SI's own 'e' notation where needed."""
    x = float(x)
    if x == 0.0:
        return "0"
    a = abs(x)
    if 1e-3 <= a < 1e5:
        d = max(0, n - 1 - int(np.floor(np.log10(a))))
        return ("%.*f" % (d, x)) if d else "%.0f" % x
    m, e = ("%.*e" % (n - 1, x)).split("e")
    return "%se%d" % (m, int(e))


def coerce_factor(abs_dlog10):
    """The single place a multiplicative factor is formed: 10^|Delta log10|.

    Deliberately not exp() of a difference of separately normalized
    parameters, which is what the withdrawn phase-1 draft printed.
    """
    return float(10.0 ** float(abs_dlog10))


def load_pairs():
    pairs = pd.read_csv(os.path.join(DATADIR, "fig3_pairs_v2.csv"))
    rb = pd.read_csv(os.path.join(DATADIR, "fig3_random_baseline_v2.csv"))
    return pairs, rb.set_index("coordinate")["median_absd_random"]


def case_rows(F, i, j):
    """Everything T6.7 needs for one pair, straight from the frozen arrays."""
    raw, Lg, J, V, Jn = F["raw"], F["L"], F["J"], F["V"], F["Jn"]
    params = []
    for k, name in enumerate(L.PARAM_NAMES):
        d = float(Lg[i, k] - Lg[j, k])
        params.append(dict(
            parameter=name, unit=PARAM_UNITS_SHORT[name],
            theta_i=float(raw[i, k]), theta_j=float(raw[j, k]),
            log10_i=float(Lg[i, k]), log10_j=float(Lg[j, k]),
            abs_dlog10=abs(d),
            # |log10(theta_i/theta_j)|, computed as a ratio of the physical
            # values rather than from the logs, so the identity the caption
            # states is checked on the way past
            abs_log10_ratio=abs(float(np.log10(raw[i, k] / raw[j, k]))),
            factor=coerce_factor(abs(d))))
    dJ = J[j] - J[i]
    k_max = int(np.argmax(np.abs(dJ)))
    summary = dict(
        test_index_i=int(i), test_index_j=int(j),
        dJ_rmse_normalized=float(np.sqrt(np.mean((Jn[i] - Jn[j]) ** 2))),
        physical_rmse_mA_cm2=float(np.sqrt(np.mean(dJ ** 2))),
        max_abs_dJ_mA_cm2=float(np.abs(dJ[k_max])),
        max_abs_dJ_at_V=float(V[k_max]),
        J_i_at_0V=float(J[i, 0]), J_j_at_0V=float(J[j, 0]),
        J_i_min=float(J[i].min()), J_j_min=float(J[j].min()),
        J_i_max=float(J[i].max()), J_j_max=float(J[j].max()))
    coords = []
    for cid, _fam, _lab, ratio in COORD_ROWS:
        p, q = L.COORDS[[c[0] for c in L.COORDS].index(cid)][2:4]
        vi = (0.5 * (Lg[i, p] + Lg[i, q]) if cid.startswith("a")
              else Lg[i, p] - Lg[i, q])
        vj = (0.5 * (Lg[j, p] + Lg[j, q]) if cid.startswith("a")
              else Lg[j, p] - Lg[j, q])
        coords.append(dict(coordinate=cid, ratio=ratio,
                           value_i=float(vi), value_j=float(vj),
                           absd=abs(float(vi - vj))))
    return params, summary, coords


def tier_rows(pairs, rb):
    """T6.8: counts, normalized medians and normalized IQRs per tier."""
    dJ = pairs["dJ_rmse"].values
    order = np.argsort(dJ, kind="stable")
    n = len(pairs)
    out = []
    for label, frac in TIER_LABELS:
        sel = order if frac is None else order[:L.tier_k(n, frac)]
        ends = np.concatenate([pairs["i"].values[sel], pairs["j"].values[sel]])
        _u, cnt = np.unique(ends, return_counts=True)
        row = dict(set=label, n_pairs=int(sel.size),
                   distinct_samples=int(_u.size),
                   samples_in_multiple_pairs=int(np.sum(cnt > 1)),
                   max_pairs_per_sample=int(cnt.max()),
                   median_dJ=float(np.median(dJ[sel])))
        for cid, _fam, _lab, _r in COORD_ROWS:
            v = pairs["absd_" + cid].values[sel] / rb[cid]
            q25, med, q75 = np.percentile(v, [25, 50, 75])
            row["med_" + cid] = float(med)
            row["q25_" + cid] = float(q25)
            row["q75_" + cid] = float(q75)
        out.append(row)
    return pd.DataFrame(out)


def cross_check(pairs, rb, tiers, cases):
    """Assert every number against the table the figure round already shipped."""
    ck = pd.read_csv(os.path.join(DATADIR, "fig3_case_parameters.csv"))
    cc = pd.read_csv(os.path.join(DATADIR, "fig3_case_coordinates.csv"))
    cs = pd.read_csv(os.path.join(DATADIR, "fig3_case_summary.csv"))
    ps = pd.read_csv(os.path.join(DATADIR, "fig3_pair_summary_v2.csv")) \
        .set_index("set")

    for (tag, i, j, _why), (params, summary, coords) in zip(L.CASES, cases):
        sub = ck[ck["test_index_i"] == i]
        assert len(sub) == 9, \
            "fig3_case_parameters.csv: %d rows for case %s" % (len(sub), tag)
        for p in params:
            r = sub[sub["parameter"] == p["parameter"]].iloc[0]
            assert abs(r["abs_delta_log10"] - p["abs_dlog10"]) < 1e-12, \
                "%s %s abs_delta_log10" % (tag, p["parameter"])
            # the caption's identity: |log10(theta_i/theta_j)|
            #                       = |log10(theta_i) - log10(theta_j)|
            assert abs(p["abs_log10_ratio"] - p["abs_dlog10"]) < 1e-12, \
                "%s %s |log10 ratio| = |Delta log10|" % (tag, p["parameter"])
            assert abs(r["theta_i"] - p["theta_i"]) / p["theta_i"] < 5e-3
            assert abs(r["theta_j"] - p["theta_j"]) / p["theta_j"] < 5e-3
        for c in coords:
            r = cc[(cc["test_index_i"] == i)
                   & (cc["family"] == COORD_FAMILY[c["coordinate"]])].iloc[0]
            axis = "a" if c["coordinate"].startswith("a") else "r"
            assert abs(r["coord_%s_i" % axis] - c["value_i"]) < 1e-9
            assert abs(r["coord_%s_j" % axis] - c["value_j"]) < 1e-9
            assert abs(r["absd_%s" % axis] - c["absd"]) < 1e-9
        s = cs[cs["test_index_i"] == i].iloc[0]
        for key in ("dJ_rmse_normalized", "physical_rmse_mA_cm2",
                    "max_abs_dJ_mA_cm2", "max_abs_dJ_at_V"):
            assert abs(s[key] - summary[key]) / max(abs(summary[key]), 1e-12) \
                < 1e-6, "%s %s" % (tag, key)

    for label, frac in TIER_LABELS:
        name = "all corrected pairs" if frac is None else label
        r = ps.loc[name]
        t = tiers[tiers["set"] == label].iloc[0]
        assert int(t["n_pairs"]) == int(r["n_pairs"]), name
        assert int(t["distinct_samples"]) == int(r["distinct_samples"]), name
        for cid, _fam, _lab, _r in COORD_ROWS:
            assert abs(t["med_" + cid] - r["median_norm_" + cid]) < 1e-9, \
                "%s %s normalized median" % (name, cid)
            # the raw quartiles of the delivered summary, divided by the same
            # baseline, must reproduce the normalized quartiles printed here
            assert abs(t["q25_" + cid] * rb[cid]
                       - r["q25_absd_" + cid]) < 1e-9, \
                "%s %s raw q25" % (name, cid)
            assert abs(t["q75_" + cid] * rb[cid]
                       - r["q75_absd_" + cid]) < 1e-9, \
                "%s %s raw q75" % (name, cid)
    return True


def attach_sample_ids(cases, picks):
    """Add the database Sample_ID of both members to each case summary.

    The Sample_ID is not in the frozen arrays: it is the identifier the source
    database uses, and it reaches this round only through the delivered
    fig3_case_summary.csv, which is also what the figure's own annotation was
    built from. It is read here and cross-checked against the pair, so the SI
    table cannot quote a Sample_ID that belongs to another curve.
    """
    cs = pd.read_csv(os.path.join(DATADIR, "fig3_case_summary.csv"))
    for (i, j), (_params, summary, _coords) in zip(picks, cases):
        r = cs[cs["test_index_i"] == i]
        assert len(r) == 1, "fig3_case_summary.csv: %d rows for index %d" \
            % (len(r), i)
        r = r.iloc[0]
        assert int(r["test_index_j"]) == j, \
            "fig3_case_summary.csv pairs index %d with %d, not %d" \
            % (i, int(r["test_index_j"]), j)
        summary["sample_id_i"] = int(r["sample_id_i"])
        summary["sample_id_j"] = int(r["sample_id_j"])
    return cases


def tables(F=None, pairs=None, rb=None):
    """The three new subsections, as plain python structures."""
    if F is None:
        F = L.load_frozen()
    if pairs is None:
        pairs, rb = load_pairs()
    picks, info = L.select_figure_cases(pairs)
    cases = [case_rows(F, i, j) for i, j in picks]
    tiers = tier_rows(pairs, rb)
    cross_check(pairs, rb, tiers, cases)
    attach_sample_ids(cases, picks)
    return dict(cases=cases, picks=picks, info=info, tiers=tiers, rb=rb)


def main():
    F = L.load_frozen()
    pairs, rb = load_pairs()
    T = tables(F, pairs, rb)
    os.makedirs(DATADIR, exist_ok=True)

    # ---- T6.7: both cases, nine parameters, full source precision ---------
    rows = []
    for (tag, i, j, _why), (params, s, _c) in zip(L.CASES, T["cases"]):
        for p in params:
            rows.append(dict(case=tag, test_index_i=i, test_index_j=j,
                             sample_id_i=s["sample_id_i"],
                             sample_id_j=s["sample_id_j"], **p))
    pd.DataFrame(rows).to_csv(
        os.path.join(DATADIR, "si_table_s6_7_figure_cases.csv"), index=False)

    rows = []
    for (tag, i, j, _why), (_p, s, coords) in zip(L.CASES, T["cases"]):
        for c in coords:
            rows.append(dict(case=tag, test_index_i=i, test_index_j=j,
                             sample_id_i=s["sample_id_i"],
                             sample_id_j=s["sample_id_j"],
                             coordinate=c["coordinate"],
                             value_i=c["value_i"], value_j=c["value_j"],
                             absd=c["absd"],
                             absd_normalized=c["absd"] / rb[c["coordinate"]]))
    pd.DataFrame(rows).to_csv(
        os.path.join(DATADIR, "si_table_s6_7_figure_case_coordinates.csv"),
        index=False)

    T["tiers"].to_csv(os.path.join(DATADIR, "si_table_s6_8_tiers.csv"),
                      index=False)
    drawn = pd.read_csv(os.path.join(DATADIR, "fig3_random_baseline_v2.csv"))
    n_ret = int(drawn["n_random_pairs"].iloc[0])
    assert (drawn["n_random_pairs"] == n_ret).all()
    pd.DataFrame([dict(coordinate=c, median_absd_random=float(rb[c]),
                       n_random_pairs_drawn=int(L.N_RANDOM),
                       n_random_pairs_retained=n_ret,
                       random_seed=L.RANDOM_SEED)
                  for c, _f, _l, _r in COORD_ROWS]).to_csv(
        os.path.join(DATADIR, "si_table_s6_9_baselines.csv"), index=False)

    # ---- report ----------------------------------------------------------
    print("selection rule: %s" % L.FIGURE_CASE_RULE)
    print("  re-derived %s  (tier n = %d of %d pairs; |Dr_mu| = %.6f, "
          "|Dr_tau| = %.6f)"
          % (T["picks"], T["info"]["tier_pairs"], T["info"]["n_pairs"],
             T["info"]["absd_r_mu"], T["info"]["absd_r_tau"]))
    for (tag, i, j, _why), (params, s, coords) in zip(L.CASES, T["cases"]):
        print("\n%s  test index %d / %d  Sample_ID %d / %d   dJ = %.6f   "
              "phys RMSE = %.4f mA cm-2"
              % (tag, i, j, s["sample_id_i"], s["sample_id_j"],
                 s["dJ_rmse_normalized"], s["physical_rmse_mA_cm2"]))
        for p in params:
            print("    %-12s %-22s %s / %s   |Dlog10| = %.6f   10^ = %.2f"
                  % (p["parameter"], p["unit"], sig(p["theta_i"]),
                     sig(p["theta_j"]), p["abs_dlog10"], p["factor"]))
        for c in coords:
            print("    %-6s %+10.6f -> %+10.6f   |D| = %.6f   /base = %.4f"
                  % (c["coordinate"], c["value_i"], c["value_j"], c["absd"],
                     c["absd"] / rb[c["coordinate"]]))
    print("\nT6.8 distance tiers (baseline-normalized medians):")
    for _i, r in T["tiers"].iterrows():
        print("  %-14s pairs %6d  curves %6d  |Da_mu| %.3f  |Dr_mu| %.3f  "
              "|Da_tau| %.3f  |Dr_tau| %.3f  |Da_D| %.3f  |Dr_D| %.3f"
              % (r["set"], r["n_pairs"], r["distinct_samples"],
                 r["med_a_mu"], r["med_r_mu"], r["med_a_tau"], r["med_r_tau"],
                 r["med_a_D"], r["med_r_D"]))
    print("\nT6.9 baselines (%d pairs retained from %d drawn, seed %d):"
          % (n_ret, L.N_RANDOM, L.RANDOM_SEED))
    for c, _f, _l, _r in COORD_ROWS:
        print("  %-6s %.6f" % (c, rb[c]))
    print("\nwrote si_table_s6_7_figure_cases.csv, "
          "_7_figure_case_coordinates.csv, _8_tiers.csv, _9_baselines.csv")
    print("all cross-checks against the delivered figure tables passed")


if __name__ == "__main__":
    main()
