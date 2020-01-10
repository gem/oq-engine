# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
from functools import lru_cache, partial
import collections
import logging
import gzip
import ast
import io
import os

import requests
from h5py._hl.dataset import Dataset
from h5py._hl.group import Group
import numpy
from openquake.baselib import config, hdf5
from openquake.baselib.hdf5 import ArrayWrapper
from openquake.baselib.general import group_array, get_array, println
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.calculators import getters
from openquake.commonlib import calc, util, oqvalidation

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
TWO32 = 2 ** 32
ALL = slice(None)
CHUNKSIZE = 4*1024**2  # 4 MB
memoized = lru_cache(100)


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
    :returns: {'stats': dic, 'loss_types': dic, 'num_rlzs': R}
    """
    oq = dstore['oqparam']
    stats = {stat: s for s, stat in enumerate(oq.hazard_stats())}
    loss_types = {lt: l for l, lt in enumerate(oq.loss_dt().names)}
    imt = {imt: i for i, imt in enumerate(oq.imtls)}
    num_rlzs = dstore['csm_info'].get_num_rlzs()
    return dict(stats=stats, num_rlzs=num_rlzs, loss_types=loss_types,
                imtls=oq.imtls, investigation_time=oq.investigation_time,
                poes=oq.poes, imt=imt, uhs_dt=oq.uhs_dt(),
                tagnames=oq.aggregate_by)


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
    loss_types = info.get('loss_types', [])
    for key, val in qdic.items():  # for instance, convert site_id to an int
        if key == 'loss_type':
            qdic[key] = [loss_types[k] for k in val]
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
        return ArrayWrapper.from_(data)


extract = Extract()


# used by the QGIS plugin in scenario
@extract.add('realizations')
def extract_realizations(dstore, dummy):
    """
    Extract an array of realizations. Use it as /extract/realizations
    """
    oq = dstore['oqparam']
    scenario = 'scenario' in oq.calculation_mode
    rlzs = dstore['csm_info'].rlzs
    # NB: branch_path cannot be of type hdf5.vstr otherwise the conversion
    # to .npz (needed by the plugin) would fail
    dt = [('rlz_id', U32), ('branch_path', '<S100'), ('weight', F32)]
    arr = numpy.zeros(len(rlzs), dt)
    arr['rlz_id'] = rlzs['ordinal']
    arr['weight'] = rlzs['weight']
    if scenario:
        gsims = dstore['csm_info/gsim_lt/branches']['uncertainty']
        if 'shakemap' in oq.inputs:
            gsims = ["[FromShakeMap]"]
        arr['branch_path'] = ['"%s"' % repr(gsim)[1:-1].replace('"', '""')
                              for gsim in gsims]  # quotes Excel-friendly
    else:
        arr['branch_path'] = rlzs['branch_path']
    return arr


@extract.add('gsims_by_trt')
def extract_gsims_by_trt(dstore, what):
    """
    Extract the dictionary gsims_by_trt
    """
    return ArrayWrapper((), dstore['csm_info'].gsim_lt.values)


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
    names = [name for name in dstore['assetcol/array'].dtype.names
             if name.startswith(('value-', 'number', 'occupants_'))
             and not name.endswith('_None')]
    return ArrayWrapper(numpy.array(names), dic)


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
    return ArrayWrapper(arr, dic)


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
    for tag, vals in qdict.items():
        cond = numpy.zeros(len(arr), bool)
        for val in vals:
            tagidx, = numpy.where(dic[tag] == val)
            cond |= arr[tag] == tagidx
        arr = arr[cond]
    return ArrayWrapper(arr, dic)


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


def get_mesh(sitecol, complete=True):
    """
    :returns:
        a lon-lat or lon-lat-depth array depending if the site collection
        is at sea level or not
    """
    sc = sitecol.complete if complete else sitecol
    if sc.at_sea_level():
        mesh = numpy.zeros(len(sc), [('lon', F64), ('lat', F64)])
        mesh['lon'] = sc.lons
        mesh['lat'] = sc.lats
    else:
        mesh = numpy.zeros(len(sc), [('lon', F64), ('lat', F64),
                                     ('depth', F64)])
        mesh['lon'] = sc.lons
        mesh['lat'] = sc.lats
        mesh['depth'] = sc.depths
    return mesh


def hazard_items(dic, mesh, *extras, **kw):
    """
    :param dic: dictionary of arrays of the same shape
    :param mesh: a mesh array with lon, lat fields of the same length
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
    yield 'all', util.compose_arrays(mesh, array)


