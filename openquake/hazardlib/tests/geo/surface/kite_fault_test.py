# The Hazard Library
# Copyright (C) 2021 GEM Foundation
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

import os
import re
import glob
import unittest
import numpy as np
import matplotlib.pyplot as plt
from openquake.hazardlib.geo import geodetic
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.geodetic import distance
from openquake.hazardlib.geo.surface.kite_fault import (
    KiteSurface, kite_to_geom, geom_to_kite,
    get_profiles_from_simple_fault_data)
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.sourceconverter import SourceConverter


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
PLOTTING = False
aae = np.testing.assert_almost_equal


def plot_prf_2d(ax, prfs):
    for i, prf in enumerate(prfs):
        coo = np.array([(p.longitude, p.latitude) for p in prf.points])
        ax.plot(coo[:, 0], coo[:, 1], 'c--', lw=2)
        ax.text(coo[0, 0], coo[0, 1], f'{i}')


def plot_mesh_2d(ax, smsh):
    """
    Plots the mesh
    """
    for i in range(smsh.mesh.lons.shape[0]):
        ax.plot(smsh.mesh.lons[i, :], smsh.mesh.lats[i, :], '-r', lw=0.5)
    for i in range(smsh.mesh.lons.shape[1]):
        ax.plot(smsh.mesh.lons[:, i], smsh.mesh.lats[:, i], '-r', lw=0.5)
    ax.plot(smsh.mesh.lons[0, :], smsh.mesh.lats[0, :], '-g', lw=1.0)


def plot_mesh_3d(ax, smsh, zfa):
    """
    Plots the mesh
    """
    for i in range(smsh.mesh.lons.shape[0]):
        ax.plot(smsh.mesh.lons[i, :], smsh.mesh.lats[i, :],
                smsh.mesh.depths[i, :]/zfa, '-r', lw=0.5)
    for i in range(smsh.mesh.lons.shape[1]):
        ax.plot(smsh.mesh.lons[:, i], smsh.mesh.lats[:, i],
                smsh.mesh.depths[:, i]/zfa, '-r', lw=0.5)


def ppp(profiles: list, smsh: KiteSurface = None, title: str = ''):
    """
    Plots the 3D mesh

    :param profiles:
        A list of profiles
    :param smsh:
        The kite surface
    """
    from mpl_toolkits.mplot3d import Axes3D  # this is needed

    # Scaling factor on the z-axis
    scl = 0.1

    # Create figure
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    plt.style.use('seaborn-bright')

    # Plotting nodes
    for ipro in profiles:
        coo = [[p.longitude, p.latitude, p.depth] for p in ipro]
        coo = np.array(coo)
        ax.plot(coo[:, 0], coo[:, 1], coo[:, 2]*scl, '--g', lw=1)
        ax.plot(coo[:, 0], coo[:, 1], coo[:, 2]*scl, 'og', lw=1, markersize=3)

    # Plotting mesh
    if smsh is not None:
        for i in range(smsh.mesh.lons.shape[0]):
            ax.plot(smsh.mesh.lons[i, :], smsh.mesh.lats[i, :],
                    smsh.mesh.depths[i, :]*scl, '-r', lw=0.5)
        for i in range(smsh.mesh.lons.shape[1]):
            ax.plot(smsh.mesh.lons[:, i], smsh.mesh.lats[:, i],
                    smsh.mesh.depths[:, i]*scl, '-r', lw=0.5)
    plt.title(title)
    ax.invert_zaxis()
    plt.show()


