#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
import operator
import itertools
import collections

import numpy

from openquake.baselib.general import AccumDict
from openquake.commonlib.export import export
from openquake.commonlib import writers, risk_writers, riskmodels
from openquake.commonlib.writers import scientificformat
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.risk_writers import (
    DmgState, DmgDistPerTaxonomy, DmgDistPerAsset, DmgDistTotal,
    ExposureData, Site)

Output = collections.namedtuple('Output', 'ltype path array')


# ########################## utility functions ############################## #

def compose_arrays(a1, a2):
    """
    Compose composite arrays by generating an extended datatype containing
    all the fields. The two arrays must have the same length.
    """
    assert len(a1) == len(a2),  (len(a1), len(a2))
    fields1 = [(f, a1.dtype.fields[f][0]) for f in a1.dtype.names]
    if a2.dtype.names is None:  # the second array is not composite
        assert len(a2.shape) == 2, a2.shape
        width = a2.shape[1]
        fields2 = [('value%d' % i, a2.dtype) for i in range(width)]
        composite = numpy.zeros(a1.shape, numpy.dtype(fields1 + fields2))
        for f1 in dict(fields1):
            composite[f1] = a1[f1]
        for i in range(width):
            composite['value%d' % i] = a2[:, i]
        return composite

    fields2 = [(f, a2.dtype.fields[f][0]) for f in a2.dtype.names]
    composite = numpy.zeros(a1.shape, numpy.dtype(fields1 + fields2))
    for f1 in dict(fields1):
        composite[f1] = a1[f1]
    for f2 in dict(fields2):
        composite[f2] = a2[f2]
    return composite

asset_dt = numpy.dtype(
    [('asset_ref', bytes, 20), ('lon', float), ('lat', float)])


def get_assets(dstore):
    """
    :param dstore: a datastore with a key `specific_assets`
    :returns: an ordered array of records (asset_ref, lon, lat)
    """
    assets = sorted(sum(map(list, dstore['assets_by_site']), []),
                    key=operator.attrgetter('id'))
    asset_data = numpy.array(
        [(asset.id, asset.location[0], asset.location[1])
         for asset in assets], asset_dt)
    return asset_data


def get_assets_sites(dstore):
    """
    :param dstore: a datastore with a key `specific_assets`
    :returns: an ordered array of records (asset_ref, lon, lat)
    """
    assetcol = dstore['assetcol']
    sitemesh = dstore['sitemesh']
    rows = []
    for asset in assetcol:
        loc = sitemesh[asset['site_id']]
        rows.append((asset['asset_ref'], loc[0], loc[1]))
    return numpy.array(rows, asset_dt)


def extract_outputs(dkey, dstore, root='', ext=''):
    """
    An utility to extract outputs ordered by loss types from a datastore
    containing nested structures as follows:

    >>> dstore = {
    ...     'risk_output':
    ...        {'structural':
    ...            {'b1': numpy.array([[0.10, 0.20], [0.30, 0.40]]),
    ...             'b2': numpy.array([[0.12, 0.22], [0.33, 0.44]]),
    ...            }}}
    >>> outputs = extract_outputs('risk_output', dstore)
    >>> [o.path for o in outputs]
    ['risk_output-structural-b1', 'risk_output-structural-b2']
    >>> [o.ltype for o in outputs]
    ['structural', 'structural']
    """
    group = dstore[dkey]
    dashkey = dkey.replace('/', '-')
    if root and not root.endswith('/'):
        root += '/'
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    outputs = []
    for ltype in sorted(group):
        subgroup = group[ltype]
        for key in subgroup:
            path = '%s%s-%s-%s%s' % (root, dashkey, ltype, key, ext)
            outputs.append(Output(ltype, path, subgroup[key][:]))
    return outputs

# ############################### exporters ############################## #


