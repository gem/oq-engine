# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
from urllib.parse import parse_qs, quote_plus
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
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import logictree, InvalidFile
from openquake.hazardlib.contexts import (
    ContextMaker, read_cmakers, read_ctx_by_grp)
from openquake.hazardlib.calc import disagg, stochastic, filters
from openquake.hazardlib.stats import calc_stats
from openquake.hazardlib.source import rupture
from openquake.risklib.scientific import LOSSTYPE, LOSSID
from openquake.risklib.asset import tagset
from openquake.commonlib import calc, util, oqvalidation, datastore
from openquake.calculators import getters

U16 = numpy.uint16
U32 = numpy.uint32
I64 = numpy.int64
F32 = numpy.float32
F64 = numpy.float64
TWO24 = 2 ** 24
TWO30 = 2 ** 30
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
    >>> parse(
    ...    'loss_type=structural+nonstructural&absolute=True&kind=rlzs')['lt']
    ['structural+nonstructural']
    """
    qdic = parse_qs(query_string)
    for key, val in sorted(qdic.items()):
        # convert site_id to an int, loss_type to an int, etc
        if key == 'loss_type':
            # NOTE: loss types such as 'structural+nonstructural' need to be
            # quoted, otherwise the plus would turn into a space
            val = [quote_plus(lt) for lt in val]
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
    oq = dstore['oqparam']
    scenario = 'scenario' in oq.calculation_mode
    full_lt = dstore['full_lt']
    rlzs = full_lt.rlzs
    if scenario and len(full_lt.trts) == 1:  # only one TRT
        gsims = encode(dstore.getitem('full_lt/gsim_lt')['uncertainty'])
        if 'shakemap' in oq.inputs:
            gsims = ["[FromShakeMap]"]
        bplen = max(len(gsim) for gsim in gsims)  # list of bytes
    else:
        bpaths = encode(rlzs['branch_path'])  # list of bytes
        bplen = max(len(bp) for bp in bpaths)

    # NB: branch_path cannot be of type hdf5.vstr otherwise the conversion
    # to .npz (needed by the plugin) would fail
    dt = [('rlz_id', U32), ('branch_path', '<S%d' % bplen), ('weight', F32)]
    arr = numpy.zeros(len(rlzs), dt)
    arr['rlz_id'] = rlzs['ordinal']
    arr['weight'] = rlzs['weight']
    if scenario and len(full_lt.trts) == 1:  # only one TRT
        # quotes Excel-friendly
        arr['branch_path'] = [gsim.replace(b'"', b'""') for gsim in gsims]
    else:  # use the compact representation for the branch paths
        arr['branch_path'] = bpaths
    return arr


@extract.add('weights')
def extract_weights(dstore, what):
    """
    Extract the realization weights
    """
    rlzs = dstore['full_lt'].get_realizations()
    return numpy.array([rlz.weight[-1] for rlz in rlzs])


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
                    if name.startswith(('value-', 'occupants'))
                    and name != 'occupants_avg']
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


@extract.add('median_spectra')
def extract_median_spectra(dstore, what):
    """
    Extracts median spectra per site and group.
    Use it as /extract/median_spectra?site_id=0&poe_id=1
    """
    qdict = parse(what)
    [site_id] = qdict['site_id']
    [poe_id] = qdict['poe_id']
    dset = dstore['median_spectra']
    dic = json.loads(dset.attrs['json'])
    spectra = dset[:, site_id, :, :, poe_id]  # (Gt, 3, M)
    return ArrayWrapper(spectra, dict(
        shape_descr=['grp_id', 'kind', 'period'],
        grp_id=numpy.arange(dic['grp_id']),
        kind=['mea', 'sig', 'wei'],
        period=dic['period']))


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
    data = numpy.zeros(n, [('src_id', U32), ('rup_id', I64)])
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
    ctx_by_grp = read_ctx_by_grp(dstore)
    cmakers = read_cmakers(dstore)
    for gid, ctx in ctx_by_grp.items():
        # shape (4, G, M, U) => U
        means = cmakers[gid].get_mean_stds([ctx], split_by_mag=True)[0].mean(
            axis=(0, 1))
        out.extend(zip(ctx.src_id, ctx.rup_id, means))
    out.sort(key=operator.itemgetter(0, 1))
    return numpy.array(out, [('src_id', U32), ('rup_id', I64), ('mean', F64)])


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
    src_gz = gzip.compress(';'.join(decode(info['source_id'])).encode('utf8'))
    oknames = [name for name in info.dtype.names  # avoid pickle issues
               if name != 'source_id']
    arr = numpy.zeros(len(info), [(n, info.dtype[n]) for n in oknames])
    for n in oknames:
        arr[n] = info[n]
    return ArrayWrapper(arr, {'src_gz': src_gz})


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
    dic = general.group_array(dstore['task_info'][()], 'taskname')
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
    try:
        tagnames = dstore['oqparam'].aggregate_by[0]
    except IndexError:
        tagnames = []
    k = qdic['k']  # rlz or stat index
    lts = qdic['lt']
    [li] = qdic['loss_type']  # loss type index
    tagdict = {tag: qdic[tag] for tag in tagnames}
    if set(tagnames) != info['tagnames']:
        raise ValueError('Expected tagnames=%s, got %s' %
                         (info['tagnames'], tagnames))
    tagvalues = [tagdict[t][0] for t in tagnames]
    if tagnames:
        lst = decode(dstore['agg_keys'][:])
        agg_id = lst.index('\t'.join(tagvalues))
    else:
        agg_id = 0  # total aggregation
    ep_fields = dstore.get_attr('aggcurves', 'ep_fields')
    if qdic['rlzs']:
        [li] = qdic['loss_type']  # loss type index
        units = dstore.get_attr('aggcurves', 'units').split()
        df = dstore.read_df('aggcurves', sel=dict(agg_id=agg_id, loss_id=li))
        rps = list(df.return_period.unique())
        P = len(rps)
        R = len(qdic['kind'])
        EP = len(ep_fields)
        arr = numpy.zeros((R, P, EP))
        for rlz in df.rlz_id.unique():
            for ep_field_idx, ep_field in enumerate(ep_fields):
                # NB: df may contains zeros but there are no missing periods
                # by construction (see build_aggcurves)
                arr[rlz, :, ep_field_idx] = df[df.rlz_id == rlz][ep_field]
    else:
        name = 'agg_curves-stats/' + lts[0]
        shape_descr = hdf5.get_shape_descr(dstore.get_attr(name, 'json'))
        rps = list(shape_descr['return_period'])
        units = dstore.get_attr(name, 'units').split()
        arr = dstore[name][agg_id, k]  # shape (P, S, EP)
    if qdic['absolute'] == [1]:
        pass
    elif qdic['absolute'] == [0]:
        evalue_sum = 0
        for lts_item in lts:
            for lt in lts_item.split('+'):
                evalue_sum += dstore['agg_values'][agg_id][lt]
        arr /= evalue_sum
    else:
        raise ValueError('"absolute" must be 0 or 1 in %s' % what)
    attrs = dict(shape_descr=['kind', 'return_period', 'ep_field'] + tagnames)
    attrs['kind'] = qdic['kind']
    attrs['return_period'] = rps
    attrs['units'] = units  # used by the QGIS plugin
    attrs['ep_field'] = ep_fields
    for tagname, tagvalue in zip(tagnames, tagvalues):
        attrs[tagname] = [tagvalue]
    if tagnames:
        arr = arr.reshape(arr.shape + (1,) * len(tagnames))
    return ArrayWrapper(arr, dict(json=hdf5.dumps(attrs)))


def _aggexp_tags(dstore):
    oq = dstore['oqparam']
    if not oq.aggregate_by:
        raise InvalidFile(f'{dstore.filename}: missing aggregate_by')
    if len(oq.aggregate_by) > 1:  # i.e. [['ID_0'], ['OCCUPANCY']]
        aggby = [','.join(a[0] for a in oq.aggregate_by)]
    else:  # i.e. [['ID_0', 'OCCUPANCY']]
        [aggby] = oq.aggregate_by
    keys = numpy.array([line.decode('utf8').split('\t')
                        for line in dstore['agg_keys'][:]])
    values = dstore['agg_values'][:-1]  # discard the total aggregation
    ok = values['structural'] > 0
    okvalues = values[ok]
    dic = {}
    for i, tag in enumerate(aggby):
        dic[tag] = keys[ok, i]
    for name in values.dtype.names:
        dic[name] = okvalues[name]
    df = pandas.DataFrame(dic)
    return df, ok


@extract.add('aggexp_tags')
def extract_aggexp_tags(dstore, what):
    """
    Aggregate the exposure values (one for each loss type) by tag. Use it as
    /extract/aggexp_tags?
    """
    return _aggexp_tags(dstore)[0]


@extract.add('aggrisk_tags')
def extract_aggrisk_tags(dstore, what):
    """
    Aggregates risk by tag. Use it as /extract/aggrisk_tags?
    """
    oq = dstore['oqparam']
    ws = dstore['weights'][:]
    adf = dstore.read_df('aggrisk')
    if 'aggrisk_quantiles' in dstore:
        # normally there are two quantiles 0.05, 0.95
        qdf = dstore.read_df('aggrisk_quantiles', ['agg_id', 'loss_id'])
        qfields = [col for col in qdf.columns if col != 'agg_id']
    else:
        qdf = ()
        qfields = []
    if len(oq.aggregate_by) > 1:  # i.e. [['ID_0'], ['OCCUPANCY']]
        # see impact_test.py
        aggby = [','.join(a[0] for a in oq.aggregate_by)]
    else:  # i.e. [['ID_0', 'OCCUPANCY']]
        # see event_based_risk_test/case_1
        [aggby] = oq.aggregate_by
    keys = numpy.array([line.decode('utf8').split('\t')
                        for line in dstore['agg_keys'][:]])
    values = dstore['agg_values'][:-1]  # discard the total aggregation
    lossdic = general.AccumDict(accum=0)
    K = len(keys)
    for agg_id, rlz_id, loss, loss_id in zip(
            adf.agg_id, adf.rlz_id, adf.loss, adf.loss_id):
        if agg_id < K:
            lossdic[agg_id, loss_id] += loss * ws[rlz_id]
    acc = general.AccumDict(accum=[])
    for (agg_id, loss_id), loss in sorted(lossdic.items()):
        lt = LOSSTYPE[loss_id]
        if lt in values.dtype.names:
            for agg_key, key in zip(aggby, keys[agg_id]):
                acc[agg_key].append(key)
            acc['loss_type'].append(lt)
            acc['value'].append(values[agg_id][lt])
            acc['lossmea'].append(loss)
            if len(qdf):
                qvalues = qdf.loc[agg_id, loss_id].to_numpy()
                for qfield, qvalue in zip(qfields, qvalues):
                    acc[qfield].append(qvalue)
    df = pandas.DataFrame(acc)
    return df


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
    if '?' in what:
        loss_type, query_string = what.rsplit('?', 1)
    else:
        loss_type, query_string = what, ''
    tags = query_string.split('&') if query_string else []
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


# TODO: extend to multiple perils
def _dmg_get(array, loss_type):
    # array of shape (A, R)
    out = []
    for name in array.dtype.names:
        try:
            ltype, _dstate = name.split('-')
        except ValueError:
            # ignore secondary perils
            continue
        if ltype == loss_type:
            out.append(array[name])
    return numpy.array(out).transpose(1, 2, 0)  # shape (A, R, Dc)


@extract.add('agg_damages')
def extract_agg_damages(dstore, what):
    """
    Aggregate damages of the given loss type and tags. Use it as
    /extract/agg_damages?taxonomy=RC&custom_site_id=20126

    :returns:
        array of shape (R, D), being R the number of realizations and D the
        number of damage states, or an array of length 0 if there is no data
        for the given tags
    """
    if '?' in what:
        loss_type, what = what.rsplit('?', 1)
        tags = what.split('&') if what else []
    else:
        loss_type = what
        tags = []
    if 'damages-rlzs' in dstore:
        damages = _dmg_get(dstore['damages-rlzs'][:], loss_type)
    else:
        raise KeyError('No damages found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], damages, tags)


@extract.add('aggregate')
def extract_aggregate(dstore, what):
    """
    /extract/aggregate/avg_losses?
    kind=mean&loss_type=structural&tag=taxonomy&tag=occupancy
    """
    _name, qstring = what.split('?', 1)
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
    R = dstore['full_lt'].get_num_paths()
    stats = oq.hazard_stats()  # statname -> statfunc
    assets = util.get_assets(dstore)
    if 'losses_by_asset' in dstore:
        losses_by_asset = dstore['losses_by_asset'][()]
        for r in range(R):
            # I am exporting the 'mean' and ignoring the 'stddev'
            losses = cast(losses_by_asset[:, r]['mean'], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield 'rlz-%03d' % r, data
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


def _gmf(df, num_sites, imts, sec_imts):
    # convert data into the composite array expected by QGIS
    gmfa = numpy.zeros(num_sites, [(imt, F32) for imt in imts + sec_imts])
    for m, imt in enumerate(imts + sec_imts):
        gmfa[imt][U32(df.sid)] = df[f'gmv_{m}'] if imt in imts else df[imt]
    return gmfa


# tested in oq-risk-tests, conditioned_gmfs
@extract.add('gmf_scenario')
def extract_gmf_scenario(dstore, what):
    oq = dstore['oqparam']
    assert oq.calculation_mode.startswith('scenario'), oq.calculation_mode
    info = get_info(dstore)
    qdict = parse(what, info)  # example {'imt': 'PGA', 'k': 1}
    [imt] = qdict['imt']
    [rlz_id] = qdict['k']
    eids = dstore['gmf_data/eid'][:]
    rlzs = dstore['events']['rlz_id']
    ok = rlzs[eids] == rlz_id
    m = list(oq.imtls).index(imt)
    eids = eids[ok]
    gmvs = dstore[f'gmf_data/gmv_{m}'][ok]
    sids = dstore['gmf_data/sid'][ok]
    try:
        N = len(dstore['complete'])
    except KeyError:
        N = len(dstore['sitecol'])
    E = len(rlzs) // info['num_rlzs']
    arr = numpy.zeros((E, N))
    for e, eid in enumerate(numpy.unique(eids)):
        event = eids == eid
        arr[e, sids[event]] = gmvs[event]
    return arr


# used by the QGIS plugin for a single eid
@extract.add('gmf_data')
def extract_gmf_npz(dstore, what):
    oq = dstore['oqparam']
    qdict = parse(what)
    [eid] = qdict.get('event_id', [0])  # there must be a single event
    rlzi = dstore['events'][eid]['rlz_id']
    try:
        complete = dstore['complete']
    except KeyError:
        complete = dstore['sitecol']
    sites = get_sites(complete)
    n = len(sites)
    try:
        df = dstore.read_df('gmf_data', 'eid').loc[eid]
    except KeyError:
        # zero GMF
        yield 'rlz-%03d' % rlzi, []
    else:
        prim_imts = list(oq.get_primary_imtls())
        gmfa = _gmf(df, n, prim_imts, oq.sec_imts)
        yield 'rlz-%03d' % rlzi, util.compose_arrays(sites, gmfa)


# extract the relevant GMFs as an npz file with fields eid, sid, gmv_
@extract.add('relevant_gmfs')
def extract_relevant_gmfs(dstore, what):
    qdict = parse(what)
    [thr] = qdict.get('threshold', ['1'])
    eids = get_relevant_event_ids(dstore, float(thr))
    try:
        sbe = dstore.read_df('gmf_data/slice_by_event', 'eid')
    except KeyError:
        df = dstore.read_df('gmf_data', 'eid')
        return df.loc[eids].reset_index()
    dfs = []
    for eid in eids:
        ser = sbe.loc[eid]
        slc = slice(ser.start, ser.stop)
        dfs.append(dstore.read_df('gmf_data', slc=slc))
    return pandas.concat(dfs)


@extract.add('avg_gmf')
def extract_avg_gmf(dstore, what):
    qdict = parse(what)
    info = get_info(dstore)
    [imt] = qdict['imt']
    imti = info['imt'][imt]
    try:
        complete = dstore['complete']
    except KeyError:
        if dstore.parent:
            complete = dstore.parent['sitecol'].complete
        else:
            complete = dstore['sitecol'].complete
    avg_gmf = dstore['avg_gmf'][0, :, imti]
    if 'station_data' in dstore:
        # discard the stations from the avg_gmf plot
        stations = dstore['station_data/site_id'][:]
        ok = (avg_gmf > 0) & ~numpy.isin(complete.sids, stations)
    else:
        ok = avg_gmf > 0
    yield imt, avg_gmf[complete.sids[ok]]
    yield 'sids', complete.sids[ok]
    yield 'lons', complete.lons[ok]
    yield 'lats', complete.lats[ok]


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
    perils = attrs['peril']
    limit_states = list(dstore.get_attr('crm', 'limit_states'))
    csqs = attrs['dmg_state'][len(limit_states) + 1:]  # consequences
    dt_list = []
    for peril in perils:
        for ds in ['no_damage'] + limit_states + csqs:
            dt_list.append((ds if peril == 'groundshaking'
                            else f'{peril}_{ds}', F32))
    damage_dt = numpy.dtype(dt_list)
    loss_types = oq.loss_dt().names
    return numpy.dtype([(lt, damage_dt) for lt in loss_types])


@extract.add('damages-rlzs')
def extract_damages_npz(dstore, what):
    oq = dstore['oqparam']
    R = dstore['full_lt'].get_num_paths()
    if oq.collect_rlzs:
        R = 1
    data = dstore['damages-rlzs']
    assets = util.get_assets(dstore)
    for r in range(R):
        yield 'rlz-%03d' % r, util.compose_arrays(assets, data[:, r])


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
    rup_df = dstore.read_df('ruptures', 'id')[
        ['mag', 'n_occ', 'occurrence_rate']]
    rup_df.mag = numpy.round(rup_df.mag, 1)
    dic = dict(mag=[], freq=[], occ_rate=[])
    for mag, df in rup_df.groupby('mag'):
        dic['mag'].append(mag)
        dic['freq'].append(df.n_occ.sum() / eff_time)
        dic['occ_rate'].append(df.occurrence_rate.sum())
    return ArrayWrapper((), {k: numpy.array(v) for k, v in dic.items()})


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
    Extract a disaggregation output as an ArrayWrapper.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/
    disagg?kind=Mag_Dist&imt=PGA&site_id=1&poe_id=0&spec=stats
    """
    qdict = parse(what)
    spec = qdict['spec'][0]
    label = qdict['kind'][0]
    sid = int(qdict['site_id'][0])
    oq = dstore['oqparam']
    imts = list(oq.imtls)
    if 'imt' in qdict:
        imti = [imts.index(imt) for imt in qdict['imt']]
    else:
        imti = slice(None)
    if 'poe_id' in qdict:
        poei = [int(x) for x in qdict['poe_id']]
    else:
        poei = slice(None)
    if 'traditional' in spec:
        spec = spec.split('-')[0]
        assert spec in {'rlzs', 'stats'}, spec
        traditional = True
    else:
        traditional = False

    def bin_edges(dset, sid):
        if len(dset.shape) == 2:  # (lon, lat) bins
            return dset[sid]
        return dset[:]  # regular bin edges

    bins = {k: bin_edges(v, sid) for k, v in dstore['disagg-bins'].items()}
    fullmatrix = dstore['disagg-%s/%s' % (spec, label)][sid]
    # matrix has shape (..., M, P, Z)
    matrix = fullmatrix[..., imti, poei, :]
    if traditional:
        poe_agg = dstore['poe4'][sid, imti, poei]  # shape (M, P, Z)
        matrix[:] = numpy.log(1. - matrix) / numpy.log(1. - poe_agg)

    disag_tup = tuple(label.split('_'))
    axis = [bins[k] for k in disag_tup]

    # compute axis mid points, except for string axis (i.e. TRT)
    axis = [(ax[: -1] + ax[1:]) / 2. if ax.dtype.char != 'S'
            else ax for ax in axis]
    attrs = qdict.copy()
    for k, ax in zip(disag_tup, axis):
        attrs[k.lower()] = ax
    attrs['imt'] = qdict['imt'] if 'imt' in qdict else imts
    imt = attrs['imt'][0]
    if len(oq.poes) == 0:
        mean_curve = dstore.sel(
            'hcurves-stats', imt=imt, stat='mean')[sid, 0, 0]
        # using loglog interpolation like in compute_hazard_maps
        attrs['poe'] = numpy.exp(
            numpy.interp(numpy.log(oq.iml_disagg[imt]),
                         numpy.log(oq.imtls[imt]),
                         numpy.log(mean_curve.reshape(-1))))
    elif 'poe_id' in qdict:
        attrs['poe'] = [oq.poes[p] for p in poei]
    else:
        attrs['poe'] = oq.poes
    attrs['traditional'] = traditional
    attrs['shape_descr'] = [k.lower() for k in disag_tup] + ['imt', 'poe']
    rlzs = dstore['best_rlzs'][sid]
    if spec == 'rlzs':
        weights = dstore['weights'][:][rlzs]
        weights /= weights.sum()  # normalize to 1
        attrs['weights'] = weights.tolist()
    extra = ['rlz%d' % rlz for rlz in rlzs] if spec == 'rlzs' else ['mean']
    return ArrayWrapper(matrix, attrs, extra)


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


