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

import os.path
import logging
import numpy
import pandas

from openquake.baselib import hdf5, general
from openquake.hazardlib.stats import compute_stats2
from openquake.risklib import scientific, connectivity
from openquake.commonlib import datastore, calc
from openquake.calculators import base
from openquake.calculators.event_based_risk import EventBasedRiskCalculator
from openquake.calculators.post_risk import (
    get_loss_builder, fix_dtypes, PostRiskCalculator)
from openquake.calculators.export import DISPLAY_NAME

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32


def zero_dmgcsq(A, R, L, crmodel):
    """
    :returns: an array of zeros of shape (A, R, L, Dc)
    """
    dmg_csq = crmodel.get_dmg_csq()
    Dc = len(dmg_csq) + 1  # damages + consequences
    P = len(crmodel.perils)
    return numpy.zeros((P, A, R, L, Dc), F32)


def damage_from_gmfs(gmfslices, oqparam, dstore, monitor):
    """
    :param gmfslices: an array (S, 3) with S slices (start, stop, weight)
    :param oqparam: OqParam instance
    :param dstore: DataStore instance from which to read the GMFs
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays, the output of event_based_damage
    """
    if dstore.parent:
        dstore.parent.open('r')
    dfs = []
    with dstore, monitor('reading data', measuremem=True):
        for gmfslice in gmfslices:
            slc = slice(gmfslice[0], gmfslice[1])
            dfs.append(dstore.read_df('gmf_data', slc=slc))
        df = pandas.concat(dfs)
    return event_based_damage(df, oqparam, dstore, monitor)


