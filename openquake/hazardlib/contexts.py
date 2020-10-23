# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2020 GEM Foundation
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

import abc
import copy
import time
import logging
import warnings
import operator
import itertools
import functools
import collections
import numpy
import h5py
from scipy.interpolate import interp1d

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import (
    AccumDict, DictArray, groupby, groupby_bin)
from openquake.baselib.performance import Monitor
from openquake.hazardlib import const, imt as imt_module
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim import base
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.filters import MagDepDistance
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.surface import PlanarSurface

bymag = operator.attrgetter('mag')
bydist = operator.attrgetter('dist')
I16 = numpy.int16
tmp = 'rrup rx ry0 rjb rhypo repi rcdpp azimuth azimuth_cp rvolc '
tmp += 'closest_point'
KNOWN_DISTANCES = frozenset(tmp.split())


def get_distances(rupture, sites, param):
    """
    :param rupture: a rupture
    :param sites: a mesh of points or a site collection
    :param param: the kind of distance to compute (default rjb)
    :returns: an array of distances from the given sites
    """
    if not rupture.surface:  # PointRupture
        dist = rupture.hypocenter.distance_to_mesh(sites)
    elif param == 'rrup':
        dist = rupture.surface.get_min_distance(sites)
    elif param == 'rx':
        dist = rupture.surface.get_rx_distance(sites)
    elif param == 'ry0':
        dist = rupture.surface.get_ry0_distance(sites)
    elif param == 'rjb':
        dist = rupture.surface.get_joyner_boore_distance(sites)
    elif param == 'rhypo':
        dist = rupture.hypocenter.distance_to_mesh(sites)
    elif param == 'repi':
        dist = rupture.hypocenter.distance_to_mesh(sites, with_depths=False)
    elif param == 'rcdpp':
        dist = rupture.get_cdppvalue(sites)
    elif param == 'azimuth':
        dist = rupture.surface.get_azimuth(sites)
    elif param == 'azimuth_cp':
        dist = rupture.surface.get_azimuth_of_closest_point(sites)
    elif param == 'closest_point':
        t = rupture.surface.get_closest_points(sites)
        dist = numpy.array([(lo, la, de) for lo, la, de in zip(t.lons,
                                                               t.lats,
                                                               t.depths)])
    elif param == "rvolc":
        # Volcanic distance not yet supported, defaulting to zero
        dist = numpy.zeros_like(sites.lons)
    else:
        raise ValueError('Unknown distance measure %r' % param)
    dist.flags.writeable = False
    return dist


class FarAwayRupture(Exception):
    """Raised if the rupture is outside the maximum distance for all sites"""


def get_num_distances(gsims):
    """
    :returns: the number of distances required for the given GSIMs
    """
    dists = set()
    for gsim in gsims:
        dists.update(gsim.REQUIRES_DISTANCES)
    return len(dists)


def make_pmap(ctxs, gsims, imtls, trunclevel, investigation_time):
    RuptureContext.temporal_occurrence_model = PoissonTOM(investigation_time)
    # easy case of independent ruptures, useful for debugging
    imts = [from_string(im) for im in imtls]
    loglevels = DictArray(imtls)
    for imt, imls in imtls.items():
        if imt != 'MMI':
            loglevels[imt] = numpy.log(imls)
    pmap = ProbabilityMap(len(loglevels.array), len(gsims))
    for ctx in ctxs:
        mean_std = ctx.get_mean_std(imts, gsims)  # shape (2, N, M, G)
        poes = base.get_poes(mean_std, loglevels, trunclevel, gsims,
                             None, ctx.mag, None, ctx.rrup)  # (N, L, G)
        pnes = ctx.get_probability_no_exceedance(poes)
        for sid, pne in zip(ctx.sids, pnes):
            pmap.setdefault(sid, 1.).array *= pne
    return ~pmap


