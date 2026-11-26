# Where `_frozen_preds.npz` comes from

The figure scripts in this folder read `_frozen_preds.npz` from **their own
directory**.  That file is produced by the single canonical extractor:

    code/pipeline/00_extract_frozen_predictions.py

There used to be a second copy of that script in this folder; it was removed
in v1.0.1 because it carried the superseded Voc convention (first sign change
of either direction, `np.interp` on a decreasing argument array).  Only one
extractor is shipped now, and it delegates device metrics to
`code/device_metrics.py`.

To regenerate the file next to the figure scripts:

    python code/pipeline/00_extract_frozen_predictions.py
    # or place it explicitly:
    JV_OUT_NPZ=code/figures/_frozen_preds.npz python code/pipeline/00_extract_frozen_predictions.py

The released `_frozen_preds.npz` (release asset `figure_source.tar.gz`) was
**not** regenerated for v1.0.1: it is the frozen artefact behind every
published figure.  `docs/REPRODUCE.md` compares the corrected extractor
against it.
