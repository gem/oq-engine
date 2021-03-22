# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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

import os
import abc
import copy
import time
import logging
import warnings
import itertools
import functools
import collections
import numpy
import pandas
from scipy.interpolate import interp1d

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import (
    AccumDict, DictArray, groupby, block_splitter)
from openquake.baselib.performance import Monitor
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.filters import MagDepDistance
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.surface import PlanarSurface

KNOWN_DISTANCES = frozenset(
    'rrup rx ry0 rjb rhypo repi rcdpp azimuth azimuth_cp rvolc closest_point'
    .split())


class Timer(object):
    """
    Timer used to save the time needed to process each source and to
    postprocess it with ``Timer('timer.csv').read_df()``. To use it, run
    the calculation on a single machine with

    OQ_TIMER=timer.csv oq run job.ini
    """
    fields = ['source_id', 'code', 'effrups', 'nsites', 'weight',
              'numctxs', 'numsites', 'dt', 'task_no']

    def __init__(self, fname):
        self.fname = fname

    def save(self, src, numctxs, numsites, dt, task_no):
        # save the source info
        if self.fname:
            row = [src.source_id, src.code.decode('ascii'),
                   src.num_ruptures, src.nsites, src.weight,
                   numctxs, numsites, dt, task_no]
            open(self.fname, 'a').write(','.join(map(str, row)) + '\n')

    def read_df(self):
        # method used to postprocess the information
        df = pandas.read_csv(self.fname, names=self.fields, index_col=0)
        df['speed'] = df['weight'] / df['dt']
        return df.sort_values('dt')


# object used to measure the time needed to process each source
timer = Timer(os.environ.get('OQ_TIMER'))


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
        dist = numpy.vstack([t.lons, t.lats, t.depths]).T  # shape (N, 3)
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


# used only in contexts_test.py
def _make_pmap(ctxs, cmaker):
    RuptureContext.temporal_occurrence_model = PoissonTOM(
        cmaker.investigation_time)
    # easy case of independent ruptures, useful for debugging
    pmap = ProbabilityMap(cmaker.loglevels.size, len(cmaker.gsims))
    for ctx, poes in cmaker.gen_ctx_poes(ctxs):
        pnes = ctx.get_probability_no_exceedance(poes)  # (N, L, G)
        for sid, pne in zip(ctx.sids, pnes):
            pmap.setdefault(sid, 1.).array *= pne
    return ~pmap


