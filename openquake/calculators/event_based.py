# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
import logging
import operator
import numpy
import pandas

from openquake.baselib import hdf5, parallel, python3compat
from openquake.baselib.general import (
    AccumDict, humansize, groupby, block_splitter)
from openquake.hazardlib.probability_map import ProbabilityMap, get_mean_curve
from openquake.hazardlib.stats import geom_avg_std, compute_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.gsim.base import ContextMaker, FarAwayRupture
from openquake.hazardlib.calc.filters import nofilter, getdefault, SourceFilter
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.conditioned_gmfs import ConditionedGmfComputer
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.calc.stochastic import get_rup_array, rupture_dt
from openquake.hazardlib.source.rupture import (
    RuptureProxy, EBRupture, get_ruptures)
from openquake.commonlib import util, logs, readinput, logictree, datastore
from openquake.commonlib.calc import (
    gmvs_to_poes, make_hmaps, slice_dt, build_slice_by_event, RuptureImporter,
    SLICE_BY_EVENT_NSITES)
from openquake.risklib.riskinput import str2rsi, rsi2str
from openquake.calculators import base, views
from openquake.calculators.getters import get_rupture_getters, sig_eps_dt
from openquake.calculators.classical import ClassicalCalculator
from openquake.engine import engine

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32
F64 = numpy.float64
TWO24 = 2 ** 24
TWO32 = numpy.float64(2 ** 32)

rup_dt = numpy.dtype(
    [('rup_id', I64), ('nsites', U16), ('rrup', F32), ('time', F32),
    ('task_no', U16)])

# ######################## hcurves_from_gmfs ############################ #


