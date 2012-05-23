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
import unittest

from nhlib import const
from nhlib.mfd import EvenlyDiscretizedMFD
from nhlib.scalerel.peer import PeerMSR
from nhlib.source.base import SeismicSource


class _BaseSeismicSourceTestCase(unittest.TestCase):
    def setUp(self):
        class FakeSource(SeismicSource):
            iter_ruptures = None
            get_rupture_enclosing_polygon = None
        self.source_class = FakeSource
        mfd = EvenlyDiscretizedMFD(min_mag=3, bin_width=1,
                                   occurrence_rates=[5, 6, 7])
        self.source = FakeSource('source_id', 'name', const.TRT.VOLCANIC,
                                 mfd=mfd, rupture_mesh_spacing=2,
                                 magnitude_scaling_relationship=PeerMSR(),
                                 rupture_aspect_ratio=1)


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
