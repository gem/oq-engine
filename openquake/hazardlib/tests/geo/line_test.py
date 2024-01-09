# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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
import unittest
import numpy as np
import matplotlib.pyplot as plt
from openquake.hazardlib import geo

PLOTTING = False


def _plott(rtra_prj, txy):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 1)
    tt = np.array(rtra_prj)
    plt.plot(txy[:, 0], txy[:, 1], '-')
    plt.plot(txy[:, 0], txy[:, 1], 'x', ms=2.0)
    plt.plot(tt[:, 0], tt[:, 1], 'o')
    for i, t in enumerate(tt):
        plt.text(t[0], t[1], f'{i}')
    ax.axis('equal')
    plt.show()

class LineResampleTestCase(unittest.TestCase):

    def test_resample(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.127183341091, 14.1421356237)
        p3 = geo.Point(0.134899286793, 0.262081472606, 35.3553390593)
        resampled = geo.Line([p1, p2, p3]).resample(10.0)
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 0.0635916705456, 7.07106781187)
        p3 = geo.Point(0.0, 0.127183341091, 14.1421356237)
        p4 = geo.Point(0.0449662998195, 0.172149398777, 21.2132034356)
        p5 = geo.Point(0.0899327195183, 0.217115442616, 28.2842712475)
        p6 = geo.Point(0.134899286793, 0.262081472606, 35.3553390593)
        p7 = geo.Point(0.17986642, 0.30704752, 42.42641368)
        expected = geo.Line([p1, p2, p3, p4, p5, p6, p7])
        self.assertEqual(expected, resampled)

    def test_resample_dense_trace(self):
        from .surface.data import atf_haiyuan_data
        # Create the line
        dat = atf_haiyuan_data.trace
        line = geo.Line([geo.Point(p[0], p[1]) for p in dat])
        # Resample
        computed = line.resample(2.)
        zro = np.zeros_like(computed.coo[:-1, 0])
        # Computing distances
        dst = geo.geodetic.distance(computed.coo[:-1, 0],
                                    computed.coo[:-1, 1], zro,
                                    computed.coo[1:, 0],
                                    computed.coo[1:, 1], zro)
        np.testing.assert_allclose(dst, 2.0, atol=0.02)
        if PLOTTING:
            _plott(computed.coo, line.coo)

    def test_resample_2(self):
        """
        Line made of 3 points (aligned in the same direction) equally spaced
        (spacing equal to 10 km). The resampled line contains 2 points
        (with spacing of 30 km) consistent with the number of points
        as predicted by n = round(20 / 30) + 1.
        """
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 0.089932202939476777)
        p3 = geo.Point(0.0, 0.1798644058789465)
        self.assertEqual(2, len(geo.Line([p1, p2, p3]).resample(30.0)))

    def test_resample_3(self):
        # Line made of 3 points (aligned in the same direction) equally spaced
        # (spacing equal to 10 km). The resampled line contains 1 point
        # (with spacing of 50 km) consistent with the number of points
        # as predicted by n = round(20 / 50) + 1, therefore a ValueError
        # is raised.
        p1 = geo.Point(0.0, 0.0)
        p2 = geo.Point(0.0, 0.089932202939476777)
        p3 = geo.Point(0.0, 0.1798644058789465)
        with self.assertRaises(ValueError):
            geo.Line([p1, p2, p3]).resample(50.0)


class LineCreationTestCase(unittest.TestCase):

    def test_one_point_needed(self):
        self.assertRaises(ValueError, geo.Line, [])

    def test_remove_adjacent_duplicates(self):
        p1 = geo.Point(0.0, 0.0, 0.0)
        p2 = geo.Point(0.0, 1.0, 0.0)
        p3 = geo.Point(0.0, 1.0, 0.0)
        p4 = geo.Point(0.0, 2.0, 0.0)
        p5 = geo.Point(0.0, 3.0, 0.0)
        p6 = geo.Point(0.0, 3.0, 0.0)
        expected = [p1, p2, p4, p5]
        self.assertEqual(expected, geo.Line([p1, p2, p3, p4, p5, p6]).points)


