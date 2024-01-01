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

import unittest
import numpy as np
import matplotlib.pyplot as plt

from openquake.hazardlib import geo
from openquake.hazardlib.geo.multiline import MultiLine
from openquake.hazardlib.tests.geo.line_test import plot_pattern, get_mesh


PLOTTING = False


class OneLineTestCase(unittest.TestCase):

    def setUp(self):

        self.line = geo.Line([geo.Point(0.2, 0.05), geo.Point(0.0, 0.05)])
        self.ml = MultiLine([self.line])

    def test_max_u(self):
        self.ml.set_u_max()
        dst = geo.geodetic.geodetic_distance([self.line.points[0].longitude],
                                             [self.line.points[0].latitude],
                                             [self.line.points[1].longitude],
                                             [self.line.points[1].latitude])
        np.testing.assert_allclose(self.ml.u_max, dst, atol=1e-4)


class MultiLineTestCase(unittest.TestCase):
    """
    Test the calculation of the strike direction for a list of polylines
    (i.e. OQ's Line objects)
    """

    def setUp(self):

        # Prepare the section traces
        loa, laa = geo.geodetic.point_at(0.2, 0.0, 45., 10)
        lob, lab = geo.geodetic.point_at(loa, laa, 45., 20)
        loc, lac = geo.geodetic.point_at(lob, lab, 90., 30)

        lonsa = np.array([0.0, 0.1, 0.2, loa])
        latsa = np.array([0.0, 0.0, 0.0, laa])
        linea = geo.Line.from_vectors(lonsa, latsa)
        linea.keep_corners(4.0)

        lonsb = np.array([loc, lob])
        latsb = np.array([lac, lab])
        lineb = geo.Line.from_vectors(lonsb, latsb)
        lineb.keep_corners(4.0)

        self.lines = [linea, lineb]

    def test_get_strike_01(self):
        """ get strike 01 """

        # Create the multiline instance and get the prevalent strike
        ml = MultiLine(self.lines)
        revert = ml.set_overall_strike()

        # Testing
        self.assertTrue(ml.strike_to_east)
        msg = 'Lines to flip are wrong'
        np.testing.assert_equal(revert, [False, True], msg)

        if PLOTTING:
            fig, ax = plt.subplots()
            fig.set_size_inches(6, 4)
            for line in self.lines:
                ax.plot(line.coo[:, 0], line.coo[:, 1], '-', color='grey')
                ax.plot(line.coo[0, 0], line.coo[0, 1], 'or')
                ax.plot(line.coo[-1, 0], line.coo[-1, 1], 'xb')
            plt.show()

    def test_set_origin(self):
        """ test computing origin """

        # Create the multiline instance and get the origin
        ml = MultiLine(self.lines)
        ml._set_origin()
        expected = [0.0, 0.0]
        np.testing.assert_almost_equal([ml.olon, ml.olat], expected)

    def test_coordinate_shift(self):
        """ test calculation of coordinate shift """

        # Creating the multiline and computing the shift
        ml = MultiLine(self.lines)
        ml._set_coordinate_shift()

        # Computing the distance between the origin and the endnode of the
        # second polyline
        ggdst = geo.geodetic.geodetic_distance
        lo = ml.lines[1].points[0].longitude
        la = ml.lines[1].points[0].latitude
        dst = ggdst(0, 0, lo, la)

        # Set the origin and compute the overall strike and the azimuths of
        # the polylines composing the multiline instance
        ml._set_origin()
        ggazi = geo.geodetic.azimuth
        azim = ggazi(ml.olon, ml.olat, lo, la)
        delta = abs(ml.overall_strike - azim)
        computed = dst * np.cos(np.radians(delta))

        # Testing
        np.testing.assert_almost_equal([0, computed], ml.shift)

    def test_set_tu(self):

        # Get the coords of the lines composing the multiline
        lons = []
        lats = []
        for line in self.lines:
            lons.append(line.coo[:, 0])
            lats.append(line.coo[:, 1])

        # Create the site collection
        mesh, plons, plats = get_mesh(-0.3, 0.8, -0.3, 0.8, 0.005)

        # Create the multiline and calculate the T and U coordinates
        ml = MultiLine(self.lines)
        ml.set_tu(mesh)
        uupp = ml.uut
        tupp = ml.tut

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(uupp, plons.shape)
            label = 'test_set_tu - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(tupp, plons.shape)
            label = 'test_set_tu - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)

    def test_set_tu_spot_checks(self):

        mesh = geo.Mesh(np.array([0.0]), np.array([0.0]))
        ml = MultiLine(self.lines)
        ml.set_tu(mesh)
        uupp = ml.uut
        np.testing.assert_almost_equal([0.0011659], uupp)

    def test_tu_figure09(self):

        # Get the multiline
        lons, lats, lines = get_lines_figure09()

        # Create the site collection
        mesh, plons, plats = get_mesh(-0.2, 0.2, -0.2, 0.2, 0.0025)

        # Create the multiline and calculate the T and U coordinates
        ml = MultiLine(lines)
        ml.set_tu(mesh)
        uupp = ml.uut
        tupp = ml.tut

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(uupp, plons.shape)
            label = 'test_tu_figure09 - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(tupp, plons.shape)
            label = 'test_tu_figure09 - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)

    def test_tu_figure08(self):

        # Get the multiline
        lons, lats, lines = get_lines_figure08()

        # Create the site collection
        mesh, plons, plats = get_mesh(-0.6, 0.6, -0.6, 0.6, 0.005)

        # Create the multiline and calculate the T and U coordinates
        ml = MultiLine(lines)
        ml.set_tu(mesh)
        uupp = ml.uut
        tupp = ml.tut

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(uupp, plons.shape)
            label = 'test_tu_figure08 - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(tupp, plons.shape)
            label = 'test_tu_figure08 - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)


