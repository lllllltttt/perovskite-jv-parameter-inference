==============================================================================
PHASE 1 — DATASET COMPATIBILITY GATE
Independent dataset: JV_database_9D_interface_lifetimes-3.csv
Original retained : JV_database_9D_interface_lifetimes-2.csv
==============================================================================

Row/column counts (excluding header):
  original retained : rows=102046  cols=141
  independent new   : rows=153067  cols=141

J-V column detection:
  original : 131 J columns, first=J_000 last=J_130
  new      : 131 J columns, first=J_000 last=J_130
  J column names identical: True
  non-J columns identical : True

------------------------------------------------------------------------------
A. PARAMETER SCHEMA (nine physical parameters)

mu_n_pvk    old=[4.560000e-07, 2.230000e-03]  new=[4.580000e-07, 2.230000e-03]  old_logspan=3.689  new_logspan=3.687  delta_logspan=-0.002
mu_p_pvk    old=[4.520000e-07, 2.110000e-03]  new=[4.490000e-07, 2.180000e-03]  old_logspan=3.669  new_logspan=3.686  delta_logspan=+0.017
tau_n_pvk   old=[4.780000e-10, 2.210000e-02]  new=[4.590000e-10, 2.200000e-02]  old_logspan=7.665  new_logspan=7.681  delta_logspan=+0.016
tau_p_pvk   old=[4.480000e-10, 2.040000e-02]  new=[4.510000e-10, 2.100000e-02]  old_logspan=7.658  new_logspan=7.668  delta_logspan=+0.010
Nc_eff_pvk  old=[4.640000e+22, 2.230000e+26]  new=[4.850000e+22, 2.230000e+26]  old_logspan=3.682  new_logspan=3.663  delta_logspan=-0.019
Nv_eff_pvk  old=[4.310000e+22, 2.180000e+26]  new=[3.530000e+22, 2.170000e+26]  old_logspan=3.704  new_logspan=3.789  delta_logspan=+0.085
tau_ETL     old=[1.000000e-12, 1.000000e-08]  new=[1.000000e-12, 1.000000e-08]  old_logspan=4.000  new_logspan=4.000  delta_logspan=+0.000
tau_HTL     old=[1.000000e-14, 1.000000e-10]  new=[1.000000e-14, 1.000000e-10]  old_logspan=4.000  new_logspan=4.000  delta_logspan=+0.000
rad_c       old=[1.000000e-12, 1.000000e-09]  new=[1.000000e-12, 1.000000e-09]  old_logspan=3.000  new_logspan=3.000  delta_logspan=+0.000

  all nine parameters strictly positive (old & new): True
  parameter order identical: True

------------------------------------------------------------------------------
B. J-V SCHEMA (131 points, 0.00-1.30 V in 0.01-V steps)

  expected grid : 0.00 -> 1.30 V, 131 points, step 0.01 V
  actual        : 131 J columns -> matches 131
  J units / magnitude:
    old J(V=0)   : min=0.3099 max=24.0962  (positive -> Jsc>0: True)
    new J(V=0)   : min=0.3235 max=24.0962  (positive -> Jsc>0: True)
    old J(V=1.30): min=-6358.7618 max=-0.0000
    new J(V=1.30): min=-6517.2233 max=-0.0000
    old global J : min=-6358.7618 max=24.0962
    new global J : min=-6517.2233 max=24.0962

  monotonic non-increasing J across sweep:
    old: 1.0000  of rows
    new: 1.0000  of rows
  zero-crossing exists within sweep (J changes sign):
    old: 1.0000  of rows
    new: 1.0000  of rows
  negative current in high-V region present (row with any J<0):
    old: True
    new: True

------------------------------------------------------------------------------
DATA QUALITY

  old rows=102046 missing=0 inf=0 dup_rows=0 dup_param_vectors=0 malformed_rows=0
  new rows=153067 missing=0 inf=0 dup_rows=0 dup_param_vectors=0 malformed_rows=0

------------------------------------------------------------------------------
C. DATA-GENERATION COMPATIBILITY

  Available evidence (from repo files, not re-run):
    - Same generator family: PSC_LHS_9D_interface_lifetimes (LHS, seed 42, 200000 draws).
    - Same COMSOL drift-diffusion family and geometry per archived recipe (see
      COMSOL_REPRODUCIBILITY_*.md, matlab&mph/; model 1D_PSC_wen.mph).
    - Same 9 physical parameters with the same average-and-ratio construction for the
      six bulk parameters (Table 1 of locked manuscript; tau_ETL/tau_HTL/rad_c sampled directly).
    - Same voltage grid 0-1.3 V, 131 points, mA/cm^2.
    - Same physical filtering concept (retained subset of the LHS draws); the new file
      carries 153,067 retained rows vs 102,046 for the old retained set.
  Range comparison (A) shows each new parameter is contained in, or overlaps strongly with,
  the old log-span for most parameters -> see A table and Phase 9 distribution analysis.

------------------------------------------------------------------------------
D. ORIGINAL-DATA OVERLAP (independent-generation support)

  Exact parameter-vector overlap (6-decimal normalized log10):
    old retained N = 102046, new N = 153067, overlapping distinct vectors = 0
  Overlap as fraction of new dataset: 0.00000

  Exact J-V row overlap (6-decimal normalized, 131-D):
    old N = 102046, new N = 153067, overlapping distinct J-vectors = 0
  Overlap as fraction of new dataset: 0.000000

==============================================================================
COMPATIBILITY VERDICT
==============================================================================
Verdict: COMPATIBILITY PASS WITH MILD SHIFT — REPORT AS DISTRIBUTION-SHIFT REPLICATION

The new dataset shares the exact schema, units, voltage grid and sign convention,
is itself physically filtered (153,067 retained rows), and shows 0/153067 exact
parameter-vector overlap with the original retained set. Any performance difference must
therefore be attributed to distribution shift (range / sampling / filtering details), not
schema incompatibility. See Phase 9 for the quantitative distribution comparison.
