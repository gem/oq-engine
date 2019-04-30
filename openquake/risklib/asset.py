# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
import logging
import csv
import os
import numpy
from shapely import wkt, geometry

from openquake.baselib import hdf5, general, parallel
from openquake.baselib.node import Node, context
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import valid, nrml, geo, InvalidFile
from openquake.risklib import countries


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
    def __init__(self, cost_types, area_types, units,
                 deduct_abs=True, limit_abs=True, tagi={'taxonomy': 0}):
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
        self.deduct_abs = deduct_abs
        self.limit_abs = limit_abs
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
            lst.append(encode(unit))
        return numpy.array(lst)

    def __toh5__(self):
        loss_types = sorted(self.cost_types)
        dt = numpy.dtype([('cost_type', hdf5.vstr),
                          ('area_type', hdf5.vstr),
                          ('unit', hdf5.vstr)])
        array = numpy.zeros(len(loss_types), dt)
        array['cost_type'] = [self.cost_types[lt] for lt in loss_types]
        array['area_type'] = [self.area_types[lt] for lt in loss_types]
        array['unit'] = [self.units[lt] for lt in loss_types]
        attrs = dict(deduct_abs=self.deduct_abs, limit_abs=self.limit_abs,
                     loss_types=hdf5.array_of_vstr(loss_types))
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

    Optionally, a Asset instance can hold also a collection of
    deductible values and insured limits considered for insured losses
    calculations.
    """
    def __init__(self,
                 ordinal,
                 tagidxs,
                 number,
                 location,
                 values,
                 area=1,
                 deductibles=None,
                 insurance_limits=None,
                 retrofitted=None,
                 calc=costcalculator):
        """
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
        :param dict deductible:
            deductible values (expressed as a percentage relative to
            the value of the asset) keyed by loss types
        :param dict insurance_limits:
            insured limits values (expressed as a percentage relative to
            the value of the asset) keyed by loss types
        :param retrofitted:
            asset retrofitted value
        :param calc:
            cost calculator instance
        :param ordinal:
            asset collection ordinal
        """
        self.ordinal = ordinal
        self.tagidxs = tagidxs
        self.number = number
        self.location = location
        self.values = values
        self.area = area
        self._retrofitted = retrofitted
        self.deductibles = deductibles
        self.insurance_limits = insurance_limits
        self.calc = calc
        self._cost = {}  # cache for the costs

    @property
    def taxonomy(self):
        return self.tagvalue('taxonomy')

    def tagvalue(self, tagname):
        """
        :returns: the tagvalue associated to the given tagname
        """
        return self.tagidxs[self.calc.tagi[tagname]]

    def value(self, loss_type, time_event=None):
        """
        :returns: the total asset value for `loss_type`
        """
        if loss_type == 'occupants':
            return self.values['occupants_' + str(time_event)]
        try:  # extract from the cache
            val = self._cost[loss_type]
        except KeyError:  # compute
            val = self.calc(loss_type, self.values, self.area, self.number)
            self._cost[loss_type] = val
        return val

    def deductible(self, loss_type, dummy=None):
        """
        :returns: the deductible fraction of the asset cost for `loss_type`
        """
        val = self.calc(loss_type, self.deductibles, self.area, self.number)
        if self.calc.deduct_abs:  # convert to relative value
            return val / self.calc(loss_type, self.values,
                                   self.area, self.number)
        else:
            return val

    def insurance_limit(self, loss_type, dummy=None):
        """
        :returns: the limit fraction of the asset cost for `loss_type`
        """
        val = self.calc(loss_type, self.insurance_limits, self.area,
                        self.number)
        if self.calc.limit_abs:  # convert to relative value
            return val / self.calc(loss_type, self.values,
                                   self.area, self.number)
        else:
            return val

    def retrofitted(self):
        """
        :returns: the asset retrofitted value
        """
        return self.calc('structural', {'structural': self._retrofitted},
                         self.area, self.number)

    def tagmask(self, tags):
        """
        :returns: a boolean array with True where the assets has tags
        """
        mask = numpy.zeros(len(tags), bool)
        for t, tag in enumerate(tags):
            tagname, tagvalue = tag.split('=')
            mask[t] = self.tagvalue(tagname) == tagvalue
        return mask

    def __lt__(self, other):
        return self.ordinal < other.ordinal

    def __repr__(self):
        return '<Asset #%s>' % self.ordinal


U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
TWO16 = 2 ** 16
by_taxonomy = operator.attrgetter('taxonomy')


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
            if idx > TWO16:
                raise InvalidFile('contains more then %d tags' % TWO16)
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

    def gen_tags(self, tagname):
        """
        :yields: the tags associated to the given tagname
        """
        for tagvalue in getattr(self, tagname):
            yield '%s=%s' % (tagname, decode(tagvalue))

    def agg_shape(self, shp, aggregate_by):
        """
        :returns: a shape shp + (T, ...) depending on the tagnames
        """
        return shp + tuple(
            len(getattr(self, tagname)) - 1 for tagname in aggregate_by)

    def __toh5__(self):
        dic = {}
        for tagname in self.tagnames:
            dic[tagname] = numpy.array(getattr(self, tagname), hdf5.vstr)
        return dic, {'tagnames': numpy.array(self.tagnames, hdf5.vstr)}

    def __fromh5__(self, dic, attrs):
        self.tagnames = [decode(name) for name in attrs['tagnames']]
        for tagname in dic:
            setattr(self, tagname + '_idx',
                    {tag: idx for idx, tag in enumerate(dic[tagname])})
            setattr(self, tagname, dic[tagname].value)

    def __iter__(self):
        tags = []
        for tagname in self.tagnames:
            for tagvalue in getattr(self, tagname):
                tags.append('%s=%s' % (tagname, tagvalue))
        return iter(sorted(tags))

    def __len__(self):
        return sum(len(getattr(self, tagname)) for tagname in self.tagnames)


class AssetCollection(object):
    # the information about the assets is stored in a numpy array and in a
    # variable-length dataset aids_by_tags; we could store everything in a
    # single array and it would be easier, but then we would need to transfer
    # unneeded strings; also we would have to use fixed-length string, since
    # numpy has no concept of variable-lenght strings; unless we associate
    # numbers to each tagvalue, which is possible
    D, I = len('deductible-'), len('insurance_limit-')

    def __init__(self, exposure, assets_by_site, time_event):
        self.asset_refs = numpy.array([
            exposure.asset_refs[asset.ordinal]
            for assets in assets_by_site for asset in assets])
        self.tagcol = exposure.tagcol
        self.cost_calculator = exposure.cost_calculator
        self.time_event = time_event
        self.tot_sites = len(assets_by_site)
        self.array, self.occupancy_periods = build_asset_array(
            assets_by_site, exposure.tagcol.tagnames, time_event)
        periods = exposure.occupancy_periods
        if self.occupancy_periods and not periods:
            logging.warning('Missing <occupancyPeriods>%s</occupancyPeriods> '
                            'in the exposure', self.occupancy_periods)
        elif self.occupancy_periods.strip() != periods.strip():
            raise ValueError('Expected %s, got %s' %
                             (periods, self.occupancy_periods))
        fields = self.array.dtype.names
        self.loss_types = [f[6:] for f in fields if f.startswith('value-')]
        if any(field.startswith('occupants_') for field in fields):
            self.loss_types.append('occupants')
        self.loss_types.sort()
        self.deduc = [n for n in fields if n.startswith('deductible-')]
        self.i_lim = [n for n in fields if n.startswith('insurance_limit-')]
        self.retro = [n for n in fields if n == 'retrofitted']

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
        return numpy.array(assets_by_site)

    def aggregate_by(self, tagnames, array):
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
        shape = [len(getattr(self.tagcol, tagname))-1 for tagname in tagnames]
        acc = numpy.zeros(shape, (F32, shp) if shp else F32)
        for asset, row in zip(self.array, array):
            acc[tuple(idx - 1 for idx in asset[tagnames])] += row
        return acc

    def agg_value(self, *tagnames):
        """
        :param tagnames:
            tagnames of lengths T1, T2, ... respectively
        :returns:
            the values of the exposure aggregated by tagnames as an array
            of shape (T1, T2, ..., L)
        """
        aval = numpy.zeros((len(self), len(self.loss_types)), F32)  # (A, L)
        for asset in self:
            for lti, lt in enumerate(self.loss_types):
                if lt == 'occupants':
                    aval[asset['ordinal'], lti] = asset[lt + '_None']
                else:
                    aval[asset['ordinal'], lti] = asset['value-' + lt]
        return self.aggregate_by(list(tagnames), aval)

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
        new.asset_refs = self.asset_refs[ok_indices]
        return new

    def reduce_also(self, sitecol):
        """
        :returns: a reduced AssetCollection on the given sitecol
        NB: diffently from .reduce, also the SiteCollection is reduced
        and turned into a complete site collection.
        """
        array = []
        asset_refs = []
        for idx, sid in enumerate(sitecol.sids):
            mask = self.array['site_id'] == sid
            arr = self.array[mask]
            arr['site_id'] = idx
            array.append(arr)
            asset_refs.append(self.asset_refs[mask])
        new = object.__new__(self.__class__)
        vars(new).update(vars(self))
        new.tot_sites = len(sitecol)
        new.array = numpy.concatenate(array)
        new.array['ordinal'] = numpy.arange(len(new.array))
        new.asset_refs = numpy.concatenate(asset_refs)
        sitecol.make_complete()
        return new

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
                 'loss_types': ' '.join(self.loss_types),
                 'deduc': ' '.join(self.deduc),
                 'i_lim': ' '.join(self.i_lim),
                 'retro': ' '.join(self.retro),
                 'tot_sites': self.tot_sites,
                 'tagnames': encode(self.tagnames),
                 'nbytes': self.array.nbytes}
        return dict(
            array=self.array, cost_calculator=self.cost_calculator,
            tagcol=self.tagcol, asset_refs=self.asset_refs), attrs

    def __fromh5__(self, dic, attrs):
        for name in ('loss_types', 'deduc', 'i_lim', 'retro'):
            setattr(self, name, [decode(x) for x in attrs[name].split()])
        self.occupancy_periods = attrs['occupancy_periods']
        self.time_event = attrs['time_event']
        self.tot_sites = attrs['tot_sites']
        self.nbytes = attrs['nbytes']
        self.array = dic['array'].value
        self.tagcol = dic['tagcol']
        self.cost_calculator = dic['cost_calculator']
        self.asset_refs = dic['asset_refs'].value
        self.cost_calculator.tagi = {
            decode(tagname): i for i, tagname in enumerate(self.tagnames)}

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
            if period != 'None':
                # see scenario_risk test_case_2d
                occupancy_periods.append(period)
            loss_types.append(name)
            # discard occupants for different time periods
        else:
            loss_types.append('value-' + name)
    # loss_types can be ['value-business_interruption', 'value-contents',
    # 'value-nonstructural', 'occupants_None', 'occupants_day',
    # 'occupants_night', 'occupants_transit']
    deductible_d = first_asset.deductibles or {}
    limit_d = first_asset.insurance_limits or {}
    if deductible_d or limit_d:
        logging.warning('Exposures with insuranceLimit/deductible fields are '
                        'deprecated and may be removed in the future')
    retro = ['retrofitted'] if first_asset._retrofitted else []
    float_fields = loss_types + retro
    int_fields = [(str(name), U16) for name in tagnames]
    tagi = {str(name): i for i, name in enumerate(tagnames)}
    asset_dt = numpy.dtype(
        [('ordinal', U32), ('lon', F32), ('lat', F32), ('site_id', U32),
         ('number', F32), ('area', F32)] + [
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
                if field == 'ordinal':
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
        inslimit = conversions.insuranceLimit
    except AttributeError:
        inslimit = Node('insuranceLimit', text=True)
    try:
        deductible = conversions.deductible
    except AttributeError:
        deductible = Node('deductible', text=True)
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
    insurance_limit_is_absolute = il = inslimit.get('isAbsolute')
    deductible_is_absolute = de = deductible.get('isAbsolute')
    cc = CostCalculator(
        {}, {}, {},
        True if de is None else de,
        True if il is None else il,
        {name: i for i, name in enumerate(tagnames)},
    )
    for ct in cost_types:
        name = ct['name']  # structural, nonstructural, ...
        cc.cost_types[name] = ct['type']  # aggregated, per_asset, per_area
        cc.area_types[name] = area['type']
        cc.units[name] = ct['unit']
    assets = []
    asset_refs = []
    exp = Exposure(
        exposure['id'], exposure['category'],
        description.text, cost_types, occupancy_periods,
        insurance_limit_is_absolute, deductible_is_absolute, retrofitted,
        area.attrib, assets, asset_refs, cc, TagCollection(tagnames))
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


class Exposure(object):
    """
    A class to read the exposure from XML/CSV files
    """
    fields = ['id', 'category', 'description', 'cost_types',
              'occupancy_periods', 'insurance_limit_is_absolute',
              'deductible_is_absolute', 'retrofitted',
              'area', 'assets', 'asset_refs',
              'cost_calculator', 'tagcol']

    @staticmethod
    def read(fnames, calculation_mode='', region_constraint='',
             ignore_missing_costs=(), asset_nodes=False, check_dupl=True,
             tagcol=None, by_country=False):
        """
        Call `Exposure.read(fname)` to get an :class:`Exposure` instance
        keeping all the assets in memory or
        `Exposure.read(fname, asset_nodes=True)` to get an iterator over
        Node objects (one Node for each asset).
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
                            ignore_missing_costs, asset_nodes, check_dupl,
                            prefix, tagcol))
        exp = None
        for exposure in parallel.Starmap(
                Exposure.read_exp, allargs, distribute='no'):
            if exp is None:  # first time
                exp = exposure
                exp.description = 'Composite exposure[%d]' % len(fnames)
            else:
                assert exposure.cost_types == exp.cost_types
                assert exposure.occupancy_periods == exp.occupancy_periods
                assert (exposure.insurance_limit_is_absolute ==
                        exp.insurance_limit_is_absolute)
                assert exposure.retrofitted == exp.retrofitted
                assert exposure.area == exp.area
                exp.assets.extend(exposure.assets)
                exp.asset_refs.extend(exposure.asset_refs)
                exp.tagcol.extend(exposure.tagcol)
        exp.exposures = [os.path.splitext(os.path.basename(f))[0]
                         for f in fnames]
        return exp

    @staticmethod
    def read_exp(fname, calculation_mode='', region_constraint='',
                 ignore_missing_costs=(), asset_nodes=False, check_dupl=True,
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
        param['relevant_cost_types'] = set(exposure.cost_types['name']) - set(
            ['occupants'])
        nodes = assetnodes if assetnodes else exposure._read_csv()
        if asset_nodes:  # this is useful for the GED4ALL import script
            return nodes
        exposure._populate_from(nodes, param, check_dupl)
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

    def _csv_header(self):
        """
        Extract the expected CSV header from the exposure metadata
        """
        fields = ['id', 'number', 'taxonomy', 'lon', 'lat']
        for name in self.cost_types['name']:
            fields.append(name)
        if 'per_area' in self.cost_types['type']:
            fields.append('area')
        if self.occupancy_periods:
            fields.extend(self.occupancy_periods.split())
        fields.extend(self.tagcol.tagnames)
        return set(fields)

    def _read_csv(self):
        """
        :yields: asset nodes
        """
        expected_header = self._csv_header()
        for fname in self.datafiles:
            with open(fname, encoding='utf-8') as f:
                fields = next(csv.reader(f))
                header = set(fields)
                if len(header) < len(fields):
                    raise InvalidFile(
                        '%s: The header %s contains a duplicated field' %
                        (fname, header))
                elif expected_header - header - {'exposure', 'country'}:
                    raise InvalidFile(
                        'Unexpected header in %s\nExpected: %s\nGot: %s' %
                        (fname, sorted(expected_header), sorted(header)))
        occupancy_periods = self.occupancy_periods.split()
        for fname in self.datafiles:
            with open(fname, encoding='utf-8') as f:
                for i, dic in enumerate(csv.DictReader(f), 1):
                    asset = Node('asset', lineno=i)
                    with context(fname, asset):
                        asset['id'] = dic['id']
                        asset['number'] = valid.positivefloat(dic['number'])
                        asset['taxonomy'] = dic['taxonomy']
                        if 'area' in dic:  # optional attribute
                            asset['area'] = dic['area']
                        loc = Node('location',
                                   dict(lon=valid.longitude(dic['lon']),
                                        lat=valid.latitude(dic['lat'])))
                        costs = Node('costs')
                        for cost in self.cost_types['name']:
                            a = dict(type=cost, value=dic[cost])
                            if 'retrofitted' in dic:
                                a['retrofitted'] = dic['retrofitted']
                            costs.append(Node('cost', a))
                        occupancies = Node('occupancies')
                        for period in occupancy_periods:
                            a = dict(occupants=float(dic[period]),
                                     period=period)
                            occupancies.append(Node('occupancy', a))
                        tags = Node('tags')
                        for tagname in self.tagcol.tagnames:
                            if tagname not in (
                                    'taxonomy', 'exposure', 'country'):
                                tags.attrib[tagname] = dic[tagname]
                        asset.nodes.extend([loc, costs, occupancies, tags])
                    yield asset

    def _populate_from(self, asset_nodes, param, check_dupl):
        asset_refs = set()
        for idx, asset_node in enumerate(asset_nodes):
            asset_id = asset_node['id']
            # check_dupl is False only in oq prepare_site_model since
            # in that case we are only interested in the asset locations
            if check_dupl and asset_id in asset_refs:
                raise nrml.DuplicatedID(asset_id)
            asset_refs.add(param['asset_prefix'] + asset_id)
            self._add_asset(idx, asset_node, param)

    def _add_asset(self, idx, asset_node, param):
        values = {}
        deductibles = {}
        insurance_limits = {}
        retrofitted = None
        asset_id = asset_node['id'].encode('utf8')
        prefix = param['asset_prefix'].encode('utf8')
        # FIXME: in case of an exposure split in CSV files the line number
        # is None because param['fname'] points to the .xml file :-(
        with context(param['fname'], asset_node):
            self.asset_refs.append(prefix + asset_id)
            taxonomy = asset_node['taxonomy']
            if 'damage' in param['calculation_mode']:
                # calculators of 'damage' kind require the 'number'
                # if it is missing a KeyError is raised
                number = asset_node['number']
            else:
                # some calculators ignore the 'number' attribute;
                # if it is missing it is considered 1, since we are going
                # to multiply by it
                try:
                    number = asset_node['number']
                except KeyError:
                    number = 1
                else:
                    if 'occupants' in self.cost_types['name']:
                        values['occupants_None'] = number
            location = asset_node.location['lon'], asset_node.location['lat']
            if param['region'] and not geometry.Point(*location).within(
                    param['region']):
                param['out_of_region'] += 1
                return
            tagnode = getattr(asset_node, 'tags', None)
            dic = {} if tagnode is None else tagnode.attrib.copy()
            dic['taxonomy'] = taxonomy
            idxs = self.tagcol.add_tags(dic, prefix)
        try:
            costs = asset_node.costs
        except AttributeError:
            costs = Node('costs', [])
        try:
            occupancies = asset_node.occupancies
        except AttributeError:
            occupancies = Node('occupancies', [])
        for cost in costs:
            with context(param['fname'], cost):
                cost_type = cost['type']
                if cost_type == 'structural':
                    # retrofitted is defined only for structural
                    retrofitted = float(cost.get('retrofitted', 0))
                if cost_type in param['relevant_cost_types']:
                    values[cost_type] = float(cost['value'])
                    try:
                        deductibles[cost_type] = cost['deductible']
                    except KeyError:
                        pass
                    try:
                        insurance_limits[cost_type] = cost['insuranceLimit']
                    except KeyError:
                        pass

        # check we are not missing a cost type
        missing = param['relevant_cost_types'] - set(values)
        if missing and missing <= param['ignore_missing_costs']:
            logging.warning(
                'Ignoring asset %s, missing cost type(s): %s',
                asset_id, ', '.join(missing))
            for cost_type in missing:
                values[cost_type] = None
        elif missing and 'damage' not in param['calculation_mode']:
            # missing the costs is okay for damage calculators
            with context(param['fname'], asset_node):
                raise ValueError("Invalid Exposure. "
                                 "Missing cost %s for asset %s" % (
                                     missing, asset_id))
        tot_occupants = 0
        for occupancy in occupancies:
            with context(param['fname'], occupancy):
                occupants = 'occupants_%s' % occupancy['period']
                values[occupants] = float(occupancy['occupants'])
                tot_occupants += values[occupants]
        if occupancies:  # store average occupants
            values['occupants_None'] = tot_occupants / len(occupancies)
        area = float(asset_node.get('area', 1))
        ass = Asset(idx, idxs, number, location, values, area,
                    deductibles, insurance_limits, retrofitted,
                    self.cost_calculator)
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
