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
from datetime import datetime
import numpy
import pandas
from scipy import sparse

from openquake.baselib import hdf5, parallel, general
from openquake.hazardlib import stats
from openquake.risklib.scientific import InsuredLosses, MultiEventRNG
from openquake.commonlib import logs, datastore
from openquake.calculators import base, event_based, getters, views
from openquake.calculators.post_risk import PostRiskCalculator

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO16 = 2 ** 16
TWO32 = 2 ** 32
get_n_occ = operator.itemgetter(1)

gmf_info_dt = numpy.dtype([('rup_id', U32), ('task_no', U16),
                           ('nsites', U16), ('gmfbytes', F32), ('dt', F32)])


def aggregate_losses(alt, K, kids, correl):
    """
    Aggregate losses and variances for each event by using the formulae

    sigma^2 = sum(sigma_i)^2 for correl=1
    sigma^2 = sum(sigma_i^2) for correl=0
    """
    lbe = general.AccumDict(accum=numpy.zeros(2, F32))
    x = numpy.sqrt(alt.variance) if correl else alt.variance
    ldf = pandas.DataFrame(dict(eid=alt.eid, loss=alt.loss, x=x))
    if len(kids):
        ldf['kid'] = kids[alt.aid.to_numpy()]
        tot = ldf.groupby(['eid', 'kid']).sum()
        for (eid, kid), loss, x in zip(
                tot.index, tot.loss, tot.x):
            lbe[eid, kid] += F32([loss, x])
    tot = ldf.groupby('eid').sum()
    for eid, loss, x in zip(tot.index, tot.loss, tot.x):
        lbe[eid, K] += F32([loss, x])
    if correl:  # restore the variances
        for ek in lbe:
            lbe[ek][1] = lbe[ek][1] ** 2
    return lbe


def average_losses(ln, alt, rlz_id, AR, collect_rlzs):
    """
    :returns: a sparse coo matrix with the losses per asset and realization
    """
    if collect_rlzs:
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss))
        tot = ldf.groupby('aid').loss.sum()
        aids = tot.index.to_numpy()
        rlzs = numpy.zeros_like(tot)
        return sparse.coo_matrix((tot.to_numpy(), (aids, rlzs)), AR)
    else:
        ldf = pandas.DataFrame(
            dict(aid=alt.aid.to_numpy(), loss=alt.loss.to_numpy(),
                 rlz=rlz_id[U32(alt.eid)]))  # NB: with the U32 here
        # the SURA calculation would fail with alt.eid being F64 (?)
        tot = ldf.groupby(['aid', 'rlz']).loss.sum()
        aids, rlzs = zip(*tot.index)
        return sparse.coo_matrix((tot.to_numpy(), (aids, rlzs)), AR)


def aggreg(outputs, crmodel, AR, kids, rlz_id, param, monitor):
    """
    :returns: (avg_losses, agg_loss_table)
    """
    mon_agg = monitor('aggregating losses', measuremem=False)
    mon_avg = monitor('averaging losses', measuremem=False)
    loss_by_AR = {ln: [] for ln in crmodel.oqparam.loss_names}
    loss_by_EK1 = {ln: general.AccumDict(accum=numpy.zeros(2, F32))
                   for ln in crmodel.oqparam.loss_names}
    for out in outputs:
        for lni, ln in enumerate(crmodel.oqparam.loss_names):
            if ln not in out or len(out[ln]) == 0:
                continue
            alt = out[ln]
            with mon_agg:
                alt = alt.reset_index()
                loss_by_EK1[ln] += aggregate_losses(
                    alt, param['K'], kids, param['asset_correlation'])
            if param['avg_losses']:
                with mon_avg:
                    coo = average_losses(ln, alt, rlz_id, AR,
                                         param['collect_rlzs'])
                    loss_by_AR[ln].append(coo)
    return dict(avg=loss_by_AR, alt=_build_risk_by_event(loss_by_EK1))


