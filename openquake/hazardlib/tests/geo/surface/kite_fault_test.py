# The Hazard Library
# Copyright (C) 2020 GEM Foundation
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
from mpl_toolkits.mplot3d import Axes3D  # This is needed
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.geodetic import distance
from openquake.hazardlib.geo.surface import KiteFaultSurface

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
PLOTTING = False


def ppp(profiles, smsh, title=''):
    """
    Plots the 3D mesh

    :param smsh:
        The mesh representing the Kite fault surface
    """

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
    for i in range(smsh.shape[0]):
        ax.plot(smsh[i, :, 0], smsh[i, :, 1], smsh[i, :, 2]*scl, '-r', lw=0.5)
    for i in range(smsh.shape[1]):
        ax.plot(smsh[:, i, 0], smsh[:, i, 1], smsh[:, i, 2]*scl, '-r', lw=0.5)

    plt.title(title)
    ax.invert_zaxis()
    plt.show()


class KiteFaultSurfaceTestCase(unittest.TestCase):
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
        """ Trivial case - Fault dipping at about 45 degrees """

        # Build the fault surface
        p_sd = 2.0
        e_sd = 5.0
        msh = KiteFaultSurface.from_profiles(self.profiles1, p_sd, e_sd)

        # The fault trace has a length of 0.5 degrees at the equator (along
        # meridians) which corresponds to a length of # 111.3/2km = 55.65km.
        # Using a sampling distance of 5 km we get 12 equally spaced profiles.
        # Along the dip the fault width is ((0.15*110.567)**2+15**2)**.5 i.e.
        # 22.36km. With a sampling of 2.0km we get exactly 7 edges.
        np.testing.assert_equal(msh.shape, (12, 12, 3))
        self.assertTrue(np.all(np.abs(msh[:, 0, 0]) < 1e-3))

        if PLOTTING:
            title = 'Trivial case - Fault dipping at about 45 degrees'
            ppp(self.profiles1, msh, title)

    def test_build_mesh_02(self):
        """ Trivial case - Vertical fault """

        # Build the fault surface
        p_sd = 2.5
        e_sd = 5.0
        msh = KiteFaultSurface.from_profiles(self.profiles2, p_sd, e_sd)

        # The fault trace has a length of 0.5 degrees at the equator (along
        # meridians) which corresponds to a length of # 111.3/2km = 55.65km.
        # Using a sampling distance of 5 km we get 12 equally spaced profiles.
        # Along the dip the fault width is 15 km. With a sampling of 2.5km
        # we get exactly 7 edges.
        np.testing.assert_equal(msh.shape, (7, 12, 3))
        self.assertTrue(np.all(np.abs(msh[0, :, 2]) < 1e-3))
        self.assertTrue(np.all(np.abs(msh[6, :, 2]-15.) < 1e-3))
        self.assertTrue(np.all(np.abs(msh[:, 0, 0]) < 1e-3))
        self.assertTrue(np.all(np.abs(msh[:, 11, 0]-0.5) < 1e-2))

        if PLOTTING:
            title = 'Trivial case - Vertical fault'
            ppp(self.profiles2, msh, title)


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
        """ Create the mesh: two parallel profiles - no top alignment """
        hsmpl = 4
        vsmpl = 4
        idl = False
        alg = False
        smsh = KiteFaultSurface.from_profiles(self.prf, hsmpl, vsmpl, idl, alg)

        #
        # Check the horizontal mesh spacing
        computed = []
        for i in range(0, smsh.shape[0]):
            tmp = []
            for j in range(0, smsh.shape[1]-1):
                k = j + 1
                dst = distance(smsh[i, j, 0], smsh[i, j, 1], smsh[i, j, 2],
                               smsh[i, k, 0], smsh[i, k, 1], smsh[i, k, 2])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        self.assertTrue(np.all(abs(computed-hsmpl)/vsmpl < 0.05))

        #
        # Check the vertical mesh spacing
        computed = []
        for i in range(0, smsh.shape[0]-1):
            tmp = []
            k = i + 1
            for j in range(0, smsh.shape[1]):
                dst = distance(smsh[i, j, 0], smsh[i, j, 1], smsh[i, j, 2],
                               smsh[k, j, 0], smsh[k, j, 1], smsh[k, j, 2])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        self.assertTrue(np.all(abs(computed-vsmpl)/vsmpl < 0.05))

        if PLOTTING:
            title = 'Two parallel profiles'
            ppp(self.prf, smsh, title)


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
        self.smsh = KiteFaultSurface.from_profiles(self.profiles, self.v_sampl,
                                                   self.h_sampl, idl, alg)

    def test_h_spacing(self):
        """ Check v-spacing: two misaligned profiles - no top alignment """
        smsh = self.smsh
        #
        # Check the horizontal mesh spacing
        computed = []
        for i in range(0, smsh.shape[0]):
            tmp = []
            for j in range(0, smsh.shape[1]-1):
                k = j + 1
                dst = distance(smsh[i, j, 0], smsh[i, j, 1], smsh[i, j, 2],
                               smsh[i, k, 0], smsh[i, k, 1], smsh[i, k, 2])
                tmp.append(dst)
            computed.append(dst)
        computed = np.array(computed)
        tmp = abs(computed-self.h_sampl)/self.h_sampl
        self.assertTrue(np.all(tmp < 0.02))

        if PLOTTING:
            ppp(self.profiles, self.smsh)

    def test__spacing(self):
        """ Check v-spacing: two misaligned profiles - no top alignment """
        smsh = self.smsh
        computed = []
        for i in range(0, smsh.shape[0]-1):
            tmp = []
            k = i + 1
            for j in range(0, smsh.shape[1]):
                dst = distance(smsh[i, j, 0], smsh[i, j, 1], smsh[i, j, 2],
                               smsh[k, j, 0], smsh[k, j, 1], smsh[k, j, 2])
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
        """ Test construction of the mesh """
        h_sampl = 5
        v_sampl = 5
        idl = False
        alg = False
        smsh = KiteFaultSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                              idl, alg)
        self.assertTrue(np.all(~np.isnan(smsh[0, :, 0])))

        if PLOTTING:
            title = 'Simple case: No top alignment'
            ppp(self.profiles, smsh, title)

    def test_mesh_creation_with_alignment(self):
        """ Test construction of the mesh """
        h_sampl = 2.5
        v_sampl = 2.5
        idl = False
        alg = True
        smsh = KiteFaultSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                              idl, alg)
        self.assertTrue(np.any(np.isnan(smsh[0, :, 0])))

        if PLOTTING:
            title = 'Simple case: Top alignment'
            ppp(self.profiles, smsh, title)


