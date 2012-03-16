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

from nhlib.site import Site
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
