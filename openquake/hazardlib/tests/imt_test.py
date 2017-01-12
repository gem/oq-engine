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
import unittest
import pickle
from openquake.hazardlib import imt as imt_module


class BaseIMTTestCase(unittest.TestCase):
    class TestIMT(imt_module._IMT):
        _fields = ('foo', 'bar')

        def __new__(cls, foo, bar):
            return imt_module._IMT.__new__(cls, foo, bar)

    def test_base(self):
        self.assertEqual(getattr(self.TestIMT, '__slots__'), ())
        self.assertFalse(hasattr(self.TestIMT(1, 2), '__dict__'))
        imt = self.TestIMT(bar=2, foo=1)
        self.assertEqual(str(imt), 'TestIMT')

    def test_equality(self):
        self.assertTrue(self.TestIMT(1, 1) == self.TestIMT(1, 1))
        self.assertTrue(self.TestIMT(1, 5) == self.TestIMT(1, 5))
        self.assertTrue(self.TestIMT('foo', 'bar') ==
                        self.TestIMT('foo', 'bar'))

        self.assertFalse(self.TestIMT(1, 1) != self.TestIMT(1, 1))
        self.assertFalse(self.TestIMT(1, 5) != self.TestIMT(1, 5))
        self.assertFalse(self.TestIMT('foo', 'bar') !=
                         self.TestIMT('foo', 'bar'))

        self.assertFalse(self.TestIMT(1, 1) == (1, 1))
        self.assertFalse(self.TestIMT(0, 1) == self.TestIMT(1, 1))
        self.assertFalse(self.TestIMT(1, 5.4) == self.TestIMT(1, 5))
        self.assertFalse(self.TestIMT('foo', 'bar') ==
                         self.TestIMT('fooz', 'bar'))
        self.assertFalse(self.TestIMT('foo', 'bar') == ('foo', 'bar'))
        self.assertFalse(self.TestIMT(False, False) is False)

        self.assertTrue(self.TestIMT(1, 1) != (1, 1))
        self.assertTrue(self.TestIMT(0, 1) != self.TestIMT(1, 1))
        self.assertTrue(self.TestIMT(1, 5.4) != self.TestIMT(1, 5))
        self.assertTrue(self.TestIMT('foo', 'bar') !=
                        self.TestIMT('fooz', 'bar'))
        self.assertTrue(self.TestIMT('foo', 'bar') != ('foo', 'bar'))

    def test_hash(self):
        imt1 = self.TestIMT('some', 'thing')
        self.assertEqual(hash(imt1), hash(self.TestIMT('some', 'thing')))
        self.assertNotEqual(hash(imt1), hash(self.TestIMT('other', 'thing')))

        class TestIMT2(self.TestIMT):
            pass

        imt2 = TestIMT2('some', 'thing')
        self.assertNotEqual(hash(imt1), hash(imt2))

    def test_pickeable(self):
        for imt in (imt_module.PGA(), imt_module.SA(0.2)):
            imt_pik = pickle.dumps(imt, pickle.HIGHEST_PROTOCOL)
            self.assertEqual(pickle.loads(imt_pik), imt)

    def test_equivalent(self):
        sa1 = imt_module.from_string('SA(0.1)')
        sa2 = imt_module.from_string('SA(0.10)')
        self.assertEqual(sa1, sa2)
        self.assertEqual(set([sa1, sa2]), set([sa1]))

    def test_from_string(self):
        sa = imt_module.from_string('SA(0.1)')
        self.assertEqual(sa, ('SA', 0.1, 5.0))
        pga = imt_module.from_string('PGA')
        self.assertEqual(pga, ('PGA', None, None))
        with self.assertRaises(ValueError):
            imt_module.from_string('XXX')


class SATestCase(unittest.TestCase):
    def test_wrong_period(self):
        self.assertRaises(ValueError, imt_module.SA, period=0, damping=5)
        self.assertRaises(ValueError, imt_module.SA, period=-1, damping=5)

    def test_wrong_damping(self):
        self.assertRaises(ValueError, imt_module.SA, period=0.1, damping=0)
        self.assertRaises(ValueError, imt_module.SA, period=0.1, damping=-1)


class ImtOrderingTestCase(unittest.TestCase):
    def test_ordering_and_equality(self):
        a = imt_module.from_string('SA(0.1)')
        b = imt_module.from_string('SA(0.10)')
        c = imt_module.from_string('SA(0.2)')
        self.assertLess(a, c)
        self.assertGreater(c, a)
        self.assertEqual(a, b)
