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

from openquake.baselib import hdf5, general, parallel
from openquake.hazardlib.stats import compute_stats2, mean_curve
from openquake.risklib import scientific, connectivity
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


def damage_from_gmfs(df, assetcol, oq, rlzs, monitor):
    """
    :param df: a DataFrame of GMFs
    :param assetcol: DataStore instance from which to read the GMFs
    :param oq: OqParam instance
    :param rlzs: E realizations or None
    :param monitor: a Monitor instance
    :returns: a dictionary of arrays, the output of event_based_damage
    """
    with monitor('reading data', measuremem=True):
        crmodel = monitor.read('crmodel')
        aggids = monitor.read('aggids')

    dmgcsq = zero_dmgcsq(len(assetcol), oq.R, oq.L, crmodel)
    P, _A, R, L, Dc = dmgcsq.shape
    D = len(crmodel.damage_states)
    dd_dict = general.AccumDict(accum=numpy.zeros((L, Dc), F32))  # eid, kid
    idx = {o: i for i, o in enumerate(assetcol['ordinal'])}
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
            A = len(adf)
            ords = adf.ordinal.to_numpy()
            idxs = [idx[o] for o in ords]
            rc = scientific.RiskComputer(crmodel, taxo)
            dd5 = rc.get_dd5(adf, gmf_df, rng, Dc-D, crmodel)  # (A, E, L, Dc)
            if R == 1:  # possibly because of collect_rlzs
                dmgcsq[:, idxs, 0] += dd5.sum(axis=2)
            else:  # use rlzs
                for e, rlz in enumerate(rlzs[eids]):
                    dmgcsq[:, idxs, rlz] += dd5[:, :, e]
            if P > 1:
                dd4 = numpy.empty(dd5.shape[1:])
                for li in range(L):
                    for a in range(A):
                        for e in range(E):
                            dd4[a, e, li, :D] = scientific.compose_dds(
                                dd5[:, a, e, li, :D])
                            dd4[a, e, li, D:] = dd5[:, a, e, li, D:].max(axis=0)
            else:
                dd4 = dd5[0]
            tot = dd4.sum(axis=0)  # (E, L, Dc)
            for e, eid in enumerate(eids):
                dd_dict[eid, oq.K] += tot[e]
                if oq.K:
                    for kids in aggids:
                        for a, o in enumerate(ords):
                            dd_dict[eid, kids[o]] += dd4[a, e]
    return dd_dict, dmgcsq, assetcol['ordinal']


