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
import unittest
import numpy as np
import matplotlib.pyplot as plt
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.geo.geodetic import geodetic_distance, npoints_towards
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.tests.geo.surface.kite_fault_test import (
    _read_profiles)
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.surface.kite_fault import KiteSurface

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
PLOTTING = False

aae = np.testing.assert_almost_equal


class MultiSurfaceOneTestCase(unittest.TestCase):

    def setUp(self):
        # First surface - Almost vertical dipping to south
        prf1 = Line([Point(0, 0, 0), Point(0, -0.00001, 20.)])
        prf2 = Line([Point(0.15, 0, 0), Point(0.15, -0.00001, 20.)])
        prf3 = Line([Point(0.3, 0, 0), Point(0.3, -0.00001, 20.)])
        sfca = KiteSurface.from_profiles([prf1, prf2, prf3], 1., 1.)
        self.msrf = MultiSurface([sfca])

    def test_get_width(self):
        # Surface is almost vertical. The width must be equal to the depth
        # difference between the points at the top and bottom
        width = self.msrf.get_width()
        msg = 'Multi fault surface: width is wrong'
        self.assertAlmostEqual(20.0, width, places=2, msg=msg)

    def test_get_dip(self):
        # Surface is almost vertical. The dip must be equal to 90
        dip = self.msrf.get_dip()
        msg = 'Multi fault surface: dip is wrong'
        self.assertAlmostEqual(90.0, dip, places=2, msg=msg)

    def test_get_area(self):
        computed = self.msrf.get_area()
        length = geodetic_distance(0.0, 0.0, 0.3, 0.0)
        expected = length * 20.0
        perc_diff = abs(computed - expected) / computed * 100
        msg = 'Multi fault surface: area is wrong'
        self.assertTrue(perc_diff < 2, msg=msg)

    def test_get_area1(self):
        pntsa = npoints_towards(lon=0.32, lat=0.0, depth=0.0, azimuth=45,
                                hdist=10.0, vdist=0.0, npoints=2)
        pntsb = npoints_towards(lon=pntsa[0][1], lat=pntsa[1][1],
                                depth=pntsa[2][1], azimuth=45+90,
                                hdist=10.0, vdist=10.0, npoints=2)
        pntsc = npoints_towards(lon=0.32, lat=0.0, depth=0.0, azimuth=45+90,
                                hdist=10.0, vdist=10.0, npoints=2)
        tmp = Point(pntsc[0][1], pntsc[1][1], pntsc[2][1])
        prf3 = Line([Point(0.32, 0, 0), tmp])
        tmp1 = Point(pntsa[0][1], pntsa[1][1], pntsa[2][1])
        tmp2 = Point(pntsb[0][1], pntsb[1][1], pntsb[2][1])
        prf4 = Line([tmp1, tmp2])
        sfcb = KiteSurface.from_profiles([prf3, prf4], 0.2, 0.2)

        computed = sfcb.get_area()
        expected = 10.0 * 14.14
        msg = 'Multi fault surface: area is wrong'
        aae(expected, computed, decimal=-1, err_msg=msg)


