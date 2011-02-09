# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base functionality for NRML serialization.
"""

from lxml import etree

from openquake import logs
from openquake import shapes
from openquake import writer

from openquake.xml import GML, NRML, NSMAP

LOG = logs.LOG

NRML_DEFAULT_ID = 'nrml'
RISKRESULT_DEFAULT_ID = 'rr'
HAZARDRESULT_DEFAULT_ID = 'hr'

GML_SRS_ATTR_NAME = 'srsName'
GML_SRS_EPSG_4326 = 'epsg:4326'

ROOT_TAG = "%snrml" % NRML
CONFIG_TAG = "%sconfig" % NRML

GML_POINT_TAG = "%sPoint" % GML
GML_POS_TAG = "%spos" % GML

class TreeNRMLWriter(writer.FileWriter):

    def close(self):
        """Overrides the default implementation writing all the
        collected lxml object model to the stream.
        """
        if self.root_node is None:
            error_msg = "You need to add at least data for one site to "\
                        "build a valid output!"
            raise RuntimeError(error_msg)

        self.file.write(etree.tostring(self.root_node, pretty_print=True,
            xml_declaration=True, encoding="UTF-8"))
        super(TreeNRMLWriter, self).close()

    def _create_root_element(self):
        self.root_node = etree.Element(ROOT_TAG, nsmap=NSMAP)


def set_gml_id(element, gml_id):
    """Set gml:id attribute for element"""
    element.set("%sid" % GML, str(gml_id))

def element_equal_to_site(element, site):
    """Check whether a given XML element (containing a gml:pos) has the same
    coordinates as a shapes.Site.
    Note: doesn't check whether the spatial reference system is the same.
    """
    (element_lon, element_lat) = lon_lat_from_site(element)
    if site == shapes.Site(element_lon, element_lat):
        return True
    else:
        return False

def lon_lat_from_site(element):
    """Extract (lon, lat) pair from gml:pos sub-element of element."""
    pos_el = element.find(".//%s" % GML_POS_TAG)
    if len(pos_el) > 1:
        error_msg = "site element %s has more than one gml:pos elements" % (
            element)
        raise ValueError(error_msg)
    return lon_lat_from_gml_pos(pos_el.text)

def lon_lat_from_gml_pos(pos_text):
    """Return (lon, lat) coordinate pair from text node 
    of gml:pos element."""
    coord = pos_text.strip().split()
    return (float(coord[0]), float(coord[1]))
