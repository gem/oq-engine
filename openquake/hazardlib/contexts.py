#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import abc
import sys
import numpy

from openquake.baselib.general import AccumDict
from openquake.baselib.performance import Monitor
from openquake.baselib.python3compat import with_metaclass, raise_
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib.probability_map import ProbabilityMap


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
    elif param == "rvolc":
        # Volcanic distance not yet supported, defaulting to zero
        dist = numpy.zeros_like(mesh.lons)
    else:
        raise ValueError('Unknown distance measure %r' % param)
    return dist


class FarAwayRupture(Exception):
    """Raised if the rupture is outside the maximum distance for all sites"""


class ContextMaker(object):
    """
    A class to manage the creation of contexts for distances, sites, rupture.
    """
    REQUIRES = ['DISTANCES', 'SITES_PARAMETERS', 'RUPTURE_PARAMETERS']

    def __init__(self, gsims, maximum_distance=None, filter_distance='rjb'):
        self.gsims = gsims
        self.maximum_distance = maximum_distance or {}
        self.filter_distance = filter_distance
        for req in self.REQUIRES:
            reqset = set()
            for gsim in gsims:
                reqset.update(getattr(gsim, 'REQUIRES_' + req))
            setattr(self, 'REQUIRES_' + req, reqset)
        self.REQUIRES_DISTANCES.add(self.filter_distance)
        if hasattr(gsims, 'items'):  # gsims is actually a dict rlzs_by_gsim
            # since the ContextMaker must be used on ruptures with all the
            # same TRT, given a realization there is a single gsim
            self.gsim_by_rlzi = {}
            for gsim, rlzis in gsims.items():
                for rlzi in rlzis:
                    self.gsim_by_rlzi[rlzi] = gsim

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
                raise FarAwayRupture
        return sites, DistancesContext([(self.filter_distance, distances)])

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
            If any of declared required parameters (that includes site, rupture
            and distance parameters) is unknown.
        """
        sites, dctx = self.filter(sites, rupture)
        for param in self.REQUIRES_DISTANCES - set([self.filter_distance]):
            setattr(dctx, param, get_distances(rupture, sites, param))
        # NB: returning a SitesContext makes .get_poes faster
        return SitesContext(sites), dctx

    def filter_ruptures(self, src, sites):
        """
        :param src: a source object, already filtered and split
        :param sites: a filtered SiteCollection
        :return: a list of filtered ruptures with context attributes
        """
        ruptures = []
        weight = 1. / (src.num_ruptures or src.count_ruptures())
        for rup in src.iter_ruptures():
            rup.weight = weight
            try:
                rup.sctx, rup.dctx = self.make_contexts(sites, rup)
            except FarAwayRupture:
                continue
            ruptures.append(rup)
        return ruptures

    def make_pmap(self, ruptures, imtls, trunclevel, rup_indep):
        """
        :param src: a source object
        :param ruptures: a list of "dressed" ruptures
        :param imtls: intensity measure and levels
        :param trunclevel: truncation level
        :param rup_indep: True if the ruptures are independent
        :returns: a ProbabilityMap instance
        """
        sids = set()
        for rup in ruptures:
            sids.update(rup.sctx.sids)
        pmap = ProbabilityMap.build(
            len(imtls.array), len(self.gsims), sids, initvalue=rup_indep)
        for rup in ruptures:
            pnes = self._make_pnes(rup, imtls, trunclevel)
            for sid, pne in zip(rup.sctx.sids, pnes):
                if rup_indep:
                    pmap[sid].array *= pne
                else:
                    pmap[sid].array += pne * rup.weight
        tildemap = ~pmap
        tildemap.eff_ruptures = len(ruptures)
        return tildemap

    def poe_map(self, src, sites, imtls, trunclevel, ctx_mon, poe_mon,
                rup_indep=True):
        """
        :param src: a source object
        :param sites: a filtered SiteCollection
        :param imtls: intensity measure and levels
        :param trunclevel: truncation level
        :param ctx_mon: a Monitor instance for make_context
        :param poe_mon: a Monitor instance for get_poes
        :param rup_indep: True if the ruptures are independent
        :returns: a ProbabilityMap instance
        """
        with ctx_mon:
            ruptures = self.filter_ruptures(src, sites)
        if not ruptures:
            return {}
        try:
            with poe_mon:
                pmap = self.make_pmap(ruptures, imtls, trunclevel, rup_indep)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = '%s (source id=%s)' % (str(err), src.source_id)
            raise_(etype, msg, tb)
        return pmap

    # NB: it is important for this to be fast since it is inside an inner loop
    def _make_pnes(self, rupture, imtls, trunclevel):
        pne_array = numpy.zeros(
            (len(rupture.sctx.sids), len(imtls.array), len(self.gsims)))
        for i, gsim in enumerate(self.gsims):
            dctx = rupture.dctx.roundup(gsim.minimum_distance)
            pnos = []  # list of arrays nsites x nlevels
            for imt in imtls:
                poes = gsim.get_poes(
                    rupture.sctx, rupture, dctx,
                    imt_module.from_string(imt), imtls[imt], trunclevel)
                pnos.append(rupture.get_probability_no_exceedance(poes))
            pne_array[:, :, i] = numpy.concatenate(pnos, axis=1)
        return pne_array

    def disaggregate(self, sitecol, ruptures, iml4, truncnorm, epsilons,
                     monitor=Monitor()):
        """
        Disaggregate (separate) PoE of `imldict` in different contributions
        each coming from `n_epsilons` distribution bins.

        :param sitecol: a SiteCollection
        :param ruptures: an iterator over ruptures with the same TRT
        :param iml4: a 4d array of IMLs of shape (N, R, M, P)
        :param truncnorm: an instance of scipy.stats.truncnorm
        :param epsilons: the epsilon bins
        :param monitor: a Monitor instance
        :returns:
            an AccumDict with keys (poe, imt, rlzi) and mags, dists, lons, lats
        """
        acc = AccumDict(accum=[])
        ctx_mon = monitor('disagg_contexts', measuremem=False)
        pne_mon = monitor('disaggregate_pne', measuremem=False)
        for rupture in ruptures:
            with ctx_mon:
                orig_dctx = DistancesContext(
                    (param, get_distances(rupture, sitecol, param))
                    for param in self.REQUIRES_DISTANCES)
            cache = {}
            for r, gsim in self.gsim_by_rlzi.items():
                dctx = orig_dctx.roundup(gsim.minimum_distance)
                for m, imt in enumerate(iml4.imts):
                    for p, poe in enumerate(iml4.poes_disagg):
                        iml = tuple(iml4.array[:, r, m, p])
                        try:
                            pne = cache[gsim, imt, iml]
                        except KeyError:
                            with pne_mon:
                                pne = gsim.disaggregate_pne(
                                    rupture, sitecol, dctx, imt, iml,
                                    truncnorm, epsilons)
                                cache[gsim, imt, iml] = pne
                        acc[poe, str(imt), r].append(pne)
            closest_points = rupture.surface.get_closest_points(sitecol)
            acc['mags'].append(rupture.mag)
            acc['dists'].append(getattr(dctx, self.filter_distance))
            acc['lons'].append(closest_points.lons)
            acc['lats'].append(closest_points.lats)
        return acc


class BaseContext(with_metaclass(abc.ABCMeta)):
    """
    Base class for context object.
    """

    def __eq__(self, other):
        """
        Return True if ``other`` has same attributes with same values.
        """
        if isinstance(other, self.__class__):
            if self._slots_ == other._slots_:
                self_other = [
                    numpy.all(
                        getattr(self, s, None) == getattr(other, s, None))
                    for s in self._slots_]
                return numpy.all(self_other)
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
    _slots_ = ('vs30', 'vs30measured', 'z1pt0', 'z2pt5', 'backarc',
               'lons', 'lats')

    def __init__(self, sitecol=None):
        if sitecol is not None:
            self.sids = sitecol.sids
            for name in self._slots_:
                setattr(self, name, getattr(sitecol, name))


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
                array = array[:]  # make a copy first
                array[small_distances] = minimum_distance
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
