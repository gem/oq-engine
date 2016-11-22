# The Hazard Library
# Copyright (C) 2012-2016 GEM Foundation
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
import unittest
import numpy

import openquake.hazardlib
from openquake.hazardlib import const
from openquake.hazardlib.geo import Point
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.filters import RtreeFilter


class HazardCurvesFiltersTestCase(unittest.TestCase):
    def test_point_sources(self):
        sources = [
            openquake.hazardlib.source.PointSource(
                source_id='point1', name='point1',
                tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
                mfd=openquake.hazardlib.mfd.EvenlyDiscretizedMFD(
                    min_mag=4, bin_width=1, occurrence_rates=[5]
                ),
                nodal_plane_distribution=openquake.hazardlib.pmf.PMF([
                    (1, openquake.hazardlib.geo.NodalPlane(strike=0.0,
                                                           dip=90.0,
                                                           rake=0.0))
                ]),
                hypocenter_distribution=openquake.hazardlib.pmf.PMF([(1, 10)]),
                upper_seismogenic_depth=0.0,
                lower_seismogenic_depth=10.0,
                magnitude_scaling_relationship=
                openquake.hazardlib.scalerel.PeerMSR(),
                rupture_aspect_ratio=2,
                temporal_occurrence_model=PoissonTOM(1.),
                rupture_mesh_spacing=1.0,
                location=Point(10, 10)
            ),
            openquake.hazardlib.source.PointSource(
                source_id='point2', name='point2',
                tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
                mfd=openquake.hazardlib.mfd.EvenlyDiscretizedMFD(
                    min_mag=4, bin_width=2, occurrence_rates=[5, 6, 7]
                ),
                nodal_plane_distribution=openquake.hazardlib.pmf.PMF([
                    (1, openquake.hazardlib.geo.NodalPlane(strike=0,
                                                           dip=90,
                                                           rake=0.0)),
                ]),
                hypocenter_distribution=openquake.hazardlib.pmf.PMF([(1, 10)]),
                upper_seismogenic_depth=0.0,
                lower_seismogenic_depth=10.0,
                magnitude_scaling_relationship=
                openquake.hazardlib.scalerel.PeerMSR(),
                rupture_aspect_ratio=2,
                temporal_occurrence_model=PoissonTOM(1.),
                rupture_mesh_spacing=1.0,
                location=Point(10, 11)
            ),
        ]
        sites = [openquake.hazardlib.site.Site(Point(11, 10), 1, True, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 16), 2, True, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 10.6), 3, True, 2, 3),
                 openquake.hazardlib.site.Site(Point(10, 10.7), 4, True, 2, 3)]
        sitecol = openquake.hazardlib.site.SiteCollection(sites)

        from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 1
        imts = {'PGA': [0.1, 0.5, 1.3]}
        s_filter = RtreeFilter(sitecol, {const.TRT.ACTIVE_SHALLOW_CRUST: 30})
        result = calc_hazard_curves(
            sources, s_filter, imts, gsims, truncation_level)['PGA']
        # there are two sources and four sites. The first source contains only
        # one rupture, the second source contains three ruptures.
        #
        # the first source has 'maximum projection radius' of 0.707 km
        # the second source has 'maximum projection radius' of 500.0 km
        #
        # the epicentral distances for source 1 are: [ 109.50558394,
        # 667.16955987,   66.71695599,   77.83644865]
        # the epicentral distances for source 2 are: [ 155.9412148 ,
        # 555.97463322,   44.47797066,   33.35847799]
        #
        # Considering that the source site filtering distance is set to 30 km,
        # for source 1, all sites have epicentral distance larger than
        # 0.707 + 30 km. This means that source 1 ('point 1') is not considered
        # in the calculation because too far.
        # for source 2, the 1st, 3rd and 4th sites have epicentral distances
        # smaller than 500.0 + 30 km. This means that source 2 ('point 2') is
        # considered in the calculation for site 1, 3, and 4.
        #
        # JB distances for rupture 1 in source 2 are: [ 155.43860273,
        #  555.26752644,   43.77086388,   32.65137121]
        # JB distances for rupture 2 in source 2 are: [ 150.98882575,
        #  548.90356541,   37.40690285,   26.28741018]
        # JB distances for rupture 3 in source 2 are: [ 109.50545819,
        # 55.97463322,    0.        ,    0.        ]
        #
        # Considering that the rupture site filtering distance is set to 30 km,
        # rupture 1 (magnitude 4) is not considered because too far, rupture 2
        # (magnitude 6) affect only the 4th site, rupture 3 (magnitude 8)
        # affect the 3rd and 4th sites.

        self.assertEqual(result.shape, (4, 3))  # 4 sites, 3 levels
        numpy.testing.assert_allclose(result[0], 0)  # no contrib to site 1
        numpy.testing.assert_allclose(result[1], 0)  # no contrib to site 2