class KiteSurfaceFromMeshTest(unittest.TestCase):
    """
    Tests the method that creates the external boundary of the rupture.
    """

    def setUp(self):
        lons = [[np.nan, 0.05, 0.1, 0.15, 0.20],
                [0.00, 0.05, 0.1, 0.15, 0.20],
                [0.00, 0.05, 0.1, 0.15, 0.20],
                [0.00, 0.05, 0.1, 0.15, np.nan],
                [0.00, np.nan, 0.1, 0.15, np.nan]]
        lats = [[np.nan, 0.0, 0.0, 0.0, 0.0],
                [0.05, 0.05, 0.05, 0.05, 0.05],
                [0.10, 0.10, 0.10, 0.10, 0.10],
                [0.15, 0.15, 0.15, 0.15, np.nan],
                [0.20, np.nan, 0.20, 0.20, np.nan]]
        deps = [[np.nan, 0.0, 0.0, 0.0, 0.0],
                [5, 5, 5, 5, 5],
                [10, 10, 10, 10, 10],
                [15, 15, 15, 15, np.nan],
                [20, np.nan, 20, 20, np.nan]]
        self.lons = np.array(lons)
        self.lats = np.array(lats)
        self.deps = np.array(deps)

        self.mesh = Mesh(self.lons, self.lats, self.deps)
        self.ksfc = KiteSurface(self.mesh)

    def test_get_external_boundary(self):
        # This mesh does not comply with the right hand rule. In the init it
        # will be adjusted

        ksfc = self.ksfc
        idxs = ksfc._get_external_boundary_indexes()

        # Checking
        expected = [[0, 0], [0, 1], [0, 2], [0, 3], [1, 4], [2, 4], [3, 4],
                    [4, 4], [3, 3], [4, 2], [4, 1], [2, 0], [1, 0]]
        np.testing.assert_almost_equal(expected, idxs)

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            ax.plot(self.lons.flatten(), self.lats.flatten(), 'o')
            lo, la = ksfc._get_external_boundary()
            ax.plot(lo, la, '-r')
            ax.invert_yaxis()
            plt.show()

    def test_get_dip(self):
        self.ksfc.get_dip()

    def test_get_cell_dimensions(self):
        ksfc = self.ksfc
        _, _, _, areas = ksfc.get_cell_dimensions()
        idx = np.isfinite(areas)

        # Computing the lenght and the width of the rectangle representing the
        # rupture surface. This includes the cells which are empty
        iul = (1, 0)
        iur = (1, -1)
        slen = distance(self.lons[iul], self.lats[iul], self.deps[iul],
                        self.lons[iur], self.lats[iur], self.deps[iur])
        iul = (0, 2)
        ill = (-1, 2)
        swid = distance(self.lons[iul], self.lats[iul], self.deps[iul],
                        self.lons[ill], self.lats[ill], self.deps[ill])

        # Computing the surface area as the total area minus the area of 4
        # cells. Note that here we assume that cells have approx the same area
        expected = slen * swid / areas.size * (np.sum(idx))

        perc_diff = abs(expected - np.sum(areas[idx])) / expected * 100
        self.assertTrue(perc_diff < 0.5)

    def test_get_tor(self):
        """ test calculation of trace (i.e. surface projection of tor) """
        lons = np.flipud([0.0, 0.05, 0.1, 0.15, 0.20])
        lats = np.array([0.0, 0.0, 0.0, 0.0, 0.05])
        tlo, tla = self.ksfc.get_tor()
        aae(lons, tlo)
        aae(lats, tla)

    def test_geom(self):
        geom = kite_to_geom(self.ksfc)
        ksfc = geom_to_kite(geom)
        for par in ('lons', 'lats', 'depths'):
            orig = getattr(self.ksfc.mesh, par)
            copy = getattr(ksfc.mesh, par)
            np.testing.assert_almost_equal(orig, copy)  # 32/64 bit mismatch


