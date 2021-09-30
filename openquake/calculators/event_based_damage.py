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
from openquake.risklib import scientific
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


def zero_dmgcsq(A, R, crmodel):
    """
    :returns: an array of zeros of shape (A, R, L, Dc)
    """
    dmg_csq = crmodel.get_dmg_csq()
    L = len(crmodel.loss_types)
    Dc = len(dmg_csq) + 1  # damages + consequences
    return numpy.zeros((A, R, L, Dc), F32)


def run_sec_sims(damages, haz, sec_sims, seed):
    """
    :param damages: array of shape (E, D) for a given asset
    :param haz: dataframe of size E with a probability field
    :param sec_sims: pair (probability field, number of simulations)
    :param seed: random seed to use

    Run secondary simulations and update the array damages
    """
    [(prob_field, num_sims)] = sec_sims
    numpy.random.seed(seed)
    probs = haz[prob_field].to_numpy()   # LiqProb
    affected = numpy.random.random((num_sims, 1)) < probs  # (N, E)
    for d, buildings in enumerate(damages.T[1:], 1):
        # doing the mean on the secondary simulations for each event
        damages[:, d] = numpy.mean(affected * buildings, axis=0)  # shape E


def event_based_damage(df, param, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_X, ...
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
    seed = crmodel.oqparam.master_seed
    sec_sims = crmodel.oqparam.secondary_simulations.items()
    dmg_csq = crmodel.get_dmg_csq()
    ci = {dc: i + 1 for i, dc in enumerate(dmg_csq)}
    dmgcsq = zero_dmgcsq(len(assets_df), param['R'], crmodel)
    A, R, L, Dc = dmgcsq.shape
    D = len(crmodel.damage_states)
    if R > 1:
        allrlzs = dstore['events']['rlz_id']
    loss_names = crmodel.oqparam.loss_names
    float_dmg_dist = param['float_dmg_dist']  # True by default
    with mon_risk:
        dddict = general.AccumDict(accum=numpy.zeros((L, Dc), F32))  # eid, kid
        for sid, asset_df in assets_df.groupby('site_id'):
            # working one site at the time
            gmf_df = df[df.sid == sid]
            if len(gmf_df) == 0:
                continue
            eids = gmf_df.eid.to_numpy()
            if R > 1:
                rlzs = allrlzs[eids]
            if not float_dmg_dist:
                rndgen = scientific.MultiEventRNG(seed, numpy.unique(eids))
            for taxo, adf in asset_df.groupby('taxonomy'):
                out = crmodel.get_output(taxo, adf, gmf_df)
                aids = adf.index.to_numpy()
                assets = adf.to_records()
                if float_dmg_dist:
                    number = assets['value-number']
                else:
                    number = U32(assets['value-number'])
                for lti, lt in enumerate(loss_names):
                    fractions = out[lt]
                    Asid, E, D = fractions.shape
                    assert len(eids) == E
                    ddd = numpy.zeros((Asid, E, Dc), F32)
                    if float_dmg_dist:
                        ddd[:, :, :D] = fractions
                        for a in range(Asid):
                            ddd[a] *= number[a]
                    else:
                        # this is a performance distaster; for instance
                        # the Messina test in oq-risk-tests becomes 12x
                        # slower even if it has only 25_736 assets
                        ddd[:, :, :D] = rndgen.discrete_dmg_dist(
                            eids, fractions, number)

                    # secondary perils and consequences
                    for a, asset in enumerate(assets):
                        if sec_sims:
                            run_sec_sims(ddd[a], gmf_df, sec_sims, seed + a)
                        csq = crmodel.compute_csq(asset, fractions[a], lt)
                        for name, values in csq.items():
                            ddd[a, :, ci[name]] = values
                    if R == 1:
                        dmgcsq[aids, 0, lti] += ddd.sum(axis=1)
                    else:
                        for e, rlz in enumerate(rlzs):
                            dmgcsq[aids, rlz, lti] += ddd[:, e]
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


@base.calculators.add('event_based_damage', 'scenario_damage')
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
        oq = self.oqparam
        number = self.assetcol['value-number']
        num_floats = (U32(number) != number).sum()
        if oq.discrete_damage_distribution and num_floats:
            raise ValueError(
                'The exposure contains %d non-integer asset numbers: '
                'you cannot use dicrete_damage_distribution=true' % num_floats)
        self.param['R'] = self.R  # 1 if collect_rlzs
        self.param['float_dmg_dist'] = not oq.discrete_damage_distribution
        if oq.investigation_time:  # event based
            self.builder = get_loss_builder(self.datastore)  # check
        eids = self.datastore['gmf_data/eid'][:]
        logging.info('Processing {:_d} rows of gmf_data'.format(len(eids)))
        self.dmgcsq = zero_dmgcsq(len(self.assetcol), self.R, self.crmodel)
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
        number = self.assetcol['value-number'].sum()
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
        """
        Store damages-rlzs/stats, aggrisk and aggcurves
        """
        oq = self.oqparam
        A, R, L, Dc = self.dmgcsq.shape
        D = len(self.crmodel.damage_states)
        # fix no_damage distribution for events with zero damage
        number = self.assetcol['value-number']
        num_events = numpy.bincount(  # events by rlz
            self.datastore['events']['rlz_id'], minlength=self.R)
        for r in range(self.R):
            ne = num_events[r]
            for li in range(L):
                self.dmgcsq[:, r, li, 0] = (  # no damage
                    number * ne - self.dmgcsq[:, r, li, 1:D].sum(axis=1))
            self.dmgcsq[:, r] /= ne
        self.datastore['damages-rlzs'] = self.dmgcsq
        set_rlzs_stats(self.datastore,
                       'damages',
                       asset_id=self.assetcol['id'],
                       rlz=numpy.arange(self.R),
                       loss_type=oq.loss_names,
                       dmg_state=['no_damage'] + self.crmodel.get_dmg_csq())
        # sanity check
        if self.dmgcsq[:, :, :, 1:].sum() == 0:
            self.nodamage = True
            logging.warning(
                'There is no damage, perhaps the hazard is too small?')
        if oq.investigation_time is None:  # scenario
            return
        size = self.datastore.getsize('risk_by_event')
        logging.info('Building aggregated curves from %s of risk_by_event',
                     general.humansize(size))
        alt_df = self.datastore.read_df('risk_by_event')
        if self.R > 1:
            rlz_id = self.datastore['events']['rlz_id']
            alt_df['rlz_id'] = rlz_id[alt_df.event_id.to_numpy()]
        else:
            alt_df['rlz_id'] = 0
        del alt_df['event_id']
        dic = general.AccumDict(accum=[])
        columns = [col for col in alt_df.columns
                   if col not in {'agg_id', 'rlz_id', 'loss_id', 'variance'}]
        csqs = [col for col in columns if not col.startswith('dmg_')]
        periods = list(self.builder.return_periods)
        wdd = {'agg_id': [], 'loss_id': [], 'event_id': []}
        for col in columns[:D-1]:
            wdd[col] = []
        aggrisk = general.AccumDict(accum=[])
        for (agg_id, rlz_id, loss_id), df in alt_df.groupby(
                ['agg_id', 'rlz_id', 'loss_id']):
            aggrisk['agg_id'].append(agg_id)
            aggrisk['rlz_id'].append(rlz_id)
            aggrisk['loss_id'].append(loss_id)
            for csq in csqs:
                aggrisk[csq].append(df[csq].sum() * oq.time_ratio)
            worst_dmgdist(df, agg_id, loss_id, wdd)
            curves = [self.builder.build_curve(df[csq].to_numpy())
                      for csq in csqs]
            for p, period in enumerate(periods):
                dic['agg_id'].append(agg_id)
                dic['rlz_id'].append(rlz_id)
                dic['loss_id'].append(loss_id)
                dic['return_period'].append(period)
                for col, curve in zip(csqs, curves):
                    dic[col].append(curve[p])
        fix_dic(dic, csqs)
        fix_dic(wdd, columns[:D-1])
        ls = ' '.join(self.crmodel.damage_states[1:])
        self.datastore.create_df('worst_dmgdist', wdd.items(), limit_states=ls)
        if csqs:
            self.datastore.create_df('aggrisk', pandas.DataFrame(aggrisk))
            self.datastore.create_df('aggcurves', pandas.DataFrame(dic),
                                     limit_states=ls)
            self.sanity_check()
