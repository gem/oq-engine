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

from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.stochastic import stochastic_event_set_poissonian


class StochasticEventSetTestCase(unittest.TestCase):
    class FakeRupture(object):
        def __init__(self, occurrences):
            self.occurrences = occurrences
        def sample_number_of_occurrences(self):
            return self.occurrences

    class FakeSource(object):
        def __init__(self, ruptures, time_span):
            self.time_span = time_span
            self.ruptures = ruptures
        def iter_ruptures(self, tom):
            assert tom.time_span is self.time_span
            assert isinstance(tom, PoissonTOM)
            return iter(self.ruptures)

    def test(self):
        time_span = 15
        r1_1 = self.FakeRupture(1)
        r1_0 = self.FakeRupture(0)
        r1_2 = self.FakeRupture(2)
        r2_1 = self.FakeRupture(1)
        source1 = self.FakeSource([r1_1, r1_0, r1_2], time_span)
        source2 = self.FakeSource([r2_1], time_span)
        ses = list(stochastic_event_set_poissonian([source1, source2],
                                                   time_span))
        self.assertEqual(ses, [r1_1, r1_2, r1_2, r2_1])
