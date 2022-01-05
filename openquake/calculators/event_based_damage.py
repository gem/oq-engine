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
from openquake.calculators.post_risk import (
    get_loss_builder, fix_dtypes, PostRiskCalculator)

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


def zero_dmgcsq(A, R, crmodel):
    """
    :returns: an array of zeros of shape (A, R, L, Dc)
    """
    dmg_csq = crmodel.get_dmg_csq()
    L = len(crmodel.loss_types)
    Dc = len(dmg_csq) + 1  # damages + consequences
    return numpy.zeros((A, R, L, Dc), F32)


def event_based_damage(df, oqparam, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_X, ...
    :param oqparam: parameters coming from the job.ini
    :param monitor: a Monitor instance
    :returns: (damages (eid, kid) -> LDc plus damages (A, Dc))
    """
    mon_risk = monitor('computing risk', measuremem=False)
    dstore = datastore.read(oqparam.hdf5path)
    K = oqparam.K
    with monitor('reading gmf_data'):
        if hasattr(df, 'start'):  # it is actually a slice
            df = dstore.read_df('gmf_data', slc=df)
        assets_df = dstore.read_df('assetcol/array', 'ordinal')
        kids = (dstore['assetcol/kids'][:] if K
                else numpy.zeros(len(assets_df), U16))
        crmodel = monitor.read('crmodel')
    master_seed = oqparam.master_seed
    sec_sims = oqparam.secondary_simulations.items()
    dmg_csq = crmodel.get_dmg_csq()
    ci = {dc: i + 1 for i, dc in enumerate(dmg_csq)}
    dmgcsq = zero_dmgcsq(len(assets_df), oqparam.R, crmodel)
    A, R, L, Dc = dmgcsq.shape
    D = len(crmodel.damage_states)
    if R > 1:
        allrlzs = dstore['events']['rlz_id']
    loss_types = crmodel.oqparam.loss_types
    float_dmg_dist = oqparam.float_dmg_dist  # True by default
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
            if sec_sims or not float_dmg_dist:
                rng = scientific.MultiEventRNG(
                    master_seed, numpy.unique(eids))
            for prob_field, num_sims in sec_sims:
                probs = gmf_df[prob_field].to_numpy()   # LiqProb
                if not float_dmg_dist:
                    dprobs = rng.boolean_dist(probs, num_sims).mean(axis=1)
            for taxo, adf in asset_df.groupby('taxonomy'):
                out = crmodel.get_output(taxo, adf, gmf_df)
                aids = adf.index.to_numpy()
                assets = adf.to_records()
                if float_dmg_dist:
                    number = assets['value-number']
                else:
                    number = U32(assets['value-number'])
                for lti, lt in enumerate(loss_types):
                    fractions = out[lt]
                    Asid, E, D = fractions.shape
                    assert len(eids) == E
                    d3 = numpy.zeros((Asid, E, Dc), F32)
                    if float_dmg_dist:
                        d3[:, :, :D] = fractions
                        for a in range(Asid):
                            d3[a] *= number[a]
                    else:
                        # this is a performance distaster; for instance
                        # the Messina test in oq-risk-tests becomes 12x
                        # slower even if it has only 25_736 assets
                        d3[:, :, :D] = rng.discrete_dmg_dist(
                            eids, fractions, number)

                    # secondary perils and consequences
                    for a, asset in enumerate(assets):
                        if sec_sims:
                            for d in range(1, D):
                                # doing the mean on the secondary simulations
                                if float_dmg_dist:
                                    d3[a, :, d] *= probs
                                else:
                                    d3[a, :, d] *= dprobs

                        csq = crmodel.compute_csq(
                            asset, d3[a, :, :D] / number[a], lt)
                        for name, values in csq.items():
                            d3[a, :, ci[name]] = values
                    if R == 1:
                        dmgcsq[aids, 0, lti] += d3.sum(axis=1)
                    else:
                        for e, rlz in enumerate(rlzs):
                            dmgcsq[aids, rlz, lti] += d3[:, e]
                    tot = d3.sum(axis=0)  # sum on the assets
                    for e, eid in enumerate(eids):
                        dddict[eid, K][lti] += tot[e]
                        if K:
                            for a, aid in enumerate(aids):
                                dddict[eid, kids[aid]][lti] += d3[a, e]
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
    fix_dtypes(dic)
    return pandas.DataFrame(dic)


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

    def create_avg_losses(self):
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
        oq.R = self.R  # 1 if collect_rlzs
        oq.float_dmg_dist = not oq.discrete_damage_distribution
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

    def post_execute(self, dummy):
        """
        Store damages-rlzs/stats, aggrisk and aggcurves
        """
        oq = self.oqparam
        # no damage check
        if self.dmgcsq[:, :, :, 1:].sum() == 0:
            self.nodamage = True
            logging.warning(
                'There is no damage, perhaps the hazard is too small?')
            return

        prc = PostRiskCalculator(oq, self.datastore.calc_id)
        prc.assetcol = self.assetcol
        if hasattr(self, 'exported'):
            prc.exported = self.exported
        with prc.datastore:
            prc.run(exports='')

        A, R, L, Dc = self.dmgcsq.shape
        D = len(self.crmodel.damage_states)
        # fix no_damage distribution for events with zero damage
        number = self.assetcol['value-number']
        for r in range(self.R):
            ne = prc.num_events[r]
            for li in range(L):
                self.dmgcsq[:, r, li, 0] = (  # no damage
                    number * ne - self.dmgcsq[:, r, li, 1:D].sum(axis=1))
            self.dmgcsq[:, r] /= ne
        self.datastore['damages-rlzs'] = self.dmgcsq
        set_rlzs_stats(self.datastore,
                       'damages',
                       asset_id=self.assetcol['id'],
                       rlz=numpy.arange(self.R),
                       loss_type=oq.loss_types,
                       dmg_state=['no_damage'] + self.crmodel.get_dmg_csq())
