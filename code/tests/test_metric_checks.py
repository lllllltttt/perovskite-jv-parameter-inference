# -*- coding: utf-8 -*-
"""Tests for code/metric_checks.py — the finite-value gate used by
code/verify_frozen_metrics.py.

Run with:  python -m unittest discover -s code/tests -v
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import metric_checks as mc  # noqa: E402


class NonFinite(unittest.TestCase):
    def test_finite_arrays_pass(self):
        arrays = {"J_test": np.zeros((4, 3)), "params_test": np.ones((4, 2)),
                  "param_mu": np.arange(8.0).reshape(4, 2)}
        self.assertEqual(mc.nonfinite_report(arrays), [])

    def test_nan_is_reported_with_name(self):
        a = np.zeros((3, 2))
        a[1, 1] = np.nan
        problems = mc.nonfinite_report({"param_mu": a})
        self.assertEqual(len(problems), 1)
        self.assertIn("param_mu", problems[0])
        self.assertIn("1 of 6", problems[0])

    def test_inf_is_reported(self):
        problems = mc.nonfinite_report({"recon_test": np.array([1.0, np.inf, -np.inf])})
        self.assertEqual(len(problems), 1)
        self.assertIn("recon_test", problems[0])
        self.assertIn("2 of 3", problems[0])

    def test_empty_array_is_reported(self):
        problems = mc.nonfinite_report({"coverage95": np.array([])})
        self.assertTrue(any("empty" in p for p in problems))

    def test_mixed_set_names_every_bad_array(self):
        problems = mc.nonfinite_report({
            "z_mean": np.ones((2, 2)),
            "param_sigma": np.array([[1.0, np.nan]]),
            "recon_test": np.array([[np.inf, 1.0]]),
        })
        joined = " ".join(problems)
        self.assertIn("param_sigma", joined)
        self.assertIn("recon_test", joined)
        self.assertNotIn("z_mean", joined)


class Shapes(unittest.TestCase):
    def test_matching_shapes_pass(self):
        arrays = {"J_test": np.zeros((15307, 131)), "params_test": np.zeros((15307, 9))}
        self.assertEqual(mc.shape_report(arrays, {"J_test": (15307, 131),
                                                  "params_test": (15307, 9)}), [])

    def test_wrong_shape_is_reported(self):
        problems = mc.shape_report({"J_test": np.zeros((100, 131))},
                                   {"J_test": (15307, 131)})
        self.assertEqual(len(problems), 1)
        self.assertIn("(100, 131)", problems[0])

    def test_missing_array_is_reported(self):
        problems = mc.shape_report({}, {"params_test": (15307, 9)})
        self.assertEqual(problems, ["params_test: missing"])


class Scalars(unittest.TestCase):
    def test_finite_scalars_pass(self):
        self.assertEqual(mc.scalar_report({"MSE mean": 1.2e-5, "rho": 0.43}), [])

    def test_nan_and_inf_scalars_fail(self):
        problems = mc.scalar_report({"MSE mean": np.nan, "mean rho": np.inf})
        self.assertEqual(len(problems), 2)

    def test_non_scalar_is_reported(self):
        problems = mc.scalar_report({"x": [1.0, 2.0]})
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
