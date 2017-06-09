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
import collections
import mock

import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict, block_splitter, humansize
from openquake.hazardlib.calc.filters import FarAwayRupture
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.geo.surface import PlanarSurface
from openquake.risklib.riskinput import (
    GmfGetter, str2rsi, rsi2str, gmf_data_dt)
from openquake.baselib import parallel
from openquake.commonlib import calc, util
from openquake.calculators import base
from openquake.calculators.classical import ClassicalCalculator, PSHACalculator

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16  # 65,536
TWO32 = 2 ** 32  # 4,294,967,296
TWO48 = 2 ** 48  # 281,474,976,710,656

# ######################## rupture calculator ############################ #


def get_seq_ids(task_no, num_ids):
    """
    Get an array of sequential indices for the given task.

    :param task_no: the number of the task
    :param num_ids: the number of indices to return

    >>> list(get_seq_ids(1, 3))
    [4294967296, 4294967297, 4294967298]
    """
    assert 0 <= task_no < TWO16, task_no
    assert 0 <= num_ids < TWO32, num_ids
    start = task_no * TWO32
    return numpy.arange(start, start + num_ids, dtype=U64)


def set_eids(ebruptures, task_no):
    """
    Set event IDs on the given list of ebruptures produced by the given task.

    :param ebruptures: a non-empty list of ruptures with the same grp_id
    :param task_no: the number of the task generating the ruptures
    :returns: the total number of events
    """
    if not ebruptures:
        return 0
    num_events = sum(ebr.multiplicity for ebr in ebruptures)
    eids = get_seq_ids(task_no, num_events)
    start = 0
    offset = U64(ebruptures[0].grp_id * TWO48)  # first 16 bits for grp_id
    for ebr in ebruptures:
        m = ebr.multiplicity
        ebr.events['eid'] = eids[start: start + m] + offset
        start += m
    return num_events


def compute_ruptures(sources, src_filter, gsims, param, monitor):
    """
    :param sources:
        List of commonlib.source.Source tuples
    :param src_filter:
        a source site filter
    :param gsims:
        a list of GSIMs for the current tectonic region model
    :param param:
        a dictionary of additional parameters
    :param monitor:
        monitor instance
    :returns:
        a dictionary src_group_id -> [Rupture instances]
    """
    # NB: by construction each block is a non-empty list with
    # sources of the same src_group_id
    grp_id = sources[0].src_group_id
    eb_ruptures = []
    calc_times = []
    rup_mon = monitor('filtering ruptures', measuremem=False)
    # Compute and save stochastic event sets
    num_ruptures = 0
    for src, s_sites in src_filter(sources):
        t0 = time.time()
        if s_sites is None:
            continue
        num_ruptures += src.num_ruptures
        num_occ_by_rup = sample_ruptures(
            src, param['ses_per_logic_tree_path'], param['samples'],
            param['seed'])
        # NB: the number of occurrences is very low, << 1, so it is
        # more efficient to filter only the ruptures that occur, i.e.
        # to call sample_ruptures *before* the filtering
        for ebr in _build_eb_ruptures(
                src, num_occ_by_rup, src_filter.integration_distance,
                s_sites, param['seed'], rup_mon):
            eb_ruptures.append(ebr)
        dt = time.time() - t0
        calc_times.append((src.id, dt))
    res = AccumDict({grp_id: eb_ruptures})
    res.num_events = set_eids(eb_ruptures, getattr(monitor, 'task_no', 0))
    res.calc_times = calc_times
    res.eff_ruptures = {grp_id: num_ruptures}
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