def read_ctxs(dstore, rctx_or_magstr, gidx=0, req_site_params=None):
    """
    Use it as `read_ctxs(dstore, 'mag_5.50')`.
    :returns: a pair (contexts, [contexts close to site for each site])
    """
    sitecol = dstore['sitecol']
    site_params = {par: sitecol[par]
                   for par in req_site_params or sitecol.array.dtype.names}
    if isinstance(rctx_or_magstr, str):
        rctx = dstore[rctx_or_magstr]['rctx'][:]
        rctx = rctx[rctx['gidx'] == gidx]
    else:
        # in disaggregation
        rctx = rctx_or_magstr
    magstr = 'mag_%.2f' % rctx[0]['mag']
    if h5py.version.version_tuple >= (2, 10, 0):
        # this version is spectacularly better in cluster1; for
        # Colombia with 1.2M ruptures I measured a speedup of 8.5x
        grp = {n: d[rctx['idx']] for n, d in dstore[magstr].items()
               if n.endswith('_')}
    else:
        # for old h5py read the whole array and then filter on the indices
        grp = {n: d[:][rctx['idx']] for n, d in dstore[magstr].items()
               if n.endswith('_')}
    ctxs = []
    for u, rec in enumerate(rctx):
        ctx = RuptureContext()
        for par in rctx.dtype.names:
            setattr(ctx, par, rec[par])
        for par, arr in grp.items():
            setattr(ctx, par[:-1], arr[u])
        for par, arr in site_params.items():
            setattr(ctx, par, arr[ctx.sids])
        ctx.idx = {sid: idx for idx, sid in enumerate(ctx.sids)}
        ctxs.append(ctx)
    # sorting for debugging convenience
    ctxs.sort(key=lambda ctx: ctx.occurrence_rate)
    close_ctxs = [[] for sid in sitecol.sids]
    for ctx in ctxs:
        for sid in ctx.idx:
            close_ctxs[sid].append(ctx)
    return ctxs, close_ctxs


