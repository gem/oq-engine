# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

from openquake.commonlib import calc
from openquake.risklib import scientific
from openquake.calculators import base


F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency


def scenario_risk(riskinput, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
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
    R = len(rlzs_assoc.realizations)
    result = dict(agg=numpy.zeros((E, L, R, 2), F64), avg=[])
    for out in riskmodel.gen_outputs(riskinput, rlzs_assoc, monitor):
        l, r = out.lr
        stats = numpy.zeros((len(out.assets), 4), F32)
        # this is ugly but using a composite array (i.e.
        # stats['mean'], stats['stddev'], ...) may return
        # bogus numbers! even with the SAME version of numpy,
        # hdf5 and h5py!! the numbers are around 1E-300 and
        # different on different systems; we found issues
        # with Ubuntu 12.04 and Red Hat 7 (MS and DV)
        stats[:, 0] = out.loss_matrix.mean(axis=1)
        stats[:, 1] = out.loss_matrix.std(ddof=1, axis=1)
        stats[:, 2] = out.insured_loss_matrix.mean(axis=1)
        stats[:, 3] = out.insured_loss_matrix.std(ddof=1, axis=1)
        for asset, stat in zip(out.assets, stats):
            result['avg'].append((l, r, asset.ordinal, stat))
        result['agg'][:, l, r, 0] += out.aggregate_losses
        result['agg'][:, l, r, 1] += out.insured_losses
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
        epsilon_matrix = self.make_eps(
            self.oqparam.number_of_ground_motion_fields)
        self.datastore['etags'], gmfs = calc.get_gmfs(self.datastore)
        hazard_by_rlz = {rlz: gmfs[rlz.ordinal]
                         for rlz in self.rlzs_assoc.realizations}
        self.riskinputs = self.build_riskinputs(hazard_by_rlz, epsilon_matrix)

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        ltypes = self.riskmodel.loss_types
        dt_list = [('mean', F32), ('stddev', F32)]
        if self.oqparam.insured_losses:
            dt_list.extend([('mean_ins', F32), ('stddev_ins', F32)])
        stat_dt = numpy.dtype(dt_list)
        multi_stat_dt = numpy.dtype([(lt, stat_dt) for lt in ltypes])
        with self.monitor('saving outputs', autoflush=True):
            R = len(self.rlzs_assoc.realizations)
            N = len(self.assetcol)

            # agg losses
            agglosses = numpy.zeros(R, multi_stat_dt)
            mean, std = scientific.mean_std(result['agg'])
            for l, lt in enumerate(ltypes):
                agg = agglosses[lt]
                agg['mean'] = numpy.float32(mean[l, :, 0])
                agg['stddev'] = numpy.float32(std[l, :, 0])
                if self.oqparam.insured_losses:
                    agg['mean_ins'] = numpy.float32(mean[l, :, 1])
                    agg['stddev_ins'] = numpy.float32(std[l, :, 1])

            # average losses
            avglosses = numpy.zeros((N, R), multi_stat_dt)
            for (l, r, aid, stat) in result['avg']:
                avglosses[ltypes[l]][aid, r] = stat
            self.datastore['losses_by_asset'] = avglosses
            self.datastore['agglosses-rlzs'] = agglosses
