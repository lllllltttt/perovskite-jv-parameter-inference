# COMSOL reproducibility — gaps, caveats, and resolution status

**Part of the EXP1–EXP4 final integration (Task #89).** Companion to `COMSOL_REPRODUCIBILITY_TABLE.md` (the SI Table S9 content). Assembled 2026-08-25 from the archived model `E:\project\work1\matlab&mph\1D_PSC_wen.mph` and the archived generation/forward recipes. **No COMSOL run was performed** (per task constraints).

**Overall verdict:** the fixed-model configuration is fully recoverable from the archived model + recipes and is internally consistent (geometry ↔ materials ↔ doping ↔ generation ↔ recombination ↔ contacts ↔ sweep all agree). The gaps below are documentation-level, not blocking; each has a resolution already in place or proposed.

---

## G1 — Mesh statistics and element resolution of the 0.01-nm interface slabs

- **Resolution of the reference mesh.** The saved mesh of the model used for both campaigns was read in COMSOL 6.3 (`mphload` of `1D_PSC_wen.mph`, stored `mesh1` read as it stands, `mphmeshstats`; no re-meshing and no solve, `hasproblems = 0`). It contains **112 1D elements**, distributed over domains 1–6 as **10 / 1 / 85 / 1 / 10 / 5**: each 0.01 nm interface slab (domain 2, mat6 "HTL&PVK"; domain 4, mat5 "C60&PVK") carries **one element**. The source model's SHA-256 `6d090d2e56ea8efef582714416088e3ca71e34f46168241f82a31c21573fc852` matches the archived `code/comsol/1D_PSC_wen.mph`, and the total agrees with the `nelem = 112` recorded for the reference mesh in the archived mesh study.  Data: `code/comsol/mesh_statistics/`.
- **Why it matters:** the two interface slabs are the physical carriers of τ_ETL / τ_HTL. If the slab is under-resolved, the effective interface recombination velocity implied by the slab thickness (S = d/τ) could be mesh-sensitive.
- **Status:** low risk. The 45-sample true-parameter control reproduces stored curves exactly (median RMSE 0.00000 mA cm⁻²), which is a strong empirical check that the archived model + recipe reproduces the database as run on the server. This is a *verification* gap, not a *configuration* gap.
- **Scope.** These counts describe the reference mesh only. The refined grades of the mesh-independence study (269 / 367 / 501 / 710 elements) keep their archived totals and are not broken down by domain here, and no convergence conclusion is drawn from the per-domain numbers.

## G2 — Interface recombination as thin-slab lifetimes: S-value mapping not stated in the manuscript

- **Gap:** interface recombination enters as SRH lifetimes τ_ETL / τ_HTL inside 0.01-nm volumetric slabs. The manuscript deliberately presents interface recombination as effective interface lifetimes (§2.1) and does not give the equivalent surface recombination velocity. A reviewer who wants S_eff = d/τ must derive it (with d = 0.01 nm = 10⁻⁷ cm → S_eff ∈ ~10–10⁵ cm s⁻¹ over the sampled τ ranges).
- **Status:** acceptable by design (the manuscript's wording is explicit about the lifetime representation). The SI table now documents the slab width, so the mapping is derivable.

## G3 — "Standard AM1.5G illumination" wording vs. uniform volume generation

- **Gap:** manuscript §2.1 states "under standard AM1.5G illumination". The model uses a **fixed, spatially uniform** volume generation G_pvk = 3.2e21 cm⁻³ s⁻¹ in the PVK only — no spectral absorption, no depth profile. An AM1.5G spectral-irradiance interpolation function existed in the modeling history and was **removed** during development.
- **Why it matters:** "AM1.5G" can be read as a wavelength-resolved illumination simulation; the actual model is a single equivalent uniform generation rate.
- **Status:** resolved for reproducibility by SI Table S9.3 (now states the uniform-generation convention explicitly). Optional manuscript-wording touch (e.g., "a fixed uniform volume generation rate equivalent to AM1.5G illumination") belongs to the integration changelog (deliverable B), not a content change.

## G4 — Vestigial parameters and disabled study steps in the raw .mph

- **Gap:** the model file contains parameters not used by the active production study: trap densities `Nt_HTL_PVK`/`Nt_ETL_PVK` (1e12 cm⁻²), ionic parameters (`D_ion_a/c`, `mu_ion_a/c`, `Cc_ion`, `Ca_ion`), transient-scan parameters (`t_pre`, `T`, `scan_rate`, `V_max`), and three disabled parametric study steps (`param`, `param1`, `param2` sweeping τ_HTL, τ_ETL, r_rad). A reader reproducing from the raw file could be misled about what is active.
- **Status:** documented in SI Table S9.5 ("defined but not used"). The archived driver scripts (`run_PSC_9D_8.m` / `run_forward_validation_unbiased.m`) are the authoritative recipe and are unambiguous about what is set and run.

## G5 — Stored parameter defaults ≠ database sample values

- **Gap:** the model's stored defaults (μn = μp = 20 cm² V⁻¹ s⁻¹, Nc = Nv = 1e19 cm⁻³, τ = 100 ns, r_rad = 1e-10 cm³ s⁻¹, τ_ETL = τ_HTL = 1 ns) are template values, overwritten per sample by the generation recipe. Running the .mph as-is gives the defaults, not a database sample.
- **Status:** standard template-model behavior; the recipe (archived) performs the per-sample override with explicit SI units. Stated in SI Table S9.5.

## G6 — J-extraction convention (sign and unit)

- **Gap:** none in substance. J is `semi.J0_1` (terminal 1, the Ag contact) in A m⁻², converted ×10⁻¹ to mA cm⁻²; dataset sign convention J_sc = |J(V=0)|, J(V_oc) = 0 (manuscript §2.1). The sign convention is a dataset-definition choice; the true-parameter control verifies the full chain.
- **Status:** verified and already stated in the manuscript.

## G7 — rad_c unit handling at the model-file level

- **Gap:** the model stores `rad_c = 1e-10[cm^3/s]`; the recipe overrides with value ×10⁻⁶ in `[m^3/s]` (CSV column is cm³ s⁻¹). This is the known unit hazard the manuscript already documents (§2.1, Table 1 note). No new gap; the SI table repeats the model-file-level fact for completeness.
- **Status:** resolved in manuscript + SI Table S9.2 note.

---

## Summary table

| Gap | Severity | Blocking? | Resolution |
|---|---|---|---|
| G1 mesh/element resolution of interface slabs | Low | No | True-control exact reproduction (empirical check) |
| G2 S-value mapping not stated | Low | No | Manuscript explicitly uses lifetimes; SI S9.1/S9.3 give slab width |
| G3 AM1.5G wording vs uniform G | Low | No | SI S9.3 states uniform-generation convention; optional wording touch (deliverable B) |
| G4 vestigial params / disabled steps | Low | No | SI S9.5 lists them explicitly |
| G5 stored defaults ≠ samples | Low | No | Archived recipe is authoritative; SI S9.5 states it |
| G6 J extraction convention | — | No | Verified + stated in manuscript §2.1 |
| G7 rad_c unit handling | — | No | Documented in manuscript + SI |

**Conclusion:** the COMSOL forward model is reproducible from the archived `.mph` + archived driver recipes to the level required for the paper's claims. All gaps are documentation-level and are addressed in SI Table S9 (S9.1–S9.5). No COMSOL rerun is required to support the integration.