class LineResampleToNumPointsTestCase(unittest.TestCase):

    def test_simple(self):
        points = [geo.Point(0, 0), geo.Point(0.1, 0.3)]
        line = geo.Line(points).resample_to_num_points(3)
        expected_points = [geo.Point(0, 0), geo.Point(0.05, 0.15),
                           geo.Point(0.1, 0.3)]
        self.assertEqual(line.points, expected_points)
        line = geo.Line(points).resample_to_num_points(4)
        expected_points = [geo.Point(0, 0), geo.Point(0.0333333, 0.1),
                           geo.Point(0.0666666, 0.2), geo.Point(0.1, 0.3)]
        self.assertEqual(line.points, expected_points)

    def test_fewer_points(self):
        points = [geo.Point(i / 10., 0) for i in range(13)]
        line = geo.Line(points).resample_to_num_points(2)
        expected_points = [points[0], points[-1]]
        self.assertEqual(line.points, expected_points)
        line = geo.Line(points).resample_to_num_points(4)
        expected_points = points[::4]
        self.assertEqual(line.points, expected_points)

    def test_cutting_corners(self):
        p1 = geo.Point(0., 0.)
        p2 = p1.point_at(1, 0, 1)
        p3 = p2.point_at(1, 0, 179)
        p4 = p3.point_at(5, 0, 90)
        line = geo.Line([p1, p2, p3, p4]).resample_to_num_points(3)
        self.assertEqual(len(line), 3)

    def test_hangup(self):
        p1 = geo.Point(0.00899322032502, 0., 0.)
        p2 = geo.Point(0.01798644058385, 0., 1.)
        p3 = geo.Point(0.02697966087241, 0., 2.)
        line = geo.Line([p1, p2, p3]).resample_to_num_points(3)
        self.assertEqual(line.points, [p1, p2, p3])

    def test_single_segment(self):
        line = geo.Line([
            geo.Point(0., 0.00899322029302, 0.),
            geo.Point(0.03344582378948, -0.00936927115925, 4.24264069)
        ])
        line = line.resample_to_num_points(7)
        self.assertEqual(len(line), 7)


class LineLengthTestCase(unittest.TestCase):

    def test(self):
        line = geo.Line([geo.Point(0, 0), geo.Point(0, 1), geo.Point(1, 2)])
        length = line.get_length()
        expected_length = (line.points[0].distance(line.points[1]) +
                           line.points[1].distance(line.points[2]))
        self.assertEqual(length, expected_length)


class LineFromVectorTest(unittest.TestCase):

    def test(self):
        lons = np.array([10.0, 20.0, 30.])
        lats = np.array([40.0, 50.0, 60.])
        line = geo.Line.from_vectors(lons, lats)
        coo = np.array([[p.longitude, p.latitude] for p in line])
        np.testing.assert_almost_equal(lons, coo[:, 0])
        np.testing.assert_almost_equal(lats, coo[:, 1])

    def test_with_depths(self):
        lons = np.array([10.0, 20.0, 30.])
        lats = np.array([40.0, 50.0, 60.])
        deps = np.array([1.0, 2.0, 3.])
        line = geo.Line.from_vectors(lons, lats, deps)
        coo = np.array([[p.longitude, p.latitude, p.depth] for p in line])
        np.testing.assert_almost_equal(lons, coo[:, 0])
        np.testing.assert_almost_equal(lats, coo[:, 1])
        np.testing.assert_almost_equal(deps, coo[:, 2])


class RevertPointsTest(unittest.TestCase):

    def test(self):
        lons = np.array([1.0, 2.0, 3.])
        lats = np.array([3.0, 4.0, 5.])
        deps = np.array([6.0, 7.0, 8.])
        line = geo.Line.from_vectors(lons, lats, deps)
        line.flip()
        computed = [p.longitude for p in line.points]
        expected = [3., 2., 1.]
        self.assertEqual(computed, expected)
        np.testing.assert_equal(line.coo[:, 0], np.array(expected))


class LineKeepCornersTest(unittest.TestCase):
    def test(self):
        #
        #                  6 + d
        #                   /
        #                5 + c
        #                 /
        #              4 + b
        #               /
        #            3 + a
        #             /
        #  +----+----+
        #  0    1    2
        loa, laa = geo.geodetic.point_at(0.2, 0.0, 45., 10)  # 3
        lob, lab = geo.geodetic.point_at(loa, laa, 55., 10)  # 4
        loc, lac = geo.geodetic.point_at(lob, lab, 53., 10)  # 5
        lod, lad = geo.geodetic.point_at(loc, lac, 53., 10)  # 6
        lons = np.array([0.0, 0.1, 0.2, loa, lob, loc, lod])
        lats = np.array([0.0, 0.0, 0.0, laa, lab, lac, lad])
        line = geo.Line.from_vectors(lons, lats)
        line.keep_corners(4.0)
        coo = np.array([[p.longitude, p.latitude, p.depth] for p in line])
        idxs = [0, 2, 3, 6]
        expected = lons[idxs]
        np.testing.assert_almost_equal(expected, coo[:, 0])
        expected = lats[idxs]
        np.testing.assert_almost_equal(expected, coo[:, 1])


