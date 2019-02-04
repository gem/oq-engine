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
import numpy as np
import unittest

from openquake.hazardlib import nrml
from openquake.hazardlib.const import TRT
from openquake.hazardlib.geo import Point
from openquake.baselib.general import DictArray
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves


DATA = os.path.join(os.path.dirname(__file__), '../source_model')


class HazardCurvesClusterTestCase01(unittest.TestCase):

    def setUp(self):
        testfile = os.path.join(DATA, 'source_group_cluster.xml')
        sc = SourceConverter(area_source_discretization=10.,
                             investigation_time=1.)
        # This provides a SourceModel
        self.sg = getattr(nrml.to_python(testfile, sc), 'src_groups')
        self.imtls = DictArray({'PGA': [0.01, 0.1, 0.2, 0.3, 1.0]})
        gsim = SadighEtAl1997()
        self.gsim_by_trt = {TRT.ACTIVE_SHALLOW_CRUST: gsim}
        site = Site(Point(1.0, -0.1), 800, z1pt0=30., z2pt5=1.)
        self.sites = SiteCollection([site])

    def test_hazard_curve(self):
        # Classical PSHA with cluster source
        curves = calc_hazard_curves(self.sg,
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = curves[0][0]
        # Expected results computed with a notebook using the original USGS
        # formulation as described in Appendix F of Petersen et al. (2008).
        # The rates of exceedance were converted a posteriori into
        # probabilities.
        rates = np.array([1.00000000e-03, 9.98565030e-04, 8.42605169e-04,
                          4.61559062e-04, 1.10100503e-06])
        expected = 1 - np.exp(-rates)
        np.testing.assert_almost_equal(crv, expected)
