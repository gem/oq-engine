# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2026 GEM Foundation
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

import copy
import time
import collections
import numpy

from openquake.baselib.general import (
    AccumDict, getsizeof)
from openquake.baselib.general import decode
from openquake.hazardlib import valid, InvalidFile
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.filters import (
    SourceFilter, FilteredAway)
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.site_amplification import (
    AmplificationFunction)
from openquake.hazardlib.contexts import (
    ContextMaker, concat, F32, F64, U32, TWO20, TWO24)


class RmapMaker(object):
    """
    A class to compute the PoEs from a given source
    """
    def __init__(self, cmaker, sitecol, group):
        vars(self).update(vars(cmaker))
        self.cmaker = cmaker
        if hasattr(sitecol, 'sitecol'):
            self.srcfilter = sitecol
        else:
            self.srcfilter = SourceFilter(sitecol, cmaker.maximum_distance)
        self.N = len(self.srcfilter.sitecol.complete)
        try:
            self.sources = group.sources
        except AttributeError:  # already a list of sources
            self.sources = group
        self.src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
        if getattr(group, 'rup_interdep', None) != 'mutex':
            self.rup_mutex = {}
        else:
            self.rup_mutex = {}  # src_id, rup_id -> rup_weight
            for src in group:
                for i, (rup, _) in enumerate(src.data):
                    self.rup_mutex[src.id, i] = rup.weight
        self.fewsites = self.N <= cmaker.max_sites_disagg
        self.grp_probability = getattr(group, 'grp_probability', 1.)
        self.cluster = self.cmaker.cluster = getattr(group, 'cluster', 0)
        if self.cluster:
            tom = group.temporal_occurrence_model
        else:
            # NOTE: I think we should raise an error here
            tom = getattr(self.sources[0], 'temporal_occurrence_model',
                          PoissonTOM(self.cmaker.investigation_time))
        self.cmaker.tom = self.tom = tom
        M, G = len(self.cmaker.imtls), len(self.cmaker.gsims)
        self.maxsize = 8 * TWO20 // (M*G)  # crucial for a fast get_mean_stds

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

    def gen_ctxs(self, src):
        if src.code == b'F':
            sites = self.srcfilter.sitecol
        else:
            sites = self.srcfilter.get_close_sites(src)
            if sites is None:
                return
        for ctx in self.cmaker.get_ctxs(src, sites):
            if self.cmaker.deltagetter:
                # Every rup listed in delta_rates is an aftershock, so
                # shift its occurrence_rate and set is_aftershock as True
                # so aftershock terms are applied in GMMs containing them
                with self.cmaker.delta_mon:
                    delta = self.cmaker.deltagetter(src.id)
                    row = delta[ctx.rup_id]
                    d = row['delta']
                    ctx.occurrence_rate += d
                    if 'is_aftershock' in ctx.dtype.names:
                        ctx.is_aftershock = d != 0
                    if 'crjb' in ctx.dtype.names:
                        ctx.crjb = row['crjb']
            if self.fewsites:  # keep rupdata in memory
                if self.src_mutex:
                    # needed for Disaggregator.init
                    ctx.src_id = valid.fragmentno(src)
                self.rupdata.append(ctx)
            yield ctx

    def _make_src_indep(self):
        # sources with the same ID
        cm = self.cmaker
        allctxs = []
        ctxlen = 0
        totlen = 0
        t0 = time.time()
        sids = self.srcfilter.sitecol.sids
        # using memory here, limited by pmap_max_mb
        pnemap = MapArray(
            sids, self.cmaker.imtls.size, len(self.cmaker.gsims),
            not self.cluster).fill(self.cluster)
        for src in self.sources:
            for ctx in self.gen_ctxs(src):
                ctxlen += len(ctx)
                totlen += len(ctx)
                allctxs.append(ctx)
                if ctxlen > self.maxsize:
                    ctxt = concat(allctxs)  # at most a few dozens of MB
                    cm.update(pnemap, ctxt)
                    allctxs.clear()
                    ctxlen = 0
        if allctxs:
            # all sources have the same tom by construction
            cm.update(pnemap, concat(allctxs))
            allctxs.clear()

        dt = (time.time() - t0) / len(self.sources)
        factor = totlen / sum(src.nctxs for src in self.sources)
        for src in self.sources:
            self.update_source_data(src, cm.task_no, dt, src.nctxs * factor)
        return pnemap

    def _make_src_mutex(self):
        # used in Japan (case_27) and in New Madrid (case_80)
        cm = self.cmaker
        G = len(self.cmaker.gsims)
        sids = self.srcfilter.sitecol.sids
        pmap = MapArray(sids, self.cmaker.imtls.size, G).fill(0)
        for src in self.sources:
            t0 = time.time()
            pm = MapArray(
                pmap.sids, cm.imtls.size, len(cm.gsims)
            ).fill(not self.rup_mutex)
            ctxs = list(self.gen_ctxs(src))
            n = sum(len(ctx) for ctx in ctxs)
            if n == 0:
                continue
            for ctx in ctxs:
                cm.update(pm, ctx, self.rup_mutex)
            if self.rup_mutex:
                # in classical/case_80
                pmap.array += (1.- pmap.array) * pm.array
            else:
                # in classical/case_27
                pmap.array += (1. - pm.array) * src.mutex_weight
            self.update_source_data(src, cm.task_no, time.time() - t0, n)
        pmap.array *= self.grp_probability
        return ~pmap

    def update_source_data(self, src, task_no, dt, nctxs):
        src.dt = dt
        self.source_data['src_id'].append(valid.basename(src))
        self.source_data['grp_id'].append(src.grp_id)
        self.source_data['nctxs'].append(nctxs)
        self.source_data['nrupts'].append(src.num_ruptures)
        self.source_data['weight'].append(src.weight)
        self.source_data['ctimes'].append(src.dt)
        self.source_data['taskno'].append(task_no)

    def make(self):
        dic = {}
        self.rupdata = []
        self.source_data = AccumDict(accum=[])
        if not self.src_mutex and not self.rup_mutex:
            pnemap = self._make_src_indep()
        else:
            pnemap = self._make_src_mutex()
        if self.cluster:  # very fast
            MINFLOAT = 1.4E-45  # minimum 32 bit float
            probs = F32(self.tom.get_probability_n_occurrences(
                self.tom.occurrence_rate, numpy.arange(20)))
            # the probs are usually very small, like
            # [9.9999881e-01, 1.2000586e-06, 7.2007114e-13, ,,,]
            # they rapidly go below the minimum 32 bit float, so
            # the length of the loop can be reduced (i.e. from 20 to 7)
            probs = probs[probs > MINFLOAT]
            array = numpy.full(pnemap.shape, probs[0], dtype=F32)
            for nocc, probn in enumerate(probs[1:], 1):
                array += pnemap.array ** nocc * probn
            pnemap.array = array

        dic['rmap'] = pnemap.to_rates()
        dic['rmap'].gid = self.cmaker.gid
        dic['cfactor'] = self.cmaker.cfactor
        if self.oq.keep_rupdata:
            dic['rup_data'] = concat(self.rupdata)
        else:
            dic['rup_data'] = ()
        dic['source_data'] = self.source_data
        dic['task_no'] = self.task_no
        dic['dparam_mb'] = getsizeof(self.cmaker.dparam) / TWO20
        dic['source_mb'] = self.cmaker.source_mb
        if self.disagg_by_src:
            # all the sources in the group must have the same source_id because
            # of the groupby(group, corename) in classical.py
            coreids = set(map(valid.corename, self.sources))
            if len(coreids) > 1:
                raise NameError('Invalid source naming: %s' % coreids)

            # in oq-risk-tests test_phl there are multiple srcids
            # (mps-0!b1;0, mps-0!b1;1, ...); you can simply use the first,
            # since in `store_mean_rates_by_src` we use corename
            dic['basename'] = valid.basename(self.sources[0])
        return dic


