# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2023 GEM Foundation
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
import operator
import itertools
import logging
import csv
import os

import numpy
import pandas
from shapely import wkt, geometry

from openquake.baselib import hdf5, general
from openquake.baselib.node import Node, context
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import valid, nrml, geo, InvalidFile
from openquake.risklib import countries

U8 = numpy.uint8
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
TWO16 = 2 ** 16
TWO32 = 2 ** 32
by_taxonomy = operator.attrgetter('taxonomy')
by_lonlat = operator.itemgetter('lon', 'lat')
ae = numpy.testing.assert_equal
OCC_FIELDS = ('occupants_day', 'occupants_night', 'occupants_transit')


def get_case_similar(names):
    """
    :param names: a list of strings
    :returns: list of case similar names, possibly empty

    >>> get_case_similar(['id', 'ID', 'lon', 'lat', 'Lon'])
    [['ID', 'id'], ['Lon', 'lon']]
    """
    dic = general.AccumDict(accum=[])
    for name in names:
        dic[name.lower()].append(name)
    return [sorted(names) for names in dic.values() if len(names) > 1]


def calc_occupants_avg(adf):
    """
    :returns: the average number of occupants, (day+night+transit)/3
    """
    occfields = [col for col in adf.columns if col in OCC_FIELDS]
    occ = adf[occfields[0]].to_numpy().copy()
    for f in occfields[1:]:
        occ += adf[f].to_numpy()
    return occ / len(occfields)


class CostCalculator(object):
    """
    Return the value of an asset for the given loss type depending
    on the cost types declared in the exposure, as follows:

        case 1: cost type: aggregated:
            cost = economic value
        case 2: cost type: per asset:
            cost * number (of assets) = economic value
        case 3: cost type: per area and area type: aggregated:
            cost * area = economic value
        case 4: cost type: per area and area type: per asset:
            cost * area * number = economic value

    The same "formula" applies to retrofitting cost.
    """
    def __init__(self, cost_types, area_types, units, tagi={'taxonomy': 0}):
        if set(cost_types) != set(area_types):
            raise ValueError('cost_types has keys %s, area_types has keys %s'
                             % (sorted(cost_types), sorted(area_types)))
        for ct in cost_types.values():
            assert ct in ('aggregated', 'per_asset', 'per_area'), ct
        for at in area_types.values():
            assert at in ('aggregated', 'per_asset'), at
        self.cost_types = cost_types
        self.area_types = area_types
        self.units = units
        self.tagi = tagi

    def update(self, assetcol):
        for name in assetcol.dtype.names:
            if name.startswith('value-') and not name in (
                    'value-area', 'value-number'):
                assetcol[name] = self(name[6:], assetcol)

    def __call__(self, loss_type, assetcol):
        A = len(assetcol)
        try:
            area = assetcol['value-area']
        except (ValueError, KeyError):
            area = numpy.ones(A)
        try:
            number = assetcol['value-number']
        except (ValueError, KeyError):
            number = numpy.ones(A)
        try:
            cost = assetcol['value-' + loss_type]
        except ValueError:
            return numpy.repeat(numpy.nan, A)
        cost_type = self.cost_types[loss_type]
        if cost_type == "aggregated":
            return cost
        if cost_type == "per_asset":
            return cost * number
        if cost_type == "per_area":
            area_type = self.area_types[loss_type]
            if area_type == "aggregated":
                return cost * area
            elif area_type == "per_asset":
                return cost * area * number
        # this should never happen
        raise RuntimeError('Unable to compute cost')

    def get_units(self, loss_types):
        """
        :param: a list of loss types
        :returns: a string of space-separated units
        """
        lst = []
        for lt in loss_types:
            if lt.endswith('_ins'):
                lt = lt[:-4]
            if lt == 'area':
                unit = 'sqm'
            elif lt == 'number':
                unit = 'dwellings'
            elif lt == 'occupants':
                unit = 'people'
            else:
                unit = self.units[lt]
            lst.append(unit)
        return ' '.join(lst)

    def __toh5__(self):
        loss_types = sorted(self.cost_types)
        dt = numpy.dtype([('cost_type', hdf5.vstr),
                          ('area_type', hdf5.vstr),
                          ('unit', hdf5.vstr)])
        array = numpy.zeros(len(loss_types), dt)
        array['cost_type'] = [self.cost_types[lt] for lt in loss_types]
        array['area_type'] = [self.area_types[lt] for lt in loss_types]
        array['unit'] = [self.units[lt] for lt in loss_types]
        attrs = dict(loss_types=hdf5.array_of_vstr(loss_types))
        return array, attrs

    def __fromh5__(self, array, attrs):
        vars(self).update(attrs)
        self.cost_types = dict(zip(self.loss_types, array['cost_type']))
        self.area_types = dict(zip(self.loss_types, array['area_type']))
        self.units = dict(zip(self.loss_types, decode(array['unit'])))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, vars(self))


