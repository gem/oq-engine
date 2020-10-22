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
import unittest
import numpy as np
from openquake.hazardlib.geo import Point
from openquake.hazardlib.imt import EAS
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.site import SiteCollection, Site
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.sung_2020 import (SungAbrahamson2020,
                                                SungAbrahamson2020NonErgodic)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class SungAbranhamson2020TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SungAbrahamson2020

    # Tables computed using the matlab script included in the supplement to
    # the BSSA paper

    def test_mean(self):
        self.check('SA20/SA20_MEAN.csv',
                   max_discrep_percentage=0.1)

"""
    def test_std_intra(self):
        self.check('BA18/BA18_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('BA18/BA18_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('BA18/BA18_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
"""

DATA = os.path.dirname(__file__)


class SungAbrahamson2020NonErgodicTest(unittest.TestCase):

    def test_01(self):

        # Closest point on the rupture
        cp_lon = 5.7664
        cp_lat = 44.6748

        # Coordinates of the site
        site_lon = 5.7664
        site_lat = 43.6748

        # Create dummy site
        location = Point(site_lon, site_lat)
        sites = SiteCollection([Site(location, vs30=2100)])

        # Rupture
        rup = Dummy.get_rupture(mag=6.0, rake=90)
        rup.ztor = 0.0

        # Distance
        dists = DistancesContext()
        tmp = geodetic_distance([cp_lon], [cp_lat], [site_lon], [site_lat])
        dists.rrup = np.array([tmp])
        dists.closest_pnts = np.expand_dims(np.array([cp_lon, cp_lat]), 0)

        fname = os.path.join(DATA, 'data', 'SA20', 'adj_RE_Site1_1Hz.h5')

        # Create GM
        gmm = SungAbrahamson2020NonErgodic(adjustment_file=fname, rlz_id=0)

        # Using pdb:
        # - I checked that the cell selected in the adjustment file is the
        #   closest to 'closest_pnt' on the rupture
        # - I checked that the adjustment value is the one expected for the
        #   the `rlz_id' provided

        imt = EAS(5.0)
        stdtype = [StdDev.TOTAL]
        mean, std = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdtype)
