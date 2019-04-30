# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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

from openquake.baselib.general import AccumDict
from openquake.hazardlib import stats
from openquake.calculators import base, classical_risk

F32 = numpy.float32

bcr_dt = numpy.dtype([('annual_loss_orig', F32), ('annual_loss_retro', F32),
                      ('bcr', F32)])


def classical_bcr(riskinputs, riskmodel, param, monitor):
    """
    Compute and return the average losses for each asset.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    """
    R = riskinputs[0].hazard_getter.num_rlzs
    result = AccumDict(accum=numpy.zeros((R, 3), F32))
    for ri in riskinputs:
        for out in riskmodel.gen_outputs(ri, monitor):
            for asset, (eal_orig, eal_retro, bcr) in zip(
                    ri.assets, out['structural']):
                aval = asset['value-structural']
                result[asset['ordinal']][out.rlzi] = numpy.array([
                    eal_orig * aval, eal_retro * aval, bcr])
    return {'bcr_data': result}


@base.calculators.add('classical_bcr')
class ClassicalBCRCalculator(classical_risk.ClassicalRiskCalculator):
    """
    Classical BCR Risk calculator
    """
    core_task = classical_bcr
    accept_precalc = ['classical']

    def pre_execute(self):
        super().pre_execute()
        for asset_ref, retrofitted in zip(self.assetcol.asset_refs,
                                          self.assetcol.array['retrofitted']):
            if numpy.isnan(retrofitted):
                raise ValueError('The asset %s has no retrofitted value!'
                                 % asset_ref.decode('utf8'))

    def post_execute(self, result):
        # NB: defined only for loss_type = 'structural'
        bcr_data = numpy.zeros((self.A, self.R), bcr_dt)
        for aid, data in result['bcr_data'].items():
            bcr_data[aid]['annual_loss_orig'] = data[:, 0]
            bcr_data[aid]['annual_loss_retro'] = data[:, 1]
            bcr_data[aid]['bcr'] = data[:, 2]
        stats.set_rlzs_stats(self.datastore, 'bcr', bcr_data)
