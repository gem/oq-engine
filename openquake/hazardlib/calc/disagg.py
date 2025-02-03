# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
:mod:`openquake.hazardlib.calc.disagg` contains :class:`Disaggregator`,
:func:`disaggregation` as well as several aggregation functions for
extracting a specific PMF from the result of :func:`disaggregation`.
"""

import operator
import collections
import itertools
from functools import lru_cache
import numpy
import scipy.stats

from openquake.baselib.general import AccumDict, groupby, humansize
from openquake.baselib.performance import idx_start_stop, Monitor
from openquake.baselib.python3compat import decode
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.calc import filters
from openquake.hazardlib.stats import truncnorm_sf
from openquake.hazardlib.valid import corename
from openquake.hazardlib.geo.utils import get_longitudinal_extent
from openquake.hazardlib.geo.utils import (angular_distance, KM_TO_DEGREES,
                                           cross_idl)
from openquake.hazardlib.tom import get_pnes
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim.base import to_distribution_values
from openquake.hazardlib.contexts import ContextMaker, Oq, FarAwayRupture
from openquake.hazardlib.calc.mean_rates import (
    calc_rmap, calc_mean_rates, to_rates, to_probs)

BIN_NAMES = 'mag', 'dist', 'lon', 'lat', 'eps', 'trt'
BinData = collections.namedtuple('BinData', 'dists, lons, lats, pnes')
TWO24 = 2 ** 24


def assert_same_shape(arrays):
    """
    Raises an AssertionError if the shapes are not consistent
    """
    shape = arrays[0].shape
    for arr in arrays[1:]:
        assert arr.shape == shape, (arr.shape, shape)


# used in calculators/disaggregation
def lon_lat_bins(lon, lat, size_km, coord_bin_width):
    """
    Define lon, lat bin edges for disaggregation histograms.

    :param lon: longitude of the site
    :param lat: latitude of the site
    :param size_km: total size of the bins in km
    :param coord_bin_width: bin width in degrees
    :returns: two arrays lon bins, lat bins
    """
    nbins = numpy.ceil(size_km * KM_TO_DEGREES / coord_bin_width)
    delta_lon = min(angular_distance(size_km, lat), 180)
    delta_lat = min(size_km * KM_TO_DEGREES, 90)
    EPS = .001  # avoid discarding the last edge
    lon_bins = lon + numpy.arange(-delta_lon, delta_lon + EPS,
                                  2*delta_lon / nbins)
    lat_bins = lat + numpy.arange(-delta_lat, delta_lat + EPS,
                                  2*delta_lat / nbins)
    if cross_idl(*lon_bins):
        lon_bins %= 360
    return lon_bins, lat_bins


def _build_bin_edges(oq, sitecol):
    # return [mag, dist, lon, lat, eps] edges

    maxdist = filters.upper_maxdist(oq.maximum_distance)
    truncation_level = oq.truncation_level
    mags_by_trt = oq.mags_by_trt

    # build mag_edges
    if 'mag' in oq.disagg_bin_edges:
        mag_edges = oq.disagg_bin_edges['mag']
    else:
        mags = set()
        trts = []
        for trt, _mags in mags_by_trt.items():
            mags.update(float(mag) for mag in _mags)
            trts.append(trt)
        mags = sorted(mags)
        min_mag = mags[0]
        max_mag = mags[-1]
        n1 = int(numpy.floor(min_mag / oq.mag_bin_width))
        n2 = int(numpy.ceil(max_mag / oq.mag_bin_width))
        if n2 == n1 or max_mag >= round((oq.mag_bin_width * n2), 3):
            n2 += 1
        mag_edges = oq.mag_bin_width * numpy.arange(n1, n2+1)

    # build dist_edges
    if 'dist' in oq.disagg_bin_edges:
        dist_edges = oq.disagg_bin_edges['dist']
    elif hasattr(oq, 'distance_bin_width'):
        dist_edges = uniform_bins(0, maxdist, oq.distance_bin_width)
    else:  # make a single bin
        dist_edges = [0, maxdist]

    # build lon_edges
    if 'lon' in oq.disagg_bin_edges or 'lat' in oq.disagg_bin_edges:
        assert len(sitecol) == 1, sitecol
        lon_edges = {0: oq.disagg_bin_edges['lon']}
        lat_edges = {0: oq.disagg_bin_edges['lat']}
    else:
        lon_edges, lat_edges = {}, {}  # by sid
        for site in sitecol:
            loc = site.location
            lon_edges[site.id], lat_edges[site.id] = lon_lat_bins(
                loc.x, loc.y, maxdist, oq.coordinate_bin_width)

    # sanity check: the shapes of the lon lat edges are consistent
    assert_same_shape(list(lon_edges.values()))
    assert_same_shape(list(lat_edges.values()))

    # build eps_edges
    if 'eps' in oq.disagg_bin_edges:
        eps_edges = oq.disagg_bin_edges['eps']
    else:
        eps_edges = numpy.linspace(
            -truncation_level, truncation_level, oq.num_epsilon_bins + 1)

    return [mag_edges, dist_edges, lon_edges, lat_edges, eps_edges]


def get_edges_shapedic(oq, sitecol, num_tot_rlzs=None):
    """
    :returns: (mag dist lon lat eps trt) edges and shape dictionary
    """
    assert oq.mags_by_trt
    trts = list(oq.mags_by_trt)

    if oq.rlz_index is None:
        Z = oq.num_rlzs_disagg or num_tot_rlzs
    else:
        Z = len(oq.rlz_index)

    edges = _build_bin_edges(oq, sitecol)
    shapedic = {}
    for i, name in enumerate(BIN_NAMES):
        if name in ('lon', 'lat'):
            # taking the first, since the shape is the same for all sites
            shapedic[name] = len(edges[i][0]) - 1
        elif name == 'trt':
            shapedic[name] = len(trts)
        else:
            shapedic[name] = len(edges[i]) - 1
    shapedic['N'] = len(sitecol)
    shapedic['M'] = len(oq.imtls)
    shapedic['P'] = len(oq.poes or (None,))
    shapedic['Z'] = Z
    return edges + [trts], shapedic


DEBUG = AccumDict(accum=[])  # sid -> pnes.mean(), useful for debugging


@lru_cache
def get_eps4(eps_edges, truncation_level):
    """
    :returns: eps_min, eps_max, eps_bands, eps_cum
    """
    # this is ultra-slow due to the infamous doccer issue, hence the lru_cache
    tn = scipy.stats.truncnorm(-truncation_level, truncation_level)
    eps_bands = tn.cdf(eps_edges[1:]) - tn.cdf(eps_edges[:-1])
    elist = range(len(eps_bands))
    eps_cum = numpy.array([eps_bands[e:].sum() for e in elist] + [0])
    return min(eps_edges), max(eps_edges), eps_bands, eps_cum


# NB: this function is the crucial bit for performance!
def _disaggregate(ctx, mea, std, cmaker, g, iml2, bin_edges, epsstar, gp,
                  infer_occur_rates, mon1, mon2, mon3):
    # ctx: a recarray of size U for a single site and magnitude bin
    # mea: array of shape (G, M, U)
    # std: array of shape (G, M, U)
    # cmaker: a ContextMaker instance
    # g: a gsim index
    # iml2: an array of shape (M, P) of logarithmic intensities
    # eps_bands: an array of E elements obtained from the E+1 eps_edges
    # bin_edges: a tuple of 5 bin edges (mag, dist, lon, lat, eps)
    # epsstar: a boolean. When True, disaggregation contains eps* results
    # gp: group_probability relevant for mutex sources, otherwise 1
    # returns a 7D-array of shape (D, Lo, La, E, M, P, Z)

    with mon1:
        eps_edges = tuple(bin_edges[-1])  # last edge
        min_eps, max_eps, eps_bands, cum_bands = get_eps4(
            eps_edges, cmaker.truncation_level)
        U, E = len(ctx), len(eps_bands)
        M, P = iml2.shape
        phi_b = cmaker.phi_b
        # U - Number of contexts (i.e. ruptures if there is a single site)
        # E - Number of epsilons
        # M - Number of IMTs
        # P - Number of PoEs
        # G - Number of gsims
        poes = numpy.zeros((U, E, M, P))
        pnes = numpy.ones((U, E, M, P))

        # disaggregate by epsilon
        for (m, p), iml in numpy.ndenumerate(iml2):
            if iml == -numpy.inf:  # zero hazard
                continue
            lvls = (iml - mea[g, m]) / std[g, m]
            # Find the index in the epsilons-bins vector where lvls (which are
            # epsilons) should be included
            idxs = numpy.searchsorted(eps_edges, lvls)
            # Split the epsilons into parts (one for each bin larger than lvls)
            if epsstar:
                ok = (lvls >= min_eps) & (lvls < max_eps)
                # The leftmost indexes are ruptures and epsilons
                poes[ok, idxs[ok] - 1, m, p] = gp*truncnorm_sf(phi_b, lvls[ok])
            else:
                poes[:, :, m, p] = gp * _disagg_eps(
                    truncnorm_sf(phi_b, lvls), idxs, eps_bands, cum_bands)

    with mon2:
        time_span = cmaker.investigation_time
        if not infer_occur_rates and any(len(po) for po in ctx.probs_occur):
            # slow lane, case_65
            for u, rec in enumerate(ctx):
                pnes[u] *= get_pnes(rec.occurrence_rate, rec.probs_occur,
                                    poes[u], time_span)
        else:
            # poissonian, fast lane
            for e, m, p in itertools.product(range(E), range(M), range(P)):
                pnes[:, e, m, p] *= numpy.exp(
                    -ctx.occurrence_rate * poes[:, e, m, p] * time_span)

    with mon3:
        bindata = BinData(ctx.rrup, ctx.clon, ctx.clat, pnes)
        return _build_disagg_matrix(bindata, bin_edges[1:])


def _disagg_eps(survival, bins, eps_bands, cum_bands):
    # disaggregate PoE of `iml` in different contributions,
    # each coming from ``epsilons`` distribution bins
    res = numpy.zeros((len(bins), len(eps_bands)))
    for e, eps_band in enumerate(eps_bands):
        res[bins <= e, e] = eps_band  # left bins
        inside = bins == e + 1  # inside bins
        res[inside, e] = survival[inside] - cum_bands[bins[inside]]
    return res  # shape (U, E)


# this is fast
def _build_disagg_matrix(bdata, bins):
    """
    :param bdata: a dictionary of probabilities of no exceedence
    :param bins: bin edges
    :returns:
        a 7D-matrix of shape (#distbins, #lonbins, #latbins, #epsbins, M, P, Z)
    """
    dist_bins, lon_bins, lat_bins, _eps_bins = bins
    dim1, dim2, dim3, _dim4 = shape = [len(b) - 1 for b in bins]

    # find bin indexes of rupture attributes; bins are assumed closed
    # on the lower bound, and open on the upper bound, that is [ )
    # longitude values need an ad-hoc method to take into account
    # the 'international date line' issue
    # the 'minus 1' is needed because the digitize method returns the
    # index of the upper bound of the bin
    dists_idx = numpy.digitize(bdata.dists, dist_bins) - 1
    lons_idx = _digitize_lons(bdata.lons, lon_bins)
    lats_idx = numpy.digitize(bdata.lats, lat_bins) - 1

    # because of the way numpy.digitize works, values equal to the last bin
    # edge are associated to an index equal to len(bins) which is not a
    # valid index for the disaggregation matrix. Such values are assumed
    # to fall in the last bin
    dists_idx[dists_idx == dim1] = dim1 - 1
    lons_idx[lons_idx == dim2] = dim2 - 1
    lats_idx[lats_idx == dim3] = dim3 - 1
    _U, _E, M, P = bdata.pnes.shape
    mat6D = numpy.ones(shape + [M, P])
    for i_dist, i_lon, i_lat, pne in zip(
            dists_idx, lons_idx, lats_idx, bdata.pnes):
        mat6D[i_dist, i_lon, i_lat] *= pne  # shape E, M, P
    return 1. - mat6D


def uniform_bins(min_value, max_value, bin_width):
    """
    Returns an array of bins including all values:

    >>> uniform_bins(1, 10, 1.)
    array([ 1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10.])
    >>> uniform_bins(1, 10, 1.1)
    array([ 0. ,  1.1,  2.2,  3.3,  4.4,  5.5,  6.6,  7.7,  8.8,  9.9, 11. ])
    """
    return bin_width * numpy.arange(
        int(numpy.floor(min_value / bin_width)),
        int(numpy.ceil(max_value / bin_width) + 1))


def _digitize_lons(lons, lon_bins):
    """
    Return indices of the bins to which each value in lons belongs.
    Takes into account the case in which longitude values cross the
    international date line.

    :parameter lons:
        An instance of `numpy.ndarray`.
    :parameter lons_bins:
        An instance of `numpy.ndarray`.
    """
    if cross_idl(lon_bins[0], lon_bins[-1]):
        idx = numpy.zeros_like(lons, dtype=int)
        for i_lon in range(len(lon_bins) - 1):
            extents = get_longitudinal_extent(lons, lon_bins[i_lon + 1])
            lon_idx = extents > 0
            if i_lon != 0:
                extents = get_longitudinal_extent(lon_bins[i_lon], lons)
                lon_idx &= extents >= 0
            idx[lon_idx] = i_lon
        return numpy.array(idx)
    else:
        return numpy.digitize(lons, lon_bins) - 1


# ########################## Disaggregator class ########################## #

def split_by_magbin(ctxt, mag_edges):
    """
    :param ctxt: a context array
    :param mag_edges: magnitude bin edges
    :returns: a dictionary magbin -> ctxt
    """
    # NB: using ctxt.sort(order='mag') would cause a ValueError
    ctx = ctxt[numpy.argsort(ctxt.mag)]
    fullmagi = numpy.searchsorted(mag_edges, ctx.mag) - 1
    fullmagi[fullmagi == -1] = 0  # magnitude on the edge
    return {magi: ctx[fullmagi == magi] for magi in numpy.unique(fullmagi)}


class Disaggregator(object):
    """
    A class to perform single-site disaggregation with methods
    .disagg_by_magi (called in standard disaggregation) and
    .disagg_mag_dist_eps (called in disaggregation by relevant source).
    Internally the attributes .mea and .std are set, with shape (G, M, U),
    for each magnitude bin.
    """
    def __init__(self, srcs_or_ctxs, site, cmaker, bin_edges, imts=None):
        if isinstance(site, Site):
            if not hasattr(site, 'id'):
                site.id = 0
            self.sitecol = SiteCollection([site])
        else:  # assume a site collection of length 1
            self.sitecol = site
            assert len(site) == 1, site
        self.sid = sid = self.sitecol.sids[0]
        if imts is not None:
            for imt in imts:
                assert imt in cmaker.imtls, imt
            cmaker.imts = [from_string(imt) for imt in imts]
        self.cmaker = cmaker
        self.epsstar = cmaker.oq.epsilon_star
        self.bin_edges = (bin_edges[0],  # mag
                          bin_edges[1],  # dist
                          bin_edges[2][sid],  # lon
                          bin_edges[3][sid],  # lat
                          bin_edges[4])  # eps
        for i, name in enumerate(['Ma', 'D', 'Lo', 'La', 'E']):
            setattr(self, name, len(self.bin_edges[i]) - 1)
        self.dist_idx = {}  # magi -> dist_idx
        self.mea, self.std = {}, {}  # magi -> array[G, M, U]

        self.g_by_rlz = {}  # dict rlz -> g
        for g, rlzs in enumerate(cmaker.gsims.values()):
            for rlz in rlzs:
                self.g_by_rlz[rlz] = g

        if isinstance(srcs_or_ctxs[0], numpy.ndarray):
            # passed contexts, see logictree_test/case_05
            # consider only the contexts affecting the site
            ctxs = [ctx[ctx.sids == sid] for ctx in srcs_or_ctxs]
        else:  # passed sources, used only in test_disaggregator
            ctxs = cmaker.from_srcs(srcs_or_ctxs, self.sitecol)
        if sum(len(c) for c in ctxs) == 0:
            raise FarAwayRupture('No ruptures affecting site #%d' % sid)

        ctx = numpy.concatenate(ctxs).view(numpy.recarray)
        self.fullctx = ctx

    def init(self, magi, src_mutex,
             mon0=Monitor('disagg mean_stds'),
             mon1=Monitor('disagg by eps'),
             mon2=Monitor('composing pnes'),
             mon3=Monitor('disagg matrix')):
        self.magi = magi
        self.src_mutex = src_mutex
        self.mon1 = mon1
        self.mon2 = mon2
        self.mon3 = mon3
        if not hasattr(self, 'ctx_by_magi'):
            # the first time build the magnitude bins
            self.ctx_by_magi = split_by_magbin(self.fullctx, self.bin_edges[0])
        try:
            self.ctx = self.ctx_by_magi[magi]
        except KeyError:
            raise FarAwayRupture
        if self.src_mutex:
            # make sure we can use idx_start_stop below, by ordering by src_id
            # the src_id is set in contexts.py to be equal to the fragmentno
            # NB: using ctx.sort(order='src_id') would cause a ValueError
            # NB: argsort can be problematic on AVX-512 processors!
            self.ctx = self.ctx[numpy.argsort(self.ctx.src_id)]
        self.dist_idx[magi] = numpy.digitize(
            self.ctx.rrup, self.bin_edges[1]) - 1
        with mon0:
            # shape (G, M, U), where M = len(imts) <= len(imtls)
            self.mea[magi], self.std[magi] = self.cmaker.get_mean_stds(
                [self.ctx])[:2]
        if self.src_mutex:
            mat = idx_start_stop(self.ctx.src_id)  # shape (n, 3)
            src_ids = mat[:, 0]  # subset contributing to the given magi
            self.src_mutex['start'] = mat[:, 1]
            self.src_mutex['stop'] = mat[:, 2]
            self.weights = [w for s, w in zip(self.src_mutex['src_id'],
                                              self.src_mutex['weight'])
                            if s in src_ids]

    def _disagg6D(self, imldic, g):
        # returns a 6D matrix of shape (D, Lo, La, E, M, P)
        # compute the logarithmic intensities
        # returns poes for src_mutex and rates otherwise
        imts = list(imldic)
        iml2 = numpy.array(list(imldic.values()))  # shape (M, P)
        imlog2 = numpy.zeros_like(iml2)
        for m, imt in enumerate(imts):
            imlog2[m] = to_distribution_values(iml2[m], imt)
        mea, std = self.mea[self.magi], self.std[self.magi]
        gp = self.src_mutex.get('grp_probability', 1.)
        if not self.src_mutex:
            poes = _disaggregate(self.ctx, mea, std, self.cmaker,
                                 g, imlog2, self.bin_edges, self.epsstar, gp,
                                 self.cmaker.oq.infer_occur_rates,
                                 self.mon1, self.mon2, self.mon3)
            return to_rates(poes)

        # else average on the src_mutex weights
        mats = []
        for s1, s2 in zip(self.src_mutex['start'], self.src_mutex['stop']):
            ctx = self.ctx[s1:s2]
            mea = self.mea[self.magi][:, :, s1:s2]  # shape (G, M, U)
            std = self.std[self.magi][:, :, s1:s2]  # shape (G, M, U)
            mat = _disaggregate(ctx, mea, std, self.cmaker, g, imlog2,
                                self.bin_edges, self.epsstar, gp,
                                self.cmaker.oq.infer_occur_rates,
                                self.mon1, self.mon2, self.mon3)
            mats.append(mat)
        poes = numpy.einsum('i,i...', self.weights, mats)
        return poes

    def disagg_by_magi(self, imtls, rlzs, rwdic, src_mutex,
                       mon0, mon1, mon2, mon3):
        """
        :param imtls:
            a dictionary imt->imls
        :param rlzs:
            an array of realization indices
        :param rwdic:
            a dictionary rlz_id->weight; if non-empty, used compute the mean
        :param src_mutex:
            dictionary used to set the self.src_mutex slices
        :yields:
            a dictionary with keys trti, magi, sid, rlzi, mean for each magi
        """
        for magi in range(self.Ma):
            try:
                self.init(magi, src_mutex, mon0, mon1, mon2, mon3)
            except FarAwayRupture:
                continue
            if src_mutex:  # mutex weights
                mw = sum(self.weights)
            else:
                mw = 1.
            res = {'trti': self.cmaker.trti,
                   'magi': self.magi,
                   'sid': self.sid}
            for rlz in rlzs:
                try:
                    g = self.g_by_rlz[rlz]
                except KeyError:  # non-contributing rlz
                    continue
                arr6D = self._disagg6D(imtls, g)
                res[rlz] = to_rates(arr6D) if src_mutex else arr6D
                if rwdic:  # compute mean rates (mean poes for src_mutex)
                    if 'mean' not in res:
                        res['mean'] = arr6D * rwdic[rlz] * mw
                    else:
                        res['mean'] += arr6D * rwdic[rlz] * mw
            if rwdic and src_mutex:
                res['mean'] = to_rates(res['mean'])
            yield res

    def disagg_mag_dist_eps(self, imldic, rlz_weights, src_mutex={}):
        """
        :param imldic: a dictionary imt->iml
        :param src_mutex: a dictionary with keys src_id, weight or empty
        :param rlz_weights: an array with the realization weights
        :returns: a 4D matrix of rates of shape (Ma, D, E, M)
        """
        M = len(imldic)
        imtls = {imt: [iml] for imt, iml in imldic.items()}
        out = numpy.zeros((self.Ma, self.D, self.E, M))  # rates
        for magi in range(self.Ma):
            try:
                self.init(magi, src_mutex)
            except FarAwayRupture:
                continue
            if src_mutex:  # mutex weights
                mw = sum(self.weights)
            else:
                mw = 1.
            for rlz, g in self.g_by_rlz.items():
                mat5 = self._disagg6D(imtls, g)[..., 0]  # p = 0
                # summing on lon, lat and producing a (D, E, M) array
                out[magi] += mat5.sum(axis=(1, 2)) * rlz_weights[rlz] * mw
        return to_rates(out) if src_mutex else out

    def __repr__(self):
        return f'<{self.__class__.__name__} {humansize(self.fullctx.nbytes)} >'


# this is used in the hazardlib tests, not in the engine
def disaggregation(
        sources, site, imt, iml, gsim_by_trt, truncation_level,
        n_epsilons=None, mag_bin_width=None, dist_bin_width=None,
        coord_bin_width=None, source_filter=filters.nofilter,
        epsstar=False, bin_edges={}, **kwargs):
    """\
    Compute "Disaggregation" matrix representing conditional probability of an
    intensity measure type ``imt`` exceeding, at least once, an intensity
    measure level ``iml`` at a geographical location ``site``, given rupture
    scenarios classified in terms of:

    - rupture magnitude
    - Joyner-Boore distance from rupture surface to site
    - longitude and latitude of the surface projection of a rupture's point
      closest to ``site``
    - epsilon: number of standard deviations by which an intensity measure
      level deviates from the median value predicted by a GSIM, given the
      rupture parameters
    - rupture tectonic region type

    In other words, the disaggregation matrix allows to compute the probability
    of each scenario with the specified properties (e.g., magnitude, or the
    magnitude and distance) to cause one or more exceedences of a given hazard
    level.

    For more detailed information about the disaggregation, see for instance
    "Disaggregation of Seismic Hazard", Paolo Bazzurro, C. Allin Cornell,
    Bulletin of the Seismological Society of America, Vol. 89, pp. 501-520,
    April 1999.

    :param sources:
        Seismic source model, as for
        :mod:`PSHA <openquake.hazardlib.calc.hazard_curve>` calculator it
        should be an iterator of seismic sources.
    :param site:
        :class:`~openquake.hazardlib.site.Site` of interest to calculate
        disaggregation matrix for.
    :param imt:
        Instance of :mod:`intensity measure type <openquake.hazardlib.imt>`
        class.
    :param iml:
        Intensity measure level. A float value in units of ``imt``.
    :param gsim_by_trt:
        Tectonic region type to GSIM objects mapping.
    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.
    :param n_epsilons:
        Integer number of epsilon histogram bins in the result matrix.
    :param mag_bin_width:
        Magnitude discretization step, width of one magnitude histogram bin.
    :param dist_bin_width:
        Distance histogram discretization step, in km.
    :param coord_bin_width:
        Longitude and latitude histograms discretization step,
        in decimal degrees.
    :param source_filter:
        Optional source-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.
    :param epsstar:
        A boolean. When true disaggregations results including epsilon are
        in terms of epsilon star rather then epsilon.
    :param bin_edges:
        Bin edges provided by the users. These override the ones automatically
        computed by the OQ Engine.
    :returns:
        A tuple of two items. First is itself a tuple of bin edges information
        for (in specified order) magnitude, distance, longitude, latitude,
        epsilon and tectonic region types.

        Second item is 6d-array representing the full disaggregation matrix.
        Dimensions are in the same order as bin edges in the first item
        of the result tuple. The matrix can be used directly by pmf-extractor
        functions.
    """
    trts = sorted(set(src.tectonic_region_type for src in sources))
    trt_num = dict((trt, i) for i, trt in enumerate(trts))
    rlzs_by_gsim = {gsim_by_trt[trt]: [0] for trt in trts}
    by_trt = groupby(sources, operator.attrgetter('tectonic_region_type'))
    sitecol = SiteCollection([site])

    # Create contexts
    ctxs = AccumDict(accum=[])
    cmaker = {}  # trt -> cmaker
    mags_by_trt = AccumDict(accum=set())
    dists = []
    tom = sources[0].temporal_occurrence_model
    oq = Oq(imtls={str(imt): [iml]},
            poes=[None],
            rlz_index=[0],
            epsilon_star=epsstar,
            truncation_level=truncation_level,
            investigation_time=tom.time_span,
            maximum_distance=source_filter.integration_distance,
            mags_by_trt=mags_by_trt,
            num_epsilon_bins=n_epsilons,
            mag_bin_width=mag_bin_width,
            distance_bin_width=dist_bin_width,
            coordinate_bin_width=coord_bin_width,
            disagg_bin_edges=bin_edges)
    for trt, srcs in by_trt.items():
        cmaker[trt] = cm = ContextMaker(trt, rlzs_by_gsim, oq)
        ctxs[trt].extend(cm.from_srcs(srcs, sitecol))
        for ctx in ctxs[trt]:
            mags_by_trt[trt] |= set(ctx.mag)
            dists.extend(ctx.rrup)

    if source_filter is filters.nofilter:
        oq.maximum_distance = filters.IntegrationDistance.new(str(max(dists)))

    # Build bin edges
    bin_edges, dic = get_edges_shapedic(oq, sitecol)

    # Compute disaggregation per TRT
    matrix = numpy.zeros([dic['mag'], dic['dist'], dic['lon'], dic['lat'],
                          dic['eps'], len(trts)])
    for trt in cmaker:
        dis = Disaggregator(ctxs[trt], sitecol, cmaker[trt], bin_edges)
        for magi in range(dis.Ma):
            try:
                dis.init(magi, src_mutex={})  # src_mutex not implemented yet
            except FarAwayRupture:
                continue
            mat4 = dis._disagg6D({imt: [iml]}, 0)[..., 0, 0]
            matrix[magi, ..., trt_num[trt]] = mat4
    return bin_edges, to_probs(matrix)


# ###################### disagg by source ################################ #

def collect_std(disaggs):
    """
    :returns: an array of shape (Ma, D, M', G)
    """
    assert len(disaggs)
    gsims = set()
    for dis in disaggs:
        gsims.update(dis.cmaker.gsims)
    gidx = {gsim: g for g, gsim in enumerate(sorted(gsims))}
    G, M = len(gidx), len(dis.cmaker.imts)
    out = AccumDict(accum=numpy.zeros((G, M)))  # (magi, dsti) -> stddev
    cnt = collections.Counter()  # (magi, dsti)
    for dis in disaggs:
        for magi in dis.std:
            for gsim, std in zip(dis.cmaker.gsims, dis.std[magi]):
                g = gidx[gsim]  # std has shape (M, U)
                for dsti, val in zip(dis.dist_idx[magi], std.T):
                    if (magi, dsti) in out:
                        out[magi, dsti][g] += val  # shape M
                    else:
                        out[magi, dsti][g] = val.copy()
                    cnt[magi, dsti] += 1 / G
    sig = numpy.zeros((dis.Ma, dis.D, M, G))
    for (magi, dsti), v in out.items():
        sig[magi, dsti] = v.T / cnt[magi, dsti]

    # the sigmas are artificially zero for not covered (magi, disti) bins
    # in that case we copy the value of the first covered bin
    # NB: this is tested in test_rtgm
    for m in range(M):
        for g in range(G):
            zeros = sig[:, :, m, g] == 0
            if zeros.any():
                magi, dsti = numpy.where(~zeros)
                sig[zeros, m, g] = sig[magi[0], dsti[0], m, g]
    return sig


def get_ints(src_ids):
    """
    :returns: array of integers from source IDs following the colon convention
    """
    out = []
    for src_id in decode(list(src_ids)):
        out.append(int(src_id.split(':')[1]))
    return numpy.uint32(out)


def disagg_source(groups, site, reduced_lt, edges_shapedic,
                  oq, imldic, monitor=Monitor()):
    """
    Compute disaggregation for the given source.

    :param groups: groups containing a single source ID
    :param site: a Site object
    :param reduced_lt: a FullLogicTree reduced to the source ID
    :param edges_shapedic: pair (bin_edges, shapedic)
    :param oq: OqParam instance
    :param imldic: dictionary imt->iml
    :param monitor: a Monitor instance
    :returns: sid, src_id, std(Ma, D, G, M), rates(Ma, D, E, M), rates(M, L1)
    """
    sitecol = SiteCollection([site])
    sitecol.sids[:] = 0
    if not hasattr(reduced_lt, 'trt_rlzs'):
        reduced_lt.init()
    edges, s = edges_shapedic
    drates4D = numpy.zeros((s['mag'], s['dist'], s['eps'], len(imldic)))
    source_id = corename(groups[0].sources[0].source_id)
    rmap, ctxs, cmakers = calc_rmap(groups, reduced_lt, sitecol, oq)
    ws = reduced_lt.rlzs['weight']
    disaggs = []
    if any(grp.src_interdep == 'mutex' for grp in groups):
        [grp] = groups  # There can be only one mutex group
        src_mutex = {
            'grp_probability': grp.grp_probability,
            'src_id': get_ints(src.source_id for src in grp),
            'weight': [src.mutex_weight for src in grp]}
    else:
        src_mutex = {}
    for ctx, cmaker in zip(ctxs, cmakers):
        dis = Disaggregator([ctx], sitecol, cmaker, edges, imldic)
        drates4D += dis.disagg_mag_dist_eps(imldic, ws, src_mutex)
        disaggs.append(dis)
    std4D = collect_std(disaggs)
    gws = reduced_lt.g_weights([cm.trt_smrs for cm in cmakers])
    rates3D = calc_mean_rates(rmap, gws, reduced_lt.gsim_lt.wget,
                              oq.imtls, list(imldic))  # (N, M, L1)
    return site.id, source_id, std4D, drates4D, rates3D[0]