class ComputeTUTest(unittest.TestCase):

    def test_compute_tu_01(self):
        # The simplest test. Straight trace going from west to east.
        lons = np.array([0.0, 0.1, 0.2])
        lats = np.array([0.0, 0.0, 0.0])
        line = geo.Line.from_vectors(lons, lats)
        line.keep_corners(4.0)

        # Prepare the mesh
        coo = np.array([[0.2, 0.1]])
        mesh = geo.Mesh(coo[:, 0], coo[:, 1])

        # Compute the TU coordinates
        tupp, uupp, wei = line.get_tu(mesh)
        expected_t = geo.geodetic.distance(0.2, 0.0, 0.0,
                                           coo[0, 0], coo[0, 1], 0.0)
        expected_u = geo.geodetic.distance(0.0, 0.0, 0.0,
                                           coo[0, 0], 0.0, 0.0)

        # Test
        self.assertAlmostEqual(-expected_t, tupp[0], places=4)
        self.assertAlmostEqual(expected_u, uupp[0], places=4)

    def test_compute_tu_02(self):

        # Prepare the section trace
        loa, laa = geo.geodetic.point_at(0.2, 0.0, 45., 20)
        lons = np.array([0.0, 0.1, 0.2, loa])
        lats = np.array([0.0, 0.0, 0.0, laa])
        line = geo.Line.from_vectors(lons, lats)
        line.keep_corners(4.0)

        # Prepare the mesh
        coo = np.array([[0.3, 0.0], [0.2, -0.1], [0.4, 0.3]])
        mesh = geo.Mesh(coo[:, 0], coo[:, 1])

        # Compute the TU coordinates
        tupp, u_upp, wei = line.get_tu(mesh)

        # TODO add test

    def test_compute_tu_03(self):

        # Prepare the section trace
        loa, laa = geo.geodetic.point_at(0.2, 0.0, 45., 20)
        lons = np.array([0.0, 0.1, 0.2, loa])
        lats = np.array([0.0, 0.0, 0.0, laa])
        line = geo.Line.from_vectors(lons, lats)
        line.keep_corners(4.0)

        # Get the site collection
        mesh, plons, plats = get_mesh(-0.5, 1.0, -0.5, 1.0, 0.005)

        # Compute the TU coordinates
        tupp, uupp, wei = line.get_tu(mesh)

        # Plotting results
        if PLOTTING:
            num = 10
            z = np.reshape(tupp, plons.shape)
            label = 'test_compute_tu_03 - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            z = np.reshape(uupp, plons.shape)
            label = 'test_compute_tu_03 - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)

    def test_compute_tu_figure04(self):

        # Get line
        lons, lats, line = get_figure04_line()

        # Get the mesh
        mesh, plons, plats = get_mesh(-0.6, 0.6, -1.0, 0.4, 0.01)

        # Compute the TU coordinates
        tupp, uupp, wei = line.get_tu(mesh)

        if PLOTTING:
            num = 10
            # T
            z = np.reshape(tupp, plons.shape)
            label = 'test_compute_tu_03 - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # U
            z = np.reshape(uupp, plons.shape)
            label = 'test_compute_tu_03 - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)


