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

import numpy as np
import unittest

from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy, new_ctx
from openquake.hazardlib.contexts import full_context, simple_cmaker
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.const import TRT, IMC, StdDev

from openquake.hazardlib.gsim.mgmpe.cy14_site_term import CY14SiteTerm
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014

aae = np.testing.assert_almost_equal


class CY14SiteTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        mgmpe = CY14SiteTerm(gmpe_name='ChiouYoungs2014')
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
        # Check the required distances
        expected = set(['rrup', 'rjb', 'rx'])
        self.assertTrue(mgmpe.REQUIRES_DISTANCES == expected,
                        msg='The assigned distance types are wrong')

    def test_all(self):
        # Test that for reference soil conditions the modified GMPE gives the
        # same results of the original gmpe
        gmpe = ChiouYoungs2014()
        mgmpe = CY14SiteTerm(gmpe_name='ChiouYoungs2014')

        cmaker = simple_cmaker([gmpe, mgmpe], ['PGA', 'SA(1.0)'])
        ctx = new_ctx(cmaker, 4)
        ctx.dip = 90.
        ctx.z1pt0 = 0.
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rx = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        ctx.vs30 = 1130.
        ctx.vs30measured = 1
        mea, sig, _, _ = cmaker.get_mean_stds([ctx])
        aae(mea[0], mea[1])
        aae(sig[0], sig[1])

        # Test that for reference soil conditions the modified GMPE gives
        # similar results to the original gmpe
        ctx.vs30 = 760.
        mea, sig, _, _ = cmaker.get_mean_stds([ctx])
        aae(mea[0], mea[1], decimal=7)
        aae(sig[0], sig[1], decimal=2)

        # Test that for reference soil conditions the modified GMPE gives the
        # similar results as the original gmpe
        ctx.vs30 = 400.
        mea, sig, _, _ = cmaker.get_mean_stds([ctx])
        aae(mea[0], mea[1], decimal=7)
        # Here we use a quite large tolerance since in the site term we take
        # the std from the calculation of motion on reference rock. This
        # does not match the std that the same GMM computes for soft soils
        # with the same remaining conditions
        aae(sig[0], sig[1], decimal=1)

    def test_raise_error(self):
        self.assertRaises(ValueError, CY14SiteTerm, 'AbrahamsonEtAl2014')
