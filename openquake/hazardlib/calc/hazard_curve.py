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
import sys
import time
import operator
import functools
import multiprocessing
import numpy

from openquake.baselib.python3compat import raise_, zip
from openquake.baselib.performance import Monitor
from openquake.baselib.general import (
    DictArray, AccumDict, nokey, split_in_blocks, block_splitter)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib.gsim.base import GroundShakingIntensityModel
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.imt import from_string


def zero_curves(num_sites, imtls):
    """
    :param num_sites: the number of sites
    :param imtls: the intensity measure levels dictionary
    :returns: an array of zero curves with length num_sites
    """
    # numpy dtype for the hazard curves
    imt_dt = numpy.dtype([(imt, float, 1 if imls is None else len(imls))
                          for imt, imls in imtls.items()])
    zero = numpy.zeros(num_sites, imt_dt)
    return zero


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


class Apply(object):
    def __init__(self, task, task_args,
                 concurrent_tasks=multiprocessing.cpu_count(),
                 maxweight=None, weight=lambda item: 1,
                 key=nokey, name=None):
        self.task = task
        self.task_args = task_args
        self.concurrent_tasks = concurrent_tasks or 1
        self.maxweight = maxweight
        self.weight = weight
        self.key = nokey

    def __iter__(self):
        arg0 = self.task_args[0]
        args = self.task_args[1:]
        if self.maxweight:
            chunks = block_splitter(
                arg0, self.maxweight, self.weight, self.key)
        else:
            chunks = split_in_blocks(
                arg0, self.concurrent_tasks, self.weight, self.key)
        for chunk in chunks:
            yield self.task(*(chunk,) + args)

    def reduce(self, agg=operator.add, acc=None):
        return functools.reduce(
            agg, self, AccumDict() if acc is None else acc)


def calc_hazard_curves(
        sources, source_site_filter, imtls, gsim_by_trt,
        truncation_level=None, apply=Apply):
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
    :param source_site_filter:
        A source filter over the site collection or the site collection itself
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
    :param apply:
        Application function, for instance `parallel.apply`; by default use
        the sequential `apply`.

    :returns:
        An array of size N, where N is the number of sites, which elements
        are records with fields given by the intensity measure types; the
        size of each field is given by the number of levels in ``imtls``.
    """
    imtls = DictArray(imtls)
    if hasattr(source_site_filter, 'sitecol'):  # a filter, as it should be
        sites = source_site_filter.sitecol
    else:  # backward compatibility, a site collection was passed
        sites = source_site_filter
        source_site_filter = SourceFilter(sites, None)
    pmap = apply(
        pmap_from_grp, (sources, source_site_filter, imtls,
                        gsim_by_trt, truncation_level),
        weight=operator.attrgetter('weight'),
        key=operator.attrgetter('tectonic_region_type')
    ).reduce(operator.or_, ProbabilityMap(len(imtls.array), 1))
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


def poe_map(src, s_sites, imtls, cmaker, trunclevel, bbs,
            ctx_mon, pne_mon, disagg_mon):
    """
    Compute the ProbabilityMap generated by the given source. Also,
    store some information in the monitors and optionally in the
    bounding boxes.
    """
    pmap = ProbabilityMap.build(
        len(imtls.array), len(cmaker.gsims), s_sites.sids, initvalue=1.)
    try:
        for rup in src.iter_ruptures():
            with ctx_mon:  # compute distances
                try:
                    sctx, rctx, dctx = cmaker.make_contexts(s_sites, rup)
                except FarAwayRupture:
                    continue
            with pne_mon:  # compute probabilities and updates the pmap
                pnes = get_probability_no_exceedance(
                    rup, sctx, rctx, dctx, imtls, cmaker.gsims, trunclevel)
                for sid, pne in zip(sctx.sites.sids, pnes):
                    pmap[sid].array *= pne

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
        sources, source_site_filter, imtls, gsims, truncation_level=None,
        bbs=(), monitor=Monitor()):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns: a ProbabilityMap instance
    """
    trt = sources[0].tectonic_region_type
    try:
        maxdist = source_site_filter.integration_distance[trt]
    except:
        maxdist = source_site_filter.integration_distance
    if hasattr(gsims, 'keys'):
        gsims = [gsims[trt]]
    with GroundShakingIntensityModel.forbid_instantiation():
        imtls = DictArray(imtls)
        cmaker = ContextMaker(gsims, maxdist)
        ctx_mon = monitor('making contexts', measuremem=False)
        pne_mon = monitor('computing poes', measuremem=False)
        disagg_mon = monitor('get closest points', measuremem=False)
        pmap = ProbabilityMap(len(imtls.array), len(gsims))
        pmap.calc_times = []  # pairs (src_id, delta_t)
        pmap.grp_id = sources[0].src_group_id
        for src, s_sites in source_site_filter(sources):
            t0 = time.time()
            pmap |= poe_map(src, s_sites, imtls, cmaker, truncation_level, bbs,
                            ctx_mon, pne_mon, disagg_mon)
            # we are attaching the calculation times to the pmap
            # so that the engine can store them
            pmap.calc_times.append(
                (src.source_id, len(s_sites), time.time() - t0))
        # storing the number of contributing ruptures too
        pmap.eff_ruptures = {pmap.grp_id: pne_mon.counts}
        return pmap
