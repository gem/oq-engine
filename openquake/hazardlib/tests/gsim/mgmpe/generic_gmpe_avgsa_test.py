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

from openquake.hazardlib import gsim, imt, const
import numpy as np
import unittest


class GenericGmpeAvgSATestCase(unittest.TestCase):

    def test_calculation_Akkar(self, avg_periods="0.05,0.15,1.0,2.0,4.0"):

        DATA_FILE = 'Data/GENERIC_GMPE_AVGSA_MEAN_STD_TOTAL_AKKAR.csv'

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
                data = np.float_(line.strip().split(','))

                # Setting ground motion attributes
                setattr(rctx, 'mag', data[0])
                setattr(dctx, 'rjb', np.array([data[1]]))
                setattr(rctx, 'rake', data[2])
                setattr(rctx, 'hypo_depth', data[3])
                setattr(sctx, 'vs30', np.array([data[4]]))

                # Compute ground motion
                mean, stdv = mgmpe.get_mean_and_stddevs(sctx, rctx,
                                                        dctx, P, S)
                np.testing.assert_almost_equal(mean, data[6])
                np.testing.assert_almost_equal(stdv, data[7])

    def test_calculation_Akkar_valueerror(self):

        # Testing not supported periods
        try:
            self.test_calculation_Akkar(
                avg_periods="0.05,0.15,1.0,2.0,4.012345")
        except ValueError:
            pass

    def test_calculation_Baker_Jayaram(self):

        DATA_FILE = 'Data/GENERIC_GMPE_AVGSA_MEAN_STD_TOTAL_BAKER_JAYARAM.csv'

        # Initialise meta-GMPE
        mgmpe = gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
                    gmpe_name='BooreAtkinson2008',
                    avg_periods="0.05,0.15,1.0,2.0,4.0",
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
                data = np.float_(line.strip().split(','))

                # Setting ground motion attributes
                setattr(rctx, 'mag', data[0])
                setattr(dctx, 'rjb', np.array([data[1]]))
                setattr(rctx, 'rake', data[2])
                setattr(rctx, 'hypo_depth', data[3])
                setattr(sctx, 'vs30', np.array([data[4]]))

                # Compute ground motion
                mean, stdv = mgmpe.get_mean_and_stddevs(sctx, rctx, dctx, P, S)
                np.testing.assert_almost_equal(mean, data[6])
                np.testing.assert_almost_equal(stdv, data[7])
