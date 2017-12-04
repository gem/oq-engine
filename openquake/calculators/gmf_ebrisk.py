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

from openquake.baselib import general
from openquake.commonlib import readinput
from openquake.calculators import base, event_based_risk as ebr

U16 = numpy.uint16
F32 = numpy.float32
U64 = numpy.uint64
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


@base.calculators.add('gmf_ebrisk')
class GmfEbRiskCalculator(base.RiskCalculator):
    """
    Run an event based risk calculation starting from precomputed GMFs
    """
    core_task = ebr.event_based_risk
    pre_calculator = None
    is_stochastic = True

    def pre_execute(self):
        logging.warn('%s is still experimental', self.__class__.__name__)
        base.RiskCalculator.pre_execute(self)
        oq = self.oqparam
        self.L = len(self.riskmodel.lti)
        self.T = len(self.assetcol.tags())
        self.A = len(self.assetcol)
        self.I = oq.insured_losses + 1
        eids, gmfs = base.get_gmfs(self)  # shape (R, N, E, I)
        self.E = len(eids)
        if oq.ignore_covs:
            eps = numpy.zeros((self.A, self.E), numpy.float32)
        else:
            logging.info('Building the epsilons')
            eps = self.make_eps(self.E)
        self.R = len(gmfs)
        self.riskinputs = self.build_riskinputs('gmf', eps, eids)
        self.param['assetcol'] = self.assetcol
        self.param['insured_losses'] = oq.insured_losses
        self.param['avg_losses'] = oq.avg_losses
        self.param['ses_ratio'] = oq.ses_ratio
        self.param['asset_loss_table'] = oq.asset_loss_table
        self.param['elt_dt'] = numpy.dtype(
            [('eid', U64), ('rlzi', U16), ('loss', (F32, (self.L * self.I,)))])
        self.taskno = 0
        self.start = 0
        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * self.I))

        events = numpy.zeros(oq.number_of_ground_motion_fields,
                             readinput.stored_event_dt)
        events['eid'] = eids
        self.datastore['events'] = events
        self.agglosses = general.AccumDict(
            accum=numpy.zeros(self.L * self.I, F32))
        self.vals = self.assetcol.values()

    def post_execute(self, result):
        """
        Save the event loss table
        """
        alt = numpy.zeros(len(self.agglosses), self.param['elt_dt'])
        i = 0
        for (e, r), loss in self.agglosses.items():
            alt[i] = (e, r, loss)
            i += 1
        self.datastore['agg_loss_table'] = alt

    def combine(self, dummy, res):
        """
        :param dummy: unused parameter
        :param res: a result dictionary
        """
        ebr.EbriskCalculator.__dict__['save_losses'](self, res, 0)
        return 1
