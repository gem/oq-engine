# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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

import os.path
import logging
import collections
import operator
import numpy

from openquake.baselib import hdf5, datastore
from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict, cached_property, get_indices
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.source import rupture
from openquake.risklib.riskinput import str2rsi
from openquake.baselib import parallel
from openquake.commonlib import calc, util, logs
from openquake.calculators import base, extract
from openquake.calculators.getters import (
    GmfGetter, RuptureGetter, gen_rupture_getters)
from openquake.calculators.classical import ClassicalCalculator
from openquake.engine import engine

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO32 = U64(2 ** 32)
rlzs_by_grp_dt = numpy.dtype(
    [('grp_id', U16), ('gsim_id', U16), ('rlzs', hdf5.vuint16)])
by_grp = operator.attrgetter('src_group_id')


def store_rlzs_by_grp(dstore):
    """
    Save in the datastore a composite array with fields (grp_id, gsim_id, rlzs)
    """
    lst = []
    assoc = dstore['csm_info'].get_rlzs_assoc()
    for grp, arr in assoc.by_grp().items():
        for gsim_id, rlzs in enumerate(arr):
            lst.append((int(grp[4:]), gsim_id, rlzs))
    dstore['csm_info/rlzs_by_grp'] = numpy.array(lst, rlzs_by_grp_dt)


# ######################## GMF calculator ############################ #

def update_nbytes(dstore, key, array):
    nbytes = dstore.get_attr(key, 'nbytes', 0)
    dstore.set_attrs(key, nbytes=nbytes + array.nbytes)


def get_mean_curves(dstore):
    """
    Extract the mean hazard curves from the datastore, as a composite
    array of length nsites.
    """
    return dict(extract.extract(dstore, 'hcurves?kind=mean'))['mean']

# ########################################################################## #


def compute_gmfs(rupgetter, srcfilter, param, monitor):
    """
    Compute GMFs and optionally hazard curves
    """
    getter = GmfGetter(rupgetter, srcfilter, param['oqparam'])
    with monitor('getting ruptures'):
        getter.init()
    return getter.compute_gmfs_curves(monitor)


