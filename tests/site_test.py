# nhlib: A New Hazard Library
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

import numpy

from nhlib.site import Site, SiteCollection
from nhlib.geo.point import Point


class SiteTestCase(unittest.TestCase):
    def _assert_creation(self, error=None, **kwargs):
        default_kwargs = {
            'location': Point(10, 20),
            'vs30': 10,
            'vs30measured': False,
            'z1pt0': 20,
            'z2pt5': 30
        }
        default_kwargs.update(kwargs)
        kwargs = default_kwargs
        if error is not None:
            with self.assertRaises(ValueError) as ar:
                Site(**kwargs)
            self.assertEqual(ar.exception.message, error)
        else:
            site = Site(**kwargs)
            for attr in kwargs:
                self.assertEqual(getattr(site, attr), kwargs[attr])

    def test_wrong_vs30(self):
        error = 'vs30 must be positive'
        self._assert_creation(error=error, vs30=0)
        self._assert_creation(error=error, vs30=-1)

    def test_wrong_z1pt0(self):
        error = 'z1pt0 must be positive'
        self._assert_creation(error=error, z1pt0=0)
        self._assert_creation(error=error, z1pt0=-1)

    def test_wrong_z2pt5(self):
        error = 'z2pt5 must be positive'
        self._assert_creation(error=error, z2pt5=0)
        self._assert_creation(error=error, z2pt5=-1)

    def test_successful_creation(self):
        self._assert_creation()


class SiteCollectionTestCase(unittest.TestCase):
    def test(self):
        s1 = Site(location=Point(10, 20, 30),
                  vs30=1.2, vs30measured=True,
                  z1pt0=3.4, z2pt5=5.6)
        s2 = Site(location=Point(-1.2, -3.4, -5.6),
                  vs30=55.4, vs30measured=False,
                  z1pt0=66.7, z2pt5=88.9)
        cll = SiteCollection([s1, s2])
        self.assertTrue((cll.vs30 == [1.2, 55.4]).all())
        self.assertTrue((cll.vs30measured == [True, False]).all())
        self.assertTrue((cll.z1pt0 == [3.4, 66.7]).all())
        self.assertTrue((cll.z2pt5 == [5.6, 88.9]).all())
        self.assertTrue((cll.mesh.lons == [10, -1.2]).all())
        self.assertTrue((cll.mesh.lats == [20, -3.4]).all())
        self.assertIs(cll.mesh.depths, None)
        for arr in (cll.vs30, cll.z1pt0, cll.z2pt5):
            self.assertIsInstance(arr, numpy.ndarray)
            self.assertEqual(arr.flags.writeable, False)
            self.assertEqual(arr.dtype, float)
        self.assertIsInstance(cll.vs30measured, numpy.ndarray)
        self.assertEqual(cll.vs30measured.flags.writeable, False)
        self.assertEqual(cll.vs30measured.dtype, bool)

        self.assertEqual(len(cll), 2)
