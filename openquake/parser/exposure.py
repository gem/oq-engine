# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""Parsers to read exposure files, including exposure portfolios.
These can include building, population, critical infrastructure,
and other asset classes."""

from lxml import etree

from openquake import producer
from openquake import shapes
from openquake.xml import NRML, GML_OLD

# do not use namespace for now
RISKML_NS = ''


def _to_site(element):
    """Convert current GML attributes to Site object"""
    # lon/lat are in XML attribute gml:pos
    # consider them as mandatory

    pos = element.find("%spos" % GML_OLD).text
    
    try:
        lat, lon = [float(x.strip()) for x in pos.split()]
        return shapes.Site(lon, lat)
    except Exception:
        error_str = "element AssetInstance: no valid lon/lat coordinates"
        raise ValueError(error_str)


class ExposurePortfolioFile(producer.FileProducer):
    """ This class parses an ExposurePortfolio XML (part of riskML?) file.
    The contents of such a file is meant to be used as input for the risk 
    engine. The class is implemented as a generator. 
    For each 'AssetInstance' element in the parsed 
    instance document, it yields a pair of objects, of which the
    first one is a shapely.geometry object of type Point (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with exposure-related attribute values for this site.
    
    The attribute dictionary looks like
    {'PortfolioID': 'PAV01',
     'PortfolioDescription': 'Collection of existing buildings in downtown Pavia',
     'AssetID': '01',
     'AssetDescription': 'Moment-resisting non-ductile concrete frame low rise',
     'AssetValue': 150000,
     'VulnerabilityFunction': 'RC/DMRF-D/LR'
    }

    Note: at the time of writing this class the author has no access to the
    XML Schema, so all XML attributes from the example instance documents are
    assumed to be mandatory.

    """

    REQUIRED_ATTRIBUTES = (('PortfolioID', str), 
                           ('PortfolioDescription', str))

    def __init__(self, path):
        super(ExposurePortfolioFile, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):

            if event == 'start' and element.tag == \
                    '%sExposureParameters' % NRML:

                self._set_meta(element)
            elif event == 'end' and element.tag == '%sAssetInstance' % NRML:
                yield (_to_site(element), 
                       self._to_site_attributes(element))

    def _to_site_attributes(self, element):
        """Build a dict of all node attributes"""
        site_attributes = {}

        site_attributes["AssetID"] = element.find("%sAssetID" % NRML).text
        site_attributes["AssetValue"] = float(element.find(
                "%sAssetValue" % NRML).text)

        # consider all attributes of AssetInstance element as mandatory
        for required_attribute in (('AssetDescription', str),
                                   ('VulnerabilityFunction', str)):
            attr_value = element.get(required_attribute[0])
            if attr_value is not None:
                site_attributes[required_attribute[0]] = \
                    required_attribute[1](attr_value)
            else:
                error_str = "element AssetInstance: missing required " \
                    "attribute %s" % required_attribute[0]
                raise ValueError(error_str) 

        try:
            site_attributes.update(self._current_meta)
        except Exception:
            error_str = "root element (ExposurePortfolio) is missing"
            raise ValueError(error_str)

        return site_attributes
