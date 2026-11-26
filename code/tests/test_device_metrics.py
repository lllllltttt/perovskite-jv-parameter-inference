# -*- coding: utf-8 -*-
"""Boundary tests for code/device_metrics.py.

Run with:  python -m unittest discover -s code/tests -v
(standard library only -- no pytest required)
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import device_metrics as dm  # noqa: E402


class VocCrossing(unittest.TestCase):
    def test_known_linear_zero(self):
        """J = [1, -1] over V = [1.26, 1.27]: the root is 1.265 V, not 1.27 V.

        This is the case a decreasing-argument np.interp gets wrong.
        """
        r = dm.device_metrics([1.0, -1.0], V=[1.26, 1.27])
        self.assertAlmostEqual(r["Voc"], 1.265, places=12)

    def test_exact_zero_at_node(self):
        r = dm.device_metrics([1.0, 0.0, -1.0], V=[1.25, 1.26, 1.27])
        self.assertEqual(r["Voc"], 1.26)
        self.assertEqual(r["n_down_cross"], 2)   # +->0 and 0->-

    def test_upward_change_is_not_a_crossing(self):
        """A reverse-bias tail (negative -> positive) must be skipped."""
        r = dm.device_metrics([-0.5, 1.0, -1.0], V=[1.24, 1.25, 1.26])
        self.assertAlmostEqual(r["Voc"], 1.255, places=12)
        self.assertEqual(r["n_down_cross"], 1)

    def test_no_downward_crossing_gives_nan(self):
        r = dm.device_metrics([1.0, 0.8, 0.6], V=[0.0, 0.01, 0.02])
        self.assertFalse(np.isfinite(r["Voc"]))
        self.assertFalse(np.isfinite(r["FF"]))
        self.assertFalse(np.isfinite(r["PCE"]))
        # Jsc stays defined: it does not depend on Voc
        self.assertEqual(r["Jsc"], 1.0)

    def test_non_finite_current_poisons_every_metric(self):
        r = dm.device_metrics([1.0, np.nan, -1.0], V=[1.25, 1.26, 1.27])
        self.assertFalse(r["finite"])
        for k in ("Jsc", "Voc", "FF", "PCE"):
            self.assertFalse(np.isfinite(r[k]), k)

    def test_length_mismatch(self):
        r = dm.device_metrics([1.0, -1.0], V=[0.0, 0.5, 1.0])
        self.assertFalse(r["finite"])
        self.assertIn("mismatch_len", r)

    def test_first_crossing_wins(self):
        r = dm.device_metrics([1.0, -1.0, 1.0, -1.0],
                              V=[1.0, 1.01, 1.02, 1.03])
        self.assertAlmostEqual(r["Voc"], 1.005, places=12)

    def test_grid_mode_matches_legacy_store(self):
        r = dm.device_metrics([1.0, -1.0], V=[1.26, 1.27], voc_mode="grid")
        self.assertEqual(r["Voc"], 1.27)


class DerivedMetrics(unittest.TestCase):
    def test_pce_equals_pmax(self):
        """PCE = Jsc*Voc*FF = Pmax by construction; FF absorbs Voc."""
        J = np.array([20.0, 18.0, 15.0, 10.0, 5.0, 0.5, -1.0])
        V = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.01])
        r = dm.device_metrics(J, V=V)
        self.assertAlmostEqual(r["PCE"], r["Pmax"], places=12)
        self.assertAlmostEqual(r["FF"], r["Pmax"] / (r["Jsc"] * r["Voc"]), places=12)

    def test_pmax_at_edge_flag(self):
        # no zero crossing: the generating quadrant ends at the last node and
        # the maximum power sits exactly there
        J = np.array([20.0, 18.0, 10.0])
        V = np.array([0.0, 0.5, 1.0])
        self.assertTrue(dm.device_metrics(J, V=V)["pmax_at_edge"])
        # an interior maximum does not raise the flag
        J2 = np.array([20.0, 15.0, 1.0, -1.0])
        V2 = np.array([0.0, 0.5, 1.0, 1.1])
        self.assertFalse(dm.device_metrics(J2, V=V2)["pmax_at_edge"])

    def test_full_grid_default(self):
        r = dm.device_metrics(np.linspace(20.0, -2.0, 131))
        self.assertEqual(dm.V_GRID.size, 131)
        self.assertTrue(0.0 <= r["Voc"] <= 1.3)
        self.assertTrue(np.isfinite(r["FF"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
