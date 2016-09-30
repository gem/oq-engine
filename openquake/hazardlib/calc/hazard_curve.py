# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2016 GEM Foundation
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
:mod:`openquake.hazardlib.calc.hazard_curve` implements
:func:`calc_hazard_curves`.
"""
from __future__ import division
import sys
import time
import operator
import collections

import numpy

from openquake.baselib.python3compat import raise_, zip
from openquake.baselib.performance import Monitor
from openquake.baselib.general import groupby, DictArray
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc import filters
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib.gsim.base import GroundShakingIntensityModel

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.source.base import SourceGroup, SourceGroupCollection


def zero_curves(num_sites, imtls):
    """
    :param num_sites: the number of sites
    :param imtls: the intensity measure levels dictionary
    :returns: an array of zero curves with length num_sites
    """
    # numpy dtype for the hazard curves
    imt_dt = numpy.dtype([(imt, float, 1 if imls is None else len(imls))
                          for imt, imls in imtls.items()])
    return numpy.zeros(num_sites, imt_dt)


def rupture_weight_pairs(src):
    """
    Generator yielding (rupture, weight) for each rupture in the source
    """
    if hasattr(src, 'weights'):
        for pair in zip(src.iter_ruptures(), src.weights):
            yield pair
    weight = 1. / (src.num_ruptures or src.count_ruptures())
    for rup in src.iter_ruptures():
        yield rup, weight


# old version working only for independent sources
def calc_hazard_curves(
        sources, sites, imtls, gsim_by_trt, truncation_level=None,
        source_site_filter=filters.source_site_noop_filter):
    """
    Compute hazard curves on a list of sites, given a set of seismic sources
    and a set of ground shaking intensity models (one per tectonic region type
    considered in the seismic sources).

    Probability of ground motion exceedance is computed using the following
    formula ::

        P(X≥x|T) = 1 - ∏ ∏ Prup_ij(X<x|T)

    where ``P(X≥x|T)`` is the probability that the ground motion parameter
    ``X`` is exceeding level ``x`` one or more times in a time span ``T``, and
    ``Prup_ij(X<x|T)`` is the probability that the j-th rupture of the i-th
    source is not producing any ground motion exceedance in time span ``T``.
    The first product ``∏`` is done over sources, while the second one is done
    over ruptures in a source.

    The above formula computes the probability of having at least one ground
    motion exceedance in a time span as 1 minus the probability that none of
    the ruptures in none of the sources is causing a ground motion exceedance
    in the same time span. The basic assumption is that seismic sources are
    independent, and ruptures in a seismic source are also independent.

    :param sources:
        A sequence of seismic sources objects (instances of subclasses
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param sites:
        Instance of :class:`~openquake.hazardlib.site.SiteCollection` object,
        representing sites of interest.
    :param imtls:
        Dictionary mapping intensity measure type strings
        to lists of intensity measure levels.
    :param gsim_by_trt:
        Dictionary mapping tectonic region types (members
        of :class:`openquake.hazardlib.const.TRT`) to
        :class:`~openquake.hazardlib.gsim.base.GMPE` or
        :class:`~openquake.hazardlib.gsim.base.IPE` objects.
    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.
    :param source_site_filter:
        Optional source-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.

    :returns:
        An array of size N, where N is the number of sites, which elements
        are records with fields given by the intensity measure types; the
        size of each field is given by the number of levels in ``imtls``.
    """
    imtls = DictArray(imtls)
    sources_by_trt = groupby(
        sources, operator.attrgetter('tectonic_region_type'))
    pmap = ProbabilityMap(len(imtls.array), 1)
    for trt in sources_by_trt:
        pmap |= pmap_from_grp(
            sources_by_trt[trt], sites, imtls, [gsim_by_trt[trt]],
            truncation_level, source_site_filter)
    return pmap.convert(imtls, len(sites))


# NB: it is important for this to be fast since it is inside an inner loop
def get_probability_no_exceedance(
        rupture, sctx, rctx, dctx, imtls, gsims, trunclevel):
    """
    :param rupture: a Rupture instance
    :param sctx: the corresponding SiteContext instance
    :param rctx: the corresponding RuptureContext instance
    :param dctx: the corresponding DistanceContext instance
    :param imtls: a dictionary-like object providing the intensity levels
    :param gsims: the list of GSIMs to use
    :param trunclevel: the truncation level
    :returns: an array of shape (num_sites, num_levels, num_gsims)
    """
    pne_array = numpy.zeros((len(sctx.sites), len(imtls.array), len(gsims)))
    for i, gsim in enumerate(gsims):
        pnos = []  # list of arrays nsites x nlevels
        for imt in imtls:
            poes = gsim.get_poes(
                sctx, rctx, dctx, from_string(imt), imtls[imt], trunclevel)
            pnos.append(rupture.get_probability_no_exceedance(poes))
        pne_array[:, :, i] = numpy.concatenate(pnos, axis=1)
    return pne_array


def poe_map(src, s_sites, imtls, cmaker, trunclevel, bbs, rup_indep,
            ctx_mon, pne_mon, disagg_mon):
    """
    Compute the ProbabilityMap generated by the given source. Also,
    store some information in the monitors and optionally in the
    bounding boxes.
    """
    pmap = ProbabilityMap.build(
        len(imtls.array), len(cmaker.gsims), s_sites.sids, initvalue=rup_indep)
    try:
        for rup, weight in rupture_weight_pairs(src):
            with ctx_mon:  # compute distances
                try:
                    sctx, rctx, dctx = cmaker.make_contexts(s_sites, rup)
                except FarAwayRupture:
                    continue
            with pne_mon:  # compute probabilities and updates the pmap
                pnes = get_probability_no_exceedance(
                    rup, sctx, rctx, dctx, imtls, cmaker.gsims, trunclevel)
                for sid, pne in zip(sctx.sites.sids, pnes):
                    if rup_indep:
                        pmap[sid].array *= pne
                    else:
                        pmap[sid].array += pne * weight
            # add optional disaggregation information (bounding boxes)
            if bbs:
                with disagg_mon:
                    sids = set(sctx.sites.sids)
                    jb_dists = dctx.rjb
                    closest_points = rup.surface.get_closest_points(
                        sctx.sites.mesh)
                    bs = [bb for bb in bbs if bb.site_id in sids]
                    # NB: the assert below is always true; we are
                    # protecting against possible refactoring errors
                    assert len(bs) == len(jb_dists) == len(closest_points)
                    for bb, dist, p in zip(bs, jb_dists, closest_points):
                        bb.update([dist], [p.longitude], [p.latitude])
    except Exception as err:
        etype, err, tb = sys.exc_info()
        msg = 'An error occurred with source id=%s. Error: %s'
        msg %= (src.source_id, str(err))
        raise_(etype, msg, tb)
    return ~pmap


# this is used by the engine
def pmap_from_grp(
        sources, sites, imtls, gsims, truncation_level=None,
        source_site_filter='SourceSitesFilter', maximum_distance=None, bbs=(),
        monitor=Monitor()):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns: a ProbabilityMap instance
    """
    if source_site_filter == 'SourceSitesFilter':  # default
        source_site_filter = (
            filters.SourceSitesFilter(maximum_distance)
            if maximum_distance else filters.source_site_noop_filter)

    if isinstance(sources, SourceGroup):
        group = sources
        sources = group.src_list
    else:
        group = SourceGroup(sources, '', 'indep', 'indep')
        sources = group.src_list

    # check all the sources belong to the same tectonic region
    trts = set(src.tectonic_region_type for src in sources)
    assert len(trts) == 1, 'Multiple TRTs: %s' % ', '.join(trts)

    with GroundShakingIntensityModel.forbid_instantiation():
        imtls = DictArray(imtls)
        cmaker = ContextMaker(gsims, maximum_distance)
        ctx_mon = monitor('making contexts', measuremem=False)
        pne_mon = monitor('computing poes', measuremem=False)
        disagg_mon = monitor('get closest points', measuremem=False)
        monitor.calc_times = []  # pairs (src_id, delta_t)
        src_indep = group.src_interdep == 'indep'
        pmap = ProbabilityMap(len(imtls.array), len(gsims))
        for src, s_sites in source_site_filter(sources, sites):
            t0 = time.time()
            poemap = poe_map(
                src, s_sites, imtls, cmaker, truncation_level, bbs,
                group.rup_interdep == 'indep', ctx_mon, pne_mon, disagg_mon)
            if src_indep:  # usual composition of probabilities
                pmap |= poemap
            else:  # mutually exclusive probabilities
                weight = float(group.srcs_weights[src.source_id])
                for sid in poemap:
                    pmap[sid] += poemap[sid] * weight
                # we are attaching the calculation times to the monitor
                # so that the engine can store them
                monitor.calc_times.append(
                    (src.source_id, len(s_sites), time.time() - t0))
        monitor.eff_ruptures = pne_mon.counts  # contributing ruptures
        return pmap


def calc_hazard_curves_ext(
        groups, sites, imtls, gsim_by_trt, truncation_level=None,
        source_site_filter=filters.source_site_noop_filter,
        maximum_distance=None):
    """
    Compute hazard curves on a list of sites, given a set of seismic source
    groups and a dictionary of ground shaking intensity models (one per
    tectonic region type).

    Probability of ground motion exceedance is computed in different ways
    depending if the sources are independent or mutually exclusive.

    :param group:
        A sequence of groups of seismic sources objects (instances of
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param sites:
        Instance of :class:`~openquake.hazardlib.site.SiteCollection` object,
        representing sites of interest.
    :param imtls:
        Dictionary mapping intensity measure type strings
        to lists of intensity measure levels.
    :param gsim_by_trt:
        Dictionary mapping tectonic region types (members
        of :class:`openquake.hazardlib.const.TRT`) to
        :class:`~openquake.hazardlib.gsim.base.GMPE` or
        :class:`~openquake.hazardlib.gsim.base.IPE` objects.
    :param truncation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.
    :param source_site_filter:
        Optional source-site filter function. See
        :mod:`openquake.hazardlib.calc.filters`.
    :param maximum_distance:
        The integration distance, if any
    :returns:
        An array of size N, where N is the number of sites, which elements
        are records with fields given by the intensity measure types; the
        size of each field is given by the number of levels in ``imtls``.
    """
    # This is ensuring backward compatibility i.e. processing a list of
    # sources.
    if not isinstance(groups, SourceGroupCollection):
        group_tmp = SourceGroup(groups, 1, 'indep', 'indep')
        groups = SourceGroupCollection([group_tmp])

    imtls = DictArray(imtls)
    pmap = ProbabilityMap(len(imtls.array), 1)
    # Processing groups
    for group in groups.grp_list:
        indep = group.src_interdep == 'indep'
        # Prepare a dictionary
        sources_by_trt = collections.defaultdict(list)
        weights_by_trt = collections.defaultdict(dict)
        # Fill the dictionary with sources for the different tectonic regions
        # belonging to this group
        if indep:
            for src in group.src_list:
                sources_by_trt[src.tectonic_region_type].append(src)
                weights_by_trt[src.tectonic_region_type][src.source_id] = 1
        else:
            for src in group.src_list:
                sources_by_trt[src.tectonic_region_type].append(src)
                w = group.srcs_weights[src.source_id]
                weights_by_trt[src.tectonic_region_type][src.source_id] = w
        # Aggregate results. Note that for now we assume that source groups
        # are independent.
        for trt in sources_by_trt:
            gsim = gsim_by_trt[trt]
            # Create a temporary group
            tmp_group = SourceGroup(sources_by_trt[trt],
                                    'temp',
                                    group.src_interdep,
                                    group.rup_interdep,
                                    weights_by_trt[trt].values(),
                                    False)
            if indep:
                pmap |= pmap_from_grp(
                    tmp_group, sites, imtls, [gsim],
                    truncation_level, source_site_filter)
            else:
                # since in this case the probability for each source have
                # been already accounted, we use a weight equal to unity
                pmap += pmap_from_grp(
                    tmp_group, sites, imtls, [gsim],
                    truncation_level, source_site_filter)
    return pmap.convert(imtls, len(sites.complete))
