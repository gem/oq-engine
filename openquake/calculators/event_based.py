# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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
import numpy
import psutil

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import AccumDict, copyobj, humansize
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import geom_avg_std, compute_pmap_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.calc.filters import nofilter
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.calc.stochastic import get_rup_array, rupture_dt
from openquake.hazardlib.source.rupture import EBRupture
from openquake.commonlib import calc, util, logs, readinput, logictree
from openquake.risklib.riskinput import str2rsi
from openquake.calculators import base, views
from openquake.calculators.getters import (
    GmfGetter, gen_rupture_getters, sig_eps_dt, time_dt)
from openquake.calculators.classical import ClassicalCalculator
from openquake.engine import engine

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = numpy.float64(2 ** 32)


# ######################## GMF calculator ############################ #

def get_mean_curves(dstore, imt):
    """
    Extract the mean hazard curves from the datastore, as an array of shape
    (N, L1)
    """
    if 'hcurves-stats' in dstore:  # shape (N, S, M, L1)
        arr = dstore.sel('hcurves-stats', stat='mean', imt=imt)
    else:  # there is only 1 realization
        arr = dstore.sel('hcurves-rlzs', rlz_id=0, imt=imt)
    return arr[:, 0, 0, :]

# ########################################################################## #


def compute_gmfs(rupgetter, param, monitor):
    """
    Compute GMFs and optionally hazard curves
    """
    oq = param['oqparam']
    srcfilter = monitor.read('srcfilter')
    getter = GmfGetter(rupgetter, srcfilter, oq, param['amplifier'],
                       param['sec_perils'])
    return getter.compute_gmfs_curves(monitor)


def compute_avg_gmf(gmf_df, weights, min_iml):
    """
    :param gmf_df: a DataFrame with colums eid, sid, rlz, gmv...
    :param weights: E weights associated to the realizations
    :param min_iml: array of M minimum intensities
    :returns: a dictionary site_id -> array of shape (2, M)
    """
    dic = {}
    E = len(weights)
    M = len(min_iml)
    for sid, df in gmf_df.groupby(gmf_df.index):
        eid = df.pop('eid')
        if len(df) < E:
            gmvs = numpy.ones((E, M), F32) * min_iml
            gmvs[eid.to_numpy()] = df.to_numpy()
        else:
            gmvs = df.to_numpy()
        dic[sid] = geom_avg_std(gmvs, weights)
    return dic


