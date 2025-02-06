# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
import time
import csv
import os

import numpy
import pandas

from openquake.baselib import hdf5, general
from openquake.baselib.node import Node, context
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import valid, nrml, geo, InvalidFile
from openquake.hazardlib.geo.utils import SiteAssociationError

U8 = numpy.uint8
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
U64 = numpy.uint64
TWO16 = 2 ** 16
TWO32 = 2 ** 32
by_taxonomy = operator.attrgetter('taxonomy')
ae = numpy.testing.assert_equal
OCC_FIELDS = ('day', 'night', 'transit')
ANR_FIELDS = {'area', 'number', 'residents'}
VAL_FIELDS = {'structural', 'nonstructural', 'contents',
              'business_interruption'}


def add_dupl_fields(df, oqfields):
    """
    Add duplicated fields to the DataFrame, if any.

    :param df: exposure dataframe
    :param oqfields: dictionary csvfield -> oqfields
    """
    columns = set(df.columns)
    for f in oqfields:
        if len(oqfields[f]) > 1:
            okfield = (oqfields[f] & columns).pop()
            for oqfield in oqfields[f]:
                if oqfield != okfield:
                    df[oqfield] = df[okfield]


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
    occfields = [col for col in adf.columns if col[10:] in OCC_FIELDS]
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
    def __init__(self, cost_types, units, tagi={'taxonomy': 0}):
        for ct in cost_types.values():
            assert ct in ('aggregated', 'per_asset', 'per_area'), ct
        self.cost_types = cost_types
        self.units = units
        self.tagi = tagi

    def update(self, assetcol):
        for name in assetcol.dtype.names:
            if name.startswith('value-') and name not in (
                    'value-area', 'value-number', 'value-residents'):
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
            area_type = self.cost_types['area']
            if area_type == "aggregated":
                return cost * area
            elif area_type == "per_asset":
                return cost * area * number
        # this should never happen
        raise RuntimeError('Unable to compute cost for %r' % loss_type)

    def get_units(self, loss_types):
        """
        :param: a list of loss types
        :returns: a string of space-separated units
        """
        lst = []
        for lt in loss_types:
            if lt.endswith('_ins'):
                lt = lt[:-4]  # rstrip _ins
            if lt == 'number':
                unit = 'units'
            elif lt in ('occupants', 'residents'):
                unit = 'people'
            elif lt == 'area':
                # tested in event_based_risk/case_8
                # NB: the Global Risk Model use SQM always, hence the default
                unit = self.units.get(lt, 'SQM')
            else:
                unit = self.units[lt]
            lst.append(unit)
        return ' '.join(lst)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, vars(self))


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

    def get_tagi(self, tagname, assets_df):
        """
        :param tagname: name of a tag
        :param assets_df: DataFrame of assets
        :returns: indices associated to the tag, from 1 to num_tags
        """
        vals = assets_df[tagname].to_numpy()
        uniq, inv = numpy.unique(vals, return_inverse=True)
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
            setattr(self, tagname + '_idx', {'?': 0})
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
    """
    Wrapper over an array of assets
    """
    def __init__(self, exposure, sitecol, time_event, aggregate_by):
        self.occupancy_periods = ' '.join(exposure.occupancy_periods)
        self.array = exposure.assets
        self.tagcol = exposure.tagcol
        self.time_event = time_event
        self.tot_sites = len(sitecol.complete)
        self.update_tagcol(aggregate_by)
        exp_periods = exposure.occupancy_periods
        if self.occupancy_periods and not exp_periods:
            logging.warning('Missing <occupancyPeriods>%s</occupancyPeriods> '
                            'in the exposure', self.occupancy_periods)
        elif self.occupancy_periods.split() != exp_periods:
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

    def get_taxidx(self):
        """
        :returns: dictionary taxonomy string -> taxonomy index starting from 1
        """
        taxonomies = self.tagcol.taxonomy[1:]
        return {taxo: taxi for taxi, taxo in enumerate(taxonomies, 1)
                if taxi in numpy.unique(self['taxonomy'])}

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
            self.array = numpy.concatenate(arrays, dtype=arr.dtype)
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


# ########################### exposure ############################ #

cost_type_dt = numpy.dtype([('name', hdf5.vstr),
                            ('type', hdf5.vstr),
                            ('unit', hdf5.vstr)])


