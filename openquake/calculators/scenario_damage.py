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

import logging
import numpy
from openquake.baselib import hdf5
from openquake.baselib.general import AccumDict, get_indices
from openquake.risklib.scientific import mean_std
from openquake.calculators import base

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


def floats_in(numbers):
    """
    :param numbers: an array of numbers
    :returns: True if there is at least one non-uint32 number
    """
    return (U32(numbers) != numbers).any()


def bin_ddd(fractions, n, seed):
    """
    Converting fractions into discrete damage distributions using bincount
    and numpy.random.choice
    """
    n = int(n)
    D = fractions.shape[1]  # shape (E, D)
    ddd = numpy.zeros(fractions.shape, U32)
    numpy.random.seed(seed)
    for e, frac in enumerate(fractions):
        ddd[e] = numpy.bincount(
            numpy.random.choice(D, n, p=frac/frac.sum()), minlength=D)
    return ddd


def approx_ddd(fractions, n, seed=None):
    """
    Converting fractions into uint16 discrete damage distributions using round
    """
    ddd = U32(numpy.round(fractions * n))
    # fix the no-damage discrete damage distributions by making sure
    # that the total sum is n: nodamage = n - sum(others)
    ddd[:, 0] = n - ddd[:, 1:].sum(axis=1)
    return ddd


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
                      'd_event': dict eid -> array of shape (L, D)
                      + optional consequences}

    `d_asset` and `d_tag` are related to the damage distributions.
    """
    L = len(crmodel.loss_types)
    D = len(crmodel.damage_states)
    consequences = crmodel.get_consequences()
    haz_mon = monitor('getting hazard', measuremem=False)
    rsk_mon = monitor('aggregating risk', measuremem=False)
    d_event = AccumDict(accum=numpy.zeros((L, D), U32))
    res = {'d_event': d_event}
    for name in consequences:
        res[name + '_by_event'] = AccumDict(accum=numpy.zeros(L, F64))
        # using F64 here is necessary: with F32 the non-commutativity
        # of addition would hurt too much with multiple tasks
    seed = param['master_seed']
    # algorithm used to compute the discrete damage distributions
    make_ddd = approx_ddd if param['approx_ddd'] else bin_ddd
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
                        ddds = make_ddd(fractions, asset['number'], seed + aid)
                        for e, ddd in enumerate(ddds):
                            eid = out.eids[e]
                            if ddd[1:].any():
                                ddic[aid, eid][l] = ddd[1:]
                                d_event[eid][l] += ddd
                        if make_ddd is approx_ddd:
                            ms = mean_std(fractions * asset['number'])
                        else:
                            ms = mean_std(ddds)
                        result['d_asset'].append((l, r, asset['ordinal'], ms))
                        # TODO: use the ddd, not the fractions in compute_csq
                        csq = crmodel.compute_csq(asset, fractions, loss_type)
                        for name, values in csq.items():
                            result[name + '_by_asset'].append(
                                (l, r, asset['ordinal'], mean_std(values)))
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
        float_algo = floats_in(self.assetcol['number'])
        if float_algo:
            logging.warning('The exposure contains non-integer asset numbers: '
                            'using floating point damage distributions')
        bad = self.assetcol['number'] > 2**32 - 1
        for ass in self.assetcol[bad]:
            aref = self.assetcol.tagcol.id[ass['id']]
            logging.error("The asset %s has number=%s > 2^32-1!",
                          aref, ass['number'])
        self.param['approx_ddd'] = self.oqparam.approx_ddd or float_algo
        self.param['aed_dt'] = aed_dt = self.crmodel.aid_eid_dd_dt()
        self.param['master_seed'] = self.oqparam.master_seed
        A = len(self.assetcol)
        self.datastore.create_dset('dd_data/data', aed_dt, compression='gzip')
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
        if not len(self.datastore['dd_data/data']):
            logging.warning('There is no damage at all!')
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
