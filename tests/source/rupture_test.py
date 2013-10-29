# The Hazard Library
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
from decimal import Decimal

from openquake.hazardlib import const
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import Rupture, ProbabilisticRupture, \
NonParametricProbabilisticRupture
from openquake.hazardlib.pmf import PMF


def make_rupture(rupture_class, **kwargs):
    default_arguments = {
        'mag': 5.5,
        'rake': 123.45,
        'tectonic_region_type': const.TRT.STABLE_CONTINENTAL,
        'hypocenter': Point(5, 6, 7),
        'surface': PlanarSurface(10, 11, 12,
            Point(0, 0, 1), Point(1, 0, 1),
            Point(1, 0, 2), Point(0, 0, 2)
        ),
        'source_typology': object()
    }
    default_arguments.update(kwargs)
    kwargs = default_arguments
    rupture = rupture_class(**kwargs)
    for key in kwargs:
        assert getattr(rupture, key) is kwargs[key]
    return rupture


class RuptureCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, rupture_class, exc, msg, **kwargs):
        with self.assertRaises(exc) as ae:
            make_rupture(rupture_class, **kwargs)
        self.assertEqual(ae.exception.message, msg)

    def test_negative_magnitude(self):
        self.assert_failed_creation(Rupture, ValueError,
            'magnitude must be positive',
            mag=-1
        )

    def test_zero_magnitude(self):
        self.assert_failed_creation(Rupture, ValueError,
            'magnitude must be positive',
            mag=0
        )

    def test_hypocenter_in_the_air(self):
        self.assert_failed_creation(Rupture, ValueError,
            'rupture hypocenter must have positive depth',
            hypocenter=Point(0, 1, -0.1)
        )

    def test_probabilistic_rupture_negative_occurrence_rate(self):
        self.assert_failed_creation(ProbabilisticRupture, ValueError,
            'occurrence rate must be positive',
            occurrence_rate=-1, temporal_occurrence_model=PoissonTOM(10)
        )

    def test_probabilistic_rupture_zero_occurrence_rate(self):
        self.assert_failed_creation(ProbabilisticRupture, ValueError,
            'occurrence rate must be positive',
            occurrence_rate=0, temporal_occurrence_model=PoissonTOM(10)
        )


class ProbabilisticRuptureTestCase(unittest.TestCase):
    def test_get_probability_one_or_more(self):
        rupture = make_rupture(ProbabilisticRupture,
                               occurrence_rate=1e-2,
                               temporal_occurrence_model=PoissonTOM(10))
        self.assertAlmostEqual(
            rupture.get_probability_one_or_more_occurrences(), 0.0951626
        )

    def test_get_probability_one_occurrence(self):
        rupture = make_rupture(ProbabilisticRupture,
                               occurrence_rate=0.4,
                               temporal_occurrence_model=PoissonTOM(10))
        self.assertAlmostEqual(rupture.get_probability_one_occurrence(),
                               0.0732626)

    def test_sample_number_of_occurrences(self):
        time_span = 20
        rate = 0.01
        num_samples = 2000
        tom = PoissonTOM(time_span)
        rupture = make_rupture(ProbabilisticRupture, occurrence_rate=rate,
                               temporal_occurrence_model=tom)
        numpy.random.seed(37)
        mean = sum(rupture.sample_number_of_occurrences()
                   for i in xrange(num_samples)) / float(num_samples)
        self.assertAlmostEqual(mean, rate * time_span, delta=2e-3)

class NonParametricProbabilisticRuptureTestCase(unittest.TestCase):
    def assert_failed_creation(self, rupture_class, exc, msg, **kwargs):
        with self.assertRaises(exc) as ae:
            make_rupture(rupture_class, **kwargs)
        self.assertEqual(ae.exception.message, msg)

    def test_creation(self):
        pmf = PMF([(Decimal('0.8'), 0), (Decimal('0.2'), 1)])
        make_rupture(NonParametricProbabilisticRupture, pmf=pmf)

    def test_minimum_number_of_ruptures_is_not_zero(self):
        pmf = PMF([(Decimal('0.8'), 1), (Decimal('0.2'), 2)])
        self.assert_failed_creation(NonParametricProbabilisticRupture,
            ValueError, 'minimum number of ruptures must be zero', pmf=pmf)

    def test_numbers_of_ruptures_not_in_increasing_order(self):
        pmf = PMF(
            [(Decimal('0.8'), 0), (Decimal('0.1'), 2), (Decimal('0.1'), 1)]
        )
        self.assert_failed_creation(NonParametricProbabilisticRupture,
            ValueError,
            'numbers of ruptures must be defined in increasing order', pmf=pmf)

    def test_numbers_of_ruptures_not_defined_with_unit_step(self):
        pmf = PMF([(Decimal('0.8'), 0), (Decimal('0.2'), 2)])
        self.assert_failed_creation(NonParametricProbabilisticRupture,
            ValueError,
            'numbers of ruptures must be defined with unit step', pmf=pmf)
        