def _rates_by_mag(sources):
    # :param sources: a list of sources
    # :returns: a list of dictionaries mag -> annual occurrence rate, one
    #     per source, read from the MFD (cheap, no ruptures enumerated)
    out = []
    for src in sources:
        # NB: nonparametric sources have no MFD, so they are not supported
        # by make_results and the callers must fall back to the slow path
        if not hasattr(src, 'get_annual_occurrence_rates'):
            raise ValueError('%s has no MFD' % type(src).__name__)
        dic = {}
        for mag, rate in src.get_annual_occurrence_rates():
            mag = round(mag, 3)
            dic[mag] = dic.get(mag, 0.) + rate
        out.append(dic)
    return out


def _mag_ratios(base, dic):
    # :param base: dictionary mag -> rate of a base source
    # :param dic: dictionary mag -> rate of another variant of the source
    # :returns: dictionary mag -> ratio of the rates, i.e. the factor
    #     applied to the occurrence rates of the base contexts of that mag;
    #     the magnitudes missing in the variant get ratio 0 (see get),
    #     the ones missing in the base are not supported
    #
    # NB: this assumes that the MFD variants rescale uniformly the
    # ruptures of a magnitude, i.e. the relative weights of the ruptures
    # (hypocenters, nodal planes) do not change, see make_results
    if set(dic) - set(base):
        raise ValueError('new magnitudes in a variant')
    return {mag: dic.get(mag, 0.) / rate for mag, rate in base.items()
            if rate > 0}