def build_hcurves(calc):
    """
    Build the hazard curves from each realization starting from
    the stored GMFs. Works only for few sites.
    """
    oq = calc.oqparam
    rlzs = calc.full_lt.get_realizations()
    # compute and save statistics; this is done in process and can
    # be very slow if there are thousands of realizations
    weights = [rlz.weight['weight'] for rlz in rlzs]
    # NB: in the future we may want to save to individual hazard
    # curves if oq.individual_rlzs is set; for the moment we
    # save the statistical curves only
    hstats = oq.hazard_stats()
    S = len(hstats)
    R = len(weights)
    N = calc.N
    M = len(oq.imtls)
    L1 = oq.imtls.size // M
    gmf_df = calc.datastore.read_df('gmf_data', 'eid')
    ev_df = calc.datastore.read_df('events', 'id')[['rlz_id']]
    gmf_df = gmf_df.join(ev_df)
    hc_mon = calc._monitor('building hazard curves', measuremem=False)
    hcurves = {}
    for (sid, rlz), df in gmf_df.groupby(['sid', 'rlz_id']):
        with hc_mon:
            poes = gmvs_to_poes(df, oq.imtls, oq.ses_per_logic_tree_path)
            for m, imt in enumerate(oq.imtls):
                hcurves[rsi2str(rlz, sid, imt)] = poes[m]
    pmaps = {r: ProbabilityMap(calc.sitecol.sids, L1*M, 1).fill(0)
             for r in range(R)}
    for key, poes in hcurves.items():
        r, sid, imt = str2rsi(key)
        array = pmaps[r].array[sid, oq.imtls(imt), 0]
        array[:] = 1. - (1. - array) * (1. - poes)
    pmaps = [p.reshape(N, M, L1) for p in pmaps.values()]
    if oq.individual_rlzs:
        logging.info('Saving individual hazard curves')
        calc.datastore.create_dset('hcurves-rlzs', F32, (N, R, M, L1))
        calc.datastore.set_shape_descr(
            'hcurves-rlzs', site_id=N, rlz_id=R,
            imt=list(oq.imtls), lvl=numpy.arange(L1))
        if oq.poes:
            P = len(oq.poes)
            M = len(oq.imtls)
            ds = calc.datastore.create_dset(
                'hmaps-rlzs', F32, (N, R, M, P))
            calc.datastore.set_shape_descr(
                'hmaps-rlzs', site_id=N, rlz_id=R,
                imt=list(oq.imtls), poe=oq.poes)
        for r in range(R):
            calc.datastore['hcurves-rlzs'][:, r] = pmaps[r].array
            if oq.poes:
                [hmap] = make_hmaps([pmaps[r]], oq.imtls, oq.poes)
                ds[:, r] = hmap.array

    if S:
        logging.info('Computing statistical hazard curves')
        calc.datastore.create_dset('hcurves-stats', F32, (N, S, M, L1))
        calc.datastore.set_shape_descr(
            'hcurves-stats', site_id=N, stat=list(hstats),
            imt=list(oq.imtls), lvl=numpy.arange(L1))
        if oq.poes:
            P = len(oq.poes)
            M = len(oq.imtls)
            ds = calc.datastore.create_dset(
                'hmaps-stats', F32, (N, S, M, P))
            calc.datastore.set_shape_descr(
                'hmaps-stats', site_id=N, stat=list(hstats),
                imt=list(oq.imtls), poes=oq.poes)
        for s, stat in enumerate(hstats):
            smap = ProbabilityMap(calc.sitecol.sids, L1, M)
            [smap.array] = compute_stats(
                numpy.array([p.array for p in pmaps]),
                [hstats[stat]], weights)
            calc.datastore['hcurves-stats'][:, s] = smap.array
            if oq.poes:
                [hmap] = make_hmaps([smap], oq.imtls, oq.poes)
                ds[:, s] = hmap.array

    if oq.compare_with_classical:  # compute classical curves
        export_dir = os.path.join(oq.export_dir, 'cl')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        oq.export_dir = export_dir
        oq.calculation_mode = 'classical'
        with logs.init('job', vars(oq)) as log:
            calc.cl = ClassicalCalculator(oq, log.calc_id)
            # TODO: perhaps it is possible to avoid reprocessing the source
            # model, however usually this is quite fast and do not dominate
            # the computation
            calc.cl.run()
            engine.expose_outputs(calc.cl.datastore)
            all = slice(None)
            for imt in oq.imtls:
                cl_mean_curves = get_mean_curve(calc.datastore, imt, all)
                eb_mean_curves = get_mean_curve(calc.datastore, imt, all)
                calc.rdiff, index = util.max_rel_diff_index(
                    cl_mean_curves, eb_mean_curves)
                logging.warning(
                    'Relative difference with the classical '
                    'mean curves: %d%% at site index %d, imt=%s',
                    calc.rdiff * 100, index, imt)


# ######################## GMF calculator ############################ #

def count_ruptures(src):
    """
    Count the number of ruptures on a heavy source
    """
    return {src.source_id: src.count_ruptures()}


def strip_zeros(gmf_df):
    # remove the rows with all zero values
    df = gmf_df[gmf_df.columns[3:]]  # strip eid, sid, rlz
    assert str(df.gmv_0.dtype) == 'float32', df.gmv_0.dtype
    ok = df.to_numpy().sum(axis=1) > 0
    return gmf_df[ok]


def get_computer(cmaker, proxy, sids, sitecol, station_sitecol, station_data):
    """
    :returns: GmfComputer or ConditionedGmfComputer
    """
    oq = cmaker.oq
    trt = cmaker.trt
    ebr = proxy.to_ebr(trt)
    if station_sitecol:
        stations = numpy.isin(sids, station_sitecol.sids)
        if stations.any():
            # if there are stations close, use them
            station_sids = sids[stations]
            target_sids = sids[~stations]
            return ConditionedGmfComputer(
                ebr, sitecol.filtered(target_sids),
                sitecol.filtered(station_sids),
                station_data.loc[station_sids],
                oq.observed_imts,
                cmaker, oq.correl_model, oq.cross_correl,
                oq.ground_motion_correlation_params,
                oq.number_of_ground_motion_fields,
                oq._amplifier, oq._sec_perils)

    return GmfComputer(
        ebr, sitecol.filtered(sids), cmaker,
        oq.correl_model, oq.cross_correl,
        oq._amplifier, oq._sec_perils)


