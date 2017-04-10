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

import numpy

from openquake.calculators import base, classical_risk

F32 = numpy.float32

bcr_dt = numpy.dtype([('annual_loss_orig', F32), ('annual_loss_retro', F32),
                      ('bcr', F32)])


def classical_bcr(riskinput, riskmodel, param, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    result = {}  # (N, R) -> data
    for outputs in riskmodel.gen_outputs(riskinput, monitor):
        assets = outputs.assets
        for l, out in enumerate(outputs):
            loss_type = riskmodel.loss_types[l]
            for asset, (eal_orig, eal_retro, bcr) in zip(assets, out):
                aval = asset.value(loss_type)
                result[asset.ordinal, loss_type, outputs.r] = numpy.array([
                    (eal_orig * aval, eal_retro * aval, bcr)], bcr_dt)
    return result


@base.calculators.add('classical_bcr')
class ClassicalBCRCalculator(classical_risk.ClassicalRiskCalculator):
    """
    Classical BCR Risk calculator
    """
    core_task = classical_bcr

    def post_execute(self, result):
        bcr_data = numpy.zeros((self.N, self.R), self.oqparam.loss_dt(bcr_dt))
        for (aid, lt, r), data in result.items():
            bcr_data[lt][aid, r] = data
        self.datastore['bcr-rlzs'] = bcr_data
