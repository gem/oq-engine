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

The non-ergodic standard deviations in the coefficient tables were provided
directly by Karen Sung on September 4th 2020. They seem to match well to
the values in the later published paper (we can only verify for 5 Hz).
"""

import os
import re
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


ADJ_NAME_RE = re.compile(r'^adj_(?P<freq>\d+(?:\.\d+)?)hz$')


def _load_adjustments(path):
    """
    Read every /<site>/adj_<N>hz dataset out of the h5 at `path` and return
    a dict keyed by (site_name, freq_hz). Any dataset starting with ``adj_``
    whose name doesn't match the ``adj_<N>hz`` pattern raises ValueError so
    typos don't silently drop frequencies.
    """
    dat = {}
    with h5py.File(path, 'r') as f:
        for site_name in f:
            site = f[site_name]
            for ds_name in site:
                if not ds_name.startswith('adj_'):
                    continue
                match = ADJ_NAME_RE.match(ds_name)
                if match is None:
                    raise ValueError(
                        '%s: dataset /%s/%s does not match the expected '
                        'adj_<N>hz naming convention'
                        % (os.path.basename(path), site_name, ds_name))
                freq = float(match.group('freq'))
                dat[(site_name, freq)] = site[ds_name][:]
    return dat


def _verify_grids_match(dat, path):
    """
    Raise if any two datasets disagree on lon/lat columns. Return the
    first dataset to use as the reference grid.
    """
    keys = list(dat)
    ref = dat[keys[0]]
    for key in keys[1:]:
        if not (np.array_equal(dat[key]['lon'], ref['lon'])
                and np.array_equal(dat[key]['lat'], ref['lat'])):
            raise ValueError(
                '%s: grid coords differ between %s and %s'
                % (os.path.basename(path), keys[0], key))
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


_LOADED_ADJUSTMENT_CACHE = {}


def _load_adjustments_cached(path):
    """
    Shared across GSIM instances with the same adjustment_h5. An N-branch
    non-ergodic LT otherwise re-reads the same file N times at construction.
    """
    hit = _LOADED_ADJUSTMENT_CACHE.get(path)
    if hit is None:
        dat = _load_adjustments(path)
        ref = _verify_grids_match(dat, path)
        params = _lattice_params(ref, path)
        hit = (dat, params)
        _LOADED_ADJUSTMENT_CACHE[path] = hit
    dat, params = hit
    return dict(dat), params


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
IMT                c1   c2           c3     c4          c5          c6           c7           c8           c9          cn          cM         chm   tot   tau   phi site_sd record_sd
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909       5.616 3.811150377 1.025   0.6 0.805   0.569     0.523
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349  0.031866505 14.31473379 5.165553252 3.507442691  0.94 0.439  0.78   0.509      0.53
""")