# The fields in the exposure are complicated. For the global
# risk model you will have things like the following:
# fields = {'ASSET_ID', 'BUILDINGS', 'COST_CONTENTS_USD',
#           'COST_NONSTRUCTURAL_USD', 'COST_STRUCTURAL_USD', 'LATITUDE',
#           'LONGITUDE', 'OCCUPANTS_PER_ASSET', 'TAXONOMY', 'TOTAL_AREA_SQM',
#           'area', 'business_interruption', 'contents', 'day', 'night',
#           'nonstructural', 'number', 'residents', 'structural', 'transit'}
# ANR_FIELDS = {'area', 'number', 'residents'}
# OCC_FIELDS = {'day', 'night', 'transit'}
# VAL_FIELDS = {'structural', 'business_interruption', 'nonstructural',
#               'contents'}
# others = {'ASSET_ID', 'BUILDINGS', 'COST_CONTENTS_USD',
#           'COST_NONSTRUCTURAL_USD', 'COST_STRUCTURAL_USD', 'LATITUDE',
#           'LONGITUDE', 'OCCUPANTS_PER_ASSET', 'TAXONOMY', 'TOTAL_AREA_SQM'}
def get_other_fields(fields):
    others = (set(fields) - set(ANR_FIELDS) - set(OCC_FIELDS) - set(VAL_FIELDS)
              - {'deduc'})
    return others


def _get_exposure(fname, stop=None):
    # returns (Exposure instance, asset nodes)
    [xml] = nrml.read(fname, stop=stop)
    if not xml.tag.endswith('exposureModel'):
        raise InvalidFile('%s: expected exposureModel, got %s' %
                          (fname, xml.tag))
    try:
        conversions = xml.conversions
    except AttributeError:
        conversions = Node('conversions', nodes=[Node('costTypes', [])])
    # input_field -> oq_field
    pairs = [(f, 'value-' + f) for f in ANR_FIELDS | VAL_FIELDS] + [
        (f, 'occupants_' + f) for f in OCC_FIELDS]
    try:
        for node in xml.exposureFields:
            noq = node['oq']
            if noq in ANR_FIELDS | VAL_FIELDS:
                pairs.append((node['input'], 'value-' + noq))
            elif noq in OCC_FIELDS:
                pairs.append((node['input'], 'occupants_' + noq))
            else:
                pairs.append((node['input'], noq))
    except AttributeError:
        pass  # no fieldmap
    try:
        occupancy_periods = xml.occupancyPeriods.text.split()
    except AttributeError:
        occupancy_periods = []
    try:
        tagNames = xml.tagNames
    except AttributeError:
        tagNames = Node('tagNames', text='')
    tagnames = ~tagNames or []
    if set(tagnames) & {'taxonomy', 'exposure'}:
        raise InvalidFile('taxonomy and exposure are reserved names '
                          'you cannot use it in <tagNames>: %s' % fname)
    tagnames.insert(0, 'taxonomy')

    # read the cost types and make some check
    cost_types = []
    for ct in conversions.costTypes:
        with context(fname, ct):
            cost_types.append(
                (ct['name'], valid.cost_type_type(ct['type']), ct['unit']))
    try:
        conv_area = conversions.area
    except AttributeError:
        # the <area> tag is not mandatory
        pass
    else:
        try:
            conv_area_unit = conv_area['unit']
        except KeyError as exc:
            raise KeyError(
                f"The 'unit' property of the <area> tag is missing"
                f" in {fname}") from exc
        else:
            cost_types.append(
                ('area', valid.cost_type_type(conv_area['type']),
                 conv_area_unit))
    if 'occupants' in cost_types:
        cost_types.append(('occupants', 'per_area', 'people'))
    cost_types.sort(key=operator.itemgetter(0))
    cost_types = numpy.array(cost_types, cost_type_dt)
    cc = CostCalculator(
        {}, {}, {name: i for i, name in enumerate(tagnames)})
    for ct in cost_types:
        name = ct['name']  # structural, nonstructural, ...
        cc.cost_types[name] = ct['type']  # aggregated, per_asset, per_area
        cc.units[name] = ct['unit']
    exp = Exposure(occupancy_periods, [], cc, TagCollection(tagnames), pairs)
    assets_text = xml.assets.text.strip()
    if assets_text:
        # the <assets> tag contains a list of file names
        dirname = os.path.dirname(fname)
        exp.datafiles = [os.path.join(dirname, f) for f in assets_text.split()]
    else:
        exp.datafiles = []
    return exp, xml.assets