# this is used by classical_risk from csv
@export.add(('avg_losses', 'csv'))
def export_avg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    avg_losses = dstore[ekey[0] + '/rlzs']
    rlzs = dstore['rlzs_assoc'].realizations
    assets = get_assets(dstore)
    columns = 'asset_ref lon lat avg_loss~structural ins_loss~structural' \
        .split()
    fnames = []
    for rlz, losses in zip(rlzs, avg_losses):
        dest = os.path.join(
            dstore.export_dir, 'rlz-%03d-avg_loss.csv' % rlz.ordinal)
        data = compose_arrays(assets, losses)
        writers.write_csv(dest, data, fmt='%10.6E', header=columns)
        fnames.append(dest)
    return fnames


# alternative export format for the average losses, used by the platform
@export.add(('avglosses-rlzs', 'csv'))
def export_avglosses_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    outs = extract_outputs(ekey[0], dstore, dstore.export_dir, ekey[1])
    sitemesh = dstore['sitemesh']
    assetcol = dstore['assetcol']
    header = ['lon', 'lat', 'asset_ref', 'asset_value', 'average_loss',
              'stddev_loss', 'loss_type']
    for out in outs:
        rows = []
        for asset, loss in zip(assetcol, out.array):
            loc = sitemesh[asset['site_id']]
            row = [loc['lon'], loc['lat'], asset['asset_ref'],
                   asset[out.ltype], loss, numpy.nan, out.ltype]
            rows.append(row)
        writers.write_csv(out.path, [header] + rows)
    return [out.path for out in outs]


# NB: agg_avgloss_rlzs is not exported on purpose, but it can be shown:
# oq-lite show <calc_id> agg_avgloss_rlzs


@export.add(
    ('avg_losses-rlzs', 'csv'),
    ('avg_losses-stats', 'csv'),
    ('rcurves-rlzs', 'csv'),
    ('icurves-rlzs', 'csv'),
    ('rcurves-stats', 'csv'),
    ('icurves-stats', 'csv'),
)
def export_ebr(ekey, dstore):
    assets = get_assets_sites(dstore)
    outs = extract_outputs(ekey[0], dstore, dstore.export_dir, ekey[1])
    for out in outs:
        writers.write_csv(
            out.path, compose_arrays(assets, out.array), fmt='%9.7E')
    return [out.path for out in outs]


@export.add(
    ('specific-loss_curves-rlzs', 'csv'),
    ('specific-ins_curves-rlzs', 'csv'),
    ('specific-loss_maps-rlzs', 'csv'),
    ('specific-loss_curves-stats', 'csv'),
    ('specific-ins_curves-stats', 'csv'),
    ('specific-loss_maps-stats', 'csv'),
)
def export_ebr_specific(ekey, dstore):
    all_assets = get_assets_sites(dstore)
    spec_assets = all_assets[dstore['spec_indices'].value]
    outs = extract_outputs(ekey[0], dstore, dstore.export_dir, ekey[1])
    for out in outs:
        arr = compose_arrays(spec_assets, out.array)
        writers.write_csv(out.path, arr, fmt='%9.7E')
    return [out.path for out in outs]


@export.add(('agg_losses-rlzs', 'csv'), ('agg_losses-stats', 'csv'))
def export_agg_losses(ekey, dstore):
    tags = dstore['tags']
    outs = extract_outputs(ekey[0], dstore, dstore.export_dir, ekey[1])
    header = ['rupture_tag', 'aggregate_loss', 'insured_loss']
    for out in outs:
        data = [[tags[rec['rup_id']], rec['loss'], rec['ins_loss']]
                for rec in out.array]
        writers.write_csv(out.path, sorted(data), fmt='%9.7E', header=header)
    return [out.path for out in outs]


