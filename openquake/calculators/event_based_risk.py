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

import os.path
import logging
import operator
from functools import partial
import numpy
import pandas
from scipy import sparse

from openquake.baselib import hdf5, performance, general, python3compat, config
from openquake.hazardlib import stats, InvalidFile
from openquake.commonlib.calc import starmap_from_gmfs
from openquake.risklib.scientific import (
    total_losses, insurance_losses, MultiEventRNG, LOSSID)
from openquake.calculators import base, event_based
from openquake.calculators.post_risk import (
    PostRiskCalculator, post_aggregate, fix_dtypes, fix_investigation_time)

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
TWO24 = 2 ** 24
TWO32 = U64(2 ** 32)
get_n_occ = operator.itemgetter(1)


def fast_agg(keys, values, correl, li, acc):
    """
    :param keys: an array of N uint64 numbers encoding (event_id, agg_id)
    :param values: an array of (N, D) floats
    :param correl: True if there is asset correlation
    :param li: loss type index
    :param acc: dictionary unique key -> array(L, D)
    """
    ukeys, avalues = general.fast_agg2(keys, values)
    if correl:  # restore the variances
        avalues[:, 0] = avalues[:, 0] ** 2
    for ukey, avalue in zip(ukeys, avalues):
        acc[ukey][li] += avalue


def update(loss_by_AR, ln, alt, rlz_id, collect_rlzs):
    """
    Populate loss_by_AR a dictionary ln -> {'aids': [], 'rlzs': [], 'loss': []}
    where `ln` is the loss name, i.e. "structural", "injured", etc

    :param alt: DataFrame agg_loss_table
    :param rlz_id: effective realization index (usually 0)
    :param collect_rlzs: usually True
    """
    if collect_rlzs or len(numpy.unique(rlz_id)) == 1:
        # fast lane
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy()))
        tot = ldf.groupby('aid').loss.sum()
        aids = tot.index.to_numpy()
        rlzs = numpy.zeros_like(tot)
    else:
        # rare case
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy(),
                 rlz=rlz_id[U32(alt.eid)]))  # NB: without the U32 here
        # the SURA calculation would fail with alt.eid being F64 (?)
        tot = ldf.groupby(['aid', 'rlz']).loss.sum()
        aids, rlzs = zip(*tot.index)
    loss_by_AR[ln]['aids'].append(aids)
    loss_by_AR[ln]['rlzs'].append(rlzs)
    loss_by_AR[ln]['loss'].append(tot.to_numpy())


def debugprint(ln, asset_loss_table, adf):
    """
    Print risk_by_event in a reasonable format. To be used with --nd
    """
    if '+' in ln or ln == 'claim':
        df = asset_loss_table.set_index('aid').rename(columns={'loss': ln})
        df['asset_id'] = python3compat.decode(adf.id[df.index].to_numpy())
        del df['variance']
        print(df)


def aggreg(outputs, crmodel, ARK, aggids, rlz_id, ideduc, monitor):
    """
    :returns: (avg_losses, agg_loss_table)
    """
    oq = crmodel.oqparam
    xtypes = oq.ext_loss_types
    if ideduc:
        xtypes.append('claim')
    loss_by_AR = {ln: {'aids': [], 'rlzs': [], 'loss': []} for ln in xtypes}
    correl = int(oq.asset_correlation)
    (A, R, K), L = ARK, len(xtypes)
    acc = general.AccumDict(accum=numpy.zeros((L, 2)))  # u8idx->array
    value_cols = ['variance', 'loss']
    for out in outputs:
        for li, ln in enumerate(xtypes):
            if ln not in out or len(out[ln]) == 0:
                continue
            alt = out[ln]
            if oq.avg_losses:  # fast
                update(loss_by_AR, ln, alt, rlz_id, oq.collect_rlzs)
            if correl:  # use sigma^2 = (sum sigma_i)^2
                alt['variance'] = numpy.sqrt(alt.variance)
            eids = alt.eid.to_numpy() * TWO32  # U64
            values = numpy.array([alt[col] for col in value_cols]).T
            # aggregate all assets
            fast_agg(eids + U64(K), values, correl, li, acc)
            if len(aggids):
                # aggregate assets for each tag combination
                aids = alt.aid.to_numpy()
                for kids in aggids[:, aids]:
                    fast_agg(eids + U64(kids), values, correl, li, acc)
    for ln in list(loss_by_AR):
        if loss_by_AR[ln]['aids']:
            aids = numpy.concatenate(loss_by_AR[ln]['aids'])
            rlzs = numpy.concatenate(loss_by_AR[ln]['rlzs'])
            loss = numpy.concatenate(loss_by_AR[ln]['loss'])
            loss_by_AR[ln] = sparse.coo_matrix((loss, (aids, rlzs)), (A, R))
        else:
            del loss_by_AR[ln]

    # building event loss table
    lis = range(len(xtypes))
    dic = general.AccumDict(accum=[])
    for ukey, arr in acc.items():
        eid, kid = divmod(ukey, TWO32)
        for li in lis:
            if arr[li].any():
                dic['event_id'].append(eid)
                dic['agg_id'].append(kid)
                dic['loss_id'].append(LOSSID[xtypes[li]])
                for c, col in enumerate(['variance', 'loss']):
                    dic[col].append(arr[li, c])
    fix_dtypes(dic)
    return loss_by_AR, pandas.DataFrame(dic)


