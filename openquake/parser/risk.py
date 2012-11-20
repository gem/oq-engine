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


# TODO(lp) move parsers into nrml schemas


"""
This module contains a class that parses NRML instance document files
for the output of risk computations. At the moment, loss and loss curve data
is supported.

Constants and helper functions for XML processing,
including namespaces, and namespace maps.

Parsers to read exposure files, including exposure portfolios.
These can include building, population, critical infrastructure,
and other asset classes.

Codec for processing vulnerability curves
from XML files.

A DOM version of the vulnerability model parser,
that takes into account the really small size of this input file.
"""

from collections import namedtuple

from lxml import etree

from openquake import logs
from openquake import shapes
import nrml


NRML_NS = 'http://openquake.org/xmlns/nrml/0.4'
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


class AttributeConstraint(object):
    """A constraint that can be used to filter input elements based on some
    attributes.

    The constructor requires a dictionary as argument. Items in this dictionary
    have to match the corresponding ones in the checked site attributes object.
    """

    def __init__(self, attribute):
        self.attribute = attribute

    def match(self, compared_attribute):
        """ Compare self.attribute against the passed in compared_attribute
        dict. If the compared_attribute dict does not contain all of the
        key/value pais from self.attribute, we return false. compared_attribute
        may have additional key/value pairs.
        """

        for k, v in self.attribute.items():
            if not (k in compared_attribute and compared_attribute[k] == v):
                return False

        return True


class FileProducer(object):
    """
    FileProducer is an interface for iteratively parsing
    a file, and returning a sequence of objects.

    TODO(jmc): fold the attributes filter in here somewhere.
    """

    # required attributes for metadata parsing
    REQUIRED_ATTRIBUTES = ()

    # optional attributes for metadata parsing
    OPTIONAL_ATTRIBUTES = ()

    def __init__(self, path):
        logs.LOG.debug('Found data at %s', path)
        self.path = path

        self.file = open(self.path, 'r')

        # contains the metadata of the node currently parsed
        self._current_meta = {}

    def __iter__(self):
        for rv in self._parse():
            yield rv

    def reset(self):
        """
        Sometimes we like to iterate the filter more than once.

        If the file is currently closed, re-open the file.
        If the file is currently open, set the file seek position to zero.
        """
        if self.file.closed:
            self.file = open(self.file.name, self.file.mode)
        else:
            self.file.seek(0)
        # contains the metadata of the node currently parsed
        self._current_meta = {}

    def filter(self, region_constraint=None, attribute_constraint=None):
        """
        Filters the elements readed by this

        region_constraint has to be of type shapes.RegionConstraint and
        specifies the region to which the elements of this producer
        should be contained.

        attribute_constraint has to be of type AttributeConstraint
        and specifies additional attributes to use in the filtring process.
        """
        for next_val in iter(self):
            if (attribute_constraint is not None and
                    (region_constraint is None
                        or region_constraint.match(next_val[0])) and
                    attribute_constraint.match(next_val[1])) or \
               (attribute_constraint is None and
                    (region_constraint is None
                        or region_constraint.match(next_val[0]))):

                yield next_val

    def _set_meta(self, element):
        """Sets the metadata of the node that is currently
        being processed."""

        for (required_attr, attr_type) in self.REQUIRED_ATTRIBUTES:
            attr_value = element.get(required_attr)

            if attr_value is not None:
                self._current_meta[required_attr] = attr_type(attr_value)
            else:
                error_str = "element %s: missing required " \
                        "attribute %s" % (element, required_attr)

                raise ValueError(error_str)

        for (optional_attr, attr_type) in self.OPTIONAL_ATTRIBUTES:
            attr_value = element.get(optional_attr)

            if attr_value is not None:
                self._current_meta[optional_attr] = attr_type(attr_value)

    def _parse(self):
        """
        Parse one logical item from the file.

        Should return a (point, data) tuple.
        """

        raise NotImplementedError


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
            self.actual_tag)

    def __str__(self):
        return self.message


def validates_against_xml_schema(xml_instance_path,
                                 schema_path=nrml.nrml_schema_file()):
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


