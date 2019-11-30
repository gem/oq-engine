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

import logging
import numpy
from openquake.baselib.general import AccumDict
from openquake.risklib import scientific
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


def scenario_damage(riskinputs, crmodel, param, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param crmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :param param:
        dictionary of extra parameters
    :returns:
        a dictionary {'d_asset': [(l, r, a, mean-stddev), ...],
                      'd_event': damage array of shape R, L, E, D,
                      + optional consequences}

    `d_asset` and `d_tag` are related to the damage distributions.
    """
    L = len(crmodel.loss_types)
    D = len(crmodel.damage_states)
    F = param['number_of_ground_motion_fields']
    R = riskinputs[0].hazard_getter.num_rlzs
    consequences = crmodel.get_consequences()
    collapse_threshold = param['collapse_threshold']
    acc = AccumDict(accum=numpy.zeros((L, D), F64))  # must be 64 bit
    # otherwise test 4b will randomly break with last digit changes
    # in dmg_by_event
    result = dict(d_asset=[], d_event=acc, nonzero=0)
    if F:  # this is defined in scenario, not in event_based
        for name in consequences:
            result[name + '_by_event'] = numpy.zeros((F, R, L), F64)
    for name in consequences:
        result[name + '_by_asset'] = []
    mon = monitor('getting hazard', measuremem=False)
    for ri in riskinputs:
        with mon:
            ri.hazard_getter.init()
        for out in ri.gen_outputs(crmodel, monitor):
            r = out.rlzi
            for l, loss_type in enumerate(crmodel.loss_types):
                for asset, fractions in zip(ri.assets, out[loss_type]):
                    dmg = fractions * asset['number']  # shape (F, D)
                    result['nonzero'] += (dmg[:, 1:] > 1).sum()
                    for eid, dmgdist in zip(out.eids, dmg):
                        if dmgdist[-1] >= collapse_threshold:
                            acc[eid][l] += dmgdist
                    result['d_asset'].append(
                        (l, r, asset['ordinal'], scientific.mean_std(dmg)))
                    csq = crmodel.compute_csq(asset, fractions, loss_type)
                    for name, value in csq.items():
                        result[name + '_by_asset'].append(
                            (l, r, asset['ordinal'],
                             scientific.mean_std(value)))
                        if F:  # in scenario
                            result[name + '_by_event'][:, r, l] += value
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
        self.F = getattr(self.oqparam, 'number_of_ground_motion_fields', None)
        if not self.F and self.oqparam.hazard_calculation_id:
            oqp = self.datastore.parent['oqparam']
            try:
                self.F = oqp.number_of_ground_motion_fields
            except AttributeError:
                pass
        self.param['number_of_ground_motion_fields'] = self.F
        self.param['collapse_threshold'] = self.oqparam.collapse_threshold
        self.riskinputs = self.build_riskinputs('gmf')

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        nonzero = result.pop('nonzero', 0)
        if not result:
            self.collapsed()
            return
        dstates = self.crmodel.damage_states
        ltypes = self.crmodel.loss_types
        L = len(ltypes)
        R = len(self.rlzs_assoc.realizations)
        D = len(dstates)
        A = len(self.assetcol)
        total = A * self.E * L * (D - 1)
        logging.info(
            f'There are {nonzero:_d}/{total:_d} nonzero damage fractions')

        # damage by asset
        dt_list = []
        mean_std_dt = numpy.dtype([('mean', (F32, D)), ('stddev', (F32, D))])
        for ltype in ltypes:
            dt_list.append((ltype, mean_std_dt))
        d_asset = numpy.zeros((A, R, L, 2, D), F32)
        for (l, r, a, stat) in result['d_asset']:
            d_asset[a, r, l] = stat
        self.datastore['dmg_by_asset'] = d_asset

        # damage by event
        eid_dmg_dt = self.crmodel.eid_dmg_dt()
        d_event = numpy.array(sorted(result['d_event'].items()), eid_dmg_dt)
        self.datastore['dmg_by_event'] = d_event

        # consequence distributions
        del result['d_asset']
        if 'd_event' in result:
            del result['d_event']
        dtlist = [('event_id', U32), ('rlz_id', U16), ('loss', (F32, (L,)))]
        stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])
        for name, csq in result.items():
            if name.endswith('_by_asset'):
                c_asset = numpy.zeros((A, R, L), stat_dt)
                for (l, r, a, stat) in result[name]:
                    c_asset[a, r, l] = stat
                self.datastore[name] = c_asset
            elif self.F and name.endswith('_by_event'):
                self.datastore[name] = numpy.fromiter(
                    ((eid + rlzi * self.F, rlzi, F32(result[name][eid, rlzi]))
                     for rlzi in range(R) for eid in range(self.F)), dtlist)


@base.calculators.add('event_based_damage')
class EventBasedDamageCalculator(ScenarioDamageCalculator):
    """
    Event Based Damage calculator, able to compute dmg_by_asset
    """
    core_task = scenario_damage
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk']