def ebr_from_gmfs(sbe, oqparam, dstore, monitor):
    """
    :param sbe: composite array with fields 'start', 'stop'
    :param oqparam: OqParam instance
    :param dstore: DataStore instance from which to read the GMFs
    :param monitor: a Monitor instance
    :yields: dictionary of arrays, the outputs of event_based_risk
    """
    if dstore.parent:
        dstore.parent.open('r')
    s0, s1 = sbe[0]['start'], sbe[-1]['stop']
    with dstore, monitor('reading GMFs', measuremem=True):
        gmf_df = dstore.read_df('gmf_data', slc=slice(s0, s1))
        risk_sids = monitor.read('sids')
    slices = performance.split_slices(
        gmf_df.eid.to_numpy(), int(config.memory.max_gmvs_chunk))
    avg = {}
    with monitor('reading crmodel', measuremem=True):
        crmodel = monitor.read('crmodel')
    for s0, s1 in slices:
        df = gmf_df[s0:s1]
        df = df[numpy.isin(df.sid.to_numpy(), risk_sids)]
        if len(df) == 0:
            yield {}
            continue
        dic = event_based_risk(df, crmodel, monitor)
        avg_ = dic.pop('avg')
        if not avg:
            avg.update(avg_)
        else:
            for ln in avg_:
                avg[ln] += avg_[ln]
        yield dic
    yield dict(avg=avg)