def mag_support(sources):
    # :param sources: a list of sources, as in a group
    # :returns: a hashable key with the magnitudes of each source; the
    #     variants with the same key can be computed together by make_results
    #     since they have the same magnitudes, see _mag_ratios
    return tuple(tuple(sorted(dic)) for dic in _rates_by_mag(sources))


def make_results(groups, cmakers, sites):
    """
    Compute the rates of several variants of the same groups, i.e. groups
    with the same sources and the same geometry but different MFDs, with
    the contexts computed only once (called by classical.bysrc_results).

    :param groups: a list of V groups, one per variant, with the same
        sources in the same order
    :param cmakers: a list of V cmakers, one per variant, with the gids
    :param sites: a SiteCollection instance
    :returns: a list of V dictionaries, as returned by RmapMaker.make
    :raises ValueError: if the variants cannot be computed this way
    :raises FilteredAway: if some sources of a variant were filtered away

    The contexts are generated from the base variant, i.e. the one with
    the most magnitudes, and for each other variant the occurrence rates
    of the contexts are rescaled by the ratio of the rates of their magnitude
    (see _mag_ratios). Only independent Poisson sources are supported,
    since the probabilities are then linear in the rates.
    """
    rates = [_rates_by_mag(grp) for grp in groups]
    b = max(range(len(groups)),
            key=lambda v: sum(len(d) for d in rates[v]))
    rmaker = RmapMaker(cmakers[b], sites, groups[b])
    if rmaker.src_mutex or rmaker.rup_mutex or rmaker.cluster:
        raise ValueError('mutually exclusive sources')
    sources = rmaker.sources
    # NB: the variants can have fewer sources than the base, since the
    # sources are filtered by minimum_magnitude after the uncertainties
    # are applied, see classical.cmakers_groups_gkeys
    nsrcs = [len(grp) for grp in groups]
    if any(n != len(sources) for n in nsrcs):
        raise FilteredAway(
            'the variants have %s sources, expected %d: some sources were '
            'filtered away by the uncertainties' % (nsrcs, len(sources)))
    # ratios[v][s] = dictionary mag -> ratio for source s of variant v
    # e.g. logictree/case_18_bis: 9 variants (3 abGR x 3 maxMagGR), the base
    # is variant 2 (3 mags, rate 0.115893 at M 5.5); variant 3 has rate
    # 0.284605 at M 5.5, i.e. ratio 2.4558, and variant 0 (maxMag 7.0)
    # has no magnitude 7.5, i.e. ratio 0 for it
    ratios = [[_mag_ratios(rates[b][s], rates[v][s])
               for s in range(len(sources))]
              for v in range(len(groups))]
    sids = rmaker.srcfilter.sitecol.sids
    cm = rmaker.cmaker
    pnemaps = [MapArray(sids, cm.imtls.size, len(cm.gsims),
                        True).fill(False) for _ in groups]
    rmaker.source_data = AccumDict(accum=[])
    rups = [[] for _ in groups]  # the rup_data of each variant
    # e.g. logictree/case_18_bis: the base has 6 ruptures, variant 1 (maxMag
    # 7.3) has 4 and variant 0 (maxMag 7.0) has 4, see _scale_rups
    t0 = time.time()
    nctxs = _process_sources(rmaker, ratios, pnemaps, rups)
    dt = (time.time() - t0) / len(sources)
    # the source data are recorded only for the first variant, the
    # others get zeros, otherwise the statistics would be repeated
    for s, src in enumerate(sources):
        rmaker.update_source_data(src, rmaker.task_no, dt, nctxs[s])
    out = []
    for v, pnemap in enumerate(pnemaps):
        sdata = rmaker.source_data if v == 0 else _zero_source_data(
            rmaker.source_data)
        rup_data = concat(rups[v]) if rups[v] else ()
        dic = dict(rmap=pnemap.to_rates(), cfactor=cm.cfactor,
                   rup_data=rup_data, source_data=sdata,
                   task_no=rmaker.task_no, dparam_mb=0.,
                   source_mb=cm.source_mb)
        if rmaker.disagg_by_src:  # see RmapMaker.make
            dic['basename'] = valid.basename(sources[0])
        out.append(dic)
    return out


