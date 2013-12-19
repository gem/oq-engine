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
from openquake.common.record import Record, Field, Unique, ForeignKey
from openquake.common import valid


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
            vulnerabilitySetID=self[0],
            assetCategory=self[1],
            lossCategory=self[2]))
        node.append(Node('IML', dict(IMT=self[3])))
        return node


class DiscreteVulnerability(Record):
    convertername = 'Vulnerability'
    pkey = Unique('vulnerabilitySetID', 'vulnerabilityFunctionID')
    fkey = ForeignKey(DiscreteVulnerabilitySet.pkey, 'vulnerabilitySetID')

    vulnerabilitySetID = Field(str)
    vulnerabilityFunctionID = Field(str)
    probabilisticDistribution = Field(str)

    def to_node(self):
        node = Node('discreteVulnerability',
                    dict(vulnerabilityFunctionID=self[1],
                         probabilisticDistribution=self[2]))
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

    # some properties useful for plotting the record
    x = property(lambda self: self.IML)
    y = property(lambda self: self.lossRatio)


# fragility records (discrete)

class FragilityDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('format')

    format = Field(valid.Choice('discrete'))
    description = Field(str)
    limitStates = Field(valid.namelist)

    def to_node(self):
        node = Node('fragilityModel', dict(format=self[0]))
        node.append(Node('description', text=self[1]))
        node.append(Node('limitStates', text=self[2]))
        return node


class FFLimitStateDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('limitState')
    limitState = Field(str)


class FFSetDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('ordinal')

    ordinal = Field(int)
    taxonomy = Field(str)
    noDamageLimit = Field(valid.NoneOr(valid.positivefloat))
    IMT = Field(valid.IMTstr)
    imlUnit = Field(str)

    def to_node(self):
        node = Node('ffs')
        ndl = self[2]
        if ndl:
            node['noDamageLimit'] = ndl
        node.append(Node('taxonomy', text=self[1]))
        node.append(Node('IML', dict(IMT=self[3], imlUnit=self[4])))
        return node


class FFDataDiscrete(Record):
    convertername = 'FragilityDiscrete'
    pkey = Unique('limitState', 'ffs_ordinal', 'iml')

    limitState = Field(str)
    ffs_ordinal = Field(int)
    iml = Field(float)
    poe = Field(valid.probability)

    # some properties useful for plotting the record
    x = property(lambda self: self.iml)
    y = property(lambda self: self.poe)


# fragility records (continuous)

class FragilityContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('format')

    format = Field(valid.Choice('continuous'))
    description = Field(str)
    limitStates = Field(valid.namelist)

    def to_node(self):
        node = Node('fragilityModel', dict(format=self[0]))
        node.append(Node('description', text=self[1]))
        node.append(Node('limitStates', text=self[2]))
        return node


class FFLimitStateContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('limitState')
    limitState = Field(str)


class FFSetContinuous(Record):
    convertername = 'FragilityContinuous'
    pkey = Unique('ordinal')

    ordinal = Field(int)
    taxonomy = Field(str)
    noDamageLimit = Field(valid.NoneOr(float))
    type = Field(str)
    IMT = Field(str)
    imlUnit = Field(str)
    minIML = Field(float)
    maxIML = Field(float)

    def to_node(self):
        node = Node('ffs')
        node.append(Node('taxonomy', text=self[1]))
        ndl = self[2]
        if ndl:
            node['noDamageLimit'] = ndl
        typ = self[3]
        if typ:
            node['type'] = typ
        node.append(Node('IML', dict(IMT=self[4], imlUnit=self[5],
                                     minIML=self[6], maxIML=self[7])))
        return node


class FFDContinuos(Record):
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
        return Node('location', dict(lon=self[1], lat=self[2]))


# exposure records

class Exposure(Record):
    convertername = 'Exposure'
    pkey = Unique('id')

    id = Field(str)
    category = Field(valid.category)
    taxonomySource = Field(str)
    description = Field(str)
    area_type = Field(str)
    area_unit = Field(str)
    deductible_is_absolute = Field(bool)
    insurance_limit_is_absolute = Field(bool)

    def to_node(self):
        node = Node('exposureModel', dict(
            id=self[0],
            category=self[1],
            taxonomySource=self[2]))
        node.append(Node('description', text=self[3]))
        if node['category'] == 'buildings':
            conv = Node('conversions')
            conv.append(Node('area', dict(type=self[4], unit=self[5])))
            conv.append(Node('costTypes'))
            conv.append(Node('deductible', dict(isAbsolute=self[6])))
            conv.append(Node('insuranceLimit', dict(isAbsolute=self[7])))
            node.append(conv)
        node.append(Node('assets'))
        return node


class CostType(Record):
    convertername = 'Exposure'
    pkey = Unique('name')

    name = Field(str)
    type = Field(str)
    unit = Field(str)
    retrofittedType = Field(str)
    retrofittedUnit = Field(str)

    def to_node(self):
        attr = dict(name=self[0], type=self[1], unit=self[2])
        if self[3]:
            attr['retrofittedType'] = self[3]
        if self[4]:
            attr['retrofittedUnit'] = self[4]
        return Node('costType', attr)


class Asset(Record):
    convertername = 'Exposure'
    pkey = Unique('asset_ref')

    location_id = Field(valid.positiveint)
    asset_ref = Field(str)
    taxonomy = Field(str)
    number = Field(float)
    area = Field(valid.NoneOr(valid.positivefloat))

    def to_node(self):
        attr = dict(id=self[1], taxonomy=self[2], number=self[3])
        if self[4]:
            attr['area'] = self[4]
        return Node('asset', attr)


class Occupancy(Record):
    convertername = 'Exposure'
    pkey = Unique('asset_ref', 'period')

    asset_ref = Field(str)
    period = Field(str)
    occupants = Field(valid.positivefloat)

    def to_node(self):
        return Node('occupancy', dict(period=self[1], occupants=self[2]))


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
        node = Node('cost', dict(type=self[1], value=self[2]))
        if self[3]:
            node['retrofitted'] = self[3]
        if self[4]:
            node['deductible'] = self[4]
        if self[5]:
            node['insuranceLimit'] = self[5]
        return node


# gmf records

class GmfCollection(Record):
    convertername = 'GmfCollection'
    pkey = Unique('sourceModelTreePath', 'gsimTreePath')

    sourceModelTreePath = Field(str)
    gsimTreePath = Field(str)

    def to_node(self):
        return Node('gmfCollection', dict(sourceModelTreePath=self[0],
                                          gsimTreePath=self[1]))


class GmfSet(Record):
    convertername = 'GmfCollection'
    pkey = Unique('stochasticEventSetId')

    stochasticEventSetId = Field(int)
    investigationTime = Field(float)

    def to_node(self):
        dic = {}
        if self[0] != '0':
            dic['stochasticEventSetId'] = self[0]
        if self[1]:
            dic['investigationTime'] = self[1]
        return Node('gmfSet', dic)


class Gmf(Record):
    convertername = 'GmfCollection'
    pkey = Unique('stochasticEventSetId', 'imtStr', 'ruptureId')

    stochasticEventSetId = Field(int)
    imtStr = Field(valid.IMTstr)
    ruptureId = Field(str)

    def to_node(self):
        imt = self[1]
        if imt.startswith('SA'):
            attr = dict(IMT='SA', saPeriod=imt[3:-1], saDamping='5.0')
        else:
            attr = dict(IMT=imt)
        rup = self[2]
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
        return Node('node', dict(lon=self[3], lat=self[4], gmv=self[5]))
