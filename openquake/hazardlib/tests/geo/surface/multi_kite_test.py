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
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from openquake.hazardlib.nrml import read
from openquake.hazardlib.geo.geodetic import (
    geodetic_distance, npoints_towards)
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.tests.geo.surface.kite_fault_test import (
    _read_profiles)
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.surface.kite_fault import (
    KiteSurface, _fix_profiles, _create_mesh, get_new_profiles)
from openquake.hazardlib.tests.geo.surface.kite_fault_test import plot_mesh_2d

NS = "{http://openquake.org/xmlns/nrml/0.5}"
BASE_PATH = os.path.dirname(__file__)
BASE_DATA_PATH = os.path.join(BASE_PATH, 'data')
PLOTTING = False
OVERWRITE = False
aae = np.testing.assert_almost_equal


def new_profiles(milo, malo, mila, mala, step=0.01):
    clo = []
    cla = []
    for lo in np.arange(milo, malo, step):
        tlo = []
        tla = []
        for la in np.arange(mila, mala, step):
            tlo.append(lo)
            tla.append(la)
        clo.append(tlo)
        cla.append(tla)
    clo = np.array(clo)
    cla = np.array(cla)
    mesh = Mesh(lons=clo.flatten(), lats=cla.flatten())
    return clo, cla, mesh


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

        # Create the surface and mesh needed for the test
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

    def test_get_area(self):
        computed = self.msrf.get_area()
        length = geodetic_distance(0.0, 0.0, 0.3, 0.0)
        expected = length * 20.0 + 100
        perc_diff = abs(computed - expected) / computed
        msg = 'Multi fault surface: area is wrong'
        self.assertTrue(perc_diff < 0.1, msg=msg)


