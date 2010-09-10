# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Output risk data (loss ratio curves, loss curves, and loss values)
as shaml-style XML.

"""

import lxml
import lxml.etree

from opengem.logs import *
from opengem import writer
from opengem.xml import SHAML_NS, GML_NS
from opengem import shapes

SHAML = "{%s}" % SHAML_NS
GML = "{%s}" % GML_NS
NSMAP = {None : SHAML_NS, "gml" : GML_NS}

class RiskXMLWriter(writer.FileWriter):
    def write(self, point, value):
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        node = lxml.etree.Element(SHAML + "cell", nsmap=NSMAP)
        node.attrib[SHAML + 'latitude'] = str(point.y)
        node.attrib[SHAML + 'longitude'] = str(point.x)
        risk_log.debug("Writing loss xml, value is %s", value)
        subnode_pe = lxml.etree.SubElement(node, SHAML + "CurvePointPE")
        subnode_pe.text = " "
        subnode_loss = lxml.etree.SubElement(node, SHAML + "CurvePointLoss")
        subnode_loss.text = " "
        for key, val in value.values.items():
            subnode_loss.text += " %s" % (val)
            subnode_pe.text += " %s" % (key)
        et = lxml.etree.ElementTree(node)
        et.write(self.file, pretty_print=True)
    