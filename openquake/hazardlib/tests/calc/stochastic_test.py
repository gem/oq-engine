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
from openquake.hazardlib import nrml, calc
from openquake.hazardlib.calc.stochastic import (
    stochastic_event_set, sample_ruptures)
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter

aae = numpy.testing.assert_almost_equal


class StochasticEventSetTestCase(unittest.TestCase):

    def test_nankai(self):
        # source model for the Nankai region provided by M. Pagani
        source_model = os.path.join(os.path.dirname(__file__), 'nankai.xml')
        # it has a single group containing 15 mutex sources
        [group] = nrml.to_python(source_model)
        for i, src in enumerate(group):
            src.id = i
        aae([src.mutex_weight for src in group],
            [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
             0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
        param = dict(ses_per_logic_tree_path=10, ses_seed=42,
                     gsims=[SiMidorikawa1999SInter()])
        sf = calc.filters.SourceFilter(None, {})
        dic = sum(sample_ruptures(group, sf, param), {})
        self.assertEqual(len(dic['rup_array']), 7)
        self.assertEqual(len(dic['calc_times']), 15)  # mutex sources

        # test no filtering 1
        ruptures = list(stochastic_event_set(group))
        self.assertEqual(len(ruptures), 19)

        # test no filtering 2
        ruptures = sum(sample_ruptures(group, sf, param), {})['rup_array']
        self.assertEqual(len(ruptures), 7)