@base.calculators.add('event_based', 'scenario', 'ucerf_hazard')
class EventBasedCalculator(base.HazardCalculator):
    """
    Event based PSHA calculator generating the ground motion fields and
    the hazard curves from the ruptures, depending on the configuration
    parameters.
    """
    core_task = compute_gmfs
    is_stochastic = True
    accept_precalc = ['event_based', 'ebrisk', 'event_based_risk']

    def init(self):
        if hasattr(self, 'csm'):
            self.check_floating_spinning()
        if hasattr(self.oqparam, 'maximum_distance'):
            self.srcfilter = self.src_filter()
        else:
            self.srcfilter = nofilter
        if not self.datastore.parent:
            self.datastore.create_dset('ruptures', rupture_dt)
            self.datastore.create_dset('rupgeoms', hdf5.vfloat32)

    def acc0(self):
        """
        Initial accumulator, a dictionary (et_id, gsim) -> curves
        """
        self.L = self.oqparam.imtls.size
        zd = {r: ProbabilityMap(self.L) for r in range(self.R)}
        return zd

    def build_events_from_sources(self):
        """
        Prefilter the composite source model and store the source_info
        """
        gsims_by_trt = self.csm.full_lt.get_gsims_by_trt()
        logging.info('Building ruptures')
        for src in self.csm.get_sources():
            src.nsites = 1  # avoid 0 weight
        maxweight = sum(sg.weight for sg in self.csm.src_groups) / (
            self.oqparam.concurrent_tasks or 1)
        eff_ruptures = AccumDict(accum=0)  # trt => potential ruptures
        calc_times = AccumDict(accum=numpy.zeros(3, F32))  # nr, ns, dt
        allargs = []
        if self.oqparam.is_ucerf():
            # manage the filtering in a special way
            for sg in self.csm.src_groups:
                for src in sg:
                    src.src_filter = self.srcfilter
            srcfilter = nofilter  # otherwise it would be ultra-slow
        else:
            srcfilter = self.srcfilter
        for sg in self.csm.src_groups:
            if not sg.sources:
                continue
            logging.info('Sending %s', sg)
            par = self.param.copy()
            par['gsims'] = gsims_by_trt[sg.trt]
            for src_group in sg.split(maxweight):
                allargs.append((src_group, srcfilter, par))
        smap = parallel.Starmap(
            sample_ruptures, allargs, h5=self.datastore.hdf5)
        mon = self.monitor('saving ruptures')
        self.nruptures = 0
        for dic in smap:
            # NB: dic should be a dictionary, but when the calculation dies
            # for an OOM it can become None, thus giving a very confusing error
            if dic is None:
                raise MemoryError('You ran out of memory!')
            rup_array = dic['rup_array']
            if len(rup_array) == 0:
                continue
            if dic['calc_times']:
                calc_times += dic['calc_times']
            if dic['eff_ruptures']:
                eff_ruptures += dic['eff_ruptures']
            with mon:
                n = len(rup_array)
                rup_array['id'] = numpy.arange(
                    self.nruptures, self.nruptures + n)
                self.nruptures += n
                hdf5.extend(self.datastore['ruptures'], rup_array)
                hdf5.extend(self.datastore['rupgeoms'], rup_array.geom)
        if len(self.datastore['ruptures']) == 0:
            raise RuntimeError('No ruptures were generated, perhaps the '
                               'investigation time is too short')

        # must be called before storing the events
        self.store_rlz_info(eff_ruptures)  # store full_lt
        self.store_source_info(calc_times)
        imp = calc.RuptureImporter(self.datastore)
        with self.monitor('saving ruptures and events'):
            imp.import_rups(self.datastore.getitem('ruptures')[()])

    def agg_dicts(self, acc, result):
        """
        :param acc: accumulator dictionary
        :param result: an AccumDict with events, ruptures, gmfs and hcurves
        """
        sav_mon = self.monitor('saving gmfs')
        agg_mon = self.monitor('aggregating hcurves')
        primary = self.oqparam.get_primary_imtls()
        sec_imts = self.oqparam.get_sec_imts()
        with sav_mon:
            df = result.pop('gmfdata')
            if len(df):
                times = result.pop('times')
                rupids = list(times['rup_id'])
                self.datastore['gmf_data/time_by_rup'][rupids] = times
                hdf5.extend(self.datastore['gmf_data/sid'], df.sid.to_numpy())
                hdf5.extend(self.datastore['gmf_data/eid'], df.eid.to_numpy())
                for m in range(len(primary)):
                    hdf5.extend(self.datastore[f'gmf_data/gmv_{m}'],
                                df[f'gmv_{m}'])
                for sec_imt in sec_imts:
                    hdf5.extend(self.datastore[f'gmf_data/{sec_imt}'],
                                df[sec_imt])
                sig_eps = result.pop('sig_eps')
                hdf5.extend(self.datastore['gmf_data/sigma_epsilon'], sig_eps)
                self.offset += len(df)
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

    def set_param(self, **kw):
        oq = self.oqparam
        if oq.ground_motion_fields and oq.min_iml.sum() == 0:
            logging.warning('The GMFs are not filtered: '
                            'you may want to set a minimum_intensity')
        else:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        self.param.update(
            oqparam=oq,
            gmf=oq.ground_motion_fields,
            truncation_level=oq.truncation_level,
            imtls=oq.imtls,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path, **kw)

    def _read_scenario_ruptures(self):
        oq = self.oqparam
        gsim_lt = readinput.get_gsim_lt(self.oqparam)
        G = gsim_lt.get_num_paths()
        if oq.inputs['rupture_model'].endswith('.xml'):
            ngmfs = oq.number_of_ground_motion_fields
            self.gsims = [gsim_rlz.value[0] for gsim_rlz in gsim_lt]
            self.cmaker = ContextMaker(
                '*', self.gsims, {'maximum_distance': oq.maximum_distance,
                                  'imtls': oq.imtls})
            rup = readinput.get_rupture(oq)
            if self.N > oq.max_sites_disagg:  # many sites, split rupture
                ebrs = [EBRupture(copyobj(rup, rup_id=rup.rup_id + i),
                                  0, 0, G, e0=i * G) for i in range(ngmfs)]
            else:  # keep a single rupture with a big occupation number
                ebrs = [EBRupture(rup, 0, 0, G * ngmfs, rup.rup_id)]
            aw = get_rup_array(ebrs, self.srcfilter)
            if len(aw) == 0:
                raise RuntimeError('The rupture is too far from the sites!')
        elif oq.inputs['rupture_model'].endswith('.csv'):
            aw = readinput.get_ruptures(oq.inputs['rupture_model'])
            aw.array['n_occ'] = G
        rup_array = aw.array
        hdf5.extend(self.datastore['rupgeoms'], aw.geom)

        if len(rup_array) == 0:
            raise RuntimeError(
                'There are no sites within the maximum_distance'
                ' of %s km from the rupture' % oq.maximum_distance(
                    rup.tectonic_region_type, rup.mag))

        # check the number of branchsets
        branchsets = len(gsim_lt._ltnode)
        if len(rup_array) == 1 and branchsets > 1:
            raise InvalidFile(
                '%s for a scenario calculation must contain a single '
                'branchset, found %d!' % (oq.inputs['job_ini'], branchsets))

        fake = logictree.FullLogicTree.fake(gsim_lt)
        self.realizations = fake.get_realizations()
        self.datastore['full_lt'] = fake
        self.store_rlz_info({})  # store weights
        self.save_params()
        calc.RuptureImporter(self.datastore).import_rups(rup_array)

    def execute(self):
        oq = self.oqparam
        self.set_param()
        self.offset = 0
        if oq.hazard_calculation_id:  # from ruptures
            self.datastore.parent = util.read(oq.hazard_calculation_id)
        elif hasattr(self, 'csm'):  # from sources
            self.build_events_from_sources()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}
        elif 'rupture_model' not in oq.inputs:
            logging.warning(
                'There is no rupture_model, the calculator will just '
                'import data without performing any calculation')
            fake = logictree.FullLogicTree.fake()
            self.datastore['full_lt'] = fake  # needed to expose the outputs
            self.datastore['weights'] = [1.]
            return {}
        else:  # scenario
            self._read_scenario_ruptures()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}
        N = len(self.sitecol.complete)
        if oq.ground_motion_fields:
            M = len(oq.get_primary_imtls())
            nrups = len(self.datastore['ruptures'])
            base.create_gmf_data(self.datastore, M, oq.get_sec_imts())
            self.datastore.create_dset('gmf_data/sigma_epsilon',
                                       sig_eps_dt(oq.imtls))
            self.datastore.create_dset('gmf_data/events_by_sid', U32, (N,))
            self.datastore.create_dset('gmf_data/time_by_rup',
                                       time_dt, (nrups,), fillvalue=None)

        # compute_gmfs in parallel
        nr = len(self.datastore['ruptures'])
        logging.info('Reading {:_d} ruptures'.format(nr))
        allargs = [(rgetter, self.param)
                   for rgetter in gen_rupture_getters(
                           self.datastore, oq.concurrent_tasks)]
        # reading the args is fast since we are not prefiltering the ruptures,
        # nor reading the geometries; using an iterator would cause the usual
        # damned h5py error, last seen on macos
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            self.core_task.__func__, allargs, h5=self.datastore.hdf5)
        smap.monitor.save('srcfilter', self.srcfilter)
        acc = smap.reduce(self.agg_dicts, self.acc0())
        if 'gmf_data' not in self.datastore:
            return acc
        if oq.ground_motion_fields:
            with self.monitor('saving avg_gmf', measuremem=True):
                self.save_avg_gmf()
        return acc

    def save_avg_gmf(self):
        """
        Compute and save avg_gmf, unless there are too many GMFs
        """
        size = self.datastore.getsize('gmf_data')
        logging.info(f'Stored {humansize(size)} of GMFs')
        if size > 1024**3:
            logging.warning(
                'There are more than 1 GB of GMFs, not computing avg_gmf')
            return numpy.unique(self.datastore['gmf_data/eid'][:])

        rlzs = self.datastore['events']['rlz_id']
        self.weights = self.datastore['weights'][:][rlzs]
        gmf_df = self.datastore.read_df('gmf_data', 'sid')
        for sec_imt in self.oqparam.get_sec_imts():  # ignore secondary perils
            del gmf_df[sec_imt]
        rel_events = gmf_df.eid.unique()
        e = len(rel_events)
        if e == 0:
            raise RuntimeError(
                'No GMFs were generated, perhaps they were '
                'all below the minimum_intensity threshold')
        elif e < len(self.datastore['events']):
            self.datastore['relevant_events'] = rel_events
            logging.info('Stored {:_d} relevant event IDs'.format(e))

        # really compute and store the avg_gmf
        M = len(self.oqparam.min_iml)
        avg_gmf = numpy.zeros((2, self.N, M), F32)
        for sid, avgstd in compute_avg_gmf(
                gmf_df, self.weights, self.oqparam.min_iml).items():
            avg_gmf[:, sid] = avgstd
        self.datastore['avg_gmf'] = avg_gmf
        return rel_events

    def post_execute(self, result):
        oq = self.oqparam
        if (not result or not oq.ground_motion_fields and not
                oq.hazard_curves_from_gmfs):
            return
        N = len(self.sitecol.complete)
        M = len(oq.imtls)  # 0 in scenario
        L = oq.imtls.size
        L1 = L // (M or 1)
        # check seed dependency unless the number of GMFs is huge
        if ('gmf_data' in self.datastore and
                self.datastore.getsize('gmf_data') < 1E9):
            logging.info('Checking seed dependency')
            err = views.view('gmf_error', self.datastore)
            if err > .05:
                logging.warning('Your results are expected to have a large '
                                'dependency from ses_seed')
        if oq.hazard_curves_from_gmfs:
            rlzs = self.datastore['full_lt'].get_realizations()
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
                self.datastore.create_dset('hcurves-rlzs', F32, (N, R, M, L1))
                self.datastore.set_shape_descr(
                    'hcurves-rlzs', site_id=N, rlz_id=R,
                    imt=list(oq.imtls), lvl=numpy.arange(L1))
                if oq.poes:
                    P = len(oq.poes)
                    M = len(oq.imtls)
                    ds = self.datastore.create_dset(
                        'hmaps-rlzs', F32, (N, R, M, P))
                    self.datastore.set_shape_descr(
                        'hmaps-rlzs', site_id=N, rlz_id=R,
                        imt=list(oq.imtls), poe=oq.poes)
                for r, pmap in enumerate(pmaps):
                    arr = numpy.zeros((N, M, L1), F32)
                    for sid in pmap:
                        arr[sid] = pmap[sid].array.reshape(M, L1)
                    self.datastore['hcurves-rlzs'][:, r] = arr
                    if oq.poes:
                        hmap = calc.make_hmap(pmap, oq.imtls, oq.poes)
                        for sid in hmap:
                            ds[sid, r] = hmap[sid].array

            if S:
                logging.info('Computing statistical hazard curves')
                self.datastore.create_dset('hcurves-stats', F32, (N, S, M, L1))
                self.datastore.set_shape_descr(
                    'hcurves-stats', site_id=N, stat=list(hstats),
                    imt=list(oq.imtls), lvl=numpy.arange(L1))
                if oq.poes:
                    P = len(oq.poes)
                    M = len(oq.imtls)
                    ds = self.datastore.create_dset(
                        'hmaps-stats', F32, (N, S, M, P))
                    self.datastore.set_shape_descr(
                        'hmaps-stats', site_id=N, stat=list(hstats),
                        imt=list(oq.imtls), poes=oq.poes)
                for s, stat in enumerate(hstats):
                    pmap = compute_pmap_stats(
                        pmaps, [hstats[stat]], weights, oq.imtls)
                    arr = numpy.zeros((N, M, L1), F32)
                    for sid in pmap:
                        arr[sid] = pmap[sid].array.reshape(M, L1)
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
            engine.expose_outputs(self.datastore)
            for imt in oq.imtls:
                cl_mean_curves = get_mean_curves(self.datastore, imt)
                eb_mean_curves = get_mean_curves(self.datastore, imt)
                self.rdiff, index = util.max_rel_diff_index(
                    cl_mean_curves, eb_mean_curves)
                logging.warning('Relative difference with the classical '
                                'mean curves: %d%% at site index %d, imt=%s',
                                self.rdiff * 100, index, imt)