@export.add(('dmg_by_asset', 'xml'))
def export_damage(ekey, dstore):
    riskmodel = dstore['riskmodel']
    rlzs = dstore['rlzs_assoc'].realizations
    dmg_by_asset = dstore['dmg_by_asset']  # shape (N, L, R)
    assetcol = dstore['assetcol']
    sitemesh = dstore['sitemesh']
    dmg_states = [DmgState(s, i)
                  for i, s in enumerate(riskmodel.damage_states)]
    D = len(dmg_states)
    N, R = dmg_by_asset.shape
    L = len(riskmodel.loss_types)
    fnames = []

    for l, r in itertools.product(range(L), range(R)):
        lt = riskmodel.loss_types[l]
        rlz = rlzs[r]
        suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (rlz.uid, lt)

        dd_asset = []
        for n in range(N):
            aref = assetcol[n]['asset_ref']
            dist = dmg_by_asset[n, r][lt]
            point = sitemesh[assetcol[n]['site_id']]
            site = Site(point['lon'], point['lat'])
            for ds in range(D):
                dd_asset.append(
                    DmgDistPerAsset(
                        ExposureData(aref, site), dmg_states[ds],
                        dist['mean'][ds], dist['stddev'][ds]))

        f1 = export_dmg_xml(('dmg_dist_per_asset', 'xml'), dstore.export_dir,
                            dmg_states, dd_asset, suffix)
        max_damage = dmg_states[-1]
        # the collapse map is extracted from the damage distribution per asset
        # (dda) by taking the value corresponding to the maximum damage
        collapse_map = [dda for dda in dd_asset if dda.dmg_state == max_damage]
        f2 = export_dmg_xml(('collapse_map', 'xml'), dstore.export_dir,
                            dmg_states, collapse_map, suffix)
        fnames.extend(sum((f1 + f2).values(), []))
    return sorted(fnames)


@export.add(('dmg_by_taxon', 'xml'))
def export_damage_taxon(ekey, dstore):
    riskmodel = dstore['riskmodel']
    rlzs = dstore['rlzs_assoc'].realizations
    dmg_by_taxon = dstore['dmg_by_taxon']  # shape (T, L, R)
    taxonomies = dstore['taxonomies']
    dmg_states = [DmgState(s, i)
                  for i, s in enumerate(riskmodel.damage_states)]
    D = len(dmg_states)
    T, R = dmg_by_taxon.shape
    L = len(riskmodel.loss_types)
    fnames = []

    for l, r in itertools.product(range(L), range(R)):
        lt = riskmodel.loss_types[l]
        rlz = rlzs[r]
        suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (rlz.uid, lt)

        dd_taxo = []
        for t in range(T):
            dist = dmg_by_taxon[t, r][lt]
            for ds in range(D):
                dd_taxo.append(
                    DmgDistPerTaxonomy(
                        taxonomies[t], dmg_states[ds],
                        dist['mean'][ds], dist['stddev'][ds]))

        f = export_dmg_xml(('dmg_dist_per_taxonomy', 'xml'),
                           dstore.export_dir, dmg_states, dd_taxo, suffix)
        fnames.extend(sum(f.values(), []))
    return sorted(fnames)


@export.add(('dmg_total', 'xml'))
def export_damage_total(ekey, dstore):
    riskmodel = dstore['riskmodel']
    rlzs = dstore['rlzs_assoc'].realizations
    dmg_total = dstore['dmg_total']
    R, = dmg_total.shape
    L = len(riskmodel.loss_types)
    dmg_states = [DmgState(s, i)
                  for i, s in enumerate(riskmodel.damage_states)]
    D = len(dmg_states)
    fnames = []
    for l, r in itertools.product(range(L), range(R)):
        lt = riskmodel.loss_types[l]
        rlz = rlzs[r]
        suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (rlz.uid, lt)

        dd_total = []
        for ds in range(D):
            dist = dmg_total[r][lt]
            dd_total.append(DmgDistTotal(
                dmg_states[ds], dist['mean'][ds], dist['stddev'][ds]))

        f = export_dmg_xml(('dmg_dist_total', 'xml'), dstore.export_dir,
                           dmg_states, dd_total, suffix)
        fnames.extend(sum(f.values(), []))
    return sorted(fnames)


