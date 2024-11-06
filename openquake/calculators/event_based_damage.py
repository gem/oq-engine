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
from dataclasses import dataclass
import numpy
import pandas

from openquake.baselib import hdf5, general
from openquake.hazardlib.stats import set_rlzs_stats
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

@dataclass
class Dparam:
    """
    Parameters for a damage calculation
    """
    eids: U32
    aggids: U16
    csqidx: dict
    D: int
    Dc: int
    rng: scientific.MultiEventRNG


def zero_dmgcsq(A, R, crmodel):
    """
    :returns: an array of zeros of shape (A, R, Dc)
    """
    dmg_csq = crmodel.get_dmg_csq()
    Dc = len(dmg_csq) + 1  # damages + consequences
    return numpy.zeros((A, R, Dc), F32)


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


def _gen_dd3(asset_df, gmf_df, crmodel, dparam, mon):
    # yields (aids, dd3) triples

    # this part is ultra-fast, even for discrete damage distributions
    oq = crmodel.oqparam
    sec_sims = oq.secondary_simulations.items()
    for prob_field, num_sims in sec_sims:
        probs = gmf_df[prob_field].to_numpy()   # LiqProb
        if not oq.float_dmg_dist:
            dprobs = dparam.rng.boolean_dist(probs, num_sims).mean(axis=1)

    # this part is ultra-slow, especially for discrete damage distributions
    E = len(dparam.eids)
    P = len(crmodel.perils)
    [lt] = oq.loss_types  # assume single loss type
    for taxo, adf in asset_df.groupby('taxonomy'):
        with mon:
            outs = crmodel.get_outputs(adf, gmf_df)  # dicts loss_type -> array
            aids = adf.index.to_numpy()
            A = len(aids)
            assets = adf.to_records()
            if oq.float_dmg_dist:
                number = assets['value-number']
            else:
                number = assets['value-number'] = U32(assets['value-number'])
            dd4 = numpy.zeros((P, A, E, dparam.Dc), F32)
            D = dparam.D
            for p, out in enumerate(outs):
                fractions = out[lt]
                if oq.float_dmg_dist:
                    for a in range(A):
                        dd4[p, a, :, :D] = fractions[a] * number[a]
                else:
                    # this is a performance distaster; for instance
                    # the Messina test in oq-risk-tests becomes 12x
                    # slower even if it has only 25_736 assets
                    dd4[p, :, :, :D] = dparam.rng.discrete_dmg_dist(
                        dparam.eids, fractions, number)

                # secondary perils and consequences
                for a, asset in enumerate(assets):
                    if sec_sims:
                        for d in range(1, D):
                            # doing the mean on the secondary simulations
                            if oq.float_dmg_dist:
                                dd4[p, a, :, d] *= probs
                            else:
                                dd4[p, a, :, d] *= dprobs

            df = crmodel.tmap_df[crmodel.tmap_df.taxi == assets[0]['taxonomy']]
            if P > 1:
                # compose damage distributions
                dd3 = numpy.empty(dd4.shape[1:])
                for a in range(A):
                    for e in range(E):
                        dd3[a, e, :D] = scientific.compose_dds(dd4[:, a, e, :D])
            else:
                dd3 = dd4[0]
            csq = crmodel.compute_csq(assets, dd4[:, :, :, :D], df, oq)
            for name, values in csq.items():
                dd3[:, :, dparam.csqidx[name]] = values
        yield aids, dd3  # dd3 has shape (A, E, Dc)