def event_based_risk(df, param, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_X, ...
    :param param: a dictionary of parameters coming from the job.ini
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays
    """
    dstore = datastore.read(param['hdf5path'], parentdir=param['parentdir'])
    with dstore, monitor('reading data'):
        if hasattr(df, 'start'):  # it is actually a slice
            df = dstore.read_df('gmf_data', slc=df)
        assets_df = dstore.read_df('assetcol/array', 'ordinal')
        kids = dstore['assetcol/kids'][:] if param['K'] else ()
        crmodel = monitor.read('crmodel')
        rlz_id = monitor.read('rlz_id')
        weights = [1] if param['collect_rlzs'] else dstore['weights'][()]
    AR = len(assets_df), len(weights)
    if crmodel.oqparam.ignore_master_seed or crmodel.oqparam.ignore_covs:
        rndgen = None
    else:
        rndgen = MultiEventRNG(
            param['master_seed'], df.eid.unique(), param['asset_correlation'])

    def outputs():
        for taxo, asset_df in assets_df.groupby('taxonomy'):
            gmf_df = df[numpy.isin(df.sid.to_numpy(),
                                   asset_df.site_id.to_numpy())]
            if len(gmf_df) == 0:
                continue
            if rndgen:
                yield crmodel.get_output(
                    taxo, asset_df, gmf_df, param['sec_losses'], rndgen)
            else:
                yield from crmodel.gen_outputs(taxo, asset_df, gmf_df, param)

    return aggreg(outputs(), crmodel, AR, kids, rlz_id, param, monitor)


def _build_risk_by_event(loss_by_EK1):
    alt = {}
    for lni, ln in enumerate(loss_by_EK1):
        nnz = len(loss_by_EK1[ln])
        if nnz:
            eid = numpy.zeros(nnz, U32)
            kid = numpy.zeros(nnz, U16)
            loss = numpy.zeros(nnz, F32)
            var = numpy.zeros(nnz, F32)
            lid = numpy.ones(nnz, U8) * lni
            for i, ((e, k), lv) in enumerate(loss_by_EK1[ln].items()):
                eid[i] = e
                kid[i] = k
                loss[i] = lv[0]
                var[i] = lv[1]
            alt[ln] = pandas.DataFrame(
                dict(event_id=eid, agg_id=kid, loss=loss, variance=var,
                     loss_id=lid))
    return alt


def start_ebrisk(rgetter, param, monitor):
    """
    Launcher for ebrisk tasks
    """
    srcfilter = monitor.read('srcfilter')
    rgetters = list(rgetter.split(srcfilter, param['maxweight']))
    for rg in rgetters[:-1]:
        msg = 'produced subtask'
        try:
            logs.dbcmd('log', monitor.calc_id, datetime.utcnow(), 'DEBUG',
                       'ebrisk#%d' % monitor.task_no, msg)
        except Exception:  # for `oq run`
            print(msg)
        yield ebrisk, rg, param
    if rgetters:
        yield from ebrisk(rgetters[-1], param, monitor)


def ebrisk(rupgetter, param, monitor):
    """
    :param rupgetter: RuptureGetter with multiple ruptures
    :param param: dictionary of parameters coming from oqparam
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays
    """
    mon_rup = monitor('getting ruptures', measuremem=False)
    mon_haz = monitor('getting hazard', measuremem=True)
    alldata = general.AccumDict(accum=[])
    gmf_info = []
    srcfilter = monitor.read('srcfilter')
    param['N'] = len(srcfilter.sitecol.complete)
    gg = getters.GmfGetter(rupgetter, srcfilter, param['oqparam'],
                           param['amplifier'])
    with mon_haz:
        for c in gg.gen_computers(mon_rup):
            data, time_by_rup = c.compute_all()
            if len(data):
                for key, val in data.items():
                    alldata[key].extend(data[key])
                nbytes = len(data['sid']) * len(data) * 4
                gmf_info.append((c.ebrupture.id, mon_haz.task_no, len(c.sids),
                                 nbytes, mon_haz.dt))
    if not alldata:
        return {}
    for key, val in sorted(alldata.items()):
        if key in 'eid sid rlz':
            alldata[key] = U32(alldata[key])
        else:
            alldata[key] = F32(alldata[key])
    yield event_based_risk(pandas.DataFrame(alldata), param, monitor)
    if gmf_info:
        yield {'gmf_info': numpy.array(gmf_info, gmf_info_dt)}


@base.calculators.add('ebrisk', 'scenario_risk', 'event_based_risk')
class EventBasedRiskCalculator(event_based.EventBasedCalculator):
    """
    Event based risk calculator generating event loss tables
    """
    core_task = start_ebrisk
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
            ne = len(parent['events'])
            logging.info('There are %d ruptures and %d events',
                         len(parent['ruptures']), ne)

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
        self.set_param(hdf5path=self.datastore.filename,
                       parentdir=parentdir,
                       ignore_covs=oq.ignore_covs,
                       master_seed=oq.master_seed,
                       asset_correlation=int(oq.asset_correlation))
        logging.info(
            'There are {:_d} ruptures'.format(len(self.datastore['ruptures'])))
        self.events_per_sid = numpy.zeros(self.N, U32)
        self.datastore.swmr_on()
        sec_losses = []
        if self.policy_dict:
            sec_losses.append(
                InsuredLosses(self.policy_name, self.policy_dict))
        if not hasattr(self, 'aggkey'):
            self.aggkey = self.assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.param['sec_losses'] = sec_losses
        self.param['aggregate_by'] = oq.aggregate_by
        self.param['M'] = len(oq.all_imts())
        self.param['N'] = self.N
        self.param['K'] = len(self.aggkey)
        ct = oq.concurrent_tasks or 1
        self.param['maxweight'] = int(oq.ebrisk_maxsize / ct)
        self.param['collect_rlzs'] = oq.collect_rlzs
        self.A = A = len(self.assetcol)
        self.L = L = len(oq.loss_names)
        if (oq.aggregate_by and self.E * A > oq.max_potential_gmfs and
                all(val == 0 for val in oq.minimum_asset_loss.values())):
            logging.warning('The calculation is really big; consider setting '
                            'minimum_asset_loss')
        base.create_risk_by_event(self)
        self.rlzs = self.datastore['events']['rlz_id']
        self.num_events = numpy.bincount(self.rlzs)  # events by rlz
        if oq.avg_losses:
            self.save_avg_losses()
        alt_nbytes = 4 * self.E * L
        if alt_nbytes / (oq.concurrent_tasks or 1) > TWO32:
            raise RuntimeError('The risk_by_event is too big to be transfer'
                               'ed with %d tasks' % oq.concurrent_tasks)
        self.datastore.create_dset('gmf_info', gmf_info_dt)

    def save_avg_losses(self):
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
            loss_type=oq.loss_names)

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        if 'gmf_data' not in self.datastore:  # start from ruptures
            srcfilter = self.src_filter()
            smap = parallel.Starmap(start_ebrisk, h5=self.datastore.hdf5)
            smap.monitor.save('srcfilter', srcfilter)
            smap.monitor.save('crmodel', self.crmodel)
            smap.monitor.save('rlz_id', self.rlzs)
            for rg in getters.get_rupture_getters(
                    self.datastore, self.oqparam.concurrent_tasks,
                    srcfilter=srcfilter):
                smap.submit((rg, self.param))
            smap.reduce(self.agg_dicts)
            gmf_bytes = self.datastore['gmf_info']['gmfbytes']
            if len(gmf_bytes) == 0:
                raise RuntimeError(
                    'No GMFs were generated, perhaps they were '
                    'all below the minimum_intensity threshold')
            logging.info(
                'Produced %s of GMFs', general.humansize(gmf_bytes.sum()))
        else:  # start from GMFs
            eids = self.datastore['gmf_data/eid'][:]
            logging.info('Processing {:_d} rows of gmf_data'.format(len(eids)))
            self.datastore.swmr_on()  # crucial!
            smap = parallel.Starmap(
                event_based_risk, self.gen_args(eids), h5=self.datastore.hdf5)
            smap.monitor.save('assets', self.assetcol.to_dframe())
            smap.monitor.save('crmodel', self.crmodel)
            smap.monitor.save('rlz_id', self.rlzs)
            smap.reduce(self.agg_dicts)
        return 1

    def agg_dicts(self, dummy, dic):
        """
        :param dummy: unused parameter
        :param dic: dictionary with keys "avg", "alt", "gmf_info"
        """
        if not dic:
            return
        if 'gmf_info' in dic:
            hdf5.extend(self.datastore['gmf_info'], dic.pop('gmf_info'))
            return
        lti = self.oqparam.lti
        self.oqparam.ground_motion_fields = False  # hack
        with self.monitor('saving risk_by_event'):
            for ln, ls in dic['alt'].items():
                for name in ls.columns:
                    dset = self.datastore['risk_by_event/' + name]
                    hdf5.extend(dset, ls[name].to_numpy())
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
                                 loss_type=oq.loss_names)

        # save agg_losses
        units = self.datastore['cost_calculator'].get_units(oq.loss_names)
        if oq.calculation_mode == 'scenario_risk':  # compute agg_losses
            alt = alt.set_index('event_id')
            alt['rlz_id'] = self.rlzs[alt.index.to_numpy()]
            agglosses = numpy.zeros((K + 1, self.R, self.L), F32)
            for (agg_id, rlz_id, loss_id), df in alt.groupby(
                    ['agg_id', 'rlz_id', 'loss_id']):
                agglosses[agg_id, rlz_id, loss_id] = (
                    df.loss.sum() * self.avg_ratio[rlz_id])
            self.datastore['agg_losses-rlzs'] = agglosses
            stats.set_rlzs_stats(self.datastore, 'agg_losses', agg_id=K,
                                 loss_types=oq.loss_names, units=units)
            logging.info('Total portfolio loss\n' +
                         views.view('portfolio_loss', self.datastore))
        else:  # event_based_risk, run post_risk
            prc = PostRiskCalculator(oq, self.datastore.calc_id)
            if hasattr(self, 'exported'):
                prc.exported = self.exported
            with prc.datastore:
                prc.run(exports='')

        if (oq.investigation_time or not oq.avg_losses or
                'agg_losses-rlzs' not in self.datastore):
            return

        # sanity check on the agg_losses and sum_losses
        sumlosses = self.avg_losses.sum(axis=0)
        if not numpy.allclose(agglosses[K], sumlosses, rtol=1E-6):
            url = ('https://docs.openquake.org/oq-engine/advanced/'
                   'addition-is-non-associative.html')
            logging.warning(
                'Due to rounding errors inherent in floating-point arithmetic,'
                ' agg_losses != sum(avg_losses): %s != %s\nsee %s',
                agglosses[K].mean(), sumlosses.mean(), url)

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
                yield slice(start, stop), self.param
                weight = 0
                start = stop
        if weight:
            yield slice(start, stop), self.param
