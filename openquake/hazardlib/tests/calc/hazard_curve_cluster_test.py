# The Hazard Library
# Copyright (C) 2016-2018 GEM Foundation
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

import os
import unittest

from openquake.hazardlib import nrml
from openquake.hazardlib.const import TRT
from openquake.hazardlib.geo import Point
from openquake.baselib.general import DictArray
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.calc.hazard_curve import classical


DATA = os.path.join(os.path.dirname(__file__), '../source_model')


class HazardCurvesTestCase01(unittest.TestCase):

    def setUp(self):
        testfile = os.path.join(DATA, 'source_group_cluster.xml')
        sc = SourceConverter(area_source_discretization=10.)
        self.sg = nrml.to_python(testfile, sc)
        self.imtls = DictArray({'PGA': [0.01, 0.1, 0.3]})
        gsim = SadighEtAl1997()
        self.gsim_by_trt = {TRT.ACTIVE_SHALLOW_CRUST: gsim}
        site = Site(Point(0.0, 0.0), 800, z1pt0=30., z2pt5=1.)
        s_filter = SourceFilter(SiteCollection([site]), {})
        self.sites = s_filter

    def test_hazard_curve_X(self):
        # Test the former calculator
        print(self.sg[0].cluster)
        curves = calc_hazard_curves(self.sg,
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = curves[0][0]
        self.assertAlmostEqual(0.3, crv[0])
