# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
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
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.sourceconverter import FaultSectionConverter
from openquake.hazardlib.geo import Point

datadir = os.path.join(os.path.dirname(__file__), 'data', 'sections')


class KiteFaultSectionsTestCase(unittest.TestCase):

    def setUp(self):
        fname = 'sections_kite.xml'
        self.fname = os.path.join(datadir, fname)

    def test_load_kite(self):
        conv = FaultSectionConverter()
        sec = to_python(self.fname, conv)
        expected = [Point(11, 45, 0), Point(11, 45.5, 10)]
        print(sec[1].profiles[0].points)
        self.assertEqual(expected[0], sec[1].profiles[0].points[0])
        self.assertEqual(expected[1], sec[1].profiles[0].points[1])

class KiteFaultSectionsTestCase(unittest.TestCase):

    def setUp(self):
        fname = 'sections_mix.xml'
        self.fname = os.path.join(datadir, fname)

    def test_load_error(self):
        conv = FaultSectionConverter()
        self.assertRaises(ValueError, to_python, self.fname, conv)
