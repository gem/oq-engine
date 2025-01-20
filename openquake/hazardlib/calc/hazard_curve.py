# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
       with logs.init(job_ini) as log:
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
from openquake.hazardlib.map_array import MapArray
from openquake.hazardlib.contexts import ContextMaker, PmapMaker
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.sourceconverter import SourceGroup


def classical(group, sitecol, cmaker):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns:
        a dictionary with keys pmap, source_data, rup_data, extra
    """
    src_filter = SourceFilter(sitecol, cmaker.maximum_distance)
    trts = set()
    for src in group:
        if not src.num_ruptures:
            # src.num_ruptures may not be set, so it is set here
            src.num_ruptures = src.count_ruptures()
        trts.add(src.tectonic_region_type)
    [trt] = trts  # there must be a single tectonic region type
    if cmaker.trt != '*':
        assert trt == cmaker.trt, (trt, cmaker.trt)
    dic = PmapMaker(cmaker, src_filter, group).make()
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
                 investigation_time=span, af=None)
    # Processing groups with homogeneous tectonic region
    mon = Monitor()
    sitecol = getattr(srcfilter, 'sitecol', srcfilter)
    pmap = MapArray(sitecol.sids, imtls.size, 1).fill(0)
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
            rmap = dic['rmap']
            pmap.array[:] = 1. - (1.-pmap.array) * numpy.exp(-rmap.array)
    return pmap.convert(imtls, len(sitecol.complete))


# called in adv-manual/developing.rst and in SingleSiteOptTestCase
def calc_hazard_curve(site1, src, gsims, oqparam, monitor=Monitor()):
    """
    :param site1: site collection with a single site
    :param src: a seismic source object
    :param gsims: a list of GSIM objects
    :param oqparam: an object with attributes .maximum_distance, .imtls
    :param monitor: a Monitor instance (optional)
    :returns: an array of shape (L, G)
    """
    assert len(site1) == 1, site1
    trt = src.tectonic_region_type
    cmaker = ContextMaker(trt, gsims, vars(oqparam), monitor)
    cmaker.tom = src.temporal_occurrence_model
    srcfilter = SourceFilter(site1, oqparam.maximum_distance)
    rmap = PmapMaker(cmaker, srcfilter, [src]).make()['rmap']
    return 1. - numpy.exp(-rmap.array[0])
