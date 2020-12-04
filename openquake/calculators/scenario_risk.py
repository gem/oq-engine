# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
import logging
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import zip
from openquake.baselib.general import AccumDict
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import scientific, riskinput
from openquake.calculators import base, views

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64  # higher precision to avoid task order dependency
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def value(asset, loss_type):
    if loss_type == 'occupants':
        return asset['occupants_None']
    return asset['value-' + loss_type]


def _event_slice(num_gmfs, r):
    return slice(r * num_gmfs, (r + 1) * num_gmfs)


def ael_dt(loss_names, rlz=False):
    """
    :returns: (asset_id, event_id, loss) or (asset_id, event_id, loss)
    """
    L = len(loss_names),
    if rlz:
        return [('asset_id', U32), ('event_id', U32),
                ('rlzi', U16), ('loss', (F32, L))]
    else:
        return [('asset_id', U32), ('event_id', U32), ('loss', (F32, L))]


def scenario_risk(riskinputs, param, monitor):
    """
    Core function for a scenario computation.

    :param riskinput:
        a of :class:`openquake.risklib.riskinput.RiskInput` object
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
    crmodel = monitor.read('crmodel')
    E = param['E']
    L = len(crmodel.loss_types)
    result = dict(agg=numpy.zeros((E, L), F32), avg=[])
    acc = AccumDict(accum=numpy.zeros(L, F64))  # aid,eid->loss
    for ri in riskinputs:
        for out in ri.gen_outputs(crmodel, monitor, param['tempname']):
            r = out.rlzi
            for l, loss_type in enumerate(crmodel.loss_types):
                losses = out[loss_type]
                if numpy.product(losses.shape) == 0:  # happens for all NaNs
                    continue
                avg = numpy.zeros(len(ri.assets), F32)
                for a, asset in enumerate(ri.assets):
                    aid = asset['ordinal']
                    avg[a] = losses[a].mean()
                    result['avg'].append((l, r, asset['ordinal'], avg[a]))
                    for loss, eid in zip(losses[a], out.eids):
                        acc[aid, eid][l] = loss
                agglosses = losses.sum(axis=0)  # shape num_gmfs
                result['agg'][out.eids, l] += agglosses

    ael = [(aid, eid, loss) for (aid, eid), loss in sorted(acc.items())]
    result['ael'] = numpy.array(ael, param['ael_dt'])
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
        self.param['tempname'] = riskinput.cache_epsilons(
            self.datastore, oq, self.assetcol, self.crmodel, E)
        self.param['E'] = E
        # assuming the weights are the same for all IMTs
        try:
            self.param['weights'] = self.datastore['weights'][()]
        except KeyError:
            self.param['weights'] = [1 / self.R for _ in range(self.R)]
        self.param['ael_dt'] = dt = ael_dt(oq.loss_names)
        A = len(self.assetcol)
        self.datastore.create_dset('loss_data/data', dt)
        self.datastore.create_dset('loss_data/indices', U32, (A, 2))

    def combine(self, acc, res):
        """
        Combine the outputs from scenario_risk and incrementally store
        the asset loss table
        """
        with self.monitor('saving loss_data', measuremem=True):
            ael = res.pop('ael', ())
            if len(ael) == 0:
                return acc + res
            hdf5.extend(self.datastore['loss_data/data'], ael)
            return acc + res

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        loss_dt = self.oqparam.loss_dt()
        L = len(loss_dt.names)
        dtlist = [('event_id', U32), ('loss', (F32, (L,)))]
        R = self.R
        with self.monitor('saving outputs'):
            A = len(self.assetcol)

            # agg losses
            res = result['agg']
            E, L = res.shape
            agglosses = numpy.zeros((R, L), stat_dt)
            for r in range(R):
                mean, std = scientific.mean_std(res[self.event_slice(r)])
                agglosses[r]['mean'] = F32(mean)
                agglosses[r]['stddev'] = F32(std)

            # losses by asset
            losses_by_asset = numpy.zeros((A, R, L), F32)
            for (l, r, aid, avg) in result['avg']:
                losses_by_asset[aid, r, l] = avg
            self.datastore['avg_losses-rlzs'] = losses_by_asset
            set_rlzs_stats(self.datastore, 'avg_losses',
                           asset_id=self.assetcol['id'],
                           loss_type=self.oqparam.loss_names)
            self.datastore['agglosses'] = agglosses

            # losses by event
            lbe = numpy.zeros(E, dtlist)
            lbe['event_id'] = range(E)
            lbe['loss'] = res
            self.datastore['losses_by_event'] = lbe
            loss_types = self.oqparam.loss_dt().names
            self.datastore.set_attrs('losses_by_event', loss_types=loss_types)
        logging.info('Mean portfolio loss\n' +
                     views.view('portfolio_loss', self.datastore))
