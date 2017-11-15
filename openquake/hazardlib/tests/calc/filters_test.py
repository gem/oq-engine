#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

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
from numpy.testing import assert_almost_equal as aae
from openquake.hazardlib.calc.filters import IntegrationDistance


class IntegrationDistanceTestCase(unittest.TestCase):
    def test_bounding_box(self):
        maxdist = IntegrationDistance({'default': [
            (3, 30), (4, 40), (5, 100), (6, 200), (7, 300), (8, 400)]})

        aae(maxdist('ANY_TRT'), 400)
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT')
        aae(bb, [-3.6527738, 6.40272, 3.6527738, 13.59728])

        aae(maxdist('ANY_TRT', mag=7.1), 400)
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT', mag=7.1)
        aae(bb, [-3.6527738, 6.40272, 3.6527738, 13.59728])

        aae(maxdist('ANY_TRT', mag=6.9), 300)
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT', mag=6.9)  # maxdist=200
        aae(bb, [-2.7395804, 7.30204, 2.7395804, 12.69796])
