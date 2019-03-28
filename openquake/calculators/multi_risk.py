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
from openquake.hazardlib.source import rupture
from openquake.risklib import riskmodels
from openquake.calculators import base

U16 = numpy.uint16
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64
VOLCANIC_HAZARDS = {'ASH', 'LAVA', 'LAHARS', 'PYRO'}


@base.calculators.add('multi_risk')
class MultiRiskCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = None  # no parallel
    is_stochastic = True

    def pre_execute(self):
        super().pre_execute()
        assert self.oqparam.multi_risk
        if 'ASH' not in self.oqparam.multi_risk:
            self.datastore['events'] = numpy.zeros(1, rupture.events_dt)
            return

        E = self.oqparam.number_of_ground_motion_fields
        self.param['number_of_ground_motion_fields'] = E
        self.param['consequence_models'] = riskmodels.get_risk_models(
            self.oqparam, 'consequence')
        self.param['tags'] = list(self.assetcol.tagcol)

    def execute(self):
        dstates = self.riskmodel.damage_states
        ltypes = self.riskmodel.loss_types
        L = len(ltypes)
        R = len(self.rlzs_assoc.realizations)
        D = len(dstates)
        A = len(self.assetcol)
        ampl = self.oqparam.humidity_amplification_factor
        dmg = numpy.zeros((A, R, L, D), F32)
        if 'ASH' in self.oqparam.multi_risk:
            gmf = self.datastore['multi_risk']['ASH']
            dmg[:, 0] = self.riskmodel.get_damage(
                self.assetcol.assets_by_site(), gmf)
            dmg[:, 1] = self.riskmodel.get_damage(
                self.assetcol.assets_by_site(), gmf * ampl)
        hazard = self.datastore['multi_risk']
        for aid, rec in enumerate(self.assetcol.array):
            haz = hazard[rec['site_id']]
            for h, hfield in enumerate(self.oqparam.multi_risk):
                dmg[aid, h + 2, 0, -1] = haz[hfield]

        self.datastore['dmg_by_asset'] = dmg

        # consequence distributions
        # self.datastore['losses_by_asset'] = c_asset

    def post_execute(self, result):
        pass
