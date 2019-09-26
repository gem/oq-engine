# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
import sys
import time
import numpy

from openquake.baselib.general import AccumDict
from openquake.baselib.performance import Monitor
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib.calc.filters import IntegrationDistance
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.geo.surface import PlanarSurface

F32 = numpy.float32
KNOWN_DISTANCES = frozenset(
    'rrup rx ry0 rjb rhypo repi rcdpp azimuth azimuth_cp rvolc'.split())


def _update(pmap, pm, src, src_mutex, rup_mutex):
    if not rup_mutex:
        pm = ~pm
    if not pm:
        return
    if src_mutex:
        pm *= src.mutex_weight
    for grp_id in src.src_group_ids:
        if src_mutex:
            pmap[grp_id] += pm
        else:
            pmap[grp_id] |= pm


def get_distances(rupture, mesh, param):
    """
    :param rupture: a rupture
    :param mesh: a mesh of points or a site collection
    :param param: the kind of distance to compute (default rjb)
    :returns: an array of distances from the given mesh
    """
    if param == 'rrup':
        dist = rupture.surface.get_min_distance(mesh)
    elif param == 'rx':
        dist = rupture.surface.get_rx_distance(mesh)
    elif param == 'ry0':
        dist = rupture.surface.get_ry0_distance(mesh)
    elif param == 'rjb':
        dist = rupture.surface.get_joyner_boore_distance(mesh)
    elif param == 'rhypo':
        dist = rupture.hypocenter.distance_to_mesh(mesh)
    elif param == 'repi':
        dist = rupture.hypocenter.distance_to_mesh(mesh, with_depths=False)
    elif param == 'rcdpp':
        dist = rupture.get_cdppvalue(mesh)
    elif param == 'azimuth':
        dist = rupture.surface.get_azimuth(mesh)
    elif param == 'azimuth_cp':
        dist = rupture.surface.get_azimuth_of_closest_point(mesh)
    elif param == "rvolc":
        # Volcanic distance not yet supported, defaulting to zero
        dist = numpy.zeros_like(mesh.lons)
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
    def __init__(self, cmaker):
        self.cmaker = cmaker
        self.data = AccumDict(accum=[])

    def from_srcs(self, srcs, sites):  # used in disagg.disaggregation
        """
        :returns: param -> array
        """
        for src in srcs:
            for rup in src.iter_ruptures():
                self.cmaker.add_rup_params(rup)
                self.add(rup, src.id, sites)
        return {k: numpy.array(v) for k, v in self.data.items()}

    def add(self, rup, src_id, sctx, dctx=None):
        rate = rup.occurrence_rate
        if numpy.isnan(rate):  # for nonparametric ruptures
            probs_occur = rup.probs_occur
        else:
            probs_occur = numpy.zeros(0, numpy.float64)
        self.data['srcidx'].append(src_id or 0)
        self.data['occurrence_rate'].append(rate)
        self.data['weight'].append(rup.weight or numpy.nan)
        self.data['probs_occur'].append(probs_occur)
        for rup_param in self.cmaker.REQUIRES_RUPTURE_PARAMETERS:
            self.data[rup_param].append(getattr(rup, rup_param))

        self.data['sid_'].append(numpy.int16(sctx.sids))
        for dst_param in self.cmaker.REQUIRES_DISTANCES:
            if dctx is None:  # compute the distances
                dists = get_distances(rup, sctx, dst_param)
            else:  # reuse already computed distances
                dists = getattr(dctx, dst_param)
            self.data[dst_param + '_'].append(F32(dists))
        closest = rup.surface.get_closest_points(sctx)
        self.data['lon_'].append(F32(closest.lons))
        self.data['lat_'].append(F32(closest.lats))


