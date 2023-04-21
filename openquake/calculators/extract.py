# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2023 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import parse_qs
from unittest.mock import Mock
from functools import lru_cache
import operator
import logging
import json
import gzip
import ast
import io

import requests
from h5py._hl.dataset import Dataset
from h5py._hl.group import Group
import numpy
import pandas
from scipy.cluster.vq import kmeans2

from openquake.baselib import config, hdf5, general, writers
from openquake.baselib.hdf5 import ArrayWrapper
from openquake.baselib.general import group_array, println
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib.gsim.base import ContextMaker, read_cmakers
from openquake.hazardlib.calc import disagg, stochastic, filters
from openquake.hazardlib.stats import calc_stats
from openquake.hazardlib.source import rupture
from openquake.risklib.scientific import LOSSTYPE, LOSSID
from openquake.risklib.asset import tagset
from openquake.commonlib import calc, util, oqvalidation, datastore, logictree
from openquake.calculators import getters

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = 2 ** 32
ALL = slice(None)
CHUNKSIZE = 4*1024**2  # 4 MB
SOURCE_ID = stochastic.rupture_dt['source_id']
memoized = lru_cache()


def lit_eval(string):
    """
    `ast.literal_eval` the string if possible, otherwise returns it unchanged
    """
    try:
        return ast.literal_eval(string)
    except (ValueError, SyntaxError):
        return string


def get_info(dstore):
    """
    :returns: a dict with 'stats', 'loss_types', 'num_rlzs', 'tagnames', etc
    """
    oq = dstore['oqparam']
    stats = {stat: s for s, stat in enumerate(oq.hazard_stats())}
    loss_types = {lt: li for li, lt in enumerate(oq.loss_dt().names)}
    imt = {imt: i for i, imt in enumerate(oq.imtls)}
    num_rlzs = len(dstore['weights'])
    return dict(stats=stats, num_rlzs=num_rlzs, loss_types=loss_types,
                imtls=oq.imtls, investigation_time=oq.investigation_time,
                poes=oq.poes, imt=imt, uhs_dt=oq.uhs_dt(),
                limit_states=oq.limit_states,
                tagnames=tagset(oq.aggregate_by))


def _normalize(kinds, info):
    a = []
    b = []
    stats = info['stats']
    rlzs = False
    for kind in kinds:
        if kind.startswith('rlz-'):
            rlzs = True
            a.append(int(kind[4:]))
            b.append(kind)
        elif kind in stats:
            a.append(stats[kind])
            b.append(kind)
        elif kind == 'stats':
            a.extend(stats.values())
            b.extend(stats)
        elif kind == 'rlzs':
            rlzs = True
            a.extend(range(info['num_rlzs']))
            b.extend(['rlz-%03d' % r for r in range(info['num_rlzs'])])
    return a, b, rlzs


def parse(query_string, info={}):
    """
    :returns: a normalized query_dict as in the following examples:

    >>> parse('kind=stats', {'stats': {'mean': 0, 'max': 1}})
    {'kind': ['mean', 'max'], 'k': [0, 1], 'rlzs': False}
    >>> parse('kind=rlzs', {'stats': {}, 'num_rlzs': 3})
    {'kind': ['rlz-000', 'rlz-001', 'rlz-002'], 'k': [0, 1, 2], 'rlzs': True}
    >>> parse('kind=mean', {'stats': {'mean': 0, 'max': 1}})
    {'kind': ['mean'], 'k': [0], 'rlzs': False}
    >>> parse('kind=rlz-3&imt=PGA&site_id=0', {'stats': {}})
    {'kind': ['rlz-3'], 'imt': ['PGA'], 'site_id': [0], 'k': [3], 'rlzs': True}
    """
    qdic = parse_qs(query_string)
    for key, val in sorted(qdic.items()):
        # convert site_id to an int, loss_type to an int, etc
        if key == 'loss_type':
            qdic[key] = [LOSSID[k] for k in val]
            qdic['lt'] = val
        else:
            qdic[key] = [lit_eval(v) for v in val]
    if info:
        qdic['k'], qdic['kind'], qdic['rlzs'] = _normalize(qdic['kind'], info)
    return qdic


def sanitize(query_string):
    """
    Replace `/`, `?`, `&` characters with underscores and '=' with '-'
    """
    return query_string.replace(
        '/', '_').replace('?', '_').replace('&', '_').replace('=', '-')


def cast(loss_array, loss_dt):
    return loss_array.copy().view(loss_dt).squeeze()


def barray(iterlines):
    """
    Array of bytes
    """
    lst = [line.encode('utf-8') for line in iterlines]
    arr = numpy.array(lst)
    return arr


def avglosses(dstore, loss_types, kind):
    """
    :returns: an array of average losses of shape (A, R, L)
    """
    lst = []
    for loss_type in loss_types:
        lst.append(dstore['avg_losses-%s/%s' % (kind, loss_type)][()])
    # shape L, A, R -> A, R, L
    return numpy.array(lst).transpose(1, 2, 0)


def extract_(dstore, dspath):
    """
    Extracts an HDF5 path object from the datastore, for instance
    extract(dstore, 'sitecol').
    """
    obj = dstore[dspath]
    if isinstance(obj, Dataset):
        return ArrayWrapper(obj[()], obj.attrs)
    elif isinstance(obj, Group):
        return ArrayWrapper(numpy.array(list(obj)), obj.attrs)
    else:
        return obj


class Extract(dict):
    """
    A callable dictionary of functions with a single instance called
    `extract`. Then `extract(dstore, fullkey)` dispatches to the function
    determined by the first part of `fullkey` (a slash-separated
    string) by passing as argument the second part of `fullkey`.

    For instance extract(dstore, 'sitecol').
    """
    def add(self, key, cache=False):
        def decorator(func):
            self[key] = memoized(func) if cache else func
            return func
        return decorator

    def __call__(self, dstore, key):
        if '/' in key:
            k, v = key.split('/', 1)
            data = self[k](dstore, v)
        elif '?' in key:
            k, v = key.split('?', 1)
            data = self[k](dstore, v)
        elif key in self:
            data = self[key](dstore, '')
        else:
            data = extract_(dstore, key)
        if isinstance(data, pandas.DataFrame):
            return data
        return ArrayWrapper.from_(data)


extract = Extract()


@extract.add('oqparam')
def extract_oqparam(dstore, dummy):
    """
    Extract job parameters as a JSON npz. Use it as /extract/oqparam
    """
    js = hdf5.dumps(vars(dstore['oqparam']))
    return ArrayWrapper((), {'json': js})