def _minimal_tagcol(fnames):
    tagnames = None
    for exp in Exposure.read_headers(fnames):
        if tagnames is None:
            tagnames = set(exp.tagcol.tagnames)
        else:
            tagnames &= set(exp.tagcol.tagnames)
    tagnames -= {'taxonomy'}
    if len(fnames) > 1:
        alltags = ['taxonomy'] + list(tagnames) + ['exposure']
    else:
        alltags = ['taxonomy'] + list(tagnames)
    return TagCollection(alltags)


def set_attrib(asset):
    retrofitted = False
    for cost in getattr(asset, 'costs', []):
        asset.attrib[cost['type']] = cost['value']
        if 'retrofitted' in cost.attrib:
            retrofitted = float(cost['retrofitted'])
    return retrofitted


def assets2df(asset_nodes, fields, ignore_missing_costs):
    """
    :returns: a DataFrame of assets from the asset nodes
    """
    first_asset = asset_nodes[0]
    for occ in getattr(first_asset, 'occupancies', []):
        name = 'occupants_' + occ['period'].lower()
        if name not in fields:
            fields.append(name)
    dtlist = [(f, object) for f in fields]
    nodes = list(asset_nodes)
    for i, asset in enumerate(nodes):
        retrofitted = set_attrib(asset)
        if i == 0:   # first asset
            if retrofitted:
                dtlist.append(('retrofitted', object))
            array = numpy.zeros(len(nodes), dtlist)
        rec = array[i]
        # fix asset.attrib
        for occ in getattr(asset, 'occupancies', []):
            ofield = 'occupants_' + occ['period'].lower()
            asset.attrib[ofield] = occ['occupants']
        if retrofitted:
            rec['retrofitted'] = retrofitted
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
                        raise KeyError('Missing type="%s" for asset %s' %
                                       (cost, rec['id']))
            else:
                rec[field] = asset.attrib.get(field, '?')
    return pandas.DataFrame({f: array[f] for f, dt in dtlist}).set_index('id')


def check_exposure_for_infr_conn_analysis(df, fname):

    exposure_columns = list(df.columns)

    # Raise an error if any of those columns is present
    mandatory_columns = ['purpose', 'start_node', 'end_node']
    mandatory_columns_not_found = []
    for mandatory_column in mandatory_columns:
        if mandatory_column not in exposure_columns:
            mandatory_columns_not_found.append(mandatory_column)
    if mandatory_columns_not_found:
        raise InvalidFile(
            f'The following mandatory columns are missing in the'
            f' exposure "{fname}": {mandatory_columns_not_found}')

    # Log a warning if node weights are present and they are not all '1',
    # because handling weights in the nodes is not implemented yet
    if 'weight' in exposure_columns:  # 'weight' is not mandatory
        if not (df[df.type.str.lower() == 'node']['weight'] == '1').all():
            logging.warning(
                f'Node weights different from 1 present in {fname} will'
                f' be ignored. Handling node weights is not implemented yet.')

    # Raise an error if the column 'graphtype' is present and it does not
    # contain a unique value
    if 'graphtype' in exposure_columns:  # 'graphtype' is not mandatory
        if not (df['graphtype'] == df['graphtype'][0]).all():
            raise InvalidFile(
                'The column "graphtype" of "%s" must contain all equal values.'
                % fname)

    # Raise an error if 'purpose' contains at least one 'TAZ' value and at
    # least a value in ['source'. 'demand']
    purpose_values = set(df['purpose'].str.lower())
    if 'taz' in purpose_values and ('source' in purpose_values
                                    or 'demand' in purpose_values):
        raise InvalidFile(
            f'Column "purpose" of {fname} can not contain at the same time'
            f' the value "TAZ" and either "source" or "demand".')


