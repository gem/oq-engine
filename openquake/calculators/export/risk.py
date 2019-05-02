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
import itertools
import collections
import logging
import numpy

from openquake.baselib import hdf5
from openquake.baselib.general import group_array,  deprecated
from openquake.hazardlib import nrml
from openquake.hazardlib.stats import compute_stats2
from openquake.risklib import scientific
from openquake.calculators.extract import (
    extract, build_damage_dt, build_damage_array, sanitize)
from openquake.calculators.export import export, loss_curves
from openquake.calculators.export.hazard import savez, get_mesh
from openquake.calculators import getters
from openquake.commonlib import writers, hazard_writers
from openquake.commonlib.util import get_assets, compose_arrays

Output = collections.namedtuple('Output', 'ltype path array')
F32 = numpy.float32
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
TWO32 = 2 ** 32
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def get_rup_data(ebruptures):
    dic = {}
    for ebr in ebruptures:
        point = ebr.rupture.surface.get_middle_point()
        dic[ebr.serial] = (ebr.rupture.mag, point.x, point.y, point.z)
    return dic

# ############################### exporters ############################## #


# this is used by event_based_risk and ebrisk
@export.add(('agg_curves-rlzs', 'csv'), ('agg_curves-stats', 'csv'))
def export_agg_curve_rlzs(ekey, dstore):
    oq = dstore['oqparam']
    R = len(dstore['weights'])
    agg_curve = dstore[ekey[0]]
    tags = (['rlz-%03d' % r for r in range(R)] if ekey[0].endswith('-rlzs')
            else ['mean'] + ['quantile-%s' % q for q in oq.quantiles])
    periods = agg_curve.attrs['return_periods']
    loss_types = tuple(agg_curve.attrs['loss_types'].split())
    if any(lt.endswith('_ins') for lt in loss_types):
        L = len(loss_types) // 2
    else:
        L = len(loss_types)
    tagnames = tuple(dstore['oqparam'].aggregate_by)
    tagcol = dstore['assetcol/tagcol']
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    header = ('annual_frequency_of_exceedence', 'return_period',
              'loss_type') + tagnames + ('loss_value', 'loss_ratio')
    expvalue = dstore['exposed_value'].value  # shape (T1, T2, ..., L)
    for r, tag in enumerate(tags):
        rows = []
        for multi_idx, loss in numpy.ndenumerate(agg_curve[:, r]):
            p, l, *tagidxs = multi_idx
            evalue = expvalue[tuple(tagidxs) + (l % L,)]
            row = tagcol.get_tagvalues(tagnames, tagidxs) + (
                loss, loss / evalue)
            rows.append((1 / periods[p], periods[p], loss_types[l]) + row)
        dest = dstore.build_fname('agg_loss', tag, 'csv')
        writer.save(rows, dest, header)
    return writer.getsaved()


def _get_data(dstore, dskey, stats):
    name, kind = dskey.split('-')  # i.e. ('avg_losses', 'stats')
    if kind == 'stats':
        weights = dstore['weights'].value
        tags, stats = zip(*stats)
        if dskey in set(dstore):  # precomputed
            value = dstore[dskey].value  # shape (A, S, LI)
        else:  # computed on the fly
            value = compute_stats2(
                dstore[name + '-rlzs'].value, stats, weights)
    else:  # rlzs
        value = dstore[dskey].value  # shape (A, R, LI)
        R = value.shape[1]
        tags = ['rlz-%03d' % r for r in range(R)]
    return name, value, tags


