# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
import itertools
import collections
import numpy
import pandas

from openquake.baselib import hdf5, writers, general
from openquake.baselib.python3compat import decode
from openquake.hazardlib.stats import compute_stats2
from openquake.risklib import scientific
from openquake.calculators.extract import (
    extract, build_damage_dt, build_csq_dt, build_damage_array, sanitize,
    avglosses)
from openquake.calculators.export import export, loss_curves
from openquake.calculators.export.hazard import savez
from openquake.commonlib.util import get_assets, compose_arrays

Output = collections.namedtuple('Output', 'ltype path array')
F32 = numpy.float32
F64 = numpy.float64
U16 = numpy.uint16
U32 = numpy.uint32
stat_dt = numpy.dtype([('mean', F32), ('stddev', F32)])


def get_rup_data(ebruptures):
    dic = {}
    for ebr in ebruptures:
        point = ebr.rupture.surface.get_middle_point()
        dic[ebr.id] = (ebr.rupture.mag, point.x, point.y, point.z)
    return dic

# ############################### exporters ############################## #


def tag2idx(tags):
    return {tag: i for i, tag in enumerate(tags)}


def _loss_type(ln):
    if ln[-4:] == '_ins':
        return ln[:-4]
    return ln


def get_aggtags(dstore):
    # returns a list of tag tuples
    if 'agg_keys' in dstore:  # there was an aggregate_by
        aggtags = [ln.decode('utf8').split(',')
                   for ln in dstore['agg_keys'][:]]
        aggtags += [('*total*',) * len(aggtags[0])]
    else:  # np aggregate_by
        aggtags = [()]
    return aggtags


def _aggrisk(oq, aggids, aggtags, agg_values, aggrisk, md, dest):
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    cols = [col for col in aggrisk.columns
            if col not in {'agg_id', 'rlz_id', 'loss_id'}]
    csqs = [col for col in cols if not col.startswith('dmg_')]
    manyrlzs = hasattr(aggrisk, 'rlz_id') and len(aggrisk.rlz_id.unique()) > 1
    fnames = []
    K = len(agg_values) - 1
    pairs = [([], aggrisk.agg_id == K)]  # full aggregation
    for tagnames, agg_ids in zip(oq.aggregate_by, aggids):
        pairs.append((tagnames, numpy.isin(aggrisk.agg_id, agg_ids)))
    for tagnames, ok in pairs:
        out = general.AccumDict(accum=[])
        for (agg_id, lid), df in aggrisk[ok].groupby(['agg_id', 'loss_id']):
            n = len(df)
            loss_type = scientific.LOSSTYPE[lid]
            if loss_type == 'occupants':
                loss_type += '_' + oq.time_event
            if loss_type == 'claim':  # temporary hack
                continue
            out['loss_type'].extend([loss_type] * n)
            if tagnames:
                for tagname, tag in zip(tagnames, aggtags[agg_id]):
                    out[tagname].extend([tag] * n)
            if manyrlzs:
                out['rlz_id'].extend(df.rlz_id)
            for col in cols:
                if col in csqs:  # normally csqs = ['loss']
                    aval = scientific.get_agg_value(
                        col, agg_values, agg_id, loss_type, oq.time_event)
                    out[col + '_value'].extend(df[col])
                    out[col + '_ratio'].extend(df[col] / aval)
                else:  # in ScenarioDamageTestCase:test_case_12
                    out[col].extend(df[col])
        dsdic = {'dmg_0': 'no_damage'}
        for s, ls in enumerate(oq.limit_states, 1):
            dsdic['dmg_%d' % s] = ls
        df = pandas.DataFrame(out).rename(columns=dsdic)
        fname = dest.format('-'.join(tagnames))
        writer.save(df, fname, comment=md)
        fnames.append(fname)
    return fnames


