# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""Parsers to read exposure files, including exposure portfolios.
These can include building, population, critical infrastructure,
and other asset classes."""

from lxml import etree

from openquake import producer
from openquake import shapes
from openquake.xml import NRML, GML

# do not use namespace for now
RISKML_NS = ''


def _to_site(element):
    """Convert current GML attributes to Site object

    We want to extract the value of <gml:pos>. We expect the input element to be
    an 'assetDefinition' and have a child element structured like this:
    
    <site>
        <gml:Point srsName="epsg:4326">
            <gml:pos>9.15000 45.16667</gml:pos>
        </gml:Point>
    </site>
    """
    # lon/lat are in XML attribute gml:pos
    # consider them as mandatory

    try: 
        site_elem = element.find('%ssite' % NRML)
        point_elem = site_elem.find('%sPoint' % GML)
        pos = point_elem.find('%spos' % GML).text
        lon, lat = [float(x.strip()) for x in pos.split()]

        del element
        return shapes.Site(lon, lat)
    except Exception:
        error_str = "element assetDefintion: no valid lon/lat coordinates"
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
    
    The attribute dictionary looks like this:
    {'listID': 'PAV01',
     'listDescription': 'Collection of existing building in ' \
                        'downtown Pavia',
     'assetID': 'asset_02',
     'assetDescription': 'Moment-resisting non-ductile concrete ' \
                         'frame low rise',
     'vulnerabilityFunctionReference': 'RC/DMRF-D/LR',
     'structureCategory': 'RC-LR-PC',
     'assetValue': 250000.0,
     'assetValueUnit': 'EUR'}


    Note: assetDescription is optional.
    """

    def __init__(self, path):
        super(ExposurePortfolioFile, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):

            if event == 'start' and element.tag == \
                    '%sexposureList' % NRML:
                # we need to get the exposureList id and description
                id = element.get('%sid' % GML)
                self._current_meta['listID'] = str(id)

                desc = element.find('%sdescription' % GML)
                if desc is not None:
                    self._current_meta['listDescription'] = str(desc.text)

            elif event == 'end' and element.tag == '%sassetDefinition' % NRML:
                yield (_to_site(element), 
                       self._to_site_attributes(element))

    def _to_site_attributes(self, element):
        """Build a dict of all node attributes"""
        site_attributes = {}

        # consider all attributes of assetDefinition element as mandatory

        site_attributes['assetID'] = element.get('%sid' % GML)
        asset_value = element.find('%sassetValue' % NRML)
        try:
            site_attributes['assetValue'] = float(asset_value.text)
        except Exception:
            error_str = 'element assetDefinition: no valid assetValue'
            raise ValueError(error_str)
        site_attributes['assetValueUnit'] = asset_value.get('unit')

        # all of these attributes are in the NRML namespace
        for (required_attr, attr_type) in (('assetDescription', str),
                                   ('vulnerabilityFunctionReference', str),
                                   ('structureCategory', str)):
            attr_value = element.find('%s%s' % (NRML, required_attr)).text
            if attr_value is not None:
                site_attributes[required_attr] = \
                    attr_type(attr_value)
            else:
                error_str = "element assetDefinition: missing required " \
                    "attribute %s" % required_attr
                raise ValueError(error_str) 

        site_attributes.update(self._current_meta)

        return site_attributes
