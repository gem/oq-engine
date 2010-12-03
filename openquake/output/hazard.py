# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
This module provides classes that serialize hazard-related objects
to NRML format.

Hazard curves:

For the serialization of hazard curves, it currently takes 
all the lxml object model in memory
due to the fact that curves can be grouped by IDmodel and
IML. Couldn't find a way to do so writing an object at a
time without making a restriction to the order on which
objects are received.

Ground Motion Fields (GMFs):

GMFs are serialized per object (=Site) as implemented in the base class.
"""

from lxml import etree

from openquake import logs
from openquake import shapes
from openquake import writer

from openquake.xml import NSMAP, NRML, GML

LOGGER = logs.HAZARD_LOG

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


class GMFXMLWriter(writer.FileWriter):
    """This class serializes ground motion field (GMF) informatiuon
    to NRML format.

    As of now, only the field information is supported. GMPEParameters is
    serialized as a stub with the only attribute that is formally required
    (but doesn't have a useful definition in the schema).
    Rupture information and full GMPEParameters are currently 
    not supported."""

    root_tag = NRML + "HazardResult"
    config_tag = NRML + "Config"
    gmpe_params_tag = NRML + "GMPEParameters"
    container_tag = NRML + "GroundMotionFieldSet"
    field_tag = NRML + "field"
    site_tag = NRML + "site"
    pos_tag = GML + "pos"
    ground_motion_attr = "groundMotion"

    def write(self, point, val):
        """Writes GMF for one site.

        point must be of type shapes.Site
        val is a dictionary:

        {'groundMotion': 0.8}
        """
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_curve_node(point, val, self.parent_node)

    def write_header(self):
        """Write out the file header"""
        self.root_node = etree.Element(self.root_tag, nsmap=NSMAP)
        config_node = etree.SubElement(self.root_node, self.config_tag, 
                                       nsmap=NSMAP)
        config_node.text = "Config file details go here."

        gmpe_params_node = etree.SubElement(self.root_node, 
                                            self.gmpe_params_tag, nsmap=NSMAP)
        
        # add required attribute stub
        gmpe_params_node.attrib['vs30method'] = 'None'

        self.parent_node = etree.SubElement(self.root_node, 
                           self.container_tag , nsmap=NSMAP)

    def write_footer(self):
        """Write out the file footer"""
        et = etree.ElementTree(self.root_node)
        et.write(self.file, pretty_print=True, xml_declaration=True,
                 encoding="UTF-8")
    
    def _append_curve_node(self, point, val, parent_node):
        
        # TODO(fab): support rupture element (not implemented so far)
        # TODO(fab): support full GMPEParameters (not implemented so far)

        # field element
        field_node = etree.SubElement(parent_node, self.field_tag, 
                                      nsmap=NSMAP)
        outer_site_node = etree.SubElement(field_node, self.site_tag, 
                                           nsmap=NSMAP)
        inner_site_node = etree.SubElement(outer_site_node, self.site_tag,
                                           nsmap=NSMAP)
        inner_site_node.attrib[self.ground_motion_attr] = str(
            val[self.ground_motion_attr])
        
        pos_node = etree.SubElement(inner_site_node, self.pos_tag, 
                                    nsmap=NSMAP)
        pos_node.text = "%s %s" % (str(point.x), str(point.y))