@extract.add('mean_rates_by_src')
def extract_mean_rates_by_src(dstore, what):
    """
    Extract the mean_rates_by_src information.
    Example: http://127.0.0.1:8800/v1/calc/30/extract/mean_rates_by_src?site_id=0&imt=PGA&iml=.001
    """
    qdict = parse(what)
    dset = dstore['mean_rates_by_src/array']
    oq = dstore['oqparam']
    src_id = dstore['mean_rates_by_src/src_id'][:]
    [imt] = qdict['imt']
    [iml] = qdict['iml']
    [site_id] = qdict.get('site_id', ['0'])
    site_id = int(site_id)
    imt_id = list(oq.imtls).index(imt)
    rates = dset[site_id, imt_id]
    _L1, Ns = rates.shape
    arr = numpy.zeros(len(src_id), [('src_id', hdf5.vstr), ('rate', '<f8')])
    arr['src_id'] = src_id
    arr['rate'] = [numpy.interp(iml, oq.imtls[imt], rates[:, i])
                   for i in range(Ns)]
    arr.sort(order='rate')
    return ArrayWrapper(arr[::-1], dict(site_id=site_id, imt=imt, iml=iml))


# TODO: extract from disagg-stats, avoid computing means on the fly
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
    full_lt = dstore['full_lt'].init()
    oq.mags_by_trt = dstore['source_mags']
    edges, shapedic = disagg.get_edges_shapedic(
        oq, sitecol, len(full_lt.weights))
    dt = _disagg_output_dt(shapedic, kinds, oq.imtls, poes_disagg)
    out = numpy.zeros(len(sitecol), dt)
    hmap3 = dstore['hmap3'][:]  # shape (N, M, P)
    best_rlzs = dstore['best_rlzs'][:]
    arr = {kind: dstore['disagg-rlzs/' + kind][:] for kind in kinds}
    for sid, lon, lat, rec in zip(
            sitecol.sids, sitecol.lons, sitecol.lats, out):
        weights = full_lt.weights[best_rlzs[sid]]
        rec['site_id'] = sid
        rec['lon'] = lon
        rec['lat'] = lat
        rec['lon_bins'] = edges[2][sid]
        rec['lat_bins'] = edges[3][sid]
        for m, imt in enumerate(oq.imtls):
            ws = full_lt.wget(weights, imt)
            ws /= ws.sum()  # normalize to 1
            for p, poe in enumerate(poes_disagg):
                for kind in kinds:
                    key = '%s-%s-%s' % (kind, imt, poe)
                    rec[key] = arr[kind][sid, ..., m, p, :] @ ws
                rec['iml-%s-%s' % (imt, poe)] = hmap3[sid, m, p]
    return ArrayWrapper(out, dict(mag=edges[0], dist=edges[1], eps=edges[-2],
                                  trt=numpy.array(encode(edges[-1]))))

