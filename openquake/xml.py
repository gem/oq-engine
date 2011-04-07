# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.



"""
Constants and helper functions for XML processing,
including namespaces, and namespace maps.
"""

from lxml import etree

from openquake import shapes


NRML_SCHEMA_FILE = 'nrml.xsd'

NRML_NS = 'http://openquake.org/xmlns/nrml/0.2'
GML_NS = 'http://www.opengis.net/gml'
QUAKEML_NS = 'http://quakeml.org/xmlns/quakeml/1.1'

NRML = "{%s}" % NRML_NS
GML = "{%s}" % GML_NS

QUAKEML = "{%s}" % QUAKEML_NS
NSMAP = {None: NRML_NS, "gml": GML_NS}
NSMAP_WITH_QUAKEML = {None: NRML_NS, "gml": GML_NS, "qml": QUAKEML_NS}

# TODO(fab): remove these when transition to new schema is completed
NRML_SCHEMA_FILE_OLD = 'old/nrml.xsd'

NRML_NS_OLD = 'http://openquake.org/xmlns/nrml/0.1'
GML_NS_OLD = 'http://www.opengis.net/gml/profile/sfgml/1.0'

NRML_OLD = "{%s}" % NRML_NS_OLD
GML_OLD = "{%s}" % GML_NS_OLD

NSMAP_OLD = {None: NRML_NS_OLD, "gml": GML_NS_OLD}
# end TODO

NRML_ROOT_TAG = "%snrml" % NRML
NRML_CONFIG_TAG = "%sconfig" % NRML

GML_POINT_TAG = "%sPoint" % GML
GML_POS_TAG = "%spos" % GML
GML_ID_ATTR_NAME = "%sid" % GML

GML_SRS_ATTR_NAME = 'srsName'
GML_SRS_EPSG_4326 = 'epsg:4326'

# common risk tag names
RISK_RESULT_TAG = "%sriskResult" % NRML
RISK_ASSET_TAG = "%sasset" % NRML
RISK_SITE_TAG = "%ssite" % NRML
RISK_LMNODE_TAG = "%sLMNode" % NRML
RISK_POE_TAG = "%spoE" % NRML
RISK_END_BRANCH_ATTR_NAME = 'endBranchLabel'

RISK_CURVE_ORDINATE_PROPERTY = 'Probability of Exceedance'

RISK_LOSS_CONTAINER_TAG = "%slossCurveList" % NRML
RISK_LOSS_CURVES_TAG = "%slossCurves" % NRML
RISK_LOSS_CURVE_TAG = "%slossCurve" % NRML
RISK_LOSS_ABSCISSA_TAG = "%sloss" % NRML
RISK_LOSS_ABSCISSA_PROPERTY = 'Loss'

RISK_LOSS_RATIO_CONTAINER_TAG = "%slossRatioCurveList" % NRML
RISK_LOSS_RATIO_CURVES_TAG = "%slossRatioCurves" % NRML
RISK_LOSS_RATIO_CURVE_TAG = "%slossRatioCurve" % NRML
RISK_LOSS_RATIO_ABSCISSA_TAG = "%slossRatio" % NRML
RISK_LOSS_RATIO_ABSCISSA_PROPERTY = 'Loss Ratio'

RISK_LOSS_MAP_CONTAINER_TAG = "%slossMap" % NRML
RISK_LOSS_MAP_LOSS_CONTAINER_TAG = "%sloss" % NRML
RISK_LOSS_MAP_MEAN_LOSS_TAG = "%smean" % NRML
RISK_LOSS_MAP_STANDARD_DEVIATION_TAG = "%sstdDev" % NRML
RISK_LOSS_MAP_LOSS_CATEGORY_ATTR = "lossCategory"
RISK_LOSS_MAP_UNIT_ATTR = "unit"
RISK_LOSS_MAP_ASSET_REF_TAG = "%sassetRef" % NRML

def validates_against_xml_schema(xml_instance_path, schema_path):
    xml_doc = etree.parse(xml_instance_path)
    xmlschema = etree.XMLSchema(etree.parse(schema_path))
    return xmlschema.validate(xml_doc)

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
    pos_el = element.findall(".//%s" % GML_POS_TAG)
    if len(pos_el) > 1:
        error_msg = "site element %s has more than one gml:pos elements" % (
            element)
        raise ValueError(error_msg)
    return lon_lat_from_gml_pos(pos_el[0])

def lon_lat_from_gml_pos(pos_el):
    """Return (lon, lat) coordinate pair from gml:pos element."""
    coord = pos_el.text.strip().split()
    return (float(coord[0]), float(coord[1]))

def strip_namespace_from_tag(full_tag, namespace):
    return full_tag[len(namespace):]
