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

import itertools
import collections

import numpy

from openquake.baselib.general import AccumDict
from openquake.risklib import scientific
from openquake.commonlib.export import export
from openquake.commonlib.export.hazard import build_etags
from openquake.commonlib import writers, risk_writers
from openquake.commonlib.util import get_assets, compose_arrays, get_ses_idx
from openquake.commonlib.risk_writers import (
    DmgState, DmgDistPerTaxonomy, DmgDistPerAsset, DmgDistTotal,
    ExposureData, Site)

Output = collections.namedtuple('Output', 'ltype path array')
F32 = numpy.float32
F64 = numpy.float64
U32 = numpy.uint32


def add_quotes(values):
    # used to escape taxonomies in CSV files
    return numpy.array(['"%s"' % val for val in values], (bytes, 100))


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
                path = dstore.build_fname(
                    dashkey, '%s%s%s' % (ltype, key, ins), ext)
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
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in rlzs:
        losses = avg_losses[:, rlz.ordinal]
        dest = dstore.build_fname('losses_by_asset', rlz, 'csv')
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
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for i, quantile in enumerate(quantiles):
        losses = avg_losses[:, i]
        dest = dstore.build_fname('avg_losses', quantile, 'csv')
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
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    etags = build_etags(dstore['events'])
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in rlzs:
        losses = agg_losses[:, rlz.ordinal]
        dest = dstore.build_fname('agg_losses', rlz, 'csv')
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
    oq = dstore['oqparam']
    dtlist = [('event_tag', (numpy.string_, 100)), ('event_set', U32)
              ] + oq.loss_dt_list()
    elt_dt = numpy.dtype(dtlist)
    etags = build_etags(dstore['events'])
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in rlzs:
        dest = dstore.build_fname('agg_losses', rlz, 'csv')
        eids = set()
        for rlzname in agg_losses:
            for loss_type in agg_losses[rlzname]:
                dset = agg_losses['%s/%s' % (rlzname, loss_type)]
                insured_losses = bool(dset.dtype['loss'].shape)
                eids.update(dset['rup_id'])
        eids = sorted(eids)
        eid2idx = dict(zip(eids, range(len(eids))))
        elt = numpy.zeros(len(eids), elt_dt)
        elt['event_tag'] = etags[eids]
        elt['event_set'] = numpy.array(
            [get_ses_idx(etag) for etag in elt['event_tag']], U32)
        for loss_type in loss_types:
            elt_lt = elt[loss_type]
            if insured_losses:
                elt_lt_ins = elt[loss_type + '_ins']
            key = 'rlz-%03d/%s' % (rlz.ordinal, loss_type)
            if key not in agg_losses:  # nothing was saved for this key
                continue
            data = agg_losses[key].value
            for i, eid in numpy.ndenumerate(data['rup_id']):
                idx = eid2idx[eid]
                if insured_losses:
                    elt_lt[idx] = data['loss'][i, 0]
                    elt_lt_ins[idx] = data['loss'][i, 1]
                else:
                    elt_lt[idx] = data['loss'][i]
        elt.sort(order='event_tag')
        writer.save(elt, dest)
    return writer.getsaved()


# alternative export format for the average losses, used by the platform
@export.add(('avglosses-rlzs', 'csv'))
def export_avglosses_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    outs = extract_outputs(ekey[0], dstore, ext=ekey[1])
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    header = ['lon', 'lat', 'asset_ref', 'asset_value', 'average_loss',
              'stddev_loss', 'loss_type']
    for out in outs:
        rows = []
        for asset, loss in zip(assetcol, out.array):
            row = [asset['lon'], asset['lat'], aref[asset['idx']],
                   asset[out.ltype], loss, numpy.nan, out.ltype]
            rows.append(row)
        writers.write_csv(out.path, [header] + rows)
    return [out.path for out in outs]


