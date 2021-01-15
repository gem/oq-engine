# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
   from openquake.commonlib import logs
   from openquake.calculators.base import get_calc

   def main(job_ini):
       calc_id = logs.init()
       calc = get_calc(job_ini, calc_id)
       calc.run(individual_curves='true', shutdown=True)
       print('The hazard curves are in %s::/hcurves-rlzs'
             % calc.datastore.filename)

   if __name__ == '__main__':
       main(sys.argv[1])  # path to a job.ini file

NB: the implementation in the engine is smarter and more
efficient. Here we start a parallel computation per each realization,
the engine manages all the realizations at once.
"""

import operator
import numpy
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import sequential_apply
from openquake.baselib.general import DictArray, groupby
from openquake.hazardlib.probability_map import (
    ProbabilityMap, ProbabilityCurve)
from openquake.hazardlib.gsim.base import ContextMaker, PmapMaker
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.tom import FatedTOM


def _cluster(imtls, tom, gsims, pmap):
    """
    Computes the probability map in case of a cluster group
    """
    L, G = imtls.size, len(gsims)
    pmapclu = ProbabilityMap(L, G)
    # Get temporal occurrence model
    # Number of occurrences for the cluster
    first = True
    for nocc in range(0, 50):
        # TODO fix this once the occurrence rate will be used just as
        # an object attribute
        ocr = tom.occurrence_rate
        prob_n_occ = tom.get_probability_n_occurrences(ocr, nocc)
        if first:
            pmapclu = (~pmap)**nocc * prob_n_occ
            first = False
        else:
            pmapclu += (~pmap)**nocc * prob_n_occ
    pmap = ~pmapclu
    return pmap


def classical(group, src_filter, gsims, param, monitor=Monitor()):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns:
        a dictionary with keys pmap, calc_times, rup_data, extra
    """
    if not hasattr(src_filter, 'sitecol'):  # do not filter
        src_filter = SourceFilter(src_filter, {})

    # Get the parameters assigned to the group
    src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
    cluster = getattr(group, 'cluster', None)
    trts = set()
    maxradius = 0
    for src in group:
        if not src.num_ruptures:
            # src.num_ruptures may not be set, so it is set here
            src.num_ruptures = src.count_ruptures()
        # set the proper TOM in case of a cluster
        if cluster:
            src.temporal_occurrence_model = FatedTOM(time_span=1)
        trts.add(src.tectonic_region_type)
        if hasattr(src, 'radius'):  # for prefiltered point sources
            maxradius = max(maxradius, src.radius)

    param['maximum_distance'] = src_filter.integration_distance
    [trt] = trts  # there must be a single tectonic region type
    cmaker = ContextMaker(trt, gsims, param, monitor)
    pmap, rup_data, calc_times = PmapMaker(cmaker, src_filter, group).make()
    extra = {}
    extra['task_no'] = getattr(monitor, 'task_no', 0)
    extra['trt'] = trt
    extra['source_id'] = src.source_id
    extra['grp_id'] = src.grp_id
    extra['maxradius'] = maxradius
    group_probability = getattr(group, 'grp_probability', None)
    if src_mutex and group_probability:
        pmap *= group_probability

    if cluster:
        tom = getattr(group, 'temporal_occurrence_model')
        pmap = _cluster(param['imtls'], tom, gsims, pmap)
    return dict(pmap=pmap, calc_times=calc_times,
                rup_data=rup_data, extra=extra)


# not used in the engine, only in tests and possibly notebooks
def calc_hazard_curves(
        groups, srcfilter, imtls, gsim_by_trt, truncation_level=None,
        apply=sequential_apply, reqv=None, **kwargs):
    """
    Compute hazard curves on a list of sites, given a set of seismic source
    groups and a dictionary of ground shaking intensity models (one per
    tectonic region type).

    Probability of ground motion exceedance is computed in different ways
    depending if the sources are independent or mutually exclusive.

    :param groups:
        A sequence of groups of seismic sources objects (instances of
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param srcfilter:
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
    # ensure the sources have the right et_id
    idx = 0
    for i, grp in enumerate(groups):
        for src in grp:
            if not hasattr(src, 'et_id'):
                src.et_id = i  # fix et_id
            src.grp_id = i
            src.id = idx
            idx += 1
    imtls = DictArray(imtls)
    shift_hypo = kwargs['shift_hypo'] if 'shift_hypo' in kwargs else False
    param = dict(imtls=imtls, truncation_level=truncation_level, reqv=reqv,
                 cluster=grp.cluster, shift_hypo=shift_hypo)
    pmap = ProbabilityMap(imtls.size, 1)
    # Processing groups with homogeneous tectonic region
    mon = Monitor()
    for group in groups:
        for src in group:
            if not src.nsites:  # not set
                src.nsites = 1
        gsim = gsim_by_trt[group[0].tectonic_region_type]
        if group.atomic:  # do not split
            it = [classical(group, srcfilter, [gsim], param, mon)]
        else:  # split the group and apply `classical` in parallel
            it = apply(
                classical, (group.sources, srcfilter, [gsim], param),
                weight=operator.attrgetter('weight'))
        for dic in it:
            pmap |= dic['pmap']
    sitecol = getattr(srcfilter, 'sitecol', srcfilter)
    return pmap.convert(imtls, len(sitecol.complete))


# called in adv-manual/developing.rst
def calc_hazard_curve(site1, src, gsims, oqparam):
    """
    :param site1: site collection with a single site
    :param src: a seismic source object
    :param gsims: a list of GSIM objects
    :param oqparam: an object with attributes .maximum_distance, .imtls
    :returns: a ProbabilityCurve object
    """
    assert len(site1) == 1, site1
    trt = src.tectonic_region_type
    cmaker = ContextMaker(trt, gsims, vars(oqparam))
    srcfilter = SourceFilter(site1, oqparam.maximum_distance)
    pmap, rup_data, calc_times = PmapMaker(cmaker, srcfilter, [src]).make()
    if not pmap:  # filtered away
        zero = numpy.zeros((oqparam.imtls.size, len(gsims)))
        return ProbabilityCurve(zero)
    return pmap[0]  # pcurve with shape (L, G) on site 0
