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


import numpy as np
import unittest
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.sgobba_2020 import SgobbaEtAl2020
from openquake.hazardlib.contexts import DistancesContext


class Sgobba2020Test(unittest.TestCase):

    def test_between_event_correction(self):
        ev_id = '090317011253'
        gm = SgobbaEtAl2020(event_id=ev_id)
        fmt = 'Between event variability for {:s} is wrong'
        msg = fmt.format(ev_id)
        self.assertAlmostEqual(gm.be, -0.089081, msg=msg, places=5)

    def test_cluster(self):
        # Let OQ choose the cluster
        gmm = SgobbaEtAl2020(cluster=1)
        # Set parameters
        sites = Dummy.get_site_collection(4, vs30=760.)
        rup = Dummy.get_rupture(mag=6.0)
        dists = DistancesContext()
        dists.rjb = np.array([1., 10., 30., 70.])
        imt = PGA()
        stdt = [const.StdDev.TOTAL]
        # Computes results
        mean, stds = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
