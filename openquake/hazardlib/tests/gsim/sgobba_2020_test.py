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
from openquake.hazardlib.geo.mesh import RectangularMesh
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
        sites = Dummy.get_site_collection(len(rjb), vs30=800., location=locs)

        # Create distance and rupture contexts
        rup = Dummy.get_rupture(mag=row.rup_mag)
        dists = DistancesContext()
        dists.rjb = np.array(rjb)

        # Instantiate the GMM
        gmm = SgobbaEtAl2020(event_id=ev_id, cluster=4)
        gmmref = SgobbaEtAl2020(cluster=0)

        fmt = 'Between event variability for event {:s} is wrong'
        msg = fmt.format(ev_id)
        self.assertAlmostEqual(gmm.be, -0.150766232, msg=msg, places=5)

        # Computes results for the non-ergodic model
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        mean, stds = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)

        # Computes results for the ergodic model
        mr, stdr = gmmref.get_mean_and_stddevs(sites, rup, dists, imt, stdt)

        expected_ref = df.gmm_PGA.to_numpy()
        computed_ref = np.exp(mr)
        np.testing.assert_allclose(computed_ref, expected_ref, rtol=1e-5)

        #expected = df.PGA.to_numpy()
        #computed = np.exp(mean)
        #np.testing.assert_allclose(computed, expected)

    def test_cluster(self):

        # Let OQ choose the cluster
        gmm = SgobbaEtAl2020()

        # Set parameters
        locations = [Point(10.97410551, 40.76758283),
                     Point(10.97410551, 40.76758283)]
        sites = Dummy.get_site_collection(2, vs30=800., location=locations)
        rup = Dummy.get_rupture(mag=4.0)

        lons = np.array([[13.19, 13.21], [13.19, 13.21]])
        lats = np.array([[42.79, 42.81], [42.79, 42.81]])
        deps = np.array([[0.0, 0.0], [10.0, 10.0]])
        rup.surface = RectangularMesh(lons, lats, deps)
        imt = PGA()

        dists = DistancesContext()
        dists.rjb = np.array([10.])
        stdt = [const.StdDev.TOTAL]

        # This is just executed to define the attribute idxs
        _, _ = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)

        # Compute correction
        expected = np.array([0.0112902662180024, 0.0112902662180024])
        computed = gmm._get_cluster_correction(sites, rup, imt)
        np.testing.assert_allclose(computed, expected)