class KiteSurfaceWithNaNs(unittest.TestCase):
    """
    Test the creation of a surface which will contain NaNs. The
    :method:`openquake.hazardlib.geo.surface.kite_fault.Kite.KiteSurface._clean`
    removes rows and cols just containing NaNs.
    """

    NAME = 'KiteSurfaceWithNaNs'

    def setUp(self):

        # Read the profiles and create the surface
        path = os.path.join(BASE_DATA_PATH, 'profiles07')
        self.prf, _ = _read_profiles(path)
        hsmpl = 4
        vsmpl = 2
        idl = False
        alg = False
        self.srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)

        # Create the mesh of sites - No need to define their depth
        step = 0.005
        plons = []
        plats = []
        for lo in np.arange(9.9, 10.4, step):
            tlo = []
            tla = []
            for la in np.arange(44.6, 45.3, step):
                tlo.append(lo)
                tla.append(la)
            plons.append(tlo)
            plats.append(tla)
        self.mlons = np.array(plons)
        self.mlats = np.array(plats)
        self.mesh = Mesh(lons=self.mlons.flatten(), lats=self.mlats.flatten())

    def test_get_tor(self):
        tlo, tla = self.srfc.get_tor()
        # Expected results extracted manually from the mesh
        elo = np.array([10.01157297, 10.04780614,
                        10.09853744, 10.14926874, 10.2])
        ela = np.array([44.99160022, 45.00003185,
                        45.00004377, 45.00003315, 45.])

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            plot_mesh_2d(ax, self.srfc)
            plot_prf_2d(ax, self.prf)
            ax.plot(tlo, tla, '-g', lw=4)
            plt.show()

        aae(elo, tlo)
        aae(ela, tla)

    def test_rjb_calculation(self):
        # Test the calculation of the Rjb distance
        dst = self.srfc.get_joyner_boore_distance(self.mesh)

        if PLOTTING:
            _ = plt.figure()
            ax = plt.gca()
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            plot_mesh_2d(ax, self.srfc)
            lo, la = self.srfc._get_external_boundary()
            plt.plot(lo, la, '-r')
            z = np.reshape(dst, self.mlons.shape)
            cs = plt.contour(self.mlons, self.mlats, z, 10, colors='k')
            _ = plt.clabel(cs)
            tlo, tla = self.srfc.get_tor()
            ax.plot(tlo, tla, '-g', lw=4)
            plt.title(f'{self.NAME} - Rjb')
            plt.show()

        mesh = Mesh(np.array([10.06]), np.array([44.91]))
        dst = self.srfc.get_joyner_boore_distance(mesh)
        self.assertAlmostEqual(0.0, dst[0])

    def test_rrup_calculation(self):
        dst = self.srfc.get_min_distance(self.mesh)

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            lo, la = self.srfc._get_external_boundary()
            plt.plot(lo, la, '-r')
            z = np.reshape(dst, self.mlons.shape)
            cs = plt.contour(self.mlons, self.mlats, z, 10, colors='k')
            _ = plt.clabel(cs)
            tlo, tla = self.srfc.get_tor()
            ax.plot(tlo, tla, '-g', lw=4)
            plt.title(f'{self.NAME} - Rrup')
            plt.show()

    def test_rx_calculation(self):
        dst = self.srfc.get_rx_distance(self.mesh)

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            lo, la = self.srfc._get_external_boundary()
            plt.plot(lo, la, '-r')
            z = np.reshape(dst, self.mlons.shape)
            cs = plt.contour(self.mlons, self.mlats, z, 10, colors='k')
            _ = plt.clabel(cs)
            tlo, tla = self.srfc.get_tor()
            ax.plot(tlo, tla, '-g', lw=4)
            plt.title(f'{self.NAME} - Rx')
            plt.show()

    def test_ry0_calculation(self):
        dst = self.srfc.get_ry0_distance(self.mesh)

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            lo, la = self.srfc._get_external_boundary()
            plt.plot(lo, la, '-r')
            z = np.reshape(dst, self.mlons.shape)
            cs = plt.contour(self.mlons, self.mlats, z, 10, colors='k')
            _ = plt.clabel(cs)
            tlo, tla = self.srfc.get_tor()
            ax.plot(tlo, tla, '-g', lw=4)
            plt.title(f'{self.NAME} - Ry0')
            plt.show()

    # TODO
    def test_get_dip(self):
        dip = self.srfc.get_dip()


