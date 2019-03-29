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


def build_asset_risk(assetcol, dmg, loss_types, damage_states, perils):
    # dmg has shape (A, R, L, 1, D)
    dtlist = []
    field2tup = {}
    for l, loss_type in enumerate(loss_types):
        for d, ds in enumerate(damage_states):
            for p, peril in enumerate(perils):
                field = ds + '-' + loss_type + '-' + peril
                field2tup[field] = (p, l, 0, d)
                dtlist.append((field, F32))
    dt = assetcol.array.dtype.descr + dtlist
    arr = numpy.zeros(len(assetcol), dt)
    for field in assetcol.array.dtype.names:
        arr[field] = assetcol.array[field]
    for field, _ in dtlist:
        arr[field] = dmg[(slice(None),) + field2tup[field]]
    return arr


@base.calculators.add('multi_risk')
class MultiRiskCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = None  # no parallel
    is_stochastic = True

    def pre_execute(self):
        super().pre_execute()
        assert self.oqparam.multi_peril
        if 'ASH' not in self.oqparam.multi_peril:
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
        P = len(self.oqparam.multi_peril) + 1
        L = len(ltypes)
        D = len(dstates)
        A = len(self.assetcol)
        ampl = self.oqparam.humidity_amplification_factor
        dmg = numpy.zeros((A, P, L, 1, D), F32)
        perils = []
        if 'ASH' in self.oqparam.multi_peril:
            gmf = self.datastore['multi_peril']['ASH']
            dmg[:, 0] = self.riskmodel.get_damage(
                self.assetcol.assets_by_site(), gmf)
            perils.append('ASH_DRY')
            dmg[:, 1] = self.riskmodel.get_damage(
                self.assetcol.assets_by_site(), gmf * ampl)
            perils.append('ASH_WET')
        hazard = self.datastore['multi_peril']
        no_fragility_perils = []
        for peril in self.oqparam.multi_peril:
            if peril != 'ASH':
                no_fragility_perils.append(peril)
        for aid, rec in enumerate(self.assetcol.array):
            haz = hazard[rec['site_id']]
            for h, hfield in enumerate(no_fragility_perils):
                dmg[aid, h + 2, 0, 0, -1] = haz[hfield]

        self.datastore['asset_risk'] = build_asset_risk(
            self.assetcol, dmg, ltypes, dstates, perils + no_fragility_perils)

        # consequence distributions
        # self.datastore['losses_by_asset'] = c_asset

    def post_execute(self, result):
        pass
