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

from openquake.hazardlib.geo.nodalplane import NodalPlane


class NodalPlaneTestCase(unittest.TestCase):
    def _test_broken_input(self, broken_parameter, **kwargs):
        with self.assertRaises(ValueError) as ae:
            NodalPlane(**kwargs)
        self.assertTrue(str(ae.exception).startswith(broken_parameter),
                        str(ae.exception))

        checker = getattr(NodalPlane, 'check_%s' % broken_parameter)
        with self.assertRaises(ValueError) as ae:
            checker(kwargs[broken_parameter])
        self.assertTrue(str(ae.exception).startswith(broken_parameter),
                        str(ae.exception))

    def test_strike_out_of_range(self):
        self._test_broken_input('strike', strike=-0.1, dip=1, rake=0)
        self._test_broken_input('strike', strike=360.1, dip=1, rake=0)
        self._test_broken_input('strike', strike=360, dip=1, rake=0)

    def test_dip_out_of_range(self):
        self._test_broken_input('dip', strike=0, dip=-0.1, rake=0)
        self._test_broken_input('dip', strike=0, dip=0, rake=0)
        self._test_broken_input('dip', strike=0, dip=90.1, rake=0)

    def test_rake_out_of_range(self):
        self._test_broken_input('rake', strike=0, dip=1, rake=-180.1)
        self._test_broken_input('rake', strike=0, dip=1, rake=-180)
        self._test_broken_input('rake', strike=0, dip=1, rake=180.1)

    def test_corner_cases(self):
        np = NodalPlane(strike=0, dip=0.001, rake=-180 + 1e-5)
        self.assertEqual((np.strike, np.dip, np.rake), (0, 0.001, -180 + 1e-5))
        np = NodalPlane(strike=360 - 1e-5, dip=90, rake=+180)
        self.assertEqual((np.strike, np.dip, np.rake), (360 - 1e-5, 90, +180))
