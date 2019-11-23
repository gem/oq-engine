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
import csv
import logging
import numpy
import shapely
from openquake.baselib import hdf5, general
from openquake.hazardlib import valid, geo, InvalidFile
from openquake.calculators import base
from openquake.calculators.extract import extract

U16 = numpy.uint16
F32 = numpy.float32
F64 = numpy.float64


def get_dmg_csq(crm, assets_by_site, gmf):
    """
    :param crm: a CompositeRiskModel object
    :param assets_by_site: a list of arrays per each site
    :param gmf: a ground motion field
    :returns:
        an array of shape (A, L, 1, D + 1) with the number of buildings
        in each damage state for each asset and loss type
    """
    A = sum(len(assets) for assets in assets_by_site)
    L = len(crm.loss_types)
    D = len(crm.damage_states)
    out = numpy.zeros((A, L, 1, D + 1), F32)
    for assets, gmv in zip(assets_by_site, gmf):
        group = general.group_array(assets, 'taxonomy')
        for taxonomy, assets in group.items():
            for l, loss_type in enumerate(crm.loss_types):
                # NB: risk logic trees are not yet supported in multi_risk
                [rm], [w] = crm.get_rmodels_weights(taxonomy)
                fracs = rm.scenario_damage(loss_type, assets, [gmv])
                for asset, frac in zip(assets, fracs):
                    dmg = asset['number'] * frac  # shape (1, D)
                    csq = crm.compute_csq(asset, frac, loss_type)
                    out[asset['ordinal'], l, 0, :D] = dmg
                    out[asset['ordinal'], l, 0, D] = csq['losses']
    return out


def build_asset_risk(assetcol, dmg_csq, hazard, loss_types, damage_states,
                     perils, binary_perils):
    # dmg_csq has shape (A, R, L, 1, D + 1)
    dtlist = []
    field2tup = {}
    occupants = [name for name in assetcol.array.dtype.names
                 if name.startswith('occupants') and
                 not name.endswith('_None')]
    for name, dt in assetcol.array.dtype.descr:
        if name not in {'area', 'occupants_None', 'ordinal'}:
            dtlist.append((name, dt))
    dtlist.sort()
    if not loss_types:  # missing ASH
        loss_types = ['structural']  # for LAVA, LAHAR, PYRO
    for l, loss_type in enumerate(loss_types):
        for d, ds in enumerate(damage_states + ['loss']):
            for p, peril in enumerate(perils):
                field = ds + '-' + loss_type + '-' + peril
                field2tup[field] = (p, l, 0, d)
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
            arr[field] = dmg_csq[(slice(None),) + field2tup[field]]
    # computed losses and fatalities for binary_perils
    for rec in arr:
        haz = hazard[rec['site_id']]
        for loss_type in loss_types:
            value = rec['value-' + loss_type]
            for peril in binary_perils:
                rec['loss-%s-%s' % (loss_type, peril)] = haz[peril] * value
        for occupant in occupants:
            occ = rec[occupant]
            for peril in binary_perils:
                rec[occupant + '-' + peril] = haz[peril] * occ
        for peril in binary_perils:
            rec['number-' + peril] = haz[peril] * rec['number']
    return arr


def csv2peril(fname, name, sitecol, tofloat, asset_hazard_distance):
    """
    Converts a CSV file into a peril array of length N
    """
    data = []
    with open(fname) as f:
        for row in csv.DictReader(f):
            intensity = tofloat(row['intensity'])
            if intensity > 0:
                data.append((valid.longitude(row['lon']),
                             valid.latitude(row['lat']),
                             intensity))
    data = numpy.array(data, [('lon', float), ('lat', float),
                              ('number', float)])
    logging.info('Read %s with %d rows' % (fname, len(data)))
    if len(data) != len(numpy.unique(data[['lon', 'lat']])):
        raise InvalidFile('There are duplicated points in %s' % fname)
    try:
        distance = asset_hazard_distance[name]
    except KeyError:
        distance = asset_hazard_distance['default']
    sites, filtdata, _discarded = geo.utils.assoc(
        data, sitecol, distance, 'filter')
    peril = numpy.zeros(len(sitecol), float)
    peril[sites.sids] = filtdata['number']
    return peril