# used by the QGIS plugin in scenario
@extract.add('realizations')
def extract_realizations(dstore, dummy):
    """
    Extract an array of realizations. Use it as /extract/realizations
    """
    dt = [('rlz_id', U32), ('branch_path', '<S100'), ('weight', F32)]
    oq = dstore['oqparam']
    scenario = 'scenario' in oq.calculation_mode
    rlzs = dstore['full_lt'].rlzs
    # NB: branch_path cannot be of type hdf5.vstr otherwise the conversion
    # to .npz (needed by the plugin) would fail
    arr = numpy.zeros(len(rlzs), dt)
    arr['rlz_id'] = rlzs['ordinal']
    arr['weight'] = rlzs['weight']
    if scenario:
        gsims = dstore.getitem('full_lt/gsim_lt')['uncertainty']
        if 'shakemap' in oq.inputs:
            gsims = ["[FromShakeMap]"]
        # NOTE: repr(gsim) has a form like "b'[ChiouYoungs2008]'"
        arr['branch_path'] = ['"%s"' % repr(gsim)[2:-1].replace('"', '""')
                              for gsim in gsims]  # quotes Excel-friendly
    else:
        arr['branch_path'] = encode(rlzs['branch_path'])
    return arr


@extract.add('weights')
def extract_weights(dstore, what):
    """
    Extract the realization weights
    """
    rlzs = dstore['full_lt'].get_realizations()
    return numpy.array([rlz.weight['weight'] for rlz in rlzs])


@extract.add('gsims_by_trt')
def extract_gsims_by_trt(dstore, what):
    """
    Extract the dictionary gsims_by_trt
    """
    return ArrayWrapper((), dstore['full_lt'].gsim_lt.values)


@extract.add('exposure_metadata')
def extract_exposure_metadata(dstore, what):
    """
    Extract the loss categories and the tags of the exposure.
    Use it as /extract/exposure_metadata
    """
    dic = {}
    dic1, dic2 = dstore['assetcol/tagcol'].__toh5__()
    dic.update(dic1)
    dic.update(dic2)
    if 'asset_risk' in dstore:
        dic['multi_risk'] = sorted(
            set(dstore['asset_risk'].dtype.names) -
            set(dstore['assetcol/array'].dtype.names))
    dic['names'] = [name for name in dstore['assetcol/array'].dtype.names
                    if name.startswith(('value-', 'number', 'occupants'))
                    and name != 'value-occupants']
    return ArrayWrapper((), dict(json=hdf5.dumps(dic)))


@extract.add('assets')
def extract_assets(dstore, what):
    """
    Extract an array of assets, optionally filtered by tag.
    Use it as /extract/assets?taxonomy=RC&taxonomy=MSBC&occupancy=RES
    """
    qdict = parse(what)
    dic = {}
    dic1, dic2 = dstore['assetcol/tagcol'].__toh5__()
    dic.update(dic1)
    dic.update(dic2)
    arr = dstore['assetcol/array'][()]
    for tag, vals in qdict.items():
        cond = numpy.zeros(len(arr), bool)
        for val in vals:
            tagidx, = numpy.where(dic[tag] == val)
            cond |= arr[tag] == tagidx
        arr = arr[cond]
    return ArrayWrapper(arr, dict(json=hdf5.dumps(dic)))


@extract.add('asset_risk')
def extract_asset_risk(dstore, what):
    """
    Extract an array of assets + risk fields, optionally filtered by tag.
    Use it as /extract/asset_risk?taxonomy=RC&taxonomy=MSBC&occupancy=RES
    """
    qdict = parse(what)
    dic = {}
    dic1, dic2 = dstore['assetcol/tagcol'].__toh5__()
    dic.update(dic1)
    dic.update(dic2)
    arr = dstore['asset_risk'][()]
    names = list(arr.dtype.names)
    for i, name in enumerate(names):
        if name == 'id':
            names[i] = 'asset_id'  # for backward compatibility
    arr.dtype.names = names
    for tag, vals in qdict.items():
        cond = numpy.zeros(len(arr), bool)
        for val in vals:
            tagidx, = numpy.where(dic[tag] == val)
            cond |= arr[tag] == tagidx
        arr = arr[cond]
    return ArrayWrapper(arr, dict(json=hdf5.dumps(dic)))


@extract.add('asset_tags')
def extract_asset_tags(dstore, tagname):
    """
    Extract an array of asset tags for the given tagname. Use it as
    /extract/asset_tags or /extract/asset_tags/taxonomy
    """
    tagcol = dstore['assetcol/tagcol']
    if tagname:
        yield tagname, barray(tagcol.gen_tags(tagname))
    for tagname in tagcol.tagnames:
        yield tagname, barray(tagcol.gen_tags(tagname))


def get_sites(sitecol, complete=True):
    """
    :returns:
        a lon-lat or lon-lat-depth array depending if the site collection
        is at sea level or not; if there is a custom_site_id, prepend it
    """
    sc = sitecol.complete if complete else sitecol
    if sc.at_sea_level():
        fields = ['lon', 'lat']
    else:
        fields = ['lon', 'lat', 'depth']
    if 'custom_site_id' in sitecol.array.dtype.names:
        fields.insert(0, 'custom_site_id')
    return sitecol[fields]


def hazard_items(dic, sites, *extras, **kw):
    """
    :param dic: dictionary of arrays of the same shape
    :param sites: a sites array with lon, lat fields of the same length
    :param extras: optional triples (field, dtype, values)
    :param kw: dictionary of parameters (like investigation_time)
    :returns: a list of pairs (key, value) suitable for storage in .npz format
    """
    for item in kw.items():
        yield item
    try:
        field = next(iter(dic))
    except StopIteration:
        return
    arr = dic[field]
    dtlist = [(str(field), arr.dtype) for field in sorted(dic)]
    for field, dtype, values in extras:
        dtlist.append((str(field), dtype))
    array = numpy.zeros(arr.shape, dtlist)
    for field in dic:
        array[field] = dic[field]
    for field, dtype, values in extras:
        array[field] = values
    yield 'all', util.compose_arrays(sites, array)


def _get_dict(dstore, name, imtls, stats):
    dic = {}
    dtlist = []
    for imt, imls in imtls.items():
        dt = numpy.dtype([(str(iml), F32) for iml in imls])
        dtlist.append((imt, dt))
    for s, stat in enumerate(stats):
        dic[stat] = dstore[name][:, s].flatten().view(dtlist)
    return dic


@extract.add('sitecol')
def extract_sitecol(dstore, what):
    """
    Extracts the site collection array (not the complete object, otherwise it
    would need to be pickled).
    Use it as /extract/sitecol?field=vs30
    """
    qdict = parse(what)
    if 'field' in qdict:
        [f] = qdict['field']
        return dstore['sitecol'][f]
    return dstore['sitecol'].array


def _items(dstore, name, what, info):
    params = parse(what, info)
    filt = {}
    if 'site_id' in params:
        filt['site_id'] = params['site_id'][0]
    if 'imt' in params:
        [imt] = params['imt']
        filt['imt'] = imt
    if params['rlzs']:
        for k in params['k']:
            filt['rlz_id'] = k
            yield 'rlz-%03d' % k, dstore.sel(name + '-rlzs', **filt)[:, 0]
    else:
        stats = list(info['stats'])
        for k in params['k']:
            filt['stat'] = stat = stats[k]
            yield stat, dstore.sel(name + '-stats', **filt)[:, 0]
    yield from params.items()