def _build_eb_ruptures(
        src, num_occ_by_rup, idist, s_sites, random_seed, rup_mon):
    """
    Filter the ruptures stored in the dictionary num_occ_by_rup and
    yield pairs (rupture, <list of associated EBRuptures>)
    """
    for rup in sorted(num_occ_by_rup, key=operator.attrgetter('rup_no')):
        with rup_mon:
            try:
                r_sites, dists = idist.get_closest(s_sites, rup)
            except FarAwayRupture:
                # ignore ruptures which are far away
                del num_occ_by_rup[rup]  # save memory
                continue

        # creating EBRuptures
        serial = rup.seed - random_seed + 1
        events = []
        for (sampleid, ses_idx), num_occ in sorted(
                num_occ_by_rup[rup].items()):
            for _ in range(num_occ):
                # NB: the 0 below is a placeholder; the right eid will be
                # set a bit later, in set_eids
                events.append((0, ses_idx, sampleid))
        if events:
            yield calc.EBRupture(
                rup, r_sites.indices,
                numpy.array(events, calc.event_dt),
                src.src_group_id, serial)


def _count(ruptures):
    if isinstance(ruptures, int):  # passed the number of ruptures
        return ruptures
    return sum(ebr.multiplicity for ebr in ruptures)


def get_events(ebruptures):
    """
    Extract an array of dtype stored_event_dt from a list of EBRuptures
    """
    events = []
    year = 0  # to be set later
    for ebr in ebruptures:
        for event in ebr.events:
            rec = (event['eid'], ebr.serial, year, event['ses'],
                   event['sample'])
            events.append(rec)
    return numpy.array(events, calc.stored_event_dt)


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
        self.min_iml = calc.fix_minimum_intensity(
            oq.minimum_intensity, oq.imtls)
        self.rupser = calc.RuptureSerializer(self.datastore)
        self.csm_info = self.datastore['csm_info']

    def zerodict(self):
        """
        Initial accumulator, a dictionary (grp_id, gsim) -> curves
        """
        zd = AccumDict()
        zd.calc_times = []
        zd.eff_ruptures = AccumDict()
        self.grp_trt = self.csm_info.grp_trt()
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
        self.save_ruptures(ruptures_by_grp_id)
        return acc

    def save_ruptures(self, ruptures_by_grp_id):
        """Extend the 'events' dataset with the given ruptures"""
        with self.monitor('saving ruptures', autoflush=True):
            for grp_id, ebrs in ruptures_by_grp_id.items():
                if len(ebrs):
                    events = get_events(ebrs)
                    dset = self.datastore.extend(
                        'events/grp-%02d' % grp_id, events)
                    if self.oqparam.save_ruptures:
                        initial_eidx = len(dset) - len(events)
                        self.rupser.save(ebrs, initial_eidx)

    def post_execute(self, result):
        """
        Save the SES collection
        """
        self.rupser.close()
        num_events = sum(_count(ruptures) for ruptures in result.values())
        if num_events == 0:
            raise RuntimeError(
                'No seismic events! Perhaps the investigation time is too '
                'small or the maximum_distance is too small')
        logging.info('Setting %d event years', num_events)
        with self.monitor('setting event years', measuremem=True,
                          autoflush=True):
            inv_time = int(self.oqparam.investigation_time)
            numpy.random.seed(self.oqparam.ses_seed)
            for sm in sorted(self.datastore['events']):
                set_random_years(self.datastore, 'events/' + sm, inv_time)
        h5 = self.datastore.hdf5
        if 'ruptures' in h5:
            self.datastore.set_nbytes('ruptures')
        if 'events' in h5:
            self.datastore.set_attrs('events', num_events=num_events)
            self.datastore.set_nbytes('events')


def set_random_years(dstore, events_sm, investigation_time):
    """
    Sort the `events` array and attach year labels sensitive to the
    SES ordinal and the investigation time.
    """
    events = dstore[events_sm].value
    eids = numpy.sort(events['eid'])
    years = numpy.random.choice(investigation_time, len(events)) + 1
    year_of = dict(zip(eids, years))
    for event in events:
        idx = event['ses'] - 1  # starts from 0
        event['year'] = idx * investigation_time + year_of[event['eid']]
    dstore[events_sm] = events


