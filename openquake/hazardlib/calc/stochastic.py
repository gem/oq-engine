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

"""
:mod:`openquake.hazardlib.calc.stochastic` contains
:func:`stochastic_event_set`.
"""
import sys
import time
import operator
import collections
import numpy
from openquake.baselib.general import AccumDict
from openquake.baselib.performance import Monitor
from openquake.baselib.python3compat import raise_
from openquake.hazardlib.source.rupture import EBRupture
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture
from openquake.hazardlib.calc import filters

TWO32 = 2 ** 32  # 4,294,967,296
F64 = numpy.float64
U64 = numpy.uint64
U32 = numpy.uint32
U16 = numpy.uint16
event_dt = numpy.dtype([('eid', U64), ('grp_id', U16), ('ses', U32),
                        ('sample', U32)])


# this is used in acceptance/stochastic_test.py, not in the engine
def stochastic_event_set(
        sources, source_site_filter=filters.source_site_noop_filter):
    """
    Generates a 'Stochastic Event Set' (that is a collection of earthquake
    ruptures) representing a possible *realization* of the seismicity as
    described by a source model.

    The calculator loops over sources. For each source, it loops over ruptures.
    For each rupture, the number of occurrence is randomly sampled by
    calling
    :meth:`openquake.hazardlib.source.rupture.BaseProbabilisticRupture.sample_number_of_occurrences`

    .. note::
        This calculator is using random numbers. In order to reproduce the
        same results numpy random numbers generator needs to be seeded, see
        http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.seed.html

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~openquake.hazardlib.source.base.BaseSeismicSource`).
    :param source_site_filter:
        The source filter to use (default noop filter)
    :returns:
        Generator of :class:`~openquake.hazardlib.source.rupture.Rupture`
        objects that are contained in an event set. Some ruptures can be
        missing from it, others can appear one or more times in a row.
    """
    for source, s_sites in source_site_filter(sources):
        try:
            for rupture in source.iter_ruptures():
                for i in range(rupture.sample_number_of_occurrences()):
                    yield rupture
        except Exception as err:
            etype, err, tb = sys.exc_info()
            msg = 'An error occurred with source id=%s. Error: %s'
            msg %= (source.source_id, str(err))
            raise_(etype, msg, tb)


# ######################## rupture calculator ############################ #

def set_eids(ebruptures):
    """
    Set event IDs on the given list of ebruptures.

    :param ebruptures: a non-empty list of ruptures with the same grp_id
    :returns: the event IDs
    """
    if not ebruptures:
        return numpy.zeros(0)
    all_eids = []
    for ebr in ebruptures:
        assert ebr.multiplicity < TWO32, ebr.multiplicity
        eids = U64(TWO32 * ebr.serial) + numpy.arange(
            ebr.multiplicity, dtype=U64)
        ebr.events['eid'] = eids
        all_eids.extend(eids)
    return numpy.array(all_eids)


def sample_ruptures(group, src_filter, gsims, param, monitor=Monitor()):
    """
    :param group:
        a SourceGroup or a sequence of sources of the same group
    :param src_filter:
        a source site filter
    :param gsims:
        a list of GSIMs for the current tectonic region model
    :param param:
        a dictionary of additional parameters
    :param monitor:
        monitor instance
    :returns:
        a dictionary with eb_ruptures, num_events, num_ruptures, calc_times
    """
    if getattr(group, 'src_interdep', None) == 'mutex':
        prob = {src: sw for src, sw in zip(group, group.srcs_weights)}
    else:
        prob = {src: 1 for src in group}
    eb_ruptures = []
    calc_times = []
    rup_mon = monitor('making contexts', measuremem=False)
    # Compute and save stochastic event sets
    num_ruptures = 0
    eids = numpy.zeros(0)
    cmaker = ContextMaker(gsims, src_filter.integration_distance,
                          param['filter_distance'], monitor)
    for src, s_sites in src_filter(group):
        t0 = time.time()
        num_ruptures += src.num_ruptures
        num_occ_by_rup = _sample_ruptures(
            src, prob[src], param['ses_per_logic_tree_path'], group.samples,
            param['seed'])
        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_ruptures *before* the filtering
        for ebr in _build_eb_ruptures(
                src, num_occ_by_rup, cmaker, s_sites, param['seed'], rup_mon):
            eb_ruptures.append(ebr)
        eids = set_eids(eb_ruptures)
        src_id = src.source_id.split(':', 1)[0]
        dt = time.time() - t0
        calc_times.append((src_id, src.nsites, eids, dt))
    dic = dict(eb_ruptures=eb_ruptures, num_events=len(eids),
               calc_times=calc_times, num_ruptures=num_ruptures)
    return dic


def _sample_ruptures(src, prob, num_ses, num_samples, seed):
    """
    Sample the ruptures contained in the given source.

    :param src: a hazardlib source object
    :param prob: a probability (1 for indep sources, < 1 for mutex sources)
    :param num_ses: the number of Stochastic Event Sets to generate
    :param num_samples: how many samples for the given source
    :param seed: master seed from the job.ini file
    :returns: a dictionary of dictionaries rupture -> {ses_id: num_occurrences}
    """
    # the dictionary `num_occ_by_rup` contains a dictionary
    # ses_id -> num_occurrences for each occurring rupture
    num_occ_by_rup = collections.defaultdict(AccumDict)
    # generating ruptures for the given source
    for rup_no, rup in enumerate(src.iter_ruptures()):
        rup.seed = src.serial[rup_no] + seed
        numpy.random.seed(rup.seed)
        for sam_idx in range(num_samples):
            for ses_idx in range(1, num_ses + 1):
                # sampling of mutex sources if prob < 1
                ok = numpy.random.random() < prob if prob < 1 else True
                if ok:
                    num_occ = rup.sample_number_of_occurrences()
                    if num_occ:
                        num_occ_by_rup[rup] += {(sam_idx, ses_idx): num_occ}
        rup.rup_no = rup_no + 1
    return num_occ_by_rup


def _build_eb_ruptures(
        src, num_occ_by_rup, cmaker, s_sites, random_seed, rup_mon):
    """
    Filter the ruptures stored in the dictionary num_occ_by_rup and
    yield pairs (rupture, <list of associated EBRuptures>)
    """
    for rup in sorted(num_occ_by_rup, key=operator.attrgetter('rup_no')):
        rup.serial = rup.seed - random_seed + 1
        with rup_mon:
            try:
                rup.sctx, rup.dctx = cmaker.make_contexts(s_sites, rup)
                indices = rup.sctx.sids
            except FarAwayRupture:
                # ignore ruptures which are far away
                del num_occ_by_rup[rup]  # save memory
                continue

        # creating EBRuptures
        events = []
        for (sam_idx, ses_idx), num_occ in sorted(
                num_occ_by_rup[rup].items()):
            for _ in range(num_occ):
                # NB: the 0 below is a placeholder; the right eid will be
                # set a bit later, in set_eids
                events.append((0, src.src_group_id, ses_idx, sam_idx))
        if events:
            yield EBRupture(rup, indices, numpy.array(events, event_dt))