@extract.add('hcurves')
def extract_hcurves(dstore, what):
    """
    Extracts hazard curves. Use it as /extract/hcurves?kind=mean&imt=PGA or
    /extract/hcurves?kind=rlz-0&imt=SA(1.0)
    """
    info = get_info(dstore)
    if what == '':  # npz exports for QGIS
        sitecol = dstore['sitecol']
        sites = get_sites(sitecol, complete=False)
        dic = _get_dict(dstore, 'hcurves-stats', info['imtls'], info['stats'])
        yield from hazard_items(
            dic, sites, investigation_time=info['investigation_time'])
        return
    yield from _items(dstore, 'hcurves', what, info)


@extract.add('hmaps')
def extract_hmaps(dstore, what):
    """
    Extracts hazard maps. Use it as /extract/hmaps?imt=PGA
    """
    info = get_info(dstore)
    if what == '':  # npz exports for QGIS
        sitecol = dstore['sitecol']
        sites = get_sites(sitecol, complete=False)
        dic = _get_dict(dstore, 'hmaps-stats',
                        {imt: info['poes'] for imt in info['imtls']},
                        info['stats'])
        yield from hazard_items(
            dic, sites, investigation_time=info['investigation_time'])
        return
    yield from _items(dstore, 'hmaps', what, info)


@extract.add('uhs')
def extract_uhs(dstore, what):
    """
    Extracts uniform hazard spectra. Use it as /extract/uhs?kind=mean or
    /extract/uhs?kind=rlz-0, etc
    """
    info = get_info(dstore)
    if what == '':  # npz exports for QGIS
        sitecol = dstore['sitecol']
        sites = get_sites(sitecol, complete=False)
        dic = {}
        for stat, s in info['stats'].items():
            hmap = dstore['hmaps-stats'][:, s]  # shape (N, M, P)
            dic[stat] = calc.make_uhs(hmap, info)
        yield from hazard_items(
            dic, sites, investigation_time=info['investigation_time'])
        return
    for k, v in _items(dstore, 'hmaps', what, info):  # shape (N, M, P)
        if hasattr(v, 'shape') and len(v.shape) == 3:
            yield k, calc.make_uhs(v, info)
        else:
            yield k, v


@extract.add('effect')
def extract_effect(dstore, what):
    """
    Extracts the effect of ruptures. Use it as /extract/effect
    """
    grp = dstore['effect_by_mag_dst_trt']
    dist_bins = dict(grp.attrs)
    ndists = len(dist_bins[next(iter(dist_bins))])
    arr = numpy.zeros((len(grp), ndists, len(dist_bins)))
    for i, mag in enumerate(grp):
        arr[i] = dstore['effect_by_mag_dst_trt/' + mag][()]
    return ArrayWrapper(arr, dict(dist_bins=dist_bins, ndists=ndists,
                                  mags=[float(mag) for mag in grp]))


@extract.add('rups_by_mag_dist')
def extract_rups_by_mag_dist(dstore, what):
    """
    Extracts the number of ruptures by mag, dist.
    Use it as /extract/rups_by_mag_dist
    """
    return extract_effect(dstore, 'rups_by_mag_dist')


# for debugging classical calculations with few sites
@extract.add('rup_ids')
def extract_rup_ids(dstore, what):
    """
    Extract src_id, rup_id from the stored contexts
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/rup_ids
    """
    n = len(dstore['rup/grp_id'])
    data = numpy.zeros(n, [('src_id', U32), ('rup_id', U32)])
    data['src_id'] = dstore['rup/src_id'][:]
    data['rup_id'] = dstore['rup/rup_id'][:]
    data = numpy.unique(data)
    return data


# for debugging classical calculations with few sites
@extract.add('mean_by_rup')
def extract_mean_by_rup(dstore, what):
    """
    Extract src_id, rup_id, mean from the stored contexts
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/mean_by_rup
    """
    N = len(dstore['sitecol'])
    assert N == 1
    out = []
    for cmaker in read_cmakers(dstore):
        for ctx in cmaker.read_ctxs(dstore):
            # shape (4, G, M, U) => U
            means = cmaker.get_mean_stds([ctx])[0].mean(axis=(0, 1))
            out.extend(zip(ctx.src_id, ctx.rup_id, means))
    out.sort(key=operator.itemgetter(0, 1))
    return numpy.array(out, [('src_id', U32), ('rup_id', U32), ('mean', F64)])


@extract.add('source_data')
def extract_source_data(dstore, what):
    """
    Extract performance information about the sources.
    Use it as /extract/source_data?
    """
    qdict = parse(what)
    if 'taskno' in qdict:
        sel = {'taskno': int(qdict['taskno'][0])}
    else:
        sel = {}
    df = dstore.read_df('source_data', 'src_id', sel=sel).sort_values('ctimes')
    dic = {col: df[col].to_numpy() for col in df.columns}
    return ArrayWrapper(df.index.to_numpy(), dic)


@extract.add('sources')
def extract_sources(dstore, what):
    """
    Extract information about a source model.
    Use it as /extract/sources?limit=10
    or /extract/sources?source_id=1&source_id=2
    or /extract/sources?code=A&code=B
    """
    qdict = parse(what)
    limit = int(qdict.get('limit', ['100'])[0])
    source_ids = qdict.get('source_id', None)
    if source_ids is not None:
        source_ids = [str(source_id) for source_id in source_ids]
    codes = qdict.get('code', None)
    if codes is not None:
        codes = [code.encode('utf8') for code in codes]
    fields = 'source_id code num_sites num_ruptures'
    info = dstore['source_info'][()][fields.split()]
    wkt = decode(dstore['source_wkt'][()])
    arrays = []
    if source_ids is not None:
        logging.info('Extracting sources with ids: %s', source_ids)
        info = info[numpy.isin(info['source_id'], source_ids)]
        if len(info) == 0:
            raise getters.NotFound(
                'There is no source with id %s' % source_ids)
    if codes is not None:
        logging.info('Extracting sources with codes: %s', codes)
        info = info[numpy.isin(info['code'], codes)]
        if len(info) == 0:
            raise getters.NotFound(
                'There is no source with code in %s' % codes)
    for code, rows in general.group_array(info, 'code').items():
        if limit < len(rows):
            logging.info('Code %s: extracting %d sources out of %s',
                         code, limit, len(rows))
        arrays.append(rows[:limit])
    if not arrays:
        raise ValueError('There  no sources')
    info = numpy.concatenate(arrays)
    wkt_gz = gzip.compress(';'.join(wkt).encode('utf8'))
    src_gz = gzip.compress(';'.join(decode(info['source_id'])).encode('utf8'))
    oknames = [name for name in info.dtype.names  # avoid pickle issues
               if name not in ('source_id', 'trt_smrs')]
    arr = numpy.zeros(len(info), [(n, info.dtype[n]) for n in oknames])
    for n in oknames:
        arr[n] = info[n]
    return ArrayWrapper(arr, {'wkt_gz': wkt_gz, 'src_gz': src_gz})


@extract.add('gridded_sources')
def extract_gridded_sources(dstore, what):
    """
    Extract information about the gridded sources (requires ps_grid_spacing)
    Use it as /extract/gridded_sources?task_no=0.
    Returns a json string id -> lonlats
    """
    qdict = parse(what)
    task_no = int(qdict.get('task_no', ['0'])[0])
    dic = {}
    for i, lonlats in enumerate(dstore['ps_grid/%02d' % task_no][()]):
        dic[i] = numpy.round(F64(lonlats), 3)
    return ArrayWrapper((), {'json': hdf5.dumps(dic)})


