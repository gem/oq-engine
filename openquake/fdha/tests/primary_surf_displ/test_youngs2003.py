# -*- coding: utf-8 -*-
"""
Tests for Youngs et al. (2003) primary surface fault displacement models.

Golden-truth values independently computed with scipy.stats (gamma, beta,
norm) using coefficients from Youngs et al. (2003) Appendix pp. 25-26
and Wells & Coppersmith (1994) Table 2.

Cross-validated against the fdhpy reference implementation
(https://github.com/NHR3-UCLA/FDHI_FDM) expected values in
``youngs_2003_prob_exceed_d_ad.csv``.
"""
import csv
import os
import unittest

import numpy as np

from openquake.fdha.primary_surf_displ.youngs2003 import (
    Youngs2003PrimaryFD_AD,
    Youngs2003PrimaryFD_MD,
)

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_FDHPY_CSV = os.path.join(
    _DATA_DIR, "expected", "youngs_2003_prob_exceed_d_ad.csv"
)


# ---------------------------------------------------------------------------
# AD class — gamma distribution
# ---------------------------------------------------------------------------
class Youngs2003ADTestCase(unittest.TestCase):
    """Tests for Youngs2003PrimaryFD_AD (average displacement)."""

    def setUp(self):
        self.model = Youngs2003PrimaryFD_AD()

    def test_get_prob_all_style(self):
        """Golden truth: mag=7.0, x_l=0.25, d=[0.1, 0.5, 1.0], all."""
        expected = np.array([
            9.2286884506663669e-01,
            6.4799057494215651e-01,
            4.4449818331816549e-01,
        ])
        got = self.model.get_prob(
            d=[0.1, 0.5, 1.0], x_l=[0.25], mag=7.0, style="all"
        )
        np.testing.assert_allclose(got.flatten(), expected, rtol=1e-10)

    def test_get_prob_normal_style(self):
        """Golden truth: mag=7.0, x_l=0.25, d=[0.1, 0.5, 1.0], normal."""
        expected = np.array([
            9.1326837515652248e-01,
            6.0871764656998451e-01,
            3.9323100672201489e-01,
        ])
        got = self.model.get_prob(
            d=[0.1, 0.5, 1.0], x_l=[0.25], mag=7.0, style="normal"
        )
        np.testing.assert_allclose(got.flatten(), expected, rtol=1e-10)

    def test_get_prob_normalized(self):
        """Gamma SF at x/L=0.25 for d_norm=[0.5, 1.0, 2.0]."""
        expected = np.array([
            6.7939262499279729e-01,
            4.2407181379529157e-01,
            1.5503742399819939e-01,
        ])
        got = self.model.get_prob_normalized(
            d_norm=[0.5, 1.0, 2.0], x_l=0.25
        )
        np.testing.assert_allclose(got, expected, rtol=1e-10)

    def test_output_shape(self):
        """Shape must be (n_displacements, n_sites)."""
        got = self.model.get_prob(
            d=[0.1, 0.5], x_l=[0.1, 0.3, 0.5], mag=7.0
        )
        self.assertEqual(got.shape, (2, 3))

    def test_get_prob_multi_site(self):
        """Golden truth: mag=7.0, d=[0.1, 1.0], x_l=[0.1, 0.5], all."""
        expected = np.array([
            [8.7092691347655693e-01, 9.7501330323892932e-01],
            [3.7465265273582099e-01, 5.7517507808766088e-01],
        ])
        got = self.model.get_prob(
            d=[0.1, 1.0], x_l=[0.1, 0.5], mag=7.0, style="all"
        )
        self.assertEqual(got.shape, (2, 2))
        np.testing.assert_allclose(got, expected, rtol=1e-10)

    def test_fdhpy_reference_d_ad(self):
        """
        Cross-validation against fdhpy expected values
        (youngs_2003_prob_exceed_d_ad.csv): D/AD, mag=7, x_l=0.5,
        WC94 All styles.
        """
        displacements = []
        expected_list = []
        with open(_FDHPY_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                displacements.append(float(row["displacement"]))
                expected_list.append(
                    float(row["probexceed_with_full_aleatory"])
                )
        displ = np.array(displacements)
        expected = np.array(expected_list)
        got = self.model.get_prob(
            d=displ, x_l=[0.5], mag=7.0, style="all"
        )
        np.testing.assert_allclose(got.flatten(), expected, rtol=1e-3)

    def test_invalid_style_raises(self):
        with self.assertRaises(ValueError):
            self.model.get_prob(d=[0.1], x_l=[0.25], mag=7.0,
                                style="reverse")

    def test_array_mag_raises(self):
        with self.assertRaises(ValueError):
            self.model.get_prob(d=[0.1], x_l=[0.25], mag=[7.0, 7.5])

# ---------------------------------------------------------------------------
# MD class — beta distribution
# ---------------------------------------------------------------------------
class Youngs2003MDTestCase(unittest.TestCase):
    """Tests for Youngs2003PrimaryFD_MD (maximum displacement)."""

    def setUp(self):
        self.model = Youngs2003PrimaryFD_MD()

    def test_get_prob_all_style(self):
        """Golden truth: mag=7.0, x_l=0.25, d=[0.1, 0.5, 1.0], all."""
        expected = np.array([
            7.7680760628065504e-01,
            4.4683538610983525e-01,
            2.6939952239662818e-01,
        ])
        got = self.model.get_prob(
            d=[0.1, 0.5, 1.0], x_l=[0.25], mag=7.0, style="all"
        )
        np.testing.assert_allclose(got.flatten(), expected, rtol=1e-10)

    def test_get_prob_normal_style(self):
        """Golden truth: mag=7.0, x_l=0.25, d=[0.1, 0.5, 1.0], normal."""
        expected = np.array([
            7.9874458761896383e-01,
            4.8019774940072169e-01,
            2.9269995877345162e-01,
        ])
        got = self.model.get_prob(
            d=[0.1, 0.5, 1.0], x_l=[0.25], mag=7.0, style="normal"
        )
        np.testing.assert_allclose(got.flatten(), expected, rtol=1e-10)

    def test_get_prob_normalized(self):
        """Beta SF at x/L=0.25 for d_norm=[0.2, 0.5, 0.8]."""
        expected = np.array([
            5.6370249992019239e-01,
            2.5249270949356473e-01,
            6.2701498298283379e-02,
        ])
        got = self.model.get_prob_normalized(
            d_norm=[0.2, 0.5, 0.8], x_l=0.25
        )
        np.testing.assert_allclose(got, expected, rtol=1e-10)

    def test_get_prob_multi_site(self):
        """Golden truth: mag=7.0, d=[0.1, 1.0], x_l=[0.1, 0.5], all."""
        expected = np.array([
            [7.1617808647947401e-01, 8.6269985480641498e-01],
            [2.3028370514491237e-01, 3.4091320586883966e-01],
        ])
        got = self.model.get_prob(
            d=[0.1, 1.0], x_l=[0.1, 0.5], mag=7.0, style="all"
        )
        self.assertEqual(got.shape, (2, 2))
        np.testing.assert_allclose(got, expected, rtol=1e-10)

# ---------------------------------------------------------------------------
# Symmetry and folding
# ---------------------------------------------------------------------------
class FoldXLTestCase(unittest.TestCase):
    """Tests for x/L folding (symmetry about midpoint)."""

    def test_fold_symmetry_ad(self):
        """x_l=0.25 and x_l=0.75 must give the same result."""
        model = Youngs2003PrimaryFD_AD()
        p1 = model.get_prob(d=[0.5], x_l=[0.25], mag=7.0)
        p2 = model.get_prob(d=[0.5], x_l=[0.75], mag=7.0)
        np.testing.assert_allclose(p1, p2, rtol=1e-14)

    def test_fold_symmetry_md(self):
        """Same symmetry test for MD class."""
        model = Youngs2003PrimaryFD_MD()
        p1 = model.get_prob(d=[0.5], x_l=[0.25], mag=7.0)
        p2 = model.get_prob(d=[0.5], x_l=[0.75], mag=7.0)
        np.testing.assert_allclose(p1, p2, rtol=1e-14)

