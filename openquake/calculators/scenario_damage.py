# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict, humansize
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.calculators import base, views

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


def floats_in(numbers):
    """
    :param numbers: an array of numbers
    :returns: number of non-uint32 number
    """
    return (U32(numbers) != numbers).sum()


def bin_ddd(fractions, n, seed):
    """
    Converting fractions into discrete damage distributions using bincount
    and numpy.random.choice
    """
    n = int(n)
    D = fractions.shape[1]  # shape (E, D)
    ddd = numpy.zeros(fractions.shape, U32)
    numpy.random.seed(seed)
    for e, frac in enumerate(fractions):
        ddd[e] = numpy.bincount(
            numpy.random.choice(D, n, p=frac/frac.sum()), minlength=D)
    return ddd


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


def scenario_damage(riskinputs, param, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :param param:
        dictionary of extra parameters
    :returns:
        a dictionary of arrays
    """
    crmodel = monitor.read('crmodel')
    L = len(crmodel.loss_types)
    D = len(crmodel.damage_states)
    consequences = crmodel.get_consequences()

    # algorithm used to compute the discrete damage distributions
    float_dmg_dist = param['float_dmg_dist']
    z = numpy.zeros((L, D - 1), F32 if float_dmg_dist else U32)
    d_event = AccumDict(accum=z)
    res = {'d_event': d_event, 'd_asset': []}
    for name in consequences:
        res['avg_' + name] = []
    seed = param['master_seed']
    num_events = param['num_events']  # per realization
    acc = []  # (aid, eid, lid, ds...)
    sec_sims = param['secondary_simulations'].items()
    mon = monitor('getting hazard', measuremem=False)
    for ri in riskinputs:
        with mon:
            df = ri.hazard_getter.get_hazard()
        R = ri.hazard_getter.num_rlzs
        for r in range(R):
            ne = num_events[r]  # total number of events
            ok = df.rlz.to_numpy() == r  # events beloging to rlz r
            if ok.sum() == 0:
                continue
            gmf_df = df[ok]
            eids = gmf_df.eid.to_numpy()
            for taxo, asset_df in ri.asset_df.groupby('taxonomy'):
                assets = asset_df.to_records()
                out = crmodel.get_output(taxo, asset_df, gmf_df)
                for lti, loss_type in enumerate(crmodel.loss_types):
                    for asset, fractions in zip(assets, out[loss_type]):
                        aid = asset['ordinal']
                        if float_dmg_dist:
                            damages = fractions * asset['number']
                            if sec_sims:
                                run_sec_sims(
                                    damages, gmf_df, sec_sims, seed + aid)
                        else:
                            damages = bin_ddd(
                                fractions, asset['number'], seed + aid)
                        # damages has shape E', D with E' == len(eids)
                        csq = crmodel.compute_csq(asset, fractions, loss_type)
                        for e, ddd in enumerate(damages):
                            dmg = ddd[1:]
                            if dmg.sum():
                                eid = eids[e]  # (aid, eid, lti) is unique
                                conseq = tuple(csq[name][e] for name in csq)
                                acc.append(
                                    (aid, eid, lti) + tuple(dmg) + conseq)
                                d_event[eid][lti] += ddd[1:]
                        tot = damages.sum(axis=0)  # (E', D) -> D
                        nodamage = asset['number'] * (ne - len(damages))
                        tot[0] += nodamage
                        res['d_asset'].append((lti, r, aid, tot))
                        for name, values in csq.items():
                            res['avg_%s' % name].append(
                                (lti, r, asset['ordinal'], values.sum(axis=0)))
    res['aed'] = numpy.array(acc, param['asset_damage_dt'])
    return res


@base.calculators.add('scenario_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Damage calculator
    """
    core_task = scenario_damage
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based', 'event_based_risk']

    def pre_execute(self):
        oq = self.oqparam
        super().pre_execute()
        num_floats = floats_in(self.assetcol['number'])
        if num_floats:
            logging.warning(
                'The exposure contains %d non-integer asset numbers: '
                'using floating point damage distributions', num_floats)
        bad = self.assetcol['number'] > 2**32 - 1
        for ass in self.assetcol[bad]:
            aref = self.assetcol.tagcol.id[ass['id']]
            logging.error("The asset %s has number=%s > 2^32-1!",
                          aref, ass['number'])
        self.param['secondary_simulations'] = oq.secondary_simulations
        self.param['float_dmg_dist'] = oq.float_dmg_dist or num_floats
        self.param['asset_damage_dt'] = self.crmodel.asset_damage_dt(
            oq.float_dmg_dist or num_floats)
        self.param['master_seed'] = oq.master_seed
        self.param['num_events'] = ne = numpy.bincount(  # events by rlz
            self.datastore['events']['rlz_id'], minlength=self.R)
        if (ne == 0).any():
            logging.warning('There are realizations with zero events')
        base.create_risk_by_event(self)
        self.riskinputs = self.build_riskinputs('gmf')

    def combine(self, acc, res):
        """
        Combine the results and grows the risk_by_event
        """
        if res is None:
            raise MemoryError('You ran out of memory!')
        with self.monitor('saving risk_by_event', measuremem=True):
            aed = res.pop('aed', ())
            if len(aed) == 0:
                return acc + res
            for name in aed.dtype.names:
                hdf5.extend(
                    self.datastore['risk_by_event/' + name], aed[name])
            return acc + res

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        if not result:
            self.collapsed()
            return
        dstates = self.crmodel.damage_states
        ltypes = self.crmodel.loss_types
        L = self.L = len(ltypes)
        R = self.R
        D = len(dstates)
        A = len(self.assetcol)
        E = len(self.datastore['events'])

        # reduction factor
        matrixsize = A * E * L * 4
        realsize = self.datastore.getsize('risk_by_event')
        logging.info('Saving %s in risk_by_event (instead of %s)',
                     humansize(realsize), humansize(matrixsize))

        # avg_ratio = ratio used when computing the averages
        oq = self.oqparam
        avg_ratio = 1. / self.param['num_events']

        # damage by asset
        d_asset = numpy.zeros((A, R, L, D), F32)
        for (l, r, a, tot) in result['d_asset']:
            d_asset[a, r, l] = tot * avg_ratio[r]
        self.datastore['damages-rlzs'] = d_asset
        set_rlzs_stats(self.datastore,
                       'damages',
                       asset_id=self.assetcol['id'],
                       loss_type=oq.loss_names,
                       dmg_state=dstates)

        tot = self.assetcol['number'].sum()
        dt = F32 if self.param['float_dmg_dist'] else U32
        dbe = numpy.zeros((self.E, L, D), dt)  # shape E, L, D
        dbe[:, :, 0] = tot
        alt = self.datastore.read_df('risk_by_event')
        df = alt.groupby(['event_id', 'loss_id']).sum().reset_index()
        df['agg_id'] = A
        for col in df.columns:
            hdf5.extend(self.datastore['risk_by_event/' + col], df[col])
        self.datastore.set_attrs('risk_by_event', K=A)
        self.sanity_check()

        # consequence distributions
        del result['d_asset']
        del result['d_event']
        for name, csq in result.items():
            # name is something like avg_losses
            c_asset = numpy.zeros((A, R, L), F32)
            for (l, r, a, stat) in result[name]:
                c_asset[a, r, l] = stat * avg_ratio[r]
            self.datastore[name + '-rlzs'] = c_asset
            set_rlzs_stats(self.datastore, name,
                           asset_id=self.assetcol['id'],
                           loss_type=oq.loss_names)

    def sanity_check(self):
        """
        Sanity check on the total number of assets
        """
        if self.R == 1:
            arr = self.datastore.sel('damages-rlzs')  # shape (A, 1, L, D)
        else:
            arr = self.datastore.sel('damages-stats', stat='mean')
        avg = arr.sum(axis=(0, 1))  # shape (L, D)
        if not len(self.datastore['risk_by_event/agg_id']):
            logging.warning('There is no damage at all!')
        elif 'avg_portfolio_damage' in self.datastore:
            df = views.portfolio_damage_error(
                'avg_portfolio_damage', self.datastore)
            rst = views.text_table(df, ext='org')
            logging.info('Portfolio damage\n%s' % rst)
        num_assets = avg.sum(axis=1)  # by loss_type
        expected = self.assetcol['number'].sum()
        nums = set(num_assets) | {expected}
        if len(nums) > 1:
            numdic = dict(expected=expected)
            for lt, num in zip(self.oqparam.loss_names, num_assets):
                numdic[lt] = num
            logging.info(
                'Due to rounding errors inherent in floating-point arithmetic,'
                ' the total number of assets is not exact: %s', numdic)
