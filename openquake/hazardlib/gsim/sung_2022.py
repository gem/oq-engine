# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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


def _load_adjustments(path):
    """
    Read every `adj_Nhz` dataset out of the h5 at `path` and return a dict
    keyed by frequency in Hz (float).
    """
    dat = {}
    with h5py.File(path, 'r') as f:
        for ds_name in f:
            if ds_name.startswith('adj_'):
                freq = float(ds_name[len('adj_'):].rstrip('hz'))
                dat[freq] = f[ds_name][:]
    return dat


def _verify_grids_match(dat, path):
    """
    Raise if any two frequency grids disagree on lon/lat columns. Return
    the first frequency's dataset to use as the reference grid.
    """
    freqs = list(dat)
    ref = dat[freqs[0]]
    for freq in freqs[1:]:
        if not (np.array_equal(dat[freq]['lon'], ref['lon'])
                and np.array_equal(dat[freq]['lat'], ref['lat'])):
            raise ValueError(
                '%s: grid coords differ between adj_%ghz and adj_%ghz'
                % (os.path.basename(path), freqs[0], freq))
    return ref


def _lattice_params(ref, path):
    """
    Verify ref's (lon, lat) is a regular dense lattice and derive the
    indexing parameters for O(1) nearest-node lookup. Returns a dict with
    keys: lon0, lat0, lon_step, lat_step, n_lon, n_lat, lon_fast,
    off_grid_tol.

    Raises ValueError if the grid isn't a lattice or the row ordering is
    neither lon-fast nor lat-fast.
    """
    lons_sorted = np.sort(np.unique(ref['lon']))
    lats_sorted = np.sort(np.unique(ref['lat']))
    lon_steps = np.diff(lons_sorted)
    lat_steps = np.diff(lats_sorted)
    # atol = 1e-4 deg absorbs float32 precision jitter but catches any
    # real irregularity (grid step is 0.1-0.5 deg in realistic cases)
    lon_uniform = np.allclose(lon_steps, lon_steps[0], atol=1e-4)
    lat_uniform = np.allclose(lat_steps, lat_steps[0], atol=1e-4)
    dense = len(lons_sorted) * len(lats_sorted) == len(ref)
    if not (lon_uniform and lat_uniform and dense):
        raise ValueError(
            '%s: grid is not a regular dense lattice '
            '(n_lon=%d, n_lat=%d, n_nodes=%d; step uniform? %s/%s)'
            % (os.path.basename(path),
               len(lons_sorted), len(lats_sorted), len(ref),
               lon_uniform, lat_uniform))

    lon0 = float(lons_sorted[0])
    lat0 = float(lats_sorted[0])
    n_lon = len(lons_sorted)
    n_lat = len(lats_sorted)
    # Detect row ordering: lon-fast means nodes are stored as
    # (lat0, lon0), (lat0, lon1), ...; flat index is i_lat*n_lon + i_lon.
    # lat-fast means the opposite; index is i_lon*n_lat + i_lat.
    lon_fast = bool(np.all(ref['lat'][:n_lon] == lat0))
    if not lon_fast and not bool(np.all(ref['lon'][:n_lat] == lon0)):
        raise ValueError(
            '%s: row ordering is neither lon-fast nor lat-fast'
            % os.path.basename(path))
    # Off-grid tolerance = half the grid step + epsilon. The epsilon
    # absorbs float32 jitter in the stored grid coords.
    off_grid_tol = max(float(lon_steps[0]),
                       float(lat_steps[0])) / 2. + 1e-4
    return dict(lon0=lon0, lat0=lat0,
                lon_step=float(lon_steps[0]),
                lat_step=float(lat_steps[0]),
                n_lon=n_lon, n_lat=n_lat,
                lon_fast=lon_fast, off_grid_tol=off_grid_tol)


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
            sigma[m] = C['tot']
            tau[m] = C['tau']
            phi[m] = C['phi']

    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot   tau   phi   site_sd record_sd
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 1.025 0.6   0.805 0.569 0.523
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.94  0.439 0.78  0.509 0.53
""")


class SungEtAl2022NonErgodic(SungEtAl2022):
    """
    Non-ergodic variant of Sung et al. (2022).

    At compute time the ergodic mean is shifted by a scalar Delta-mu
    looked up from a site-specific adjustment table. The shift depends
    only on the rupture's nearest grid cell and the frequency. Each
    table entry already sums the model's non-ergodic source, site and
    path terms, which were integrated when the h5 was generated (i.e.,
    compute() does no ray-tracing itself).

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
    REQUIRES_DISTANCES = {'rrup', 'clon_clat'}

    def __init__(self, adjustment_h5, rlz_id="mean"):
        # Resolve the per-site adjustment table path (bare filenames are
        # looked up under gsim/sung_2022/; absolute paths pass through)
        self.adjustment_h5 = os.path.join(ADJ_DIR, adjustment_h5)
        self.rlz_id = rlz_id
        assert os.path.exists(self.adjustment_h5), \
            'Adjustment h5 not found: %s' % self.adjustment_h5

        # Load every frequency dataset (keyed by float Hz), verify they
        # share the same grid, and cache the lattice parameters used by
        # compute() for O(1) nearest-node indexing
        self.dat = _load_adjustments(self.adjustment_h5)
        ref = _verify_grids_match(self.dat, self.adjustment_h5)
        p = _lattice_params(ref, self.adjustment_h5)
        self._lon0 = p['lon0']
        self._lat0 = p['lat0']
        self._lon_step = p['lon_step']
        self._lat_step = p['lat_step']
        self._n_lon = p['n_lon']
        self._n_lat = p['n_lat']
        self._lon_fast = p['lon_fast']
        self.off_grid_tol = p['off_grid_tol']

    def compute(self, ctx: np.recarray, imts, mean, sigma, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Grid coordinates should be identical across all frequency
        # datasets in the h5 (checked at instantiation), so the nearest
        # node lookup is IMT-independent and uses lattice arithmetic.
        grid = self.dat[next(iter(self.dat))]
        # Nearest-node index from lattice arithmetic; O(n_ctx) ops total
        i_lon = np.round(
            (ctx.clon - self._lon0) / self._lon_step).astype(np.int64)
        i_lat = np.round(
            (ctx.clat - self._lat0) / self._lat_step).astype(np.int64)
        # Clip indices before the flat-index computation; off-grid ctx
        # points will be caught below by the tolerance check
        i_lon = np.clip(i_lon, 0, self._n_lon - 1)
        i_lat = np.clip(i_lat, 0, self._n_lat - 1)
        if self._lon_fast:
            idx_all = i_lat * self._n_lon + i_lon
        else:
            idx_all = i_lon * self._n_lat + i_lat

        # Off-grid check: compare the selected node's coords to the query;
        # catches both out-of-envelope ruptures and any lattice-index bug
        dlon = np.abs(grid['lon'][idx_all] - ctx.clon)
        dlat = np.abs(grid['lat'][idx_all] - ctx.clat)
        off = (dlon > self.off_grid_tol) | (dlat > self.off_grid_tol)
        if off.any():
            i = int(np.where(off)[0][0])
            raise ValueError(
                'Rupture (%.4f, %.4f) is outside the provided adjustment '
                'grid: nearest node (%.4f, %.4f), delta=(%.4f, %.4f) deg'
                % (ctx.clon[i], ctx.clat[i],
                   grid['lon'][idx_all[i]], grid['lat'][idx_all[i]],
                   dlon[i], dlat[i]))

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Pull Delta-mu for every ctx row from the per-frequency grid
            dat = self.dat[imt.frequency]
            if self.rlz_id == 'mean':
                adj = dat['mean'][idx_all]
            else:
                adj = dat['rlz'][idx_all, int(self.rlz_id)]

            # Ergodic mean (same as baseline) plus the non-ergodic shift
            mean[m] = (_magnitude_scaling(C, ctx) +
                       _path_scaling(C, ctx) +
                       _ztor_scaling(C, ctx) +
                       _linear_site_response(C, ctx)) + adj

            # Sigma (phi not stored, derive from tot and tau)
            sigma[m] = C['tot']
            tau[m] = C['tau']
            phi[m] = np.sqrt(max(C['tot'] ** 2 - C['tau'] ** 2, 0.))

    # The Coefficients used here are the same of the ergodic model BUT the
    # standard deviations which are based on information Karen sent on
    # Sept 4th 2020 (consistent with the later published paper)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT c1             c2   c3           c4     c5          c6          c7           c8           c9           cn          cM          chm         tot      tau
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909 6           3.811150377 0.705 0.476
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349 0.031866505  14.31473379 5.165553252 3.507442691 0.591 0.337
""")
