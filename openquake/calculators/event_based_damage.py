# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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

import logging
import numpy
import pandas

from openquake.baselib import hdf5, general, parallel
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.commonlib import datastore
from openquake.calculators import base
from openquake.calculators.event_based_risk import EventBasedRiskCalculator
from openquake.calculators.post_risk import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


def fix_dtype(dic, dtype, names):
    for name in names:
        dic[name] = dtype(dic[name])


def fix_dic(dic, columns):
    fix_dtype(dic, U16, ['agg_id'])
    fix_dtype(dic, U8, ['loss_id'])
    if 'event_id' in dic:
        fix_dtype(dic, U32, ['event_id'])
    if 'return_period' in dic:
        fix_dtype(dic, U32, ['return_period'])
    fix_dtype(dic, F32, columns)


def agg_damages(dstore, slc, monitor):
    """
    :returns: dict (agg_id, loss_id) -> [dmg1, dmg2, ...]
    """
    with dstore:
        df = dstore.read_df('risk_by_event', ['agg_id', 'loss_id'], slc=slc)
        del df['event_id']
        agg = df.groupby(df.index).sum()
        dic = dict(zip(agg.index, agg.to_numpy()))
    return dic


def zero_dmgcsq(assetcol, crmodel):
    """
    :returns: an array of zeros of shape (A, L, Dc)
    """
    dmg_csq = crmodel.get_dmg_csq()
    A = len(assetcol)
    L = len(crmodel.loss_types)
    Dc = len(dmg_csq) + 1  # damages + consequences
    return numpy.zeros((A, L, Dc), F32)


