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
import mock
import pickle
import unittest

from types import GeneratorType

from openquake.hazardlib.calc import filters


def assert_pickleable(obj):
    assert (pickle.loads(pickle.dumps(obj)).integration_distance ==
            obj.integration_distance)


class SourceSiteDistanceFilterTestCase(unittest.TestCase):
    def test(self):
        assert_pickleable(filters.source_site_distance_filter(100))

        class FakeSource(object):
            def __init__(self, integration_distance, sites_mapping):
                self.integration_distance = integration_distance
                self.sites_mapping = sites_mapping

            def filter_sites_by_distance_to_source(
                    self, integration_distance, sites):
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
        filtered = filter_func(zip(sources, sites))
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
        assert_pickleable(filters.rupture_site_distance_filter(100))

        def fake_filter(rupture, integration_distance, sites):
            if rupture == 1:
                return None  # all filtered out
            elif rupture == 2:  # partial filtering
                return sites3  # nothing filtered out
            elif rupture == 3:
                return sites1

        sites1 = object()
        sites2 = object()
        sites3 = object()
        sites = [sites1, sites2, sites1]
        ruptures = [1, 2, 3]
        with mock.patch('openquake.hazardlib.calc.filters.'
                        'filter_sites_by_distance_to_rupture', fake_filter):
            filter_func = filters.rupture_site_distance_filter(13)
            filtered = filter_func(zip(ruptures, sites))
            self.assertIsInstance(filtered, GeneratorType)

            rupt, sites = next(filtered)
            self.assertIs(rupt, ruptures[1])
            self.assertIs(sites, sites3)

            rupt, sites = next(filtered)
            self.assertIs(rupt, ruptures[2])
            self.assertIs(sites, sites1)

            self.assertEqual(list(filtered), [])