class RiskXMLReader(FileProducer):
    """ This class parses a NRML loss/loss ratio curve file.
    The class is implemented as a generator.
    For each curve element in the parsed
    instance document, it yields a pair of objects, of which the
    first one is a shapes object of type Site (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with risk-related attribute values for this site.

    The attribute dictionary looks like
    {'nrml_id': 'nrml',
     'result_id': 'rr',
     'list_id': 'list_1',
     'assetID': 'a100',
     'poE': [0.2, 0.02, ...],
     'loss': [0.0, 1280.0, ...], # for loss
     'lossRatio': [0.0, 0.1, ...], # for loss ratio
     'endBranchLabel': '1_1',
     'property': 'Loss' # 'Loss Ratio'
    }
    """

    # these tag names and properties have to be redefined in the
    # derived classes for loss and loss ratio
    container_tag = None
    curves_tag = None
    curve_tag = None
    abscissa_tag = None
    abscissa_property = None

    # common names
    ordinate_property = RISK_CURVE_ORDINATE_PROPERTY
    ordinate_tag = RISK_POE_TAG

    property_output_key = 'property'

    def __init__(self, path):
        self._current_site = None
        self._current_id_meta = None
        self._current_asset_meta = None

        self.abscissa_output_key = strip_namespace_from_tag(
            self.abscissa_tag, NRML)
        self.ordinate_output_key = strip_namespace_from_tag(
            self.ordinate_tag, NRML)
        super(RiskXMLReader, self).__init__(path)

    def _parse(self):
        for event, element in etree.iterparse(
                self.file, events=('start', 'end')):
            if event == 'start' and element.tag == NRML_ROOT_TAG:
                self._to_id_attributes(element)

            # IMPORTANT: we parse RISK_ASSET_TAG at the 'end' event,
            # because in the 'start' event children are not assumed to be
            # *there*
            elif event == 'end' and element.tag == RISK_ASSET_TAG:
                self._to_asset_attributes(element)

                curve_els = element.findall('.//%s' % self.curve_tag)

                for curve_el in curve_els:
                    curr_attributes = self._to_curve_attributes(curve_el)
                    yield (self._current_site, curr_attributes)

    def _to_id_attributes(self, element):
        """Collect id attributes from root element."""

        self._current_id_meta = {}

        # get nrml id
        self._current_id_meta['nrml_id'] = \
            element.attrib[GML_ID_ATTR_NAME]

        # get riskResult id
        curr_el = element.find('.//%s' % RISK_RESULT_TAG)
        self._current_id_meta['result_id'] = \
            curr_el.attrib[GML_ID_ATTR_NAME]

        # get lossCurveList id
        curr_el = element.find('.//%s' % self.container_tag)
        self._current_id_meta['list_id'] = \
            curr_el.attrib[GML_ID_ATTR_NAME]

    def _to_asset_attributes(self, element):
        """Collect metadata attributes for new asset element."""

        # assetID
        self._current_asset_meta = {
            'assetID': element.attrib[GML_ID_ATTR_NAME]}

        # get site
        lon, lat = lon_lat_from_site(element)
        self._current_site = shapes.Site(lon, lat)

    def _to_curve_attributes(self, element):
        """Build an attributes dict from NRML curve element (this can be
        'lossCurve' or 'lossRatioCurve'.
        This element contains abscissae (loss/loss ratio) and ordinate
        (PoE) values of a curve.
        """

        attributes = {self.property_output_key: self.abscissa_property}

        abscissa_el_txt = element.findtext(self.abscissa_tag)
        attributes[self.abscissa_output_key] = [float(x) \
            for x in abscissa_el_txt.strip().split()]

        ordinate_el_txt = element.findtext(self.ordinate_tag)
        attributes[self.ordinate_output_key] = [float(x) \
            for x in ordinate_el_txt.strip().split()]

        if RISK_END_BRANCH_ATTR_NAME in element.attrib:
            attributes[RISK_END_BRANCH_ATTR_NAME] = \
                element.attrib[RISK_END_BRANCH_ATTR_NAME]

        attributes.update(self._current_id_meta)
        attributes.update(self._current_asset_meta)
        return attributes


class LossCurveXMLReader(RiskXMLReader):
    """NRML parser class for loss curves"""
    container_tag = RISK_LOSS_CONTAINER_TAG
    curves_tag = RISK_LOSS_CURVES_TAG
    curve_tag = RISK_LOSS_CURVE_TAG
    abscissa_tag = RISK_LOSS_ABSCISSA_TAG
    abscissa_property = RISK_LOSS_ABSCISSA_PROPERTY


