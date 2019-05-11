# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
       csm = readinput.get_composite_source_model(oq, srcfilter=src_filter)
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

import sys
import time
import operator
import numpy
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import sequential_apply
from openquake.baselib.general import DictArray, groupby, AccumDict
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.tom import FatedTOM


def _cluster(param, tom, imtls, gsims, grp_ids, pmap):
    """
    Computes the probability map in case of a cluster group
    """
    pmapclu = AccumDict({grp_id: ProbabilityMap(len(imtls.array), len(gsims))
                         for grp_id in grp_ids})
    # Get temporal occurrence model
    # Number of occurrences for the cluster
    first = True
    for nocc in range(0, 50):
        # TODO fix this once the occurrence rate will be used just as
        # an object attribute
        ocr = tom.occurrence_rate
        prob_n_occ = tom.get_probability_n_occurrences(ocr, nocc)
        if first:
            pmapclu = prob_n_occ * (~pmap)**nocc
            first = False
        else:
            pmapclu += prob_n_occ * (~pmap)**nocc
    pmap = ~pmapclu
    return pmap


def classical(group, src_filter, gsims, param, monitor=Monitor()):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns:
        a dictionary {grp_id: pmap} with attributes .grp_ids, .calc_times,
        .eff_ruptures
    """
    if not hasattr(src_filter, 'sitecol'):  # a sitecol was passed
        src_filter = SourceFilter(src_filter, {})

    # Get the parameters assigned to the group
    src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
    rup_mutex = getattr(group, 'rup_interdep', None) == 'mutex'
    cluster = getattr(group, 'cluster', None)
    # Compute the number of ruptures
    grp_ids = set()
    for src in group:
        if not src.num_ruptures:
            # src.num_ruptures is set when parsing the XML, but not when
            # the source is instantiated manually, so it is set here
            src.num_ruptures = src.count_ruptures()
        # This sets the proper TOM in case of a cluster
        if cluster:
            src.temporal_occurrence_model = FatedTOM(time_span=1)
        # Updating IDs
        grp_ids.update(src.src_group_ids)
    # Now preparing context
    maxdist = src_filter.integration_distance
    imtls = param['imtls']
    trunclevel = param.get('truncation_level')
    cmaker = ContextMaker(
        src.tectonic_region_type, gsims, maxdist, param, monitor)
    # Prepare the accumulator for the probability maps
    pmap = AccumDict({grp_id: ProbabilityMap(len(imtls.array), len(gsims))
                      for grp_id in grp_ids})
    rupdata = {grp_id: [] for grp_id in grp_ids}
    # AccumDict of arrays with 2 elements weight, calc_time
    calc_times = AccumDict(accum=numpy.zeros(2, numpy.float32))
    eff_ruptures = AccumDict(accum=0)  # grp_id -> num_ruptures
    nsites = {}  # src.id -> num_sites
    # Computing hazard
    for src, s_sites in src_filter(group):  # filter now
        nsites[src.id] = src.nsites
        t0 = time.time()
        try:
            poemap = cmaker.poe_map(src, s_sites, imtls, trunclevel,
                                    rup_indep=not rup_mutex)
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = '%s (source id=%s)' % (str(err), src.source_id)
            raise etype(msg).with_traceback(tb)
        if src_mutex:  # mutex sources, there is a single group
            for sid in poemap:
                pcurve = pmap[src.src_group_id].setdefault(sid, 0)
                pcurve += poemap[sid] * src.mutex_weight
        elif poemap:
            for gid in src.src_group_ids:
                pmap[gid] |= poemap
        if len(cmaker.rupdata):
            for gid in src.src_group_ids:
                rupdata[gid].append(cmaker.rupdata)
        calc_times[src.id] += numpy.array([src.weight, time.time() - t0])
        # storing the number of contributing ruptures too
        eff_ruptures += {gid: getattr(poemap, 'eff_ruptures', 0)
                         for gid in src.src_group_ids}
    # Updating the probability map in the case of mutually exclusive
    # sources
    group_probability = getattr(group, 'grp_probability', None)
    if src_mutex and group_probability:
        pmap[src.src_group_id] *= group_probability
    # Processing cluster
    if cluster:
        tom = getattr(group, 'temporal_occurrence_model')
        pmap = _cluster(param, tom, imtls, gsims, grp_ids, pmap)
    # Return results
    for gid, data in rupdata.items():
        if len(data):
            rupdata[gid] = numpy.concatenate(data)
    return dict(pmap=pmap, calc_times=calc_times, eff_ruptures=eff_ruptures,
                rup_data=rupdata, nsites=nsites)


def calc_hazard_curves(
        groups, ss_filter, imtls, gsim_by_trt, truncation_level=None,
        apply=sequential_apply, filter_distance='rjb', reqv=None):
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
    :param apply:
        apply function to use (default sequential_apply)
    :param filter_distance:
        The distance used to filter the ruptures (default rjb)
    :param reqv:
        If not None, an instance of RjbEquivalent
    :returns:
        An array of size N, where N is the number of sites, which elements
        are records with fields given by the intensity measure types; the
        size of each field is given by the number of levels in ``imtls``.
    """
    # This is ensuring backward compatibility i.e. processing a list of
    # sources
    if not isinstance(groups[0], SourceGroup):  # sent a list of sources
        odic = groupby(groups, operator.attrgetter('tectonic_region_type'))
        groups = [SourceGroup(trt, odic[trt], 'src_group', 'indep', 'indep')
                  for trt in odic]
    # ensure the sources have the right src_group_id
    for i, grp in enumerate(groups):
        for src in grp:
            if src.src_group_id is None:
                src.src_group_id = i
    imtls = DictArray(imtls)
    param = dict(imtls=imtls, truncation_level=truncation_level,
                 filter_distance=filter_distance, reqv=reqv,
                 cluster=grp.cluster)
    pmap = ProbabilityMap(len(imtls.array), 1)
    # Processing groups with homogeneous tectonic region
    gsim = gsim_by_trt[groups[0][0].tectonic_region_type]
    mon = Monitor()
    for group in groups:
        if group.atomic:  # do not split
            it = [classical(group, ss_filter, [gsim], param, mon)]
        else:  # split the group and apply `classical` in parallel
            it = apply(
                classical, (group.sources, ss_filter, [gsim], param, mon),
                weight=operator.attrgetter('weight'))
        for dic in it:
            for grp_id, pval in dic['pmap'].items():
                pmap |= pval
    sitecol = getattr(ss_filter, 'sitecol', ss_filter)
    return pmap.convert(imtls, len(sitecol.complete))
