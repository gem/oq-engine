# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from lxml import etree

from opengem import producer
from opengem import region

SHAML_NS='http://shaml.org/xmlns/shaml/0.1'
GML_NS='http://www.opengis.net/gml'

class ShamlOutputFile(producer.FileProducer):
    def _parse(self):
        for event, element in etree.iterparse(self.file,
                                              events=('start', 'end')):

            if event == 'start' and element.tag == '{%s}Result' % SHAML_NS:
                self._set_result_meta(element)
            elif event == 'end' and element.tag == '{%s}Descriptor' % SHAML_NS:
                self._set_result_descriptor(element)
            elif event == 'end' and element.tag == '{%s}IML' % SHAML_NS:
                self._set_curvelist_iml(element)
            elif event == 'end' and element.tag == '{%s}Curve' % SHAML_NS:
                yield (self._to_site(element), 
                       self._to_site_attributes(element))

    def _set_result_meta(self, result_element):

        self._current_result_meta = {}

        for required_attribute in ('IMT', 'IDmodel', 'timeSpanDuration'):
            attr_value = result_element.get(required_attribute)
            if attr_value is not None:
                self._current_result_meta[required_attribute] = attr_value
            else:
                error_str = "element shaml:Result: missing required " \
                    "attribute %s" % required_attribute
                raise ValueError(error_str) 

        for optional_attribute in ('saPeriod', 'saDamping', 'calcSettingsID'):
            attr_value = result_element.get(optional_attribute)
            if attr_value is not None:
                self._current_result_meta[optional_attribute] = attr_value

    def _set_result_descriptor(self, descriptor_element):
        
        self._current_result_descriptor = {}

        # Descriptor/[endBranchLabel|aggregationType] [1]
        descriptor_endBranchLabel = descriptor_element.xpath(
            'shaml:endBranchLabel', 
            namespaces={'shaml': SHAML_NS})
        descriptor_aggregationType = descriptor_element.xpath(
            'shaml:aggregationType', 
            namespaces={'shaml': SHAML_NS})

        if (len(descriptor_endBranchLabel) == 1) and \
            (len(descriptor_aggregationType) == 0):
            self._current_result_descriptor['endBranchLabel'] = \
                descriptor_endBranchLabel[0].text.strip()
        elif (len(descriptor_endBranchLabel) == 0) and \
            (len(descriptor_aggregationType) == 1):
            self._current_result_descriptor['aggregationType'] = \
                descriptor_aggregationType[0].text.strip()
        else:
            error_str = "shaML output instance Descriptor element " \
                "is missing or broken"
            raise ValueError(error_str) 

    def _set_curvelist_iml(self, iml_element):
        try:
            self._current_curvelist_iml = {
                'IML': map(float, iml_element.text.strip().split()) }
        except Exception:
            error_str = "invalid shaML HazardCurveList IML array"
            raise ValueError(error_str)

    def _to_site(self, element):
        pos_el = element.xpath('shaml:Site/shaml:Site/gml:pos',
            namespaces={'shaml': SHAML_NS, 'gml': GML_NS})
        try:
            coord = map(float, pos_el[0].text.strip().split())
            return region.Point(coord[0], coord[1])
        except Exception:
            error_str = "shaML point coordinate error: %s" % \
                ( pos_el[0].text )
            raise ValueError(error_str)

    def _to_site_attributes(self, element):

        site_attributes = {}

        value_el = element.xpath('shaml:Site/shaml:Values', 
            namespaces={'shaml': SHAML_NS})
        try:
            site_attributes['Values'] = map(float, 
                value_el[0].text.strip().split())
        except Exception:
            error_str = "invalid shaML site values array"
            raise ValueError(error_str)

        vs30_el = element.xpath('shaml:Site/shaml:vs30', 
            namespaces={'shaml': SHAML_NS})
        try:
            site_attributes['vs30'] = float(vs30_el[0].text)
        except Exception:
            error_str = "invalid shaML site vs30 value"
            raise ValueError(error_str) 

        for optional_attribute in ('minProb', 'maxProb'):
            try:
                site_attributes[optional_attribute] = \
                    float(element.get(optional_attribute))
            except Exception:
                pass

        site_attributes.update(self._current_result_meta)
        site_attributes.update(self._current_result_descriptor)
        site_attributes.update(self._current_curvelist_iml)

        return site_attributes