def _get_dict(dstore, name, imtls, stats):
    dic = {}
    dtlist = []
    for imt, imls in imtls.items():
        dt = numpy.dtype([(str(iml), F32) for iml in imls])
        dtlist.append((imt, dt))
    for s, stat in enumerate(stats):
        dic[stat] = dstore[name][:, s].flatten().view(dtlist)
    return dic


@extract.add('hcurves')
def extract_hcurves(dstore, what):
    """
    Extracts hazard curves. Use it as /extract/hcurves?kind=mean or
    /extract/hcurves?kind=rlz-0, /extract/hcurves?kind=stats,
    /extract/hcurves?kind=rlzs etc
    """
    info = get_info(dstore)
    if what == '':  # npz exports for QGIS
        sitecol = dstore['sitecol']
        mesh = get_mesh(sitecol, complete=False)
        dic = _get_dict(dstore, 'hcurves-stats', info['imtls'], info['stats'])
        yield from hazard_items(
            dic, mesh, investigation_time=info['investigation_time'])
        return
    params = parse(what, info)
    if 'imt' in params:
        [imt] = params['imt']
        slc = info['imtls'](imt)
    else:
        slc = ALL
    sids = params.get('site_id', ALL)
    if params['rlzs']:
        dset = dstore['hcurves-rlzs']
        for k in params['k']:
            yield 'rlz-%03d' % k, hdf5.extract(dset, sids, k, slc)[:, 0]
    else:
        dset = dstore['hcurves-stats']
        stats = list(info['stats'])
        for k in params['k']:
            yield stats[k], hdf5.extract(dset, sids, k, slc)[:, 0]
    yield from params.items()


@extract.add('hmaps')
def extract_hmaps(dstore, what):
    """
    Extracts hazard maps. Use it as /extract/hmaps?imt=PGA
    """
    info = get_info(dstore)
    if what == '':  # npz exports for QGIS
        sitecol = dstore['sitecol']
        mesh = get_mesh(sitecol, complete=False)
        dic = _get_dict(dstore, 'hmaps-stats',
                        {imt: info['poes'] for imt in info['imtls']},
                        info['stats'])
        yield from hazard_items(
            dic, mesh, investigation_time=info['investigation_time'])
        return
    params = parse(what, info)
    if 'imt' in params:
        [imt] = params['imt']
        m = info['imt'][imt]
        s = slice(m, m + 1)
    else:
        s = ALL
    if params['rlzs']:
        dset = dstore['hmaps-rlzs']
        for k in params['k']:
            yield 'rlz-%03d' % k, hdf5.extract(dset, ALL, k, s, ALL)[:, 0]
    else:
        dset = dstore['hmaps-stats']
        stats = list(info['stats'])
        for k in params['k']:
            yield stats[k], hdf5.extract(dset, ALL, k, s, ALL)[:, 0]
    yield from params.items()


@extract.add('uhs')
def extract_uhs(dstore, what):
    """
    Extracts uniform hazard spectra. Use it as /extract/uhs?kind=mean or
    /extract/uhs?kind=rlz-0, etc
    """
    info = get_info(dstore)
    if what == '':  # npz exports for QGIS
        sitecol = dstore['sitecol']
        mesh = get_mesh(sitecol, complete=False)
        dic = {}
        for stat, s in info['stats'].items():
            hmap = dstore['hmaps-stats'][:, s]
            dic[stat] = calc.make_uhs(hmap, info)
        yield from hazard_items(
            dic, mesh, investigation_time=info['investigation_time'])
        return
    params = parse(what, info)
    periods = []
    for m, imt in enumerate(info['imtls']):
        if imt == 'PGA' or imt.startswith('SA'):
            periods.append(m)
    if 'site_id' in params:
        sids = params['site_id']
    else:
        sids = ALL
    if params['rlzs']:
        dset = dstore['hmaps-rlzs']
        for k in params['k']:
            yield ('rlz-%03d' % k,
                   hdf5.extract(dset, sids, k, periods, ALL)[:, 0])
    else:
        dset = dstore['hmaps-stats']
        stats = list(info['stats'])
        for k in params['k']:
            yield stats[k], hdf5.extract(dset, sids, k, periods, ALL)[:, 0]
    yield from params.items()


