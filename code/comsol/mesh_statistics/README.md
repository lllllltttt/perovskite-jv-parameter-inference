# Reference-mesh element counts, by domain

`reference_mesh_domain_elements.csv` records the element distribution of the
saved reference mesh (`mesh1`) of the model used for both simulation campaigns.

## How the numbers were obtained

Run by the authors in COMSOL Multiphysics 6.3 on 2026-11-27, on the server copy
of the model:

```
mphload('/home/student2/mph/1D_PSC_wen.mph')
% the saved mesh1 was read as stored
mphmeshstats(model, 'mesh1')          % domain/entity element counts
```

The saved mesh was read as it stands: no re-meshing and no solve were performed.
`hasproblems = 0`.

| Quantity | Value |
|---|---|
| Total 1D elements (edge) | 112 |
| Domain 1 (HTL, 0–20 nm) | 10 |
| Domain 2 (HTL\|PVK slab, 20–20.01 nm, mat6 "HTL&PVK") | 1 |
| Domain 3 (PVK, 20.01–490 nm) | 85 |
| Domain 4 (PVK\|C60 slab, 490–490.01 nm, mat5 "C60&PVK") | 1 |
| Domain 5 (C60, 490.01–510 nm) | 10 |
| Domain 6 (SnO2, 510–530 nm) | 5 |

Both 0.01 nm interface slabs carry exactly one element each.

## Identity checks against the archived model

* **Domain and material numbering** agree with Table S9.1 of the SI, which was
  assembled from the archived `1D_PSC_wen.mph`: domain 2 is the HTL|PVK slab on
  mat6 "HTL&PVK", domain 4 is the PVK|C60 slab on mat5 "C60&PVK".
* **Total element count** agrees with the value recorded for the same reference
  mesh in the archived mesh study: `nelem = 112` (E2 v1 reference rows,
  `code/comsol_validation/E2_v1_coarse_chain/outputs/curves/row_*.csv`).
* **Model file bytes.** The server file the run used and the archived
  `code/comsol/1D_PSC_wen.mph` are the same file: both have SHA-256
  `6d090d2e56ea8efef582714416088e3ca71e34f46168241f82a31c21573fc852`
  (verified 2026-11-27).

## Scope

These are the counts of the **reference mesh only**.  The refined grades of the
mesh-independence study (269 / 367 / 501 / 710 elements) keep their previously
archived totals and are not broken down by domain here, and no convergence
conclusion is drawn from this table.
