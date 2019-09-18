# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.morikawa_fujiwara_2013 import \
        MorikawaFujiwara2013


class MorikawaFujiwara2013Test(unittest.TestCase):
    """
    """

    def test_instantiation(self):
        dists = DistancesContext()
        dists.rrup = np.array([10., 50., 100.])
        imt = PGA()
        mag = 6.0
        rup = Dummy.get_rupture(mag=mag, hypo_depth=10.)
        slen = len(dists.rrup)
        sites = Dummy.get_site_collection(slen, vs30=760., z1pt4=100., xvf=10.)
        stdt = [const.StdDev.TOTAL]
        gmm = MorikawaFujiwara2013(model='model1', region=None)
        mean, stds = gmm.get_mean_and_stddevs(sites, rup, dists, imt, stdt)
