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
from decimal import Decimal

import unittest
import numpy as np
from openquake.hazardlib.pmf import PMF


class PMFTestCase(unittest.TestCase):
    def test_creation(self):
        pmf = PMF((Decimal('0.1'), i) for i in range(10))
        self.assertEqual(pmf.data, [(0.1, i) for i in range(10)])

    def test_wrong_sum(self):
        data = [(0.1, i) for i in range(10)]
        self.assertRaises(ValueError, PMF, data, 1E-16)

    def test_empty_data(self):
        self.assertRaises(ValueError, PMF, [])

    def test_negative_or_zero_prob(self):
        # negative probs are refused
        data = [(-1, 0)] + [(Decimal('1.0'), 1), (Decimal('1.0'), 2)]
        self.assertRaises(ValueError, PMF, data)

        # 0 probs are accepted
        data = [(0, 0)] + [(Decimal('0.5'), 1), (Decimal('0.5'), 2)]
        PMF(data)

    def test_sample_pmf_numerical(self):
        """
        Tests the sampling function for numerical data - using a random
        seed approach
        """
        pmf = PMF([(0.3, 1), (0.5, 2), (0.2, 4)])
        np.random.seed(22)
        self.assertListEqual(pmf.sample(10),
                             [1, 2, 2, 4, 1, 2, 1, 2, 1, 4])

    def test_sample_pmf_non_numerical(self):
        """
        Tests the sampling function for non-numerical data - using a random
        seed approach
        """
        pmf = PMF([(0.3, "apples"),
                   (0.1, "oranges"),
                   (0.4, "bananas"),
                   (0.2, "lemons")])
        np.random.seed(22)
        expected = ['apples', 'bananas', 'bananas', 'lemons', 'apples',
                    'oranges', 'apples', 'bananas', 'apples', 'lemons']
        self.assertListEqual(pmf.sample(10), expected)

    def test_sample_pmf_convergence(self):
        """
        Tests the PMF sampling function for numerical convergence
        """
        pmf = PMF([(0.3, 1.), (0.5, 2.), (0.2, 4.)])
        # Take 100000 samples of the PMF and find the density of the results
        output = np.histogram(pmf.sample(100000),
                              np.array([0.5, 1.5, 2.5, 3.5, 4.5]),
                              density=True)[0]
        np.testing.assert_array_almost_equal(output,
                                             np.array([0.3, 0.5, 0.0, 0.2]),
                                             2)  # Tests to 2 decimal places
