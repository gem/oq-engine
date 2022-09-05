# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2022 GEM Foundation
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

import re
import abc
import copy
import time
import warnings
import itertools
import collections
from unittest.mock import patch
import numpy
import shapely
from scipy.interpolate import interp1d

from openquake.baselib.general import (
    AccumDict, DictArray, RecordBuilder, gen_slices, kmean)
from openquake.baselib.performance import Monitor, split_array, compile, numba
from openquake.baselib.python3compat import decode
from openquake.hazardlib import valid, imt as imt_module
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.tom import (
    registry, get_pnes, FatedTOM, NegativeBinomialTOM)
from openquake.hazardlib.site import site_param_dt
from openquake.hazardlib.stats import _truncnorm_sf
from openquake.hazardlib.calc.filters import (
    SourceFilter, IntegrationDistance, magdepdist, get_distances, getdefault,
    MINMAG, MAXMAG)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.surface.planar import (
    project, project_back, get_distances_planar)

U32 = numpy.uint32
F64 = numpy.float64
TWO20 = 2**20  # used when collapsing
TWO16 = 2**16
TWO24 = 2**24
TWO32 = 2**32
STD_TYPES = (StdDev.TOTAL, StdDev.INTER_EVENT, StdDev.INTRA_EVENT)
MAX_MB = 512
KNOWN_DISTANCES = frozenset(
    'rrup rx ry0 rjb rhypo repi rcdpp azimuth azimuth_cp rvolc closest_point'
    .split())
# the following is used in the collapse method
IGNORE_PARAMS = {'mag', 'rrup', 'vs30', 'occurrence_rate', 'sids', 'mdvbin'}

# These coordinates were provided by M Gerstenberger (personal
# communication, 10 August 2018)
cshm_polygon = shapely.geometry.Polygon([(171.6, -43.3), (173.2, -43.3),
                                         (173.2, -43.9), (171.6, -43.9)])


def is_modifiable(gsim):
    """
    :returns: True if it is a ModifiableGMPE
    """
    return hasattr(gsim, 'gmpe') and hasattr(gsim, 'params')


def concat(ctxs):
    """
    Concatenate context arrays.
    :returns: list with 0, 1 or 2 elements
    """
    out, poisson, nonpoisson, nonparam = [], [], [], []
    for ctx in ctxs:
        if numpy.isnan(ctx.occurrence_rate).all():
            nonparam.append(ctx)

        # If ctx has probs_occur and occur_rate is parametric non-poisson
        elif hasattr(ctx, 'probs_occur') and ctx.probs_occur.shape[1] >= 1:
            nonpoisson.append(ctx)
        else:
            poisson.append(ctx)
    if poisson:
        out.append(numpy.concatenate(poisson).view(numpy.recarray))
    if nonpoisson:
        # Ctxs with the same shape of prob_occur are concatenated
        # and different shape sets are appended separately
        for shp in set(ctx.probs_occur.shape[1] for ctx in nonpoisson):
            p_array = [p for p in nonpoisson
                       if p.probs_occur.shape[1] == shp]
            out.append(numpy.concatenate(p_array).view(numpy.recarray))
    if nonparam:
        out.append(numpy.concatenate(nonparam).view(numpy.recarray))
    return out


def get_maxsize(M, G):
    """
    :returns: an integer N such that arrays N*M*G fit in the CPU cache
    """
    maxs = TWO20 // (16*M*G)
    assert maxs > 1, maxs
    return maxs


# numbified below
def update_pmap_n(dic, poes, rates, probs_occur, sids, itime):
    for poe, rate, probs, sid in zip(poes, rates, probs_occur, sids):
        dic[sid] *= get_pnes(rate, probs, poe, itime)


# numbified below
def update_pmap_c(dic, poes, rates, probs_occur, allsids, sizes, itime):
    start = 0
    for poe, rate, probs, size in zip(poes, rates, probs_occur, sizes):
        pne = get_pnes(rate, probs, poe, itime)
        for sid in allsids[start:start + size]:
            dic[sid] *= pne
        start += size


if numba:
    t = numba.types
    sig = t.void(t.DictType(t.uint32, t.float64[:, :]),  # dic
                 t.float64[:, :, :],                     # poes
                 t.float64[:],                           # rates
                 t.float64[:, :],                        # probs_occur
                 t.uint32[:],                            # sids
                 t.float64)                              # itime
    update_pmap_n = compile(sig)(update_pmap_n)

    sig = t.void(t.DictType(t.uint32, t.float64[:, :]),  # dic
                 t.float64[:, :, :],                     # poes
                 t.float64[:],                           # rates
                 t.float64[:, :],                        # probs_occur
                 t.uint32[:],                            # allsids
                 t.uint32[:],                            # sizes
                 t.float64)                              # itime
    update_pmap_c = compile(sig)(update_pmap_c)


def size(imtls):
    """
    :returns: size of the dictionary of arrays imtls
    """
    imls = imtls[next(iter(imtls))]
    return len(imls) * len(imtls)


def trivial(ctx, name):
    """
    :param ctx: a recarray
    :param name: name of a parameter
    :returns: True if the parameter is missing or single valued
    """
    if name not in ctx.dtype.names:
        return True
    return len(numpy.unique(numpy.float32(ctx[name]))) == 1


def expand_mdvbin(mdvbin):
    """
    :returns: a triple of integers (magbin, distbin, vs30bin)
    """
    magbin, rest = numpy.divmod(mdvbin, TWO24)
    distbin, vs30bin = numpy.divmod(rest, TWO16)
    return magbin, distbin, vs30bin


def sqrscale(x_min, x_max, n):
    """
    :param x_min: minumum value
    :param x_max: maximum value
    :param n: number of steps
    :returns: an array of n values from x_min to x_max in a quadratic scale
    """
    if not (isinstance(n, int) and n > 0):
        raise ValueError('n must be a positive integer, got %s' % n)
    if x_min < 0:
        raise ValueError('x_min must be positive, got %s' % x_min)
    if x_max <= x_min:
        raise ValueError('x_max (%s) must be bigger than x_min (%s)' %
                         (x_max, x_min))
    delta = numpy.sqrt(x_max - x_min) / (n - 1)
    return x_min + (delta * numpy.arange(n))**2


class Collapser(object):
    """
    Class managing the collapsing logic.
    """
    mag_bins = numpy.linspace(MINMAG, MAXMAG, 256)
    dist_bins = sqrscale(1, 600, 255)
    vs30_bins = numpy.linspace(0, 32767, 65536)

    def __init__(self, collapse_level, dist_types, has_vs30=False):
        self.collapse_level = collapse_level
        self.dist_types = dist_types
        self.has_vs30 = has_vs30
        self.cfactor = numpy.zeros(2)
        self.npartial = 0
        self.nfull = 0

    def calc_mdvbin(self, ctx):
        """
        :param ctx: a RuptureContext or a context array
        :return: an array of dtype numpy.uint32
        """
        dist = numpy.mean([getattr(ctx, dt) for dt in self.dist_types], axis=0)
        magbin = numpy.searchsorted(self.mag_bins, ctx.mag)
        distbin = numpy.searchsorted(self.dist_bins, dist)
        if self.has_vs30:
            vs30bin = numpy.searchsorted(self.vs30_bins, ctx.vs30)
            return magbin * TWO24 + distbin * TWO16 + vs30bin
        else:  # in test_collapse_area
            return magbin * TWO24 + distbin * TWO16

    def expand(self, mdvbin):
        """
        :returns: mag, dist and vs30 corresponding to mdvbin
        """
        mbin, dbin, vbin = expand_mdvbin(mdvbin)
        return self.mag_bins[mbin], self.dist_bins[dbin], self.vs30bins[vbin]

    def collapse(self, ctx, rup_indep, collapse_level=None):
        """
        Collapse a context recarray if possible.

        :param ctx: a recarray with fields "mdvbin" and "sids"
        :param rup_indep: False if the ruptures are mutually exclusive
        :param collapse_level: if None, use .collapse_level
        :returns: the collapsed array and a list of arrays with site IDs
        """
        ctx['mdvbin'] = self.calc_mdvbin(ctx)
        clevel = (collapse_level if collapse_level is not None
                  else self.collapse_level)
        if not rup_indep or clevel < 0:
            # no collapse
            self.cfactor[0] += len(numpy.unique(ctx.mdvbin))
            self.cfactor[1] += len(ctx)
            return ctx, ctx.sids.reshape(-1, 1)

        # names are mag, rake, vs30, rjb, mdvbin, sids, ...
        relevant = set(ctx.dtype.names) - IGNORE_PARAMS
        if all(trivial(ctx, param) for param in relevant):
            # collapse all
            far = ctx
            close = numpy.zeros(0, ctx.dtype)
            self.nfull += 1
        else:
            # collapse far away ruptures
            dst = ctx.mag * 10 * self.collapse_level
            far = ctx[ctx.rrup >= dst]
            close = ctx[ctx.rrup < dst]
            self.npartial += 1
        C = len(close)
        if len(far):
            uic = numpy.unique(  # this is fast
                far['mdvbin'], return_inverse=True, return_counts=True)
            mean = kmean(far, 'mdvbin', uic)
        else:
            mean = numpy.zeros(0, ctx.dtype)
        self.cfactor[0] += len(close) + len(mean)
        self.cfactor[1] += len(ctx)
        out = numpy.zeros(len(close) + len(mean), ctx.dtype)
        out[:C] = close
        out[C:] = mean
        allsids = [[sid] for sid in close['sids']]
        if len(far):  # this is slow
            allsids.extend(split_array(far['sids'], uic[1], uic[2]))
        # print(len(out), len(ctx))
        return out.view(numpy.recarray), allsids


