# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Tests for the FDHA distance metrics added to hazardlib:

- ``rtor``: horizontal distance to the top rupture trace
- ``x_l``:  normalized along-strike position (x/L)
- ``length``: top-trace length as a rupture parameter

Values are pinned against the oq-pfdha reference calculator
(``openquake.fdha.calc.utils.rupture_distance``); the two implementations
agree to sub-metre level on the shared Norcia trace.
"""
import unittest
import numpy
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.calc.filters import get_dparam, get_distances
from openquake.hazardlib.contexts import KNOWN_DISTANCES, ContextMaker
from openquake.hazardlib.contexts import RuptureContext

# Norcia MVFS trace (same as GetXLRatioTestCase)
NORCIA = Line([
    Point(13.1015, 43.0131), Point(13.1332, 42.9931),
    Point(13.1523, 42.9766), Point(13.1685, 42.9544),
    Point(13.1627, 42.9394), Point(13.1750, 42.9201),
    Point(13.1970, 42.9097), Point(13.2264, 42.8846),
    Point(13.2476, 42.8449), Point(13.2482, 42.8211),
    Point(13.2616, 42.8094), Point(13.2725, 42.7865),
    Point(13.2813, 42.7550)])


def norcia_surface():
    return SimpleFaultSurface.from_fault_data(
        NORCIA, upper_seismogenic_depth=0.0,
        lower_seismogenic_depth=11.0, dip=47.0, mesh_spacing=1.0)


def straight_surface():
    trace = Line([Point(0.0, 0.0), Point(0.0, 1.0)])
    return SimpleFaultSurface.from_fault_data(
        trace, upper_seismogenic_depth=0.0,
        lower_seismogenic_depth=10.0, dip=90.0, mesh_spacing=0.5)


class RtorAndXlTestCase(unittest.TestCase):

    def test_norcia_values(self):
        surf = norcia_surface()
        mesh = Mesh(numpy.array([13.278, 13.20, 13.30]),
                    numpy.array([42.767, 42.95, 42.80]))
        # pinned from the oq-pfdha RuptureDistanceCalculator
        numpy.testing.assert_allclose(
            surf.get_rtor(mesh), [0.00410271, 2.69367832, 2.61320799],
            atol=1e-3)
        x_l, L = surf.get_x_l_ratio(mesh)
        numpy.testing.assert_allclose(
            x_l, [0.94855032, 0.26470584, 0.86349514], atol=1e-4)
        self.assertAlmostEqual(L, 34.0, delta=0.05)
        self.assertAlmostEqual(surf.get_tor_length(), L, places=6)

    def test_off_end_clamps_and_distances_to_endpoint(self):
        surf = straight_surface()
        mesh = Mesh(numpy.array([0.1]), numpy.array([1.5]))
        rtor = surf.get_rtor(mesh)
        x_l, _L = surf.get_x_l_ratio(mesh)
        self.assertAlmostEqual(float(x_l[0]), 1.0, places=6)
        # beyond the trace end the distance is to the endpoint, measured in
        # the local OrthographicProjection frame (~0.3% from the geodesic
        # distance at 56 km, so a 0.5 km tolerance)
        from openquake.hazardlib.geo import geodetic
        expected = geodetic.geodetic_distance(0.0, 1.0, 0.1, 1.5)
        self.assertAlmostEqual(float(rtor[0]), float(expected), delta=0.5)

    def test_on_trace_zero_distance(self):
        surf = straight_surface()
        mesh = Mesh(numpy.array([0.0]), numpy.array([0.5]))
        self.assertAlmostEqual(float(surf.get_rtor(mesh)[0]), 0.0, places=6)
        x_l, _L = surf.get_x_l_ratio(mesh)
        self.assertAlmostEqual(float(x_l[0]), 0.5, delta=1e-3)

    def test_rtor_is_shared_with_x_l_sweep(self):
        # both come from the same _get_tor_metrics sweep
        surf = straight_surface()
        mesh = Mesh(numpy.array([0.1]), numpy.array([0.5]))
        rtor, x_l, l_km = surf._get_tor_metrics(mesh)
        numpy.testing.assert_array_equal(rtor, surf.get_rtor(mesh))
        numpy.testing.assert_array_equal(x_l, surf.get_x_l_ratio(mesh)[0])
        self.assertEqual(l_km, surf.get_tor_length())


class FDHAKnownDistancesTestCase(unittest.TestCase):

    def test_known_distances_contains_metrics(self):
        self.assertIn('rtor', KNOWN_DISTANCES)
        self.assertIn('x_l', KNOWN_DISTANCES)

    def test_length_is_a_rupture_parameter_slot(self):
        self.assertIn('length', RuptureContext._slots_)


class DispatchTestCase(unittest.TestCase):

    def _fake_rup(self, surface):
        class Rup(object):
            pass
        rup = Rup()
        rup.surface = surface
        return rup

    def test_get_distances_rtor_x_l(self):
        surf = straight_surface()
        mesh = Mesh(numpy.array([0.1, 0.2]), numpy.array([0.5, 0.6]))
        rup = self._fake_rup(surf)
        numpy.testing.assert_array_equal(
            get_distances(rup, mesh, 'rtor'), surf.get_rtor(mesh))
        numpy.testing.assert_array_equal(
            get_distances(rup, mesh, 'x_l'),
            surf.get_x_l_ratio(mesh)[0])
        numpy.testing.assert_array_equal(
            get_dparam(surf, mesh, 'rtor'), surf.get_rtor(mesh))
        numpy.testing.assert_array_equal(
            get_dparam(surf, mesh, 'x_l'), surf.get_x_l_ratio(mesh)[0])

    def test_point_rupture_rejected(self):
        mesh = Mesh(numpy.array([0.1]), numpy.array([0.5]))
        rup = self._fake_rup(None)
        with self.assertRaises(ValueError):
            get_distances(rup, mesh, 'rtor')
        with self.assertRaises(ValueError):
            get_distances(rup, mesh, 'x_l')

    def test_get_rparams_length(self):
        surf = straight_surface()
        cm = ContextMaker.__new__(ContextMaker)
        cm.dparam = None
        cm.REQUIRES_RUPTURE_PARAMETERS = {'mag', 'length'}
        rup = self._fake_rup(surf)
        rup.mag = 7.0
        params = cm.get_rparams(rup)
        self.assertAlmostEqual(params['length'], surf.get_tor_length(),
                               places=6)


if __name__ == '__main__':
    unittest.main()
