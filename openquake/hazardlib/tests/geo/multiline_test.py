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
from openquake.hazardlib.tests.geo.line_test import plot_pattern
from openquake.hazardlib.site import Site, SiteCollection


PLOTTING = True


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

        # Set the origin and compute the overall azimuth and the azimuths of
        # the polylines composing the multiline instance
        _ = ml._set_origin()
        azim = ml.get_average_azimuths()
        delta = abs(ml.overall_azimuth - azim[1])
        computed = dst * np.cos(np.radians(delta))

        # Testing
        np.testing.assert_almost_equal([0, computed], ml.shift)

    def test_getTU(self):

        # Get the coords of the lines composing the multiline
        lons = []
        lats = []
        for line in self.lines:
            lons.append(line.coo[:, 0])
            lats.append(line.coo[:, 1])

        # Create the site collection
        sites = []
        plons = []
        plats = []
        step = 0.005
        for lo in np.arange(-0.3, 0.8, step):
            tlo = []
            tla = []
            for la in np.arange(-0.3, 0.8, step):
                pnt = geo.Point(lo, la)
                site = Site(pnt, vs30=800, z1pt0=30, z2pt5=1.0)
                sites.append(site)
                tlo.append(lo)
                tla.append(la)
            plons.append(tlo)
            plats.append(tla)
        plons = np.array(plons)
        plats = np.array(plats)
        sitec = SiteCollection(sites)

        # Create the multiline and calculate the T and U coordinates
        ml = MultiLine(self.lines)
        uupp, tupp = ml.get_TU(sitec)

        if PLOTTING:
            num = 10
            # U
            z = np.reshape(uupp, plons.shape)
            label = 'test_getTU - U'
            plot_pattern(lons, lats, z, plons, plats, label, num)
            # T
            z = np.reshape(tupp, plons.shape)
            label = 'test_getTU - T'
            plot_pattern(lons, lats, z, plons, plats, label, num)
