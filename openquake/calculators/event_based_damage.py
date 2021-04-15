# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
import pandas

from openquake.baselib import hdf5, datastore, general, parallel
from openquake.hazardlib.stats import avg_std
from openquake.risklib import scientific
from openquake.calculators import base
from openquake.calculators.event_based_risk import EventBasedRiskCalculator

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


def fix_dtype(dic, dtype, names):
    for name in names:
        dic[name] = dtype(dic[name])


def event_based_damage(df, param, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_...
    :param param: a dictionary of parameters coming from the job.ini
    :param monitor: a Monitor instance
    :returns: damages as a dictionary (eid, kid) -> LD
    """
    mon_risk = monitor('computing risk', measuremem=False)
    dstore = datastore.read(param['hdf5path'])
    K = param['K']
    with monitor('reading data'):
        if hasattr(df, 'start'):  # it is actually a slice
            df = dstore.read_df('gmf_data', slc=df)
        assets_df = dstore.read_df('assetcol/array', 'ordinal')
        kids = (dstore['assetcol/kids'][:] if K
                else numpy.zeros(len(assets_df), U16))
        crmodel = monitor.read('crmodel')
    rndgen = scientific.MultiEventRNG(
        param['master_seed'], numpy.unique(df.eid), param['asset_correlation'])
    L = len(crmodel.loss_types)
    D = len(crmodel.damage_states)
    dddict = general.AccumDict(accum=numpy.zeros((L, D), U32))  # by eid, kid
    for taxo, asset_df in assets_df.groupby('taxonomy'):
        gmf_df = df[numpy.isin(df.sid.to_numpy(), asset_df.site_id.to_numpy())]
        if len(gmf_df) == 0:
            continue
        with mon_risk:
            out = crmodel.get_output(taxo, asset_df, gmf_df)
            eids = out['eids']
            taxkids = kids[asset_df.index]
            ukids = numpy.unique(taxkids)
            numbers = U32(out['assets']['number'])
            for lti, lt in enumerate(out['loss_types']):
                ddd = rndgen.discrete_dmg_dist(eids, out[lt], numbers)
                if K:
                    tot = ddd.sum(axis=0)  # shape AED -> ED
                res = general.fast_agg(taxkids, ddd)  # shape KED
                for e, eid in enumerate(eids):
                    for k, kid in enumerate(ukids):
                        dddict[eid, kid][lti] += res[k, e]
                    if K:
                        dddict[eid, K][lti] += tot[e]
    dic = general.AccumDict(accum=[])
    for (eid, kid), dd in dddict.items():
        for lti in range(L):
            dic['event_id'].append(eid)
            dic['agg_id'].append(kid)
            dic['loss_id'].append(lti)
            for dsi in range(1, D):
                dic['dmg_%d' % dsi].append(dd[lti, dsi])
    fix_dtype(dic, U32, ['event_id'])
    fix_dtype(dic, U16, ['agg_id'])
    fix_dtype(dic, U8, ['loss_id'])
    fix_dtype(dic, F32, ['dmg_%d' % d for d in range(1, D)])
    return pandas.DataFrame(dic)


@base.calculators.add('event_based_damage')
class DamageCalculator(EventBasedRiskCalculator):
    """
    Damage calculator
    """
    core_task = event_based_damage
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based',
                      'event_based_risk', 'event_based_damage']

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        smap = parallel.Starmap(
            event_based_damage, self.gen_args(), h5=self.datastore.hdf5)
        smap.monitor.save('assets', self.assetcol.to_dframe())
        smap.monitor.save('crmodel', self.crmodel)
        return smap.reduce(self.combine)

    def combine(self, acc, res):
        """
        Combine the results and grows agg_damage_table with fields
        (event_id, agg_id, loss_id) and (dmg_0, dmg_1, dmg_2, ...)
        """
        if res is None:
            raise MemoryError('You ran out of memory!')
        with self.monitor('saving dd_data', measuremem=True):
            for name in res.columns:
                dset = self.datastore['agg_damage_table/' + name]
                hdf5.extend(dset, res[name].to_numpy())

    def post_execute(self, result):
        pass
