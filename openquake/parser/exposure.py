# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""Parsers to read exposure files, including exposure portfolios.
These can include building, population, critical infrastructure,
and other asset classes."""

from collections import namedtuple
from lxml import etree

from openquake import producer
from openquake import shapes
from openquake import xml
from openquake.nrml.utils import nrml_schema_file
from openquake.xml import NRML, GML

# do not use namespace for now
RISKML_NS = ''


OCCUPANCY = namedtuple("OCCUPANCY", "occupants, description")


def _to_site(element):
    """Convert current GML attributes to Site object

    We want to extract the value of <gml:pos>. We expect the input
    element to be an 'assetDefinition' and have a child element
    structured like this:

    <site>
        <gml:Point srsName="epsg:4326">
            <gml:pos>9.15000 45.16667</gml:pos>
        </gml:Point>
    </site>
    """
    # lon/lat are in XML attribute gml:pos
    # consider them as mandatory

    try:
        site_elem = element.find('%ssite' % NRML)
        point_elem = site_elem.find('%sPoint' % GML)
        pos = point_elem.find('%spos' % GML).text
        lon, lat = [float(x.strip()) for x in pos.split()]

        return shapes.Site(lon, lat)
    except Exception:
        error_str = "element assetDefintion: no valid lon/lat coordinates"
        raise ValueError(error_str)


def _to_occupancy(element):
    """Convert the 'occupants' tags to named tuples.

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


class ExposureModelFile(producer.FileProducer):
    """ This class parses an ExposureModel XML (part of riskML?) file.
    The contents of such a file is meant to be used as input for the risk
    engine. The class is implemented as a generator.
    For each 'AssetInstance' element in the parsed
    instance document, it yields a pair of objects, of which the
    first one is a shapely.geometry object of type Point (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with exposure-related attribute values for this site.

    The attribute dictionary looks like this::

        {'listID': 'PAV01',
         'listDescription': 'Collection of existing building in ' \
                            'downtown Pavia',
         'assetID': 'asset_02',
         'assetCategory': 'buildings',
         'taxonomy': 'RC/DMRF-D/LR',
         'structureCategory': 'RC-LR-PC',
         'assetValue': 250000.0,
         'assetValueUnit': 'EUR'}

    """

    def __init__(self, path):
        super(ExposureModelFile, self).__init__(path)

    def _parse(self):
        try:
            for i in self._do_parse():
                yield i
        except etree.XMLSyntaxError as ex:
            # when using .iterparse, the error message does not
            # contain a file name
            raise xml.XMLValidationError(ex.message, self.file.name)

    def _do_parse(self):
        """_parse implementation"""
        nrml_schema = etree.XMLSchema(etree.parse(nrml_schema_file()))
        level = 0
        for event, element in etree.iterparse(
                self.file, events=('start', 'end'), schema=nrml_schema):

            if event == 'start' and element.tag == \
                    '%sexposureList' % NRML:
                # we need to get the exposureList id, description and
                # asset category
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
                         "recoType", "recoUnit", "stcoType", "stcoUnit",
                         "unitType")
                for attr_name in attrs:
                    attr_value = element.get(attr_name)
                    if attr_value is not None:
                        self._current_meta[attr_name] = attr_value

            elif event == 'start' and level < 2:
                # check that the first child of the root element is an
                # exposure portfolio
                if level == 1 and element.tag != '%sexposureModel' % NRML:
                    raise xml.XMLMismatchError(
                        self.file.name, str(element.tag)[len(NRML):],
                        'exposureModel')

                level += 1

            elif event == 'end' and element.tag == '%sassetDefinition' % NRML:
                site_data = (_to_site(element), _to_occupancy(element),
                             self._to_site_attributes(element))
                del element
                yield site_data

    def _to_site_attributes(self, element):
        """Build a dict of all node attributes"""
        site_attributes = {}

        site_attributes['assetID'] = element.get('%sid' % GML)

        # Optional elements
        attrs = (('coco', float), ('reco', float), ('stco', float),
                 ('area', float), ('number', float), ('limit', float),
                 ('deductible', float))
        for (attr_name, attr_type) in attrs:
            attr_value = element.find('%s%s' % (NRML, attr_name))
            if attr_value is not None:
                site_attributes[attr_name] = attr_type(attr_value.text)

        # Mandatory elements
        for (required_attr, attr_type) in (('taxonomy', str),):
            attr_value = element.find('%s%s' % (NRML, required_attr)).text
            if attr_value is not None:
                site_attributes[required_attr] = attr_type(attr_value)
            else:
                error_str = ("element assetDefinition: missing required "
                             "attribute %s" % required_attr)
                raise ValueError(error_str)

        # TODO, al-maisan, Thu, 16 Feb 2012 15:55:01 +0100
        # add the logic that handles the 'occupants' tags.
        # https://bugs.launchpad.net/openquake/+bug/942178

        site_attributes.update(self._current_meta)

        return site_attributes
