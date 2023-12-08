# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy as np
from openquake.hazardlib.imt import PGA, AvgSA
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib import gsim, imt, const
from openquake.hazardlib.gsim.mgmpe.generic_gmpe_avgsa import (
    GenericGmpeAvgSA, GmpeIndirectAvgSA)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class GenericGmpeAvgSATestCase(unittest.TestCase):
    """
    Testing instantiation and usage of the GenericGmpeAvgSA class
    """

    def test_calculation_Akkar_valueerror(self):
        # Testing not supported periods
        avg_periods = [0.05, 0.15, 1.0, 2.0, 4.1]
        with self.assertRaises(ValueError) as ve:
            gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
                gmpe_name='AkkarEtAlRepi2014',
                avg_periods=avg_periods,
                corr_func='akkar')
        self.assertEqual(str(ve.exception),
                         "'avg_periods' contains values outside of the range "
                         "supported by the Akkar et al. (2014) correlation "
                         "model")


class GenericGMPEAvgSaTablesTestCaseAkkar(BaseGSIMTestCase):
    """
    Conventional GMPE test case for Akkar correlation table
    """
    GSIM_CLASS = GenericGmpeAvgSA

    def test_all(self):
        self.check(
            'generic_avgsa/GENERIC_GMPE_AVGSA_AKKAR_MEAN.csv',
            'generic_avgsa/GENERIC_GMPE_AVGSA_AKKAR_TOTAL_STDDEV.csv',
            max_discrep_percentage=0.1,
            gmpe_name="BooreAtkinson2008",
            avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
            corr_func="akkar")


class GenericGMPEAvgSaTablesTestCaseBakerJayaram(BaseGSIMTestCase):
    """
    Conventional GMPE test case for Baker & Jayaram correlation model
    """
    GSIM_CLASS = GenericGmpeAvgSA

    def test_all(self):
        self.check(
            'generic_avgsa/GENERIC_GMPE_AVGSA_BAKER_JAYARAM_MEAN.csv',
            'generic_avgsa/GENERIC_GMPE_AVGSA_BAKER_JAYARAM_TOTAL_STDDEV.csv',
            max_discrep_percentage=0.1,
            gmpe_name="BooreAtkinson2008",
            avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
            corr_func="baker_jayaram")


class GmpeIndirectAvgSAGeneralTestCase(unittest.TestCase):
    """General test case for the GmpeIndirectAvgSA, specifically verifying
    that it produces identical outputs to the GenericGmpeAvgSA when the
    configurations should match
    """

    def setUp(self):
        # Build a realistic context object
        rjbs = np.arange(0.0, 250.0, 50.0)
        n_r = len(rjbs)
        mags = np.hstack([m * np.ones(n_r) for m in [4.5, 6.0, 7.5]])
        self.n = len(mags)
        rjbs = np.tile(rjbs, [1, 3]).flatten()

        ctx_dtypes = [
            ("sids", int),
            ("mag", float),
            ("rake", float),
            ("rjb", float),
            ("vs30", float),

        ]

        self.ctx = np.recarray(self.n, dtype=ctx_dtypes)
        self.ctx["sids"] = np.arange(self.n)
        self.ctx["mag"] = mags
        self.ctx["rake"] = 0.0
        self.ctx["rjb"] = rjbs.copy()
        self.ctx["vs30"] = 800.0

    def test_generic_gmpe_equivalence(self):
        # Test that under comparable configurations the GmpeAvgSa gives
        # the same values as the GenericGmpeAvgSA
        t0 = 1.0
        periods_t0 = np.linspace(0.2 * t0, 1.5 * t0, 10)
        # Configure the generic GMPE for AvgSA conditioned on the above periods
        original_model = GenericGmpeAvgSA(gmpe_name="BindiEtAl2014Rjb",
                                          corr_func="baker_jayaram",
                                          avg_periods=periods_t0)

        new_model = GmpeIndirectAvgSA(gmpe_name="BindiEtAl2014Rjb",
                                      corr_func="baker_jayaram",
                                      t_low=0.2, t_high=1.5, n_per=10)

        # Call the generic model with a scalar AvgSA
        mean_orig = np.zeros([1, self.n])
        sigma_orig = np.zeros_like(mean_orig)
        tau_orig = np.zeros_like(mean_orig)
        phi_orig = np.zeros_like(mean_orig)
        original_model.compute(self.ctx, [AvgSA()], mean_orig,
                               sigma_orig, tau_orig, phi_orig)

        # Call the new model with a vector AvgSA
        mean_new = np.zeros([1, self.n])
        sigma_new = np.zeros_like(mean_new)
        tau_new = np.zeros_like(mean_new)
        phi_new = np.zeros_like(mean_new)
        new_model.compute(self.ctx, [AvgSA(t0)], mean_new,
                          sigma_new, tau_new, phi_new)

        # Verify the outputs are equal
        np.testing.assert_array_almost_equal(mean_orig, mean_new)
        np.testing.assert_array_almost_equal(sigma_orig, sigma_new)


class GmpeIndirectAvgSATestCase(BaseGSIMTestCase):
    """
    Conventional OpenQuake test case for the GmpeAvgSA class, covering two
    different correlation models and cases when the maximum number of periods
    is exceeded ("long") or not ("short")
    """
    GSIM_CLASS = GmpeIndirectAvgSA

    def test_eshm20_correlation_model_long(self):
        self.check('generic_avgsa/gmpe_avgsa_mean_eshm20_long.csv',
                   'generic_avgsa/gmpe_avgsa_total_stddev_eshm20_long.csv',
                   max_discrep_percentage=0.01,
                   gmpe_name="KothaEtAl2020ESHM20",
                   corr_func="eshm20",
                   t_low=0.2, t_high=1.5, n_per=10)

    def test_eshm20_correlation_model_short(self):
        self.check('generic_avgsa/gmpe_avgsa_mean_eshm20_short.csv',
                   'generic_avgsa/gmpe_avgsa_total_stddev_eshm20_short.csv',
                   max_discrep_percentage=0.01,
                   gmpe_name="KothaEtAl2020ESHM20",
                   corr_func="eshm20",
                   t_low=0.2, t_high=1.5, n_per=10)

    def test_bj08_correlation_model_long(self):
        self.check('generic_avgsa/gmpe_avgsa_mean_bj08_long.csv',
                   'generic_avgsa/gmpe_avgsa_total_stddev_bj08_long.csv',
                   max_discrep_percentage=0.01,
                   gmpe_name="KothaEtAl2020ESHM20",
                   corr_func="baker_jayaram",
                   t_low=0.2, t_high=1.5, n_per=10)
