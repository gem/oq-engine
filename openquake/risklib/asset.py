# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

from __future__ import division
import operator
import numpy

from openquake.baselib import hdf5
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import valid


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
                 deduct_abs=True, limit_abs=True):
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
                 asset_id,
                 taxonomy,
                 number,
                 location,
                 values,
                 area=1,
                 deductibles=None,
                 insurance_limits=None,
                 retrofitteds=None,
                 calc=costcalculator,
                 ordinal=None):
        """
        :param asset_id:
            an unique identifier of the assets within the given exposure
        :param taxonomy:
            asset taxonomy
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
        :param dict retrofitteds:
            asset retrofitting values keyed by loss types
        :param calc:
            cost calculator instance
        :param ordinal:
            asset collection ordinal
        """
        self.idx = asset_id
        self.taxonomy = taxonomy
        self.number = number
        self.location = location
        self.values = values
        self.area = area
        self.retrofitteds = retrofitteds
        self.deductibles = deductibles
        self.insurance_limits = insurance_limits
        self.calc = calc
        self.ordinal = ordinal
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

    def retrofitted(self, loss_type, time_event=None):
        """
        :returns: the asset retrofitted value for `loss_type`
        """
        if loss_type == 'occupants':
            return self.values['occupants_' + str(time_event)]
        return self.calc(loss_type, self.retrofitteds,
                         self.area, self.number)

    def __lt__(self, other):
        return self.idx < other.idx

    def __repr__(self):
        return '<Asset %s>' % self.idx


U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
U64 = numpy.uint64
TWO48 = 2 ** 48
EVENTS = -2
NBYTES = -1

FIELDS = ('site_id', 'lon', 'lat', 'idx', 'area', 'number',
          'occupants', 'deductible-', 'insurance_limit-', 'retrofitted-')

by_taxonomy = operator.attrgetter('taxonomy')

aids_dt = numpy.dtype([('aids', hdf5.vuint32)])


