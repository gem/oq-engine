# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""This module contains a class that parses instance document files of a
specific flavour of the NRML data format. This flavour is NRML the potential
outcome of the hazard calculations in the engine. The root element of such
NRML instance documents is <HazardResultList>.
"""

from lxml import etree

from openquake import logs

from openquake import producer
from openquake import shapes

from openquake.xml import NRML_NS, GML_NS, NRML

LOG = logs.LOG

def _to_site(element):
    """Convert current GML attributes to Site object"""
    # lon/lat are in XML attributes 'Longitude' and 'Latitude'
    # consider them as mandatory
    pos_el = element.xpath("gml:pos", namespaces={"gml": GML_NS})
    coord = [float(x) for x in pos_el[0].text.strip().split()]
    return shapes.Site(coord[0], coord[1])


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
     'timeSpanDuration': 50.0,
     'endBranchLabel': 'Foo', 
     'IML': [5.0000e-03, 7.0000e-03, ...], 
     'Values': [9.8728e-01, 9.8266e-01, ...],
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

    PROCESSING_ATTRIBUTES = (('IDmodel', str), ('timeSpanDuration', float),
                             ('saPeriod', float), ('saDamping', float))

    def __init__(self, path):
        super(NrmlFile, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'start' and element.tag == NRML + 'HazardProcessing':
                self._hazard_curve_meta(element)
            # The HazardMap is not yet implemented
            #elif event == 'start' and element.tag == NRML + 'HazardMap':
             #error_str = "parsing of HazardMap elements is not yet implemented"
             #raise NotImplementedError(error_str)    
            elif event == 'end' and element.tag == NRML + 'HazardCurve':
                yield (_to_site(element), 
                       self._to_attributes(element))
    
    def _hazard_curve_meta(self, element):
        """ Hazard curve metadata from the element """
        self._current_hazard_meta = {} #pylint: disable=W0201
        for (required_attribute, attrib_type) in self.PROCESSING_ATTRIBUTES:
            id_model_value = element.get(required_attribute)
            if id_model_value is not None:
                self._current_hazard_meta[required_attribute]\
                = attrib_type(id_model_value)
            else:
                error_str = "element Hazard Curve metadata: missing required " \
                    "attribute %s" % required_attribute
                raise ValueError(error_str)

    def _to_attributes(self, element):
        """ Build an attributes dict from XML element """
        
        attributes = {}
        
        float_strip = lambda x: [float(o) for o in x[0].text.strip().split()]
        string_strip = lambda x: x[0].text.strip()
        # TODO(JMC): This is hardly efficient, but it's simple for the moment...
        
        for (child_el, child_key, etl) in (
            ('nrml:Values', 'Values', float_strip),
            ('../nrml:Common/nrml:IMLValues','IMLValues', float_strip),
            ('../nrml:Common/nrml:IMT', 'IMT', string_strip)):
            child_node = element.xpath(child_el, 
                namespaces={"gml": GML_NS, "nrml": NRML_NS})

            try:
                attributes[child_key] = etl(child_node)
            except Exception:
                error_str = "invalid or missing %s value" % child_key
                raise ValueError(error_str) 

        # consider all attributes of HazardProcessing element as mandatory 
        for (required_attribute, attrib_type) in [('endBranchLabel', str)]:
            (haz_list_element,) = element.xpath("..", 
                namespaces={"gml": GML_NS, "nrml": NRML_NS})
            attr_value = haz_list_element.get(required_attribute)
            if attr_value is not None:
                attributes[required_attribute] = \
                    attrib_type(attr_value)
            else:
                error_str = "element endBranchLabel: missing required "\
                   "attribute %s" % required_attribute
                raise ValueError(error_str) 

        try:
            attributes.update(self._current_hazard_meta)
        except Exception:
            error_str = "root element (HazardProcessing) is missing"
            raise ValueError(error_str) 
        
        return attributes
    # 
    # def filter(self, attribute_constraint=None):
    #    for next in iter(self):
    #        if (attribute_constraint is not None and \
    #                attribute_constraint.match(next)):
    #            yield next


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
        site_nesting_level = 0
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'start' and element.tag == NRML + 'HazardResult':
                self._gmf_attributes()
            elif event == 'start' and element.tag == NRML + 'site':
                site_nesting_level += 1
            elif event == 'end' and element.tag == NRML + 'site':
                site_nesting_level -= 1

                # yield only for outer site elements
                if site_nesting_level == 0:
                    yield (self._to_site_data(element))

    def _gmf_attributes(self):
        """TODO(fab): Collect instance-wide attributes here."""
        pass

    def _to_site_data(self, element):
        """this is called on the outer 'site' elements"""
        
        attributes = {}
        attributes['groundMotion'] = float(element.get('groundMotion'))
        (inner_site_node,) = element.xpath('nrml:site', 
                namespaces={"gml": GML_NS, "nrml": NRML_NS})
        return (_to_site(inner_site_node), attributes)


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
