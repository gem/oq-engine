# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
This modules serializes objects in nrml format.

It currently takes all the lxml object model in memory
due to the fact that curves can be grouped by IDmodel and
IML. Couldn't find a way to do so writing an object at a
time without making a restriction to the order on which
objects are received.

"""

from lxml import etree

from openquake import writer
from openquake.xml import NSMAP, NRML, GML

class HazardCurveXMLWriter(writer.FileWriter):
    """This class writes an hazard curve into the nrml format."""

    def __init__(self, path):
        super(HazardCurveXMLWriter, self).__init__(path)

        self.result_tag = None
        self.curves_per_branch_label = {}

    def close(self):
        """Overrides the default implementation writing all the
        collected lxml object model to the stream."""

        if self.result_tag is None:
            error = "You need to add at least a curve to build a valid output!"
            raise RuntimeError(error)

        self.file.write(etree.tostring(self.result_tag, 
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8"))
                
        super(HazardCurveXMLWriter, self).close()
            
    def write(self, point, values):
        """Writes an hazard curve.
        
        point must be of type shapes.Site
        values is a dictionary that matches the one produced by the
        parser nrml.NrmlFile
        
        """
        
        if self.result_tag is None:
            # <nrml:Result />
            self.result_tag = etree.Element(NRML + "HazardResult", nsmap=NSMAP)
            
            # <nrml:Config />
            config_tag = etree.SubElement(self.result_tag, NRML + "Config")
            
            # <nrml:HazardProcessing />
            hazard_processing_tag = etree.SubElement(config_tag, NRML + 
                "HazardProcessing")
            
            hazard_processing_tag.attrib["timeSpanDuration"] = str(values
                ["timeSpanDuration"])
                
            hazard_processing_tag.attrib["IDmodel"] = str(values["IDmodel"])
            
            hazard_processing_tag.attrib["saPeriod"] = \
                str(values.get("saPeriod",""))
            hazard_processing_tag.attrib["saDamping"] = \
                str(values.get("saDamping",""))

        try:
            hazard_curve_list_tag = \
                self.curves_per_branch_label[values["endBranchLabel"]]
        except KeyError:
            # <nrml:HazardCurveList />
            hazard_curve_list_tag = etree.SubElement(self.result_tag, 
                NRML + "HazardCurveList")
            hazard_curve_list_tag.attrib["endBranchLabel"] = \
                str(values["endBranchLabel"])
                
             # <nrml:IMT />
            common_tag = etree.Element(NRML + "Common", nsmap=NSMAP)
            hazard_curve_list_tag.insert(0, common_tag)    
            # <nrml:IMT />
            imt_tag = etree.SubElement(common_tag, NRML + "IMT")
            imt_tag.text = str(values["IMT"])
            
            # <nrml:IMLValues />
            iml_tag = etree.SubElement(common_tag, NRML + "IMLValues")
            iml_tag.text = " ".join([str(x) for x in values.get("IMLValues")])
            
            self.curves_per_branch_label[values["endBranchLabel"]] = \
                hazard_curve_list_tag
        
        # <nrml:HazardCurve />
        curve_tag = etree.SubElement(hazard_curve_list_tag, 
                NRML + "HazardCurve")

        # <gml:pos />
        gml_tag = etree.SubElement(curve_tag, GML + "pos")
        gml_tag.text = " ".join([str(x) for x in (point.longitude, 
                point.latitude)])

        # <nrml:Values />
        curve_values_tag = etree.SubElement(curve_tag, NRML + "Values")
        curve_values_tag.text = " ".join([str(x) for x in values["Values"]])