class AssetCollection(object):
    D, I, R = len('deductible-'), len('insurance_limit-'), len('retrofitted-')

    def __init__(self, assets_by_site, assets_by_tag, cost_calculator,
                 time_event, time_events=''):
        self.cc = cost_calculator
        self.time_event = time_event
        self.time_events = time_events
        self.tot_sites = len(assets_by_site)
        self.array = self.build_asset_collection(assets_by_site, time_event)
        dic = dict(zip(self.array['idx'], range(len(self.array))))
        self.tagnames = assets_by_tag.tagnames
        self.aids_by_tag = {}
        for tag, idxs in assets_by_tag.items():
            aids = []
            for idx in idxs:
                try:
                    aids.append(dic[idx])
                except KeyError:  # discarded by assoc_assets_sites
                    continue
            self.aids_by_tag[tag] = set(aids)
        fields = self.array.dtype.names
        self.loss_types = [f[6:] for f in fields if f.startswith('value-')]
        if 'occupants' in fields:
            self.loss_types.append('occupants')
        self.loss_types.sort()
        self.deduc = [n for n in fields if n.startswith('deductible-')]
        self.i_lim = [n for n in fields if n.startswith('insurance_limit-')]
        self.retro = [n for n in fields if n.startswith('retrofitted-')]

    @property
    def taxonomies(self):
        """
        Return a list of taxonomies, one per asset (with duplicates)
        """
        if not hasattr(self, '_taxonomy'):
            self._taxonomy = [None] * len(self)
            for tag, aids in self.aids_by_tag.items():
                name, value = tag.split('=', 1)
                if name == 'taxonomy':
                    for aid in aids:
                        self._taxonomy[aid] = value
        return self._taxonomy

    def tags(self):
        """
        :returns: list of sorted tags
        """
        return sorted(self.aids_by_tag)

    def units(self, loss_types):
        """
        :param: a list of loss types
        :returns: an array of units as byte strings, suitable for HDF5
        """
        units = self.cc.units
        lst = []
        for lt in loss_types:
            if lt.endswith('_ins'):
                lt = lt[:-4]
            lst.append(encode(units[lt]))
        return numpy.array(lst)

    def assets_by_site(self):
        """
        :returns: numpy array of lists with the assets by each site
        """
        assets_by_site = [[] for sid in range(self.tot_sites)]
        for i, ass in enumerate(self.array):
            assets_by_site[ass['site_id']].append(self[i])
        return numpy.array(assets_by_site)

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

    def tagmask(self):
        """
        :returns: array of booleans of shape (A, T)
        """
        tags = self.tags()
        tagidx = {t: i for i, t in enumerate(tags)}
        mask = numpy.zeros((len(self), len(tags)), bool)
        for tag, aids in self.aids_by_tag.items():
            mask[sorted(aids), tagidx[tag]] = True
        return mask

    def get_tax_idx(self):
        """
        :returns: list of tag indices corresponding to taxonomies
        """
        return [i for i, t in enumerate(self.tags())
                if t.startswith('taxonomy=')]

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __getitem__(self, aid):
        a = self.array[aid]
        values = {lt: a['value-' + lt] for lt in self.loss_types
                  if lt != 'occupants'}
        if 'occupants' in self.array.dtype.names:
            values['occupants_' + str(self.time_event)] = a['occupants']
        return Asset(
            a['idx'],
            self.taxonomies[aid],
            number=a['number'],
            location=(valid.longitude(a['lon']),  # round coordinates
                      valid.latitude(a['lat'])),
            values=values,
            area=a['area'],
            deductibles={lt[self.D:]: a[lt] for lt in self.deduc},
            insurance_limits={lt[self.I:]: a[lt] for lt in self.i_lim},
            retrofitteds={lt[self.R:]: a[lt] for lt in self.retro},
            calc=self.cc, ordinal=aid)

    def __len__(self):
        return len(self.array)

    def __toh5__(self):
        # NB: the loss types do not contain spaces, so we can store them
        # together as a single space-separated string
        attrs = {'time_event': self.time_event or 'None',
                 'time_events': ' '.join(map(decode, self.time_events)),
                 'loss_types': ' '.join(self.loss_types),
                 'deduc': ' '.join(self.deduc),
                 'i_lim': ' '.join(self.i_lim),
                 'retro': ' '.join(self.retro),
                 'tot_sites': self.tot_sites,
                 'tagnames': encode(self.tagnames),
                 'nbytes': self.array.nbytes}
        tags, all_aids = [], []
        for tag, aids in sorted(self.aids_by_tag.items()):
            tags.append(tag)
            all_aids.append((numpy.array(sorted(aids), U32),))
        return dict(array=self.array,
                    tags=numpy.array(tags, hdf5.vstr),
                    aids=numpy.array(all_aids, aids_dt),
                    cost_calculator=self.cc), attrs

    def __fromh5__(self, dic, attrs):
        for name in ('time_events', 'loss_types', 'deduc', 'i_lim', 'retro'):
            setattr(self, name, attrs[name].split())
        self.tagnames = attrs['tagnames']
        self.time_event = attrs['time_event']
        self.tot_sites = attrs['tot_sites']
        self.nbytes = attrs['nbytes']
        self.array = dic['array'].value
        self.cc = dic['cost_calculator']
        # dic['aids'] is an array of dtype `aids_dt` with field 'aids'
        self.aids_by_tag = {
            tag: set(aids) for tag, aids in zip(
                dic['tags'], dic['aids']['aids'])}

    @staticmethod
    def build_asset_collection(assets_by_site, time_event=None):
        """
        :param assets_by_site: a list of lists of assets
        :param time_event: a time event string (or None)
        :returns: an array `assetcol`
        """
        for assets in assets_by_site:
            if len(assets):
                first_asset = assets[0]
                break
        else:  # no break
            raise ValueError('There are no assets!')
        candidate_loss_types = list(first_asset.values)
        loss_types = []
        the_occupants = 'occupants_%s' % time_event
        for candidate in sorted(candidate_loss_types):
            if candidate.startswith('occupants'):
                if candidate == the_occupants:
                    loss_types.append('occupants')
                # discard occupants for different time periods
            else:
                loss_types.append('value-' + candidate)
        deductible_d = first_asset.deductibles or {}
        limit_d = first_asset.insurance_limits or {}
        retrofitting_d = first_asset.retrofitteds or {}
        deductibles = ['deductible-%s' % name for name in deductible_d]
        limits = ['insurance_limit-%s' % name for name in limit_d]
        retrofittings = ['retrofitted-%s' % n for n in retrofitting_d]
        float_fields = loss_types + deductibles + limits + retrofittings
        asset_dt = numpy.dtype(
            [('idx', U32), ('lon', F32), ('lat', F32), ('site_id', U32),
             ('number', F32), ('area', F32)] + [
                 (str(name), float) for name in float_fields])
        num_assets = sum(len(assets) for assets in assets_by_site)
        assetcol = numpy.zeros(num_assets, asset_dt)
        asset_ordinal = 0
        fields = set(asset_dt.fields)
        for sid, assets_ in enumerate(assets_by_site):
            for asset in sorted(assets_, key=operator.attrgetter('idx')):
                asset.ordinal = asset_ordinal
                record = assetcol[asset_ordinal]
                asset_ordinal += 1
                for field in fields:
                    if field == 'number':
                        value = asset.number
                    elif field == 'area':
                        value = asset.area
                    elif field == 'idx':
                        value = asset.idx
                    elif field == 'site_id':
                        value = sid
                    elif field == 'lon':
                        value = asset.location[0]
                    elif field == 'lat':
                        value = asset.location[1]
                    elif field == 'occupants':
                        value = asset.values[the_occupants]
                    else:
                        try:
                            name, lt = field.split('-')
                        except ValueError:  # no - in field
                            name, lt = 'value', field
                        # the line below retrieve one of `deductibles`,
                        # `insured_limits` or `retrofitteds` ("s" suffix)
                        value = getattr(asset, name + 's')[lt]
                    record[field] = value
        return assetcol
