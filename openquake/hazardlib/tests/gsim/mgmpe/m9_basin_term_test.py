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
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.const import TRT, IMC
from openquake.hazardlib.gsim.mgmpe.m9_basin_term import M9BasinTerm

ae = np.testing.assert_equal
aae = np.testing.assert_almost_equal


class M9BasinTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        mgmpe = M9BasinTerm(gmpe_name='KuehnEtAl2020SInter')

        # Check the assigned IMTs
        expected = set([PGA, SA, PGV])
        ae(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES, expected)
        # Check the TR
        expected = TRT.SUBDUCTION_INTERFACE
        ae(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE, expected)
        # Check the IM component
        expected = IMC.RotD50
        ae(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT, expected)
        # Check the required distances
        expected = {'rrup'}
        ae(mgmpe.REQUIRES_DISTANCES, expected)
        

    def test_all(self):
        """
        Test that the M9 basin term applied to Kuehn et al. (2020)
        provides the expected values (using sites with z2pt5 above
        and below 6 km threshold and considering SAs with periods
        above and below 1.9 s)
        """
        k20 = valid.gsim('KuehnEtAl2020SInter')
        
        # Make original GMM
        gmpe = valid.modified_gsim(k20)

        # Make GMM with basin term using the mgmpe class directly
        mgmpe_cls = M9BasinTerm(gmpe_name='KuehnEtAl2020SInter')

        # Make GMM with basin term using ModifiableGMPE and kwargs
        mgmpe_val = valid.modified_gsim(k20, m9_basin_term={})
        
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
        
        # For SA with period less than 2 all means should be
        # the same (amp term only applied for long periods)
        ori_mea_pga = mea[0][0]
        cls_mea_pga = mea[1][0]
        val_mea_pga = mea[2][0]
        ae(ori_mea_pga, cls_mea_pga, val_mea_pga)
        ori_mea_sa1pt0 = mea[0][1]
        cls_mea_sa1pt0 = mea[1][1]
        val_mea_sa1pt0 = mea[2][1]
        ae(ori_mea_sa1pt0, cls_mea_sa1pt0, val_mea_sa1pt0)

        # Check means using m9 term from mgmpe cls and 
        # valid.modifiable_gmpe are the same
        ae(mea[1], mea[2])

        # For SA(2.0) basin amplification should be added
        ori_sa2pt0 = mea[0][2]
        cls_sa2pt0 = mea[1][2]
        val_sa2pt0 = mea[2][2]
        exp_diff = np.array([np.log(2.0), 0., np.log(2.0)]) # Site 1 intensities
        for idx_v, v in enumerate(exp_diff):                # note be changed
            diff_cls = cls_sa2pt0[idx_v] - ori_sa2pt0[idx_v]
            diff_val = val_sa2pt0[idx_v] - ori_sa2pt0[idx_v]
            aae(diff_cls, exp_diff[idx_v])
            aae(diff_val, exp_diff[idx_v])