# ######################### extracting ruptures ##############################


class RuptureData(object):
    """
    Container for information about the ruptures of a given
    tectonic region type.
    """
    def __init__(self, trt, gsims, mags):
        self.trt = trt
        self.cmaker = ContextMaker(trt, gsims, {'imtls': {}, 'mags': mags})
        self.params = sorted(self.cmaker.REQUIRES_RUPTURE_PARAMETERS -
                             set('mag strike dip rake hypo_depth'.split()))
        self.dt = numpy.dtype([
            ('rup_id', I64), ('source_id', SOURCE_ID), ('multiplicity', U32),
            ('occurrence_rate', F64),
            ('mag', F32), ('lon', F32), ('lat', F32), ('depth', F32),
            ('strike', F32), ('dip', F32), ('rake', F32),
            ('boundaries', hdf5.vfloat32)] +
            [(param, F32) for param in self.params])

    def to_array(self, proxies):
        """
        Convert a list of rupture proxies into an array of dtype RuptureData.dt
        """
        data = []
        for proxy in proxies:
            ebr = proxy.to_ebr(self.trt)
            rup = ebr.rupture
            dic = self.cmaker.get_rparams(rup)
            ruptparams = tuple(dic[param] for param in self.params)
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


@extract.add('ebruptures')
def extract_ebruptures(dstore, what):
    """
    Extract the hypocenter of the ruptures.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/ebruptures?min_mag=6
    """
    qdict = parse(what)
    rups = dstore['ruptures'][:]
    if 'min_mag' in qdict:
        [min_mag] = qdict['min_mag']
        rups = rups[rups['mag'] >= min_mag]
    return rups