@extract.add('effect')
def extract_effect(dstore, what):
    """
    Extracts the effect of ruptures. Use it as /extract/effect
    """
    what = what or 'effect'
    grp = dstore[what]
    dist_bins = dict(grp.attrs)
    ndists = len(dist_bins[next(iter(dist_bins))])
    arr = numpy.zeros((len(grp), ndists, len(dist_bins)))
    for i, mag in enumerate(grp):
        arr[i] = dstore[what + '/' + mag][()]
    return ArrayWrapper(arr, dict(dist_bins=dist_bins, ndists=ndists,
                                  mags=[float(mag) for mag in grp]))


@extract.add('rups_by_mag_dist')
def extract_rups_by_mag_dist(dstore, what):
    """
    Extracts the number of ruptures by mag, dist.
    Use it as /extract/rups_by_mag_dist
    """
    return extract_effect(dstore, 'rups_by_mag_dist')


@extract.add('sources')
def extract_sources(dstore, what):
    """
    Extract information about a source model.
    Use it as /extract/sources?sm_id=0
    """
    qdict = parse(what)
    sm_id = int(qdict['sm_id'][0])
    arr = dstore['source_info']['sm_id', 'source_id', 'eff_ruptures', 'wkt']
    if sm_id not in numpy.unique(arr['sm_id']):
        raise ValueError('There is no source model #%d' % sm_id)
    return ArrayWrapper(get_array(arr, sm_id=sm_id), {'sm_id': sm_id})


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


def _get_curves(curves, li):
    shp = curves.shape + curves.dtype.shape
    return curves[()].view(F32).reshape(shp)[:, :, :, li]


def extract_curves(dstore, what, tot):
    """
    Porfolio loss curves from the ebrisk calculator:

    /extract/tot_curves?
    kind=stats&absolute=1&loss_type=occupants

    Returns an array of shape (P, S) or (P, R)
    """
    info = get_info(dstore)
    qdic = parse(what, info)
    k = qdic['k']  # rlz or stat index
    [l] = qdic['loss_type']  # loss type index
    tup = (slice(None), k, l)
    if qdic['rlzs']:
        kinds = ['rlz-%d' % r for r in k]
        arr = dstore[tot + 'curves-rlzs'][tup]  # shape P, R
        units = dstore.get_attr(tot + 'curves-rlzs', 'units')
        rps = dstore.get_attr(tot + 'curves-rlzs', 'return_periods')
    else:
        kinds = list(info['stats'])
        arr = dstore[tot + 'curves-stats'][tup]  # shape P, S
        units = dstore.get_attr(tot + 'curves-stats', 'units')
        rps = dstore.get_attr(tot + 'curves-stats', 'return_periods')
    if qdic['absolute'] == [1]:
        pass
    elif qdic['absolute'] == [0]:
        evalue = dstore['exposed_values/agg'][l]
        arr /= evalue
    else:
        raise ValueError('"absolute" must be 0 or 1 in %s' % what)
    attrs = dict(shape_descr=['return_period', 'kind'])
    attrs['return_period'] = list(rps)
    attrs['kind'] = kinds
    attrs['units'] = units  # used by the QGIS plugin
    return ArrayWrapper(arr, attrs)


extract.add('tot_curves')(partial(extract_curves, tot='tot_'))
extract.add('app_curves')(partial(extract_curves, tot='app_'))