@export.add(('rcurves-rlzs', 'csv'))
def export_rcurves(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    curves = compactify(dstore[ekey[0]].value)
    name = ekey[0].split('-')[0]
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in rlzs:
        array = compose_arrays(assets, curves[:, rlz.ordinal])
        path = dstore.build_fname(name, rlz, 'csv')
        writer.save(array, path)
    return writer.getsaved()


# this is used by classical_risk
@export.add(('loss_curves-rlzs', 'csv'))
def export_loss_curves(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    assets = get_assets(dstore)
    curves = dstore[ekey[0]]
    name = ekey[0].split('-')[0]
    writer = writers.CsvWriter(fmt='%9.6E')
    for rlz in rlzs:
        for ltype in loss_types:
            array = compose_arrays(assets, curves[ltype][:, rlz.ordinal])
            path = dstore.build_fname('%s-%s' % (name, ltype), rlz, 'csv')
            writer.save(array, path)
    return writer.getsaved()


@export.add(('dmg_by_asset', 'xml'))
def export_damage(ekey, dstore):
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    dmg_by_asset = dstore['dmg_by_asset']  # shape (N, L, R)
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    D = len(dmg_states)
    N, R = dmg_by_asset.shape
    L = len(loss_types)
    fnames = []

    for l, r in itertools.product(range(L), range(R)):
        lt = loss_types[l]
        rlz = rlzs[r]
        dd_asset = []
        for n, ass in enumerate(assetcol):
            assref = aref[ass['idx']]
            dist = dmg_by_asset[n, r][lt]
            site = Site(ass['lon'], ass['lat'])
            for ds in range(D):
                dd_asset.append(
                    DmgDistPerAsset(
                        ExposureData(assref, site), dmg_states[ds],
                        dist['mean'][ds], dist['stddev'][ds]))

        f1 = export_dmg_xml(('dmg_dist_per_asset', 'xml'), dstore,
                            dmg_states, dd_asset, lt, rlz)
        max_damage = dmg_states[-1]
        # the collapse map is extracted from the damage distribution per asset
        # (dda) by taking the value corresponding to the maximum damage
        collapse_map = [dda for dda in dd_asset if dda.dmg_state == max_damage]
        f2 = export_dmg_xml(('collapse_map', 'xml'), dstore,
                            dmg_states, collapse_map, lt, rlz)
        fnames.extend(sum((f1 + f2).values(), []))
    return sorted(fnames)


@export.add(('dmg_by_taxon', 'xml'))
def export_damage_taxon(ekey, dstore):
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
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
        dd_taxo = []
        for t in range(T):
            dist = dmg_by_taxon[t, r][lt]
            for ds in range(D):
                dd_taxo.append(
                    DmgDistPerTaxonomy(
                        taxonomies[t], dmg_states[ds],
                        dist['mean'][ds], dist['stddev'][ds]))

        f = export_dmg_xml(('dmg_dist_per_taxonomy', 'xml'),
                           dstore, dmg_states, dd_taxo, lt, rlz)
        fnames.extend(sum(f.values(), []))
    return sorted(fnames)


@export.add(('dmg_total', 'xml'))
def export_damage_total(ekey, dstore):
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    damage_states = dstore.get_attr('composite_risk_model', 'damage_states')
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    dmg_total = dstore['dmg_total']
    R, = dmg_total.shape
    L = len(loss_types)
    dmg_states = [DmgState(s, i) for i, s in enumerate(damage_states)]
    D = len(dmg_states)
    fnames = []
    for l, r in itertools.product(range(L), range(R)):
        lt = loss_types[l]
        rlz = rlzs[r]
        dd_total = []
        for ds in range(D):
            dist = dmg_total[r][lt]
            dd_total.append(DmgDistTotal(
                dmg_states[ds], dist['mean'][ds], dist['stddev'][ds]))

        f = export_dmg_xml(('dmg_dist_total', 'xml'), dstore,
                           dmg_states, dd_total, lt, rlz)
        fnames.extend(sum(f.values(), []))
    return sorted(fnames)


@export.add(('loss_maps-rlzs', 'csv'))
def export_loss_maps_csv(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    value = dstore[ekey[0]].value  # matrix N x R or T x R
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value.T):
        fname = dstore.build_fname('loss_maps', rlz, ekey[1])
        writer.save(compose_arrays(assets, values), fname)
    return writer.getsaved()


@export.add(('damages-rlzs', 'csv'), ('csq_by_asset', 'csv'))
def export_rlzs_by_asset_csv(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    value = dstore[ekey[0]].value  # matrix N x R or T x R
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value.T):
        fname = dstore.build_fname(ekey[0], rlz.gsim_rlz, ekey[1])
        writer.save(compose_arrays(assets, values), fname)
    return writer.getsaved()


@export.add(('csq_by_taxon', 'csv'))
def export_csq_by_taxon_csv(ekey, dstore):
    taxonomies = add_quotes(dstore['assetcol/taxonomies'].value)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    value = dstore[ekey[0]].value  # matrix T x R
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value.T):
        fname = dstore.build_fname(ekey[0], rlz.gsim_rlz, ekey[1])
        writer.save(compose_arrays(taxonomies, values, 'taxonomy'), fname)
    return writer.getsaved()


# TODO: export loss_maps-stats csv
@export.add(('csq_total', 'csv'))
def export_csq_total_csv(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    value = dstore[ekey[0]].value
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value):
        fname = dstore.build_fname(ekey[0], rlz.gsim_rlz, ekey[1])
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
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    assets = get_assets(dstore)
    for rlz in rlzs:
        dmg_by_asset = build_damage_array(data[:, rlz.ordinal], damage_dt)
        fname = dstore.build_fname(ekey[0], rlz.gsim_rlz, ekey[1])
        writer.save(compose_arrays(assets, dmg_by_asset), fname)
    return writer.getsaved()


@export.add(('dmg_by_taxon', 'csv'))
def export_dmg_by_taxon_csv(ekey, dstore):
    damage_dt = build_damage_dt(dstore)
    taxonomies = add_quotes(dstore['assetcol/taxonomies'].value)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    for rlz in rlzs:
        dmg_by_taxon = build_damage_array(data[:, rlz.ordinal], damage_dt)
        fname = dstore.build_fname(ekey[0], rlz.gsim_rlz, ekey[1])
        array = compose_arrays(taxonomies, dmg_by_taxon, 'taxonomy')
        writer.save(array, fname)
    return writer.getsaved()


@export.add(('dmg_total', 'csv'))
def export_dmg_totalcsv(ekey, dstore):
    damage_dt = build_damage_dt(dstore)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    for rlz in rlzs:
        dmg_total = build_damage_array(data[rlz.ordinal], damage_dt)
        fname = dstore.build_fname(ekey[0], rlz.gsim_rlz, ekey[1])
        writer.save(dmg_total, fname)
    return writer.getsaved()


def export_dmg_xml(key, dstore, damage_states, dmg_data, lt, rlz):
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
    :param lt:
        loss type string
    :param rlz:
        a realization object
    """
    dest = dstore.build_fname('%s-%s' % (key[0], lt), rlz, key[1])
    risk_writers.DamageWriter(damage_states).to_nrml(key[0], dmg_data, dest)
    return AccumDict({key: [dest]})


# exports for scenario_risk

LossMap = collections.namedtuple('LossMap', 'location asset_ref value std_dev')
LossCurve = collections.namedtuple(
    'LossCurve', 'location asset_ref poes losses loss_ratios '
    'average_loss stddev_loss')


# emulate a Django point
class Location(object):
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.wkt = 'POINT(%s %s)' % (x, y)


# used by event_based_risk and classical_risk
@export.add(('loss_maps-rlzs', 'xml'), ('loss_maps-rlzs', 'geojson'))
def export_loss_maps_rlzs_xml_geojson(ekey, dstore):
    oq = dstore['oqparam']
    cc = dstore['assetcol/cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_maps = dstore[ekey[0]]
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    R = len(rlzs)
    fnames = []
    export_type = ekey[1]
    writercls = (risk_writers.LossMapGeoJSONWriter
                 if export_type == 'geojson' else
                 risk_writers.LossMapXMLWriter)
    loss_types = loss_maps.dtype.names
    for lt in loss_types:
        loss_maps_lt = loss_maps[lt]
        for r in range(R):
            lmaps = loss_maps_lt[:, r]
            for poe in oq.conditional_loss_poes:
                for insflag in range(oq.insured_losses + 1):
                    ins = '_ins' if insflag else ''
                    rlz = rlzs[r]
                    unit = unit_by_lt[lt]
                    root = ekey[0][:-5]  # strip -rlzs
                    name = '%s-%s-poe-%s%s' % (root, lt, poe, ins)
                    fname = dstore.build_fname(name, rlz, ekey[1])
                    data = []
                    poe_str = 'poe-%s' % poe + ins
                    for ass, stat in zip(assetcol, lmaps[poe_str]):
                        loc = Location(ass['lon'], ass['lat'])
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
        poe_str = 'poe-%s' % poe + ins
        for ass, val in zip(assetcol, array[poe_str]):
            loc = Location(ass['lon'], ass['lat'])
            curve = LossMap(loc, aref[ass['idx']], val, None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


# this is used by scenario_risk
@export.add(('losses_by_asset', 'xml'), ('losses_by_asset', 'geojson'))
def export_loss_map_xml_geojson(ekey, dstore):
    oq = dstore['oqparam']
    cc = dstore['assetcol/cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_map = dstore[ekey[0]]
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    R = len(rlzs)
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
                root = ekey[0][:-5]  # strip -rlzs
                name = '%s-%s%s' % (root, lt, '_ins' if ins else '')
                fname = dstore.build_fname(name, rlz, ekey[1])
                data = []
                for ass, mean, stddev in zip(
                        assetcol, means[:, r], stddevs[:, r]):
                    loc = Location(ass['lon'], ass['lat'])
                    lm = LossMap(loc, aref[ass['idx']], mean, stddev)
                    data.append(lm)
                writer = writercls(
                    fname, oq.investigation_time, poe=None, loss_type=lt,
                    gsim_tree_path=rlz.uid, unit=unit,
                    risk_investigation_time=oq.risk_investigation_time)
                writer.serialize(data)
                fnames.append(fname)
    return sorted(fnames)

agg_dt = numpy.dtype([('unit', (bytes, 6)), ('mean', F32), ('stddev', F32)])


# this is used by scenario_risk
@export.add(('agglosses-rlzs', 'csv'))
def export_agglosses(ekey, dstore):
    cc = dstore['assetcol/cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    agglosses = dstore[ekey[0]]
    fnames = []
    for rlz in dstore['csm_info'].get_rlzs_assoc().realizations:
        gsim, = rlz.gsim_rlz.value
        loss = agglosses[rlz.ordinal]
        losses = numpy.zeros(
            1, numpy.dtype([(lt, agg_dt) for lt in loss.dtype.names]))
        header = []
        for lt in loss.dtype.names:
            losses[lt]['unit'] = unit_by_lt[lt]
            header.append('%s-unit' % lt)
            losses[lt]['mean'] = loss[lt]['mean']
            header.append('%s-mean' % lt)
            losses[lt]['stddev'] = loss[lt]['stddev']
            header.append('%s-stddev' % lt)
        dest = dstore.build_fname('agglosses', gsim, 'csv')
        writers.write_csv(dest, losses, header=header)
        fnames.append(dest)
    return sorted(fnames)


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
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    cc = dstore['assetcol/cost_calculator']
    poes = oq.conditional_loss_poes if 'maps' in root else [None]
    for poe in poes:
        poe_str = '-%s' % poe if poe is not None else ''
        for l, loss_type in enumerate(cc.loss_types):
            for ins in range(oq.insured_losses + 1):
                if root.endswith('-rlzs'):
                    for rlz in rlzs:
                        dest = dstore.build_fname(
                            '%s-%s%s%s' %
                            (root[:-5],  # strip -rlzs
                             loss_type, poe_str, '_ins' if ins else ''),
                            rlz, 'xml')
                        yield writercls(
                            dest, oq.investigation_time, poe=poe,
                            loss_type=loss_type, unit=cc.units[loss_type],
                            risk_investigation_time=oq.risk_investigation_time,
                            **get_paths(rlz)), (
                                loss_type, poe, rlz.ordinal, ins)
                elif root.endswith('-stats'):
                    pairs = [('mean', None)] + [
                        ('quantile-%s' % q, q)
                        for q in oq.quantile_loss_curves]
                    for ordinal, (statname, statvalue) in enumerate(pairs):
                        prefix = root[:-6]  # strip -stats
                        key = '%s-%s%s%s' % (statname, loss_type, poe_str,
                                             '_ins' if ins else '')
                        dest = dstore.build_fname(prefix, key, 'xml')
                        yield writercls(
                            dest, oq.investigation_time,
                            poe=poe, loss_type=loss_type,
                            risk_investigation_time=oq.risk_investigation_time,
                            statistics='mean' if ordinal == 0 else 'quantile',
                            quantile_value=statvalue,
                            unit=cc.units[loss_type],
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
            loc = Location(ass['lon'], ass['lat'])
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
            loc = Location(ass['lon'], ass['lat'])
            value = (ass['occupants'] if ltype == 'occupants'
                     else ass['value-' + ltype])
            losses = loss_ratios[ltype] * value
            avg = scientific.average_loss((losses, poes))
            curve = LossCurve(loc, aref[ass['idx']], poes,
                              losses, loss_ratios[ltype], avg, None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


# used by ebr calculator
@export.add(('losses_by_taxon', 'csv'))
def export_losses_by_taxon_csv(ekey, dstore):
    taxonomies = add_quotes(dstore['assetcol/taxonomies'].value)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    value = dstore[ekey[0]].value  # matrix of shape (T, L, R)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    dt = numpy.dtype([('taxonomy', taxonomies.dtype)]
                     + [(lt, F64) for lt in loss_types])
    for rlz, values in zip(rlzs, value.transpose(2, 0, 1)):
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
        array = numpy.zeros(len(values), dt)
        array['taxonomy'] = taxonomies
        for l, lt in enumerate(loss_types):
            array[lt] = values[:, l]
        writer.save(array, fname)
    return writer.getsaved()


# this is used by classical_risk
@export.add(('loss_curves-rlzs', 'xml'),
            ('loss_curves-rlzs', 'geojson'))
def export_loss_curves_rlzs(ekey, dstore):
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
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
            loc = Location(ass['lon'], ass['lat'])
            losses = data['losses' + ins]
            poes = data['poes' + ins]
            avg = data['avg' + ins]
            if lt == 'occupants':
                loss_ratios = losses / ass['occupants']
            else:
                loss_ratios = losses / ass['value-' + lt]
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
    bcr_data = dstore['bcr-rlzs']
    N, R = bcr_data.shape
    oq = dstore['oqparam']
    realizations = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    writercls = risk_writers.BCRMapXMLWriter
    fnames = []
    for rlz in realizations:
        for l, loss_type in enumerate(loss_types):
            rlz_data = bcr_data[loss_type][:, rlz.ordinal]
            path = dstore.build_fname('bcr-%s' % loss_type, rlz, 'xml')
            writer = writercls(
                path, oq.interest_rate, oq.asset_life_expectancy, loss_type,
                **get_paths(rlz))
            data = []
            for ass, value in zip(assetcol, rlz_data):
                loc = Location(ass['lon'], ass['lat'])
                data.append(BcrData(loc, aref[ass['idx']],
                                    value['annual_loss_orig'],
                                    value['annual_loss_retro'],
                                    value['bcr']))
            writer.serialize(data)
            fnames.append(path)
    return sorted(fnames)

# TODO: add export_bcr_map_stats