def wkt2peril(fname, name, sitecol):
    """
    Converts a WKT file into a peril array of length N
    """
    with open(fname) as f:
        header = next(f)  # skip header
        if header != 'geom\n':
            raise ValueError('%s has header %r, should be geom instead' %
                             (fname, header))
        wkt = f.read()
        if not wkt.startswith('"'):
            raise ValueError('The geometry must be quoted in %s : "%s..."' %
                             (fname, wkt.split('(')[0]))
        geom = shapely.wkt.loads(wkt.strip('"'))  # strip quotes
    peril = numpy.zeros(len(sitecol), float)
    for sid, lon, lat in sitecol.complete.array[['sids', 'lon', 'lat']]:
        peril[sid] = shapely.geometry.Point(lon, lat).within(geom)
    return peril


@base.calculators.add('multi_risk')
class MultiRiskCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = None  # no parallel
    is_stochastic = True

    def save_multi_peril(self):
        """
        Read the hazard fields as csv files, associate them to the sites
        and create the `hazard` dataset.
        """
        oq = self.oqparam
        perils, fnames = zip(*oq.inputs['multi_peril'].items())
        dt = [(haz, float) for haz in perils]
        N = len(self.sitecol)
        self.datastore['multi_peril'] = z = numpy.zeros(N, dt)
        for name, fname in zip(perils, fnames):
            tofloat = (valid.positivefloat if name == 'ASH'
                       else valid.probability)
            with open(fname) as f:
                header = next(f)
            if 'geom' in header:
                peril = wkt2peril(fname, name, self.sitecol)
            else:
                peril = csv2peril(fname, name, self.sitecol, tofloat,
                                  oq.asset_hazard_distance)
            if peril.sum() == 0:
                logging.warning('No sites were affected by %s' % name)
            self.datastore['multi_peril'][name] = peril
        self.datastore.set_attrs('multi_peril', nbytes=z.nbytes)

    def execute(self):
        dstates = self.crmodel.damage_states
        ltypes = self.crmodel.loss_types
        theperils = self.oqparam.inputs['multi_peril']
        P = len(theperils) + 1
        L = len(ltypes)
        D = len(dstates)
        A = len(self.assetcol)
        ampl = self.oqparam.ash_wet_amplification_factor
        dmg_csq = numpy.zeros((A, P, L, 1, D + 1), F32)
        perils = []
        if 'ASH' in theperils:
            assets = self.assetcol.assets_by_site()
            gmf = self.datastore['multi_peril']['ASH']
            dmg_csq[:, 0] = get_dmg_csq(self.crmodel, assets, gmf)
            perils.append('ASH_DRY')
            dmg_csq[:, 1] = get_dmg_csq(self.crmodel, assets, gmf * ampl)
            perils.append('ASH_WET')
        hazard = self.datastore['multi_peril']
        binary_perils = []
        for peril in theperils:
            if peril != 'ASH':
                binary_perils.append(peril)
        self.datastore['asset_risk'] = arr = build_asset_risk(
            self.assetcol, dmg_csq, hazard, ltypes, dstates,
            perils, binary_perils)
        self.all_perils = perils + binary_perils
        return arr

    def get_fields(self, cat):
        return [cat + '-' + peril for peril in self.all_perils]

    def post_execute(self, arr):
        """
        Compute aggregated risk
        """
        md = extract(self.datastore, 'exposure_metadata')
        categories = [cat.replace('value-', 'loss-') for cat in md] + [
            ds + '-structural' for ds in self.crmodel.damage_states]
        multi_risk = list(md.array)
        multi_risk += sorted(
            set(arr.dtype.names) -
            set(self.datastore['assetcol/array'].dtype.names))
        tot = {risk: arr[risk].sum() for risk in multi_risk}
        cats = []
        values = []
        for cat in categories:
            val = [tot.get(f, numpy.nan) for f in self.get_fields(cat)]
            if not numpy.isnan(val).all():
                cats.append(cat)
                values.append(val)
        dt = [('peril', hdf5.vstr)] + [(c, float) for c in cats]
        agg_risk = numpy.zeros(len(self.all_perils), dt)
        for cat, val in zip(cats, values):
            agg_risk[cat] = val
        agg_risk['peril'] = self.all_perils
        self.datastore['agg_risk'] = agg_risk
