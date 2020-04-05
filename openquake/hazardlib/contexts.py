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
import warnings
import operator
import itertools
import collections
import numpy
from scipy.interpolate import interp1d


from openquake.baselib.general import (
    AccumDict, DictArray, groupby, groupby_bin)
from openquake.baselib.performance import Monitor
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib.gsim import base
from openquake.hazardlib.calc.filters import IntegrationDistance, getdefault
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.surface import PlanarSurface

bymag = operator.attrgetter('mag')
I16 = numpy.int16
F32 = numpy.float32
KNOWN_DISTANCES = frozenset(
    'rrup rx ry0 rjb rhypo repi rcdpp azimuth azimuth_cp rvolc'.split())
POINT_RUPTURE_BINS = 20


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


class RupData(object):
    """
    A class to collect rupture information into an array
    """
    def __init__(self, cmaker, data=None):
        self.cmaker = cmaker
        self.data = AccumDict(accum=[]) if data is None else data

    def from_srcs(self, srcs, sites):  # used in disagg.disaggregation
        """
        :returns: param -> array
        """
        grp_ids = [0]
        for src in srcs:
            rups = list(src.iter_ruptures(shift_hypo=self.cmaker.shift_hypo))
            for rup in rups:
                self.cmaker.add_rup_params(rup)
            ctxs = self.cmaker.make_ctxs(rups, sites, grp_ids, False)
            self.add(ctxs, sites, grp_ids)
        return self.dictarray()

    def add(self, ctxs, sites, grp_ids):
        U, N = len(ctxs), len(sites.complete)
        params = (sorted(self.cmaker.REQUIRES_DISTANCES | {'rrup'}) +
                  ['lon', 'lat'])
        data = {par + '_': numpy.ones((U, N), F32) * 9999 for par in params}
        for par in data:
            self.data[par].append(data[par])
        for r, (rup, dctx) in enumerate(ctxs):
            if numpy.isnan(rup.occurrence_rate):  # for nonparametric ruptures
                probs_occur = rup.probs_occur
            else:
                probs_occur = numpy.zeros(0, numpy.float64)
            self.data['occurrence_rate'].append(rup.occurrence_rate)
            self.data['probs_occur'].append(probs_occur)
            self.data['weight'].append(rup.weight or numpy.nan)
            self.data['grp_id'].append(grp_ids)
            for rup_param in self.cmaker.REQUIRES_RUPTURE_PARAMETERS:
                self.data[rup_param].append(getattr(rup, rup_param))
            for dst_param in params[:-2]:  # except lon, lat
                for s, dst in zip(sites.sids, getattr(dctx, dst_param)):
                    data[dst_param + '_'][r, s] = dst
            closest = rup.surface.get_closest_points(sites)
            for s, lon, lat in zip(sites.sids, closest.lons, closest.lats):
                data['lon_'][r, s] = lon
                data['lat_'][r, s] = lat

    def dictarray(self):
        """
        :returns: key -> array
        """
        dic = {}
        for k, v in self.data.items():
            if k.endswith('_'):
                dic[k] = numpy.concatenate(v)
            else:
                dic[k] = numpy.array(v)
        return dic