def _process_sources(rmaker, ratios, pnemaps, rups):
    # Feed the probability maps of the variants with the contexts of all the
    # sources, see make_results. The contexts are concatenated in chunks, as
    # in _make_src_indep, otherwise gen_poes is called on tiny arrays and the
    # mean_stds are computed many more times; the chunks are processed by
    # _update_chunk, which computes the GMPEs once per magnitude and chunk.
    #
    # :param rmaker: a RmapMaker instance for the base variant
    # :param ratios: ratios[v][s] as in make_results
    # :param pnemaps: a list of V MapArrays, one per variant, to update
    # :param rups: a list of V lists, the rup_data of each variant, to extend
    # :returns: the number of contexts of each source
    cm = rmaker.cmaker
    tspan = rmaker.tom.time_span
    nctxs = []
    chunk, sidxs, nrows = [], [], 0
    rmaker.rupdata = []  # used by gen_ctxs with few sites
    for s, src in enumerate(rmaker.sources):
        ctxs = list(rmaker.gen_ctxs(src))
        rmaker.rupdata = []  # the contexts are kept in ctxs
        nctxs.append(sum(len(ctx) for ctx in ctxs))
        # the ruptures of each variant, kept only with few sites as in gen_ctxs
        if cm.oq.keep_rupdata and rmaker.fewsites:
            for v, rup in enumerate(rups):
                rup.extend(_scale_rups(ctxs, ratios[v][s]))
        for ctx in ctxs:
            chunk.append(ctx)
            sidxs.append(numpy.full(len(ctx), s))
            nrows += len(ctx)
        if nrows > rmaker.maxsize:
            _update_chunk(cm, pnemaps, ratios, tspan, chunk, sidxs)
            chunk, sidxs, nrows = [], [], 0
    if chunk:
        _update_chunk(cm, pnemaps, ratios, tspan, chunk, sidxs)
    return nctxs


def _update_chunk(cm, pnemaps, ratios, tspan, ctxs, sidxs):
    # Update the probability maps of the variants with the contexts of
    # several sources, computing the PoEs once per magnitude (see
    # make_results)
    #
    # :param cm: a ContextMaker instance
    # :param pnemaps: a list of V MapArrays, one per variant
    # :param ratios: ratios[v][s] is the dictionary mag -> ratio for the
    #     source s of the variant v, see _mag_ratios
    # :param tspan: the time span of the temporal occurrence model
    # :param ctxs: a list of context arrays of the sources
    # :param sidxs: a list of arrays with the source index of each row
    ctx = concat(ctxs)
    sidx = numpy.concatenate(sidxs)
    ctx.mag = numpy.round(ctx.mag, 3)
    # sorting by magnitude (stable, so the order within each magnitude is
    # preserved) allows to process each magnitude as a contiguous slice
    order = numpy.argsort(ctx.mag, kind='stable')
    ctx = ctx[order]
    sidx = sidx[order]
    umags, starts, counts = numpy.unique(
        ctx.mag, return_index=True, return_counts=True)
    itime = tspan
    for mag, start, count in zip(umags, starts, counts):
        ctxt = ctx[start:start+count]
        si = sidx[start:start+count]
        # R[v, s] is the rate ratio of the source s in the variant v
        R = numpy.array([[r.get(float(mag), 0.) for r in rv]
                         for rv in ratios])
        cm.cfactor += [len(ctxt), 1]  # as in gen_poes
        for poes, _, _, _, slc in cm._gen_poes(ctxt):
            c = ctxt[slc]
            # read the record fields once for all the variants
            sids = c.sids
            probs_occur = c.probs_occur
            occ_rate = c.occurrence_rate
            poes = poes.astype(F64)
            for v, pnemap in enumerate(pnemaps):
                rates_v = occ_rate * R[v, si[slc]]
                pnemap._update_indep_arrays(poes, rates_v, probs_occur,
                                            sids, itime)


