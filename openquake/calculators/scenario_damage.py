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
from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict, get_indices
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
    consequences = crmodel.get_consequences()
    collapse_threshold = param['collapse_threshold']
    haz_mon = monitor('getting hazard', measuremem=False)
    rsk_mon = monitor('aggregating risk', measuremem=False)
    acc = AccumDict(accum=numpy.zeros((L, D), F64))  # must be 64 bit
    res = {'d_event': acc}
    for name in consequences:
        res[name + '_by_event'] = AccumDict(accum=numpy.zeros(L, F64))
    for ri in riskinputs:
        # otherwise test 4b will randomly break with last digit changes
        # in dmg_by_event :-(
        result = dict(d_asset=[])
        for name in consequences:
            result[name + '_by_asset'] = []
        ddic = AccumDict(accum=numpy.zeros((L, D - 1), F32))  # aid,eid->dd
        with haz_mon:
            ri.hazard_getter.init()
        for out in ri.gen_outputs(crmodel, monitor):
            with rsk_mon:
                r = out.rlzi
                for l, loss_type in enumerate(crmodel.loss_types):
                    for asset, fractions in zip(ri.assets, out[loss_type]):
                        aid = asset['ordinal']
                        dmg = fractions * asset['number']  # shape (F, D)
                        for e, dmgdist in enumerate(dmg):
                            eid = out.eids[e]
                            acc[eid][l] += dmgdist
                            if dmgdist[-1] >= collapse_threshold:
                                ddic[aid, eid][l] = fractions[e, 1:]
                        result['d_asset'].append(
                            (l, r, asset['ordinal'], scientific.mean_std(dmg)))
                        csq = crmodel.compute_csq(asset, fractions, loss_type)
                        for name, values in csq.items():
                            result[name + '_by_asset'].append(
                                (l, r, asset['ordinal'],
                                 scientific.mean_std(values)))
                            by_event = res[name + '_by_event']
                            for eid, value in zip(out.eids, values):
                                by_event[eid][l] += value
        with rsk_mon:
            result['aed'] = aed = numpy.zeros(len(ddic), param['aed_dt'])
            for i, ((aid, eid), dd) in enumerate(sorted(ddic.items())):
                aed[i] = (aid, eid, dd)
        yield result
    yield res


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
        self.param['collapse_threshold'] = self.oqparam.collapse_threshold
        self.param['aed_dt'] = aed_dt = self.crmodel.aid_eid_dd_dt()
        A = len(self.assetcol)
        self.datastore.create_dset('dd_data/data', aed_dt)
        self.datastore.create_dset('dd_data/indices', U32, (A, 2))
        self.riskinputs = self.build_riskinputs('gmf')
        self.start = 0

    def combine(self, acc, res):
        aed = res.pop('aed', ())
        if len(aed) == 0:
            return acc + res
        for aid, [(i1, i2)] in get_indices(aed['aid']).items():
            self.datastore['dd_data/indices'][aid] = (
                self.start + i1, self.start + i2)
        self.start += len(aed)
        hdf5.extend(self.datastore['dd_data/data'], aed)
        return acc + res

    def post_execute(self, result):
        """
        Compute stats for the aggregated distributions and save
        the results on the datastore.
        """
        if not result:
            self.collapsed()
            return
        dstates = self.crmodel.damage_states
        ltypes = self.crmodel.loss_types
        L = len(ltypes)
        R = len(self.rlzs_assoc.realizations)
        D = len(dstates)
        A = len(self.assetcol)
        indices = self.datastore['dd_data/indices'][()]
        events_per_asset = (indices[:, 1] - indices[:, 0]).mean()
        logging.info('Found ~%d dmg distributions per asset', events_per_asset)

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
        del result['d_event']
        dtlist = [('event_id', U32), ('rlz_id', U16), ('loss', (F32, (L,)))]
        stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])
        rlz = self.datastore['events']['rlz_id']
        for name, csq in result.items():
            if name.endswith('_by_asset'):
                c_asset = numpy.zeros((A, R, L), stat_dt)
                for (l, r, a, stat) in result[name]:
                    c_asset[a, r, l] = stat
                self.datastore[name] = c_asset
            elif name.endswith('_by_event'):
                arr = numpy.zeros(len(csq), dtlist)
                for i, (eid, loss) in enumerate(csq.items()):
                    arr[i] = (eid, rlz[eid], loss)
                self.datastore[name] = arr


@base.calculators.add('event_based_damage')
class EventBasedDamageCalculator(ScenarioDamageCalculator):
    """
    Event Based Damage calculator, able to compute dmg_by_asset, dmg_by_event
    and consequences.
    """
    core_task = scenario_damage
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk']