class MultiSurfaceTwoTestCase(unittest.TestCase):

    def setUp(self):

        # First surface - Almost vertical dipping to south
        prf1 = Line([Point(0, 0, 0), Point(0, -0.00001, 20.)])
        prf2 = Line([Point(0.15, 0, 0), Point(0.15, -0.00001, 20.)])
        prf3 = Line([Point(0.3, 0, 0), Point(0.3, -0.00001, 20.)])
        sfca = KiteSurface.from_profiles([prf1, prf2, prf3], 1., 1.)

        # Second surface - Strike to NE and dip to SE
        pntsa = npoints_towards(lon=0.32, lat=0.0, depth=0.0, azimuth=45,
                                hdist=10.0, vdist=0.0, npoints=2)
        pntsb = npoints_towards(lon=pntsa[0][1], lat=pntsa[1][1],
                                depth=pntsa[2][1], azimuth=45+90,
                                hdist=10.0, vdist=10.0, npoints=2)
        pntsc = npoints_towards(lon=0.32, lat=0.0, depth=0.0, azimuth=45+90,
                                hdist=10.0, vdist=10.0, npoints=2)
        tmp = Point(pntsc[0][1], pntsc[1][1], pntsc[2][1])
        prf3 = Line([Point(0.32, 0, 0), tmp])
        tmp1 = Point(pntsa[0][1], pntsa[1][1], pntsa[2][1])
        tmp2 = Point(pntsb[0][1], pntsb[1][1], pntsb[2][1])
        prf4 = Line([tmp1, tmp2])
        sfcb = KiteSurface.from_profiles([prf3, prf4], 0.2, 0.2)

        # Create surface and mesh needed for the test
        self.msrf = MultiSurface([sfca, sfcb])
        self.coo = np.array([[-0.1, 0.0], [0.0, 0.1]])
        self.mesh = Mesh(self.coo[:, 0], self.coo[:, 1])

    def test_areas(self):
        """ Compute the areas of surfaces """
        length = geodetic_distance(0.0, 0.0, 0.3, 0.0)
        expected = np.array([length * 20.0, 10 * 14.14])
        computed = self.msrf._get_areas()
        msg = 'Multi fault surface: areas are wrong'
        np.testing.assert_almost_equal(expected, computed, err_msg=msg,
                                       decimal=-1)

    def test_width(self):
        """ Compute the width of a multifault surface with 2 sections"""
        computed = self.msrf.get_width()
        # The width of the first surface is about 20 km while the second one
        # is about 14 km. The total width is the weighted mean of the width of
        # each section (weight proportional to the area)
        smm = np.sum(self.msrf.areas)
        expected = (20.0*self.msrf.areas[0] + 14.14*self.msrf.areas[1]) / smm
        perc_diff = abs(computed - expected) / computed * 100
        msg = f'Multi fault surface: width is wrong. % diff {perc_diff}'
        self.assertTrue(perc_diff < 0.2, msg=msg)

    # TODO
    def test_rx(self):
        """  Compute Rx for a multifault surface with 2 sections """
        # Test Rx - Both must be negative. The Rx for the first surface is 0
        # while the Rx for the second one is
        expected = np.array([-3.416027, -13.276342])
        computed = self.msrf.get_rx_distance(self.mesh)
        #np.testing.assert_allclose(computed, expected)

    def test_get_area(self):
        computed = self.msrf.get_area()
        length = geodetic_distance(0.0, 0.0, 0.3, 0.0)
        expected = length * 20.0 + 100
        perc_diff = abs(computed - expected) / computed
        msg = 'Multi fault surface: area is wrong'
        self.assertTrue(perc_diff < 0.1, msg=msg)


