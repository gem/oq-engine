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
import operator
import itertools
import numpy
import pandas
from scipy import sparse

from openquake.baselib import hdf5, parallel, general
from openquake.hazardlib import stats, InvalidFile
from openquake.hazardlib.source.rupture import RuptureProxy
from openquake.risklib.scientific import InsuredLosses, MultiEventRNG
from openquake.commonlib import datastore
from openquake.calculators import base, event_based
from openquake.calculators.post_risk import (
    PostRiskCalculator, post_aggregate, fix_dtypes)

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
TWO32 = U64(2 ** 32)
get_n_occ = operator.itemgetter(1)


def save_curve_stats(dstore):
    """
    Save agg_curves-stats
    """
    oq = dstore['oqparam']
    units = dstore['cost_calculator'].get_units(oq.loss_types)
    try:
        K1 = len(dstore['agg_keys']) + 1
    except KeyError:
        K1 = 1
    stats = oq.hazard_stats()
    S = len(stats)
    L = len(oq.lti)
    weights = dstore['weights'][:]
    aggcurves_df = dstore.read_df('aggcurves')
    periods = aggcurves_df.return_period.unique()
    P = len(periods)
    out = numpy.zeros((K1, S, L, P))
    for (agg_id, loss_id), df in aggcurves_df.groupby(["agg_id", "loss_id"]):
        for s, stat in enumerate(stats.values()):
            for p in range(P):
                dfp = df[df.return_period == periods[p]]
                ws = weights[dfp.rlz_id.to_numpy()]
                ws /= ws.sum()
                out[agg_id, s, loss_id, p] = stat(dfp.loss.to_numpy(), ws)
    dstore['agg_curves-stats'] = out
    dstore.set_shape_descr('agg_curves-stats', agg_id=K1, stat=list(stats),
                           lti=L, return_period=periods)
    dstore.set_attrs('agg_curves-stats', units=units)


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


def average_losses(ln, alt, rlz_id, AR, collect_rlzs):
    """
    :returns: a sparse coo matrix with the losses per asset and realization
    """
    if collect_rlzs or len(numpy.unique(rlz_id)) == 1:
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy()))
        tot = ldf.groupby('aid').loss.sum()
        aids = tot.index.to_numpy()
        rlzs = numpy.zeros_like(tot)
        return sparse.coo_matrix((tot.to_numpy(), (aids, rlzs)), AR)
    else:
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy(),
                 rlz=rlz_id[U32(alt.eid)]))  # NB: without the U32 here
        # the SURA calculation would fail with alt.eid being F64 (?)
        tot = ldf.groupby(['aid', 'rlz']).loss.sum()
        aids, rlzs = zip(*tot.index)
        return sparse.coo_matrix((tot.to_numpy(), (aids, rlzs)), AR)


def aggreg(outputs, crmodel, ARKD, kids, rlz_id, monitor):
    """
    :returns: (avg_losses, agg_loss_table)
    """
    mon_agg = monitor('aggregating losses', measuremem=False)
    mon_avg = monitor('averaging losses', measuremem=False)
    mon_df = monitor('building dataframe', measuremem=True)
    oq = crmodel.oqparam
    loss_by_AR = {ln: [] for ln in oq.loss_types}
    correl = int(oq.asset_correlation)
    (A, R, K, D), L = ARKD, len(oq.loss_types)
    acc = general.AccumDict(accum=numpy.zeros((L, D)))  # u8idx->array
    for out in outputs:
        for li, ln in enumerate(oq.loss_types):
            if ln not in out or len(out[ln]) == 0:
                continue
            alt = out[ln].reset_index()
            value_cols = alt.columns[2:]  # strip eid, aid
            if oq.avg_losses:
                with mon_avg:
                    coo = average_losses(
                        ln, alt, rlz_id, (A, R), oq.collect_rlzs)
                    loss_by_AR[ln].append(coo)
            with mon_agg:
                if correl:  # use sigma^2 = (sum sigma_i)^2
                    alt['variance'] = numpy.sqrt(alt.variance)
                eids = alt.eid.to_numpy() * TWO32  # U64
                values = numpy.array([alt[col] for col in value_cols]).T
                fast_agg(eids + U64(K), values, correl, li, acc)
                if len(kids):
                    aids = alt.aid.to_numpy()
                    fast_agg(eids + U64(kids[aids]), values, correl, li, acc)
    with mon_df:
        dic = general.AccumDict(accum=[])
        for ukey, arr in acc.items():
            eid, kid = divmod(ukey, TWO32)
            for li in range(L):
                if arr[li].any():
                    dic['event_id'].append(eid)
                    dic['agg_id'].append(kid)
                    dic['loss_id'].append(li)
                    for c, col in enumerate(value_cols):
                        dic[col].append(arr[li, c])
        fix_dtypes(dic)
        df = pandas.DataFrame(dic)
    return dict(avg=loss_by_AR, alt=df)


