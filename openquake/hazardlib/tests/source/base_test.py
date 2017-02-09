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

import numpy

from openquake.hazardlib import const
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo import Polygon, Point, RectangularMesh
from openquake.hazardlib.calc import filters
from openquake.hazardlib.site import \
    Site, SiteCollection, FilteredSiteCollection
from openquake.hazardlib.tom import PoissonTOM


class FakeSource(ParametricSeismicSource):
    MODIFICATIONS = set(())
    iter_ruptures = None
    count_ruptures = None
    get_rupture_enclosing_polygon = None


class _BaseSeismicSourceTestCase(unittest.TestCase):
    POLYGON = Polygon([Point(0, 0), Point(0, 0.001),
                       Point(0.001, 0.001), Point(0.001, 0)])
    SITES = [
        Site(Point(0.0005, 0.0005, -0.5), 0.1, True, 3, 4),  # inside, middle
        Site(Point(0.0015, 0.0005), 1, True, 3, 4),  # outside, middle-east
        Site(Point(-0.0005, 0.0005), 2, True, 3, 4),  # outside, middle-west
        Site(Point(0.0005, 0.0015), 3, True, 3, 4),  # outside, north-middle
        Site(Point(0.0005, -0.0005), 4, True, 3, 4),  # outside, south-middle
        Site(Point(0., 0.), 5, True, 3, 4),  # south-west corner
        Site(Point(0., 0.001), 6, True, 3, 4),  # north-west corner
        Site(Point(0.001, 0.001), 7, True, 3, 4),  # north-east corner
        Site(Point(0.001, 0.), 8, True, 3, 4),  # south-east corner
        Site(Point(0., -0.01), 9, True, 3, 4),  # 1.1 km away
        Site(Point(0.3, 0.3), 10, True, 3, 4),  # 47 km away
        Site(Point(0., -1), 11, True, 3, 4),  # 111.2 km away
    ]

    def setUp(self):
        self.source_class = FakeSource
        mfd = EvenlyDiscretizedMFD(min_mag=3, bin_width=1,
                                   occurrence_rates=[5, 6, 7])
        self.source = FakeSource('source_id', 'name', const.TRT.VOLCANIC,
                                 mfd=mfd, rupture_mesh_spacing=2,
                                 magnitude_scaling_relationship=PeerMSR(),
                                 rupture_aspect_ratio=1,
                                 temporal_occurrence_model=PoissonTOM(50.))
        self.sitecol = SiteCollection(self.SITES)


class SeismicSourceGetAnnOccRatesTestCase(_BaseSeismicSourceTestCase):
    def setUp(self):
        super(SeismicSourceGetAnnOccRatesTestCase, self).setUp()
        self.source.mfd = EvenlyDiscretizedMFD(min_mag=3, bin_width=1,
                                               occurrence_rates=[5, 0, 7, 0])

    def test_default_filtering(self):
        rates = self.source.get_annual_occurrence_rates()
        self.assertEqual(rates, [(3, 5), (5, 7)])

    def test_none_filtering(self):
        rates = self.source.get_annual_occurrence_rates(min_rate=None)
        self.assertEqual(rates, [(3, 5), (4, 0), (5, 7), (6, 0)])

    def test_positive_filtering(self):
        rates = self.source.get_annual_occurrence_rates(min_rate=5)
        self.assertEqual(rates, [(5, 7)])


class SeismicSourceFilterSitesTestCase(_BaseSeismicSourceTestCase):
    def setUp(self):
        super(SeismicSourceFilterSitesTestCase, self).setUp()

        def get_rup_encl_poly(dilation=0):
            if dilation:
                return self.POLYGON.dilate(dilation)
            else:
                return self.POLYGON
        self.source.get_rupture_enclosing_polygon = get_rup_encl_poly

    def test_source_filter_zero_integration_distance(self):
        filtered = self.source.filter_sites_by_distance_to_source(
            integration_distance=0, sites=self.sitecol
        )
        self.assertIsInstance(filtered, FilteredSiteCollection)
        self.assertEqual(len(filtered), 5)
        numpy.testing.assert_array_equal(filtered.indices, [0, 5, 6, 7, 8])
        numpy.testing.assert_array_equal(filtered.vs30, [0.1, 5, 6, 7, 8])
        numpy.testing.assert_array_equal(filtered.mesh.depths,
                                         [-0.5, 0, 0, 0, 0])

    def test_source_filter_half_km_integration_distance(self):
        filtered = self.source.filter_sites_by_distance_to_source(
            integration_distance=0.5, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices,
                                         [0, 1, 2, 3, 4, 5, 6, 7, 8])

    def test_source_filter_fifty_km_integration_distance(self):
        filtered = self.source.filter_sites_by_distance_to_source(
            integration_distance=50, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices,
                                         [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_source_filter_thousand_km_integration_distance(self):
        filtered = self.source.filter_sites_by_distance_to_source(
            integration_distance=1000, sites=self.sitecol
        )
        self.assertIs(filtered, self.sitecol)  # nothing filtered

    def test_source_filter_filter_all_out(self):
        col = SiteCollection([Site(Point(10, 10), 1, True, 2, 3),
                              Site(Point(11, 12), 2, True, 2, 3),
                              Site(Point(13, 14), 1, True, 2, 3)])
        for int_dist in (0, 1, 10, 100, 1000):
            filtered = self.source.filter_sites_by_distance_to_source(
                integration_distance=int_dist, sites=col
            )
            self.assertIs(filtered, None)  # all filtered


class SeismicSourceFilterSitesByRuptureTestCase(
        _BaseSeismicSourceTestCase):
    def test(self):
        surface_mesh = RectangularMesh(self.POLYGON.lons.reshape((2, 2)),
                                       self.POLYGON.lats.reshape((2, 2)),
                                       depths=None)

        class rupture(object):
            class surface(object):
                @classmethod
                def get_joyner_boore_distance(cls, mesh):
                    return surface_mesh.get_joyner_boore_distance(mesh)

        filtered = filters.filter_sites_by_distance_to_rupture(
            rupture=rupture, integration_distance=1.01, sites=self.sitecol
        )
        numpy.testing.assert_array_equal(filtered.indices,
                                         [0, 1, 2, 3, 4, 5, 6, 7, 8])
        numpy.testing.assert_array_equal(filtered.mesh.depths,
                                         [-0.5, 0, 0, 0, 0, 0, 0, 0, 0])