class KiteSurfaceSimpleTests(unittest.TestCase):
    """
    Simple test for the creation of a KiteSurface
    """

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles05')
        self.prf, _ = _read_profiles(path)

    def test_mesh_creation(self):
        # Create the mesh: two parallel profiles - no top alignment
        hsmpl = 4
        vsmpl = 2
        idl = False
        alg = False
        srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)

        if PLOTTING:
            title = 'Test mesh creation'
            ppp(self.prf, srfc, title)

    def test_get_area(self):
        hsmpl = 4
        vsmpl = 2
        idl = False
        alg = False
        srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)
        area = srfc.get_area()
        self.assertAlmostEqual(271.3134, area, places=2)

    def test_ztor(self):
        # Create the mesh: two parallel profiles - no top alignment
        hsmpl = 4
        vsmpl = 2
        idl = False
        alg = False
        srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)
        ztor = srfc.get_top_edge_depth()
        self.assertAlmostEqual(20.0, ztor)

    def test_compute_joyner_boore_distance(self):

        # Create the mesh: two parallel profiles - no top alignment
        hsmpl = 2
        vsmpl = 2
        idl = False
        alg = False
        srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)

        plons = np.array([10.0, 10.15])
        plats = np.array([45.0, 45.15])
        mesh = Mesh(lons=plons, lats=plats)
        dsts = srfc.get_joyner_boore_distance(mesh)

        if PLOTTING:
            _ = plt.figure()
            plt.plot(srfc.mesh.lons, srfc.mesh.lats, '.', color='gray')
            plt.plot(plons, plats, 'o')
            plt.show()

        # Distance computed here:
        # https://www.movable-type.co.uk/scripts/latlong.html
        expected = np.array([13.61, 0.0])
        np.testing.assert_almost_equal(np.array(dsts), expected, decimal=2)


class KinkedKiteSurfaceTestCase(unittest.TestCase):
    """ Test the construction of a kinked kite fault surface. """

    def setUp(self):
        """ This creates a fault dipping to north """

        self.profiles1 = []
        tmp = [Point(0.0, 0.00, 0.0),
               Point(0.0, 0.05, 5.0),
               Point(0.0, 0.10, 10.0),
               Point(0.0, 0.20, 20.0)]
        self.profiles1.append(Line(tmp))

        tmp = [Point(0.17, 0.00, 0.0),
               Point(0.17, 0.05, 5.0),
               Point(0.17, 0.10, 10.0),
               Point(0.17, 0.15, 15.0)]
        self.profiles1.append(Line(tmp))

        tmp = [Point(0.20, 0.00, 0.0),
               Point(0.20, 0.05, 5.0),
               Point(0.20, 0.10, 10.0),
               Point(0.20, 0.15, 15.0)]

        tmp = [Point(0.23, 0.13, 0.0),
               Point(0.23, 0.18, 5.0),
               Point(0.23, 0.23, 10.0),
               Point(0.23, 0.28, 15.0)]
        self.profiles1.append(Line(tmp))

    def test_build_kinked_mesh_01(self):
        # Trivial case - Fault dipping at about 45 degrees

        # Build the fault surface
        p_sd = 5.0
        e_sd = 15.0
        msh = KiteSurface.from_profiles(self.profiles1, p_sd, e_sd)

        if PLOTTING:
            title = 'Trivial case - Fault dipping at about 45 degrees'
            ppp(self.profiles1, msh, title)