@extract.add('agg_curves')
def extract_agg_curves(dstore, what):
    """
    Aggregate loss curves from the ebrisk calculator:

    /extract/agg_curves?
    kind=stats&absolute=1&loss_type=occupants&occupancy=RES

    Returns an array of shape (P, S, 1...) or (P, R, 1...)
    """
    info = get_info(dstore)
    qdic = parse(what, info)
    tagdict = qdic.copy()
    for a in ('k', 'rlzs', 'kind', 'loss_type', 'absolute'):
        del tagdict[a]
    k = qdic['k']  # rlz or stat index
    [l] = qdic['loss_type']  # loss type index
    tagnames = sorted(tagdict)
    if set(tagnames) != set(info['tagnames']):
        raise ValueError('Expected tagnames=%s, got %s' %
                         (info['tagnames'], tagnames))
    tagvalues = [tagdict[t][0] for t in tagnames]
    tagidx = []
    if tagnames:
        tagcol = dstore['assetcol/tagcol']
        for tagname, tagvalue in zip(tagnames, tagvalues):
            values = list(getattr(tagcol, tagname)[1:])
            tagidx.append(values.index(tagvalue))
    tup = tuple([slice(None), k, l] + tagidx)
    if qdic['rlzs']:
        kinds = ['rlz-%d' % r for r in k]
        arr = dstore['agg_curves-rlzs'][tup]  # shape P, R
        units = dstore.get_attr('agg_curves-rlzs', 'units')
        rps = dstore.get_attr('agg_curves-rlzs', 'return_periods')
    else:
        kinds = list(info['stats'])
        arr = dstore['agg_curves-stats'][tup]  # shape P, S
        units = dstore.get_attr('agg_curves-stats', 'units')
        rps = dstore.get_attr('agg_curves-stats', 'return_periods')
    if qdic['absolute'] == [1]:
        pass
    elif qdic['absolute'] == [0]:
        aggname = '_'.join(['agg'] + tagnames)
        tl = tuple(tagidx) + (l,)
        evalue = dstore['exposed_values/' + aggname][tl]  # shape T...
        arr /= evalue
    else:
        raise ValueError('"absolute" must be 0 or 1 in %s' % what)
    attrs = dict(shape_descr=['return_period', 'kind'] + tagnames)
    attrs['return_period'] = list(rps)
    attrs['kind'] = kinds
    attrs['units'] = units  # used by the QGIS plugin
    for tagname, tagvalue in zip(tagnames, tagvalues):
        attrs[tagname] = [tagvalue]
    if tagnames:
        arr = arr.reshape(arr.shape + (1,) * len(tagnames))
    return ArrayWrapper(arr, attrs)


