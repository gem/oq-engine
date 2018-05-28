# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2018 GEM Foundation
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

from openquake.baselib import hdf5, general
from openquake.baselib.node import Node, context
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import valid, nrml, geo, InvalidFile


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

    @property
    def taxonomy(self):
        return self.tagvalue('taxonomy')

    def tagvalue(self, tagname):
        """
        :returns: the tagvalue associated to the given tagname
        """
        return self.tagidxs[self.calc.tagi[tagname]]

    def deductible(self, loss_type):
        """
        :returns: the deductible fraction of the asset cost for `loss_type`
        """
        val = self.calc(loss_type, self.deductibles, self.area, self.number)
        if self.calc.deduct_abs:  # convert to relative value
            return val / self.calc(loss_type, self.values,
                                   self.area, self.number)
        else:
            return val

    def insurance_limit(self, loss_type):
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
        self.tagnames = tagnames
        for tagname in self.tagnames:
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
            assert idx < TWO16, idx
            return idx

    def add_tags(self, dic):
        """
        :param dic: a dictionary tagname -> tagvalue
        :returns: a list of tag indices, one per tagname
        """
        # fill missing tagvalues with "?", raise an error for unknown tagnames
        idxs = []
        for tagname in self.tagnames:
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

    def get_tag(self, tagname, tagidx):
        """
        :returns: the tag associated to the given tagname and tag index
        """
        return '%s=%s' % (tagname, decode(getattr(self, tagname)[tagidx]))

    def gen_tags(self, tagname):
        """
        :yields: the tags associated to the given tagname
        """
        for tagvalue in getattr(self, tagname):
            yield '%s=%s' % (tagname, decode(tagvalue))

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

    def __init__(self, asset_refs, assets_by_site, tagcol, cost_calculator,
                 time_event, occupancy_periods):
        self.tagcol = tagcol
        self.cost_calculator = cost_calculator
        self.time_event = time_event
        self.tot_sites = len(assets_by_site)
        self.array, self.occupancy_periods = build_asset_array(
            assets_by_site, tagcol.tagnames)
        if self.occupancy_periods and not occupancy_periods:
            logging.warn('Missing <occupancyPeriods>%s</occupancyPeriods> '
                         'in the exposure', self.occupancy_periods)
        elif self.occupancy_periods.strip() != occupancy_periods.strip():
            raise ValueError('Expected %s, got %s' %
                             (occupancy_periods, self.occupancy_periods))
        self.asset_refs = asset_refs
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

    def get_aids_by_tag(self):
        """
        :returns: dict tag -> asset ordinals
        """
        aids_by_tag = general.AccumDict(accum=set())
        for aid, ass in enumerate(self):
            for tagname, tagidx in zip(self.tagnames, ass.tagidxs):
                tag = self.tagcol.get_tag(tagname, tagidx)
                aids_by_tag[tag].add(aid)
        return aids_by_tag

    @property
    def taxonomies(self):
        """
        Return a list of taxonomies, one per asset (with duplicates)
        """
        return self.array['taxonomy']

    def units(self, loss_types):
        """
        :param: a list of loss types
        :returns: an array of units as byte strings, suitable for HDF5
        """
        units = self.cost_calculator.units
        lst = []
        for lt in loss_types:
            if lt.endswith('_ins'):
                lt = lt[:-4]
            if lt == 'occupants':
                unit = 'people'
            else:
                unit = units[lt]
            lst.append(encode(unit))
        return numpy.array(lst)

    def assets_by_site(self):
        """
        :returns: numpy array of lists with the assets by each site
        """
        assets_by_site = [[] for sid in range(self.tot_sites)]
        for i, ass in enumerate(self.array):
            assets_by_site[ass['site_id']].append(self[i])
        return numpy.array(assets_by_site)

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
        new.array = numpy.concatenate(array)
        new.asset_refs = numpy.concatenate(asset_refs)
        sitecol.make_complete()
        return new

    def values(self, aids=None):
        """
        :param aids: asset indices where to compute the values (None means all)
        :returns: a structured array of asset values by loss type
        """
        if aids is None:
            aids = range(len(self))
        loss_dt = numpy.dtype([(str(lt), F32) for lt in self.loss_types])
        vals = numpy.zeros(len(aids), loss_dt)  # asset values by loss_type
        for i, aid in enumerate(aids):
            asset = self[aid]
            for lt in self.loss_types:
                vals[i][lt] = asset.value(lt, self.time_event)
        return vals

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, aid):
        a = self.array[aid]
        values = {lt: a['value-' + lt] for lt in self.loss_types
                  if lt != 'occupants'}
        for name in self.array.dtype.names:
            if name.startswith('occupants_'):
                values[name] = a[name]
        return Asset(
            aid,
            [a[decode(name)] for name in self.tagnames],
            number=a['number'],
            location=(valid.longitude(a['lon']),  # round coordinates
                      valid.latitude(a['lat'])),
            values=values,
            area=a['area'],
            deductibles={lt[self.D:]: a[lt] for lt in self.deduc},
            insurance_limits={lt[self.I:]: a[lt] for lt in self.i_lim},
            retrofitted=a['retrofitted'] if self.retro else None,
            calc=self.cost_calculator)

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


