# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Output risk data (loss ratio curves, loss curves, and loss values)
as shaml-style XML.

"""

import lxml
import lxml.etree
from opengem import writer
from opengem.xml import SHAML_NS, GML_NS

SHAML = "{%s}" % SHAML_NS
GML = "{%s}" % GML_NS
NSMAP = {None : SHAML_NS, "gml" : GML_NS}

class RiskXMLWriter(writer.FileWriter):
    def write(self, cell, value):
        node = lxml.etree.Element(SHAML + "cell", nsmap=NSMAP)
        node.attrib[SHAML + 'latitude'] = str(cell.latitude)
        node.attrib[SHAML + 'longitude'] = str(cell.longitude)
        for key, val in value.items():
            subnode = lxml.etree.SubElement(node, SHAML + key)
            subnode.text = str(val)
        et = lxml.etree.ElementTree(node)
        et.write(self.file)
    