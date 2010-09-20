# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Output risk data (loss ratio curves, loss curves, and loss values)
as shaml-style XML.

"""

import lxml
import lxml.etree
from lxml.builder import ElementMaker

from opengem.logs import RISK_LOG
from opengem import writer
from opengem.xml import SHAML_NS, GML_NS
from opengem import shapes

SHAML = "{%s}" % SHAML_NS
GML = "{%s}" % GML_NS
NSMAP = {None : SHAML_NS, "gml" : GML_NS}

class RiskXMLWriter(writer.FileWriter):
    pass


class LossCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    
    def write(self, point, value):
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        node = lxml.etree.SubElement(self.parent_node, SHAML + "cell", nsmap=NSMAP)
        node.attrib[SHAML + 'latitude'] = str(point.y)
        node.attrib[SHAML + 'longitude'] = str(point.x)
        RISK_LOG.debug("Writing loss xml, value is %s", value)
        subnode_pe = lxml.etree.SubElement(node, SHAML + "CurvePointPE")
        subnode_pe.text = " "
        subnode_loss = lxml.etree.SubElement(node, SHAML + "CurvePointLoss")
        subnode_loss.text = " "
        for key, val in value.values.items():
            subnode_loss.text += " %s" % (key)
            subnode_pe.text += " %s" % (val)
    
    def write_header(self):
        """Write out the file header"""
        self.root_node = lxml.etree.Element(SHAML + "RiskResult", nsmap=NSMAP)
        self.parent_node = lxml.etree.SubElement(self.root_node, SHAML + "LossCurveList", nsmap=NSMAP)

    def write_footer(self):
        """Write out the file footer"""
        et = lxml.etree.ElementTree(self.root_node)
        et.write(self.file, pretty_print=True)
