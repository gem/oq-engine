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

from openquake.commonlib import calc
from openquake.calculators import base, event_based_risk as ebr

U16 = numpy.uint16
F32 = numpy.float32
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
        logging.info('Building the epsilons')
        oq = self.oqparam
        A = len(self.assetcol)
        E = oq.number_of_ground_motion_fields
        if oq.ignore_covs:
            eps = numpy.zeros((A, E), numpy.float32)
        else:
            eps = self.make_eps(E)
        self.datastore['etags'], gmfs = calc.get_gmfs(
            self.datastore, self.precalc)
        hazard_by_rlz = {rlz: gmfs[rlz.ordinal]
                         for rlz in self.rlzs_assoc.realizations}
        self.riskinputs = self.build_riskinputs('gmf', hazard_by_rlz, eps)
        self.param['assetcol'] = self.assetcol
        self.param['insured_losses'] = oq.insured_losses
        self.param['avg_losses'] = oq.avg_losses
        self.param['asset_loss_table'] = oq.asset_loss_table or oq.loss_ratios
        self.taskno = 0
        self.start = 0
        self.R = len(hazard_by_rlz)
        self.L = len(self.riskmodel.lti)
        self.T = len(self.assetcol.taxonomies)
        self.A = len(self.assetcol)
        self.I = I = self.oqparam.insured_losses + 1
        self.datastore.create_dset('losses_by_taxon-rlzs', F32,
                                   (self.T, self.R, self.L * I))
        avg_losses = self.oqparam.avg_losses
        if avg_losses:
            self.dset = self.datastore.create_dset(
                'avg_losses-rlzs', F32, (self.A, self.R, self.L * I))

    def post_execute(self, result):
        pass

    def combine(self, dummy, res):
        """
        :param dummy: unused parameter
        :param res: a result dictionary
        """
        ebr.EbriskCalculator.__dict__['save_losses'](self, res, self.taskno)
