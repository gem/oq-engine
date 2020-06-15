# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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

from openquake.baselib import hdf5
from openquake.baselib.python3compat import decode
from openquake.hazardlib.stats import compute_stats2
from openquake.risklib import scientific
from openquake.calculators.extract import (
    extract, build_damage_dt, build_damage_array, sanitize)
from openquake.calculators.export import export, loss_curves
from openquake.calculators.export.hazard import savez
from openquake.commonlib import writers
from openquake.commonlib.util import get_assets, compose_arrays

Output = collections.namedtuple('Output', 'ltype path array')
F32 = numpy.float32
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def add_columns(table, **columns):
    """
    :param table: a list of rows, with the first row being an header
    :param columns: a dictionary of functions producing the dynamic columns
    """
    fields, *rows = table
    Ntuple = collections.namedtuple('nt', fields)
    newtable = [fields + tuple(columns)]
    for rec in itertools.starmap(Ntuple, rows):
        newrow = list(rec)
        for col in columns:
            newrow.append(columns[col](rec))
        newtable.append(newrow)
    return newtable


def get_rup_data(ebruptures):
    dic = {}
    for ebr in ebruptures:
        point = ebr.rupture.surface.get_middle_point()
        dic[ebr.rup_id] = (ebr.rupture.mag, point.x, point.y, point.z)
    return dic

# ############################### exporters ############################## #


def tag2idx(tags):
    return {tag: i for i, tag in enumerate(tags)}


# this is used by event_based_risk and ebrisk
@export.add(('agg_curves-rlzs', 'csv'), ('agg_curves-stats', 'csv'),
            ('tot_curves-rlzs', 'csv'), ('tot_curves-stats', 'csv'))
def export_agg_curve_rlzs(ekey, dstore):
    oq = dstore['oqparam']
    assetcol = dstore['assetcol']
    if ekey[0].startswith('agg_'):
        aggregate_by = oq.aggregate_by
    else:  # tot_curves
        aggregate_by = []

    name = '_'.join(['agg'] + aggregate_by)
    aggvalue = dstore['exposed_values/' + name][()]

    lti = tag2idx(oq.loss_names)
    tagi = {tagname: tag2idx(getattr(assetcol.tagcol, tagname))
            for tagname in aggregate_by}

    def get_loss_ratio(rec):
        idxs = tuple(tagi[tagname][getattr(rec, tagname)] - 1
                     for tagname in aggregate_by) + (lti[rec.loss_types],)
        return rec.loss_value / aggvalue[idxs]

    # shape (T1, T2, ..., L)
    md = dstore.metadata
    md.update(dict(
        kind=ekey[0], risk_investigation_time=oq.risk_investigation_time))
    fname = dstore.export_path('%s.%s' % ekey)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    aw = hdf5.ArrayWrapper.from_(dstore[ekey[0]], 'loss_value')
    table = add_columns(
        aw.to_table(), loss_ratio=get_loss_ratio,
        annual_frequency_of_exceedence=lambda rec: 1 / rec.return_periods)
    table[0] = [c[:-1] if c.endswith('s') else c for c in table[0]]
    writer.save(table, fname, comment=md)
    return writer.getsaved()


def _get_data(dstore, dskey, stats):
    name, kind = dskey.split('-')  # i.e. ('avg_losses', 'stats')
    if kind == 'stats':
        weights = dstore['weights'][()]
        if dskey in set(dstore):  # precomputed
            tags = [decode(s) for s in dstore.get_attr(dskey, 'stat')]
            statfuncs = [stats[tag] for tag in tags]
            value = dstore[dskey][()]  # shape (A, S, LI)
        else:  # computed on the fly
            tags, statfuncs = zip(*stats.items())
            value = compute_stats2(
                dstore[name + '-rlzs'][()], statfuncs, weights)
    else:  # rlzs
        value = dstore[dskey][()]  # shape (A, R, LI)
        R = value.shape[1]
        tags = ['rlz-%03d' % r for r in range(R)]
    return name, value, tags


# this is used by event_based_risk, classical_risk and scenario_risk
@export.add(('avg_losses-rlzs', 'csv'), ('avg_losses-stats', 'csv'))
def export_avg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    dskey = ekey[0]
    oq = dstore['oqparam']
    dt = [(ln, F32) for ln in oq.loss_names]
    name, value, tags = _get_data(dstore, dskey, oq.hazard_stats())
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    assets = get_assets(dstore)
    md = dstore.metadata
    md.update(dict(investigation_time=oq.investigation_time,
                   risk_investigation_time=oq.risk_investigation_time))
    for tag, values in zip(tags, value.transpose(1, 0, 2)):
        dest = dstore.build_fname(name, tag, 'csv')
        array = numpy.zeros(len(values), dt)
        for li, ln in enumerate(oq.loss_names):
            array[ln] = values[:, li]
        writer.save(compose_arrays(assets, array), dest, comment=md,
                    renamedict=dict(id='asset_id'))
    return writer.getsaved()


