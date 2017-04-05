from __future__ import division
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
from nose.plugins.attrib import attr

import numpy
import os
from decimal import Decimal
from openquake.hazardlib import const
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.source.rupture import BaseRupture, \
    ParametricProbabilisticRupture, NonParametricProbabilisticRupture
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface


def make_rupture(rupture_class, **kwargs):
    default_arguments = {
        'mag': 5.5,
        'rake': 123.45,
        'tectonic_region_type': const.TRT.STABLE_CONTINENTAL,
        'hypocenter': Point(5, 6, 7),
        'surface': PlanarSurface(10, 11, 12, Point(0, 0, 1), Point(1, 0, 1),
                                 Point(1, 0, 2), Point(0, 0, 2)),
        'source_typology': object()
    }
    default_arguments.update(kwargs)
    kwargs = default_arguments
    rupture = rupture_class(**kwargs)
    for key in kwargs:
        if key != 'pmf':
            # for pmf .pmf is a numpy array whereas pmf is a PMF instance
            assert getattr(rupture, key) is kwargs[key], (
                getattr(rupture, key), kwargs[key])
    return rupture


class RuptureCreationTestCase(unittest.TestCase):
    def assert_failed_creation(self, rupture_class, exc, msg, **kwargs):
        with self.assertRaises(exc) as ae:
            make_rupture(rupture_class, **kwargs)
        self.assertEqual(str(ae.exception), msg)

    def test_negative_magnitude(self):
        self.assert_failed_creation(
            BaseRupture, ValueError,
            'magnitude must be positive',
            mag=-1
        )

    def test_zero_magnitude(self):
        self.assert_failed_creation(
            BaseRupture, ValueError,
            'magnitude must be positive',
            mag=0
        )

    def test_probabilistic_rupture_negative_occurrence_rate(self):
        self.assert_failed_creation(
            ParametricProbabilisticRupture, ValueError,
            'occurrence rate must be positive',
            occurrence_rate=-1, temporal_occurrence_model=PoissonTOM(10)
        )

    def test_probabilistic_rupture_zero_occurrence_rate(self):
        self.assert_failed_creation(
            ParametricProbabilisticRupture, ValueError,
            'occurrence rate must be positive',
            occurrence_rate=0, temporal_occurrence_model=PoissonTOM(10)
        )

    def test_rupture_topo(self):
        rupture = make_rupture(BaseRupture, hypocenter=Point(5, 6, -2))
        self.assertEqual(rupture.hypocenter.depth, -2)


class ParametricProbabilisticRuptureTestCase(unittest.TestCase):
    def test_get_probability_one_or_more(self):
        rupture = make_rupture(ParametricProbabilisticRupture,
                               occurrence_rate=1e-2,
                               temporal_occurrence_model=PoissonTOM(10))
        self.assertAlmostEqual(
            rupture.get_probability_one_or_more_occurrences(), 0.0951626
        )

    def test_get_probability_one_occurrence(self):
        rupture = make_rupture(ParametricProbabilisticRupture,
                               occurrence_rate=0.4,
                               temporal_occurrence_model=PoissonTOM(10))
        self.assertAlmostEqual(rupture.get_probability_one_occurrence(),
                               0.0732626)

    def test_sample_number_of_occurrences(self):
        time_span = 20
        rate = 0.01
        num_samples = 2000
        tom = PoissonTOM(time_span)
        rupture = make_rupture(ParametricProbabilisticRupture,
                               occurrence_rate=rate,
                               temporal_occurrence_model=tom)
        numpy.random.seed(37)
        mean = sum(rupture.sample_number_of_occurrences()
                   for i in range(num_samples)) / float(num_samples)
        self.assertAlmostEqual(mean, rate * time_span, delta=2e-3)

    def test_get_probability_no_exceedance(self):
        rupture = make_rupture(ParametricProbabilisticRupture,
                               occurrence_rate=0.01,
                               temporal_occurrence_model=PoissonTOM(50))
        poes = numpy.array([[0.9, 0.8, 0.7], [0.6, 0.5, 0.4]])
        pne = rupture.get_probability_no_exceedance(poes)
        numpy.testing.assert_allclose(
            pne,
            numpy.array([[0.6376282, 0.6703200, 0.7046881],
                         [0.7408182, 0.7788008, 0.8187308]])
        )