def _scale_rups(rupdata, ratio):
    # :param rupdata: a list of context arrays of the same source
    # :param ratio: dictionary mag -> ratio of the occurrence rates, see
    #     _mag_ratios
    # :returns: a list of context arrays with the occurrence rates rescaled
    #     by the ratio of their magnitude; the ruptures with zero rate, i.e.
    #     with a magnitude missing in the variant, are dropped
    out = []
    for ctxs in rupdata:
        factor = numpy.array([ratio.get(round(float(m), 3), 0.)
                              for m in ctxs.mag])
        mask = factor > 0
        new = ctxs[mask].copy()
        new['occurrence_rate'] *= factor[mask]
        out.append(new)
    return out


def _zero_source_data(sdata):
    # :returns: a copy of the source data with zero counts, i.e. the
    #     same grp_id and src_id but no contexts, ruptures or times
    out = AccumDict(accum=[])
    for key in sdata:
        vals = sdata[key]
        out[key] = [0 * v if key in ('nctxs', 'nrupts', 'weight',
                                     'ctimes') else v for v in vals]
    return out


class ContextMakerSequence(collections.abc.Sequence):
    """
    Wrapper over a sequence of ContextMakers
    """
    def __init__(self, cmakers, inverse):
        self.cmakers = cmakers
        self.inverse = inverse

    @property
    def Gt(self):
        """
        The total number of gsims in the underlying context makers
        """
        return sum(len(cm.gsims) for cm in self.cmakers)

    def __getitem__(self, idx):
        return self.cmakers[idx]

    def __len__(self):
        return len(self.cmakers)

    def enumerate(self):
        for grp_id, inv in enumerate(self.inverse):
            yield grp_id, self[inv]

    def to_array(self, grp_ids=slice(None)):
        return numpy.array([self[inv] for inv in self.inverse[grp_ids]])

    def get_rmap(self, src_groups, sitecol):
        """
        :returns: a RateMap of shape (N, L, Gt)
        """
        cmakers = self.to_array()
        assert cmakers[0].oq.use_rates
        assert len(src_groups) == len(cmakers)
        L = cmakers[0].imtls.size
        rmap = MapArray(sitecol.sids, L, self.Gt).fill(0)
        for group, cmaker in zip(src_groups, cmakers):
            rmap += RmapMaker(cmaker, sitecol, group).make()['rmap']
        return rmap

    def get_rmaps(self, sources, sitecol):
        """
        :param sources: a list of R variations of the same source
        :param sitecol: a SiteCollection instance
        :returns: a list of RateMaps of shape (N, L, G), one per smr
        """
        # FIXME: works only for logic trees not changing the geometries
        # and only for pointlike sources
        R = len(sources)
        cmaker = self.cmakers[0]
        assert cmaker.oq.use_rates
        assert len(self) == R, (len(self), R)
        L = cmaker.imtls.size
        G = len(cmaker.gsims)
        tom = PoissonTOM(cmaker.oq.investigation_time)
        pmaps = [MapArray(sitecol.sids, L, G, True).fill(0) for rlz in range(R)]
        ctx = cmaker.from_srcs([sources[0]], sitecol)
        magrates = [{numpy.round(mag, 3): rate
                     for mag, rate in src.get_annual_occurrence_rates()}
                     for src in sources]
        for poes, mea, sig, tau, ctxt in cmaker.gen_poes(ctx):
            mag = ctxt.mag[0]  # ctxt contains a single magnitude
            for smr, magrate in enumerate(magrates):
                orate = ctxt.occurrence_rate / magrates[0][mag] * magrate[mag]
                pmaps[smr].update_indep(poes, ctxt, tom.time_span, orate)
        return [pmap.to_rates() for pmap in pmaps]

    def combine_rates(self, rmap):
        """
        :returns: an array of shape (N, L, R) for the given site ID
        """
        N, L, G = rmap.array.shape
        assert self.Gt == G, (self.Gt, G)
        maxr = 0
        for cm in self.cmakers:
            for rlzs in cm.gsims.values():
                maxr = max(maxr, rlzs[-1])
        r0 = numpy.zeros((N, L, maxr + 1))
        g = 0
        for cm in self.cmakers:
            for i, rlzs in enumerate(cm.gsims.values()):
                rates = rmap.array[:, :, g]
                for rlz in rlzs:
                    r0[:, :, rlz] += rates
                g += 1
        return r0

    def __repr__(self):
        name = self.__class__.__name__
        return f'<{name} Gt={self.Gt}, groups={len(self.inverse)}>'