costcalculator = CostCalculator(
    cost_types=dict(structural='per_area'),
    area_types=dict(structural='per_asset'),
    units=dict(structural='EUR'))


def build_assets(adf, tagnames):
    """
    :param adf: DataFrame associated to the exposure.csv file
    :param tagnames: tag names (including taxonomy)
    """
    T = len(tagnames)
    STR_FIELDS = ['id', 'taxonomy'] + [
        name for name in tagnames if name not in ('id', 'site_id')]
    F64_FIELDS = ['lon', 'lat', 'ideductible', 'retrofitted',
                  'value-structural', 'value-nonstructural',
                  'value-contents', 'value-business_interruption',
                  'value-area', 'value-number',
                  'occupants_avg', 'occupants_night',
                  'occupants_day', 'occupants_transit']
    dtlist = [('tagidxs', (U32, (T,))), ('site_id', U32)]
    for f in sorted(adf.columns):
        if f in STR_FIELDS:
            dtlist.append((f, object))
        elif f in F64_FIELDS:
            dtlist.append((f, float))
    assets = numpy.zeros(len(adf), dtlist)
    for f, _ in dtlist[2:]:
        assets[f] = adf[f]
    return assets.view(numpy.recarray)


class TagCollection(object):
    """
    An iterable collection of tags in the form "tagname=tagvalue".

    :param tagnames: a list of tagnames starting with 'taxonomy'

    The collection has a couple of attributes for each tagname,
    starting with .taxonomy (a list of taxonomies) and .taxonomy_idx
    (a dictionary taxonomy -> integer index).
    """
    def __init__(self, tagnames):
        assert tagnames[0] == 'taxonomy', tagnames
        assert len(tagnames) == len(set(tagnames)), (
            'The tagnames %s contain duplicates' % tagnames)
        self.tagnames = []
        for tagname in tagnames:
            self.add_tagname(tagname)

    def add_tagname(self, tagname):
        self.tagnames.append(tagname)
        setattr(self, tagname + '_idx', {'?': 0})
        setattr(self, tagname, ['?'])

    def get_tagi(self, tagname, assets):
        """
        :param tagname: name of a tag
        :param assets: composite array of assets with string-valued tags
        :returns: indices associated to the tag, from 1 to num_tags
        """
        uniq, inv = numpy.unique(assets[tagname], return_inverse=True)
        dic = {u: i for i, u in enumerate(uniq, 1)}
        getattr(self, tagname + '_idx').update(dic)
        getattr(self, tagname).extend(uniq)
        return inv + 1

    def get_tag(self, tagname, tagidx):
        """
        :returns: the tag associated to the given tagname and tag index
        """
        return '%s=%s' % (tagname, decode(getattr(self, tagname)[tagidx]))

    def get_tagvalues(self, tagnames, tagidxs):
        """
        :returns: the tag associated to the given tagname and tag index
        """
        values = tuple(getattr(self, tagname)[tagidx + 1]
                       for tagidx, tagname in zip(tagidxs, tagnames))
        return values

    def get_aggkey(self, alltagnames, max_aggregations):
        """
        :param alltagnames: array of (Ag, T) tag names
        :returns: a dictionary tuple of indices -> tagvalues
        """
        aggkey = {}
        if not alltagnames:
            return aggkey
        for ag, tagnames in enumerate(alltagnames):
            alltags = [getattr(self, tagname) for tagname in tagnames]
            ranges = [range(1, len(tags)) for tags in alltags]
            for idxs in itertools.product(*ranges):
                aggkey[ag, idxs] = tuple(
                    tags[idx] for idx, tags in zip(idxs, alltags))
            if len(aggkey) >= TWO16:
                logging.warning('Performing {:_d} aggregations!'.
                                format(len(aggkey)))
            if len(aggkey) >= max_aggregations:
                # forbid too many aggregations
                raise ValueError(
                    'Too many aggregation tags: %d >= max_aggregations=%d' %
                    (len(aggkey), max_aggregations))
        return aggkey

    def gen_tags(self, tagname):
        """
        :yields: the tags associated to the given tagname
        """
        for tagvalue in getattr(self, tagname):
            yield '%s=%s' % (tagname, decode(tagvalue))

    def agg_shape(self, aggregate_by=None, *shp):
        """
        :returns: a shape shp + (T, ...) depending on the tagnames
        """
        if aggregate_by is None:
            aggregate_by = self.tagnames
        return shp + tuple(
            len(getattr(self, tagname)) - 1 for tagname in aggregate_by)

    def __toh5__(self):
        dic = {}
        sizes = []
        for tagname in self.tagnames:
            dic[tagname] = numpy.array(getattr(self, tagname))
            sizes.append(len(dic[tagname]))
        return dic, {'tagnames': numpy.array(self.tagnames, hdf5.vstr),
                     'tagsizes': sizes}

    def __fromh5__(self, dic, attrs):
        self.tagnames = [decode(name) for name in attrs['tagnames']]
        sizes = []
        for tagname in dic:
            setattr(self, tagname, decode(dic[tagname][()]))
            sizes.append(len(dic[tagname]))
        # sanity check to protect against /home/michele/oqdata/calc_10826.hdf5
        numpy.testing.assert_equal(sorted(sizes), sorted(attrs['tagsizes']))

    def __iter__(self):
        tags = []
        for tagname in self.tagnames:
            for tagvalue in getattr(self, tagname):
                tags.append('%s=%s' % (tagname, tagvalue))
        return iter(sorted(tags))

    def __len__(self):
        return sum(len(getattr(self, tagname)) for tagname in self.tagnames)


