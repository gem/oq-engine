# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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

from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hazardlib.geo import Point, Mesh
from openquake.hazardlib.geo.surface import PlanarSurface
from openquake.hazardlib.tom import PoissonTOM

from openquake.hazardlib.tests import assert_pickleable


class _BaseFaultSourceTestCase(unittest.TestCase):
    SOURCE_ID = NAME = 'test-source'
    TRT = 'Active Shallow Crust'
    STRIKE = 0.0
    DIP = 90.0
    RAKE = 0
    MIN_MAG = 5.0
    BIN_WIDTH = 0.1
    RATES = [0.3, 0.2, 0.1]
    CORNER_LONS = numpy.array([-1., 1., -1., 1.])
    CORNER_LATS = numpy.array([0., 0., 0., 0.])
    CORNER_DEPTHS = numpy.array([0., 0., 10., 10.])
    MESH_SPACING = 1.0
    TOM = PoissonTOM(50.0)

    def _make_source(self):
        points = [Point(lon, lat, depth) for lon, lat, depth in
                  zip(self.CORNER_LONS, self.CORNER_LATS, self.CORNER_DEPTHS)]
        source = CharacteristicFaultSource(
            source_id=self.SOURCE_ID,
            name=self.NAME,
            tectonic_region_type=self.TRT,
            mfd=EvenlyDiscretizedMFD(self.MIN_MAG, self.BIN_WIDTH, self.RATES),
            temporal_occurrence_model=self.TOM,
            surface=PlanarSurface(self.MESH_SPACING, self.STRIKE, self.DIP,
                                  points[0], points[1], points[3], points[2]),
            rake=self.RAKE
        )
        assert_pickleable(source)
        return source


class CharacteristicFaultSourceGetRuptureEnclosingPolygon(
        _BaseFaultSourceTestCase):

    def test(self):
        # relies on mesh.get_convex_hull() and polygon.dilate
        source = self._make_source()
        poly = source.get_rupture_enclosing_polygon(dilation=5.0)

        mesh = Mesh(numpy.array([[-1., 1.], [-1., 1.]]),
                    numpy.array([[0., 0.], [0., 0.]]),
                    numpy.array([[0., 0.], [10., 10.]]))

        numpy.testing.assert_equal(
            poly.lons, mesh.get_convex_hull().dilate(5.0).lons
        )
        numpy.testing.assert_equal(
            poly.lats, mesh.get_convex_hull().dilate(5.0).lats
        )


class CharacteristicFaultSourceIterRuptures(_BaseFaultSourceTestCase):

    def test(self):
        source = self._make_source()
        ruptures = [rup for rup in source.iter_ruptures()]

        self.assertTrue(len(ruptures) == source.count_ruptures())

        self.assertTrue(ruptures[0].mag == 5.0)
        self.assertTrue(ruptures[1].mag == 5.1)
        self.assertTrue(ruptures[2].mag == 5.2)

        for i in range(3):
            self.assertTrue(ruptures[i].rake == self.RAKE)
            self.assertTrue(ruptures[i].tectonic_region_type == self.TRT)
            self.assertTrue(ruptures[i].hypocenter == Point(0., 0., 5.))
            self.assertTrue(
                ruptures[i].surface.mesh_spacing == self.MESH_SPACING
            )
            self.assertTrue(ruptures[i].surface.strike == self.STRIKE)
            self.assertTrue(ruptures[i].surface.dip == self.DIP)
            self.assertTrue(
                ruptures[i].source_typology == CharacteristicFaultSource
            )
            numpy.testing.assert_equal(ruptures[i].surface.corner_lons,
                                       self.CORNER_LONS)
            numpy.testing.assert_equal(ruptures[i].surface.corner_lats,
                                       self.CORNER_LATS)
            numpy.testing.assert_equal(ruptures[i].surface.corner_depths,
                                       self.CORNER_DEPTHS)
            self.assertTrue(ruptures[i].occurrence_rate == self.RATES[i])
            self.assertTrue(ruptures[i].temporal_occurrence_model == self.TOM)


class ModifyCharacteristicFaultSurfaceTestCase(_BaseFaultSourceTestCase):

    def setUp(self):
        self.fault = self._make_source()

    def test_modify_set_geometry(self):
        new_corner_lons = numpy.array([-1.1, 1.1, -1.1, 1.1])
        new_corner_lats = numpy.array([0., 0., 0., 0.])
        new_corner_depths = numpy.array([0., 0., 15., 15.])
        points = [Point(lon, lat, depth) for lon, lat, depth in
                  zip(new_corner_lons, new_corner_lats, new_corner_depths)]
        new_surface = PlanarSurface(self.MESH_SPACING, self.STRIKE, self.DIP,
                                    points[0], points[1], points[3], points[2])
        self.fault.modify_set_geometry(new_surface, "XYZ")
        self.assertEqual(self.fault.surface_node, "XYZ")
        numpy.testing.assert_array_almost_equal(self.fault.surface.corner_lons,
                                                new_corner_lons)
        numpy.testing.assert_array_almost_equal(self.fault.surface.corner_lats,
                                                new_corner_lats)
        numpy.testing.assert_array_almost_equal(
            self.fault.surface.corner_depths,
            new_corner_depths)
