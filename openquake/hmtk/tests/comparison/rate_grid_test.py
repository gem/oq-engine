#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2015-2017, GEM Foundation, G. Weatherill, M. Pagani
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""
Tests the rate grid calculations
"""
import os
import unittest
import numpy as np
from openquake.hazardlib.source.complex_fault import ComplexFaultSource
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.scalerel.point import PointMSR
from openquake.hazardlib.scalerel.peer import PeerMSR
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hmtk.comparison.rate_grids import RateGrid, RatePolygon

SOURCE_MODEL_FILE = os.path.join(os.path.dirname(__file__),
                                 "rate_grid_test_model.xml")

POINT_SOURCE = PointSource("PNT000", "Point 000",
                           "Active Shallow Crust",
                           EvenlyDiscretizedMFD(5.0, 0.1, [1.0]),
                           1.0,
                           PointMSR(),
                           1.0,
                           PoissonTOM(1.0),
                           0.0,
                           20.0,
                           Point(15.05, 15.05),
                           PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                           PMF([(1.0, 5.0)]))

BORDER_POINT_SOURCE = PointSource("PNT000", "Point 000",
                                  "Active Shallow Crust",
                                  EvenlyDiscretizedMFD(5.0, 0.1, [1.0]),
                                  1.0,
                                  PointMSR(),
                                  1.0,
                                  PoissonTOM(1.0),
                                  0.0,
                                  20.0,
                                  Point(15.0, 15.0),
                                  PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                                  PMF([(1.0, 5.0)]))

OUTSIDE_POINT_SOURCE = PointSource(
    "PNT000", "Point 000",
    "Active Shallow Crust",
    EvenlyDiscretizedMFD(5.0, 0.1, [1.0]),
    1.0,
    PointMSR(),
    1.0,
    PoissonTOM(1.0),
    0.0,
    20.0,
    Point(15.0, 15.2),
    PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
    PMF([(1.0, 5.0)]))

AREA_POLY = Polygon([Point(14.95, 15.05),
                     Point(15.05, 15.05),
                     Point(15.05, 14.95),
                     Point(14.95, 14.95)])

AREA_SOURCE = AreaSource("AREA000", "Area 000",
                         "Active Shallow Crust",
                         EvenlyDiscretizedMFD(5.0, 0.1, [1.0]),
                         1.0,
                         PointMSR(),
                         1.0,
                         PoissonTOM(1.0),
                         0.,
                         40.,
                         PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))]),
                         PMF([(0.5, 5.0), (0.5, 15.0)]),
                         AREA_POLY,
                         4.0)

SIMPLE_TRACE = Line([Point(14.975, 15.0, 0.0), Point(15.025, 15.0, 0.0)])

SIMPLE_FAULT = SimpleFaultSource("SFLT000", "Simple Fault Source",
                                 "Active Shallow Crust",
                                 EvenlyDiscretizedMFD(7.0, 0.1, [1.0]),
                                 1.0,
                                 PeerMSR(),
                                 1.0,
                                 PoissonTOM(1.0),
                                 0.0,
                                 20.0,
                                 SIMPLE_TRACE,
                                 90.,
                                 0.0)

COMPLEX_EDGES = [SIMPLE_TRACE,
                 Line([Point(14.975, 15.0, 20.0),
                       Point(15.025, 15.0, 20.0)])]

COMPLEX_FAULT = ComplexFaultSource("CFLT000", "Complex Fault Source",
                                   "Active Shallow Crust",
                                   EvenlyDiscretizedMFD(7.0, 0.1, [1.0]),
                                   1.0,
                                   PeerMSR(),
                                   1.0,
                                   PoissonTOM(1.0),
                                   COMPLEX_EDGES,
                                   0.0)

SIMPLE_FAULT_SURFACE = SimpleFaultSurface.from_fault_data(SIMPLE_TRACE,
                                                          0.0,
                                                          20.0,
                                                          90.0,
                                                          1.0)

CHARACTERISTIC_FAULT = CharacteristicFaultSource(
    "CHRFLT000",
    "Characteristic 000",
    "Active Shallow Crust",
    EvenlyDiscretizedMFD(7.0, 0.1, [1.0]),
    PoissonTOM(1.0),
    SIMPLE_FAULT_SURFACE,
    0.0)


class RateGridTestCase(unittest.TestCase):
    """
    General test class for Rate Grid calculation
    """
    def setUp(self):
        """
        Set up limits
        """
        self.limits = [14.9, 15.1, 0.1, 14.9, 15.1, 0.1, 0., 20., 10.]

    def test_instantiation(self):
        """
        Tests a simple instantiation with one area source
        """
        rate_grid1 = RateGrid(self.limits, [AREA_SOURCE],
                              area_discretisation=4.0)
        np.testing.assert_array_almost_equal(rate_grid1.xlim,
                                             np.array([14.9, 15.0, 15.1]))
        np.testing.assert_array_almost_equal(rate_grid1.ylim,
                                             np.array([14.9, 15.0, 15.1]))
        np.testing.assert_array_almost_equal(rate_grid1.zlim,
                                             np.array([0., 10., 20.]))
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             np.zeros([2, 2, 2]))

    def test_number_sources(self):
        """
        Checks the correct number of sources
        """
        rate_grid1 = RateGrid(self.limits, [POINT_SOURCE, AREA_SOURCE],
                              area_discretisation=4.0)
        self.assertEqual(rate_grid1.number_sources(), 2)

    def test_point_location_easy(self):
        """
        Checks the correct identifier of the point location for the
        cases that the point is not on the border
        """
        rate_grid1 = RateGrid(self.limits, [POINT_SOURCE],
                              area_discretisation=4.0)
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(14.95, 14.95)),
            (0, 0))
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(14.95, 15.05)),
            (0, 1))
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(15.05, 14.95)),
            (1, 0))
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(15.05, 15.05)),
            (1, 1))

    def test_point_location_outside(self):
        """
        Checks that when the point is outside the box then (None, None) is
        returned
        """
        # Outside longitude box
        rate_grid1 = RateGrid(self.limits, [POINT_SOURCE],
                              area_discretisation=4.0)
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(14.85, 14.95)),
            (None, None))
        # Outside latitude box
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(14.95, 15.25)),
            (None, None))

    def test_point_location_border(self):
        """
        Checks the correct identifier of the point location for the
        cases that the point is not on the border
        """
        rate_grid1 = RateGrid(self.limits, [POINT_SOURCE],
                              area_discretisation=4.0)
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(14.9, 14.9)),
            (0, 0))
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(14.9, 15.0)),
            (0, 1))
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(15.0, 14.9)),
            (1, 0))
        self.assertTupleEqual(
            rate_grid1._get_point_location(Point(15.0, 15.0)),
            (1, 1))

    def test_point_rate_simple(self):
        """
        Tests the point rates when the point is inside the limits
        """
        rate_grid1 = RateGrid(self.limits, [POINT_SOURCE],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        expected_rates[1, 1, 0] = 1.0
        rate_grid1.get_rates(5.0)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates)
        # Tests the case when Mmin is outside the magnitude range
        rate_grid2 = RateGrid(self.limits, [POINT_SOURCE],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        rate_grid2.get_rates(6.0)
        np.testing.assert_array_almost_equal(rate_grid2.rates,
                                             expected_rates)
        # Tests the case when Mmax is set below the rate of the source
        rate_grid3 = RateGrid(self.limits, [POINT_SOURCE],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        rate_grid3.get_rates(4.0, 4.5)
        np.testing.assert_array_almost_equal(rate_grid3.rates,
                                             expected_rates)

    def test_point_rate_out_of_limits(self):
        """
        Tests the point rates when the point is outside the limits
        """
        rate_grid1 = RateGrid(self.limits, [OUTSIDE_POINT_SOURCE],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        rate_grid1.get_rates(5.0)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates)

    def test_area_rate(self):
        """
        Tests the area rates
        """
        rate_grid1 = RateGrid(self.limits, [AREA_SOURCE],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        expected_rates[:, 0, :] = 1.0 / 12.0
        expected_rates[:, 1, :] = 2.0 / 12.0
        rate_grid1.get_rates(5.0)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates)

    def test_simple_fault_rate(self):
        """
        Tests the simple fault rates
        """
        rate_grid1 = RateGrid(self.limits, [SIMPLE_FAULT],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        expected_rates[:, :, 0] = np.array([[10., 20.],
                                            [0., 30.]])
        expected_rates[:, :, 1] = np.array([[11., 22.],
                                            [0., 33.]])
        rate_grid1.get_rates(6.0)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates / 126.0)

    def test_simple_fault_rate_out_of_magnitude_range(self):
        """
        Tests the simple fault rates out of the magnitude range
        """
        rate_grid1 = RateGrid(self.limits, [SIMPLE_FAULT],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        rate_grid1.get_rates(6.0, 6.5)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates)

    def test_complex_fault_rate(self):
        """
        Tests the simple fault rates
        """
        rate_grid1 = RateGrid(self.limits, [COMPLEX_FAULT],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        expected_rates[:, :, 0] = np.array([[9., 21.],
                                            [0., 30.]])
        expected_rates[:, :, 1] = np.array([[11., 22.],
                                            [0., 33.]])
        rate_grid1.get_rates(6.0)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates / 126.0)

    def test_characteristic_fault_rate(self):
        """
        Tests the simple fault rates
        """
        rate_grid1 = RateGrid(self.limits, [CHARACTERISTIC_FAULT],
                              area_discretisation=4.0)
        expected_rates = np.zeros([2, 2, 2])
        expected_rates[:, :, 0] = np.array([[10., 20.],
                                            [0., 30.]])
        expected_rates[:, :, 1] = np.array([[11., 22.],
                                            [0., 33.]])
        rate_grid1.get_rates(6.0)
        np.testing.assert_array_almost_equal(rate_grid1.rates,
                                             expected_rates / 126.0)


class Dummy(object):
    """
    Dummy class to check coverage of non-supported source type
    """
    def __init__(self, name):
        """
        """
        self.name = name


class RateGridFromFilesTestCase(unittest.TestCase):
    """
    Tests to ensure that the same source models give the same rates if
    input from a source list or a file
    """
    def setUp(self):
        """
        """
        self.limits = [14.9, 15.1, 0.1, 14.9, 15.1, 0.1, 0., 20., 10.]

    def test_source_input_equivalence(self):
        """
        Verify that the same source model gives the same rate grid results
        when input as a source model or as an xml
        """
        ratemodel1 = RateGrid(self.limits,
                              [POINT_SOURCE,
                               AREA_SOURCE,
                               SIMPLE_FAULT,
                               COMPLEX_FAULT,
                               CHARACTERISTIC_FAULT,
                               Dummy("Rubbish")],
                              area_discretisation=4.0)
        ratemodel2 = RateGrid.from_model_files(self.limits,
                                               SOURCE_MODEL_FILE,
                                               complex_mesh_spacing=1.0,
                                               area_discretisation=4.0)
        ratemodel1.get_rates(5.0)
        ratemodel2.get_rates(5.0)
        np.testing.assert_array_almost_equal(ratemodel1.rates,
                                             ratemodel2.rates)

class RatePolygonTestCase(unittest.TestCase):
    """
    Tests of the Rate polygon tool
    """
    def setUp(self):
        """
        """
        self.limits = {}

    def test_instantiation(self):
        """
        Tests simple instantiation of the class
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 10.0}
        model1 = RatePolygon(self.limits, [POINT_SOURCE],
                             area_discretisation=4.0)
        self.assertAlmostEqual(model1.upper_depth, 0.0)
        self.assertAlmostEqual(model1.lower_depth, 10.0)
        self.assertAlmostEqual(model1.rates, 0.0)

    def test_point_source_good(self):
        """
        Tests the case of a single point source inside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 10.0}
        model1 = RatePolygon(self.limits, [POINT_SOURCE],
                             area_discretisation=4.0)
        model1.get_rates(5.0)
        self.assertAlmostEqual(model1.rates, 1.0)

    def test_point_source_outside_polygon(self):
        """
        Tests the case of a single point source outside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.0),
                                           Point(15.0, 15.0),
                                           Point(15.0, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 10.0}
        model1 = RatePolygon(self.limits, [POINT_SOURCE],
                             area_discretisation=4.0)
        model1.get_rates(5.0)
        self.assertAlmostEqual(model1.rates, 0.0)

    def test_point_source_outside_depth_limit(self):
        """
        Tests the case of a single point source outside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 3.0}
        model1 = RatePolygon(self.limits, [POINT_SOURCE],
                             area_discretisation=4.0)
        model1.get_rates(5.0)
        self.assertAlmostEqual(model1.rates, 0.0)

    def test_point_source_outside_mag_limit(self):
        """
        Tests the case of a single point source outside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 3.0}
        model1 = RatePolygon(self.limits, [POINT_SOURCE],
                             area_discretisation=4.0)
        model1.get_rates(5.5, 6.0)
        self.assertAlmostEqual(model1.rates, 0.0)

    def test_fault_source_full_polygon(self):
        """
        Tests the rates when the whole fault is inside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 20.0}
        model1 = RatePolygon(self.limits, [SIMPLE_FAULT],
                             area_discretisation=4.0)
        model1.get_rates(7.0)
        self.assertAlmostEqual(model1.rates, 1.0)

    def test_fault_source_partial_polygon(self):
        """
        Tests the rates when the whole fault is partially inside the polygon
        """
        self.limits = {"polygon": Polygon([Point(15.0, 14.9),
                                           Point(15.0, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 20.0}
        model1 = RatePolygon(self.limits, [SIMPLE_FAULT],
                             area_discretisation=4.0)
        model1.get_rates(7.0)
        self.assertAlmostEqual(model1.rates, 0.5)

    def test_fault_source_outside_mag_range(self):
        """
        Tests the rates when the whole fault is inside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 0.0,
                       "lower_depth": 20.0}
        model1 = RatePolygon(self.limits, [SIMPLE_FAULT],
                             area_discretisation=4.0)
        model1.get_rates(6.5, 6.8)
        self.assertAlmostEqual(model1.rates, 0.0)

    def test_fault_source_outside_depth_range(self):
        """
        Tests the rates when the whole fault is inside the polygon
        """
        self.limits = {"polygon": Polygon([Point(14.9, 14.9),
                                           Point(14.9, 15.1),
                                           Point(15.1, 15.1),
                                           Point(15.1, 14.9)]),
                       "upper_depth": 21.0,
                       "lower_depth": 25.0}
        model1 = RatePolygon(self.limits, [SIMPLE_FAULT],
                             area_discretisation=4.0)
        model1.get_rates(7.0)
        self.assertAlmostEqual(model1.rates, 0.0)
