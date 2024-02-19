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
from openquake.hazardlib.gsim.atkinson_boore_2006 import AtkinsonBoore2006
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.const import TRT, IMC
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import (
    NRCan15SiteTerm, NRCan15SiteTermLinear)


def check(n, mgmpe, imt='PGA', gmpe=AtkinsonBoore2006(), slc=slice(None),
          atol=0., **kw):
    # Test that for reference soil conditions the modified GMPE gives the
    # same results of the original gmpe

    cmaker = simple_cmaker([gmpe, mgmpe], [imt])
    ctx = new_ctx(cmaker, n)
    for k, v in kw.items():
        setattr(ctx, k, v)
    mea, std, _, _ = cmaker.get_mean_stds([ctx])  # shape (G=2, M=1, N=n)
    np.testing.assert_allclose(mea[0, 0, slc], mea[1, 0, slc], atol=atol)
    np.testing.assert_allclose(std[0, 0, slc], std[1, 0, slc], atol=atol)


class NRCan15SiteTermTestCase(unittest.TestCase):

    def test_instantiation(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreEtAl2014')

        # Check the assigned IMTs
        expected = {PGA, SA, PGV}
        self.assertEqual(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES, expected)

        # Check the TR
        expected = TRT.ACTIVE_SHALLOW_CRUST
        self.assertEqual(mgmpe.DEFINED_FOR_TECTONIC_REGION_TYPE, expected)

        # Check the IM component
        expected = IMC.RotD50
        self.assertEqual(mgmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT,
                         expected)

        # Check the required distances
        expected = {'rjb'}
        self.assertEqual(mgmpe.REQUIRES_DISTANCES, expected)

    def test_gm_calculationAB06_hard_bedrock(self):
        mgmpe = NRCan15SiteTerm(gmpe_name='AtkinsonBoore2006')
        check(4, mgmpe, vs30=1999, rrup=[10., 20., 30., 40.])

    def test_gm_calculationAB06(self):
        mgmpe = NRCan15SiteTerm(gmpe_name='AtkinsonBoore2006')
        check(4, mgmpe, vs30=[1000., 1500., 1000., 1500.],
              rrup=[10., 10., 40., 40.])

    def test_gm_calculation_soilBC(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='AtkinsonBoore2006')
        check(4, mgmpe, vs30=760, rrup=[1., 10., 30., 70.])

    def test_gm_calculation_hard_rock(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='AtkinsonBoore2006')
        for imt in ['PGA', 'SA(1.0)', 'SA(5.0)']:
            check(2, mgmpe, atol=.1, vs30=[760, 2010], rrup=[15, 15], mag=7)

    def test_gm_calculationBA08(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreAtkinson2008')
        check(4, mgmpe, gmpe=BooreAtkinson2008(), vs30=400,
              rjb=[1, 10, 30, 70], rrup=[1, 10, 30, 70])

    def test_gm_calculationBA08_1site(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreAtkinson2008')
        check(1, mgmpe, gmpe=BooreAtkinson2008(), vs30=400, rjb=10, rrup=10)

    def test_gm_calculationBA08_vs30variable(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='BooreAtkinson2008')
        check(3, mgmpe, gmpe=BooreAtkinson2008(), slc=slice(0, -1),
              vs30=[400., 600, 1000], rjb=[10, 10, 10], rrup=[10, 10, 10])

    def test_raise_error(self):
        with self.assertRaises(AttributeError):
            NRCan15SiteTermLinear(gmpe_name='FukushimaTanaka1990')

    def test_set_vs30_attribute(self):
        mgmpe = NRCan15SiteTermLinear(gmpe_name='Campbell2003SHARE')
        msg = '{:s} does not have vs30 in the required site parameters'
        self.assertTrue('vs30' in mgmpe.REQUIRES_SITES_PARAMETERS, msg=msg)