def event_based_damage(df, oq, dstore, monitor):
    """
    :param df: a DataFrame of GMFs with fields sid, eid, gmv_X, ...
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
    dmg_csq = crmodel.get_dmg_csq()
    csqidx = {dc: i + 1 for i, dc in enumerate(dmg_csq)}
    dmgcsq = zero_dmgcsq(len(assetcol), oq.R, crmodel)
    _A, R, Dc = dmgcsq.shape
    D = Dc - len(crmodel.get_consequences())
    rlzs = dstore['events']['rlz_id']
    dddict = general.AccumDict(accum=numpy.zeros(Dc, F32))  # eid, kid
    for sid, asset_df in assetcol.to_dframe().groupby('site_id'):
        # working one site at the time
        gmf_df = df[df.sid == sid]
        if len(gmf_df) == 0:
            continue
        oq = crmodel.oqparam
        eids = gmf_df.eid.to_numpy()
        if oq.secondary_simulations or not oq.float_dmg_dist:
            rng = scientific.MultiEventRNG(
                oq.master_seed, numpy.unique(eids))
        else:
            rng = None
        dparam = Dparam(eids, aggids, csqidx, D, Dc, rng)
        for aids, dd3 in _gen_dd3(asset_df, gmf_df, crmodel, dparam, mon):
            if R == 1:  # possibly because of collect_rlzs
                dmgcsq[aids, 0] += dd3.sum(axis=1)
            else:
                for e, rlz in enumerate(rlzs[eids]):
                    dmgcsq[aids, rlz] += dd3[:, e]
            tot = dd3.sum(axis=0)  # sum on the assets
            for e, eid in enumerate(eids):
                dddict[eid, oq.K] += tot[e]
                if oq.K:
                    for kids in dparam.aggids:
                        for a, aid in enumerate(aids):
                            dddict[eid, kids[aid]] += dd3[a, e]
    try:
        [lt] = oq.loss_types
    except ValueError:
        lt = oq.total_losses
    return _dframe(dddict, csqidx, [lt]), dmgcsq


def _dframe(dddic, csqidx, loss_types):
    # convert {(eid, kid): dd} into a DataFrame (agg_id, event_id, loss_id)
    dic = general.AccumDict(accum=[])
    for (eid, kid), dd in sorted(dddic.items()):
        for li, lt in enumerate(loss_types):
            dic['agg_id'].append(kid)
            dic['event_id'].append(eid)
            dic['loss_id'].append(scientific.LOSSID[lt])
            for cname, ci in csqidx.items():
                dic[cname].append(dd[ci])
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
        self.dmgcsq = zero_dmgcsq(len(self.assetcol), self.R, self.crmodel)
        if oq.K:
            aggids, _ = self.assetcol.build_aggids(
                oq.aggregate_by, oq.max_aggregations)
        else:
            aggids = 0
        smap = calc.starmap_from_gmfs(damage_from_gmfs, oq,
                                      self.datastore, self._monitor)
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
        if self.dmgcsq[:, :, 1:].sum() == 0:
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
        with prc.datastore:
            prc.run(exports='')

        _A, _R, _Dc = self.dmgcsq.shape
        D = len(self.crmodel.damage_states)
        # fix no_damage distribution for events with zero damage
        number = self.assetcol['value-number']
        for r in range(self.R):
            self.dmgcsq[:, r] /= prc.num_events[r]
            self.dmgcsq[:, r, 0] = number - self.dmgcsq[:, r, 1:D].sum(axis=1)

        assert (self.dmgcsq >= 0).all()  # sanity check
        self.datastore['damages-rlzs'] = self.dmgcsq
        set_rlzs_stats(self.datastore,
                       'damages-rlzs',
                       asset_id=self.assetcol['id'],
                       rlz=numpy.arange(self.R),
                       dmg_state=['no_damage'] + self.crmodel.get_dmg_csq())

        if (hasattr(oq, 'infrastructure_connectivity_analysis')
                and oq.infrastructure_connectivity_analysis):

            logging.info('Running connectivity analysis')
            conn_results = connectivity.analysis(self.datastore)
            self._store_connectivity_analysis_results(conn_results)

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
            avg_df = pandas.DataFrame(data=avg_dict)
            self.datastore.create_df(
                'infra-avg_loss', avg_df,
                display_name=DISPLAY_NAME['infra-avg_loss'])
            logging.info(
                'Stored avarage connectivity loss (infra-avg_loss)')
        if 'event_connectivity_loss_eff' in conn_results:
            self.datastore.create_df(
                'infra-event_efl',
                conn_results['event_connectivity_loss_eff'],
                display_name=DISPLAY_NAME['infra-event_efl'])
            logging.info(
                'Stored efficiency loss by event (infra-event_efl)')
        if 'event_connectivity_loss_pcl' in conn_results:
            self.datastore.create_df(
                'infra-event_pcl',
                conn_results['event_connectivity_loss_pcl'],
                display_name=DISPLAY_NAME['infra-event_pcl'])
            logging.info(
                'Stored partial connectivity loss by event (infra-event_pcl)')
        if 'event_connectivity_loss_wcl' in conn_results:
            self.datastore.create_df(
                'infra-event_wcl',
                conn_results['event_connectivity_loss_wcl'],
                display_name=DISPLAY_NAME['infra-event_wcl'])
            logging.info(
                'Stored weighted connectivity loss by event (infra-event_wcl)')
        if 'event_connectivity_loss_ccl' in conn_results:
            self.datastore.create_df(
                'infra-event_ccl',
                conn_results['event_connectivity_loss_ccl'],
                display_name=DISPLAY_NAME['infra-event_ccl'])
            logging.info(
                'Stored complete connectivity loss by event (infra-event_ccl)')
        if 'taz_cl' in conn_results:
            self.datastore.create_df(
                'infra-taz_cl',
                conn_results['taz_cl'],
                display_name=DISPLAY_NAME['infra-taz_cl'])
            logging.info(
                'Stored connectivity loss of TAZ nodes (taz_cl)')
        if 'dem_cl' in conn_results:
            self.datastore.create_df(
                'infra-dem_cl',
                conn_results['dem_cl'],
                display_name=DISPLAY_NAME['infra-dem_cl'])
            logging.info(
                'Stored connectivity loss of demand nodes (dem_cl)')
        if 'node_el' in conn_results:
            self.datastore.create_df(
                'infra-node_el',
                conn_results['node_el'],
                display_name=DISPLAY_NAME['infra-node_el'])
            logging.info(
                'Stored efficiency loss of nodes (node_el)')
