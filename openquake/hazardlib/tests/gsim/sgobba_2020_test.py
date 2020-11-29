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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
import numpy as np
import pandas as pd
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.geo import Point
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.sgobba_2020 import SgobbaEtAl2020
from openquake.hazardlib.contexts import DistancesContext

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'SEA20')


class Sgobba2020Test(unittest.TestCase):

    def test_amatrice_eqk(self):

        ev_id = '160824013632'

        # Read dataframe with information
        df = pd.read_csv(os.path.join(DATA_FOLDER, 'check_160824013632.csv'))

        # Get parameters
        locs = []
        rjb = []
        for idx, row in df.iterrows():
            locs.append(Point(row.lon_sites, row.lat_sites))
            rjb.append(row.dist_jb)

        # Create the sites
        sites = Dummy.get_site_collection(len(rjb), vs30=760., location=locs)

        # Create distance and rupture contexts
        rup = Dummy.get_rupture(mag=row.rup_mag)
        dists = DistancesContext()
        dists.rjb = np.array(rjb)

        # Instantiate the GMM
        gmm = SgobbaEtAl2020(event_id=ev_id, cluster=4)

        # Computes results
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        mean, stds = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)

        expected = df.PGA.to_numpy()
        computed    = np.exp(mean)
        np.testing.assert_allclose(computed, expected)

        #fmt = 'Between event variability for {:s} is wrong'
        #msg = fmt.format(ev_id)
        #self.assertAlmostEqual(gm.be, -0.089081, msg=msg, places=5)

    def test_cluster(self):

        # Let OQ choose the cluster
        gmm = SgobbaEtAl2020(cluster=1)

        # Set parameters
        locations = [Point(13.0, 42.5), Point(13.0, 42.8), Point(12.8, 42.8)]
        sites = Dummy.get_site_collection(3, vs30=760., location=locations)
        rup = Dummy.get_rupture(mag=6.0)
        dists = DistancesContext()
        dists.rjb = np.array([1., 10., 30.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]

        # Computes results
        mean, stds = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