class LossRatioCurveXMLReader(RiskXMLReader):
    """NRML parser class for loss ratio curves"""
    container_tag = RISK_LOSS_RATIO_CONTAINER_TAG
    curves_tag = RISK_LOSS_RATIO_CURVES_TAG
    curve_tag = RISK_LOSS_RATIO_CURVE_TAG
    abscissa_tag = RISK_LOSS_RATIO_ABSCISSA_TAG
    abscissa_property = RISK_LOSS_RATIO_ABSCISSA_PROPERTY


# do not use namespace for now
RISKML_NS = ''


OCCUPANCY = namedtuple("OCCUPANCY", "occupants, description")


def _to_site(element):
    """Convert current GML attributes to Site object

    We want to extract the value of <gml:pos>. We expect the input
    element to be an 'assetDefinition' and have a child element
    structured like this:

    <site>
        <gml:Point srsName="epsg:4326">
            <gml:pos>9.15000 45.16667</gml:pos>
        </gml:Point>
    </site>
    """
    # lon/lat are in XML attribute gml:pos
    # consider them as mandatory

    try:
        site_elem = element.find('%ssite' % NRML)
        point_elem = site_elem.find('%sPoint' % GML)
        pos = point_elem.find('%spos' % GML).text
        lon, lat = [float(x.strip()) for x in pos.split()]

        return shapes.Site(lon, lat)
    except Exception:
        error_str = "element assetDefintion: no valid lon/lat coordinates"
        raise ValueError(error_str)


def _to_occupancy(element):
    """Convert the 'occupants' tags to named tuples.

    We want to extract the value of <occupants>. We expect the input
    element to be an 'assetDefinition' and have a child element
    structured like this:

    <occupants description="day">245</occupants>
    """
    occupancy_data = []
    for otag in element.findall('%soccupants' % NRML):
        occupancy_data.append(OCCUPANCY(
            occupants=int(otag.text), description=otag.attrib["description"]))
    return occupancy_data


class ExposureModelFile(FileProducer):
    """ This class parses an ExposureModel XML (part of riskML?) file.
    The contents of such a file is meant to be used as input for the risk
    engine. The class is implemented as a generator.
    For each 'AssetInstance' element in the parsed
    instance document, it yields a pair of objects, of which the
    first one is a shapely.geometry object of type Point (representing a
    geographical site as WGS84 lon/lat), and the second one
    is a dictionary with exposure-related attribute values for this site.

    The attribute dictionary looks like this::

        {'listID': 'PAV01',
         'listDescription': 'Collection of existing building in ' \
                            'downtown Pavia',
         'assetID': 'asset_02',
         'assetCategory': 'buildings',
         'taxonomy': 'RC/DMRF-D/LR',
         'structureCategory': 'RC-LR-PC',
         'assetValue': 250000.0,
         'assetValueUnit': 'EUR'}

    """

    def __init__(self, path):
        super(ExposureModelFile, self).__init__(path)

    def _parse(self):
        try:
            for i in self._do_parse():
                yield i
        except etree.XMLSyntaxError as ex:
            # when using .iterparse, the error message does not
            # contain a file name
            raise XMLValidationError(ex.message, self.file.name)

    def _do_parse(self):
        """_parse implementation"""
        nrml_schema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))
        level = 0

        for event, element in etree.iterparse(
                self.file, events=('start', 'end'), schema=nrml_schema):

            if event == 'start' and element.tag == \
                    '%sexposureList' % NRML:
                # we need to get the exposureList id, description and
                # asset category
                exp_id = element.get('%sid' % GML)
                self._current_meta['listID'] = str(exp_id)

                desc = element.find('%sdescription' % GML)
                if desc is not None:
                    self._current_meta['listDescription'] = str(desc.text)

                taxsrc = element.find('%staxonomySource' % NRML)
                if taxsrc is not None:
                    self._current_meta['taxonomySource'] = str(taxsrc.text)

                asset_category = str(element.get('assetCategory'))
                self._current_meta['assetCategory'] = asset_category

                # type and unit for area, contents cost, retrofitting cost
                # and structural cost.
                attrs = ("areaType", "areaUnit", "cocoType", "cocoUnit",
                         "recoType", "recoUnit", "stcoType", "stcoUnit")
                for attr_name in attrs:
                    attr_value = element.get(attr_name)
                    if attr_value is not None:
                        self._current_meta[attr_name] = attr_value

            elif event == 'start' and level < 2:
                # check that the first child of the root element is an
                # exposure portfolio
                if level == 1 and element.tag != '%sexposureModel' % NRML:
                    raise XMLMismatchError(
                        self.file.name, element.tag,
                        'exposureModel')

                level += 1

            elif event == 'end' and element.tag == '%sassetDefinition' % NRML:
                site_data = (_to_site(element), _to_occupancy(element),
                             self._to_site_attributes(element))
                del element
                yield site_data

    def _to_site_attributes(self, element):
        """Build a dict of all node attributes"""
        site_attributes = {}

        site_attributes['assetID'] = element.get('%sid' % GML)

        # Optional elements
        attrs = (('coco', float), ('reco', float), ('stco', float),
                 ('area', float), ('number', float), ('limit', float),
                 ('deductible', float))
        for (attr_name, attr_type) in attrs:
            attr_value = element.find('%s%s' % (NRML, attr_name))
            if attr_value is not None:
                site_attributes[attr_name] = attr_type(attr_value.text)

        # Mandatory elements
        for (required_attr, attr_type) in (('taxonomy', str),):
            attr_value = element.find('%s%s' % (NRML, required_attr)).text
            if attr_value is not None:
                site_attributes[required_attr] = attr_type(attr_value)
            else:
                error_str = ("element assetDefinition: missing required "
                             "attribute %s" % required_attr)
                raise ValueError(error_str)

        # TODO, al-maisan, Thu, 16 Feb 2012 15:55:01 +0100
        # add the logic that handles the 'occupants' tags.
        # https://bugs.launchpad.net/openquake/+bug/942178

        site_attributes.update(self._current_meta)

        return site_attributes


