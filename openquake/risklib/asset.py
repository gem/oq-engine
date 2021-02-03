# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2021 GEM Foundation
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
ae = numpy.testing.assert_equal


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

    def __call__(self, loss_type, values, area, number):
        cost = values.get(loss_type)
        if cost is None:
            return numpy.nan
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
        :returns: an array of units as byte strings, suitable for HDF5
        """
        lst = []
        for lt in loss_types:
            if lt.endswith('_ins'):
                lt = lt[:-4]
            if lt == 'occupants':
                unit = 'people'
            else:
                unit = self.units[lt]
            lst.append(unit)
        return lst

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
        self.units = dict(zip(self.loss_types, array['unit']))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, vars(self))


costcalculator = CostCalculator(
    cost_types=dict(structural='per_area'),
    area_types=dict(structural='per_asset'),
    units=dict(structural='EUR'))


class Asset(object):
    """
    Describe an Asset as a collection of several values. A value can
    represent a replacement cost (e.g. structural cost, business
    interruption cost) or another quantity that can be considered for
    a risk analysis (e.g. occupants).
    """
    def __init__(self,
                 asset_id,
                 ordinal,
                 tagidxs,
                 number,
                 location,
                 values,
                 area=1,
                 retrofitted=None,
                 calc=costcalculator):
        """
        :param asset_id:
            a short string identifier
        :param ordinal:
            an integer identifier for the asset, used to order them
        :param tagidxs:
            a list of indices for the taxonomy and other tags
        :param number:
            number of apartments of number of people in the given asset
        :param location:
            geographic location of the asset
        :param dict values:
            asset values keyed by loss types
        :param retrofitted:
            asset retrofitted value
        :param calc:
            cost calculator instance
        :param ordinal:
            asset collection ordinal
        """
        self.asset_id = asset_id
        self.ordinal = ordinal
        self.tagidxs = tagidxs
        self.number = number
        self.location = location
        self.values = values
        self.area = area
        self._retrofitted = retrofitted
        self.calc = calc

    def value(self, loss_type, time_event=None):
        """
        :returns: the total asset value for `loss_type`
        """
        if loss_type == 'occupants':
            return (self.values['occupants_' + str(time_event)]
                    if time_event else self.values['occupants'])
        return self.calc(loss_type, self.values, self.area, self.number)

    def retrofitted(self):
        """
        :returns: the asset retrofitted value
        """
        return self.calc('structural', {'structural': self._retrofitted},
                         self.area, self.number)

    def __repr__(self):
        return '<Asset #%s>' % self.ordinal


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

    def get_tagidx(self, tagname):
        """
        :returns: a dictionary tag string -> tag index
        """
        return {tag: idx for idx, tag in enumerate(getattr(self, tagname))}

    def add_tagname(self, tagname):
        self.tagnames.append(tagname)
        setattr(self, tagname + '_idx', {'?': 0})
        setattr(self, tagname, ['?'])

    def add(self, tagname, tagvalue):
        """
        :returns: numeric index associated to the tag
        """
        dic = getattr(self, tagname + '_idx')
        try:
            return dic[tagvalue]
        except KeyError:
            dic[tagvalue] = idx = len(dic)
            getattr(self, tagname).append(tagvalue)
            if idx > TWO32:
                raise InvalidFile('contains more then %d tags' % TWO32)
            return idx

    def add_tags(self, dic, prefix):
        """
        :param dic: a dictionary tagname -> tagvalue
        :returns: a list of tag indices, one per tagname
        """
        # fill missing tagvalues with "?", raise an error for unknown tagnames
        idxs = []
        for tagname in self.tagnames:
            if tagname in ('exposure', 'country'):
                idxs.append(self.add(tagname, prefix))
                continue
            try:
                tagvalue = dic.pop(tagname)
            except KeyError:
                tagvalue = '?'
            else:
                if tagvalue in '?*':
                    raise ValueError(
                        'Invalid tagvalue="%s"' % tagvalue)
            idxs.append(self.add(tagname, tagvalue))
        if dic:
            raise ValueError(
                'Unknown tagname %s or <tagNames> not '
                'specified in the exposure' % ', '.join(dic))
        return idxs

    def extend(self, other):
        for tagname in other.tagnames:
            for tagvalue in getattr(other, tagname):
                self.add(tagname, tagvalue)

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

    def get_tagdict(self, tagidxs):
        """
        :returns: dictionary {tagname: tag}
        """
        return {tagname: getattr(self, tagname)[tagidx]
                for tagidx, tagname in zip(tagidxs, self.tagnames)}

    def get_aggkey(self, tagnames):
        """
        :returns: a dictionary tuple of indices -> tagvalues
        """
        aggkey = {}
        if not tagnames:
            return aggkey
        alltags = [getattr(self, tagname) for tagname in tagnames]
        ranges = [range(1, len(tags)) for tags in alltags]
        for i, idxs in enumerate(itertools.product(*ranges)):
            aggkey[idxs] = tuple(tags[idx] for idx, tags in zip(idxs, alltags))
        if len(aggkey) >= TWO32:
            raise ValueError('Too many aggregation tags: %d >= %d' %
                             (len(aggkey), TWO32))
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
            setattr(self, tagname, dic[tagname][()])
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


class AssetCollection(object):
    def __init__(self, exposure, assets_by_site, time_event, aggregate_by):
        self.tagcol = exposure.tagcol
        if 'site_id' in aggregate_by:
            self.tagcol.add_tagname('site_id')
            self.tagcol.site_id.extend(range(len(assets_by_site)))
        self.time_event = time_event
        self.aggregate_by = aggregate_by
        self.tot_sites = len(assets_by_site)
        self.array, self.occupancy_periods = build_asset_array(
            assets_by_site, exposure.tagcol.tagnames, time_event)
        if 'id' in aggregate_by:
            self.tagcol.add_tagname('id')
            self.tagcol.id.extend(self['id'])
        exp_periods = exposure.occupancy_periods
        if self.occupancy_periods and not exp_periods:
            logging.warning('Missing <occupancyPeriods>%s</occupancyPeriods> '
                            'in the exposure', self.occupancy_periods)
        elif self.occupancy_periods.strip() != exp_periods.strip():
            raise ValueError('Expected %s, got %s' %
                             (exp_periods, self.occupancy_periods))
        self.fields = [f[6:] for f in self.array.dtype.names
                       if f.startswith('value-')]

    @property
    def tagnames(self):
        """
        :returns: the tagnames
        """
        return self.tagcol.tagnames

    @property
    def asset_refs(self):
        """
        :returns: array of asset ids as strings
        """
        return self.array['id']

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
        return numpy.array(assets_by_site)

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

    def get_agg_values(self, loss_names, tagnames):
        """
        :param loss_names:
            the relevant loss_names
        :param tagnames:
            tagnames
        :returns:
            an array of shape (K+1, L)
        """
        aggkey = {key: k for k, key in enumerate(
            self.tagcol.get_aggkey(tagnames))}
        K, L = len(aggkey), len(loss_names)
        dic = {tagname: self[tagname] for tagname in tagnames}
        for ln in loss_names:
            if ln.endswith('_ins'):
                dic[ln] = self['value-' + ln[:-4]]
            elif ln in self.fields:
                dic[ln] = self['value-' + ln]
        agg_values = numpy.zeros((K+1, L))
        df = pandas.DataFrame(dic)
        if tagnames:
            df = df.set_index(list(tagnames))
            if tagnames == ['id']:
                df.index = self['ordinal'] + 1
            elif tagnames == ['site_id']:
                df.index = self['site_id'] + 1
            for key, grp in df.groupby(df.index):
                if isinstance(key, int):
                    key = key,  # turn it into a 1-value tuple
                agg_values[aggkey[key], :] = numpy.array(grp.sum())
        if self.fields:  # missing in scenario_damage case_8
            agg_values[-1, :] = [df[ln].sum() for ln in loss_names]
        return agg_values

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
        attrs = {'time_event': self.time_event or 'None',
                 'occupancy_periods': op,
                 'tot_sites': self.tot_sites,
                 'fields': ' '.join(self.fields),
                 'tagnames': encode(self.tagnames),
                 'nbytes': self.array.nbytes}
        return dict(array=self.array, tagcol=self.tagcol), attrs

    def __fromh5__(self, dic, attrs):
        self.occupancy_periods = attrs['occupancy_periods']
        self.time_event = attrs['time_event']
        self.tot_sites = attrs['tot_sites']
        self.fields = attrs['fields'].split()
        self.nbytes = attrs['nbytes']
        self.array = dic['array'][()]
        self.tagcol = dic['tagcol']

    def __repr__(self):
        return '<%s with %d asset(s)>' % (self.__class__.__name__, len(self))


def build_asset_array(assets_by_site, tagnames=(), time_event=None):
    """
    :param assets_by_site: a list of lists of assets
    :param tagnames: a list of tag names
    :returns: an array `assetcol`
    """
    for assets in assets_by_site:
        if len(assets):
            first_asset = assets[0]
            break
    else:  # no break
        raise ValueError('There are no assets!')
    loss_types = []
    occupancy_periods = []
    for name in sorted(first_asset.values):
        if name.startswith('occupants_'):
            period = name.split('_', 1)[1]
            # see scenario_risk test_case_2d
            occupancy_periods.append(period)
            loss_types.append(name)
        else:
            loss_types.append('value-' + name)
    # loss_types can be ['value-business_interruption', 'value-contents',
    # 'value-nonstructural', 'value-occupants', 'occupants_day',
    # 'occupants_night', 'occupants_transit']
    retro = ['retrofitted'] if first_asset._retrofitted else []
    float_fields = loss_types + retro
    int_fields = [(str(name), U32) for name in tagnames
                  if name not in ('id', 'site_id')]
    tagi = {str(name): i for i, name in enumerate(tagnames)}
    asset_dt = numpy.dtype(
        [('id', (numpy.string_, valid.ASSET_ID_LENGTH)),
         ('ordinal', U32), ('lon', F32), ('lat', F32),
         ('site_id', U32), ('number', F32), ('area', F32)] + [
             (str(name), float) for name in float_fields] + int_fields)
    num_assets = sum(len(assets) for assets in assets_by_site)
    assetcol = numpy.zeros(num_assets, asset_dt)
    asset_ordinal = 0
    fields = set(asset_dt.fields)
    for sid, assets_ in enumerate(assets_by_site):
        for asset in assets_:
            asset.ordinal = asset_ordinal
            record = assetcol[asset_ordinal]
            asset_ordinal += 1
            for field in fields:
                if field == 'id':
                    value = asset.asset_id
                elif field == 'ordinal':
                    value = asset.ordinal
                elif field == 'number':
                    value = asset.number
                elif field == 'area':
                    value = asset.area
                elif field == 'site_id':
                    value = sid
                elif field == 'lon':
                    value = asset.location[0]
                elif field == 'lat':
                    value = asset.location[1]
                elif field.startswith('occupants_'):
                    value = asset.values[field]
                elif field == 'retrofitted':
                    value = asset.retrofitted()
                elif field in tagnames:
                    value = asset.tagidxs[tagi[field]]
                else:
                    name, lt = field.split('-')
                    value = asset.value(lt, time_event)
                record[field] = value
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
    try:
        area = conversions.area
    except AttributeError:
        # NB: the area type cannot be an empty string because when sending
        # around the CostCalculator object we would run into this numpy bug
        # about pickling dictionaries with empty strings:
        # https://github.com/numpy/numpy/pull/5475
        area = Node('area', dict(type='?'))
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
        area.attrib, [], cc, TagCollection(tagnames))
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


def assets2array(asset_nodes, fields, retrofitted, ignore_missing_costs):
    """
    :returns: an array of assets from the asset nodes
    """
    first_asset = asset_nodes[0]
    for occ in getattr(first_asset, 'occupancies', []):
        name = 'occupants_' + occ['period']
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
            asset.attrib['occupants_' + occ['period']] = occ['occupants']
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
            elif field in 'area number':
                rec[field] = float(asset.attrib.get(field, 1))
            elif field.startswith('value-'):
                cost = field[6:]
                try:
                    rec[field] = asset[cost]
                except KeyError:
                    if cost not in ignore_missing_costs:
                        raise
            else:
                rec[field] = asset.attrib.get(field, '?')
    return array


class Exposure(object):
    """
    A class to read the exposure from XML/CSV files
    """
    fields = ['id', 'category', 'description', 'cost_types',
              'occupancy_periods', 'retrofitted',
              'area', 'assets', 'cost_calculator', 'tagcol']

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
             tagcol=None, by_country=False):
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
            if by_country and len(fnames) > 1:
                prefix = prefix2cc['E%02d_' % i] + '_'
            elif len(fnames) > 1:
                prefix = 'E%02d_' % i
            else:
                prefix = ''
            allargs.append((fname, calculation_mode, region_constraint,
                            ignore_missing_costs, check_dupl, prefix, tagcol))
        exp = None
        for exposure in itertools.starmap(Exposure.read_exp, allargs):
            if exp is None:  # first time
                exp = exposure
                exp.description = 'Composite exposure[%d]' % len(fnames)
            else:
                ae(exposure.cost_types, exp.cost_types)
                ae(exposure.occupancy_periods, exp.occupancy_periods)
                ae(exposure.retrofitted, exp.retrofitted)
                ae(exposure.area, exp.area)
                exp.assets.extend(exposure.assets)
                exp.tagcol.extend(exposure.tagcol)
        exp.exposures = [os.path.splitext(os.path.basename(f))[0]
                         for f in fnames]
        for i, ass in enumerate(exp.assets):
            # used by the GED4ALL importer
            ass.tags = exp.tagcol.get_tagdict(ass.tagidxs)
        return exp

    @staticmethod
    def read_exp(fname, calculation_mode='', region_constraint='',
                 ignore_missing_costs=(), check_dupl=True,
                 asset_prefix='', tagcol=None, monitor=None):
        logging.info('Reading %s', fname)
        param = {'calculation_mode': calculation_mode}
        param['asset_prefix'] = asset_prefix
        param['out_of_region'] = 0
        if region_constraint:
            param['region'] = wkt.loads(region_constraint)
        else:
            param['region'] = None
        param['fname'] = fname
        param['ignore_missing_costs'] = set(ignore_missing_costs)
        exposure, assetnodes = _get_exposure(param['fname'])
        if tagcol:
            exposure.tagcol = tagcol
        if assetnodes:
            array = assets2array(
                assetnodes, exposure._csv_header(),
                exposure.retrofitted or calculation_mode == 'classical_bcr',
                ignore_missing_costs)
        else:
            array = exposure._read_csv()
        param['relevant_cost_types'] = set(exposure.cost_types['name']) - set(
            ['occupants'])
        exposure._populate_from(array, param, check_dupl)
        if param['region'] and param['out_of_region']:
            logging.info('Discarded %d assets outside the region',
                         param['out_of_region'])
        if len(exposure.assets) == 0:
            raise RuntimeError('Could not find any asset within the region!')
        # sanity checks
        values = any(len(ass.values) + ass.number for ass in exposure.assets)
        assert values, 'Could not find any value??'
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
        fields = ['id', 'number', 'taxonomy', 'lon', 'lat']
        for name in self.cost_types['name']:
            fields.append(value + name)
        if 'per_area' in self.cost_types['type']:
            fields.append('area')
        for op in self.occupancy_periods.split():
            fields.append(occupants + op)
        fields.extend(self.tagcol.tagnames)
        wrong = get_case_similar(set(fields))
        if wrong:
            raise InvalidFile('Found case-duplicated fields %s in %s' %
                              (wrong, self.datafiles))
        return sorted(set(fields))

    def _read_csv(self):
        """
        :yields: asset nodes
        """
        expected_header = set(self._csv_header('', ''))
        for fname in self.datafiles:
            with open(fname, encoding='utf-8-sig') as f:
                fields = next(csv.reader(f))
                header = set(fields)
                missing = expected_header - header - {'exposure', 'country'}
                if len(header) < len(fields):
                    raise InvalidFile(
                        '%s: The header %s contains a duplicated field' %
                        (fname, header))
                elif missing:
                    msg = ('Unexpected header in %s\nExpected: %s\nGot: %s\n'
                           'Missing: %s')
                    raise InvalidFile(msg % (fname, sorted(expected_header),
                                             sorted(header), missing))
        conv = {'lon': float, 'lat': float, 'number': float, 'area': float,
                'retrofitted': float, None: object}
        rename = {}
        for field in self.cost_types['name']:
            conv[field] = float
            rename[field] = 'value-' + field
        for field in self.occupancy_periods.split():
            conv[field] = float
            rename[field] = 'occupants_' + field
        for fname in self.datafiles:
            array = hdf5.read_csv(fname, conv, rename).array
            array['lon'] = numpy.round(array['lon'], 5)
            array['lat'] = numpy.round(array['lat'], 5)
            yield from array

    def _populate_from(self, asset_array, param, check_dupl):
        asset_refs = set()
        for idx, asset in enumerate(asset_array):
            asset_id = asset['id']
            # check_dupl is False only in oq prepare_site_model since
            # in that case we are only interested in the asset locations
            if check_dupl and asset_id in asset_refs:
                raise nrml.DuplicatedID(asset_id)
            asset_refs.add(param['asset_prefix'] + asset_id)
            self._add_asset(idx, asset, param)

    def _add_asset(self, idx, asset, param):
        values = {}
        try:
            retrofitted = asset['retrofitted']
        except ValueError:
            retrofitted = None
        asset_id = asset['id']
        prefix = param['asset_prefix']
        # FIXME: in case of an exposure split in CSV files the line number
        # is None because param['fname'] points to the .xml file :-(
        taxonomy = asset['taxonomy']
        number = asset['number']
        location = asset['lon'], asset['lat']
        if param['region'] and not geometry.Point(*location).within(
                param['region']):
            param['out_of_region'] += 1
            return
        dic = {tagname: asset[tagname] for tagname in self.tagcol.tagnames
               if tagname not in ('country', 'exposure') and
               asset[tagname] != '?'}
        dic['taxonomy'] = taxonomy
        idxs = self.tagcol.add_tags(dic, prefix)
        tot_occupants = 0
        num_occupancies = 0
        for name in asset.dtype.names:
            if name.startswith('value-'):
                values[name[6:]] = asset[name]
            elif name.startswith('occupants_'):
                values[name] = occ = float(asset[name])
                tot_occupants += occ
                num_occupancies += 1
        if num_occupancies:
            # store average occupants
            values['occupants'] = tot_occupants / num_occupancies

        # check if we are not missing a cost type
        missing = param['relevant_cost_types'] - set(values)
        if missing and missing <= param['ignore_missing_costs']:
            logging.warning(
                'Ignoring asset %s, missing cost type(s): %s',
                asset_id, ', '.join(missing))
            for cost_type in missing:
                values[cost_type] = None
        elif missing and 'damage' not in param['calculation_mode']:
            # missing the costs is okay for damage calculators
            raise ValueError("Invalid Exposure. "
                             "Missing cost %s for asset %s" % (
                                 missing, asset_id))
        try:
            area = asset['area']
        except ValueError:
            area = 1
        ass = Asset(prefix + asset_id, idx, idxs, number, location, values,
                    area, retrofitted, self.cost_calculator)
        self.assets.append(ass)

    def get_mesh_assets_by_site(self):
        """
        :returns: (Mesh instance, assets_by_site list)
        """
        assets_by_loc = general.groupby(self, key=lambda a: a.location)
        mesh = geo.Mesh.from_coords(list(assets_by_loc))
        assets_by_site = [
            assets_by_loc[lonlat] for lonlat in zip(mesh.lons, mesh.lats)]
        return mesh, assets_by_site

    def __iter__(self):
        return iter(self.assets)

    def __repr__(self):
        return '<%s with %s assets>' % (self.__class__.__name__,
                                        len(self.assets))