def get_lines_figure09():
    """
    Returns the lines describing the rupture traces in Figure 9 of Spudich and
    Chiou (2015).
    :returns:
        A tuple with two lists of :class:`numpy.ndarray` instances (longitudes
        and latitudes of the points defining the trace) and a list of
        :class:`openquake.hazardlib.geo.line.Line` instances
    """
    lons = []
    lats = []
    lines = []

    # Projection
    oprj = geo.utils.OrthographicProjection
    proj = oprj.from_lons_lats(np.array([-0.1, 0.1]), np.array([-0.1, 0.1]))

    # Section trace 1
    px = np.array([8, -9])
    py = np.array([-15, -11])
    los, las, line = _get_lola(px, py, proj)
    lons.append(los)
    lats.append(las)
    lines.append(line)

    # Section trace 2
    px = np.array([6, -9])
    py = np.array([-10, -5])
    los, las, line = _get_lola(px, py, proj)
    lons.append(los)
    lats.append(las)
    lines.append(line)

    return lons, lats, lines


def _get_lola(px, py, proj):
    los, las = proj(px, py, reverse=True)
    line = geo.Line.from_vectors(los, las)
    return los, las, line


def get_lines_figure08():
    # Digitized using https://automeris.io/WebPlotDigitizer/

    lons = []
    lats = []
    lines = []

    # Projection
    oprj = geo.utils.OrthographicProjection
    proj = oprj.from_lons_lats(np.array([-0.1, 0.1]), np.array([-0.1, 0.1]))

    px = np.array([-2.1416918, -40.01534, -43.44729])
    py = np.array([13.50913, 47.34280, 55.86207])
    los, las, line = _get_lola(px, py, proj)
    lons.append(los)
    lats.append(las)
    lines.append(line)

    px = np.array([-0.1617771, -1.663781])
    py = np.array([-0.6085193, 18.37728])
    los, las, line = _get_lola(px, py, proj)
    lons.append(los)
    lats.append(las)
    lines.append(line)

    px = np.array([-2.386583, 47.70247])
    py = np.array([13.99594, -29.81744])
    los, las, line = _get_lola(px, py, proj)
    lons.append(los)
    lats.append(las)
    lines.append(line)

    return lons, lats, lines