class ComputeUiTiTest(unittest.TestCase):
    """
    For test 1 we use the same mapping of sites used for test 01 in
    ComputeWeightsTest.
    """

    def test_uiti_01(self):

        # Prepare the trace
        lons = np.array([0.0, 0.2])
        lats = np.array([0.0, 0.0])
        line = geo.Line([geo.Point(lo, la) for lo, la in zip(lons, lats)])

        # Prepare the mesh
        coo = np.array([[0.0, 0.05], [0.2, 0.0], [0.3, -0.05],
                        [0.1, -0.1], [0.3, 0.05]])
        mesh = geo.Mesh(coo[:, 0], coo[:, 1])

        # slen, uhat and that as expected
        slen, uhat, that = line.get_tu_hat()
        np.testing.assert_almost_equal(np.array([[1, 0, 0]]), uhat, decimal=5)

        # Now computing ui and ti
        ui, ti = line.get_ui_ti(mesh, uhat, that)

        self.assertEqual((1, 5), ui.shape)
        self.assertEqual((1, 5), ti.shape)

        # TODO add test

    def test_uiti_02(self):

        # Prepare the trace
        lons = np.array([0.0, 0.2, 0.25])
        lats = np.array([0.0, 0.0, 0.05])
        line = geo.Line([geo.Point(lo, la) for lo, la in zip(lons, lats)])

        # Get the mesh
        mesh, plons, plats = get_mesh(-0.4, 0.6, -0.2, 0.3, 0.005)

        # slen, uhat and that as expected
        slen, uhat, that = line.get_tu_hat()

        # Now computing ui and ti
        ui, ti = line.get_ui_ti(mesh, uhat, that)

        # TODO add test

        # Plot
        if PLOTTING:
            label = 'test_uiti_02 - ui first segment'
            plot_pattern(lons, lats, ui[0], plons, plats, label)
            label = 'test_uiti_02 - ui second segment'
            plot_pattern(lons, lats, ui[1], plons, plats, label)
            label = 'test_uiti_02 - ti first segment'
            plot_pattern(lons, lats, ti[0], plons, plats, label)
            label = 'test_uiti_02 - ti second segment'
            plot_pattern(lons, lats, ti[1], plons, plats, label)


class ComputeWeightsTest(unittest.TestCase):

    def test_weights_01(self):
        # Simple test with the following sites:
        #
        #       x site 0            x site 4
        #       |
        #       ---------------     x site 1
        #                     |
        #                     |
        #                     x site 2
        #
        #             x site 3
        #
        n_seg = 1
        n_sites = 5
        ui = np.zeros((n_seg, n_sites))
        ti = np.zeros((n_seg, n_sites))
        ui[0, :] = np.array([-0.1, 30.0, 20.1, 10.0, 30.0])
        ti[0, :] = np.array([5.0, 0.0, -5.0, -10.0, 5.0])
        segl = np.array([20.0])
        wei, iot = geo.line.get_ti_weights(ui, ti, segl)

        # Compute weight for site 1
        i = 0
        sid = 1
        expected = 1 / (ui[i, sid] - segl[i]) - 1 / ui[i, sid]
        msg = 'Weight for site 1 is wrong'
        self.assertAlmostEqual(expected, wei[i, sid], msg)

        # Compute weight for site 2
        i = 0
        sid = 2
        expected = (np.arctan((segl[i] - ui[i, sid]) / ti[i, sid]) -
                    np.arctan(- ui[i, sid] / ti[i, sid]))
        expected *= 1 / ti[i, sid]
        msg = 'Weight for site 2 is wrong'
        self.assertAlmostEqual(expected, wei[i, sid], msg)

    def test_weights_02(self):
        # Check the weights for test_compute_tu_03

        # Prepare the section trace
        loa, laa = geo.geodetic.point_at(0.2, 0.0, 45., 20)
        lons = np.array([0.0, 0.1, 0.2, loa])
        lats = np.array([0.0, 0.0, 0.0, laa])
        line = geo.Line.from_vectors(lons, lats)
        line.keep_corners(4.0)

        # Get the site collection
        mesh, plons, plats = get_mesh(-0.5, 1.0, -0.5, 1.0, 0.01)

        # slen, uhat and that
        slen, uhat, that = line.get_tu_hat()

        # Compute ui and ti
        ui, ti = line.get_ui_ti(mesh, uhat, that)

        # Compute weights
        wei, iot = geo.line.get_ti_weights(ui, ti, slen)

        # TODO add test

        if PLOTTING:
            label = 'test_weights_02 - weights first segment'
            plot_pattern(lons, lats, wei[0], plons, plats, label)
            label = 'test_weights_02 - weights second segment'
            plot_pattern(lons, lats, wei[1], plons, plats, label)

    def test_weights_figure04(self):

        # Get line
        lons, lats, line = get_figure04_line()

        # Get the site collection
        mesh, plons, plats = get_mesh(-0.2, 0.6, -0.8, 0.1, 0.0025)

        # slen, uhat and that
        slen, uhat, that = line.get_tu_hat()

        # Compute ui and ti
        ui, ti = line.get_ui_ti(mesh, uhat, that)

        # Compute weights
        wei, iot = geo.line.get_ti_weights(ui, ti, slen)

        # Total weights
        weit = np.sum(wei, axis=0)

        if PLOTTING:
            label = 'test_weights_figure04 - weights first segment'
            plot_pattern(lons, lats, np.log10(wei[0]), plons, plats, label)
            label = 'test_weights_figure04 - weights second segment'
            plot_pattern(lons, lats, np.log10(wei[1]), plons, plats, label)
            label = 'test_weights_figure04 - weights third segment'
            plot_pattern(lons, lats, np.log10(wei[2]), plons, plats, label)
            label = 'test_weights_figure04 - sum of weights'
            plot_pattern(lons, lats, np.log10(weit), plons, plats, label)


