# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

import io
import math
import time
import os.path
import logging
import numpy
import pandas
from shapely import geometry
from openquake.baselib import config, hdf5, parallel, python3compat
from openquake.baselib.general import (
    AccumDict, humansize, block_splitter, group_array)
from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib.map_array import MapArray, get_mean_curve
from openquake.hazardlib.stats import geom_avg_std, compute_stats
from openquake.hazardlib.calc.stochastic import sample_ruptures
from openquake.hazardlib.contexts import ContextMaker, FarAwayRupture
from openquake.hazardlib.calc.filters import (
    close_ruptures, magstr, nofilter, getdefault, get_distances, SourceFilter)
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.conditioned_gmfs import ConditionedGmfComputer
from openquake.hazardlib import logictree, InvalidFile
from openquake.hazardlib.calc.stochastic import get_rup_array, rupture_dt
from openquake.hazardlib.source.rupture import (
    RuptureProxy, EBRupture, get_ruptures)
from openquake.commonlib import util, logs, readinput, datastore
from openquake.commonlib.calc import (
    gmvs_to_poes, make_hmaps, slice_dt, build_slice_by_event, RuptureImporter,
    SLICE_BY_EVENT_NSITES, get_close_mosaic_models, get_proxies)
from openquake.risklib.riskinput import str2rsi, rsi2str
from openquake.calculators import base, views
from openquake.calculators.getters import sig_eps_dt
from openquake.calculators.classical import ClassicalCalculator
from openquake.calculators.extract import Extractor
from openquake.calculators.postproc.plots import plot_avg_gmf
from openquake.calculators.base import expose_outputs
from PIL import Image

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32
F64 = numpy.float64
TWO24 = 2 ** 24
TWO32 = numpy.float64(2 ** 32)
rup_dt = numpy.dtype(
    [('rup_id', I64), ('rrup', F32), ('time', F32), ('task_no', U16)])


def rup_weight(rup):
    # rup['nsites'] is 0 if the ruptures were generated without a sitecol
    if isinstance(rup, numpy.ndarray):
        nsites = numpy.clip(rup['nsites'], 1., numpy.inf)
        return numpy.ceil(nsites / 100.)
    return math.ceil((rup['nsites'] or 1) / 100.)

# ######################## hcurves_from_gmfs ############################ #