class MultiSurfaceWithNaNsTestCase(unittest.TestCase):

    NAME = 'MultiSurfaceWithNaNsTestCase'

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
        self.clo, self.cla, mesh = new_profiles(-71.8, -69, 19.25, 20.25, 0.01)
        # Define multisurface and mesh of sites
        self.srfc50 = srfc50
        self.srfc51 = srfc51
        self.msrf = MultiSurface([srfc50, srfc51])
        self.mesh = mesh
        self.los = [self.msrf.surfaces[0].mesh.lons,
                    self.msrf.surfaces[1].mesh.lons]
        self.las = [self.msrf.surfaces[0].mesh.lats,
                    self.msrf.surfaces[1].mesh.lats]

    def test_get_edge_set(self):
        # The vertexes of the expected edges are the first and last vertexes of
        # the topmost row of the mesh
        expected = [np.array([[-70.33, 19.65, 0.],
                              [-70.57722702, 19.6697801, 0.0]]),
                    np.array([[-70.10327766, 19.67957463, 0.0],
                              [-70.33, 19.65, 0.0]])]
        self.msrf._set_tor()

        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            for sfc in self.msrf.surfaces:
                col = np.random.rand(3)
                mesh = sfc.mesh
                ax.plot(mesh.lons, mesh.lats, '.', color=col)
                ax.plot(mesh.lons[0, :],  mesh.lats[0, :], lw=3)
            for line in self.msrf.tors.lines:
                ax.plot(line.coo[:, 0], line.coo[:, 1], 'x-r')
            plt.show()

        # Note that method is executed when the object is initialized
        for es, expct in zip(self.msrf.tors.lines, expected):
            np.testing.assert_array_almost_equal(es.coo, expct, decimal=2)

    def test_get_strike(self):
        # Since the two surfaces dip to the north, we expect the strike to
        # point toward W
        msg = 'Multi fault surface: strike is wrong'
        strike = self.msrf.get_strike()
        self.assertAlmostEqual(268.867, strike, places=2, msg=msg)

    def test_get_dip(self):
        dip = self.msrf.get_dip()
        expected = 69.649
        msg = 'Multi fault surface: dip is wrong'
        aae(dip, expected, err_msg=msg, decimal=2)

    def test_get_width(self):
        """ check the width """
        # Measuring the width
        width = self.msrf.get_width()
        np.testing.assert_allclose(width, 20.44854)

    def test_get_area(self):
        # The area is computed by summing the areas of each section.
        a1 = self.msrf.surfaces[0].get_area()
        a2 = self.msrf.surfaces[1].get_area()
        area = self.msrf.get_area()
        aae(a1 + a2, area)

    def test_get_bounding_box(self):
        bb = self.msrf.get_bounding_box()
        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            ax.plot([bb.west, bb.east, bb.east, bb.west],
                    [bb.south, bb.south, bb.north, bb.north], '-')
            ax.plot(self.los[0], self.las[0], '.')
            ax.plot(self.los[1], self.las[1], '.')
            plt.show()
        aae([bb.west, bb.east, bb.south, bb.north],
            [-70.5772, -70.1032, 19.650, 19.7405], decimal=2)

    def test_get_middle_point(self):
        # The computed middle point is the mid point of the first surface
        midp = self.msrf.get_middle_point()
        expected = [-70.453372, 19.695377, 10.2703]
        computed = [midp.longitude, midp.latitude, midp.depth]
        aae(expected, computed, decimal=4)

    def test_get_surface_boundaries01(self):
        # This checks the boundary of the first surface. The result is checked
        # visually
        blo, bla = self.srfc50.get_surface_boundaries()
        # Saving data
        fname = os.path.join(BASE_PATH, 'results', 'results_t01.npz')
        if OVERWRITE:
            np.savez_compressed(fname, blo=blo, bla=bla)
        # Load expected results
        er = np.load(fname)
        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            ax.plot(er['blo'], er['bla'], '-r')
            plt.show()
        # Testing
        aae(er['blo'], blo, decimal=1)
        aae(er['bla'], bla, decimal=1)

    @unittest.skip("Differences betweeen various architectures")
    def test_get_surface_boundaries(self):
        # The result is checked visually
        blo, bla = self.msrf.get_surface_boundaries()
        # Saving data
        fname = os.path.join(BASE_PATH, 'results', 'results_t02.npz')
        if OVERWRITE:
            np.savez_compressed(fname, blo=blo, bla=bla)
        # Load expected results
        er = np.load(fname)
        if PLOTTING:
            _, ax = plt.subplots(1, 1)
            ax.plot(blo, bla, '-r')
            ax.plot(self.los[0], self.las[0], '.')
            ax.plot(self.los[1], self.las[1], '.')
            plt.show()
        # Testing
        aae(er['blo'], blo, decimal=2)
        aae(er['bla'], bla, decimal=2)

    def test_get_rx(self):

        # Results visually inspected
        dst = self.msrf.get_rx_distance(self.mesh)

        if PLOTTING:
            title = f'{type(self).__name__} - Rx'
            _plt_results(self.clo, self.cla, dst, self.msrf, title)

        # Saving data
        fname = os.path.join(BASE_PATH, 'results', 'results_msf_nan_rx.npz')
        if OVERWRITE:
            np.savez_compressed(fname, rx=dst)

        # Load expected results
        er = np.load(fname)

        # Testing
        aae(er['rx'], dst, decimal=1)

    def test_get_ry0(self):

        # Results visually inspected
        dst = self.msrf.get_ry0_distance(self.mesh)

        if PLOTTING:
            title = f'{type(self).__name__} - Ry0'
            fig, ax = _plt_results(self.clo, self.cla, dst, self.msrf, title)
            for line in self.msrf.tors.lines:
                ax.plot(line.coo[:, 0], line.coo[:, 1], '-r', lw=3)
            self.msrf.tors._set_origin()
            ax.plot(self.msrf.tors.olon, self.msrf.tors.olat, 'o')
            plt.show()

        # Saving data
        fname = os.path.join(BASE_PATH, 'results', 'results_msf_nan_ry0.npz')
        if OVERWRITE:
            np.savez_compressed(fname, rx=dst)

        # Load expected results
        er = np.load(fname)

        # Testing
        aae(er['rx'], dst, decimal=1)