# ######################## GMF calculator ############################ #

def compute_gmfs_and_curves(getter, oq, monitor):
    """
    :param getter:
        a GmfGetter instance
    :param oq:
        an OqParam instance
    :param monitor:
        a Monitor instance
    :returns:
        a dictionary with keys gmfcoll and hcurves
   """
    with monitor('making contexts', measuremem=True):
        getter.init()
    grp_id = getter.grp_id
    hcurves = {}  # key -> poes
    gmfcoll = {}  # grp_id, rlz -> gmfa
    if oq.hazard_curves_from_gmfs:
        hc_mon = monitor('building hazard curves', measuremem=False)
        duration = oq.investigation_time * oq.ses_per_logic_tree_path
        for gsim in getter.rlzs_by_gsim:
            with monitor('building hazard', measuremem=True):
                gmfcoll[grp_id, gsim] = data = numpy.fromiter(
                    getter.gen_gmv(gsim), gmf_data_dt)
                hazard = getter.get_hazard(gsim, data)
            for r, rlz in enumerate(getter.rlzs_by_gsim[gsim]):
                hazardr = hazard[r]
                for sid in getter.sids:
                    for imti, imt in enumerate(getter.imts):
                        array = hazardr[sid, imti]
                        if len(array) == 0:  # no data
                            continue
                        with hc_mon:
                            poes = calc._gmvs_to_haz_curve(
                                array['gmv'], oq.imtls[imt],
                                oq.investigation_time, duration)
                            hcurves[rsi2str(rlz.ordinal, sid, imt)] = poes
    else:  # fast lane
        for gsim in getter.rlzs_by_gsim:
            with monitor('building hazard', measuremem=True):
                gmfcoll[grp_id, gsim] = numpy.fromiter(
                    getter.gen_gmv(gsim), gmf_data_dt)
    return dict(gmfcoll=gmfcoll if oq.ground_motion_fields else None,
                hcurves=hcurves, gmdata=getter.gmdata)


def get_ruptures_by_grp(dstore):
    """
    Extracts the dictionary `ruptures_by_grp` from the given calculator
    """
    n = 0
    for grp in dstore['ruptures']:
        n += len(dstore['ruptures/' + grp])
    logging.info('Reading %d ruptures from the datastore', n)
    # disable check on PlaceSurface to support UCERF ruptures
    with mock.patch(
            'openquake.hazardlib.geo.surface.PlanarSurface.'
            'IMPERFECT_RECTANGLE_TOLERANCE', numpy.inf):
        ruptures_by_grp = AccumDict(accum=[])
        for grp in dstore['ruptures']:
            grp_id = int(grp[4:])  # strip 'grp-'
            ruptures_by_grp[grp_id] = list(calc.get_ruptures(dstore, grp_id))
    return ruptures_by_grp


