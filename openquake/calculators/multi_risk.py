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
from openquake.commonlib import source
from openquake.calculators import base

U16 = numpy.uint16
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64


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
        R = len(self.oqparam.multi_risk) + 1
        #self.datastore['csm_info'] = source.CompositionInfo.fake(self.R)
        if 'ASH' not in self.oqparam.multi_risk:
            self.datastore['events'] = numpy.zeros(1, rupture.events_dt)
            return

        E = self.oqparam.number_of_ground_motion_fields
        self.param['number_of_ground_motion_fields'] = E
        self.param['consequence_models'] = riskmodels.get_risk_models(
            self.oqparam, 'consequence')
        self.param['tags'] = list(self.assetcol.tagcol)
        self.riskmodel.taxonomy = self.assetcol.tagcol.taxonomy

    def execute(self):
        dstates = self.riskmodel.damage_states
        ltypes = self.riskmodel.loss_types
        R = len(self.oqparam.multi_risk) + 1
        L = len(ltypes)
        D = len(dstates)
        A = len(self.assetcol)
        ampl = self.oqparam.humidity_amplification_factor
        dmg = numpy.zeros((A, R, L, 1, D), F32)
        if 'ASH' in self.oqparam.multi_risk:
            gmf = self.datastore['multi_risk']['ASH']
            dmg[:, 0] = self.riskmodel.get_damage(
                self.assetcol.assets_by_site(), gmf)
            dmg[:, 1] = self.riskmodel.get_damage(
                self.assetcol.assets_by_site(), gmf * ampl)
        hazard = self.datastore['multi_risk']
        volcanic = [risk for risk in self.oqparam.multi_risk if risk != 'ASH']
        for aid, rec in enumerate(self.assetcol.array):
            haz = hazard[rec['site_id']]
            for h, hfield in enumerate(volcanic):
                dmg[aid, h + 2, 0, 0, -1] = haz[hfield]

        self.datastore['dmg_by_asset'] = dmg

        # consequence distributions
        # self.datastore['losses_by_asset'] = c_asset

    def post_execute(self, result):
        pass


def dmg_by_asset_csv(ekey, dstore):
    damage_dt = build_damage_dt(dstore, mean_std=False)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    data = dstore[ekey[0]]
    assets = get_assets(dstore)
    for rlz in rlzs:
        dmg_by_asset = build_damage_array(data[:, rlz.ordinal], damage_dt)
        compose_arrays(assets, dmg_by_asset)
