# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
import pickle
import numpy

import openquake.hazardlib
from openquake.hazardlib import const
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.filters import SourceFilter, IntegrationDistance
from openquake.baselib.parallel import Sequential, Processmap
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim import akkar_bommer_2010
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997


class HazardCurvesFiltersTestCase(unittest.TestCase):
    def test_MagnitudeDistance_pickleable(self):
        md = IntegrationDistance(
            dict(default=[(1, 10), (2, 20), (3, 30), (4, 40), (5, 100),
                          (6, 200), (7, 400), (8, 800)]))
        md2 = pickle.loads(pickle.dumps(md))
        self.assertEqual(md.dic, md2.dic)

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
                 openquake.hazardlib.site.Site(
                     Point(10, 10.6, 1), 3, True, 2, 3),
                 openquake.hazardlib.site.Site(
                     Point(10, 10.7, -1), 4, True, 2, 3)]
        sitecol = openquake.hazardlib.site.SiteCollection(sites)
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}
        truncation_level = 1
        imts = {'PGA': [0.1, 0.5, 1.3]}
        s_filter = SourceFilter(sitecol, {const.TRT.ACTIVE_SHALLOW_CRUST: 30})
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

        # test that depths are kept after filtering (sites 3 and 4 remain)
        s_filter = SourceFilter(sitecol, {'default': 100})
        numpy.testing.assert_array_equal(
            s_filter.get_close_sites(sources[0]).depths, ([1, -1]))


# this example originally came from the Hazard Modeler Toolkit
def example_calc(apply):
    sitecol = SiteCollection([
        Site(Point(30.0, 30.0), 760., True, 1.0, 1.0),
        Site(Point(30.25, 30.25), 760., True, 1.0, 1.0),
        Site(Point(30.4, 30.4), 760., True, 1.0, 1.0)])
    mfd_1 = TruncatedGRMFD(4.5, 8.0, 0.1, 4.0, 1.0)
    mfd_2 = TruncatedGRMFD(4.5, 7.5, 0.1, 3.5, 1.1)
    sources = [PointSource('001', 'Point1', 'Active Shallow Crust',
                           mfd_1, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                           0.0, 30.0, Point(30.0, 30.5),
                           PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                           PMF([(1.0, 10.0)])),
               PointSource('002', 'Point2', 'Active Shallow Crust',
                           mfd_2, 1.0, WC1994(), 1.0, PoissonTOM(50.0),
                           0.0, 30.0, Point(30.0, 30.5),
                           PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                           PMF([(1.0, 10.0)]))]
    imtls = {'PGA': [0.01, 0.1, 0.2, 0.5, 0.8],
             'SA(0.5)': [0.01, 0.1, 0.2, 0.5, 0.8]}
    gsims = {'Active Shallow Crust': akkar_bommer_2010.AkkarBommer2010()}
    return calc_hazard_curves(sources, sitecol, imtls, gsims, apply=apply)


class HazardCurvesParallelTestCase(unittest.TestCase):
    def test_same_curves_as_sequential(self):
        curves_par = example_calc(Processmap.apply)  # use multiprocessing
        curves_seq = example_calc(Sequential.apply)  # sequential computation
        for name in curves_par.dtype.names:
            numpy.testing.assert_almost_equal(
                curves_seq[name], curves_par[name])