def build_hcurves(calc):
    """
    Build the hazard curves from each realization starting from
    the stored GMFs. Works only for few sites.
    """
    oq = calc.oqparam
    # compute and save statistics; this is done in process and can
    # be very slow if there are thousands of realizations
    weights = calc.datastore['weights'][:]
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
    pmaps = {r: MapArray(calc.sitecol.sids, L1*M, 1).fill(0)
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
            smap = MapArray(calc.sitecol.sids, L1, M)
            [smap.array] = compute_stats(
                numpy.array([p.array for p in pmaps]),
                [hstats[stat]], weights)
            calc.datastore['hcurves-stats'][:, s] = smap.array
            if oq.poes:
                [hmap] = make_hmaps([smap], oq.imtls, oq.poes)
                ds[:, s] = hmap.array


# ######################## GMF calculator ############################ #

def count_ruptures(src):
    """
    Count the number of ruptures on a heavy source
    """
    return {src.source_id: src.count_ruptures()}


def get_computer(cmaker, proxy, srcfilter, station_data, station_sitecol):
    """
    :returns: GmfComputer or ConditionedGmfComputer
    """
    sids = srcfilter.close_sids(proxy, cmaker.trt)
    if len(sids) == 0:  # filtered away
        raise FarAwayRupture

    ebr = proxy.to_ebr(cmaker.trt)
    oq = cmaker.oq

    if station_sitecol:
        stations = numpy.isin(sids, station_sitecol.sids)
        if stations.any():
            station_sids = sids[stations]
            return ConditionedGmfComputer(
                ebr, srcfilter.sitecol.filtered(sids),
                srcfilter.sitecol.filtered(station_sids),
                station_data.loc[station_sids],
                oq.observed_imts,
                cmaker, oq.correl_model, oq.cross_correl,
                oq.ground_motion_correlation_params,
                oq.number_of_ground_motion_fields,
                oq._amplifier, oq._sec_perils)
        else:
            logging.warning('There are no stations!')

    return GmfComputer(
        ebr, srcfilter.sitecol.filtered(sids), cmaker,
        oq.correl_model, oq.cross_correl,
        oq._amplifier, oq._sec_perils)


def _event_based(proxies, cmaker, stations, srcfilter, shr,
                 fmon, cmon, umon, mmon):
    oq = cmaker.oq
    alldata = []
    sig_eps = []
    times = []
    max_iml = oq.get_max_iml()
    se_dt = sig_eps_dt(oq.imtls)
    mea_tau_phi = []
    for proxy in proxies:
        t0 = time.time()
        with fmon:
            if proxy['mag'] < cmaker.min_mag:
                continue
            try:
                computer = get_computer(cmaker, proxy, srcfilter, *stations)
            except FarAwayRupture:
                # skip this rupture
                continue
        if stations and stations[0] is not None:  # conditioned GMFs
            assert cmaker.scenario
            with shr['mea'] as mea, shr['tau'] as tau, shr['phi'] as phi:
                df = computer.compute_all(
                    [mea, tau, phi], max_iml, mmon, cmon, umon)
        else:  # regular GMFs
            df = computer.compute_all(None, max_iml, mmon, cmon, umon)
            if oq.mea_tau_phi:
                mtp = numpy.array(computer.mea_tau_phi, GmfComputer.mtp_dt)
                mea_tau_phi.append(mtp)
        sig_eps.append(computer.build_sig_eps(se_dt))
        dt = time.time() - t0
        times.append((proxy['id'], computer.ctx.rrup.min(), dt))
        alldata.append(df)
    times = numpy.array([tup + (fmon.task_no,) for tup in times], rup_dt)
    times.sort(order='rup_id')
    if sum(len(df) for df in alldata) == 0:
        return dict(gmfdata={}, times=times, sig_eps=())

    gmfdata = pandas.concat(alldata)  # ~40 MB
    dic = dict(gmfdata={k: gmfdata[k].to_numpy() for k in gmfdata.columns},
               times=times, sig_eps=numpy.concatenate(sig_eps, dtype=se_dt))
    if oq.mea_tau_phi:
        mtpdata = numpy.concatenate(mea_tau_phi, dtype=GmfComputer.mtp_dt)
        dic['mea_tau_phi'] = {col: mtpdata[col] for col in mtpdata.dtype.names}
    return dic


def event_based(proxies, cmaker, sitecol, stations, dstore, monitor):
    """
    Compute GMFs and optionally hazard curves
    """
    if isinstance(dstore, str):
        # when passing ruptures.hdf5
        dstore = hdf5.File(dstore)
    oq = cmaker.oq
    rmon = monitor('reading sites and ruptures', measuremem=True)
    fmon = monitor('instantiating GmfComputer', measuremem=False)
    mmon = monitor('computing mean_stds', measuremem=False)
    cmon = monitor('computing gmfs', measuremem=False)
    umon = monitor('updating gmfs', measuremem=False)
    cmaker.scenario = 'scenario' in oq.calculation_mode
    with dstore, rmon:
        srcfilter = SourceFilter(
            sitecol.complete, oq.maximum_distance(cmaker.trt))
        dset = dstore['rupgeoms']
        for proxy in proxies:
            proxy.geom = dset[proxy['geom_id']]
    for block in block_splitter(proxies, 20_000, rup_weight):
        yield _event_based(block, cmaker, stations, srcfilter,
                           monitor.shared, fmon, cmon, umon, mmon)


def filter_stations(station_df, complete, rup, maxdist):
    """
    :param station_df: DataFrame with the stations
    :param complete: complete SiteCollection
    :param rup: rupture
    :param maxdist: maximum distance
    :returns: filtered (station_df, station_sitecol)
    """
    ns = len(station_df)
    ok = (get_distances(rup, complete, 'rrup') <= maxdist) & numpy.isin(
        complete.sids, station_df.index)
    station_sites = complete.filter(ok)
    if station_sites is None:
        station_data = None
        logging.warning('Discarded %d/%d stations more distant than %d km, '
                        'switching to the unconditioned GMF computer',
                        ns, ns, maxdist)
    else:
        station_data = station_df[
            numpy.isin(station_df.index, station_sites.sids)]
        assert len(station_data) == len(station_sites), (
            len(station_data), len(station_sites))
        if len(station_data) < ns:
            logging.info('Discarded %d/%d stations more distant than %d km',
                         ns - len(station_data), ns, maxdist)
    return station_data, station_sites


def starmap_from_rups_hdf5(oq, sitecol, dstore):
    """
    :returns: a Starmap instance sending event_based tasks
    """
    ruptures_hdf5 = oq.inputs['rupture_model']
    trts = {}
    rlzs_by_gsim = {}
    with hdf5.File(ruptures_hdf5) as r:
        for model in r['full_lt']:
            full_lt = r[f'full_lt/{model}']
            trts[model] = full_lt.trts
            logging.info('Building rlzs_by_gsim for %s', model)
            for trt_smr, rbg in full_lt.get_rlzs_by_gsim_dic().items():
                rlzs_by_gsim[model, trt_smr] = rbg
        dstore['full_lt'] = full_lt  # saving the last lt (hackish)
        r.copy('events', dstore.hdf5) # saving the events
        logging.info('Selecting the ruptures close to the sites')
        rups = close_ruptures(r['ruptures'][:], sitecol)
        dstore['ruptures'] = rups
        R = full_lt.num_samples
        dstore['weights'] = numpy.ones(R) / R
    rups_dic = group_array(rups, 'model', 'trt_smr')
    totw = sum(rup_weight(rups).sum() for rups in rups_dic.values())
    maxw = totw / (oq.concurrent_tasks or 1)
    extra = sitecol.array.dtype.names
    dstore.swmr_on()
    smap = parallel.Starmap(event_based, h5=dstore.hdf5)
    logging.info('Computing the GMFs')
    for (model, trt_smr), rups in rups_dic.items():
        model = model.decode('ascii')
        trt = trts[model][trt_smr // TWO24]
        proxies = get_proxies(ruptures_hdf5, rups)
        mags = numpy.unique(numpy.round(rups['mag'], 2))
        oq.mags_by_trt = {trt: [magstr(mag) for mag in mags]}
        cmaker = ContextMaker(trt, rlzs_by_gsim[model, trt_smr],
                              oq, extraparams=extra)
        cmaker.min_mag = getdefault(oq.minimum_magnitude, trt)
        for block in block_splitter(proxies, maxw * 1.02, rup_weight):
            args = block, cmaker, sitecol, (None, None), ruptures_hdf5
            smap.submit(args)
    return smap


# NB: save_tmp is passed in event_based_risk
def starmap_from_rups(func, oq, full_lt, sitecol, dstore, save_tmp=None):
    """
    Submit the ruptures and apply `func` (event_based or ebrisk)
    """
    try:
        vs30 = sitecol.vs30
    except ValueError:  # in scenario test_case_14
        pass
    else:
        if numpy.isnan(vs30).any():
            raise ValueError('The vs30 is NaN, missing site model '
                             'or site parameter')
    set_mags(oq, dstore)
    rups = dstore['ruptures'][:]
    logging.info('Reading {:_d} ruptures'.format(len(rups)))
    logging.info('Affected sites ~%.0f per rupture, max=%.0f',
                 rups['nsites'].mean(), rups['nsites'].max())
    allproxies = [RuptureProxy(rec) for rec in rups]
    if "station_data" in oq.inputs:
        trt = full_lt.trts[0]
        proxy = allproxies[0]
        proxy.geom = dstore['rupgeoms'][proxy['geom_id']]
        rup = proxy.to_ebr(trt).rupture
        station_df = dstore.read_df('station_data', 'site_id')
        maxdist = (oq.maximum_distance_stations or
                   oq.maximum_distance['default'][-1][1])
        station_data, station_sites = filter_stations(
            station_df, sitecol.complete, rup, maxdist)
    else:
        station_data, station_sites = None, None

    maxw = sum(rup_weight(p) for p in allproxies) / (
        oq.concurrent_tasks or 1)
    logging.info('maxw = {:_d}'.format(round(maxw)))
    if station_data is not None:
        # assume scenario with a single true rupture
        rlzs_by_gsim = full_lt.get_rlzs_by_gsim(0)
        cmaker = ContextMaker(trt, rlzs_by_gsim, oq)
        cmaker.scenario = True
        maxdist = oq.maximum_distance(cmaker.trt)
        srcfilter = SourceFilter(sitecol.complete, maxdist)
        computer = get_computer(
            cmaker, proxy, srcfilter, station_data, station_sites)
        G = len(cmaker.gsims)
        M = len(cmaker.imts)
        N = len(computer.sitecol)
        size = 2 * G * M * N * N * 8  # tau, phi
        msg = f'{G=} * {M=} * {humansize(N*N*8)} * 2'
        logging.info('Requiring %s for tau, phi [%s]', humansize(size), msg)
        if size > float(config.memory.conditioned_gmf_gb) * 1024**3:
            raise ValueError(
                f'The calculation is too large: {G=}, {M=}, {N=}. '
                'You must reduce the number of sites i.e. maximum_distance')
        mea, tau, phi = computer.get_mea_tau_phi(dstore.hdf5)
        del proxy.geom  # to reduce data transfer

    dstore.swmr_on()
    smap = parallel.Starmap(func, h5=dstore.hdf5)
    if save_tmp:
        save_tmp(smap.monitor)

    # NB: for conditioned scenarios we are looping on a single trt
    toml_gsims = []
    for trt_smr, start, stop in dstore['trt_smr_start_stop']:
        proxies = allproxies[start:stop]
        trt = full_lt.trts[trt_smr // TWO24]
        extra = sitecol.array.dtype.names
        rlzs_by_gsim = full_lt.get_rlzs_by_gsim(trt_smr)
        cmaker = ContextMaker(trt, rlzs_by_gsim, oq, extraparams=extra)
        cmaker.min_mag = getdefault(oq.minimum_magnitude, trt)
        for gsim in rlzs_by_gsim:
            toml_gsims.append(gsim._toml)
        if station_data is not None:
            if parallel.oq_distribute() in ('zmq', 'slurm'):
                logging.error('Conditioned scenarios are not meant to be run'
                              ' on a cluster')
            smap.share(mea=mea, tau=tau, phi=phi)
        # producing slightly less than concurrent_tasks thanks to the 1.02
        for block in block_splitter(proxies, maxw * 1.02, rup_weight):
            args = block, cmaker, sitecol, (station_data, station_sites), dstore
            smap.submit(args)
    dstore['gsims'] = numpy.array(toml_gsims)
    return smap


def set_mags(oq, dstore):
    """
    Set the attribute oq.mags_by_trt
    """
    if 'source_mags' in dstore:
        # classical or event_based
        oq.mags_by_trt = {
            trt: python3compat.decode(dset[:])
            for trt, dset in dstore['source_mags'].items()}
    elif oq.ruptures_hdf5:
        pass                
    elif 'ruptures' in dstore:
        # scenario
        trts = dstore['full_lt'].trts
        ruptures = dstore['ruptures'][:]
        dic = {}
        for trti, trt in enumerate(trts):
            rups = ruptures[ruptures['trt_smr'] == trti]
            mags = numpy.unique(numpy.round(rups['mag'], 2))
            dic[trt] = ['%.02f' % mag for mag in mags]
        oq.mags_by_trt = dic


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
        gmvs = numpy.ones((E, M), F32) * min_iml
        gmvs[eid.to_numpy()] = df.to_numpy()
        dic[sid] = geom_avg_std(gmvs, weights)
    return dic


def read_gsim_lt(oq):
    # in impact mode the gsim_lt is read from the exposure.hdf5 file
    if oq.impact and not oq.shakemap_uri:
        if not oq.mosaic_model:
            if oq.rupture_dict:
                lon, lat = [oq.rupture_dict['lon'], oq.rupture_dict['lat']]
            elif oq.rupture_xml:
                hypo = readinput.get_rupture(oq).hypocenter
                lon, lat = [hypo.x, hypo.y]
            mosaic_models = get_close_mosaic_models(lon, lat, 5)
            # NOTE: using the first mosaic model
            oq.mosaic_model = mosaic_models[0]
            if len(mosaic_models) > 1:
                logging.info('Using the "%s" model' % oq.mosaic_model)
        [expo_hdf5] = oq.inputs['exposure']
        if oq.mosaic_model == '???':
            raise ValueError(
                '(%(lon)s, %(lat)s) is not covered by the mosaic!' %
                oq.rupture_dict)
        if oq.gsim != '[FromFile]':
            raise ValueError(
                'In Aristotle mode the gsim can not be specified in'
                ' the job.ini: %s' % oq.gsim)
        if oq.tectonic_region_type == '*':
            raise ValueError(
                'The tectonic_region_type parameter must be specified')
        gsim_lt = logictree.GsimLogicTree.from_hdf5(
            expo_hdf5, oq.mosaic_model, oq.tectonic_region_type.encode('utf8'))
    else:
        gsim_lt = readinput.get_gsim_lt(oq)
    return gsim_lt


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

    def counting_ruptures(self):
        """
        Sets src.num_ruptures and src.offset
        """
        sources = self.csm.get_sources()
        logging.info('Counting the ruptures in the CompositeSourceModel')
        self.datastore.swmr_on()
        with self.monitor('counting ruptures', measuremem=True):
            nrups = parallel.Starmap(  # weighting the heavy sources
                count_ruptures, [(src,) for src in sources
                                 if src.code in b'AMSC'],
                h5=self.datastore.hdf5,
                progress=logging.debug).reduce()
            # NB: multifault sources must be considered light to avoid a large
            # data transfer, even if .count_ruptures can be slow
            for src in sources:
                try:
                    src.num_ruptures = nrups[src.source_id]
                except KeyError:  # light sources
                    src.num_ruptures = src.count_ruptures()
                src.weight = src.num_ruptures
            self.csm.fix_src_offset()  # NB: must be AFTER count_ruptures
        maxweight = sum(sg.weight for sg in self.csm.src_groups) / (
            self.oqparam.concurrent_tasks or 1)
        return maxweight

    def build_events_from_sources(self):
        """
        Prefilter the composite source model and store the source_info
        """
        oq = self.oqparam
        maxweight = self.counting_ruptures()
        eff_ruptures = AccumDict(accum=0)  # grp_id => potential ruptures
        source_data = AccumDict(accum=[])
        allargs = []
        srcfilter = self.srcfilter
        if 'geometry' in oq.inputs:
            fname = oq.inputs['geometry']
            with fiona.open(fname) as f:
                model_geom = geometry.shape(f[0].geometry)
        elif oq.mosaic_model:  # 3-letter mosaic model
            mosaic_df = readinput.read_mosaic_df(buffer=0).set_index('code')
            mmodel = 'CAN' if oq.mosaic_model == 'CND' else oq.mosaic_model
            model_geom = mosaic_df.loc[mmodel].geom
        logging.info('Building ruptures')
        g_index = 0
        for sg_id, sg in enumerate(self.csm.src_groups):
            if not sg.sources:
                continue
            rgb = self.full_lt.get_rlzs_by_gsim(sg.sources[0].trt_smr)
            cmaker = ContextMaker(sg.trt, rgb, oq)
            cmaker.gid = numpy.arange(g_index, g_index + len(rgb))
            g_index += len(rgb)
            cmaker.model = oq.mosaic_model or '???'
            if oq.mosaic_model or 'geometry' in oq.inputs:
                cmaker.model_geom = model_geom
            for src_group in sg.split(maxweight):
                allargs.append((src_group, cmaker, srcfilter.sitecol))
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            sample_ruptures, allargs, h5=self.datastore.hdf5)
        mon = self.monitor('saving ruptures')
        self.nruptures = 0  # estimated classical ruptures within maxdist
        t0 = time.time()
        tot_ruptures = 0
        filtered_ruptures = 0
        for dic in smap:
            # NB: dic should be a dictionary, but when the calculation dies
            # for an OOM it can become None, thus giving a very confusing error
            if dic is None:
                raise MemoryError('You ran out of memory!')
            rup_array = dic['rup_array']
            tot_ruptures += len(rup_array)
            if len(rup_array) == 0:
                continue
            geom = rup_array.geom
            filtered_ruptures += len(rup_array)
            if dic['source_data']:
                source_data += dic['source_data']
            if dic['eff_ruptures']:
                eff_ruptures += dic['eff_ruptures']
            with mon:
                self.nruptures += len(rup_array)
                # NB: the ruptures will we reordered and resaved later
                hdf5.extend(self.datastore['ruptures'], rup_array)
                hdf5.extend(self.datastore['rupgeoms'], geom)
        t1 = time.time()
        logging.info(f'Generated {filtered_ruptures}/{tot_ruptures} ruptures,'
                     f' stored in {t1 - t0} seconds')
        if len(self.datastore['ruptures']) == 0:
            raise RuntimeError('No ruptures were generated, perhaps the '
                               'effective investigation time is too short')

        # don't change the order of the 3 things below!
        self.store_source_info(source_data)
        self.store_rlz_info(eff_ruptures)
        imp = RuptureImporter(self.datastore)
        with self.monitor('saving ruptures and events'):
            imp.import_rups_events(self.datastore.getitem('ruptures')[()])

    def agg_dicts(self, acc, result):
        """
        :param acc: accumulator dictionary
        :param result: an AccumDict with events, ruptures and gmfs
        """
        if result is None:  # instead of a dict
            raise MemoryError('You ran out of memory!')
        sav_mon = self.monitor('saving gmfs')
        primary = self.oqparam.get_primary_imtls()
        sec_imts = self.oqparam.sec_imts
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

            # optionally save mea_tau_phi
            mtp = result.pop('mea_tau_phi', None)
            if mtp:
                for col, arr in mtp.items():
                    hdf5.extend(self.datastore[f'mea_tau_phi/{col}'], arr)
        return acc

    def _read_scenario_ruptures(self):
        oq = self.oqparam
        gsim_lt = read_gsim_lt(oq)
        trts = list(gsim_lt.values)
        if (str(gsim_lt.branches[0].gsim) == '[FromFile]'
                and 'gmfs' not in oq.inputs):
            raise InvalidFile('%s: missing gsim or gsim_logic_tree_file' %
                              oq.inputs['job_ini'])
        G = gsim_lt.get_num_paths()
        if oq.calculation_mode.startswith('scenario'):
            ngmfs = oq.number_of_ground_motion_fields
        if oq.rupture_dict or oq.rupture_xml:
            # check the number of branchsets
            bsets = len(gsim_lt._ltnode)
            if bsets > 1:
                raise InvalidFile(
                    '%s for a scenario calculation must contain a single '
                    'branchset, found %d!' % (oq.inputs['job_ini'], bsets))
            [(trt_smr, rlzs_by_gsim)] = gsim_lt.get_rlzs_by_gsim_dic().items()
            trt = trts[trt_smr // TWO24]
            rup = readinput.get_rupture(oq)
            oq.mags_by_trt = {trt: [magstr(rup.mag)]}
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
        self.datastore['full_lt'] = fake
        self.store_rlz_info({})  # store weights
        self.save_params()
        imp = RuptureImporter(self.datastore)
        imp.import_rups_events(rup_array)

    def execute(self):
        oq = self.oqparam
        if oq.impact and oq.shakemap_uri:
            # this is creating gmf_data
            base.store_gmfs_from_shakemap(self, self.sitecol, self.assetcol)
            return {}
        dstore = self.datastore
        E = None
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
            self.full_lt = dstore.parent['full_lt'].init()
            set_mags(oq, dstore)
        elif hasattr(self, 'csm'):  # from sources
            set_mags(oq, dstore)
            self.build_events_from_sources()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}
        elif not oq.rupture_dict and 'rupture_model' not in oq.inputs:
            logging.warning(
                'There is no rupture_model, the calculator will just '
                'import data without performing any calculation')
            fake = logictree.FullLogicTree.fake()
            dstore['full_lt'] = fake  # needed to expose the outputs
            dstore['weights'] = [1.]
            return {}
        elif oq.ruptures_hdf5:
            with hdf5.File(oq.ruptures_hdf5) as r:
                E = len(r['events'])
        else:  # scenario
            self._read_scenario_ruptures()
            if (oq.ground_motion_fields is False and
                    oq.hazard_curves_from_gmfs is False):
                return {}

        if oq.ground_motion_fields:
            prim_imts = oq.get_primary_imtls()
            base.create_gmf_data(dstore, prim_imts, oq.sec_imts,
                                 E=E, R=oq.number_of_logic_tree_samples)
            dstore.create_dset('gmf_data/sigma_epsilon', sig_eps_dt(oq.imtls))
            dstore.create_dset('gmf_data/rup_info', rup_dt)
            if self.N >= SLICE_BY_EVENT_NSITES:
                dstore.create_dset('gmf_data/slice_by_event', slice_dt)

        # event_based in parallel
        if oq.ruptures_hdf5:
            smap = starmap_from_rups_hdf5(oq, self.sitecol, dstore)
        else:
            smap = starmap_from_rups(
                event_based, oq, self.full_lt, self.sitecol, dstore)
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
            return

        rlzs = self.datastore['events'][:]['rlz_id']
        self.weights = self.datastore['weights'][:][rlzs]
        gmf_df = self.datastore.read_df('gmf_data', 'sid')
        for sec_imt in self.oqparam.sec_imts:  # ignore secondary perils
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
        avg_gmf = numpy.zeros((2, len(self.sitecol.complete), M), F32)
        for sid, avgstd in compute_avg_gmf(
                gmf_df, self.weights, self.oqparam.min_iml).items():
            avg_gmf[:, sid] = avgstd
        self.datastore['avg_gmf'] = avg_gmf
        # make avg_gmf plots only if running via the webui
        if os.environ.get('OQ_APPLICATION_MODE') == 'ARISTOTLE':
            imts = list(self.oqparam.imtls)
            ex = Extractor(self.datastore.calc_id)
            for imt in imts:
                plt = plot_avg_gmf(ex, imt)
                bio = io.BytesIO()
                plt.savefig(bio, format='png', bbox_inches='tight')
                fig_path = f'png/avg_gmf-{imt}.png'
                logging.info(f'Saving {fig_path} into the datastore')
                self.datastore[fig_path] = Image.open(bio)

    def post_execute(self, dummy):
        oq = self.oqparam
        if not oq.ground_motion_fields or 'gmf_data' not in self.datastore:
            return
        # check seed dependency unless the number of GMFs is huge
        size = self.datastore.getsize('gmf_data/gmv_0')
        if 'gmf_data' in self.datastore and size < 4E9 and not oq.ruptures_hdf5:
            # TODO: check why there is an error for ruptures_hdf5
            logging.info('Checking stored GMFs')
            msg = views.view('extreme_gmvs', self.datastore)
            logging.info(msg)
        if self.datastore.parent:
            self.datastore.parent.open('r')
        if oq.hazard_curves_from_gmfs:
            if size > 4E6:
                msg = 'gmf_data has {:_d} rows'.format(size)
                raise RuntimeError(f'{msg}: too big to compute the hcurves')
            build_hcurves(self)
            if oq.compare_with_classical:  # compute classical curves
                export_dir = os.path.join(oq.export_dir, 'cl')
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir)
                oq.export_dir = export_dir
                oq.calculation_mode = 'classical'
                with logs.init(vars(oq)) as log:
                    self.cl = ClassicalCalculator(oq, log.calc_id)
                    # TODO: perhaps it is possible to avoid reprocessing the
                    # source model, however usually this is quite fast and
                    # does not dominate the computation
                    self.cl.run()
                    expose_outputs(self.cl.datastore)
                    all = slice(None)
                    for imt in oq.imtls:
                        cl_mean_curves = get_mean_curve(
                            self.datastore, imt, all)
                        eb_mean_curves = get_mean_curve(
                            self.datastore, imt, all)
                        self.rdiff, index = util.max_rel_diff_index(
                            cl_mean_curves, eb_mean_curves)
                        logging.warning(
                            'Relative difference with the classical '
                            'mean curves: %d%% at site index %d, imt=%s',
                            self.rdiff * 100, index, imt)