class ContextMaker(object):
    """
    A class to manage the creation of contexts for distances, sites, rupture.
    """
    REQUIRES = ['DISTANCES', 'SITES_PARAMETERS', 'RUPTURE_PARAMETERS']

    def __init__(self, trt, gsims, param=None, monitor=Monitor()):
        param = param or {}
        self.af = param.get('af', None)
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.collapse_level = param.get('collapse_level', False)
        self.point_rupture_bins = param.get('point_rupture_bins', 20)
        self.trt = trt
        self.gsims = gsims
        self.maximum_distance = (
            param.get('maximum_distance') or MagDepDistance({}))
        self.trunclevel = param.get('truncation_level')
        self.effect = param.get('effect')
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
            setattr(self, 'REQUIRES_' + req, reqset)
        # self.pointsource_distance is a dict mag -> dist, possibly empty
        if param.get('pointsource_distance'):
            self.pointsource_distance = param['pointsource_distance'][trt]
        else:
            self.pointsource_distance = {}
        self.filter_distance = 'rrup'
        if 'imtls' in param:
            self.imtls = param['imtls']
        elif 'hazard_imtls' in param:
            self.imtls = DictArray(param['hazard_imtls'])
        else:
            self.imtls = {}
        self.imts = [imt_module.from_string(imt) for imt in self.imtls]
        self.reqv = param.get('reqv')
        if self.reqv is not None:
            self.REQUIRES_DISTANCES.add('repi')
        self.mon = monitor
        self.ctx_mon = monitor('make_contexts', measuremem=False)
        self.loglevels = DictArray(self.imtls)
        self.shift_hypo = param.get('shift_hypo')
        with warnings.catch_warnings():
            # avoid RuntimeWarning: divide by zero encountered in log
            warnings.simplefilter("ignore")
            for imt, imls in self.imtls.items():
                if imt != 'MMI':
                    self.loglevels[imt] = numpy.log(imls)

    def get_ctx_params(self):
        """
        :returns: the interesting attributes of the context
        """
        params = {'gidx', 'occurrence_rate', 'sids_',
                  'probs_occur', 'clon_', 'clat_', 'rrup_'}
        params.update(self.REQUIRES_RUPTURE_PARAMETERS)
        for dparam in self.REQUIRES_DISTANCES:
            params.add(dparam + '_')
        return params

    def from_srcs(self, srcs, site1):  # used in disagg.disaggregation
        """
        :returns: a list RuptureContexts
        """
        allctxs = []
        for src in srcs:
            ctxs = []
            for rup in src.iter_ruptures(shift_hypo=self.shift_hypo):
                ctxs.append(self.make_rctx(rup))
            allctxs.extend(self.make_ctxs(ctxs, site1, 0, [0], True))
        return allctxs

    def filter(self, sites, rup):
        """
        Filter the site collection with respect to the rupture.

        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.
        :param rup:
            Instance of
            :class:`openquake.hazardlib.source.rupture.BaseRupture`
        :returns:
            (filtered sites, distance context)
        """
        distances = get_distances(rup, sites, self.filter_distance)
        mdist = self.maximum_distance(self.trt, rup.mag)
        mask = distances <= mdist
        if mask.any():
            sites, distances = sites.filter(mask), distances[mask]
        else:
            raise FarAwayRupture('%d: %d km' % (rup.rup_id, distances.min()))
        return sites, DistancesContext([(self.filter_distance, distances)])

    def get_dctx(self, sites, rup):
        """
        :param sites: :class:`openquake.hazardlib.site.SiteCollection`
        :param rup: :class:`openquake.hazardlib.source.rupture.BaseRupture`
        :returns: :class:`DistancesContext`
        """
        distances = get_distances(rup, sites, self.filter_distance)
        mdist = self.maximum_distance(self.trt, rup.mag)
        if (distances > mdist).all():
            raise FarAwayRupture('%d: %d km' % (rup.rup_id, distances.min()))
        return DistancesContext([(self.filter_distance, distances)])

    def make_rctx(self, rupture):
        """
        Add .REQUIRES_RUPTURE_PARAMETERS to the rupture
        """
        ctx = RuptureContext()
        vars(ctx).update(vars(rupture))
        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            if param == 'mag':
                value = rupture.mag
            elif param == 'strike':
                value = rupture.surface.get_strike()
            elif param == 'dip':
                value = rupture.surface.get_dip()
            elif param == 'rake':
                value = rupture.rake
            elif param == 'ztor':
                value = rupture.surface.get_top_edge_depth()
            elif param == 'hypo_lon':
                value = rupture.hypocenter.longitude
            elif param == 'hypo_lat':
                value = rupture.hypocenter.latitude
            elif param == 'hypo_depth':
                value = rupture.hypocenter.depth
            elif param == 'width':
                value = rupture.surface.get_width()
            else:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (type(self).__name__, param))
            setattr(ctx, param, value)
        return ctx

    def make_contexts(self, sites, rupture):
        """
        Filter the site collection with respect to the rupture and
        create context objects.

        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.

        :param rupture:
            Instance of
            :class:`openquake.hazardlib.source.rupture.BaseRupture`

        :returns:
            Tuple of three items: rupture, sites and distances context.

        :raises ValueError:
            If any of declared required parameters (site, rupture and
            distance parameters) is unknown.
        """
        sites, dctx = self.filter(sites, rupture)
        for param in self.REQUIRES_DISTANCES - set([self.filter_distance]):
            distances = get_distances(rupture, sites, param)
            setattr(dctx, param, distances)
        reqv_obj = (self.reqv.get(self.trt) if self.reqv else None)
        if reqv_obj and isinstance(rupture.surface, PlanarSurface):
            reqv = reqv_obj.get(dctx.repi, rupture.mag)
            if 'rjb' in self.REQUIRES_DISTANCES:
                dctx.rjb = reqv
            if 'rrup' in self.REQUIRES_DISTANCES:
                dctx.rrup = numpy.sqrt(reqv**2 + rupture.hypocenter.depth**2)
        return self.make_rctx(rupture), sites, dctx

    def make_ctxs(self, ruptures, sites, gidx, grp_ids, fewsites):
        """
        :returns:
            a list of fat RuptureContexts
        """
        ctxs = []
        for rup in ruptures:
            try:
                ctx, r_sites, dctx = self.make_contexts(
                    getattr(rup, 'sites', sites), rup)
            except FarAwayRupture:
                continue
            for par in self.REQUIRES_SITES_PARAMETERS:
                setattr(ctx, par, r_sites[par])
            ctx.sids = r_sites.sids
            for par in self.REQUIRES_DISTANCES | {'rrup'}:
                setattr(ctx, par, getattr(dctx, par))
            ctx.grp_ids = grp_ids
            ctx.gidx = gidx
            if fewsites:
                closest = rup.surface.get_closest_points(sites.complete)
                ctx.clon = closest.lons[ctx.sids]
                ctx.clat = closest.lats[ctx.sids]
            ctxs.append(ctx)
        return ctxs

    def collapse_the_ctxs(self, ctxs):
        """
        Collapse contexts with similar parameters and distances.

        :param ctxs: a list of pairs (rup, dctx)
        :returns: collapsed contexts
        """
        if len(ctxs) == 1:
            return ctxs

        if self.collapse_level >= 3:  # hack, ignore everything except mag
            rrp = ['mag']
            rnd = 0  # round distances to 1 km
        else:
            rrp = self.REQUIRES_RUPTURE_PARAMETERS
            rnd = 1  # round distances to 100 m

        def params(ctx):
            lst = []
            for par in rrp:
                lst.append(getattr(ctx, par))
            for dst in self.REQUIRES_DISTANCES:
                lst.extend(numpy.round(getattr(ctx, dst), rnd))
            return tuple(lst)

        out = []
        for values in groupby(ctxs, params).values():
            out.extend(_collapse(values))
        return out

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
            means = []
            for gsim in self.gsims:
                try:
                    mean = ctx.get_mean_std(  # shape (2, N, M, G) -> M
                        self.imts, [gsim])[0, 0, :, 0]
                except ValueError:  # magnitude outside of supported range
                    continue
                means.append(mean.max())
            if means:
                gmv[m, d] = numpy.exp(max(means))
        return gmv


