# COMSOL forward-model reproducibility table (SI Table S9)

**Status:** assembled 2026-08-25 · **Source:** `E:\project\work1\matlab&mph\1D_PSC_wen.mph` (the model copied from the server that generated the database; see `forward_validation_unbiased/run_forward_validation_unbiased.m`), cross-checked against `E:\project\work1\matlab&mph\run_PSC_9D_8.m` (server database-generation recipe) and the forward-validation MATLAB runner.

**Verification anchor:** the true-parameter control reproduced the stored target curve for sample `test_index=269` with RMSE = 0 (model version, parameter names, units, sweep, and J extraction jointly correct), and the full 45-sample true-parameter control passed within the verification tolerance (manuscript §2.11). Every number below was extracted from the archived model file (XML model tree + mphbin geometry/mesh), not re-run.

---

## S9.1 Fixed device configuration

One-dimensional drift–diffusion model along x, total thickness 530 nm. The six geometry intervals are `Interval` features i1–i6; the union `fin` produces six domains, numbered in increasing x. The three overlap regions of the input intervals (i2∩i5, i2∩i6, i3∩i6) tessellate in the union exactly as listed below — **domain labels below are the union domain numbers referenced by the stored selections**.

| Domain | x range (nm) | Thickness (nm) | Layer | Material (model tag) | Doping |
|---|---|---|---|---|---|
| 1 | [0, 20] | 20 | HTL | mat3 “HTL” | acceptor N_A = 1.8e18 cm⁻³ |
| 2 | [20, 20.01] | 0.01 | HTL\|PVK interface | mat6 “HTL&PVK” | (PVK-like; donor doping of domain 4/5 does not extend here) |
| 3 | [20.01, 490] | 469.99 | PVK absorber | mat2 “PVK” | intrinsic |
| 4 | [490, 490.01] | 0.01 | PVK\|C60 interface | mat5 “C60&PVK” | donor N_D = 1e17 cm⁻³ |
| 5 | [490.01, 510] | 19.99 | C60 ETL | mat1 “C60” | donor N_D = 1e17 cm⁻³ |
| 6 | [510, 530] | 20 | SnO2 ETL | mat4 “SnO2” | donor N_D = 1e16 cm⁻³ |

> **Doping placement (AnalyticDopingModel features):** adm1 “HTL” (acceptor, N_Ac = 1.8e18 cm⁻³) is selected on domain 1; adm2 “C60” (donor, N_Dc = 1e17 cm⁻³) on domains 4 and 5; adm3 “SnO2” (donor, N_Dc = 1e16 cm⁻³) on domain 6. The two 0.01-nm interface slabs are thin finite volumes that carry the interface-recombination lifetimes (S9.3); they are not zero-thickness boundaries.

## S9.2 Material parameters (per domain)

Fixed material parameters stored in the model. The PVK and the two interface slabs share the PVK mobility/DOS parameters, which are among the *sampled* quantities (Table 1); the three transport layers are fixed.

| Property | HTL (mat3) | PVK (mat2) | C60 (mat1) | SnO2 (mat4) | HTL\|PVK (mat6) | PVK\|C60 (mat5) |
|---|---|---|---|---|---|---|
| Relative permittivity εr | 11 | 70 (ε_pvk) | 4 | 9 | 70 | 70 |
| Band gap Eg (eV) | 3.6 | 1.56 | 2.0 | 3.5 | 1.56 | 1.56 |
| Electron affinity χ (eV) | 1.46 | 3.9 | 3.9 | 4.0 | 3.9 | 3.9 |
| Nc (cm⁻³) | 1.1e19 | 1e19 (= Nc_eff_pvk, sampled) | 1e20 | 2.2e17 | 1e19 | 1e19 |
| Nv (cm⁻³) | 1.6e19 | 1e19 (= Nv_eff_pvk, sampled) | 1e20 | 2.2e17 | 1e19 | 1e19 |
| μn (cm² V⁻¹ s⁻¹) | 50 | 20 (= μn_pvk, sampled) | 0.03 | 20 | 20 | 20 |
| μp (cm² V⁻¹ s⁻¹) | 50 | 20 (= μp_pvk, sampled) | 1e-4 | 10 | 20 | 20 |
| SRH lifetime τn = τp | 10 ns | τn_pvk / τp_pvk (sampled) | 10 ns | 10 ns | τ_HTL (sampled) | τ_ETL (sampled) |
| Radiative coefficient C | — | r_rad (sampled; Direct feature active on domain 3 only) | — | — | — | — |

> The generation recipe (`run_forward_validation_unbiased.m`, replicating `run_PSC_9D_8.m`) overrides the seven sampled global parameters with **explicit SI unit strings**: `mu_n_pvk`/`mu_p_pvk` in m² V⁻¹ s⁻¹, `tau_n_pvk`/`tau_p_pvk` in s, `Nc_eff_pvk`/`Nv_eff_pvk` in m⁻³, `tau_ETL`/`tau_HTL` in s, and `rad_c` with value ×10⁻⁶ in m³ s⁻¹ (CSV column is cm³ s⁻¹). The values in Table 1 are the consumed SI convention; the stored defaults above are cm-based model labels.

## S9.3 Recombination and generation

