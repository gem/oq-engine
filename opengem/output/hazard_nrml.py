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

from opengem import writer
from opengem.xml import NSMAP, NRML, GML

class HazardCurveXMLWriter(writer.FileWriter):
    """This class writes an hazard curve into the nrml format."""

    def __init__(self, path):
        super(HazardCurveXMLWriter, self).__init__(path)
        self.result_list_tag = etree.Element(
                NRML + "HazardResult", nsmap=NSMAP)

        self.curves_per_iml = {}
        self.curves_per_model_id = {}

    def close(self):
        """Overrides the default implementation writing all the
        collected lxml object model to the stream."""

        if not len(self.result_list_tag):
            error = "You need to add at least a curve to build a valid output!"
            raise RuntimeError(error)

        self.file.write(etree.tostring(self.result_list_tag, 
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8"))
                
        super(HazardCurveXMLWriter, self).close()

    def _add_curve_to_proper_set(self, point, values, hazard_curve_list_tag):
        """Adds the curve to the proper set depending on the IML values."""
        
        try:
            list_tag = self.curves_per_iml[str(values["IML"])]
        except KeyError:
            curve_list_tag = etree.SubElement(hazard_curve_list_tag, NRML + "HazardCurve")
        
        # <gml:pos />
        gml_tag = etree.SubElement(curve_list_tag, GML + "pos")
        gml_tag.text = " ".join(map(str, (point.longitude, 
            point.latitude)))
            
        # <nrml:Values />
        curve_values_tag = etree.SubElement(curve_list_tag, NRML + "Values")
        curve_values_tag.text = " ".join(map(str, values["Values"]))
            
        # <nrml:IML />
        iml_tag = etree.SubElement(hazard_curve_list_tag, NRML + "IMLValues")
        iml_tag.text = " ".join(map(str, values.get("IML","")))
            

    def write(self, point, values):
        """Writes an hazard curve.
        
        point must be of type shapes.Site
        values is a dictionary that matches the one produced by the
        parser nrml.NrmlFile
        
        """
        
        try:
            hazard_curve_list_tag = self.curves_per_model_id[values["endBranchLabel"]]
        except KeyError:
            # <nrml:Result />
            result_tag = etree.SubElement(self.result_list_tag, NRML + "Config")

            # <nrml:HazardProcessing />
            HazardProcessing_tag = etree.SubElement(result_tag, NRML + 
                "HazardProcessing")
            HazardProcessing_tag.attrib["timeSpanDuration"] = str(values
                ["timeSpanDuration"])
            HazardProcessing_tag.attrib["IDmodel"] = str(values["IDmodel"])
            HazardProcessing_tag.attrib["saPeriod"] = str(values.get("saPeriod",""))
            HazardProcessing_tag.attrib["saDamping"] = str(values.get("saDamping",""))
            
             # <nrml:IML values />
            imt_tag = etree.SubElement(HazardProcessing_tag, NRML + "IMT")
            imt_tag.text = str(values["IMT"])
            
            # <nrml:Values />
            hazard_curve_list_tag = etree.SubElement(self.result_list_tag, NRML + "HazardCurveList")
            hazard_curve_list_tag.attrib["endBranchLabel"] = str(values["endBranchLabel"])

            
            self.curves_per_model_id[values["endBranchLabel"]] = hazard_curve_list_tag
        
        self._add_curve_to_proper_set(point, values, hazard_curve_list_tag)