# used in the rupture exporter and in the plugin
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
    try:
        source_id = dstore['source_info']['source_id']
    except KeyError:  # scenario
        source_id = None
    dtlist = [('rup_id', I64), ('source_id', '<S75'), ('multiplicity', U32),
              ('mag', F32), ('centroid_lon', F32), ('centroid_lat', F32),
              ('centroid_depth', F32), ('trt', '<S50'),
              ('strike', F32), ('dip', F32), ('rake', F32)]
    rows = []
    boundaries = []
    full_lt = dstore['full_lt']
    rlzs_by_gsim = full_lt.get_rlzs_by_gsim_dic()
    try:
        tss = dstore['trt_smr_start_stop']
    except KeyError:
        # when starting from GMFs there are no ruptures
        raise getters.NotFound
    for trt_smr, start, stop in tss:
        proxies = calc.get_proxies(dstore.filename, slice(start, stop), min_mag)
        trt = full_lt.trts[trt_smr // TWO24]
        if 'source_mags' not in dstore:  # ruptures import from CSV
            mags = numpy.unique(dstore['ruptures']['mag'])
        else:
            mags = dstore[f'source_mags/{trt}'][:]
        rdata = RuptureData(trt, rlzs_by_gsim[trt_smr], mags)
        arr = rdata.to_array(proxies)
        for r in arr:
            if source_id is None:
                srcid = 'no-source'
            else:
                srcid = source_id[r['source_id']]
            coords = ['%.5f %.5f' % xyz[:2] for xyz in zip(*r['boundaries'])]
            coordset = sorted(set(coords))
            if len(coordset) < 4:   # degenerate to line
                boundaries.append('LINESTRING(%s)' % ', '.join(coordset))
            else:  # good polygon
                boundaries.append('POLYGON((%s))' % ', '.join(coords))
            rows.append(
                (r['rup_id'], srcid, r['multiplicity'],
                 r['mag'], r['lon'], r['lat'], r['depth'],
                 trt, r['strike'], r['dip'], r['rake']))
    arr = numpy.array(rows, dtlist)
    geoms = gzip.compress('\n'.join(boundaries).encode('utf-8'))
    return ArrayWrapper(arr, dict(investigation_time=oq.investigation_time,
                                  boundaries=geoms))


def get_relevant_rup_ids(dstore, threshold):
    """
    :param dstore:
        a DataStore instance with a `risk_by_rupture` dataframe
    :param threshold:
        fraction of the total losses
    :returns:
        array with the rupture IDs cumulating the highest losses
        up to the threshold (usually 95% of the total loss)
    """
    assert 0 <= threshold <= 1, threshold
    if 'loss_by_rupture' not in dstore:
        return
    rupids = dstore['loss_by_rupture/rup_id'][:]
    cumsum = dstore['loss_by_rupture/loss'][:].cumsum()
    thr = threshold * cumsum[-1]
    for i, csum in enumerate(cumsum, 1):
        if csum > thr:
            break
    return rupids[:i]


def get_relevant_event_ids(dstore, threshold):
    """
    :param dstore:
        a DataStore instance with a `risk_by_rupture` dataframe
    :param threshold:
        fraction of the total losses
    :returns:
        array with the event IDs cumulating the highest losses
        up to the threshold (usually 95% of the total loss)
    """
    assert 0 <= threshold <= 1, threshold
    if 'loss_by_event' not in dstore:
        return
    eids = dstore['loss_by_event/event_id'][:]
    try:
        cumsum = dstore['loss_by_event/loss'][:].cumsum()
    except KeyError:  # no losses
        return eids
    thr = threshold * cumsum[-1]
    for i, csum in enumerate(cumsum, 1):
        if csum > thr:
            break
    return eids[:i]


@extract.add('ruptures')
def extract_ruptures(dstore, what):
    """
    Extract the ruptures with their geometry as a big CSV string
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/ruptures?rup_id=6
    """
    oq = dstore['oqparam']
    trts = list(dstore.getitem('full_lt').attrs['trts'])
    comment = dict(trts=trts, ses_seed=oq.ses_seed)
    qdict = parse(what)
    if 'min_mag' in qdict:
        [min_mag] = qdict['min_mag']
    else:
        min_mag = 0
    if 'rup_id' in qdict:
        rup_id = int(qdict['rup_id'][0])
        ebrups = [getters.get_ebrupture(dstore, rup_id)]
        info = dstore['source_info'][rup_id // TWO30]
        comment['source_id'] = info['source_id'].decode('utf8')
    else:
        if 'threshold' in qdict:
            [threshold] = qdict['threshold']
            rup_ids = get_relevant_rup_ids(dstore, threshold)
            ebrups = [ebr for ebr in getters.get_ebruptures(dstore)
                      if ebr.id in rup_ids and ebr.mag >= min_mag]
        else:
            ebrups = [ebr for ebr in getters.get_ebruptures(dstore)
                      if ebr.mag >= min_mag]
    if 'slice' in qdict:
        s0, s1 = qdict['slice']
        slc = slice(s0, s1)
    else:
        slc = slice(None)
    bio = io.StringIO()
    arr = rupture.to_csv_array(ebrups[slc])
    writers.write_csv(bio, arr, comment=comment)
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


@extract.add('med_gmv')
def extract_med_gmv(dstore, what):
    """
    Extract med_gmv array for the given source
    """
    return extract_(dstore, 'med_gmv/' + what)


@extract.add('high_sites')
def extract_high_sites(dstore, what):
    """
    Returns an array of boolean with the high hazard sites (max_poe > .2)
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/high_sites
    """
    max_hazard = dstore.sel('hcurves-stats', stat='mean', lvl=0)[:, 0, :, 0]  # NSML1 -> NM
    return (max_hazard > .2).all(axis=1)  # shape N


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
                general.println('Downloaded {:,} bytes'.format(down))
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
    :returns: array of K elements with dtype (rlzs, branch_paths, centroid)
    """
    R, M, P = hmaps.shape
    hmaps = hmaps.transpose(0, 2, 1).reshape(R, M * P)
    dt = [('rlzs', hdf5.vuint32), ('branch_paths', object),
          ('centroid', (F32, M*P))]
    centroid, labels = kmeans2(hmaps, k, minit='++')
    df = pandas.DataFrame(dict(path=rlzs['branch_path'], label=labels))
    tbl = []
    for label, grp in df.groupby('label'):
        paths = logictree.collect_paths(encode(list(grp['path'])))
        tbl.append((grp.index, paths, centroid[label]))
    return numpy.array(tbl, dt)
