# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

""" This module contains a class that parses instance document files of a
specific flavour of the NRML data format. This flavour is NRML the potential
outcome of the hazard calculations in the engine. The root element of such
NRML instance documents is <HazardResultList>.
"""

from lxml import etree

from opengem import producer
from opengem import shapes
from opengem.xml import SHAML_NS, GML_NS, NRML_NS #### REMOVE SHAML_NS°°####

class NrmlFile(producer.FileProducer):
    #° was ShamlOutputFile
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
     'timeSpanDuration': 50.0,
     'endBranchLabel': 'Foo', 
     'IML': [5.0000e-03, 7.0000e-03, ...], 
     'Values': [9.8728e-01, 9.8266e-01, ...],
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

    REQUIRED_ATTRIBUTES = (('IDmodel', str), ('timeSpanDuration', float))
            
    OPTIONAL_ATTRIBUTES = (('saPeriod', float), ('saDamping', float))

    def __init__(self, path):
        super(NrmlFile, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):

            if event == 'start' and element.tag == 'HazardProcessing':
                self._hazard_curve_meta(element)
            elif event == 'end' and element.tag == 'HazardCurveList':
                yield (self._to_attributes(element))
        
    def _hazard_curve_meta(self, hazard_element):

        self._current_hazard_meta = {}
            
        for required_attribute in (('IDmodel', str)):
            
            id_model_value = hazard_element.get(required_attribute[0])
            if id_model_value is not None:
                self._current_hazard_meta[required_attribute[0]]\
                = required_attribute[1](id_model_value)
            else:
                error_str = "element Hazard Curve metadata: missing required " \
                    "attribute %s" % required_attribute[0]
                raise ValueError(error_str)

    def _to_attributes(self, element):

        attributes = {}
        
        for child_el in ('gml:pos', 'Values',
        'IMLValues'):
           child_node = element.xpath(child_el)

           try:
               attributes[child_el] = map(float, 
                   child_node[0].text.strip().split())
           except Exception:
               error_str = "invalid or missing %s value" % child_el
               raise ValueError(error_str) 

        # consider all attributes of HazardProcessing element as mandatory 
        for required_attribute in ('endBranchLabel', str):

           attr_value = element.get(required_attribute[0])
           if attr_value is not None:
               attributes[required_attribute[0]] = \
                   required_attribute[1](attr_value)
           else:
               error_str = "element endBranchLabel: missing required "\
                   "attribute %s" % required_attribute[0]
               raise ValueError(error_str) 

        try:
           attributes.update(self._current_hazard_meta)
        except Exception:
           error_str = "root element (HazardProcessing) is missing"
           raise ValueError(error_str) 
        
        return attributes

    def filter(self, attribute_constraint=None):
       for next in iter(self):
           if (attribute_constraint is not None and \
                   attribute_constraint.match(next)):
               yield next

        
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
        for k, v in self.attribute.items():
            if not ( k in compared_attribute and compared_attribute[k] == v ):
                return False
        return True