class SungEtAl2022NonErgodic(SungEtAl2022):
    """
    Non-ergodic variant of Sung et al. (2022).

    At compute time the ergodic mean is shifted by a scalar Delta-mu
    looked up from the adjustment h5 at the rupture's nearest grid
    cell. The adjustment is conditional on the target site, so each
    row is routed to the group matching its `custom_site_id`.

    :param adjustment_h5:
        Bare filename (default "adj_RE_france.h5") inside the
        gsim/sung_2022/ data folder, or an absolute path. The file has
        a /<site_name>/adj_<N>hz group structure; `custom_site_id`
        values in the job's sites.csv must match one of the site groups
        in the h5. Each dataset is a structured array of 5551 grid nodes
        with fields (lon, lat, mean, std, rlz[N]) covering the France
        0.2x0.2 degree grid. All sites share the same grid; dat['mean']
        and dat['rlz'] differ per site because the posterior is
        conditional on the receiver.
    :param rlz_id:
        Selects which posterior draw of the adjustment field to use.
        "mean" (default) uses the posterior mean field `mean`; an integer
        0..N-1 selects one of the sampled realization maps in `rlz[rlz_id]`.
        The same rlz_id applies across all sites in the h5; each LT
        branch corresponds to one posterior draw.
    """
    REQUIRES_SITES_PARAMETERS = {'vs30', 'custom_site_id'}
    REQUIRES_DISTANCES = {'rrup', 'clon', 'clat'}

    experimental = True # For now

    def __init__(self, adjustment_h5="adj_RE_france.h5", rlz_id="mean"):
        self.adjustment_h5 = os.path.join(ADJ_DIR, adjustment_h5)
        self.rlz_id = rlz_id
        assert os.path.exists(self.adjustment_h5), \
            'Adjustment h5 not found: %s' % self.adjustment_h5

        # Load every (site, freq) dataset, verify they share the same grid,
        # cache the lattice parameters for O(1) nearest-node indexing.
        # The h5 read + grid verification + lattice derivation are
        # amortised across all GSIM instances sharing this adjustment_h5
        # (100-branch non-ergodic LTs instantiate 100 copies).
        self.dat, p = _load_adjustments_cached(self.adjustment_h5)
        self.sites = sorted({s for s, _ in self.dat})
        self.freqs = sorted({f for _, f in self.dat})
        self._lon0 = p['lon0']
        self._lat0 = p['lat0']
        self._lon_step = p['lon_step']
        self._lat_step = p['lat_step']
        self._n_lon = p['n_lon']
        self._n_lat = p['n_lat']
        self._lon_fast = p['lon_fast']
        self.off_grid_tol = p['off_grid_tol']

    @property
    def central_key(self):
        """
        Branches with the same adjustment h5 share the same backbone and
        the same nearest-neighbour lookup. ContextMaker computes those once
        per batch and reuses the result across every branch returning the
        same key (see contexts.py:get_mean_stds).
        """
        return (self.adjustment_h5,)

    # Generic func name so method accepted in get_mean_stds for speedup
    def compute_central(self, ctx, imts, mean, sigma, tau, phi, **_kw):
        """
        Branch-independent work: ergodic backbone + nearest-node index +
        per-row site-name decode. Returns (idx_all, csids) so
        apply_branch_shift() can pull the per-rlz column for the right
        site without redoing the work.

        ``**_kw`` absorbs ContextMaker kwargs (e.g. ``gra_mon``) that this
        GSIM has no use for - accepted for interface compatibility only.
        """
        missing = sorted({imt.frequency for imt in imts} - set(self.freqs))
        if missing:
            raise ValueError(
                '%s: no adjustment dataset for frequency %s Hz '
                '(available: %s Hz)' % (
                    os.path.basename(self.adjustment_h5),
                    ', '.join('%g' % f for f in missing),
                    ', '.join('%g' % f for f in self.freqs)))

        # Decode custom_site_id per row and reject any unknown ones
        csids = np.array([s.decode('utf-8').strip('\x00')
                          if isinstance(s, (bytes, bytearray))
                          else str(s).strip('\x00')
                          for s in ctx.custom_site_id])
        unknown = sorted(set(csids) - set(self.sites))
        if unknown:
            raise ValueError(
                '%s: custom_site_id(s) not present in the adjustment h5: '
                '%s. Known sites: %s'
                % (os.path.basename(self.adjustment_h5),
                   unknown, self.sites))
        # Every (site, freq) pair touched by this batch must exist
        for site in set(csids):
            for imt in imts:
                if (site, imt.frequency) not in self.dat:
                    raise ValueError(
                        '%s: no adjustment for site=%s at frequency=%g Hz'
                        % (os.path.basename(self.adjustment_h5),
                           site, imt.frequency))

        grid = self.dat[(self.sites[0], self.freqs[0])]
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

        # Ergodic backbone + sigma components (do NOT depend on rlz_id)
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = (_magnitude_scaling(C, ctx) +
                       _path_scaling(C, ctx) + # Assuming cRB = 50 km as in BA18
                       _ztor_scaling(C, ctx) +
                       _linear_site_response(C, ctx))
            sigma[m] = C['tot']
            tau[m] = C['tau']
            phi[m] = np.sqrt(max(C['tot'] ** 2 - C['tau'] ** 2, 0.))
        return idx_all, csids

    # Generic func name so method accepted in get_mean_stds for speedup
    def apply_branch_shift(self, central, imts, mean):
        """
        Branch-specific shift: for each unique custom_site_id in the batch,
        add Delta-mu from that site's rlz column into the central mean.
        """
        idx_all, csids = central
        for site in np.unique(csids):
            mask = csids == site
            nidx = idx_all[mask]
            for m, imt in enumerate(imts):
                dat = self.dat[(site, imt.frequency)]
                if self.rlz_id == 'mean':
                    mean[m, mask] += dat['mean'][nidx]
                else:
                    mean[m, mask] += dat['rlz'][nidx, int(self.rlz_id)]

    # The Coefficients used here are the same of the ergodic model BUT the
    # standard deviations differ given they are for the non-ergodic variant
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT                c1   c2           c3     c4          c5          c6           c7           c8           c9          cn          cM         chm   tot   tau
EAS(1.0) -3.831335618 1.27 -0.339593397 -2.165 7.581303952 0.451924112 -0.003743823 -1.220089093 -0.002488724 3.714155909       5.616 3.811150377 0.705 0.476
EAS(5.0) -4.042505531 1.27 -0.041712502 -2.165 7.487714222 0.476000074 -0.007202382 -0.699440349  0.031866505 14.31473379 5.165553252 3.507442691 0.591 0.337
""")