# see contexts_tests.py for examples of collapse
def combine_pmf(o1, o2):
    """
    Combine probabilities of occurrence; used to collapse nonparametric
    ruptures.

    :param o1: probability distribution of length n1
    :param o2: probability distribution of length n2
    :returns: probability distribution of length n1 + n2

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


def _collapse(ctxs):
    # collapse a list of contexts into a single context
    if len(ctxs) < 2:  # nothing to collapse
        return ctxs
    prups, nrups, out = [], [], []
    for ctx in ctxs:
        if numpy.isnan(ctx.occurrence_rate):  # nonparametric
            nrups.append(ctx)
        else:  # parametrix
            prups.append(ctx)
    if len(prups) > 1:
        ctx = copy.copy(prups[0])
        ctx.occurrence_rate = sum(r.occurrence_rate for r in prups)
        out.append(ctx)
    else:
        out.extend(prups)
    if len(nrups) > 1:
        ctx = copy.copy(nrups[0])
        ctx.probs_occur = functools.reduce(
            combine_pmf, (n.probs_occur for n in nrups))
        out.append(ctx)
    else:
        out.extend(nrups)
    return out


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
        self.group = group
        self.src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
        self.rup_indep = getattr(group, 'rup_interdep', None) != 'mutex'
        self.fewsites = self.N <= cmaker.max_sites_disagg
        self.poe_mon = cmaker.mon('get_poes', measuremem=False)
        self.pne_mon = cmaker.mon('composing pnes', measuremem=False)
        self.gmf_mon = cmaker.mon('computing mean_std', measuremem=False)

    def _update_pmap(self, ctxs, pmap=None):
        # compute PoEs and update pmap
        if pmap is None:  # for src_indep
            pmap = self.pmap
        rup_indep = self.rup_indep
        for ctx in ctxs:
            # this must be fast since it is inside an inner loop
            with self.gmf_mon:
                # shape (2, N, M, G)
                mean_std = ctx.get_mean_std(self.imts, self.gsims)
            with self.poe_mon:
                ll = self.loglevels
                af = self.cmaker.af
                if af:
                    [sitecode] = ctx.sites['ampcode']  # single-site only
                else:
                    sitecode = None
                poes = base.get_poes(mean_std, ll, self.trunclevel, self.gsims,
                                     af, ctx.mag, sitecode, ctx.rrup)
                for g, gsim in enumerate(self.gsims):
                    for m, imt in enumerate(ll):
                        if hasattr(gsim, 'weight') and gsim.weight[imt] == 0:
                            # set by the engine when parsing the gsim logictree
                            # when 0 ignore the gsim: see _build_trts_branches
                            poes[:, ll(imt), g] = 0

            with self.pne_mon:
                # pnes and poes of shape (N, L, G)
                pnes = ctx.get_probability_no_exceedance(poes)
                for sid, pne in zip(ctx.sids, pnes):
                    for grp_id in ctx.grp_ids:
                        probs = pmap[grp_id].setdefault(sid, rup_indep).array
                        if rup_indep:
                            probs *= pne
                        else:  # rup_mutex
                            probs += (1. - pne) * ctx.weight

    def _ruptures(self, src, filtermag=None):
        return list(src.iter_ruptures(
            shift_hypo=self.shift_hypo, mag=filtermag))

    def _make_ctxs(self, rups, sites, gidx, grp_ids):
        with self.ctx_mon:
            if self.rup_indep and self.pointsource_distance != {}:
                rups = self.collapse_point_ruptures(rups, sites)
            ctxs = self.cmaker.make_ctxs(
                rups, sites, gidx, grp_ids, self.fewsites)
            if self.collapse_level > 1:
                ctxs = self.cmaker.collapse_the_ctxs(ctxs)
            if self.fewsites:  # keep the contexts in memory
                self.rupdata.extend(ctxs)
            self.numrups += len(ctxs)
            self.numsites += sum(len(ctx.sids) for ctx in ctxs)
        return ctxs

    def _make_src_indep(self):
        # srcs with the same source_id and grp_ids
        for srcs, sites in self.srcfilter.get_sources_sites(self.group):
            t0 = time.time()
            src_id = srcs[0].source_id
            grp_ids = numpy.array(srcs[0].grp_ids)
            gidx = getattr(srcs[0], 'gidx', 0)
            self.numrups = 0
            self.numsites = 0
            if self.N == 1:  # plenty of memory, collapse all sources together
                rups = self._get_rups(srcs, sites)
                ctxs = self._make_ctxs(rups, sites, gidx, grp_ids)
                self._update_pmap(ctxs)
            else:  # collapse one source at the time
                for src in srcs:
                    rups = self._get_rups([src], sites)
                    ctxs = self._make_ctxs(rups, sites, gidx, grp_ids)
                    self._update_pmap(ctxs)
            self.calc_times[src_id] += numpy.array(
                [self.numrups, self.numsites, time.time() - t0])
        return AccumDict((grp_id, ~p if self.rup_indep else p)
                         for grp_id, p in self.pmap.items())

    def _make_src_mutex(self):
        for src, indices in self.srcfilter.filter(self.group):
            sites = self.srcfilter.sitecol.filtered(indices)
            t0 = time.time()
            self.totrups += src.num_ruptures
            self.numrups = 0
            self.numsites = 0
            rups = self._ruptures(src)
            gidx = getattr(src, 'gidx', 0)
            L, G = len(self.cmaker.imtls.array), len(self.cmaker.gsims)
            pmap = {grp_id: ProbabilityMap(L, G) for grp_id in src.grp_ids}
            ctxs = self._make_ctxs(rups, sites, gidx, numpy.array(src.grp_ids))
            self._update_pmap(ctxs, pmap)
            for grp_id in src.grp_ids:
                p = pmap[grp_id]
                if self.rup_indep:
                    p = ~p
                p *= src.mutex_weight
                self.pmap[grp_id] += p
            self.calc_times[src.source_id] += numpy.array(
                [self.numrups, self.numsites, time.time() - t0])
        return self.pmap

    def dictarray(self, ctxs):
        dic = {}  # par -> array
        z = numpy.zeros(0)
        for par in self.cmaker.get_ctx_params():
            pa = par[:-1] if par.endswith('_') else par
            dic[par] = numpy.array([getattr(ctx, pa, z) for ctx in ctxs])
        return dic

    def make(self):
        self.rupdata = []
        imtls = self.cmaker.imtls
        L, G = len(imtls.array), len(self.gsims)
        self.pmap = AccumDict(accum=ProbabilityMap(L, G))  # grp_id -> pmap
        # AccumDict of arrays with 3 elements nrups, nsites, calc_time
        self.calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
        self.totrups = 0
        if self.src_mutex:
            pmap = self._make_src_mutex()
        else:
            pmap = self._make_src_indep()
        rupdata = groupby(self.rupdata, lambda ctx: '%.2f' % ctx.mag)
        for mag, ctxs in rupdata.items():
            rupdata[mag] = self.dictarray(ctxs)
        return (pmap, rupdata, self.calc_times, dict(totrups=self.totrups))

    def collapse_point_ruptures(self, rups, sites):
        """
        Collapse ruptures more distant than the pointsource_distance
        """
        pointlike, output = [], []
        for rup in rups:
            if not rup.surface:
                pointlike.append(rup)
            else:
                output.append(rup)
        for mag, mrups in groupby(pointlike, bymag).items():
            if len(mrups) == 1:  # nothing to do
                output.extend(mrups)
                continue
            mdist = self.maximum_distance(self.trt, mag)
            coll = []
            for rup in mrups:  # called on a single site
                rup.dist = get_distances(rup, sites, 'rrup').min()
                if rup.dist <= mdist:
                    coll.append(rup)
            for rs in groupby_bin(coll, self.point_rupture_bins, bydist):
                # group together ruptures in the same distance bin
                output.extend(_collapse(rs))
        return output

    def _get_rups(self, srcs, sites):
        # returns a list of ruptures, each one with a .sites attribute
        rups = []

        def _add(rupiter, sites):
            for rup in rupiter:
                rup.sites = sites
                rups.append(rup)
        for src in srcs:
            self.totrups += src.num_ruptures
            loc = getattr(src, 'location', None)
            if loc and self.pointsource_distance == 0:
                # all finite size effects are ignored
                _add(src.point_ruptures(), sites)
            elif loc and self.pointsource_distance:
                # finite site effects are ignored only for sites over the
                # pointsource_distance from the rupture (if any)
                for pr in src.point_ruptures():
                    pdist = self.pointsource_distance['%.2f' % pr.mag]
                    close, far = sites.split(pr.hypocenter, pdist)
                    if self.fewsites:
                        if close is None:  # all is far, common for small mag
                            _add([pr], sites)
                        else:  # something is close
                            _add(self._ruptures(src, pr.mag), sites)
                    else:  # many sites
                        if close is None:  # all is far
                            _add([pr], far)
                        elif far is None:  # all is close
                            _add(self._ruptures(src, pr.mag), close)
                        else:  # some sites are far, some are close
                            _add([pr], far)
                            _add(self._ruptures(src, pr.mag), close)
            else:  # just add the ruptures
                _add(self._ruptures(src), sites)
        return rups


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
    _slots_ = (
        'mag', 'strike', 'dip', 'rake', 'ztor', 'hypo_lon', 'hypo_lat',
        'hypo_depth', 'width', 'hypo_loc')
    temporal_occurrence_model = None  # to be set

    @classmethod
    def full(cls, rup, sites, dctx=None):
        """
        :returns: a full context with all the relevant attributes
        """
        self = cls()
        for par, val in vars(rup).items():
            setattr(self, par, val)
        for par in sites.array.dtype.names:
            setattr(self, par, sites[par])
        if dctx:
            for par, val in vars(dctx).items():
                setattr(self, par, val)
        return self

    def __init__(self, param_pairs=()):
        for param, value in param_pairs:
            setattr(self, param, value)

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

    def get_mean_std(self, imts, gsims):
        """
        :returns: an array of shape (2, N, M, G) with means and stddevs
        """
        N = len(self.sids)
        M = len(imts)
        G = len(gsims)
        arr = numpy.zeros((2, N, M, G))
        num_tables = base.CoeffsTable.num_instances
        for g, gsim in enumerate(gsims):
            new = self.roundup(gsim.minimum_distance)
            for m, imt in enumerate(imts):
                mean, [std] = gsim.get_mean_and_stddevs(self, self, new, imt,
                                                        [const.StdDev.TOTAL])
                arr[0, :, m, g] = mean
                arr[1, :, m, g] = std
                if base.CoeffsTable.num_instances > num_tables:
                    raise RuntimeError('Instantiating CoeffsTable inside '
                                       '%s.get_mean_and_stddevs' %
                                       gsim.__class__.__name__)
        return arr

    def get_probability_no_exceedance(self, poes):
        """
        Compute and return the probability that in the time span for which the
        rupture is defined, the rupture itself never generates a ground motion
        value higher than a given level at a given site.

        Such calculation is performed starting from the conditional probability
        that an occurrence of the current rupture is producing a ground motion
        value higher than the level of interest at the site of interest.
        The actual formula used for such calculation depends on the temporal
        occurrence model the rupture is associated with.
        The calculation can be performed for multiple intensity measure levels
        and multiple sites in a vectorized fashion.

        :param poes:
            2D numpy array containing conditional probabilities the the a
            rupture occurrence causes a ground shaking value exceeding a
            ground motion level at a site. First dimension represent sites,
            second dimension intensity measure levels. ``poes`` can be obtained
            calling the :func:`func <openquake.hazardlib.gsim.base.get_poes>`
        """
        if numpy.isnan(self.occurrence_rate):  # nonparametric rupture
            # Uses the formula
            #
            #    ∑ p(k|T) * p(X<x|rup)^k
            #
            # where `p(k|T)` is the probability that the rupture occurs k times
            # in the time span `T`, `p(X<x|rup)` is the probability that a
            # rupture occurrence does not cause a ground motion exceedance, and
            # thesummation `∑` is done over the number of occurrences `k`.
            #
            # `p(k|T)` is given by the attribute probs_occur and
            # `p(X<x|rup)` is computed as ``1 - poes``.
            prob_no_exceed = numpy.float64(
                [v * (1 - poes) ** i for i, v in enumerate(self.probs_occur)]
            ).sum(axis=0)
            return numpy.clip(prob_no_exceed, 0., 1.)  # avoid numeric issues

        # parametric rupture
        tom = self.temporal_occurrence_model
        return tom.get_probability_no_exceedance(self.occurrence_rate, poes)


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
    :param maximum_distance: an MagDepDistance object
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
        gmv[:, :, t] = cmaker.max_intensity(
            sitecol1, [float(mag) for mag in mags], dist_bins)
    return dict(zip(mags, gmv))


# used in calculators/classical.py
def get_effect(mags, sitecol1, gsims_by_trt, oq):
    """
    :params mags:
       a dictionary trt -> magnitudes
    :param sitecol1:
       a SiteCollection with a single site
    :param gsims_by_trt:
       a dictionary trt -> gsims
    :param oq:
       an object with attributes imtls, minimum_intensity,
       maximum_distance and pointsource_distance
    :returns:
       an ArrayWrapper trt -> effect_by_mag_dst and a nested dictionary
       trt -> mag -> dist with the effective pointsource_distance

    Updates oq.maximum_distance.magdist
    """
    assert list(mags) == list(gsims_by_trt), 'Missing TRTs!'
    dist_bins = {trt: oq.maximum_distance.get_dist_bins(trt)
                 for trt in gsims_by_trt}
    aw = hdf5.ArrayWrapper((), {})
    # computing the effect make sense only if all IMTs have the same
    # unity of measure; for simplicity we will consider only PGA and SA
    psd = oq.pointsource_distance
    if psd is not None:
        psd.interp(mags)
        psd = psd.ddic
    if psd:
        logging.info('Computing effect of the ruptures')
        allmags = set()
        for trt in mags:
            allmags.update(mags[trt])
        eff_by_mag = parallel.Starmap.apply(
            get_effect_by_mag, (sorted(allmags), sitecol1, gsims_by_trt,
                                oq.maximum_distance, oq.imtls)
        ).reduce()
        effect = {}
        for t, trt in enumerate(mags):
            arr = numpy.array([eff_by_mag[mag][:, t] for mag in mags[trt]])
            setattr(aw, trt, arr)  # shape (#mags, #dists)
            setattr(aw, trt + '_dist_bins', dist_bins[trt])
            effect[trt] = Effect(dict(zip(mags[trt], arr)), dist_bins[trt])
        minint = oq.minimum_intensity.get('default', 0)
        for trt, eff in effect.items():
            if minint:
                oq.maximum_distance.ddic[trt] = eff.dist_by_mag(minint)
            # build a dict trt -> mag -> dst
            if psd and set(psd[trt].values()) == {-1}:
                maxdist = oq.maximum_distance(trt)
                psd[trt] = eff.dist_by_mag(eff.collapse_value(maxdist))
    return aw


# not used right now
def ruptures_by_mag_dist(sources, srcfilter, gsims, params, monitor):
    """
    :returns: a dictionary trt -> mag string -> counts by distance
    """
    assert len(srcfilter.sitecol) == 1
    trt = sources[0].tectonic_region_type
    dist_bins = srcfilter.integration_distance.get_dist_bins(trt)
    nbins = len(dist_bins)
    mags = set('%.2f' % mag for src in sources for mag in src.get_mags())
    dic = {mag: numpy.zeros(len(dist_bins), int) for mag in sorted(mags)}
    cmaker = ContextMaker(trt, gsims, params, monitor)
    for src, indices in srcfilter.filter(sources):
        sites = srcfilter.sitecol.filtered(indices)
        for rup in src.iter_ruptures(shift_hypo=cmaker.shift_hypo):
            try:
                sctx, dctx = cmaker.make_contexts(sites, rup)
            except FarAwayRupture:
                continue
            di = numpy.searchsorted(dist_bins, dctx.rrup[0])
            if di == nbins:
                di = nbins - 1
            dic['%.2f' % rup.mag][di] += 1
    return {trt: AccumDict(dic)}
