#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from openquake.nrmllib.node import Node
from openquake.commonlib.record import Record, Field, Unique, ForeignKey
from openquake.commonlib import valid


# vulnerability records (discrete)

class DiscreteVulnerabilitySet(Record):
    convertername = 'Vulnerability'
    pkey = Unique('vulnerabilitySetID')

    vulnerabilitySetID = Field(str)
    assetCategory = Field(valid.category)
    lossCategory = Field(str)
    IMT = Field(valid.IMTstr)

    def to_node(self):
        node = Node('discreteVulnerabilitySet', dict(
            vulnerabilitySetID=self['vulnerabilitySetID'],
            assetCategory=self['assetCategory'],
            lossCategory=self['lossCategory']))
        node.append(Node('IML', dict(IMT=self['IMT'])))
        return node


class DiscreteVulnerability(Record):
    convertername = 'Vulnerability'
    pkey = Unique('vulnerabilitySetID', 'vulnerabilityFunctionID')
    fkey = ForeignKey(DiscreteVulnerabilitySet.pkey, 'vulnerabilitySetID')

    vulnerabilitySetID = Field(str)
    vulnerabilityFunctionID = Field(str)
    probabilisticDistribution = Field(str)

    def to_node(self):
        node = Node(
            'discreteVulnerability',
            dict(vulnerabilityFunctionID=self['vulnerabilityFunctionID'],
                 probabilisticDistribution=self['probabilisticDistribution']))
        node.append(Node('lossRatio'))
        node.append(Node('coefficientsVariation'))
        return node


class DiscreteVulnerabilityData(Record):
    convertername = 'Vulnerability'
    pkey = Unique('vulnerabilitySetID', 'vulnerabilityFunctionID', 'IML')
    fkey = ForeignKey(DiscreteVulnerability.pkey,
                      'vulnerabilitySetID', 'vulnerabilityFunctionID')

    vulnerabilitySetID = Field(str)
    vulnerabilityFunctionID = Field(str)
    IML = Field(float)
    lossRatio = Field(float)
    coefficientsVariation = Field(float)


# fragility records (discrete)

class FragilityDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('format')

    format = Field(valid.Choice('discrete'))
    description = Field(str)
    limitStates = Field(valid.namelist)

    def to_node(self):
        node = Node('fragilityModel', dict(format=self['format']))
        node.append(Node('description', text=self['description']))
        node.append(Node('limitStates', text=self['limitStates']))
        return node


class FFLimitStateDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('limitState')
    limitState = Field(str)


class FFSetDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('ordinal')

    ordinal = Field(int)
    taxonomy = Field(valid.not_empty)
    noDamageLimit = Field(valid.NoneOr(valid.positivefloat))
    IMT = Field(valid.IMTstr)
    imlUnit = Field(str)

    def to_node(self):
        node = Node('ffs')
        ndl = self['noDamageLimit']
        if ndl:
            node['noDamageLimit'] = ndl
        node.append(Node('taxonomy', text=self['taxonomy']))
        node.append(Node('IML', dict(IMT=self['IMT'],
                                     imlUnit=self['imlUnit'])))
        return node


class FFDataDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('limitState', 'ffs_ordinal', 'iml')

    limitState = Field(str)
    ffs_ordinal = Field(int)
    iml = Field(float)
    poe = Field(valid.probability)


# fragility records (continuous)

class FragilityContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('format')

    format = Field(valid.Choice('continuous'))
    description = Field(str)
    limitStates = Field(valid.namelist)

    def to_node(self):
        node = Node('fragilityModel', dict(format=self['format']))
        node.append(Node('description', text=self['description']))
        node.append(Node('limitStates', text=self['limitStates']))
        return node


class FFLimitStateContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('limitState')
    limitState = Field(str)


class FFSetContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('ordinal')

    ordinal = Field(int)
    taxonomy = Field(valid.not_empty)
    noDamageLimit = Field(valid.NoneOr(valid.positivefloat))
    type = Field(str)
    IMT = Field(str)
    imlUnit = Field(str)
    minIML = Field(float)
    maxIML = Field(float)

    def to_node(self):
        node = Node('ffs')
        node.append(Node('taxonomy', text=self['taxonomy']))
        ndl = self['noDamageLimit']
        if ndl:
            node['noDamageLimit'] = ndl
        typ = self['type']
        if typ:
            node['type'] = typ
        node.append(Node('IML',
                         dict(IMT=self['IMT'], imlUnit=self['imlUnit'],
                              minIML=self['minIML'], maxIML=self['maxIML'])))
        return node


class FFDataContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('limitState', 'ffs_ordinal', 'param')

    limitState = Field(str)
    ffs_ordinal = Field(int)
    param = Field(str)
    value = Field(float)


# location records

class Location(Record):
    convertername = 'Exposure'
    pkey = Unique('id')
    unique = Unique('lon', 'lat')

    id = Field(valid.positiveint)
    lon = Field(valid.longitude)
    lat = Field(valid.latitude)

    def to_node(self):
        return Node('location', dict(lon=self['lon'], lat=self['lat']))


# exposure records

