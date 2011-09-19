# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
This module contains a class that parses instance document files of a
specific flavour of the NRML data format. This flavour is NRML the potential
outcome of the hazard calculations in the engine. The root element of such
NRML instance documents is <HazardResultList>.
"""

from lxml import etree

from openquake import producer
from openquake import shapes

from openquake.xml import NRML_NS, GML_NS, NRML


NAMESPACES = {'gml': GML_NS, 'nrml': NRML_NS}


def _to_site(element):
    """Extract site information from an HCNode or GMFNode
    and return a Site object"""
    # lon/lat are in XML attributes 'Longitude' and 'Latitude'
    # consider them as mandatory
    pos_el = element.xpath("./nrml:site/gml:Point/gml:pos",
                           namespaces=NAMESPACES)
    assert len(pos_el) == 1

    try:
        coord = [float(x) for x in pos_el[0].text.strip().split()]
    except (AttributeError, ValueError, IndexError, TypeError):
        raise ValueError('Missing or invalid lon/lat')
    return shapes.Site(coord[0], coord[1])


def _to_gmf_site_data(element):
    """ Extract site and ground motion values from a given GMFNode element

    returns a tuple of (shapes.Site, dict)"""

    attributes = {}

    ground_motion_elems = element.xpath('./nrml:groundMotion',
                                        namespaces=NAMESPACES)
    assert len(ground_motion_elems) == 1

    try:
        attributes['groundMotion'] = \
            float(ground_motion_elems[0].text.strip())
    except (AttributeError, ValueError, IndexError, TypeError):
        raise ValueError('invalid or missing groundMotion value')
    return (_to_site(element), attributes)


class NrmlFile(producer.FileProducer):
    """ This class parses a NRML hazard curve file. The contents of a NRML
    file is meant to be used as input for the risk engine. The class is
    implemented as a generator. For each 'Curve' element in the parsed
    instance document, it yields a pair of objects, of which the
    first one is a shapes object of type Site (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with hazard-related attribute values for this site.

    The attribute dictionary looks like
    {'IMT': 'PGA',
     'IDmodel': 'Model_Id',
     'investigationTimeSpan': 50.0,
     'endBranchLabel': 'Foo',
     'saDamping': 0.2,
     'saPeriod': 0.1,
     'IMLValues': [5.0000e-03, 7.0000e-03, ...],
     'PoEValues': [9.8728e-01, 9.8266e-01, ...],
    }

    Notes:
    1) TODO(fab): require that attribute values of 'IMT' are from list
       of allowed values (see NRML XML Schema)
    2) 'endBranchLabel' can be replaced by 'aggregationType'
    3) TODO(fab): require that value of 'aggregationType' element is from a
       list of allowed values (see NRML XML Schema)
    4) 'saPeriod', 'saDamping', 'calcSettingsID', are optional
    5) NRML output can also contain hazard maps, parsing of those is not yet
       implemented

    """

    PROCESSING_ATTRIBUTES = (('IDmodel', str),
                             ('investigationTimeSpan', float),
                             ('saPeriod', float), ('saDamping', float))

    def __init__(self, path):
        super(NrmlFile, self).__init__(path)
        self._current_hazard_meta = None

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'start' and element.tag == NRML + 'hazardProcessing':
                self._hazard_curve_meta(element)
            elif event == 'end' and element.tag == NRML + 'HCNode':
                site_data = (_to_site(element), self._to_attributes(element))
                del element
                yield site_data

    def _hazard_curve_meta(self, element):
        """ Hazard curve metadata from the element """
        self._current_hazard_meta = {}
        for (required_attribute, attrib_type) in self.PROCESSING_ATTRIBUTES:
            id_model_value = element.get(required_attribute)
            if id_model_value is not None:
                self._current_hazard_meta[required_attribute]\
                = attrib_type(id_model_value)
            else:
                error_str = "element Hazard Curve metadata: " \
                    "missing required attribute %s" % required_attribute
                raise ValueError(error_str)

    def _to_attributes(self, element):
        """ Build an attributes dict from an HCNode element """

        attributes = {}

        invalid_value_error = 'invalid or missing %s value'

        float_strip = lambda x: [float(o) for o in x[0].text.strip().split()]
        get_imt = lambda x: x[0].get('IMT').strip()
        get_ebl = lambda x: x[0].get('endBranchLabel').strip()

        for (child_el, child_key, etl) in (
            ('./nrml:hazardCurve/nrml:poE', 'PoEValues', float_strip),
            ('../nrml:IML', 'IMLValues', float_strip),
            ('../nrml:IML', 'IMT', get_imt),
            ('../../nrml:hazardCurveField', 'endBranchLabel', get_ebl)):
            child_node = element.xpath(child_el,
                namespaces=NAMESPACES)

            try:
                attributes[child_key] = etl(child_node)
            except Exception:
                raise ValueError(invalid_value_error % child_key)

        if self._current_hazard_meta is None:
            raise ValueError("config element 'hazardProcessing' is missing")

        attributes.update(self._current_hazard_meta)
        return attributes


class GMFReader(producer.FileProducer):
    """ This class parses a NRML GMF (ground motion field) file.
    The class is implemented as a generator. For each 'site' element
    in the parsed instance document, it yields a pair of objects, of
    which the first one is a shapes object of type Site (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with GMF-related attribute values for this site.

    The attribute dictionary looks like
    {'groundMotion': 0.8}
    """

    def __init__(self, path):
        super(GMFReader, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'end' and element.tag == NRML + 'GMFNode':
                yield (_to_gmf_site_data(element))


class HazardConstraint(object):
    """ This class represents a constraint that can be used to filter
    VulnerabilityFunction elements from an VulnerabilityModel XML instance
    document based on their attributes. The constructor requires a dictionary
    as argument. Items in this dictionary have to match the corresponding ones
    in the checked attribute object.
    """

    def __init__(self, attribute):
        self.attribute = attribute

    def match(self, compared_attribute):
        """ Compare self.attribute against the passed in compared_attribute
        dict. If the compared_attribute dict does not contain all of the
        key/value pais from self.attribute, we return false. compared_attribute
        may have additional key/value pairs.
        """
        for k, v in self.attribute.items():
            if not (k in compared_attribute and compared_attribute[k] == v):
                return False
        return True


class HazardMapReader(producer.FileProducer):
    """This class parses a NRML hazard map file. This class is
    implemented as a generator. For each "HMNode" element in the parsed
    instance document, it yields a pair of objects, of which the
    first one is a shapes object of type Site (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with hazard-related attribute values for this site.

    The attribute dictionary looks like:
    { "IMT": "PGA", "poE": 0.1, "IML": 0.5 }

    A sample file is provided under docs/schema/examples (hazard-map.xml).

    This parser currently doesn't support:
        * the </config /> element
        * the "gml:id" and "endBranchLabel"
          attributes of the <hazardMap /> element
        * the "vs30" element
    """

    def __init__(self, path):
        self.data = {}
        self.current_element = None
        producer.FileProducer.__init__(self, path)

    def _parse(self):
        """Parse iteratively the instance document.

        :returns: a tuple for each <HMNode /> element found in the document.
        :rtype: tuple of two elements:
            * an instance of :py:class:`openquake.shapes.Site` as first element
              (the site to which the current node is related)
            * :py:class:`dict` containing the attributes related to the node
              Example: { "IMT": "PGA", "poE": 0.1, "IML": 0.5 }
        """

        for event, element in etree.iterparse(
            self.file, events=("start", "end")):

            self.current_element = element

            if event == "start" and element.tag == NRML + "hazardMap":
                self.data["IMT"] = element.attrib["IMT"].strip()
                self.data["poE"] = float(element.attrib["poE"].strip())

            elif event == "start" and element.tag == NRML + "HMNode":
                site = self._extract_site()
                self.data["IML"] = self._extract_iml()

                yield (site, dict(self.data))

    def _extract_iml(self):
        """Extract the IML (Intensity Measure Level) for the current node.

        :returns: the IML value
        :rtype: float
        """

        iml_el = self.current_element.xpath(
            "./nrml:IML", namespaces=NAMESPACES)

        return float(iml_el[0].text.strip())

    def _extract_site(self):
        """Extract the site to which the current node is related.

        :returns: the site to which the current node is related
        :rtype: :py:class:`openquake.shapes.Site`
        """

        pos_el = self.current_element.xpath(
            "./nrml:HMSite/gml:Point/gml:pos", namespaces=NAMESPACES)

        assert len(pos_el) == 1

        try:
            coord = [float(x) for x in pos_el[0].text.strip().split()]
        except (AttributeError, ValueError, IndexError, TypeError):
            raise ValueError("Missing or invalid lon/lat")

        return shapes.Site(coord[0], coord[1])