@extract.add('agg_losses')
def extract_agg_losses(dstore, what):
    """
    Aggregate losses of the given loss type and tags. Use it as
    /extract/agg_losses/structural?taxonomy=RC&zipcode=20126
    /extract/agg_losses/structural?taxonomy=RC&zipcode=*

    :returns:
        an array of shape (T, R) if one of the tag names has a `*` value
        an array of shape (R,), being R the number of realizations
        an array of length 0 if there is no data for the given tags
    """
    loss_type, tags = get_loss_type_tags(what)
    if not loss_type:
        raise ValueError('loss_type not passed in agg_losses/<loss_type>')
    L = dstore['oqparam'].lti[loss_type]
    if 'losses_by_asset' in dstore:  # scenario_risk
        stats = None
        losses = dstore['losses_by_asset'][:, :, L]['mean']
    elif 'avg_losses' in dstore:  # ebrisk
        stats = ['mean']
        losses = dstore['avg_losses'][:, L].reshape(-1, 1)
    elif 'avg_losses-stats' in dstore:  # event_based_risk, classical_risk
        stats = decode(dstore['avg_losses-stats'].attrs['stats'])
        losses = dstore['avg_losses-stats'][:, :, L]
    elif 'avg_losses-rlzs' in dstore:  # event_based_risk, classical_risk
        stats = ['mean']
        losses = dstore['avg_losses-rlzs'][:, :, L]
    else:
        raise KeyError('No losses found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], losses, tags, stats)


@extract.add('agg_damages')
def extract_agg_damages(dstore, what):
    """
    Aggregate damages of the given loss type and tags. Use it as
    /extract/agg_damages/structural?taxonomy=RC&zipcode=20126

    :returns:
        array of shape (R, D), being R the number of realizations and D the
        number of damage states, or an array of length 0 if there is no data
        for the given tags
    """
    loss_type, tags = get_loss_type_tags(what)
    if 'dmg_by_asset' in dstore:  # scenario_damage
        lti = dstore['oqparam'].lti[loss_type]
        losses = dstore['dmg_by_asset'][:, :, lti, 0]
    else:
        raise KeyError('No damages found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], losses, tags)


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
    ltypes = qdic.get('loss_type', [])  # list of indices
    if ltypes:
        lti = ltypes[0]
        lt = [lt for lt, i in loss_types.items() if i == lti]
        array = dstore[name + suffix][:, qdic['k'][0], lti]
        aw = ArrayWrapper(assetcol.aggregate_by(tagnames, array), {}, (lt,))
    else:
        array = dstore[name + suffix][:, qdic['k'][0]]
        aw = ArrayWrapper(assetcol.aggregate_by(tagnames, array), {},
                          loss_types)
    for tagname in tagnames:
        setattr(aw, tagname, getattr(assetcol.tagcol, tagname)[1:])
    aw.shape_descr = tagnames
    return aw


@extract.add('losses_by_asset')
def extract_losses_by_asset(dstore, what):
    loss_dt = dstore['oqparam'].loss_dt()
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = util.get_assets(dstore)
    if 'losses_by_asset' in dstore:
        losses_by_asset = dstore['losses_by_asset'][()]
        for rlz in rlzs:
            # I am exporting the 'mean' and ignoring the 'stddev'
            losses = cast(losses_by_asset[:, rlz.ordinal]['mean'], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield 'rlz-%03d' % rlz.ordinal, data
    elif 'avg_losses-stats' in dstore:
        avg_losses = dstore['avg_losses-stats'][()]
        stats = decode(dstore['avg_losses-stats'].attrs['stats'])
        for s, stat in enumerate(stats):
            losses = cast(avg_losses[:, s], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield stat, data
    elif 'avg_losses-rlzs' in dstore:  # there is only one realization
        avg_losses = dstore['avg_losses-rlzs'][()]
        losses = cast(avg_losses, loss_dt)
        data = util.compose_arrays(assets, losses)
        yield 'rlz-000', data


@extract.add('losses_by_event')
def extract_losses_by_event(dstore, what):
    dic = group_array(dstore['losses_by_event'][()], 'rlzi')
    for rlzi in dic:
        yield 'rlz-%03d' % rlzi, dic[rlzi]


def _gmf(data, num_sites, imts):
    # convert data into the composite array expected by QGIS
    eids = sorted(numpy.unique(data['eid']))
    eid2idx = {eid: idx for idx, eid in enumerate(eids)}
    E = len(eid2idx)
    gmf_dt = numpy.dtype([(imt, (F32, (E,))) for imt in imts])
    gmfa = numpy.zeros(num_sites, gmf_dt)
    for rec in data:
        arr = gmfa[rec['sid']]
        for imt, gmv in zip(imts, rec['gmv']):
            arr[imt][eid2idx[rec['eid']]] = gmv
    return gmfa


# used by the QGIS plugin
@extract.add('gmf_data')
def extract_gmf_npz(dstore, what):
    oq = dstore['oqparam']
    qdict = parse(what)
    [eid] = qdict.get('event_id', [None])
    mesh = get_mesh(dstore['sitecol'])
    n = len(mesh)
    data = dstore['gmf_data/data']
    if eid is None:  # get all events
        rlz = dstore['events']['rlz_id']
        for rlzi in sorted(set(rlz)):
            idx = rlz[data['eid']] == rlzi
            gmfa = _gmf(data[idx], n, oq.imtls)
            logging.info('Exporting array%s for rlz#%d', gmfa.shape, rlzi)
            yield 'rlz-%03d' % rlzi, util.compose_arrays(mesh, gmfa)
    else:  # get a single event
        rlzi = dstore['events'][eid]['rlz_id']
        idx = data['eid'] == eid
        if idx.any():
            gmfa = _gmf(data[idx], n, oq.imtls)
            yield 'rlz-%03d' % rlzi, util.compose_arrays(mesh, gmfa)
        else:  # zero GMF
            yield 'rlz-%03d' % rlzi, []


@extract.add('num_events')
def extract_num_events(dstore, what):
    """
    :returns: the number of events (if any)
    """
    yield 'num_events', len(dstore['events'])


def build_damage_dt(dstore, mean_std=True):
    """
    :param dstore: a datastore instance
    :param mean_std: a flag (default True)
    :returns:
       a composite dtype loss_type -> (mean_ds1, stdv_ds1, ...) or
       loss_type -> (ds1, ds2, ...) depending on the flag mean_std
    """
    oq = dstore['oqparam']
    damage_states = ['no_damage'] + list(
        dstore.get_attr('risk_model', 'limit_states'))
    dt_list = []
    for ds in damage_states:
        ds = str(ds)
        if mean_std:
            dt_list.append(('%s_mean' % ds, F32))
            dt_list.append(('%s_stdv' % ds, F32))
        else:
            dt_list.append((ds, F32))
    damage_dt = numpy.dtype(dt_list)
    loss_types = oq.loss_dt().names
    return numpy.dtype([(lt, damage_dt) for lt in loss_types])


def build_damage_array(data, damage_dt):
    """
    :param data: an array of shape (A, L, 1, D) or (A, L, 2, D)
    :param damage_dt: a damage composite data type loss_type -> states
    :returns: a composite array of length N and dtype damage_dt
    """
    A, L, MS, D = data.shape
    dmg = numpy.zeros(A, damage_dt)
    for a in range(A):
        for l, lt in enumerate(damage_dt.names):
            std = any(f for f in damage_dt[lt].names if f.endswith('_stdv'))
            if MS == 1 or not std:  # there is only the mean value
                dmg[lt][a] = tuple(data[a, l, 0])
            else:  # there are both mean and stddev
                # data[a, l].T has shape (D, 2)
                dmg[lt][a] = tuple(numpy.concatenate(data[a, l].T))
    return dmg


@extract.add('dmg_by_asset')
def extract_dmg_by_asset_npz(dstore, what):
    damage_dt = build_damage_dt(dstore)
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    data = dstore['dmg_by_asset']
    assets = util.get_assets(dstore)
    for rlz in rlzs:
        dmg_by_asset = build_damage_array(data[:, rlz.ordinal], damage_dt)
        yield 'rlz-%03d' % rlz.ordinal, util.compose_arrays(
            assets, dmg_by_asset)


@extract.add('event_based_mfd')
def extract_mfd(dstore, what):
    """
    Display num_ruptures by magnitude for event based calculations.
    Example: http://127.0.0.1:8800/v1/calc/30/extract/event_based_mfd?kind=mean
    """
    oq = dstore['oqparam']
    qdic = parse(what)
    kind_mean = 'mean' in qdic.get('kind', [])
    kind_by_group = 'by_group' in qdic.get('kind', [])
    weights = dstore['csm_info/sm_data']['weight']
    sm_idx = dstore['csm_info/sg_data']['sm_id']
    grp_weight = weights[sm_idx]
    duration = oq.investigation_time * oq.ses_per_logic_tree_path
    dic = {'duration': duration}
    dd = collections.defaultdict(float)
    rups = dstore['ruptures']['grp_id', 'mag', 'n_occ']
    mags = sorted(numpy.unique(rups['mag']))
    magidx = {mag: idx for idx, mag in enumerate(mags)}
    num_groups = rups['grp_id'].max() + 1
    frequencies = numpy.zeros((len(mags), num_groups), float)
    for grp_id, mag, n_occ in rups:
        if kind_mean:
            dd[mag] += n_occ * grp_weight[grp_id] / duration
        if kind_by_group:
            frequencies[magidx[mag], grp_id] += n_occ / duration
    dic['magnitudes'] = numpy.array(mags)
    if kind_mean:
        dic['mean_frequency'] = numpy.array([dd[mag] for mag in mags])
    if kind_by_group:
        for grp_id, freqs in enumerate(frequencies.T):
            dic['grp-%02d_frequency' % grp_id] = freqs
    return ArrayWrapper((), dic)

# NB: this is an alternative, slower approach giving exactly the same numbers;
# it is kept here for sake of comparison in case of dubious MFDs
# @extract.add('event_based_mfd')
# def extract_mfd(dstore, what):
#     oq = dstore['oqparam']
#     rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
#     weights = [rlz.weight['default'] for rlz in rlzs]
#     duration = oq.investigation_time * oq.ses_per_logic_tree_path
#     mag = dict(dstore['ruptures']['rup_id', 'mag'])
#     mags = numpy.unique(dstore['ruptures']['mag'])
#     mags.sort()
#     magidx = {mag: idx for idx, mag in enumerate(mags)}
#     occurrences = numpy.zeros((len(mags), len(weights)), numpy.uint32)
#     events = dstore['events'][()]
#     dic = {'duration': duration, 'magnitudes': mags,
#            'mean_frequencies': numpy.zeros(len(mags))}
#     for rlz, weight in enumerate(weights):
#         eids = get_array(events, rlz=rlz)['id']
#         if len(eids) == 0:
#             continue
#         rupids, n_occs = numpy.unique(eids // 2 ** 32, return_counts=True)
#         for rupid, n_occ in zip(rupids, n_occs):
#             occurrences[magidx[mag[rupid]], rlz] += n_occ
#         dic['mean_frequencies'] += occurrences[:, rlz] * weight / duration
#     return ArrayWrapper(occurrences, dic)


@extract.add('src_loss_table')
def extract_src_loss_table(dstore, loss_type):
    """
    Extract the source loss table for a give loss type, ordered in decreasing
    order. Example:
    http://127.0.0.1:8800/v1/calc/30/extract/src_loss_table/structural
    """
    source_ids = dstore['source_info']['source_id']
    idxs = dstore['ruptures'][('srcidx', 'grp_id')]
    losses = dstore['rup_loss_table'][loss_type]
    slt = numpy.zeros(len(source_ids), [('grp_id', U32), (loss_type, F32)])
    for loss, (srcidx, grp_id) in zip(losses, idxs):
        slt[srcidx][loss_type] += loss
        slt[srcidx]['grp_id'] = grp_id
    slt = util.compose_arrays(source_ids, slt, 'source_id')
    slt.sort(order=loss_type)
    return slt[::-1]


@extract.add('mean_std_curves')
def extract_mean_std_curves(dstore, what):
    """
    Yield imls/IMT and poes/IMT containg mean and stddev for all sites
    """
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    w = [rlz.weight for rlz in rlzs_assoc.realizations]
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
    return ArrayWrapper((), dstore.get_attrs('risk_model'))


def _get(dstore, name):
    try:
        dset = dstore[name + '-stats']
        return dset, decode(dset.attrs['stats'])
    except KeyError:  # single realization
        return dstore[name + '-rlzs'], ['mean']


@extract.add('rupture')
def extract_rupture(dstore, rup_id):
    """
    Extract information about the given event index.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/rupture/1066
    """
    ridx = list(dstore['ruptures']['id']).index(int(rup_id))
    [getter] = getters.gen_rupture_getters(dstore, slice(ridx, ridx + 1))
    [ebr] = getter.get_ruptures()
    return ArrayWrapper((), ebr.rupture.todict())


@extract.add('event_info')
def extract_event_info(dstore, eidx):
    """
    Extract information about the given event index.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/event_info/0
    """
    event = dstore['events'][int(eidx)]
    ridx = event['rup_id']
    [getter] = getters.gen_rupture_getters(dstore, slice(ridx, ridx + 1))
    rupdict = getter.get_rupdict()
    rlzi = event['rlz_id']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    gsim = rlzs_assoc.gsim_by_trt[rlzi][rupdict['trt']]
    for key, val in rupdict.items():
        yield key, val
    yield 'rlzi', rlzi
    yield 'gsim', repr(gsim)


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


def disagg_outputs(dstore, imt, sid, poe_id, rlz=None):
    """
    :returns:
        a list of output keys (one per realization) unless rlz is specified,
        then returns a list with a single element corresponding to the rlz
    """
    key = '%s-sid-%d-poe-%d' % (imt, sid, poe_id)
    if rlz is not None:
        key = 'rlz-%d-%s' % (rlz, key)
    outs = []
    for name, out in dstore['disagg'].items():
        if name.endswith(key):
            outs.append(out)
    return outs


@extract.add('disagg')
def extract_disagg(dstore, what):
    """
    Extract a disaggregation output
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/
    disagg?kind=Mag_Dist&imt=PGA&poe_id=0&site_id=1&rlz=0
    """
    qdict = parse(what)
    label = qdict['kind'][0]
    imt = qdict['imt'][0]
    poe_idx = int(qdict['poe_id'][0])
    sid = int(qdict['site_id'][0])
    rlz = int(qdict['rlz'][0]) if 'rlz' in qdict else None
    allnames = []
    allvalues = []
    for dset in disagg_outputs(dstore, imt, sid, poe_idx, rlz):
        matrix = dset[label][()]

        # adapted from the nrml_converters
        disag_tup = tuple(label.split('_'))
        if disag_tup == ('Mag', 'Lon', 'Lat'):
            matrix = numpy.swapaxes(matrix, 0, 1)
            matrix = numpy.swapaxes(matrix, 1, 2)
            disag_tup = ('Lon', 'Lat', 'Mag')

        axis = [dset.attrs[v.lower() + '_bin_edges'] for v in disag_tup]
        # compute axis mid points
        axis = [(ax[: -1] + ax[1:]) / 2. if ax.dtype == float
                else ax for ax in axis]
        values = None
        if len(axis) == 1:
            values = numpy.array([axis[0], matrix.flatten()]).T
        else:
            grids = numpy.meshgrid(*axis, indexing='ij')
            values = [g.flatten() for g in grids]
            values.append(matrix.flatten())
            values = numpy.array(values).T
        allnames.append(os.path.basename(dset.name))
        allvalues.append(values)
    if not allnames:
        raise KeyError('No data for ' + what)
    elif len(allnames) == 1:
        return ArrayWrapper(values, qdict)
    else:
        qdict['names'] = allnames
        return ArrayWrapper(numpy.array(allvalues), qdict)


@extract.add('disagg_layer')
def extract_disagg_layer(dstore, what):
    """
    Extract a disaggregation output containing all sites
    for the first realization.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/
    disagg_layer?kind=Mag_Dist&imt=PGA&poe_id=0
    """
    qdict = parse(what)
    [label] = qdict['kind']
    [imt] = qdict['imt']
    poe_id = int(qdict['poe_id'][0])
    grp = disagg_outputs(dstore, imt, 0, poe_id)[0]
    dset = grp[label]
    edges = {k: grp.attrs[k] for k in grp.attrs if k.endswith('_edges')}
    dt = [('site_id', U32), ('lon', F32), ('lat', F32), ('rlz', U32),
          ('poes', (dset.dtype, dset.shape))]
    sitecol = dstore['sitecol']
    out = numpy.zeros(len(sitecol), dt)
    out[0] = (0, sitecol.lons[0], sitecol.lats[0], grp.attrs['rlzi'], dset[()])
    for sid, lon, lat, rec in zip(
            sitecol.sids, sitecol.lons, sitecol.lats, out):
        if sid > 0:
            grp = disagg_outputs(dstore, imt, sid, poe_id)[0]
            rec['site_id'] = sid
            rec['lon'] = lon
            rec['lat'] = lat
            rec['rlz'] = grp.attrs['rlzi']
            rec['poes'] = grp[label][()]
    return ArrayWrapper(out, edges)

# ######################### extracting ruptures ##############################


class RuptureData(object):
    """
    Container for information about the ruptures of a given
    tectonic region type.
    """
    def __init__(self, trt, gsims):
        self.trt = trt
        self.cmaker = ContextMaker(trt, gsims)
        self.params = sorted(self.cmaker.REQUIRES_RUPTURE_PARAMETERS -
                             set('mag strike dip rake hypo_depth'.split()))
        self.dt = numpy.dtype([
            ('rup_id', U32), ('srcidx', U32), ('multiplicity', U16),
            ('occurrence_rate', F64),
            ('mag', F32), ('lon', F32), ('lat', F32), ('depth', F32),
            ('strike', F32), ('dip', F32), ('rake', F32),
            ('boundaries', hdf5.vfloat32)] +
            [(param, F32) for param in self.params])

    def to_array(self, ebruptures):
        """
        Convert a list of ebruptures into an array of dtype RuptureRata.dt
        """
        data = []
        for ebr in ebruptures:
            rup = ebr.rupture
            self.cmaker.add_rup_params(rup)
            ruptparams = tuple(getattr(rup, param) for param in self.params)
            point = rup.surface.get_middle_point()
            boundaries = rup.surface.get_surface_boundaries_3d()
            try:
                rate = ebr.rupture.occurrence_rate
            except AttributeError:  # for nonparametric sources
                rate = numpy.nan
            data.append(
                (ebr.id, ebr.srcidx, ebr.n_occ, rate,
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
    dtlist = [('rup_id', U32), ('multiplicity', U16), ('mag', F32),
              ('centroid_lon', F32), ('centroid_lat', F32),
              ('centroid_depth', F32), ('trt', '<S50'),
              ('strike', F32), ('dip', F32), ('rake', F32)]
    rows = []
    boundaries = []
    for rgetter in getters.gen_rupture_getters(dstore):
        rups = rgetter.get_ruptures(min_mag)
        rup_data = RuptureData(rgetter.trt, rgetter.rlzs_by_gsim)
        for r, rup in zip(rup_data.to_array(rups), rups):
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
    arr.sort(order='rup_id')
    geoms = gzip.compress('\n'.join(boundaries).encode('utf-8'))
    return ArrayWrapper(arr, dict(investigation_time=oq.investigation_time,
                                  boundaries=geoms))

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
        self.calc_id = calc_id
        self.dstore = util.read(calc_id)
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
        url = '%s/v1/calc/%d/oqparam' % (self.server, calc_id)
        logging.info('GET %s', url)
        resp = self.sess.get(url)
        if resp.status_code == 404:
            raise WebAPIError('Not Found: %s' % url)
        elif resp.status_code != 200:
            raise WebAPIError(resp.text)
        self.status = self.sess.get(
            '%s/v1/calc/%d/status' % (self.server, calc_id)).json()
        self.oqparam = object.__new__(oqvalidation.OqParam)
        vars(self.oqparam).update(resp.json())

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
        npz = numpy.load(io.BytesIO(resp.content), allow_pickle=True)
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