def tagset(aggregate_by):
    """
    :returns: set of unique tags in aggregate_by
    """
    s = set()
    for aggby in aggregate_by:
        s.update(aggby)
    return s


class AssetCollection(object):
    def __init__(self, exposure, sitecol, array, occupancy_periods,
                 time_event, aggregate_by):
        self.tagcol = exposure.tagcol
        self.time_event = time_event
        self.tot_sites = len(sitecol.complete)
        self.array = array
        self.occupancy_periods = occupancy_periods
        self.update_tagcol(aggregate_by)
        exp_periods = exposure.occupancy_periods
        if self.occupancy_periods and not exp_periods:
            logging.warning('Missing <occupancyPeriods>%s</occupancyPeriods> '
                            'in the exposure', self.occupancy_periods)
        elif self.occupancy_periods.strip() != exp_periods.strip():
            raise ValueError('Expected %s, got %s' %
                             (exp_periods, self.occupancy_periods))
        self.fields = [f[6:] for f in self.array.dtype.names
                       if f.startswith('value-')]
        self.occfields = [f for f in self.array.dtype.names
                          if f.startswith('occupants')]

    def update_tagcol(self, aggregate_by):
        """
        Possibly adds tags 'id' and 'site_id'
        """
        self.aggregate_by = aggregate_by
        ts = tagset(aggregate_by)
        if 'id' in ts and not hasattr(self.tagcol, 'id'):
            self.tagcol.add_tagname('id')
            self.tagcol.id.extend(self['id'])
        if 'site_id' in ts and not hasattr(self.tagcol, 'site_id'):
            self.tagcol.add_tagname('site_id')
            self.tagcol.site_id.extend(range(self.tot_sites))

    @property
    def tagnames(self):
        """
        :returns: the tagnames
        """
        return self.tagcol.tagnames

    def num_taxonomies_by_site(self):
        """
        :returns: an array with the number of assets per each site
        """
        dic = general.group_array(self.array, 'site_id')
        num_taxonomies = numpy.zeros(self.tot_sites, U32)
        for sid, arr in dic.items():
            num_taxonomies[sid] = len(numpy.unique(arr['taxonomy']))
        return num_taxonomies

    def get_aids_by_tag(self):
        """
        :returns: dict tag -> asset ordinals
        """
        aids_by_tag = general.AccumDict(accum=set())
        for aid, ass in enumerate(self):
            for tagname in self.tagnames:
                tag = self.tagcol.get_tag(tagname, ass[tagname])
                aids_by_tag[tag].add(aid)
        return aids_by_tag

    @property
    def taxonomies(self):
        """
        Return a list of taxonomies, one per asset (with duplicates)
        """
        return self.array['taxonomy']

    def assets_by_site(self):
        """
        :returns: numpy array of lists with the assets by each site
        """
        assets_by_site = [[] for sid in range(self.tot_sites)]
        for i, ass in enumerate(self.array):
            assets_by_site[ass['site_id']].append(self[i])
        return numpy.array(assets_by_site, dtype=object)

    # used in the extract API
    def aggregateby(self, tagnames, array):
        """
        :param tagnames: a list of valid tag names
        :param array: an array with the same length as the asset collection
        :returns: an array of aggregate values with the proper shape
        """
        missing = set(tagnames) - set(self.tagcol.tagnames)
        if missing:
            raise ValueError('Unknown tagname(s) %s' % missing)
        A, *shp = array.shape
        if A != len(self):
            raise ValueError('The array must have length %d, got %d' %
                             (len(self), A))
        if not tagnames:
            return array.sum(axis=0)
        elif len(tagnames) == 1:
            # fast track for single-tag aggregation
            # for the Canada exposure it is 30x faster
            # fast_agg(assets['taxonomy'], values)  => 47.6 ms
            # fast_agg2(assets[['taxonomy']], values) => 1.4 s
            [tagname] = tagnames
            avalues = general.fast_agg(self.array[tagname], array)[1:]
            tagids = [(i + 1,) for i in range(len(avalues))]
        else:  # multi-tag aggregation
            tagids, avalues = general.fast_agg2(self.array[tagnames], array)
        shape = [len(getattr(self.tagcol, tagname))-1 for tagname in tagnames]
        arr = numpy.zeros(shape, (F32, tuple(shp)) if shp else F32)
        for tagid, aval in zip(tagids, avalues):
            arr[tuple(i - 1 for i in tagid)] = aval
        return arr

    def arr_value(self, loss_types):
        """
        :param loss_types: the relevant loss types
        :returns: an array of shape (A, L) with the values of the assets
        """
        array = self.array
        aval = numpy.zeros((len(self), len(loss_types)), F32)  # (A, L)
        for lti, lt in enumerate(loss_types):
            if lt.endswith('_ins'):
                aval[array['ordinal'], lti] = array['value-' + lt[:-4]]
            elif lt in self.fields:
                aval[array['ordinal'], lti] = array['value-' + lt]
        return aval

    def get_value_fields(self):
        """
        :returns: list of fields starting with value-
        """
        return [f for f in self.array.dtype.names if f.startswith('value-')]

    def get_agg_values(self, aggregate_by, max_aggregations):
        """
        :param aggregate_by:
            a list of Ag lists of tag names
        :returns:
            a structured array of length K+1 with the value fields
        """
        allnames = tagset(aggregate_by)
        aggkey = {key: k for k, key in enumerate(
            self.tagcol.get_aggkey(aggregate_by, max_aggregations))}
        K = len(aggkey)
        dic = {tagname: self[tagname] for tagname in allnames}
        for field in self.fields:
            dic[field] = self['value-' + field]
        for field in self.occfields:
            dic[field] = self[field]
        vfields = self.fields + self.occfields
        value_dt = [(f, F32) for f in vfields]
        agg_values = numpy.zeros(K+1, value_dt)
        dataf = pandas.DataFrame(dic)
        for ag, tagnames in enumerate(aggregate_by):
            df = dataf.set_index(tagnames)
            if tagnames == ['id']:
                df.index = self['ordinal'] + 1
            elif tagnames == ['site_id']:
                df.index = self['site_id'] + 1
            for key, grp in df.groupby(df.index):
                if isinstance(key, int):
                    key = key,  # turn it into a 1-value tuple
                agg_values[aggkey[ag, key]] = tuple(grp[vfields].sum())
        if self.fields:  # missing in scenario_damage case_8
            agg_values[K] = tuple(dataf[vfields].sum())
        return agg_values

    def build_aggids(self, aggregate_by, max_aggregations):
        """
        :param aggregate_by: list of Ag lists of strings
        :returns: (array of (Ag, A) integers, list of K strings)
        """
        aggkey = self.tagcol.get_aggkey(aggregate_by, max_aggregations)
        aggids = numpy.zeros((len(aggregate_by), len(self)), U32)
        key2i = {key: i for i, key in enumerate(aggkey)}
        for ag, aggby in enumerate(aggregate_by):
            if aggby == ['id']:
                aggids[ag] = self['ordinal']
            elif aggby == ['site_id']:
                aggids[ag] = self['site_id']
            else:
                aggids[ag] = [key2i[ag, tuple(t)] for t in self[aggby]]
        return aggids, [decode(vals) for vals in aggkey.values()]

    def reduce(self, sitecol):
        """
        :returns: a reduced AssetCollection on the given sitecol
        """
        ok_indices = numpy.sum(
            [self.array['site_id'] == sid for sid in sitecol.sids],
            axis=0, dtype=bool)
        new = object.__new__(self.__class__)
        vars(new).update(vars(self))
        new.array = self.array[ok_indices]
        new.array['ordinal'] = numpy.arange(len(new.array))
        return new

    def reduce_also(self, sitecol):
        """
        Reduced self on the given sitecol.
        NB: also the SiteCollection is reduced
        and turned into a complete site collection.
        """
        uniq, inv = numpy.unique(self['site_id'], return_inverse=True)
        if len(uniq) == len(sitecol) and (uniq == sitecol.sids).all():
            # do not reduce the assetcol, just fix the site IDs
            self.array['site_id'] = numpy.arange(len(uniq))[inv]
        else:  # the sitecol is shorter, like in case_shakemap
            arrays = []
            for idx, sid in enumerate(sitecol.sids):
                arr = self[self['site_id'] == sid]
                arr['site_id'] = idx
                arrays.append(arr)
            self.array = numpy.concatenate(arrays)
            self.array['ordinal'] = numpy.arange(len(self.array))
            self.tot_sites = len(sitecol)
        sitecol.make_complete()

    def to_dframe(self, indexfield='ordinal'):
        """
        :returns: the associated DataFrame
        """
        dic = {name: self.array[name] for name in self.array.dtype.names}
        dic['id'] = decode(dic['id'])
        return pandas.DataFrame(dic, dic[indexfield])

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, aid):
        return self.array[aid]

    def __len__(self):
        return len(self.array)

    def __toh5__(self):
        # NB: the loss types do not contain spaces, so we can store them
        # together as a single space-separated string
        op = decode(self.occupancy_periods)
        attrs = {'time_event': self.time_event,
                 'occupancy_periods': op,
                 'tot_sites': self.tot_sites,
                 'fields': ' '.join(self.fields),
                 'occfields': ' '.join(self.occfields),
                 'tagnames': encode(self.tagnames),
                 'nbytes': self.array.nbytes}
        return dict(array=self.array, tagcol=self.tagcol), attrs

    def __fromh5__(self, dic, attrs):
        self.occupancy_periods = attrs['occupancy_periods']
        self.time_event = attrs['time_event']
        self.tot_sites = attrs['tot_sites']
        self.fields = attrs['fields'].split()
        self.occfields = attrs['occfields'].split()
        self.nbytes = attrs['nbytes']
        self.array = dic['array'][()]
        self.tagcol = dic['tagcol']

    def __repr__(self):
        return '<%s with %d asset(s)>' % (self.__class__.__name__, len(self))


