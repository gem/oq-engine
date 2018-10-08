# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.const import TRT, IMC
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import NRCan15SiteTerm


class NRCan15SiteTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        """ Tests the instantiation """
        mgmpe = NRCan15SiteTerm(gmpe_name='BooreEtAl2014')
        #
        # Check the assigned IMTs
        expected = set([PGA, SA, PGV])
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
        # Check the standard deviations
        expected = set(['Intra event', 'Total', 'Inter event'])
        self.assertTrue(mgmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES == expected,
                        msg='The standard deviations assigned are wrong')
        # Check the required distances
        expected = set(['rjb'])
        self.assertTrue(mgmpe.REQUIRES_DISTANCES == expected,
                        msg='The assigned distance types are wrong')

    def test_gm_calculation(self):
        """ Test mean and std calculation """
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='AtkinsonBoore2006')
        # Set parameters
        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        dists = DistancesContext()
        dists.rrup = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
        # Compute the expected results
        gmpe = AtkinsonBoore2006()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(sites, rup,
                                                                 dists, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_gm_calculation_amplification(self):
        """ Test mean and std calculation """
        # Modified gmpe
        mgmpe = NRCan15SiteTerm(gmpe_name='BooreAtkinson2008')
        # Set parameters
        sites = Dummy.get_site_collection(4, vs30=400.)
        rup = Dummy.get_rupture(mag=6.0)
        dists = DistancesContext()
        dists.rjb = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = mgmpe.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
        # Compute the expected results
        gmpe = BooreAtkinson2008()
        mean_expected, stds_expected = gmpe.get_mean_and_stddevs(sites, rup,
                                                                 dists, imt,
                                                                 stdt)
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        np.testing.assert_almost_equal(mean, mean_expected)
        np.testing.assert_almost_equal(stds, stds_expected)

    def test_raise_error(self):
        """ Tests that exception is raised """
        with self.assertRaises(AttributeError):
            mgmpe = NRCan15SiteTerm(gmpe_name='FukushimaTanaka1990')