def event_based_damage(df, oq, dstore, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, imt, ...
    :param oq: parameters coming from the job.ini
    :param dstore: a DataStore instance
    :param monitor: a Monitor instance
    :returns: (damages (eid, kid) -> LDc plus damages (A, Dc))
    """
    mon = monitor('computing dds', measuremem=False)
    with monitor('reading gmf_data'):
        if oq.parentdir:
            dstore = datastore.read(oq.hdf5path, parentdir=oq.parentdir)
        else:
            dstore.open('r')
        assetcol = dstore['assetcol']
        crmodel = monitor.read('crmodel')
        aggids = monitor.read('aggids')
    dmgcsq = zero_dmgcsq(len(assetcol), oq.R, oq.L, crmodel)
    P, _A, R, L, Dc = dmgcsq.shape
    D = len(crmodel.damage_states)
    rlzs = dstore['events']['rlz_id']
    dddict = general.AccumDict(accum=numpy.zeros((L, Dc), F32))  # eid, kid
    for sid, asset_df in assetcol.to_dframe().groupby('site_id'):
        # working one site at the time
        gmf_df = df[df.sid == sid]
        if len(gmf_df) == 0:
            continue
        eids = gmf_df.eid.to_numpy()
        E = len(eids)
        if not oq.float_dmg_dist:
            rng = scientific.MultiEventRNG(
                oq.master_seed, numpy.unique(eids))
        else:
            rng = None
        for taxo, adf in asset_df.groupby('taxonomy'):
            aids = adf.index.to_numpy()
            A = len(aids)
            with mon:
                rc = scientific.RiskComputer(crmodel, taxo)
                dd5 = rc.get_dd5(adf, gmf_df, rng, Dc-D, crmodel)  # (A, E, L, Dc)
            if R == 1:  # possibly because of collect_rlzs
                dmgcsq[:, aids, 0] += dd5.sum(axis=2)
            else:
                for e, rlz in enumerate(rlzs[eids]):
                    dmgcsq[:, aids, rlz] += dd5[:, :, e]
            if P > 1:
                dd4 = numpy.empty(dd5.shape[1:])
                for li in range(L):
                    for a in range(A):
                        for e in range(E):
                            dd4[a, e, li, :D] = scientific.compose_dds(dd5[:, a, e, li, :D])
                            dd4[a, e, li, D:] = dd5[:, a, e, li, D:].max(axis=0)
            else:
                dd4 = dd5[0]
            tot = dd4.sum(axis=0)  # (E, L, Dc)
            for e, eid in enumerate(eids):
                dddict[eid, oq.K] += tot[e]
                if oq.K:
                    for kids in aggids:
                        for a, aid in enumerate(aids):
                            dddict[eid, kids[aid]] += dd4[a, e]
    csqidx = {dc: i + 1 for i, dc in enumerate(crmodel.get_dmg_csq())}
    return _dframe(dddict, csqidx, oq.loss_types), dmgcsq


def _dframe(dddic, csqidx, loss_types):
    # convert {(eid, kid): dd} into a DataFrame (agg_id, event_id, loss_id)
    dic = general.AccumDict(accum=[])
    for (eid, kid), dd in sorted(dddic.items()):
        for li, lt in enumerate(loss_types):
            dic['agg_id'].append(kid)
            dic['event_id'].append(eid)
            dic['loss_id'].append(scientific.LOSSID[lt])
            for cname, ci in csqidx.items():
                dic[cname].append(dd[li, ci])
    fix_dtypes(dic)
    return pandas.DataFrame(dic)


@base.calculators.add('event_based_damage', 'scenario_damage')
class DamageCalculator(EventBasedRiskCalculator):
    """
    Damage calculator
    """
    core_task = event_based_damage
    is_stochastic = True
    precalc = 'event_based'
    accept_precalc = ['scenario', 'event_based',
                      'event_based_risk', 'event_based_damage']

    def create_avg_losses(self):
        """
        Do nothing: there are no losses in the DamageCalculator
        """

    def execute(self):
        """
        Compute risk from GMFs or ruptures depending on what is stored
        """
        oq = self.oqparam
        number = self.assetcol['value-number']
        num_floats = (U32(number) != number).sum()
        if oq.discrete_damage_distribution and num_floats:
            raise ValueError(
                'The exposure contains %d non-integer asset numbers: '
                'you cannot use dicrete_damage_distribution=true' % num_floats)
        oq.R = self.R  # 1 if collect_rlzs
        oq.float_dmg_dist = not oq.discrete_damage_distribution
        if oq.hazard_calculation_id:
            oq.parentdir = os.path.dirname(self.datastore.ppath)
        if oq.investigation_time:  # event based
            self.builder = get_loss_builder(self.datastore, oq)  # check
        self.dmgcsq = zero_dmgcsq(
            len(self.assetcol), self.R, oq.L, self.crmodel)
        if oq.K:
            aggids, _ = self.assetcol.build_aggids(oq.aggregate_by)
        else:
            aggids = 0
        smap = calc.starmap_from_gmfs(
            damage_from_gmfs, oq, self.datastore, self._monitor)
        smap.monitor.save('aggids', aggids)
        smap.monitor.save('assets', self.assetcol.to_dframe('id'))
        smap.monitor.save('crmodel', self.crmodel)
        return smap.reduce(self.combine)

    def combine(self, acc, res):
        """
        :param acc:
            unused
        :param res:
            DataFrame with fields (event_id, agg_id, loss_id, dmg1 ...)
            plus array with damages and consequences of shape (A, Dc)

        Combine the results and grows risk_by_event with fields
        (event_id, agg_id, loss_id) and (dmg_0, dmg_1, dmg_2, ...)
        """
        df, dmgcsq = res
        self.dmgcsq += dmgcsq
        with self.monitor('saving risk_by_event', measuremem=True):
            for name in df.columns:
                dset = self.datastore['risk_by_event/' + name]
                hdf5.extend(dset, df[name].to_numpy())
        return 1

    def post_execute(self, dummy):
        """
        Store damages-rlzs/stats, aggrisk and aggcurves
        """
        oq = self.oqparam
        # no damage check, perhaps the sites where disjoint from gmf_data
        if self.dmgcsq[:, :, :, :, 1:].sum() == 0:
            haz_sids = self.datastore['gmf_data/sid'][:]
            count = numpy.isin(haz_sids, self.sitecol.sids).sum()
            if count == 0:
                raise ValueError('The sites in gmf_data are disjoint from the '
                                 'site collection!?')
            else:
                logging.warning(
                    'There is no damage, perhaps the hazard is too small?')
            return

        prc = PostRiskCalculator(oq, self.datastore.calc_id)
        prc.assetcol = self.assetcol
        if hasattr(self, 'exported'):
            prc.exported = self.exported

        prc.pre_execute()
        res = prc.execute()
        prc.post_execute(res)

        P, _A, _R, L, _Dc = self.dmgcsq.shape
        D = len(self.crmodel.damage_states)
        # fix no_damage distribution for events with zero damage
        number = self.assetcol['value-number']
        for p in range(P):
            for r in range(self.R):
                self.dmgcsq[p, :, r] /= prc.num_events[r]
                ndamaged = self.dmgcsq[p, :, r, :, 1:D].sum(axis=2)
                # shape (A, L)
                for li in range(L):
                    # set no_damage
                    self.dmgcsq[p, :, r, li, 0] = number - ndamaged[:, li]

        # due numeric errors we can have small negative damages; we fix them
        small = self.dmgcsq < 0
        assert (small > -1E-6).all()
        self.dmgcsq[small] = 0

        self.datastore['damages-rlzs'] = arr = self.crmodel.to_multi_damage(
            self.dmgcsq)
        self.datastore.set_shape_descr(
            'damages-rlzs', asset_id=len(arr), rlz_id=self.R)
        s = oq.hazard_stats()
        if s and self.R > 1:
            _statnames, statfuncs = zip(*s.items())
            weights = self.datastore['weights'][:]
            self.datastore.hdf5.create_dataset(
                'damages-stats', data=compute_stats2(arr, statfuncs, weights))
            self.datastore.set_shape_descr(
                'damages-stats', asset_id=len(arr), stat=list(s))
        if oq.infrastructure_connectivity_analysis:
            logging.info('Running connectivity analysis')
            results = connectivity.analysis(self.datastore)
            self._store_connectivity_analysis_results(results)

    def _store_connectivity_analysis_results(self, conn_results):
        avg_dict = {}
        if 'avg_connectivity_loss_eff' in conn_results:
            avg_dict['efl'] = [conn_results['avg_connectivity_loss_eff']]
        if 'avg_connectivity_loss_pcl' in conn_results:
            avg_dict['pcl'] = [conn_results['avg_connectivity_loss_pcl']]
        if 'avg_connectivity_loss_wcl' in conn_results:
            avg_dict['wcl'] = [conn_results['avg_connectivity_loss_wcl']]
        if 'avg_connectivity_loss_ccl' in conn_results:
            avg_dict['ccl'] = [conn_results['avg_connectivity_loss_ccl']]
        if avg_dict:
            self.datastore.create_df(
                'infra-avg_loss', pandas.DataFrame(data=avg_dict),
                display_name=DISPLAY_NAME['infra-avg_loss'])
        if 'event_connectivity_loss_eff' in conn_results:
            self.datastore.create_df(
                'infra-event_efl',
                conn_results['event_connectivity_loss_eff'],
                display_name=DISPLAY_NAME['infra-event_efl'])
        if 'event_connectivity_loss_pcl' in conn_results:
            self.datastore.create_df(
                'infra-event_pcl',
                conn_results['event_connectivity_loss_pcl'],
                display_name=DISPLAY_NAME['infra-event_pcl'])
        if 'event_connectivity_loss_wcl' in conn_results:
            self.datastore.create_df(
                'infra-event_wcl',
                conn_results['event_connectivity_loss_wcl'],
                display_name=DISPLAY_NAME['infra-event_wcl'])
        if 'event_connectivity_loss_ccl' in conn_results:
            self.datastore.create_df(
                'infra-event_ccl',
                conn_results['event_connectivity_loss_ccl'],
                display_name=DISPLAY_NAME['infra-event_ccl'])
        if 'taz_cl' in conn_results:
            self.datastore.create_df(
                'infra-taz_cl',
                conn_results['taz_cl'],
                display_name=DISPLAY_NAME['infra-taz_cl'])
        if 'dem_cl' in conn_results:
            self.datastore.create_df(
                'infra-dem_cl',
                conn_results['dem_cl'],
                display_name=DISPLAY_NAME['infra-dem_cl'])
        if 'node_el' in conn_results:
            self.datastore.create_df(
                'infra-node_el',
                conn_results['node_el'],
                display_name=DISPLAY_NAME['infra-node_el'])
