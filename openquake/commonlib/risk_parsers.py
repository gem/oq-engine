# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
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

"""
Module containing parsers for risk input artifacts.
"""
from openquake.commonlib.node import iterparse
from collections import namedtuple

from openquake.commonlib import nrml

NRML = "{%s}" % nrml.NAMESPACE
GML = "{%s}" % nrml.GML_NAMESPACE

AssetData = namedtuple(
    "AssetData",
    "exposure_metadata site asset_ref taxonomy area number costs occupancy")
Site = namedtuple("Site", "longitude latitude")
ExposureMetadata = namedtuple(
    "ExposureMetadata",
    "exposure_id taxonomy_source asset_category description conversions")


class Conversions(object):
    def __init__(self, cost_types, area_type, area_unit,
                 deductible_is_absolute, insurance_limit_is_absolute):
        self.cost_types = cost_types
        self.area_type = area_type
        self.area_unit = area_unit
        self.deductible_is_absolute = deductible_is_absolute
        self.insurance_limit_is_absolute = insurance_limit_is_absolute

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, cs):
        return (
            self.cost_types == cs.cost_types and
            self.area_type == cs.area_type and
            self.area_unit == cs.area_unit and
            self.deductible_is_absolute == cs.deductible_is_absolute and
            self.insurance_limit_is_absolute == cs.insurance_limit_is_absolute)


CostType = namedtuple(
    "CostType",
    "name conversion_type unit retrofitted_type retrofitted_unit")
Cost = namedtuple("Cost", "cost_type value retrofitted deductible limit")
Occupancy = namedtuple("Occupancy", "occupants period")


# TODO: this class will disappear soon, see
# https://bugs.launchpad.net/oq-engine/+bug/1380465
class ExposureModelParser(object):
    """
    Exposure model parser. This class is implemented as a generator.

    For each `asset` element in the parsed document,
    it yields an `AssetData` instance

    :param source:
        Filename or file-like object containing the XML data.
    """

    def __init__(self, source):
        self._source = source

        # contains the data of the node currently parsed.
        self._meta = None

    def __iter__(self):
        """
        Parse the document iteratively.
        """
        for event, element in iterparse(self._source, events=('start', 'end')):

            # exposure metadata
            if event == 'start' and element.tag == '%sexposureModel' % NRML:
                desc = element.find('%sdescription' % NRML)
                if desc is not None:
                    desc = desc.text
                else:
                    desc = ""

                self._meta = ExposureMetadata(
                    exposure_id=element.get('id'),
                    description=desc,
                    taxonomy_source=element.get('taxonomySource'),
                    asset_category=str(element.get('category')),
                    conversions=Conversions(
                        cost_types=[], area_type=None, area_unit=None,
                        deductible_is_absolute=True,
                        insurance_limit_is_absolute=True))

            # conversions
            if event == 'start' and element.tag == "%sarea" % NRML:
                self._meta.conversions.area_type = element.get('type')
                self._meta.conversions.area_unit = element.get('unit')
            elif event == 'start' and element.tag == "%sdeductible" % NRML:
                self._meta.conversions.deductible_is_absolute = not (
                    element.get('isAbsolute', "false") == "false")
            elif event == 'start' and element.tag == "%sinsuranceLimit" % NRML:
                self._meta.conversions.insurance_limit_is_absolute = not (
                    element.get('isAbsolute', "false") == "false")
            elif event == 'start' and element.tag == "%scostType" % NRML:
                self._meta.conversions.cost_types.append(
                    CostType(
                        name=element.get('name'),
                        conversion_type=element.get('type'),
                        unit=element.get('unit'),
                        retrofitted_type=element.get('retrofittedType'),
                        retrofitted_unit=element.get('retrofittedUnit')))

            # asset data
            elif event == 'end' and element.tag == '%sasset' % NRML:
                if element.get('area') is not None:
                    area = float(element.get('area'))
                else:
                    area = None

                if element.get('number') is not None:
                    number = float(element.get('number'))
                else:
                    number = None

                point_elem = element.find('%slocation' % NRML)

                site_data = AssetData(
                    exposure_metadata=self._meta,
                    site=Site(float(point_elem.get("lon")),
                              float(point_elem.get("lat"))),
                    asset_ref=element.get('id'),
                    taxonomy=element.get('taxonomy'),
                    area=area,
                    number=number,
                    costs=_to_costs(element),
                    occupancy=_to_occupancy(element))
                del element

                yield site_data


def _to_occupancy(element):
    """
    Convert the 'occupancy' tags to named tuples.

    We want to extract the values of <occupancies>. We expect the node
    to have child elements structured like this:

    <occupancy occupants="100" period="day"/>
    <occupancy occupants="50" period="night"/>
    ...
    """

    occupancy_data = []
    for otag in element.findall('.//%soccupancy' % NRML):
        occupancy_data.append(Occupancy(
            float(otag.attrib['occupants']),
            otag.attrib["period"]))
    return occupancy_data


def _to_costs(element):
    """
    Convert the 'cost' elements to named tuples.
    """

    costs = []
    for otag in element.findall('.//%scost' % NRML):
        retrofitted = otag.get('retrofitted')
        deductible = otag.get('deductible')
        limit = otag.get('insuranceLimit')

        if retrofitted is not None:
            retrofitted = float(retrofitted)
        if deductible is not None:
            deductible = float(deductible)
        if limit is not None:
            limit = float(limit)

        costs.append(Cost(
            otag.attrib['type'],
            float(otag.attrib['value']),
            retrofitted, deductible, limit))

    return costs