def event_based_risk(df, crmodel, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_X, ...
    :param crmodel: CompositeRiskModel instance
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays
    """
    if os.environ.get('OQ_DEBUG_SITE'):
        print(df)

    oq = crmodel.oqparam
    aggids = monitor.read('aggids')
    rlz_id = monitor.read('rlz_id')
    weights = [1] if oq.collect_rlzs else monitor.read('weights')

    ARK = (oq.A, len(weights), oq.K)
    if oq.ignore_master_seed or oq.ignore_covs:
        rng = None
    else:
        rng = MultiEventRNG(oq.master_seed, df.eid.unique(),
                            int(oq.asset_correlation))

    outgen = output_gen(df, crmodel, rng, monitor)
    with monitor('aggregating losses', measuremem=True) as agg_mon:
        avg, alt = aggreg(outgen, crmodel, ARK, aggids, rlz_id, oq.ideduc,
                          monitor)
    # avg[ln] is a coo_matrix with data, row, col of 4 bytes per element
    out_bytes = (sum(avg[ln].data.nbytes * 3 for ln in avg) +
                 alt.memory_usage().sum())
    agg_mon.duration -= monitor.ctime  # subtract the computing time
    return dict(avg=avg, alt=alt, gmf_bytes=df.memory_usage().sum(),
                out_bytes=out_bytes)


def output_gen(df, crmodel, rng, monitor):
    """
    :param df: GMF dataframe (a slice of events)
    :param crmodel: CompositeRiskModel instance
    :param rng: random number generator
    :param monitor: Monitor instance
    :yields: one output per taxonomy and slice of events
    """
    risk_mon = monitor('computing risk', measuremem=True)
    fil_mon = monitor('filtering GMFs', measuremem=False)
    ass_mon = monitor('reading assets', measuremem=False)
    sids = df.sid.to_numpy()
    monitor.ctime = 0
    for id0taxo, s0, s1 in risk_mon.read('start-stop'):
        # the assets have all the same taxonomy and country
        with ass_mon:
            adf = risk_mon.read('assets', slice(s0, s1)).set_index('ordinal')
        # multiple countries are tested in test_impact_mode
        country = crmodel.countries[id0taxo // TWO24]
        with fil_mon:
            # *crucial* for the performance of the next step
            gmf_df = df[numpy.isin(sids, adf.site_id.unique())]
        if len(gmf_df) == 0:  # common enough
            continue
        with risk_mon:
            [out] = crmodel.get_outputs(
                adf, gmf_df, crmodel.oqparam._sec_losses, rng, country)
        monitor.ctime += ass_mon.dt + fil_mon.dt + risk_mon.dt
        yield out


def _tot_loss_unit_consistency(units, total_losses, loss_types):
    total_losses_units = set()
    for separate_lt in total_losses.split('+'):
        assert separate_lt in loss_types, (separate_lt, loss_types)
        for unit, lt in zip(units, loss_types):
            if separate_lt == lt:
                total_losses_units.add(unit)
    if len(total_losses_units) != 1:
        logging.warning(
            'The units of the single components of the total losses'
            ' are not homogeneous: %s" ' % total_losses_units)


def set_oqparam(oq, assetcol, dstore):
    """
    Set the attributes .M, .K, .A, .ideduc, ._sec_losses
    """
    try:
        K = len(dstore['agg_keys'])
    except KeyError:
        K = 0
    sec_losses = []  # one insured loss for each loss type with a policy
    try:
        policy_df = dstore.read_df('policy')
    except KeyError:
        pass
    else:
        if 'reinsurance' not in oq.inputs:
            sec_losses.append(
                partial(insurance_losses, policy_df=policy_df))

    ideduc = assetcol['ideductible'].any()
    cc = dstore['exposure'].cost_calculator
    if oq.total_losses and oq.total_loss_types and cc.cost_types:
        # cc.cost_types is empty in scenario_damage/case_21 (consequences)
        units = cc.get_units(oq.total_loss_types)
        _tot_loss_unit_consistency(
            units.split(), oq.total_losses, oq.total_loss_types)
        sec_losses.append(
            partial(total_losses, kind=oq.total_losses, ideduc=ideduc))
    elif ideduc:
        # subtract the insurance deductible for a single loss_type
        [lt] = oq.loss_types
        sec_losses.append(partial(total_losses, kind=lt, ideduc=ideduc))

    oq._sec_losses = sec_losses
    oq.ideduc = int(ideduc)
    oq.M = len(oq.all_imts())
    oq.K = K
    oq.A = assetcol['ordinal'].max() + 1


def _expand3(arrayN3, maxsize):
    # expand array with rows (id0taxo, start, stop) in chunks under
    # maxsize
    out = []
    for idx, start, stop in arrayN3:
        for slc in general.gen_slices(start, stop, maxsize):
            out.append((idx, slc.start, slc.stop))
    return U32(out)


def ebrisk(proxies, cmaker, sitecol, stations, dstore, monitor):
    """
    :param proxies: list of RuptureProxies with the same trt_smr
    :param cmaker: ContextMaker instance associated to the trt_smr
    :param stations: empty pair or (station_data, station_sitecol)
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays
    """
    cmaker.oq.ground_motion_fields = True
    with monitor('reading crmodel', measuremem=True):
        crmodel = monitor.read('crmodel')
    for block in general.block_splitter(
            proxies, 20_000, event_based.rup_weight):
        for dic in event_based.event_based(
                block, cmaker, sitecol, stations, dstore, monitor):
            if len(dic['gmfdata']):
                gmf_df = pandas.DataFrame(dic['gmfdata'])
                yield event_based_risk(gmf_df, crmodel, monitor)


@base.calculators.add('ebrisk', 'scenario_risk', 'event_based_risk')
class EventBasedRiskCalculator(event_based.EventBasedCalculator):
    """
    Event based risk calculator generating event loss tables
    """
    core_task = ebrisk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based', 'event_based_risk', 'ebrisk']

    def save_tmp(self, monitor):
        """
        Save some useful data in the file calc_XXX_tmp.hdf5
        """
        oq = self.oqparam
        monitor.save('sids', self.sitecol.sids)
        adf = self.assetcol.to_dframe()
        del adf['id']
        if 'ID_0' not in adf.columns:
            adf['ID_0'] = 0
        adf = adf.sort_values(['ID_0', 'taxonomy', 'ordinal'])
        # NB: this is subtle! without the ordering by 'ordinal'
        # the asset dataframe will be ordered differently on AMD machines
        # with respect to Intel machines, depending on the machine, thus
        # causing different losses
        monitor.save('assets', adf)

        if 'ID_0' in self.assetcol.tagnames:
            self.crmodel.countries = self.assetcol.tagcol.ID_0
        else:
            self.crmodel.countries = ['?']

        # storing start-stop indices in a smart way, so that the assets are
        # read from the workers by taxonomy
        id0taxo = TWO24 * adf.ID_0.to_numpy() + adf.taxonomy.to_numpy()
        max_assets = int(config.memory.max_assets_chunk)
        tss = _expand3(performance.idx_start_stop(id0taxo), max_assets)
        monitor.save('start-stop', tss)
        monitor.save('crmodel', self.crmodel)
        monitor.save('rlz_id', self.rlzs)
        monitor.save('weights', self.datastore['weights'][:])
        if oq.K:
            aggids, _ = self.assetcol.build_aggids(oq.aggregate_by)
        else:
            aggids = ()
        monitor.save('aggids', aggids)

    def pre_execute(self):
        oq = self.oqparam
        if oq.calculation_mode == 'ebrisk':
            oq.ground_motion_fields = False
        parent = self.datastore.parent
        if parent:
            self.datastore['full_lt'] = parent['full_lt']
            self.parent_events = ne = len(parent['events'])
            logging.info('There are %d ruptures and %d events',
                         len(parent['ruptures']), ne)
        else:
            self.parent_events = None
        super().pre_execute()
        parentdir = (os.path.dirname(self.datastore.ppath)
                     if self.datastore.ppath else None)
        oq.hdf5path = self.datastore.filename
        oq.parentdir = parentdir
        logging.info(
            'There are {:_d} ruptures and {:_d} events'.format(
                len(self.datastore['ruptures']),
                len(self.datastore['events'])))
        self.events_per_sid = numpy.zeros(self.N, U32)
        self.datastore.swmr_on()
        set_oqparam(oq, self.assetcol, self.datastore)
        self.A = A = len(self.assetcol)
        self.L = L = len(oq.loss_types)
        ELT = len(oq.ext_loss_types)
        if oq.calculation_mode == 'event_based_risk' and oq.avg_losses:
            R = 1 if oq.collect_rlzs else self.R
            logging.info('Transfering %s * %d per task in avg_losses',
                         general.humansize(A * 8 * R), ELT)
            if A * ELT * 8 > int(config.memory.avg_losses_max):
                raise ValueError('For large exposures you must set '
                                 'avg_losses=false')
            elif A * ELT * self.R * 8 > int(config.memory.avg_losses_max):
                raise ValueError('For large exposures you must set '
                                 'collect_rlzs = true')
        if (oq.aggregate_by and self.E * A > oq.max_potential_gmfs and
                all(val == 0 for val in oq.minimum_asset_loss.values())):
            logging.warning('The calculation is really big; consider setting '
                            'minimum_asset_loss')
        base.create_risk_by_event(self)
        self.rlzs = self.datastore['events']['rlz_id']
        self.num_events = numpy.bincount(self.rlzs, minlength=self.R)
        self.xtypes = oq.ext_loss_types
        if self.assetcol['ideductible'].any():
            self.xtypes.append('claim')

        if oq.avg_losses:
            self.create_avg_losses()
        alt_nbytes = 4 * self.E * L
        if alt_nbytes / (oq.concurrent_tasks or 1) > TWO32:
            raise RuntimeError('The risk_by_event is too big to be transfer'
                               'ed with %d tasks' % oq.concurrent_tasks)

    def create_avg_losses(self):
        oq = self.oqparam
        ws = self.datastore['weights']
        R = 1 if oq.collect_rlzs else len(ws)
        S = len(oq.hazard_stats())
        fix_investigation_time(oq, self.datastore)
        if oq.collect_rlzs:
            if oq.investigation_time:  # event_based
                self.avg_ratio = numpy.array([oq.time_ratio / len(ws)])
            else:  # scenario
                self.avg_ratio = numpy.array([1. / self.num_events.sum()])
        else:
            if oq.investigation_time:  # event_based
                self.avg_ratio = numpy.array([oq.time_ratio] * len(ws))
            else:  # scenario
                self.avg_ratio = 1. / self.num_events
        self.avg_losses = {}
        for lt in self.xtypes:
            self.avg_losses[lt] = numpy.zeros((self.A, R), F32)
            self.datastore.create_dset(
                'avg_losses-rlzs/' + lt, F32, (self.A, R))
            if S and R > 1:
                self.datastore.create_dset(
                    'avg_losses-stats/' + lt, F32, (self.A, S))

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        oq = self.oqparam
        self.gmf_bytes = 0
        self.out_bytes = 0
        if oq.calculation_mode == 'ebrisk' or 'gmf_data' not in self.datastore:
            # start from ruptures
            if (oq.ground_motion_fields and
                    'gsim_logic_tree' not in oq.inputs and
                    oq.gsim == '[FromFile]'):
                raise InvalidFile('%s: missing gsim or gsim_logic_tree_file'
                                  % oq.inputs['job_ini'])
            elif not hasattr(oq, 'maximum_distance'):
                raise InvalidFile('Missing maximum_distance in %s'
                                  % oq.inputs['job_ini'])
            full_lt = self.datastore['full_lt']
            smap = event_based.starmap_from_rups(
                ebrisk, oq, full_lt, self.sitecol, self.datastore,
                self.save_tmp)
            smap.reduce(self.agg_dicts)
            if self.gmf_bytes == 0:
                raise RuntimeError(
                    'No GMFs were generated, perhaps they were '
                    'all below the minimum_intensity threshold')
            logging.info(
                'Produced %s of GMFs', general.humansize(self.gmf_bytes))
        else:  # start from GMFs
            smap = starmap_from_gmfs(ebr_from_gmfs, oq, self.datastore,
                                     self._monitor)
            self.save_tmp(smap.monitor)
            smap.reduce(self.agg_dicts)

        if self.parent_events:
            assert self.parent_events == len(self.datastore['events'])
        return 1

    def log_info(self, eids):
        """
        Printing some information about the risk calculation
        """
        logging.info('Processing {:_d} rows of gmf_data'.format(len(eids)))
        E = len(numpy.unique(eids))
        K = self.oqparam.K
        logging.info('Risk parameters (rel_E={:_d}, K={:_d}, L={})'.
                     format(E, K, self.L))

    def agg_dicts(self, dummy, dic):
        """
        :param dummy: unused parameter
        :param dic: dictionary with keys "avg", "alt"
        """
        if not dic:
            return
        self.gmf_bytes += dic.pop('gmf_bytes', 0)
        self.out_bytes = max(self.out_bytes, dic.pop('out_bytes', 0))
        self.oqparam.ground_motion_fields = False  # hack
        if 'alt' in dic:
            with self.monitor('saving risk_by_event'):
                alt = dic.pop('alt')
                for name in alt.columns:
                    dset = self.datastore['risk_by_event/' + name]
                    hdf5.extend(dset, alt[name].to_numpy())
        if 'avg' in dic:
            # avg_losses are stored as coo matrices or csr matrices
            # for each loss name (ln)
            with self.monitor('saving avg_losses'):
                for ln, coo in dic.pop('avg').items():
                    if not hasattr(coo, 'row'):  # csr_matrix
                        coo = coo.tocoo()
                    self.avg_losses[ln][coo.row, coo.col] += coo.data

    def post_execute(self, dummy):
        """
        Compute and store average losses from the risk_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        logging.info('max output size = %s', general.humansize(self.out_bytes))
        K = self.datastore['risk_by_event'].attrs.get('K', 0)
        upper_limit = self.E * (K + 1) * len(self.xtypes)
        if upper_limit < 1E7:
            # sanity check on risk_by_event if not too large
            alt = self.datastore.read_df('risk_by_event')
            size = len(alt)
            assert size <= upper_limit, (size, upper_limit)
            # sanity check on uniqueness by (agg_id, loss_id, event_id)
            arr = alt[['agg_id', 'loss_id', 'event_id']].to_numpy()
            uni, cnt = numpy.unique(arr, axis=0, return_counts=True)
            if len(uni) < len(arr):
                dupl = uni[cnt > 1]  # (agg_id, loss_id, event_id)
                raise RuntimeError(
                    'risk_by_event contains %d duplicates for event %s' %
                    (len(arr) - len(uni), dupl[0, 2]))

        s = oq.hazard_stats()
        if s:
            _statnames, statfuncs = zip(*s.items())
            weights = self.datastore['weights'][:]
        if oq.avg_losses:
            for lt in self.xtypes:
                al = self.avg_losses[lt]  # shape (A, R)
                for r in range(self.R):
                    al[:, r] *= self.avg_ratio[r]
                name = 'avg_losses-rlzs/' + lt
                logging.info(f'Storing {name}')
                self.datastore[name][:] = al
                if s and self.R > 1:
                    self.datastore[name.replace('-rlzs', '-stats')][:] = \
                        stats.compute_stats2(al, statfuncs, weights)

        self.build_aggcurves()
        if oq.reaggregate_by:
            post_aggregate(self.datastore.calc_id,
                           ','.join(oq.reaggregate_by))

    def build_aggcurves(self):
        prc = PostRiskCalculator(self.oqparam, self.datastore.calc_id)
        prc.assetcol = self.assetcol
        if hasattr(self, 'exported'):
            prc.exported = self.exported
        prc.pre_execute()
        res = prc.execute()
        prc.post_execute(res)
