# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
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

import numpy as np
import unittest

from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib import const
from openquake.hazardlib.gsim.atkinson_boore_2006 import AtkinsonBoore2006
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.const import TRT, IMC
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import (
    NRCan15SiteTerm, NRCan15SiteTermLinear)


class NRCan15SiteTermTestCase(unittest.TestCase):

    def ctx(self, nsites, vs30):
        sites = Dummy.get_site_collection(nsites, vs30=vs30)
        rup = Dummy.get_rupture(mag=6.0)
        ctx = RuptureContext()
        vars(ctx).update(vars(rup))
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        return ctx

    def test_instantiation(self):
        mgmpe = NRCan15SiteTerm(gmpe_name='BooreEtAl2014')

        # Check the assigned IMTs
        expected = {PGA, SA, PGV}
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES == expected,
                        msg='The assigned IMTs are incorrect')
        # Check the TR
        expected = TRT.ACTIVE_SHALLOW_CRUST
        self.assertTrue(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE == expected,
                        msg='The assigned TRT is incorrect')
        # Check the IM component
        expected = IMC.RotD50
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT ==
                        expected, msg='The IM component is wrong')
        # Check the required distances
        expected = {'rjb'}
        self.assertTrue(mgmpe.REQUIRES_DISTANCES == expected,
                        msg='The assigned distance types are wrong')

    def test_gm_calculation_soilBC(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='AtkinsonBoore2006')
        ctx = self.ctx(4, 760.)
        ctx.rrup = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = AtkinsonBoore2006()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, imt, stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationAB06_hard_bedrock(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='AtkinsonBoore2006')
        ctx = self.ctx(4, 1999.)
        ctx.rrup = np.array([10., 20., 30., 40.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = AtkinsonBoore2006()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, imt, stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationAB06(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='AtkinsonBoore2006')
        ctx = self.ctx(4, [1000., 1500., 1000., 1500.])
        ctx.rrup = np.array([10., 10., 40., 40.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = AtkinsonBoore2006()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, imt, stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationBA08(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='BooreAtkinson2008')
        # Set parameters
        ctx = self.ctx(4, vs30=400.)
        ctx.rjb = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationBA08_1site(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='BooreAtkinson2008')
        # Set parameters
        ctx = self.ctx(1, vs30=400.)
        ctx.rjb = np.array([10])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationBA08_vs30variable(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='BooreAtkinson2008')
        # Set parameters
        ctx = self.ctx(3, vs30=[400., 600, 1000])
        ctx.rjb = np.array([10., 10., 10.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean[:-1], mean_expected[:-1])
        np.testing.assert_almost_equal(stds[:-1], stds_expected[:-1])

    def test_raise_error(self):
        with self.assertRaises(AttributeError):
            NRCan15SiteTerm(gmpe_name='FukushimaTanaka1990')

    def test_set_vs30_attribute(self):
        mgmpe = NRCan15SiteTerm(gmpe_name='Campbell2003SHARE')
        msg = '{:s} does not have vs30 in the required site parameters'
        self.assertTrue('vs30' in mgmpe.REQUIRES_SITES_PARAMETERS, msg=msg)

    def test_instantiation(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreEtAl2014')
        #
        # Check the assigned IMTs
        expected = set([PGA, SA, PGV])
        self.assertEqual(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES, expected)

        # Check the TR
        expected = TRT.ACTIVE_SHALLOW_CRUST
        self.assertEqual(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE, expected)

        # Check the IM component
        expected = IMC.RotD50
        self.assertEqual(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT,
                         expected)

        # Check the required distances
        expected = set(['rjb'])
        self.assertEqual(mgmpe.REQUIRES_DISTANCES, expected)

    def test_gm_calculation_soilBC(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTermLinear(gmpe_name='AtkinsonBoore2006')
        # Set parameters
        ctx = self.ctx(4, vs30=760.)
        ctx.rrup = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = AtkinsonBoore2006()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculation_hard_rock(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTermLinear(gmpe_name='AtkinsonBoore2006')
        # Set parameters
        ctx = self.ctx(2, vs30=[760, 2010])
        ctx.rrup = np.array([15., 15.])
        ctx.mag = 7.0
        stdt = [const.StdDev.TOTAL]
        gmpe = AtkinsonBoore2006()

        for imt in [PGA(), SA(1.0), SA(5.0)]:
            # Computes results
            mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt,
                                                    stdt)
            # Compute the expected results
            mean_expected, stds_expected = gmpe.get_mean_and_stddevs(
                ctx,  ctx, ctx, imt, stdt)
            # Test that for reference soil conditions the modified GMPE gives
            # the same results of the original gmpe
            np.testing.assert_allclose(np.exp(mean), np.exp(mean_expected),
                                       rtol=1.0e-1)
            np.testing.assert_allclose(stds, stds_expected)

    def test_gm_calculationBA08(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreAtkinson2008')
        # Set parameters
        ctx = self.ctx(4, vs30=400.)
        ctx.rjb = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationBA08_1site(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreAtkinson2008')
        ctx = self.ctx(1, vs30=400.)
        ctx.rjb = np.array([10])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculationBA08_vs30variable(self):
        # Modified gmpe
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreAtkinson2008')
        ctx = self.ctx(3, vs30=[400., 600, 1000])
        ctx.rjb = np.array([10., 10., 10.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(ctx, ctx,
                                                                 ctx, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean[:-1], mean_expected[:-1])
        np.testing.assert_almost_equal(stds[:-1], stds_expected[:-1])

    def test_raise_error(self):
        with self.assertRaises(AttributeError):
            NRCan15SiteTermLinear(gmpe_name='FukushimaTanaka1990')

    def test_set_vs30_attribute(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='Campbell2003SHARE')
        msg = '{:s} does not have vs30 in the required site parameters'
        self.assertTrue('vs30' in mgmpe.REQUIRES_SITES_PARAMETERS, msg=msg)
