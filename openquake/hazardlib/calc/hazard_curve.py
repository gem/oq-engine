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


def get_weights(source):
    """
    :returns: an array of nr weights, where nr is the number of ruptures

    If the source has no weigths, builds an array of uniform weights,
    each one with a value of 1 / nr, so that that total sum is 1.
    """
    try:
        return source.weights
    except AttributeError:
        nr = source.count_ruptures()
        return numpy.ones(nr) / nr


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


def agg_curves(acc, curves):
    """
    Aggregate hazard curves by composing the probabilities.

    :param acc: an accumulator array
    :param curves: an array of hazard curves
    :returns: a new accumulator
    """
    new = numpy.array(acc)  # copy of the accumulator
    for imt in curves.dtype.fields:
        new[imt] = 1. - (1. - curves[imt]) * (1. - acc[imt])
    return new


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
        for rup, weight in zip(src.iter_ruptures(), get_weights(src)):
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

    # Check that the all the sources belong to the same tectonic region
    trts = set(src.tectonic_region_type for src in sources)
    assert len(trts) == 1, 'Multiple TRTs: %s' % ', '.join(trts)

    src_indep = group.src_interdep == 'indep'
    with GroundShakingIntensityModel.forbid_instantiation():
        imtls = DictArray(imtls)
        cmaker = ContextMaker(gsims, maximum_distance)
        ctx_mon = monitor('making contexts', measuremem=False)
        pne_mon = monitor('computing poes', measuremem=False)
        disagg_mon = monitor('get closest points', measuremem=False)
        monitor.calc_times = []  # pairs (src_id, delta_t)
        pmap = ProbabilityMap(len(imtls.array), len(gsims))
        for src, s_sites in source_site_filter(sources, sites):
            t0 = time.time()
        poemap = poe_map(src, s_sites, imtls, cmaker, truncation_level, bbs,
                         group.rup_interdep == 'indep',
                         ctx_mon, pne_mon, disagg_mon)
        if src_indep:
            pmap |= poemap
        else:  # mutually exclusive probabilities
            weight = float(group.srcs_weights[src.source_id])
            for sid in poemap:
                pmap[sid] += poemap[sid] * weight
            # we are attaching the calculation times to the monitor
            # so that oq-lite (and the engine) can store them
            monitor.calc_times.append(
                (src.source_id, len(s_sites), time.time() - t0))
            # NB: source.id is an integer; it should not be confused
            # with source.source_id, which is a string
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
    pmap = ProbabilityMap()
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
                # in this case this is a dummy variable
                weights_by_trt[src.tectonic_region_type][src.source_id] = 1.0
        else:
            for src in group.src_list:
                sources_by_trt[src.tectonic_region_type].append(src)
                wei = group.srcs_weights[src.source_id]
                weights_by_trt[src.tectonic_region_type][src.source_id] = wei
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
                # Since in this case the probability for each source have
                # been already accounted we use a weight equal to unity
                pmap += pmap_from_grp(
                    tmp_group, sites, imtls, [gsim],
                    truncation_level, source_site_filter)
    return array_of_curves(pmap, len(sites), imtls)

# #########################################################################
# original implementation by Marco, to be removed if the new one is correct
# #########################################################################


def _init_curves(num_sites, imtls, interdep='indep'):
    """
    :param num_sites: the number of sites
    :param imtls: the intensity measure levels dictionary
    :returns: an array of zero curves with length num_sites
    """
    # numpy dtype for the hazard curves
    imt_dt = numpy.dtype([(imt, float, 1 if imls is None else len(imls))
                          for imt, imls in imtls.items()])
    if interdep == 'indep':
        zero = numpy.zeros(num_sites, imt_dt)
    else:
        zero = numpy.ones(num_sites, imt_dt)
    return zero


def agg_curves_mutex(acc, curves, weight):
    """
    Aggregate hazard curves by composing the probabilities. Probabilities
    here are mutually exclusive.

    :param acc: an accumulator array
    :param curves: an array of hazard curves
    :returns: a new accumulator
    """
    new = numpy.array(acc)  # copy of the accumulator
    for imt in curves.dtype.fields:
        new[imt] = 1. - (1. - curves[imt]) * weight + (1. - acc[imt])
    return new