def _dframe(dd_dic, csqidx, loss_types):
    # convert {(eid, kid): dd} into a DataFrame (agg_id, event_id, loss_id)
    dic = general.AccumDict(accum=[])
    for (eid, kid), dd in sorted(dd_dic.items()):
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
    core_task = damage_from_gmfs
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
        if oq.investigation_time:  # event based
            self.builder = get_loss_builder(self.datastore, oq)  # check
        self.dmgcsq = zero_dmgcsq(
            len(self.assetcol), self.R, oq.L, self.crmodel)
        if oq.K:
            aggids, _ = self.assetcol.build_aggids(oq.aggregate_by)
        else:
            aggids = 0
        gmf_df = self.datastore.read_df('gmf_data')
        if oq.R > 1:
            # i.e. case_9 in scenario_damage
            rlzs = self.datastore['events']['rlz_id']
        else:
            rlzs = None
        self.datastore.swmr_on()
        smap =  parallel.Starmap(damage_from_gmfs, h5=self.datastore)
        smap.monitor.save('aggids', aggids)
        smap.monitor.save('crmodel', self.crmodel)
        ct = oq.concurrent_tasks or 1
        sids = self.assetcol['site_id']
        for t in range(ct):
            gmf_tile = gmf_df[gmf_df.sid % ct == t]
            asset_tile = self.assetcol.new(self.assetcol.array[sids % ct == t])
            if len(asset_tile):
                smap.submit((gmf_tile, asset_tile, oq, rlzs))
        csqidx = {dc: i + 1 for i, dc in enumerate(self.crmodel.get_dmg_csq())}
        dd_dict = general.AccumDict(accum=0)
        for ddd, dmgcsq, ords in smap:
            dd_dict += ddd
            self.dmgcsq[:, ords] += dmgcsq
        df = _dframe(dd_dict, csqidx, oq.loss_types)
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
        self._check_no_damage()
        if self.dmgcsq[:, :, :, :, 1:].sum() == 0:
            return
        prc = self._run_postrisk()
        self._fix_no_damage(prc)
        self._store_damages()
        if oq.infrastructure_connectivity_analysis:
            self._run_connectivity()
        if 'interdependencies' in oq.inputs:  # we are in the child
            self._store_interdependencies(oq)
            if oq.infrastructure_connectivity_analysis:
                self._run_connectivity(prefix='inter')

    def _check_no_damage(self):
        """
        Raise or warn if the sites in gmf_data are disjoint from the site
        collection, i.e. there is no damage at all
        """
        # no damage check, perhaps the sites where disjoint from gmf_data
        if self.dmgcsq[:, :, :, :, 1:].sum() == 0:
            haz_sids = self.datastore['gmf_data/sid'][:]
            count = numpy.isin(haz_sids, self.sitecol.sids).sum()
            if count == 0:
                raise ValueError('The sites in gmf_data are disjoint from the '
                                 'site collection!?')
            logging.warning(
                'There is no damage, perhaps the hazard is too small?')

    def _run_postrisk(self):
        """
        Run the postrisk calculator to compute aggrisk and aggcurves
        """
        oq = self.oqparam
        prc = PostRiskCalculator(oq, self.datastore.calc_id)
        prc.assetcol = self.assetcol
        if hasattr(self, 'exported'):
            prc.exported = self.exported
        prc.pre_execute()
        res = prc.execute()
        prc.post_execute(res)
        return prc

    def _fix_no_damage(self, prc):
        """
        Fix the no_damage distribution for events with zero damage and
        correct the small negative damages arising from numeric errors
        """
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

    def _store_damages(self):
        """
        Store the damages-rlzs and, when there are multiple realizations,
        the mean damages-stats
        """
        oq = self.oqparam
        self.datastore['damages-rlzs'] = arr = self.crmodel.to_multi_damage(
            self.dmgcsq)
        self.datastore.set_shape_descr(
            'damages-rlzs', asset_id=len(arr), rlz_id=self.R)
        s = oq.hazard_stats()
        if s and self.R > 1:
            logging.info('Computing mean damages per asset')
            weights = self.datastore['weights'][:]
            data = compute_stats2(arr, [mean_curve], weights)
            self.datastore.hdf5.create_dataset('damages-stats', data=data)
            self.datastore.set_shape_descr(
                'damages-stats', asset_id=len(arr), stat=['mean'])

    def _run_connectivity(self, prefix='infra'):
        """
        Run the infrastructure connectivity analysis and store its results
        """
        logging.info('Running connectivity analysis')
        results = connectivity.analysis(self.datastore)
        self._store_connectivity_analysis_results(results, prefix)

    def _store_interdependencies(self, oq):
        """
        Build the interdependencies graph between the parent (hazard) and
        the child (damage) calculations and store the resulting
        non_operational columns in the child's risk_by_event dataset
        """
        asset2id_parent = {a.decode('ascii'): i for i, a in enumerate(
            self.datastore.parent['assetcol']['id'])}
        asset2id_child = {a.decode('ascii'): i for i, a in enumerate(
            self.assetcol['id'])}

        state2column = dict(zip(self.crmodel.damage_states[1:],
                                self.crmodel.get_dmg_csq()))
        # Allow non_operational as source state too
        state2column['non_operational'] = 'non_operational'

        self.interdep_df['col'] = [state2column[s] for s in
                                   self.interdep_df.source_damage_state]
        self.interdep_df['parent_id'] = [asset2id_parent[a] for a in
                                         self.interdep_df.source_asset_id]
        self.interdep_df['child_id'] = [asset2id_child[a] for a in
                                        self.interdep_df.target_asset_id]
        parent_df = self.datastore.parent.read_df('risk_by_event', 'event_id')
        child_df = self.datastore.read_df('risk_by_event', 'event_id')

        child_df = child_df.rename(
            columns={'non_operational': 'non_operational_orig'})
        child_df['non_operational_inter'] = 0

        for i, row in self.interdep_df.iterrows():
            # Find events where the source assets in in the
            # triggering damage/functionality state
            source_mask = (
                (parent_df.agg_id == row.parent_id) &
                (parent_df[row.col] == 1)
                )
            selected_events = parent_df.index[source_mask].unique()

            # Set the target asset as non-operational for those events
            target_mask = (
                (child_df.agg_id == row.child_id) &
                child_df.index.isin(selected_events)
                )
            child_df.loc[target_mask, 'non_operational_inter'] = 1

        child_df['non_operational'] = numpy.maximum(
            child_df['non_operational_orig'].to_numpy(),
            child_df['non_operational_inter'].to_numpy())

        # Correct the total values per event
        total_agg_id = child_df.agg_id.max()
        asset_mask = child_df.agg_id != total_agg_id
        total_mask = child_df.agg_id == total_agg_id

        inter_totals = (
            child_df.loc[asset_mask]
            .groupby(level='event_id')['non_operational_inter']
            .sum()
        )
        nonop_totals = (
            child_df.loc[asset_mask]
            .groupby(level='event_id')['non_operational']
            .sum()
        )

        child_df.loc[total_mask, 'non_operational_inter'] = (
            child_df.loc[total_mask].index.map(inter_totals)
        )

        child_df.loc[total_mask, 'non_operational'] = (
            child_df.loc[total_mask].index.map(nonop_totals)
        )

        # Storing new columns in the dstore
        self.datastore['risk_by_event/non_operational'][:] = (
            child_df['non_operational'])
        self.datastore['risk_by_event/non_operational_orig'] = (
            child_df['non_operational_orig'])
        self.datastore['risk_by_event/non_operational_inter'] = (
            child_df['non_operational_inter'])

    def _store_connectivity_analysis_results(self, conn_results, prefix='infra'):
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
                prefix+'-avg_loss', pandas.DataFrame(data=avg_dict),
                display_name=DISPLAY_NAME['infra-avg_loss'])
        if 'event_connectivity_loss_eff' in conn_results:
            self.datastore.create_df(
                prefix+'-event_efl',
                conn_results['event_connectivity_loss_eff'],
                display_name=DISPLAY_NAME['infra-event_efl'])
        if 'event_connectivity_loss_pcl' in conn_results:
            self.datastore.create_df(
                prefix+'-event_pcl',
                conn_results['event_connectivity_loss_pcl'],
                display_name=DISPLAY_NAME['infra-event_pcl'])
        if 'event_connectivity_loss_wcl' in conn_results:
            self.datastore.create_df(
                prefix+'-event_wcl',
                conn_results['event_connectivity_loss_wcl'],
                display_name=DISPLAY_NAME['infra-event_wcl'])
        if 'event_connectivity_loss_ccl' in conn_results:
            self.datastore.create_df(
                prefix+'-event_ccl',
                conn_results['event_connectivity_loss_ccl'],
                display_name=DISPLAY_NAME['infra-event_ccl'])
        if 'taz_cl' in conn_results:
            self.datastore.create_df(
                prefix+'-taz_cl',
                conn_results['taz_cl'],
                display_name=DISPLAY_NAME['infra-taz_cl'])
        if 'dem_cl' in conn_results:
            self.datastore.create_df(
                prefix+'-dem_cl',
                conn_results['dem_cl'],
                display_name=DISPLAY_NAME['infra-dem_cl'])
        if 'node_el' in conn_results:
            self.datastore.create_df(
                prefix+'-node_el',
                conn_results['node_el'],
                display_name=DISPLAY_NAME['infra-node_el'])
