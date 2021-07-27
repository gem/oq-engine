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

import pathlib
import unittest
import numpy as np

from openquake.hazardlib.imt import PGA
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib import gsim, imt, const
from openquake.hazardlib.gsim.mgmpe.generic_gmpe_avgsa import GenericGmpeAvgSA
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

data = pathlib.Path(__file__).parent / 'data'


class GenericGmpeAvgSATestCase(unittest.TestCase):
    """
    Testing instantiation and usage of the  GenericGmpeAvgSA class
    """

    def ctx(self, nsites, vs30):
        sites = Dummy.get_site_collection(nsites, vs30=vs30)
        rup = Dummy.get_rupture(mag=6.0)
        ctx = RuptureContext()
        ctx.sid = np.arange(nsites)
        vars(ctx).update(vars(rup))
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        return ctx

    def test01(self):
        avg_periods = [0.05, 0.15, 1.0, 2.0, 4.0]
        gmm = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='ZhaoEtAl2006Asc',
            avg_periods=avg_periods,
            corr_func='akkar')
        msg = 'The class name is incorrect'
        self.assertTrue(gmm.__class__.__name__ == 'GenericGmpeAvgSA', msg=msg)

        ctx = self.ctx(4, vs30=760.)
        ctx.hypo_depth = 10.
        ctx.rrup = np.array([1., 10., 30., 70.])
        imtype = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, _ = gmm.get_mean_and_stddevs(ctx, ctx, ctx, imtype, stdt)
        expected = np.array([-1.33735637, -2.62649473, -3.64500654,
                             -4.60067093])
        np.testing.assert_almost_equal(mean, expected)

    def test02(self):
        avg_periods = [0.05, 0.15, 1.0, 2.0, 4.0]
        gmm = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='AkkarEtAlRepi2014',
            avg_periods=avg_periods,
            corr_func='akkar')
        msg = 'The class name is incorrect'
        self.assertTrue(gmm.__class__.__name__ == 'GenericGmpeAvgSA', msg=msg)

        ctx = self.ctx(4, vs30=760.)
        ctx.repi = np.array([1., 10., 30., 70.])
        imtype = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, _ = gmm.get_mean_and_stddevs(ctx, ctx, ctx, imtype, stdt)
        expected = np.array([-2.0383581, -2.6548699, -3.767237, -4.7775653])
        np.testing.assert_almost_equal(mean, expected)

    def test_calculation_addition_args(self):
        avg_periods = [0.05, 0.15, 1.0, 2.0, 4.0]
        gmm = GenericGmpeAvgSA(gmpe_name="KothaEtAl2020ESHM20",
                               avg_periods=avg_periods,
                               corr_func="akkar", sigma_mu_epsilon=1.0)

        ctx = self.ctx(4, vs30=500.)
        ctx.hypo_depth = 15.
        ctx.rjb = np.array([1., 10., 30., 70.])
        ctx.vs30measured = np.ones(4, dtype="bool")
        ctx.region = np.zeros(4, dtype=int)
        stdt = [const.StdDev.TOTAL]
        expected_mean = np.array([-1.72305707, -2.2178751,
                                  -3.20100306, -4.19948242])
        expected_stddev = np.array([0.5532021, 0.5532021,
                                    0.5532021, 0.5532021])
        imtype = imt.AvgSA()
        mean, [stddev] = gmm.get_mean_and_stddevs(
            ctx, ctx, ctx, imtype, stdt)
        np.testing.assert_almost_equal(mean, expected_mean)
        np.testing.assert_almost_equal(stddev, expected_stddev)

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

    def test_calculation_akkar(self, avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0]):

        DATA_FILE = data/'GENERIC_GMPE_AVGSA_MEAN_STD_TOTAL_AKKAR.csv'

        # Initialise meta-GMPE
        mgmpe = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='BooreAtkinson2008',
            avg_periods=avg_periods,
            corr_func='akkar')

        ctx = gsim.base.RuptureContext()
        ctx.sids = [0]
        P = imt.AvgSA
        S = [const.StdDev.TOTAL]

        with open(DATA_FILE, 'r') as f:

            # Skip header
            for i in [1, 2, 3]:
                f.readline()

            for line in f:
                arr = np.float_(line.strip().split(','))

                # Setting ground motion attributes
                ctx.mag = arr[0]
                ctx.rjb = np.array([arr[1]])
                ctx.rake = arr[2]
                ctx.hypo_depth = arr[3]
                ctx.vs30 = np.array([arr[4]])

                # Compute ground motion
                mean, stdv = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, P, S)
                np.testing.assert_almost_equal(mean, arr[6])
                np.testing.assert_almost_equal(stdv, arr[7])

    def test_calculation_Baker_Jayaram(self):

        DATA_FILE = data/'GENERIC_GMPE_AVGSA_MEAN_STD_TOTAL_BAKER_JAYARAM.csv'

        # Initialise meta-GMPE
        mgmpe = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='BooreAtkinson2008',
            avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
            corr_func='baker_jayaram')

        ctx = RuptureContext()
        ctx.sids = [0]
        P = imt.AvgSA
        S = [const.StdDev.TOTAL]

        with open(DATA_FILE, 'r') as f:

            # Skip header
            for i in [1, 2, 3]:
                f.readline()

            for line in f:
                arr = np.float_(line.strip().split(','))

                # Setting ground motion attributes
                ctx.mag = arr[0]
                ctx.rjb = np.array([arr[1]])
                ctx.rake = arr[2]
                ctx.hypo_depth = arr[3]
                ctx.vs30 = np.array([arr[4]])

                # Compute ground motion
                mean, stdv = mgmpe.get_mean_and_stddevs(ctx, ctx, ctx, P, S)
                np.testing.assert_almost_equal(mean, arr[6])
                np.testing.assert_almost_equal(stdv, arr[7])


class GenericGMPEAvgSaTablesTestCaseAkkar(BaseGSIMTestCase):
    """
    Conventional GMPE test case for Akkar correlation table
    """
    GSIM_CLASS = GenericGmpeAvgSA

    def test_mean(self):
        self.check('generic_avgsa/GENERIC_GMPE_AVGSA_AKKAR_MEAN.csv',
                   max_discrep_percentage=0.1,
                   gmpe_name="BooreAtkinson2008",
                   avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
                   corr_func="akkar")

    def test_std_total(self):
        self.check('generic_avgsa/GENERIC_GMPE_AVGSA_AKKAR_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1,
                   gmpe_name="BooreAtkinson2008",
                   avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
                   corr_func="akkar")


class GenericGMPEAvgSaTablesTestCaseBakerJayaram(BaseGSIMTestCase):
    """
    Conventional GMPE test case for Baker & Jayaram correlation model
    """
    GSIM_CLASS = GenericGmpeAvgSA

    def test_mean(self):
        self.check('generic_avgsa/GENERIC_GMPE_AVGSA_BAKER_JAYARAM_MEAN.csv',
                   max_discrep_percentage=0.1,
                   gmpe_name="BooreAtkinson2008",
                   avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
                   corr_func="baker_jayaram")

    def test_std_total(self):
        self.check('generic_avgsa/'
                   'GENERIC_GMPE_AVGSA_BAKER_JAYARAM_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.1,
                   gmpe_name="BooreAtkinson2008",
                   avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
                   corr_func="baker_jayaram")
