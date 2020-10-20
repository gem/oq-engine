# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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

from openquake.baselib import hdf5, parallel
from openquake.baselib.general import AccumDict, copyobj
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.stats import compute_pmap_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.calc.filters import nofilter
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.calc.stochastic import get_rup_array, rupture_dt
from openquake.hazardlib.source.rupture import EBRupture
from openquake.hazardlib.geo.mesh import surface_to_array
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
by_grp = operator.attrgetter('grp_id')


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
        Initial accumulator, a dictionary (grp_id, gsim) -> curves
        """
        self.L = len(self.oqparam.imtls.array)
        zd = {r: ProbabilityMap(self.L) for r in range(self.R)}
        return zd

    def build_events_from_sources(self):
        """
        Prefilter the composite source model and store the source_info
        """
        gsims_by_trt = self.csm.full_lt.get_gsims_by_trt()
        logging.info('Building ruptures')
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
        with self.monitor('store source_info'):
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
        M = len(self.oqparam.imtls)
        sec_outputs = self.oqparam.get_sec_outputs()
        with sav_mon:
            data = result.pop('gmfdata')
            if len(data):
                times = result.pop('times')
                rupids = list(times['rup_id'])
                self.datastore['gmf_data/time_by_rup'][rupids] = times
                hdf5.extend(self.datastore['gmf_data/sid'], data['sid'])
                hdf5.extend(self.datastore['gmf_data/eid'], data['eid'])
                for m in range(M):
                    hdf5.extend(self.datastore[f'gmf_data/gmv_{m}'],
                                data['gmv'][:, m])
                for sec_out in sec_outputs:
                    hdf5.extend(self.datastore[f'gmf_data/{sec_out}'],
                                data[sec_out])
                sig_eps = result.pop('sig_eps')
                hdf5.extend(self.datastore['gmf_data/sigma_epsilon'], sig_eps)
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

    def set_param(self, **kw):
        oq = self.oqparam
        # set the minimum_intensity
        if hasattr(self, 'crmodel') and not oq.minimum_intensity:
            # infer it from the risk models if not directly set in job.ini
            oq.minimum_intensity = self.crmodel.min_iml
        min_iml = oq.min_iml
        if oq.ground_motion_fields and min_iml.sum() == 0:
            logging.warning('The GMFs are not filtered: '
                            'you may want to set a minimum_intensity')
        else:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        self.param.update(
            oqparam=oq,
            gmf=oq.ground_motion_fields,
            truncation_level=oq.truncation_level,
            imtls=oq.imtls, filter_distance=oq.filter_distance,
            ses_per_logic_tree_path=oq.ses_per_logic_tree_path, **kw)

    def _read_scenario_ruptures(self):
        oq = self.oqparam
        gsim_lt = readinput.get_gsim_lt(self.oqparam)
        G = gsim_lt.get_num_paths()
        if oq.inputs['rupture_model'].endswith('.xml'):
            ngmfs = oq.number_of_ground_motion_fields
            self.gsims = readinput.get_gsims(oq)
            self.cmaker = ContextMaker(
                '*', self.gsims, {'maximum_distance': oq.maximum_distance,
                                  'imtls': oq.imtls})
            rup = readinput.get_rupture(oq)
            mesh = surface_to_array(rup.surface).transpose(1, 2, 0).flatten()
            if self.N > oq.max_sites_disagg:  # many sites, split rupture
                ebrs = [EBRupture(copyobj(rup, rup_id=rup.rup_id + i),
                                  0, 0, G, e0=i * G) for i in range(ngmfs)]
                meshes = numpy.array([mesh] * ngmfs, object)
            else:  # keep a single rupture with a big occupation number
                ebrs = [EBRupture(rup, 0, 0, G * ngmfs, rup.rup_id)]
                meshes = numpy.array([mesh] * ngmfs, object)
            rup_array = get_rup_array(ebrs, self.srcfilter).array
            hdf5.extend(self.datastore['rupgeoms'], meshes)
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
        elif 'rupture_model' not in oq.inputs:  # download ShakeMap
            logging.warning(
                'There is no rupture_model, the calculator will just '
                'import data without performing any calculation')
            fake = logictree.FullLogicTree.fake()
            self.datastore['full_lt'] = fake  # needed to expose the outputs
            return {}
        else:  # scenario
            self._read_scenario_ruptures()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}
        if not oq.imtls:
            raise InvalidFile('There are no intensity measure types in %s' %
                              oq.inputs['job_ini'])
        N = len(self.sitecol.complete)
        if oq.ground_motion_fields:
            M = len(oq.imtls)
            nrups = len(self.datastore['ruptures'])
            base.create_gmf_data(self.datastore, M, self.param['sec_perils'])
            self.datastore.create_dset('gmf_data/sigma_epsilon',
                                       sig_eps_dt(oq.imtls))
            self.datastore.create_dset('gmf_data/events_by_sid', U32, (N,))
            self.datastore.create_dset('gmf_data/time_by_rup',
                                       time_dt, (nrups,), fillvalue=None)

        # compute_gmfs in parallel
        nr = len(self.datastore['ruptures'])
        self.datastore.swmr_on()
        logging.info('Reading {:_d} ruptures'.format(nr))
        iterargs = ((rgetter, self.param)
                    for rgetter in gen_rupture_getters(
                            self.datastore, oq.concurrent_tasks))
        smap = parallel.Starmap(
            self.core_task.__func__, iterargs, h5=self.datastore.hdf5,
            num_cores=oq.num_cores)
        smap.monitor.save('srcfilter', self.srcfilter)
        acc = smap.reduce(self.agg_dicts, self.acc0())
        if 'gmf_data' not in self.datastore:
            return acc
        if oq.ground_motion_fields and oq.minimum_intensity:
            eids = self.datastore['gmf_data/eid'][:]
            rel_events = numpy.unique(eids)
            e = len(rel_events)
            if e == 0:
                raise RuntimeError(
                    'No GMFs were generated, perhaps they were '
                    'all below the minimum_intensity threshold')
            elif e < len(self.datastore['events']):
                self.datastore['relevant_events'] = rel_events
                logging.info('Stored %d relevant event IDs', e)
        return acc

    def post_execute(self, result):
        oq = self.oqparam
        if (not result or not oq.ground_motion_fields and not
                oq.hazard_curves_from_gmfs):
            return
        N = len(self.sitecol.complete)
        M = len(oq.imtls)  # 0 in scenario
        L = len(oq.imtls.array)
        L1 = L // (M or 1)
        # check seed dependency
        if 'gmf_data' in self.datastore:
            logging.info('Checking GMFs')
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
                self.datastore.set_shape_attrs(
                    'hcurves-rlzs', site_id=N, rlz_id=R,
                    imt=list(oq.imtls), lvl=numpy.arange(L1))
                if oq.poes:
                    P = len(oq.poes)
                    M = len(oq.imtls)
                    ds = self.datastore.create_dset(
                        'hmaps-rlzs', F32, (N, R, M, P))
                    self.datastore.set_shape_attrs(
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
                self.datastore.set_shape_attrs(
                    'hcurves-stats', site_id=N, stat=list(hstats),
                    imt=list(oq.imtls), lvl=numpy.arange(L1))
                if oq.poes:
                    P = len(oq.poes)
                    M = len(oq.imtls)
                    ds = self.datastore.create_dset(
                        'hmaps-stats', F32, (N, S, M, P))
                    self.datastore.set_shape_attrs(
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