class LineSphereIntersectionTest(unittest.TestCase):

    def test01(self):
        """ See example https://www.geogebra.org/m/mwanwvwj """
        pnt0 = np.array([13, 2, 9])
        # pnt1 = np.array([7, -4, 6])
        pnt1 = np.array([5, -6, 5])
        ref_pnt = np.array([0, 0, 0])
        distance = 10.
        from openquake.hazardlib.geo.line import find_t
        computed = find_t(pnt0, pnt1, ref_pnt, distance)
        expected = np.array([6.92, -4.08, 5.96])
        np.testing.assert_almost_equal(computed, expected, decimal=1)


def get_figure04_line():
    """
    Returns the line describing the rupture trace in Figure 4 of Spudich and
    Chiou (2015).
    :returns:
        A tuple with two :class:`numpy.ndarray` instances (longitudes and
        latitudes of the pooints defininf the trace) and
        :class:`openquake.hazardlib.geo.line.Line` instance
    """

    # Projection
    oprj = geo.utils.OrthographicProjection
    proj = oprj.from_lons_lats(np.array([-0.1, 0.1]), np.array([-0.1, 0.1]))

    # Prepare the section trace
    px = np.array([0.0, 0.0, 12.68, 35.66])
    py = np.array([0.0, -40.0, -67.19, -86.47])
    lons, lats = proj(px, py, reverse=True)
    line = geo.Line.from_vectors(lons, lats)
    return lons, lats, line


def get_mesh(lomin, lomax, lamin, lamax, step):
    """
    Create a site collection
    """
    plons = []
    plats = []
    for lo in np.arange(lomin, lomax, step):
        tlo = []
        tla = []
        for la in np.arange(lamin, lamax, step):
            tlo.append(lo)
            tla.append(la)
        plons.append(tlo)
        plats.append(tla)
    plons = np.array(plons)
    plats = np.array(plats)
    mesh = geo.Mesh(plons.flatten(), plats.flatten())
    return mesh, plons, plats


def plot_pattern(lons, lats, z, plons, plats, label, num=5, show=True):
    """
    :param lons:
        Traces longitudes
    :param lats:
        Traces latitudes
    :param z:
        Grid scalar quantity
    :param plons:
        2D Grid longitudes
    :param plats:
        2D Grid latitudes
    :param scoo:
        Sites coordinates
    :param label:
        Label
    """

    # If necessary, make lons and lats iterable
    from collections.abc import Iterable
    if len(lons) and not isinstance(lons[0], Iterable):
        lons = [lons]
        lats = [lats]

    # Colormap
    cmap = plt.get_cmap('coolwarm', 11)

    # Plot
    fig, ax = plt.subplots()
    fig.set_size_inches(8, 6)
    z = np.reshape(z, plons.shape)
    cs = plt.contour(plons, plats, z, num, colors='k')
    ax.clabel(cs, inline=True, fontsize=10)
    if len(lons):
        for los, las in zip(lons, lats):
            ax.plot(los, las, '-r')
            ax.plot(los[0], las[0], 'g', marker='$s$', mfc='none', ms=5)
            ax.plot(los[-1], las[-1], 'r', marker='$e$', mfc='none', ms=5)
    ax.scatter(plons.flatten(), plats.flatten(), c=z.flatten(), marker='.',
               s=0.5, cmap=cmap)
    ax.set_title(f'Test: {label}')
    ax.axis('equal')
    if show:
        plt.show()
    return ax