def build_asset_array(tagcol, calc, sids, assets, area, tagnames=()):
    """
    :param assets_by_site: a list of assets
    :param area: True if there is an area field in the exposure
    :param tagnames: a list of tag names
    :returns: an array `assetcol`
    """
    loss_types = []
    occupancy_periods = []
    for name in assets.dtype.names:
        if name.startswith('occupants_'):
            period = name.split('_', 1)[1]
            # see scenario_risk test_case_2d
            if period != 'avg':
                occupancy_periods.append(period)
            loss_types.append(name)
        elif name.startswith('value-'):
            loss_types.append(name)
    # loss_types can be ['value-business_interruption', 'value-contents',
    # 'value-nonstructural', 'occupants_avg', 'occupants_day',
    # 'occupants_night', 'occupants_transit']
    retro = ['retrofitted'] if 'retrofitted' in assets.dtype.names else []
    float_fields = loss_types + ['ideductible'] + retro
    int_fields = [(str(name), U32) for name in tagnames
                  if name not in ('id', 'site_id')]
    tagi = {str(name): i for i, name in enumerate(tagnames)}
    asset_dt = numpy.dtype(
        [('id', (numpy.string_, valid.ASSET_ID_LENGTH)),
         ('ordinal', U32), ('lon', F32), ('lat', F32),
         ('site_id', U32)] + [
             (str(name), F32) for name in float_fields] + int_fields)
    num_assets = len(assets)
    assetcol = numpy.zeros(num_assets, asset_dt)
    fields = set(asset_dt.fields) - {'ordinal'}
    for field in fields:
        if field in tagnames:
            assetcol[field] = tagcol.get_tagi(field, assets)
        elif field in assets.dtype.names:
            assetcol[field] = assets[field]
    calc.update(assetcol)
    assetcol['ordinal'] = numpy.arange(num_assets)
    return assetcol, ' '.join(occupancy_periods)


