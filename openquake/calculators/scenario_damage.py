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
from openquake.baselib.general import AccumDict, get_nbytes_msg
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.calculators import base, views

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


def floats_in(numbers):
    """
    :param numbers: an array of numbers
    :returns: number of non-uint32 number
    """
    return (U32(numbers) != numbers).sum()


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


def scenario_damage(riskinputs, param, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
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
    crmodel = monitor.read('crmodel')
    L = len(crmodel.loss_types)
    D = len(crmodel.damage_states)
    consequences = crmodel.get_consequences()
    # algorithm used to compute the discrete damage distributions
    approx_ddd = param['approx_ddd']
    z = numpy.zeros((L, D - 1), F32 if approx_ddd else U32)
    d_event = AccumDict(accum=z)
    res = {'d_event': d_event, 'd_asset': []}
    for name in consequences:
        res['avg_' + name] = []
        res[name + '_by_event'] = AccumDict(accum=numpy.zeros(L, F64))
        # using F64 here is necessary: with F32 the non-commutativity
        # of addition would hurt too much with multiple tasks
    seed = param['master_seed']
    num_events = param['num_events']  # per realization
    for ri in riskinputs:
        # here instead F32 floats are ok
        acc = []  # (aid, eid, lid, ds...)
        ri.hazard_getter.init()
        for out in ri.gen_outputs(crmodel, monitor):
            r = out.rlzi
            ne = num_events[r]  # total number of events
            for l, loss_type in enumerate(crmodel.loss_types):
                for asset, fractions in zip(ri.assets, out[loss_type]):
                    aid = asset['ordinal']
                    if approx_ddd:
                        ddds = fractions * asset['number']
                    else:
                        ddds = bin_ddd(
                            fractions, asset['number'], seed + aid)
                    # ddds has shape E', D with E' == len(out.eids)
                    for e, ddd in enumerate(ddds):
                        dmg = ddd[1:]
                        if dmg.sum():
                            eid = out.eids[e]  # (aid, eid, l) is unique
                            acc.append((aid, eid, l) + tuple(dmg))
                            d_event[eid][l] += ddd[1:]
                    tot = ddds.sum(axis=0)  # shape D
                    nodamage = asset['number'] * (ne - len(ddds))
                    tot[0] += nodamage
                    res['d_asset'].append((l, r, aid, tot))
                    # TODO: use the ddd, not the fractions in compute_csq
                    csq = crmodel.compute_csq(asset, fractions, loss_type)
                    for name, values in csq.items():
                        res['avg_%s' % name].append(
                            (l, r, asset['ordinal'], values.sum(axis=0)))
                        by_event = res[name + '_by_event']
                        for eid, value in zip(out.eids, values):
                            by_event[eid][l] += value
        res['aed'] = numpy.array(acc, param['asset_damage_dt'])
    return res


@base.calculators.add('scenario_damage', 'event_based_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Damage calculator
    """
    core_task = scenario_damage
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based', 'event_based_risk']

    def pre_execute(self):
        super().pre_execute()
        num_floats = floats_in(self.assetcol['number'])
        if num_floats:
            logging.warning(
                'The exposure contains %d non-integer asset numbers: '
                'using floating point damage distributions', num_floats)
        bad = self.assetcol['number'] > 2**32 - 1
        for ass in self.assetcol[bad]:
            aref = self.assetcol.tagcol.id[ass['id']]
            logging.error("The asset %s has number=%s > 2^32-1!",
                          aref, ass['number'])
        self.param['approx_ddd'] = self.oqparam.approx_ddd or num_floats
        self.param['asset_damage_dt'] = self.crmodel.asset_damage_dt(
            self.oqparam.approx_ddd or num_floats)
        self.param['master_seed'] = self.oqparam.master_seed
        self.param['num_events'] = numpy.bincount(  # events by rlz
            self.datastore['events']['rlz_id'])
        self.datastore.create_dframe(
            'dd_data', self.param['asset_damage_dt'], 'gzip')
        self.riskinputs = self.build_riskinputs('gmf')

    def combine(self, acc, res):
        with self.monitor('saving dd_data', measuremem=True):
            aed = res.pop('aed', ())
            if len(aed) == 0:
                return acc + res
            for name in aed.dtype.names:
                hdf5.extend(self.datastore['dd_data/' + name], aed[name])
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
        L = self.L = len(ltypes)
        R = self.R
        D = len(dstates)
        A = len(self.assetcol)
        E = len(self.datastore['events'])

        # reduction factor
        _, msg1 = get_nbytes_msg(dict(A=A, E=E, L=L))
        _, msg2 = get_nbytes_msg(dict(nrows=len(self.datastore['dd_data/eid']),
                                      ncols=D+2))
        logging.info('Using %s\ninstead of %s', msg2, msg1)

        # avg_ratio = ratio used when computing the averages
        oq = self.oqparam
        if oq.investigation_time:  # event_based_damage
            avg_ratio = numpy.array([oq.ses_ratio] * R)
        else:  # scenario_damage
            avg_ratio = 1. / self.param['num_events']

        # damage by asset
        d_asset = numpy.zeros((A, R, L, D), F32)
        for (l, r, a, tot) in result['d_asset']:
            d_asset[a, r, l] = tot * avg_ratio[r]
        self.datastore['damages-rlzs'] = d_asset
        set_rlzs_stats(self.datastore,
                       'damages',
                       asset_id=self.assetcol['id'],
                       loss_type=oq.loss_names,
                       dmg_state=dstates)
        self.sanity_check()

        # damage by event: make sure the sum of the buildings is consistent
        tot = self.assetcol['number'].sum()
        dt = F32 if self.param['approx_ddd'] else U32
        dbe = numpy.zeros((self.E, L, D), dt)  # shape E, L, D
        dbe[:, :, 0] = tot
        for e, dmg_by_lt in result['d_event'].items():
            for l, dmg in enumerate(dmg_by_lt):
                dbe[e, l,  0] = tot - dmg.sum()
                dbe[e, l,  1:] = dmg
        self.datastore['dmg_by_event'] = dbe

        # consequence distributions
        del result['d_asset']
        del result['d_event']
        dtlist = [('event_id', U32), ('rlz_id', U16), ('loss', (F32, (L,)))]
        rlz = self.datastore['events']['rlz_id']
        for name, csq in result.items():
            if name.startswith('avg_'):
                c_asset = numpy.zeros((A, R, L), F32)
                for (l, r, a, stat) in result[name]:
                    c_asset[a, r, l] = stat * avg_ratio[r]
                self.datastore[name + '-rlzs'] = c_asset
                set_rlzs_stats(self.datastore, name,
                               asset_id=self.assetcol['id'],
                               loss_type=oq.loss_names)
            elif name.endswith('_by_event'):
                arr = numpy.zeros(len(csq), dtlist)
                for i, (eid, loss) in enumerate(csq.items()):
                    arr[i] = (eid, rlz[eid], loss)
                self.datastore[name] = arr

    def sanity_check(self):
        """
        Sanity check on the total number of assets
        """
        if self.R == 1:
            arr = self.datastore.sel('damages-rlzs')  # shape (A, 1, L, D)
        else:
            arr = self.datastore.sel('damages-stats', stat='mean')
        avg = arr.sum(axis=(0, 1))  # shape (L, D)
        if not len(self.datastore['dd_data/aid']):
            logging.warning('There is no damage at all!')
        else:
            df = views.portfolio_damage_error(self.datastore, avg[:, 1:])
            rst = views.rst_table(numpy.array(df), list(df.columns))
            logging.info('Portfolio damage\n%s' % rst)
        num_assets = avg.sum(axis=1)  # by loss_type
        expected = self.assetcol['number'].sum()
        nums = set(num_assets) | {expected}
        if len(nums) > 1:
            numdic = dict(expected=expected)
            for lt, num in zip(self.oqparam.loss_names, num_assets):
                numdic[lt] = num
            logging.info('Due to numeric errors the total number of assets'
                         ' is imprecise: %s', numdic)
