# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import logging
import numpy

from openquake.baselib import hdf5, parallel, performance
from openquake.baselib.python3compat import decode
from openquake.baselib.general import (
    AccumDict, split_in_blocks, deprecated as depr)
from openquake.hazardlib.stats import compute_stats2
from openquake.risklib import scientific, riskinput
from openquake.calculators.export import export, loss_curves
from openquake.calculators.export.hazard import savez
from openquake.commonlib import writers, risk_writers, calc
from openquake.commonlib.util import (
    get_assets, compose_arrays, reader)
from openquake.commonlib.risk_writers import (
    DmgState, DmgDistPerTaxonomy, DmgDistPerAsset, DmgDistTotal,
    ExposureData, Site)

Output = collections.namedtuple('Output', 'ltype path array')
F32 = numpy.float32
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


deprecated = depr('Use the csv exporter instead')


def add_quotes(values):
    # used to escape taxonomies in CSV files
    return numpy.array(['"%s"' % val for val in values], (bytes, 100))


def get_rup_data(ebruptures):
    dic = {}
    for ebr in ebruptures:
        point = ebr.rupture.surface.get_middle_point()
        dic[ebr.serial] = (ebr.rupture.mag, point.x, point.y, point.z)
    return dic


def copy_to(elt, rup_data, rup_ids):
    """
    Copy information from the ruptures into the elt array for
    the given rupture serials.
    """
    assert len(elt) == len(rup_ids), (len(elt), len(rup_ids))
    for i, serial in numpy.ndenumerate(rup_ids):
        rec = elt[i]
        rec['rup_id'] = serial
        (rec['magnitude'], rec['centroid_lon'], rec['centroid_lat'],
         rec['centroid_depth']) = rup_data[serial]

# ############################### exporters ############################## #


# this is used by event_based_risk
@export.add(('avg_losses-rlzs', 'csv'), ('avg_losses-stats', 'csv'))
def export_avg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    dt = oq.loss_dt()
    assets = get_assets(dstore)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    name, kind = ekey[0].split('-')
    value = dstore[name + '-rlzs'].value  # shape (A, R, L')
    if kind == 'stats':
        weights = dstore['realizations']['weight']
        tags, stats = zip(*oq.risk_stats())
        value = compute_stats2(value, stats, weights)
    else:  # rlzs
        tags = ['rlz-%03d' % r for r in range(len(dstore['realizations']))]
    for tag, values in zip(tags, value.transpose(1, 0, 2)):
        dest = dstore.build_fname(name, tag, 'csv')
        array = numpy.zeros(len(values), dt)
        for l, lt in enumerate(dt.names):
            array[lt] = values[:, l]
        writer.save(compose_arrays(assets, array), dest)
    return writer.getsaved()


