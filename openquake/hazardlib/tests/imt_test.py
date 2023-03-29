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
import unittest
from openquake.hazardlib import imt as imt_module


class ImtOrderingTestCase(unittest.TestCase):
    def test_ordering_and_equality(self):
        a = imt_module.from_string('SA(0.1)')
        b = imt_module.from_string('SA(0.10)')
        c = imt_module.from_string('SA(0.2)')
        self.assertLess(a, c)
        self.assertGreater(c, a)
        self.assertEqual(a, b)
        self.assertLess(imt_module.from_string('SA(9)'),
                        imt_module.from_string('SA(10)'))
        self.assertGreater(imt_module.from_string('SA(10)'),
                           imt_module.from_string('SA(9)'))

    def test_equivalent(self):
        sa1 = imt_module.from_string('SA(0.1)')
        sa2 = imt_module.from_string('SA(0.10)')
        self.assertEqual(sa1, sa2)
        self.assertEqual({sa1, sa2}, {sa1})

    def test_from_string(self):
        sa = imt_module.from_string('SA(0.1)')
        self.assertEqual(sa, ('SA(0.1)', 0.1, 5.0))
        pga = imt_module.from_string('PGA')
        self.assertEqual(pga, ('PGA', 0, 5.0))
        with self.assertRaises(KeyError):
            imt_module.from_string('XXX')
