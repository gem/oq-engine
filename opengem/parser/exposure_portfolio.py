# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from lxml import etree
import sys
sys.path.append("/Users/benwyss/Projects/opengem")
from opengem import producer
from opengem import region


# do not use namespace for now
RISKML_NS=''

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
    assumed to be mandatory
    """
    def _parse(self):
        for event, element in etree.iterparse(self.file,
                                              events=('start', 'end')):

            if event == 'start' and element.tag == 'ExposurePortfolio':
                self._set_portfolio_meta(element)
            elif event == 'end' and element.tag == 'AssetInstance':
                yield (self._to_site(element), 
                       self._to_site_attributes(element))

    def _set_portfolio_meta(self, portfolio_element):

        self._current_portfolio_meta = {}

        for required_attribute in (('PortfolioID', str), 
                                   ('PortfolioDescription', str)):
            attr_value = portfolio_element.get(required_attribute[0])
            if attr_value is not None:
                self._current_portfolio_meta[required_attribute[0]] = \
                    required_attribute[1](attr_value)
            else:
                error_str = "element ExposurePortfolio: missing required " \
                    "attribute %s" % required_attribute[0]
                raise ValueError(error_str) 

    def _to_site(self, element):

        # lon/lat are in XML attributes 'Longitude' and 'Latitude'
        # consider them as mandatory
        try:
            lon = float(element.get('Longitude').strip())
            lat = float(element.get('Latitude').strip())
            return region.Point(lon, lat)
        except Exception:
            error_str = "element AssetInstance: no valid lon/lat coordinates"
            raise ValueError(error_str)

    def _to_site_attributes(self, element):

        site_attributes = {}

        # consider all attributes of AssetInstance element as mandatory
        for required_attribute in (('AssetID', str), 
                                   ('AssetDescription', str),
                                   ('AssetValue', float),
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
            site_attributes.update(self._current_portfolio_meta)
        except Exception:
            error_str = "root element (ExposurePortfolio) is missing"
            raise ValueError(error_str)

        return site_attributes

    def filter(self, region_constraint, attribute_constraint=None):
        for next in iter(self):
            if (attribute_constraint is not None and \
                    region_constraint.match(next[0]) and \
                    attribute_constraint.match(next[1])) or \
               (attribute_constraint is None and \
                    region_constraint.match(next[0])):
                yield next


class ExposurePortfolioConstraint(object):
    """ This class represents a constraint that can be used to filter
    AssetInstance elements from an ExposurePortfolio XML instance document
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