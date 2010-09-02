# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

""" This module contains a class that parses instance document files of a
specific flavour of the shaML data format. This flavour is shaML "output",
i.e., the potential outcome of the hazard engine. The root element of such
shaML instance documents is <HazardResultList>.

In the future, this module will probably be refactored/renamed in order to 
support other flavours of shaML (the "input" formats).
"""

from lxml import etree

from opengem import producer
from opengem import shapes
from opengem.xml import SHAML_NS, GML_NS

class ShamlOutputFile(producer.FileProducer):
    """ This class parses a shaML output file. The contents of a shaML output
    file is meant to be used as input for the risk engine. The class is
    implemented as a generator. For each 'Curve' element in the parsed 
    instance document, it yields a pair of objects, of which the
    first one is a shapely.geometry object of type Point (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with hazard-related attribute values for this site.
    
    The attribute dictionary looks like
    {'IMT': 'PGA',
     'IDmodel': 'Model_Id',
     'timeSpanDuration': 50.0,
     'saPeriod': 1.0,
     'saDamping': 1.0,
     'calcSettingsID': 'foo',
     'endBranchLabel': '1_2_3', 
     'IML': [-5.3, -4.9, ...],
     'maxProb': 0.7,
     'minProb': 0.001, 
     'Values': [0.70, 0.68, ...],
     'vs30': 760.0
    }

    Notes:
    1) TODO(fab): require that attribute values of 'IMT' are from list
       of allowed values (see shaML XML Schema)
    2) 'endBranchLabel' can be replaced by 'aggregationType'
    3) TODO(fab): require that value of 'aggregationType' element is from a
       list of allowed values (see shaML XML Schema)
    4) 'saPeriod', 'saDamping', 'calcSettingsID', 'maxProb' and 'minProb' are
       optional
    5) shaML output can also contain hazard maps, parsing of those is not yet
       implemented
    """

    def _parse(self):
        self._current_result_meta = None
        self._current_result_descriptor = None
        self._current_curvelist_iml = None
        for event, element in etree.iterparse(self.file,
                                              events=('start', 'end')):

            if event == 'start' and element.tag == '{%s}Result' % SHAML_NS:
                self._set_result_meta(element)
            elif event == 'end' and element.tag == '{%s}Descriptor' % SHAML_NS:
                self._set_result_descriptor(element)
            elif event == 'start' and element.tag == '{%s}HazardMap' \
                % SHAML_NS:
                error_str = "parsing of HazardMap elements is not yet " \
                    "implemented"
                raise NotImplementedError()
            elif event == 'end' and element.tag == '{%s}IML' % SHAML_NS:
                self._set_curvelist_iml(element)
            elif event == 'end' and element.tag == '{%s}Curve' % SHAML_NS:
                yield (self._to_site(element), 
                       self._to_site_attributes(element))

    def _set_result_meta(self, result_element):

        self._current_result_meta = {}

        for (required_attr, attr_type) in (('IMT', str), ('IDmodel', str),
            ('timeSpanDuration', float)):
            attr_value = result_element.get(required_attr)
            if attr_value is not None:
                self._current_result_meta[required_attr] = \
                    attr_type(attr_value)
            else:
                error_str = "element shaml:Result: missing required " \
                    "attribute %s" % required_attr
                raise ValueError(error_str) 

        for (optional_attr, attr_type) in (('saPeriod', float), 
            ('saDamping', float), ('calcSettingsID', str)):
            attr_value = result_element.get(optional_attr)
            if attr_value is not None:
                self._current_result_meta[optional_attr] = \
                    attr_type(attr_value)

    def _set_result_descriptor(self, descriptor_element):
        
        self._current_result_descriptor = {}

        # Descriptor/[endBranchLabel|aggregationType] [1]
        descriptor_endBranchLabel = descriptor_element.xpath(
            'shaml:endBranchLabel', 
            namespaces={'shaml': SHAML_NS})
        descriptor_aggregationType = descriptor_element.xpath(
            'shaml:aggregationType', 
            namespaces={'shaml': SHAML_NS})

        if (len(descriptor_endBranchLabel) == 1) and \
            (len(descriptor_aggregationType) == 0):
            self._current_result_descriptor['endBranchLabel'] = \
                descriptor_endBranchLabel[0].text.strip()
        elif (len(descriptor_endBranchLabel) == 0) and \
            (len(descriptor_aggregationType) == 1):
            self._current_result_descriptor['aggregationType'] = \
                descriptor_aggregationType[0].text.strip()
        else:
            error_str = "shaML output instance Descriptor element " \
                "is broken"
            raise ValueError(error_str) 

    def _set_curvelist_iml(self, iml_element):
        try:
            self._current_curvelist_iml = {
                'IML': map(float, iml_element.text.strip().split()) }
        except Exception:
            error_str = "invalid shaML HazardCurveList IML array"
            raise ValueError(error_str)

    def _to_site(self, element):
        pos_el = element.xpath('shaml:Site/shaml:Site/gml:pos',
            namespaces={'shaml': SHAML_NS, 'gml': GML_NS})
        try:
            coord = map(float, pos_el[0].text.strip().split())
            return shapes.Site(coord[0], coord[1])
        except Exception:
            error_str = "shaML point coordinate error: %s" % \
                ( pos_el[0].text )
            raise ValueError(error_str)

    def _to_site_attributes(self, element):

        site_attributes = {}

        value_el = element.xpath('shaml:Site/shaml:Values', 
            namespaces={'shaml': SHAML_NS})
        try:
            site_attributes['Values'] = map(float, 
                value_el[0].text.strip().split())
        except Exception:
            error_str = "invalid or missing shaML site values array"
            raise ValueError(error_str)

        vs30_el = element.xpath('shaml:Site/shaml:vs30', 
            namespaces={'shaml': SHAML_NS})
        try:
            site_attributes['vs30'] = float(vs30_el[0].text)
        except Exception:
            error_str = "invalid or missing shaML site vs30 value"
            raise ValueError(error_str) 

        for optional_attribute in ('minProb', 'maxProb'):
            try:
                site_attributes[optional_attribute] = \
                    float(element.get(optional_attribute))
            except Exception:
                pass

        for (attribute_chunk, ref_string) in (
            (self._current_result_meta, "Result"),
            (self._current_result_descriptor, "Result/Descriptor"),
            (self._current_curvelist_iml, "HazardCurveList/IML")):

            try:
                site_attributes.update(attribute_chunk)
            except Exception:
                error_str = "missing shaML element: %s" % ref_string
                raise ValueError(error_str)

        return site_attributes

    def filter(self, region_constraint, attribute_constraint=None):
        """ region_constraint has to be of type shapes.RegionConstraint 
        (defined in file shapes.py)
        """
        for next in iter(self):
            if (attribute_constraint is not None and \
                    region_constraint.match(next[0]) and \
                    attribute_constraint.match(next[1])) or \
               (attribute_constraint is None and \
                    region_constraint.match(next[0])):
                yield next


class ShamlOutputConstraint(object):
    """ This class represents a constraint that can be used to filter
    hazard curve elements from a shaML output instance document
    based on their site attributes. The constructor requires a dictionary as
    argument. Items in this dictionary have to match the corresponding ones
    in the checked site attribute object.
    """
    def __init__(self, attribute):
        self.attribute = attribute

    def match(self, compared_attribute):
        for k, v in self.attribute.items():
            if not ( k in compared_attribute and compared_attribute[k] == v ):
                return False
        return True