def read_exp_df(fname, calculation_mode='', ignore_missing_costs=(),
                check_dupl=True, asset_prefix='',
                tagcol=None, errors=None, infr_conn_analysis=False,
                aggregate_by=None, monitor=None):
    # NB: errors is not None only for scenario_test/case_17
    logging.info('Reading %s', fname)
    exposure, assetnodes = _get_exposure(fname)
    if tagcol:
        exposure.tagcol = tagcol
    if assetnodes:
        df = assets2df(
            assetnodes, exposure._csv_header(), ignore_missing_costs)
        fname_dfs = [(fname, df)]
    else:
        fname_dfs = exposure._read_csv(errors)
    # loop on each CSV file associated to exposure.xml
    dfs = []
    for fname, df in fname_dfs:
        if len(df) == 0 and errors != 'ignore':
            raise InvalidFile('%s is empty' % fname)
        elif asset_prefix:  # multiple exposure files
            df['exposure'] = asset_prefix[:-1]
        names = df.columns
        df = df.reset_index()
        occupants = any(n.startswith('occupants_') for n in names)
        if occupants and 'occupants_avg' not in names:
            df['occupants_avg'] = calc_occupants_avg(df)
        if 'retrofitted' in df.columns:
            df['retrofitted'] = exposure.cost_calculator(
                'structural', {'value-structural': df.retrofitted,
                               'value-number': df['value-number']})
        if infr_conn_analysis:
            check_exposure_for_infr_conn_analysis(df, fname)
        if aggregate_by:
            for taglist in aggregate_by:
                for tag in taglist:
                    if tag == 'site_id':
                        # 'site_id' is added later in Exposure.init
                        continue
                    if (tag not in df.columns
                            and f'value-{tag}' not in df.columns):
                        raise InvalidFile(f'Missing tag "{tag}" in {fname}')
        df['id'] = asset_prefix + df.id
        dfs.append(df)

    assets_df = pandas.concat(dfs)
    del fname_dfs  # save memory
    del dfs  # save memory

    # check_dupl is False only in oq prepare_site_model since
    # in that case we are only interested in the asset locations
    if check_dupl:
        u, c = numpy.unique(assets_df['id'], return_counts=1)
        dupl = u[c > 1]
        if len(dupl):
            raise nrml.DuplicatedID(dupl)

    return exposure, assets_df


# used in impact calculations
def impact_read_assets(h5, start, stop):
    """
    Builds a DataFrame of assets by reading the global exposure file
    """
    group = h5['assets']
    dic = {}
    TAGS = {'ID_0': numpy.array(decode(h5['tagcol/ID_0'][:])),
            'ID_1': numpy.array(decode(h5['tagcol/ID_1'][:])),
            'OCCUPANCY': numpy.array(decode(h5['tagcol/OCCUPANCY'][:])),
            'TAXONOMY': numpy.array(decode(h5['tagcol/taxonomy'][:]))}
    for field in group:
        if field == field.upper():
            dic[field] = arr = group[field][start:stop]
            if field in TAGS:
                # go back from indices to strings
                dic[field] = TAGS[field][arr]
    df = pandas.DataFrame(dic)
    df['occupants_avg'] = (df.OCCUPANTS_PER_ASSET_DAY +
                           df.OCCUPANTS_PER_ASSET_NIGHT +
                           df.OCCUPANTS_PER_ASSET_TRANSIT) / 3
    return df


