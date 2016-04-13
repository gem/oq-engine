# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

import operator
import itertools
import collections

import numpy

from openquake.baselib.general import AccumDict
from openquake.risklib import scientific
from openquake.commonlib.export import export
from openquake.commonlib import writers, risk_writers
from openquake.commonlib.util import get_assets, compose_arrays

from openquake.commonlib.risk_writers import (
    DmgState, DmgDistPerTaxonomy, DmgDistPerAsset, DmgDistTotal,
    ExposureData, Site)

Output = collections.namedtuple('Output', 'ltype path array')
F32 = numpy.float32
U32 = numpy.uint32


def extract_outputs(dkey, dstore, loss_type=None, ext=''):
    """
    An utility to extract outputs ordered by loss types from a datastore
    containing nested structures as follows:


    >> dstore = {
    ..     'risk_output':
    ..        {'structural':
    ..            {'b1': array N x 2,
    ..             'b2': array N x 2,
    ..            }}}
    >> outputs = extract_outputs('risk_output', dstore)
    >> [o.path for o in outputs]
    ['risk_output-structural-b1', 'risk_output-structural-b2']
    >> [o.ltype for o in outputs]
    ['structural', 'structural']
    """
    group = dstore[dkey]
    dashkey = dkey.replace('-rlzs', '').replace('-stats', '')
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    outputs = []
    for ltype in sorted(group):
        subgroup = group[ltype]
        for key in subgroup:
            for i in 0, 1:
                ins = '_ins' if i else ''
                path = dstore.export_path(
                    '%s-%s-%s%s%s' % (dashkey, ltype, key, ins, ext))
                if loss_type:
                    data = subgroup[key][loss_type][:, i]
                else:
                    data = subgroup[key][:, i]
                outputs.append(Output(ltype, path, data))
    return outputs

# ############################### exporters ############################## #


def compactify(array):
    """
    Compactify a composite array of type (name, N1, N2, N3, 2) into a
    composite array of type (name, N1, N2, (N3, 2)). Works with any number
    of Ns.
    """
    if array.shape[-1] != 2:
        raise ValueError('You can only compactify an array which last '
                         'dimension is 2, got shape %s' % str(array.shape))
    dtype = array.dtype
    pairs = []
    for name in dtype.names:
        dt = dtype.fields[name][0]
        if dt.subdtype is None:
            pairs.append((name, (dt, 2)))
        else:  # this is the case for rcurves
            sdt, shp = dt.subdtype
            pairs.append((name, (sdt, shp + (2,))))
    zeros = numpy.zeros(array.shape[:-1], numpy.dtype(pairs))
    for idx, _ in numpy.ndenumerate(zeros):
        zeros[idx] = array[idx]
    return zeros


# this is used by classical_risk, event_based_risk and scenario_risk
@export.add(('avg_losses-rlzs', 'csv'), ('losses_by_asset', 'csv'))
def export_avg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    avg_losses = dstore[ekey[0]].value
    rlzs = dstore['rlzs_assoc'].realizations
    assets = get_assets(dstore)
    writer = writers.CsvWriter(fmt='%.6E')
    for rlz in rlzs:
        losses = avg_losses[:, rlz.ordinal]
        dest = dstore.export_path('losses_by_asset-rlz%03d.csv' % rlz.ordinal)
        data = compose_arrays(assets, losses)
        writer.save(data, dest)
    return writer.getsaved()