@base.calculators.add('event_based')
class EventBasedCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    core_task = compute_gmfs
    is_stochastic = True
    accept_precalc = ['event_based', 'event_based_risk', 'ucerf_hazard']
    build_ruptures = sample_ruptures

    @cached_property
    def csm_info(self):
        """
        :returns: a cached CompositionInfo object
        """
        try:
            return self.csm.info
        except AttributeError:
            return self.datastore.parent['csm_info']

    def init(self):
        if hasattr(self, 'csm'):
            self.check_floating_spinning()
        self.rupser = calc.RuptureSerializer(self.datastore)

    def init_logic_tree(self, csm_info):
        self.trt_by_grp = csm_info.grp_by("trt")
        self.rlzs_assoc = csm_info.get_rlzs_assoc()
        self.rlzs_by_gsim_grp = csm_info.get_rlzs_by_gsim_grp()
        self.samples_by_grp = csm_info.get_samples_by_grp()
        self.num_rlzs_by_grp = {
            grp_id:
            sum(len(rlzs) for rlzs in self.rlzs_by_gsim_grp[grp_id].values())
            for grp_id in self.rlzs_by_gsim_grp}

    def acc0(self):
        """
        Initial accumulator, a dictionary (grp_id, gsim) -> curves
        """
        self.L = len(self.oqparam.imtls.array)
        zd = {r: ProbabilityMap(self.L) for r in range(self.R)}
        return zd

    def build_events_from_sources(self):
        """
        Prefilter the composite source model and store the source_info
        """
        oq = self.oqparam
        gsims_by_trt = self.csm.gsim_lt.values

        def weight_src(src):
            return src.num_ruptures

        logging.info('Building ruptures')
        smap = parallel.Starmap(
            self.build_ruptures.__func__, monitor=self.monitor())
        eff_ruptures = AccumDict(accum=0)  # grp_id => potential ruptures
        calc_times = AccumDict(accum=numpy.zeros(2, F32))
        ses_idx = 0
        for sm_id, sm in enumerate(self.csm.source_models):
            logging.info('Sending %s', sm)
            for sg in sm.src_groups:
                if not sg.sources:
                    continue
                par = self.param.copy()
                par['gsims'] = gsims_by_trt[sg.trt]
                if sg.atomic:  # do not split the group
                    smap.submit(sg, self.src_filter, par)
                else:  # traditional groups
                    for block in self.block_splitter(
                            sg.sources, weight_src, by_grp):
                        if 'ucerf' in oq.calculation_mode:
                            for i in range(oq.ses_per_logic_tree_path):
                                par['ses_seeds'] = [
                                    (ses_idx, oq.ses_seed + i + 1)]
                                smap.submit(block, self.src_filter, par)
                                ses_idx += 1
                        else:
                            smap.submit(block, self.src_filter, par)
        mon = self.monitor('saving ruptures')
        for dic in smap:
            if dic['calc_times']:
                calc_times += dic['calc_times']
            if dic['eff_ruptures']:
                eff_ruptures += dic['eff_ruptures']
            if dic['rup_array']:
                with mon:
                    self.rupser.save(dic['rup_array'])
        self.rupser.close()
        if not self.rupser.nruptures:
            raise RuntimeError('No ruptures were generated, perhaps the '
                               'investigation time is too short')

        # logic tree reduction, must be called before storing the events
        self.store_rlz_info(eff_ruptures)
        store_rlzs_by_grp(self.datastore)
        self.init_logic_tree(self.csm.info)
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(calc_times)
        logging.info('Reordering the ruptures and storing the events')
        attrs = self.datastore.getitem('ruptures').attrs
        sorted_ruptures = self.datastore.getitem('ruptures').value
        # order the ruptures by serial
        sorted_ruptures.sort(order='serial')
        ngroups = len(self.csm.info.trt_by_grp)
        grp_indices = numpy.zeros((ngroups, 2), U32)
        grp_ids = sorted_ruptures['grp_id']
        for grp_id, [startstop] in get_indices(grp_ids).items():
            grp_indices[grp_id] = startstop
        self.datastore['ruptures'] = sorted_ruptures
        self.datastore.set_attrs('ruptures', grp_indices=grp_indices, **attrs)
        self.save_events(sorted_ruptures)

    def gen_rupture_getters(self):
        """
        :returns: a list of RuptureGetters
        """
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        hdf5cache = dstore.hdf5cache()
        mode = 'r+' if os.path.exists(hdf5cache) else 'w'
        with hdf5.File(hdf5cache, mode) as cache:
            if 'ruptures' not in cache:
                dstore.hdf5.copy('ruptures', cache)
            if 'rupgeoms' not in cache:
                dstore.hdf5.copy('rupgeoms', cache)
        yield from gen_rupture_getters(
            dstore, concurrent_tasks=self.oqparam.concurrent_tasks or 1,
            hdf5cache=hdf5cache)
        if self.datastore.parent:
            self.datastore.parent.close()

    @cached_property
    def eid2idx(self):
        """
        :returns: a dict eid -> index in the events table
        """
        return dict(zip(self.datastore['events']['id'], range(self.E)))

    def agg_dicts(self, acc, result):
        """
        :param acc: accumulator dictionary
        :param result: an AccumDict with events, ruptures, gmfs and hcurves
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        with sav_mon:
            data = result.pop('gmfdata')
            if len(data) == 0:
                return acc
            idxs = base.get_idxs(data, self.eid2idx)  # this has to be fast
            data['eid'] = idxs  # replace eid with idx
            self.datastore.extend('gmf_data/data', data)
            sig_eps = result.pop('sig_eps')
            sig_eps['eid'] = base.get_idxs(sig_eps, self.eid2idx)
            self.datastore.extend('gmf_data/sigma_epsilon', sig_eps)
            # it is important to save the number of bytes while the
            # computation is going, to see the progress
            update_nbytes(self.datastore, 'gmf_data/data', data)
            for sid, start, stop in result['indices']:
                self.indices[sid, 0].append(start + self.offset)
                self.indices[sid, 1].append(stop + self.offset)
            self.offset += len(data)
            if self.offset >= TWO32:
                raise RuntimeError(
                    'The gmf_data table has more than %d rows' % TWO32)
        imtls = self.oqparam.imtls
        with agg_mon:
            for key, poes in result.get('hcurves', {}).items():
                r, sid, imt = str2rsi(key)
                array = acc[r].setdefault(sid, 0).array[imtls(imt), 0]
                array[:] = 1. - (1. - array) * (1. - poes)
        sav_mon.flush()
        agg_mon.flush()
        self.datastore.flush()
        return acc

    def save_events(self, rup_array):
        """
        :param rup_array: an array of ruptures with fields grp_id
        :returns: a list of RuptureGetters
        """
        # this is very fast compared to saving the ruptures
        eids = rupture.get_eids(
            rup_array, self.samples_by_grp, self.num_rlzs_by_grp)
        self.check_overflow()  # check the number of events
        events = numpy.zeros(len(eids), rupture.events_dt)
        # when computing the events all ruptures must be considered,
        # including the ones far away that will be discarded later on
        rgetters = self.gen_rupture_getters()

        # build the associations eid -> rlz in parallel
        smap = parallel.Starmap(RuptureGetter.get_eid_rlz,
                                ((rgetter,) for rgetter in rgetters),
                                self.monitor('get_eid_rlz'),
                                progress=logging.debug)
        i = 0
        for eid_rlz in smap:  # 30 million of events associated in 1 minute!
            for er in eid_rlz:
                events[i] = er
                i += 1
        events.sort(order='id')  # fast too
        n_unique_events = len(numpy.unique(events['id']))
        assert n_unique_events == len(events), (n_unique_events, len(events))
        self.datastore['events'] = events

    def check_overflow(self):
        """
        Raise a ValueError if the number of sites is larger than 65,536 or the
        number of IMTs is larger than 256 or the number of ruptures is larger
        than 4,294,967,296. The limits are due to the numpy dtype used to
        store the GMFs (gmv_dt). They could be relaxed in the future.
        """
        max_ = dict(sites=TWO32, events=TWO32, imts=2**8)
        num_ = dict(events=self.E, imts=len(self.oqparam.imtls))
        if self.sitecol:
            num_['sites'] = len(self.sitecol)
        for var in num_:
            if num_[var] > max_[var]:
                raise ValueError(
                    'The event based calculator is restricted to '
                    '%d %s, got %d' % (max_[var], var, num_[var]))

    def set_param(self, **kw):
        oq = self.oqparam
        # set the minimum_intensity
        if hasattr(self, 'riskmodel') and not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.riskmodel.min_iml
        min_iml = oq.min_iml
        if min_iml.sum() == 0:
            logging.warning('The GMFs are not filtered: '
                            'you may want to set a minimum_intensity')
        else:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        self.param.update(
            oqparam=oq,
            gmf=oq.ground_motion_fields,
            truncation_level=oq.truncation_level,
            ruptures_per_block=oq.ruptures_per_block,
            imtls=oq.imtls, filter_distance=oq.filter_distance,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path, **kw)

    def execute(self):
        oq = self.oqparam
        self.set_param()
        self.offset = 0
        self.indices = collections.defaultdict(list)  # sid, idx -> indices
        if oq.hazard_calculation_id and 'ruptures' in self.datastore:
            # from ruptures
            self.datastore.parent = datastore.read(oq.hazard_calculation_id)
            self.init_logic_tree(self.csm_info)
        else:
            # from sources
            self.build_events_from_sources()
            if oq.ground_motion_fields is False:
                return {}
        iterargs = ((rgetter, self.src_filter, self.param)
                    for rgetter in self.gen_rupture_getters())
        # call compute_gmfs in parallel
        acc = parallel.Starmap(
            self.core_task.__func__, iterargs, self.monitor()
        ).reduce(self.agg_dicts, self.acc0())

        if self.indices:
            N = len(self.sitecol.complete)
            logging.info('Saving gmf_data/indices')
            with self.monitor('saving gmf_data/indices', measuremem=True,
                              autoflush=True):
                self.datastore['gmf_data/imts'] = ' '.join(oq.imtls)
                dset = self.datastore.create_dset(
                    'gmf_data/indices', hdf5.vuint32,
                    shape=(N, 2), fillvalue=None)
                num_evs = self.datastore.create_dset(
                    'gmf_data/events_by_sid', U32, (N,))
                for sid in self.sitecol.complete.sids:
                    start = numpy.array(self.indices[sid, 0])
                    stop = numpy.array(self.indices[sid, 1])
                    dset[sid, 0] = start
                    dset[sid, 1] = stop
                    num_evs[sid] = (stop - start).sum()
                avg_events_by_sid = num_evs.value.sum() / N
                logging.info('Found ~%d GMVs per site', avg_events_by_sid)
                self.datastore.set_attrs(
                    'gmf_data', avg_events_by_sid=avg_events_by_sid,
                    max_events_by_sid=num_evs.value.max())
        elif oq.ground_motion_fields:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')
        return acc

    def post_execute(self, result):
        oq = self.oqparam
        if not oq.ground_motion_fields:
            return
        N = len(self.sitecol.complete)
        L = len(oq.imtls.array)
        if result and oq.hazard_curves_from_gmfs:
            rlzs = self.rlzs_assoc.realizations
            # compute and save statistics; this is done in process and can
            # be very slow if there are thousands of realizations
            weights = [rlz.weight for rlz in rlzs]
            # NB: in the future we may want to save to individual hazard
            # curves if oq.individual_curves is set; for the moment we
            # save the statistical curves only
            hstats = oq.hazard_stats()
            S = len(hstats)
            pmaps = list(result.values())
            R = len(weights)
            if len(pmaps) != R:
                # this should never happen, unless I break the
                # logic tree reduction mechanism during refactoring
                raise AssertionError('Expected %d pmaps, got %d' %
                                     (len(weights), len(pmaps)))
            if oq.individual_curves:
                logging.info('Saving individual hazard curves')
                self.datastore.create_dset('hcurves-rlzs', F32, (N, R, L))
                self.datastore.set_attrs('hcurves-rlzs', nbytes=N * R * L * 4)
                if oq.poes:
                    P = len(oq.poes)
                    M = len(oq.imtls)
                    ds = self.datastore.create_dset(
                        'hmaps-rlzs', F32, (N, R, M, P))
                    self.datastore.set_attrs(
                        'hmaps-rlzs', nbytes=N * R * P * M * 4)
                for r, pmap in enumerate(pmaps):
                    arr = numpy.zeros((N, L), F32)
                    for sid in pmap:
                        arr[sid] = pmap[sid].array[:, 0]
                    self.datastore['hcurves-rlzs'][:, r] = arr
                    if oq.poes:
                        hmap = calc.make_hmap(pmap, oq.imtls, oq.poes)
                        for sid in hmap:
                            ds[sid, r] = hmap[sid].array

            if S:
                logging.info('Computing statistical hazard curves')
                self.datastore.create_dset('hcurves-stats', F32, (N, S, L))
                self.datastore.set_attrs('hcurves-stats', nbytes=N * S * L * 4)
                if oq.poes:
                    P = len(oq.poes)
                    M = len(oq.imtls)
                    ds = self.datastore.create_dset(
                        'hmaps-stats', F32, (N, S, M, P))
                    self.datastore.set_attrs(
                        'hmaps-stats', nbytes=N * S * P * M * 4)
                for s, stat in enumerate(hstats):
                    pmap = compute_pmap_stats(
                        pmaps, [hstats[stat]], weights, oq.imtls)
                    arr = numpy.zeros((N, L), F32)
                    for sid in pmap:
                        arr[sid] = pmap[sid].array[:, 0]
                    self.datastore['hcurves-stats'][:, s] = arr
                    if oq.poes:
                        hmap = calc.make_hmap(pmap, oq.imtls, oq.poes)
                        for sid in hmap:
                            ds[sid, s] = hmap[sid].array

        if self.datastore.parent:
            self.datastore.parent.open('r')
        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            job_id = logs.init('job')
            self.cl = ClassicalCalculator(oq, job_id)
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            self.cl.run(close=False)
            engine.expose_outputs(self.cl.datastore)
            cl_mean_curves = get_mean_curves(self.cl.datastore)
            eb_mean_curves = get_mean_curves(self.datastore)
            self.rdiff, index = util.max_rel_diff_index(
                cl_mean_curves, eb_mean_curves)
            logging.warning('Relative difference with the classical '
                            'mean curves: %d%% at site index %d',
                            self.rdiff * 100, index)
