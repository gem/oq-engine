# The Hazard Library
# Copyright (C) 2016-2017 GEM Foundation
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
from openquake.hazardlib.mfd import ArbitraryMFD

from openquake.hazardlib.tests.mfd.base_test import BaseMFDTestCase

class ArbitrarydMFDMFDConstraintsTestCase(BaseMFDTestCase):
    def test_empty_occurrence_rates(self):
        exc = self.assert_mfd_error(
            ArbitraryMFD,
            magnitudes=[4., 5.], occurrence_rates=[]
        )
        self.assertEqual(str(exc), 'at least one bin must be specified')

    def test_negative_occurrence_rate(self):
        exc = self.assert_mfd_error(
            ArbitraryMFD,
            magnitudes=[4., 5.], occurrence_rates=[-0.1, 1]
        )
        self.assertEqual(str(exc), 'all occurrence rates '
                                      'must not be negative')

    def test_all_zero_occurrence_rates(self):
        exc = self.assert_mfd_error(
            ArbitraryMFD,
            magnitudes=[4., 5.], occurrence_rates=[0, 0]
        )
        self.assertEqual(str(exc), 'at least one occurrence rate '
                                      'must be positive')


    def test_unequal_lengths(self):
        exc = self.assert_mfd_error(
            ArbitraryMFD,
            magnitudes=[4., 5., 6.], occurrence_rates=[0.1, 1]
        )
        self.assertEqual(str(exc),
                         'lists of magnitudes and rates must have same length')

class ArbitraryMFDTestCase(BaseMFDTestCase):
    def test_get_annual_occurrence_rates(self):
        mfd = ArbitraryMFD(magnitudes=[4, 5, 6], occurrence_rates=[1, 2, 3])
        self.assertEqual(mfd.get_annual_occurrence_rates(),
                         [(4, 1), (5, 2), (6, 3)])

    def test_get_min_max(self):
        mfd = ArbitraryMFD(magnitudes=[4, 5, 6], occurrence_rates=[1, 2, 3])
        self.assertEqual(mfd.get_min_max_mag(), (4, 6))
    
    def test_modify_mfd(self):
        mfd = ArbitraryMFD(magnitudes=(4., 5., 6.),
                           occurrence_rates=(1., 2., 3.))
        mfd.modify(
            "set_mfd",
            {"magnitudes": [7, 8, 9], "occurrence_rates": [0, 2, 1]})
        self.assertListEqual(mfd.magnitudes, [7, 8, 9])
        self.assertListEqual(mfd.occurrence_rates, [0, 2, 1])