class NZLTestCase(unittest.TestCase):

    def setUp(self):

        # Create converter
        self.rms = 2.5
        sconv = SourceConverter(investigation_time=1.,
                                rupture_mesh_spacing=self.rms)

        # Read geometry model. It contains a list of surfaces, instances of
        # :class:`openquake.hazardlib.geo.surface.KiteFault`
        fname = 'sections_rupture200_sections.xml'
        fname = os.path.join(BASE_DATA_PATH, fname)
        gmodel = to_python(fname, sconv)

        # Create the surface
        sfcs = []
        for sec in gmodel.sections:
            sfcs.append(gmodel.sections[sec])
        self.msrf = MultiSurface(sfcs)

        # Create second surface
        keys = list(gmodel.sections)
        self.sec_id = keys[1]
        sfcs2 = [gmodel.sections[self.sec_id]]
        self.msrf2 = MultiSurface(sfcs2)

    def test_nzl_tors(self):

        # Set the rupture traces
        self.msrf._set_tor()

        if PLOTTING:
            # Plotting profiles and surfaces
            _, ax = plt.subplots(1, 1)
            for sfc in self.msrf.surfaces:
                plot_mesh_2d(ax, sfc)
                for pro in sfc.profiles:
                    ax.plot(pro.coo[:, 0], pro.coo[:, 1], '--b')
            # Plotting traces
            for line in self.msrf.tors.lines:
                col = np.random.rand(3)
                coo = line.coo
                ax.plot(coo[:, 0], coo[:, 1], color=col)
                ax.plot(coo[0, 0], coo[0, 1], marker='$s$', color=col)
            plt.show()

    def test_nzl_1_get_rx(self):
        """ Testing the calculation of the rx distance """

        # Set the output name
        title = f'{type(self).__name__} - Rx - Surface 1'
        fname = os.path.join(BASE_PATH, 'results', 'results_nzl_1_rx.txt')

        # Test
        _test_nzl_get_rx(self.msrf, title, fname)

    def test_nzl_2_profiles(self):
        """ Testing the resampled profiles """

        # Name of the file with the Geometry Model
        fname = 'sections_rupture200_sections.xml'
        fname = os.path.join(BASE_DATA_PATH, fname)

        # Read data and get resampled profiles
        profiles = _get_profiles(fname)
        prof = profiles[self.sec_id][0]
        rprof, ref_idx = _fix_profiles(prof, self.rms, False, False)

        # Save results
        fname0 = 'results_nzl_2_rprof_0.txt'
        fname0 = os.path.join(BASE_PATH, 'results', fname0)
        fname2 = 'results_nzl_2_rprof_2.txt'
        fname2 = os.path.join(BASE_PATH, 'results', fname2)
        fnamei = 'results_nzl_2_ref_idx.txt'
        fnamei = os.path.join(BASE_PATH, 'results', fnamei)
        if OVERWRITE:
            np.savetxt(fname0, rprof[0], fmt='%.8e')
            np.savetxt(fname2, rprof[2], fmt='%.8e')
            np.savetxt(fnamei, np.array([ref_idx]), fmt='%.8e')

        # Check profiles
        expected_prof0 = np.loadtxt(fname0)
        aae(expected_prof0, rprof[0], decimal=3)
        expected_prof2 = np.loadtxt(fname2)
        aae(expected_prof2, rprof[2], decimal=3)
        expected_refi = np.loadtxt(fnamei)
        aae(expected_refi, ref_idx, decimal=3)

    def test_nzl_2_sfc_building(self):
        """ Testing the mesh """

        # Name of the file with the Geometry Model
        fname = 'sections_rupture200_sections.xml'
        fname = os.path.join(BASE_DATA_PATH, fname)

        # Rupture mesh spacing
        rms = self.rms

        # Get profiles
        profiles = _get_profiles(fname)
        prof = profiles[self.sec_id][0]
        rprof, ref_idx = _fix_profiles(prof, rms, False, idl=False)

        # Create mesh (note that we flip it to replicate the right_hand rule
        # fix). The 'get_new_profiles' function provides the same results on
        # MacOS and Linux
        msh = _create_mesh(rprof, ref_idx, rms, idl=False)
        tmp = np.fliplr(msh[:, :, 0])
        mback = get_new_profiles(rprof, ref_idx, rms, idl=False)

        # Save results
        fname = 'results_nzl_2_mesh.txt'
        fname = os.path.join(BASE_PATH, 'results', fname)
        fnameb = 'results_nzl_2_mesh_back.txt'
        fnameb = os.path.join(BASE_PATH, 'results', fnameb)
        if OVERWRITE:
            np.savetxt(fname, tmp, fmt='%.8e')
            np.savetxt(fnameb, np.array(mback)[:, :, 0], fmt='%.8e')

        # Check the mesh
        expected_mshb = np.loadtxt(fnameb)
        aae(expected_mshb, np.array(mback)[:, :, 0], decimal=3)
        expected_msh = np.loadtxt(fname)
        aae(expected_msh, self.msrf2.surfaces[0].mesh.lons, decimal=3)

    def test_nzl_2_get_rx(self):

        # Saving the mesh
        fname_lo = 'results_nzl_2_mesh_lons.txt'
        fname_lo = os.path.join(BASE_PATH, 'results', fname_lo)
        if OVERWRITE:
            np.savetxt(fname_lo, self.msrf2.surfaces[0].mesh.lons, fmt='%.8e')

        # Checking the mesh
        expected_lons = np.loadtxt(fname_lo)
        aae(expected_lons, self.msrf2.surfaces[0].mesh.lons, decimal=3)

        # Checking Rx
        title = f'{type(self).__name__} - Rx - Surface 2'
        fname = os.path.join(BASE_PATH, 'results', 'results_nzl_2_rx.txt')
        _test_nzl_get_rx(self.msrf2, title, fname)


