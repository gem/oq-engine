#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2019, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy
from openquake.hazardlib.probability_map import ProbabilityMap


class ProbabilityMapTestCase(unittest.TestCase):
    def test(self):
        pmap1 = ProbabilityMap.build(3, 1, sids=[0, 1, 2])
        pmap1[0].array[0] = .4

        pmap2 = ProbabilityMap.build(3, 1, sids=[0, 1, 2])
        pmap2[0].array[0] = .5

        # test probability composition
        pmap = pmap1 | pmap2
        numpy.testing.assert_equal(pmap[0].array, [[.7], [0], [0]])

        # test probability multiplication
        pmap = pmap1 * pmap2
        numpy.testing.assert_equal(pmap[0].array, [[.2], [0], [0]])

        # test pmap power
        pmap = pmap1 ** 2
        numpy.testing.assert_almost_equal(pmap[0].array, [[.16], [0], [0]])
