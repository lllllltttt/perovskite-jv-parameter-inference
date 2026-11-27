# -*- coding: utf-8 -*-
"""Finiteness and shape checks shared by the verification scripts.

Kept free of TensorFlow so the checks can be unit-tested quickly.
"""


def _arr(a):
    import numpy as np
    return np.asarray(a)


def nonfinite_report(arrays):
    """Return a list of problems for any array containing NaN or Inf.

    ``arrays`` maps a label to an array-like.  An empty array is reported too:
    a metric computed over no samples is not a valid result.
    """
    import numpy as np
    problems = []
    for name, a in arrays.items():
        try:
            arr = np.asarray(a)
        except Exception as exc:                     # pragma: no cover
            problems.append(f"{name}: not array-like ({exc})")
            continue
        if arr.size == 0:
            problems.append(f"{name}: empty array")
            continue
        bad = ~np.isfinite(arr)
        if bad.any():
            problems.append(f"{name}: {int(bad.sum())} of {arr.size} values "
                            f"are not finite")
    return problems


def shape_report(arrays, expected):
    """Return a list of problems where ``arrays[name].shape != expected[name]``."""
    import numpy as np
    problems = []
    for name, want in expected.items():
        if name not in arrays:
            problems.append(f"{name}: missing")
            continue
        got = tuple(np.asarray(arrays[name]).shape)
        if got != tuple(want):
            problems.append(f"{name}: shape {got}, expected {tuple(want)}")
    return problems


def scalar_report(scalars):
    """Return a list of problems for named scalar metrics that are NaN/Inf."""
    import numpy as np
    problems = []
    for name, v in scalars.items():
        try:
            f = float(v)
        except Exception:
            problems.append(f"{name}: not a scalar ({v!r})")
            continue
        if not np.isfinite(f):
            problems.append(f"{name}: {f}")
    return problems
