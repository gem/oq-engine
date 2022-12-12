# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2020 GEM Foundation
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
#

import unittest
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.lanzano_2019 import LanzanoEtAl2019_RJB_OMO


class Lanzano2019Modified2022Test(unittest.TestCase):

    def setUp(self):
        self.ctx = ctx = RuptureContext()
        ctx.mag = 6.
        ctx.rake = 0.
        ctx.hypo_depth = 10.
        ctx.occurrence_rate = .001
        sites = Dummy.get_site_collection(4, vs30=760.)
        for name in sites.array.dtype.names:
            setattr(ctx, name, sites[name])
        ctx.rrup = np.array([1., 10., 30., 70.])
        ctx.rjb = np.array([1., 10., 30., 70.])
        self.imt = PGA()

    def test_adjustement_to_ref(self):
        """ Checks that the modified GMM provides the expected values """
        stds_types = [const.StdDev.TOTAL, const.StdDev.INTRA_EVENT,
                      const.StdDev.INTER_EVENT]
        gmm = LanzanoEtAl2019_RJB_OMO(kappa0=0.02)
        out = gmm.get_mean_and_stddevs(self.ctx, self.ctx, self.ctx,
                                       self.imt, stds_types)
        # Expected results hand computed
        breakpoint()
        expected = np.array([0.001, 0.02, 0.003, 0.004])
        aae = np.testing.assert_array_almost_equal
        aae(expected, np.exp(out[0]))