def export_dmg_xml(key, export_dir, damage_states, dmg_data, suffix):
    """
    Export damage outputs in XML format.

    :param key:
        dmg_dist_per_asset|dmg_dist_per_taxonomy|dmg_dist_total|collapse_map
    :param export_dir:
        the export directory
    :param damage_states:
        the list of damage states
    :param dmg_data:
        a list [(loss_type, unit, asset_ref, mean, stddev), ...]
    :param suffix:
        a suffix specifying the GSIM realization
    """
    dest = os.path.join(export_dir, '%s%s.%s' % (key[0], suffix, key[1]))
    risk_writers.DamageWriter(damage_states).to_nrml(key[0], dmg_data, dest)
    return AccumDict({key: [dest]})


@export.add(('damages_by_rlz', 'csv'))
def export_classical_damage_csv(ekey, dstore):
    damages_by_rlz = dstore['damages_by_rlz']
    rlzs = dstore['rlzs_assoc'].realizations
    damage_states = dstore['riskmodel'].damage_states
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    fnames = []
    for rlz in rlzs:
        damages = damages_by_rlz[rlz.ordinal]
        fname = 'damage_%d.csv' % rlz.ordinal
        fnames.append(
            _export_classical_damage_csv(
                dstore.export_dir, fname, dmg_states, damages))
    return fnames


def _export_classical_damage_csv(export_dir, fname, damage_states,
                                 fractions_by_asset):
    """
    Export damage fractions in CSV.

    :param export_dir: the export directory
    :param fname: the name of the exported file
    :param damage_states: the damage states
    :fractions_by_asset: a dictionary with the fractions by asset
    """
    dest = os.path.join(export_dir, fname)
    with open(dest, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='|', lineterminator='\n')
        writer.writerow(['asset_ref'] + [ds.dmg_state for ds in damage_states])
        for asset_ref in sorted(fractions_by_asset):
            data = fractions_by_asset[asset_ref]
            writer.writerow([asset_ref] + list(map(scientificformat, data)))
    return dest


# exports for scenario_risk

AggLoss = collections.namedtuple(
    'AggLoss', 'loss_type unit mean stddev')

PerAssetLoss = collections.namedtuple(
    'PerAssetLoss', 'loss_type unit asset_ref mean stddev')


