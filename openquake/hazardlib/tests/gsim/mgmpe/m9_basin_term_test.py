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

from openquake.hazardlib.tests.gsim.mgmpe.dummy import new_ctx
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.const import TRT, IMC
from openquake.hazardlib.gsim.mgmpe.m9_basin_term import M9BasinTerm
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import ModifiableGMPE
from openquake.hazardlib.gsim.kuehn_2020 import KuehnEtAl2020SInter

aae = np.testing.assert_almost_equal


class M9BasinTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        mgmpe = M9BasinTerm(gmpe_name='KuehnEtAl2020SInter')

        # Check the assigned IMTs
        expected = set([PGA, SA, PGV])
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES == expected,
                        msg='The assigned IMTs are incorrect')
        # Check the TR
        expected = TRT.SUBDUCTION_INTERFACE
        self.assertTrue(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE == expected,
                        msg='The assigned TRT is incorrect')
        # Check the IM component
        expected = IMC.RotD50
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT ==
                        expected, msg='The IM component is wrong')
        # Check the required distances
        expected = {'rrup'}
        self.assertTrue(mgmpe.REQUIRES_DISTANCES == expected,
                        msg='The assigned distance types are wrong')
        

    def test_all(self):
        """
        Test that the M9 basin term applied to Kuehn et al. (2020)
        provides the expected values (using sites with z2pt5 above
        and below 6 km threshold and considering SAs with periods
        above and below 1.9 s)
        """
        # Make base GMM
        gmpe = KuehnEtAl2020SInter()
        
        # Make GMM with basin term using the mgmpe class directly
        mgmpe_cls = M9BasinTerm(gmpe_name='KuehnEtAl2020SInter')
        
        # Make GMM with basin term using ModifiableGMPE and kwargs
        kwargs = {'gmpe': {'KuehnEtAl2020SInter': {}},
                  'm9_basin_term': {}}
        mgmpe_kws = ModifiableGMPE(**kwargs)

        # Make the ctx
        cmaker = simple_cmaker([gmpe, mgmpe_cls, mgmpe_kws],
                               ['PGA', 'SA(1.0)', 'SA(2.0)'])
                               
        ctx = new_ctx(cmaker, 6)
        ctx.dip = 60.
        ctx.rake = 90.
        ctx.z1pt0 = np.array([522.32, 516.98, 522.32, 516.98, 522.32])
        ctx.z2pt5 = np.array([6.32, 3.53, 6.32, 3.53, 6.32])
        ctx.rrup = np.array([1., 10., 30., 70., 200., 500.])
        ctx.vs30 = 1100.
        ctx.vs30measured = 1
        mea, sig, _, _ = cmaker.get_mean_stds([ctx])
        aae(mea[0], mea[1])
        aae(sig[0], sig[1])