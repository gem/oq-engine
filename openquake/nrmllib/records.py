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

from openquake.nrmllib.record import Record, Field, Unique
from openquake.nrmllib.node import Node
from openquake.nrmllib import valid


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

    vulnerabilitySetID = Field(str)
    vulnerabilityFunctionID = Field(str)
    IML = Field(float)
    lossRatio = Field(float)
    coefficientsVariation = Field(float)


# fragility records

class Fragility(Record):
    convertername = 'Fragility'
    pkey = Unique('format')

    format = Field(valid.Choice('discrete', 'continuous'))
    description = Field(str)
    limitStates = Field(valid.namelist)

    def to_node(self):
        node = Node('fragilityModel', dict(format=self[0]))
        node.append(Node('description', text=self[1]))
        node.append(Node('limitStates', text=self[2]))
        return node


class FFSetDiscrete(Record):
    convertername = 'Fragility'
    pkey = Unique('ordinal')

    ordinal = Field(int)
    taxonomy = Field(str)
    noDamageLimit = Field(float)
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


class FFSetContinuous(Record):
    convertername = 'Fragility'
    pkey = Unique('ordinal')

    ordinal = Field(int)
    taxonomy = Field(str)
    noDamageLimit = Field(float)
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


class FFDataDiscrete(Record):
    convertername = 'Fragility'
    pkey = Unique('ffs_ordinal', 'limitState', 'iml')

    ffs_ordinal = Field(int)
    limitState = Field(str)
    iml = Field(float)
    poe = Field(valid.probability)


class FFDContinuos(Record):
    convertername = 'Fragility'
    pkey = Unique('ffs_ordinal', 'limitState', 'param')

    ffs_ordinal = Field(int)
    limitState = Field(str)
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


class AssetPopulation(Record):
    convertername = 'Exposure'
    pkey = Unique('id')

    id = Field(str)
    taxonomy = Field(str)
    number = Field(float)
    location = Field(int)

    def to_node(self):
        return Node('asset', dict(id=self[0], taxonomy=self[1],
                                  number=self[2]))


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
