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

from lxml import etree

from openquake import logs
import nrml


NRML_NS = 'http://openquake.org/xmlns/nrml/0.4'
GML_NS = 'http://www.opengis.net/gml'

NRML = "{%s}" % NRML_NS
GML = "{%s}" % GML_NS
NSMAP = {None: NRML_NS, "gml": GML_NS}
GML_POS_TAG = "%spos" % GML


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
