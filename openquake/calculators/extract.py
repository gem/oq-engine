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
from functools import lru_cache
import collections
import operator
import logging
import ast
import io

import requests
from h5py._hl.dataset import Dataset
from h5py._hl.group import Group
import numpy
from openquake.baselib import config, hdf5
from openquake.baselib.hdf5 import ArrayWrapper, vstr
from openquake.baselib.general import group_array, deprecated, println
from openquake.baselib.python3compat import encode
from openquake.calculators import getters
from openquake.commonlib import calc, util, oqvalidation

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
                poes=oq.poes, imt=imt, uhs_dt=oq.uhs_dt())


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
        return ArrayWrapper(obj.value, obj.attrs)
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

    For instance extract(dstore, 'sitecol'), extract(dstore, 'asset_values/0')
    etc.
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


# used by the QGIS plugin
@extract.add('realizations')
def extract_realizations(dstore, dummy):
    """
    Extract an array of realizations. Use it as /extract/realizations
    """
    rlzs = dstore['csm_info'].rlzs
    dt = [('ordinal', U32), ('weight', F32), ('gsims', '<S64')]
    arr = numpy.zeros(len(rlzs), dt)
    arr['ordinal'] = rlzs['ordinal']
    arr['weight'] = rlzs['weight']
    arr['gsims'] = rlzs['branch_path']  # this is used in scenario by QGIS
    return arr


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
    arr = dstore['assetcol/array'].value
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
    arr = dstore['asset_risk'].value
    for tag, vals in qdict.items():
        cond = numpy.zeros(len(arr), bool)
        for val in vals:
            tagidx, = numpy.where(dic[tag] == val)
            cond |= arr[tag] == tagidx
        arr = arr[cond]
    return ArrayWrapper(arr, dic)


@extract.add('asset_values', cache=True)
def extract_asset_values(dstore, sid):
    """
    Extract an array of asset values for the given sid. Use it as
    /extract/asset_values/0

    :returns:
        (aid, loss_type1, ..., loss_typeN) composite array
    """
    if sid:
        return extract(dstore, 'asset_values')[int(sid)]
    assetcol = extract(dstore, 'assetcol')
    asset_refs = assetcol.asset_refs
    assets_by_site = assetcol.assets_by_site()
    lts = assetcol.loss_types
    dt = numpy.dtype([('aref', asset_refs.dtype), ('aid', numpy.uint32)] +
                     [(str(lt), numpy.float32) for lt in lts])
    data = []
    for assets in assets_by_site:
        vals = numpy.zeros(len(assets), dt)
        for a, asset in enumerate(assets):
            vals[a]['aref'] = asset_refs[a]
            vals[a]['aid'] = asset['ordinal']
            for lt in lts:
                vals[a][lt] = asset['value-' + lt]
        data.append(vals)
    return data


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
    return curves.value.view(F32).reshape(shp)[:, :, :, li]


# this is used by the QGIS plugin, but it should be removed
@extract.add('agg_curves')
def extract_agg_curves(dstore, what):
    """
    Aggregate loss curves of the given loss type and tags for
    event based risk calculations. Use it as
    /extract/agg_curves/structural?taxonomy=RC&zipcode=20126
    :returns:
        array of shape (S, P), being P the number of return periods
        and S the number of statistics
    """
    from openquake.calculators.export.loss_curves import get_loss_builder
    oq = dstore['oqparam']
    loss_type, tags = get_loss_type_tags(what)
    if 'curves-stats' in dstore:  # event_based_risk
        losses = _get_curves(dstore['curves-stats'], oq.lti[loss_type])
        stats = dstore['curves-stats'].attrs['stats']
    elif 'curves-rlzs' in dstore:  # event_based_risk, 1 rlz
        losses = _get_curves(dstore['curves-rlzs'], oq.lti[loss_type])
        assert losses.shape[1] == 1, 'There must be a single realization'
        stats = [b'mean']  # suitable to be stored as hdf5 attribute
    else:
        raise KeyError('No curves found in %s' % dstore)
    res = _filter_agg(dstore['assetcol'], losses, tags, stats)
    cc = dstore['assetcol/cost_calculator']
    res.units = cc.get_units(loss_types=[loss_type])
    res.return_periods = get_loss_builder(dstore).return_periods
    return res


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
    l = dstore['oqparam'].lti[loss_type]
    if 'losses_by_asset' in dstore:  # scenario_risk
        stats = None
        losses = dstore['losses_by_asset'][:, :, l]['mean']
    elif 'avg_losses-stats' in dstore:  # event_based_risk, classical_risk
        stats = dstore['avg_losses-stats'].attrs['stats']
        losses = dstore['avg_losses-stats'][:, :, l]
    elif 'avg_losses-rlzs' in dstore:  # event_based_risk, classical_risk
        stats = [b'mean']
        losses = dstore['avg_losses-rlzs'][:, :, l]
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
    ltypes = qdic.get('loss_type', [])
    if ltypes:
        array = dstore[name + suffix][:, qdic['k'][0], ltypes[0]]
    else:
        array = dstore[name + suffix][:, qdic['k'][0]]
    aw = ArrayWrapper(assetcol.aggregate_by(tagnames, array), {})
    for tagname in tagnames:
        setattr(aw, tagname, getattr(assetcol.tagcol, tagname))
    aw.tagnames = encode(tagnames)
    if not ltypes:
        aw.extra = ('loss_type',) + tuple(info['loss_types'])
    return aw