def event_based_risk(df, oqparam, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_X, ...
    :param oqparam: parameters coming from the job.ini
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays
    """
    dstore = datastore.read(oqparam.hdf5path, parentdir=oqparam.parentdir)
    with dstore, monitor('reading data'):
        if hasattr(df, 'start'):  # it is actually a slice
            df = dstore.read_df('gmf_data', slc=df)
        assets_df = dstore.read_df('assetcol/array', 'ordinal')
        kids = dstore['assetcol/kids'][:] if oqparam.K else ()
        crmodel = monitor.read('crmodel')
        rlz_id = monitor.read('rlz_id')
        weights = [1] if oqparam.collect_rlzs else dstore['weights'][()]
    ARKD = len(assets_df), len(weights), oqparam.K, oqparam.D
    if oqparam.ignore_master_seed or oqparam.ignore_covs:
        rng = None
    else:
        rng = MultiEventRNG(oqparam.master_seed, df.eid.unique(),
                            int(oqparam.asset_correlation))

    def outputs():
        mon_risk = monitor('computing risk', measuremem=False)
        for taxo, asset_df in assets_df.groupby('taxonomy'):
            gmf_df = df[numpy.isin(df.sid.to_numpy(),
                                   asset_df.site_id.to_numpy())]
            if len(gmf_df) == 0:
                continue
            with mon_risk:
                out = crmodel.get_output(
                    taxo, asset_df, gmf_df, oqparam._sec_losses, rng)
            yield out

    return aggreg(outputs(), crmodel, ARKD, kids, rlz_id, monitor)


def ebrisk(proxies, full_lt, oqparam, dstore, monitor):
    """
    :param proxies: list of RuptureProxies with the same trt_smr
    :param full_lt: a FullLogicTree instance
    :param oqparam: input parameters
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays
    """
    oqparam.ground_motion_fields = True
    dic = event_based.event_based(proxies, full_lt, oqparam, dstore, monitor)
    if len(dic['gmfdata']) == 0:  # no GMFs
        return {}
    return event_based_risk(dic['gmfdata'], oqparam, monitor)


@base.calculators.add('ebrisk', 'scenario_risk', 'event_based_risk')
class EventBasedRiskCalculator(event_based.EventBasedCalculator):
    """
    Event based risk calculator generating event loss tables
    """
    core_task = ebrisk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based', 'event_based_risk', 'ebrisk']

    def pre_execute(self):
        oq = self.oqparam
        if oq.calculation_mode == 'ebrisk':
            oq.ground_motion_fields = False
            logging.warning('You should be using the event_based_risk '
                            'calculator, not ebrisk!')
        parent = self.datastore.parent
        if parent:
            self.datastore['full_lt'] = parent['full_lt']
            self.parent_events = ne = len(parent['events'])
            logging.info('There are %d ruptures and %d events',
                         len(parent['ruptures']), ne)
        else:
            self.parent_events = None

        if oq.investigation_time and oq.return_periods != [0]:
            # setting return_periods = 0 disable loss curves
            eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
            if eff_time < 2:
                logging.warning(
                    'eff_time=%s is too small to compute loss curves',
                    eff_time)
        super().pre_execute()
        parentdir = (os.path.dirname(self.datastore.ppath)
                     if self.datastore.ppath else None)
        oq.hdf5path = self.datastore.filename
        oq.parentdir = parentdir
        logging.info(
            'There are {:_d} ruptures'.format(len(self.datastore['ruptures'])))
        self.events_per_sid = numpy.zeros(self.N, U32)
        self.datastore.swmr_on()
        sec_losses = []  # one insured loss for each loss type with a policy
        oq.D = 2
        if self.policy_dict:
            sec_losses.append(
                InsuredLosses(self.policy_name, self.policy_dict))
            self.oqparam.D = 3
        if not hasattr(self, 'aggkey'):
            self.aggkey = self.assetcol.tagcol.get_aggkey(oq.aggregate_by)
        oq._sec_losses = sec_losses
        oq.M = len(oq.all_imts())
        oq.N = self.N
        oq.K = len(self.aggkey)
        ct = oq.concurrent_tasks or 1
        oq.maxweight = int(oq.ebrisk_maxsize / ct)
        self.A = A = len(self.assetcol)
        self.L = L = len(oq.loss_types)
        if (oq.aggregate_by and self.E * A > oq.max_potential_gmfs and
                all(val == 0 for val in oq.minimum_asset_loss.values())):
            logging.warning('The calculation is really big; consider setting '
                            'minimum_asset_loss')
        base.create_risk_by_event(self)
        self.rlzs = self.datastore['events']['rlz_id']
        self.num_events = numpy.bincount(self.rlzs)  # events by rlz
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
        self.avg_losses = numpy.zeros((self.A, R, self.L), F32)
        self.datastore.create_dset('avg_losses-rlzs', F32, (self.A, R, self.L))
        self.datastore.set_shape_descr(
            'avg_losses-rlzs', asset_id=self.assetcol['id'], rlz=R,
            loss_type=oq.loss_types)

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        oq = self.oqparam
        self.gmf_bytes = 0
        if 'gmf_data' not in self.datastore:  # start from ruptures
            if (oq.ground_motion_fields and
                    'gsim_logic_tree' not in oq.inputs and
                    oq.gsim == '[FromFile]'):
                raise InvalidFile('Missing gsim or gsim_logic_tree_file in %s'
                                  % oq.inputs['job_ini'])
            elif not hasattr(oq, 'maximum_distance'):
                raise InvalidFile('Missing maximum_distance in %s'
                                  % oq.inputs['job_ini'])
            srcfilter = self.src_filter()
            scenario = 'scenario' in oq.calculation_mode
            proxies = [RuptureProxy(rec, scenario)
                       for rec in self.datastore['ruptures'][:]]
            full_lt = self.datastore['full_lt']
            self.datastore.swmr_on()  # must come before the Starmap
            smap = parallel.Starmap.apply_split(
                ebrisk, (proxies, full_lt, oq, self.datastore),
                key=operator.itemgetter('trt_smr'),
                weight=operator.itemgetter('n_occ'),
                h5=self.datastore.hdf5,
                duration=oq.time_per_task,
                outs_per_task=5)
            smap.monitor.save('srcfilter', srcfilter)
            smap.monitor.save('crmodel', self.crmodel)
            smap.monitor.save('rlz_id', self.rlzs)
            smap.reduce(self.agg_dicts)
            if self.gmf_bytes == 0:
                raise RuntimeError(
                    'No GMFs were generated, perhaps they were '
                    'all below the minimum_intensity threshold')
            logging.info(
                'Produced %s of GMFs', general.humansize(self.gmf_bytes))
        else:  # start from GMFs
            eids = self.datastore['gmf_data/eid'][:]
            self.log_info(eids)
            self.datastore.swmr_on()  # crucial!
            smap = parallel.Starmap(
                event_based_risk, self.gen_args(eids), h5=self.datastore.hdf5)
            smap.monitor.save('assets', self.assetcol.to_dframe())
            smap.monitor.save('crmodel', self.crmodel)
            smap.monitor.save('rlz_id', self.rlzs)
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
        names = {'loss', 'variance'}
        for sec_loss in self.oqparam._sec_losses:
            names.update(sec_loss.sec_names)
        D = len(names)
        logging.info('Risk parameters (rel_E={:_d}, K={:_d}, L={}, D={})'.
                     format(E, K, self.L, D))

    def agg_dicts(self, dummy, dic):
        """
        :param dummy: unused parameter
        :param dic: dictionary with keys "avg", "alt"
        """
        if not dic:
            return
        self.gmf_bytes += dic['alt'].memory_usage().sum()
        lti = self.oqparam.lti
        self.oqparam.ground_motion_fields = False  # hack
        with self.monitor('saving risk_by_event'):
            alt = dic['alt']
            if alt is not None:
                for name in alt.columns:
                    dset = self.datastore['risk_by_event/' + name]
                    hdf5.extend(dset, alt[name].to_numpy())
            for ln, ls in dic['avg'].items():
                for coo in ls:
                    self.avg_losses[coo.row, coo.col, lti[ln]] += coo.data

    def post_execute(self, dummy):
        """
        Compute and store average losses from the risk_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam

        # sanity check on the risk_by_event
        alt = self.datastore.read_df('risk_by_event')
        K = self.datastore['risk_by_event'].attrs.get('K', 0)
        upper_limit = self.E * self.L * (K + 1)
        size = len(alt)
        assert size <= upper_limit, (size, upper_limit)
        # sanity check on uniqueness by (agg_id, loss_id, event_id)
        arr = alt[['agg_id', 'loss_id', 'event_id']].to_numpy()
        uni = numpy.unique(arr, axis=0)
        if len(uni) < len(arr):
            raise RuntimeError('risk_by_event contains %d duplicates!' %
                               (len(arr) - len(uni)))
        if oq.avg_losses:
            for r in range(self.R):
                self.avg_losses[:, r] *= self.avg_ratio[r]
            self.datastore['avg_losses-rlzs'] = self.avg_losses
            stats.set_rlzs_stats(self.datastore, 'avg_losses',
                                 asset_id=self.assetcol['id'],
                                 loss_type=oq.loss_types)

        self.build_aggcurves()
        if oq.reaggregate_by:
            post_aggregate(self.datastore.calc_id,
                           ','.join(oq.reaggregate_by))

    def build_aggcurves(self):
        prc = PostRiskCalculator(self.oqparam, self.datastore.calc_id)
        prc.assetcol = self.assetcol
        if hasattr(self, 'exported'):
            prc.exported = self.exported
        with prc.datastore:
            prc.run(exports='')

        # save agg_curves-stats
        if self.R > 1 and 'aggcurves' in self.datastore:
            save_curve_stats(self.datastore)

    def gen_args(self, eids):
        """
        :yields: pairs (gmf_slice, param)
        """
        ct = self.oqparam.concurrent_tasks or 1
        maxweight = len(eids) / ct
        start = stop = weight = 0
        # IMPORTANT!! we rely on the fact that the hazard part
        # of the calculation stores the GMFs in chunks of constant eid
        for eid, group in itertools.groupby(eids):
            nsites = sum(1 for _ in group)
            stop += nsites
            weight += nsites
            if weight > maxweight:
                yield slice(start, stop), self.oqparam
                weight = 0
                start = stop
        if weight:
            yield slice(start, stop), self.oqparam