def save_gmdata(calc, n_rlzs):
    """
    Save a composite array `gmdata` in the datastore.

    :param calc: a calculator with a dictionary .gmdata {rlz: data}
    :param n_rlzs: the total number of realizations
    """
    n_sites = len(calc.sitecol)
    dtlist = ([(imt, F32) for imt in calc.oqparam.imtls] +
              [('events', U32), ('nbytes', U32)])
    array = numpy.zeros(n_rlzs, dtlist)
    for rlzi in sorted(calc.gmdata):
        data = calc.gmdata[rlzi]  # (imts, events, nbytes)
        events = data[-2]
        nbytes = data[-1]
        gmv = data[:-2] / events / n_sites
        array[rlzi] = tuple(gmv) + (events, nbytes)
    calc.datastore['gmdata'] = array
    logging.info('Generated %s of GMFs', humansize(array['nbytes'].sum()))


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
        self.gmdata += res['gmdata']
        if res['gmfcoll'] is not None:
            with sav_mon:
                for (grp_id, gsim), array in res['gmfcoll'].items():
                    if len(array):
                        key = 'gmf_data/grp-%02d/%s' % (grp_id, gsim)
                        hdf5.extend3(self.datastore.hdf5path, key, array)
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
            vars(EventBasedRuptureCalculator)['save_ruptures'](
                self, res['ruptures'])
        return acc

    def gen_args(self, ruptures_by_grp):
        """
        :param ruptures_by_grp: a dictionary of EBRupture objects
        :yields: the arguments for compute_gmfs_and_curves
        """
        oq = self.oqparam
        monitor = self.monitor(self.core_task.__name__)
        imts = list(oq.imtls)
        min_iml = calc.fix_minimum_intensity(oq.minimum_intensity, imts)
        correl_model = oq.get_correl_model()
        for grp_id in ruptures_by_grp:
            ruptures = ruptures_by_grp[grp_id]
            if not ruptures:
                continue
            rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(grp_id)
            for block in block_splitter(ruptures, oq.ruptures_per_block):
                samples = self.rlzs_assoc.samples[grp_id]
                getter = GmfGetter(grp_id, rlzs_by_gsim, block, self.sitecol,
                                   imts, min_iml, oq.truncation_level,
                                   correl_model, samples)
                yield getter, oq, monitor

    def execute(self):
        """
        Run in parallel `core_task(sources, sitecol, monitor)`, by
        parallelizing on the ruptures according to their weight and
        tectonic region type.
        """
        oq = self.oqparam
        if not oq.hazard_curves_from_gmfs and not oq.ground_motion_fields:
            return
        if self.oqparam.ground_motion_fields:
            calc.check_overflow(self)

        with self.monitor('reading ruptures', autoflush=True):
            ruptures_by_grp = (self.precalc.result if self.precalc
                               else get_ruptures_by_grp(self.datastore.parent))

        self.csm_info = self.datastore['csm_info']
        self.sm_id = {tuple(sm.path): sm.ordinal
                      for sm in self.csm_info.source_models}
        L = len(oq.imtls.array)
        rlzs = self.rlzs_assoc.realizations
        res = parallel.Starmap(
            self.core_task.__func__, self.gen_args(ruptures_by_grp)
        ).submit_all()
        self.gmdata = {}
        acc = res.reduce(self.combine_pmaps_and_save_gmfs, {
            rlz.ordinal: ProbabilityMap(L, 1) for rlz in rlzs})
        save_gmdata(self, len(rlzs))
        return acc

    def save_gmf_bytes(self):
        """Save the attribute nbytes in the gmf_data datasets"""
        ds = self.datastore
        for sm_id in ds['gmf_data']:
            for rlzno in ds['gmf_data/' + sm_id]:
                ds.set_nbytes('gmf_data/%s/%s' % (sm_id, rlzno))
            ds['gmf_data'].attrs['num_sites'] = len(self.sitecol.complete)
            ds['gmf_data'].attrs['num_imts'] = len(self.oqparam.imtls)
            ds.set_nbytes('gmf_data')

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
            for i in sorted(result):
                key = 'hcurves/rlz-%03d' % i
                if result[i]:
                    self.datastore[key] = result[i]
                else:
                    self.datastore[key] = ProbabilityMap(oq.imtls.array.size)
                    logging.info('Zero curves for %s', key)
            # compute and save statistics; this is done in process
            # we don't need to parallelize, since event based calculations
            # involves a "small" number of sites (<= 65,536)
            weights = [rlz.weight for rlz in rlzs]
            hstats = self.oqparam.hazard_stats()
            if len(hstats) and len(rlzs) > 1:
                for kind, stat in hstats:
                    pmap = compute_pmap_stats(result.values(), [stat], weights)
                    self.datastore['hcurves/' + kind] = pmap
        if 'gmf_data' in self.datastore:
            self.save_gmf_bytes()
        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # one could also set oq.number_of_logic_tree_samples = 0
            self.cl = ClassicalCalculator(oq, self.monitor('classical'))
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