def read_ctxs(dstore, slc=slice(None), req_site_params=None):
    """
     :returns: a list of contexts
    """
    sitecol = dstore['sitecol'].complete
    site_params = {par: sitecol[par]
                   for par in req_site_params or sitecol.array.dtype.names}
    params = {n: dstore['rup/' + n][slc] for n in dstore['rup']}
    ctxs = []
    for u in range(len(params['mag'])):
        ctx = RuptureContext()
        for par, arr in params.items():
            if par.endswith('_'):
                par = par[:-1]
            setattr(ctx, par, arr[u])
        for par, arr in site_params.items():
            setattr(ctx, par, arr[ctx.sids])
        ctx.idx = {sid: idx for idx, sid in enumerate(ctx.sids)}
        ctxs.append(ctx)
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
        param = param or {}  # empty in the gmpe-smtk
        self.af = param.get('af', None)
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.collapse_level = param.get('collapse_level', False)
        self.trt = trt
        self.gsims = gsims
        self.single_site_opt = numpy.array(
            [hasattr(gsim, 'get_mean_std1') for gsim in gsims])
        self.maximum_distance = (
            param.get('maximum_distance') or MagDepDistance({}))
        self.investigation_time = param.get('investigation_time')
        self.trunclevel = param.get('truncation_level')
        self.num_epsilon_bins = param.get('num_epsilon_bins', 1)
        self.effect = param.get('effect')
        self.task_no = getattr(monitor, 'task_no', 0)
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
            setattr(self, 'REQUIRES_' + req, reqset)
        # self.pointsource_distance is a dict mag -> dist, possibly empty
        psd = param.get('pointsource_distance')
        if hasattr(psd, 'ddic'):
            self.pointsource_distance = psd.ddic.get(trt, {})
        else:
            self.pointsource_distance = {}
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
        self.loglevels = DictArray(self.imtls) if self.imtls else {}
        self.shift_hypo = param.get('shift_hypo')
        with warnings.catch_warnings():
            # avoid RuntimeWarning: divide by zero encountered in log
            warnings.simplefilter("ignore")
            for imt, imls in self.imtls.items():
                if imt != 'MMI':
                    self.loglevels[imt] = numpy.log(imls)

        # instantiate monitors
        self.gmf_mon = monitor('computing mean_std', measuremem=False)
        self.poe_mon = monitor('get_poes', measuremem=False)

    def multi(self, ctxs):
        """
        :params ctxs: a list of contexts, all referring to a single point
        :returns: a multiple RuptureContext
        """
        ctx = RuptureContext()
        for par in self.REQUIRES_SITES_PARAMETERS:
            setattr(ctx, par, getattr(ctxs[0], par))
        for par in self.REQUIRES_RUPTURE_PARAMETERS:
            vals = [getattr(ctx, par) for ctx in ctxs]
            setattr(ctx, par, numpy.array(vals))
        for par in self.REQUIRES_DISTANCES:
            dists = [getattr(ctx, par)[0] for ctx in ctxs]
            setattr(ctx, par, numpy.array(dists))
        ctx.ctxs = ctxs
        return ctx

    def gen_ctx_poes(self, ctxs):
        """
        :param ctxs: a list of C context objects
        :yields: C pairs (ctx, poes of shape (N, L, G))
        """
        nsites = numpy.array([len(ctx.sids) for ctx in ctxs])
        C = len(ctxs)
        N = nsites.sum()
        poes = numpy.zeros((N, self.loglevels.size, len(self.gsims)))
        if self.single_site_opt.any():
            ctx = self.multi(ctxs)
        for g, gsim in enumerate(self.gsims):
            with self.gmf_mon:
                # builds mean_std of shape (2, N, M)
                if self.single_site_opt[g] and C > 1 and (nsites == 1).all():
                    mean_std = gsim.get_mean_std1(ctx, self.imts)
                else:
                    mean_std = gsim.get_mean_std(ctxs, self.imts)
            with self.poe_mon:
                # builds poes of shape (N, L, G)
                poes[:, :, g] = gsim.get_poes(
                    mean_std, self.loglevels, self.trunclevel, self.af, ctxs)
        s = 0
        for ctx, n in zip(ctxs, nsites):
            yield ctx, poes[s:s+n]
            s += n

    def get_ctx_params(self):
        """
        :returns: the interesting attributes of the context
        """
        params = {'occurrence_rate', 'sids_', 'src_id',
                  'probs_occur_', 'clon_', 'clat_', 'rrup_'}
        params.update(self.REQUIRES_RUPTURE_PARAMETERS)
        for dparam in self.REQUIRES_DISTANCES:
            params.add(dparam + '_')
        return params

    def from_srcs(self, srcs, site1):  # used in disagg.disaggregation
        """
        :returns: a list RuptureContexts
        """
        allctxs = []
        for i, src in enumerate(srcs):
            src.id = i
            ctxs = []
            for rup in src.iter_ruptures(shift_hypo=self.shift_hypo):
                ctxs.append(self.make_rctx(rup))
            allctxs.extend(self.gen_ctxs(ctxs, site1, src.id))
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
        distances = get_distances(rup, sites, 'rrup')
        mdist = self.maximum_distance(self.trt, rup.mag)
        mask = distances <= mdist
        if mask.any():
            sites, distances = sites.filter(mask), distances[mask]
        else:
            raise FarAwayRupture('%d: %d km' % (rup.rup_id, distances.min()))
        return sites, DistancesContext([('rrup', distances)])

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
        for param in self.REQUIRES_DISTANCES - {'rrup'}:
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

    def gen_ctxs(self, ruptures, sites, src_id, mon=Monitor()):
        """
        :param ruptures:
            a list of ruptures generated by the same source
        :param sites:
            a (filtered) SiteCollection
        :param src_id:
            the ID of the source (for debugging purposes)
        :param mon:
            a Monitor object
        :yields:
            fat RuptureContexts
        """
        fewsites = len(sites.complete) <= self.max_sites_disagg
        for rup in ruptures:
            with mon:
                try:
                    ctx, r_sites, dctx = self.make_contexts(
                        getattr(rup, 'sites', sites), rup)
                except FarAwayRupture:
                    continue
                for par in self.REQUIRES_SITES_PARAMETERS:
                    setattr(ctx, par, r_sites[par])
                ctx.sids = r_sites.sids
                ctx.src_id = src_id
                for par in self.REQUIRES_DISTANCES | {'rrup'}:
                    setattr(ctx, par, getattr(dctx, par))
                if fewsites:
                    closest = rup.surface.get_closest_points(sites.complete)
                    ctx.clon = closest.lons[ctx.sids]
                    ctx.clat = closest.lats[ctx.sids]
            yield ctx

    # this is used with pointsource_distance approximation for close distances,
    # when there are many ruptures affecting few sites
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
                    mean = gsim.get_mean_std([ctx], self.imts)[0, 0]
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
        self.pne_mon = cmaker.mon('composing pnes', measuremem=False)
        # NB: if maxsites is too big or too small the performance of
        # get_poes can easily become 2-3 times worse!
        self.maxsites = 512000 / len(self.gsims) / self.imtls.size

    def count_bytes(self, ctxs):
        # # usuful for debugging memory issues
        rparams = len(self.cmaker.REQUIRES_RUPTURE_PARAMETERS)
        sparams = len(self.cmaker.REQUIRES_SITES_PARAMETERS) + 1
        dparams = len(self.cmaker.REQUIRES_DISTANCES)
        nbytes = 0
        for ctx in ctxs:
            nsites = len(ctx.sids)
            nbytes += 8 * rparams
            nbytes += 8 * sparams * nsites
            nbytes += 8 * dparams * nsites
        return nbytes

    def _update_pmap(self, ctxs, pmap=None):
        # compute PoEs and update pmap
        if pmap is None:  # for src_indep
            pmap = self.pmap
        rup_indep = self.rup_indep
        # splitting in blocks makes sure that the maximum poes array
        # generated has size N x L x G x 8 = 4 MB
        for block in block_splitter(
                ctxs, self.maxsites, lambda ctx: len(ctx.sids)):
            for ctx, poes in self.cmaker.gen_ctx_poes(block):
                with self.pne_mon:
                    # pnes and poes of shape (N, L, G)
                    pnes = ctx.get_probability_no_exceedance(poes)
                    for sid, pne in zip(ctx.sids, pnes):
                        probs = pmap.setdefault(sid, rup_indep).array
                        if rup_indep:
                            probs *= pne
                        else:  # rup_mutex
                            probs += (1. - pne) * ctx.weight

    def _ruptures(self, src, filtermag=None):
        return src.iter_ruptures(
            shift_hypo=self.shift_hypo, mag=filtermag)

    def _gen_ctxs(self, rups, sites, srcid):
        # yield context objects to save memory
        ctxs = self.cmaker.gen_ctxs(rups, sites, srcid, self.ctx_mon)
        if self.collapse_level > 1:
            ctxs = self.cmaker.collapse_the_ctxs(list(ctxs))
        for ctx in ctxs:
            self.numsites += len(ctx.sids)
            self.numctxs += 1
            if self.fewsites:  # keep the contexts in memory
                self.rupdata.append(ctx)
            yield ctx

    def _make_src_indep(self):
        # sources with the same ID
        for src, sites in self.srcfilter.split(self.group):
            if self.fewsites:
                sites = sites.complete
            t0 = time.time()
            self.numctxs = 0
            self.numsites = 0
            rups = self._gen_rups(src, sites)
            self._update_pmap(self._gen_ctxs(rups, sites, src.id))
            dt = time.time() - t0
            self.calc_times[src.id] += numpy.array(
                [self.numctxs, self.numsites, dt])
            timer.save(src, self.numctxs, self.numsites, dt,
                       self.cmaker.task_no)
        return ~self.pmap if self.rup_indep else self.pmap

    def _make_src_mutex(self):
        for src, indices in self.srcfilter.filter(self.group):
            t0 = time.time()
            sites = self.srcfilter.sitecol.filtered(indices)
            self.numctxs = 0
            self.numsites = 0
            rups = self._ruptures(src)
            L, G = self.cmaker.imtls.size, len(self.cmaker.gsims)
            pmap = ProbabilityMap(L, G)
            self._update_pmap(self._gen_ctxs(rups, sites, src.id), pmap)
            p = pmap
            if self.rup_indep:
                p = ~p
            p *= src.mutex_weight
            self.pmap += p
            dt = time.time() - t0
            self.calc_times[src.id] += numpy.array(
                [self.numctxs, self.numsites, dt])
            timer.save(src, self.numctxs, self.numsites, dt,
                       self.cmaker.task_no)
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
        L, G = imtls.size, len(self.gsims)
        self.pmap = ProbabilityMap(L, G)
        # AccumDict of arrays with 3 elements nrups, nsites, calc_time
        self.calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
        if self.src_mutex:
            pmap = self._make_src_mutex()
        else:
            pmap = self._make_src_indep()
        rupdata = self.dictarray(self.rupdata)
        return pmap, rupdata, self.calc_times

    def _gen_rups(self, src, sites):
        # yield ruptures, each one with a .sites attribute
        def rups(rupiter, sites):
            for rup in rupiter:
                rup.sites = sites
                yield rup
        bigps = getattr(src, 'location', None) and src.count_nphc() > 1
        if bigps and self.pointsource_distance == 0:
            # finite size effects are averaged always
            yield from rups(src.avg_ruptures(), sites)
        elif bigps and self.pointsource_distance:
            # finite site effects are averaged for sites over the
            # pointsource_distance from the rupture (if any)
            cdist = sites.get_cdist(src.location)
            for ar in src.avg_ruptures():
                pdist = self.pointsource_distance['%.2f' % ar.mag]
                close = sites.filter(cdist <= pdist)
                far = sites.filter(cdist > pdist)
                if self.fewsites:
                    if close is None:  # all is far, common for small mag
                        yield from rups([ar], sites)
                    else:  # something is close
                        yield from rups(self._ruptures(src, ar.mag), sites)
                else:  # many sites
                    if close is None:  # all is far
                        yield from rups([ar], far)
                    elif far is None:  # all is close
                        yield from rups(self._ruptures(src, ar.mag), close)
                    else:  # some sites are far, some are close
                        yield from rups([ar], far)
                        yield from rups(self._ruptures(src, ar.mag), close)
        else:  # just add the ruptures
            yield from rups(self._ruptures(src), sites)


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


def get_dists(ctx):
    """
    Extract the distance parameters from a context.

    :returns: a dictionary dist_name -> distances
    """
    return {par: dist for par, dist in vars(ctx).items()
            if par in KNOWN_DISTANCES}


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

    def size(self):
        """
        If the context is a multi rupture context, i.e. it contains an array
        of magnitudes and it refers to a single site, returns the size of
        the array, otherwise returns 1.
        """
        if isinstance(self.mag, numpy.ndarray) and len(self.vs30) == 1:
            return len(self.mag)
        return 1

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
