# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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

""":mod:`openquake.hazardlib.calc.hazard_curve` implements
:func:`calc_hazard_curves`. Here is an example of a classical PSHA
parallel calculator computing the hazard curves per each realization in less
than 20 lines of code:

.. code-block:: python

   import sys
   import logging
   from openquake.baselib import parallel
   from openquake.hazardlib.calc.filters import SourceFilter
   from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
   from openquake.commonlib import readinput

   def main(job_ini):
       logging.basicConfig(level=logging.INFO)
       oq = readinput.get_oqparam(job_ini)
       sitecol = readinput.get_site_collection(oq)
       src_filter = SourceFilter(sitecol, oq.maximum_distance)
       csm = readinput.get_composite_source_model(oq).filter(src_filter)
       rlzs_assoc = csm.info.get_rlzs_assoc()
       for i, sm in enumerate(csm.source_models):
           for rlz in rlzs_assoc.rlzs_by_smodel[i]:
               gsim_by_trt = rlzs_assoc.gsim_by_trt[rlz.ordinal]
               hcurves = calc_hazard_curves(
                   sm.src_groups, src_filter, oq.imtls,
                   gsim_by_trt, oq.truncation_level,
                   parallel.Starmap.apply)
           print('rlz=%s, hcurves=%s' % (rlz, hcurves))

   if __name__ == '__main__':
       main(sys.argv[1])  # path to a job.ini file

NB: the implementation in the engine is smarter and more
efficient. Here we start a parallel computation per each realization,
the engine manages all the realizations at once.
"""
from __future__ import division
import sys
import time
import operator
import numpy

from openquake.baselib.python3compat import raise_, zip
from openquake.baselib.performance import Monitor
from openquake.baselib.general import DictArray, groupby
from openquake.baselib.parallel import Sequential
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.gsim.base import GroundShakingIntensityModel
from openquake.hazardlib.calc.filters import SourceFilter, FarAwayRupture
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.sourceconverter import SourceGroup


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


# NB: it is important for this to be fast since it is inside an inner loop
def get_probability_no_exceedance(
        rupture, sctx, rctx, dctx, imtls, gsims, trunclevel, pne_mons):
    """
    :param rupture: a Rupture instance
    :param sctx: the corresponding SiteContext instance
    :param rctx: the corresponding RuptureContext instance
    :param dctx: the corresponding DistanceContext instance
    :param imtls: a dictionary-like object providing the intensity levels
    :param gsims: the list of GSIMs to use
    :param trunclevel: the truncation level
    :param pne_mons: monitors for the probability of no exceedance
    :returns: an array of shape (num_sites, num_levels, num_gsims)
    """
    pne_array = numpy.zeros((len(sctx.sites), len(imtls.array), len(gsims)))
    for i, gsim in enumerate(gsims):
        with pne_mons[i]:
            pnos = []  # list of arrays nsites x nlevels
            for imt in imtls:
                poes = gsim.get_poes(
                    sctx, rctx, dctx, from_string(imt), imtls[imt], trunclevel)
                pnos.append(rupture.get_probability_no_exceedance(poes))
            pne_array[:, :, i] = numpy.concatenate(pnos, axis=1)
    return pne_array


