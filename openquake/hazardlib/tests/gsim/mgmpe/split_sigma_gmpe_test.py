# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np
import unittest
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib.gsim.mgmpe.split_sigma_gmpe import SplitSigmaGMPE


class SplitSigmaGMPETest(unittest.TestCase):
    def _get_stds(self, within_absolute=None, between_absolute=None):
        if within_absolute is not None:
            gmm = SplitSigmaGMPE(gmpe_name='Campbell2003',
                                 within_absolute=within_absolute)
        elif between_absolute is not None:
            gmm = SplitSigmaGMPE(gmpe_name='Campbell2003',
                                 between_absolute=between_absolute)
        else:
            raise ValueError('Unknown option')
        # Set parameters
        ctx = RuptureContext()
        ctx.mag = 6.0
        ctx.sids = [0, 1, 2, 3]
        ctx.vs30 = [760.] * 4
        ctx.rrup = np.array([1., 10., 30., 70.])
        imt = PGA()
        stds_types = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
                      const.StdDev.INTRA_EVENT]
        # Compute results
        mean, stds = gmm.get_mean_and_stddevs(ctx, ctx, ctx, imt, stds_types)
        return stds, stds_types

    def test_instantiation(self):
        within_absolute = 0.3
        SplitSigmaGMPE(gmpe_name='Campbell2003',
                       within_absolute=within_absolute)

    def test_within_absolute(self):
        within_absolute = 0.3
        stds, stds_types = self._get_stds(within_absolute=within_absolute)
        # Check
        idx = stds_types.index(const.StdDev.INTER_EVENT)
        between = stds[idx]
        idx = stds_types.index(const.StdDev.INTRA_EVENT)
        within = stds[idx]
        computed = (within**2 + between**2)**0.5
        idx = stds_types.index(const.StdDev.TOTAL)
        expected = stds[idx]
        np.testing.assert_array_almost_equal(expected, computed)
        computed = np.ones_like(stds[idx])*within_absolute
        np.testing.assert_array_almost_equal(within, computed)

    def test_between_absolute(self):
        between_absolute = 0.45
        stds, stds_types = self._get_stds(between_absolute=between_absolute)
        # Check
        idx = stds_types.index(const.StdDev.INTER_EVENT)
        between = stds[idx]
        idx = stds_types.index(const.StdDev.INTRA_EVENT)
        within = stds[idx]
        computed = (within**2 + between**2)**0.5
        idx = stds_types.index(const.StdDev.TOTAL)
        expected = stds[idx]
        np.testing.assert_array_almost_equal(expected, computed)
        computed = np.ones_like(stds[idx])*between_absolute
        np.testing.assert_array_almost_equal(between, computed)