def gen_event_based(allproxies, cmaker, dstore, monitor):
    """
    Launcher of event_based tasks
    """
    fmon = monitor('filtering ruptures', measuremem=False)
    blocksize = 20
    t0 = time.time()
    n = 0
    for proxies in block_splitter(allproxies, blocksize):
        n += len(proxies)
        with fmon:
            computers = get_computers(proxies, cmaker, dstore)
        if not computers:
            continue
        yield event_based(computers, monitor)
        rem = allproxies[n:]  # remaining ruptures
        dt = time.time() - t0
        if dt > cmaker.oq.time_per_task and len(rem) >= 3:
            s = len(rem) // 3
            yield gen_event_based, rem[:s], cmaker, dstore
            yield gen_event_based, rem[s:2*s], cmaker, dstore
            yield gen_event_based, rem[2*s:], cmaker, dstore
            return


def get_computers(proxies, cmaker, dstore):
    oq = cmaker.oq
    computers = []
    with dstore:
        sitecol = dstore['sitecol']
        srcfilter = SourceFilter(sitecol, oq.maximum_distance(cmaker.trt))
        rupgeoms = dstore['rupgeoms']
        if "station_data" in oq.inputs:
            station_data = dstore.read_df('station_data', 'site_id')
            station_sitecol = sitecol.filtered(station_data.index)
        else:
            station_data = None
            station_sitecol = None
        for proxy in proxies:
            if proxy['mag'] < cmaker.min_mag:
                continue
            sids = srcfilter.close_sids(proxy, cmaker.trt)
            if len(sids) == 0:  # filtered away
                continue
            proxy.geom = rupgeoms[proxy['geom_id']]
            try:
                computers.append(get_computer(
                    cmaker, proxy, sids, sitecol,
                    station_sitecol, station_data))
            except FarAwayRupture:
                # skip this rupture
                continue
    return computers


def event_based(computers, monitor):
    """
    Compute GMFs and optionally hazard curves
    """
    oq = computers[0].cmaker.oq
    alldata = []
    se_dt = sig_eps_dt(oq.imtls)
    sig_eps = []
    times = []  # rup_id, nsites, dt
    cmon = monitor('computing gmfs', measuremem=False)
    max_iml = oq.get_max_iml()
    scenario = 'scenario' in oq.calculation_mode
    t0 = time.time()
    for computer in computers:
            with cmon:
                df = computer.compute_all(scenario, sig_eps, max_iml)
            dt = time.time() - t0
            times.append((computer.ebrupture.id, len(computer.ctx.sids),
                          computer.ctx.rrup.min(), dt))
            alldata.append(df)
    if sum(len(df) for df in alldata):
        gmfdata = strip_zeros(pandas.concat(alldata))
    else:
        gmfdata = {}
    times = numpy.array([tup + (monitor.task_no,) for tup in times], rup_dt)
    times.sort(order='rup_id')
    if not oq.ground_motion_fields:
        gmfdata = {}
    return dict(gmfdata=todict(gmfdata), times=times,
                sig_eps=numpy.array(sig_eps, se_dt))


def todict(dframe):
    if len(dframe) == 0:
        return {}
    return {k: dframe[k].to_numpy() for k in dframe.columns}


