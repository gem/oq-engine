# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Module containing parsers for risk input artifacts.
"""

from lxml import etree
from collections import namedtuple

import openquake.nrmllib

NRML = "{%s}" % openquake.nrmllib.NAMESPACE
GML = "{%s}" % openquake.nrmllib.GML_NAMESPACE

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
        openquake.nrmllib.assert_valid(self._source)

        # contains the data of the node currently parsed.
        self._meta = None

    def __iter__(self):
        for i in self._parse():
            yield i

    def _parse(self):
        """
        Parse the document iteratively.
        """

        schema = etree.XMLSchema(etree.parse(
            openquake.nrmllib.nrml_schema_file()))

        for event, element in etree.iterparse(
                self._source, events=('start', 'end'), schema=schema):

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
    Convert the 'occupants' tags to named tuples.

    We want to extract the value of <occupants>. We expect the input
    element to be an 'assetDefinition' and have a child element
    structured like this:

    <occupants description="day">245</occupants>
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


class VulnerabilityModelParser(object):
    """
    Vulnerability model parser. This class is implemented as a generator.

    For each `discreteVulnerability` element in the parsed document,
    it yields a dictionary containing the function attributes.

    :param source:
        Filename or file-like object containing the XML data.
    """

    def __init__(self, source):
        self._source = source
        openquake.nrmllib.assert_valid(self._source)

        self._vulnerability_model = etree.parse(self._source).getroot()

    def __iter__(self):
        """
        Parse the vulnerability model.
        """

        for vulnerability_set in self._vulnerability_model.findall(
                ".//%sdiscreteVulnerabilitySet" % NRML):

            vulnerability_function = self._parse_set_attributes(
                vulnerability_set)

            for vf in vulnerability_set.findall(
                    ".//%sdiscreteVulnerability" % NRML):

                loss_ratios = [float(x) for x in vf.find(
                    "%slossRatio" % NRML).text.strip().split()]

                coefficients_variation = [float(x) for x in vf.find(
                    "%scoefficientsVariation" % NRML).text.strip().split()]

                vulnerability_function["ID"] = vf.attrib[
                    "vulnerabilityFunctionID"]

                vulnerability_function["probabilisticDistribution"] = \
                    vf.attrib["probabilisticDistribution"]

                vulnerability_function["lossRatio"] = loss_ratios
                vulnerability_function["coefficientsVariation"] = \
                    coefficients_variation

                yield dict(vulnerability_function)

    @staticmethod
    def _parse_set_attributes(vset):
        """
        Extract the attributes common to all the vulnerability functions
        belonging to the given set.
        """

        attrs = dict()
        imls = vset.find(".//%sIML" % NRML)

        attrs["IMT"] = imls.attrib["IMT"]
        attrs["IML"] = [float(x) for x in imls.text.strip().split()]

        attrs["lossCategory"] = vset.attrib["lossCategory"]
        attrs["assetCategory"] = vset.attrib["assetCategory"]
        attrs["vulnerabilitySetID"] = vset.attrib["vulnerabilitySetID"]

        return attrs


def find(tag, elem):
    "Find all the subelements matching the given tag"
    return elem.findall(NRML + tag, elem)


def findone(tag, elem, default=None):
    """
    Find the unique subelement matching the given tag. Raise ValueError
    if there are too many elements and returns the default if there is
    no match.
    """
    elems = elem.findall(NRML + tag, elem)
    n = len(elems)
    if n == 0:  # not found
        return default
    if n > 1:
        raise ValueError('Found %d elements of kind %s, expected one'
                         % (n, tag))
    return elems[0]


class FragilityModelParser(object):
    """
    Fragility model parser. This class is implemented as a generator.
    It yields a triple (format, iml, limit_states), associated to a
    fragility model, followed by a sequence of triples of the form
    (taxonomy, params, no_damage_limit), associated each to a
    different fragility function sequence.

    :param source:
        Filename or file-like object containing the XML data.
    """

    def __init__(self, source):
        self._source = source
        openquake.nrmllib.assert_valid(self._source)
        self._fragility_model = etree.parse(self._source).getroot()
        self.limit_states = None

    def __iter__(self):
        """
        Parse the fragility model. The first iteration yields the
        format and the limit states, then the fragility function
        params
        """
        fragilityModel = findone('fragilityModel', self._fragility_model)
        fmt = fragilityModel.attrib['format']
        self.limit_states = findone('limitStates', fragilityModel).text.split()
        yield fmt, self.limit_states

        for ffs in find('ffs', fragilityModel):
            taxonomy = findone('taxonomy', ffs).text
            iml_element = findone('IML', ffs)
            iml = dict(IMT=iml_element.attrib['IMT'])

            # in discrete case we expect to find the levels in the text of IML
            # element.
            if fmt == 'discrete':
                iml['imls'] = map(float, iml_element.text.split())
            else:
                iml['imls'] = None

            no_damage_limit = ffs.attrib.get('noDamageLimit')
            if no_damage_limit:
                no_damage_limit = float(no_damage_limit)
            if fmt == 'discrete':
                all_params = [(ffd.attrib['ls'],
                               map(float, findone('poEs', ffd).text.split()))
                              for ffd in find('ffd', ffs)]
            else:  # continuous
                all_params = [(ffc.attrib['ls'],
                               (float(findone('params', ffc).attrib['mean']),
                                float(
                                    findone('params', ffc).attrib['stddev'])))
                              for ffc in find('ffc', ffs)]
            all_params = map(
                lambda x: x[1],
                sorted(all_params,
                       key=lambda x: self.limit_states.index(x[0])))
            yield taxonomy, iml, all_params, no_damage_limit

    def _check_limit_state(self, lsi, ls):
        if ls != self.limit_states[lsi]:
            raise ValueError('Expected limitState %s, got %s' %
                             (self.limit_states[lsi], ls))
