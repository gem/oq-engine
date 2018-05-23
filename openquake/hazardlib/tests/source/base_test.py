# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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

from openquake.hazardlib import const
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo import Polygon, Point
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.tom import PoissonTOM


class FakeSource(ParametricSeismicSource):
    MODIFICATIONS = set(())
    iter_ruptures = None
    count_ruptures = None


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
        super().setUp()
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