# ########################### exposure ############################ #

cost_type_dt = numpy.dtype([('name', hdf5.vstr),
                            ('type', hdf5.vstr),
                            ('unit', hdf5.vstr)])


def _get_exposure(fname, stop=None):
    """
    :param fname:
        path of the XML file containing the exposure
    :param stop:
        node at which to stop parsing (or None)
    :returns:
        a pair (Exposure instance, list of asset nodes)
    """
    [exposure] = nrml.read(fname, stop=stop)
    if not exposure.tag.endswith('exposureModel'):
        raise InvalidFile('%s: expected exposureModel, got %s' %
                          (fname, exposure.tag))
    description = exposure.description
    try:
        conversions = exposure.conversions
    except AttributeError:
        conversions = Node('conversions', nodes=[Node('costTypes', [])])
    fieldmap = {}  # input_field -> oq_field
    try:
        for node in exposure.exposureFields:
            fieldmap[node['input']] = node['oq']
    except AttributeError:
        pass  # no fieldmap
    try:
        area = conversions.area
    except AttributeError:
        # NB: the area type cannot be an empty string because when sending
        # around the CostCalculator object we would run into this numpy bug
        # about pickling dictionaries with empty strings:
        # https://github.com/numpy/numpy/pull/5475
        area = Node('area', dict(type='?'))
    else:
        logging.warning('The <area> conversion in the exposure is deprecated '
                        'and will be removed in future versions of the engine')
    try:
        occupancy_periods = exposure.occupancyPeriods.text or ''
    except AttributeError:
        occupancy_periods = ''
    try:
        tagNames = exposure.tagNames
    except AttributeError:
        tagNames = Node('tagNames', text='')
    tagnames = ~tagNames or []
    if set(tagnames) & {'taxonomy', 'exposure', 'country'}:
        raise InvalidFile('taxonomy, exposure and country are reserved names '
                          'you cannot use it in <tagNames>: %s' % fname)
    tagnames.insert(0, 'taxonomy')

    # read the cost types and make some check
    cost_types = []
    retrofitted = False
    for ct in conversions.costTypes:
        with context(fname, ct):
            ctname = ct['name']
            if ctname == 'structural' and 'retrofittedType' in ct.attrib:
                if ct['retrofittedType'] != ct['type']:
                    raise ValueError(
                        'The retrofittedType %s is different from the type'
                        '%s' % (ct['retrofittedType'], ct['type']))
                if ct['retrofittedUnit'] != ct['unit']:
                    raise ValueError(
                        'The retrofittedUnit %s is different from the unit'
                        '%s' % (ct['retrofittedUnit'], ct['unit']))
                retrofitted = True
            cost_types.append(
                (ctname, valid.cost_type_type(ct['type']), ct['unit']))
    if 'occupants' in cost_types:
        cost_types.append(('occupants', 'per_area', 'people'))
    cost_types.sort(key=operator.itemgetter(0))
    cost_types = numpy.array(cost_types, cost_type_dt)
    cc = CostCalculator(
        {}, {}, {}, {name: i for i, name in enumerate(tagnames)})
    for ct in cost_types:
        name = ct['name']  # structural, nonstructural, ...
        cc.cost_types[name] = ct['type']  # aggregated, per_asset, per_area
        cc.area_types[name] = area['type']
        cc.units[name] = ct['unit']
    exp = Exposure(
        exposure['id'], exposure['category'],
        description.text, cost_types, occupancy_periods, retrofitted,
        area.attrib, [], cc, TagCollection(tagnames), fieldmap)
    assets_text = exposure.assets.text.strip()
    if assets_text:
        # the <assets> tag contains a list of file names
        dirname = os.path.dirname(fname)
        exp.datafiles = [os.path.join(dirname, f) for f in assets_text.split()]
    else:
        exp.datafiles = []
    return exp, exposure.assets


