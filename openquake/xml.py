# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Constants and helper functions for XML processing,
including namespaces, and namespace maps.
"""

from lxml import etree

from openquake import shapes
from openquake.nrml import utils as nrml_utils


NRML_NS = 'http://openquake.org/xmlns/nrml/0.3'
GML_NS = 'http://www.opengis.net/gml'

NRML = "{%s}" % NRML_NS
GML = "{%s}" % GML_NS

NSMAP = {None: NRML_NS, "gml": GML_NS}

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
RISK_BCR_NODE_TAG = "%sBCRNode" % NRML
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
RISK_LOSS_MAP_VALUE = "%svalue" % NRML
RISK_LOSS_MAP_LOSS_CATEGORY_ATTR = "lossCategory"
RISK_LOSS_MAP_UNIT_ATTR = "unit"
RISK_LOSS_MAP_ASSET_REF_ATTR = "assetRef"

RISK_BCR_MAP_CONTAINER_TAG = "%sbenefitCostRatioMap" % NRML
RISK_BCR_MAP_BCR_CONTAINER_TAG = "%sbenefitCostRatioValue" % NRML
RISK_BCR_MAP_BCR_VALUE = "%sbenefitCostRatio" % NRML
RISK_BCR_MAP_EAL_ORIGINAL_VALUE = "%sexpectedAnnualLossOriginal" % NRML
RISK_BCR_MAP_EAL_RETROFITTED_VALUE = "%sexpectedAnnualLossRetrofitted" % NRML


class XMLValidationError(Exception):
    """XML schema validation error"""

    def __init__(self, message, file_name):
        """Constructs a new validation exception for the given file name"""
        Exception.__init__(self, "XML Validation error for file '%s': %s" %
                                 (file_name, message))

        self.file_name = file_name


class XMLMismatchError(Exception):
    """Wrong document type (eg. logic tree instead of source model)"""

    def __init__(self, file_name, actual_tag, expected_tag):
        """Constructs a new type mismatch exception for the given file name"""
        Exception.__init__(self)

        self.file_name = file_name
        self.actual_tag = actual_tag
        self.expected_tag = expected_tag

    _HUMANIZE_FILE = {
        'logicTree': 'logic tree',
        'sourceModel': 'source model',
        'exposureModel': 'exposure model',
        'vulnerabilityModel': 'vulnerability model',
        }

    @property
    def message(self):
        """Exception message string"""
        return "XML mismatch error for file '%s': expected %s but got %s" % (
            self.file_name, self._HUMANIZE_FILE.get(self.expected_tag),
            self._HUMANIZE_FILE.get(self.actual_tag, 'unknown file type'))

    def __str__(self):
        return self.message


def validates_against_xml_schema(xml_instance_path,
                                 schema_path=nrml_utils.nrml_schema_file()):
    """
    Checks whether an XML file validates against an XML Schema

    :param xml_instance_path: XML document path
    :param schema_path: XML schema path
    :returns: boolean success value
    """
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
        raise ValueError(
            "site element %s has more than one gml:pos elements" %
            '||'.join(element.attrib.values()))
    if len(pos_el) < 1:
        raise ValueError("site element %s has zero gml:pos elements" %
        '||'.join(element.attrib.values()))
    return lon_lat_from_gml_pos(pos_el[0])


def lon_lat_from_gml_pos(pos_el):
    """Return (lon, lat) coordinate pair from gml:pos element."""
    coord = pos_el.text.strip().split()
    return (float(coord[0]), float(coord[1]))


def strip_namespace_from_tag(full_tag, namespace):
    """Remove namespace alias from a tag"""
    return full_tag[len(namespace):]
