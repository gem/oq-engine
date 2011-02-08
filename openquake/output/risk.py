# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
NRML serialization of risk-related data sets.
- loss ratio curves
- loss curves
"""

from lxml import etree

from openquake import logs
from openquake import shapes
from openquake import writer
#from openquake.xml import GML_OLD, NSMAP_OLD, NRML_OLD
from openquake.xml import GML, NRML, NSMAP

LOGGER = logs.RISK_LOG

class RiskXMLWriter(writer.FileWriter):
    """This class serializes a set of loss or loss ratio curves to NRML.
    """

    container_tag = None
    curves_tag = None
    curve_tag = None
    abcissa_tag = None
    
    root_tag = "%snrml" % NRML
    result_tag = "%sriskResult" % NRML
    config_tag = "%sconfig" % NRML

    def write(self, point, val):
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_curve_node(point, val, self.parent_node)

    def write_header(self):
        """Header (i.e., common) information for all curves."""
        self.root_node = etree.Element(self.root_tag, nsmap=NSMAP)
        result_node = etree.SubElement(self.root_node, self.result_tag,
            nsmap=NSMAP)

        config_node = etree.SubElement(result_node, self.config_tag, 
            nsmap=NSMAP)

        #pylint: disable=W0201
        self.parent_node = etree.SubElement(result_node, self.container_tag, 
            nsmap=NSMAP)

    def write_footer(self):
        """Serialize tree to file."""
        et = etree.ElementTree(self.root_node)
        et.write(self.file, pretty_print=True, xml_declaration=True,
            encoding="UTF-8")

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
    """NRML serialization of loss curves"""
    container_tag = "%slossCurveList" % NRML
    curves_tag = "%slossCurves" % NRML
    curve_tag = "%slossCurve" % NRML
    abcissa_tag = "%sloss" % NRML
    

class LossRatioCurveXMLWriter(RiskXMLWriter):
    """NRML serialization of loss ratio curves"""
    container_tag = "%slossRatioCurveList" % NRML
    curves_tag = "%slossRatioCurves" % NRML
    curve_tag = "%slossRatioCurve" % NRML
    abcissa_tag = "%slossRatio" % NRML

def _curve_vals_as_gmldoublelist(curve_object):
    """Return the list of loss/loss ratio values from a curve object.
    This is the abscissa of the curve.
    The list of values is converted to string joined by a space.
    """
    return " ".join([str(abscissa) for abscissa in curve_object.abscissae])

def _curve_poe_as_gmldoublelist(curve_object):
    """Return the list of PoE values from a curve object.
    This is the ordinate of the curve.
    The list of values is converted to string joined by a space.
    """
    return " ".join([str(ordinate) for ordinate in curve_object.ordinates])
