# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import operator
import collections
import numpy

from openquake.baselib import hdf5, datastore
from openquake.baselib.python3compat import zip
from openquake.baselib.general import (
    AccumDict, split_in_blocks, cached_property)
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.source import rupture
from openquake.risklib.riskinput import str2rsi
from openquake.baselib import parallel
from openquake.commonlib import calc, util
from openquake.calculators import base
from openquake.calculators.getters import (
    GmfGetter, RuptureGetter, get_code2cls)
from openquake.calculators.classical import ClassicalCalculator

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO32 = U64(2 ** 32)
rlzs_by_grp_dt = numpy.dtype(
    [('grp_id', U16), ('gsim_id', U16), ('rlzs', hdf5.vuint16)])


def get_idxs(data, eid2idx):
    """
    Convert from event IDs to event indices.

    :param data: an array with a field eid
    :param eid2idx: a dictionary eid -> idx
    :returns: the array of event indices
    """
    uniq, inv = numpy.unique(data['eid'], return_inverse=True)
    idxs = numpy.array([eid2idx[eid] for eid in uniq])[inv]
    return idxs


def store_rlzs_by_grp(dstore):
    """
    Save in the datastore a composite array with fields (grp_id, gsim_id, rlzs)
    """
    lst = []
    assoc = dstore['csm_info'].get_rlzs_assoc()
    logging.info('There are %d realizations', len(assoc.realizations))
    for grp, arr in assoc.by_grp().items():
        for gsim_id, rlzs in enumerate(arr):
            lst.append((int(grp[4:]), gsim_id, rlzs))
    dstore['csm_info/rlzs_by_grp'] = numpy.array(lst, rlzs_by_grp_dt)


def build_ruptures(srcs, srcfilter, param, monitor):
    """
    A small wrapper around :func:
    `openquake.hazardlib.calc.stochastic.sample_ruptures`
    """
    acc = []  # a list of sources with an attribute eb_ruptures
    n = 0
    mon = monitor('making contexts', measuremem=False)
    for src in srcs:
        dic = sample_ruptures([src], param, srcfilter, mon)
        vars(src).update(dic)
        acc.append(src)
        n += len(dic['eb_ruptures'])
        if n > param['ruptures_per_block']:
            yield acc
            n = 0
            acc.clear()
    if acc:
        yield acc


def get_events(ebruptures, rlzs_by_gsim):
    ebrs = list(ebruptures)  # iterate on the rupture getter
    if not ebrs:
        return ()
    return numpy.concatenate(
        [ebr.get_events(rlzs_by_gsim) for ebr in ebrs])


# ######################## GMF calculator ############################ #

def update_nbytes(dstore, key, array):
    nbytes = dstore.get_attr(key, 'nbytes', 0)
    dstore.set_attrs(key, nbytes=nbytes + array.nbytes)


def get_mean_curves(dstore):
    """
    Extract the mean hazard curves from the datastore, as a composite
    array of length nsites.
    """
    return dstore['hcurves/mean'].value

# ########################################################################## #


