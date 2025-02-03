# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import json
import numpy
import pandas
from openquake.baselib import hdf5, general
from openquake.calculators import base
from openquake.calculators.extract import extract

U16 = numpy.uint16
F32 = numpy.float32
F64 = numpy.float64


def get_dmg_csq(crm, assets_by_site, gmf, time_event):
    """
    :param crm: a CompositeRiskModel object
    :param assets_by_site: a dictionary of arrays per each site
    :param gmf: a ground motion field
    :param time_event: used in when the occupancy depend on the time (the
        default is avg)
    :returns:
        an array of shape (A, L, D + 1) with the number of buildings
        in each damage state for each asset and loss type
    """
    A = sum(len(assets) for assets in assets_by_site.values())
    L = len(crm.loss_types)
    D = len(crm.damage_states)
    out = numpy.zeros((A, L, D + 1), F32)
    for sid, assets in assets_by_site.items():
        gmv = gmf[sid]
        group = general.group_array(assets, 'taxonomy')
        for taxonomy, assets in group.items():
            number = assets['value-number']
            ordinal = assets['ordinal']
            dd5 = numpy.zeros((1, len(assets), 1, L, D), F32)  # 1 peril, 1 event
            # NB: assuming trivial taxonomy mapping for multi_risk
            df = crm.tmap_df[crm.tmap_df.taxi == taxonomy]
            [rm] = [crm._riskmodels[k] for k, w in zip(df.risk_id, df.weight)]
            [sec_imt] = rm.imt_by_lt.values()
            for li, loss_type in enumerate(crm.loss_types):
                dd5[:, :, :, li] = rm.scenario_damage(
                    'groundshaking', loss_type, assets,
                    pandas.DataFrame({sec_imt: [gmv]}))
            csq = crm.compute_csq(assets, dd5, df, crm.oqparam)  # ->PAE
            for li in range(L):
                # shape (A, 1) times (A, D) has shape (A, D)
                out[ordinal, li, :D] = number[:, None] * dd5[0, :, 0, li]
                out[ordinal, li, D] = csq['losses', li][0, :, 0]
    return out  # (A, L, D+1)


def build_asset_risk(assetcol, dmg_csq, hazard, loss_types, damage_states,
                     perils, binary_perils):
    # dmg_csq has shape (P, A, R, L, D + 1)
    dtlist = []
    field2tup = {}
    occupants = [name for name in assetcol.array.dtype.names
                 if name.startswith('occupants') and not
                 name.startswith('occupants_avg')]
    for name, dt in assetcol.array.dtype.descr:
        if name not in {'occupants_avg', 'ordinal', 'id', 'ideductible'}:
            dtlist.append((name, dt))
    dtlist.sort()
    dtlist.insert(0, ('id', '<S100'))
    if not loss_types:  # missing ASH
        loss_types = ['structural']  # for LAVA, LAHAR, PYRO
    for li, loss_type in enumerate(loss_types):
        for d, ds in enumerate(damage_states + ['loss']):
            for p, peril in enumerate(perils):
                field = ds + '-' + loss_type + '-' + peril
                # i.e. field = 'no_damage-structural-ASH_DRY'
                field2tup[field] = (p, slice(None), li, d)
                dtlist.append((field, F32))
        for peril in binary_perils:
            dtlist.append(('loss-' + loss_type + '-' + peril, F32))
    for peril in binary_perils:
        for occ in occupants:
            dtlist.append((occ + '-' + peril, F32))
        dtlist.append(('number-' + peril, F32))
    arr = numpy.zeros(len(assetcol), dtlist)
    for field, _ in dtlist:
        if field in assetcol.array.dtype.fields:
            arr[field] = assetcol.array[field]
        elif field in field2tup:  # dmg_csq field
            arr[field] = dmg_csq[field2tup[field]]
    # computed losses and fatalities for binary_perils
    for rec in arr:
        haz = hazard.loc[rec['site_id']]
        for loss_type in loss_types:
            value = rec['value-' + loss_type]
            for peril in binary_perils:
                rec['loss-%s-%s' % (loss_type, peril)] = haz[peril] * value
        for occupant in occupants:
            occ = rec[occupant]
            for peril in binary_perils:
                rec[occupant + '-' + peril] = haz[peril] * occ
        for peril in binary_perils:
            rec['number-' + peril] = haz[peril] * rec['value-number']
    return arr


@base.calculators.add('multi_risk')
class MultiRiskCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = None  # no parallel
    is_stochastic = True

    def execute(self):
        """
        Compute the perils without any parallelization
        """
        dstates = self.crmodel.damage_states
        ltypes = self.crmodel.loss_types
        multi_peril = self.oqparam.inputs['multi_peril']
        P = len(multi_peril) + 1
        L = len(ltypes)
        D = len(dstates)
        A = len(self.assetcol)
        ampl = self.oqparam.ash_wet_amplification_factor
        dmg_csq = numpy.zeros((P, A, L, D + 1), F32)
        perils = []
        if 'ASH' in multi_peril:
            assets = general.group_array(self.assetcol, 'site_id')
            gmf = self.datastore['gmf_data/ASH'][:]
            dmg_csq[0] = get_dmg_csq(self.crmodel, assets, gmf,
                                     self.oqparam.time_event)
            dmg_csq[1] = get_dmg_csq(self.crmodel, assets, gmf * ampl,
                                     self.oqparam.time_event)
            perils.append('ASH_DRY')
            perils.append('ASH_WET')
        hazard = self.datastore.read_df('gmf_data', 'sid')
        binary_perils = []
        for peril in multi_peril:
            if peril != 'ASH':
                binary_perils.append(peril)
        self.datastore['asset_risk'] = arr = build_asset_risk(
            self.assetcol, dmg_csq, hazard, ltypes, dstates, perils, binary_perils)
        self.all_perils = perils + binary_perils
        return arr

    def post_execute(self, arr):
        """
        Compute aggregated risk
        """
        md = json.loads(extract(self.datastore, 'exposure_metadata').json)
        categories = [n.replace('value-', 'loss-') for n in md['names']] + [
            ds + '-structural' for ds in self.crmodel.damage_states]
        multi_risk = md['names']
        multi_risk += sorted(
            set(arr.dtype.names) -
            set(self.datastore['assetcol/array'].dtype.names))
        tot = {risk: arr[risk].sum() for risk in multi_risk}
        cats = []
        values = []
        for cat in categories:
            fields = [cat + '-' + peril for peril in self.all_perils]
            val = [tot.get(f, numpy.nan) for f in fields]
            if not numpy.isnan(val).all():
                cats.append(cat)
                values.append(val)
        dt = [('peril', hdf5.vstr)] + [(c, float) for c in cats]
        agg_risk = numpy.zeros(len(self.all_perils), dt)
        for cat, val in zip(cats, values):
            agg_risk[cat] = val
        agg_risk['peril'] = self.all_perils
        self.datastore['agg_risk'] = agg_risk
