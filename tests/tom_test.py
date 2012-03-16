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

from nhe.tom import PoissonTOM


class PoissonTOMTestCase(unittest.TestCase):
    def test_non_positive_time_span(self):
        self.assertRaises(ValueError, PoissonTOM, -1)
        self.assertRaises(ValueError, PoissonTOM, 0)

    def test_get_probability(self):
        pdf = PoissonTOM(time_span=50)
        self.assertEqual(pdf.get_probability(occurrence_rate=10), 1)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability(occurrence_rate=0.1), 0.9932621)
        aae(pdf.get_probability(occurrence_rate=0.01), 0.39346934)

        pdf = PoissonTOM(time_span=5)
        self.assertEqual(pdf.get_probability(occurrence_rate=8), 1)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability(occurrence_rate=0.1), 0.3934693)
        aae(pdf.get_probability(occurrence_rate=0.01), 0.0487706)