class ContextMaker(object):
    """
    A class to manage the creation of contexts for distances, sites, rupture.
    """
    REQUIRES = ['DISTANCES', 'SITES_PARAMETERS', 'RUPTURE_PARAMETERS']

    def __init__(self, trt, gsims, param=None, monitor=Monitor()):
        param = param or {}
        self.max_sites_disagg = param.get('max_sites_disagg', 10)
        self.trt = trt
        self.gsims = gsims
        self.maximum_distance = (
            param.get('maximum_distance') or IntegrationDistance({}))
        self.trunclevel = param.get('truncation_level')
        self.pointsource_distance = param.get('pointsource_distance', {})
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
            setattr(self, 'REQUIRES_' + req, reqset)
        filter_distance = param.get('filter_distance')
        if filter_distance is None:
            if 'rrup' in self.REQUIRES_DISTANCES:
                filter_distance = 'rrup'
            elif 'rjb' in self.REQUIRES_DISTANCES:
                filter_distance = 'rjb'
            else:
                filter_distance = 'rrup'
        self.filter_distance = filter_distance
        self.imtls = param.get('imtls', {})
        self.imts = [imt_module.from_string(imt) for imt in self.imtls]
        self.reqv = param.get('reqv')
        self.REQUIRES_DISTANCES.add(self.filter_distance)
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
        self.ctx_mon = monitor('make_contexts', measuremem=False)
        self.poe_mon = monitor('get_poes', measuremem=False)
        self.gmf_mon = monitor('computing mean_std', measuremem=False)

    def filter(self, sites, rupture):
        """
        Filter the site collection with respect to the rupture.

        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.
        :param rupture:
            Instance of
            :class:`openquake.hazardlib.source.rupture.BaseRupture`
        :returns:
            (filtered sites, distance context)
        """
        distances = get_distances(rupture, sites, self.filter_distance)
        if self.maximum_distance:
            mask = distances <= self.maximum_distance(
                rupture.tectonic_region_type, rupture.mag)
            if mask.any():
                sites, distances = sites.filter(mask), distances[mask]
            else:
                raise FarAwayRupture(
                    '%d: %d km' % (rupture.rup_id, distances.min()))
        return sites, DistancesContext([(self.filter_distance, distances)])

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
            Tuple of two items: sites and distances context.

        :raises ValueError:
            If any of declared required parameters (site, rupture and
            distance parameters) is unknown.
        """
        sites, dctx = self.filter(sites, rupture)
        for param in self.REQUIRES_DISTANCES - set([self.filter_distance]):
            distances = get_distances(rupture, sites, param)
            setattr(dctx, param, distances)
        reqv_obj = (self.reqv.get(rupture.tectonic_region_type)
                    if self.reqv else None)
        if reqv_obj and isinstance(rupture.surface, PlanarSurface):
            reqv = reqv_obj.get(dctx.repi, rupture.mag)
            if 'rjb' in self.REQUIRES_DISTANCES:
                dctx.rjb = reqv
            if 'rrup' in self.REQUIRES_DISTANCES:
                reqv_rup = numpy.sqrt(reqv**2 + rupture.hypocenter.depth**2)
                dctx.rrup = reqv_rup
        self.add_rup_params(rupture)
        return sites, dctx

    def get_pmap(self, src, s_sites, rup_indep=True):
        """
        :param src: a hazardlib source
        :param s_sites: the sites affected by it
        :returns: the probability map generated by the source
        """
        imts = self.imts
        sitecol = s_sites.complete
        N, M = len(sitecol), len(imts)
        fewsites = N <= self.max_sites_disagg
        rupdata = RupData(self)
        nrups, nsites = 0, 0
        L, G = len(self.imtls.array), len(self.gsims)
        poemap = ProbabilityMap(L, G)
        for rup, sites in self._gen_rup_sites(src, s_sites):
            try:
                with self.ctx_mon:
                    sctx, dctx = self.make_contexts(sites, rup)
            except FarAwayRupture:
                continue
            with self.gmf_mon:
                mean_std = numpy.zeros((G, 2, len(sctx), M))
                for i, gsim in enumerate(self.gsims):
                    dctx_ = dctx.roundup(gsim.minimum_distance)
                    mean_std[i] = gsim.get_mean_std(sctx, rup, dctx_, imts)
            with self.poe_mon:
                for sid, pne in self._make_pnes(rup, sctx.sids, mean_std):
                    pcurve = poemap.setdefault(sid, rup_indep)
                    if rup_indep:
                        pcurve.array *= pne
                    else:
                        pcurve.array += (1.-pne) * rup.weight
            nrups += 1
            nsites += len(sctx)
            if fewsites:  # store rupdata
                rupdata.add(rup, src.id, sctx, dctx)
        poemap.nrups = nrups
        poemap.nsites = nsites
        poemap.data = rupdata.data
        return poemap

    def _gen_rup_sites(self, src, sites):
        # implements the pointsource_distance feature
        pdist = self.pointsource_distance.get(src.tectonic_region_type)
        if hasattr(src, 'location') and pdist and src.count_nphc() > 1:
            close_sites, far_sites = sites.split(src.location, pdist)
            if close_sites is None:  # all is far
                for rup in src.iter_ruptures(False, False):
                    yield rup, far_sites
            elif far_sites is None:  # all is close
                for rup in src.iter_ruptures(True, True):
                    yield rup, close_sites
            else:
                for rup in src.iter_ruptures(True, True):
                    yield rup, close_sites
                for rup in src.iter_ruptures(False, False):
                    yield rup, far_sites
        else:
            for rup in src.iter_ruptures():
                yield rup, sites

    def get_pmap_by_grp(self, src_sites, src_mutex=False, rup_mutex=False):
        """
        :param src_sites: an iterator of pairs (source, sites)
        :param src_mutex: True if the sources are mutually exclusive
        :param rup_mutex: True if the ruptures are mutually exclusive
        :return: dictionaries pmap, rdata, calc_times
        """
        imtls = self.imtls
        L, G = len(imtls.array), len(self.gsims)
        pmap = AccumDict(accum=ProbabilityMap(L, G))
        gids = []
        rup_data = AccumDict(accum=[])
        # AccumDict of arrays with 3 elements nrups, nsites, calc_time
        calc_times = AccumDict(accum=numpy.zeros(3, numpy.float32))
        it = iter(src_sites)
        while True:
            t0 = time.time()
            try:
                src, s_sites = next(it)
                poemap = self.get_pmap(src, s_sites, not rup_mutex)
                _update(pmap, poemap, src, src_mutex, rup_mutex)
            except StopIteration:
                break
            except Exception as err:
                etype, err, tb = sys.exc_info()
                msg = '%s (source id=%s)' % (str(err), src.source_id)
                raise etype(msg).with_traceback(tb)
            if len(poemap.data):
                nr = len(poemap.data['sid_'])
                for gid in src.src_group_ids:
                    gids.extend([gid] * nr)
                    for k, v in poemap.data.items():
                        rup_data[k].extend(v)
            calc_times[src.id] += numpy.array(
                [poemap.nrups, poemap.nsites, time.time() - t0])

        rdata = {k: numpy.array(v) for k, v in rup_data.items()}
        rdata['grp_id'] = numpy.uint16(gids)
        return pmap, rdata, calc_times

    # NB: it is important for this to be fast since it is inside an inner loop
    def _make_pnes(self, rupture, sids, mean_std):
        imtls = self.imtls
        nsites = len(sids)
        pne_array = numpy.zeros((nsites, len(imtls.array), len(self.gsims)))
        for i, gsim in enumerate(self.gsims):
            for m, imt in enumerate(imtls):
                slc = imtls(imt)
                if hasattr(gsim, 'weight') and gsim.weight[imt] == 0:
                    # set by the engine when parsing the gsim logictree;
                    # when 0 ignore the gsim: see _build_trts_branches
                    pno = numpy.ones((nsites, slc.stop - slc.start))
                else:
                    poes = gsim.get_poes(
                        mean_std[i, :, :, m], imtls[imt], self.trunclevel)
                    pno = rupture.get_probability_no_exceedance(poes)
                pne_array[:, slc, i] = pno
        return zip(sids, pne_array)


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
            calling the :meth:`method
            <openquake.hazardlib.gsim.base.GroundShakingIntensityModel.get_poes>
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
