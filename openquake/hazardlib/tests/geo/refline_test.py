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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Tests for the multi-section PFD reference-line builders (``ecs``/``lcp``/
``segments``).

The expected values are pinned from the oq-pfdha reference implementations
(``openquake.fdha.calc.utils.{ecs,lcp,segments}``); they are hardcoded so
that the engine test suite does not import ``openquake.fdha``, which lives
in a separate repository. The engine port reproduces them exactly (the
assertions here use a small tolerance only to absorb platform ULP noise).
"""
import unittest

import numpy
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.refline import (
    ecs_from_traces, lcp_from_traces, reference_line, SegmentsResult)


def kite_traces():
    """Two en-echelon kite surfaces sharing the pfd_distances fixture."""

    def kite(x0, y0):
        prfs = [
            Line([Point(x0, y0, 0), Point(x0, y0 - 1e-5, 20.)]),
            Line([Point(x0 + 0.15, y0, 0),
                  Point(x0 + 0.15, y0 - 1e-5, 20.)]),
            Line([Point(x0 + 0.3, y0, 0),
                  Point(x0 + 0.3, y0 - 1e-5, 20.)])]
        return KiteSurface.from_profiles(prfs, 1., 1.)

    msrf = MultiSurface([kite(0.0, 0.0), kite(0.5, 0.1)])
    return [(ln.coo[:, 0], ln.coo[:, 1]) for ln in msrf.tor.lines]


MESH = Mesh(numpy.array([0.1, 0.4, 0.65, 0.9, 0.8]),
            numpy.array([0.0, 0.05, 0.1, 0.0, 0.1]))


class ReferenceLineTestCase(unittest.TestCase):

    def test_ecs(self):
        ref = ecs_from_traces(kite_traces())
        x_l, l_km = ref.x_l(MESH.lons, MESH.lats)
        numpy.testing.assert_allclose(
            x_l, [0.8789292029, 0.4983941870, 0.1790717237, 0.0, 0.0],
            atol=1e-9)
        self.assertAlmostEqual(l_km, 91.9, places=4)
        numpy.testing.assert_allclose(
            ref.r_km(MESH.lons, MESH.lats),
            [1.5482499766, 0.0880428127, 1.9717977145, 15.9806543736,
             0.3582657086], atol=1e-9)

    def test_lcp(self):
        ref = lcp_from_traces(kite_traces())
        x_l, l_km = ref.x_l(MESH.lons, MESH.lats)
        numpy.testing.assert_allclose(
            x_l, [0.8795228900, 0.4988249503, 0.1744382946, 0.0, 0.0],
            atol=1e-9)
        self.assertAlmostEqual(l_km, 93.2563491861, places=6)
        numpy.testing.assert_allclose(
            ref.r_km(MESH.lons, MESH.lats),
            [0.0639322868, 4.3167229726, 0.0012335676, 16.0215407669,
             0.4128290742], atol=1e-9)

    def test_segments(self):
        ref = SegmentsResult(kite_traces())
        x_l, l_km = ref.x_l(MESH.lons, MESH.lats)
        numpy.testing.assert_allclose(
            x_l, [0.12550563, 0.50202274, 0.81578696, 1.0, 1.0],
            atol=1e-6)
        self.assertAlmostEqual(l_km, 88.5974272728, places=6)
        numpy.testing.assert_allclose(
            ref.r_km(MESH.lons, MESH.lats),
            [0.0, 12.4319540106, 3.7692091091e-05, 15.9805618582,
             0.3583854216], atol=1e-9)

    def test_factory(self):
        for method in ('segments', 'ecs', 'lcp'):
            ref = reference_line(kite_traces(), method)
            x_l, l_km = ref.x_l(MESH.lons, MESH.lats)
            self.assertEqual(x_l.shape, (5,))
            self.assertGreater(l_km, 0.0)
        with self.assertRaises(ValueError):
            reference_line(kite_traces(), 'unknown')


if __name__ == '__main__':
    unittest.main()
