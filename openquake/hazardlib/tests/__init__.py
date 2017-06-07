# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
import pickle
import unittest
from openquake.baselib.general import assert_independent


def assert_angles_equal(testcase, angle1, angle2, delta):
    if abs(angle1 - angle2) > 180:
        angle1, angle2 = 360 - max((angle1, angle2)), min((angle1, angle2))
    testcase.assertAlmostEqual(angle1, angle2, delta=delta)


def assert_pickleable(obj):
    pickle.loads(pickle.dumps(obj)).assert_equal(obj)


class IndependenceTestCase(unittest.TestCase):
    def test(self):
        assert_independent('openquake.baselib', 'openquake.hazardlib')
        assert_independent('openquake.hazardlib', 'openquake.hmtk')