class KiteSurfaceTestCase(unittest.TestCase):
    """ Test the construction of a Kite fault surface. """

    def setUp(self):
        """ This creates a fault dipping to north """

        self.profiles1 = []
        tmp = [Point(0.0, 0.00, 0.0),
               Point(0.0, 0.05, 5.0),
               Point(0.0, 0.10, 10.0),
               Point(0.0, 0.15, 15.0)]
        self.profiles1.append(Line(tmp))

        tmp = [Point(0.3, 0.00, 0.0),
               Point(0.3, 0.05, 5.0),
               Point(0.3, 0.10, 10.0),
               Point(0.3, 0.15, 15.0)]
        self.profiles1.append(Line(tmp))

        tmp = [Point(0.5, 0.00, 0.0),
               Point(0.5, 0.05, 5.0),
               Point(0.5, 0.10, 10.0),
               Point(0.5, 0.15, 15.0)]
        self.profiles1.append(Line(tmp))

        self.profiles2 = []
        tmp = [Point(0.0, 0.000, 0.0),
               Point(0.0, 0.001, 15.0)]
        self.profiles2.append(Line(tmp))
        tmp = [Point(0.5, 0.000, 0.0),
               Point(0.5, 0.001, 15.0)]
        self.profiles2.append(Line(tmp))

    def test_build_mesh_01(self):
        # Trivial case - Fault dipping at about 45 degrees

        # Build the fault surface
        p_sd = 2.0
        e_sd = 5.0
        msh = KiteSurface.from_profiles(self.profiles1, p_sd, e_sd)

        # The fault trace has a length of 0.5 degrees at the equator (along
        # meridians) which corresponds to a length of # 111.3/2km = 55.65km.
        # Using a sampling distance of 5 km we get 12 equally spaced profiles.
        # Along the dip the fault width is ((0.15*110.567)**2+15**2)**.5 i.e.
        # 22.36km. With a sampling of 2.0km we get 12 edges.
        np.testing.assert_equal(msh.mesh.lons.shape, (12, 12))

        # We take the last index since we are flipping the mesh to comply with
        # the right hand rule
        self.assertTrue(np.all(np.abs(msh.mesh.lons[:, -1]) < 1e-3))

        # Tests the position of the center
        pnt = msh.get_center()
        tmp = (abs(msh.mesh.lons-pnt.longitude) +
               abs(msh.mesh.lats-pnt.latitude) +
               abs(msh.mesh.depths-pnt.depth)*0.01)
        idx = np.unravel_index(np.argmin(tmp, axis=None), tmp.shape)
        msg = "We computed center of the surface is wrong"
        self.assertEqual(idx, (6, 6), msg)

        if PLOTTING:
            title = 'Trivial case - Fault dipping at about 45 degrees'
            ppp(self.profiles1, msh, title)

    def test_build_mesh_02(self):
        # Trivial case - Vertical fault

        # Build the fault surface
        p_sd = 2.5
        e_sd = 5.0
        srfc = KiteSurface.from_profiles(self.profiles2, p_sd, e_sd)

        # The fault trace has a length of 0.5 degrees at the equator (along
        # meridians) which corresponds to a length of 111.3/2km = 55.65km.
        # Using a sampling distance of 5 km we get 12 equally spaced profiles.
        # Along the dip the fault width is 15 km. With a sampling of 2.5km
        # we get exactly 7 edges.
        msh = srfc.mesh
        np.testing.assert_equal(msh.lons.shape, (7, 12))

        # Note that this mesh is flipped at the construction level
        self.assertTrue(np.all(np.abs(msh.depths[0, :]) < 1e-3))
        self.assertTrue(np.all(np.abs(msh.depths[6, :]-15.) < 1e-3))
        self.assertTrue(np.all(np.abs(msh.lons[:, -1]) < 1e-3))
        self.assertTrue(np.all(np.abs(msh.lons[:, 0]-0.5) < 1e-2))

        dip = srfc.get_dip()
        msg = "The value of dip computed is wrong: {dip:.3f}"
        self.assertTrue(abs(dip-90) < 0.5, msg)

        strike = srfc.get_strike()
        msg = "The value of strike computed is wrong.\n"
        msg += "computed: {strike:.3f} expected:"
        self.assertTrue(abs(strike-270) < 0.01, msg)

        if PLOTTING:
            title = 'Trivial case - Vertical fault'
            ppp(self.profiles2, srfc, title)