@export.add(('avglosses', 'csv'))
def export_avglosses(ekey, dstore):
    unit_by_lt = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                  for ct in dstore['cost_types']}
    unit_by_lt['fatalities'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    avglosses = dstore['avglosses']
    riskmodel = dstore['riskmodel']
    assets = dstore['assetcol']['asset_ref']
    N, R = avglosses.shape
    L = len(riskmodel.loss_types)
    fnames = []
    for l, lt in enumerate(riskmodel.loss_types):
        alosses = avglosses[lt]
        for r in range(R):
            rlz = rlzs[r]
            lt = riskmodel.loss_types[l]
            unit = unit_by_lt[lt]
            suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (
                rlz.uid, lt)
            losses = [PerAssetLoss(lt, unit, ass, stat['mean'], stat['stddev'])
                      for ass, stat in zip(assets, alosses[:, r])]
            out = export_loss_csv(
                ('avg', 'csv'), dstore.export_dir, losses, suffix)
            fnames.append(out)
    return sorted(fnames)

LossMap = collections.namedtuple('LossMap', 'location asset_ref value std_dev')


# emulate a Django point
class Location(object):
    def __init__(self, xy):
        self.x, self.y = xy
        self.wkt = 'POINT(%s %s)' % tuple(xy)


@export.add(('avglosses', 'xml'), ('avglosses', 'geojson'))
def export_lossmaps_xml_geojson(ekey, dstore):
    oq = OqParam.from_(dstore.attrs)
    unit_by_lt = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                  for ct in dstore['cost_types']}
    unit_by_lt['fatalities'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    avglosses = dstore['avglosses']
    riskmodel = dstore['riskmodel']
    assetcol = dstore['assetcol']
    sitemesh = dstore['sitemesh']
    L = len(riskmodel.loss_types)
    N, R = avglosses.shape
    fnames = []
    export_type = ekey[1]
    writercls = (risk_writers.LossMapGeoJSONWriter
                 if export_type == 'geojson' else
                 risk_writers.LossMapXMLWriter)
    for l, lt in riskmodel.loss_types:
        alosses = avglosses[lt]
        for r in range(R):
            rlz = rlzs[r]
            unit = unit_by_lt[lt]
            suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (
                rlz.uid, lt)
            fname = os.path.join(
                dstore.export_dir, '%s%s.%s' % (ekey[0], suffix, ekey[1]))
            data = []
            for ass, stat in zip(assetcol, alosses[:, r]):
                loc = Location(sitemesh[ass['site_id']])
                lm = LossMap(loc, ass['asset_ref'],
                             stat['mean'], stat['stddev'])
                data.append(lm)
            writer = writercls(
                fname, oq.investigation_time, poe=None, loss_type=lt,
                gsim_tree_path=None, unit=unit, loss_category=None)
            # TODO: replace the category with the exposure category
            writer.serialize(data)
            fnames.append(fname)
    return sorted(fnames)


@export.add(('agglosses', 'csv'))
def export_agglosses(ekey, dstore):
    unit_by_lt = {riskmodels.cost_type_to_loss_type(ct['name']): ct['unit']
                  for ct in dstore['cost_types']}
    unit_by_lt['fatalities'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    agglosses = dstore['agglosses']
    riskmodel = dstore['riskmodel']
    L = len(riskmodel.loss_types)
    R, = agglosses.shape
    fnames = []
    for lt in riskmodel.loss_types:
        for r in range(R):
            rlz = rlzs[r]
            unit = unit_by_lt[lt]
            suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (
                rlz.uid, lt)
            loss = agglosses[r][lt]
            losses = [AggLoss(lt, unit, loss['mean'], loss['stddev'])]
            out = export_loss_csv(
                ('agg', 'csv'), dstore.export_dir, losses, suffix)
            fnames.append(out)
    return sorted(fnames)


def export_loss_csv(key, export_dir, data, suffix):
    """
    Export (aggregate) losses in CSV.

    :param key: per_asset_loss|asset-ins
    :param export_dir: the export directory
    :param data: a list [(loss_type, unit, asset_ref, mean, stddev), ...]
    :param suffix: a suffix specifying the GSIM realization
    """
    dest = os.path.join(export_dir, '%s%s.%s' % (key[0], suffix, key[1]))
    if key[0] in ('agg', 'ins'):  # aggregate
        header = ['LossType', 'Unit', 'Mean', 'Standard Deviation']
    else:
        header = ['LossType', 'Unit', 'Asset', 'Mean', 'Standard Deviation']
        data.sort(key=operator.itemgetter(2))  # order by asset_ref
    writers.write_csv(dest, [header] + data, fmt='%11.7E')
    return dest


@export.add(('assetcol', 'csv'))
def export_assetcol(ekey, dstore):
    assetcol = dstore[ekey[0]].value
    sitemesh = dstore['sitemesh'].value
    taxonomies = dstore['taxonomies'].value
    header = list(assetcol.dtype.names)
    dest = os.path.join(dstore.export_dir, '%s.%s' % ekey)
    columns = [None] * len(header)
    for i, field in enumerate(header):
        if field == 'taxonomy':
            columns[i] = taxonomies[assetcol[field]]
        elif field == 'site_id':
            header[i] = 'lon_lat'
            columns[i] = sitemesh[assetcol[field]]
        else:
            columns[i] = assetcol[field]
    writers.write_csv(dest, [header] + list(zip(*columns)), fmt='%s')
    return [dest]
