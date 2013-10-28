# The Hazard Library
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
from decimal import Decimal

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.source import AreaSource, SimpleFaultSource
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo import NodalPlane
from openquake.hazardlib.scalerel import PeerMSR, PointMSR
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.calc import hazard_curves_poissonian as hazard_curves
from openquake.hazardlib.tom import PoissonTOM

from tests.acceptance import _peer_test_data as test_data


def assert_hazard_curve_is(testcase, actual, expected, atol, rtol):
    actual, expected = numpy.array(actual), numpy.array(expected)
    testcase.assertTrue(numpy.allclose(actual, expected, atol=atol, rtol=rtol),
                        "%s != %s" % (actual, expected))

class Set1TestCase(unittest.TestCase):
    def test_case_10(self):
        hypocenter_pmf = PMF([(1, test_data.SET1_CASE10_HYPOCENTER_DEPTH)])
        sources = [AreaSource(source_id='area', name='area',
            tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=test_data.SET1_CASE10_MFD,
            nodal_plane_distribution=PMF([(1, NodalPlane(0.0, 90.0, 0.0))]),
            hypocenter_distribution=hypocenter_pmf,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship = PointMSR(),
            rupture_aspect_ratio=test_data.SET1_RUPTURE_ASPECT_RATIO,
            polygon=test_data.SET1_CASE10_SOURCE_POLYGON,
            area_discretization=10.0,
            rupture_mesh_spacing=10.0,
            temporal_occurrence_model=PoissonTOM(1.)
        )]
        sites = SiteCollection([
            test_data.SET1_CASE10_SITE1, test_data.SET1_CASE10_SITE2,
            test_data.SET1_CASE10_SITE3, test_data.SET1_CASE10_SITE4
        ])
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 0
        time_span = 1.0
        imts = {test_data.IMT: test_data.SET1_CASE10_IMLS}

        curves = hazard_curves(sources, sites, imts, time_span,
                               gsims, truncation_level)
        s1hc, s2hc, s3hc, s4hc = curves[test_data.IMT]

        assert_hazard_curve_is(self, s1hc, test_data.SET1_CASE10_SITE1_POES,
                               atol=1e-4, rtol=1e-1)
        assert_hazard_curve_is(self, s2hc, test_data.SET1_CASE10_SITE2_POES,
                               atol=1e-4, rtol=1e-1)
        assert_hazard_curve_is(self, s3hc, test_data.SET1_CASE10_SITE3_POES,
                               atol=1e-4, rtol=1e-1)
        assert_hazard_curve_is(self, s4hc, test_data.SET1_CASE10_SITE4_POES,
                               atol=1e-4, rtol=1e-1)

    def test_case_11(self):
        hypocenter_probability = (
            Decimal(1) / len(test_data.SET1_CASE11_HYPOCENTERS)
        )
        hypocenter_pmf = PMF([
            (hypocenter_probability, hypocenter)
            for hypocenter in test_data.SET1_CASE11_HYPOCENTERS
        ])
        # apart from hypocenter pmf repeats case 10
        sources = [AreaSource(source_id='area', name='area',
            tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=test_data.SET1_CASE11_MFD,
            nodal_plane_distribution=PMF([(1, NodalPlane(0.0, 90.0, 0.0))]),
            hypocenter_distribution=hypocenter_pmf,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship = PointMSR(),
            rupture_aspect_ratio=test_data.SET1_RUPTURE_ASPECT_RATIO,
            polygon=test_data.SET1_CASE11_SOURCE_POLYGON,
            area_discretization=10.0,
            rupture_mesh_spacing=10.0,
            temporal_occurrence_model=PoissonTOM(1.)
        )]
        sites = SiteCollection([
            test_data.SET1_CASE11_SITE1, test_data.SET1_CASE11_SITE2,
            test_data.SET1_CASE11_SITE3, test_data.SET1_CASE11_SITE4
        ])
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 0
        time_span = 1.0
        imts = {test_data.IMT: test_data.SET1_CASE11_IMLS}

        curves = hazard_curves(sources, sites, imts, time_span,
                               gsims, truncation_level)
        s1hc, s2hc, s3hc, s4hc = curves[test_data.IMT]

        assert_hazard_curve_is(self, s1hc, test_data.SET1_CASE11_SITE1_POES,
                               atol=1e-4, rtol=1e-1)
        assert_hazard_curve_is(self, s2hc, test_data.SET1_CASE11_SITE2_POES,
                               atol=1e-4, rtol=1e-1)
        assert_hazard_curve_is(self, s3hc, test_data.SET1_CASE11_SITE3_POES,
                               atol=1e-4, rtol=1e-1)
        assert_hazard_curve_is(self, s4hc, test_data.SET1_CASE11_SITE4_POES,
                               atol=1e-4, rtol=1e-1)

    def test_case_2(self):
        sources = [SimpleFaultSource(source_id='fault1', name='fault1',
            tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=test_data.SET1_CASE2_MFD,
            rupture_mesh_spacing=1.0,
            magnitude_scaling_relationship=PeerMSR(),
            rupture_aspect_ratio=test_data.SET1_RUPTURE_ASPECT_RATIO,
            upper_seismogenic_depth=test_data.SET1_CASE1TO9_UPPER_SEISMOGENIC_DEPTH,
            lower_seismogenic_depth=test_data.SET1_CASE1TO9_LOWER_SEISMOGENIC_DEPTH,
            fault_trace=test_data.SET1_CASE1TO9_FAULT_TRACE,
            dip=test_data.SET1_CASE1TO9_DIP,
            rake=test_data.SET1_CASE1TO9_RAKE,
            temporal_occurrence_model=PoissonTOM(1.)
        )]
        sites = SiteCollection([
            test_data.SET1_CASE1TO9_SITE1, test_data.SET1_CASE1TO9_SITE2,
            test_data.SET1_CASE1TO9_SITE3, test_data.SET1_CASE1TO9_SITE4,
            test_data.SET1_CASE1TO9_SITE5, test_data.SET1_CASE1TO9_SITE6,
            test_data.SET1_CASE1TO9_SITE7
        ])
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 0
        time_span = 1.0
        imts = {test_data.IMT: test_data.SET1_CASE2_IMLS}

        curves = hazard_curves(sources, sites, imts, time_span,
                               gsims, truncation_level)
        s1hc, s2hc, s3hc, s4hc, s5hc, s6hc, s7hc = curves[test_data.IMT]

        assert_hazard_curve_is(self, s1hc, test_data.SET1_CASE2_SITE1_POES,
                               atol=3e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s2hc, test_data.SET1_CASE2_SITE2_POES,
                               atol=2e-5, rtol=1e-5)
        assert_hazard_curve_is(self, s3hc, test_data.SET1_CASE2_SITE3_POES,
                               atol=2e-5, rtol=1e-5)
        assert_hazard_curve_is(self, s4hc, test_data.SET1_CASE2_SITE4_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s5hc, test_data.SET1_CASE2_SITE5_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s6hc, test_data.SET1_CASE2_SITE6_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s7hc, test_data.SET1_CASE2_SITE7_POES,
                               atol=2e-5, rtol=1e-5)

    def test_case_5(self):
        # only mfd differs from case 2
        sources = [SimpleFaultSource(source_id='fault1', name='fault1',
            tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
            mfd=test_data.SET1_CASE5_MFD,
            rupture_mesh_spacing=1.0,
            magnitude_scaling_relationship=PeerMSR(),
            rupture_aspect_ratio=test_data.SET1_RUPTURE_ASPECT_RATIO,
            upper_seismogenic_depth=test_data.SET1_CASE1TO9_UPPER_SEISMOGENIC_DEPTH,
            lower_seismogenic_depth=test_data.SET1_CASE1TO9_LOWER_SEISMOGENIC_DEPTH,
            fault_trace=test_data.SET1_CASE1TO9_FAULT_TRACE,
            dip=test_data.SET1_CASE1TO9_DIP,
            rake=test_data.SET1_CASE1TO9_RAKE,
            temporal_occurrence_model=PoissonTOM(1.)
        )]
        sites = SiteCollection([
            test_data.SET1_CASE1TO9_SITE1, test_data.SET1_CASE1TO9_SITE2,
            test_data.SET1_CASE1TO9_SITE3, test_data.SET1_CASE1TO9_SITE4,
            test_data.SET1_CASE1TO9_SITE5, test_data.SET1_CASE1TO9_SITE6,
            test_data.SET1_CASE1TO9_SITE7
        ])
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 0
        time_span = 1.0
        imts = {test_data.IMT: test_data.SET1_CASE5_IMLS}

        curves = hazard_curves(sources, sites, imts, time_span,
                               gsims, truncation_level)
        s1hc, s2hc, s3hc, s4hc, s5hc, s6hc, s7hc = curves[test_data.IMT]

        assert_hazard_curve_is(self, s1hc, test_data.SET1_CASE5_SITE1_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s2hc, test_data.SET1_CASE5_SITE2_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s3hc, test_data.SET1_CASE5_SITE3_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s4hc, test_data.SET1_CASE5_SITE4_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s5hc, test_data.SET1_CASE5_SITE5_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s6hc, test_data.SET1_CASE5_SITE6_POES,
                               atol=1e-3, rtol=1e-5)
        assert_hazard_curve_is(self, s7hc, test_data.SET1_CASE5_SITE7_POES,
                               atol=1e-3, rtol=1e-5)