class IdealisedSimpleMeshTest(unittest.TestCase):
    """
    This is the simplest test implemented for the construction of the mesh. It
    uses just two parallel profiles gently dipping northward and it checks
    that the size of the cells agrees with the input parameters
    """

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles05')
        self.prf, _ = _read_profiles(path)

    def test_mesh_creation(self):
        # Create the mesh: two parallel profiles - no top alignment
        hsmpl = 4
        vsmpl = 4
        idl = False
        alg = False
        srfc = KiteSurface.from_profiles(self.prf, hsmpl, vsmpl, idl, alg)
        smsh = srfc.mesh

        # Check the horizontal mesh spacing
        computed = []
        for i in range(0, smsh.lons.shape[0]):
            tmp = []
            for j in range(0, smsh.lons.shape[1]-1):
                k = j + 1
                dst = distance(smsh.lons[i, j], smsh.lats[i, j],
                               smsh.depths[i, j], smsh.lons[i, k],
                               smsh.lats[i, k], smsh.depths[i, k])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        self.assertTrue(np.all(abs(computed-hsmpl)/vsmpl < 0.05))

        # Check the vertical mesh spacing
        computed = []
        for i in range(0, smsh.lons.shape[0]-1):
            tmp = []
            k = i + 1
            for j in range(0, smsh.lons.shape[1]):
                dst = distance(
                    smsh.lons[i, j], smsh.lats[i, j], smsh.depths[i, j],
                    smsh.lons[k, j], smsh.lats[k, j], smsh.depths[k, j])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        self.assertTrue(np.all(abs(computed-vsmpl)/vsmpl < 0.05))

        if PLOTTING:
            title = 'Two parallel profiles'
            ppp(self.prf, srfc, title)


class IdealisedSimpleDisalignedMeshTest(unittest.TestCase):
    """
    Similar to
    :class:`openquake.sub.tests.misc.mesh_test.IdealisedSimpleMeshTest`
    but with profiles at different depths
    """

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles06')
        self.profiles, _ = _read_profiles(path)
        self.h_sampl = 2
        self.v_sampl = 4
        idl = False
        alg = False
        self.smsh = KiteSurface.from_profiles(self.profiles, self.v_sampl,
                                              self.h_sampl, idl, alg)

    def test_h_spacing(self):
        # Check v-spacing: two misaligned profiles - no top alignment
        srfc = self.smsh
        smsh = srfc.mesh
        #
        # Check the horizontal mesh spacing
        computed = []
        for i in range(0, smsh.lons.shape[0]):
            tmp = []
            for j in range(0, smsh.lons.shape[1]-1):
                k = j + 1
                dst = distance(
                    smsh.lons[i, j], smsh.lats[i, j], smsh.depths[i, j],
                    smsh.lons[i, k], smsh.lats[i, k], smsh.depths[i, k])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        tmp = abs(computed-self.h_sampl)/self.h_sampl
        self.assertTrue(np.all(tmp < 0.02))

        if PLOTTING:
            title = 'Simple case: top alignment '
            title += '(IdealisedSimpleDisalignedMeshTest)'
            ppp(self.profiles, srfc, title)

    def test_spacing(self):
        # Check v-spacing: two misaligned profiles - no top alignment
        srfc = self.smsh
        smsh = srfc.mesh
        computed = []
        for i in range(0, smsh.lons.shape[0]-1):
            tmp = []
            k = i + 1
            for j in range(0, smsh.lons.shape[1]):
                dst = distance(
                    smsh.lons[i, j], smsh.lats[i, j], smsh.depths[i, j],
                    smsh.lons[k, j], smsh.lats[k, j], smsh.depths[k, j])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        tmp = abs(computed-self.v_sampl)/self.v_sampl
        self.assertTrue(np.all(tmp < 0.01))


class IdealisedAsimmetricMeshTest(unittest.TestCase):
    """
    Tests the creation of a surface using profiles not 'aligned' at the top
    (i.e. they do not start at the same depth) and with different lenghts
    """

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles03')
        self.profiles, _ = _read_profiles(path)

    def test_mesh_creation(self):
        # Test construction of the mesh
        h_sampl = 5
        v_sampl = 5
        idl = False
        alg = False
        srfc = KiteSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                         idl, alg)
        smsh = srfc.mesh
        self.assertTrue(np.all(~np.isnan(smsh.lons[0, :])))

        if PLOTTING:
            title = 'Simple case: No top alignment '
            title += '(IdealisedAsimmetricMeshTest)'
            ppp(self.profiles, srfc, title)

    def test_mesh_creation_with_alignment(self):
        # Test construction of the mesh
        h_sampl = 2.5
        v_sampl = 2.5
        idl = False
        alg = True
        srfc = KiteSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                         idl, alg)
        self.assertTrue(np.any(np.isnan(srfc.mesh.lons[0, :])))

        if PLOTTING:
            title = 'Simple case: Top alignment'
            title += '(IdealisedAsimmetricMeshTest)'
            ppp(self.profiles, srfc, title)

    def test_get_surface_projection(self):
        h_sampl = 2.5
        v_sampl = 2.5
        idl = False
        alg = True
        srfc = KiteSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                         idl, alg)
        lons, lats = srfc.surface_projection
        # TODO

    def test_get_width(self):
        # Test the calculation of the width
        h_sampl = 2.5
        v_sampl = 2.5
        idl = False
        alg = True
        srfc = KiteSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                         idl, alg)
        width = srfc.get_width()
        np.testing.assert_almost_equal(38.13112131, width)