class Exposure(Record):
    convertername = 'Exposure'
    pkey = Unique('id')

    id = Field(valid.not_empty)
    category = Field(valid.category)
    taxonomySource = Field(str)
    description = Field(str)
    area_type = Field(valid.NoneOr(valid.Choice('aggregated', 'per_asset')))
    area_unit = Field(valid.NoneOr(str))
    deductible_is_absolute = Field(valid.NoneOr(valid.boolean))
    insurance_limit_is_absolute = Field(valid.NoneOr(valid.boolean))

    def check_area(self):
        return (self.area_type is None and self.area_unit is None) or \
               (self.area_type is not None and self.area_unit is not None)

    _constraints = [check_area]

    def to_node(self):
        node = Node('exposureModel', dict(
            id=self['id'],
            category=self['category'],
            taxonomySource=self['taxonomySource']))
        node.append(Node('description', text=self['description']))
        if node['category'] == 'buildings':
            conv = Node('conversions')
            conv.append(Node('area', dict(type=self['area_type'],
                                          unit=self['area_unit'])))
            conv.append(Node('costTypes'))
            conv.append(Node('deductible', dict(
                isAbsolute=self['deductible_is_absolute'])))
            conv.append(Node('insuranceLimit', dict(
                isAbsolute=self['insurance_limit_is_absolute'])))
            node.append(conv)
        node.append(Node('assets'))
        return node


class CostType(Record):
    convertername = 'Exposure'
    pkey = Unique('name')

    name = Field(str)
    type = Field(valid.Choice('aggregated', 'per_asset', 'per_area'))
    unit = Field(str)
    retrofittedType = Field(valid.NoneOr(
        valid.Choice('aggregated', 'per_asset', 'per_area')))
    retrofittedUnit = Field(str)

    def to_node(self):
        attr = dict(name=self['name'], type=self['type'], unit=self['unit'])
        if self['retrofittedType']:
            attr['retrofittedType'] = self['retrofittedType']
        if self['retrofittedUnit']:
            attr['retrofittedUnit'] = self['retrofittedUnit']
        return Node('costType', attr)


class Asset(Record):
    convertername = 'Exposure'
    pkey = Unique('asset_ref')

    location_id = Field(valid.positiveint)
    asset_ref = Field(str)
    taxonomy = Field(valid.not_empty)
    number = Field(valid.positivefloat)
    area = Field(valid.NoneOr(valid.positivefloat))

    def to_node(self):
        attr = dict(id=self['asset_ref'],
                    taxonomy=self['taxonomy'],
                    number=self['number'])
        if self['area']:
            attr['area'] = self['area']
        return Node('asset', attr)


class Occupancy(Record):
    convertername = 'Exposure'
    pkey = Unique('asset_ref', 'period')

    asset_ref = Field(str)
    period = Field(str)
    occupants = Field(valid.positivefloat)

    def to_node(self):
        return Node('occupancy', dict(period=self['period'],
                                      occupants=self['occupants']))


class Cost(Record):
    convertername = 'Exposure'
    pkey = Unique('asset_ref', 'type')

    asset_ref = Field(str)
    type = Field(str)
    value = Field(valid.positivefloat)
    retrofitted = Field(valid.NoneOr(valid.positivefloat))
    deductible = Field(valid.NoneOr(valid.positivefloat))
    insurance_limit = Field(valid.NoneOr(valid.positivefloat))

    def to_node(self):
        """
        Here are two examples:

        <cost type="structural" value="150000" deductible=".1"
              insuranceLimit="0.8" retrofitted="109876"/>
        <cost type="non_structural" value="25000" deductible=".09"
              insuranceLimit="0.82"/>
        """
        node = Node('cost', dict(type=self['type'], value=self['value']))
        if self['retrofitted']:
            node['retrofitted'] = self['retrofitted']
        if self['deductible']:
            node['deductible'] = self['deductible']
        if self['insurance_limit']:
            node['insuranceLimit'] = self['insurance_limit']
        return node


# gmf records

class GmfCollection(Record):
    convertername = 'GmfCollection'
    pkey = Unique('sourceModelTreePath', 'gsimTreePath')

    sourceModelTreePath = Field(str)
    gsimTreePath = Field(str)

    def to_node(self):
        return Node('gmfCollection',
                    dict(sourceModelTreePath=self['sourceModelTreePath'],
                         gsimTreePath=self['gsimTreePath']))


class GmfSet(Record):
    convertername = 'GmfCollection'
    pkey = Unique('stochasticEventSetId')

    stochasticEventSetId = Field(int)
    investigationTime = Field(float)

    def to_node(self):
        dic = {}
        if self['stochasticEventSetId'] != '0':
            dic['stochasticEventSetId'] = self['stochasticEventSetId']
        if self[1]:
            dic['investigationTime'] = self['investigationTime']
        return Node('gmfSet', dic)


class Gmf(Record):
    convertername = 'GmfCollection'
    pkey = Unique('stochasticEventSetId', 'imtStr', 'ruptureId')

    stochasticEventSetId = Field(int)
    imtStr = Field(valid.IMTstr)
    ruptureId = Field(str)

    def to_node(self):
        imt = self['imtStr']
        if imt.startswith('SA'):
            attr = dict(IMT='SA', saPeriod=imt[3:-1], saDamping='5.0')
        else:
            attr = dict(IMT=imt)
        rup = self['ruptureId']
        if rup:
            attr['ruptureId'] = rup
        return Node('gmf', attr)


class GmfData(Record):
    convertername = 'GmfCollection'
    pkey = Unique('stochasticEventSetId', 'imtStr', 'ruptureId', 'lon', 'lat')

    stochasticEventSetId = Field(int)
    imtStr = Field(str)
    ruptureId = Field(str)
    lon = Field(float)
    lat = Field(float)
    gmv = Field(float)

    def to_node(self):
        return Node('node', dict(lon=self['lon'],
                                 lat=self['lat'],
                                 gmv=self['gmv']))