def build_asset_array(assets_by_site, tagnames=()):
    """
    :param assets_by_site: a list of lists of assets
    :param tagnames: a list of tag names
    :param time_event: a time event string (or None)
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
    deductible_d = first_asset.deductibles or {}
    limit_d = first_asset.insurance_limits or {}
    deductibles = ['deductible-%s' % name for name in deductible_d]
    limits = ['insurance_limit-%s' % name for name in limit_d]
    retro = ['retrofitted'] if first_asset._retrofitted else []
    float_fields = loss_types + deductibles + limits + retro
    int_fields = [(str(name), U16) for name in tagnames]
    tagi = {str(name): i for i, name in enumerate(tagnames)}
    asset_dt = numpy.dtype(
        [('lon', F32), ('lat', F32), ('site_id', U32),
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
                if field == 'number':
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
                    value = asset._retrofitted
                elif field in tagnames:
                    value = asset.tagidxs[tagi[field]]
                else:
                    try:
                        name, lt = field.split('-')
                    except ValueError:  # no - in field
                        name, lt = 'value', field
                    # the line below retrieve one of `deductibles` or
                    # `insurance_limits` ("s" suffix)
                    value = getattr(asset, name + 's')[lt]
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
    return exp, exposure.assets


class Exposure(object):
    """
    A class to read the exposure from XML/CSV files
    """
    fields = ['id', 'category', 'description', 'cost_types',
              'occupancy_periods', 'insurance_limit_is_absolute',
              'deductible_is_absolute', 'retrofitted',
              'area', 'assets', 'asset_refs',
              'cost_calculator', 'tagcol']

    @classmethod
    def read(cls, fname, calculation_mode='', region_constraint='',
             ignore_missing_costs=(), asset_nodes=False):
        """
        Call `Exposure.read(fname)` to get an :class:`Exposure` instance
        keeping all the assets in memory or
        `Exposure.read(fname, asset_nodes=True)` to get an iterator over
        Node objects (one Node for each asset).
        """
        param = {'calculation_mode': calculation_mode}
        param['out_of_region'] = 0
        if region_constraint:
            param['region'] = wkt.loads(region_constraint)
        else:
            param['region'] = None
        param['fname'] = fname
        param['ignore_missing_costs'] = set(ignore_missing_costs)
        exposure, assets = _get_exposure(param['fname'])
        param['relevant_cost_types'] = set(exposure.cost_types['name']) - set(
            ['occupants'])
        nodes = assets if assets else exposure._read_csv(
            assets.text, os.path.dirname(param['fname']))
        if asset_nodes:  # this is useful for the GED4ALL import script
            return nodes
        exposure._populate_from(nodes, param)
        if param['region'] and param['out_of_region']:
            logging.info('Discarded %d assets outside the region',
                         param['out_of_region'])
        if len(exposure.assets) == 0:
            raise RuntimeError('Could not find any asset within the region!')
        # sanity checks
        values = any(len(ass.values) + ass.number for ass in exposure.assets)
        assert values, 'Could not find any value??'
        return exposure

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

    def _read_csv(self, csvnames, dirname):
        """
        :param csvnames: names of csv files, space separated
        :param dirname: the directory where the csv files are
        :yields: asset nodes
        """
        expected_header = self._csv_header()
        fnames = [os.path.join(dirname, f) for f in csvnames.split()]
        for fname in fnames:
            with open(fname) as f:
                fields = next(csv.reader(f))
                header = set(fields)
                if len(header) < len(fields):
                    raise InvalidFile(
                        '%s: The header %s contains a duplicated field' %
                        (fname, header))
                elif expected_header - header:
                    raise InvalidFile(
                        'Unexpected header in %s\nExpected: %s\nGot: %s' %
                        (fname, sorted(expected_header), sorted(header)))
        occupancy_periods = self.occupancy_periods.split()
        for fname in fnames:
            with open(fname) as f:
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
                            costs.append(Node('cost', a))
                        occupancies = Node('occupancies')
                        for period in occupancy_periods:
                            a = dict(occupants=float(dic[period]),
                                     period=period)
                            occupancies.append(Node('occupancy', a))
                        tags = Node('tags')
                        for tagname in self.tagcol.tagnames:
                            if tagname != 'taxonomy':
                                tags.attrib[tagname] = dic[tagname]
                        asset.nodes.extend([loc, costs, occupancies, tags])
                        if i % 100000 == 0:
                            logging.info('Read %d assets', i)
                    yield asset

    def _populate_from(self, asset_nodes, param):
        asset_refs = set()
        for idx, asset_node in enumerate(asset_nodes):
            asset_id = asset_node['id']
            if asset_id in asset_refs:
                raise nrml.DuplicatedID(asset_id)
            asset_refs.add(asset_id)
            self._add_asset(idx, asset_node, param)

    def _add_asset(self, idx, asset_node, param):
        values = {}
        deductibles = {}
        insurance_limits = {}
        retrofitted = None
        asset_id = asset_node['id'].encode('utf8')
        # FIXME: in case of an exposure split in CSV files the line number
        # is None because param['fname'] points to the .xml file :-(
        with context(param['fname'], asset_node):
            self.asset_refs.append(asset_id)
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
            with context(param['fname'], tagnode):
                dic['taxonomy'] = taxonomy
                idxs = self.tagcol.add_tags(dic)
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
                    retrofitted = cost.get('retrofitted')
                if cost_type in param['relevant_cost_types']:
                    values[cost_type] = cost['value']
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
            logging.warn(
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