class IdealizedATest(unittest.TestCase):

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'profiles04')
        self.profiles, _ = _read_profiles(path)

    def test_mesh_creation_no_alignment(self):
        """ Test construction of the mesh """
        h_sampl = 4
        v_sampl = 4
        idl = False
        alg = False
        smsh = KiteFaultSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                              idl, alg)
        self.assertTrue(np.all(~np.isnan(smsh[0, :, 0])))

        if PLOTTING:
            title = 'Simple mesh creation - no top alignment'
            ppp(self.profiles, smsh, title)

    def test_mesh_creation_with_alignment(self):
        """ Test construction of the mesh """
        h_sampl = 4
        v_sampl = 4
        idl = False
        alg = True
        smsh = KiteFaultSurface.from_profiles(self.profiles, v_sampl, h_sampl,
                                              idl, alg)
        self.assertTrue(np.any(np.isnan(smsh[0, :, 0])))

        if PLOTTING:
            title = 'Simple case: Top alignment'
            ppp(self.profiles, smsh, title)


class SouthAmericaSegmentTest(unittest.TestCase):

    def setUp(self):
        path = os.path.join(BASE_DATA_PATH, 'sam_seg6_slab')
        self.profiles, _ = _read_profiles(path)

    def test_mesh_creation(self):
        """ Create mesh from profiles for SA """
        sampling = 40
        idl = False
        alg = False
        smsh = KiteFaultSurface.from_profiles(self.profiles, sampling,
                                              sampling, idl, alg)
        idx = np.isfinite(smsh[:, :, 0])
        self.assertEqual(np.sum(np.sum(idx)), 202)

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
