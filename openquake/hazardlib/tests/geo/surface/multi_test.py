# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import pathlib
import unittest
import numpy
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.multi import MultiSurface

cd = pathlib.Path(__file__).parent
aac = numpy.testing.assert_allclose


class MultiSurfaceTestCase(unittest.TestCase):
    # Test multiplanar surfaces used in UCERF, which are build from
    # pre-exiting multisurfaces. In this test there are 3 original
    # multisurfaces (from sections 18, 19, 20) and a reference point;
    # the rjb distances are 51.610675, 54.441119, -60.205692 respectively;
    # then two multisurfaces are built (a from 18+19, b from 19+20)
    # and distances recomputed; as expected for the rjb distances one gets
    # rjb(18+19) = min(rjb(18), rjb(19)) and same for 19+20.
    # This is NOT true for rx distances.

    def test_rjb(self):
        mesh = Mesh(numpy.array([-118.]), numpy.array([33]))   # 1 point
        surf18 = MultiSurface.from_csv(cd / 'msurface18.csv')  # 2 planes
        surf19 = MultiSurface.from_csv(cd / 'msurface19.csv')  # 2 planes
        surf20 = MultiSurface.from_csv(cd / 'msurface20.csv')  # 1 plane
        rjb18 = surf18.get_joyner_boore_distance(mesh)[0]
        rjb19 = surf19.get_joyner_boore_distance(mesh)[0]
        rjb20 = surf20.get_joyner_boore_distance(mesh)[0]
        aac([rjb18, rjb19, rjb20], [85.676294, 89.225542, 92.937021])

        surfa = MultiSurface(surf18.surfaces + surf19.surfaces)
        surfb = MultiSurface(surf19.surfaces + surf20.surfaces)
        rjba = surfa.get_joyner_boore_distance(mesh)[0]
        rjbb = surfb.get_joyner_boore_distance(mesh)[0]
        aac([rjba, rjbb], [85.676294, 89.225542])

    def test_rx(self):
        mesh = Mesh(numpy.array([-118.]), numpy.array([33]))   # 1 point
        surf18 = MultiSurface.from_csv(cd / 'msurface18.csv')  # 2 planes
        surf19 = MultiSurface.from_csv(cd / 'msurface19.csv')  # 2 planes
        surf20 = MultiSurface.from_csv(cd / 'msurface20.csv')  # 1 plane
        rx18 = surf18.get_rx_distance(mesh)[0]
        rx19 = surf19.get_rx_distance(mesh)[0]
        rx20 = surf20.get_rx_distance(mesh)[0]
        aac([rx18, rx19, rx20], [51.610675, 54.441119, -60.205692])

        surfa = MultiSurface(surf18.surfaces + surf19.surfaces)
        surfb = MultiSurface(surf19.surfaces + surf20.surfaces)
        rxa = surfa.get_rx_distance(mesh)[0]
        rxb = surfb.get_rx_distance(mesh)[0]
        aac([rxa, rxb], [53.034889, -56.064366])
