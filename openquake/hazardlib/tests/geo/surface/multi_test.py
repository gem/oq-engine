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
    """
    Test multiplanar surfaces used in UCERF
    """
    def test(self):
        mesh = Mesh(numpy.array([-118.]), numpy.array([33]))
        surf18 = MultiSurface.from_csv(cd / 'msurface18.csv')  # 2 planes
        surf19 = MultiSurface.from_csv(cd / 'msurface19.csv')  # 2 planes
        surf20 = MultiSurface.from_csv(cd / 'msurface20.csv')  # 1 plane
        surf_a = MultiSurface(surf18.surfaces + surf19.surfaces)
        surf_b = MultiSurface(surf19.surfaces + surf20.surfaces)
        rx18 = surf18.get_rx_distance(mesh)
        aac(rx18, 51.610675)
        rx19 = surf19.get_rx_distance(mesh)
        aac(rx19, 54.441119)
        rx20 = surf20.get_rx_distance(mesh)
        aac(rx20, -60.205692)
        rxa = surf_a.get_rx_distance(mesh)
        aac(rxa, 53.034889)
        rxb = surf_b.get_rx_distance(mesh)
        aac(rxb, -56.064366)
