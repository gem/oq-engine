#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import collections
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
from openquake.baselib.general import DictArray
from openquake.commonlib import calc


def extract_(dstore, dspath):
    """
    Extracts an HDF5 path object from the datastore, for instance
    extract('sitecol', dstore)
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

    def __call__(self, dstore, key, *extra):
        try:
            k, v = key.split('/', 1)
        except ValueError:   # no slashes
            k, v = key, ''
        if k in self:
            return self[k](dstore, v, *extra)
        else:
            return extract_(dstore, key)

extract = Extract()


class ArrayWrapper(object):
    """
    A pickleable wrapper over an HDF5 dataset or group
    """
    def __init__(self, array, attrs):
        vars(self).update(attrs)
        self.array = array

    def __iter__(self):
        return iter(self.array)

    def __len__(self):
        return len(self.array)

    def __getitem__(self, idx):
        return self.array[idx]

    def __toh5__(self):
        return (self.array, {k: v for k, v in vars(self).items()
                             if k != 'array' and not k.startswith('_')})

    def __fromh5__(self, array, attrs):
        self.__init__(array, attrs)

    @property
    def dtype(self):
        return self.array.dtype


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
    asset_refs = extract(dstore, 'asset_refs')
    assetcol = extract(dstore, 'assetcol')
    assets_by_site = assetcol.assets_by_site()
    lts = assetcol.loss_types
    time_event = assetcol.time_event
    dt = numpy.dtype([('aref', asset_refs.dtype), ('aid', numpy.uint32)] +
                     [(str(lt), numpy.float32) for lt in lts])
    data = []
    for assets in assets_by_site:
        vals = numpy.zeros(len(assets), dt)
        for a, asset in enumerate(assets):
            vals[a]['aref'] = asset_refs[asset.idx]
            vals[a]['aid'] = asset.ordinal
            for lt in lts:
                vals[a][lt] = asset.value(lt, time_event)
        data.append(vals)
    return data


def convert_to_array(pmap, nsites, imtls):
    """
    Convert the probability map into a composite array with header
    of the form PGA-0.1, PGA-0.2 ...

    :param pmap: probability map
    :param nsites: total number of sites
    :param imtls: a DictArray with IMT and levels
    :returns: a composite array of lenght nsites
    """
    lst = []
    # build the export dtype, of the form PGA-0.1, PGA-0.2 ...
    for imt, imls in imtls.items():
        for iml in imls:
            lst.append(('%s-%s' % (imt, iml), numpy.float64))
    curves = numpy.zeros(nsites, numpy.dtype(lst))
    for sid, pcurve in pmap.items():
        curve = curves[sid]
        idx = 0
        for imt, imls in imtls.items():
            for iml in imls:
                curve['%s-%s' % (imt, iml)] = pcurve.array[idx]
                idx += 1
    return curves


@extract.add('hazard')
def extract_hazard(dstore, what):
    """
    Extracts hazard curves and possibly hazard maps and/or uniform hazard
    spectra. Use it as /extract/hazard/mean or /extract/hazard/rlz-0, etc
    """
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    yield 'sitecol', sitecol
    yield 'oqparam', dstore['oqparam']
    N = len(sitecol)
    if oq.poes:
        pdic = DictArray({imt: oq.poes for imt in oq.imtls})
    for kind, hcurves in calc.PmapGetter(dstore).items(what):
        logging.info('extracting hazard/%s', kind)
        yield 'hcurves-' + kind, convert_to_array(hcurves, N, oq.imtls)
        if oq.poes and oq.uniform_hazard_spectra:
            yield 'uhs-' + kind, calc.make_uhs(hcurves, oq.imtls, oq.poes, N)
        if oq.poes and oq.hazard_maps:
            hmaps = calc.make_hmap(hcurves, oq.imtls, oq.poes)
            yield 'hmaps-' + kind, convert_to_array(hmaps, N, pdic)


def _agg(losses, idxs):
    shp = losses.shape[1:]
    if not idxs:
        # no intersection, return a 0-dim matrix
        return numpy.zeros((0,) + shp, losses.dtype)
    # numpy.array wants lists, not sets, hence the sorted below
    return losses[numpy.array(sorted(idxs))].sum(axis=0)


def _filter_agg(assetcol, losses, tags):
    # losses is an array of shape (A, ..., R) with A=#assets, R=#realizations
    idxs = set(range(len(assetcol)))
    tagnames = []
    for tag in tags:
        tagname, tagvalue = tag.split('=', 1)
        if tagvalue == '*':
            tagnames.append(tagname)
        else:
            idxs &= assetcol.aids_by_tag[tag]
    if len(tagnames) > 1:
        raise ValueError('Too many * as tag values in %s' % tagnames)
    elif not tagnames:  # return an array of shape (..., R)
        return _agg(losses, idxs)
    else:  # return an array of shape (T, ..., R)
        all_idxs = (idxs & assetcol.aids_by_tag[t] for t in assetcol.tags()
                    if t.startswith(tagname))
        return numpy.array([_agg(losses, idxs) for idxs in all_idxs])


@extract.add('agglosses')
def extract_agglosses(dstore, loss_type, *tags):
    """
    Aggregate losses of the given loss type and tags. Use it as
    /extract/agglosses/structural?taxonomy=RC&zipcode=20126
    /extract/agglosses/structural?taxonomy=RC&zipcode=*

    :returns:
        an array of shape (R,), being R the number of realizations
        an array of length 0 if there is no data for the given tags
        an array of shape (T, R) if one of the tag names has a `*` value
    """
    if not loss_type:
        raise ValueError('loss_type not passed in agglosses/<loss_type>')
    l = dstore['oqparam'].lti[loss_type]
    if 'losses_by_asset' in dstore:  # scenario_risk
        losses = dstore['losses_by_asset'][:, :, l]['mean']
    elif 'avg_losses-rlzs' in dstore:  # event_based_risk
        losses = dstore['avg_losses-rlzs'][:, :, l]
    else:
        raise KeyError('No losses found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], losses, tags)


@extract.add('aggdamages')
def extract_aggdamages(dstore, loss_type, *tags):
    """
    Aggregate damages of the given loss type and tags. Use it as
    /extract/aggdamages/structural?taxonomy=RC&zipcode=20126

    :returns:
        array of shape (R, D), being R the number of realizations and D
        the number of damage states or array of length 0 if there is no
        data for the given tags
    """
    if 'dmg_by_asset' in dstore:  # scenario_damage
        losses = dstore['dmg_by_asset'][loss_type]['mean']
    else:
        raise KeyError('No damages found in %s' % dstore)
    return _filter_agg(dstore['assetcol'], losses, tags)


@extract.add('aggcurves')
def extract_aggcurves(dstore, loss_type, *tags):
    """
    Aggregate loss curves of the given loss type and tags for
    event based risk calculations. Use it as
    /extract/aggcurves/structural?taxonomy=RC&zipcode=20126

    :returns:
        array of shape (S, P), being P the number of return periods
        and S the number of statistics
    """
    if 'curves-stats' in dstore:  # event_based_risk
        losses = dstore['curves-stats'][loss_type]
    else:
        raise KeyError('No curves found in %s' % dstore)
    curves = _filter_agg(dstore['assetcol'], losses, tags)
    return ArrayWrapper(curves, dstore.get_attrs('curves-stats'))