def _minimal_tagcol(fnames, by_country):
    tagnames = None
    for exp in Exposure.read_headers(fnames):
        if tagnames is None:
            tagnames = set(exp.tagcol.tagnames)
        else:
            tagnames &= set(exp.tagcol.tagnames)
    tagnames -= set(['taxonomy'])
    if len(fnames) > 1:
        alltags = ['taxonomy'] + list(tagnames) + [
            'country' if by_country else 'exposure']
    else:
        alltags = ['taxonomy'] + list(tagnames)
    return TagCollection(alltags)


def assets2df(asset_nodes, fields, retrofitted, ignore_missing_costs):
    """
    :returns: a DataFrame of assets from the asset nodes
    """
    first_asset = asset_nodes[0]
    for occ in getattr(first_asset, 'occupancies', []):
        name = 'occupants_' + occ['period'].lower()
        if name not in fields:
            fields.append(name)
    dtlist = [(f, object) for f in fields]
    if retrofitted:
        dtlist.append(('retrofitted', object))
    nodes = list(asset_nodes)
    array = numpy.zeros(len(nodes), dtlist)
    for asset, rec in zip(nodes, array):
        # fix asset.attrib
        for occ in getattr(asset, 'occupancies', []):
            ofield = 'occupants_' + occ['period'].lower()
            asset.attrib[ofield] = occ['occupants']
        for cost in getattr(asset, 'costs', []):
            asset.attrib[cost['type']] = cost['value']
            if retrofitted and 'retrofitted' in cost.attrib:
                rec['retrofitted'] = float(cost['retrofitted'])
        if hasattr(asset, 'tags'):
            asset.attrib.update(asset.tags.attrib)

        # set record
        for field in fields:
            if field == 'lon':
                rec[field] = asset.location['lon']
            elif field == 'lat':
                rec[field] = asset.location['lat']
            elif field == 'value-area':
                rec[field] = float(asset.attrib.get('area', 1))
            elif field == 'value-number':
                rec[field] = float(asset.attrib.get('number', 1))
            elif field.startswith('value-'):
                cost = field[6:]
                try:
                    rec[field] = asset[cost]
                except KeyError:
                    if cost not in ignore_missing_costs:
                        raise
            else:
                rec[field] = asset.attrib.get(field, '?')
    return pandas.DataFrame({f: array[f] for f, dt in dtlist}).set_index('id')