class IdealizedATest(unittest.TestCase):
    """
    Tests the creation of a surface starting from profiles that are not
    'aligned' at the top i.e. they do not start at the same depth.
    """

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles04')
        self.profiles, _ = _read_profiles(path)

    def test_mesh_creation_no_alignment(self):
        # Test construction of the mesh
        h_sampl = 4
        v_sampl = 4
        idl = False
        alg = False
        smsh = KiteSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                         idl, alg)
        self.assertTrue(np.all(~np.isnan(smsh.mesh.lons[0, :])))

        if PLOTTING:
            title = 'Simple mesh creation - no top alignment'
            ppp(self.profiles, smsh, title)

    def test_mesh_creation_with_alignment(self):
        # Test construction of the mesh
        h_sampl = 4
        v_sampl = 4
        idl = False
        alg = True
        smsh = KiteSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                         idl, alg)
        self.assertTrue(np.any(np.isnan(smsh.mesh.lons[0, :])))

        if PLOTTING:
            title = 'Simple case: Top alignment'
            ppp(self.profiles, smsh, title)


class SouthAmericaSegmentTest(unittest.TestCase):
    """
    Tests the creation using information for one of the slab segments included
    in the hazard model for South America
    """

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'sam_seg6_slab')
        self.profiles, _ = _read_profiles(path)

    def test_mesh_creation(self):
        # Create mesh from profiles for SA
        sampling = 40
        idl = False
        alg = False
        smsh = KiteSurface.from_profiles(self.profiles, sampling,
                                         sampling, idl, alg)
        idx = np.isfinite(smsh.mesh.lons[:, :])
        self.assertEqual(np.sum(np.sum(idx)), 205)

        if PLOTTING:
            title = 'Top of the slab'
            ppp(self.profiles, smsh, title)


class VerticalProfilesTest(unittest.TestCase):

    def test_vertical_01(self):

        fname = os.path.join(BASE_DATA_PATH, 'poly_problem.xml')
        sconv = SourceConverter(1.0, 2.5)
        ssm = to_python(fname, sconv)
        src = ssm[0][0]
        profiles = src.surface.profiles

        # Create the surface from the profiles
        sfc = KiteSurface.from_profiles(profiles, 2., 2.)

        if PLOTTING:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            zfa = 50.
            ax.plot(sfc.mesh.lons.flatten(), sfc.mesh.lats.flatten(),
                    sfc.mesh.depths.flatten()/zfa, '.')
            plot_mesh_3d(ax, sfc, zfa)
            for pr in profiles:
                coo = np.array([[p.longitude, p.latitude, p.depth/zfa]
                                for p in pr])
                ax.plot(coo[:, 0], coo[:, 1], coo[:, 2])
            lo, la = sfc._get_external_boundary()
            ax.plot(lo, la, np.zeros_like(lo))
            ax.invert_zaxis()
            # ax.set_box_aspect([1, 1, 1])
            plt.show()

        # Testing that the mesh is vertical
        expected = [-75.03541, 19.85003, -75.03541, 19.85003]
        computed = [sfc.mesh.lons[0, 0], sfc.mesh.lats[0, 0],
                    sfc.mesh.lons[-1, 0], sfc.mesh.lats[-1, 0]]
        np.testing.assert_allclose(expected, computed)

        # Testing the calculation of the polygon
        eblo, ebla = sfc._get_external_boundary()
        mgd = geodetic.min_geodetic_distance
        idx = np.min(np.where(np.isfinite(sfc.mesh.lons[:, 0])))
        dst = mgd((sfc.mesh.lons[idx, 0], sfc.mesh.lats[idx, 0]),
                  (eblo[:2], ebla[:2]))
        self.assertTrue(np.all(dst < 0.1+0.01))