@export.add(('aggrisk', 'csv'))
def export_aggrisk(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    assetcol = dstore['assetcol']
    md = dstore.metadata
    md.update(dict(investigation_time=oq.investigation_time,
                   risk_investigation_time=oq.risk_investigation_time or
                   oq.investigation_time))

    aggrisk = dstore.read_df('aggrisk')
    dest = dstore.build_fname('aggrisk-{}', '', 'csv')
    agg_values = assetcol.get_agg_values(
        oq.aggregate_by, oq.max_aggregations)
    aggids, aggtags = assetcol.build_aggids(
        oq.aggregate_by, oq.max_aggregations)
    return _aggrisk(oq, aggids, aggtags, agg_values, aggrisk, md, dest)


@export.add(('aggrisk-stats', 'csv'), ('aggcurves-stats', 'csv'))
def export_aggrisk_stats(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    key = ekey[0].split('-')[0]  # aggrisk or aggcurves
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    dest = dstore.build_fname(key + '-stats-{}', '', 'csv')
    dataf = extract(dstore, 'risk_stats/' + key)
    assetcol = dstore['assetcol']
    agg_values = assetcol.get_agg_values(
        oq.aggregate_by, oq.max_aggregations)
    K = len(agg_values) - 1
    aggids, aggtags = assetcol.build_aggids(
        oq.aggregate_by, oq.max_aggregations)
    pairs = [([], dataf.agg_id == K)]  # full aggregation
    for tagnames, agg_ids in zip(oq.aggregate_by, aggids):
        pairs.append((tagnames, numpy.isin(dataf.agg_id, agg_ids)))
    fnames = []
    for tagnames, ok in pairs:
        df = dataf[ok].copy()
        if tagnames:
            tagvalues = numpy.array([aggtags[agg_id] for agg_id in df.agg_id])
            for n, name in enumerate(tagnames):
                df[name] = tagvalues[:, n]
        del df['agg_id']
        fname = dest.format('-'.join(tagnames))
        writer.save(df, fname, df.columns, comment=dstore.metadata)
        fnames.append(fname)
    return fnames


def _get_data(dstore, dskey, loss_types, stats):
    name, kind = dskey.split('-')  # i.e. ('avg_losses', 'stats')
    if kind == 'stats':
        weights = dstore['weights'][()]
        if dskey in set(dstore):  # precomputed
            rlzs_or_stats = list(stats)
            statfuncs = [stats[ros] for ros in stats]
            value = avglosses(dstore, loss_types, 'stats')  # shape (A, S, L)
        elif dstore['oqparam'].collect_rlzs:
            rlzs_or_stats = list(stats)
            value = avglosses(dstore, loss_types, 'rlzs')
        else:  # compute on the fly
            rlzs_or_stats, statfuncs = zip(*stats.items())
            value = compute_stats2(
                avglosses(dstore, loss_types, 'rlzs'), statfuncs, weights)
    else:  # rlzs
        value = avglosses(dstore, loss_types, kind)  # shape (A, R, L)
        R = value.shape[1]
        rlzs_or_stats = ['rlz-%03d' % r for r in range(R)]
    return name, value, rlzs_or_stats


# this is used by event_based_risk, classical_risk and scenario_risk
@export.add(('avg_losses-rlzs', 'csv'), ('avg_losses-stats', 'csv'))
def export_avg_losses(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    dskey = ekey[0]
    oq = dstore['oqparam']
    dt = [(ln, F32) for ln in oq.ext_loss_types]
    name, value, rlzs_or_stats = _get_data(
        dstore, dskey, oq.ext_loss_types, oq.hazard_stats())
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    assets = get_assets(dstore)
    md = dstore.metadata
    md.update(dict(investigation_time=oq.investigation_time,
                   risk_investigation_time=oq.risk_investigation_time
                   or oq.investigation_time))
    for ros, values in zip(rlzs_or_stats, value.transpose(1, 0, 2)):
        dest = dstore.build_fname(name, ros, 'csv')
        array = numpy.zeros(len(values), dt)
        for li, ln in enumerate(oq.ext_loss_types):
            array[ln] = values[:, li]
        writer.save(compose_arrays(assets, array), dest, comment=md,
                    renamedict=dict(id='asset_id'))
    return writer.getsaved()


@export.add(('src_loss_table', 'csv'))
def export_src_loss_table(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    md = dstore.metadata
    md.update(dict(investigation_time=oq.investigation_time,
                   risk_investigation_time=oq.risk_investigation_time or
                   oq.investigation_time))
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for lt in dstore['src_loss_table']:
        aw = hdf5.ArrayWrapper.from_(dstore['src_loss_table/' + lt])
        dest = dstore.build_fname('src_loss_' + lt, '', 'csv')
        writer.save(aw.to_dframe(), dest, comment=md)
    return writer.getsaved()


# this is used by all GMF-based risk calculators
# NB: it exports only the event loss table, i.e. the totals
@export.add(('risk_by_event', 'csv'))
def export_event_loss_table(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    dest = dstore.build_fname('risk_by_event', '', 'csv')
    md = dstore.metadata
    if 'scenario' not in oq.calculation_mode:
        md.update(dict(investigation_time=oq.investigation_time,
                       risk_investigation_time=oq.risk_investigation_time
                       or oq.investigation_time))
    events = dstore.read_df('events', 'id')
    K = dstore.get_attr('risk_by_event', 'K', 0)
    try:
        lstates = dstore.get_attr('risk_by_event', 'limit_states').split()
    except KeyError:  # ebrisk, no limit states
        lstates = []
    df = dstore.read_df('risk_by_event', 'agg_id', dict(agg_id=K))
    df['loss_type'] = scientific.LOSSTYPE[df.loss_id.to_numpy()]
    del df['loss_id']
    if 'variance' in df.columns:
        del df['variance']
    ren = {'dmg_%d' % i: lstate for i, lstate in enumerate(lstates, 1)}
    df.rename(columns=ren, inplace=True)
    df = df.join(events, on='event_id')
    if 'ses_id' in df.columns:
        del df['ses_id']
    del df['rlz_id']
    if 'scenario' in oq.calculation_mode:
        del df['rup_id']
        if 'year' in df.columns:
            del df['year']
    df.sort_values(['event_id', 'loss_type'], inplace=True)
    writer.save(df, dest, comment=md)
    return writer.getsaved()


def _compact(array):
    # convert an array of shape (a, e) into an array of shape (a,)
    dt = array.dtype
    a, e = array.shape
    lst = []
    for name in dt.names:
        lst.append((name, (dt[name], e)))
    return array.view(numpy.dtype(lst)).reshape(a)


# this is used by classical_risk
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
        rlzs_or_stats = dstore['full_lt'].get_realizations()
    else:
        rlzs_or_stats = oq.hazard_stats()
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    md = dstore.metadata
    for i, ros in enumerate(rlzs_or_stats):
        if hasattr(ros, 'ordinal'):  # is a realization
            ros = 'rlz-%d' % ros.ordinal
        fname = dstore.build_fname('loss_maps', ros, ekey[1])
        md.update(
            dict(kind=ros, risk_investigation_time=oq.risk_investigation_time
                 or oq.investigation_time))
        writer.save(compose_arrays(assets, value[:, i]), fname, comment=md,
                    renamedict=dict(id='asset_id'))
    return writer.getsaved()


# used by classical_risk
@export.add(('loss_maps-rlzs', 'npz'), ('loss_maps-stats', 'npz'))
def export_loss_maps_npz(ekey, dstore):
    kind = ekey[0].split('-')[1]  # rlzs or stats
    assets = get_assets(dstore)
    value = get_loss_maps(dstore, kind)
    R = dstore['full_lt'].get_num_paths()
    if kind == 'rlzs':
        rlzs_or_stats = ['rlz-%03d' % r for r in range(R)]
    else:
        oq = dstore['oqparam']
        rlzs_or_stats = oq.hazard_stats()
    fname = dstore.export_path('%s.%s' % ekey)
    dic = {}
    for i, ros in enumerate(rlzs_or_stats):
        dic[ros] = compose_arrays(assets, value[:, i])
    savez(fname, **dic)
    return [fname]


def modal_damage_array(data, damage_dt):
    # determine the damage state with the highest probability
    A, L, D = data.shape
    dmgstate = damage_dt['structural'].names
    arr = numpy.zeros(A, [('modal-ds-' + lt, hdf5.vstr)
                          for lt in damage_dt.names])
    for li, loss_type in enumerate(damage_dt.names):
        arr['modal-ds-' + loss_type] = [dmgstate[data[a, li].argmax()]
                                        for a in range(A)]
    return arr


# used by event_based_damage, scenario_damage, classical_damage
@export.add(('damages-rlzs', 'csv'), ('damages-stats', 'csv'))
def export_damages_csv(ekey, dstore):
    oq = dstore['oqparam']
    ebd = oq.calculation_mode == 'event_based_damage'
    dmg_dt = build_damage_dt(dstore)
    rlzs = dstore['full_lt'].get_realizations()
    orig = dstore[ekey[0]][:]  # shape (A, R, L, D)
    writer = writers.CsvWriter(fmt='%.6E')
    assets = get_assets(dstore)
    md = dstore.metadata
    if oq.investigation_time:
        rit = oq.risk_investigation_time or oq.investigation_time
        md.update(dict(investigation_time=oq.investigation_time,
                       risk_investigation_time=rit))
    D = len(oq.limit_states) + 1
    R = 1 if oq.collect_rlzs else len(rlzs)
    if ekey[0].endswith('stats'):
        rlzs_or_stats = oq.hazard_stats()
    else:
        rlzs_or_stats = ['rlz-%03d' % r for r in range(R)]
    name = ekey[0].split('-')[0]
    if oq.calculation_mode != 'classical_damage':
        name = 'avg_' + name
    for i, ros in enumerate(rlzs_or_stats):
        if ebd:  # export only the consequences from damages-rlzs, i == 0
            rate = len(dstore['events']) * oq.time_ratio / len(rlzs)
            data = orig[:, i] * rate
            A, L, Dc = data.shape
            if Dc == D:  # no consequences, export nothing
                return []
            csq_dt = build_csq_dt(dstore)
            damages = numpy.zeros(A, csq_dt)
            for a in range(A):
                for li, lt in enumerate(csq_dt.names):
                    damages[lt][a] = tuple(data[a, li, D:Dc])
            fname = dstore.build_fname('avg_risk', ros, ekey[1])
        else:  # scenario_damage, classical_damage
            if oq.modal_damage_state:
                damages = modal_damage_array(orig[:, i], dmg_dt)
            else:
                damages = build_damage_array(orig[:, i], dmg_dt)
            fname = dstore.build_fname(name, ros, ekey[1])
        writer.save(compose_arrays(assets, damages), fname,
                    comment=md, renamedict=dict(id='asset_id'))
    return writer.getsaved()


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
        rlzs_or_stats = oq.hazard_stats()
    else:
        rlzs_or_stats = ['rlz-%03d' % r for r in range(R)]
    fnames = []
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    for t, ros in enumerate(rlzs_or_stats):
        path = dstore.build_fname('bcr', ros, 'csv')
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
    writer.save(aw.to_dframe(), fname)
    fnames.append(fname)
    return fnames


# used in multi_risk
@export.add(('asset_risk', 'csv'))
def export_asset_risk_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    path = '%s.%s' % (sanitize(ekey[0]), ekey[1])
    fname = dstore.export_path(path)
    md = json.loads(extract(dstore, 'exposure_metadata').json)
    tostr = {'taxonomy': md['taxonomy']}
    for tagname in md['tagnames']:
        tostr[tagname] = md[tagname]
    tagnames = sorted(set(md['tagnames']) - {'id'})
    arr = extract(dstore, 'asset_risk').array
    rows = []
    lossnames = sorted(name for name in arr.dtype.names if 'loss' in name)
    expnames = [name for name in arr.dtype.names if name not in md['tagnames']
                and 'loss' not in name and name not in 'lon lat']
    colnames = tagnames + ['lon', 'lat'] + expnames + lossnames
    # sanity check
    assert len(colnames) == len(arr.dtype.names)
    for rec in arr:
        row = []
        for name in colnames:
            value = rec[name]
            try:
                row.append(tostr[name][value])
            except KeyError:
                row.append(value)
        rows.append(row)
    writer.save(rows, fname, colnames)
    return [fname]


# used in multi_risk
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


@export.add(('aggcurves', 'csv'))
def export_aggcurves_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    oq = dstore['oqparam']
    assetcol = dstore['assetcol']
    agg_values = assetcol.get_agg_values(
        oq.aggregate_by, oq.max_aggregations)
    aggids, aggtags = assetcol.build_aggids(
        oq.aggregate_by, oq.max_aggregations)
    E = len(dstore['events'])
    R = len(dstore['weights'])
    K = len(dstore['agg_values']) - 1
    dataf = dstore.read_df('aggcurves')
    consequences = [col for col in dataf.columns
                    if col in scientific.KNOWN_CONSEQUENCES]
    dest = dstore.export_path('%s-{}.%s' % ekey)
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    md = dstore.metadata
    md['risk_investigation_time'] = (oq.risk_investigation_time or
                                     oq.investigation_time)
    md['num_events'] = E
    md['effective_time'] = (
        oq.investigation_time * oq.ses_per_logic_tree_path * R)
    md['limit_states'] = dstore.get_attr('aggcurves', 'limit_states')

    # aggcurves
    def fix(col):
        if col.endswith(('_aep', '_oep')):
            return col[:-4]  # strip suffix
        return col
    cols = [col for col in dataf.columns if
            fix(col) not in consequences and
            col not in ('agg_id', 'rlz_id', 'loss_id')]
    edic = general.AccumDict(accum=[])
    manyrlzs = not oq.collect_rlzs and R > 1
    fnames = []
    pairs = [([], dataf.agg_id == K)]  # full aggregation
    for tagnames, agg_ids in zip(oq.aggregate_by, aggids):
        pairs.append((tagnames, numpy.isin(dataf.agg_id, agg_ids)))
    LT = scientific.LOSSTYPE
    for tagnames, ok in pairs:
        edic = general.AccumDict(accum=[])
        for (agg_id, rlz_id, loss_id), d in dataf[ok].groupby(
                ['agg_id', 'rlz_id', 'loss_id']):
            if loss_id == scientific.LOSSID['claim']:  # temporary hack
                continue
            if loss_id == scientific.LOSSID['occupants']:
                lt = LT[loss_id] + '_' + oq.time_event
            else:
                lt = LT[loss_id]
            if tagnames:
                for tagname, tag in zip(tagnames, aggtags[agg_id]):
                    edic[tagname].extend([tag] * len(d))
            for col in cols:
                edic[col].extend(d[col])
            edic['loss_type'].extend([LT[loss_id]] * len(d))
            if manyrlzs:
                edic['rlz_id'].extend([rlz_id] * len(d))
            for cons in consequences:
                edic[cons + '_value'].extend(d[cons])
                aval = scientific.get_agg_value(
                    cons, agg_values, agg_id, lt, oq.time_event)
                edic[cons + '_ratio'].extend(d[cons] / aval)
        fname = dest.format('-'.join(tagnames))
        writer.save(pandas.DataFrame(edic), fname, comment=md)
        fnames.append(fname)
    return fnames


@export.add(('reinsurance-risk_by_event', 'csv'),
            ('reinsurance-aggcurves', 'csv'),
            ('reinsurance-avg_portfolio', 'csv'),
            ('reinsurance-avg_policy', 'csv'))
def export_reinsurance(ekey, dstore):
    dest = dstore.export_path('%s.%s' % ekey)
    df = dstore.read_df(ekey[0])
    if 'event_id' in df.columns:
        events = dstore['events'][()]
        if 'year' not in events.dtype.names:  # gmfs.hdf5 missing events
            df['year'] = 1
        else:
            df['year'] = events[df.event_id.to_numpy()]['year']
    if 'policy_id' in df.columns:  # convert policy_id -> policy name
        policy_names = dstore['agg_keys'][:]
        df['policy_id'] = decode(policy_names[df['policy_id'].to_numpy() - 1])
    fmap = json.loads(dstore.get_attr('treaty_df', 'field_map'))
    treaty_df = dstore.read_df('treaty_df')
    for code, col in zip(treaty_df.code, treaty_df.id):
        fmap['over_' + code] = 'overspill_' + col
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    writer.save(df.rename(columns=fmap), dest, comment=dstore.metadata)
    return [dest]


@export.add(('infra-avg_loss', 'csv'),
            ('infra-node_el', 'csv'),
            ('infra-taz_cl', 'csv'),
            ('infra-dem_cl', 'csv'),
            ('infra-event_ccl', 'csv'),
            ('infra-event_pcl', 'csv'),
            ('infra-event_wcl', 'csv'),
            ('infra-event_efl', 'csv'))
def export_node_el(ekey, dstore):
    dest = dstore.export_path('%s.%s' % ekey)
    df = dstore.read_df(ekey[0])
    writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
    writer.save(df, dest, comment=dstore.metadata)
    return writer.getsaved()
