# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Output risk data (loss ratio curves, loss curves, and loss values)
as shaml-style XML.

"""

from lxml import etree

from opengem.logs import RISK_LOG
from opengem import writer
from opengem.xml import SHAML, GML, NSMAP
from opengem import shapes

class RiskXMLWriter(writer.FileWriter):
    curve_tag = SHAML + "Curve"
    abcissa_tag = SHAML + "PE"
    container_tag = SHAML + "RiskElementList"
    
    def write(self, point, curve_object):
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_curve_node(point, curve_object, self.parent_node)

    def write_header(self):
        """Write out the file header"""
        self.root_node = etree.Element(SHAML + "RiskResult", nsmap=NSMAP)
        config_node = etree.SubElement(self.root_node, 
                           SHAML + "Config" , nsmap=NSMAP)
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
        pos.text = "%s %s" % (str(point.y), str(point.x))
        
        pe_values = _curve_pe_as_gmldoublelist(curve_object)
        
        # This use of not None is b/c of the trap w/ ElementTree find
        # for nodes that have no child nodes.
        subnode_pe = self.root_node.find(self.abcissa_tag)
        if subnode_pe is not None:
            if subnode_pe.find(SHAML + "Values").text != pe_values:
                raise Exception("Curves must share the same Abcissa!")
        else:
            subnode_pe = etree.SubElement(self.root_node, 
                            self.abcissa_tag, nsmap=NSMAP)
            etree.SubElement(subnode_pe, 
                    SHAML + "Values", nsmap=NSMAP).text = pe_values
        
        RISK_LOG.debug("Writing xml, object is %s", curve_object)
        subnode_loss = etree.SubElement(node, SHAML + "Values", nsmap=NSMAP)
        subnode_loss.text = _curve_vals_as_gmldoublelist(curve_object)


class LossCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    curve_tag = SHAML + "LossCurve"
    abcissa_tag = SHAML + "LossCurvePE"
    container_tag = SHAML + "LossCurveList"
    

class LossRatioCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    curve_tag = SHAML + "LossRatioCurve"
    abcissa_tag = SHAML + "LossRatioCurvePE"
    container_tag = SHAML + "LossRatioCurveList"


def _curve_pe_as_gmldoublelist(curve_object):
    return " ".join(map(str, curve_object.values.values()))
    

def _curve_vals_as_gmldoublelist(curve_object):
    return " ".join(map(str, curve_object.values.keys()))