class FarAwayRupture(Exception):
    """Raised if the rupture is outside the maximum distance for all sites"""


def basename(src):
    """
    :returns: the base name of a split source
    """
    src_id = src if isinstance(src, str) else src.source_id
    splits = re.split('[.:]', src_id, 1)
    if len(splits) == 2 and ';' in splits[1]:
        return splits[0] + ';' + splits[1].split(';')[1]
    return splits[0]


def get_num_distances(gsims):
    """
    :returns: the number of distances required for the given GSIMs
    """
    dists = set()
    for gsim in gsims:
        dists.update(gsim.REQUIRES_DISTANCES)
    return len(dists)


def csdict(M, N, P, start, stop):
    """
    :param M: number of IMTs
    :param N: number of sites
    :param P: number of IMLs
    :param start: index
    :param stop: index > start
    """
    ddic = {}
    for _g in range(start, stop):
        ddic[_g] = AccumDict({'_c': numpy.zeros((M, N, 2, P)),
                              '_s': numpy.zeros((N, P))})
    return ddic


def _interp(param, name, trt):
    try:
        mdd = param[name]
    except KeyError:
        return magdepdist([(MINMAG, 1000), (MAXMAG, 1000)])
    if isinstance(mdd, IntegrationDistance):
        return mdd(trt)
    elif isinstance(mdd, dict):
        return magdepdist(getdefault(mdd, trt))
    return mdd


