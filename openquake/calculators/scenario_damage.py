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

import itertools
import numpy

from openquake.baselib.python3compat import encode
from openquake.commonlib import riskmodels
from openquake.risklib import scientific
from openquake.calculators import base, event_based

F32 = numpy.float32
F64 = numpy.float64


def dist_by_asset(data, multi_stat_dt):
    """
    :param data: array of shape (N, R, L, 2, ...)
    :param multi_stat_dt: numpy dtype for statistical outputs
    :returns: array of shape (N, R) with records of type multi_stat_dt
    """
    N, R, L = data.shape[:3]
    out = numpy.zeros((N, R), multi_stat_dt)
    for l, lt in enumerate(multi_stat_dt.names):
        out_lt = out[lt]
        for n, r in itertools.product(range(N), range(R)):
            out_lt[n, r] = data[n, r, l]
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
                      'd_tag': damage array of shape T, R, L, E, D,
                      'c_asset': [(l, r, a, mean-stddev), ...],
                      'c_tag': damage array of shape T, R, L, E}

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
    T = len(param['tags'])
    result = dict(d_asset=[], d_tag=numpy.zeros((T, R, L, E, D), F64),
                  c_asset=[], c_tag=numpy.zeros((T, R, L, E), F64))
    for outputs in riskmodel.gen_outputs(riskinput, monitor):
        r = outputs.rlzi
        for l, damages in enumerate(outputs):
            loss_type = riskmodel.loss_types[l]
            c_model = c_models.get(loss_type)
            for a, fraction in enumerate(damages):
                asset = outputs.assets[a]
                damages = fraction * asset.number
                t = asset.tagmask
                result['d_tag'][t, r, l] += damages  # shape (E, D)
                if c_model:  # compute consequences
                    means = [par[0] for par in c_model[asset.taxonomy].params]
                    # NB: we add a 0 in front for nodamage state
                    c_ratio = numpy.dot(fraction, [0] + means)
                    consequences = c_ratio * asset.value(loss_type)
                    result['c_asset'].append(
                        (l, r, asset.ordinal,
                         scientific.mean_std(consequences)))
                    result['c_tag'][t, r, l] += consequences
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
        base.get_gmfs(self)
        self.param['number_of_ground_motion_fields'] = (
            self.oqparam.number_of_ground_motion_fields)
        self.param['consequence_models'] = riskmodels.get_risk_models(
            self.oqparam, 'consequence')
        self.riskinputs = self.build_riskinputs('gmf')
        self.param['tags'] = self.assetcol.tags()

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
            d_asset, multi_stat_dt)

        # consequence distributions
        if result['c_asset']:
            stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])
            c_asset = numpy.zeros((N, R, L), stat_dt)
            for (l, r, a, stat) in result['c_asset']:
                c_asset[a, r, l] = stat
            multi_stat_dt = self.oqparam.loss_dt(stat_dt)
            self.datastore['losses_by_asset'] = c_asset

        # save gmdata
        self.gmdata = result['gmdata']
        for arr in self.gmdata.values():
            arr[-2] = self.oqparam.number_of_ground_motion_fields  # events
        event_based.save_gmdata(self, R)
