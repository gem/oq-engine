# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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
import numpy
import pathlib
import unittest
from openquake.hazardlib import nrml, contexts
from openquake.hazardlib.calc.stochastic import (
    stochastic_event_set, sample_ruptures)
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter

aae = numpy.testing.assert_almost_equal
HERE = pathlib.Path(__file__)


class StochasticEventSetTestCase(unittest.TestCase):

    def test_nankai(self):
        raise unittest.SkipTest("Not working yet")

        # source model for the Nankai region provided by M. Pagani
        source_model = HERE.parent / 'nankai.xml'
        # it has a single group containing 15 mutex sources
        [group] = nrml.to_python(source_model)
        for i, src in enumerate(group):
            src.id = i
            src.grp_id = 0
        aae([src.mutex_weight for src in group],
            [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
             0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
        param = dict(ses_per_logic_tree_path=10, ses_seed=42, imtls={})
        cmaker = contexts.ContextMaker('*', [SiMidorikawa1999SInter()], param)
        dic = sum(sample_ruptures(group, cmaker), {})
        self.assertEqual(len(dic['rup_array']), 8)
        self.assertEqual(len(dic['source_data']), 6)  # mutex sources

        # test no filtering 1
        ruptures = list(stochastic_event_set(group))
        self.assertEqual(len(ruptures), 19)

        # test no filtering 2
        ruptures = sum(sample_ruptures(group, cmaker), {})['rup_array']
        self.assertEqual(len(ruptures), 8)

    def test_nankai_grp_prob(self):
        raise unittest.SkipTest("Not working yet")

        fname = HERE.parent / 'data' / 'stochastic' / 'ssm.xml'
        [group] = nrml.to_python(fname)
        for i, src in enumerate(group):
            src.id = i
            src.grp_id = 0
        param = dict(ses_per_logic_tree_path=10, ses_seed=42, imtls={})
        cmaker = contexts.ContextMaker('*', [SiMidorikawa1999SInter()], param)
        ruptures = sum(sample_ruptures(group, cmaker), {})['rup_array']
