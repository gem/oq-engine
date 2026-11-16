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
Module exports :class:`SungAbrahamson2020`
"""

import os
import h5py
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import EAS
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim.bayless_abrahamson_2018 import (
    _path_scaling, _ztor_scaling)


def _magnitude_scaling(C, ctx):
    """Sung variant: t3 = c3 * ln(1 + exp(cn*(cM-M)))"""
    t1 = C['c1']
    t2 = C['c2'] * (ctx.mag - 6.)
    tmp = np.log(1.0 + np.exp(C['cn'] * (C['cM'] - ctx.mag)))
    t3 = C['c3'] * tmp
    return t1 + t2 + t3


def _site_response(C, ctx):
    """Linear Vs30 site term"""
    tmp = np.minimum(ctx.vs30, 1000.)
    return C['c8'] * np.log(tmp / 1000.)


class SungAbrahamson2020(GMPE):
    """
    Implements the Sung and Abrahamson (2020) model for France based on the
    Bayless and Abrahamson (2018) GMM.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {EAS}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    REQUIRES_SITES_PARAMETERS = {'vs30'}
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_magnitude_scaling(C, ctx) +
                       _path_scaling(C, ctx) +
                       _ztor_scaling(C, ctx) +
                       _site_response(C, ctx))
            sigma[m] = np.ones_like(ctx.vs30) * C['tot']
            tau[m] = np.ones_like(ctx.vs30) * C['tau']
            phi[m] = np.ones_like(ctx.vs30) * C['phi']

    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot   tau   phi   site_sd record_sd
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 1.025 0.6   0.805 0.569 0.523
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.94  0.439 0.78  0.509 0.53
""")


class SungAbrahamson2020NonErgodic(SungAbrahamson2020):
    """
    Modification of Sung and Abrahamson (2020) with non ergodic adjustments.
    """

    REQUIRES_DISTANCES = {'rrup', 'clon', 'clat'}

    def __init__(self, adjustment_file=None, rlz_id="mean", **kwargs):
        super().__init__(**kwargs)
        self.adjustment_file = adjustment_file
        self.rlz_id = rlz_id
        assert self.adjustment_file is not None and \
            os.path.exists(self.adjustment_file), \
            'Adjustment file not found: %s' % self.adjustment_file

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        with h5py.File(self.adjustment_file, 'r') as fcoeff:
            dat = fcoeff['init'][:]

        lonn = 'xxx'
        n = len(ctx)
        adj = np.zeros(n)
        for i in range(n):
            lon_r = ctx.clon[i]
            lat_r = ctx.clat[i]
            idx = np.argmin(
                ((dat[lonn] - lon_r) ** 2 + (dat['lat'] - lat_r) ** 2) ** 0.5)

            if (abs(dat[lonn][idx] - lon_r) > 0.22 or
                    abs(dat['lat'][idx] - lat_r) > 0.22):
                print('   Point mesh:', dat[lonn][idx], dat['lat'][idx])
                print('Point rupture:', lon_r, lat_r)
                print('      Diff lo:', abs(dat[lonn][idx] - lon_r))
                print('      Diff la:', abs(dat['lat'][idx] - lat_r))
                raise ValueError('')

            if self.rlz_id == 'mean':
                adj[i] = dat['mea'][idx]
            else:
                adj[i] = dat['rlz'][idx][int(self.rlz_id)]

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_magnitude_scaling(C, ctx) +
                       _path_scaling(C, ctx) +
                       _ztor_scaling(C, ctx) +
                       _site_response(C, ctx)) + adj
            sigma[m] = np.ones_like(ctx.vs30) * C['tot']
            tau[m] = np.ones_like(ctx.vs30) * C['tau']
            # phi not stored in non-ergodic table; derive from tot and tau
            phi_val = float(np.sqrt(max(C['tot'] ** 2 - C['tau'] ** 2, 0.)))
            phi[m] = np.ones_like(ctx.vs30) * phi_val

    # The Coefficients used here are the same of the ergodic model BUT the
    # standard deviations which are based on information Karen sent on
    # Sept 4th.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot      tau
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 0.705 0.476
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.591 0.337
""")
