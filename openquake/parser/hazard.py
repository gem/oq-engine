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

    PROCESSING_ATTRIBUTES = (('IDmodel', str), ('investigationTimeSpan', float),
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
                error_str = "element Hazard Curve metadata: missing required " \
                    "attribute %s" % required_attribute
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
            ('../nrml:IML','IMLValues', float_strip),
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