@extract.add('losses_by_asset')
def extract_losses_by_asset(dstore, what):
    loss_dt = dstore['oqparam'].loss_dt()
    rlzs = dstore['csm_info'].get_rlzs_assoc().realizations
    assets = util.get_assets(dstore)
    if 'losses_by_asset' in dstore:
        losses_by_asset = dstore['losses_by_asset'].value
        for rlz in rlzs:
            # I am exporting the 'mean' and ignoring the 'stddev'
            losses = cast(losses_by_asset[:, rlz.ordinal]['mean'], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield 'rlz-%03d' % rlz.ordinal, data
    elif 'avg_losses-stats' in dstore:
        avg_losses = dstore['avg_losses-stats'].value
        stats = dstore['avg_losses-stats'].attrs['stats']
        for s, stat in enumerate(stats):
            losses = cast(avg_losses[:, s], loss_dt)
            data = util.compose_arrays(assets, losses)
            yield stat, data
    elif 'avg_losses-rlzs' in dstore:  # there is only one realization
        avg_losses = dstore['avg_losses-rlzs'].value
        losses = cast(avg_losses, loss_dt)
        data = util.compose_arrays(assets, losses)
        yield 'rlz-000', data


@extract.add('losses_by_event')
def extract_losses_by_event(dstore, what):
    dic = group_array(dstore['losses_by_event'].value, 'rlzi')
    for rlzi in dic:
        yield 'rlz-%03d' % rlzi, dic[rlzi]


def _gmf_scenario(data, num_sites, imts):
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
    return gmfa, E


@extract.add('gmf_data')
def extract_gmf_scenario_npz(dstore, what):
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    n = len(mesh)
    data_by_rlzi = group_array(dstore['gmf_data/data'].value, 'rlzi')
    for rlzi in data_by_rlzi:
        gmfa, e = _gmf_scenario(data_by_rlzi[rlzi], n, oq.imtls)
        logging.info('Exporting array of shape %s for rlz %d',
                     (n, e), rlzi)
        yield 'rlz-%03d' % rlzi, util.compose_arrays(mesh, gmfa)


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
    Example: http://127.0.0.1:8800/v1/calc/30/extract/event_based_mfd
    """
    dd = collections.defaultdict(int)
    for rup in dstore['ruptures'].value:
        dd[rup['mag']] += 1
    dt = numpy.dtype([('mag', float), ('freq', int)])
    magfreq = numpy.array(sorted(dd.items(), key=operator.itemgetter(0)), dt)
    return magfreq


@extract.add('src_loss_table')
def extract_src_loss_table(dstore, loss_type):
    """
    Extract the source loss table for a give loss type, ordered in decreasing
    order. Example:
    http://127.0.0.1:8800/v1/calc/30/extract/src_loss_table/structural
    """
    oq = dstore['oqparam']
    li = oq.lti[loss_type]
    source_ids = dstore['source_info']['source_id']
    idxs = dstore['ruptures'].value[['srcidx', 'grp_id']]
    losses = dstore['rup_loss_table'][:, li]
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
    getter = getters.PmapGetter(dstore)
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
        return dset, [b.decode('utf8') for b in dset.attrs['stats']]
    except KeyError:  # single realization
        return dstore[name + '-rlzs'], ['mean']


@extract.add('losses_by_tag')
@deprecated(msg='This feature will be removed soon')
def losses_by_tag(dstore, tag):
    """
    Statistical average losses by tag. For instance call

    $ oq extract losses_by_tag/occupancy
    """
    dt = [(tag, vstr)] + dstore['oqparam'].loss_dt_list()
    aids = dstore['assetcol/array'][tag]
    dset, stats = _get(dstore, 'avg_losses')
    arr = dset.value
    tagvalues = dstore['assetcol/tagcol/' + tag][1:]  # except tagvalue="?"
    for s, stat in enumerate(stats):
        out = numpy.zeros(len(tagvalues), dt)
        for li, (lt, lt_dt) in enumerate(dt[1:]):
            for i, tagvalue in enumerate(tagvalues):
                out[i][tag] = tagvalue
                counts = arr[aids == i + 1, s, li].sum()
                if counts:
                    out[i][lt] = counts
        yield stat, out


@extract.add('rupture')
def extract_rupture(dstore, serial):
    """
    Extract information about the given event index.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/rupture/1066
    """
    ridx = list(dstore['ruptures']['serial']).index(int(serial))
    [getter] = getters.gen_rupture_getters(dstore, slice(ridx, ridx + 1))
    yield from getter.get_rupdict().items()


@extract.add('event_info')
def extract_event_info(dstore, eidx):
    """
    Extract information about the given event index.
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/event_info/0
    """
    event = dstore['events'][int(eidx)]
    serial = int(event['id'] // TWO32)
    ridx = list(dstore['ruptures']['serial']).index(serial)
    [getter] = getters.gen_rupture_getters(dstore, slice(ridx, ridx + 1))
    rupdict = getter.get_rupdict()
    rlzi = event['rlz']
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


@extract.add('source_geom')
def extract_source_geom(dstore, srcidxs):
    """
    Extract the geometry of a given sources
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/source_geom/1,2,3
    """
    for i in srcidxs.split(','):
        rec = dstore['source_info'][int(i)]
        geom = dstore['source_geom'][rec['gidx1']:rec['gidx2']]
        yield rec['source_id'], geom

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

    def get(self, what):
        """
        :param what: what to extract
        :returns: an ArrayWrapper instance
        """
        return extract(self.dstore, what)

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
