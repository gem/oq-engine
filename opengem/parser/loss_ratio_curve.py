# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from lxml import etree

from opengem import producer
from opengem import shapes


# do not use namespace for now
RISKML_NS=''

class LossRatioCurveFile(producer.FileProducer):
    """ This class parses an LossRatioCurve XML file.
    The contents of such a file is meant to be used as input for the risk 
    engine. The class is implemented as a generator. 
    For each curve element in the parsed instance document, it yields a pair of
    objects, of which the first one is a shapely.geometry object of type Point 
    (representing a geographical site as WGS84 lon/lat), and the second one
    is a dictionary with probability of exceedance-related attribute for 
    the site.
    """
    def _parse(self):
        for event, element in etree.iterparse(self.file,
                                              events=('start', 'end')):

            if event == 'start' and element.tag == 'LossRatioCurve':
                self._set_portfolio_meta(element)
            elif event == 'end' and element.tag == 'CurvePointLoss':
                yield (self._to_site(element), 
                       self._to_site_attributes(element))
 
    def _to_site(self, element):

        # lon/lat are in XML attributes 'Longitude' and 'Latitude'
        # consider them as mandatory
        try:
            lon = float(element.get('longitude').strip())
            lat = float(element.get('latitude').strip())
            return shapes.Site(lon, lat)
        except Exception:
            error_str = "element AssetInstance: no valid lon/lat coordinates"
            raise ValueError(error_str)

    def _to_site_attributes(self, element):

        site_attributes = {}

        # consider all attributes of AssetInstance element as mandatory
        for required_attribute in (('CurvePointPE', float), ('CurvePointLoss', float):
            attr_value = element.get(required_attribute[0])
            if attr_value is not None:
                site_attributes[required_attribute[0]] = \
                    required_attribute[1](attr_value)
            else:
                error_str = "element AssetInstance: missing required " \
                    "attribute %s" % required_attribute[0]
                raise ValueError(error_str) 

        try:
            site_attributes.update(self._current_loss_meta)
        except Exception:
            error_str = "root element (LossRatioCurve) is missing"
            raise ValueError(error_str)

        return site_attributes