class Exposure(object):
    """
    A class to read the exposure from XML/CSV files
    """
    fields = ['occupancy_periods', 'assets',
              'cost_calculator', 'tagcol', 'pairs']

    @property
    def loss_types(self):
        return sorted(self.cost_calculator.cost_types)

    def __toh5__(self):
        cc = self.cost_calculator
        loss_types = sorted(cc.cost_types)
        dt = numpy.dtype([('loss_type', hdf5.vstr), ('cost_type', hdf5.vstr),
                          ('unit', hdf5.vstr)])
        array = numpy.zeros(len(loss_types), dt)
        array['loss_type'] = loss_types
        array['cost_type'] = [cc.cost_types[lt] for lt in loss_types]
        array['unit'] = [cc.units[lt] for lt in loss_types]
        attrs = dict(
            occupancy_periods=hdf5.array_of_vstr(self.occupancy_periods),
            pairs=self.pairs)
        return array, attrs

    def __fromh5__(self, array, attrs):
        vars(self).update(attrs)
        cc = self.cost_calculator = object.__new__(CostCalculator)
        # in exposure.hdf5 `loss_types` is an attribute
        loss_types = attrs.get('loss_types')
        if loss_types is None:
            # for engine version >= 3.22
            loss_types = decode(array['loss_type'])
        cc.cost_types = dict(zip(loss_types, decode(array['cost_type'])))
        cc.units = dict(zip(self.loss_types, decode(array['unit'])))

    @staticmethod
    def check(fname):
        exp = Exposure.read_all([fname])
        err = []
        for asset in exp.assets:
            if asset['value-number'] > 65535:
                err.append('Asset %s has number %s > 65535' %
                           (asset['id'].decode('utf8'), asset['value-number']))
        return '\n'.join(err)

    @staticmethod
    def read_around(exposure_hdf5, gh3s):
        """
        Read the global exposure in HDF5 format and returns the subset
        specified by the given geohashes.
        """
        with hdf5.File(exposure_hdf5) as f:
            exp = f['exposure']
            sbg = f['assets/slice_by_gh3'][:]
            slices = sbg[numpy.isin(sbg['gh3'], gh3s)]
            if len(slices) == 0:
                raise SiteAssociationError(
                    'There are no assets within the maximum_distance')
            assets_df = pandas.concat(
                impact_read_assets(f, start, stop)
                for gh3, start, stop in slices)
            tagcol = f['tagcol']
            # tagnames = ['taxonomy', 'ID_0', 'ID_1', 'OCCUPANCY']
            exp.tagcol = TagCollection(tagcol.tagnames)
        rename = dict(exp.pairs)
        rename['TAXONOMY'] = 'taxonomy'
        for f in ANR_FIELDS:
            rename[f] = 'value-' + f
        for f in OCC_FIELDS:
            rename[f] = 'occupants_' + f
        adf = assets_df.rename(columns=rename)
        exp.build_mesh(adf)
        return exp

    @staticmethod
    def read_all(fnames, calculation_mode='', ignore_missing_costs=(),
                 check_dupl=True, tagcol=None, errors=None,
                 infr_conn_analysis=False, aggregate_by=None):
        """
        :returns: an :class:`Exposure` instance keeping all the assets in
            memory
        """
        allargs = []
        tagcol = _minimal_tagcol(fnames)
        for i, fname in enumerate(fnames, 1):
            if len(fnames) > 1:
                # multiple exposure.xml files, add a prefix
                # this is tested in oq-risk-tests/old_hazard
                prefix = 'E%02d_' % i
            else:
                prefix = ''
            allargs.append((fname, calculation_mode, ignore_missing_costs,
                            check_dupl, prefix, tagcol, errors,
                            infr_conn_analysis, aggregate_by))
        exp = None
        dfs = []
        for exposure, df in itertools.starmap(read_exp_df, allargs):
            dfs.append(df)
            if exp is None:  # first time
                exp = exposure
                exp.description = 'Composite exposure[%d]' % len(fnames)
            else:
                cc = exposure.cost_calculator
                ae(cc.cost_types, exp.cost_calculator.cost_types)
                ae(exposure.occupancy_periods, exp.occupancy_periods)
        exp.exposures = [os.path.splitext(os.path.basename(f))[0]
                         for f in fnames]
        assets_df = pandas.concat(dfs)
        del dfs  # save memory
        exp.build_mesh(assets_df)
        return exp

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
        self.fieldmap = dict(self.pairs)  # inp -> oq

    def build_mesh(self, assets_df):
        """
        Set the attributes .mesh, .assets, .loss_types, .occupancy_periods
        """
        t0 = time.time()
        vfields = []
        ofields = []
        missing = VAL_FIELDS - set(self.cost_calculator.cost_types)
        for name in assets_df.columns:
            if name.startswith('occupants_'):
                period = name.split('_', 1)[1]
                # see scenario_risk test_case_2d
                if period != 'avg':
                    ofields.append(period)
                vfields.append(name)
            elif name.startswith('value-'):
                field = name[6:]
                if field not in missing:
                    vfields.append(name)
            elif name in self.tagcol.tagnames:
                assets_df[name] = self.tagcol.get_tagi(name, assets_df)

        assets_df.sort_values(['lon', 'lat'], inplace=True)
        ll = numpy.zeros((len(assets_df), 2))
        ll[:, 0] = assets_df['lon']
        ll[:, 1] = assets_df['lat']
        ll, sids = numpy.unique(ll, return_inverse=1, axis=0)
        assets_df['site_id'] = sids
        mesh = geo.Mesh(ll[:, 0], ll[:, 1])
        logging.info(
            'Inferred exposure mesh in %.2f seconds', time.time() - t0)

        names = set(assets_df.columns)
        # vfields can be ['value-business_interruption', 'value-contents',
        # 'value-nonstructural', 'occupants_avg', 'occupants_day',
        # 'occupants_night', 'occupants_transit']
        retro = ['retrofitted'] if 'retrofitted' in names else []
        float_fields = vfields + ['ideductible'] + retro
        int_fields = [(str(name), U32) for name in self.tagcol.tagnames
                      if name not in ('id', 'site_id')]
        asset_dt = numpy.dtype(
            [('id', (numpy.bytes_, valid.ASSET_ID_LENGTH)),
             ('ordinal', U32), ('lon', F32), ('lat', F32),
             ('site_id', U32)] + [
                 (str(name), F32) for name in float_fields] + int_fields)
        num_assets = len(assets_df)
        array = numpy.zeros(num_assets, asset_dt)
        fields = set(asset_dt.fields) - {'ordinal'}
        for field in fields & names:
            array[field] = assets_df[field]
        self.cost_calculator.update(array)
        self.mesh = mesh
        self.assets = array
        #self.loss_types = vfields
        self.occupancy_periods = ofields

    def _csv_header(self, value='value-', occupants='occupants_'):
        """
        Extract the expected CSV header from the exposure metadata
        """
        fields = ['id', value + 'number', 'taxonomy', 'lon', 'lat']
        cc = self.cost_calculator
        for name in cc.cost_types:
            fields.append(value + name)
        if 'per_area' in cc.cost_types.values():
            fields.append(value + 'area')
        for op in self.occupancy_periods:
            fields.append(occupants + op)
        fields.extend(self.tagcol.tagnames)
        wrong = get_case_similar(set(fields))
        if wrong:
            raise InvalidFile('Found case-duplicated fields %s in %s' %
                              (wrong, self.datafiles))
        return sorted('value-' + f if f in ANR_FIELDS | VAL_FIELDS else f
                      for f in set(fields))

    def _read_csv(self, errors=None):
        """
        :yields: asset nodes
        """
        expected_header = set(self._csv_header(''))
        floatfields = set()
        strfields = self.tagcol.tagnames + ['id']
        oqfields = general.AccumDict(accum=set())
        for csvfield, oqfield in self.pairs:
            oqfields[csvfield].add(oqfield)
        other_fields = get_other_fields(self.fieldmap)
        for fname in self.datafiles:
            with open(fname, encoding='utf-8-sig', errors=errors) as f:
                try:
                    fields = next(csv.reader(f))
                except UnicodeDecodeError:
                    msg = ("%s is not encoded as UTF-8\ntry oq shell "
                           "and then o.fix_latin1('%s')\nor set "
                           "ignore_encoding_errors=true" % (fname, fname))
                    raise RuntimeError(msg)
                for inp in other_fields:
                    if inp not in fields:
                        raise InvalidFile('%s: missing field %s, declared in '
                                          'the XML file' % (fname, inp))
                header = set()
                for f in fields:
                    header.update(oqfields.get(f, [f]))
                for field in fields:
                    if field not in strfields:
                        floatfields.add(field)
                missing = expected_header - header - {'exposure'}
                if len(header) < len(fields):
                    raise InvalidFile(
                        '%s: expected %d fields in %s, got %d' %
                        (fname, len(fields), header, len(header)))
                elif missing:
                    raise InvalidFile('%s: missing %s' % (fname, missing))
        conv = {'lon': float, 'lat': float, 'number': float, 'area': float,
                'residents': float, 'retrofitted': float, 'ideductible': float,
                'occupants_day': float, 'occupants_night': float,
                'occupants_transit': float, None: object}
        for f in strfields:
            conv[f] = str
        for inp, oq in self.fieldmap.items():
            if oq in conv:
                conv[inp] = conv[oq]
            elif oq not in strfields:
                conv[inp] = float
        rename = self.fieldmap.copy()
        for f in ANR_FIELDS:
            rename[f] = 'value-' + f
        for f in OCC_FIELDS:
            rename[f] = 'occupants_' + f
        for fname in self.datafiles:
            t0 = time.time()
            df = hdf5.read_csv(fname, conv, rename, errors=errors, index='id')
            asset = os.environ.get('OQ_DEBUG_ASSET')
            if asset:
                df = df[df.index == asset]
                if len(df) == 0:
                    continue
            add_dupl_fields(df, oqfields)
            df['lon'] = numpy.round(df.lon, 5)
            df['lat'] = numpy.round(df.lat, 5)
            sa = float(os.environ.get('OQ_SAMPLE_ASSETS', 0))
            if sa:
                df = general.random_filter(df, sa)
            logging.info('Read {:_d} assets in {:.2f}s from {}'.format(
                len(df), time.time() - t0, fname))
            yield fname, df

    def associate(self, haz_sitecol, haz_distance, region=None):
        """
        Associate the exposure to the given site collection within
        the given distance.

        :returns: filtered site collection, discarded assets
        """
        return geo.utils._GeographicObjects(
            haz_sitecol).assoc2(self, haz_distance, region, 'filter')

    def __repr__(self):
        try:
            num_assets = len(self.assets)
        except AttributeError:
            num_assets = '?'
        return '<%s with %s assets>' % (self.__class__.__name__, num_assets)