def _parse_set_attributes(vulnerability_set):
    """Parse and return the attributes for all the
    vulnerability functions defined in this set of the NRML file."""

    imls = vulnerability_set.find(".//%sIML" % NRML)

    vuln_function = {"IMT": imls.attrib["IMT"]}

    vuln_function["IML"] = \
            [float(x) for x in imls.text.strip().split()]

    vuln_function["vulnerabilitySetID"] = \
            vulnerability_set.attrib["vulnerabilitySetID"]

    vuln_function["assetCategory"] = \
            vulnerability_set.attrib["assetCategory"]

    vuln_function["lossCategory"] = \
            vulnerability_set.attrib["lossCategory"]

    return vuln_function


class VulnerabilityModelFile(FileProducer):
    """This class parsers a vulnerability model NRML file.

    The class is implemented as a generator. For each vulnerability
    function in the parsed instance document it yields a dictionary
    with all the data defined for that function.
    """

    def __init__(self, path):
        FileProducer.__init__(self, path)
        nrml_schema = etree.XMLSchema(etree.parse(nrml.nrml_schema_file()))
        self.vuln_model = etree.parse(self.path).getroot()
        if not nrml_schema.validate(self.vuln_model):
            raise XMLValidationError(
                nrml_schema.error_log.last_error, path)
        model_el = self.vuln_model.getchildren()[0]
        if model_el.tag != "%svulnerabilityModel" % NRML:
            raise XMLMismatchError(
                path, 'vulnerabilityModel', str(model_el.tag)[len(NRML):])

    def filter(self, region_constraint=None, attribute_constraint=None):
        """Filtering is not needed/supported for the vulnerability model."""

    def _parse(self):
        """Parse the vulnerability model."""

        for vuln_set in self.vuln_model.findall(
                ".//%sdiscreteVulnerabilitySet" % NRML):

            vuln_function = _parse_set_attributes(vuln_set)

            for raw_vuln_function in vuln_set.findall(
                    ".//%sdiscreteVulnerability" % NRML):

                loss_ratios = [float(x) for x in
                        raw_vuln_function.find(
                        "%slossRatio" % NRML).text.strip().split()]

                coefficients_variation = [float(x) for x in
                        raw_vuln_function.find(
                        "%scoefficientsVariation" % NRML)
                        .text.strip().split()]

                vuln_function["ID"] = \
                        raw_vuln_function.attrib["vulnerabilityFunctionID"]

                vuln_function["probabilisticDistribution"] = \
                        raw_vuln_function.attrib["probabilisticDistribution"]

                vuln_function["lossRatio"] = loss_ratios
                vuln_function["coefficientsVariation"] = coefficients_variation

                yield dict(vuln_function)
