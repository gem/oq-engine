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
from openquake.hazardlib.gsim.mgmpe.ba08_site_term import BA08SiteTerm

aae = np.testing.assert_almost_equal


exp_gmm_origin = np.array([[ 2.95002695,  2.95002695,  2.95002695,  2.95002695],
                           [ 3.48372038,  3.48372038,  3.48372038,  3.48372038],
                           [-0.00382746, -0.00382746, -0.00382746, -0.00382746]])

exp_with_ba08 = np.array([[3.05906356, 3.15177686, 3.21616174, 3.23047657],
                           [3.53086955, 3.61696047, 3.67674643, 3.69003877],
                           [0.44547026, 0.44547026, 0.44547026, 0.44547026]])


class BA08SiteTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        mgmpe = BA08SiteTerm(gmpe_name='BooreAtkinson2008')

        # Check the assigned IMTs
        expected = set([PGA, SA, PGV])
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES == expected,
                        msg='The assigned IMTs are incorrect')
        # Check the TR
        expected = TRT.ACTIVE_SHALLOW_CRUST
        self.assertTrue(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE == expected,
                        msg='The assigned TRT is incorrect')
        # Check the IM component
        expected = IMC.GMRotI50
        self.assertTrue(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT ==
                        expected, msg='The IM component is wrong')
        # Check the required distances
        expected = {'rjb'}
        self.assertTrue(mgmpe.REQUIRES_DISTANCES == expected,
                        msg='The assigned distance type is wrong')

    def test_all(self):
        """
        Check that the BA08 site term applied to reference conditions
        obtaines the same values as the original GMM.

        Also check that the BA08 ModifiableGMPE class applied to the
        Aktinson and Macias (2009) GMM obtains the expected values.
        """
        # Check 1: Application of BA08 for reference conditions
        # to the BA08 GMM is the same as the original GMM class
        ba08 = valid.gsim('BooreAtkinson2008')
        gmpe = valid.modified_gsim(ba08)
        mgmpe = BA08SiteTerm(gmpe_name='BooreAtkinson2008')

        cmaker = simple_cmaker(
            [gmpe, mgmpe], ['PGA', 'SA(0.1)', 'SA(1.0)'])
        ctx = new_ctx(cmaker, 4)
        ctx.dip = 90.
        ctx.rake = 60.
        ctx.rjb = np.array([1., 10., 30., 70.])
        ctx.vs30 = 760. # BA08 reference velocity
        ctx.vs30measured = 1
        mea, sig, _, _ = cmaker.get_mean_stds([ctx]) # imtls on bedrock
        
        aae(mea[0], mea[1])
        aae(sig[0], sig[1])

        # Check 2: Expected values for non-reference condition
        # using the Atkinson and Macias (2009) GMM
        am09 = valid.gsim('AtkinsonMacias2009')
        gmpe = valid.modified_gsim(am09)
        # Instantiate from mgmpe class + from regular mgmpe
        mgmpe2 = BA08SiteTerm(gmpe_name='AtkinsonMacias2009')
        mgmpe1 = valid.modified_gsim(am09, ba08_site_term={})

        ctx.vs30 = 400.
        cmaker = simple_cmaker(
            [gmpe, mgmpe1, mgmpe2], ['PGA', 'SA(0.1)', 'SA(1.0)'])
        mea, sig, _, _ = cmaker.get_mean_stds([ctx]) # imtls on soil

        aae(mea[0], exp_gmm_origin) # Check expected is observed
        aae(mea[1], exp_with_ba08)  # (original vs modified with
        aae(mea[2], exp_with_ba08)  # with site term)