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

   # REQUIRED_ATTRIBUTES = (('IMLValues', str), ('IDmodel', str),
    #        ('timeSpanDuration', float))
            
   # OPTIONAL_ATTRIBUTES = (('saPeriod', float),
  #          ('saDamping', float))

    def __init__(self, path):
        super(NrmlFile, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
                
            if event == 'start' and element.tag == 'HazardResult':
                self._set_meta(element)
            elif event == 'end' and element.tag == 'Config':
                self._set_config(element)
            elif event == 'end' and element.tag == 'HazardCurveList':
                self._to_site_attributes(element),
                self._to_site(element)
            elif event == 'end' and element.tag == 'IMLValues':
                yield (self._curvelist_iml(element))
                
    def _set_curvelist_iml(self, iml_element):
        try:
            self._current_curvelist_iml = {
                'IMLValues': map(float, iml_element.text.strip().split()) }
        except Exception:
            error_str = "invalid nrml HazardCurveList IML array"
            raise ValueError(error_str)

    def _to_site(self, element):
        pos_el = element.xpath('HazardCurve/gml:pos',
            namespaces={'gml': GML_NS})
        try:
            coord = map(float, pos_el[0].text.strip().split())
            return shapes.Site(coord[0], coord[1])
        except Exception:
            error_str = "nrml point coordinate error: %s" % \
                ( pos_el[0].text )
            raise ValueError(error_str)
       

    def _to_site_attributes(self, element):

        site_attributes = {}

        value_el = element.xpath('HazardCurve/Values')
        
        try:
            site_attributes['Values'] = map(float, 
                value_el[0].text.strip().split())
        except Exception:
            error_str = "invalid or missing nrml site values array"
            raise ValueError(error_str)

        for (attribute_chunk, ref_string) in (
            (self._current_result_config, "HazardResult/Config"),
            (self._current_curvelist_iml, "HazardCurveList/IMLValues")):

            try:
                site_attributes.update(attribute_chunk)
            except Exception:
                error_str = "missing nrml element: %s" % ref_string
                raise ValueError(error_str)
                
        #print "site attributes is %s" % (site_attributes)

        return site_attributes
