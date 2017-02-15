# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

import time
import os.path
import operator
import logging
import functools
import collections

import numpy

from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict, split_in_blocks
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib.probability_map import ProbabilityMap, PmapStats
from openquake.hazardlib.geo.surface import PlanarSurface
from openquake.risklib.riskinput import GmfGetter, str2rsi, rsi2str
from openquake.baselib import parallel
from openquake.commonlib import calc, util, datastore
from openquake.calculators import base
from openquake.calculators.classical import ClassicalCalculator, PSHACalculator

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16

# ######################## rupture calculator ############################ #


def get_seq_ids(task_no, num_ids):
    """
    Get an array of sequential indices for the given task.

    :param task_no: the number of the task
    :param num_ids: the number of indices to return

    >>> list(get_seq_ids(1, 3))
    [65536, 65537, 65538]
    """
    assert 0 <= task_no < TWO16, task_no
    assert 0 <= num_ids < TWO16, num_ids
    start = task_no * TWO16
    return numpy.arange(start, start + num_ids, dtype=U32)


def compute_ruptures(sources, src_filter, gsims, monitor):
    """
    :param sources:
        List of commonlib.source.Source tuples
    :param src_filter:
        a source site filter
    :param gsims:
        a list of GSIMs for the current tectonic region model
    :param monitor:
        monitor instance
    :returns:
        a dictionary src_group_id -> [Rupture instances]
    """
    # NB: by construction each block is a non-empty list with
    # sources of the same src_group_id
    grp_id = sources[0].src_group_id
    trt = sources[0].tectonic_region_type
    eb_ruptures = []
    calc_times = []
    rup_mon = monitor('filtering ruptures', measuremem=False)
    num_samples = monitor.samples
    num_events = 0
    cmaker = ContextMaker(gsims, src_filter.integration_distance)
    # Compute and save stochastic event sets
    for src, s_sites in src_filter(sources):
        t0 = time.time()
        if s_sites is None:
            continue
        num_occ_by_rup = sample_ruptures(
            src, monitor.ses_per_logic_tree_path, num_samples,
            monitor.seed)
        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_ruptures *before* the filtering
        for ebr in build_eb_ruptures(
                src, num_occ_by_rup, cmaker, s_sites, monitor.seed, rup_mon):
            eb_ruptures.append(ebr)
            num_events += ebr.multiplicity
        dt = time.time() - t0
        calc_times.append((src.id, dt))
    eids = get_seq_ids(monitor.task_no, num_events)
    start = 0
    for ebr in eb_ruptures:
        m = ebr.multiplicity
        ebr.events['eid'] = eids[start: start + m]
        start += m
    res = AccumDict({grp_id: eb_ruptures})
    res.num_events = num_events
    res.calc_times = calc_times
    if gsims:  # we can pass an empty gsims list to disable saving of rup_data
        res.rup_data = {
            grp_id: calc.RuptureData(trt, gsims).to_array(eb_ruptures)}
    return res