def get_unique_inverse(all_trt_smrs):
    """
    :returns: unique tuples trt_smrs and an array of indices
    """
    strings = [','.join(map(str, ts)) for ts in all_trt_smrs]
    unique, inverse = numpy.unique(strings, return_inverse=True)
    return [tuple(map(int, u.split(','))) for u in unique], inverse


def _core_gids(trt_smrs, core_trt_smrs, core_gids):
    # returns the gids of the largest set of realizations in core_trt_smrs
    # contained in trt_smrs, i.e. the whole group when it is a core set;
    # the other covering sets are partitions of the same realizations,
    # so using them too would double count the weights, see get_cmakers
    covering = [(len(ts), gids) for ts, gids in zip(core_trt_smrs, core_gids)
                if set(ts) <= set(trt_smrs)]
    if not covering:
        raise ValueError('No core set in %s' % (trt_smrs,))
    return max(covering, key=lambda pair: pair[0])[1]


def get_cmakers(all_trt_smrs, full_lt, oq, core_trt_smrs=None):
    """
    :params all_trt_smrs: a list of arrays, one per source group
    :param full_lt: a FullLogicTree instance
    :param oq: object containing the calculation parameters
    :param core_trt_smrs: the sets of realizations with the same
        uncertainties, see classical.read_gid_dic; if given, the gids
        and the weights of the cmakers are numbered as in the core list,
        so that they agree with the gids used by the master
    :returns: list of ContextMakers associated to the given src_groups
    """
    if not hasattr(full_lt, 'weights'):
        full_lt.init()
    unique_trt_smrs, inverse = get_unique_inverse(all_trt_smrs)
    numbering = (unique_trt_smrs if core_trt_smrs is None else
                 [tuple(ts) for ts in core_trt_smrs])
    if 'amplification' in oq.inputs and oq.amplification_method == 'kernel':
        df = AmplificationFunction.read_df(oq.inputs['amplification'])
        oq.af = AmplificationFunction.from_dframe(df)
    else:
        oq.af = None
    trts = list(full_lt.gsim_lt.values)
    gweights = full_lt.g_weights(numbering)[:, -1]  # shape Gt
    cmakers = []
    for grp_id, trt_smrs in enumerate(unique_trt_smrs):
        rlzs_by_gsim = full_lt.get_rlzs_by_gsim(trt_smrs)
        if not rlzs_by_gsim:  # happens for gsim_lt.reduce() on empty TRTs
            continue
        trti = trt_smrs[0] // TWO24
        cm = ContextMaker(trts[trti], rlzs_by_gsim, oq)
        cm.trti = trti
        cm.trt_smrs = trt_smrs
        cmakers.append(cm)
    if core_trt_smrs is None:
        gids = full_lt.get_gids(unique_trt_smrs)
    else:
        core_gids = full_lt.get_gids(numbering)
        gids = [_core_gids(cm.trt_smrs, numbering, core_gids)
                for cm in cmakers]
    for cm, gsim_idx in zip(cmakers, gids):
        # NB: the ids of the gsims of a group become the gids of the
        # columns of the rates only when the cmaker is restricted to an
        # index of rate attribution, see restrict_trt_smrs
        assert len(gsim_idx) == len(cm.gsims), (len(gsim_idx), cm.gsims)
        cm.gsim_idx = gsim_idx
        cm.wei = gweights[gsim_idx]
    return ContextMakerSequence(cmakers, inverse)


def read_core_trt_smrs(dstore):
    """
    :param dstore: a DataStore instance, possibly closed
    :returns: a list of trt_smrs tuples, one per realization set, i.e.
        len(dstore['core_trt_smrs']) tuples, less than the core size Gt
    """
    with dstore:  # NB: the datastore is closed when passed to a task
        return [tuple(t) for t in dstore['core_trt_smrs'][:]]