# this is used by ebrisk
@export.add(('agg_losses-rlzs', 'csv'), ('agg_losses-stats', 'csv'),
            ('tot_losses-rlzs', 'csv'), ('tot_losses-stats', 'csv'))
def export_agg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    dskey = ekey[0]
    oq = dstore['oqparam']
    aggregate_by = oq.aggregate_by if dskey.startswith('agg_') else []
    name, value, tags = _get_data(dstore, dskey, oq.hazard_stats())
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    assetcol = dstore['assetcol']
    aggname = '_'.join(['agg'] + aggregate_by)
    expvalue = dstore['exposed_values/' + aggname][()]
    # shape (T1, T2, ..., L)
    tagnames = tuple(aggregate_by)
    header = ('loss_type',) + tagnames + (
        'loss_value', 'exposed_value', 'loss_ratio')
    md = dstore.metadata
    md.update(dict(investigation_time=oq.investigation_time,
              risk_investigation_time=oq.risk_investigation_time))
    for r, tag in enumerate(tags):
        rows = []
        for multi_idx, loss in numpy.ndenumerate(value[:, r]):
            l, *tagidxs = multi_idx
            evalue = expvalue[tuple(tagidxs) + (l,)]
            row = assetcol.tagcol.get_tagvalues(tagnames, tagidxs) + (
                loss, evalue, loss / evalue)
            rows.append((oq.loss_names[l],) + row)
        dest = dstore.build_fname(name, tag, 'csv')
        writer.save(rows, dest, header, comment=md)
    return writer.getsaved()


