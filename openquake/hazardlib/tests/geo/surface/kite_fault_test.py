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
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.geodetic import distance
from openquake.hazardlib.geo.surface import KiteSurface


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
PLOTTING = False


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


class KiteSurfaceWithNaNs(unittest.TestCase):

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles07')
        self.prf, _ = _read_profiles(path)
        hsmpl = 4
        vsmpl = 2
        idl = False
        alg = False
        self.srfc = KiteSurface.from_profiles(self.prf, vsmpl, hsmpl, idl, alg)

        coo = []
        step = 0.025
        for lo in np.arange(9.9, 10.4, step):
            for la in np.arange(44.6, 45.3, step):
                coo.append([lo, la])
        coo = np.array(coo)
        self.mesh = Mesh(lons=coo[:, 0], lats=coo[:, 1])

    def test_rjb_calculation(self):
        dst = self.srfc.get_joyner_boore_distance(self.mesh)

        if PLOTTING:
            _ = plt.figure()
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            plt.plot(self.srfc.mesh.lons, self.srfc.mesh.lats, '.',
                     color='red')
            plt.title('Rjb')
            plt.show()

        if PLOTTING:
            title = 'Test mesh with NaNs'
            ppp(self.prf, self.srfc, title)

    def test_rrup_calculation(self):
        dst = self.srfc.get_min_distance(self.mesh)

        if PLOTTING:
            _ = plt.figure()
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            plt.plot(self.srfc.mesh.lons, self.srfc.mesh.lats, '.',
                     color='red')
            plt.title('Rrup')
            plt.show()

    def test_rx_calculation(self):
        dst = self.srfc.get_rx_distance(self.mesh)

        if PLOTTING:
            _ = plt.figure()
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            plt.plot(self.srfc.mesh.lons, self.srfc.mesh.lats, '.',
                     color='red')
            plt.title('Rx')
            plt.show()

    def test_ry0_calculation(self):
        dst = self.srfc.get_ry0_distance(self.mesh)

        if PLOTTING:
            _ = plt.figure()
            plt.scatter(self.mesh.lons, self.mesh.lats, c=dst,
                        edgecolors='none', s=15)
            plt.plot(self.srfc.mesh.lons, self.srfc.mesh.lats, '.',
                     color='red')
            plt.title('Ry0')
            plt.show()


class KiteSurfaceSimpleTests(unittest.TestCase):

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
        msg = "The value of dip computed is wrong: {:.3f}".format(dip)
        self.assertTrue(abs(dip-90) < 0.5, msg)

        strike = srfc.get_strike()
        msg = "The value of strike computed is wrong.\n"
        msg += "computed: {:.3f} expected:".format(strike)
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

        #
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

        #
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


def _read_profiles(path, prefix='cs'):
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
    path = os.path.join(path, '{:s}*.*'.format(prefix))
    profiles = []
    names = []
    for filename in sorted(glob.glob(path)):
        profiles.append(_read_profile(filename))
        names.append(os.path.basename(filename))
    return profiles, names


def _read_profile(filename):
    """
    Reads a file with one profile

    :parameter filename:
        The name of the folder file (usually with prefix 'cs_')
        specifing the geometry of the top of the slab
    :returns:
        An instance of :class:`openquake.hazardlib.geo.line.Line`
    """
    points = []
    for line in open(filename, 'r'):
        aa = re.split('\\s+', line)
        points.append(Point(float(aa[0]),
                            float(aa[1]),
                            float(aa[2])))
    return Line(points)
