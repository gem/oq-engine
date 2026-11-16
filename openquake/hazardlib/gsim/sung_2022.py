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
Module exports :class:`SungEtAl2022` and :class:`SungEtAl2022NonErgodic`.

Reference:
    Sung, C.-H., Abrahamson, N.A., Kuehn, N.M., Traversa, P., Zentner, I.
    (2023). A non-ergodic ground-motion model of Fourier amplitude spectra
    for France. Bulletin of Earthquake Engineering 21: 5293-5317.
"""

import os
import h5py
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import EAS
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim.bayless_abrahamson_2018 import (
    _path_scaling, _ztor_scaling, _linear_site_response)

ADJ_DIR = os.path.join(os.path.dirname(__file__), 'sung_2022')


def _magnitude_scaling(C, ctx):
    """
    Sung et al. (2022) magnitude term.

    Cannot reuse bayless_abrahamson_2018._magnitude_scaling because the
    functional form differs: BA18 computes the third term as
    t3 = (c2 - c3) / cn * ln(1 + exp(cn * (cM - M))),
    while Sung et al. (2022) uses t3 = c3 * ln(1 + exp(cn * (cM - M)))
    directly. This is the Sung form.
    """
    t1 = C['c1']
    t2 = C['c2'] * (ctx.mag - 6.)
    tmp = np.log(1.0 + np.exp(C['cn'] * (C['cM'] - ctx.mag)))
    t3 = C['c3'] * tmp
    return t1 + t2 + t3


class SungEtAl2022(GMPE):
    """
    Implements the Sung et al. (2022) ergodic model for France based on the
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
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Ergodic mean = magnitude + path + Ztor + linear Vs30 terms
            mean[m] = (_magnitude_scaling(C, ctx) +
                       _path_scaling(C, ctx) +
                       _ztor_scaling(C, ctx) +
                       _linear_site_response(C, ctx))
            # Sigma components are constants per frequency, broadcast over sites
            sigma[m] = np.ones_like(ctx.vs30) * C['tot']
            tau[m] = np.ones_like(ctx.vs30) * C['tau']
            phi[m] = np.ones_like(ctx.vs30) * C['phi']

    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot   tau   phi   site_sd record_sd
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 1.025 0.6   0.805 0.569 0.523
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.94  0.439 0.78  0.509 0.53
""")


class SungEtAl2022NonErgodic(SungEtAl2022):
    """
    Non-ergodic variant of Sung et al. (2022).

    At compute time the posterior-mean prediction of the ergodic model is
    shifted by a pre-computed Delta-mu drawn from a per-site adjustment table.
    Delta-mu depends on rupture location (closest point to the site) and
    frequency, and encodes the combined non-ergodic source, site and path
    terms from the varying-coefficient model + cell-specific anelastic
    attenuation in the paper.

    :param adjustment_h5:
        Bare filename (e.g. "adj_RE_Site1.h5") inside the gsim/sung_2022/
        data folder, or an absolute path. The file holds one dataset per
        frequency named `adj_Nhz` (e.g. `adj_1hz`, `adj_5hz`). Each provided
        dataset in sung_2022/ is a structured array of 5551 grid nodes with
        fields (lon, lat, mean, std, rlz[N]) covering the France 0.2x0.2 degree
        grid. N is the number of posterior realizations stored in the file
        (100 for the files in sung_2022). Each file is specific to one target
        site (the site location and Vs30 are baked in at generation time).
    :param rlz_id:
        Selects which posterior draw of the adjustment field to use.
        "mean" (default) uses the posterior mean field `mean`; an integer
        0..N-1 selects one of the sampled realization maps in `rlz[rlz_id]`.
        Each branch of SungEtAl2020 in a GMM logic tree XML specifies a single
        realization (rlz_id=0..N-1) to sample the full epistemic uncertainty of
        the VCM model. The LT size can be anything up to N.
    """

    # clon/clat are the closest point of the rupture to the site
    REQUIRES_DISTANCES = {'rrup', 'clon', 'clat'}

    def __init__(self, adjustment_h5, rlz_id="mean"):
        # Get the filepath
        self.adjustment_h5 = os.path.join(ADJ_DIR, adjustment_h5)
        # Selects which posterior draw: "mean" or integer 0..99
        self.rlz_id = rlz_id
        assert os.path.exists(self.adjustment_h5), \
            'Adjustment h5 not found: %s' % self.adjustment_h5
        # Load one adjustment grid per frequency the h5 provides;
        # keyed by float Hz (e.g. 1.0, 5.0)
        self.dat = {}
        with h5py.File(self.adjustment_h5, 'r') as f:
            for ds_name in f:
                if ds_name.startswith('adj_'):
                    freq = float(ds_name[len('adj_'):].rstrip('hz'))
                    self.dat[freq] = f[ds_name][:]

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        n = len(ctx)
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Pick the adjustment grid for this frequency
            dat = self.dat[imt.frequency]

            # Per-rupture Delta-mu lookup against the per-frequency grid
            adj = np.zeros(n)
            for i in range(n):
                # Rupture coordinates = closest point of rupture mesh to site
                lon_r = ctx.clon[i]
                lat_r = ctx.clat[i]
                # Snap to nearest grid node (0.2 degree cells)
                idx = np.argmin(
                    ((dat['lon'] - lon_r) ** 2 +
                     (dat['lat'] - lat_r) ** 2) ** 0.5)

                # Fail if the rupture is off the grid envelope (0.2 degree
                # grid, so anything > 0.22 degrees is outside the nearest cell)
                dlon = abs(dat['lon'][idx] - lon_r)
                dlat = abs(dat['lat'][idx] - lat_r)
                if dlon > 0.22 or dlat > 0.22:
                    raise ValueError(
                        'Rupture (%.4f, %.4f) is outside the France '
                        'adjustment grid: nearest node (%.4f, %.4f), '
                        'delta=(%.4f, %.4f) deg' % (
                            lon_r, lat_r,
                            dat['lon'][idx], dat['lat'][idx],
                            dlon, dlat))

                # Pick either the posterior mean or one of the 100 realizations
                if self.rlz_id == 'mean':
                    adj[i] = dat['mean'][idx]
                else:
                    adj[i] = dat['rlz'][idx][int(self.rlz_id)]

            # Ergodic mean (same as baseline) plus the non-ergodic shift
            mean[m] = (_magnitude_scaling(C, ctx) +
                       _path_scaling(C, ctx) +
                       _ztor_scaling(C, ctx) +
                       _linear_site_response(C, ctx)) + adj

            # Sigma
            sigma[m] = np.ones_like(ctx.vs30) * C['tot']
            tau[m] = np.ones_like(ctx.vs30) * C['tau']
            phi_val = float(
                np.sqrt(max(C['tot'] ** 2 - C['tau'] ** 2, 0.))) # Phi not stored
            phi[m] = np.ones_like(ctx.vs30) * phi_val

    # The Coefficients used here are the same of the ergodic model BUT the
    # standard deviations which are based on information Karen sent on
    # Sept 4th.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot      tau
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 0.705 0.476
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.591 0.337
""")