def sample_ruptures(src, num_ses, num_samples, seed):
    """
    Sample the ruptures contained in the given source.

    :param src: a hazardlib source object
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
        for sampleid in range(num_samples):
            for ses_idx in range(1, num_ses + 1):
                num_occurrences = rup.sample_number_of_occurrences()
                if num_occurrences:
                    num_occ_by_rup[rup] += {
                        (sampleid, ses_idx): num_occurrences}
        rup.rup_no = rup_no + 1
    return num_occ_by_rup


def build_eb_ruptures(
        src, num_occ_by_rup, cmaker, s_sites, random_seed, rup_mon):
    """
    Filter the ruptures stored in the dictionary num_occ_by_rup and
    yield pairs (rupture, <list of associated EBRuptures>)
    """
    for rup in sorted(num_occ_by_rup, key=operator.attrgetter('rup_no')):
        with rup_mon:
            try:
                r_sites, dists = cmaker.get_closest(s_sites, rup)
            except FarAwayRupture:
                # ignore ruptures which are far away
                del num_occ_by_rup[rup]  # save memory
                continue

        # creating EBRuptures
        serial = rup.seed - random_seed + 1
        events = []
        for (sampleid, ses_idx), num_occ in sorted(
                num_occ_by_rup[rup].items()):
            for occ_no in range(1, num_occ + 1):
                # NB: the 0 below is a placeholder; the right eid will be
                # set a bit later, in compute_ruptures
                events.append((0, ses_idx, occ_no, sampleid))
        if events:
            yield calc.EBRupture(
                rup, r_sites.indices,
                numpy.array(events, calc.event_dt),
                src.source_id, src.src_group_id, serial)


def _count(ruptures):
    if isinstance(ruptures, int):  # passed the number of ruptures
        return ruptures
    return sum(ebr.multiplicity for ebr in ruptures)


@base.calculators.add('event_based_rupture')
class EventBasedRuptureCalculator(PSHACalculator):
    """
    Event based PSHA calculator generating the ruptures only
    """
    core_task = compute_ruptures
    is_stochastic = True

    def init(self):
        """
        Set the random seed passed to the SourceManager and the
        minimum_intensity dictionary.
        """
        oq = self.oqparam
        self.rlzs_assoc = self.datastore['csm_info'].get_rlzs_assoc()
        self.min_iml = calc.fix_minimum_intensity(
            oq.minimum_intensity, oq.imtls)

    def count_eff_ruptures(self, ruptures_by_grp_id, src_group):
        """
        Returns the number of ruptures sampled in the given src_group.

        :param ruptures_by_grp_id: a dictionary with key grp_id
        :param src_group: a SourceGroup instance
        """
        nr = sum(
            len(ruptures) for grp_id, ruptures in ruptures_by_grp_id.items()
            if src_group.id == grp_id)
        return nr

    def zerodict(self):
        """
        Initial accumulator, a dictionary (grp_id, gsim) -> curves
        """
        zd = AccumDict()
        zd.calc_times = []
        zd.eff_ruptures = AccumDict()
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        self.grp_trt = self.csm.info.grp_trt()
        return zd

    def agg_dicts(self, acc, ruptures_by_grp_id):
        """
        Accumulate dictionaries of ruptures and populate the `events`
        dataset in the datastore.

        :param acc: accumulator dictionary
        :param ruptures_by_grp_id: a nested dictionary grp_id -> ruptures
        """
        if hasattr(ruptures_by_grp_id, 'calc_times'):
            acc.calc_times.extend(ruptures_by_grp_id.calc_times)
        if hasattr(ruptures_by_grp_id, 'eff_ruptures'):
            acc.eff_ruptures += ruptures_by_grp_id.eff_ruptures
        acc += ruptures_by_grp_id
        self.save_events(ruptures_by_grp_id)
        return acc

    def save_events(self, ruptures_by_grp_id):
        """Extend the 'events' dataset with the given ruptures"""
        with self.monitor('saving ruptures', autoflush=True):
            for grp_id, ebrs in ruptures_by_grp_id.items():
                events = []
                sm_id = self.sm_by_grp[grp_id]
                for ebr in ebrs:
                    for event in ebr.events:
                        rec = (event['eid'],
                               ebr.serial,
                               0,  # year to be set
                               event['ses'],
                               event['occ'],
                               event['sample'],
                               grp_id)
                        events.append(rec)
                    if self.oqparam.save_ruptures:
                        key = 'ruptures/grp-%02d/%s' % (grp_id, ebr.serial)
                        self.datastore[key] = ebr
                if events:
                    ev = 'events/sm-%04d' % sm_id
                    self.datastore.extend(
                        ev, numpy.array(events, calc.stored_event_dt))

            # save rup_data
            if hasattr(ruptures_by_grp_id, 'rup_data'):
                for grp_id, data in sorted(
                        ruptures_by_grp_id.rup_data.items()):
                    if len(data):
                        key = 'rup_data/grp-%02d' % grp_id
                        self.rup_data = self.datastore.extend(key, data)

    def post_execute(self, result):
        """
        Save the SES collection
        """
        num_events = sum(_count(ruptures) for ruptures in result.values())
        if num_events == 0:
            raise RuntimeError(
                'No seismic events! Perhaps the investigation time is too '
                'small or the maximum_distance is too small')
        logging.info('Setting %d event years', num_events)
        with self.monitor('setting event years', measuremem=True,
                          autoflush=True):
            inv_time = int(self.oqparam.investigation_time)
            numpy.random.seed(self.oqparam.random_seed)
            for sm in sorted(self.datastore['events']):
                set_random_years(self.datastore, 'events/' + sm, inv_time)

        if 'ruptures' in self.datastore:
            self.datastore.set_nbytes('ruptures')
        self.datastore.set_nbytes('events')
        if 'rup_data' not in self.datastore:
            return
        for dset in self.datastore['rup_data'].values():
            if len(dset):
                numsites = dset['numsites']
                multiplicity = dset['multiplicity']
                spr = numpy.average(numsites, weights=multiplicity)
                mul = numpy.average(multiplicity, weights=numsites)
                self.datastore.set_attrs(
                    dset.name, sites_per_rupture=spr,
                    multiplicity=mul, nbytes=datastore.get_nbytes(dset))
        self.datastore.set_nbytes('rup_data')


def set_random_years(dstore, events_sm, investigation_time):
    """
    Sort the `events` array and attach year labels sensitive to the
    SES ordinal and the investigation time.
    """
    events = dstore[events_sm].value
    sorted_events = sorted(tuple(event)[1:] for event in events)
    years = numpy.random.choice(investigation_time, len(events)) + 1
    year_of = dict(zip(sorted_events, years))
    for event in events:
        idx = event['ses'] - 1  # starts from 0
        event['year'] = idx * investigation_time + year_of[tuple(event)[1:]]
    dstore[events_sm] = events


# ######################## GMF calculator ############################ #

def compute_gmfs_and_curves(getter, rlzs, monitor):
    """
    :param getter:
        a GmfGetter instance
    :param rlzs:
        realizations for the current source group
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary with keys gmfcoll and hcurves
   """
    oq = monitor.oqparam
    with monitor('making contexts', measuremem=True):
        getter.init()
    haz = {sid: {} for sid in getter.sids}
    gmfcoll = {}  # rlz -> gmfa
    for rlz in rlzs:
        gmfcoll[rlz] = []
        for i, gmvdict in enumerate(getter(rlz)):
            if gmvdict:
                sid = getter.sids[i]
                for imti, imt in enumerate(getter.imts):
                    if oq.hazard_curves_from_gmfs:
                        try:
                            gmv = gmvdict[imt]
                        except KeyError:
                            # no gmv for the given imt, this may happen
                            pass
                        else:
                            haz[sid][imt, rlz] = gmv
                    for rec in gmvdict.get(imt, []):
                        gmfcoll[rlz].append(
                            (sid, rec['eid'], imti, rec['gmv']))
    for rlz in gmfcoll:
        gmfcoll[rlz] = numpy.array(gmfcoll[rlz], calc.gmv_dt)
    result = dict(gmfcoll=gmfcoll if oq.ground_motion_fields else None,
                  hcurves={})
    if oq.hazard_curves_from_gmfs:
        with monitor('building hazard curves', measuremem=False):
            duration = oq.investigation_time * oq.ses_per_logic_tree_path
            for sid, haz_by_imt_rlz in haz.items():
                for imt, rlz in haz_by_imt_rlz:
                    gmvs = haz_by_imt_rlz[imt, rlz]['gmv']
                    poes = calc._gmvs_to_haz_curve(
                        gmvs, oq.imtls[imt], oq.investigation_time, duration)
                    key = rsi2str(rlz.ordinal, sid, imt)
                    result['hcurves'][key] = poes
    return result


def get_ruptures_by_grp(dstore):
    """
    Extracts the dictionary `ruptures_by_grp` from the given calculator
    """
    n = 0
    for grp in dstore['ruptures']:
        n += len(dstore['ruptures/' + grp])
    logging.info('Reading %d ruptures from the datastore', n)
    # disable check on PlaceSurface to support UCERF ruptures
    PlanarSurface.IMPERFECT_RECTANGLE_TOLERANCE = numpy.inf
    ruptures_by_grp = AccumDict(accum=[])
    for grp in dstore['ruptures']:
        grp_id = int(grp[4:])  # strip 'grp-'
        for serial in dstore['ruptures/' + grp]:
            sr = dstore['ruptures/%s/%s' % (grp, serial)]
            ruptures_by_grp[grp_id].append(sr)
    return ruptures_by_grp


@base.calculators.add('event_based')
class EventBasedCalculator(ClassicalCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    pre_calculator = 'event_based_rupture'
    core_task = compute_gmfs_and_curves
    is_stochastic = True

    def combine_pmaps_and_save_gmfs(self, acc, res):
        """
        Combine the hazard curves (if any) and save the gmfs (if any)
        sequentially; notice that the gmfs may come from
        different tasks in any order.

        :param acc: an accumulator for the hazard curves
        :param res: a dictionary rlzi, imt -> [gmf_array, curves_by_imt]
        :returns: a new accumulator
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        if res['gmfcoll'] is not None:
            with sav_mon:
                for rlz, array in res['gmfcoll'].items():
                    if len(array):
                        sm_id = self.sm_id[rlz.sm_lt_path]
                        key = 'gmf_data/sm-%04d/%04d' % (sm_id, rlz.ordinal)
                        self.datastore.extend(key, array)
        slicedic = self.oqparam.imtls.slicedic
        with agg_mon:
            for key, poes in res['hcurves'].items():
                rlzi, sid, imt = str2rsi(key)
                array = acc[rlzi].setdefault(sid, 0).array[slicedic[imt], 0]
                array[:] = 1. - (1. - array) * (1. - poes)
        sav_mon.flush()
        agg_mon.flush()
        self.datastore.flush()
        if 'ruptures' in res:
            vars(EventBasedRuptureCalculator)['save_events'](
                self, res['ruptures'])
        return acc

    def gen_args(self, ruptures_by_grp):
        """
        :param ruptures_by_grp: a dictionary of EBRupture objects
        :yields: the arguments for compute_gmfs_and_curves
        """
        oq = self.oqparam
        monitor = self.monitor(self.core_task.__name__)
        monitor.oqparam = oq
        imts = list(oq.imtls)
        min_iml = calc.fix_minimum_intensity(oq.minimum_intensity, imts)
        self.grp_trt = self.csm.info.grp_trt()
        rlzs_by_grp = self.rlzs_assoc.get_rlzs_by_grp_id()
        correl_model = oq.get_correl_model()
        for grp_id in ruptures_by_grp:
            ruptures = ruptures_by_grp[grp_id]
            if not ruptures:
                continue
            for block in split_in_blocks(ruptures, oq.concurrent_tasks or 1):
                trt = self.grp_trt[grp_id]
                gsims = [dic[trt] for dic in self.rlzs_assoc.gsim_by_trt]
                samples = self.rlzs_assoc.samples[grp_id]
                getter = GmfGetter(gsims, block, self.sitecol,
                                   imts, min_iml, oq.truncation_level,
                                   correl_model, samples)
                yield getter, rlzs_by_grp[grp_id], monitor

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        ruptures_by_grp = (self.precalc.result if self.precalc
                           else get_ruptures_by_grp(self.datastore.parent))
        if self.oqparam.ground_motion_fields:
            calc.check_overflow(self)
        self.sm_id = {tuple(sm.path): sm.ordinal
                      for sm in self.csm.info.source_models}
        L = len(oq.imtls.array)
        res = parallel.Starmap(
            self.core_task.__func__, self.gen_args(ruptures_by_grp)
        ).submit_all()
        acc = functools.reduce(self.combine_pmaps_and_save_gmfs, res, {
            rlz.ordinal: ProbabilityMap(L, 1)
            for rlz in self.rlzs_assoc.realizations})
        self.save_data_transfer(res)
        return acc

    def post_execute(self, result):
        """
        :param result:
            a dictionary (src_group_id, gsim) -> haz_curves or an empty
            dictionary if hazard_curves_from_gmfs is false
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        elif oq.hazard_curves_from_gmfs:
            rlzs = self.rlzs_assoc.realizations
            # save individual curves
            if self.oqparam.individual_curves:
                for i in sorted(result):
                    key = 'hcurves/rlz-%03d' % i
                    if result[i]:
                        self.datastore[key] = result[i]
                    else:
                        logging.info('Zero curves for %s', key)
            # compute and save statistics; this is done in process
            # we don't need to parallelize, since event based calculations
            # involves a "small" number of sites (<= 65,536)
            weights = (None if self.oqparam.number_of_logic_tree_samples
                       else [rlz.weight for rlz in rlzs])
            pstats = PmapStats(self.oqparam.quantile_hazard_curves, weights)
            for kind, stat in pstats.compute(
                    self.sitecol.sids, list(result.values())):
                if kind == 'mean' and not self.oqparam.mean_hazard_curves:
                    continue
                self.datastore['hcurves/' + kind] = stat

        if ('gmf_data' in self.datastore and 'nbytes' not
                in self.datastore['gmf_data'].attrs):
            self.datastore.set_nbytes('gmf_data')
            for sm_id in self.datastore['gmf_data']:
                for rlzno in self.datastore['gmf_data/' + sm_id]:
                    self.datastore.set_nbytes(
                        'gmf_data/%s/%s' % (sm_id, rlzno))

        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # one could also set oq.number_of_logic_tree_samples = 0
            self.cl = ClassicalCalculator(oq, self.monitor)
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            self.cl.run(close=False)
            cl_mean_curves = get_mean_curves(self.cl.datastore)
            eb_mean_curves = get_mean_curves(self.datastore)
            for imt in eb_mean_curves.dtype.names:
                rdiff, index = util.max_rel_diff_index(
                    cl_mean_curves[imt], eb_mean_curves[imt])
                logging.warn('Relative difference with the classical '
                             'mean curves for IMT=%s: %d%% at site index %d',
                             imt, rdiff * 100, index)


def get_mean_curves(dstore):
    """
    Extract the mean hazard curves from the datastore, as a composite
    array of length nsites.
    """
    imtls = dstore['oqparam'].imtls
    nsites = len(dstore['sitecol'])
    hcurves = dstore['hcurves']
    if 'mean' in hcurves:
        mean = dstore['hcurves/mean']
    elif len(hcurves) == 1:  # there is a single realization
        mean = dstore['hcurves/rlz-0000']
    return mean.convert(imtls, nsites)
