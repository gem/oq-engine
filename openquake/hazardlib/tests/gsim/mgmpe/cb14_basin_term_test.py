# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
from openquake.hazardlib import valid
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.const import TRT, IMC
from openquake.hazardlib.gsim.mgmpe.cb14_basin_term import CB14BasinTerm

ae = np.testing.assert_equal
aae = np.testing.assert_almost_equal

exp_gmm_origin = np.array([[-1.55067862, -3.8245714 , -5.48623229],
                           [-2.25723424, -3.72056054, -5.28051045],
                           [-3.45764676, -4.67077352, -5.84789307]])

exp_with_basin = np.array([[-1.35815033, -3.78220564, -5.293704  ],
                           [-1.86104115, -3.63337845, -4.88431736],
                           [-3.04727152, -4.58047065, -5.43751783]])

class CB14BasinTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        mgmpe = CB14BasinTerm(gmpe_name='AtkinsonMacias2009')

        # Check the assigned IMTs
        expected = set([PGA, SA])
        ae(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES, expected)
        # Check the TR
        expected = TRT.SUBDUCTION_INTERFACE
        ae(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE, expected)
        # Check the IM component
        expected = IMC.RANDOM_HORIZONTAL
        ae(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT, expected)
        # Check the required distances
        expected = {'rrup'}
        ae(mgmpe.REQUIRES_DISTANCES, expected)
        
    def test_all(self):
        """
        Test that the CB14 basin term applied to Atkinson and
        Macias (2009) provides the expected values.
        """
        am09 = valid.gsim('AtkinsonMacias2009')
        
        # Make original GMM
        gmpe = valid.modified_gsim(am09)

        # Make GMM with basin term using the mgmpe class directly
        mgmpe_cls = CB14BasinTerm(gmpe_name='AtkinsonMacias2009')

        # Make GMM with basin term using ModifiableGMPE and kwargs
        mgmpe_val = valid.modified_gsim(am09, cb14_basin_term={})

        # Make the ctx
        imts = ['PGA', 'SA(1.0)', 'SA(2.0)']
        cmaker = simple_cmaker([gmpe, mgmpe_cls, mgmpe_val], imts)                       
        ctx = new_ctx(cmaker, 3)
        ctx.dip = 60.
        ctx.rake = 90.
        ctx.z1pt0 = np.array([522.32, 516.98, 522.32])
        ctx.z2pt5 = np.array([6.32, 3.53, 6.32])
        ctx.rrup = np.array([50., 200., 500.])
        ctx.vs30 = 1100.
        ctx.vs30measured = 1
        mea, _, _, _ = cmaker.get_mean_stds([ctx])

        # Check expected is observed (original vs modified with basin term)
        aae(mea[0], exp_gmm_origin)
        aae(mea[1], exp_with_basin)
        aae(mea[2], exp_with_basin)