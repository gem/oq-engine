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

import nrml

NRML = "{%s}" % nrml.NAMESPACE
GML = "{%s}" % nrml.GML_NAMESPACE

OCCUPANCY = namedtuple("OCCUPANCY", "occupants, description")


class ExposureModelParser(object):
    """
    Exposure model parser. This class is implemented as a generator.

    For each `assetDefinition` element in the parsed document,
    it yields a tuple, where:

    * the first element is a list with the geographical information,
      in the following format: [lon, lat].
    * the second element is a list of occupancy objects, each one with
      a property called `occupants` (the number of
      occupants), and a property called `description` (the context
      in which the number of occupants has been measured, for example
      during the day or night).
    * the third element is a dictionary with all the other information
      related to the asset. The attributes dictionary looks like this:
      {'listID': 'PAV01',
       'listDescription': 'Collection of existing building in Pavia',
       'assetID': 'asset_02',
       'assetCategory': 'buildings',
       'taxonomy': 'RC/DMRF-D/LR',
       'structureCategory': 'RC-LR-PC',
       'assetValue': 250000.0,
       'assetValueUnit': 'EUR'}

    :param source:
        Filename or file-like object containing the XML data.
    """

    def __init__(self, source):
        self._source = source
        assert_is_valid(self._source)

        # contains the data of the node currently parsed.
        self._current_meta = {}

    def assert_is_valid(self):
        """
        Check the input file is valid according to the schema.
        """

        exposure = etree.parse(self._source)
        xmlschema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))

        if not xmlschema.validate(exposure):
            raise ValueError("Exposure model is not valid.")

    def __iter__(self):
        for i in self._parse():
            yield i

    def _parse(self):
        """
        Parse the document iteratively.
        """

        schema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))

        for event, element in etree.iterparse(
            self._source, events=('start', 'end'), schema=schema):

            if event == 'start' and element.tag == \
               '%sexposureList' % NRML:
                # we need to get the exposureList id, description and
                # asset category.
                exp_id = element.get('%sid' % GML)
                self._current_meta['listID'] = str(exp_id)

                desc = element.find('%sdescription' % GML)
                if desc is not None:
                    self._current_meta['listDescription'] = str(desc.text)

                taxsrc = element.find('%staxonomySource' % NRML)
                if taxsrc is not None:
                    self._current_meta['taxonomySource'] = str(taxsrc.text)

                asset_category = str(element.get('assetCategory'))
                self._current_meta['assetCategory'] = asset_category

                # type and unit for area, contents cost, retrofitting cost
                # and structural cost.
                attrs = ("areaType", "areaUnit", "cocoType", "cocoUnit",
                         "recoType", "recoUnit", "stcoType", "stcoUnit")
                for attr_name in attrs:
                    attr_value = element.get(attr_name)
                    if attr_value is not None:
                        self._current_meta[attr_name] = attr_value

            elif event == 'end' and element.tag == '%sassetDefinition' % NRML:
                site_data = (_to_site(element), _to_occupancy(element),
                             self._to_site_attributes(element))
                del element
                yield site_data

    def _to_site_attributes(self, element):
        """
        Build a dict of all node attributes.
        """

        site_attributes = {}
        site_attributes['assetID'] = element.get('%sid' % GML)

        # Optional elements.
        attrs = (('coco', float), ('reco', float), ('stco', float),
                 ('area', float), ('number', float), ('limit', float),
                 ('deductible', float))
        for (attr_name, attr_type) in attrs:
            attr_value = element.find('%s%s' % (NRML, attr_name))
            if attr_value is not None:
                site_attributes[attr_name] = attr_type(attr_value.text)

        # Mandatory elements.
        for (required_attr, attr_type) in (('taxonomy', str),):
            attr_value = element.find('%s%s' % (NRML, required_attr)).text
            if attr_value is not None:
                site_attributes[required_attr] = attr_type(attr_value)
            else:
                error_str = ("element assetDefinition: missing required "
                             "attribute %s" % required_attr)
                raise ValueError(error_str)

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
    for otag in element.findall('%soccupants' % NRML):
        occupancy_data.append(OCCUPANCY(
            occupants=int(otag.text), description=otag.attrib["description"]))
    return occupancy_data


def _to_site(element):
    """
    Convert current GML attributes to Site object.

    We want to extract the value of <gml:pos>. We expect the input
    element to be an 'assetDefinition' and have a child element
    structured like this:

    <site>
        <gml:Point srsName="epsg:4326">
            <gml:pos>9.15000 45.16667</gml:pos>
        </gml:Point>
    </site>
    """

    point_elem = element.find('%ssite' % NRML).find('%sPoint' % GML)
    return [float(x.strip()) for x in point_elem.find(
        '%spos' % GML).text.split()]


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
        assert_is_valid(self._source)

        self._vulnerability_model = etree.parse(self._source).getroot()

    def __iter__(self):
        """
        Parse the vulnerability model.
        """

        for vulnerability_set in self._vulnerability_model.findall(
            ".//%sdiscreteVulnerabilitySet" % NRML):

            vulnerability_function = _parse_set_attributes(vulnerability_set)

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


def assert_is_valid(source):
    """
    Check the input file is valid according to the schema.
    """

    exposure = etree.parse(source)
    xmlschema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))

    if not xmlschema.validate(exposure):
        raise ValueError("Exposure model is not valid.")
