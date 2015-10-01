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


def dmg_by_taxon(agg_damage, stat_dt):
    """
    :param agg_damage: array of shape (T, L, R, E, D)
    :param stat_dt: numpy dtype for statistical outputs
    :returns: array of shape (T, L, R) with records of type stat_dt
    """
    T, L, R, E, D = agg_damage.shape
    out = numpy.zeros((T, L, R), stat_dt)
    for t, l, r in itertools.product(range(T), range(L), range(R)):
        out[t, l, r] = scientific.mean_std(agg_damage[t, l, r])
    return out


def dmg_total(agg_damage, stat_dt):
    """
    :param agg_damage: array of shape (T, L, R, E, D)
    :param stat_dt: numpy dtype for statistical outputs
    :returns: array of shape (L, R) with records of type stat_dt
    """
    T, L, R, E, D = agg_damage.shape
    total = agg_damage.sum(axis=0)
    out = numpy.zeros((L, R), stat_dt)
    for l, r in itertools.product(range(L), range(R)):
        out[l, r] = scientific.mean_std(total[l, r])
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
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
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
        L = len(self.riskmodel.loss_types)
        R = len(self.rlzs_assoc.realizations)
        D = len(dstates)
        E = self.oqparam.number_of_ground_motion_fields
        N = len(self.assetcol)
        T = len(self.monitor.taxonomies)

        dt = numpy.dtype([(ds, numpy.float64) for ds in dstates])
        stat_dt = numpy.dtype([('mean', dt), ('stddev', dt)])

        arr = dict(asset=numpy.zeros((N, L, R), stat_dt),
                   taxon=numpy.zeros((T, L, R, E, D), numpy.float64))
        for (l, r), res in result.items():
            for keytype, key in res:
                arr[keytype][key, l, r] = res[keytype, key]
        self.datastore['dmg_by_asset'] = arr['asset']
        self.datastore['dmg_by_taxon'] = dmg_by_taxon(arr['taxon'], stat_dt)
        self.datastore['dmg_total'] = dmg_total(arr['taxon'], stat_dt)
