#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014-2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

import numpy

from openquake.baselib import general
from openquake.commonlib import parallel, datastore
from openquake.risklib import scientific
from openquake.calculators import base, calc


F64 = numpy.float64

stat_dt = numpy.dtype([('mean', F64), ('stddev', F64),
                       ('mean_ins', F64), ('stddev_ins', F64)])


@parallel.litetask
def scenario_risk(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a scenario computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    :returns:
        a dictionary (key_type, loss_type) -> losses where the `key_type` can
        be "agg" (for the aggregate losses) or "ins" (for the insured losses).
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    L = len(riskmodel.loss_types)
    R = len(rlzs_assoc.realizations)
    result = calc.build_dict((L,), general.AccumDict)
    lt2idx = {lt: i for i, lt in enumerate(riskmodel.loss_types)}
    for out_by_rlz in riskmodel.gen_outputs(
            riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            lti = lt2idx[out.loss_type],
            r = out.hid  # realization index
            stats = numpy.zeros((len(out.assets), R, 4), F64)
            # this is ugly but using a composite array (i.e.
            # stats['mean'], stats['stddev'], ...) may return
            # bogus numbers! even with the SAME version of numpy,
            # hdf5 and h5py!! the numbers are around 1E-300 and
            # different on different systems; we found issues
            # with Ubuntu 12.04 and Red Hat 7 (MS and DV)
            stats[:, r, 0] = out.loss_matrix.mean(axis=1)
            stats[:, r, 1] = out.loss_matrix.std(ddof=1, axis=1)
            stats[:, r, 2] = out.insured_loss_matrix.mean(axis=1)
            stats[:, r, 3] = out.insured_loss_matrix.std(ddof=1, axis=1)
            avg = result[lti]
            for asset, stat in zip(out.assets, stats):
                avg['avg', r, asset.idx] = stat
            result[lti]['agg', r, 0] = out.aggregate_losses
            result[lti]['agg', r, 1] = out.insured_losses
    return result


@base.calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Run a scenario risk calculation
    """
    core_func = scenario_risk
    epsilon_matrix = datastore.persistent_attribute('epsilon_matrix')
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
        eps_dict = self.make_eps_dict(
            self.oqparam.number_of_ground_motion_fields)
        self.epsilon_matrix = numpy.array(
            [eps_dict[a['asset_ref']] for a in self.assetcol])
        self.riskinputs = self.build_riskinputs(self.gmfs, eps_dict)

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        ltypes = self.riskmodel.loss_types
        multi_stat_dt = numpy.dtype([(lt, stat_dt) for lt in ltypes])
        with self.monitor('saving outputs', autoflush=True):
            R = len(self.rlzs_assoc.realizations)
            N = len(self.assetcol)
            avglosses = numpy.zeros((N, R), multi_stat_dt)
            agglosses = numpy.zeros(R, multi_stat_dt)
            for [l], res in result.items():
                lt = ltypes[l]
                avg = avglosses[lt]
                agg = agglosses[lt]
                for keytype, r, k in res:
                    val = res[keytype, r, k]
                    if keytype == 'agg':
                        mean, std = scientific.mean_std(val)
                        if k == 0:
                            agg[r]['mean'] = mean
                            agg[r]['stddev'] = std
                        else:
                            agg[r]['mean_ins'] = mean
                            agg[r]['stddev_ins'] = std
                    else:  # avg
                        avg[k, r] = val
            self.datastore['avglosses'] = avglosses
            self.datastore['agglosses'] = agglosses