class ContextMaker(object):
    """
    A class to manage the creation of contexts for distances, sites, rupture.
    """
    REQUIRES = ['DISTANCES', 'SITES_PARAMETERS', 'RUPTURE_PARAMETERS']

    def __init__(self, trt, gsims, param=None, monitor=Monitor()):
        param = param or {}
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.collapse_ctxs = param.get('collapse_ctxs', False)
        self.trt = trt
        self.gsims = gsims
        self.maximum_distance = (
            param.get('maximum_distance') or IntegrationDistance({}))
        self.trunclevel = param.get('truncation_level')
        self.effect = param.get('effect')
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
            setattr(self, 'REQUIRES_' + req, reqset)
        psd = param.get('pointsource_distance', {'default': {}})
        self.pointsource_distance = getdefault(psd, trt)  # can be 0 or {}
        # NB: self.pointsource_distance is a dict mag -> pdist, possibly empty
        self.filter_distance = 'rrup'
        self.imtls = param.get('imtls', {})
        self.imts = [imt_module.from_string(imt) for imt in self.imtls]
        self.reqv = param.get('reqv')
        if self.reqv is not None:
            self.REQUIRES_DISTANCES.add('repi')
        if hasattr(gsims, 'items'):
            # gsims is actually a dict rlzs_by_gsim
            # since the ContextMaker must be used on ruptures with the
            # same TRT, given a realization there is a single gsim
            self.gsim_by_rlzi = {}
            for gsim, rlzis in gsims.items():
                for rlzi in rlzis:
                    self.gsim_by_rlzi[rlzi] = gsim
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

    def add_rup_params(self, rupture):
        """
        Add .REQUIRES_RUPTURE_PARAMETERS to the rupture
        """
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
            setattr(rupture, param, value)

    def make_contexts(self, sites, rupture, filt=True):
        """
        Filter the site collection with respect to the rupture and
        create context objects.

        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.

        :param rupture:
            Instance of
            :class:`openquake.hazardlib.source.rupture.BaseRupture`

        :param boolean filt:
            If True filter the sites

        :returns:
            Tuple of two items: sites and distances context.

        :raises ValueError:
            If any of declared required parameters (site, rupture and
            distance parameters) is unknown.
        """
        if filt:
            sites, dctx = self.filter(sites, rupture)
        else:
            dctx = self.get_dctx(sites, rupture)
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
        self.add_rup_params(rupture)
        return sites, dctx

    def make_ctxs(self, ruptures, sites, grp_ids, filt):
        """
        :returns:
            a list of triples (rctx, sctx, dctx) if filt is True,
            a list of pairs (rctx, dctx) if filt is False
        """
        ctxs = []
        for rup in ruptures:
            try:
                sctx, dctx = self.make_contexts(sites, rup, filt)
            except FarAwayRupture:
                continue
            rup.grp_ids = grp_ids
            if filt:
                ctxs.append((rup, sctx, dctx))
            else:
                ctxs.append((rup, dctx))
        return ctxs

    def max_intensity(self, onesite, mags, dists):
        """
        :param onesite: a SiteCollection instance with a single site
        :param mags: a sequence of magnitudes
        :param dists: a sequence of distances
        :returns: an array of GMVs of shape (#mags, #dists)
        """
        assert len(onesite) == 1, onesite
        nmags, ndists = len(mags), len(dists)
        gmv = numpy.zeros((nmags, ndists))
        for m, d in itertools.product(range(nmags), range(ndists)):
            mag, dist = mags[m], dists[d]
            rup = RuptureContext()
            for par in self.REQUIRES_RUPTURE_PARAMETERS:
                setattr(rup, par, 0)
            rup.mag = mag
            rup.width = .01  # 10 meters to avoid warnings in abrahamson_2014
            dctx = DistancesContext(
                (dst, numpy.array([dist])) for dst in self.REQUIRES_DISTANCES)
            means = []
            for gsim in self.gsims:
                try:
                    mean = base.get_mean_std(  # shape (2, N, M, G) -> M
                        onesite, rup, dctx, self.imts, [gsim])[0, 0, :, 0]
                except ValueError:  # magnitude outside of supported range
                    continue
                means.append(mean.max())
            if means:
                gmv[m, d] = numpy.exp(max(means))
        return gmv


