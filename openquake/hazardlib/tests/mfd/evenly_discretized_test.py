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
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD

from openquake.hazardlib.tests.mfd.base_test import BaseMFDTestCase


class EvenlyDiscretizedMFDMFDConstraintsTestCase(BaseMFDTestCase):
    def test_empty_occurrence_rates(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=2, occurrence_rates=[]
        )
        self.assertEqual(str(exc), 'at least one bin must be specified')

    def test_negative_occurrence_rate(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=2, occurrence_rates=[-0.1, 1]
        )
        self.assertEqual(str(exc), 'all occurrence rates '
                                      'must not be negative')

    def test_all_zero_occurrence_rates(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=2, occurrence_rates=[0, 0]
        )
        self.assertEqual(str(exc), 'at least one occurrence rate '
                                      'must be positive')

    def test_negative_minimum_magnitude(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=-1, bin_width=2, occurrence_rates=[0.1, 1]
        )
        self.assertEqual(str(exc), 'minimum magnitude must be non-negative')

    def test_negative_bin_width(self):
        exc = self.assert_mfd_error(
            EvenlyDiscretizedMFD,
            min_mag=1, bin_width=-2, occurrence_rates=[0.1, 1]
        )
        self.assertEqual(str(exc), 'bin width must be positive')


class EvenlyDiscretizedMFDTestCase(BaseMFDTestCase):
    def test_zero_min_mag(self):
        mfd = EvenlyDiscretizedMFD(min_mag=0, bin_width=1,
                                   occurrence_rates=[1])
        self.assertEqual(mfd.get_annual_occurrence_rates(), [(0, 1)])
        self.assertEqual(mfd.get_min_max_mag(), (0, 0))

    def test_zero_rate(self):
        evenly_discretized = EvenlyDiscretizedMFD(
            min_mag=1, bin_width=2, occurrence_rates=[4, 0, 5]
        )
        self.assertEqual(evenly_discretized.get_annual_occurrence_rates(),
                         [(1, 4), (3, 0), (5, 5)])

    def test(self):
        evenly_discretized = EvenlyDiscretizedMFD(
            min_mag=0.2, bin_width=0.3, occurrence_rates=[2.1, 2.4, 5.3]
        )
        self.assertEqual(evenly_discretized.get_annual_occurrence_rates(),
                         [(0.2, 2.1), (0.5, 2.4), (0.8, 5.3)])
        self.assertEqual(evenly_discretized.get_min_max_mag(), (0.2, 0.8))


class EvenlyDiscretizedMFDTestCase(BaseMFDTestCase):
    def test_modify_mfd(self):
        mfd = EvenlyDiscretizedMFD(min_mag=4.0, bin_width=0.1,
                                   occurrence_rates=[1, 2, 3])
        mfd.modify(
            "set_mfd",
            {"min_mag": 4.5, "bin_width": 0.2, "occurrence_rates": [4, 5, 6]})
        self.assertAlmostEqual(mfd.min_mag, 4.5)
        self.assertAlmostEqual(mfd.bin_width, 0.2)
        self.assertListEqual(mfd.occurrence_rates, [4, 5, 6])

    def test_modify_mfd_constraints(self):
        mfd = EvenlyDiscretizedMFD(min_mag=4.0, bin_width=0.1,
                                   occurrence_rates=[1, 2, 3])
        exc = self.assert_mfd_error(
            mfd.modify,
            "set_mfd",
            {"min_mag": 4.0, "bin_width": 0.1, "occurrence_rates": [-1, 2, 3]})

        self.assertEqual(str(exc), 'all occurrence rates must not be negative')
