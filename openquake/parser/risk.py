# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This module contains a class that parses NRML instance document files
for the output of risk computations. At the moment, loss and loss curve data
is supported.
"""

from lxml import etree

from openquake import producer
from openquake import shapes
from openquake import xml

from openquake.parser import nrml

#from openquake.xml import NRML_NS_OLD, GML_NS_OLD, NRML_OLD

# TODO(fab): use same function from xml module
def _to_site(element):
    """Convert current GML attributes to Site object."""
    # lon/lat are in XML attributes 'Longitude' and 'Latitude'
    # consider them as mandatory
    pos_el = element.xpath("gml:pos", namespaces={"gml": xml.GML_NS_OLD})
    coord = [float(x) for x in pos_el[0].text.strip().split()]
    return shapes.Site(coord[0], coord[1])

class RiskXMLReader(producer.FileProducer):
    """ This class parses a NRML loss/loss ratio curve file. 
    The class is implemented as a generator. 
    For each curve element in the parsed 
    instance document, it yields a pair of objects, of which the
    first one is a shapes object of type Site (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with risk-related attribute values for this site.
    
    The attribute dictionary looks like
    {'POE': [0.2, 0.02, ...], 
     'Values': [0.0, 1280.0, ...],
     'Property': 'Loss' # 'Loss Ratio'
    }
    """

    # these tag names and properties have to be redefined in the 
    # derived classes
    abscissa_property = None
    ordinate_element = None
    abscissa_container = None

    ordinate_property = 'Probability of Exceedance'
    abscissa_element = 'Values'

    abscissa_output_key = 'Values'
    ordinate_output_key = 'POE'
    property_output_key = 'Property'

    #def __init__(self, path):
        #super(RiskXMLReader, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'end' and \
                element.tag == xml.NRML_OLD + self.abscissa_container:
                yield (shapes.Site(xml.lon_lat_from_site(element)), 
                       self._to_attributes(element))

    def _to_attributes(self, element):
        """ Build an attributes dict from XML element """
        
        attributes = {self.property_output_key: self.abscissa_property}
        
        float_strip = lambda x: [float(o) for o in x[0].text.strip().split()]
        # TODO(JMC): This is hardly efficient, but it's simple for the moment...
        
        for (child_el, child_key, etl) in (
            ('nrml:%s' % self.abscissa_element, self.abscissa_output_key, 
                float_strip),
            ('../nrml:Common/nrml:%s/nrml:Values' % self.ordinate_element,
                self.ordinate_output_key, float_strip)):
            
            child_node = element.xpath(child_el, 
                namespaces={"gml": xml.GML_NS_OLD, "nrml": xml.NRML_NS_OLD})

            try:
                attributes[child_key] = etl(child_node)
            except Exception:
                error_str = "invalid or missing %s value" % child_key
                raise ValueError(error_str) 
        
        attributes["AssetID"] = element.attrib.get("AssetID", None)
        return attributes


class LossCurveXMLReader(RiskXMLReader):
    """NRML parser class for loss curves"""
    
    abscissa_property = 'Loss'
    ordinate_element = 'LossCurvePE'
    abscissa_container = 'LossCurve'

    #container_tag = "%slossCurveList" % xml.NRML
    #curves_tag = "%slossCurves" % xml.NRML
    #curve_tag = "%slossCurve" % xml.NRML
    #abscissa_tag = "%sloss" % xml.NRML
    

class LossRatioCurveXMLReader(RiskXMLReader):
    """NRML parser class for loss ratio curves"""

    abscissa_property = 'Loss Ratio'
    ordinate_element = 'LossRatioCurvePE'
    abscissa_container = 'LossRatioCurve'

    #container_tag = "%slossRatioCurveList" % xml.NRML
    #curves_tag = "%slossRatioCurves" % xml.NRML
    #curve_tag = "%slossRatioCurve" % xml.NRML
    #abscissa_tag = "%slossRatio" % xml.NRML

