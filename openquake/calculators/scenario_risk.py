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

import functools
import numpy

from openquake.baselib.python3compat import zip, encode
from openquake.baselib.general import AccumDict
from openquake.risklib import scientific, riskinput
from openquake.calculators import base

U16 = numpy.uint16
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def _event_slice(num_gmfs, r):
    return slice(r * num_gmfs, (r + 1) * num_gmfs)


def scenario_risk(riskinputs, riskmodel, param, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a dictionary {
        'agg': array of shape (E, L, R, 2),
        'avg': list of tuples (lt_idx, rlz_idx, asset_ordinal, statistics)
        }
        where E is the number of simulated events, L the number of loss types,
        R the number of realizations  and statistics is an array of shape
        (n, R, 4), with n the number of assets in the current riskinput object
    """
    E = param['E']
    L = len(riskmodel.loss_types)
    result = dict(agg=numpy.zeros((E, L), F32), avg=[],
                  all_losses=AccumDict(accum={}))
    for ri in riskinputs:
        for out in riskmodel.gen_outputs(ri, monitor, param['epspath']):
            r = out.rlzi
            weight = param['weights'][r]
            slc = param['event_slice'](r)
            for l, loss_type in enumerate(riskmodel.loss_types):
                losses = out[loss_type]
                if numpy.product(losses.shape) == 0:  # happens for all NaNs
                    continue
                stats = numpy.zeros(len(ri.assets), stat_dt)  # mean, stddev
                for a, asset in enumerate(ri.assets):
                    stats['mean'][a] = losses[a].mean()
                    stats['stddev'][a] = losses[a].std(ddof=1)
                    result['avg'].append((l, r, asset['ordinal'], stats[a]))
                agglosses = losses.sum(axis=0)  # shape num_gmfs
                result['agg'][slc, l] += agglosses * weight
                if param['asset_loss_table']:
                    aids = ri.assets['ordinal']
                    result['all_losses'][l, r] += AccumDict(zip(aids, losses))
    return result


@base.calculators.add('scenario_risk')
class ScenarioRiskCalculator(base.RiskCalculator):
    """
    Run a scenario risk calculation
    """
    core_task = scenario_risk
    is_stochastic = True
    precalc = 'scenario'
    accept_precalc = ['scenario']

    def pre_execute(self):
        """
        Compute the GMFs, build the epsilons, the riskinputs, and a dictionary
        with the unit of measure, used in the export phase.
        """
        oq = self.oqparam
        super().pre_execute()
        self.assetcol = self.datastore['assetcol']
        self.event_slice = functools.partial(
            _event_slice, oq.number_of_ground_motion_fields)
        E = oq.number_of_ground_motion_fields * self.R
        self.riskinputs = self.build_riskinputs('gmf')
        self.param['epspath'] = riskinput.cache_epsilons(
            self.datastore, oq, self.assetcol, self.riskmodel, E)
        self.param['E'] = E
        # assuming the weights are the same for all IMTs
        try:
            self.param['weights'] = self.datastore['weights'].value
        except KeyError:
            self.param['weights'] = [1 / self.R for _ in range(self.R)]
        self.param['event_slice'] = self.event_slice
        self.param['asset_loss_table'] = self.oqparam.asset_loss_table

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        loss_dt = self.oqparam.loss_dt()
        LI = len(loss_dt.names)
        dtlist = [('eid', U64), ('loss', (F32, LI))]
        R = self.R
        with self.monitor('saving outputs', autoflush=True):
            A = len(self.assetcol)

            # agg losses
            res = result['agg']
            E, L = res.shape
            mean, std = scientific.mean_std(res)  # shape L
            agglosses = numpy.zeros(L, stat_dt)
            agglosses['mean'] = F32(mean)
            agglosses['stddev'] = F32(std)

            # losses by asset
            losses_by_asset = numpy.zeros((A, R, L), stat_dt)
            for (l, r, aid, stat) in result['avg']:
                losses_by_asset[aid, r, l] = stat
            self.datastore['losses_by_asset'] = losses_by_asset
            self.datastore['agglosses'] = agglosses

            # losses by event
            lbe = numpy.fromiter(((ei, res[ei]) for ei in range(E)), dtlist)
            self.datastore['losses_by_event'] = lbe
            loss_types = ' '.join(self.oqparam.loss_dt().names)
            self.datastore.set_attrs('losses_by_event', loss_types=loss_types)

            # all losses
            if self.oqparam.asset_loss_table:
                array = numpy.zeros((A, E), loss_dt)
                for (l, r), losses_by_aid in result['all_losses'].items():
                    slc = self.event_slice(r)
                    for aid in losses_by_aid:
                        lba = losses_by_aid[aid]  # E
                        lt = loss_dt.names[l]
                        array[lt][aid, slc] = lba
                self.datastore['asset_loss_table'] = array
                tags = [encode(tag) for tag in self.assetcol.tagcol]
                self.datastore.set_attrs('asset_loss_table', tags=tags)