def event_based_damage(df, param, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_...
    :param param: a dictionary of parameters coming from the job.ini
    :param monitor: a Monitor instance
    :returns: (damages (eid, kid) -> LDc plus damages (A, Dc))
    """
    mon_risk = monitor('computing risk', measuremem=False)
    dstore = datastore.read(param['hdf5path'])
    K = param['K']
    with monitor('reading data'):
        if hasattr(df, 'start'):  # it is actually a slice
            df = dstore.read_df('gmf_data', slc=df)
        assets_df = dstore.read_df('assetcol/array', 'ordinal')
        kids = (dstore['assetcol/kids'][:] if K
                else numpy.zeros(len(assets_df), U16))
        crmodel = monitor.read('crmodel')
    dmg_csq = crmodel.get_dmg_csq()
    ci = {dc: i + 1 for i, dc in enumerate(dmg_csq)}
    dmgcsq = zero_dmgcsq(assets_df, crmodel)  # shape (A, L, Dc)
    A, L, Dc = dmgcsq.shape
    D = len(crmodel.damage_states)
    loss_names = crmodel.oqparam.loss_names
    with mon_risk:
        dddict = general.AccumDict(accum=numpy.zeros((L, Dc), F32))  # eid, kid
        for sid, asset_df in assets_df.groupby('site_id'):
            # working one site at the time
            gmf_df = df[df.sid == sid]
            if len(gmf_df) == 0:
                continue
            eids = gmf_df.eid.to_numpy()
            for taxo, adf in asset_df.groupby('taxonomy'):
                out = crmodel.get_output(taxo, adf, gmf_df)
                aids = adf.index.to_numpy()
                for lti, lt in enumerate(loss_names):
                    fractions = out[lt]
                    Asid, E, D = fractions.shape
                    ddd = numpy.zeros((Asid, E, Dc), F32)
                    ddd[:, :, :D] = fractions
                    for a, asset in enumerate(adf.to_records()):
                        # NB: uncomment the lines below to see the performance
                        # disaster of scenario_damage.bin_ddd; for instance
                        # the Messina test in oq-risk-tests becomes 10x
                        # slower even if it has only 25_736 assets:
                        # scenario_damage.bin_ddd(
                        #     fractions[a], asset['number'],
                        #     param['master_seed'] + a)
                        ddd[a] *= asset['number']
                        csq = crmodel.compute_csq(asset, fractions[a], lt)
                        for name, values in csq.items():
                            ddd[a, :, ci[name]] = values
                    dmgcsq[aids, lti] += ddd.sum(axis=1)  # sum on the events
                    tot = ddd.sum(axis=0)  # sum on the assets
                    for e, eid in enumerate(eids):
                        dddict[eid, K][lti] += tot[e]
                        if K:
                            for a, aid in enumerate(aids):
                                dddict[eid, kids[aid]][lti] += ddd[a, e]
    return to_dframe(dddict, ci, L), dmgcsq


def to_dframe(adic, ci, L):
    dic = general.AccumDict(accum=[])
    for (eid, kid), dd in sorted(adic.items()):
        for lti in range(L):
            dic['event_id'].append(eid)
            dic['agg_id'].append(kid)
            dic['loss_id'].append(lti)
            for sname, si in ci.items():
                dic[sname].append(dd[lti, si])
    fix_dic(dic, ci)
    return pandas.DataFrame(dic)


def worst_dmgdist(df, agg_id, loss_id, dic):
    cols = [col for col in df.columns if col.startswith('dmg_')]
    event_id = df[cols[-1]].to_numpy().argmax()
    dic['event_id'].append(event_id)
    dic['loss_id'].append(loss_id)
    dic['agg_id'].append(agg_id)
    for col in cols:
        dic[col].append(df[col].to_numpy()[event_id])


@base.calculators.add('event_based_damage')
class DamageCalculator(EventBasedRiskCalculator):
    """
    Damage calculator
    """
    core_task = event_based_damage
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based',
                      'event_based_risk', 'event_based_damage']

    def save_avg_losses(self):
        """
        Do nothing: there are no losses in the DamageCalculator
        """

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        self.builder = get_loss_builder(self.datastore)  # check
        eids = self.datastore['gmf_data/eid'][:]
        logging.info('Processing {:_d} rows of gmf_data'.format(len(eids)))
        self.dmgcsq = zero_dmgcsq(self.assetcol, self.crmodel)
        self.datastore.swmr_on()
        smap = parallel.Starmap(
            event_based_damage, self.gen_args(eids), h5=self.datastore.hdf5)
        smap.monitor.save('assets', self.assetcol.to_dframe())
        smap.monitor.save('crmodel', self.crmodel)
        return smap.reduce(self.combine)

    def combine(self, acc, res):
        """
        :param acc:
            unused
        :param res:
            DataFrame with fields (event_id, agg_id, loss_id, dmg1 ...)
            plus array with damages and consequences of shape (A, Dc)

        Combine the results and grows risk_by_event with fields
        (event_id, agg_id, loss_id) and (dmg_0, dmg_1, dmg_2, ...)
        """
        df, dmgcsq = res
        self.dmgcsq += dmgcsq
        with self.monitor('saving risk_by_event', measuremem=True):
            for name in df.columns:
                dset = self.datastore['risk_by_event/' + name]
                hdf5.extend(dset, df[name].to_numpy())
        return 1

    def sanity_check(self):
        """
        Compare agglosses with aggregate avglosses and check that
        damaged buildings < total buildings
        """
        ac_df = self.datastore.read_df(
            'aggcurves', sel=dict(agg_id=self.param['K']))
        number = self.assetcol['number'].sum()
        for (loss_id, period), df in ac_df.groupby(
                ['loss_id', 'return_period']):
            tot = sum(df[col].sum() for col in df.columns
                      if col.startswith('dmg_'))
            if tot > number:
                logging.info('For loss type %s, return_period=%d the '
                             'damaged buildings are %d > %d, but it is okay',
                             self.oqparam.loss_names[loss_id],
                             period, tot, number)

    def post_execute(self, dummy):
        oq = self.oqparam
        A, L, Dc = self.dmgcsq.shape
        D = len(self.crmodel.damage_states)
        # fix no_damage distribution for events with zero damage
        number = self.assetcol['number']
        for li in range(L):
            self.dmgcsq[:, li, 0] = (
                number * self.E - self.dmgcsq[:, li, 1:D].sum(axis=1))
        self.dmgcsq /= self.E
        self.datastore['damages-rlzs'] = self.dmgcsq.reshape((A, 1, L, Dc))
        set_rlzs_stats(self.datastore,
                       'damages',
                       asset_id=self.assetcol['id'],
                       rlz=[0],
                       loss_type=oq.loss_names,
                       dmg_state=['no_damage'] + self.crmodel.get_dmg_csq())
        size = self.datastore.getsize('risk_by_event')
        logging.info('Building aggregated curves from %s of risk_by_event',
                     general.humansize(size))
        alt_df = self.datastore.read_df('risk_by_event')
        del alt_df['event_id']
        dic = general.AccumDict(accum=[])
        columns = [col for col in alt_df.columns
                   if col not in {'agg_id', 'loss_id', 'variance'}]
        csqs = [col for col in columns if not col.startswith('dmg_')]
        periods = list(self.builder.return_periods)
        wdd = {'agg_id': [], 'loss_id': [], 'event_id': []}
        for col in columns[:D-1]:
            wdd[col] = []
        for (agg_id, loss_id), df in alt_df.groupby(
                [alt_df.agg_id, alt_df.loss_id]):
            worst_dmgdist(df, agg_id, loss_id, wdd)
            curves = [self.builder.build_curve(df[csq].to_numpy())
                      for csq in csqs]
            for p, period in enumerate(periods):
                dic['agg_id'].append(agg_id)
                dic['loss_id'].append(loss_id)
                dic['return_period'].append(period)
                for col, curve in zip(csqs, curves):
                    dic[col].append(curve[p])
        fix_dic(dic, csqs)
        fix_dic(wdd, columns[:D-1])
        ls = ' '.join(self.crmodel.damage_states[1:])
        self.datastore.create_df('worst_dmgdist', wdd.items(), limit_states=ls)
        if csqs:
            self.datastore.create_df('aggcurves', dic.items(), limit_states=ls)
            self.sanity_check()
