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

import numpy

from openquake.hazardlib.tom import PoissonTOM


class PoissonTOMTestCase(unittest.TestCase):
    def test_non_positive_time_span(self):
        self.assertRaises(ValueError, PoissonTOM, -1)
        self.assertRaises(ValueError, PoissonTOM, 0)

    def test_get_probability_one_or_more_occurrences(self):
        pdf = PoissonTOM(time_span=50)
        self.assertEqual(pdf.get_probability_one_or_more_occurrences(10), 1)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability_one_or_more_occurrences(0.1), 0.9932621)
        aae(pdf.get_probability_one_or_more_occurrences(0.01), 0.39346934)

        pdf = PoissonTOM(time_span=5)
        self.assertEqual(pdf.get_probability_one_or_more_occurrences(8), 1)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability_one_or_more_occurrences(0.1), 0.3934693)
        aae(pdf.get_probability_one_or_more_occurrences(0.01), 0.0487706)

    def test_get_probability_one_occurrence(self):
        pdf = PoissonTOM(time_span=30)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability_one_occurrence(10), 0)
        aae(pdf.get_probability_one_occurrence(0.1), 0.1493612)
        aae(pdf.get_probability_one_occurrence(0.01), 0.2222455)

    def test_sample_number_of_occurrences(self):
        time_span = 40
        rate = 0.05
        num_samples = 8000
        tom = PoissonTOM(time_span)
        numpy.random.seed(31)
        mean = sum(tom.sample_number_of_occurrences(rate)
                   for i in range(num_samples)) / float(num_samples)
        self.assertAlmostEqual(mean, rate * time_span, delta=1e-3)

    def test_get_probability_no_exceedance(self):
        time_span = 50.
        rate = 0.01
        poes = numpy.array([[0.9, 0.8, 0.7], [0.6, 0.5, 0.4]])
        tom = PoissonTOM(time_span)
        pne = tom.get_probability_no_exceedance(rate, poes)
        numpy.testing.assert_allclose(
            pne,
            numpy.array([[0.6376282, 0.6703200, 0.7046881],
                         [0.7408182, 0.7788008, 0.8187308]])
        )
