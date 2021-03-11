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

import copy
import logging
import operator
from datetime import datetime
import numpy
import pandas

from openquake.baselib import datastore, hdf5, parallel, general
from openquake.hazardlib import stats
from openquake.risklib.scientific import AggLossTable, InsuredLosses
from openquake.risklib.riskinput import MultiEventRNG
from openquake.commonlib import logs
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


def event_based_risk(df, param, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_...
    :param param: a dictionary of parameters coming from the job.ini
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays with keys alt, losses_by_A
    """
    mon_risk = monitor('computing risk', measuremem=False)
    mon_agg = monitor('aggregating losses', measuremem=False)
    mon_avg = monitor('averaging losses', measuremem=False)
    dstore = datastore.read(param['hdf5path'])
    with monitor('getting assets'):
        assets_df = dstore.read_df('assetcol/array', 'ordinal')
    with monitor('getting crmodel'):
        crmodel = monitor.read('crmodel')
        rlz_id = monitor.read('rlz_id')
        weights = dstore['weights'][()]
    acc = dict(events_per_sid=numpy.zeros(param['N'], U32))
    alt = copy.copy(param['alt'])  # avoid issues with OQ_DISTRIBUTE=no
    aggby = param['aggregate_by']
    haz_by_sid = {s: d for s, d in df.groupby('sid')}
    AE = len(assets_df), len(rlz_id)
    ARL = len(assets_df), len(weights), len(alt.loss_names)
    losses_by_A = numpy.zeros(ARL, F32)
    acc['momenta'] = numpy.zeros((2, param['N'], param['M']))
    cols = [col for col in df.columns if col not in {'sid', 'eid', 'rlz'}]
    for sid, haz in haz_by_sid.items():
        gmvs = haz[cols].to_numpy()
        ws = weights[rlz_id[haz.eid.to_numpy()]]
        acc['momenta'][:, sid] = stats.calc_momenta(
            numpy.log(numpy.maximum(gmvs, param['min_iml'])), ws)
        acc['events_per_sid'][sid] += len(haz)
    if param['ignore_covs']:
        rndgen = None
    else:
        rndgen = MultiEventRNG(
            param['master_seed'], param['asset_correlation'], df.eid)
    for taxo, asset_df in assets_df.groupby('taxonomy'):
        gmf_df = df[numpy.isin(df.sid.to_numpy(), asset_df.site_id.to_numpy())]
        with mon_risk:
            out = crmodel.get_output(
                taxo, asset_df, gmf_df, param['sec_losses'], rndgen, AE=AE)
        with mon_agg:
            alt.aggregate(out, aggby)
        if param['avg_losses']:
            with mon_avg:
                for lni, ln in enumerate(alt.loss_names):
                    for (aid, eid), loss in out[ln].items():
                        losses_by_A[aid, rlz_id[eid], lni] += loss

    acc['alt'] = alt.to_dframe()
    if param['avg_losses']:
        acc['losses_by_A'] = losses_by_A
    return acc


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
        yield ebrisk(rgetters[-1], param, monitor)


def ebrisk(rupgetter, param, monitor):
    """
    :param rupgetter: RuptureGetter with multiple ruptures
    :param param: dictionary of parameters coming from oqparam
    :param monitor: a Monitor instance
    :returns: a dictionary with keys alt, losses_by_A
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
            data, time_by_rup = c.compute_all(gg.min_iml, gg.rlzs_by_gsim)
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
    res = event_based_risk(pandas.DataFrame(alldata), param, monitor)
    if gmf_info:
        res['gmf_info'] = numpy.array(gmf_info, gmf_info_dt)
    return res


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
        self.set_param(hdf5path=self.datastore.filename,
                       ignore_covs=oq.ignore_covs,
                       master_seed=oq.master_seed,
                       asset_correlation=int(oq.asset_correlation))
        logging.info(
            'There are {:_d} ruptures'.format(len(self.datastore['ruptures'])))
        self.events_per_sid = numpy.zeros(self.N, U32)
        self.datastore.swmr_on()
        M = len(oq.all_imts())
        self.momenta = numpy.zeros((2, self.N, M))
        sec_losses = []
        if self.policy_dict:
            sec_losses.append(
                InsuredLosses(self.policy_name, self.policy_dict))
        if not hasattr(self, 'aggkey'):
            self.aggkey = self.assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.param['alt'] = alt = AggLossTable.new(self.aggkey, oq.loss_names)
        self.param['sec_losses'] = sec_losses
        self.param['aggregate_by'] = oq.aggregate_by
        self.param['min_iml'] = oq.min_iml
        self.param['M'] = len(oq.all_imts())
        self.param['N'] = self.N
        ct = oq.concurrent_tasks or 1
        self.param['maxweight'] = int(oq.ebrisk_maxsize / ct)
        self.A = A = len(self.assetcol)
        self.L = L = len(alt.loss_names)
        if (oq.aggregate_by and self.E * A > oq.max_potential_gmfs and
                any(val == 0 for val in oq.minimum_asset_loss.values())):
            logging.warning('The calculation is really big; consider setting '
                            'minimum_asset_loss')

        descr = [('event_id', U32), ('agg_id', U32), ('loss_id', U8),
                 ('loss', F64)]
        self.datastore.create_dframe(
            'agg_loss_table', descr, K=len(self.aggkey), L=len(oq.loss_names))
        R = len(self.datastore['weights'])
        self.rlzs = self.datastore['events']['rlz_id']
        self.num_events = numpy.bincount(self.rlzs)  # events by rlz
        if oq.avg_losses:
            if oq.investigation_time:  # event_based
                self.avg_ratio = numpy.array([oq.ses_ratio] * R)
            else:  # scenario
                self.avg_ratio = 1. / self.num_events
            self.avg_losses = numpy.zeros((A, R, L), F32)
            self.datastore.create_dset('avg_losses-rlzs', F32, (A, R, L))
            self.datastore.set_shape_descr(
                'avg_losses-rlzs', asset_id=self.assetcol['id'], rlz=R,
                loss_type=oq.loss_names)
        alt_nbytes = 4 * self.E * L
        if alt_nbytes / (oq.concurrent_tasks or 1) > TWO32:
            raise RuntimeError('The event loss table is too big to be transfer'
                               'red with %d tasks' % oq.concurrent_tasks)
        self.datastore.create_dset('gmf_info', gmf_info_dt)

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        if 'gmf_data' not in self.datastore:  # start from ruptures
            smap = parallel.Starmap(start_ebrisk, h5=self.datastore.hdf5)
            smap.monitor.save('srcfilter', self.src_filter())
            smap.monitor.save('crmodel', self.crmodel)
            smap.monitor.save('rlz_id', self.rlzs)
            for rg in getters.gen_rupture_getters(
                    self.datastore, self.oqparam.concurrent_tasks):
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
            smap = parallel.Starmap(
                event_based_risk, self.gen_args(), h5=self.datastore.hdf5)
            smap.monitor.save('assets', self.assetcol.to_dframe())
            smap.monitor.save('crmodel', self.crmodel)
            smap.monitor.save('rlz_id', self.rlzs)
            smap.reduce(self.agg_dicts)
        return 1

    def agg_dicts(self, dummy, dic):
        """
        :param dummy: unused parameter
        :param dic: dictionary with keys alt, losses_by_A
        """
        if 'gmf_info' in dic:
            hdf5.extend(self.datastore['gmf_info'], dic.pop('gmf_info'))
        if not dic:
            return
        self.oqparam.ground_motion_fields = False  # hack
        with self.monitor('saving agg_loss_table'):
            df = dic['alt']
            for name in df.columns:
                dset = self.datastore['agg_loss_table/' + name]
                hdf5.extend(dset, df[name].to_numpy())
        if self.oqparam.avg_losses:
            self.avg_losses += dic['losses_by_A']
        self.events_per_sid += dic['events_per_sid']
        self.momenta += dic['momenta']

    def post_execute(self, dummy):
        """
        Compute and store average losses from the agg_loss_table dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        if oq.avg_losses:
            for r in range(self.R):
                self.avg_losses[:, r] *= self.avg_ratio[r]
            self.datastore['avg_losses-rlzs'] = self.avg_losses
            stats.set_rlzs_stats(self.datastore, 'avg_losses',
                                 asset_id=self.assetcol['id'],
                                 loss_type=oq.loss_names)
        logging.info('Events per site: ~%d', self.events_per_sid.mean())
        totw = self.datastore['weights'][:][self.rlzs].sum()
        self.datastore['avg_gmf'] = numpy.exp(
            stats.calc_avg_std(self.momenta, totw))

        # save agg_losses
        alt = self.datastore.read_df('agg_loss_table', 'event_id')
        K = self.datastore['agg_loss_table'].attrs.get('K', 0)
        units = self.datastore['cost_calculator'].get_units(oq.loss_names)
        if oq.investigation_time is None:  # scenario, compute agg_losses
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
            prc.run(exports='')

        if (oq.investigation_time or not oq.avg_losses or
                'agg_losses-rlzs' not in self.datastore):
            return

        # sanity check on the agg_losses and sum_losses
        sumlosses = self.avg_losses.sum(axis=0)
        if not numpy.allclose(agglosses, sumlosses, rtol=1E-6):
            url = ('https://docs.openquake.org/oq-engine/advanced/'
                   'addition-is-non-associative.html')
            logging.warning(
                'Due to rounding errors inherent in floating-point arithmetic,'
                ' agg_losses != sum(avg_losses): %s != %s\nsee %s',
                agglosses.mean(), sumlosses.mean(), url)

    def gen_args(self):
        """
        :yields: pairs (gmf_df, param)
        """
        recs = self.datastore['gmf_data/by_task'][:]
        recs.sort(order='task_no')
        for task_no, start, stop in recs:
            df = self.datastore.read_df('gmf_data', slc=slice(start, stop))
            yield df, self.param
