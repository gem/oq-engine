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

Occupancy = namedtuple("Occupancy", "occupants period")
Cost = namedtuple("Cost", "type value retrofitted deductible limit")


class ExposureModelParser(object):
    """
    Exposure model parser. This class is implemented as a generator.

    For each `asset` element in the parsed document,
    it yields a tuple, where:

    * the first element is a list with the geographical information,
      in the following format: [lon, lat].
    * the second element is a list of occupancy objects, each one with
      a property called `occupants` (the number of
      occupants), and a property called `period` (the context
      in which the number of occupants has been measured, for example
      during the day or night).
    * the third element is a dictionary with all the other information
      related to the asset as well as the whole exposure model.
      The attributes dictionary looks like this:
      {'exposure': 'PAV01',
       'description': 'Collection of existing building in Pavia',
       'id': 'asset_02',
       'category': 'buildings',
       'taxonomy': 'RC/DMRF-D/LR'}
    * the fourth element is a list of costs objects, each one with a
      property called `type` (the type of cost, e.g. structural),
      a property named `value`, a property named `retrofitted` (optional)
      a property named `deductible` and a property named `insuranceLimit`.
    * the fifth element holds the cost types with a dictionary mapping a
      cost type with a tuple with four elements (representing type and unit for
      standard and retrofitted case)

    :param source:
        Filename or file-like object containing the XML data.
    """

    def __init__(self, source):
        self._source = source
        openquake.nrmllib.assert_valid(self._source)

        # contains the data of the node currently parsed.
        self._current_meta = {}
        self._cost_types = {}

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

            if event == 'start' and element.tag == '%sexposureModel' % NRML:
                # we need to get the exposureList id, description and
                # asset category.
                exp_id = element.get('id')
                self._current_meta['exposureID'] = str(exp_id)

                desc = element.find('%sdescription' % NRML)
                if desc is not None:
                    self._current_meta['description'] = str(desc.text)

                self._current_meta['taxonomySource'] = element.get(
                    'taxonomySource')

                asset_category = str(element.get('category'))
                self._current_meta['category'] = asset_category

            if event == 'start' and element.tag == "%sconversions" % NRML:
                for el in element.findall(".//"):
                    if el.tag[len(NRML):] == "area":
                        self._current_meta['areaType'] = el.get('type')
                        self._current_meta['areaUnit'] = el.get('unit')
                    elif el.tag[len(NRML):] == "deductible":
                        self._current_meta['deductibleIsAbsolute'] = not (
                            el.get('isAbsolute', "false") == "false")
                        self._current_meta['insuranceLimitIsAbsolute'] = not (
                            el.get('isAbsolute', "false") == "false")
            if event == 'start' and element.tag == "%scostTypes" % NRML:
                for el in element.findall(".//"):
                    self._cost_types[el.get('name')] = (
                        el.get('type'), el.get('unit'),
                        el.get('retrofittedType'), el.get('retrofittedUnit'))

            elif event == 'end' and element.tag == '%sasset' % NRML:
                site_data = (_to_site(element), _to_occupancy(element),
                             self._to_site_attributes(element),
                             _to_costs(element), self._cost_types)
                del element
                yield site_data

    def _to_site_attributes(self, element):
        """
        Build a dict of all node attributes.
        """

        site_attributes = {}
        site_attributes['id'] = element.get('id')
        site_attributes['taxonomy'] = element.get('taxonomy')
        if element.get('area') is not None:
            site_attributes['area'] = float(element.get('area'))
        if element.get('number') is not None:
            site_attributes['number'] = float(element.get('number'))
        site_attributes.update(self._current_meta)
        return site_attributes


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
            int(otag.attrib['occupants']),
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


def _to_site(element):
    """
    Get lon lat from an <asset> element
    """

    point_elem = element.find('%slocation' % NRML)
    return map(float, [point_elem.get("lon"), point_elem.get("lat")])


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
