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
from openquake.risklib import scientific
from openquake.calculators import base

U16 = numpy.uint16
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64


def scenario_damage(riskinputs, riskmodel, param, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :param param:
        dictionary of extra parameters
    :returns:
        a dictionary {'d_asset': [(l, r, a, mean-stddev), ...],
                      'd_event': damage array of shape R, L, E, D,
                      'c_asset': [(l, r, a, mean-stddev), ...],
                      'c_event': damage array of shape R, L, E}

    `d_asset` and `d_tag` are related to the damage distributions
    whereas `c_asset` and `c_tag` are the consequence distributions.
    If there is no consequence model `c_asset` is an empty list and
    `c_tag` is a zero-valued array.
    """
    L = len(riskmodel.loss_types)
    D = len(riskmodel.damage_states)
    E = param['number_of_ground_motion_fields']
    R = riskinputs[0].hazard_getter.num_rlzs
    result = dict(d_asset=[], d_event=numpy.zeros((E, R, L, D), F64),
                  c_asset=[], c_event=numpy.zeros((E, R, L), F64))
    for ri in riskinputs:
        for out in riskmodel.gen_outputs(ri, monitor):
            r = out.rlzi
            for l, loss_type in enumerate(riskmodel.loss_types):
                for asset, fractions in zip(ri.assets, out[loss_type]):
                    dmg = fractions[:, :D] * asset['number']  # shape (E, D)
                    result['d_event'][:, r, l] += dmg
                    result['d_asset'].append(
                        (l, r, asset['ordinal'], scientific.mean_std(dmg)))
                    if riskmodel.consequences:
                        csq = fractions[:, D] * asset['value-' + loss_type]
                        result['c_asset'].append(
                            (l, r, asset['ordinal'], scientific.mean_std(csq)))
                        result['c_event'][:, r, l] += csq
    return result


@base.calculators.add('scenario_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = scenario_damage
    is_stochastic = True
    precalc = 'scenario'
    accept_precalc = ['scenario']

    def pre_execute(self):
        super().pre_execute()
        F = self.oqparam.number_of_ground_motion_fields
        self.param['number_of_ground_motion_fields'] = F
        self.riskinputs = self.build_riskinputs('gmf')
        self.param['tags'] = list(self.assetcol.tagcol)

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        if not result:
            self.collapsed()
            return
        dstates = self.riskmodel.damage_states
        ltypes = self.riskmodel.loss_types
        L = len(ltypes)
        R = len(self.rlzs_assoc.realizations)
        D = len(dstates)
        N = len(self.assetcol)
        F = self.oqparam.number_of_ground_motion_fields

        # damage distributions
        dt_list = []
        mean_std_dt = numpy.dtype([('mean', (F32, D)), ('stddev', (F32, D))])
        for ltype in ltypes:
            dt_list.append((ltype, mean_std_dt))
        d_asset = numpy.zeros((N, R, L, 2, D), F32)
        for (l, r, a, stat) in result['d_asset']:
            d_asset[a, r, l] = stat
        self.datastore['dmg_by_asset'] = d_asset
        dmg_dt = [(ds, F32) for ds in self.riskmodel.damage_states]
        d_event = numpy.zeros((F, R, L), dmg_dt)
        for d, ds in enumerate(self.riskmodel.damage_states):
            d_event[ds] = result['d_event'][:, :, :, d]
        self.datastore['dmg_by_event'] = d_event

        # consequence distributions
        if result['c_asset']:
            dtlist = [('eid', U64), ('rlzi', U16), ('loss', (F32, L))]
            stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])
            c_asset = numpy.zeros((N, R, L), stat_dt)
            for (l, r, a, stat) in result['c_asset']:
                c_asset[a, r, l] = stat
            self.datastore['losses_by_asset'] = c_asset
            self.datastore['losses_by_event'] = numpy.fromiter(
                ((eid, rlzi, F32(result['c_event'][eid, rlzi]))
                 for rlzi in range(R) for eid in range(F)), dtlist)
