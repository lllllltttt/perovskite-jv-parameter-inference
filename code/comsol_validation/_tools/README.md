# Archived shared library (`v2lib.py`)

`v2lib.py` is the module the final Figure 4 and the mesh-study analysis import
for device metrics, window RMSE and the interval score.  It is vendored here
byte-identically to `supplementary_validation_v2/_tools/v2lib.py` (MD5
`2be91d004d7cf5dc45ad483217438cd8`; the v3 copy is the same file).

Two things to know:

* `v2lib.device_metrics` is the **published** device-metric convention
  (downward crossing, interpolated root).  `code/device_metrics.py` is a
  cleaned, documented, tested re-implementation of exactly that function and is
  the entry point to prefer; the two agree to 1e-12 on every curve tested.
* The historical figure scripts add
  `<BASE>/supplementary_validation_v2/_tools` to `sys.path` before importing
  it.  When running them from a clone, either edit that line or copy this file
  to the path the script expects.

`infer_frozen.py` is the frozen encoder/head inference helper used by the
mesh-inversion study.
