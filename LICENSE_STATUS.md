# Licence status — action required by the authors

**No licence file is included in this release, deliberately.**  The authors have
not yet decided the terms under which this material may be reused, and choosing a
licence is the authors' decision, not one this release can make on their behalf.

Making the repository public makes it *viewable and downloadable*.  It does not
grant an open-source or Creative Commons licence, and it does not place the content
in the public domain.  Until a `LICENSE` file is added, default copyright applies:
others may read and cite the material, but may not redistribute it or build on it
without permission.

## What the authors need to decide

1. **Code** — e.g. MIT, BSD-3-Clause or Apache-2.0.
2. **Data and derived tables** — e.g. CC BY 4.0 or CC0.
3. **Trained model weights** — typically the same as the code licence.
4. Whether a DOI should be registered through Zenodo or an institutional archive.
   *No DOI has been created for this release.*  The GitHub URL is a URL, not a DOI.

Once a decision is made, add `LICENSE` (and optionally `LICENSE-DATA`) at the
repository root and update the README.

## Third-party components referenced but not redistributed

| Component | Licence | How it is used here |
|---|---|---|
| COMSOL Multiphysics 6.3 | commercial, per-seat | required to regenerate J–V curves; **not** distributed |
| MATLAB / LiveLink for MATLAB | commercial, per-seat | required to run `code/comsol/*.m`; **not** distributed |
| TensorFlow 2.20, Keras 3.15 | Apache-2.0 | installed by the user from PyPI |
| NumPy, SciPy, pandas, scikit-learn, Matplotlib, h5py | BSD-3-Clause | installed by the user |

`code/comsol/1D_PSC_wen.mph` is the authors' own model file, not a COMSOL
distribution; it contains no licence material.

No licence file, activation code, or other credential from COMSOL or MathWorks is
included anywhere in this repository or its release assets.