# used by ebrisk
@export.add(('agg_maps-rlzs', 'csv'), ('agg_maps-stats', 'csv'))
def export_agg_maps_csv(ekey, dstore):
    name, kind = ekey[0].split('-')
    oq = dstore['oqparam']
    tagcol = dstore['assetcol/tagcol']
    agg_maps = dstore[ekey[0]].value  # shape (C, R, L, T...)
    R = agg_maps.shape[1]
    kinds = (['rlz-%03d' % r for r in range(R)] if ekey[0].endswith('-rlzs')
             else ['mean'] + ['quantile-%s' % q for q in oq.quantiles])
    clp = [str(p) for p in oq.conditional_loss_poes]
    dic = dict(tagnames=['clp', 'kind', 'loss_type'] + oq.aggregate_by,
               clp=['?'] + clp, kind=['?'] + kinds,
               loss_type=('?',) + oq.loss_dt().names)
    for tagname in oq.aggregate_by:
        dic[tagname] = getattr(tagcol, tagname)
    aw = hdf5.ArrayWrapper(agg_maps, dic)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fname = dstore.export_path('%s.%s' % ekey)
    writer.save(aw.to_table(), fname)
    return [fname]


# this is used by event_based_risk and classical_risk
@export.add(('avg_losses-rlzs', 'csv'), ('avg_losses-stats', 'csv'))
def export_avg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    dskey = ekey[0]
    oq = dstore['oqparam']
    dt = oq.loss_dt()
    name, value, tags = _get_data(dstore, dskey, oq.hazard_stats().items())
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    assets = get_assets(dstore)
    for tag, values in zip(tags, value.transpose(1, 0, 2)):
        dest = dstore.build_fname(name, tag, 'csv')
        array = numpy.zeros(len(values), dt)
        for l, lt in enumerate(dt.names):
            array[lt] = values[:, l]
        writer.save(compose_arrays(assets, array), dest)
    return writer.getsaved()


# this is used by ebrisk
@export.add(('agg_losses-rlzs', 'csv'), ('agg_losses-stats', 'csv'))
def export_agg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    dskey = ekey[0]
    oq = dstore['oqparam']
    dt = oq.loss_dt()
    name, value, tags = _get_data(dstore, dskey, oq.hazard_stats().items())
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    expvalue = dstore['exposed_value'].value  # shape (T1, T2, ..., L)
    tagcol = dstore['assetcol/tagcol']
    tagnames = tuple(dstore['oqparam'].aggregate_by)
    header = ('loss_type',) + tagnames + (
        'loss_value', 'exposed_value', 'loss_ratio')
    for r, tag in enumerate(tags):
        rows = []
        for multi_idx, loss in numpy.ndenumerate(value[:, r]):
            l, *tagidxs = multi_idx
            evalue = expvalue[tuple(tagidxs) + (l,)]
            row = tagcol.get_tagvalues(tagnames, tagidxs) + (
                loss, evalue, loss / evalue)
            rows.append((dt.names[l],) + row)
        dest = dstore.build_fname(name, tag, 'csv')
        writer.save(rows, dest, header)
    return writer.getsaved()


