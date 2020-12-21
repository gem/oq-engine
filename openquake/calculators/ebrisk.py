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

import copy
import logging
import operator
from datetime import datetime
import numpy

from openquake.baselib import datastore, hdf5, parallel, general
from openquake.risklib.scientific import AggLossTable, InsuredLosses
from openquake.risklib.riskinput import (
    cache_epsilons, get_assets_by_taxo, get_output)
from openquake.commonlib import logs
from openquake.calculators import base, event_based, getters
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


def calc_risk(gmfs, param, monitor):
    """
    :param gmfs: an array of GMFs with fields sid, eid, gmv
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
        weights = dstore['weights'][()]
    acc = dict(events_per_sid=0)
    alt = copy.copy(param['alt'])  # avoid issues with OQ_DISTRIBUTE=no
    alt_dt = param['oqparam'].alt_dt()
    tempname = param['tempname']
    aggby = param['aggregate_by']
    haz_by_sid = general.group_array(gmfs, 'sid')
    losses_by_A = numpy.zeros((len(assets_df), len(alt.loss_names)), F32)
    acc['avg_gmf'] = avg_gmf = {}
    for col in gmfs.dtype.names:
        if col not in 'sid eid rlz':
            avg_gmf[col] = numpy.zeros(param['N'], F32)

    for sid, asset_df in assets_df.groupby('site_id'):
        try:
            haz = haz_by_sid[sid]
        except KeyError:  # no hazard here
            continue
        with mon_risk:
            assets = asset_df.to_records()  # fast
            acc['events_per_sid'] += len(haz)
            assets_by_taxo = get_assets_by_taxo(assets, tempname)  # fast
            out = get_output(crmodel, assets_by_taxo, haz)  # slow
        with mon_agg:
            alt.aggregate(out, param['minimum_asset_loss'], aggby)
            # NB: after the aggregation out contains losses, not loss_ratios
        ws = weights[haz['rlz']]
        for col in gmfs.dtype.names:
            if col not in 'sid eid rlz':
                avg_gmf[col][sid] = haz[col] @ ws
        if param['avg_losses']:
            with mon_avg:
                for lni, ln in enumerate(alt.loss_names):
                    losses_by_A[assets['ordinal'], lni] += out[ln] @ ws
    if len(gmfs):
        acc['events_per_sid'] /= len(gmfs)
    out = []
    for eid, arr in alt.items():
        for k, vals in enumerate(arr):  # arr has shape K, L'
            if vals.sum() > 0:
                # in the demo there are 264/1694 nonzero events, i.e.
                # vals.sum() is zero most of the time
                out.append((eid, k) + tuple(vals))
    acc['alt'] = numpy.array(out, alt_dt)
    if param['avg_losses']:
        acc['losses_by_A'] = losses_by_A * param['ses_ratio']
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
    gmfs = []
    gmf_info = []
    srcfilter = monitor.read('srcfilter')
    param['N'] = len(srcfilter.sitecol.complete)
    gg = getters.GmfGetter(rupgetter, srcfilter, param['oqparam'],
                           param['amplifier'])
    nbytes = 0
    with mon_haz:
        for c in gg.gen_computers(mon_rup):
            data, time_by_rup = c.compute_all(gg.min_iml, gg.rlzs_by_gsim)
            if len(data):
                gmfs.append(data)
                nbytes += data.nbytes
                gmf_info.append((c.ebrupture.id, mon_haz.task_no, len(c.sids),
                                 data.nbytes, mon_haz.dt))
    if not gmfs:
        return {}
    conc = numpy.concatenate(gmfs)
    res = calc_risk(conc, param, monitor)
    if gmf_info:
        res['gmf_info'] = numpy.array(gmf_info, gmf_info_dt)
    return res


@base.calculators.add('ebrisk')
class EbriskCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating event loss tables
    """
    core_task = start_ebrisk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk']

    def pre_execute(self):
        oq = self.oqparam
        oq.ground_motion_fields = False
        super().pre_execute()
        sec_losses = []
        if self.policy_dict:
            sec_losses.append(
                InsuredLosses(self.policy_name, self.policy_dict))
        if not hasattr(self, 'aggkey'):
            self.aggkey = self.assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.param['alt'] = alt = AggLossTable(
            self.aggkey, oq.loss_dt().names, sec_losses)
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['aggregate_by'] = oq.aggregate_by
        ct = oq.concurrent_tasks or 1
        self.param['maxweight'] = int(oq.ebrisk_maxsize / ct)
        self.A = A = len(self.assetcol)
        self.L = L = len(alt.loss_names)
        self.check_number_loss_curves()
        mal = self.param['minimum_asset_loss']
        if (oq.aggregate_by and self.E * A > oq.max_potential_gmfs and
                any(val == 0 for val in mal.values())):
            logging.warning('The calculation is really big; consider setting '
                            'minimum_asset_loss')

        descr = [('event_id', U32), ('agg_id', U16)]
        for name in oq.loss_names:
            descr.append((name, F32))
        self.datastore.create_dframe(
            'agg_loss_table', descr, K=len(self.aggkey))
        self.param.pop('oqparam', None)  # unneeded
        self.datastore.create_dset('avg_losses-stats', F32, (A, 1, L),
                                   attrs=dict(stat=[b'mean']))  # mean
        alt_nbytes = 4 * self.E * L
        if alt_nbytes / (oq.concurrent_tasks or 1) > TWO32:
            raise RuntimeError('The event loss table is too big to be transfer'
                               'red with %d tasks' % oq.concurrent_tasks)
        self.datastore.create_dset('gmf_info', gmf_info_dt)

    def check_number_loss_curves(self):
        """
        Raise an error for too many loss curves (> max_num_loss_curves)
        """
        shp = self.assetcol.tagcol.agg_shape(self.oqparam.aggregate_by, self.L)
        if numpy.prod(shp) > self.oqparam.max_num_loss_curves:
            dic = dict(loss_types=self.L)
            for aggby in self.oqparam.aggregate_by:
                dic[aggby] = len(getattr(self.assetcol.tagcol, aggby)) - 1
            tot = numpy.prod(list(dic.values()))
            msg = ' * ' .join('(%s=%d)' % item for item in dic.items())
            raise ValueError('Producing too many aggregate loss curves, please'
                             ' reduce the aggregate_by\n%s = %d' % (msg, tot))

    def execute(self):
        self.datastore.flush()  # just to be sure
        oq = self.oqparam
        self.set_param(
            hdf5path=self.datastore.filename,
            tempname=cache_epsilons(
                self.datastore, oq, self.assetcol, self.crmodel, self.E))
        srcfilter = self.src_filter()
        logging.info(
            'Sending {:_d} ruptures'.format(len(self.datastore['ruptures'])))
        self.events_per_sid = []
        self.datastore.swmr_on()
        self.avg_gmf = general.AccumDict(
            accum=numpy.zeros(self.N, F32))  # imt -> gmvs
        smap = parallel.Starmap(start_ebrisk, h5=self.datastore.hdf5)
        smap.monitor.save('srcfilter', srcfilter)
        smap.monitor.save('crmodel', self.crmodel)
        for rg in getters.gen_rupture_getters(
                self.datastore, oq.concurrent_tasks):
            smap.submit((rg, self.param))
        smap.reduce(self.agg_dicts)
        gmf_bytes = self.datastore['gmf_info']['gmfbytes'].sum()
        logging.info(
            'Produced %s of GMFs', general.humansize(gmf_bytes))
        size = general.humansize(self.datastore.getsize('agg_loss_table'))
        logging.info('Stored %s in the agg_loss_table', size)
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
            arr = dic['alt']
            for name in arr.dtype.names:
                dset = self.datastore['agg_loss_table/' + name]
                hdf5.extend(dset, arr[name])
        if self.oqparam.avg_losses:
            with self.monitor('saving avg_losses'):
                self.datastore['avg_losses-stats'][:, 0] += dic['losses_by_A']
        self.events_per_sid.append(dic['events_per_sid'])
        self.avg_gmf += dic['avg_gmf']

    def post_execute(self, dummy):
        """
        Compute and store average losses from the losses_by_event dataset,
        and then loss curves and maps.
        """
        oq = self.oqparam
        self.datastore.create_dframe('avg_gmf', self.avg_gmf.items())
        prc = PostRiskCalculator(oq, self.datastore.calc_id)
        prc.datastore.parent = self.datastore.parent
        prc.run()