@extract.add('task_info')
def extract_task_info(dstore, what):
    """
    Extracts the task distribution. Use it as /extract/task_info?kind=classical
    """
    dic = group_array(dstore['task_info'][()], 'taskname')
    if 'kind' in what:
        name = parse(what)['kind'][0]
        yield name, dic[encode(name)]
        return
    for name in dic:
        yield decode(name), dic[name]


def _agg(losses, idxs):
    shp = losses.shape[1:]
    if not idxs:
        # no intersection, return a 0-dim matrix
        return numpy.zeros((0,) + shp, losses.dtype)
    # numpy.array wants lists, not sets, hence the sorted below
    return losses[numpy.array(sorted(idxs))].sum(axis=0)


def _filter_agg(assetcol, losses, selected, stats=''):
    # losses is an array of shape (A, ..., R) with A=#assets, R=#realizations
    aids_by_tag = assetcol.get_aids_by_tag()
    idxs = set(range(len(assetcol)))
    tagnames = []
    for tag in selected:
        tagname, tagvalue = tag.split('=', 1)
        if tagvalue == '*':
            tagnames.append(tagname)
        else:
            idxs &= aids_by_tag[tag]
    if len(tagnames) > 1:
        raise ValueError('Too many * as tag values in %s' % tagnames)
    elif not tagnames:  # return an array of shape (..., R)
        return ArrayWrapper(
            _agg(losses, idxs), dict(selected=encode(selected), stats=stats))
    else:  # return an array of shape (T, ..., R)
        [tagname] = tagnames
        _tags = list(assetcol.tagcol.gen_tags(tagname))
        all_idxs = [idxs & aids_by_tag[t] for t in _tags]
        # NB: using a generator expression for all_idxs caused issues (?)
        data, tags = [], []
        for idxs, tag in zip(all_idxs, _tags):
            agglosses = _agg(losses, idxs)
            if len(agglosses):
                data.append(agglosses)
                tags.append(tag)
        return ArrayWrapper(
            numpy.array(data),
            dict(selected=encode(selected), tags=encode(tags), stats=stats))


def get_loss_type_tags(what):
    try:
        loss_type, query_string = what.rsplit('?', 1)
    except ValueError:  # no question mark
        loss_type, query_string = what, ''
    tags = query_string.split('&') if query_string else []
    return loss_type, tags


# probably not used
@extract.add('csq_curves')
def extract_csq_curves(dstore, what):
    """
    Aggregate damages curves from the event_based_damage calculator:

    /extract/csq_curves?agg_id=0&loss_type=occupants

    Returns an ArrayWrapper of shape (P, D1) with attribute return_periods
    """
    info = get_info(dstore)
    qdic = parse(what + '&kind=mean', info)
    [li] = qdic['loss_type']  # loss type index
    [agg_id] = qdic.get('agg_id', [0])
    df = dstore.read_df('aggcurves', 'return_period',
                        dict(agg_id=agg_id, loss_id=li))
    cols = [col for col in df.columns if col not in 'agg_id loss_id']
    return ArrayWrapper(df[cols].to_numpy(),
                        dict(return_period=df.index.to_numpy(),
                             consequences=cols))


# NB: used by QGIS but not by the exporters
# tested in test_case_1_ins
@extract.add('agg_curves')
def extract_agg_curves(dstore, what):
    """
    Aggregate loss curves from the ebrisk calculator:

    /extract/agg_curves?kind=stats&absolute=1&loss_type=occupants&occupancy=RES

    Returns an array of shape (#periods, #stats) or (#periods, #rlzs)
    """
    info = get_info(dstore)
    qdic = parse(what, info)
    tagdict = qdic.copy()
    for a in ('k', 'rlzs', 'kind', 'loss_type', 'absolute'):
        del tagdict[a]
    k = qdic['k']  # rlz or stat index
    lts = tagdict.pop('lt')  # loss type string
    [l] = qdic['loss_type']  # loss type index
    tagnames = list(tagdict)
    if set(tagnames) != info['tagnames']:
        raise ValueError('Expected tagnames=%s, got %s' %
                         (info['tagnames'], tagnames))
    tagvalues = [tagdict[t][0] for t in tagnames]
    if tagnames:
        lst = decode(dstore['agg_keys'][:])
        agg_id = lst.index(','.join(tagvalues))
    else:
        agg_id = 0  # total aggregation
    if qdic['rlzs']:
        [li] = qdic['loss_type']  # loss type index
        units = dstore.get_attr('aggcurves', 'units').split()
        df = dstore.read_df('aggcurves', sel=dict(agg_id=agg_id, loss_id=li))
        rps = list(df.return_period.unique())
        P = len(rps)
        oq = dstore['oqparam']
        if oq.collect_rlzs:
            R = 1
            qdic['kind'] = ['collected_rlzs']
        else:
            R = len(qdic['kind'])
        arr = numpy.zeros((P, R))
        for rlz in df.rlz_id.unique():
            # NB: df may contains zeros but there are no missing periods
            # by construction (see build_aggcurves)
            arr[:, rlz] = df[df.rlz_id == rlz].loss
    else:
        name = 'agg_curves-stats/' + lts[0]
        shape_descr = hdf5.get_shape_descr(dstore.get_attr(name, 'json'))
        rps = list(shape_descr['return_period'])
        units = dstore.get_attr(name, 'units').split()
        arr = dstore[name][agg_id, k].T  # shape P, R
    if qdic['absolute'] == [1]:
        pass
    elif qdic['absolute'] == [0]:
        evalue, = dstore['agg_values'][agg_id][lts]
        arr /= evalue
    else:
        raise ValueError('"absolute" must be 0 or 1 in %s' % what)
    attrs = dict(shape_descr=['return_period', 'kind'] + tagnames)
    attrs['return_period'] = rps
    attrs['kind'] = qdic['kind']
    attrs['units'] = units  # used by the QGIS plugin
    for tagname, tagvalue in zip(tagnames, tagvalues):
        attrs[tagname] = [tagvalue]
    if tagnames:
        arr = arr.reshape(arr.shape + (1,) * len(tagnames))
    return ArrayWrapper(arr, dict(json=hdf5.dumps(attrs)))