@export.add(('avg_losses-stats', 'csv'))
def export_avg_losses_stats(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    avg_losses = dstore[ekey[0]].value
    quantiles = ['mean'] + ['quantile-%s' % q for q in oq.quantile_loss_curves]
    assets = get_assets(dstore)
    writer = writers.CsvWriter(fmt='%10.6E')
    for i, quantile in enumerate(quantiles):
        losses = avg_losses[:, i]
        dest = dstore.export_path('avg_losses-%s.csv' % quantile)
        data = compose_arrays(assets, losses)
        writer.save(data, dest)
    return writer.getsaved()


# this is used by classical_risk
@export.add(('agg_losses-rlzs', 'csv'))
def export_agg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    agg_losses = compactify(dstore[ekey[0]].value)
    rlzs = dstore['rlzs_assoc'].realizations
    etags = dstore['etags'].value
    writer = writers.CsvWriter(fmt='%10.6E')
    for rlz in rlzs:
        losses = agg_losses[:, rlz.ordinal]
        dest = dstore.export_path('agg_losses-rlz%03d.csv' % rlz.ordinal)
        data = compose_arrays(etags, losses)
        writer.save(data, dest)
    return writer.getsaved()


# this is used by event_based_risk
@export.add(('agg_loss_table', 'csv'))
def export_agg_losses_ebr(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    agg_losses = dstore[ekey[0]]
    etags = dstore['etags'].value
    rlzs = dstore['rlzs_assoc'].realizations
    writer = writers.CsvWriter(fmt='%10.6E')
    for rlz in rlzs:
        for loss_type in loss_types:
            data = agg_losses['rlz-%03d/%s' % (rlz.ordinal, loss_type)].value
            data.sort(order='rup_id')
            dest = dstore.export_path(
                'agg_losses-rlz%03d-%s.csv' % (rlz.ordinal, loss_type))
            tags = etags[data['rup_id']]
            if data.dtype['loss'].shape == (2,):  # insured losses
                losses = data['loss'][:, 0]
                inslosses = data['loss'][:, 1]
                edata = [('event_tag', 'loss', 'loss_ins')] + zip(
                    tags, losses, inslosses)
            else:
                edata = [('event_tag', 'loss')] + zip(tags, data['loss'])
            writer.save(edata, dest)
    return writer.getsaved()


# alternative export format for the average losses, used by the platform
@export.add(('avglosses-rlzs', 'csv'))
def export_avglosses_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    outs = extract_outputs(ekey[0], dstore, ext=ekey[1])
    sitemesh = dstore['sitemesh']
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    header = ['lon', 'lat', 'asset_ref', 'asset_value', 'average_loss',
              'stddev_loss', 'loss_type']
    for out in outs:
        rows = []
        for asset, loss in zip(assetcol, out.array):
            loc = sitemesh[asset['site_id']]
            row = [loc['lon'], loc['lat'], aref[asset['idx']],
                   asset[out.ltype], loss, numpy.nan, out.ltype]
            rows.append(row)
        writers.write_csv(out.path, [header] + rows)
    return [out.path for out in outs]


@export.add(('rcurves-rlzs', 'csv'))
def export_rcurves(ekey, dstore):
    rlzs = dstore['rlzs_assoc'].realizations
    assets = get_assets(dstore)
    curves = compactify(dstore[ekey[0]].value)
    name = ekey[0].split('-')[0]
    writer = writers.CsvWriter(fmt='%9.7E')
    for rlz in rlzs:
        array = compose_arrays(assets, curves[:, rlz.ordinal])
        path = dstore.export_path('%s-%s.csv' % (name, rlz.uid))
        writer.save(array, path)
    return writer.getsaved()


# this is used by classical_risk
@export.add(('loss_curves-rlzs', 'csv'))
def export_loss_curves(ekey, dstore):
    rlzs = dstore['rlzs_assoc'].realizations
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    assets = get_assets(dstore)
    curves = dstore[ekey[0]]
    name = ekey[0].split('-')[0]
    writer = writers.CsvWriter(fmt='%9.6E')
    for rlz in rlzs:
        for ltype in loss_types:
            array = compose_arrays(assets, curves[ltype][:, rlz.ordinal])
            path = dstore.export_path('%s-%s-%s.csv' % (name, ltype, rlz.uid))
            writer.save(array, path)
    return writer.getsaved()


@export.add(('dmg_by_asset', 'xml'))
def export_damage(ekey, dstore):
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    rlzs = dstore['rlzs_assoc'].realizations
    dmg_by_asset = dstore['dmg_by_asset']  # shape (N, L, R)
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    sitemesh = dstore['sitemesh']
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    D = len(dmg_states)
    N, R = dmg_by_asset.shape
    L = len(loss_types)
    fnames = []

    for l, r in itertools.product(range(L), range(R)):
        lt = loss_types[l]
        rlz = rlzs[r]
        suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (rlz.uid, lt)

        dd_asset = []
        for n in range(N):
            assref = aref[assetcol[n]['idx']]
            dist = dmg_by_asset[n, r][lt]
            point = sitemesh[assetcol[n]['site_id']]
            site = Site(point['lon'], point['lat'])
            for ds in range(D):
                dd_asset.append(
                    DmgDistPerAsset(
                        ExposureData(assref, site), dmg_states[ds],
                        dist['mean'][ds], dist['stddev'][ds]))

        f1 = export_dmg_xml(('dmg_dist_per_asset', 'xml'), dstore,
                            dmg_states, dd_asset, suffix)
        max_damage = dmg_states[-1]
        # the collapse map is extracted from the damage distribution per asset
        # (dda) by taking the value corresponding to the maximum damage
        collapse_map = [dda for dda in dd_asset if dda.dmg_state == max_damage]
        f2 = export_dmg_xml(('collapse_map', 'xml'), dstore,
                            dmg_states, collapse_map, suffix)
        fnames.extend(sum((f1 + f2).values(), []))
    return sorted(fnames)


@export.add(('dmg_by_taxon', 'xml'))
def export_damage_taxon(ekey, dstore):
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    rlzs = dstore['rlzs_assoc'].realizations
    dmg_by_taxon = dstore['dmg_by_taxon']  # shape (T, L, R)
    taxonomies = dstore['assetcol/taxonomies']
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    D = len(dmg_states)
    T, R = dmg_by_taxon.shape
    L = len(loss_types)
    fnames = []

    for l, r in itertools.product(range(L), range(R)):
        lt = loss_types[l]
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
                           dstore, dmg_states, dd_taxo, suffix)
        fnames.extend(sum(f.values(), []))
    return sorted(fnames)


@export.add(('dmg_total', 'xml'))
def export_damage_total(ekey, dstore):
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    rlzs = dstore['rlzs_assoc'].realizations
    dmg_total = dstore['dmg_total']
    R, = dmg_total.shape
    L = len(loss_types)
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    D = len(dmg_states)
    fnames = []
    for l, r in itertools.product(range(L), range(R)):
        lt = loss_types[l]
        rlz = rlzs[r]
        suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (rlz.uid, lt)

        dd_total = []
        for ds in range(D):
            dist = dmg_total[r][lt]
            dd_total.append(DmgDistTotal(
                dmg_states[ds], dist['mean'][ds], dist['stddev'][ds]))

        f = export_dmg_xml(('dmg_dist_total', 'xml'), dstore,
                           dmg_states, dd_total, suffix)
        fnames.extend(sum(f.values(), []))
    return sorted(fnames)


@export.add(
    ('loss_maps-rlzs', 'csv'), ('damages-rlzs', 'csv'),
    ('csq_by_asset', 'csv'))
def export_rlzs_by_asset_csv(ekey, dstore):
    rlzs = dstore['rlzs_assoc'].realizations
    assets = get_assets(dstore)
    R = len(rlzs)
    value = dstore[ekey[0]].value  # matrix N x R or T x R
    writer = writers.CsvWriter(fmt='%9.6E')
    for rlz, values in zip(rlzs, value.T):
        suffix = '.csv' if R == 1 else '-gsimltp_%s.csv' % rlz.uid
        fname = dstore.export_path(ekey[0] + suffix)
        writer.save(compose_arrays(assets, values), fname)
    return writer.getsaved()


@export.add(('csq_by_taxon', 'csv'))
def export_csq_by_taxon_csv(ekey, dstore):
    taxonomies = dstore['assetcol/taxonomies'].value
    rlzs = dstore['rlzs_assoc'].realizations
    R = len(rlzs)
    value = dstore[ekey[0]].value  # matrix T x R
    writer = writers.CsvWriter(fmt='%9.6E')
    for rlz, values in zip(rlzs, value.T):
        suffix = '.csv' if R == 1 else '-gsimltp_%s.csv' % rlz.uid
        fname = dstore.export_path(ekey[0] + suffix)
        writer.save(compose_arrays(taxonomies, values, 'taxonomy'), fname)
    return writer.getsaved()


# TODO: export loss_maps-stats csv
@export.add(('csq_total', 'csv'))
def export_csq_total_csv(ekey, dstore):
    rlzs = dstore['rlzs_assoc'].realizations
    R = len(rlzs)
    value = dstore[ekey[0]].value
    writer = writers.CsvWriter(fmt='%9.6E')
    for rlz, values in zip(rlzs, value):
        suffix = '.csv' if R == 1 else '-gsimltp_%s.csv' % rlz.uid
        fname = dstore.export_path(ekey[0] + suffix)
        writer.save(numpy.array([values], value.dtype), fname)
    return writer.getsaved()


def build_damage_dt(dstore):
    """
    :param dstore: a datastore instance
    :returns: a composite dtype loss_type -> (mean_ds1, stdv_ds1, ...)
    """
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    dt_list = []
    for ds in damage_states:
        dt_list.append(('%s_mean' % ds, F32))
        dt_list.append(('%s_stdv' % ds, F32))
    damage_dt = numpy.dtype(dt_list)
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    return numpy.dtype([(lt, damage_dt) for lt in loss_types])


def build_damage_array(data, damage_dt):
    """
    :param data: an array of length N with fields 'mean' and 'stddev'
    :param damage_dt: a damage composite data type loss_type -> states
    :returns: a composite array of length N and dtype damage_dt
    """
    L = len(data) if data.shape else 1
    dmg = numpy.zeros(L, damage_dt)
    for lt in damage_dt.names:
        for i, ms in numpy.ndenumerate(data[lt]):
            lst = []
            for m, s in zip(ms['mean'], ms['stddev']):
                lst.append(m)
                lst.append(s)
            dmg[lt][i] = tuple(lst)
    return dmg


@export.add(('dmg_by_asset', 'csv'))
def export_dmg_by_asset_csv(ekey, dstore):
    damage_dt = build_damage_dt(dstore)
    rlzs = dstore['rlzs_assoc'].realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    assets = get_assets(dstore)
    for rlz in rlzs:
        gsim, = rlz.value
        dmg_by_asset = build_damage_array(data[:, rlz.ordinal], damage_dt)
        fname = dstore.export_path('%s-%s.%s' % (ekey[0], gsim, ekey[1]))
        writer.save(compose_arrays(assets, dmg_by_asset), fname)
    return writer.getsaved()


@export.add(('dmg_by_taxon', 'csv'))
def export_dmg_by_taxon_csv(ekey, dstore):
    damage_dt = build_damage_dt(dstore)
    taxonomies = dstore['assetcol/taxonomies'].value
    rlzs = dstore['rlzs_assoc'].realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    for rlz in rlzs:
        gsim, = rlz.value
        dmg_by_taxon = build_damage_array(data[:, rlz.ordinal], damage_dt)
        fname = dstore.export_path('%s-%s.%s' % (ekey[0], gsim, ekey[1]))
        array = compose_arrays(taxonomies, dmg_by_taxon, 'taxonomy')
        writer.save(array, fname)
    return writer.getsaved()


@export.add(('dmg_total', 'csv'))
def export_dmg_totalcsv(ekey, dstore):
    damage_dt = build_damage_dt(dstore)
    rlzs = dstore['rlzs_assoc'].realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    for rlz in rlzs:
        gsim, = rlz.value
        dmg_total = build_damage_array(data[rlz.ordinal], damage_dt)
        fname = dstore.export_path('%s-%s.%s' % (ekey[0], gsim, ekey[1]))
        writer.save(dmg_total, fname)
    return writer.getsaved()


def export_dmg_xml(key, dstore, damage_states, dmg_data, suffix):
    """
    Export damage outputs in XML format.

    :param key:
        dmg_dist_per_asset|dmg_dist_per_taxonomy|dmg_dist_total|collapse_map
    :param dstore:
        the datastore
    :param damage_states:
        the list of damage states
    :param dmg_data:
        a list [(loss_type, unit, asset_ref, mean, stddev), ...]
    :param suffix:
        a suffix specifying the GSIM realization
    """
    dest = dstore.export_path('%s%s.%s' % (key[0], suffix, key[1]))
    risk_writers.DamageWriter(damage_states).to_nrml(key[0], dmg_data, dest)
    return AccumDict({key: [dest]})


# exports for scenario_risk

AggLoss = collections.namedtuple(
    'AggLoss', 'loss_type unit mean stddev')

LossMap = collections.namedtuple('LossMap', 'location asset_ref value std_dev')
LossCurve = collections.namedtuple(
    'LossCurve', 'location asset_ref poes losses loss_ratios '
    'average_loss stddev_loss')


# emulate a Django point
class Location(object):
    def __init__(self, xy):
        self.x, self.y = xy
        self.wkt = 'POINT(%s %s)' % tuple(xy)


# used by event_based_risk and classical_risk
@export.add(('loss_maps-rlzs', 'xml'), ('loss_maps-rlzs', 'geojson'))
def export_loss_maps_rlzs_xml_geojson(ekey, dstore):
    oq = dstore['oqparam']
    unit_by_lt = {ct['name']: ct['unit'] for ct in dstore['cost_types']}
    unit_by_lt['occupants'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    loss_maps = dstore[ekey[0]]
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    R = len(rlzs)
    sitemesh = dstore['sitemesh']
    fnames = []
    export_type = ekey[1]
    writercls = (risk_writers.LossMapGeoJSONWriter
                 if export_type == 'geojson' else
                 risk_writers.LossMapXMLWriter)
    loss_types = loss_maps.dtype.names
    L = len(loss_types)
    for lt in loss_types:
        loss_maps_lt = loss_maps[lt]
        for r in range(R):
            lmaps = loss_maps_lt[:, r]
            for poe in oq.conditional_loss_poes:
                for insflag in range(oq.insured_losses + 1):
                    ins = '_ins' if insflag else ''
                    rlz = rlzs[r]
                    unit = unit_by_lt[lt]
                    suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (
                        rlz.uid, lt)
                    root = ekey[0][:-5]  # strip -rlzs
                    name = '%s%s-poe-%s%s.%s' % (
                        root, suffix, poe, ins, ekey[1])
                    fname = dstore.export_path(name)
                    data = []
                    poe_str = 'poe~%s' % poe + ins
                    for ass, stat in zip(assetcol, lmaps[poe_str]):
                        loc = Location(sitemesh[ass['site_id']])
                        lm = LossMap(loc, aref[ass['idx']], stat, None)
                        data.append(lm)
                    writer = writercls(
                        fname, oq.investigation_time, poe=poe, loss_type=lt,
                        unit=unit,
                        risk_investigation_time=oq.risk_investigation_time,
                        **get_paths(rlz))
                    writer.serialize(data)
                    fnames.append(fname)
    return sorted(fnames)


# used by event_based_risk and classical_risk
@export.add(('loss_maps-stats', 'xml'), ('loss_maps-stats', 'geojson'))
def export_loss_maps_stats_xml_geojson(ekey, dstore):
    loss_maps = dstore[ekey[0]]
    N, S = loss_maps.shape
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    sitemesh = dstore['sitemesh']
    fnames = []
    export_type = ekey[1]
    writercls = (risk_writers.LossMapGeoJSONWriter
                 if export_type == 'geojson' else
                 risk_writers.LossMapXMLWriter)
    for writer, (ltype, poe, s, insflag) in _gen_writers(
            dstore, writercls, ekey[0]):
        ins = '_ins' if insflag else ''
        if ltype not in loss_maps.dtype.names:
            continue
        array = loss_maps[ltype][:, s]
        curves = []
        poe_str = 'poe~%s' % poe + ins
        for ass, val in zip(assetcol, array[poe_str]):
            loc = Location(sitemesh[ass['site_id']])
            curve = LossMap(loc, aref[ass['idx']], val, None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


# this is used by scenario_risk
@export.add(('losses_by_asset', 'xml'), ('losses_by_asset', 'geojson'))
def export_loss_map_xml_geojson(ekey, dstore):
    oq = dstore['oqparam']
    unit_by_lt = {ct['name']: ct['unit'] for ct in dstore['cost_types']}
    unit_by_lt['occupants'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    loss_map = dstore[ekey[0]]
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    R = len(rlzs)
    sitemesh = dstore['sitemesh']
    L = len(loss_types)
    fnames = []
    export_type = ekey[1]
    writercls = (risk_writers.LossMapGeoJSONWriter
                 if export_type == 'geojson' else
                 risk_writers.LossMapXMLWriter)
    for lt in loss_types:
        alosses = loss_map[lt]
        for ins in range(oq.insured_losses + 1):
            means = alosses['mean' + ('_ins' if ins else '')]
            stddevs = alosses['stddev' + ('_ins' if ins else '')]
            for r in range(R):
                rlz = rlzs[r]
                unit = unit_by_lt[lt]
                suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (
                    rlz.uid, lt)
                root = ekey[0][:-5]  # strip -rlzs
                name = '%s%s%s.%s' % (
                    root, suffix, '_ins' if ins else '', ekey[1])
                fname = dstore.export_path(name)
                data = []
                for ass, mean, stddev in zip(
                        assetcol, means[:, r], stddevs[:, r]):
                    loc = Location(sitemesh[ass['site_id']])
                    lm = LossMap(loc, aref[ass['idx']], mean, stddev)
                    data.append(lm)
                writer = writercls(
                    fname, oq.investigation_time, poe=None, loss_type=lt,
                    gsim_tree_path=rlz.uid, unit=unit,
                    risk_investigation_time=oq.risk_investigation_time)
                writer.serialize(data)
                fnames.append(fname)
    return sorted(fnames)


# this is used by scenario_risk
@export.add(('agglosses-rlzs', 'csv'))
def export_agglosses(ekey, dstore):
    unit_by_lt = {ct['name']: ct['unit'] for ct in dstore['cost_types']}
    unit_by_lt['occupants'] = 'people'
    rlzs = dstore['rlzs_assoc'].realizations
    agglosses = dstore[ekey[0]]
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    L = len(loss_types)
    R, = agglosses.shape
    fnames = []
    for lt in loss_types:
        for r in range(R):
            rlz = rlzs[r]
            unit = unit_by_lt[lt]
            suffix = '' if L == 1 and R == 1 else '-gsimltp_%s_%s' % (
                rlz.uid, lt)
            loss = agglosses[r][lt]
            losses = [AggLoss(lt, unit, loss['mean'], loss['stddev'])]
            out = export_loss_csv(('agg', 'csv'), dstore, losses, suffix)
            fnames.append(out)
    return sorted(fnames)


def export_loss_csv(ekey, dstore, data, suffix):
    """
    Export (aggregate) losses in CSV.

    :param key: per_asset_loss|asset-ins
    :param dstore: the datastore
    :param data: a list [(loss_type, unit, asset_ref, mean, stddev), ...]
    :param suffix: a suffix specifying the GSIM realization
    """
    dest = dstore.export_path('%s%s.%s' % (ekey[0], suffix, ekey[1]))
    if ekey[0] in ('agg', 'ins'):  # aggregate
        header = ['LossType', 'Unit', 'Mean', 'Standard Deviation']
    else:  # loss_map
        header = ['LossType', 'Unit', 'Asset', 'Mean', 'Standard Deviation']
        data.sort(key=operator.itemgetter(2))  # order by asset idx
    writers.write_csv(dest, [header] + data, fmt='%11.7E')
    return dest

AggCurve = collections.namedtuple(
    'AggCurve', ['losses', 'poes', 'average_loss', 'stddev_loss'])


def get_paths(rlz):
    """
    :param rlz:
        a logic tree realization (composite or simple)
    :returns:
        a dict {'source_model_tree_path': string, 'gsim_tree_path': string}
    """
    dic = {}
    if hasattr(rlz, 'sm_lt_path'):  # composite realization
        dic['source_model_tree_path'] = '_'.join(rlz.sm_lt_path)
        dic['gsim_tree_path'] = '_'.join(rlz.gsim_lt_path)
    else:  # simple GSIM realization
        dic['source_model_tree_path'] = ''
        dic['gsim_tree_path'] = '_'.join(rlz.lt_path)
    return dic


def _gen_writers(dstore, writercls, root):
    # build XMLWriter instances
    oq = dstore['oqparam']
    rlzs = dstore['rlzs_assoc'].realizations
    cost_types = dstore['cost_types']
    L, R = len(cost_types), len(rlzs)
    poes = oq.conditional_loss_poes if 'maps' in root else [None]
    for poe in poes:
        poe_str = '-%s' % poe if poe is not None else ''
        for l, ct in enumerate(cost_types):
            loss_type = ct['name']
            for ins in range(oq.insured_losses + 1):
                if root.endswith('-rlzs'):
                    for rlz in rlzs:
                        suffix = ('' if L == 1 and R == 1
                                  else '-gsimltp_%s_%s' % (rlz.uid, loss_type))
                        dest = dstore.export_path('%s%s%s%s.xml' % (
                            root[:-5],  # strip -rlzs
                            suffix, poe_str, '_ins' if ins else ''))
                        yield writercls(
                            dest, oq.investigation_time, poe=poe,
                            loss_type=loss_type, unit=ct['unit'],
                            risk_investigation_time=oq.risk_investigation_time,
                            **get_paths(rlz)), (
                                loss_type, poe, rlz.ordinal, ins)
                elif root.endswith('-stats'):
                    pairs = [('mean', None)] + [
                        ('quantile-%s' % q, q)
                        for q in oq.quantile_loss_curves]
                    for ordinal, (statname, statvalue) in enumerate(pairs):
                        dest = dstore.export_path('%s-%s-%s%s%s.xml' % (
                            root[:-6],  # strip -stats
                            statname, loss_type, poe_str,
                            '_ins' if ins else ''))
                        yield writercls(
                            dest, oq.investigation_time,
                            poe=poe, loss_type=loss_type,
                            risk_investigation_time=oq.risk_investigation_time,
                            statistics='mean' if ordinal == 0 else 'quantile',
                            quantile_value=statvalue, unit=ct['unit']
                        ), (loss_type, poe, ordinal, ins)


# this is used by event_based_risk
@export.add(('agg_curve-rlzs', 'xml'), ('agg_curve-stats', 'xml'))
def export_agg_curve(ekey, dstore):
    agg_curve = dstore[ekey[0]]
    fnames = []
    for writer, (loss_type, poe, r, insflag) in _gen_writers(
            dstore, risk_writers.AggregateLossCurveXMLWriter, ekey[0]):
        ins = '_ins' if insflag else ''
        rec = agg_curve[loss_type][r]
        curve = AggCurve(rec['losses' + ins], rec['poes' + ins],
                         rec['avg' + ins], None)
        writer.serialize(curve)
        fnames.append(writer._dest)
    return sorted(fnames)


# this is used by classical risk and event_based_risk
@export.add(('loss_curves-stats', 'xml'),
            ('loss_curves-stats', 'geojson'))
def export_loss_curves_stats(ekey, dstore):
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    sitemesh = dstore['sitemesh']
    loss_curves = dstore[ekey[0]]
    ok_loss_types = loss_curves.dtype.names
    [loss_ratios] = dstore['loss_ratios']
    fnames = []
    writercls = (risk_writers.LossCurveGeoJSONWriter
                 if ekey[0] == 'geojson' else
                 risk_writers.LossCurveXMLWriter)
    for writer, (ltype, poe, s, insflag) in _gen_writers(
            dstore, writercls, ekey[0]):
        if ltype not in ok_loss_types:
            continue  # ignore loss type
        ins = '_ins' if insflag else ''
        array = loss_curves[ltype][:, s]
        curves = []
        for ass, rec in zip(assetcol, array):
            loc = Location(sitemesh[ass['site_id']])
            curve = LossCurve(loc, aref[ass['idx']], rec['poes' + ins],
                              rec['losses' + ins], loss_ratios[ltype],
                              rec['avg' + ins], None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


# this is used by event_based_risk
@export.add(('rcurves-rlzs', 'xml'),
            ('rcurves-rlzs', 'geojson'))
def export_rcurves_rlzs(ekey, dstore):
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    sitemesh = dstore['sitemesh']
    rcurves = dstore[ekey[0]]
    [loss_ratios] = dstore['loss_ratios']
    fnames = []
    writercls = (risk_writers.LossCurveGeoJSONWriter
                 if ekey[0] == 'geojson' else
                 risk_writers.LossCurveXMLWriter)
    for writer, (ltype, poe, r, ins) in _gen_writers(
            dstore, writercls, ekey[0]):
        if ltype not in loss_ratios.dtype.names:
            continue  # ignore loss type
        array = rcurves[ltype][:, r, ins]
        curves = []
        for ass, poes in zip(assetcol, array):
            loc = Location(sitemesh[ass['site_id']])
            losses = loss_ratios[ltype] * ass[ltype]
            avg = scientific.average_loss((losses, poes))
            curve = LossCurve(loc, aref[ass['idx']], poes,
                              losses, loss_ratios[ltype], avg, None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


# this is used by classical_risk
@export.add(('loss_curves-rlzs', 'xml'),
            ('loss_curves-rlzs', 'geojson'))
def export_loss_curves_rlzs(ekey, dstore):
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    sitemesh = dstore['sitemesh']
    loss_curves = dstore[ekey[0]]
    fnames = []
    writercls = (risk_writers.LossCurveGeoJSONWriter
                 if ekey[0] == 'geojson' else
                 risk_writers.LossCurveXMLWriter)
    for writer, (lt, poe, r, insflag) in _gen_writers(
            dstore, writercls, ekey[0]):
        ins = '_ins' if insflag else ''
        array = loss_curves[lt][:, r]
        curves = []
        for ass, data in zip(assetcol, array):
            loc = Location(sitemesh[ass['site_id']])
            losses = data['losses' + ins]
            poes = data['poes' + ins]
            avg = data['avg' + ins]
            loss_ratios = losses / ass[lt]
            curve = LossCurve(loc, aref[ass['idx']], poes,
                              losses, loss_ratios, avg, None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)

BcrData = collections.namedtuple(
    'BcrData', ['location', 'asset_ref', 'average_annual_loss_original',
                'average_annual_loss_retrofitted', 'bcr'])


# this is used by classical_bcr
@export.add(('bcr-rlzs', 'xml'))
def export_bcr_map_rlzs(ekey, dstore):
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    sitemesh = dstore['sitemesh']
    bcr_data = dstore['bcr-rlzs']
    N, R = bcr_data.shape
    oq = dstore['oqparam']
    realizations = dstore['rlzs_assoc'].realizations
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    writercls = risk_writers.BCRMapXMLWriter
    fnames = []
    for rlz in realizations:
        suffix = '.xml' if R == 1 else '-gsimltp_%s.xml' % rlz.uid
        for l, loss_type in enumerate(loss_types):
            rlz_data = bcr_data[loss_type][:, rlz.ordinal]
            path = dstore.export_path('bcr-%s%s' % (loss_type, suffix))
            writer = writercls(
                path, oq.interest_rate, oq.asset_life_expectancy, loss_type,
                **get_paths(rlz))
            data = []
            for ass, value in zip(assetcol, rlz_data):
                loc = Location(sitemesh[ass['site_id']])
                data.append(BcrData(loc, aref[ass['idx']],
                                    value['annual_loss_orig'],
                                    value['annual_loss_retro'],
                                    value['bcr']))
            writer.serialize(data)
            fnames.append(path)
    return sorted(fnames)

# TODO: add export_bcr_map_stats


@export.add(('realizations', 'csv'))
def export_realizations(ekey, dstore):
    rlzs = dstore[ekey[0]]
    data = [['ordinal', 'uid', 'weight']]
    for i, rlz in enumerate(rlzs):
        data.append([i, rlz['uid'], rlz['weight']])
    path = dstore.export_path('realizations.csv')
    writers.write_csv(path, data, fmt='%s', sep='\t')
    return [path]