def _test_nzl_get_rx(msrf, title, fname):

    # Mesh of sites
    mlons = []
    mlats = []
    step = 0.01
    for lo in np.arange(165, 168, step):
        tlo = []
        tla = []
        for la in np.arange(-46.0, -44.5, step):
            tlo.append(lo)
            tla.append(la)
        mlons.append(tlo)
        mlats.append(tla)
    mlons = np.array(mlons)
    mlats = np.array(mlats)
    mesh = Mesh(lons=mlons.flatten(), lats=mlats.flatten())

    # Compute the Rx distance
    dst = msrf.get_rx_distance(mesh)

    if PLOTTING:
        _plt_results(mlons, mlats, dst, msrf, title, boundary=False)
        plt.show()

    # We did not have a way to compute these results independently
    if OVERWRITE:
        np.savetxt(fname, dst, fmt='%.8e')

    # Load expected results
    dst_expected = np.loadtxt(fname)

    dst_expected = np.sort(dst_expected.flatten())
    dst = np.sort(dst.flatten())

    # Testing
    aae(dst_expected, dst, decimal=3)


def _plt_results(clo, cla, dst, msrf, title, boundary=True):
    """ Plot results """
    fig, ax = plt.subplots(1, 1)
    plt.scatter(clo, cla, c=dst, edgecolors='none', s=15, cmap=cm.coolwarm)
    for srf in msrf.surfaces:
        plot_mesh_2d(ax, srf)
    if boundary:
        lo, la = msrf.get_surface_boundaries()
        plt.plot(lo, la, '-r')
    z = np.reshape(dst, clo.shape)
    cs = plt.contour(clo, cla, z, 10, colors='k', alpha=.5)
    _ = plt.clabel(cs)
    plt.title(title)
    return fig, ax


def _get_profiles(fname):
    """ Gets profiles from a Geometry Model """
    [node] = read(fname)
    all_profiles = {}
    # Parse file
    for section in node:
        if section.tag == f"{NS}section":
            # Parse the surfaces in each section
            for surface in section:
                section_profiles = []
                if surface.tag == f"{NS}kiteSurface":
                    # Parse the profiles for each surface
                    profiles = []
                    for profile in surface:
                        # Get poslists
                        for points in profile.LineString:
                            pnts = np.array(~points)
                            rng = range(0, len(pnts), 3)
                            pro = Line([Point(pnts[i], pnts[i+1], pnts[i+2])
                                        for i in rng])
                            profiles.append(pro)
                    section_profiles = [profiles]
            all_profiles[section['id']] = section_profiles
    return all_profiles