# this is used by ebrisk
@export.add(('avg_losses', 'csv'))
def export_avg_losses_ebrisk(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    name = ekey[0]
    oq = dstore['oqparam']
    dt = oq.loss_dt()
    value = dstore[name].value  # shape (A, L)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    assets = get_assets(dstore)
    dest = dstore.build_fname(name, 'mean', 'csv')
    array = numpy.zeros(len(value), dt)
    for l, lt in enumerate(dt.names):
        array[lt] = value[:, l]
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
    if oq.calculation_mode.startswith('scenario'):
        dtlist = [('eid', U64)] + oq.loss_dt_list()
        arr = dstore['losses_by_event'].value[['eid', 'loss']]
        writer.save(arr.copy().view(dtlist), dest)
    elif oq.calculation_mode == 'ebrisk':
        tagcol = dstore['assetcol/tagcol']
        lbe = dstore['losses_by_event'].value
        lbe.sort(order='eid')
        dic = dict(tagnames=['event_id', 'loss_type'] + oq.aggregate_by)
        for tagname in oq.aggregate_by:
            dic[tagname] = getattr(tagcol, tagname)
        dic['event_id'] = ['?'] + list(lbe['eid'])
        dic['loss_type'] = ('?',) + oq.loss_dt().names
        aw = hdf5.ArrayWrapper(lbe['loss'], dic)  # shape (E, L, T...)
        writer.save(aw.to_table(), dest)
    else:
        dtlist = [('event_id', U64), ('rup_id', U32), ('year', U32)] + \
                 oq.loss_dt_list()
        eids = dstore['losses_by_event']['eid']
        year_of = year_dict(dstore['events']['id'],
                            oq.investigation_time, oq.ses_seed)
        arr = numpy.zeros(len(dstore['losses_by_event']), dtlist)
        arr['event_id'] = eids
        arr['rup_id'] = arr['event_id'] / TWO32
        arr['year'] = [year_of[eid] for eid in eids]
        loss = dstore['losses_by_event']['loss'].T  # shape (L, E)
        for losses, loss_type in zip(loss, oq.loss_dt().names):
            arr[loss_type] = losses
        writer.save(arr, dest)
    return writer.getsaved()


@export.add(('losses_by_asset', 'npz'))
def export_losses_by_asset_npz(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    fname = dstore.export_path('%s.%s' % ekey)
    savez(fname, **dict(extract(dstore, 'losses_by_asset')))
    return [fname]


def _compact(array):
    # convert an array of shape (a, e) into an array of shape (a,)
    dt = array.dtype
    a, e = array.shape
    lst = []
    for name in dt.names:
        lst.append((name, (dt[name], e)))
    return array.view(numpy.dtype(lst)).reshape(a)


@export.add(('rup_loss_table', 'xml'))
def export_maxloss_ruptures(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    rlzs_by_gsim = dstore['csm_info'].get_rlzs_by_gsim_grp()
    num_ses = oq.ses_per_logic_tree_path
    fnames = []
    for loss_type in oq.loss_dt().names:
        ebr = getters.get_maxloss_rupture(dstore, loss_type)
        root = hazard_writers.rupture_to_element(
            ebr.export(mesh, rlzs_by_gsim[ebr.grp_id], num_ses))
        dest = dstore.export_path('rupture-%s.xml' % loss_type)
        with open(dest, 'wb') as fh:
            nrml.write(list(root), fh)
        fnames.append(dest)
    return fnames


def year_dict(eids, investigation_time, ses_seed):
    numpy.random.seed(ses_seed)
    years = numpy.random.choice(int(investigation_time), len(eids)) + 1
    return dict(zip(numpy.sort(eids), years))  # eid -> year


# this is used by event_based_risk
@export.add(('agg_loss_table', 'csv'))
@deprecated(msg='This exporter will be removed soon')
def export_agg_losses_ebr(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    if 'ruptures' not in dstore:
        logging.warning('There are no ruptures in the datastore')
        return []
    name, ext = export.keyfunc(ekey)
    agg_losses = dstore['losses_by_event']
    has_rup_data = 'ruptures' in dstore
    extra_list = [('magnitude', F32),
                  ('centroid_lon', F32),
                  ('centroid_lat', F32),
                  ('centroid_depth', F32)] if has_rup_data else []
    oq = dstore['oqparam']
    lti = oq.lti
    dtlist = ([('event_id', U64), ('rup_id', U32), ('year', U32)]
              + extra_list + oq.loss_dt_list())
    elt_dt = numpy.dtype(dtlist)
    elt = numpy.zeros(len(agg_losses), elt_dt)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    events = dstore['events'].value
    events_by_rupid = collections.defaultdict(list)
    for event in events:
        rupid = event['id'] // TWO32
        events_by_rupid[rupid].append(event)
    year_of = year_dict(events['id'], oq.investigation_time, oq.ses_seed)
    rup_data = {}
    event_by_eid = {}  # eid -> event
    # populate rup_data and event_by_eid
    # TODO: avoid reading the events twice
    for rgetter in getters.gen_rupture_getters(dstore):
        ruptures = rgetter.get_ruptures()
        for ebr in ruptures:
            for event in events_by_rupid[ebr.serial]:
                event_by_eid[event['id']] = event
        if has_rup_data:
            rup_data.update(get_rup_data(ruptures))
    for r, row in enumerate(agg_losses):
        rec = elt[r]
        event = event_by_eid[row['eid']]
        rec['event_id'] = eid = event['id']
        rec['year'] = year_of[eid]
        if rup_data:
            rec['rup_id'] = rup_id = event['id'] // TWO32
            (rec['magnitude'], rec['centroid_lon'], rec['centroid_lat'],
             rec['centroid_depth']) = rup_data[rup_id]
        for lt, i in lti.items():
            rec[lt] = row['loss'][i]
    elt.sort(order=['year', 'event_id'])
    dest = dstore.build_fname('elt', '', 'csv')
    writer.save(elt, dest)
    return writer.getsaved()


# this is used by classical_risk and event_based_risk
@export.add(('loss_curves-rlzs', 'csv'), ('loss_curves-stats', 'csv'),
            ('loss_curves', 'csv'))
def export_loss_curves(ekey, dstore):
    if '/' in ekey[0]:
        kind = ekey[0].split('/', 1)[1]
    else:
        kind = ekey[0].split('-', 1)[1]  # rlzs or stats
    return loss_curves.LossCurveExporter(dstore).export('csv', kind)


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
        tags = ['mean'] + ['quantile-%s' % q for q in oq.quantiles]
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for i, tag in enumerate(tags):
        fname = dstore.build_fname('loss_maps', tag, ekey[1])
        writer.save(compose_arrays(assets, value[:, i]), fname)
    return writer.getsaved()


# used by classical_risk and event_based_risk
@export.add(('loss_maps-rlzs', 'npz'), ('loss_maps-stats', 'npz'))
def export_loss_maps_npz(ekey, dstore):
    kind = ekey[0].split('-')[1]  # rlzs or stats
    assets = get_assets(dstore)
    value = get_loss_maps(dstore, kind)
    R = dstore['csm_info'].get_num_rlzs()
    if kind == 'rlzs':
        tags = ['rlz-%03d' % r for r in range(R)]
    else:
        oq = dstore['oqparam']
        tags = ['mean'] + ['quantile-%s' % q for q in oq.quantiles]
    fname = dstore.export_path('%s.%s' % ekey)
    dic = {}
    for i, tag in enumerate(tags):
        dic[tag] = compose_arrays(assets, value[:, i])
    savez(fname, **dic)
    return [fname]


@export.add(('damages-rlzs', 'csv'), ('damages-stats', 'csv'))
def export_damages_csv(ekey, dstore):
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    oq = dstore['oqparam']
    loss_types = oq.loss_dt().names
    assets = get_assets(dstore)
    value = dstore[ekey[0]].value  # matrix N x R x LI or T x R x LI
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    if ekey[0].endswith('stats'):
        tags = ['mean'] + ['quantile-%s' % q for q in oq.quantiles]
    else:
        tags = ['rlz-%03d' % r for r in range(len(rlzs))]
    for lti, lt in enumerate(loss_types):
        for tag, values in zip(tags, value[:, :, lti].T):
            fname = dstore.build_fname('damages-%s' % lt, tag, ekey[1])
            writer.save(compose_arrays(assets, values), fname)
    return writer.getsaved()


def modal_damage_array(data, damage_dt):
    # determine the damage state with the highest probability
    A, L, MS, D = data.shape
    dmgstate = damage_dt['structural'].names
    arr = numpy.zeros(A, [('modal-ds-' + lt, hdf5.vstr)
                          for lt in damage_dt.names])
    for l, loss_type in enumerate(damage_dt.names):
        arr['modal-ds-' + loss_type] = [dmgstate[data[a, l, 0].argmax()]
                                        for a in range(A)]
    return arr


@export.add(('dmg_by_asset', 'csv'))
def export_dmg_by_asset_csv(ekey, dstore):
    E = len(dstore['events'])
    oq = dstore['oqparam']
    damage_dt = build_damage_dt(dstore, mean_std=E > 1)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    data = dstore[ekey[0]]
    writer = writers.CsvWriter(fmt='%.6E')
    assets = get_assets(dstore)
    for rlz in rlzs:
        if oq.modal_damage_state:
            dmg_by_asset = modal_damage_array(data[:, rlz.ordinal], damage_dt)
        else:
            dmg_by_asset = build_damage_array(data[:, rlz.ordinal], damage_dt)
        fname = dstore.build_fname(ekey[0], rlz, ekey[1])
        writer.save(compose_arrays(assets, dmg_by_asset), fname)
    return writer.getsaved()


@export.add(('dmg_by_asset', 'npz'))
def export_dmg_by_asset_npz(ekey, dstore):
    fname = dstore.export_path('%s.%s' % ekey)
    savez(fname, **dict(extract(dstore, 'dmg_by_asset')))
    return [fname]


@export.add(('dmg_by_event', 'csv'))
def export_dmg_by_event(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    damage_dt = build_damage_dt(dstore, mean_std=False)
    dt_list = [('event_id', numpy.uint64), ('rlzi', numpy.uint16)] + [
        (f, damage_dt.fields[f][0]) for f in damage_dt.names]
    all_losses = dstore[ekey[0]].value  # shape (E, R, LI)
    events_by_rlz = group_array(dstore['events'], 'rlz')
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    fname = dstore.build_fname('dmg_by_event', '', 'csv')
    writer.save(numpy.zeros(0, dt_list), fname)
    with open(fname, 'ab') as dest:
        for rlz in rlzs:
            data = all_losses[:, rlz.ordinal].copy().view(damage_dt)  # shape E
            arr = numpy.zeros(len(data), dt_list)
            arr['event_id'] = events_by_rlz[rlz.ordinal]['id']
            arr['rlzi'] = rlz.ordinal
            for field in damage_dt.names:
                arr[field] = data[field].squeeze()
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
        return _to_loss_maps(dstore[name].value, oq.loss_maps_dt())
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
    cc = dstore['assetcol/cost_calculator']
    unit_by_lt = cc.units
    unit_by_lt['occupants'] = 'people'
    agglosses = dstore[ekey[0]]
    losses = []
    header = ['loss_type', 'unit', 'mean', 'stddev']
    for l, lt in enumerate(loss_dt.names):
        unit = unit_by_lt[lt.replace('_ins', '')]
        mean = agglosses[l]['mean']
        stddev = agglosses[l]['stddev']
        losses.append((lt, unit, mean, stddev))
    dest = dstore.build_fname('agglosses', '', 'csv')
    writers.write_csv(dest, losses, header=header)
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
        tags = ['mean'] + ['quantile-%s' % q for q in oq.quantiles]
    else:
        tags = ['rlz-%03d' % r for r in range(R)]
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for t, tag in enumerate(tags):
        path = dstore.build_fname('bcr', tag, 'csv')
        writer.save(compose_arrays(assets, bcr_data[:, t]), path)
        fnames.append(path)
    return writer.getsaved()


@export.add(('losses_by_tag', 'csv'))
@deprecated(msg='This exporter will be removed soon')
def export_by_tag_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    token, tag = ekey[0].split('/')
    data = extract(dstore, token + '/' + tag)
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for stat, arr in data:
        tup = (ekey[0].replace('/', '-'), stat, ekey[1])
        path = '%s-%s.%s' % tup
        fname = dstore.export_path(path)
        writer.save(arr, fname)
        fnames.append(fname)
    return fnames


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
    arr = extract(dstore, 'asset_risk').array
    arefs = dstore['assetcol/asset_refs'].value
    rows = []
    lossnames = sorted(name for name in arr.dtype.names if 'loss' in name)
    perilnames = sorted(name for name in arr.dtype.names
                        if name.upper() == name)
    expnames = [name for name in arr.dtype.names if name not in md.tagnames
                and 'loss' not in name and name not in perilnames
                and name not in 'lon lat']
    colnames = (['asset_ref'] + sorted(md.tagnames) + ['lon', 'lat'] +
                expnames + perilnames + lossnames)
    # sanity check
    assert len(colnames) == len(arr.dtype.names) + 1
    for aref, rec in zip(arefs, arr):
        row = [aref]
        for name in colnames[1:]:
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
    writer.save(dset.value, fname, dset.dtype.names)
    return [fname]