class TestNarrowSurface(unittest.TestCase):

    def test_narrow_01(self):

        # The profiles are aligned at the top and the bottom. Their horizontal
        # distance is lower than the sampling distance
        self.profiles = []
        tmp = [Point(0.0, 0.000, 0.0),
               Point(0.0, 0.001, 15.0)]
        self.profiles.append(Line(tmp))
        tmp = [Point(0.01, 0.000, 0.0),
               Point(0.01, 0.001, 15.0)]
        self.profiles.append(Line(tmp))

        # Computing the mesh
        idl = False
        alg = False
        v_sampl = 5.0
        h_sampl = 5.0
        smsh = KiteSurface.from_profiles(
            self.profiles, v_sampl, h_sampl, idl, alg)

        # Testing
        expected_lons = np.array([[0.01, 0.], [0.01, 0.], [0.01, 0.],
                                  [0.01, 0.]])
        expected_lats = np.array([[0., 0.], [0.00029411, 0.00029411],
                                  [0.00058822, 0.00058822],
                                  [0.00088233, 0.00088233]])
        expected_deps = np.array([[0., 0.], [4.99989305, 4.99989305],
                                  [9.99978609, 9.99978609],
                                  [14.99967914, 14.99967914]])
        aae(smsh.mesh.lons, expected_lons)
        aae(smsh.mesh.lats, expected_lats)
        aae(smsh.mesh.depths, expected_deps)


class TestProfilesFromSimpleFault(unittest.TestCase):

    def test_from_simple_geometry(self):

        # Fault is dipping SE with azimuth toward NE
        trace = Line([Point(10, 45.), Point(10.2, 45.2)])
        usd = 0
        lsd = 10.
        dip = 60.0
        rup_mesh_spacing = 1.0

        pro = get_profiles_from_simple_fault_data(trace, usd, lsd, dip,
                                                  rup_mesh_spacing)

        from openquake.hazardlib.geo.geodetic import npoints_towards, azimuth

        # This is the initial width
        width = (lsd - usd) / np.sin(np.radians(dip))
        np.testing.assert_array_almost_equal(width, 11.547, decimal=3)

        # This is the rounded width
        width_round = width // rup_mesh_spacing

        delta_x = width_round * np.cos(np.radians(dip))
        delta_h = width_round * np.sin(np.radians(dip))
        azim = azimuth(trace[0].longitude, trace[0].latitude,
                       trace[-1].longitude, trace[-1].latitude)
        coo = npoints_towards(trace[0].longitude, trace[0].latitude, 0.0,
                              azim + 90.0, delta_x, delta_h, 2)

        np.testing.assert_almost_equal(pro[0].coo[-1,0], coo[0][-1], decimal=3)
        np.testing.assert_almost_equal(pro[0].coo[-1,1], coo[1][-1], decimal=3)


def _read_profiles(path: str, prefix: str = 'cs') -> (list, list):
    """
    Reads a set of files each one containing a profile

    :param path:
        The path to a folder containing a set of profiles
    :param prefix:
        The prefix of the files containing the profiles
    :returns:
        A tuple with two lists one containing the profiles and the other one
        with the names of the files
    """
    path = os.path.join(path, f'{prefix}*.*')
    profiles = []
    names = []
    for filename in sorted(glob.glob(path)):
        profiles.append(_read_profile(filename))
        names.append(os.path.basename(filename))
    return profiles, names


def _read_profile(filename: str) -> Line:
    """
    Reads a file with one profile

    :parameter filename:
        The name of the folder file (usually with prefix 'cs_')
        specifing the geometry of the top of the slab
    :returns:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    """
    points = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            aa = re.split('\\s+', line)
            points.append(Point(float(aa[0]),
                                float(aa[1]),
                                float(aa[2])))
    return Line(points)