def _hazard_curves_per_group(
        group, sites, imtls, gsims, truncation_level=None,
        source_site_filter=filters.source_site_noop_filter,
        maximum_distance=None, bbs=(), monitor=Monitor()):
    """
    Compute the hazard curves for a set of sources belonging to the same
    source group. We assume that the group contains sources belonging to the
    same tectonic region.
    The arguments are the same as in :func:`pmap_from_grp`, except
    for ``group``, which can be either a :class:`SourceGroup` instance or
    a list of seismic sources (instances of subclasses of
    :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).

    :returns:
        A list of G arrays of size N, where N is the number of sites and
        G the number of gsims. Each array contains records with fields given
        by the intensity measure types; the size of each field is given by the
        number of levels in ``imtls``.
    """
    # Get source list
    if not isinstance(group, SourceGroup):
        sources = group
        group = SourceGroup(group, '', 'indep', 'indep')
    else:
        sources = group.src_list
    # Check that the all the sources belong to the same tectonic region
    assert len(set([src.tectonic_region_type for src in sources])) == 1
    # Prepare
    cmaker = ContextMaker(gsims, maximum_distance)
    gnames = list(map(str, gsims))
    imt_dt = numpy.dtype([(imt, float, len(imtls[imt]))
                         for imt in sorted(imtls)])
    imts = {from_string(imt): imls for imt, imls in imtls.items()}
    sources_sites = ((source, sites) for source in sources)
    ctx_mon = monitor('making contexts', measuremem=False)
    pne_mon = monitor('computing poes', measuremem=False)
    monitor.calc_times = []  # pairs (src_id, delta_t)
    # Initialise temporary accumulator for the probability of non-exceedance
    if group.src_interdep == 'indep':
        tc_gru = [numpy.ones(len(sites), imt_dt) for gname in gnames]
    else:
        tc_gru = [numpy.zeros(len(sites), imt_dt) for gname in gnames]
    tot_wei = 0.0
    # Computing contributions by all the sources
    for source, s_sites in source_site_filter(sources_sites):
        t0 = time.time()
        # Initialise temporary accumulator for the probability of
        # non-exceedance
        if group.rup_interdep == 'indep':
            tc_src = [numpy.ones(len(sites), imt_dt) for gname in gnames]
        else:
            tc_src = [numpy.zeros(len(sites), imt_dt) for gname in gnames]
        # Set weights
        weights = get_weights(source)
        # Processing ruptures
        try:
            for cnt, rupture in enumerate(source.iter_ruptures()):
                with ctx_mon:
                    try:
                        sctx, rctx, dctx = cmaker.make_contexts(
                            s_sites, rupture)
                    except FarAwayRupture:
                        continue
                    # add optional disaggregation information (bounding boxes)
                    if bbs:
                        sids = set(sctx.sites.sids)
                        jb_dists = dctx.rjb
                        closest_points = rupture.surface.get_closest_points(
                            sctx.sites.mesh)
                        bs = [bb for bb in bbs if bb.site_id in sids]
                        # NB: the assert below is always true; we are
                        # protecting against possible refactoring errors
                        assert len(bs) == len(jb_dists) == len(closest_points)
                        for bb, dist, p in zip(bs, jb_dists, closest_points):
                            bb.update([dist], [p.longitude], [p.latitude])
                for i, gsim in enumerate(gsims):
                    with pne_mon:
                        for imt in imts:
                            poes = gsim.get_poes(
                                sctx, rctx, dctx, imt, imts[imt],
                                truncation_level)
                            pno = rupture.get_probability_no_exceedance(poes)
                            # Updating the probability of non-exceedance
                            expanded_pno = sctx.sites.expand(pno, 1.0)
                            if group.rup_interdep is 'indep':
                                tc_src[i][str(imt)] *= expanded_pno
                            else:
                                tc_src[i][str(imt)] += (expanded_pno *
                                                        weights[cnt])

            # Updating the probability of non-exceedance for all the sources
            # in the group
            for i, gsim in enumerate(gsims):
                if group.src_interdep is 'indep':
                    for imt in imtls:
                        tc_gru[i][str(imt)] *= tc_src[i][str(imt)]
                else:
                    for imt in imtls:
                        tc_gru[i][str(imt)] += (
                            tc_src[i][str(imt)] *
                            float(group.srcs_weights[source.source_id]))
                        tot_wei += float(group.srcs_weights[source.source_id])
            del tc_src

        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, str(err))
            raise_(etype, msg, tb)

        # we are attaching the calculation times to the monitor
        # so that oq-lite (and the engine) can store them
        monitor.calc_times.append((source.id, time.time() - t0))
        # NB: source.id is an integer; it should not be confused
        # with source.source_id, which is a string

    # Finally we get the probability of exceedance
    for i in range(len(gnames)):
        for imt in imtls:
            tc_gru[i][imt] = 1. - tc_gru[i][imt]

    return tc_gru


def _calc_hazard_curves_ext(
        groups, sites, imtls, gsim_by_trt, truncation_level=None,
        source_site_filter=filters.source_site_noop_filter,
        maximum_distance=None):
    """
    """
    # This is ensuring backward compatibility i.e. processing a list of
    # sources.
    if not isinstance(groups, SourceGroupCollection):
        group_tmp = SourceGroup(groups, 1, 'indep', 'indep')
        groups = SourceGroupCollection([group_tmp])
    # Initialise the curves accumulator
    curves_fin = _init_curves(len(sites), imtls)
    # Processing groups
    for group in groups.grp_list:
        # Prepare a dictionary
        sources_by_trt = collections.defaultdict(list)
        weights_by_trt = collections.defaultdict(dict)
        # Fill the dictionary with sources for the different tectonic regions
        # belonging to this group
        if group.src_interdep is 'indep':
            for src in group.src_list:
                sources_by_trt[src.tectonic_region_type].append(src)
                # in this case this is a dummy variable
                weights_by_trt[src.tectonic_region_type][src.source_id] = 1.0
        else:
            for src in group.src_list:
                sources_by_trt[src.tectonic_region_type].append(src)
                wei = group.srcs_weights[src.source_id]
                weights_by_trt[src.tectonic_region_type][src.source_id] = wei
        # Initialise the curves accumulator
        curves = _init_curves(len(sites), imtls, group.src_interdep)
        # Aggregate results. Note that for now we assume that source groups
        # are independent.
        for trt in sources_by_trt:
            # Create a temporary group
            tmp_group = SourceGroup(sources_by_trt[trt],
                                    'temp',
                                    group.src_interdep,
                                    group.rup_interdep,
                                    weights_by_trt[trt],
                                    False)
            # Compute curves
            if group.src_interdep == 'indep':
                curves = agg_curves(curves, _hazard_curves_per_group(
                    tmp_group, sites, imtls, [gsim_by_trt[trt]],
                    truncation_level, source_site_filter)[0])
            else:
                # Since in this case the probability for each source have
                # been already accounted we use a weight equal to unity
                curves = agg_curves_mutex(curves, _hazard_curves_per_group(
                    tmp_group, sites, imtls, [gsim_by_trt[trt]],
                    truncation_level, source_site_filter)[0], 1.0)
        # Final aggregation
        curves_fin = agg_curves(curves_fin, curves)
    return curves_fin


