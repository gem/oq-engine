# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Output risk data (loss ratio curves, loss curves, and loss values)
as nrml-style XML.

"""

from lxml import etree

from openquake import logs
from openquake import shapes
from openquake import writer
from openquake.xml import GML_OLD, NSMAP_OLD, NRML_OLD

LOGGER = logs.RISK_LOG

class RiskXMLWriter(writer.FileWriter):
    """This class writes a risk curve into the nrml format."""
    curve_tag = NRML_OLD + "Curve"
    abcissa_tag = NRML_OLD + "PE"
    container_tag = NRML_OLD + "RiskElementList"
    
    def write(self, point, val):
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_curve_node(point, val, self.parent_node)

    def write_header(self):
        """Write out the file header"""
        self.root_node = etree.Element(NRML_OLD + "RiskResult", nsmap=NSMAP_OLD)
        config_node = etree.SubElement(self.root_node, 
                           NRML_OLD + "Config" , nsmap=NSMAP_OLD)
        config_node.text = "Config file details go here."

        #pylint: disable=W0201
        self.parent_node = etree.SubElement(self.root_node, 
                           self.container_tag , nsmap=NSMAP_OLD)

    def write_footer(self):
        """Write out the file footer"""
        et = etree.ElementTree(self.root_node)
        et.write(self.file, pretty_print=True)
    
    def _append_curve_node(self, point, val, parent_node):
        """ This method appends a curve node to the parent node """

        (curve_object, asset_object) = val
        node = etree.SubElement(parent_node, self.curve_tag, nsmap=NSMAP_OLD)
        node.attrib['AssetID'] = asset_object['AssetID']    
        pos = etree.SubElement(node, GML_OLD + "pos", nsmap=NSMAP_OLD)
        pos.text = "%s %s" % (str(point.x), str(point.y))
        
        pe_values = _curve_pe_as_gmldoublelist(curve_object)
        
        # This use of not None is b/c of the trap w/ ElementTree find
        # for nodes that have no child nodes.
        subnode_pe = self.parent_node.find(
            NRML_OLD + "Common/" + self.abcissa_tag)
        if subnode_pe is not None:
            if subnode_pe.find(NRML_OLD + "Values").text != pe_values:
                LOGGER.error("Abcissa doesn't match between \n %s \n %s"
                    % (subnode_pe.find(NRML_OLD + "Values").text, pe_values))
                raise Exception("Curves must share the same Abcissa!")
        else:
            common_node = self.parent_node.find(NRML_OLD + "Common")
            if common_node is None:
                common_node = etree.Element(NRML_OLD + "Common", nsmap=NSMAP_OLD)
                parent_node.insert(0, common_node)  
            subnode_pe = etree.SubElement(common_node, 
                            self.abcissa_tag, nsmap=NSMAP_OLD)
            etree.SubElement(subnode_pe, 
                    NRML_OLD + "Values", nsmap=NSMAP_OLD).text = pe_values

        LOGGER.debug("Writing xml, object is %s", curve_object)
        subnode_loss = etree.SubElement(
            node, NRML_OLD + "Values", nsmap=NSMAP_OLD)
        subnode_loss.text = _curve_vals_as_gmldoublelist(curve_object)


class LossCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    curve_tag = NRML_OLD + "LossCurve"
    abcissa_tag = NRML_OLD + "LossCurvePE"
    container_tag = NRML_OLD + "LossCurveList"
    

class LossRatioCurveXMLWriter(RiskXMLWriter):
    """Simple serialization of loss curves and loss ratio curves"""
    curve_tag = NRML_OLD + "LossRatioCurve"
    abcissa_tag = NRML_OLD + "LossRatioCurvePE"
    container_tag = NRML_OLD + "LossRatioCurveList"


def _curve_pe_as_gmldoublelist(curve_object):
    """ Return the list of abscissae converted to string joined by a space """
    return " ".join([str(abscissa) for abscissa in curve_object.abscissae])

def _curve_vals_as_gmldoublelist(curve_object):
    """ Return the list of ordinates converted to string joined by a space """
    return " ".join([str(ordinate) for ordinate in curve_object.ordinates])
