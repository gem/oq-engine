# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.baselib.general import AccumDict
from openquake.commonlib import calc
from openquake.risklib import scientific
from openquake.calculators import base


F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency


def scenario_risk(riskinput, riskmodel, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary {
        'agg': array of shape (E, L, R, 2),
        'avg': list of tuples (lt_idx, rlz_idx, asset_idx, statistics)
        }
        where E is the number of simulated events, L the number of loss types,
        R the number of realizations  and statistics is an array of shape
        (n, R, 4), with n the number of assets in the current riskinput object
    """
    E = monitor.oqparam.number_of_ground_motion_fields
    L = len(riskmodel.loss_types)
    R = len(riskinput.rlzs)
    I = monitor.oqparam.insured_losses + 1
    all_losses = monitor.oqparam.all_losses
    result = dict(agg=numpy.zeros((E, L, R, I), F64), avg=[],
                  all_losses=AccumDict(accum={}))
    for outputs in riskmodel.gen_outputs(riskinput, monitor):
        r = outputs.r
        assets = outputs.assets
        for l, out in enumerate(outputs):
            if out is None:  # this may happen
                continue
            stats = numpy.zeros((len(assets), 2), (F32, I))  # mean, stddev
            for aid, asset in enumerate(assets):
                stats[aid, 0] = out[aid].mean()
                stats[aid, 1] = out[aid].std(ddof=1)
                result['avg'].append((l, r, asset.ordinal, stats[aid]))
            agglosses = out.sum(axis=0)  # shape E, I
            for i in range(I):
                result['agg'][:, l, r, i] += agglosses[:, i]
            if all_losses:
                aids = [asset.ordinal for asset in outputs.assets]
                result['all_losses'][l, r] = AccumDict(zip(aids, out))
    return result


@base.calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Run a scenario risk calculation
    """
    core_task = scenario_risk
    pre_calculator = 'scenario'
    is_stochastic = True

    def pre_execute(self):
        """
        Compute the GMFs, build the epsilons, the riskinputs, and a dictionary
        with the unit of measure, used in the export phase.
        """
        if 'gmfs' in self.oqparam.inputs:
            self.pre_calculator = None
        base.RiskCalculator.pre_execute(self)

        logging.info('Building the epsilons')
        if self.oqparam.ignore_covs:
            eps = None
        else:
            eps = self.make_eps(self.oqparam.number_of_ground_motion_fields)
        self.datastore['etags'], gmfs = calc.get_gmfs(
            self.datastore, self.precalc)
        hazard_by_rlz = {rlz: gmfs[rlz.ordinal]
                         for rlz in self.rlzs_assoc.realizations}
        self.riskinputs = self.build_riskinputs(hazard_by_rlz, eps)

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        ltypes = self.riskmodel.loss_types
        I = self.oqparam.insured_losses + 1
        stat_dt = numpy.dtype([('mean', (F32, I)), ('stddev', (F32, I))])
        multi_stat_dt = numpy.dtype([(lt, stat_dt) for lt in ltypes])
        with self.monitor('saving outputs', autoflush=True):
            A = len(self.assetcol)

            # agg losses
            res = result['agg']
            E, L, R, I = res.shape
            if I == 1:
                res = res.reshape(E, L, R)
            mean, std = scientific.mean_std(res)
            agglosses = numpy.zeros(R, multi_stat_dt)
            for l, lt in enumerate(ltypes):
                agglosses[lt]['mean'] = numpy.float32(mean[l])
                agglosses[lt]['stddev'] = numpy.float32(std[l])

            # average losses
            avglosses = numpy.zeros((A, R), multi_stat_dt)
            for (l, r, aid, stat) in result['avg']:
                avglosses[ltypes[l]][aid, r] = stat
            self.datastore['losses_by_asset'] = avglosses
            self.datastore['agglosses-rlzs'] = agglosses

            if self.oqparam.all_losses:
                loss_dt = self.oqparam.loss_dt()
                array = numpy.zeros((A, E, R), loss_dt)
                for (l, r), losses_by_aid in result['all_losses'].items():
                    for aid in losses_by_aid:
                        lba = losses_by_aid[aid]  # (E, I)
                        array[ltypes[l]][aid, :, r] = lba[:, 0]
                        if I == 2:
                            array[ltypes[l] + '_ins'][aid, :, r] = lba[:, 1]
                self.datastore['all_losses-rlzs'] = array
