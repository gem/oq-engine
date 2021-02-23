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

import copy
import logging
import numpy
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import scientific, riskinput
from openquake.calculators import base, post_risk, views

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency


def run_sec_sims(out, loss_types, sec_sims, seed):
    """
    :param out: a dictionary of losses
    :param loss_types: the loss types
    :param sec_sims: pair (probability field, number of simulations)
    :param seed: random seed to use

    Run secondary simulations and update the losses
    """
    [(prob_field, num_sims)] = sec_sims
    numpy.random.seed(seed)
    probs = out.haz[prob_field].to_numpy()   # LiqProb
    affected = numpy.random.random((num_sims, 1)) < probs  # (N, E)
    # doing the mean on the secondary simulations for each event
    for lt in loss_types:
        out[lt][:] = numpy.mean(affected * out[lt], axis=0)  # shape E


def event_based_risk(riskinputs, param, monitor):
    """
    Core function for a scenario_risk/event_based_risk computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary {
        'alt': AggLoggTable instance
        'losses_by_asset': list of tuples
        (lt_idx, rlz_idx, asset_ordinal, totloss)}
    """
    crmodel = monitor.read('crmodel')
    alt = copy.copy(param['alt'])
    result = dict(losses_by_asset=[], alt=alt)
    sec_sims = param['secondary_simulations'].items()
    for ri in riskinputs:
        for out in ri.gen_outputs(crmodel, monitor, param['tempname']):
            if sec_sims:
                run_sec_sims(out, crmodel.loss_types, sec_sims,
                             param['master_seed'])
            alt.aggregate(
                out, param['minimum_asset_loss'], param['aggregate_by'])
            for lti, loss_type in enumerate(crmodel.loss_types):
                losses = out[loss_type]
                for a, asset in enumerate(ri.assets):
                    aid = asset['ordinal']
                    lba = losses[a].sum()
                    if lba:
                        result['losses_by_asset'].append(
                            (lti, out.rlzi, aid, lba))
    return result


@base.calculators.add('scenario_risk', 'event_based_risk')
class EventBasedRiskCalculator(base.RiskCalculator):
    """
    Run a scenario/event_based risk calculation
    """
    core_task = event_based_risk
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based', 'event_based_risk', 'ebrisk']

    def pre_execute(self):
        """
        Compute the GMFs, build the epsilons, the riskinputs, and a dictionary
        with the unit of measure, used in the export phase.
        """
        oq = self.oqparam
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
        if not oq.ground_motion_fields:
            return  # this happens in the reportwriter

        self.assetcol = self.datastore['assetcol']
        self.riskinputs = self.build_riskinputs('gmf')
        self.param['tempname'] = riskinput.cache_epsilons(
            self.datastore, oq, self.assetcol, self.crmodel, self.E)
        self.param['aggregate_by'] = oq.aggregate_by
        self.param['secondary_simulations'] = oq.secondary_simulations
        self.param['master_seed'] = oq.master_seed
        self.rlzs = self.datastore['events']['rlz_id']
        self.num_events = numpy.bincount(self.rlzs)  # events by rlz
        aggkey = self.assetcol.tagcol.get_aggkey(oq.aggregate_by)
        self.param['alt'] = self.acc = scientific.AggLossTable.new(
            aggkey, oq.loss_names, sec_losses=[])
        L = len(oq.loss_names)
        self.avglosses = numpy.zeros((len(self.assetcol), self.R, L), F32)
        if oq.investigation_time:  # event_based
            self.avg_ratio = numpy.array([oq.ses_ratio] * self.R)
        else:  # scenario
            self.avg_ratio = 1. / self.num_events

    def combine(self, acc, res):
        if res is None:
            raise MemoryError('You ran out of memory!')
        with self.monitor('aggregating losses', measuremem=False):
            self.acc += res['alt']
            for (l, r, aid, lba) in res['losses_by_asset']:
                self.avglosses[aid, r, l] = lba * self.avg_ratio[r]
        return acc

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        oq = self.oqparam
        L = len(oq.loss_names)
        # avg losses must be 32 bit otherwise export losses_by_asset will
        # break the QGIS test for ScenarioRisk
        self.datastore['avg_losses-rlzs'] = self.avglosses
        set_rlzs_stats(self.datastore, 'avg_losses',
                       asset_id=self.assetcol['id'],
                       loss_type=self.oqparam.loss_names)

        with self.monitor('saving agg_loss_table'):
            logging.info('Saving the agg_loss_table')
            K = len(result.aggkey)
            alt = result.to_dframe()
            self.datastore.create_dframe('agg_loss_table', alt)

        # save agg_losses
        units = self.datastore['cost_calculator'].get_units(oq.loss_names)
        if oq.investigation_time is None:  # scenario, compute agg_losses
            alt['rlz_id'] = self.rlzs[alt.event_id.to_numpy()]
            agglosses = numpy.zeros((K, self.R, L), F32)
            for (agg_id, rlz_id), df in alt.groupby(['agg_id', 'rlz_id']):
                agglosses[agg_id, rlz_id] = numpy.array(
                    [df[ln].sum() for ln in oq.loss_names]
                ) * self.avg_ratio[rlz_id]
            self.datastore['agg_losses-rlzs'] = agglosses
            set_rlzs_stats(self.datastore, 'agg_losses',
                           agg_id=K, loss_types=oq.loss_names, units=units)
            logging.info('Total portfolio loss\n' +
                         views.view('portfolio_loss', self.datastore))
        else:  # event_based_risk, run post_risk
            prc = post_risk.PostRiskCalculator(oq, self.datastore.calc_id)
            if hasattr(self, 'exported'):
                prc.exported = self.exported
            prc.run(exports='')
            try:
                agglosses = self.datastore['agg_losses-rlzs'][K - 1]
            except KeyError:  # not enough events in post_risk
                logging.error('No agg_losses-rlzs')
                return

        # sanity check on the agg_losses and sum_losses
        sumlosses = self.avglosses.sum(axis=0)
        if not numpy.allclose(agglosses, sumlosses, rtol=1E-6):
            url = ('https://docs.openquake.org/oq-engine/advanced/'
                   'addition-is-non-associative.html')
            logging.warning(
                'Due to rounding errors inherent in floating-point arithmetic,'
                ' agg_losses != sum(avg_losses): %s != %s\nsee %s',
                agglosses.mean(), sumlosses.mean(), url)
