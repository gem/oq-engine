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
from openquake.calculators import base, event_based_risk as ebr


F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def gmf_ebrisk(riskinput, riskmodel, taxid, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    I = monitor.insured_losses + 1
    eids = riskinput.eids
    E = len(eids)
    L = len(riskmodel.lti)
    T = len(taxid)
    R = sum(len(rlzs)
            for gsim, rlzs in riskinput.hazard_getter.rlzs_by_gsim.items())
    idx = dict(zip(eids, range(E)))
    agg = AccumDict(accum=numpy.zeros((E, L, I), F32))  # r -> array
    ass = AccumDict(accum=[])
    result = dict(agglosses=AccumDict(), asslosses=AccumDict(),
                  losses_by_taxon=numpy.zeros((T, R, L * I), F32))
    if monitor.avg_losses:
        result['avglosses'] = AccumDict(accum=numpy.zeros((A, I), F32))

    outputs = riskmodel.gen_outputs(riskinput, monitor)
    ebr._aggregate(outputs, riskmodel, taxid, agg, ass, idx, result, monitor)
    for r in sorted(agg):
        records = [(eids[i], loss) for i, loss in enumerate(agg[r])
                   if loss.sum() > 0]
        if records:
            result['agglosses'][r] = numpy.array(records, monitor.elt_dt)
    for r in ass:
        if ass[r]:
            result['asslosses'][r] = numpy.concatenate(ass[r])

    # store info about the GMFs
    result['gmdata'] = riskinput.gmdata
    return result


@base.calculators.add('gmf_ebrisk')
class GmfEbRiskCalculator(ebr.RiskCalculator):
    """
    Run an event based risk calculation starting from precomputed GMFs
    """
    core_task = gmf_ebrisk
    pre_calculator = None
    is_stochastic = True

    def pre_execute(self):
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
        self.riskinputs = self.build_riskinputs(hazard_by_rlz, eps)

    def post_execute(self, result):
        pass