class MultiSurfaceWithNaNsTestCase(unittest.TestCase):

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles08')

        hsmpl = 2
        vsmpl = 2
        idl = False
        alg = False

        # Read the profiles with prefix cs_50. These profiles dip toward
        # north
        prf, _ = _read_profiles(path, 'cs_50')
        srfc50 = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        # Read the profiles with prefix cs_52. These profiles dip toward
        # north. This section is west to the section defined by cs_50
        prf, _ = _read_profiles(path, 'cs_51')
        srfc51 = KiteSurface.from_profiles(prf, vsmpl, hsmpl, idl, alg)

        coo = []
        step = 0.5
        for lo in np.arange(-74, -68, step):
            for la in np.arange(17, 20, step):
                coo.append([lo, la])
        coo = np.array(coo)
        mesh = Mesh(coo[:, 0], coo[:, 1])

        # Define multisurface and mesh of sites
        self.msrf = MultiSurface([srfc50, srfc51])
        self.mesh = mesh

    def test_get_edge_set(self):

        # The vertexes of the expected edges are the first and last vertexes of
        # the topmost row of the mesh
        expected = [np.array([[-70.33, 19.65, 0. ],
                              [-70.57722702, 19.6697801 , 0.0]]),
                    np.array([[-70.10327766, 19.67957463, 0.0],
                              [-70.33, 19.65, 0.0]])]

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            for sfc in self.msrf.surfaces:
                col = np.random.rand(3)
                mesh = sfc.mesh
                ax.plot(mesh.lons, mesh.lats, '.', color=col)
                ax.plot(mesh.lons[0, :],  mesh.lats[0, :], lw=3)
            for edge in self.msrf.edge_set:
                ax.plot(edge[:, 0], edge[:, 1], 'x-r')
            plt.show()

        # Note that method is executed when the object is initialized
        ess = self.msrf.edge_set
        for es, expct in zip(ess, expected):
            np.testing.assert_array_almost_equal(es, expct, decimal=2)

    # TODO
    def test_get_cartesian_edge_set(self):
        es = self.msrf._get_cartesian_edge_set()

    def test_get_strike(self):
        # Since the two surf aces dip to the north we expect the strike to point
        # toward W
        msg = 'Multi fault surface: strike is wrong'
        strike = self.msrf.get_strike()
        self.assertAlmostEqual(268.878, strike, places=2)

    def test_get_dip(self):
        dip = self.msrf.get_dip()
        expected = 69.649
        msg = 'Multi fault surface: dip is wrong'
        aae(dip, expected, err_msg=msg, decimal=2)

    def test_get_width(self):
        width = self.msrf.get_width()
        print(width)

    # TODO
    def test_get_area(self):
        area = self.msrf.get_area()

    # TODO
    def test_get_bounding_box(self):
        bb = self.msrf.get_bounding_box()

    # TODO
    def test_get_middle_point(self):
        midp = self.msrf.get_middle_point()

    # TODO remove NaNs
    def test_get_surface_boundaries(self):
        bnd = self.msrf.get_surface_boundaries()

    # TODO test the updated attributes
    def test_setup_gc2_framework(self):
        gc2f = self.msrf._setup_gc2_framework()

    # TODO
    def test_get_gc2_coordinates_for_rupture(self):
        es = self.msrf._get_cartesian_edge_set()
        gc2c = self.msrf._get_gc2_coordinates_for_rupture(es)

    # TODO
    def test_get_generalised_coordinates(self):
        gcoo = self.msrf.get_generalised_coordinates(self.mesh.lons,
                                                     self.mesh.lats)

    # TODO fix the error
    def test_get_rx(self):
        dsts = self.msrf.get_rx_distance(self.mesh)

    # TODO fix the error
    def test_get_ry0(self):
        dsts = self.msrf.get_ry0_distance(self.mesh)


class MultiSurfaceTestCase65(unittest.TestCase):

    def setUp(self):
        path_qa = os.path.join('..', '..', '..', '..', 'qa_tests_data')
        path = os.path.join(path_qa, 'classical', 'case_65')
        fname = os.path.join(path, 'ssm.xml')
        fname_sections = os.path.join(path, 'sections.xml')

        sc = SourceConverter(investigation_time=1.0,
                             rupture_mesh_spacing=2,
                             complex_fault_mesh_spacing=5,
                             width_of_mfd_bin=0.1,
                             area_source_discretization=10.)

        ssm = to_python(fname)
        self.src = ssm[0][0]
        gsm = to_python(fname_sections, sc)
        self.src.set_sections(gsm.sections)

    def test01(self):
        mesh = Mesh(np.array([9.85]), np.array([45.0]))
        for i, rup in enumerate(self.src.iter_ruptures()):
            print(i)
            rup.surface.get_joyner_boore_distance(mesh)
            rup.surface.get_min_distance(mesh)
            rup.surface.get_ry0_distance(mesh)
            rup.surface.get_rx_distance(mesh)
            rup.surface.get_width()
            rup.surface.get_dip()
            rup.surface.get_top_edge_depth()
