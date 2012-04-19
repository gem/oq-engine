# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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
"""
Tests are based on report "PEER 2010/106 - Verification of Probabilistic
Seismic Hazard Analysis Computer Programs" by  Patricia Thomas, Ivan Wong,
Norman Abrahamson, see
`http://peer.berkeley.edu/publications/peer_reports/reports_2010/web_PEER_10106_THOMASetal.pdf`_.
"""
import unittest

import numpy

from nhlib import const
from nhlib.source import AreaSource
from nhlib.pmf import PMF
from nhlib.geo import NodalPlane
from nhlib.scalerel import PeerMSR
from nhlib.gsim.sadigh_1997 import SadighEtAl1997
from nhlib.calc import hazard_curves

from tests.acceptance import _peer_test_data as test_data


def assert_hazard_curve_is(testcase, actual, expected, tolerance):
    actual, expected = numpy.array(actual), numpy.array(expected)
    testcase.assertTrue(numpy.allclose(actual, expected, atol=tolerance),
                        "%s != %s" % (actual, expected))

class Set1TestCase(unittest.TestCase):
    def test_case_10(self):
        hypocenter_pmf = PMF([(1, test_data.SET1_CASE10_HYPOCENTER_DEPTH)])
        sources = [AreaSource(source_id='src1', name='src1',
            tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=test_data.SET1_CASE10_MFD,
            nodal_plane_distribution=PMF([(1, NodalPlane(0.0, 90.0, 0.0))]),
            hypocenter_distribution=hypocenter_pmf,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship = PeerMSR(),
            rupture_aspect_ratio=1.0,
            polygon=test_data.SET1_CASE10_SOURCE_POLYGON,
            area_discretization=30.0,
            rupture_mesh_spacing=10.0
        )]
        sites = [
            test_data.SET1_CASE10_SITE1, test_data.SET1_CASE10_SITE2,
            test_data.SET1_CASE10_SITE3, test_data.SET1_CASE10_SITE4
        ]
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        component_type = const.IMC.AVERAGE_HORIZONTAL
        truncation_level = 0
        time_span = 1.0
        imts = {test_data.IMT: test_data.SET1_CASE10_IMLS}

        curves = hazard_curves(sources, sites, imts, time_span,
                               gsims, component_type, truncation_level)
        s1hc, s2hc, s3hc, s4hc = curves[test_data.IMT]

        assert_hazard_curve_is(self, s1hc, test_data.SET1_CASE10_SITE1_POES,
                               tolerance=2e-3)
        assert_hazard_curve_is(self, s2hc, test_data.SET1_CASE10_SITE2_POES,
                               tolerance=2e-3)
        assert_hazard_curve_is(self, s3hc, test_data.SET1_CASE10_SITE3_POES,
                               tolerance=2e-3)
        assert_hazard_curve_is(self, s4hc, test_data.SET1_CASE10_SITE4_POES,
                               tolerance=2e-3)
