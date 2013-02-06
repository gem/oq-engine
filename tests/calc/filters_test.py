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
import unittest
from itertools import izip
from types import GeneratorType

from openquake.hazardlib.calc import filters


class SourceSiteDistanceFilterTestCase(unittest.TestCase):
    def test(self):
        class FakeSource(object):
            def __init__(self, integration_distance, sites_mapping):
                self.integration_distance = integration_distance
                self.sites_mapping = sites_mapping
            def filter_sites_by_distance_to_source(self, integration_distance,
                                                   sites):
                assert integration_distance is self.integration_distance
                return self.sites_mapping[sites]
        sites1 = object()
        sites2 = object()
        sites3 = object()
        sources = [FakeSource(123, {sites1: None}),  # all filtered out
                   FakeSource(123, {sites2: sites3}),  # partial filtering
                   FakeSource(123, {sites1: sites1})]  # nothing filtered out
        sites = [sites1, sites2, sites1]
        filter_func = filters.source_site_distance_filter(123)
        filtered = filter_func(izip(sources, sites))
        self.assertIsInstance(filtered, GeneratorType)

        source, sites = next(filtered)
        self.assertIs(source, sources[1])
        self.assertIs(sites, sites3)

        source, sites = next(filtered)
        self.assertIs(source, sources[2])
        self.assertIs(sites, sites1)

        self.assertEqual(list(filtered), [])


class RuptureSiteDistanceFilterTestCase(unittest.TestCase):
    def test(self):
        class FakeRupture(object):
            def __init__(self, integration_distance, sites_mapping):
                self.integration_distance = integration_distance
                self.sites_mapping = sites_mapping
            @property
            def source_typology(self):
                return self
            def filter_sites_by_distance_to_rupture(self, rupture,
                                                    integration_distance,
                                                    sites):
                assert rupture is self
                assert integration_distance is self.integration_distance
                return self.sites_mapping[sites]
        sites1 = object()
        sites2 = object()
        sites3 = object()

        ruptures = [FakeRupture(13, {sites1: None}),  # all filtered out
                    FakeRupture(13, {sites2: sites3}),  # partial filtering
                    FakeRupture(13, {sites1: sites1})]  # nothing filtered out
        sites = [sites1, sites2, sites1]
        filter_func = filters.rupture_site_distance_filter(13)
        filtered = filter_func(izip(ruptures, sites))
        self.assertIsInstance(filtered, GeneratorType)

        source, sites = next(filtered)
        self.assertIs(source, ruptures[1])
        self.assertIs(sites, sites3)

        source, sites = next(filtered)
        self.assertIs(source, ruptures[2])
        self.assertIs(sites, sites1)

        self.assertEqual(list(filtered), [])
