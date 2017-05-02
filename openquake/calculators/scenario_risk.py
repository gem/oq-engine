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

from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict
from openquake.commonlib import calc
from openquake.risklib import scientific
from openquake.calculators import base


F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def scenario_risk(riskinput, riskmodel, param, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
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
    E = param['number_of_ground_motion_fields']
    L = len(riskmodel.loss_types)
    R = len(riskinput.rlzs)
    I = param['insured_losses'] + 1
    asset_loss_table = param['asset_loss_table']
    lbt = AccumDict(accum=numpy.zeros((R, L * I), F32))
    result = dict(agg=numpy.zeros((E, R, L * I), F32), avg=[],
                  losses_by_taxon=lbt, all_losses=AccumDict(accum={}))
    for outputs in riskmodel.gen_outputs(riskinput, monitor):
        r = outputs.r
        assets = outputs.assets
        for l, losses in enumerate(outputs):
            if losses is None:  # this may happen
                continue
            stats = numpy.zeros((len(assets), I), stat_dt)  # mean, stddev
            for a, asset in enumerate(assets):
                stats['mean'][a] = losses[a].mean()
                stats['stddev'][a] = losses[a].std(ddof=1)
                result['avg'].append((l, r, asset.ordinal, stats[a]))
                for i in range(I):
                    lbt[asset.taxonomy][r, l + L * i] += losses[a].sum()
            agglosses = losses.sum(axis=0)  # shape E, I
            for i in range(I):
                result['agg'][:, r, l + L * i] += agglosses[:, i]
            if asset_loss_table:
                aids = [asset.ordinal for asset in outputs.assets]
                result['all_losses'][l, r] += AccumDict(zip(aids, losses))
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
        A = len(self.assetcol)
        E = self.oqparam.number_of_ground_motion_fields
        if self.oqparam.ignore_covs:
            eps = numpy.zeros((A, E), numpy.float32)
        else:
            eps = self.make_eps(E)
        self.datastore['etags'], gmfs = calc.get_gmfs(
            self.datastore, self.precalc)
        hazard_by_rlz = {rlz: gmfs[rlz.ordinal]
                         for rlz in self.rlzs_assoc.realizations}
        self.riskinputs = self.build_riskinputs('gmf', hazard_by_rlz, eps)
        self.param['number_of_ground_motion_fields'] = E
        self.param['insured_losses'] = self.oqparam.insured_losses
        self.param['asset_loss_table'] = self.oqparam.asset_loss_table

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        loss_dt = self.oqparam.loss_dt()
        I = self.oqparam.insured_losses + 1
        with self.monitor('saving outputs', autoflush=True):
            A = len(self.assetcol)

            # agg losses
            res = result['agg']
            E, R, LI = res.shape
            L = LI // I
            mean, std = scientific.mean_std(res)  # shape (R, LI)
            agglosses = numpy.zeros((R, L * I), stat_dt)
            agglosses['mean'] = F32(mean)
            agglosses['stddev'] = F32(std)

            # losses by taxonomy
            taxid = {t: i for i, t in enumerate(
                sorted(self.assetcol.taxonomies))}
            T = len(taxid)
            dset = self.datastore.create_dset(
                'losses_by_taxon-rlzs', F32, (T, R, LI))
            for tax, array in result['losses_by_taxon'].items():
                dset[taxid[tax]] = array

            # losses by asset
            losses_by_asset = numpy.zeros((A, R, L * I), stat_dt)
            for (l, r, aid, stat) in result['avg']:
                for i in range(I):
                    losses_by_asset[aid, r, l + L * i] = stat[i]
            self.datastore['losses_by_asset'] = losses_by_asset
            self.datastore['agglosses-rlzs'] = agglosses

            # losses by event
            self.datastore['losses_by_event'] = res  # shape (E, R, LI)

            if self.oqparam.asset_loss_table:
                array = numpy.zeros((A, E, R), loss_dt)
                for (l, r), losses_by_aid in result['all_losses'].items():
                    for aid in losses_by_aid:
                        lba = losses_by_aid[aid]  # (E, I)
                        for i in range(I):
                            lt = loss_dt.names[l + L * i]
                            array[lt][aid, :, r] = lba[:, i]
                self.datastore['all_losses-rlzs'] = array
