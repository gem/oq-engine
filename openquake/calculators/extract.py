# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
import collections
import operator
import logging
from h5py._hl.dataset import Dataset
from h5py._hl.group import Group
import numpy
try:
    from functools import lru_cache
except ImportError:
    from openquake.risklib.utils import memoized
else:
    memoized = lru_cache(100)
from openquake.baselib.hdf5 import ArrayWrapper, vstr
from openquake.baselib.general import group_array
from openquake.baselib.python3compat import encode, decode
from openquake.calculators import getters
from openquake.calculators.export.loss_curves import get_loss_builder
from openquake.commonlib import calc, util

U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


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
    extract('sitecol', dstore). It is also possibly to extract the
    attributes, for instance with extract('sitecol.attrs', dstore).
    """
    obj = dstore[dspath]
    if isinstance(obj, Dataset):
        return ArrayWrapper(obj.value, obj.attrs)
    elif isinstance(obj, Group):
        return ArrayWrapper(numpy.array(list(obj)), obj.attrs)
    else:
        return obj


class Extract(collections.OrderedDict):
    """
    A callable dictionary of functions with a single instance called
    `extract`. Then `extract(dstore, fullkey)` dispatches to the function
    determined by the first part of `fullkey` (a slash-separated
    string) by passing as argument the second part of `fullkey`.

    For instance extract(dstore, 'sitecol), extract(dstore, 'asset_values/0')
    etc.
    """
    def add(self, key, cache=False):
        def decorator(func):
            self[key] = memoized(func) if cache else func
            return func
        return decorator

    def __call__(self, dstore, key):
        try:
            k, v = key.split('/', 1)
        except ValueError:   # no slashes
            k, v = key, ''
        if k in self:
            return self[k](dstore, v)
        else:
            return extract_(dstore, key)


extract = Extract()


# used by the QGIS plugin
@extract.add('realizations')
def extract_realizations(dstore, dummy):
    """
    Extract an array of realizations. Use it as /extract/realizations
    """
    return dstore['csm_info'].rlzs


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
    time_event = assetcol.time_event
    dt = numpy.dtype([('aref', asset_refs.dtype), ('aid', numpy.uint32)] +
                     [(str(lt), numpy.float32) for lt in lts])
    data = []
    for assets in assets_by_site:
        vals = numpy.zeros(len(assets), dt)
        for a, asset in enumerate(assets):
            vals[a]['aref'] = asset_refs[a]
            vals[a]['aid'] = asset.ordinal
            for lt in lts:
                vals[a][lt] = asset.value(lt, time_event)
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


@extract.add('hazard')
def extract_hazard(dstore, what):
    """
    Extracts hazard curves and possibly hazard maps and/or uniform hazard
    spectra. Use it as /extract/hazard/mean or /extract/hazard/rlz-0, etc
    """
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    yield 'sitecol', sitecol
    yield 'oqparam', oq
    yield 'imtls', oq.imtls
    yield 'realizations', dstore['csm_info'].rlzs
    yield 'checksum32', dstore['/'].attrs['checksum32']
    nsites = len(sitecol)
    M = len(oq.imtls)
    P = len(oq.poes)
    for statname, pmap in getters.PmapGetter(dstore, rlzs_assoc).items(what):
        for imt in oq.imtls:
            key = 'hcurves/%s/%s' % (imt, statname)
            arr = numpy.zeros((nsites, len(oq.imtls[imt])))
            for sid in pmap:
                arr[sid] = pmap[sid].array[oq.imtls(imt), 0]
            logging.info('extracting %s', key)
            yield key, arr
        try:
            hmap = dstore['hmaps/' + statname]
        except KeyError:  # for statname=rlz-XXX
            hmap = calc.make_hmap(pmap, oq.imtls, oq.poes)
        for p, poe in enumerate(oq.poes):
            key = 'hmaps/poe-%s/%s' % (poe, statname)
            arr = numpy.zeros((nsites, M))
            idx = [m * P + p for m in range(M)]
            for sid in pmap:
                arr[sid] = hmap[sid].array[idx, 0]
            logging.info('extracting %s', key)
            yield key, arr


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
    arr = dic[next(iter(dic))]
    dtlist = [(str(field), arr.dtype) for field in sorted(dic)]
    for field, dtype, values in extras:
        dtlist.append((str(field), dtype))
    array = numpy.zeros(arr.shape, dtlist)
    for field in dic:
        array[field] = dic[field]
    for field, dtype, values in extras:
        array[field] = values
    yield 'all', util.compose_arrays(mesh, array)


def _get_dict(dstore, name, imts, imls):
    dic = {}
    dtlist = []
    for imt, imls in zip(imts, imls):
        dt = numpy.dtype([(str(iml), F32) for iml in imls])
        dtlist.append((imt, dt))
    for statname, curves in dstore[name].items():
        dic[statname] = curves.value.view(dtlist).flatten()
    return dic


@extract.add('hcurves')
def extract_hcurves(dstore, what):
    """
    Extracts hazard curves. Use it as /extract/hcurves/mean or
    /extract/hcurves/rlz-0, /extract/hcurves/stats, /extract/hcurves/rlzs etc
    """
    if 'hcurves' not in dstore:
        return []
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    mesh = get_mesh(sitecol, complete=False)
    dic = _get_dict(dstore, 'hcurves', oq.imtls, oq.imtls.values())
    return hazard_items(dic, mesh, investigation_time=oq.investigation_time)


@extract.add('hmaps')
def extract_hmaps(dstore, what):
    """
    Extracts hazard maps. Use it as /extract/hmaps/mean or
    /extract/hmaps/rlz-0, etc
    """
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    mesh = get_mesh(sitecol)
    dic = _get_dict(dstore, 'hmaps', oq.imtls, [oq.poes] * len(oq.imtls))
    return hazard_items(dic, mesh, investigation_time=oq.investigation_time)


@extract.add('uhs')
def extract_uhs(dstore, what):
    """
    Extracts uniform hazard spectra. Use it as /extract/uhs/mean or
    /extract/uhs/rlz-0, etc
    """
    oq = dstore['oqparam']
    mesh = get_mesh(dstore['sitecol'])
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    dic = {}
    for name, hcurves in getters.PmapGetter(dstore, rlzs_assoc).items(what):
        dic[name] = calc.make_uhs(hcurves, oq.imtls, oq.poes, len(mesh))
    return hazard_items(dic, mesh, investigation_time=oq.investigation_time)


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
        array of shape (R, D), being R the number of realizations and D
        the number of damage states or array of length 0 if there is no
        data for the given tags
    """
    loss_type, tags = get_loss_type_tags(what)
    if 'dmg_by_asset' in dstore:  # scenario_damage
        losses = dstore['dmg_by_asset'][loss_type]['mean']
    else:
        raise KeyError('No damages found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], losses, tags)


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
    loss_type, tags = get_loss_type_tags(what)
    if 'curves-stats' in dstore:  # event_based_risk
        losses = dstore['curves-stats'][loss_type]
        stats = dstore['curves-stats'].attrs['stats']
    elif 'curves-rlzs' in dstore:  # event_based_risk, 1 rlz
        losses = dstore['curves-rlzs'][loss_type]
        assert losses.shape[1] == 1, 'There must be a single realization'
        stats = [b'mean']  # suitable to be stored as hdf5 attribute
    else:
        raise KeyError('No curves found in %s' % dstore)
    res = _filter_agg(dstore['assetcol'], losses, tags, stats)
    cc = dstore['assetcol/cost_calculator']
    res.units = cc.get_units(loss_types=[loss_type])
    res.return_periods = get_loss_builder(dstore).return_periods
    return res


@extract.add('aggregate_by')
def extract_aggregate_by(dstore, what):
    """
    /extract/aggregate_by/structural/taxonomy,occupancy/curves-stats
    return an array of shape (T, O, S, P)

    /extract/aggregate_by/structural/taxonomy,occupancy/avg_losses-stats
    return an array of shape (T, O, S)
    """
    loss_type, tagnames, dsetname = what.split('/')
    assert dsetname in ('avg_losses-stats', 'curves-stats'), dsetname
    tagnames = tagnames.split(',')
    assetcol = dstore['assetcol']
    if dsetname == 'curves-stats':
        array = dstore[dsetname][loss_type]
    else:
        lti = dstore['oqparam'].lti
        array = dstore[dsetname][:, :, lti[loss_type]]
    attrs = dstore[dsetname].attrs
    aw = ArrayWrapper(assetcol.aggregate_by(tagnames, array), {})
    for tagname in tagnames:
        setattr(aw, tagname, getattr(assetcol.tagcol, tagname))
    aw.stat = attrs['stats']
    if dsetname == 'curves-stats':
        aw.return_period = attrs['return_periods']
        aw.tagnames = encode(tagnames + ['stat', 'return_period'])
    else:
        aw.tagnames = encode(tagnames + ['stat'])
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
        dstore.get_attr(oq.risk_model, 'limit_states'))
    dt_list = []
    for ds in damage_states:
        ds = str(ds)
        if mean_std:
            dt_list.append(('%s_mean' % ds, F32))
            dt_list.append(('%s_stdv' % ds, F32))
        else:
            dt_list.append((ds, F32))
    damage_dt = numpy.dtype(dt_list)
    loss_types = dstore.get_attr(oq.risk_model, 'loss_types')
    return numpy.dtype([(str(lt), damage_dt) for lt in loss_types])


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
            if damage_dt[lt].names[0].endswith('_mean'):
                lst = []
                for m, s in zip(ms['mean'], ms['stddev']):
                    lst.append(m)
                    lst.append(s)
                dmg[lt][i] = tuple(lst)
            else:
                dmg[lt][i] = ms['mean']
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
    name = dstore['oqparam'].risk_model
    return ArrayWrapper(0, dstore.get_attrs(name))


def _get(dstore, name):
    try:
        dset = dstore[name + '-stats']
        return dset, [b.decode('utf8') for b in dset.attrs['stats']]
    except KeyError:  # single realization
        return dstore[name + '-rlzs'], ['mean']


@extract.add('losses_by_tag')
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


@extract.add('curves_by_tag')
def curves_by_tag(dstore, tag):
    """
    Statistical loss curves by tag. For instance call

    $ oq extract curves_by_tag/occupancy
    """
    dt = ([(tag, vstr), ('return_period', U32)] +
          dstore['oqparam'].loss_dt_list())
    aids = dstore['assetcol/array'][tag]
    dset, stats = _get(dstore, 'curves')
    periods = dset.attrs['return_periods']
    arr = dset.value
    P = arr.shape[-1]  # shape (A, S, P)
    tagvalues = dstore['assetcol/tagcol/' + tag][1:]  # except tagvalue="?"
    for s, stat in enumerate(stats):
        out = numpy.zeros(len(tagvalues) * P, dt)
        for li, (lt, lt_dt) in enumerate(dt[2:]):
            n = 0
            for i, tagvalue in enumerate(tagvalues):
                for p, period in enumerate(periods):
                    out[n][tag] = tagvalue
                    out[n]['return_period'] = period
                    counts = arr[aids == i + 1, s, p][lt].sum()
                    if counts:
                        out[n][lt] = counts
                    n += 1
        yield stat, out
