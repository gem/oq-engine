# -*- coding: utf-8 -*-
"""
Tests for :mod:`openquake.fdha.utils`.
"""
import unittest

import numpy as np

from openquake.fdha.utils import rake_to_style


class RakeToStyleScalarTestCase(unittest.TestCase):
    """Scalar rake -> single style string."""

    def test_strike_slip_zero(self):
        self.assertEqual(rake_to_style(0.0), "strike_slip")

    def test_strike_slip_180(self):
        self.assertEqual(rake_to_style(180.0), "strike_slip")

    def test_strike_slip_neg180(self):
        self.assertEqual(rake_to_style(-180.0), "strike_slip")

    def test_normal(self):
        self.assertEqual(rake_to_style(-90.0), "normal")

    def test_normal_boundary_inside(self):
        self.assertEqual(rake_to_style(-60.0), "normal")

    def test_reverse(self):
        self.assertEqual(rake_to_style(90.0), "reverse")

    def test_reverse_boundary_inside(self):
        self.assertEqual(rake_to_style(120.0), "reverse")

    def test_undefined_string(self):
        self.assertEqual(rake_to_style("undefined"), "all")

    def test_undefined_mixed_case(self):
        self.assertEqual(rake_to_style("Undefined"), "all")


class RakeToStyleArrayTestCase(unittest.TestCase):
    """Array rake -> array of style strings."""

    def test_array(self):
        rakes = np.array([0.0, -90.0, 90.0, -150.0])
        expected = np.array([
            "strike_slip", "normal", "reverse", "strike_slip",
        ])
        got = rake_to_style(rakes)
        np.testing.assert_array_equal(got, expected)

    def test_single_element_array(self):
        got = rake_to_style(np.array([45.0]))
        self.assertEqual(got, "reverse")


class RakeToStyleValidationTestCase(unittest.TestCase):
    """Invalid inputs raise ValueError."""

    def test_out_of_range_positive(self):
        with self.assertRaises(ValueError):
            rake_to_style(200.0)

    def test_out_of_range_negative(self):
        with self.assertRaises(ValueError):
            rake_to_style(-200.0)

    def test_invalid_string(self):
        with self.assertRaises(ValueError):
            rake_to_style("reverse")
