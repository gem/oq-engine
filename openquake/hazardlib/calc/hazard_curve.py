# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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
import time
import operator
import numpy
from openquake.baselib.python3compat import zip
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import sequential_apply
from openquake.baselib.general import DictArray, groupby, AccumDict
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.sourceconverter import SourceGroup


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
    if getattr(group, 'src_interdep', None) == 'mutex':
        mutex_weight = {src.source_id: weight for src, weight in
                        zip(group.sources, group.srcs_weights)}
    else:
        mutex_weight = None
    grp_ids = set()
    for src in group:
        grp_ids.update(src.src_group_ids)
    maxdist = src_filter.integration_distance
    imtls = param['imtls']
    trunclevel = param.get('truncation_level')
    cmaker = ContextMaker(gsims, maxdist, param['filter_distance'], monitor)
    pmap = AccumDict({grp_id: ProbabilityMap(len(imtls.array), len(gsims))
                      for grp_id in grp_ids})
    # AccumDict of arrays with 4 elements weight, nsites, calc_time, split
    pmap.calc_times = AccumDict(accum=numpy.zeros(4))
    pmap.eff_ruptures = AccumDict()  # grp_id -> num_ruptures
    for src, s_sites in src_filter(group):  # filter now
        t0 = time.time()
        indep = group.rup_interdep == 'indep' if mutex_weight else True
        poemap = cmaker.poe_map(src, s_sites, imtls, trunclevel, indep)
        if mutex_weight:  # mutex sources
            weight = mutex_weight[src.source_id]
            for sid in poemap:
                pcurve = pmap[group.id].setdefault(sid, 0)
                pcurve += poemap[sid] * weight
        elif poemap:
            for grp_id in src.src_group_ids:
                pmap[grp_id] |= poemap
        src_id = src.source_id.split(':', 1)[0]
        pmap.calc_times[src_id] += numpy.array(
            [src.weight, len(s_sites), time.time() - t0, 1])
        # storing the number of contributing ruptures too
        pmap.eff_ruptures += {grp_id: getattr(poemap, 'eff_ruptures', 0)
                              for grp_id in src.src_group_ids}
    if mutex_weight and group.grp_probability is not None:
        pmap[group.id] *= group.grp_probability
    return pmap


def calc_hazard_curves(
        groups, ss_filter, imtls, gsim_by_trt, truncation_level=None,
        apply=sequential_apply, filter_distance='rjb'):
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
        odic = groupby(groups, operator.attrgetter('tectonic_region_type'))
        groups = [SourceGroup(trt, odic[trt], 'src_group', 'indep', 'indep')
                  for trt in odic]
    for i, grp in enumerate(groups):
        for src in grp:
            if src.src_group_id is None:
                src.src_group_id = i
    if hasattr(ss_filter, 'sitecol'):  # a filter, as it should be
        sitecol = ss_filter.sitecol
    else:  # backward compatibility, a site collection was passed
        sitecol = ss_filter
        ss_filter = SourceFilter(sitecol, {})

    imtls = DictArray(imtls)
    param = dict(imtls=imtls, truncation_level=truncation_level,
                 filter_distance=filter_distance)
    pmap = ProbabilityMap(len(imtls.array), 1)
    # Processing groups with homogeneous tectonic region
    gsim = gsim_by_trt[groups[0][0].tectonic_region_type]
    mon = Monitor()
    for group in groups:
        if group.src_interdep == 'mutex':  # do not split the group
            it = [classical(group, ss_filter, [gsim], param, mon)]
        else:  # split the group and apply `classical` in parallel
            it = apply(
                classical, (group, ss_filter, [gsim], param, mon),
                weight=operator.attrgetter('weight'))
        for res in it:
            for grp_id in res:
                pmap |= res[grp_id]
    return pmap.convert(imtls, len(sitecol.complete))