def compute_gmfs(rupgetter, sitecol, param, monitor):
    """
    Compute GMFs and optionally hazard curves
    """
    with monitor('getting ruptures'):
        ebruptures = list(rupgetter)
    getter = GmfGetter(
        rupgetter.rlzs_by_gsim, ebruptures, sitecol,
        param['oqparam'], param['min_iml'])
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
    build_ruptures = build_ruptures

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
        self.grp_trt = csm_info.grp_by("trt")
        self.rlzs_assoc = csm_info.get_rlzs_assoc()
        self.rlzs_by_gsim_grp = csm_info.get_rlzs_by_gsim_grp()
        self.samples_by_grp = csm_info.get_samples_by_grp()
        self.num_rlzs_by_grp = {
            grp_id:
            sum(len(rlzs) for rlzs in self.rlzs_by_gsim_grp[grp_id].values())
            for grp_id in self.rlzs_by_gsim_grp}
        self.R = len(self.rlzs_assoc.realizations)

    def zerodict(self):
        """
        Initial accumulator, a dictionary (grp_id, gsim) -> curves
        """
        self.L = len(self.oqparam.imtls.array)
        zd = {r: ProbabilityMap(self.L) for r in range(self.R)}
        self.E = len(self.datastore['events'])
        self.rlzi = numpy.zeros(self.E, U16)
        return zd

    def from_sources(self, par):
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
        calc_times = AccumDict(accum=numpy.zeros(3, F32))
        ses_idx = 0
        for sm_id, sm in enumerate(self.csm.source_models):
            logging.info('Sending %s', sm)
            for sg in sm.src_groups:
                if not sg.sources:
                    continue
                par['gsims'] = gsims_by_trt[sg.trt]
                for block in self.block_splitter(sg.sources, weight_src):
                    if 'ucerf' in oq.calculation_mode:
                        for i in range(oq.ses_per_logic_tree_path):
                            par['ses_seeds'] = [(ses_idx, oq.ses_seed + i + 1)]
                            smap.submit(block, self.src_filter, par)
                            ses_idx += 1
                    else:
                        smap.submit(block, self.src_filter, par)
        mon = self.monitor('saving ruptures')
        for srcs in smap:
            eb_ruptures = []
            for src in srcs:
                eb_ruptures.extend(src.eb_ruptures)
                eff_ruptures[src.src_group_id] += src.num_ruptures
            if eb_ruptures:
                with mon:
                    self.rupser.save(eb_ruptures)
            for src in srcs:
                calc_times += src.calc_times
        self.rupser.close()

        # logic tree reduction, must be called before storing the events
        self.store_csm_info(eff_ruptures)
        store_rlzs_by_grp(self.datastore)
        self.init_logic_tree(self.csm.info)
        logging.info('Storing source_info')
        with self.monitor('store source_info', autoflush=True):
            self.store_source_info(calc_times)

        logging.info('Reordering the ruptures and the events')
        attrs = self.datastore.getitem('ruptures').attrs
        sorted_ruptures = self.datastore.getitem('ruptures').value
        # order the ruptures by serial
        sorted_ruptures.sort(order='serial')
        self.datastore['ruptures'] = sorted_ruptures
        self.datastore.set_attrs('ruptures', **attrs)
        n_events = self.save_events(sorted_ruptures)
        self.check_overflow()  # check the number of events
        logging.info('Stored {:,d} ruptures and {:,d} events'
                     .format(len(sorted_ruptures), n_events))
        return self.from_ruptures(par)

    def from_ruptures(self, param):
        """
        :yields: the arguments for compute_gmfs_and_curves
        """
        oq = self.oqparam
        concurrent_tasks = oq.concurrent_tasks
        dstore = (self.datastore.parent if self.datastore.parent
                  else self.datastore)
        start = 0
        logging.info('Reading/sending ruptures')
        with self.monitor('getting ruptures'):
            rups = dstore.getitem('ruptures').value
            code2cls = get_code2cls(dstore.get_attrs('ruptures'))
            hdf5cache = dstore.hdf5cache()
            with hdf5.File(hdf5cache, 'r+') as cache:
                if 'rupgeoms' not in cache:
                    dstore.hdf5.copy('rupgeoms', cache)
        eid2rlz_mon = self.monitor('associating eid->rlz')
        by_grp = operator.itemgetter(2)  # fields serial, srcidx, grp_id, ...
        for block in split_in_blocks(rups, concurrent_tasks or 1, key=by_grp):
            nr = len(block)  # number of ruptures per block
            grp_id = block[0]['grp_id']
            rlzs_by_gsim = self.rlzs_by_gsim_grp[grp_id]
            if not rlzs_by_gsim:
                # this may happen if a source model has no sources, like
                # in event_based_risk/case_3
                continue
            par = param.copy()
            par['samples'] = self.samples_by_grp[grp_id]
            rup_array = rups[start: start + nr]
            rgetter = RuptureGetter(hdf5cache, code2cls, rup_array,
                                    self.grp_trt[grp_id], par['samples'],
                                    rlzs_by_gsim)
            with eid2rlz_mon:
                eid_rlz = rgetter.get_eid_rlz()
                idxs = get_idxs(eid_rlz, self.eid2idx)
                self.rlzi[idxs] = eid_rlz['rlz']
            yield rgetter, self.sitecol, par
            start += nr
        if self.datastore.parent:
            self.datastore.parent.close()

    def agg_dicts(self, acc, result):
        """
        :param acc: accumulator dictionary
        :param result: an AccumDict with events, ruptures, gmfs and hcurves
        """
        eid2idx = self.eid2idx
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        with sav_mon:
            data = result.pop('gmfdata')
            if len(data) == 0:
                return acc
            idxs = get_idxs(data, eid2idx)  # this has to be fast
            data['eid'] = idxs  # replace eid with idx
            self.datastore.extend('gmf_data/data', data)
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
        :returns: the number of saved events
        """
        # this is very fast compared to saving the ruptures
        eids = rupture.get_eids(
            rup_array, self.samples_by_grp, self.num_rlzs_by_grp)
        events = numpy.zeros(len(eids), rupture.events_dt)
        events['eid'] = eids
        self.datastore['events'] = events
        return len(eids)

    def check_overflow(self):
        """
        Raise a ValueError if the number of sites is larger than 65,536 or the
        number of IMTs is larger than 256 or the number of ruptures is larger
        than 4,294,967,296. The limits are due to the numpy dtype used to
        store the GMFs (gmv_dt). They could be relaxed in the future.
        """
        max_ = dict(events=2**32, imts=2**8)
        try:
            events = len(self.datastore['events'])
        except KeyError:
            events = 0
        num_ = dict(events=events, imts=len(self.oqparam.imtls))
        if self.sitecol:
            max_['sites'] = 2**16
            num_['sites'] = len(self.sitecol)
        for var in max_:
            if num_[var] > max_[var]:
                raise ValueError(
                    'The event based calculator is restricted to '
                    '%d %s, got %d' % (max_[var], var, num_[var]))

    def execute(self):
        oq = self.oqparam
        self.offset = 0
        self.indices = collections.defaultdict(list)  # sid, idx -> indices
        self.min_iml = self.get_min_iml(oq)
        param = self.param.copy()
        param.update(
            oqparam=oq, min_iml=self.min_iml,
            gmf=oq.ground_motion_fields,
            truncation_level=oq.truncation_level,
            ruptures_per_block=oq.ruptures_per_block,
            imtls=oq.imtls, filter_distance=oq.filter_distance,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path)
        if oq.hazard_calculation_id:  # from ruptures
            assert oq.ground_motion_fields, 'must be True!'
            self.datastore.parent = datastore.read(oq.hazard_calculation_id)
            self.init_logic_tree(self.csm_info)
            iterargs = self.from_ruptures(param)
        else:  # from sources
            iterargs = self.from_sources(param)
            if oq.ground_motion_fields is False:
                return {}
        # call compute_gmfs in parallel
        acc = parallel.Starmap(
            self.core_task.__func__, iterargs, self.monitor()
        ).reduce(self.agg_dicts, self.zerodict())

        # storing events['rlz']
        if not self.datastore.parent:
            self.datastore['events']['rlz'] = self.rlzi
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
                self.datastore.set_attrs(
                    'gmf_data', avg_events_by_sid=num_evs.value.sum() / N,
                    max_events_by_sid=num_evs.value.max())
        elif oq.ground_motion_fields:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')
        return acc

    def save_gmf_bytes(self):
        """Save the attribute nbytes in the gmf_data datasets"""
        ds = self.datastore
        for sm_id in ds['gmf_data']:
            ds.set_nbytes('gmf_data/' + sm_id)
        ds.set_nbytes('gmf_data')

    @cached_property
    def eid2idx(self):
        eids = self.datastore['events']['eid']
        eid2idx = dict(zip(eids, numpy.arange(len(eids), dtype=U32)))
        return eid2idx

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
            pmaps = list(result.values())
            if len(hstats):
                logging.info('Computing statistical hazard curves')
                if len(weights) != len(pmaps):
                    # this should never happen, unless I break the
                    # logic tree reduction mechanism during refactoring
                    raise AssertionError('Expected %d pmaps, got %d' %
                                         (len(weights), len(pmaps)))
                for statname, stat in hstats:
                    pmap = compute_pmap_stats(pmaps, [stat], weights)
                    arr = numpy.zeros((N, L), F32)
                    for sid in pmap:
                        arr[sid] = pmap[sid].array[:, 0]
                    self.datastore['hcurves/' + statname] = arr
                    if oq.poes:
                        P = len(oq.poes)
                        I = len(oq.imtls)
                        self.datastore.create_dset(
                            'hmaps/' + statname, F32, (N, P * I))
                        self.datastore.set_attrs(
                            'hmaps/' + statname, nbytes=N * P * I * 4)
                        hmap = calc.make_hmap(pmap, oq.imtls, oq.poes)
                        ds = self.datastore['hmaps/' + statname]
                        for sid in hmap:
                            ds[sid] = hmap[sid].array[:, 0]

        if self.datastore.parent:
            self.datastore.parent.open('r')
        if 'gmf_data' in self.datastore:
            self.save_gmf_bytes()
        if oq.compare_with_classical:  # compute classical curves
            export_dir = os.path.join(oq.export_dir, 'cl')
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            oq.export_dir = export_dir
            # one could also set oq.number_of_logic_tree_samples = 0
            self.cl = ClassicalCalculator(oq)
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            self.cl.run(close=False)
            cl_mean_curves = get_mean_curves(self.cl.datastore)
            eb_mean_curves = get_mean_curves(self.datastore)
            rdiff, index = util.max_rel_diff_index(
                cl_mean_curves, eb_mean_curves)
            logging.warn('Relative difference with the classical '
                         'mean curves: %d%% at site index %d',
                         rdiff * 100, index)
