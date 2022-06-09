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
import os
import pathlib
import unittest
import numpy
import matplotlib.pyplot as plt
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.tests.geo.line_test import get_mesh, plot_pattern
from openquake.hazardlib.tests.geo.surface.kite_fault_test import plot_mesh_2d

cd = pathlib.Path(__file__).parent
aac = numpy.testing.assert_allclose
aae = numpy.testing.assert_almost_equal

PLOTTING = False


class GetTorTestCase(unittest.TestCase):
    """
    Tests the extraction of the traces of the sections composing a rupture
    """

    def test_planar_tor01(self):
        """ Planar rupture """
        tmp = os.path.join(cd, 'data', 'msurface18.csv')
        surf = MultiSurface.from_csv(tmp)
        surf._set_tor()

        # Expected value inferred from the input file
        expected = numpy.array([[-117.955505, 33.769615],
                                [-117.9903, 33.797646]])
        aae(expected, surf.tors.lines[0].coo)
        expected = numpy.array([[-117.9903, 33.797646],
                                [-117.99624, 33.802425]])
        aae(expected, surf.tors.lines[1].coo)


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
        tmp = os.path.join('data', 'msurface18.csv')
        surf18 = MultiSurface.from_csv(cd / tmp)  # 2 planes
        tmp = os.path.join('data', 'msurface19.csv')
        surf19 = MultiSurface.from_csv(cd / tmp)  # 2 planes
        tmp = os.path.join('data', 'msurface20.csv')
        surf20 = MultiSurface.from_csv(cd / tmp)  # 1 plane
        rjb18 = surf18.get_joyner_boore_distance(mesh)[0]
        rjb19 = surf19.get_joyner_boore_distance(mesh)[0]
        rjb20 = surf20.get_joyner_boore_distance(mesh)[0]
        aac([rjb18, rjb19, rjb20], [85.676294, 89.225542, 92.937021])
        surfa = MultiSurface(surf18.surfaces + surf19.surfaces)
        surfb = MultiSurface(surf19.surfaces + surf20.surfaces)
        rjba = surfa.get_joyner_boore_distance(mesh)[0]
        rjbb = surfb.get_joyner_boore_distance(mesh)[0]

        # Test
        aac([rjba, rjbb], [85.676294, 89.225542])

    def test_rx(self):
        meshtest = Mesh(numpy.array([-118.]), numpy.array([33]))  # 1 point
        tmp = os.path.join('data', 'msurface18.csv')
        surf18 = MultiSurface.from_csv(cd / tmp)  # 2 planes
        tmp = os.path.join('data', 'msurface19.csv')
        surf19 = MultiSurface.from_csv(cd / tmp)  # 2 planes
        tmp = os.path.join('data', 'msurface20.csv')
        surf20 = MultiSurface.from_csv(cd / tmp)  # 1 plane
        rx18 = surf18.get_rx_distance(meshtest)[0]
        rx19 = surf19.get_rx_distance(meshtest)[0]
        rx20 = surf20.get_rx_distance(meshtest)[0]

        # Plotting
        if PLOTTING:

            # Creating the mesh
            mesh, mlons, mlats = get_mesh(-118.5, -117.5, 33.0, 34., 0.005)

            # Plots
            rx = surf18.get_rx_distance(mesh)
            _ = _plotting(surf18, rx, mlons, mlats, label='Rx - surf18')
            plt.show()

            rx = surf19.get_rx_distance(mesh)
            _ = _plotting(surf19, rx, mlons, mlats, label='Rx - surf19')
            plt.show()

            rx = surf20.get_rx_distance(mesh)
            _ = _plotting(surf20, rx, mlons, mlats, label='Rx - surf20')
            plt.show()

        # Test first set of surfaces
        aac([rx18, rx19, rx20], [-64.328038, -64.288793, -60.205692])

        # Create surfaces and compute Rx
        surfa = MultiSurface(surf18.surfaces + surf19.surfaces)
        surfb = MultiSurface(surf19.surfaces + surf20.surfaces)
        rxa = surfa.get_rx_distance(meshtest)[0]
        rxb = surfb.get_rx_distance(meshtest)[0]

        # Plotting
        if PLOTTING:
            mesh, mlons, mlats = get_mesh(-118.5, -117.5, 33.0, 34., 0.005)
            rx = surfa.get_rx_distance(mesh)
            _ = _plotting(surfa, rx, mlons, mlats, label='Rx - surfa')
            plt.show()

            rx = surfb.get_rx_distance(mesh)
            _ = _plotting(surfb, rx, mlons, mlats, label='Rx - surfb')
            plt.show()

        # Test second set of surfaces
        aac([rxa, rxb], [-64.309214, -62.332508], rtol=1e-5)

    def test_rx_ry0_kite(self):

        # Define the surface that is a plane dipping towards north
        spc = 2.0
        pro1 = Line([Point(0.2, 0.0, 0.0), Point(0.2, 0.05, 15.0)])
        pro2 = Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.05, 15.0)])
        sfc1 = KiteSurface.from_profiles([pro1, pro2], spc, spc)
        msurf = MultiSurface([sfc1])

        # Define the mesh of sites
        pcoo = numpy.array([[0.2, 0.1], [0.0, -0.1]])
        mesh = Mesh(pcoo[:, 0], pcoo[:, 1])

        # Compute expected distances
        lo = pro1.points[0].longitude
        la = pro1.points[0].longitude
        tmp0 = geodetic_distance(lo, la, pcoo[0, 0], pcoo[0, 1])
        lo = pro2.points[0].longitude
        la = pro2.points[0].longitude
        tmp1 = geodetic_distance(lo, la, pcoo[1, 0], pcoo[1, 1])

        # Checking Rx
        rx = msurf.get_rx_distance(mesh)
        expected = numpy.array([tmp0, -tmp1])
        computed = numpy.squeeze(rx)
        numpy.testing.assert_almost_equal(expected, computed, decimal=5)

        # Checking Ry0
        expected = numpy.array([0.0, tmp1])
        ry0 = msurf.get_ry0_distance(mesh)

        # Plotting
        if PLOTTING:
            mesh, mlons, mlats = get_mesh(-0.2, 0.4, -0.2, 0.2, 0.0025)
            rx = msurf.get_rx_distance(mesh)
            ax = _plotting(msurf, rx, mlons, mlats, label='Rx - Kite')
            ax.plot(pcoo[:, 0], pcoo[:, 1], 'o')
            for srf in msurf.surfaces:
                plot_mesh_2d(ax, srf)
            plt.show()

            ry0 = msurf.get_ry0_distance(mesh)
            ax = _plotting(msurf, ry0, mlons, mlats, label='Ry0 - Kite')
            ax.plot(pcoo[:, 0], pcoo[:, 1], 'o')
            for srf in msurf.surfaces:
                plot_mesh_2d(ax, srf)
            plt.show()


def _plotting(surf, dst, mlons, mlats, lons=[], lats=[], label=''):
    """
    Plots mesh and surface
    """
    num = 10
    ax = plot_pattern(lons, lats, numpy.reshape(dst, mlons.shape),
                      mlons, mlats, label, num, show=False)
    lons = surf.surfaces[0].mesh.lons
    lats = surf.surfaces[0].mesh.lats
    for line in surf.tors.lines:
        ax.plot(line.coo[:, 0], line.coo[:, 1], '-r')
        ax.plot(line.coo[0, 0], line.coo[0, 1], 'g', marker="$s$", ms=5)
        ax.plot(line.coo[-1, 0], line.coo[-1, 1], 'r', marker="$e$",
                mfc='none', ms=8)
    return ax
