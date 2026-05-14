# -*- coding: utf-8 -*-
"""
GEM-style verification tests for the Bayless and Somerville (2024) GMM.

Reference values in the CSV files were computed from the Fortran reference
subroutine bs24_gmm.f (provided by Jeff Bayless, jeff.bayless@aecom.com),
not from the Python implementation itself. This ensures the test data is
truly independent of the code being tested.

Agreement between Fortran and Python: max difference 0.000045 ln units on
mean SA, 0.000005 ln units on sigma, across 14,256 test cases.

Place the CSV files at:
    openquake/hazardlib/tests/gsim/data/BS24/BS24_CRATONIC.csv
    openquake/hazardlib/tests/gsim/data/BS24/BS24_NONCRATONIC.csv

Author: Thuany Costa de Lima, Geoscience Australia (May 2026)
"""
import unittest

from openquake.hazardlib.gsim.bayless_somerville_2024 import (
    BaylessSomerville2024Cratonic,
    BaylessSomerville2024NonCratonic,
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BaylessSomerville2024CratonicTestCase(BaseGSIMTestCase):
    """
    Verification tests for the Cratonic version of BS24.
    Applicable to Yilgarn, Gawler, Pilbara, Kimberley, and Northern
    Australian Cratons (NSHA23 Precambrian classification).
    """
    GSIM_CLASS = BaylessSomerville2024Cratonic

    def test_mean(self):
        self.check('BS24/BS24_CRATONIC.csv', max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('BS24/BS24_CRATONIC.csv', max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('BS24/BS24_CRATONIC.csv', max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('BS24/BS24_CRATONIC.csv', max_discrep_percentage=0.1)


class BaylessSomerville2024NonCratonicTestCase(BaseGSIMTestCase):
    """
    Verification tests for the NonCratonic version of BS24.
    Applicable to Eastern Australian Phanerozoic Accretionary Terranes,
    extended and oceanic crust (NSHA23 Phanerozoic classification).
    """
    GSIM_CLASS = BaylessSomerville2024NonCratonic

    def test_mean(self):
        self.check('BS24/BS24_NONCRATONIC.csv', max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('BS24/BS24_NONCRATONIC.csv', max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('BS24/BS24_NONCRATONIC.csv', max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('BS24/BS24_NONCRATONIC.csv', max_discrep_percentage=0.1)


if __name__ == '__main__':
    unittest.main()