class Cdppvalue(unittest.TestCase):

    def make_rupture_fordpp(self, rupture_class, **kwargs):
        # Create the rupture surface.
        upper_seismogenic_depth = 0.
        lower_seismogenic_depth = 15.
        dip = 90.
        mesh_spacing = 1.
        fault_trace_start = Point(10., 45.2)
        fault_trace_end = Point(10., 45.919457)
        fault_trace = Line([fault_trace_start, fault_trace_end])
        default_arguments = {
            'mag': 7.2,
            'rake': 0.,
            'tectonic_region_type': const.TRT.STABLE_CONTINENTAL,
            'hypocenter': Point(10.0, 45.334898, 10),
            'surface': SimpleFaultSurface.from_fault_data(
                fault_trace, upper_seismogenic_depth, lower_seismogenic_depth,
                dip=dip, mesh_spacing=mesh_spacing),
            'source_typology': object(),
            'rupture_slip_direction': 0.
        }
        default_arguments.update(kwargs)
        kwargs = default_arguments
        rupture = rupture_class(**kwargs)
        for key in kwargs:
            assert getattr(rupture, key) is kwargs[key]
        return rupture

    def test_get_dppvalue(self):
        rupture = self.make_rupture_fordpp(
            ParametricProbabilisticRupture, occurrence_rate=0.01,
            temporal_occurrence_model=PoissonTOM(50))
        # Load the testing site.
        data_path = os.path.dirname(__file__)
        filename = os.path.join(
            data_path, "./data/geo_cycs_ss3_testing_site.csv")
        data = numpy.genfromtxt(filename,
                                dtype=float, delimiter=',', names=True,
                                skip_header=6675, skip_footer=6673)

        for loc in range(len(data)):
            lon = data[loc][0]
            lat = data[loc][1]
            ref_dpp = data[loc][2]
            dpp = rupture.get_dppvalue(Point(lon, lat))

            self.assertAlmostEqual(dpp, ref_dpp, delta=0.1)

    @attr('slow')
    def test_get_cdppvalue(self):
        rupture = self.make_rupture_fordpp(
            ParametricProbabilisticRupture, occurrence_rate=0.01,
            temporal_occurrence_model=PoissonTOM(50))
        # Load the testing site.
        data_path = os.path.dirname(__file__)
        filename = os.path.join(
            data_path, "./data/geo_cycs_ss3_testing_site.csv")
        data = numpy.genfromtxt(filename,
                                dtype=float, delimiter=',', names=True,
                                skip_header=6675, skip_footer=6673)
        points = []
        for loc in range(len(data)):
            lon = data[loc][0]
            lat = data[loc][1]
            points.append(Point(lon, lat))

        mesh = Mesh.from_points_list(points)
        cdpp = rupture.get_cdppvalue(mesh)
        self.assertAlmostEqual(cdpp[0], data[0][3], delta=0.1)
        self.assertAlmostEqual(cdpp[1], data[1][3], delta=0.1)


class NonParametricProbabilisticRuptureTestCase(unittest.TestCase):
    def assert_failed_creation(self, rupture_class, exc, msg, **kwargs):
        with self.assertRaises(exc) as ae:
            make_rupture(rupture_class, **kwargs)
        self.assertEqual(str(ae.exception), msg)

    def test_creation(self):
        pmf = PMF([(Decimal('0.8'), 0), (Decimal('0.2'), 1)])
        make_rupture(NonParametricProbabilisticRupture, pmf=pmf)

    def test_minimum_number_of_ruptures_is_not_zero(self):
        pmf = PMF([(Decimal('0.8'), 1), (Decimal('0.2'), 2)])
        self.assert_failed_creation(
            NonParametricProbabilisticRupture,
            ValueError, 'minimum number of ruptures must be zero', pmf=pmf
        )

    def test_numbers_of_ruptures_not_in_increasing_order(self):
        pmf = PMF(
            [(Decimal('0.8'), 0), (Decimal('0.1'), 2), (Decimal('0.1'), 1)]
        )
        self.assert_failed_creation(
            NonParametricProbabilisticRupture,
            ValueError,
            'numbers of ruptures must be defined in increasing order', pmf=pmf
        )

    def test_numbers_of_ruptures_not_defined_with_unit_step(self):
        pmf = PMF([(Decimal('0.8'), 0), (Decimal('0.2'), 2)])
        self.assert_failed_creation(
            NonParametricProbabilisticRupture,
            ValueError,
            'numbers of ruptures must be defined with unit step', pmf=pmf
        )

    def test_get_probability_no_exceedance(self):
        pmf = PMF(
            [(Decimal('0.7'), 0), (Decimal('0.2'), 1), (Decimal('0.1'), 2)]
        )
        poes = numpy.array([[0.9, 0.8, 0.7], [0.6, 0.5, 0.4]])
        rup = make_rupture(NonParametricProbabilisticRupture, pmf=pmf)
        pne = rup.get_probability_no_exceedance(poes)
        numpy.testing.assert_allclose(
            pne,
            numpy.array([[0.721, 0.744, 0.769], [0.796, 0.825, 0.856]])
        )

    def test_sample_number_of_occurrences(self):
        pmf = PMF(
            [(Decimal('0.7'), 0), (Decimal('0.2'), 1), (Decimal('0.1'), 2)]
        )
        rup = make_rupture(NonParametricProbabilisticRupture, pmf=pmf)
        numpy.random.seed(123)

        n_samples = 50000
        n_occs = numpy.array([
            rup.sample_number_of_occurrences() for i in range(n_samples)
        ])

        p_occs_0 = float(len(n_occs[n_occs == 0])) / n_samples
        p_occs_1 = float(len(n_occs[n_occs == 1])) / n_samples
        p_occs_2 = float(len(n_occs[n_occs == 2])) / n_samples

        self.assertAlmostEqual(p_occs_0, 0.7, places=2)
        self.assertAlmostEqual(p_occs_1, 0.2, places=2)
        self.assertAlmostEqual(p_occs_2, 0.1, places=2)
