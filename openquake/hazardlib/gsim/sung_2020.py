# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020 GEM Foundation
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

"""
Module exports :class:`Sung2020`
"""

import os
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.bayless_abrahamson_2018 import \
        BaylessAbrahamson2018


class SungAbrahamson2020(BaylessAbrahamson2018):
    """
    Implements the Sung and Abrahamson (2020) model for France based on the
    Bayliss and Abrahamson (2018) GMM.
    """

    #: Supported standard deviation types
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    def _site_response(self, C, vs30, ln_ir_outcrop, imt):
        """ Compute the site response term """
        # Linear term
        tmp = np.minimum(vs30, 1000.)
        fsl = C['c8'] * np.log(tmp / 1000.)
        return fsl

    def _get_stddevs(self, C, rup, stddev_types, vs30):
        """
        Compute the standard deviations
        """
        # Set components of std
        tau = C['tau']
        phi = C['phi']
        tot = C['tot']

        # Collect the requested stds
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma = tot
                stddevs.append(np.ones_like(vs30) * sigma)
            elif stddev_type == const.StdDev.INTRA_EVENT:
                sigma = phi
                stddevs.append(np.ones_like(vs30) * sigma)
            elif stddev_type == const.StdDev.INTER_EVENT:
                sigma = tau
                stddevs.append(np.ones_like(vs30) * sigma)
        return stddevs


    COEFF = CoeffsTable(sa_damping=5, table="""\
IMT c1           c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot   tau   phi   site_sd record_sd
f_1 -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 1.025 0.6   0.805 0.569 0.523
f_5 -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.94  0.439 0.78  0.509 0.53
""")


class SungAbrahamson2020NonErgodic(SungAbrahamson2020):
    """
    Modification of Sung and Abrahamson (2020) with non ergodic adjustments.
    """

    REQUIRES_DISTANCES = {'rrup', 'closest_pnts'}

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.adjustment_file = kwargs.get("adjustment_file", None)
        msg = 'Adjustment file not found'
        assert os.path.exists(self.adjustment_file), msg

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # Original coefficients
        C = self.COEFFS[imt]

        # Results of the ergodic model
        mean, stddevs = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                   stddev_types)

        # Removing term
        mean -= C['c7'] * dists.rrup

        return mean, stddevs
