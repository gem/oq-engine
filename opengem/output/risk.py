# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Output risk data (loss ratio curves, loss curves, and loss values)
as nrml-style XML.

"""

from lxml import etree

from opengem import logs
from opengem import shapes
from opengem import writer
from opengem.xml import GML, NRML, NSMAP
from opengem import shapes

logger = logs.RISK_LOG

class RiskXMLWriter(writer.FileWriter):
    curve_tag = NRML + "Curve"
    abcissa_tag = NRML + "PE"
    container_tag = NRML + "RiskElementList"
    
    def write(self, point, curve_object):
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_curve_node(point, curve_object, self.parent_node)

    def write_header(self):
        """Write out the file header"""
        self.root_node = etree.Element(NRML + "RiskResult", nsmap=NSMAP)
        config_node = etree.SubElement(self.root_node, 
                           NRML + "Config" , nsmap=NSMAP)
        config_node.text = "Config file details go here."
        self.parent_node = etree.SubElement(self.root_node, 
                           self.container_tag , nsmap=NSMAP)

    def write_footer(self):
        """Write out the file footer"""
        et = etree.ElementTree(self.root_node)
        et.write(self.file, pretty_print=True)
    
    def _append_curve_node(self, point, curve_object, parent_node):
        node = etree.SubElement(parent_node, self.curve_tag, nsmap=NSMAP)    
        pos = etree.SubElement(node, GML + "pos", nsmap=NSMAP)
        pos.text = "%s %s" % (str(point.x), str(point.y))
        
        pe_values = _curve_pe_as_gmldoublelist(curve_object)
        
        # This use of not None is b/c of the trap w/ ElementTree find
        # for nodes that have no child nodes.
        subnode_pe = self.root_node.find(self.abcissa_tag)
        if subnode_pe is not None:
            if subnode_pe.find(NRML + "Values").text != pe_values:
                raise Exception("Curves must share the same Abcissa!")
        else:
            common_node = self.parent_node.find(NRML + "Common")
            if common_node is None:
                common_node = etree.Element(NRML + "Common", nsmap=NSMAP)
                parent_node.insert(0, common_node)  
            subnode_pe = etree.SubElement(common_node, 
                            self.abcissa_tag, nsmap=NSMAP)
            etree.SubElement(subnode_pe, 
                    NRML + "Values", nsmap=NSMAP).text = pe_values
        

        logger.debug("Writing xml, object is %s", curve_object)
        subnode_loss = etree.SubElement(node, NRML + "Values", nsmap=NSMAP)
        subnode_loss.text = _curve_vals_as_gmldoublelist(curve_object)


class LossCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    curve_tag = NRML + "LossCurve"
    abcissa_tag = NRML + "LossCurvePE"
    container_tag = NRML + "LossCurveList"
    

class LossRatioCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    curve_tag = NRML + "LossRatioCurve"
    abcissa_tag = NRML + "LossRatioCurvePE"
    container_tag = NRML + "LossRatioCurveList"


def _curve_pe_as_gmldoublelist(curve_object):
    return " ".join(map(str, curve_object.codomain()))

def _curve_vals_as_gmldoublelist(curve_object):
    return " ".join(map(str, curve_object.domain()))
