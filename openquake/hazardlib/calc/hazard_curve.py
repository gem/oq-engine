# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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
   from openquake.calculators.base import calculators

   def main(job_ini):
       with logs.init('job', job_ini) as log:
           calc = calculators(log.get_oqparam(), log.calc_id)
           calc.run(individual_rlzs='true', shutdown=True)
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
from openquake.hazardlib.probability_map import ProbabilityMap, ProbabilityCurve
from openquake.hazardlib.gsim.base import ContextMaker, PmapMaker
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.tom import PoissonTOM, FatedTOM


def _cluster(sids, imtls, tom, gsims, pmap):
    """
    Computes the probability map in case of a cluster group
    """
    for nocc in range(0, 50):
        ocr = tom.occurrence_rate
        prob_n_occ = tom.get_probability_n_occurrences(ocr, nocc)
        if nocc == 0:
            pmapclu = pmap.new(numpy.full(pmap.shape, prob_n_occ))
        else:
            pmapclu.array += (1.-pmap.array)**nocc * prob_n_occ
    return ~pmapclu


def classical(group, sitecol, cmaker, pmap=None):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns:
        a dictionary with keys pmap, source_data, rup_data, extra
    """
    not_passed_pmap = pmap is None
    src_filter = SourceFilter(sitecol, cmaker.maximum_distance)
    cluster = getattr(group, 'cluster', None)
    rup_indep = getattr(group, 'rup_interdep', None) != 'mutex'
    trts = set()
    for src in group:
        if not src.num_ruptures:
            # src.num_ruptures may not be set, so it is set here
            src.num_ruptures = src.count_ruptures()
        # set the proper TOM in case of a cluster
        if cluster:
            src.temporal_occurrence_model = FatedTOM(time_span=1)
        trts.add(src.tectonic_region_type)
    [trt] = trts  # there must be a single tectonic region type
    if cmaker.trt != '*':
        assert trt == cmaker.trt, (trt, cmaker.trt)
    cmaker.tom = getattr(group, 'temporal_occurrence_model', None)
    if cmaker.tom is None:
        time_span = cmaker.investigation_time  # None for nonparametric
        cmaker.tom = PoissonTOM(time_span) if time_span else None
    if cluster:
        cmaker.tom = FatedTOM(time_span=1)
    if not_passed_pmap:
        pmap = ProbabilityMap(
            sitecol.sids, cmaker.imtls.size, len(cmaker.gsims))
        pmap.fill(rup_indep)

    dic = PmapMaker(cmaker, src_filter, group).make(pmap)
    if getattr(group, 'src_interdep', None) != 'mutex' and rup_indep:
        pmap.array[:] = 1. - pmap.array
    if cluster:
        pmap.array[:] = _cluster(sitecol.sids, cmaker.imtls,
                                 group.temporal_occurrence_model,
                                 cmaker.gsims, pmap).array
    if not_passed_pmap:
        dic['pmap'] = pmap
    return dic


# not used in the engine, only in tests and possibly notebooks
def calc_hazard_curves(
        groups, srcfilter, imtls, gsim_by_trt, truncation_level=99.,
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
    idx = 0
    span = None
    for i, grp in enumerate(groups):
        for src in grp:
            tom = getattr(src, 'temporal_occurrence_model', None)
            span = tom.time_span if tom else kwargs['investigation_time']
            src.weight = src.count_ruptures()
            src.grp_id = i
            src.id = idx
            idx += 1
    imtls = DictArray(imtls)
    shift_hypo = kwargs['shift_hypo'] if 'shift_hypo' in kwargs else False
    param = dict(imtls=imtls, truncation_level=truncation_level, reqv=reqv,
                 cluster=grp.cluster, shift_hypo=shift_hypo,
                 investigation_time=span)
    # Processing groups with homogeneous tectonic region
    mon = Monitor()
    sitecol = getattr(srcfilter, 'sitecol', srcfilter)
    pmap = ProbabilityMap(sitecol.sids, imtls.size, 1).fill(0)
    for group in groups:
        trt = group.trt
        if sitecol is not srcfilter:
            param['maximum_distance'] = srcfilter.integration_distance(trt)
        cmaker = ContextMaker(trt, [gsim_by_trt[trt]], param, mon)
        if group.atomic:  # do not split
            it = [classical(group, sitecol, cmaker)]
        else:  # split the group and apply `classical` in parallel
            it = apply(
                classical, (group.sources, sitecol, cmaker),
                weight=operator.attrgetter('weight'))
        for dic in it:
            pmap.array[:] = 1. - (1.-pmap.array) * (1. - dic['pmap'].array)
    return pmap.convert(imtls, len(sitecol.complete))


# called in adv-manual/developing.rst and in SingleSiteOptTestCase
def calc_hazard_curve(site1, src, gsims, oqparam, monitor=Monitor()):
    """
    :param site1: site collection with a single site
    :param src: a seismic source object
    :param gsims: a list of GSIM objects
    :param oqparam: an object with attributes .maximum_distance, .imtls
    :param monitor: a Monitor instance (optional)
    :returns: a ProbabilityCurve object
    """
    assert len(site1) == 1, site1
    trt = src.tectonic_region_type
    cmaker = ContextMaker(trt, gsims, vars(oqparam), monitor)
    cmaker.tom = src.temporal_occurrence_model
    srcfilter = SourceFilter(site1, oqparam.maximum_distance)
    pmap = ProbabilityMap(site1.sids, oqparam.imtls.size, 1).fill(1)
    PmapMaker(cmaker, srcfilter, [src]).make(pmap)
    pmap.array[:] = 1. - pmap.array
    if not pmap:  # filtered away
        zero = numpy.zeros((oqparam.imtls.size, len(gsims)))
        return ProbabilityCurve(zero)
    return ProbabilityCurve(pmap.array[0])
