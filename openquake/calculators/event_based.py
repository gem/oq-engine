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
import operator
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict, get_indices, block_splitter
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.source import rupture
from openquake.risklib.riskinput import str2rsi
from openquake.baselib import parallel
from openquake.commonlib import source, calc, util, logs
from openquake.calculators import base, extract
from openquake.calculators.getters import (
    GmfGetter, RuptureGetter, gen_rupture_getters, sig_eps_dt, time_dt)
from openquake.calculators.classical import ClassicalCalculator
from openquake.engine import engine

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = numpy.float64(2 ** 32)
by_grp = operator.attrgetter('src_group_id')


# ######################## GMF calculator ############################ #

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
    oq = param['oqparam']
    getter = GmfGetter(rupgetter, srcfilter, oq)
    return getter.compute_gmfs_curves(param.get('rlz_by_event'), monitor)


@base.calculators.add('event_based')
class EventBasedCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    core_task = compute_gmfs
    is_stochastic = True
    accept_precalc = ['event_based', 'ebrisk', 'event_based_risk',
                      'ucerf_hazard']
    build_ruptures = sample_ruptures

    def init(self):
        if hasattr(self, 'csm'):
            self.check_floating_spinning()
        if not self.datastore.parent:
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

    # called multiple times
    def block_splitter(self, sources, weight=operator.attrgetter('weight'),
                       key=lambda src: 1):
        """
        :param sources: a list of sources
        :param weight: a weight function (default .weight)
        :param key: None or 'src_group_id'
        :returns: an iterator over blocks of sources
        """
        if not hasattr(self, 'maxweight'):
            trt_sources = self.csm.get_trt_sources()
            self.maxweight = sum(sum(weight(s) for s in srcs)
                                 for _, srcs, _ in trt_sources) / (
                self.oqparam.concurrent_tasks or 1)
            if self.maxweight < source.MINWEIGHT:
                self.maxweight = source.MINWEIGHT
                logging.info('Using minweight=%d', source.MINWEIGHT)
            else:
                logging.info('Using maxweight=%d', self.maxweight)
        return block_splitter(sources, self.maxweight, weight, key)

    def build_events_from_sources(self, srcfilter):
        """
        Prefilter the composite source model and store the source_info
        """
        oq = self.oqparam
        gsims_by_trt = self.csm.info.get_gsims_by_trt()
        logging.info('Building ruptures')
        eff_ruptures = AccumDict(accum=0)  # grp_id => potential ruptures
        calc_times = AccumDict(accum=numpy.zeros(3, F32))  # nr, ns, dt
        ses_idx = 0
        allargs = []
        for sm_id, sm in enumerate(self.csm.source_models):
            logging.info('Sending %s', sm)
            for sg in sm.src_groups:
                if not sg.sources:
                    continue
                par = self.param.copy()
                par['gsims'] = gsims_by_trt[sg.trt]
                if sg.atomic:  # do not split the group
                    allargs.append((sg, srcfilter, par))
                else:  # traditional groups
                    for block in self.block_splitter(sg.sources, key=by_grp):
                        if 'ucerf' in oq.calculation_mode:
                            for i in range(oq.ses_per_logic_tree_path):
                                par = par.copy()  # avoid mutating the dict
                                par['ses_seeds'] = [
                                    (ses_idx, oq.ses_seed + i + 1)]
                                allargs.append((block, srcfilter, par))
                                ses_idx += 1
                        else:
                            allargs.append((block, srcfilter, par))
        smap = parallel.Starmap(
            self.build_ruptures.__func__, allargs, h5=self.datastore.hdf5)
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
        self.init_logic_tree(self.csm.info)
        with self.monitor('store source_info'):
            self.store_source_info(calc_times)
        logging.info('Reordering the ruptures and storing the events')
        attrs = self.datastore.getitem('ruptures').attrs
        sorted_ruptures = self.datastore.getitem('ruptures')[()]
        # order the ruptures by rup_id
        sorted_ruptures.sort(order='serial')
        ngroups = len(self.csm.info.trt_by_grp)
        grp_indices = numpy.zeros((ngroups, 2), U32)
        grp_ids = sorted_ruptures['grp_id']
        for grp_id, [startstop] in get_indices(grp_ids).items():
            grp_indices[grp_id] = startstop
        self.datastore['ruptures'] = sorted_ruptures
        self.datastore['ruptures']['id'] = numpy.arange(len(sorted_ruptures))
        self.datastore.set_attrs('ruptures', grp_indices=grp_indices, **attrs)
        with self.monitor('saving events'):
            self.save_events(sorted_ruptures)

    def agg_dicts(self, acc, result):
        """
        :param acc: accumulator dictionary
        :param result: an AccumDict with events, ruptures, gmfs and hcurves
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        with sav_mon:
            data = result.pop('gmfdata')
            if len(data):
                times = result.pop('times')
                rupids = list(times['rup_id'])
                self.datastore['gmf_data/time_by_rup'][rupids] = times
                hdf5.extend(self.datastore['gmf_data/data'], data)
                sig_eps = result.pop('sig_eps')
                hdf5.extend(self.datastore['gmf_data/sigma_epsilon'], sig_eps)
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
        rgetters = gen_rupture_getters(self.datastore)
        # build the associations eid -> rlz sequentially or in parallel
        # this is very fast: I saw 30 million events associated in 1 minute!
        logging.info('Building assocs event_id -> rlz_id for {:_d} events'
                     ' and {:_d} ruptures'.format(len(events), len(rup_array)))
        if len(events) < 1E5:
            it = map(RuptureGetter.get_eid_rlz, rgetters)
        else:
            it = parallel.Starmap(RuptureGetter.get_eid_rlz,
                                  ((rgetter,) for rgetter in rgetters),
                                  progress=logging.debug,
                                  h5=self.datastore.hdf5)
        i = 0
        for eid_rlz in it:
            for er in eid_rlz:
                events[i] = er
                i += 1
                if i >= TWO32:
                    raise ValueError('There are more than %d events!' % i)
        events.sort(order='rup_id')  # fast too
        # sanity check
        n_unique_events = len(numpy.unique(events[['id', 'rup_id']]))
        assert n_unique_events == len(events), (n_unique_events, len(events))
        events['id'] = numpy.arange(len(events))
        self.datastore['events'] = events
        eindices = get_indices(events['rup_id'])
        arr = numpy.array(list(eindices.values()))[:, 0, :]
        self.datastore['eslices'] = arr  # shape (U, 2)

    def check_overflow(self):
        """
        Raise a ValueError if the number of sites is larger than 65,536 or the
        number of IMTs is larger than 256 or the number of ruptures is larger
        than 4,294,967,296. The limits are due to the numpy dtype used to
        store the GMFs (gmv_dt). There also a limit of max_potential_gmfs on
        the number of sites times the number of events, to avoid producing too
        many GMFs. In that case split the calculation or be smarter.
        """
        oq = self.oqparam
        max_ = dict(sites=TWO32, events=TWO32, imts=2**8)
        num_ = dict(events=self.E, imts=len(self.oqparam.imtls))
        num_['sites'] = n = len(self.sitecol) if self.sitecol else 0
        if oq.calculation_mode == 'event_based' and oq.ground_motion_fields:
            if n > oq.max_sites_per_gmf:
                raise ValueError(
                    'You cannot compute the GMFs for %d > %d sites' %
                    (n, oq.max_sites_per_gmf))
            elif n * self.E > oq.max_potential_gmfs:
                raise ValueError(
                    'A GMF calculation with %d sites and %d events is '
                    'impossibly large' % (n, self.E))
        for var in num_:
            if num_[var] > max_[var]:
                raise ValueError(
                    'The %s calculator is restricted to %d %s, got %d' %
                    (oq.calculation_mode, max_[var], var, num_[var]))

    def set_param(self, **kw):
        oq = self.oqparam
        # set the minimum_intensity
        if hasattr(self, 'crmodel') and not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.crmodel.min_iml
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
        srcfilter = self.src_filter(self.datastore.tempname)
        self.indices = AccumDict(accum=[])  # sid, idx -> indices
        if oq.hazard_calculation_id:  # from ruptures
            self.datastore.parent = util.read(oq.hazard_calculation_id)
            self.init_logic_tree(self.datastore.parent['csm_info'])
        else:  # from sources
            self.build_events_from_sources(srcfilter)
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}
        if not oq.imtls:
            raise InvalidFile('There are no intensity measure types in %s' %
                              oq.inputs['job_ini'])
        N = len(self.sitecol.complete)
        if oq.ground_motion_fields:
            nrups = len(self.datastore['ruptures'])
            self.datastore.create_dset('gmf_data/data', oq.gmf_data_dt())
            self.datastore.create_dset('gmf_data/sigma_epsilon',
                                       sig_eps_dt(oq.imtls))
            self.datastore.create_dset(
                'gmf_data/indices', hdf5.vuint32, shape=(N, 2), fillvalue=None)
            self.datastore.create_dset('gmf_data/events_by_sid', U32, (N,))
            self.datastore.create_dset('gmf_data/time_by_rup',
                                       time_dt, (nrups,), fillvalue=None)
        if oq.hazard_curves_from_gmfs:
            self.param['rlz_by_event'] = self.datastore['events']['rlz_id']

        # compute_gmfs in parallel
        self.datastore.swmr_on()
        logging.info('Reading %d ruptures', len(self.datastore['ruptures']))
        iterargs = ((rgetter, srcfilter, self.param)
                    for rgetter in gen_rupture_getters(self.datastore,
                                                       srcfilter=srcfilter))
        acc = parallel.Starmap(
            self.core_task.__func__, iterargs, h5=self.datastore.hdf5,
            num_cores=oq.num_cores
        ).reduce(self.agg_dicts, self.acc0())

        if self.indices:
            dset = self.datastore['gmf_data/indices']
            num_evs = self.datastore['gmf_data/events_by_sid']
            logging.info('Saving gmf_data/indices')
            with self.monitor('saving gmf_data/indices', measuremem=True):
                self.datastore['gmf_data/imts'] = ' '.join(oq.imtls)
                for sid in self.sitecol.complete.sids:
                    start = numpy.array(self.indices[sid, 0])
                    stop = numpy.array(self.indices[sid, 1])
                    dset[sid, 0] = start
                    dset[sid, 1] = stop
                    num_evs[sid] = (stop - start).sum()
            avg_events_by_sid = num_evs[()].sum() / N
            logging.info('Found ~%d GMVs per site', avg_events_by_sid)
        elif oq.ground_motion_fields:
            raise RuntimeError('No GMFs were generated, perhaps they were '
                               'all below the minimum_intensity threshold')
        return acc

    def post_execute(self, result):
        oq = self.oqparam
        if not oq.ground_motion_fields and not oq.hazard_curves_from_gmfs:
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
            oq.calculation_mode = 'classical'
            self.cl = ClassicalCalculator(oq, job_id)
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            self.cl.run()
            engine.expose_outputs(self.cl.datastore)
            cl_mean_curves = get_mean_curves(self.cl.datastore)
            eb_mean_curves = get_mean_curves(self.datastore)
            self.rdiff, index = util.max_rel_diff_index(
                cl_mean_curves, eb_mean_curves)
            logging.warning('Relative difference with the classical '
                            'mean curves: %d%% at site index %d',
                            self.rdiff * 100, index)