class Exposure(object):
    """
    A class to read the exposure from XML/CSV files
    """
    fields = ['id', 'category', 'description', 'cost_types',
              'occupancy_periods', 'retrofitted',
              'area', 'assets', 'cost_calculator', 'tagcol', 'fieldmap']

    @staticmethod
    def check(fname):
        exp = Exposure.read([fname])
        err = []
        for asset in exp.assets:
            if asset.number > 65535:
                err.append('Asset %s has number %s > 65535' %
                           (asset.asset_id, asset.number))
        return '\n'.join(err)

    @staticmethod
    def read(fnames, calculation_mode='', region_constraint='',
             ignore_missing_costs=(), check_dupl=True,
             tagcol=None, by_country=False, errors=None):
        """
        Call `Exposure.read(fnames)` to get an :class:`Exposure` instance
        keeping all the assets in memory.
        """
        if by_country:  # E??_ -> countrycode
            prefix2cc = countries.from_exposures(
                os.path.basename(f) for f in fnames)
        else:
            prefix = ''
        allargs = []
        tagcol = _minimal_tagcol(fnames, by_country)
        for i, fname in enumerate(fnames, 1):
            if len(fnames) > 1:
                # multiple exposure.xml files, add a prefix
                # this is tested in oq-risk-tests/old_hazard
                if by_country:
                    prefix = prefix2cc['E%02d_' % i] + '_'
                else:
                    prefix = 'E%02d_' % i
            else:
                prefix = ''
            allargs.append((fname, calculation_mode, region_constraint,
                            ignore_missing_costs, check_dupl, by_country,
                            prefix, tagcol, errors))
        exp = None
        all_assets = []
        for exposure in itertools.starmap(Exposure.read_exp, allargs):
            all_assets.append(exposure.assets)
            if exp is None:  # first time
                exp = exposure
                exp.description = 'Composite exposure[%d]' % len(fnames)
            else:
                ae(exposure.cost_types, exp.cost_types)
                ae(exposure.occupancy_periods, exp.occupancy_periods)
                ae(exposure.retrofitted, exp.retrofitted)
                ae(exposure.area, exp.area)
        exp.exposures = [os.path.splitext(os.path.basename(f))[0]
                         for f in fnames]
        exp.assets = numpy.concatenate(all_assets)
        return exp

    @staticmethod
    def read_exp(fname, calculation_mode='', region_constraint='',
                 ignore_missing_costs=(), check_dupl=True, by_country=False,
                 asset_prefix='', tagcol=None, errors=None, monitor=None):
        logging.info('Reading %s', fname)
        param = {'calculation_mode': calculation_mode}
        param['asset_prefix'] = asset_prefix
        if region_constraint:
            param['region'] = wkt.loads(region_constraint)
        else:
            param['region'] = None
        param['ignore_missing_costs'] = set(ignore_missing_costs)
        exposure, assetnodes = _get_exposure(fname)
        if tagcol:
            exposure.tagcol = tagcol
        if calculation_mode == 'classical_bcr':
            exposure.retrofitted = True
        if assetnodes:
            df = assets2df(
                assetnodes, exposure._csv_header(),
                exposure.retrofitted, ignore_missing_costs)
            fname_dfs = [(fname, df)]
        else:
            fname_dfs = exposure._read_csv(errors)
        param['relevant_cost_types'] = set(exposure.cost_types['name']) - {
            'occupants'}
        all_assets = []
        asset_refs = set()
        # loop on each CSV file associated to exposure.xml
        for fname, df in fname_dfs:
            if len(df) == 0:
                raise InvalidFile('%s is empty' % fname)
            elif by_country:
                df['country'] = asset_prefix[:-1]
            elif asset_prefix:  # multiple exposure files
                df['exposure'] = asset_prefix[:-1]

            param['fname'] = fname
            names = df.columns
            param['area'] = 'area' in names
            occupants = any(n.startswith('occupants_') for n in names)
            if occupants and 'calc_occupants_avg' not in names:
                df['occupants_avg'] = calc_occupants_avg(df)
            if exposure.retrofitted:
                df['retrofitted'] = exposure.cost_calculator(
                    'structural', {'value-structural':df.retrofitted,
                                   'value-number': df['value-number']})
            assets = build_assets(df.reset_index(), tagcol.tagnames)
            assets = exposure._populate_from(
                assets, param, check_dupl, asset_refs)
            all_assets.append(assets)

        if not asset_refs:
            raise RuntimeError('Could not find any asset within the region!')

        exposure.assets = numpy.concatenate(all_assets, dtype=assets.dtype)
        exposure.param = param
        return exposure

    @staticmethod
    def read_headers(fnames):
        """
        :param fname: path to an exposure file in XML format
        :returns: an Exposure object without assets
        """
        return [_get_exposure(fname, stop='asset')[0] for fname in fnames]

    def __init__(self, *values):
        assert len(values) == len(self.fields)
        for field, value in zip(self.fields, values):
            setattr(self, field, value)

    def _csv_header(self, value='value-', occupants='occupants_'):
        """
        Extract the expected CSV header from the exposure metadata
        """
        fields = ['id', value + 'number', 'taxonomy', 'lon', 'lat']
        for name in self.cost_types['name']:
            fields.append(value + name)
        if 'per_area' in self.cost_types['type']:
            fields.append(value + 'area')
        for op in self.occupancy_periods.split():
            fields.append(occupants + op)
        fields.extend(self.tagcol.tagnames)
        wrong = get_case_similar(set(fields))
        if wrong:
            raise InvalidFile('Found case-duplicated fields %s in %s' %
                              (wrong, self.datafiles))
        return sorted(set(fields))

    def _read_csv(self, errors=None):
        """
        :yields: asset nodes
        """
        expected_header = set(self._csv_header('', ''))
        floatfields = set()
        strfields = self.tagcol.tagnames + self.occupancy_periods.split()
        for fname in self.datafiles:
            with open(fname, encoding='utf-8-sig', errors=errors) as f:
                try:
                    fields = next(csv.reader(f))
                except UnicodeDecodeError:
                    msg = ("%s is not encoded as UTF-8\ntry oq shell "
                           "and then o.fix_latin1('%s')\nor set "
                           "ignore_encoding_errors=true" % (fname, fname))
                    raise RuntimeError(msg)
                header = set(self.fieldmap.get(f, f) for f in fields)
                for field in fields:
                    if field not in strfields:
                        floatfields.add(field)
                missing = expected_header - header - {'exposure', 'country'}
                if len(header) < len(fields):
                    raise InvalidFile(
                        '%s: The header %s contains a duplicated field' %
                        (fname, header))
                elif missing:
                    raise InvalidFile('%s: missing %s' % (fname, missing))
        conv = {'lon': float, 'lat': float, 'number': float, 'area': float,
                'retrofitted': float, 'ideductible': float, None: object}
        for f in strfields:
            conv[f] = str
        revmap = {}  # oq -> inp
        for inp, oq in self.fieldmap.items():
            revmap[oq] = inp
            if oq in conv:
                conv[inp] = conv[oq]
        rename = self.fieldmap.copy()
        for field in set(self.cost_types['name']) | {'area', 'number'}:
            f = revmap.get(field, field)
            conv[f] = float
            rename[f] = 'value-' + field
        for field in self.occupancy_periods.split():
            f = revmap.get(field, field)
            conv[f] = float
            rename[f] = 'occupants_' + field
        for fname in self.datafiles:
            df = hdf5.read_csv(fname, conv, rename, errors=errors, index='id')
            df['lon'] = numpy.round(df.lon, 5)
            df['lat'] = numpy.round(df.lat, 5)
            sa = float(os.environ.get('OQ_SAMPLE_ASSETS', 0))
            if sa:
                df = general.random_filter(df, sa)
            yield fname, df

    def _populate_from(self, assets, param, check_dupl, asset_refs):
        logging.info('Read {:_d} assets in {}'.format(
            len(assets), param['fname']))
        out_of_region = []
        for idx, asset in enumerate(assets):
            asset_id = param['asset_prefix'] + asset['id']
            asset['id'] = asset_id
            # check_dupl is False only in oq prepare_site_model since
            # in that case we are only interested in the asset locations
            if check_dupl and asset_id in asset_refs:
                raise nrml.DuplicatedID('asset_id=%s while processing %s' % (
                    asset_id, param['fname']))
            asset_refs.add(asset_id)
            location = asset['lon'], asset['lat']
            if param['region'] and not geometry.Point(*location).within(
                    param['region']):
                out_of_region.append(idx)
        if out_of_region:
            if len(out_of_region) == len(assets):                
                raise RuntimeError('Could not find any asset within the region')
            logging.info('Discarded %d assets outside the region',
                         len(out_of_region))
            out = numpy.isin(numpy.arange(len(assets)), out_of_region)
            return assets[~out]
        return assets

    def get_mesh_assets_by_site(self):
        """
        :returns: (Mesh instance, assets_by_site list)
        """
        assets_by_loc = general.groupby(self, key=by_lonlat)
        mesh = geo.Mesh.from_coords(list(assets_by_loc))
        assets_by_site = [
            assets_by_loc[lonlat] for lonlat in zip(mesh.lons, mesh.lats)]
        return mesh, assets_by_site

    def __iter__(self):
        return iter(self.assets)

    def __repr__(self):
        return '<%s with %s assets>' % (self.__class__.__name__,
                                        len(self.assets))
