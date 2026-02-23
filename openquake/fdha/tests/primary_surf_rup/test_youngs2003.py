# -*- coding: utf-8 -*-
"""
Tests for Youngs et al. (2003) surface rupture probability models.

All golden-truth values independently computed with scipy.special.expit
using coefficients from Youngs et al. (2003), Appendix, p. 25.
"""
import unittest

import numpy as np

from openquake.hazardlib.contexts import RuptureContext
from openquake.fdha.primary_surf_rup.youngs2003 import (
    Youngs2003PrimarySR_ExC,
    Youngs2003PrimarySR_GB,
    Youngs2003PrimarySR_nBR,
)


# ---------------------------------------------------------------------------
# Extensional Cordillera (ExC)
# Coefficients: a = -12.53, b = 1.921
# Data: 105 earthquakes, Mw 4.5–7.6
# Source: Youngs et al. (2003), Appendix, p. 25
# ---------------------------------------------------------------------------
class Youngs2003ExCTestCase(unittest.TestCase):
    """Tests for Youngs2003PrimarySR_ExC."""

    def setUp(self):
        self.model = Youngs2003PrimarySR_ExC()

    # --- Golden-truth regression ---
    # Values computed with scipy.special.expit using (a=-12.53, b=1.921)
    # from Youngs et al. (2003), Appendix, p. 25.

    def test_golden_truth(self):
        mags = np.array([5.0, 5.5, 6.0, 6.5, 7.0, 7.5])
        expected = np.array([
            5.0931470252943589e-02, 1.2298086895506556e-01,
            2.6815570087449986e-01, 4.8912671452713180e-01,
            7.1443044088033858e-01, 8.6732370731218145e-01,
        ])
        got = self.model.get_prob(RuptureContext([('mag', mags)]))
        np.testing.assert_allclose(got, expected, rtol=1e-10)


# ---------------------------------------------------------------------------
# Great Basin (GB)
# Coefficients: a = -16.02, b = 2.685
# Data: 32 earthquakes, Mw 4.9–7.2
# Source: Youngs et al. (2003), Appendix, p. 25
# ---------------------------------------------------------------------------
class Youngs2003GBTestCase(unittest.TestCase):
    """Tests for Youngs2003PrimarySR_GB."""

    def setUp(self):
        self.model = Youngs2003PrimarySR_GB()

    # --- Golden-truth regression ---
    # Values computed with scipy.special.expit using (a=-16.02, b=2.685)
    # from Youngs et al. (2003), Appendix, p. 25.

    def test_golden_truth(self):
        mags = np.array([5.0, 5.5, 6.0, 6.5, 7.0, 7.5])
        expected = np.array([
            6.9460905900564127e-02, 2.2226767688715679e-01,
            5.2248482479180003e-01, 8.0729054588192506e-01,
            9.4130982500790894e-01, 9.8397578070554537e-01,
        ])
        got = self.model.get_prob(RuptureContext([('mag', mags)]))
        np.testing.assert_allclose(got, expected, rtol=1e-10)


# ---------------------------------------------------------------------------
# northern Basin and Range (nBR)
# Coefficients: a = -18.71, b = 3.041
# Data: 47 earthquakes, Mw 4.9–7.4
# Source: Youngs et al. (2003), Appendix, p. 25
# ---------------------------------------------------------------------------
class Youngs2003nBRTestCase(unittest.TestCase):
    """Tests for Youngs2003PrimarySR_nBR."""

    def setUp(self):
        self.model = Youngs2003PrimarySR_nBR()

    # --- Golden-truth regression ---
    # Values computed with scipy.special.expit using (a=-18.71, b=3.041)
    # from Youngs et al. (2003), Appendix, p. 25.

    def test_golden_truth(self):
        mags = np.array([5.0, 5.5, 6.0, 6.5, 7.0, 7.5])
        expected = np.array([
            2.9170299953100755e-02, 1.2083995215380161e-01,
            3.8603734270860302e-01, 7.4202112282000621e-01,
            9.2936658960231722e-01, 9.8365736029029804e-01,
        ])
        got = self.model.get_prob(RuptureContext([('mag', mags)]))
        np.testing.assert_allclose(got, expected, rtol=1e-10)