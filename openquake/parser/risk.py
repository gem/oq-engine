# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""This module contains a class that parses NRML instance document files
for the output of risk computations. At the moment, loss and loss curve data
is supported. The root element of such NRML instance documents 
is <RiskResult>.
"""

from lxml import etree

from openquake import producer
from openquake import shapes
from openquake.xml import NRML_NS, GML_NS, NRML

class NrmlFile(producer.FileProducer):
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

    def __init__(self, path, mode='loss'):
        self.mode = mode

        self.ordinate_property = 'Probability of Exceedance'
        self.abscissa_element = 'Values'

        self.abscissa_output_key = 'Values'
        self.ordinate_output_key = 'POE'
        self.property_output_key = 'Property'

        if self.mode == 'loss_ratio':
            self.abscissa_property = 'Loss Ratio'
            self.ordinate_element = 'LossRatioCurvePE'
            self.abscissa_container = 'LossRatioCurve'
        else:
            self.abscissa_property = 'Loss'
            self.ordinate_element = 'LossCurvePE'
            self.abscissa_container = 'LossCurve'

        super(NrmlFile, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'end' and element.tag == NRML + self.abscissa_container:
                yield (self._to_site(element), 
                       self._to_attributes(element))

    def _to_site(self, element):
        """Convert current GML attributes to Site object."""
        # lon/lat are in XML attributes 'Longitude' and 'Latitude'
        # consider them as mandatory
        pos_el = element.xpath("gml:pos", namespaces={"gml":GML_NS})
        coord = [float(x) for x in pos_el[0].text.strip().split()]
        return shapes.Site(coord[0], coord[1])

    def _to_attributes(self, element):
        
        attributes = {self.property_output_key: self.abscissa_property}
        
        float_strip = lambda x: map(float, x[0].text.strip().split())
        # TODO(JMC): This is hardly efficient, but it's simple for the moment...
        
        for (child_el, child_key, etl) in (
            ('nrml:%s' % self.abscissa_element, self.abscissa_output_key, 
                float_strip),
            ('../nrml:Common/nrml:%s/nrml:Values' % self.ordinate_element,
                self.ordinate_output_key, float_strip)):
            
            child_node = element.xpath(child_el, 
                namespaces={"gml":GML_NS,"nrml":NRML_NS})

            try:
                attributes[child_key] = etl(child_node)
            except Exception:
                error_str = "invalid or missing %s value" % child_key
                raise ValueError(error_str) 
        
        attributes["AssetID"] = element.attrib.get("AssetID", None)
        return attributes