def read_cmakers(dstore, full_lt=None):
    """
    :param dstore: a DataStore-like object
    :param all_trt_smrs: a list of arrays
    :returns: an array of ContextMaker instances, one per source group
    """
    oq = dstore['oqparam']
    oq.mags_by_trt = {
        k: decode(v[:]) for k, v in dstore['source_mags'].items()}
    all_trt_smrs = dstore['trt_smrs'][:]
    if not full_lt:
        full_lt = dstore['full_lt'].init()
    core = read_core_trt_smrs(dstore) if 'core_trt_smrs' in dstore else None
    cmakers = get_cmakers(all_trt_smrs, full_lt, oq, core)
    return cmakers


def read_full_lt_by_label(dstore, full_lt=None):
    """
    :param dstore: a DataStore-like object
    :param full_lt: FullLogicTree instance; if None, it is read from the dstore
    :returns: a dictionary label -> full_lt
    """
    oq = dstore['oqparam']
    full_lt = full_lt or dstore['full_lt'].init()
    glt = full_lt.gsim_lt
    attrs = vars(full_lt)
    dic = {'Default': full_lt}
    for label in oq.site_labels:
        dic[label] = flt = copy.copy(full_lt)
        dic[label].__dict__.update(attrs)
        dic[label]._rlzs_by = {}  # reset cache, tested in logictree/case_06
        flt.label = label
        dic[label].gsim_lt = dstore['gsim_lt' + label]
        flt.weights = numpy.array(
            [rlz.weight for rlz in flt.get_realizations()])

        # all gsim logic trees in the dictionary must have the same
        # trts and the same number of gsims per trt
        exp = list(glt.values)
        got = list(flt.gsim_lt.values)
        if exp != got:
            raise InvalidFile(
                f'{oq.inputs["gsim_logic_tree"]}: expected {exp} got {got}')
        for trt, gsims in full_lt.gsim_lt.values.items():
            got = len(gsims)
            exp = len(glt.values[trt])
            if exp != got:
                raise InvalidFile(
                    f'{oq.inputs["gsim_logic_tree"]}: expected {exp} gsims '
                    f'got {got} for {trt=}')

    # sanity check: the gids must be consistent
    unique_trt_smrs, _ = get_unique_inverse(dstore['trt_smrs'][:])
    default_gids = dic['Default'].get_gids(unique_trt_smrs)
    for label in list(dic)[1:]:
        gids = dic[label].get_gids(unique_trt_smrs)
        numpy.testing.assert_equal(gids, default_gids)
    return dic


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


def get_src_mutex(srcs):
    """
    :param srcs: a list of sources with weights and the same grp_id
    :returns: a dictionary grp_id -> {'src_id': [...], 'weight': [...]}
    """
    grp_ids = [src.grp_id for src in srcs]
    [grp_id] = set(grp_ids)
    ok = all(hasattr(src, 'mutex_weight') for src in srcs)
    if not ok:
        return {grp_id: {}}
    dic = dict(src_ids=U32([src.id for src in srcs]),
               weights=F64([src.mutex_weight for src in srcs]))
    return {grp_id: dic}


def read_ctx_by_grp(dstore):
    """
    :param dstore: DataStore instance
    :returns: dictionary grp_id -> ctx
    """
    sitecol = dstore['sitecol'].complete.array
    # NB: the gid of each context, i.e. of the index of rate attribution
    # it was computed for, is a column of the rup dataframe; the gids are
    # the gsim_idx, see gmf.py
    params = {n: dstore['rup/' + n][:] for n in dstore['rup']}
    dtlist = []
    for par, val in params.items():
        if len(val) == 0:
            return {}
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
    ctx = numpy.zeros(len(params['grp_id']), dtlist).view(numpy.recarray)
    for par, val in params.items():
        ctx[par] = val
    for par in sitecol.dtype.names:
        if par != 'sids':
            ctx[par] = sitecol[par][ctx.sids]
    grp_ids = numpy.unique(ctx.grp_id)
    ctx = ctx[numpy.argsort(ctx.mag)]  # NB: crucial for performance
    return {grp_id: ctx[ctx.grp_id == grp_id] for grp_id in grp_ids}