def starmap_from_rups(func, oq, full_lt, sitecol, dstore, save_tmp=None):
    """
    Submit the ruptures and apply `func` (event_based or ebrisk)
    """
    set_mags(oq, dstore)
    nr = len(dstore['ruptures'])
    logging.info('Reading {:_d} ruptures'.format(nr))
    allproxies = [RuptureProxy(rec) for rec in dstore['ruptures'][:]]
    if "station_data" in oq.inputs:
        # this is meant to be used in conditioned scenario calculations with
        # a single rupture; we are taking the first copy of the rupture
        # (remember: _read_scenario_ruptures makes num_gmfs copies to
        # parallelize, but the conditioning process is computationally
        # expensive, so we want to avoid repeating it num_gmfs times)
        # TODO: this is ugly and must be improved upon!
        allproxies = allproxies[0:1]

    dstore.swmr_on()
    smap = parallel.Starmap(func, h5=dstore.hdf5)
    if save_tmp:
        save_tmp(smap.monitor)
    gb = groupby(allproxies, operator.itemgetter('trt_smr'))
    for trt_smr, proxies in gb.items():
        trt = full_lt.trts[trt_smr // TWO24]
        extra = sitecol.array.dtype.names
        rlzs_by_gsim = full_lt.get_rlzs_by_gsim(trt_smr)
        cmaker = ContextMaker(trt, rlzs_by_gsim, oq, extraparams=extra)
        cmaker.min_mag = getdefault(oq.minimum_magnitude, trt)
        hint = 2 * nr / (oq.concurrent_tasks or 1)  # double size blocks
        for block in block_splitter(proxies, hint):
            smap.submit((block, cmaker, dstore))
    return smap


def set_mags(oq, dstore):
    """
    Set the attribute oq.mags_by_trt
    """
    if 'source_mags' in dstore:
        oq.mags_by_trt = {
            trt: python3compat.decode(dset[:])
            for trt, dset in dstore['source_mags'].items()}


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
    core_task = event_based
    is_stochastic = True
    accept_precalc = ['event_based', 'ebrisk', 'event_based_risk']

    def init(self):
        if self.oqparam.cross_correl.__class__.__name__ == 'GodaAtkinson2009':
            logging.warning(
                'The truncation_level param is ignored with GodaAtkinson2009')
        if hasattr(self, 'csm'):
            self.check_floating_spinning()
        if hasattr(self.oqparam, 'maximum_distance'):
            self.srcfilter = self.src_filter()
        else:
            self.srcfilter = nofilter
        if not self.datastore.parent:
            self.datastore.create_dset('ruptures', rupture_dt)
            self.datastore.create_dset('rupgeoms', hdf5.vfloat32)

    def build_events_from_sources(self):
        """
        Prefilter the composite source model and store the source_info
        """
        oq = self.oqparam
        self.csm.fix_src_offset()  # NB: essential
        sources = self.csm.get_sources()

        # weighting the heavy sources
        self.datastore.swmr_on()
        nrups = parallel.Starmap(
            count_ruptures, [(src,) for src in sources if src.code in b'AMC'],
            progress=logging.debug
        ).reduce()
        for src in sources:
            try:
                src.num_ruptures = nrups[src.source_id]
            except KeyError:  # light source
                src.num_ruptures = src.count_ruptures()
            src.weight = src.num_ruptures
        maxweight = sum(sg.weight for sg in self.csm.src_groups) / (
            self.oqparam.concurrent_tasks or 1)
        eff_ruptures = AccumDict(accum=0)  # grp_id => potential ruptures
        source_data = AccumDict(accum=[])
        allargs = []
        srcfilter = self.srcfilter
        logging.info('Building ruptures')
        for sg in self.csm.src_groups:
            if not sg.sources:
                continue
            rgb = self.full_lt.get_rlzs_by_gsim(sg.sources[0].trt_smr)
            cmaker = ContextMaker(sg.trt, rgb, oq)
            for src_group in sg.split(maxweight):
                allargs.append((src_group, cmaker, srcfilter.sitecol))
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            sample_ruptures, allargs, h5=self.datastore.hdf5)
        mon = self.monitor('saving ruptures')
        self.nruptures = 0  # estimated classical ruptures within maxdist
        for dic in smap:
            # NB: dic should be a dictionary, but when the calculation dies
            # for an OOM it can become None, thus giving a very confusing error
            if dic is None:
                raise MemoryError('You ran out of memory!')
            rup_array = dic['rup_array']
            if len(rup_array) == 0:
                continue
            if dic['source_data']:
                source_data += dic['source_data']
            if dic['eff_ruptures']:
                eff_ruptures += dic['eff_ruptures']
            with mon:
                self.nruptures += len(rup_array)
                # NB: the ruptures will we reordered and resaved later
                hdf5.extend(self.datastore['ruptures'], rup_array)
                hdf5.extend(self.datastore['rupgeoms'], rup_array.geom)
        if len(self.datastore['ruptures']) == 0:
            raise RuntimeError('No ruptures were generated, perhaps the '
                               'investigation time is too short')

        # don't change the order of the 3 things below!
        self.store_source_info(source_data)
        self.store_rlz_info(eff_ruptures)
        imp = RuptureImporter(self.datastore)
        with self.monitor('saving ruptures and events'):
            imp.import_rups_events(
                self.datastore.getitem('ruptures')[()], get_rupture_getters)

    def agg_dicts(self, acc, result):
        """
        :param acc: accumulator dictionary
        :param result: an AccumDict with events, ruptures and gmfs
        """
        if result is None:  # instead of a dict
            raise MemoryError('You ran out of memory!')
        sav_mon = self.monitor('saving gmfs')
        primary = self.oqparam.get_primary_imtls()
        sec_imts = self.oqparam.get_sec_imts()
        with sav_mon:
            gmfdata = result.pop('gmfdata')
            if len(gmfdata):
                df = pandas.DataFrame(gmfdata)
                dset = self.datastore['gmf_data/sid']
                times = result.pop('times')
                hdf5.extend(self.datastore['gmf_data/rup_info'], times)
                if self.N >= SLICE_BY_EVENT_NSITES:
                    sbe = build_slice_by_event(
                        df.eid.to_numpy(), self.offset)
                    hdf5.extend(self.datastore['gmf_data/slice_by_event'], sbe)
                hdf5.extend(dset, df.sid.to_numpy())
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
        return acc

    def _read_scenario_ruptures(self):
        oq = self.oqparam
        gsim_lt = readinput.get_gsim_lt(self.oqparam)
        G = gsim_lt.get_num_paths()
        if oq.calculation_mode.startswith('scenario'):
            ngmfs = oq.number_of_ground_motion_fields
        if oq.inputs['rupture_model'].endswith('.xml'):
            # check the number of branchsets
            bsets = len(gsim_lt._ltnode)
            if bsets > 1:
                raise InvalidFile(
                    '%s for a scenario calculation must contain a single '
                    'branchset, found %d!' % (oq.inputs['job_ini'], bsets))
            [(trt, rlzs_by_gsim)] = gsim_lt.get_rlzs_by_gsim_trt().items()
            rup = readinput.get_rupture(oq)
            oq.mags_by_trt = {trt: ['%.2f' % rup.mag]}
            self.cmaker = ContextMaker(trt, rlzs_by_gsim, oq)
            if self.N > oq.max_sites_disagg:  # many sites, split rupture
                ebrs = []
                for i in range(ngmfs):
                    ebr = EBRupture(rup, 0, 0, G, i, e0=i * G)
                    ebr.seed = oq.ses_seed + i
                    ebrs.append(ebr)
            else:  # keep a single rupture with a big occupation number
                ebrs = [EBRupture(rup, 0, 0, G * ngmfs, 0)]
                ebrs[0].seed = oq.ses_seed
            srcfilter = SourceFilter(self.sitecol, oq.maximum_distance(trt))
            aw = get_rup_array(ebrs, srcfilter)
            if len(aw) == 0:
                raise RuntimeError(
                    'The rupture is too far from the sites! Please check the '
                    'maximum_distance and the position of the rupture')
        elif oq.inputs['rupture_model'].endswith('.csv'):
            aw = get_ruptures(oq.inputs['rupture_model'])
            if len(gsim_lt.values) == 1:  # fix for scenario_damage/case_12
                aw['trt_smr'] = 0  # a single TRT
            if oq.calculation_mode.startswith('scenario'):
                # rescale n_occ by ngmfs and nrlzs
                aw['n_occ'] *= ngmfs * gsim_lt.get_num_paths()
        else:
            raise InvalidFile("Something wrong in %s" % oq.inputs['job_ini'])
        rup_array = aw.array
        hdf5.extend(self.datastore['rupgeoms'], aw.geom)

        if len(rup_array) == 0:
            raise RuntimeError(
                'There are no sites within the maximum_distance'
                ' of %s km from the rupture' % oq.maximum_distance(
                    rup.tectonic_region_type)(rup.mag))

        fake = logictree.FullLogicTree.fake(gsim_lt)
        self.realizations = fake.get_realizations()
        self.datastore['full_lt'] = fake
        self.store_rlz_info({})  # store weights
        self.save_params()
        imp = RuptureImporter(self.datastore)
        imp.import_rups_events(rup_array, get_rupture_getters)

    def execute(self):
        oq = self.oqparam
        dstore = self.datastore
        if oq.ground_motion_fields and oq.min_iml.sum() == 0:
            logging.warning('The GMFs are not filtered: '
                            'you may want to set a minimum_intensity')
        elif oq.minimum_intensity:
            logging.info('minimum_intensity=%s', oq.minimum_intensity)
        else:
            logging.info('min_iml=%s', oq.min_iml)
        self.offset = 0
        if oq.hazard_calculation_id:  # from ruptures
            dstore.parent = datastore.read(oq.hazard_calculation_id)
            self.full_lt = dstore.parent['full_lt']
            set_mags(oq, dstore)
        elif hasattr(self, 'csm'):  # from sources
            set_mags(oq, dstore)
            self.build_events_from_sources()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}
        elif 'rupture_model' not in oq.inputs:
            logging.warning(
                'There is no rupture_model, the calculator will just '
                'import data without performing any calculation')
            fake = logictree.FullLogicTree.fake()
            dstore['full_lt'] = fake  # needed to expose the outputs
            dstore['weights'] = [1.]
            return {}
        else:  # scenario
            self._read_scenario_ruptures()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}

        if oq.ground_motion_fields:
            imts = oq.get_primary_imtls()
            base.create_gmf_data(dstore, imts, oq.get_sec_imts())
            dstore.create_dset('gmf_data/sigma_epsilon', sig_eps_dt(oq.imtls))
            dstore.create_dset('gmf_data/rup_info', rup_dt)
            if self.N >= SLICE_BY_EVENT_NSITES:
                dstore.create_dset('gmf_data/slice_by_event', slice_dt)

        # event_based in parallel
        smap = starmap_from_rups(
            gen_event_based, oq, self.full_lt, self.sitecol, dstore)
        acc = smap.reduce(self.agg_dicts)
        if 'gmf_data' not in dstore:
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
        maxsize = self.oqparam.gmf_max_gb * 1024 ** 3
        logging.info(f'Stored {humansize(size)} of GMFs')
        if size > maxsize:
            logging.warning(
                f'There are more than {humansize(maxsize)} of GMFs,'
                ' not computing avg_gmf')
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

    def post_execute(self, dummy):
        oq = self.oqparam
        if not oq.ground_motion_fields or 'gmf_data' not in self.datastore:
            return
        # check seed dependency unless the number of GMFs is huge
        size = self.datastore.getsize('gmf_data/gmv_0')
        if 'gmf_data' in self.datastore and size < 4E8:
            logging.info('Checking stored GMFs')
            msg = views.view('extreme_gmvs', self.datastore)
            logging.warning(msg)
        if self.datastore.parent:
            self.datastore.parent.open('r')
        if oq.hazard_curves_from_gmfs:
            if size > 4E6:
                msg = 'gmf_data has {:_d} rows'.format(size)
                raise RuntimeError(f'{msg}: too big to compute the hcurves')
            build_hcurves(self)
