# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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

import itertools
import logging
import numpy

from openquake.risklib import scientific, riskmodels
from openquake.calculators import base

U16 = numpy.uint16
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64


def dist_by_asset(data, multi_stat_dt, number):
    """
    :param data: array of shape (N, R, L, 2, ...)
    :param multi_stat_dt: numpy dtype for statistical outputs
    :param number: expected number of units per asset
    :returns: array of shape (N, R) with records of type multi_stat_dt
    """
    N, R, L = data.shape[:3]
    out = numpy.zeros((N, R), multi_stat_dt)
    for l, lt in enumerate(multi_stat_dt.names):
        out_lt = out[lt]
        for n, r in itertools.product(range(N), range(R)):
            mean, stddev = data[n, r, l]
            out_lt[n, r] = (mean, stddev)
            # sanity check on the sum over all damage states
            if abs(mean.sum() / number[n] - 1) > 1E-3:
                logging.warn(
                    'Asset #%d, rlz=%d, expected %s, got %s for %s damage',
                    n, r, number[n], mean.sum(), lt)
    return out


def scenario_damage(riskinput, riskmodel, param, monitor):
    """
    Core function for a damage computation.

    :param riskinput:
        a :class:`openquake.risklib.riskinput.RiskInput` object
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
    c_models = param['consequence_models']
    L = len(riskmodel.loss_types)
    R = riskinput.hazard_getter.num_rlzs
    D = len(riskmodel.damage_states)
    E = param['number_of_ground_motion_fields']
    result = dict(d_asset=[], d_event=numpy.zeros((E, R, L, D), F64),
                  c_asset=[], c_event=numpy.zeros((E, R, L), F64))
    for outputs in riskmodel.gen_outputs(riskinput, monitor):
        r = outputs.rlzi
        for l, damages in enumerate(outputs):
            loss_type = riskmodel.loss_types[l]
            c_model = c_models.get(loss_type)
            for a, fraction in enumerate(damages):
                asset = outputs.assets[a]
                taxo = riskmodel.taxonomy[asset.taxonomy]
                damages = fraction * asset.number
                result['d_event'][:, r, l] += damages  # shape (E, D)
                if c_model:  # compute consequences
                    means = [par[0] for par in c_model[taxo].params]
                    # NB: we add a 0 in front for nodamage state
                    c_ratio = numpy.dot(fraction, [0] + means)
                    consequences = c_ratio * asset.value(loss_type)
                    result['c_asset'].append(
                        (l, r, asset.ordinal,
                         scientific.mean_std(consequences)))
                    result['c_event'][:, r, l] += consequences
                    # TODO: consequences for the occupants
                result['d_asset'].append(
                    (l, r, asset.ordinal, scientific.mean_std(damages)))
    result['gmdata'] = riskinput.gmdata
    return result


@base.calculators.add('scenario_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    pre_calculator = 'scenario'
    core_task = scenario_damage
    is_stochastic = True

    def pre_execute(self):
        if 'gmfs' in self.oqparam.inputs:
            self.pre_calculator = None
        base.RiskCalculator.pre_execute(self)
        E = self.oqparam.number_of_ground_motion_fields
        self.param['number_of_ground_motion_fields'] = E
        self.param['consequence_models'] = riskmodels.get_risk_models(
            self.oqparam, 'consequence')
        self.riskinputs = self.build_riskinputs('gmf', num_events=E)
        self.param['tags'] = list(self.assetcol.tagcol)

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        dstates = self.riskmodel.damage_states
        ltypes = self.riskmodel.loss_types
        L = len(ltypes)
        R = len(self.rlzs_assoc.realizations)
        D = len(dstates)
        N = len(self.assetcol)
        E = self.oqparam.number_of_ground_motion_fields

        # damage distributions
        dt_list = []
        for ltype in ltypes:
            dt_list.append((ltype, numpy.dtype([('mean', (F32, D)),
                                                ('stddev', (F32, D))])))
        multi_stat_dt = numpy.dtype(dt_list)
        d_asset = numpy.zeros((N, R, L, 2, D), F32)
        for (l, r, a, stat) in result['d_asset']:
            d_asset[a, r, l] = stat
        self.datastore['dmg_by_asset'] = dist_by_asset(
            d_asset, multi_stat_dt, self.assetcol.array['number'])
        dmg_dt = [(ds, F32) for ds in self.riskmodel.damage_states]
        d_event = numpy.zeros((E, R, L), dmg_dt)
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
            multi_stat_dt = self.oqparam.loss_dt(stat_dt)
            self.datastore['losses_by_asset'] = c_asset
            self.datastore['losses_by_event'] = numpy.fromiter(
                ((eid, rlzi, F32(result['c_event'][eid, rlzi]))
                 for rlzi in range(R) for eid in range(E)), dtlist)

        # save gmdata
        self.gmdata = result['gmdata']
        for arr in self.gmdata.values():
            arr[-2] = self.oqparam.number_of_ground_motion_fields  # events
        base.save_gmdata(self, R)