class ContextMaker(object):
    """
    A class to manage the creation of contexts and to compute mean/stddevs
    and possibly PoEs.

    :param trt: tectonic region type string
    :param gsims: list of GSIMs or a dictionary gsim -> rlz indices
    :param oq:
       dictionary of parameters like the maximum_distance, the IMTLs,
       the investigation time, etc, or an OqParam instance
    :param extraparams:
       additional site parameters to consider, used only in the tests

    NB: the trt can be different from the tectonic region type for which
    the underlying GSIMs are defined. This is intentional.
    """
    REQUIRES = ['DISTANCES', 'SITES_PARAMETERS', 'RUPTURE_PARAMETERS']
    fewsites = False
    rup_indep = True
    tom = None

    def __init__(self, trt, gsims, oq, monitor=Monitor(), extraparams=()):
        if isinstance(oq, dict):
            param = oq
            self.mags = param.get('mags', ())
            self.cross_correl = param.get('cross_correl')  # cond_spectra_test
        else:  # OqParam
            param = vars(oq)
            param['split_sources'] = oq.split_sources
            param['min_iml'] = oq.min_iml
            param['reqv'] = oq.get_reqv()
            param['af'] = getattr(oq, 'af', None)
            self.cross_correl = oq.cross_correl
            self.imtls = oq.imtls
            try:
                self.mags = oq.mags_by_trt[trt]
            except AttributeError:
                self.mags = ()
            except KeyError:  # missing TRT but there is only one
                [(_, self.mags)] = oq.mags_by_trt.items()
        if 'imtls' in param:
            for imt in param['imtls']:
                if not isinstance(imt, str):
                    raise TypeError('Expected string, got %s' % type(imt))
            self.imtls = param['imtls']
        elif 'hazard_imtls' in param:
            self.imtls = DictArray(param['hazard_imtls'])
        elif not hasattr(self, 'imtls'):
            raise KeyError('Missing imtls in ContextMaker!')

        self.cache_distances = param.get('cache_distances', False)
        if self.cache_distances:
            # use a cache (surface ID, dist_type) for MultiFaultSources
            self.dcache = AccumDict()
            self.dcache.hit = 0
        else:
            self.dcache = None  # disabled
        self.af = param.get('af')
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.max_sites_per_tile = param.get('max_sites_per_tile', 50_000)
        self.time_per_task = param.get('time_per_task', 60)
        self.disagg_by_src = param.get('disagg_by_src')
        self.collapse_level = int(param.get('collapse_level', -1))
        self.disagg_by_src = param.get('disagg_by_src', False)
        self.trt = trt
        self.gsims = gsims
        for gsim in gsims:
            if hasattr(gsim, 'set_tables'):
                if not self.mags and not is_modifiable(gsim):
                    raise ValueError(
                        'You must supply a list of magnitudes as 2-digit '
                        'strings, like mags=["6.00", "6.10", "6.20"]')
                gsim.set_tables(self.mags, self.imtls)
        self.maximum_distance = _interp(param, 'maximum_distance', trt)
        if 'pointsource_distance' not in param:
            self.pointsource_distance = 1000.
        else:
            self.pointsource_distance = getdefault(
                param['pointsource_distance'], trt)
        self.minimum_distance = param.get('minimum_distance', 0)
        self.investigation_time = param.get('investigation_time')
        if self.investigation_time:
            self.tom = registry['PoissonTOM'](self.investigation_time)
        self.ses_seed = param.get('ses_seed', 42)
        self.ses_per_logic_tree_path = param.get('ses_per_logic_tree_path', 1)
        self.truncation_level = param.get('truncation_level', 99.)
        self.num_epsilon_bins = param.get('num_epsilon_bins', 1)
        self.ps_grid_spacing = param.get('ps_grid_spacing')
        self.split_sources = param.get('split_sources')
        self.effect = param.get('effect')
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
                if self.af and req == 'SITES_PARAMETERS':
                    reqset.add('ampcode')
                if (is_modifiable(gsim) and req == 'SITES_PARAMETERS' and
                        'apply_swiss_amplification' in gsim.params):
                    reqset.add('amplfactor')
            setattr(self, 'REQUIRES_' + req, reqset)
        try:
            self.min_iml = param['min_iml']
        except KeyError:
            self.min_iml = [0. for imt in self.imtls]
        self.reqv = param.get('reqv')
        if self.reqv is not None:
            self.REQUIRES_DISTANCES.add('repi')
        # NB: REQUIRES_DISTANCES is empty when gsims = [FromFile]
        REQUIRES_DISTANCES = self.REQUIRES_DISTANCES | {'rrup'}
        reqs = (sorted(self.REQUIRES_RUPTURE_PARAMETERS) +
                sorted(self.REQUIRES_SITES_PARAMETERS | set(extraparams)) +
                sorted(REQUIRES_DISTANCES))
        dic = {}
        for req in reqs:
            if req in site_param_dt:
                dt = site_param_dt[req]
                if isinstance(dt, tuple):  # (string_, size)
                    dic[req] = b'X' * dt[1]
                else:
                    dic[req] = dt(0)
            else:
                dic[req] = 0.
        dic['src_id'] = U32(0)
        dic['rup_id'] = U32(0)
        dic['mdvbin'] = U32(0)  # velocity-magnitude-distance bin
        dic['sids'] = U32(0)
        dic['rrup'] = numpy.float64(0)
        dic['weight'] = numpy.float64(0)
        dic['occurrence_rate'] = numpy.float64(0)
        self.defaultdict = dic
        self.collapser = Collapser(
            self.collapse_level, REQUIRES_DISTANCES, 'vs30' in dic)
        self.loglevels = DictArray(self.imtls) if self.imtls else {}
        self.shift_hypo = param.get('shift_hypo')
        with warnings.catch_warnings():
            # avoid RuntimeWarning: divide by zero encountered in log
            warnings.simplefilter("ignore")
            for imt, imls in self.imtls.items():
                if imt != 'MMI':
                    self.loglevels[imt] = numpy.log(imls)
        self.init_monitoring(monitor)

    def init_monitoring(self, monitor):
        # instantiating child monitors, may be called in the workers
        self.ctx_mon = monitor('make_contexts', measuremem=False)
        self.col_mon = monitor('collapsing contexts', measuremem=False)
        self.gmf_mon = monitor('computing mean_std', measuremem=False)
        self.poe_mon = monitor('get_poes', measuremem=False)
        self.pne_mon = monitor('composing pnes', measuremem=False)
        self.ir_mon = monitor('iter_ruptures', measuremem=False)
        self.task_no = getattr(monitor, 'task_no', 0)
        self.out_no = getattr(monitor, 'out_no', self.task_no)

    def dcache_size(self):
        """
        :returns: the size in bytes of the distance cache
        """
        if not self.dcache:
            return 0
        nbytes = 0
        for arr in self.dcache.values():
            if isinstance(arr, numpy.ndarray):
                nbytes += arr.nbytes
        return nbytes

    def read_ctxs(self, dstore, slc=None, magi=None):
        """
        :param dstore: a DataStore instance
        :param slice: a slice of contexts with the same grp_id
        :returns: a list of contexts
        """
        self.src_mutex, self.rup_mutex = dstore['mutex_by_grp'][self.grp_id]
        sitecol = dstore['sitecol'].complete.array
        if slc is None:
            slc = dstore['rup/grp_id'][:] == self.grp_id
        params = {n: dstore['rup/' + n][slc] for n in dstore['rup']}
        dtlist = []
        for par, val in params.items():
            if len(val) == 0:
                return []
            elif par == 'probs_occur':
                item = (par, object)
            elif par == 'occurrence_rate':
                item = (par, F64)
            else:
                item = (par, val[0].dtype)
            dtlist.append(item)
        for par in sitecol.dtype.names:
            if par != 'sids':
                dtlist.append((par, sitecol.dtype[par]))
        if magi is not None:
            dtlist.append(('magi', numpy.uint8))
        ctx = numpy.zeros(len(params['grp_id']), dtlist).view(numpy.recarray)
        for par, val in params.items():
            ctx[par] = val
        for par in sitecol.dtype.names:
            if par != 'sids':
                ctx[par] = sitecol[par][ctx['sids']]
        if magi is not None:
            ctx['magi'] = magi
        # NB: sorting the contexts break the disaggregation! (see case_1)

        # split parametric vs nonparametric contexts
        nans = numpy.isnan(ctx.occurrence_rate)
        if nans.sum() in (0, len(ctx)):  # no nans or all nans
            ctxs = [ctx]
        else:
            # happens in the oq-risk-tests for NZ
            ctxs = [ctx[nans], ctx[~nans]]
        return ctxs

    def recarray(self, ctxs, magi=None):
        """
        :params ctxs: a non-empty list of homogeneous contexts
        :returns: a recarray, possibly collapsed
        """
        assert ctxs
        dd = self.defaultdict.copy()
        if magi is not None:  # magnitude bin used in disaggregation
            dd['magi'] = numpy.uint8(0)

        if not hasattr(ctxs[0], 'probs_occur'):
            for ctx in ctxs:
                ctx.probs_occur = numpy.zeros(0)
            np = 0
        else:
            shps = [ctx.probs_occur.shape for ctx in ctxs]
            np = max(i[1] if len(i) > 1 else i[0] for i in shps)
        dd['probs_occur'] = numpy.zeros(np)
        if self.fewsites:  # must be at the end
            dd['clon'] = numpy.float64(0.)
            dd['clat'] = numpy.float64(0.)
        C = sum(len(ctx) for ctx in ctxs)
        ra = RecordBuilder(**dd).zeros(C)
        start = 0
        for ctx in ctxs:
            ctx = ctx.roundup(self.minimum_distance)
            slc = slice(start, start + len(ctx))
            for par in dd:
                if par == 'rup_id':
                    val = getattr(ctx, par)
                elif par == 'magi':  # in disaggregation
                    val = magi
                elif par == 'mdvbin':
                    val = 0  # overridden later
                elif par == 'weight':
                    val = getattr(ctx, par, 0.)
                else:
                    val = getattr(ctx, par, numpy.nan)
                getattr(ra, par)[slc] = val
            ra.sids[slc] = ctx.sids
            start = slc.stop
        return ra

    def get_ctx_params(self):
        """
        :returns: the interesting attributes of the context
        """
        params = {'occurrence_rate', 'sids', 'src_id',
                  'probs_occur', 'clon', 'clat', 'rrup'}
        params.update(self.REQUIRES_RUPTURE_PARAMETERS)
        for dparam in self.REQUIRES_DISTANCES:
            params.add(dparam + '_')
        return params

    def from_srcs(self, srcs, sitecol):  # used in disagg.disaggregation
        """
        :param srcs: a list of Source objects
        :param sitecol: a SiteCollection instance
        :returns: a list of context arrays
        """
        ctxs = []
        srcfilter = SourceFilter(sitecol, self.maximum_distance)
        for i, src in enumerate(srcs):
            src.id = i
            sites = srcfilter.get_close_sites(src)
            if sites is not None:
                ctxs.extend(self.get_ctxs(src, sites))
        return concat(ctxs)

    def make_rctx(self, rup):
        """
        Add .REQUIRES_RUPTURE_PARAMETERS to the rupture
        """
        ctx = RuptureContext()
        vars(ctx).update(vars(rup))
        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            if param == 'mag':
                value = numpy.round(rup.mag, 6)
            elif param == 'strike':
                value = rup.surface.get_strike()
            elif param == 'dip':
                value = rup.surface.get_dip()
            elif param == 'rake':
                value = rup.rake
            elif param == 'ztor':
                value = rup.surface.get_top_edge_depth()
            elif param == 'hypo_lon':
                value = rup.hypocenter.longitude
            elif param == 'hypo_lat':
                value = rup.hypocenter.latitude
            elif param == 'hypo_depth':
                value = rup.hypocenter.depth
            elif param == 'width':
                value = rup.surface.get_width()
            elif param == 'in_cshm':
                # used in McVerry and Bradley GMPEs
                if rup.surface:
                    lons = rup.surface.mesh.lons.flatten()
                    lats = rup.surface.mesh.lats.flatten()
                    points_in_polygon = (
                        shapely.geometry.Point(lon, lat).within(cshm_polygon)
                        for lon, lat in zip(lons, lats))
                    value = any(points_in_polygon)
                else:
                    value = False
            elif param == 'zbot':
                # needed for width estimation in CampbellBozorgnia2014
                if rup.surface:
                    value = rup.surface.mesh.depths.max()
                else:
                    value = rup.hypocenter.depth
            else:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (type(self).__name__, param))
            setattr(ctx, param, value)
        if not hasattr(ctx, 'occurrence_rate'):
            ctx.occurrence_rate = numpy.nan
        if hasattr(ctx, 'temporal_occurrence_model'):
            if isinstance(ctx.temporal_occurrence_model, NegativeBinomialTOM):
                ctx.probs_occur = ctx.temporal_occurrence_model.get_pmf(
                    ctx.occurrence_rate)

        return ctx

    def get_ctx(self, rup, sites, distances=None):
        """
        :returns: a RuptureContext (or None if filtered away)
        """
        with self.ctx_mon:
            ctx = self.make_rctx(rup)
            for name in sites.array.dtype.names:
                setattr(ctx, name, sites[name])

            if distances is None:
                distances = rup.surface.get_min_distance(sites.mesh)
            ctx.rrup = distances
            ctx.sites = sites
            for param in self.REQUIRES_DISTANCES - {'rrup'}:
                dists = get_distances(rup, sites, param, self.dcache)
                setattr(ctx, param, dists)

            # Equivalent distances
            reqv_obj = (self.reqv.get(self.trt) if self.reqv else None)
            if reqv_obj and not rup.surface:  # PointRuptures have no surface
                reqv = reqv_obj.get(ctx.repi, rup.mag)
                if 'rjb' in self.REQUIRES_DISTANCES:
                    ctx.rjb = reqv
                if 'rrup' in self.REQUIRES_DISTANCES:
                    ctx.rrup = numpy.sqrt(reqv**2 + rup.hypocenter.depth**2)

        return ctx

    def _get_ctx_planar(self, mag, planar, sites, src_id, start_stop, tom):
        with self.ctx_mon:
            # computing distances
            rrup, xx, yy = project(planar, sites.xyz)  # (3, U, N)
            if self.fewsites:
                # get the closest points on the surface
                closest = project_back(planar, xx, yy)  # (3, U, N)
            dists = {'rrup': rrup}
            for par in self.REQUIRES_DISTANCES - {'rrup'}:
                dists[par] = get_distances_planar(planar, sites, par)
            for par in dists:
                dst = dists[par]
                if self.minimum_distance:
                    dst[dst < self.minimum_distance] = self.minimum_distance

            # building contexts; ctx has shape (U, N), ctxt (N, U)
            ctx = self.build_ctx((len(planar), len(sites)))
            ctxt = ctx.T  # smart trick taking advantage of numpy magic
            ctxt['src_id'] = src_id

            if self.fewsites:
                # the loop below is a bit slow
                for u, rup_id in enumerate(range(*start_stop)):
                    ctx[u]['rup_id'] = rup_id

            # setting rupture parameters
            for par in self.ruptparams:
                if par == 'mag':
                    ctxt[par] = mag
                elif par == 'occurrence_rate':
                    ctxt[par] = planar.wlr[:, 2]  # shape U-> (N, U)
                elif par == 'width':
                    ctxt[par] = planar.wlr[:, 0]
                elif par == 'strike':
                    ctxt[par] = planar.sdr[:, 0]
                elif par == 'dip':
                    ctxt[par] = planar.sdr[:, 1]
                elif par == 'rake':
                    ctxt[par] = planar.sdr[:, 2]
                elif par == 'ztor':  # top edge depth
                    ctxt[par] = planar.corners[:, 2, 0]
                elif par == 'zbot':  # bottom edge depth
                    ctxt[par] = planar.corners[:, 2, 3]
                elif par == 'hypo_lon':
                    ctxt[par] = planar.hypo[:, 0]
                elif par == 'hypo_lat':
                    ctxt[par] = planar.hypo[:, 1]
                elif par == 'hypo_depth':
                    ctxt[par] = planar.hypo[:, 2]

            # setting distance parameters
            for par in dists:
                ctx[par] = dists[par]
            if self.fewsites:
                ctx['clon'] = closest[0]
                ctx['clat'] = closest[1]

            # setting site parameters
            for par in self.siteparams:
                ctx[par] = sites.array[par]  # shape N-> (U, N)
            if hasattr(tom, 'get_pmf'):  # NegativeBinomialTOM
                # read Probability Mass Function from model and reshape it
                # into predetermined shape of probs_occur
                pmf = tom.get_pmf(planar.wlr[:, 2],
                                  n_max=ctx['probs_occur'].shape[2])
                ctx['probs_occur'] = pmf[:, numpy.newaxis, :]

        return ctx

    def get_ctxs_planar(self, src, sitecol):
        """
        :param src: a (Collapsed)PointSource
        :param sitecol: a filtered SiteCollection
        :returns: a list with 0 or 1 context array
        """
        dd = self.defaultdict.copy()
        tom = src.temporal_occurrence_model

        if isinstance(tom, NegativeBinomialTOM):
            if hasattr(src, 'pointsources'):  # CollapsedPointSource
                maxrate = max(max(ps.mfd.occurrence_rates)
                              for ps in src.pointsources)
            else:  # regular source
                maxrate = max(src.mfd.occurrence_rates)
            p_size = tom.get_pmf(maxrate).shape[1]
            dd['probs_occur'] = numpy.zeros(p_size)
        else:
            dd['probs_occur'] = numpy.zeros(0)

        if self.fewsites:
            dd['clon'] = numpy.float64(0.)
            dd['clat'] = numpy.float64(0.)

        self.build_ctx = RecordBuilder(**dd).zeros
        self.siteparams = [par for par in sitecol.array.dtype.names
                           if par in dd]
        self.ruptparams = (
            self.REQUIRES_RUPTURE_PARAMETERS | {'occurrence_rate'})

        with self.ir_mon:
            # building planar geometries
            planardict = src.get_planar(self.shift_hypo)

        magdist = {mag: self.maximum_distance(mag)
                   for mag, rate in src.get_annual_occurrence_rates()}
        maxmag = max(magdist)
        ctxs = []
        max_radius = src.max_radius()
        cdist = sitecol.get_cdist(src.location)
        mask = cdist <= magdist[maxmag] + max_radius
        sitecol = sitecol.filter(mask)
        if sitecol is None:
            return []

        for magi, mag, planarlist, sites in self._quartets(
                src, sitecol, cdist[mask], planardict):
            if not planarlist:
                continue
            elif len(planarlist) > 1:  # when using ps_grid_spacing
                pla = numpy.concatenate(planarlist).view(numpy.recarray)
            else:
                pla = planarlist[0]

            offset = src.offset + magi * len(pla)
            start_stop = offset, offset + len(pla)
            ctx = self._get_ctx_planar(
                mag, pla, sites, src.id, start_stop, tom).flatten()
            ctxt = ctx[ctx.rrup < magdist[mag]]
            if len(ctxt):
                ctxs.append(ctxt)
        return concat(ctxs)

    def _quartets(self, src, sitecol, cdist, planardict):
        # splitting by magnitude
        quartets = []
        if src.count_nphc() == 1:
            # one rupture per magnitude
            for m, (mag, pla) in enumerate(planardict.items()):
                quartets.append((m, mag, pla, sitecol))
        else:
            for m, rup in enumerate(src.iruptures()):
                mag = rup.mag
                arr = [rup.surface.array.reshape(-1, 3)]
                pla = planardict[mag]
                psdist = (self.pointsource_distance + src.ps_grid_spacing +
                          src.radius[m])
                close = sitecol.filter(cdist <= psdist)
                far = sitecol.filter(cdist > psdist)
                if self.fewsites:
                    if close is None:  # all is far, common for small mag
                        quartets.append((m, mag, arr, sitecol))
                    else:  # something is close
                        quartets.append((m, mag, pla, sitecol))
                else:  # many sites
                    if close is None:  # all is far
                        quartets.append((m, mag, arr, far))
                    elif far is None:  # all is close
                        quartets.append((m, mag, pla, close))
                    else:  # some sites are far, some are close
                        quartets.append((m, mag, arr, far))
                        quartets.append((m, mag, pla, close))
        return quartets

    def get_ctxs(self, src, sitecol, src_id=0, step=1):
        """
        :param src:
            a source object (already split) or a list of ruptures
        :param sitecol:
            a (filtered) SiteCollection
        :param src_id:
            integer source ID used where src is actually a list
        :param step:
            > 1 only in preclassical
        :returns:
            fat RuptureContexts sorted by mag
        """
        self.fewsites = len(sitecol.complete) <= self.max_sites_disagg
        ctxs = []
        if getattr(src, 'location', None) and step == 1:
            return self.get_ctxs_planar(src, sitecol)
        elif hasattr(src, 'source_id'):  # other source
            with self.ir_mon:
                allrups = numpy.array(list(src.iter_ruptures(
                    shift_hypo=self.shift_hypo, step=step)))
                for i, rup in enumerate(allrups):
                    rup.rup_id = src.offset + i
                self.num_rups = len(allrups)
                # sorted by mag by construction
                u32mags = U32([rup.mag * 100 for rup in allrups])
                rups_sites = [(rups, sitecol)
                              for rups in split_array(allrups, u32mags)]
            src_id = src.id
        else:  # in event based we get a list with a single rupture
            rups_sites = [(src, sitecol)]
            src_id = 0
        for rups, sites in rups_sites:  # ruptures with the same magnitude
            if len(rups) == 0:  # may happen in case of min_mag/max_mag
                continue

            magdist = self.maximum_distance(rups[0].mag)
            dists = [get_distances(rup, sites, 'rrup', self.dcache)
                     for rup in rups]
            for u, rup in enumerate(rups):
                mask = dists[u] <= magdist
                if mask.any():
                    r_sites = sites.filter(mask)
                    ctx = self.get_ctx(rup, r_sites, dists[u][mask])
                    ctx.src_id = src_id
                    ctx.rup_id = rup.rup_id
                    ctxs.append(ctx)
                    if self.fewsites:
                        c = rup.surface.get_closest_points(sites.complete)
                        ctx.clon = c.lons[ctx.sids]
                        ctx.clat = c.lats[ctx.sids]
        return [] if not ctxs else [self.recarray(ctxs)]

    def max_intensity(self, sitecol1, mags, dists):
        """
        :param sitecol1: a SiteCollection instance with a single site
        :param mags: a sequence of magnitudes
        :param dists: a sequence of distances
        :returns: an array of GMVs of shape (#mags, #dists)
        """
        assert len(sitecol1) == 1, sitecol1
        nmags, ndists = len(mags), len(dists)
        gmv = numpy.zeros((nmags, ndists))
        for m, d in itertools.product(range(nmags), range(ndists)):
            mag, dist = mags[m], dists[d]
            ctx = RuptureContext()
            for par in self.REQUIRES_RUPTURE_PARAMETERS:
                setattr(ctx, par, 0)
            for dst in self.REQUIRES_DISTANCES:
                setattr(ctx, dst, numpy.array([dist]))
            for par in self.REQUIRES_SITES_PARAMETERS:
                setattr(ctx, par, getattr(sitecol1, par))
            ctx.sids = sitecol1.sids
            ctx.mag = mag
            ctx.width = .01  # 10 meters to avoid warnings in abrahamson_2014
            try:
                maxmean = self.get_mean_stds([ctx])[0].max()
                # shape NM
            except ValueError:  # magnitude outside of supported range
                continue
            else:
                gmv[m, d] = numpy.exp(maxmean)
        return gmv

    # not used by the engine, is is meant for notebooks
    def get_poes(self, srcs, sitecol, collapse_level=-1):
        """
        :param srcs: a list of sources with the same TRT
        :param sitecol: a SiteCollection instance with N sites
        :returns: an array of PoEs of shape (N, L, G)
        """
        self.collapser.cfactor = numpy.zeros(2)
        ctxs = self.from_srcs(srcs, sitecol)
        with patch.object(self.collapser, 'collapse_level', collapse_level):
            return self.get_pmap(ctxs).array(len(sitecol))

    def get_pmap(self, ctxs, probmap=None):
        """
        :param ctxs: a list of context arrays
        :param probmap: if not None, update it
        :returns: a new ProbabilityMap if probmap is None
        """
        if probmap is None:  # create new pmap
            pmap = ProbabilityMap(size(self.imtls), len(self.gsims))
        else:  # update passed probmap
            pmap = probmap
        if self.tom is None:
            itime = -1.
        elif isinstance(self.tom, FatedTOM):
            itime = 0.
        else:
            itime = self.tom.time_span
        if numba:
            dic = numba.typed.Dict.empty(
                key_type=t.uint32,
                value_type=t.float64[:, :])
        else:
            dic = {}  # sid -> array of shape (L, G)
        for ctx in ctxs:
            # allocating pmap in advance
            for sid in numpy.unique(ctx.sids):
                dic[sid] = pmap.setdefault(sid, self.rup_indep).array
            for poes, ctxt, slcsids in self.gen_poes(ctx):
                probs_occur = getattr(ctxt, 'probs_occur',
                                      numpy.zeros((len(ctxt), 0)))
                rates = ctxt.occurrence_rate
                with self.pne_mon:
                    if isinstance(slcsids, numpy.ndarray):
                        # no collapse: avoiding an inner loop can give a 25%
                        if self.rup_indep:
                            update_pmap_n(dic, poes, rates, probs_occur,
                                          ctxt.sids, itime)
                        else:  # USAmodel, New Madrid cluster
                            z = zip(poes, rates, probs_occur,
                                    ctxt.weight, ctxt.sids)
                            for poe, rate, probs, wei, sid in z:
                                pne = get_pnes(rate, probs, poe, itime)
                                dic[sid] += (1. - pne) * wei
                    else:  # collapse is possible only for rup_indep
                        allsids = []
                        sizes = []
                        for sids in slcsids:
                            allsids.extend(sids)
                            sizes.append(len(sids))
                        update_pmap_c(dic, poes, rates, probs_occur,
                                      U32(allsids), U32(sizes), itime)

        if probmap is None:  # return the new pmap
            if self.rup_indep:
                for arr in dic.values():
                    arr[:] = 1. - arr
            return pmap

    # called by gen_poes and by the GmfComputer
    def get_mean_stds(self, ctxs):
        """
        :param ctxs: a list of contexts with N=sum(len(ctx) for ctx in ctxs)
        :returns: an array of shape (4, G, M, N) with mean and stddevs
        """
        if not hasattr(self, 'imts'):
            self.imts = tuple(imt_module.from_string(im) for im in self.imtls)
        N = sum(len(ctx) for ctx in ctxs)
        M = len(self.imtls)
        G = len(self.gsims)
        out = numpy.zeros((4, G, M, N))
        if all(isinstance(ctx, numpy.recarray) for ctx in ctxs):
            # contexts already vectorized
            recarrays = ctxs
        else:  # vectorize the contexts
            recarrays = [self.recarray(ctxs)]
        if any(hasattr(gsim, 'gmpe_table') for gsim in self.gsims):
            assert len(recarrays) == 1, len(recarrays)
            recarrays = split_array(recarrays[0], U32(recarrays[0].mag*100))
        self.adj = {gsim: [] for gsim in self.gsims}  # NSHM2014 adjustments
        for g, gsim in enumerate(self.gsims):
            compute = gsim.__class__.compute
            start = 0
            for ctx in recarrays:
                slc = slice(start, start + len(ctx))
                adj = compute(gsim, ctx, self.imts, *out[:, g, :, slc])
                if adj is not None:
                    self.adj[gsim].append(adj)
                start = slc.stop
            if self.adj[gsim]:
                self.adj[gsim] = numpy.concatenate(self.adj[gsim])
            if self.truncation_level not in (0, 99.) and (
                    out[1, g] == 0.).any():
                raise ValueError('Total StdDev is zero for %s' % gsim)
        return out

    # http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.845.163&rep=rep1&type=pdf
    def get_cs_contrib(self, ctx, imti, imls):
        """
        :param ctx:
           a context array
        :param imti:
            IMT index in the range 0..M-1
        :param imls:
            P intensity measure levels for the IMT specified by the index
        :returns:
            a dictionary g_ -> key -> array where g_ is an index,
            key is the string '_c' or '_s',  and the arrays have shape
            (M, N, 2, P) or (N, P) respectively.

        Compute the contributions to the conditional spectra, in a form
        suitable for later composition.

        NB: at the present if works only for poissonian contexts
        """
        assert self.tom
        sids, counts = numpy.unique(ctx.sids, return_counts=True)
        assert len(set(counts)) == 1, counts  # must be all equal
        N = len(sids)
        U = len(ctx) // N
        G = len(self.gsims)
        M = len(self.imtls)
        P = len(imls)
        out = csdict(M, N, P, self.start, self.start + G)
        mean_stds = self.get_mean_stds([ctx])  # (4, G, M, N*C)
        imt_ref = self.imts[imti]
        rho = numpy.array([self.cross_correl.get_correlation(imt_ref, imt)
                           for imt in self.imts])
        m_range = range(len(self.imts))
        # probs = 1 - exp(-occurrence_rates*time_span)
        probs = self.tom.get_probability_one_or_more_occurrences(
            ctx.occurrence_rate)  # shape N * U
        for n in range(N):
            # NB: to understand the code below, consider the case with
            # N=3 sites and C=2 contexts; then the indices N*C are
            # 0: first site
            # 1: second site
            # 2: third site
            # 3: first site
            # 4: second site
            # 5: third site
            # i.e. idxs = [0, 3], [1, 4], [2, 5] for sites 0, 1, 2
            slc = slice(n, N * U, N)  # U indices
            for g in range(G):
                mu = mean_stds[0, g, :, slc]  # shape (M, U)
                sig = mean_stds[1, g, :, slc]  # shape (M, U)
                c = out[self.start + g]['_c']
                s = out[self.start + g]['_s']
                for p in range(P):
                    eps = (imls[p] - mu[imti]) / sig[imti]  # shape U
                    poes = _truncnorm_sf(self.truncation_level, eps)  # shape U
                    ws = -numpy.log(
                        (1. - probs[slc]) ** poes) / self.investigation_time
                    s[n, p] = ws.sum()  # weights not summing up to 1
                    for m in m_range:
                        c[m, n, 0, p] = ws @ (mu[m] + rho[m] * eps * sig[m])
                        c[m, n, 1, p] = ws @ (sig[m]**2 * (1. - rho[m]**2))
        return out

    def gen_poes(self, ctx):
        """
        :param ctx: a vectorized context (recarray) of size N
        :yields: poes, ctxt, slcsids with poes of shape (N, L, G)
        """
        from openquake.hazardlib.site_amplification import get_poes_site
        (M, L1), G = self.loglevels.array.shape, len(self.gsims)
        maxsize = get_maxsize(M, G)
        # L1 is the reduction factor such that the NLG arrays have
        # the same size as the GMN array and fit in the CPU cache

        # collapse if possible
        with self.col_mon:
            ctx, allsids = self.collapser.collapse(ctx, self.rup_indep)

        # split large context arrays to avoid filling the CPU cache
        if ctx.nbytes > maxsize:
            slices = gen_slices(0, len(ctx), maxsize)
        else:
            slices = [slice(0, len(ctx))]

        for bigslc in slices:
            s = bigslc.start
            with self.gmf_mon:
                mean_stdt = self.get_mean_stds([ctx[bigslc]])
            for slc in gen_slices(bigslc.start, bigslc.stop, maxsize // L1):
                slcsids = allsids[slc]
                ctxt = ctx[slc]
                self.slc = slice(slc.start - s, slc.stop - s)  # in get_poes
                with self.poe_mon:
                    poes = numpy.zeros((len(ctxt), M*L1, G))
                    for g, gsim in enumerate(self.gsims):
                        ms = mean_stdt[:2, g, :, self.slc]
                        # builds poes of shape (n, L, G)
                        if self.af:  # kernel amplification method
                            poes[:, :, g] = get_poes_site(ms, self, ctxt)
                        else:  # regular case
                            poes[:, :, g] = gsim.get_poes(ms, self, ctxt)
                yield poes, ctxt, slcsids

    def estimate_sites(self, src, sites):
        """
        :returns: how many sites are impacted overall
        """
        nphc = src.count_nphc()
        dists = sites.get_cdist(src.location)
        planardict = src.get_planar(iruptures=True)
        esites = 0
        for m, (mag, [planar]) in enumerate(planardict.items()):
            rrup = dists[dists < self.maximum_distance(mag) + src.radius[m]]
            nclose = (rrup < self.pointsource_distance + src.ps_grid_spacing +
                      src.radius[m]).sum()
            nfar = len(rrup) - nclose
            esites += nclose * nphc + nfar
        return esites

    # tested in test_collapse_small
    def estimate_weight(self, src, srcfilter, multiplier=1):
        """
        :param src: a source object
        :param srcfilter: a SourceFilter instance
        :returns: the weight of the source (num_ruptures * <num_sites/N>)
        """
        sites = srcfilter.get_close_sites(src)
        if sites is None:
            # may happen for CollapsedPointSources
            return 0
        src.nsites = len(sites)
        N = len(srcfilter.sitecol.complete)  # total sites
        if (hasattr(src, 'location') and src.count_nphc() > 1 and
                self.pointsource_distance < 1000):
            esites = self.estimate_sites(src, sites) * multiplier
        else:
            ctxs = self.get_ctxs(src, sites, step=10)  # reduced number
            if not ctxs:
                return src.num_ruptures if N == 1 else 0
            esites = (len(ctxs[0]) * src.num_ruptures /
                      self.num_rups * multiplier)
        weight = esites / N  # the weight is the effective number of ruptures
        src.esites = int(esites)
        return weight

    def set_weight(self, sources, srcfilter, multiplier=1, mon=Monitor()):
        """
        Set the weight attribute on each prefiltered source
        """
        if hasattr(srcfilter, 'array'):  # a SiteCollection was passed
            srcfilter = SourceFilter(srcfilter, self.maximum_distance)
        N = len(srcfilter.sitecol)
        G = len(self.gsims)
        for src in sources:
            src.num_ruptures = src.count_ruptures()
            if src.nsites == 0:  # was discarded by the prefiltering
                src.weight = .001
                src.esites = 0
            else:
                with mon:
                    src.esites = 0  # overridden inside estimate_weight
                    src.weight = .1 + self.estimate_weight(
                        src, srcfilter, multiplier) * G
                    if src.code == b'F' and N <= self.max_sites_disagg:
                        src.weight *= 20  # test ucerf
                    elif src.code == b'S':
                        src.weight += .9
                    elif src.code == b'C':
                        src.weight += 9.9


# see contexts_tests.py for examples of collapse
# probs_occur = functools.reduce(combine_pmf, (r.probs_occur for r in rups))
def combine_pmf(o1, o2):
    """
    Combine probabilities of occurrence; used to collapse nonparametric
    ruptures.

    :param o1: probability distribution of length n1
    :param o2: probability distribution of length n2
    :returns: probability distribution of length n1 + n2 - 1

    >>> combine_pmf([.99, .01], [.98, .02])
    array([9.702e-01, 2.960e-02, 2.000e-04])
    """
    n1 = len(o1)
    n2 = len(o2)
    o = numpy.zeros(n1 + n2 - 1)
    for i in range(n1):
        for j in range(n2):
            o[i + j] += o1[i] * o2[j]
    return o


def print_finite_size(rups):
    """
    Used to print the number of finite-size ruptures
    """
    c = collections.Counter()
    for rup in rups:
        if rup.surface:
            c['%.2f' % rup.mag] += 1
    print(c)
    print('total finite size ruptures = ', sum(c.values()))


class PmapMaker(object):
    """
    A class to compute the PoEs from a given source
    """
    def __init__(self, cmaker, srcfilter, group):
        vars(self).update(vars(cmaker))
        self.cmaker = cmaker
        self.srcfilter = srcfilter
        self.N = len(self.srcfilter.sitecol.complete)
        try:
            self.sources = group.sources
        except AttributeError:  # already a list of sources
            self.sources = group
        self.src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
        self.cmaker.rup_indep = getattr(group, 'rup_interdep', None) != 'mutex'
        self.fewsites = self.N <= cmaker.max_sites_disagg

    def count_bytes(self, ctxs):
        # # usuful for debugging memory issues
        rparams = len(self.cmaker.REQUIRES_RUPTURE_PARAMETERS)
        sparams = len(self.cmaker.REQUIRES_SITES_PARAMETERS) + 1
        dparams = len(self.cmaker.REQUIRES_DISTANCES)
        nbytes = 0
        for ctx in ctxs:
            nsites = len(ctx)
            nbytes += 8 * rparams
            nbytes += 8 * sparams * nsites
            nbytes += 8 * dparams * nsites
        return nbytes

    def _get_ctxs(self, src):
        sites = self.srcfilter.get_close_sites(src)
        if sites is None:
            return []
        ctxs = self.cmaker.get_ctxs(src, sites)
        if hasattr(src, 'mutex_weight'):
            for ctx in ctxs:
                if ctx.weight.any():
                    ctx['weight'] *= src.mutex_weight
                else:
                    ctx['weight'] = src.mutex_weight
        if self.fewsites:  # keep rupdata in memory (before collapse)
            for ctx in ctxs:
                self.rupdata.append(ctx)
        return ctxs

    def _make_src_indep(self):
        # sources with the same ID
        pmap = ProbabilityMap(size(self.imtls), len(self.gsims))
        cm = self.cmaker
        allctxs = []
        ctxs_mb = 0
        totlen = 0
        t0 = time.time()
        for src in self.sources:
            ctxs = self._get_ctxs(src)
            ctxs_mb += sum(ctx.nbytes for ctx in ctxs) / TWO20  # TWO20=1MB
            src.nsites = sum(len(ctx) for ctx in ctxs)
            totlen += src.nsites
            allctxs.extend(ctxs)
            if ctxs_mb > MAX_MB:
                cm.get_pmap(concat(allctxs), pmap)
                allctxs.clear()
                ctxs_mb = 0
        if allctxs:
            cm.get_pmap(concat(allctxs), pmap)
            allctxs.clear()
        dt = time.time() - t0
        nsrcs = len(self.sources)
        for src in self.sources:
            self.source_data['src_id'].append(src.source_id)
            self.source_data['grp_id'].append(src.grp_id)
            self.source_data['nsites'].append(src.nsites)
            self.source_data['esites'].append(src.esites)
            self.source_data['nrupts'].append(src.num_ruptures)
            self.source_data['weight'].append(src.weight)
            self.source_data['ctimes'].append(
                dt * src.nsites / totlen if totlen else dt / nsrcs)
            self.source_data['taskno'].append(cm.task_no)
        return ~pmap if cm.rup_indep else pmap

    def _make_src_mutex(self):
        # used in the Japan model, test case_27
        pmap_by_src = {}
        cm = self.cmaker
        for src in self.sources:
            t0 = time.time()
            pm = ProbabilityMap(cm.imtls.size, len(cm.gsims))
            ctxs = self._get_ctxs(src)
            nctxs = len(ctxs)
            nsites = sum(len(ctx) for ctx in ctxs)
            if nsites:
                cm.get_pmap(ctxs, pm)

            p = (~pm if cm.rup_indep else pm) * src.mutex_weight
            if ':' in src.source_id:
                srcid = basename(src)
                if srcid in pmap_by_src:
                    pmap_by_src[srcid] += p
                else:
                    pmap_by_src[srcid] = p
            else:
                pmap_by_src[src.source_id] = p
            dt = time.time() - t0
            self.source_data['src_id'].append(src.source_id)
            self.source_data['grp_id'].append(src.grp_id)
            self.source_data['nsites'].append(nsites)
            self.source_data['esites'].append(src.esites)
            self.source_data['nrupts'].append(nctxs)
            self.source_data['weight'].append(src.weight)
            self.source_data['ctimes'].append(dt)
            self.source_data['taskno'].append(cm.task_no)

        return pmap_by_src

    def make(self):
        dic = {}
        self.rupdata = []
        self.source_data = AccumDict(accum=[])
        grp_id = self.sources[0].grp_id
        if self.src_mutex:
            pmap = ProbabilityMap(size(self.imtls), len(self.gsims))
            pmap_by_src = self._make_src_mutex()
            for source_id, pm in pmap_by_src.items():
                pmap += pm
        else:
            pmap = self._make_src_indep()
        dic['pmap'] = pmap
        dic['cfactor'] = self.cmaker.collapser.cfactor
        dic['rup_data'] = concat(self.rupdata)
        dic['source_data'] = self.source_data
        dic['task_no'] = self.task_no
        dic['grp_id'] = grp_id
        if self.disagg_by_src and self.src_mutex:
            dic['pmap_by_src'] = pmap_by_src
        elif self.disagg_by_src:
            # all the sources in the group have the same source_id because
            # of the groupby(group, get_source_id) in classical.py
            srcid = basename(self.sources[0])
            dic['pmap_by_src'] = {srcid: pmap}
        return dic


class BaseContext(metaclass=abc.ABCMeta):
    """
    Base class for context object.
    """
    def __eq__(self, other):
        """
        Return True if ``other`` has same attributes with same values.
        """
        if isinstance(other, self.__class__):
            if self._slots_ == other._slots_:
                oks = []
                for s in self._slots_:
                    a, b = getattr(self, s, None), getattr(other, s, None)
                    if a is None and b is None:
                        ok = True
                    elif a is None and b is not None:
                        ok = False
                    elif a is not None and b is None:
                        ok = False
                    elif hasattr(a, 'shape') and hasattr(b, 'shape'):
                        if a.shape == b.shape:
                            ok = numpy.allclose(a, b)
                        else:
                            ok = False
                    else:
                        ok = a == b
                    oks.append(ok)
                return numpy.all(oks)
        return False


# mock of a site collection used in the tests and in the SMTK
class SitesContext(BaseContext):
    """
    Sites calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of the sites collection.
    Every GSIM class is required to declare what :attr:`sites parameters
    <GroundShakingIntensityModel.REQUIRES_SITES_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    # _slots_ is used in hazardlib check_gsim and in the SMTK
    def __init__(self, slots='vs30 vs30measured z1pt0 z2pt5'.split(),
                 sitecol=None):
        self._slots_ = slots
        if sitecol is not None:
            self.sids = sitecol.sids
            for slot in slots:
                setattr(self, slot, getattr(sitecol, slot))

    # used in the SMTK
    def __len__(self):
        return len(self.sids)


class DistancesContext(BaseContext):
    """
    Distances context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant distances between sites from the collection
    and the rupture. Every GSIM class is required to declare what
    :attr:`distance measures <GroundShakingIntensityModel.REQUIRES_DISTANCES>`
    does it need. Only those required values are calculated and made available
    in a result context object.
    """
    _slots_ = ('rrup', 'rx', 'rjb', 'rhypo', 'repi', 'ry0', 'rcdpp',
               'azimuth', 'hanging_wall', 'rvolc')

    def __init__(self, param_dist_pairs=()):
        for param, dist in param_dist_pairs:
            setattr(self, param, dist)

    def roundup(self, minimum_distance):
        """
        If the minimum_distance is nonzero, returns a copy of the
        DistancesContext with updated distances, i.e. the ones below
        minimum_distance are rounded up to the minimum_distance. Otherwise,
        returns the original DistancesContext unchanged.
        """
        if not minimum_distance:
            return self
        ctx = DistancesContext()
        for dist, array in vars(self).items():
            small_distances = array < minimum_distance
            if small_distances.any():
                array = numpy.array(array)  # make a copy first
                array[small_distances] = minimum_distance
                array.flags.writeable = False
            setattr(ctx, dist, array)
        return ctx


def get_dists(ctx):
    """
    Extract the distance parameters from a context.

    :returns: a dictionary dist_name -> distances
    """
    return {par: dist for par, dist in vars(ctx).items()
            if par in KNOWN_DISTANCES}


# used to produce a RuptureContext suitable for legacy code, i.e. for calls
# to .get_mean_and_stddevs, like for instance in the SMTK
def full_context(sites, rup, dctx=None):
    """
    :returns: a full RuptureContext with all the relevant attributes
    """
    self = RuptureContext()
    self.src_id = 0
    for par, val in vars(rup).items():
        setattr(self, par, val)
    if not hasattr(self, 'occurrence_rate'):
        self.occurrence_rate = numpy.nan
    if hasattr(sites, 'array'):  # is a SiteCollection
        for par in sites.array.dtype.names:
            setattr(self, par, sites[par])
    else:  # sites is a SitesContext
        for par, val in vars(sites).items():
            setattr(self, par, val)
    if dctx:
        for par, val in vars(dctx).items():
            setattr(self, par, val)
    return self


def get_mean_stds(gsim, ctx, imts, **kw):
    """
    :param gsim: a single GSIM or a a list of GSIMs
    :param ctx: a RuptureContext or a recarray of size N
    :param imts: a list of M IMTs
    :param kw: additional keyword arguments
    :returns:
        an array of shape (4, M, N) obtained by applying the
        given GSIM, ctx amd imts, or an array of shape (G, 4, M, N)
    """
    imtls = {imt.string: [0] for imt in imts}
    single = hasattr(gsim, 'compute')
    kw['imtls'] = imtls
    cmaker = ContextMaker('*', [gsim] if single else gsim, kw)
    out = cmaker.get_mean_stds([ctx])  # (4, G, M, N)
    return out[:, 0] if single else out


# mock of a rupture used in the tests and in the SMTK
class RuptureContext(BaseContext):
    """
    Rupture calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of a single rupture. Every
    GSIM class is required to declare what :attr:`rupture parameters
    <GroundShakingIntensityModel.REQUIRES_RUPTURE_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    src_id = 0
    rup_id = 0
    _slots_ = (
        'mag', 'strike', 'dip', 'rake', 'ztor', 'hypo_lon', 'hypo_lat',
        'hypo_depth', 'width', 'hypo_loc', 'src_id', 'rup_id')

    def __init__(self, param_pairs=()):
        for param, value in param_pairs:
            setattr(self, param, value)

    def size(self):
        """
        If the context is a multi rupture context, i.e. it contains an array
        of magnitudes and it refers to a single site, returns the size of
        the array, otherwise returns 1.
        """
        nsites = len(self.sids)
        if nsites == 1 and isinstance(self.mag, numpy.ndarray):
            return len(self.mag)
        return nsites

    # used in acme_2019
    def __len__(self):
        return len(self.sids)

    def roundup(self, minimum_distance):
        """
        If the minimum_distance is nonzero, returns a copy of the
        RuptureContext with updated distances, i.e. the ones below
        minimum_distance are rounded up to the minimum_distance. Otherwise,
        returns the original.
        """
        if not minimum_distance:
            return self
        ctx = copy.copy(self)
        for dist, array in vars(self).items():
            if dist in KNOWN_DISTANCES:
                small_distances = array < minimum_distance
                if small_distances.any():
                    array = numpy.array(array)  # make a copy first
                    array[small_distances] = minimum_distance
                    array.flags.writeable = False
                setattr(ctx, dist, array)
        return ctx


class Effect(object):
    """
    Compute the effect of a rupture of a given magnitude and distance.

    :param effect_by_mag: a dictionary magstring -> intensities
    :param dists: array of distances, one per each intensity
    :param cdist: collapse distance
    """
    def __init__(self, effect_by_mag, dists, collapse_dist=None):
        self.effect_by_mag = effect_by_mag
        self.dists = dists
        self.nbins = len(dists)

    def collapse_value(self, collapse_dist):
        """
        :returns: intensity at collapse distance
        """
        # get the maximum magnitude with a cutoff at 7
        for mag in self.effect_by_mag:
            if mag > '7.00':
                break
        effect = self.effect_by_mag[mag]
        idx = numpy.searchsorted(self.dists, collapse_dist)
        return effect[idx-1 if idx == self.nbins else idx]

    def __call__(self, mag, dist):
        di = numpy.searchsorted(self.dists, dist)
        if di == self.nbins:
            di = self.nbins
        eff = self.effect_by_mag['%.2f' % mag][di]
        return eff

    # this is used to compute the magnitude-dependent pointsource_distance
    def dist_by_mag(self, intensity):
        """
        :returns: a dict magstring -> distance
        """
        dst = {}  # magnitude -> distance
        for mag, intensities in self.effect_by_mag.items():
            if intensity < intensities.min():
                dst[mag] = self.dists[-1]  # largest distance
            elif intensity > intensities.max():
                dst[mag] = self.dists[0]  # smallest distance
            else:
                dst[mag] = interp1d(intensities, self.dists)(intensity)
        return dst


def get_effect_by_mag(mags, sitecol1, gsims_by_trt, maximum_distance, imtls):
    """
    :param mags: an ordered list of magnitude strings with format %.2f
    :param sitecol1: a SiteCollection with a single site
    :param gsims_by_trt: a dictionary trt -> gsims
    :param maximum_distance: an IntegrationDistance object
    :param imtls: a DictArray with intensity measure types and levels
    :returns: a dict magnitude-string -> array(#dists, #trts)
    """
    trts = list(gsims_by_trt)
    ndists = 51
    gmv = numpy.zeros((len(mags), ndists, len(trts)))
    param = dict(maximum_distance=maximum_distance, imtls=imtls)
    for t, trt in enumerate(trts):
        dist_bins = maximum_distance.get_dist_bins(trt, ndists)
        cmaker = ContextMaker(trt, gsims_by_trt[trt], param)
        gmv[:, :, t] = cmaker.max_intensity(sitecol1, F64(mags), dist_bins)
    return dict(zip(mags, gmv))


def read_cmakers(dstore, full_lt=None):
    """
    :param dstore: a DataStore-like object
    :param full_lt: a FullLogicTree instance, if given
    :returns: a list of ContextMaker instance, one per source group
    """
    from openquake.hazardlib.site_amplification import AmplFunction
    cmakers = []
    oq = dstore['oqparam']
    full_lt = full_lt or dstore['full_lt']
    trt_smrs = dstore['trt_smrs'][:]
    toms = decode(dstore['toms'][:])
    rlzs_by_gsim_list = full_lt.get_rlzs_by_gsim_list(trt_smrs)
    trts = list(full_lt.gsim_lt.values)
    num_eff_rlzs = len(full_lt.sm_rlzs)
    start = 0
    for grp_id, rlzs_by_gsim in enumerate(rlzs_by_gsim_list):
        trti = trt_smrs[grp_id][0] // num_eff_rlzs
        trt = trts[trti]
        if ('amplification' in oq.inputs and
                oq.amplification_method == 'kernel'):
            df = AmplFunction.read_df(oq.inputs['amplification'])
            oq.af = AmplFunction.from_dframe(df)
        else:
            oq.af = None
        oq.mags_by_trt = {k: decode(v[:])
                          for k, v in dstore['source_mags'].items()}
        cmaker = ContextMaker(trt, rlzs_by_gsim, oq)
        cmaker.tom = valid.occurrence_model(toms[grp_id])
        cmaker.trti = trti
        cmaker.start = start
        cmaker.grp_id = grp_id
        start += len(rlzs_by_gsim)
        cmakers.append(cmaker)
    return cmakers


# used in event_based
def read_cmaker(dstore, trt_smr):
    """
    :param dstore: a DataStore-like object
    :returns: a ContextMaker instance
    """
    oq = dstore['oqparam']
    full_lt = dstore['full_lt']
    trts = list(full_lt.gsim_lt.values)
    trt = trts[trt_smr // len(full_lt.sm_rlzs)]
    rlzs_by_gsim = full_lt._rlzs_by_gsim(trt_smr)
    return ContextMaker(trt, rlzs_by_gsim, oq)
