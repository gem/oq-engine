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


class RiskXMLReader(producer.FileProducer):
    """ This class parses a NRML loss/loss ratio curve file. 
    The class is implemented as a generator. 
    For each curve element in the parsed 
    instance document, it yields a pair of objects, of which the
    first one is a shapes object of type Site (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with risk-related attribute values for this site.
    
    The attribute dictionary looks like
    {'nrml_id': 'nrml',
     'result_id': 'rr',
     'list_id': 'list_1',
     'assetID': 'a100',
     'poE': [0.2, 0.02, ...], 
     'loss': [0.0, 1280.0, ...], # for loss
     'lossRatio': [0.0, 0.1, ...], # for loss ratio
     'endBranchLabel': '1_1',
     'property': 'Loss' # 'Loss Ratio'
    }
    """

    # these tag names and properties have to be redefined in the 
    # derived classes for loss and loss ratio
    container_tag = None
    curves_tag = None
    curve_tag = None
    abscissa_tag = None
    abscissa_property = None

    # common names
    ordinate_property = xml.RISK_CURVE_ORDINATE_PROPERTY
    ordinate_tag = xml.RISK_POE_TAG

    property_output_key = 'property'

    def __init__(self, path):
        self.abscissa_output_key = xml.strip_namespace_from_tag(
            self.abscissa_tag, xml.NRML)
        self.ordinate_output_key = xml.strip_namespace_from_tag(
            self.ordinate_tag, xml.NRML)
        super(RiskXMLReader, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'start' and element.tag == xml.NRML_ROOT_TAG:
                self._to_id_attributes(element)

            elif event == 'start' and element.tag == xml.RISK_ASSET_TAG:
                self._to_asset_attributes(element)

            elif event == 'end' and element.tag == self.curve_tag:

                curr_attributes = self._to_curve_attributes(element)

                # free memory of just parsed element
                element.clear()
                yield (self._current_site, curr_attributes)

    def _to_id_attributes(self, element):
        """Collect id attributes from root element."""

        self._current_id_meta = {}

        # get nrml id
        self._current_id_meta['nrml_id'] = \
            element.attrib[xml.GML_ID_ATTR_NAME]

        # get riskResult id
        curr_el = element.find('.//%s' % xml.RISK_RESULT_TAG)
        self._current_id_meta['result_id'] = \
            curr_el.attrib[xml.GML_ID_ATTR_NAME]

        # get lossCurveList id
        curr_el = element.find('.//%s' % self.container_tag)
        self._current_id_meta['list_id'] = \
            curr_el.attrib[xml.GML_ID_ATTR_NAME]

    def _to_asset_attributes(self, element):
        """Collect metadata attributes for new asset element."""

        # assetID
        self._current_asset_meta = {
            'assetID': element.attrib[xml.GML_ID_ATTR_NAME]}

        # get site
        lon, lat = xml.lon_lat_from_site(element)
        self._current_site = shapes.Site(lon, lat)

    def _to_curve_attributes(self, element):
        """Build an attributes dict from NRML curve element (this can be
        'lossCurve' or 'lossRatioCurve'.
        This element contains abscissae (loss/loss ratio) and ordinate 
        (PoE) values of a curve.
        """
        
        attributes = {self.property_output_key: self.abscissa_property}

        abscissa_el_txt = element.findtext(self.abscissa_tag)
        attributes[self.abscissa_output_key] = [float(x) \
            for x in abscissa_el_txt.strip().split()]

        ordinate_el_txt = element.findtext(self.ordinate_tag)
        attributes[self.ordinate_output_key] = [float(x) \
            for x in ordinate_el_txt.strip().split()]

        if xml.RISK_END_BRANCH_ATTR_NAME in element.attrib: 
            attributes[xml.RISK_END_BRANCH_ATTR_NAME] = \
                element.attrib[xml.RISK_END_BRANCH_ATTR_NAME]
 
        attributes.update(self._current_id_meta)
        attributes.update(self._current_asset_meta)
        return attributes


class LossCurveXMLReader(RiskXMLReader):
    """NRML parser class for loss curves"""
    container_tag = xml.RISK_LOSS_CONTAINER_TAG
    curves_tag = xml.RISK_LOSS_CURVES_TAG
    curve_tag = xml.RISK_LOSS_CURVE_TAG
    abscissa_tag = xml.RISK_LOSS_ABSCISSA_TAG
    abscissa_property = xml.RISK_LOSS_ABSCISSA_PROPERTY

class LossRatioCurveXMLReader(RiskXMLReader):
    """NRML parser class for loss ratio curves"""
    container_tag = xml.RISK_LOSS_RATIO_CONTAINER_TAG
    curves_tag = xml.RISK_LOSS_RATIO_CURVES_TAG
    curve_tag = xml.RISK_LOSS_RATIO_CURVE_TAG
    abscissa_tag = xml.RISK_LOSS_RATIO_ABSCISSA_TAG
    abscissa_property = xml.RISK_LOSS_RATIO_ABSCISSA_PROPERTY
