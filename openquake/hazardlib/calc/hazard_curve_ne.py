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

""":mod:`openquake.hazardlib.calc.hazard_curve_ne` implements
:func:`calc_hazard_curves`
"""

import operator
from openquake.hazardlib.contexts_ne import ContextMakerNonErgodic
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import sequential_apply
from openquake.baselib.general import DictArray, groupby
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib.tom import FatedTOM


def classical(group, src_filter, gsims, param, monitor=Monitor()):
    """
    Compute the hazard curves for a set of sources belonging to the same
    tectonic region type for all the GSIMs associated to that TRT.
    The arguments are the same as in :func:`calc_hazard_curves`, except
    for ``gsims``, which is a list of GSIM instances.

    :returns:
        a dictionary {grp_id: pmap} with attributes .grp_ids, .calc_times,
    """
    if not hasattr(src_filter, 'sitecol'):  # do not filter
        src_filter = SourceFilter(src_filter, {})
    # Get the parameters assigned to the group
    src_mutex = getattr(group, 'src_interdep', None) == 'mutex'
    rup_mutex = getattr(group, 'rup_interdep', None) == 'mutex'
    cluster = getattr(group, 'cluster', None)
    trts = set()
    # Set the number of ruptures, if missing, and fix the temporal occurrence
    # model in case of a cluster. Note that the probability of occurrence of
    # each source is set to one
    for src in group:
        if not src.num_ruptures:
            # src.num_ruptures is set when parsing the XML, but not when
            # the source is instantiated manually, so it is set here
            src.num_ruptures = src.count_ruptures()
        # set the proper TOM in case of a cluster
        if cluster:
            src.temporal_occurrence_model = FatedTOM(time_span=1)
        trts.add(src.tectonic_region_type)
    # Set the integration distance
    param['maximum_distance'] = src_filter.integration_distance
    [trt] = trts  # there must be a single tectonic region type
    # Create contexts. This is advantageous since we compute rupture to site
    # distances only once.
    cmaker = ContextMakerNonErgodic(trt, gsims, param, monitor)
    # Compute the probability map. The probability map is a
    # :class:`openquake.baselib.general.AccumDict` instance i.e. a specialised
    # dictionary
    pmap, pcec = cmaker.get_pmap_by_src(src_filter(group), src_mutex, rup_mutex)
    return pmap, pcec


def calc_hazard_curves(
        groups, srcfilter, imtls, gsim_by_trt, truncation_level=None,
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
    sitecol = getattr(srcfilter, 'sitecol', srcfilter)
    for group in groups:
        for src in group.sources:
            poemap, pcecff = classical([src], srcfilter, [gsim], param, mon)
            yield pcecff