# this is used by scenario_risk
@export.add(('losses_by_asset', 'csv'))
def export_losses_by_asset(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    loss_dt = dstore['oqparam'].loss_dt(stat_dt)
    losses_by_asset = dstore[ekey[0]].value
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in rlzs:
        losses = losses_by_asset[:, rlz.ordinal]
        dest = dstore.build_fname('losses_by_asset', rlz, 'csv')
        data = compose_arrays(assets, losses.copy().view(loss_dt)[:, 0])
        writer.save(data, dest)
    return writer.getsaved()


# this is used by scenario_risk
@export.add(('losses_by_event', 'csv'))
def export_losses_by_event(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    loss_dt = dstore['oqparam'].loss_dt()
    all_losses = dstore[ekey[0]].value
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in rlzs:
        dest = dstore.build_fname('losses_by_event', rlz, 'csv')
        data = all_losses[:, rlz.ordinal].copy().view(loss_dt)
        writer.save(data, dest)
    return writer.getsaved()


@export.add(('losses_by_asset', 'npz'))
def export_losses_by_asset_npz(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    loss_dt = dstore['oqparam'].loss_dt()
    losses_by_asset = dstore[ekey[0]].value
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    dic = {}
    for rlz in rlzs:
        # I am exporting the 'mean' and ignoring the 'stddev'
        losses = losses_by_asset[:, rlz.ordinal]['mean'].copy()  # shape (N, 1)
        data = compose_arrays(assets, losses.view(loss_dt)[:, 0])
        dic['rlz-%03d' % rlz.ordinal] = data
    fname = dstore.export_path('%s.%s' % ekey)
    savez(fname, **dic)
    return [fname]


def _compact(array):
    # convert an array of shape (a, e) into an array of shape (a,)
    dt = array.dtype
    a, e = array.shape
    lst = []
    for name in dt.names:
        lst.append((name, (dt[name], e)))
    return array.view(numpy.dtype(lst)).reshape(a)


# used by scenario_risk
@export.add(('all_losses-rlzs', 'npz'))
def export_all_losses_npz(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    losses = dstore['all_losses-rlzs']
    dic = {}
    for rlz in rlzs:
        rlz_losses = _compact(losses[:, :, rlz.ordinal])
        data = compose_arrays(assets, rlz_losses)
        dic['all_losses-%03d' % rlz.ordinal] = data
    fname = dstore.build_fname('all_losses', 'rlzs', 'npz')
    savez(fname, **dic)
    return [fname]


# this is used by classical_risk
@export.add(('agg_losses-rlzs', 'csv'))
def export_agg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    agg_losses = dstore[ekey[0]].value
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    etags = calc.build_etags(dstore['events'], 0)
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
    name, ext = export.keyfunc(ekey)
    agg_losses = dstore[name]
    has_rup_data = 'ruptures' in dstore
    extra_list = [('magnitude', F32),
                  ('centroid_lon', F32),
                  ('centroid_lat', F32),
                  ('centroid_depth', F32)] if has_rup_data else []
    oq = dstore['oqparam']
    dtlist = ([('event_id', U64), ('rup_id', U32), ('year', U32)] +
              extra_list + oq.loss_dt_list())
    elt_dt = numpy.dtype(dtlist)
    csm_info = dstore['csm_info']
    rlzs_assoc = csm_info.get_rlzs_assoc()
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for sm_id, rlzs in rlzs_assoc.rlzs_by_smodel.items():
        # populate rup_data and event_by_eid
        rup_data = {}
        event_by_grp = {}  # grp_id -> eid -> event
        for grp_id in csm_info.get_grp_ids(sm_id):
            event_by_grp[grp_id] = event_by_eid = {}
            try:
                events = dstore['events/grp-%02d' % grp_id]
            except KeyError:
                continue
            for event in events:
                event_by_eid[event['eid']] = event
            if has_rup_data:
                rup_data.update(
                    get_rup_data(calc.get_ruptures(dstore, grp_id)))

        for rlz in rlzs:
            rlzname = 'rlz-%03d' % rlz.ordinal
            if rlzname not in agg_losses:
                continue
            data = agg_losses[rlzname].value
            eids = data['eid']
            losses = data['loss']
            eids_, years, serials = get_eids_years_serials(event_by_grp, eids)
            elt = numpy.zeros(len(eids), elt_dt)
            elt['event_id'] = eids_
            elt['year'] = years
            if rup_data:
                copy_to(elt, rup_data, serials)
            for i, ins in enumerate(
                    ['', '_ins'] if oq.insured_losses else ['']):
                for l, loss_type in enumerate(loss_types):
                    elt[loss_type + ins][:] = losses[:, l, i]
            elt.sort(order=['year', 'event_id'])
            dest = dstore.build_fname('agg_losses', rlz, 'csv')
            writer.save(elt, dest)
    return writer.getsaved()


def get_eids_years_serials(events_by_grp, eids):
    etags = []
    years = []
    serials = []
    for eid in eids:
        for grp_id, event_by_eid in events_by_grp.items():
            try:
                event = event_by_eid[eid]
            except KeyError:
                continue
            else:
                etags.append(event['eid'])
                years.append(event['year'])
                serials.append(event['rup_id'])
                break
    return numpy.array(etags), numpy.array(years), numpy.array(serials)


# this is used by classical_risk
@export.add(('loss_curves', 'csv'))
def export_loss_curves(ekey, dstore):
    if '/' not in ekey[0]:  # full loss curves are not exportable
        logging.error('Use the command oq export loss_curves/rlz-0 to export '
                      'the first realization')
        return []
    what = ekey[0].split('/', 1)[1]
    return loss_curves.LossCurveExporter(dstore).export('csv', what)


@export.add(('dmg_by_asset', 'xml'))
@deprecated
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
            assref = decode(aref[ass['idx']])
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
@deprecated
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
@deprecated
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


# used by classical_risk and event_based_risk
@export.add(('loss_maps-rlzs', 'csv'), ('loss_maps-stats', 'csv'))
def export_loss_maps_csv(ekey, dstore):
    kind = ekey[0].split('-')[1]  # rlzs or stats
    assets = get_assets(dstore)
    value = get_loss_maps(dstore, kind)
    if kind == 'rlzs':
        tags = dstore['csm_info'].get_rlzs_assoc().realizations
    else:
        oq = dstore['oqparam']
        tags = ['mean'] + ['quantile-%s' % q for q in oq.quantile_loss_curves]
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for tag, values in zip(tags, value.T):
        fname = dstore.build_fname('loss_maps', tag, ekey[1])
        writer.save(compose_arrays(assets, values), fname)
    return writer.getsaved()


# used by classical_risk and event_based_risk
@export.add(('loss_maps-rlzs', 'npz'), ('loss_maps-stats', 'npz'))
def export_loss_maps_npz(ekey, dstore):
    kind = ekey[0].split('-')[1]  # rlzs or stats
    assets = get_assets(dstore)
    value = get_loss_maps(dstore, kind)
    R = len(dstore['realizations'])
    if kind == 'rlzs':
        tags = ['rlz-%03d' % r for r in range(R)]
    else:
        oq = dstore['oqparam']
        tags = ['mean'] + ['quantile-%s' % q for q in oq.quantile_loss_curves]
    fname = dstore.export_path('%s.%s' % ekey)
    dic = {}
    for tag, values in zip(tags, value.T):
        dic[tag] = compose_arrays(assets, values)
    savez(fname, **dic)
    return [fname]


@export.add(('damages-rlzs', 'csv'))
def export_rlzs_by_asset_csv(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = get_assets(dstore)
    value = dstore[ekey[0]].value  # matrix N x R or T x R
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value.T):
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
        writer.save(compose_arrays(assets, values), fname)
    return writer.getsaved()


@export.add(('losses_total', 'csv'))
def export_losses_total_csv(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    value = dstore[ekey[0]].value
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value):
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
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
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
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
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
        array = compose_arrays(taxonomies, dmg_by_taxon, 'taxonomy')
        writer.save(array, fname)
    return writer.getsaved()


@export.add(('dmg_total', 'csv'))
def export_dmg_totalcsv(ekey, dstore):
    damage_dt = build_damage_dt(dstore)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    dset = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    for rlz in rlzs:
        dmg_total = build_damage_array(dset[rlz.ordinal], damage_dt)
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
        data = [['loss_type', 'damage_state', 'damage_value']]
        for loss_type in dmg_total.dtype.names:
            tot = dmg_total[loss_type]
            for name in tot.dtype.names:
                data.append((loss_type, name, tot[name]))
        writer.save(data, fname)
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


def indices(*sizes):
    return itertools.product(*map(range, sizes))


def get_loss_maps(dstore, kind):
    """
    :param dstore: a DataStore instance
    :param kind: 'rlzs' or 'stats'
    """
    oq = dstore['oqparam']
    name = 'loss_maps-%s' % kind
    if name in dstore:  # event_based risk
        return dstore[name].value
    name = 'loss_curves-%s' % kind
    if name in dstore:  # classical_risk
        loss_curves = dstore[name]
        loss_maps = scientific.broadcast(
            scientific.loss_maps, loss_curves, oq.conditional_loss_poes)
        return loss_maps
    raise KeyError('loss_maps/loss_curves missing in %s' % dstore)


# used by event_based_risk and classical_risk
@export.add(('loss_maps-rlzs', 'xml'), ('loss_maps-rlzs', 'geojson'))
@deprecated
def export_loss_maps_rlzs_xml_geojson(ekey, dstore):
    oq = dstore['oqparam']
    cc = dstore['assetcol/cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_maps = get_loss_maps(dstore, 'rlzs')
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
                rlz = rlzs[r]
                unit = unit_by_lt[lt[:-4] if lt.endswith('_ins') else lt]
                root = ekey[0][:-5]  # strip -rlzs
                name = '%s-%s-poe-%s' % (root, lt, poe)
                fname = dstore.build_fname(name, rlz, ekey[1])
                data = []
                poe_str = 'poe-%s' % poe
                for ass, stat in zip(assetcol, lmaps[poe_str]):
                    loc = Location(ass['lon'], ass['lat'])
                    lm = LossMap(loc, decode(aref[ass['idx']]), stat, None)
                    data.append(lm)
                writer = writercls(
                    fname, oq.investigation_time, poe=poe, loss_type=lt,
                    unit=unit,
                    risk_investigation_time=oq.risk_investigation_time,
                    **get_paths(rlz))
                writer.serialize(data)
                fnames.append(fname)
    return sorted(fnames)


# used by classical_risk and event_based_risk
# NB: loss_maps-stats are NOT computed as stats of loss_maps-rlzs,
# instead they are extracted directly from loss_maps-stats
@export.add(('loss_maps-stats', 'xml'), ('loss_maps-stats', 'geojson'))
@deprecated
def export_loss_maps_stats_xml_geojson(ekey, dstore):
    loss_maps = get_loss_maps(dstore, 'stats')
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
        array = loss_maps[ltype + ins][:, s]
        curves = []
        poe_str = 'poe-%s' % poe
        for ass, val in zip(assetcol, array[poe_str]):
            loc = Location(ass['lon'], ass['lat'])
            curve = LossMap(loc, decode(aref[ass['idx']]), val, None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


agg_dt = numpy.dtype([('unit', (bytes, 6)), ('mean', F32), ('stddev', F32)])


# this is used by scenario_risk
@export.add(('agglosses-rlzs', 'csv'))
def export_agglosses(ekey, dstore):
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt()
    cc = dstore['assetcol/cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    agglosses = dstore[ekey[0]]
    fnames = []
    for rlz in dstore['csm_info'].get_rlzs_assoc().realizations:
        loss = agglosses[rlz.ordinal]
        losses = []
        header = ['loss_type', 'unit', 'mean', 'stddev']
        for l, lt in enumerate(loss_dt.names):
            unit = unit_by_lt[lt.replace('_ins', '')]
            mean = loss[l]['mean']
            stddev = loss[l]['stddev']
            losses.append((lt, unit, mean, stddev))
        dest = dstore.build_fname('agglosses', rlz, 'csv')
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
    # build Writer instances
    name = writercls.__name__
    if 'XML' in name:
        ext = 'xml'
    elif 'JSON' in name:
        ext = 'geojson'
    else:
        raise ValueError('Unsupported writer class: %s' % writercls)
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
                            rlz, ext)
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
                        dest = dstore.build_fname(prefix, key, ext)
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
def export_agg_curve_rlzs(ekey, dstore):
    agg_curve = dstore[ekey[0]]
    fnames = []
    for writer, (loss_type, poe, r, ins) in _gen_writers(
            dstore, risk_writers.AggregateLossCurveXMLWriter, ekey[0]):
        rec = agg_curve[loss_type][ins, r]
        curve = AggCurve(rec['losses'], rec['poes'], rec['avg'], None)
        writer.serialize(curve)
        fnames.append(writer._dest)
    return sorted(fnames)


# this is used by classical risk
@export.add(('loss_curves-stats', 'xml'),
            ('loss_curves-stats', 'geojson'))
@deprecated
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
            curve = LossCurve(loc, decode(aref[ass['idx']]), rec['poes' + ins],
                              rec['losses' + ins], loss_ratios[ltype],
                              rec['avg' + ins], None)
            curves.append(curve)
        writer.serialize(curves)
        fnames.append(writer._dest)
    return sorted(fnames)


# used by scenario_damage
@export.add(('losses_by_taxon', 'csv'))
def export_csq_by_taxon_csv(ekey, dstore):
    taxonomies = add_quotes(dstore['assetcol/taxonomies'].value)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    value = dstore[ekey[0]].value  # matrix T x R
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz, values in zip(rlzs, value.T):
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
        writer.save(compose_arrays(taxonomies, values, 'taxonomy'), fname)
    return writer.getsaved()


# used by event_based_risk and scenario_risk
@export.add(('losses_by_taxon-rlzs', 'csv'), ('losses_by_taxon-stats', 'csv'))
def export_losses_by_taxon_csv(ekey, dstore):
    oq = dstore['oqparam']
    taxonomies = add_quotes(dstore['assetcol/taxonomies'].value)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_types = oq.loss_dt().names
    key, kind = ekey[0].split('-')
    value = dstore[key + '-rlzs'].value
    if kind == 'stats':
        weights = dstore['realizations']['weight']
        tags, stats = zip(*oq.risk_stats())
        value = compute_stats2(value, stats, weights)
    else:  # rlzs
        tags = rlzs
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    dt = numpy.dtype([('taxonomy', taxonomies.dtype)] + oq.loss_dt_list())
    for tag, values in zip(tags, value.transpose(1, 0, 2)):
        fname = dstore.build_fname(key, tag, ekey[1])
        array = numpy.zeros(len(values), dt)
        array['taxonomy'] = taxonomies
        for l, lt in enumerate(loss_types):
            array[lt] = values[:, l]
        writer.save(array, fname)
    return writer.getsaved()


# this is used by classical_risk
@export.add(('loss_curves-rlzs', 'xml'),
            ('loss_curves-rlzs', 'geojson'))
@depr('Use `oq export loss_curves/rlz-XX` instead')
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
@deprecated
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
                data.append(BcrData(loc, decode(aref[ass['idx']]),
                                    value['annual_loss_orig'],
                                    value['annual_loss_retro'],
                                    value['bcr']))
            writer.serialize(data)
            fnames.append(path)
    return sorted(fnames)


@export.add(('bcr-rlzs', 'csv'))
def export_bcr_map(ekey, dstore):
    assetcol = dstore['assetcol/array'].value
    aref = dstore['asset_refs'].value
    bcr_data = dstore['bcr-rlzs']
    N, R = bcr_data.shape
    realizations = dstore['csm_info'].get_rlzs_assoc().realizations
    loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for rlz in realizations:
        for l, loss_type in enumerate(loss_types):
            rlz_data = bcr_data[loss_type][:, rlz.ordinal]
            path = dstore.build_fname('bcr-%s' % loss_type, rlz, 'csv')
            data = [['lon', 'lat', 'asset_ref', 'average_annual_loss_original',
                     'average_annual_loss_retrofitted', 'bcr']]
            for ass, value in zip(assetcol, rlz_data):
                data.append((ass['lon'], ass['lat'],
                             decode(aref[ass['idx']]),
                             value['annual_loss_orig'],
                             value['annual_loss_retro'],
                             value['bcr']))
            writer.save(data, path)
            fnames.append(path)
    return writer.getsaved()

# TODO: add export_bcr_map_stats


@reader
def get_loss_ratios(lrgetter, aids, monitor):
    with lrgetter.dstore:
        loss_ratios = lrgetter.get_all(aids)  # list of arrays of dtype lrs_dt
    return zip(aids, loss_ratios)


@export.add(('asset_loss_table', 'hdf5'))
def export_asset_loss_table(ekey, dstore):
    """
    Export in parallel the asset loss table from the datastore.

    NB1: for large calculation this may run out of memory
    NB2: due to an heisenbug in the parallel reading of .hdf5 files this works
    reliably only if the datastore has been created by a different process

    The recommendation is: *do not use this exporter*: rather, study its source
    code and write what you need. Every postprocessing is different.
    """
    key, fmt = ekey
    oq = dstore['oqparam']
    assetcol = dstore['assetcol']
    arefs = dstore['asset_refs'].value
    avals = assetcol.values()
    loss_types = dstore.get_attr('all_loss_ratios', 'loss_types').split()
    dtlist = [(lt, F32) for lt in loss_types]
    if oq.insured_losses:
        for lt in loss_types:
            dtlist.append((lt + '_ins', F32))
    lrs_dt = numpy.dtype([('rlzi', U16), ('losses', dtlist)])
    fname = dstore.export_path('%s.%s' % ekey)
    monitor = performance.Monitor(key, fname)
    lrgetter = riskinput.LossRatiosGetter(dstore)
    aids = range(len(assetcol))
    allargs = [(lrgetter, list(block), monitor)
               for block in split_in_blocks(aids, oq.concurrent_tasks)]
    dstore.close()  # avoid OSError: Can't read data (Wrong b-tree signature)
    L = len(loss_types)
    with hdf5.File(fname, 'w') as f:
        nbytes = 0
        total = numpy.zeros(len(dtlist), F32)
        for pairs in parallel.Starmap(get_loss_ratios, allargs):
            for aid, data in pairs:
                asset = assetcol[aid]
                avalue = avals[aid]
                for l, lt in enumerate(loss_types):
                    aval = avalue[lt]
                    for i in range(oq.insured_losses + 1):
                        data['ratios'][:, l + L * i] *= aval
                aref = arefs[asset.idx]
                f[b'asset_loss_table/' + aref] = data.view(lrs_dt)
                total += data['ratios'].sum(axis=0)
                nbytes += data.nbytes
        f['asset_loss_table'].attrs['loss_types'] = ' '.join(loss_types)
        f['asset_loss_table'].attrs['total'] = total
        f['asset_loss_table'].attrs['nbytes'] = nbytes
    return [fname]
