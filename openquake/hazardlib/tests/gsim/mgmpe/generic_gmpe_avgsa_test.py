# The Hazard Library
# Copyright (C) 2012-2019 GEM Foundation
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
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib import gsim, imt, const
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy

data = pathlib.Path(__file__).parent / 'data'


class GenericGmpeAvgSATestCase(unittest.TestCase):
    """
    Testing instantiation and usage of the  GenericGmpeAvgSA class
    """

    def test01(self):
        avg_periods = [0.05, 0.15, 1.0, 2.0, 4.0]
        gmm = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='ZhaoEtAl2006Asc',
            avg_periods=avg_periods,
            corr_func='akkar')
        msg = 'The class name is incorrect'
        self.assertTrue(gmm.__class__.__name__ == 'GenericGmpeAvgSA', msg=msg)

        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        rup.hypo_depth = 10.
        dists = DistancesContext()
        dists.rrup = np.array([1., 10., 30., 70.])
        imtype = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, _ = gmm.get_mean_and_stddevs(sites, rup, dists, imtype, stdt)
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

        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        dists = DistancesContext()
        dists.repi = np.array([1., 10., 30., 70.])
        imtype = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, _ = gmm.get_mean_and_stddevs(sites, rup, dists, imtype, stdt)
        expected = np.array([-2.0383581, -2.6548699, -3.767237 , -4.7775653])
        np.testing.assert_almost_equal(mean, expected)

    def test_calculation_akkar(self, avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0]):

        DATA_FILE = data/'GENERIC_GMPE_AVGSA_MEAN_STD_TOTAL_AKKAR.csv'

        # Initialise meta-GMPE
        mgmpe = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='BooreAtkinson2008',
            avg_periods=avg_periods,
            corr_func='akkar')

        sctx = gsim.base.SitesContext()
        rctx = gsim.base.RuptureContext()
        dctx = gsim.base.DistancesContext()

        P = imt.AvgSA
        S = [const.StdDev.TOTAL]

        with open(DATA_FILE, 'r') as f:

            # Skip header
            for i in [1, 2, 3]:
                f.readline()

            for line in f:
                arr = np.float_(line.strip().split(','))

                # Setting ground motion attributes
                setattr(rctx, 'mag', arr[0])
                setattr(dctx, 'rjb', np.array([arr[1]]))
                setattr(rctx, 'rake', arr[2])
                setattr(rctx, 'hypo_depth', arr[3])
                setattr(sctx, 'vs30', np.array([arr[4]]))

                # Compute ground motion
                mean, stdv = mgmpe.get_mean_and_stddevs(sctx, rctx,
                                                        dctx, P, S)
                np.testing.assert_almost_equal(mean, arr[6])
                np.testing.assert_almost_equal(stdv, arr[7])

    def test_calculation_Akkar_valueerror(self):

        # Testing not supported periods
        try:
            self.test_calculation_akkar(
                avg_periods=[0.05, 0.15, 1.0, 2.0, 4.012345])
        except ValueError:
            pass

    def test_calculation_Baker_Jayaram(self):

        DATA_FILE = data/'GENERIC_GMPE_AVGSA_MEAN_STD_TOTAL_BAKER_JAYARAM.csv'

        # Initialise meta-GMPE
        mgmpe = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
            gmpe_name='BooreAtkinson2008',
            avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
            corr_func='baker_jayaram')

        sctx = gsim.base.SitesContext()
        rctx = gsim.base.RuptureContext()
        dctx = gsim.base.DistancesContext()

        P = imt.AvgSA
        S = [const.StdDev.TOTAL]

        with open(DATA_FILE, 'r') as f:

            # Skip header
            for i in [1, 2, 3]:
                f.readline()

            for line in f:
                arr = np.float_(line.strip().split(','))

                # Setting ground motion attributes
                setattr(rctx, 'mag', arr[0])
                setattr(dctx, 'rjb', np.array([arr[1]]))
                setattr(rctx, 'rake', arr[2])
                setattr(rctx, 'hypo_depth', arr[3])
                setattr(sctx, 'vs30', np.array([arr[4]]))

                # Compute ground motion
                mean, stdv = mgmpe.get_mean_and_stddevs(sctx, rctx, dctx, P, S)
                np.testing.assert_almost_equal(mean, arr[6])
                np.testing.assert_almost_equal(stdv, arr[7])
