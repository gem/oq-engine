#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014-2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import itertools
import numpy

from openquake.commonlib import parallel
from openquake.risklib import scientific
from openquake.baselib.general import AccumDict
from openquake.calculators import base, calc

F64 = numpy.float64


def dmg_by_asset(avg_damage, multi_stat_dt):
    """
    :param avg_damage: array of shape (N, L, R, 2, D)
    :param multi_stat_dt: numpy dtype for statistical outputs
    :returns: array of shape (N, R) with records of type multi_stat_dt
    """
    N, L, R = avg_damage.shape[:3]
    out = numpy.zeros((N, R), multi_stat_dt)
    for l, lt in enumerate(multi_stat_dt.names):
        data = out[lt]
        for n, r in itertools.product(range(N), range(R)):
            data[n, r] = avg_damage[n, l, r]
    return out


def dmg_by_taxon(agg_damage, multi_stat_dt):
    """
    :param agg_damage: array of shape (T, L, R, E, D)
    :param multi_stat_dt: numpy dtype for statistical outputs
    :returns: array of shape (T, R) with records of type multi_stat_dt
    """
    T, L, R, E, D = agg_damage.shape
    out = numpy.zeros((T, R), multi_stat_dt)
    for l, lt in enumerate(multi_stat_dt.names):
        data = out[lt]
        for t, r in itertools.product(range(T), range(R)):
            data[t, r] = scientific.mean_std(agg_damage[t, l, r])
    return out


def dmg_total(agg_damage, multi_stat_dt):
    """
    :param agg_damage: array of shape (T, L, R, E, D)
    :param multi_stat_dt: numpy dtype for statistical outputs
    :returns: array of shape (R,) with records of type multi_stat_dt
    """
    T, L, R, E, D = agg_damage.shape
    total = agg_damage.sum(axis=0)
    out = numpy.zeros(R, multi_stat_dt)
    for l, lt in enumerate(multi_stat_dt.names):
        data = out[lt]
        for r in range(R):
            data[r] = scientific.mean_std(total[l, r])
    return out


@parallel.litetask
def scenario_damage(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.RiskModel` instance
    :param rlzs_assoc:
        a class:`openquake.commonlib.source.RlzsAssoc` instance
    :param monitor:
        :class:`openquake.baselib.performance.PerformanceMonitor` instance
    :returns:
        a dictionary {('asset', asset): <mean stddev>,
                      ('taxonomy', asset.taxonomy): <damage array>}
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    L = len(riskmodel.loss_types)
    R = len(rlzs_assoc.realizations)
    # D = len(riskmodel.damage_states)
    taxo2idx = {taxo: i for i, taxo in enumerate(monitor.taxonomies)}
    lt2idx = {lt: i for i, lt in enumerate(riskmodel.loss_types)}
    result = calc.build_dict((L, R), AccumDict)
    for out_by_rlz in riskmodel.gen_outputs(
            riskinputs, rlzs_assoc, monitor):
        for out in out_by_rlz:
            lti = lt2idx[out.loss_type]
            for asset, fraction in zip(out.assets, out.damages):
                damages = fraction * asset.number
                result[lti, out.hid] += {
                    ('asset', asset.idx): scientific.mean_std(damages)}
                result[lti, out.hid] += {
                    ('taxon', taxo2idx[asset.taxonomy]): damages}
    return result


@base.calculators.add('scenario_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    pre_calculator = 'scenario'
    core_func = scenario_damage
    is_stochastic = True

    def pre_execute(self):
        if 'gmfs' in self.oqparam.inputs:
            self.pre_calculator = None
        base.RiskCalculator.pre_execute(self)
        self.riskinputs = self.build_riskinputs(self.gmfs)
        self.monitor.taxonomies = sorted(self.taxonomies)

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
        E = self.oqparam.number_of_ground_motion_fields
        N = len(self.assetcol)
        T = len(self.monitor.taxonomies)

        dt_list = []
        for ltype in ltypes:
            dt_list.append((ltype, numpy.dtype([('mean', (F64, D)),
                                                ('stddev', (F64, D))])))
        multi_stat_dt = numpy.dtype(dt_list)

        arr = dict(asset=numpy.zeros((N, L, R, 2, D), F64),
                   taxon=numpy.zeros((T, L, R, E, D), F64))
        for (l, r), res in result.items():
            for keytype, key in res:
                arr[keytype][key, l, r] = res[keytype, key]
        self.datastore['dmg_by_asset'] = dmg_by_asset(
            arr['asset'], multi_stat_dt)
        self.datastore['dmg_by_taxon'] = dmg_by_taxon(
            arr['taxon'], multi_stat_dt)
        self.datastore['dmg_total'] = dmg_total(
            arr['taxon'], multi_stat_dt)
