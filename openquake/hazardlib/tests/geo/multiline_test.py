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

from openquake.hazardlib import geo
from openquake.hazardlib.geo.multiline import MultiLine
from openquake.hazardlib.tests.geo.line_test import plot_pattern, get_mesh


PLOTTING = False


class OneLineTestCase(unittest.TestCase):

    def setUp(self):
        self.line = geo.Line([geo.Point(0.2, 0.05), geo.Point(0.0, 0.05)])
        self.ml = MultiLine([self.line])

    def test_u_max(self):
        dst = geo.geodetic.geodetic_distance([self.line.points[0].longitude],
                                             [self.line.points[0].latitude],
                                             [self.line.points[1].longitude],
                                             [self.line.points[1].latitude])
        np.testing.assert_allclose(self.ml.set_u_max(), dst, atol=1e-4)

  
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

    def test_get_tuw(self):
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
        ts, us = ml.get_tu(mesh)

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(us, plons.shape)
            label = 'test_get_ut - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(ts, plons.shape)
            label = 'test_get_ut - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)

    def test_tu_figure09(self):

        # Get the multiline
        lons, lats, lines = get_lines_figure09()

        # Create the site collection
        mesh, plons, plats = get_mesh(-0.2, 0.2, -0.2, 0.2, 0.0025)

        # Create the multiline and calculate the T and U coordinates
        ml = MultiLine(lines)
        ts, us = ml.get_tu(mesh)

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(us, plons.shape)
            label = 'test_tu_figure09 - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(ts, plons.shape)
            label = 'test_tu_figure09 - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)

    def test_tu_figure08(self):

        # Get the multiline
        lons, lats, lines = get_lines_figure08()

        # Create the site collection
        mesh, plons, plats = get_mesh(-0.6, 0.6, -0.6, 0.6, 0.005)

        # Create the multiline and calculate the T and U coordinates
        ml = MultiLine(lines)
        ts, us = ml.get_tu(mesh)

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(us, plons.shape)
            label = 'test_tu_figure08 - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(ts, plons.shape)
            label = 'test_tu_figure08 - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)

    def test_string_representation(self):
        # there is a line with 4 points and then one with 2 points
        self.assertEqual(str(MultiLine(self.lines)),
                         '7zzzz_kpbpf_kpbpu_s000m;s003p_s0030')


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
    px = np.array([8, -9.])
    py = np.array([-15, -11.])
    los, las, line = _get_lola(px, py, proj)
    lons.append(los)
    lats.append(las)
    lines.append(line)

    # Section trace 2
    px = np.array([6., -9.])
    py = np.array([-10, -5.])
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