def _collapse(rups):
    # collapse a list of ruptures into a single rupture
    if len(rups) < 2:
        return rups
    rup = copy.copy(rups[0])
    rup.occurrence_rate = sum(r.occurrence_rate for r in rups)
    return [rup]


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
        self.group = group
        self.src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
        self.rup_indep = getattr(group, 'rup_interdep', None) != 'mutex'
        self.fewsites = len(srcfilter.sitecol) <= cmaker.max_sites_disagg
        self.poe_mon = cmaker.mon('get_poes', measuremem=False)
        self.pne_mon = cmaker.mon('composing pnes', measuremem=False)
        self.gmf_mon = cmaker.mon('computing mean_std', measuremem=False)

    def _ctxs(self, rups, sites, grp_ids):
        if self.fewsites:  # do not filter, but collapse
            rup_parametric = not numpy.isnan(
                [r.occurrence_rate for r in rups]).any()
            if (self.rup_indep and rup_parametric and len(sites) == 1
                    and self.pointsource_distance != {}):
                rups = self.collapse_point_ruptures(rups, sites)
                # print_finite_size(rups)
            ctxs = self.cmaker.make_ctxs(rups, sites, grp_ids, filt=False)
            if self.rup_indep and rup_parametric and self.collapse_ctxs:
                ctxs = self.collapse_the_ctxs(ctxs)
            self.numrups += len(ctxs)
            if ctxs:
                self.rupdata.add(ctxs, sites, grp_ids)
            for rup, dctx in ctxs:
                mask = (dctx.rrup <= self.maximum_distance(
                    rup.tectonic_region_type, rup.mag))
                r_sites = sites.filter(mask)
                for name in self.REQUIRES_DISTANCES:
                    setattr(dctx, name, getattr(dctx, name)[mask])
                self.numsites += len(r_sites)
                yield rup, r_sites, dctx
        else:  # many sites, do not collapse, but filter
            ctxs = self.cmaker.make_ctxs(rups, sites, grp_ids, filt=True)
            self.numrups += len(ctxs)
            self.numsites += sum(len(ctx[1]) for ctx in ctxs)
            yield from ctxs

    def _update_pmap(self, ctxs, pmap=None):
        # compute PoEs and update pmap
        if pmap is None:  # for src_indep
            pmap = self.pmap
        for rup, r_sites, dctx in ctxs:
            # this must be fast since it is inside an inner loop
            with self.gmf_mon:
                mean_std = base.get_mean_std(  # shape (2, N, M, G)
                    r_sites, rup, dctx, self.imts, self.gsims)
            with self.poe_mon:
                ll = self.loglevels
                poes = base.get_poes(mean_std, ll, self.trunclevel, self.gsims)
                for g, gsim in enumerate(self.gsims):
                    for m, imt in enumerate(ll):
                        if hasattr(gsim, 'weight') and gsim.weight[imt] == 0:
                            # set by the engine when parsing the gsim logictree
                            # when 0 ignore the gsim: see _build_trts_branches
                            poes[:, ll(imt), g] = 0
            with self.pne_mon:
                # pnes and poes of shape (N, L, G)
                pnes = rup.get_probability_no_exceedance(poes)
                for grp_id in rup.grp_ids:
                    p = pmap[grp_id]
                    if self.rup_indep:
                        for sid, pne in zip(r_sites.sids, pnes):
                            p.setdefault(sid, 1.).array *= pne
                    else:  # rup_mutex
                        for sid, pne in zip(r_sites.sids, pnes):
                            p.setdefault(sid, 0.).array += (
                                1.-pne) * rup.weight

    def _ruptures(self, src, filtermag=None):
        with self.cmaker.mon('iter_ruptures', measuremem=False):
            return list(src.iter_ruptures(shift_hypo=self.shift_hypo,
                                          mag=filtermag))

    def _make_src_indep(self):
        # srcs with the same source_id and grp_ids
        for srcs, sites in self.srcfilter.get_sources_sites(self.group):
            t0 = time.time()
            src_id = srcs[0].source_id
            grp_ids = numpy.array(srcs[0].grp_ids)
            self.numrups = 0
            self.numsites = 0
            ctxs = []
            rups = self._get_rups(srcs, sites)
            # print_finite_size(rups)
            with self.ctx_mon:
                if self.fewsites:
                    ctxs.extend(self._ctxs(rups, sites, grp_ids))
                else:  # many sites
                    for rup in rups:
                        ctxs.extend(self._ctxs([rup], rup.sites, grp_ids))
            self._update_pmap(ctxs)
            self.calc_times[src_id] += numpy.array(
                [self.numrups, self.numsites, time.time() - t0])
        return AccumDict((grp_id, ~p if self.rup_indep else p)
                         for grp_id, p in self.pmap.items())

    def _make_src_mutex(self):
        for src, sites in self.srcfilter(self.group):
            t0 = time.time()
            self.totrups += src.num_ruptures
            self.numrups = 0
            self.numsites = 0
            rups = self._ruptures(src)
            with self.ctx_mon:
                L, G = len(self.cmaker.imtls.array), len(self.cmaker.gsims)
                pmap = {grp_id: ProbabilityMap(L, G) for grp_id in src.grp_ids}
                ctxs = list(self._ctxs(rups, sites, numpy.array(src.grp_ids)))
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

    def make(self):
        self.rupdata = RupData(self.cmaker)
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
        return (pmap, self.rupdata.dictarray(), self.calc_times,
                dict(totrups=self.totrups))

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
            for rs in groupby_bin(
                    coll, POINT_RUPTURE_BINS, operator.attrgetter('dist')):
                # group together ruptures in the same distance bin
                output.extend(_collapse(rs))
        return output

    def collapse_the_ctxs(self, ctxs):
        """
        Collapse contexts with similar parameters and distances.

        :param ctxs: a list of pairs (rup, dctx)
        :returns: collapsed contexts
        """
        def params(ctx):
            rup, dctx = ctx
            lst = []
            for par in self.REQUIRES_RUPTURE_PARAMETERS:
                lst.append(getattr(rup, par))
            for dst in self.REQUIRES_DISTANCES:
                lst.extend(numpy.round(getattr(dctx, dst)))
            return tuple(lst)

        out = []
        for values in groupby(ctxs, params).values():
            if len(values) == 1:
                out.append(values[0])
            else:
                [rup] = _collapse([rup for rup, dctx in values])
                dctx = values[0][1]  # get the first dctx
                out.append((rup, dctx))
        return out

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

    def __init__(self, param_pairs=()):
        for param, value in param_pairs:
            setattr(self, param, value)

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
            calling the :func:`func <openquake.hazardlib.gsim.base.get_poes>
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
            # Converting from 1d to 2d
            if len(poes.shape) == 1:
                poes = numpy.reshape(poes, (-1, len(poes)))
            p_kT = self.probs_occur
            prob_no_exceed = numpy.array(
                [v * ((1 - poes) ** i) for i, v in enumerate(p_kT)])
            prob_no_exceed = numpy.sum(prob_no_exceed, axis=0)
            if isinstance(prob_no_exceed, numpy.ndarray):
                prob_no_exceed[prob_no_exceed > 1.] = 1.  # sanity check
                prob_no_exceed[poes == 0.] = 1.  # avoid numeric issues
            return prob_no_exceed
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
        :returns: intensity at the maximum magnitude and collapse distance
        """
        effectmax = self.effect_by_mag[max(self.effect_by_mag)]
        idx = numpy.searchsorted(self.dists, collapse_dist)
        return effectmax[idx-1 if idx == self.nbins else idx]

    def __call__(self, mag, dist):
        di = numpy.searchsorted(self.dists, dist)
        if di == self.nbins:
            di = self.nbins
        eff = self.effect_by_mag['%.2f' % mag][di]
        return eff

    # this is useful to compute the collapse_distance and minimum_distance
    def dist_by_mag(self, intensity=0):
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


# used in calculators/classical.py
def get_effect_by_mag(mags, onesite, gsims_by_trt, maximum_distance, imtls,
                      monitor):
    """
    :param mag: an ordered list of magnitude strings with format %.2f
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
            onesite, [float(mag) for mag in mags], dist_bins)
    return dict(zip(mags, gmv))


# used in calculators/classical.py
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
    for src, sites in srcfilter(sources):
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