def poe_map(src, s_sites, imtls, cmaker, trunclevel, ctx_mon, pne_mons,
            bbs=(), rup_indep=True, disagg_mon=None):
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
            # compute probabilities and updates the pmap
            pnes = get_probability_no_exceedance(
                rup, sctx, rctx, dctx, imtls, cmaker.gsims, trunclevel,
                pne_mons)
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
        msg = '%s (source id=%s)' % (str(err), src.source_id)
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
    if isinstance(sources, SourceGroup):
        group = sources
        sources = group.sources
        trt = sources[0].tectonic_region_type
        mutex_weight = {src.source_id: weight for src, weight in
                        zip(group.sources, group.srcs_weights)}
    else:  # list of sources
        trt = sources[0].tectonic_region_type
        group = SourceGroup(trt, sources, 'src_group', 'indep', 'indep')
    grp_id = sources[0].src_group_id
    maxdist = source_site_filter.integration_distance
    if hasattr(gsims, 'keys'):  # dictionary trt -> gsim
        gsims = [gsims[trt]]
    srcs = []
    for src in sources:
        if hasattr(src, '__iter__'):  # MultiPointSource
            srcs.extend(src)
        else:
            srcs.append(src)
    del sources
    with GroundShakingIntensityModel.forbid_instantiation():
        imtls = DictArray(imtls)
        cmaker = ContextMaker(gsims, maxdist)
        ctx_mon = monitor('making contexts', measuremem=False)
        pne_mons = [monitor('%s.get_poes' % gsim, measuremem=False)
                    for gsim in gsims]
        disagg_mon = monitor('get closest points', measuremem=False)
        src_indep = group.src_interdep == 'indep'
        pmap = ProbabilityMap(len(imtls.array), len(gsims))
        pmap.calc_times = []  # pairs (src_id, delta_t)
        pmap.grp_id = grp_id
        for src, s_sites in source_site_filter(srcs):
            t0 = time.time()
            poemap = poe_map(
                src, s_sites, imtls, cmaker, truncation_level, ctx_mon,
                pne_mons, bbs, group.rup_interdep == 'indep', disagg_mon)
            if src_indep:  # usual composition of probabilities
                pmap |= poemap
            else:  # mutually exclusive probabilities
                weight = mutex_weight[src.source_id]
                for sid in poemap:
                    pcurve = pmap.setdefault(sid, 0)
                    pcurve += poemap[sid] * weight
            pmap.calc_times.append(
                (src.source_id, len(s_sites), time.time() - t0))
        # storing the number of contributing ruptures too
        pmap.eff_ruptures = {pmap.grp_id: pne_mons[0].counts}
        if group.grp_probability is not None:
            return pmap * group.grp_probability
        return pmap


def calc_hazard_curves(
        groups, ss_filter, imtls, gsim_by_trt, truncation_level=None,
        apply=Sequential.apply):
    """
    Compute hazard curves on a list of sites, given a set of seismic source
    groups and a dictionary of ground shaking intensity models (one per
    tectonic region type).

    Probability of ground motion exceedance is computed in different ways
    depending if the sources are independent or mutually exclusive.

    :param groups:
        A sequence of groups of seismic sources objects (instances of
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param ss_filter:
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
    :param maximum_distance:
        The integration distance, if any
    :returns:
        An array of size N, where N is the number of sites, which elements
        are records with fields given by the intensity measure types; the
        size of each field is given by the number of levels in ``imtls``.
    """
    # This is ensuring backward compatibility i.e. processing a list of
    # sources
    if not isinstance(groups[0], SourceGroup):  # sent a list of sources
        dic = groupby(groups, operator.attrgetter('tectonic_region_type'))
        groups = [SourceGroup(trt, dic[trt], 'src_group', 'indep', 'indep')
                  for trt in dic]
    if hasattr(ss_filter, 'sitecol'):  # a filter, as it should be
        sitecol = ss_filter.sitecol
    else:  # backward compatibility, a site collection was passed
        sitecol = ss_filter
        ss_filter = SourceFilter(sitecol, {})

    imtls = DictArray(imtls)
    pmap = ProbabilityMap(len(imtls.array), 1)
    # Processing groups with homogeneous tectonic region
    for group in groups:
        if group.src_interdep == 'mutex':  # do not split the group
            pmap |= pmap_from_grp(
                group, ss_filter, imtls, gsim_by_trt, truncation_level)
        else:  # split the group and apply `pmap_from_grp` in parallel
            pmap |= apply(
                pmap_from_grp,
                (group, ss_filter, imtls, gsim_by_trt, truncation_level),
                weight=operator.attrgetter('weight')).reduce(operator.or_)
    return pmap.convert(imtls, len(sitecol.complete))
