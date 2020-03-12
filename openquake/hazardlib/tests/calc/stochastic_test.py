# The Hazard Library
# Copyright (C) 2012-2020 GEM Foundation
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
from openquake.hazardlib.calc.filters import IntegrationDistance
from openquake.hazardlib.geo import Point
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib import nrml, calc
from openquake.hazardlib.calc.stochastic import (
    stochastic_event_set, sample_ruptures, sample_cluster)
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter

aae = numpy.testing.assert_almost_equal


class StochasticEventSetTestCase(unittest.TestCase):

    def test_nankai(self):
        # source model for the Nankai region provided by M. Pagani
        path = os.path.join(os.path.dirname(__file__), 'data')
        fname = os.path.join(path, 'nankai.xml')
        # it has a single group containing 15 mutex sources
        [group] = nrml.to_python(fname)
        aae([src.mutex_weight for src in group],
            [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
             0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
        seed = 42
        start = 0
        for i, src in enumerate(group):
            src.id = i
            nr = src.num_ruptures
            src.serial = start + seed
            start += nr
        param = dict(ses_per_logic_tree_path=10, filter_distance='rjb',
                     gsims=[SiMidorikawa1999SInter()])
        sf = calc.filters.SourceFilter(None, {})
        dic = sum(sample_ruptures(group, sf, param), {})
        self.assertEqual(len(dic['rup_array']), 6)
        self.assertEqual(len(dic['calc_times']), 15)  # mutex sources

        # test no filtering 1
        ruptures = list(stochastic_event_set(group))
        self.assertEqual(len(ruptures), 19)

        # test no filtering 2
        ruptures = sum(sample_ruptures(group, sf, param), {})['rup_array']
        self.assertEqual(len(ruptures), 6)


class SampleClusterTestCase(unittest.TestCase):

    def test_cluster_mutex(self):

        path = os.path.join(os.path.dirname(__file__), 'data', )
        fname = os.path.join(path, 'cluster_with_mutex_sources.xml')
        [group] = nrml.to_python(fname)
        #
        idis = IntegrationDistance({'default': 400})
        scol = SiteCollection([Site(Point(0., 0.))])
        sf = calc.filters.SourceFilter(scol, idis)
        # Create list of parameters
        param = dict(ses_per_logic_tree_path=1,
                     filter_distance='rjb',
                     gsims=[SiMidorikawa1999SInter()])
        seed = 1
        start = 0
        for i, src in enumerate(group):
            src.id = i
            nr = src.num_ruptures
            src.serial = start + seed
            start += nr
        # Counting the number of occuurences of the three ruptures admitted
        # by this test model
        rups, tme = sample_cluster(group, sf, num_ses=1000, param=param)
        nocc = sum([r.n_occ for r in rups])
        # The number of occurrences must be close to 10 since the occurrence
        # rate of the cluster is 0.01 events/year
        assert nocc == 9
