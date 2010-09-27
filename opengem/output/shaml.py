# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
This modules serializes objects in shaml format.

It currently takes all the lxml object model in memory
due to the fact that curves can be grouped by IDmodel and
IML. Couldn't find a way to do so writing an object at a
time without making a restriction to the order on which
objects are received.

"""

from lxml import etree

from opengem import writer
from opengem.xml import NSMAP, SHAML, GML

class HazardCurveXMLWriter(writer.FileWriter):
    """This class writes an hazard curve into the shaml format."""

    def __init__(self, path):
        super(HazardCurveWriter, self).__init__(path)
        self.result_list_tag = etree.Element(
                SHAML + "HazardResultList", nsmap=NSMAP)

        self.curves_per_iml = {}
        self.curves_per_model_id = {}

    def close(self):
        """Overrides the default implementation writing all the
        collected lxml object model to the stream."""

        self.file.write(etree.tostring(self.result_list_tag, 
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8"))
                
        super(HazardCurveWriter, self).close()

    def _add_curve_to_proper_set(self, point, values, values_tag):
        """Adds the curve to the proper set depending on the IML values."""
        
        try:
            list_tag = self.curves_per_iml[str(values["IML"])]
        except KeyError:
            curve_list_tag = etree.SubElement(
                    values_tag, SHAML + "HazardCurveList")
            
            # <shaml:IML />
            iml_tag = etree.SubElement(curve_list_tag, SHAML + "IML")
            iml_tag.text = " ".join(map(str, values["IML"]))
            
            # <shaml:List />
            list_tag = etree.SubElement(curve_list_tag, SHAML + "List")
            
            self.curves_per_iml[str(values["IML"])] = list_tag

        # <shaml:Curve />
        curve_tag = etree.SubElement(list_tag, SHAML + "Curve")
        curve_tag.attrib["maxProb"] = str(values["maxProb"])
        curve_tag.attrib["minProb"] = str(values["minProb"])

        # <shaml:Site />
        site_tag = etree.SubElement(curve_tag, SHAML + "Site")

        # <shaml:Site />
        inner_site_tag = etree.SubElement(site_tag, SHAML + "Site")

        # <gml:pos />
        gml_tag = etree.SubElement(inner_site_tag, GML + "pos")
        gml_tag.text = " ".join(map(str, (point.longitude, point.latitude)))

        # <shaml:Values />
        curve_values_tag = etree.SubElement(site_tag, SHAML + "Values")
        curve_values_tag.text = " ".join(map(str, values["Values"]))

        # <shaml:vs30 />
        vs30_tag = etree.SubElement(site_tag, SHAML + "vs30")
        vs30_tag.text = str(values["vs30"])

    def write(self, point, values):
        """Writes an hazard curve.
        
        point must be of type shapes.Site
        values is a dictionary that matches the one produced by the
        parser shaml_output.ShamlOutputFile
        
        """
        
        try:
            values_tag = self.curves_per_model_id[values["IDmodel"]]
        except KeyError:
            # <shaml:Result />
            result_tag = etree.SubElement(
                    self.result_list_tag, SHAML + "Result")
  
            result_tag.attrib["timeSpanDuration"] = \
                    str(values["timeSpanDuration"])

            result_tag.attrib["IDmodel"] = str(values["IDmodel"])
            result_tag.attrib["IMT"] = str(values["IMT"])

            # <shaml:Descriptor />
            descriptor_tag = etree.SubElement(result_tag, SHAML + "Descriptor")
        
            # <shaml:endBranchLabel />
            end_branch_label_tag = etree.SubElement(
                    descriptor_tag, SHAML + "endBranchLabel")

            end_branch_label_tag.text = str(values["endBranchLabel"])

            # <shaml:Values />
            values_tag = etree.SubElement(result_tag, SHAML + "Values")
            
            self.curves_per_model_id[values["IDmodel"]] = values_tag
        
        self._add_curve_to_proper_set(point, values, values_tag)
