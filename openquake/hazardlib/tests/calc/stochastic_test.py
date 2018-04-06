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
import os
import unittest
import numpy
from openquake.hazardlib import nrml, geo
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.stochastic import (
    stochastic_event_set, sample_ruptures)
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter

aae = numpy.testing.assert_almost_equal


class StochasticEventSetTestCase(unittest.TestCase):
    class FakeRupture(object):
        def __init__(self, occurrences):
            self.occurrences = occurrences

        def sample_number_of_occurrences(self):
            return self.occurrences

    class FakeSource(object):
        def __init__(self, source_id, ruptures):
            self.source_id = source_id
            self.ruptures = ruptures

        def iter_ruptures(self):
            return iter(self.ruptures)

    class FailSource(FakeSource):
        def iter_ruptures(self):
            raise ValueError('Something bad happened')

    def setUp(self):
        self.time_span = 15
        self.r1_1 = self.FakeRupture(1)
        self.r1_0 = self.FakeRupture(0)
        self.r1_2 = self.FakeRupture(2)
        self.r2_1 = self.FakeRupture(1)
        self.source1 = self.FakeSource(
            1, [self.r1_1, self.r1_0, self.r1_2])
        self.source2 = self.FakeSource(
            2, [self.r2_1])

    def test_no_filter(self):
        ses = list(
            stochastic_event_set(
                [self.source1, self.source2]
            ))
        self.assertEqual(ses, [self.r1_1, self.r1_2, self.r1_2, self.r2_1])

    def test(self):
        ses = list(stochastic_event_set(
            [self.source1, self.source2]))
        self.assertEqual(ses, [self.r1_1, self.r1_2, self.r1_2, self.r2_1])

    def test_source_errors(self):
        # exercise the case where an error occurs while computing on a given
        # seismic source; in this case, we expect an error to be raised which
        # signals the id of the source in question
        fail_source = self.FailSource(2, [self.r2_1])
        with self.assertRaises(ValueError) as ae:
            list(stochastic_event_set([self.source1, fail_source]))

        expected_error = (
            'An error occurred with source id=2. Error: Something bad happened'
        )
        self.assertEqual(expected_error, str(ae.exception))

    def test_source_errors_with_sites(self):
        # exercise the case where an error occurs while computing on a given
        # seismic source; in this case, we expect an error to be raised which
        # signals the id of the source in question
        fail_source = self.FailSource(2, [self.r2_1])
        fake_sites = [1, 2, 3]
        with self.assertRaises(ValueError) as ae:
            list(stochastic_event_set([self.source1, fail_source],
                                      sites=fake_sites))

        expected_error = (
            'An error occurred with source id=2. Error: Something bad happened'
        )
        self.assertEqual(expected_error, str(ae.exception))

    def test_nankai(self):
        # source model for the Nankai region provided by M. Pagani
        source_model = os.path.join(os.path.dirname(__file__), 'nankai.xml')
        # it has a single group containing 15 mutex sources
        [group] = nrml.to_python(source_model)
        aae(group.srcs_weights,
            [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
             0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
        rup_serial = numpy.arange(group.tot_ruptures, dtype=numpy.uint32)
        start = 0
        for i, src in enumerate(group):
            src.id = i
            nr = src.num_ruptures
            src.serial = rup_serial[start:start + nr]
            start += nr
        group.samples = 1
        lonlat = 135.68, 35.68
        site = Site(geo.Point(*lonlat), 800, True, z1pt0=100., z2pt5=1.)
        s_filter = SourceFilter(SiteCollection([site]), {})
        param = dict(ses_per_logic_tree_path=10, seed=42)
        gsims = [SiMidorikawa1999SInter()]
        dic = sample_ruptures(group, s_filter, gsims, param)
        self.assertEqual(dic['num_ruptures'], 19)  # total ruptures
        self.assertEqual(dic['num_events'], 16)
        self.assertEqual(len(dic['eb_ruptures']), 8)
        self.assertEqual(len(dic['calc_times']), 15)  # mutex sources

        # test export
        mesh = numpy.array([lonlat], [('lon', float), ('lat', float)])
        ebr = dic['eb_ruptures'][0]
        ebr.export(mesh)