@extract.add('agg_losses')
def extract_agg_losses(dstore, what):
    """
    Aggregate losses of the given loss type and tags. Use it as
    /extract/agg_losses/structural?taxonomy=RC&custom_site_id=20126
    /extract/agg_losses/structural?taxonomy=RC&custom_site_id=*

    :returns:
        an array of shape (T, R) if one of the tag names has a `*` value
        an array of shape (R,), being R the number of realizations
        an array of length 0 if there is no data for the given tags
    """
    loss_type, tags = get_loss_type_tags(what)
    if not loss_type:
        raise ValueError('loss_type not passed in agg_losses/<loss_type>')
    if 'avg_losses-stats/' + loss_type in dstore:
        stats = list(dstore['oqparam'].hazard_stats())
        losses = dstore['avg_losses-stats/' + loss_type][:]
    elif 'avg_losses-rlzs/' + loss_type in dstore:
        stats = ['mean']
        losses = dstore['avg_losses-rlzs/' + loss_type][:]
    else:
        raise KeyError('No losses found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], losses, tags, stats)


@extract.add('agg_damages')
def extract_agg_damages(dstore, what):
    """
    Aggregate damages of the given loss type and tags. Use it as
    /extract/agg_damages/structural?taxonomy=RC&custom_site_id=20126

    :returns:
        array of shape (R, D), being R the number of realizations and D the
        number of damage states, or an array of length 0 if there is no data
        for the given tags
    """
    loss_type, tags = get_loss_type_tags(what)
    if 'damages-rlzs' in dstore:
        oq = dstore['oqparam']
        lti = oq.lti[loss_type]
        D = len(oq.limit_states) + 1
        damages = dstore['damages-rlzs'][:, :, lti]
    else:
        raise KeyError('No damages found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], damages, tags)


@extract.add('aggregate')
def extract_aggregate(dstore, what):
    """
    /extract/aggregate/avg_losses?
    kind=mean&loss_type=structural&tag=taxonomy&tag=occupancy
    """
    name, qstring = what.split('?', 1)
    info = get_info(dstore)
    qdic = parse(qstring, info)
    suffix = '-rlzs' if qdic['rlzs'] else '-stats'
    tagnames = qdic.get('tag', [])
    assetcol = dstore['assetcol']
    loss_types = info['loss_types']
    ridx = qdic['k'][0]
    lis = qdic.get('loss_type', [])  # list of indices
    if lis:
        lt = LOSSTYPE[lis[0]]
        array = dstore['avg_losses%s/%s' % (suffix, lt)][:, ridx]
        aw = ArrayWrapper(assetcol.aggregateby(tagnames, array), {}, [lt])
    else:
        array = avglosses(dstore, loss_types, suffix[1:])[:, ridx]
        aw = ArrayWrapper(assetcol.aggregateby(tagnames, array), {},
                          loss_types)
    for tagname in tagnames:
        setattr(aw, tagname, getattr(assetcol.tagcol, tagname)[1:])
    aw.shape_descr = tagnames
    return aw


@extract.add('losses_by_asset')
def extract_losses_by_asset(dstore, what):
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt(F32)
    rlzs = dstore['full_lt'].get_realizations()
    stats = oq.hazard_stats()  # statname -> statfunc
    assets = util.get_assets(dstore)
    if 'losses_by_asset' in dstore:
        losses_by_asset = dstore['losses_by_asset'][()]
        for rlz in rlzs:
            # I am exporting the 'mean' and ignoring the 'stddev'
            losses = cast(losses_by_asset[:, rlz.ordinal]['mean'], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield 'rlz-%03d' % rlz.ordinal, data
    elif 'avg_losses-stats' in dstore:
        # only QGIS is testing this
        avg_losses = avglosses(dstore, loss_dt.names, 'stats')  # shape ASL
        for s, stat in enumerate(stats):
            losses = cast(avg_losses[:, s], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield stat, data
    elif 'avg_losses-rlzs' in dstore:  # there is only one realization
        avg_losses = avglosses(dstore, loss_dt.names, 'rlzs')
        losses = cast(avg_losses, loss_dt)
        data = util.compose_arrays(assets, losses)
        yield 'rlz-000', data


def _gmf(df, num_sites, imts):
    # convert data into the composite array expected by QGIS
    gmfa = numpy.zeros(num_sites, [(imt, F32) for imt in imts])
    for m, imt in enumerate(imts):
        gmfa[imt][U32(df.sid)] = df[f'gmv_{m}']
    return gmfa


# used by the QGIS plugin for a single eid
@extract.add('gmf_data')
def extract_gmf_npz(dstore, what):
    oq = dstore['oqparam']
    qdict = parse(what)
    [eid] = qdict.get('event_id', [0])  # there must be a single event
    rlzi = dstore['events'][eid]['rlz_id']
    sites = get_sites(dstore['sitecol'])
    n = len(sites)
    try:
        df = dstore.read_df('gmf_data', 'eid').loc[eid]
    except KeyError:
        # zero GMF
        yield 'rlz-%03d' % rlzi, []
    else:
        gmfa = _gmf(df, n, oq.imtls)
        yield 'rlz-%03d' % rlzi, util.compose_arrays(sites, gmfa)


@extract.add('avg_gmf')
def extract_avg_gmf(dstore, what):
    qdict = parse(what)
    info = get_info(dstore)
    [imt] = qdict['imt']
    imti = info['imt'][imt]
    sitecol = dstore['sitecol']
    avg_gmf = dstore['avg_gmf'][0, :, imti]
    yield imt, avg_gmf[sitecol.sids]
    yield 'sids', sitecol.sids
    yield 'lons', sitecol.lons
    yield 'lats', sitecol.lats


@extract.add('num_events')
def extract_num_events(dstore, what):
    """
    :returns: the number of events (if any)
    """
    yield 'num_events', len(dstore['events'])


def build_damage_dt(dstore):
    """
    :param dstore: a datastore instance
    :returns:
       a composite dtype loss_type -> (ds1, ds2, ...)
    """
    oq = dstore['oqparam']
    attrs = json.loads(dstore.get_attr('damages-rlzs', 'json'))
    limit_states = list(dstore.get_attr('crm', 'limit_states'))
    csqs = attrs['dmg_state'][len(limit_states) + 1:]  # consequences
    dt_list = [(ds, F32) for ds in ['no_damage'] + limit_states + csqs]
    damage_dt = numpy.dtype(dt_list)
    loss_types = oq.loss_dt().names
    return numpy.dtype([(lt, damage_dt) for lt in loss_types])


def build_csq_dt(dstore):
    """
    :param dstore: a datastore instance
    :returns:
       a composite dtype loss_type -> (csq1, csq2, ...)
    """
    oq = dstore['oqparam']
    attrs = json.loads(dstore.get_attr('damages-rlzs', 'json'))
    limit_states = list(dstore.get_attr('crm', 'limit_states'))
    csqs = attrs['dmg_state'][len(limit_states) + 1:]  # consequences
    dt = numpy.dtype([(csq, F32) for csq in csqs])
    loss_types = oq.loss_dt().names
    return numpy.dtype([(lt, dt) for lt in loss_types])


def build_damage_array(data, damage_dt):
    """
    :param data: an array of shape (A, L, D)
    :param damage_dt: a damage composite data type loss_type -> states
    :returns: a composite array of length N and dtype damage_dt
    """
    A, L, D = data.shape
    dmg = numpy.zeros(A, damage_dt)
    for a in range(A):
        for li, lt in enumerate(damage_dt.names):
            dmg[lt][a] = tuple(data[a, li])
    return dmg


@extract.add('damages-rlzs')
def extract_damages_npz(dstore, what):
    oq = dstore['oqparam']
    damage_dt = build_damage_dt(dstore)
    rlzs = dstore['full_lt'].get_realizations()
    if oq.collect_rlzs:
        rlzs = [Mock(ordinal=0)]
    data = dstore['damages-rlzs']
    assets = util.get_assets(dstore)
    for rlz in rlzs:
        damages = build_damage_array(data[:, rlz.ordinal], damage_dt)
        yield 'rlz-%03d' % rlz.ordinal, util.compose_arrays(
            assets, damages)


# tested on oq-risk-tests event_based/etna
@extract.add('event_based_mfd')
def extract_mfd(dstore, what):
    """
    Compare n_occ/eff_time with occurrence_rate.
    Example: http://127.0.0.1:8800/v1/calc/30/extract/event_based_mfd?
    """
    oq = dstore['oqparam']
    R = len(dstore['weights'])
    eff_time = oq.investigation_time * oq.ses_per_logic_tree_path * R
    rup_df = dstore.read_df('ruptures', 'id')
    dic = dict(mag=[], freq=[], occ_rate=[])
    for mag, df in rup_df.groupby('mag'):
        dic['mag'].append(round(mag, 2))
        dic['freq'].append(df.n_occ.sum() / eff_time)
        dic['occ_rate'].append(df.occurrence_rate.sum())
    return ArrayWrapper((), {k: numpy.array(v) for k, v in dic.items()})


@extract.add('mean_std_curves')
def extract_mean_std_curves(dstore, what):
    """
    Yield imls/IMT and poes/IMT containg mean and stddev for all sites
    """
    rlzs = dstore['full_lt'].get_realizations()
    w = [rlz.weight for rlz in rlzs]
    getter = getters.PmapGetter(dstore, w)
    arr = getter.get_mean().array
    for imt in getter.imtls:
        yield 'imls/' + imt, getter.imtls[imt]
        yield 'poes/' + imt, arr[:, getter.imtls(imt)]


@extract.add('composite_risk_model.attrs')
def crm_attrs(dstore, what):
    """
    :returns:
        the attributes of the risk model, i.e. limit_states, loss_types,
        min_iml and covs, needed by the risk exporters.
    """
    attrs = dstore.get_attrs('crm')
    return ArrayWrapper((), dict(json=hdf5.dumps(attrs)))


def _get(dstore, name):
    try:
        dset = dstore[name + '-stats']
        return dset, list(dstore['oqparam'].hazard_stats())
    except KeyError:  # single realization
        return dstore[name + '-rlzs'], ['mean']


@extract.add('events')
def extract_relevant_events(dstore, dummy=None):
    """
    Extract the relevant events
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/events
    """
    all_events = dstore['events'][:]
    if 'relevant_events' not in dstore:
        all_events.sort(order='id')
        return all_events
    rel_events = dstore['relevant_events'][:]
    events = all_events[rel_events]
    events.sort(order='id')
    return events


@extract.add('event_info')
def extract_event_info(dstore, eidx):
    """
    Extract information about the given event index.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/event_info/0
    """
    event = dstore['events'][int(eidx)]
    ridx = event['rup_id']
    [getter] = getters.get_rupture_getters(dstore, slc=slice(ridx, ridx + 1))
    rupdict = getter.get_rupdict()
    rlzi = event['rlz_id']
    full_lt = dstore['full_lt']
    rlz = full_lt.get_realizations()[rlzi]
    gsim = full_lt.gsim_by_trt(rlz)[rupdict['trt']]
    for key, val in rupdict.items():
        yield key, val
    yield 'rlzi', rlzi
    yield 'gsim', repr(gsim)


@extract.add('extreme_event')
def extract_extreme_event(dstore, eidx):
    """
    Extract information about the given event index.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/extreme_event
    """
    arr = dstore['gmf_data/gmv_0'][()]
    idx = arr.argmax()
    eid = dstore['gmf_data/eid'][idx]
    dic = dict(extract_event_info(dstore, eid))
    dic['gmv'] = arr[idx]
    return dic


@extract.add('ruptures_within')
def get_ruptures_within(dstore, bbox):
    """
    Extract the ruptures within the given bounding box, a string
    minlon,minlat,maxlon,maxlat.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/ruptures_with/8,44,10,46
    """
    minlon, minlat, maxlon, maxlat = map(float, bbox.split(','))
    hypo = dstore['ruptures']['hypo'].T  # shape (3, N)
    mask = ((minlon <= hypo[0]) * (minlat <= hypo[1]) *
            (maxlon >= hypo[0]) * (maxlat >= hypo[1]))
    return dstore['ruptures'][mask]


@extract.add('disagg')
def extract_disagg(dstore, what):
    """
    Extract a disaggregation output as a 2D array.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/
    disagg?kind=Mag_Dist&imt=PGA&poe_id=0&site_id=1&traditional=1
    """
    qdict = parse(what)
    label = qdict['kind'][0]
    imt = qdict['imt'][0]
    poe_id = int(qdict['poe_id'][0])
    sid = int(qdict['site_id'][0])
    traditional = qdict.get('traditional')

    def get(v, sid):
        if len(v.shape) == 2:
            return v[sid]
        return v[:]
    oq = dstore['oqparam']
    imt2m = {imt: m for m, imt in enumerate(oq.imtls)}
    bins = {k: get(v, sid) for k, v in dstore['disagg-bins'].items()}
    m = imt2m[imt]
    matrix = dstore['disagg/' + label][sid, m, poe_id]  # shape (..., Z)
    poe_agg = dstore['poe4'][sid, m, poe_id]
    Z = len(poe_agg)
    if traditional and traditional != '0':
        if matrix.any():  # nonzero
            matrix = numpy.log(1. - matrix) / numpy.log(1. - poe_agg)

    # adapted from the nrml_converters
    disag_tup = tuple(label.split('_'))
    axis = [bins[k] for k in disag_tup]

    # compute axis mid points, except for the TRT axis
    axis = [(ax[: -1] + ax[1:]) / 2. if ax.dtype != object
            else ax for ax in axis]
    if len(axis) == 1:  # i.e. Mag or Dist
        values = numpy.array([axis[0]] + list(matrix.T))  # i.e. shape (2, 3)
    else:  # i.e. Mag_Dist
        # axis = [[5.5, 6.5, 7.5], [12.5, 37.5, 62.5, 87.5]]
        grids = numpy.meshgrid(*axis, indexing='ij')
        # with the 2 axis above there are 2 grids of shape (3, 4) each
        values = [g.flatten() for g in grids] + [matrix[..., z].flatten()
                                                 for z in range(Z)]
        # list of arrays of lenghts [12, 12, 12]
        values = numpy.array(values)  # shape (3, 12)
    attrs = qdict.copy()
    for k in disag_tup:
        attrs[k] = bins[k]
    attrs['kind'] = disag_tup
    attrs['rlzs'] = dstore['best_rlzs'][sid]
    weights = numpy.array([dstore['weights'][r] for r in attrs['rlzs']])
    weights /= weights.sum()
    attrs['weights'] = weights
    return ArrayWrapper(values.T, attrs)


def _disagg_output_dt(shapedic, disagg_outputs, imts, poes_disagg):
    dt = [('site_id', U32), ('lon', F32), ('lat', F32),
          ('lon_bins', (F32, shapedic['lon'] + 1)),
          ('lat_bins', (F32, shapedic['lat'] + 1))]
    Z = shapedic['Z']
    for out in disagg_outputs:
        shp = tuple(shapedic[key] for key in out.lower().split('_'))
        for imt in imts:
            for poe in poes_disagg:
                dt.append(('%s-%s-%s' % (out, imt, poe), (F32, shp)))
    for imt in imts:
        for poe in poes_disagg:
            dt.append(('iml-%s-%s' % (imt, poe), (F32, (Z,))))
    return dt


def norm(qdict, params):
    dic = {}
    for par in params:
        dic[par] = int(qdict[par][0]) if par in qdict else 0
    return dic


@extract.add('disagg_by_src')
def extract_disagg_by_src(dstore, what):
    """
    Extract the disagg_by_src information.
    Example: http://127.0.0.1:8800/v1/calc/30/extract/disagg_by_src?site_id=0&imt=PGA&poe=.001
    """
    qdict = parse(what)
    dset = dstore['disagg_by_src']
    oq = dstore['oqparam']
    attr = hdf5.get_shape_descr(dset.attrs['json'])
    src_id = attr['src_id']
    [imt] = qdict['imt']
    [poe] = qdict['poe']
    [site_id] = qdict.get('site_id', ['0'])
    site_id = int(site_id)
    mean = dstore.sel('hcurves-stats', imt=imt, stat='mean', site_id=site_id)[0, 0, 0]
    lvl_id = calc.get_lvl(mean, oq.imtls[imt], float(poe))
    imt_id = list(oq.imtls).index(imt)
    poes = dset[site_id, :, imt_id, lvl_id]  # shape (R, Ns)
    if oq.collect_rlzs:  # already averaged
        poes = poes[0, :]
    else:  # compute the average
        poes = dstore['weights'][:] @ poes
    arr = numpy.zeros(len(src_id), [('src_id', '<S16'), ('poe', '<f8')])
    arr['src_id'] = src_id
    arr['poe'] = poes[:len(src_id)]
    arr.sort(order='poe')
    return ArrayWrapper(arr[::-1], dict(site_id=site_id, imt=imt, poe=poe))


@extract.add('disagg_layer')
def extract_disagg_layer(dstore, what):
    """
    Extract a disaggregation layer containing all sites and outputs
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/disagg_layer?
    """
    qdict = parse(what)
    oq = dstore['oqparam']
    oq.maximum_distance = filters.IntegrationDistance(oq.maximum_distance)
    if 'kind' in qdict:
        kinds = qdict['kind']
    else:
        kinds = oq.disagg_outputs
    sitecol = dstore['sitecol']
    poes_disagg = oq.poes_disagg or (None,)
    realizations = numpy.array(dstore['full_lt'].get_realizations())
    edges, shapedic = disagg.get_edges_shapedic(
        oq, sitecol, dstore['source_mags'], len(realizations))
    dt = _disagg_output_dt(shapedic, kinds, oq.imtls, poes_disagg)
    out = numpy.zeros(len(sitecol), dt)
    hmap4 = dstore['hmap4'][:]
    best_rlzs = dstore['best_rlzs'][:]
    arr = {kind: dstore['disagg/' + kind][:] for kind in kinds}
    for sid, lon, lat, rec in zip(
            sitecol.sids, sitecol.lons, sitecol.lats, out):
        rlzs = realizations[best_rlzs[sid]]
        rec['site_id'] = sid
        rec['lon'] = lon
        rec['lat'] = lat
        rec['lon_bins'] = edges[2][sid]
        rec['lat_bins'] = edges[3][sid]
        for m, imt in enumerate(oq.imtls):
            ws = numpy.array([rlz.weight[imt] for rlz in rlzs])
            ws /= ws.sum()  # normalize to 1
            for p, poe in enumerate(poes_disagg):
                for kind in kinds:
                    key = '%s-%s-%s' % (kind, imt, poe)
                    rec[key] = arr[kind][sid, m, p] @ ws
                rec['iml-%s-%s' % (imt, poe)] = hmap4[sid, m, p]
    return ArrayWrapper(out, dict(mag=edges[0], dist=edges[1], eps=edges[-2],
                                  trt=numpy.array(encode(edges[-1]))))

# ######################### extracting ruptures ##############################


class RuptureData(object):
    """
    Container for information about the ruptures of a given
    tectonic region type.
    """
    def __init__(self, trt, gsims):
        self.trt = trt
        self.cmaker = ContextMaker(trt, gsims, {'imtls': {}})
        self.params = sorted(self.cmaker.REQUIRES_RUPTURE_PARAMETERS -
                             set('mag strike dip rake hypo_depth'.split()))
        self.dt = numpy.dtype([
            ('rup_id', U32), ('source_id', SOURCE_ID), ('multiplicity', U32),
            ('occurrence_rate', F64),
            ('mag', F32), ('lon', F32), ('lat', F32), ('depth', F32),
            ('strike', F32), ('dip', F32), ('rake', F32),
            ('boundaries', hdf5.vfloat32)] +
            [(param, F32) for param in self.params])

    def to_array(self, proxies):
        """
        Convert a list of rupture proxies into an array of dtype RuptureRata.dt
        """
        data = []
        for proxy in proxies:
            ebr = proxy.to_ebr(self.trt)
            rup = ebr.rupture
            ctx = self.cmaker.make_rctx(rup)
            ruptparams = tuple(getattr(ctx, param) for param in self.params)
            point = rup.surface.get_middle_point()
            boundaries = rup.surface.get_surface_boundaries_3d()
            try:
                rate = ebr.rupture.occurrence_rate
            except AttributeError:  # for nonparametric sources
                rate = numpy.nan
            data.append(
                (ebr.id, ebr.source_id, ebr.n_occ, rate,
                 rup.mag, point.x, point.y, point.z, rup.surface.get_strike(),
                 rup.surface.get_dip(), rup.rake, boundaries) + ruptparams)
        return numpy.array(data, self.dt)


@extract.add('rupture_info')
def extract_rupture_info(dstore, what):
    """
    Extract some information about the ruptures, including the boundary.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/rupture_info?min_mag=6
    """
    qdict = parse(what)
    if 'min_mag' in qdict:
        [min_mag] = qdict['min_mag']
    else:
        min_mag = 0
    oq = dstore['oqparam']
    dtlist = [('rup_id', U32), ('multiplicity', U32), ('mag', F32),
              ('centroid_lon', F32), ('centroid_lat', F32),
              ('centroid_depth', F32), ('trt', '<S50'),
              ('strike', F32), ('dip', F32), ('rake', F32)]
    rows = []
    boundaries = []
    for rgetter in getters.get_rupture_getters(dstore):
        proxies = rgetter.get_proxies(min_mag)
        rup_data = RuptureData(rgetter.trt, rgetter.rlzs_by_gsim)
        for r in rup_data.to_array(proxies):
            coords = ['%.5f %.5f' % xyz[:2] for xyz in zip(*r['boundaries'])]
            coordset = sorted(set(coords))
            if len(coordset) < 4:   # degenerate to line
                boundaries.append('LINESTRING(%s)' % ', '.join(coordset))
            else:  # good polygon
                boundaries.append('POLYGON((%s))' % ', '.join(coords))
            rows.append(
                (r['rup_id'], r['multiplicity'], r['mag'],
                 r['lon'], r['lat'], r['depth'],
                 rgetter.trt, r['strike'], r['dip'], r['rake']))
    arr = numpy.array(rows, dtlist)
    geoms = gzip.compress('\n'.join(boundaries).encode('utf-8'))
    return ArrayWrapper(arr, dict(investigation_time=oq.investigation_time,
                                  boundaries=geoms))


@extract.add('ruptures')
def extract_ruptures(dstore, what):
    """
    Extract the ruptures with their geometry as a big CSV string
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/ruptures?min_mag=6
    """
    qdict = parse(what)
    if 'min_mag' in qdict:
        [min_mag] = qdict['min_mag']
    else:
        min_mag = 0
    bio = io.StringIO()
    first = True
    trts = list(dstore.getitem('full_lt').attrs['trts'])
    for rgetter in getters.get_rupture_getters(dstore):
        rups = [rupture._get_rupture(proxy.rec, proxy.geom, rgetter.trt)
                for proxy in rgetter.get_proxies(min_mag)]
        arr = rupture.to_csv_array(rups)
        if first:
            header = None
            comment = dict(trts=trts)
            first = False
        else:
            header = 'no-header'
            comment = None
        writers.write_csv(bio, arr, header=header, comment=comment)
    return bio.getvalue()


@extract.add('eids_by_gsim')
def extract_eids_by_gsim(dstore, what):
    """
    Returns a dictionary gsim -> event_ids for the first TRT
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/eids_by_gsim
    """
    rlzs = dstore['full_lt'].get_realizations()
    gsims = [str(rlz.gsim_rlz.value[0]) for rlz in rlzs]
    evs = extract_relevant_events(dstore)
    df = pandas.DataFrame({'id': evs['id'], 'rlz_id': evs['rlz_id']})
    for r, evs in df.groupby('rlz_id'):
        yield gsims[r], numpy.array(evs['id'])


@extract.add('risk_stats')
def extract_risk_stats(dstore, what):
    """
    Compute the risk statistics from a DataFrame with individual realizations
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/risk_stats/aggrisk
    """
    oq = dstore['oqparam']
    stats = oq.hazard_stats()
    df = dstore.read_df(what)
    df['loss_type'] = [LOSSTYPE[lid] for lid in df.loss_id]
    del df['loss_id']
    kfields = [f for f in df.columns if f in {
        'agg_id', 'loss_type', 'return_period'}]
    weights = dstore['weights'][:]
    return calc_stats(df, kfields, stats, weights)


# #####################  extraction from the WebAPI ###################### #


class WebAPIError(RuntimeError):
    """
    Wrapper for an error on a WebAPI server
    """


class Extractor(object):
    """
    A class to extract data from a calculation.

    :param calc_id: a calculation ID

    NB: instantiating the Extractor opens the datastore.
    """
    def __init__(self, calc_id):
        self.dstore = datastore.read(calc_id)
        self.calc_id = self.dstore.calc_id
        self.oqparam = self.dstore['oqparam']

    def get(self, what, asdict=False):
        """
        :param what: what to extract
        :returns: an ArrayWrapper instance or a dictionary if asdict is True
        """
        aw = extract(self.dstore, what)
        if asdict:
            return {k: v for k, v in vars(aw).items() if not k.startswith('_')}
        return aw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """
        Close the datastore
        """
        self.dstore.close()


class WebExtractor(Extractor):
    """
    A class to extract data from the WebAPI.

    :param calc_id: a calculation ID
    :param server: hostname of the webapi server (can be '')
    :param username: login username (can be '')
    :param password: login password (can be '')

    NB: instantiating the WebExtractor opens a session.
    """
    def __init__(self, calc_id, server=None, username=None, password=None):
        self.calc_id = calc_id
        self.server = config.webapi.server if server is None else server
        if username is None:
            username = config.webapi.username
        if password is None:
            password = config.webapi.password
        self.sess = requests.Session()
        if username:
            login_url = '%s/accounts/ajax_login/' % self.server
            logging.info('POST %s', login_url)
            resp = self.sess.post(
                login_url, data=dict(username=username, password=password))
            if resp.status_code != 200:
                raise WebAPIError(resp.text)
        url = '%s/v1/calc/%d/extract/oqparam' % (self.server, calc_id)
        logging.info('GET %s', url)
        resp = self.sess.get(url)
        if resp.status_code == 404:
            raise WebAPIError('Not Found: %s' % url)
        elif resp.status_code != 200:
            raise WebAPIError(resp.text)
        self.oqparam = object.__new__(oqvalidation.OqParam)
        js = bytes(numpy.load(io.BytesIO(resp.content))['json'])
        vars(self.oqparam).update(json.loads(js))

    def get(self, what):
        """
        :param what: what to extract
        :returns: an ArrayWrapper instance
        """
        url = '%s/v1/calc/%d/extract/%s' % (self.server, self.calc_id, what)
        logging.info('GET %s', url)
        resp = self.sess.get(url)
        if resp.status_code != 200:
            raise WebAPIError(resp.text)
        logging.info('Read %s of data' % general.humansize(len(resp.content)))
        npz = numpy.load(io.BytesIO(resp.content))
        attrs = {k: npz[k] for k in npz if k != 'array'}
        try:
            arr = npz['array']
        except KeyError:
            arr = ()
        return ArrayWrapper(arr, attrs)

    def dump(self, fname):
        """
        Dump the remote datastore on a local path.
        """
        url = '%s/v1/calc/%d/datastore' % (self.server, self.calc_id)
        resp = self.sess.get(url, stream=True)
        down = 0
        with open(fname, 'wb') as f:
            logging.info('Saving %s', fname)
            for chunk in resp.iter_content(CHUNKSIZE):
                f.write(chunk)
                down += len(chunk)
                println('Downloaded {:,} bytes'.format(down))
        print()

    def close(self):
        """
        Close the session
        """
        self.sess.close()


def clusterize(hmaps, rlzs, k):
    """
    :param hmaps: array of shape (R, M, P)
    :param rlzs: composite array of shape R
    :param k: number of clusters to build
    :returns: (array(K, MP), labels(R))
    """
    R, M, P = hmaps.shape
    hmaps = hmaps.transpose(0, 2, 1).reshape(R, M * P)
    dt = [('label', U32), ('branch_paths', object), ('centroid', (F32, M*P))]
    centroid, labels = kmeans2(hmaps, k, minit='++')
    dic = dict(path=rlzs['branch_path'], label=labels)
    df = pandas.DataFrame(dic)
    tbl = []
    for label, grp in df.groupby('label'):
        paths = [encode(path) for path in grp['path']]
        tbl.append((label, logictree.collect_paths(paths), centroid[label]))
    return numpy.array(tbl, dt), labels


def read_ebrupture(dstore, rup_id):
    """
    :param dstore: a DataStore instance
    :param rup_id: an integer rupture ID
    :returns: an EBRupture instance
    """
    [getter] = getters.get_rupture_getters(
        dstore, slc=slice(rup_id, rup_id + 1))
    [proxy] = getter.get_proxies()
    return proxy.to_ebr(getter.trt)