@export.add(('src_loss_table', 'csv'))
def export_src_loss_table(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    trts = dstore['full_lt'].trts
    trt_by_source_id = {}
    for rec in dstore['source_info']:
        trt_by_source_id[rec['source_id'][:16]] = trts[rec['trti']]

    def get_trt(row):
        return trt_by_source_id[row.source]
    md = dstore.metadata
    md.update(dict(investigation_time=oq.investigation_time,
                   risk_investigation_time=oq.risk_investigation_time))
    aw = hdf5.ArrayWrapper.from_(dstore['src_loss_table'], 'loss_value')
    dest = dstore.build_fname('src_loss_table', '', 'csv')
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    rows = add_columns(aw.to_table(), trt=get_trt)
    writer.save(rows, dest, comment=md)
    return writer.getsaved()


# this is used by scenario_risk, event_based_risk and ebrisk
@export.add(('losses_by_event', 'csv'))
def export_losses_by_event(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    dest = dstore.build_fname('losses_by_event', '', 'csv')
    md = dstore.metadata
    if 'scenario' not in oq.calculation_mode:
        md.update(dict(investigation_time=oq.investigation_time,
                       risk_investigation_time=oq.risk_investigation_time))
    events = dstore['events'][()]
    columns = dict(rlz_id=lambda rec: events[rec.event_id]['rlz_id'])
    if oq.investigation_time:  # not scenario
        columns['rup_id'] = lambda rec: events[rec.event_id]['rup_id']
        columns['year'] = lambda rec: events[rec.event_id]['year']
    lbe = dstore['losses_by_event'][()]
    lbe.sort(order='event_id')
    dic = dict(shape_descr=['event_id'])
    dic['event_id'] = list(lbe['event_id'])
    # example (0, 1, 2, 3) -> (0, 2, 3, 1)
    axis = [0] + list(range(2, len(lbe['loss'].shape))) + [1]
    data = lbe['loss'].transpose(axis)  # shape (E, T..., L)
    aw = hdf5.ArrayWrapper(data, dic, oq.loss_names)
    table = add_columns(aw.to_table(), **columns)
    writer.save(table, dest, comment=md)
    return writer.getsaved()


def _compact(array):
    # convert an array of shape (a, e) into an array of shape (a,)
    dt = array.dtype
    a, e = array.shape
    lst = []
    for name in dt.names:
        lst.append((name, (dt[name], e)))
    return array.view(numpy.dtype(lst)).reshape(a)


# this is used by classical_risk and event_based_risk
@export.add(('loss_curves-rlzs', 'csv'), ('loss_curves-stats', 'csv'),
            ('loss_curves', 'csv'))
def export_loss_curves(ekey, dstore):
    if '/' in ekey[0]:
        kind = ekey[0].split('/', 1)[1]
    else:
        kind = ekey[0].split('-', 1)[1]  # rlzs or stats
    return loss_curves.LossCurveExporter(dstore).export('csv', kind)


# used by classical_risk
@export.add(('loss_maps-rlzs', 'csv'), ('loss_maps-stats', 'csv'))
def export_loss_maps_csv(ekey, dstore):
    kind = ekey[0].split('-')[1]  # rlzs or stats
    assets = get_assets(dstore)
    value = get_loss_maps(dstore, kind)
    oq = dstore['oqparam']
    if kind == 'rlzs':
        tags = dstore['full_lt'].get_realizations()
    else:
        tags = oq.hazard_stats()
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    md = dstore.metadata
    for i, tag in enumerate(tags):
        if hasattr(tag, 'ordinal'):  # is a realization
            tag = 'rlz-%d' % tag.ordinal
        fname = dstore.build_fname('loss_maps', tag, ekey[1])
        md.update(
            dict(kind=tag, risk_investigation_time=oq.risk_investigation_time))
        writer.save(compose_arrays(assets, value[:, i]), fname, comment=md,
                    renamedict=dict(id='asset_id'))
    return writer.getsaved()


# used by classical_risk
@export.add(('loss_maps-rlzs', 'npz'), ('loss_maps-stats', 'npz'))
def export_loss_maps_npz(ekey, dstore):
    kind = ekey[0].split('-')[1]  # rlzs or stats
    assets = get_assets(dstore)
    value = get_loss_maps(dstore, kind)
    R = dstore['full_lt'].get_num_rlzs()
    if kind == 'rlzs':
        tags = ['rlz-%03d' % r for r in range(R)]
    else:
        oq = dstore['oqparam']
        tags = oq.hazard_stats()
    fname = dstore.export_path('%s.%s' % ekey)
    dic = {}
    for i, tag in enumerate(tags):
        dic[tag] = compose_arrays(assets, value[:, i])
    savez(fname, **dic)
    return [fname]


def modal_damage_array(data, damage_dt):
    # determine the damage state with the highest probability
    A, L, D = data.shape
    dmgstate = damage_dt['structural'].names
    arr = numpy.zeros(A, [('modal-ds-' + lt, hdf5.vstr)
                          for lt in damage_dt.names])
    for l, loss_type in enumerate(damage_dt.names):
        arr['modal-ds-' + loss_type] = [dmgstate[data[a, l].argmax()]
                                        for a in range(A)]
    return arr


# damages and avg_damages require different DISPLAY_NAMEs, so they are
# kept separated even if the exporter is the same; see Anirudh's comment
# in https://github.com/gem/oq-engine/pull/5851
@export.add(('avg_damages-rlzs', 'csv'), ('avg_damages-stats', 'csv'),
            ('damages-rlzs', 'csv'), ('damages-stats', 'csv'))
def export_avg_damages_csv(ekey, dstore):
    oq = dstore['oqparam']
    dmg_dt = build_damage_dt(dstore)
    rlzs = dstore['full_lt'].get_realizations()
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    assets = get_assets(dstore)
    md = dstore.metadata
    if oq.investigation_time:
        md.update(dict(investigation_time=oq.investigation_time,
                       risk_investigation_time=oq.risk_investigation_time))
    if ekey[0].endswith('stats'):
        tags = oq.hazard_stats()
    else:
        tags = ['%03d' % r for r in range(len(rlzs))]
    for i, tag in enumerate(tags):
        if oq.modal_damage_state:
            avg_damages = modal_damage_array(data[:, i], dmg_dt)
        else:
            avg_damages = build_damage_array(data[:, i], dmg_dt)
        fname = dstore.build_fname(ekey[0].split('-')[0], tag, ekey[1])
        writer.save(compose_arrays(assets, avg_damages), fname,
                    comment=md, renamedict=dict(id='asset_id'))
    return writer.getsaved()


@export.add(('dmg_by_event', 'csv'))
def export_dmg_by_event(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    damage_dt = build_damage_dt(dstore)
    dt_list = [('event_id', U32), ('rlz_id', U16)] + [
        (f, damage_dt.fields[f][0]) for f in damage_dt.names]
    dmg_by_event = dstore[ekey[0]][()]  # shape E, L, D
    events = dstore['events'][()]
    writer = writers.CsvWriter(fmt='%g')
    fname = dstore.build_fname('dmg_by_event', '', 'csv')
    writer.save(numpy.zeros(0, dt_list), fname)
    with open(fname, 'a') as dest:
        for rlz_id in numpy.unique(events['rlz_id']):
            ok, = numpy.where(events['rlz_id'] == rlz_id)
            arr = numpy.zeros(len(ok), dt_list)
            arr['event_id'] = events['id'][ok]
            arr['rlz_id'] = rlz_id
            for l, loss_type in enumerate(damage_dt.names):
                for d, dmg_state in enumerate(damage_dt[loss_type].names):
                    arr[loss_type][dmg_state] = dmg_by_event[ok, l, d]
            writer.save_block(arr, dest)
    return [fname]


# emulate a Django point
class Location(object):
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.wkt = 'POINT(%s %s)' % (x, y)


def indices(*sizes):
    return itertools.product(*map(range, sizes))


def _to_loss_maps(array, loss_maps_dt):
    # convert a 4D array into a 2D array of dtype loss_maps_dt
    A, R, C, LI = array.shape
    lm = numpy.zeros((A, R), loss_maps_dt)
    for li, name in enumerate(loss_maps_dt.names):
        for p, poe in enumerate(loss_maps_dt[name].names):
            lm[name][poe] = array[:, :, p, li]
    return lm


def get_loss_maps(dstore, kind):
    """
    :param dstore: a DataStore instance
    :param kind: 'rlzs' or 'stats'
    """
    oq = dstore['oqparam']
    name = 'loss_maps-%s' % kind
    if name in dstore:  # event_based risk
        return _to_loss_maps(dstore[name][()], oq.loss_maps_dt())
    name = 'loss_curves-%s' % kind
    if name in dstore:  # classical_risk
        # the loss maps are built on the fly from the loss curves
        loss_curves = dstore[name]
        loss_maps = scientific.broadcast(
            scientific.loss_maps, loss_curves, oq.conditional_loss_poes)
        return loss_maps
    raise KeyError('loss_maps/loss_curves missing in %s' % dstore)


agg_dt = numpy.dtype([('unit', (bytes, 6)), ('mean', F32), ('stddev', F32)])


# this is used by scenario_risk
@export.add(('agglosses', 'csv'))
def export_agglosses(ekey, dstore):
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt()
    cc = dstore['cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    agglosses = dstore[ekey[0]]
    losses = []
    header = ['rlz_id', 'loss_type', 'unit', 'mean', 'stddev']
    for r in range(len(agglosses)):
        for l, lt in enumerate(loss_dt.names):
            unit = unit_by_lt[lt]
            mean = agglosses[r, l]['mean']
            stddev = agglosses[r, l]['stddev']
            losses.append((r, lt, unit, mean, stddev))
    dest = dstore.build_fname('agglosses', '', 'csv')
    writers.write_csv(dest, losses, header=header, comment=dstore.metadata)
    return [dest]


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


@export.add(('bcr-rlzs', 'csv'), ('bcr-stats', 'csv'))
def export_bcr_map(ekey, dstore):
    oq = dstore['oqparam']
    assets = get_assets(dstore)
    bcr_data = dstore[ekey[0]]
    N, R = bcr_data.shape
    if ekey[0].endswith('stats'):
        tags = oq.hazard_stats()
    else:
        tags = ['rlz-%03d' % r for r in range(R)]
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for t, tag in enumerate(tags):
        path = dstore.build_fname('bcr', tag, 'csv')
        writer.save(compose_arrays(assets, bcr_data[:, t]), path,
                    renamedict=dict(id='asset_id'))
        fnames.append(path)
    return writer.getsaved()


@export.add(('aggregate_by', 'csv'))
def export_aggregate_by_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    token, what = ekey[0].split('/', 1)
    aw = extract(dstore, 'aggregate/' + what)
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    path = '%s.%s' % (sanitize(ekey[0]), ekey[1])
    fname = dstore.export_path(path)
    writer.save(aw.to_table(), fname)
    fnames.append(fname)
    return fnames


@export.add(('asset_risk', 'csv'))
def export_asset_risk_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    path = '%s.%s' % (sanitize(ekey[0]), ekey[1])
    fname = dstore.export_path(path)
    md = extract(dstore, 'exposure_metadata')
    tostr = {'taxonomy': md.taxonomy}
    for tagname in md.tagnames:
        tostr[tagname] = getattr(md, tagname)
    tagnames = sorted(set(md.tagnames) - {'id'})
    arr = extract(dstore, 'asset_risk').array
    rows = []
    lossnames = sorted(name for name in arr.dtype.names if 'loss' in name)
    expnames = [name for name in arr.dtype.names if name not in md.tagnames
                and 'loss' not in name and name not in 'lon lat']
    colnames = tagnames + ['lon', 'lat'] + expnames + lossnames
    # sanity check
    assert len(colnames) == len(arr.dtype.names)
    for rec in arr:
        row = []
        for name in colnames:
            value = rec[name]
            try:
                row.append('"%s"' % tostr[name][value])
            except KeyError:
                row.append(value)
        rows.append(row)
    writer.save(rows, fname, colnames)
    return [fname]


@export.add(('agg_risk', 'csv'))
def export_agg_risk_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    path = '%s.%s' % (sanitize(ekey[0]), ekey[1])
    fname = dstore.export_path(path)
    dset = dstore['agg_risk']
    writer.save(dset[()], fname, dset.dtype.names)
    return [fname]