- **SRH bulk recombination** (`tar1`, all six domains): midgap trap (E_t − E_i = 0), carrier lifetimes taken from the material (τn = τp per domain as in S9.2). In the PVK these are the sampled τn/τp; in the two interface slabs the sampled τ_ETL / τ_HTL; in the transport layers the fixed 10 ns.
- **Interface recombination** is therefore represented as volumetric SRH inside the two 0.01-nm interface slabs carrying τ_ETL / τ_HTL (phenomenological effective interface lifetimes at the perovskite/ETL and perovskite/HTL boundaries — manuscript §2.1).
- **Radiative (bimolecular) recombination** (`dir1`): C = r_rad, active on the PVK domain (3) only.
- **Optical generation** (`udg1`, user-defined, PVK domain 3 only): G_n = G_p = G_pvk = 3.2e21 cm⁻³ s⁻¹, spatially uniform. The manuscript’s “standard AM1.5G illumination” corresponds to this **fixed uniform volume generation** in the absorber, not a wavelength-resolved spectrum.

## S9.4 Contacts and J–V sweep

- **Contacts** (`mc1`/`mc2`): ohmic, Richardson-type thermionic description with ideal barriers. `mc1` “Ag” (terminal 1, V0 = 0 V) at the HTL side; `mc2` “FTO” (terminal 2, V0 = V_app) at the SnO2 side. The terminal current is extracted as `semi.J0_1` (A m⁻²).
- **Study** (`std1`): stationary (steady-state) study. The J–V curve is produced by a parametric sweep of `V_app` over `range(0, 0.01, 1.3)` V (131 points) with continuation, matching the fixed grid V ∈ {0, 0.01, …, 1.3} V of the dataset. J is converted from A m⁻² to mA cm⁻² (×10⁻¹) downstream.
- **Mesh**: semiconductor ("semi") size settings stored in the model (h_min ≈ 1.06, h_max ≈ 6.89, h_curve 0.3, h_grad 1.15, in the model’s nm length unit); the mesh conforms to the 0.01-nm interface slabs. Element counts were not extracted (would require a COMSOL run).

## S9.5 Fixed (non-sampled) global parameter values

| Parameter | Value | Role |
|---|---|---|
| thickness_HTL / PVK / C60 / SnO2 | 20 / 470 / 20 / 20 nm | layer stack (i1–i6 derive from these) |
| epsilon_pvk | 70 | PVK relative permittivity |
| mu_n_pvk = mu_p_pvk | 20 cm² V⁻¹ s⁻¹ (default) | PVK mobilities (sampled per sample) |
| Nc_eff_pvk = Nv_eff_pvk | 1e19 cm⁻³ (default) | PVK DOS (sampled per sample) |
| tau_n_pvk = tau_p_pvk | 100 ns (default) | PVK SRH lifetimes (sampled per sample) |
| rad_c | 1e-10 cm³ s⁻¹ (default) | radiative coefficient (sampled per sample; consumed in m³ s⁻¹) |
| tau_ETL / tau_HTL | 1 ns (default) | interface lifetimes (sampled per sample) |
| G_pvk | 3.2e21 cm⁻³ s⁻¹ | uniform generation in PVK |
| T_cell | 300 K | lattice temperature |

**Defined but not used by any active feature of the production static study** (vestigial from an earlier transient/ionic formulation): `Nt_HTL_PVK`, `Nt_ETL_PVK` (1e12 cm⁻² trap densities — interface recombination is lifetime-based, not trap-density-based); ionic parameters `D_ion_a`, `D_ion_c`, `mu_ion_a`, `mu_ion_c`, `Cc_ion`, `Ca_ion`; transient-scan parameters `t_pre` (50 s), `T` (20 s), `scan_rate` (0.065 V s⁻¹), `V_max` (1.3 V); and the disabled parametric study steps `param`/`param1`/`param2` (sweeps over τ_HTL, τ_ETL, r_rad used during model development).

---

## Provenance and cross-verification

Every value above is traceable to the archived model:

1. **Layer stack / thicknesses** — `Interval` feature stored coordinates (dmodel.xml, live feature nodes, not edit history): i1 [0, 20], i2 [20, 490], i3 [490, 510], i4 [510, 530], i5 [20, 20.01], i6 [490, 490.01] (nm). Thickness parameters: 20/470/20/20 nm. The union of the overlapping intervals produces the six domains in S9.1.
2. **Material→domain mapping** — stored explicit selections (`selType="GEOMDIM"`), consistent with the doping selections and the geometry: mat3→domain 1, mat6→2, mat2→3, mat5→4, mat1→5, mat4→6. **No inconsistency found** between material, doping, and geometry domains.
3. **Doping** — adm1/adm2/adm3 impurity types and densities (acceptor 1.8e18 cm⁻³ on HTL; donor 1e17 cm⁻³ on C60 + PVK|C60 interface; donor 1e16 cm⁻³ on SnO2).
4. **Material properties** — `smodel.json` material nodes (Basic + Semiconductor_material + SRH + Direct groups), values as listed in S9.2.
5. **Generation / recombination selection** — udg1 (G_pvk, domain 3), dir1 (rad_c, domain 3), tar1 (from_mat lifetimes, all domains).
6. **Contacts and sweep** — mc1/mc2 settings; study std1 stationary step; solver parametric sweep over V_app `range(0, 0.01, 1.3)`.
7. **Recipe** — `run_forward_validation_unbiased.m` header replicates the server recipe exactly and reproduces stored curves (RMSE 0 on the sample verified); it is the authoritative statement of unit handling and J extraction.
