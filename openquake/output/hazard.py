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
This module provides classes that serialize hazard-related objects
to NRML format.
"""

import logging

from collections import defaultdict, namedtuple
from lxml import etree

from openquake import shapes
from openquake import writer
from openquake.db import models
from openquake.job.params import REVERSE_ENUM_MAP
from openquake.utils import config
from openquake.utils import general
from openquake.utils import round_float
from openquake.utils import stats
from openquake.xml import NSMAP, NRML, GML


LOGGER = logging.getLogger('hazard-serializer')


NRML_GML_ID = 'n1'
HAZARDRESULT_GML_ID = 'hr1'
GMFS_GML_ID = 'gmfs_1'
GMF_GML_ID = 'gmf_1'
SRS_EPSG_4326 = 'epsg:4326'


class HazardCurveXMLWriter(writer.FileWriter):
    """This class serializes hazard curve information to NRML format."""

    def __init__(self, path):
        """Initialize the data to be used."""
        super(HazardCurveXMLWriter, self).__init__(path)
        self.nrml_el = None
        self.result_el = None
        self.curves_per_branch_label = {}
        self.hcnode_counter = 0
        self.hcfield_counter = 0

    def _maintain_debug_stats(self):
        """Capture the file written if debug statistics are turned on."""
        key = stats.key_name(config.Config().job_id,
                             *stats.STATS_KEYS["hcls_xmlcurvewrites"])
        if key:
            stats.kvs_op("rpush", key, self.path)

    def open(self):
        """Make sure the mode is set before the base class' open is called."""
        self.mode = SerializerContext().get_mode()
        super(HazardCurveXMLWriter, self).open()

    def close(self):
        """Write all the collected lxml object model to the stream."""

        if self.nrml_el is None:
            error_msg = ("You need to add at least a curve to build "
                         "a valid output!")
            raise RuntimeError(error_msg)

        self.mode = SerializerContext().get_mode()
        if self.mode.end:
            self._maintain_debug_stats()
            self.file.write(etree.tostring(
                self.nrml_el, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))
            writer.FileWriter.close(self)

    def write(self, point, values):
        """Write a hazard curve.

        point must be of type shapes.Site values is a dictionary that matches
        the one produced by the parser nrml.NrmlFile."""

        # if we are writing the first hazard curve, create wrapping elements
        if self.nrml_el is None:

            # nrml:nrml, needs gml:id
            self.nrml_el = etree.Element("%snrml" % NRML, nsmap=NSMAP)

            _set_gml_id(self.nrml_el, _gml_id("nrml_id", values,
                    NRML_GML_ID))

            # nrml:hazardResult, needs gml:id
            self.result_el = etree.SubElement(self.nrml_el,
                "%shazardResult" % NRML)

            _set_gml_id(self.result_el,
                        _gml_id("hazres_id", values, HAZARDRESULT_GML_ID))

            # nrml:config
            config_el = etree.SubElement(self.result_el, "%sconfig" % NRML)

            # nrml:hazardProcessing
            hazard_processing_el = etree.SubElement(
                config_el, "%shazardProcessing" % NRML)

            # the following XML attributes are all optional
            _set_optional_attributes(hazard_processing_el, values,
                ('investigationTimeSpan', 'IDmodel', 'saPeriod', 'saDamping'))

        # check if we have hazard curves for an end branch label, or
        # for mean/median/quantile
        if 'endBranchLabel' in values and 'statistics' in values:
            error_msg = ("hazardCurveField cannot have both an end branch "
                         "and a statistics label")
            raise ValueError(error_msg)
        elif 'endBranchLabel' in values:
            curve_label = values['endBranchLabel']
        elif 'statistics' in values:
            curve_label = values['statistics']
        else:
            error_msg = ("hazardCurveField has to have either an end branch "
                         "or a statistics label")
            raise ValueError(error_msg)

        if curve_label in self.curves_per_branch_label:
            hazard_curve_field_el = self.curves_per_branch_label[curve_label]
        else:
            # nrml:hazardCurveField, needs gml:id
            hazard_curve_field_el = etree.SubElement(self.result_el,
                "%shazardCurveField" % NRML)

            _set_gml_id(hazard_curve_field_el, _gml_id(
                    "hcfield_id", values,
                    "hcf_%s" % self.hcfield_counter))

            if "hcfield_id" not in values:
                self.hcfield_counter += 1

            if 'endBranchLabel' in values:
                hazard_curve_field_el.set("endBranchLabel",
                    str(values["endBranchLabel"]))
            elif 'statistics' in values:
                hazard_curve_field_el.set("statistics",
                    str(values["statistics"]))
                if 'quantileValue' in values:
                    hazard_curve_field_el.set("quantileValue",
                        str(values["quantileValue"]))

            # nrml:IML
            iml_el = etree.SubElement(hazard_curve_field_el, "%sIML" % NRML)
            iml_el.text = " ".join([str(x) for x in values["IMLValues"]])
            iml_el.set("IMT", str(values["IMT"]))

            self.curves_per_branch_label[curve_label] = hazard_curve_field_el

        # nrml:HCNode, needs gml:id
        hcnode_el = etree.SubElement(hazard_curve_field_el, "%sHCNode" % NRML)

        _set_gml_id(hcnode_el, _gml_id(
                "hcnode_id", values,
                "hcn_%s" % self.hcnode_counter))

        if "hcnode_id" not in values:
            self.hcnode_counter += 1

        # nrml:site, nrml:Point
        point_el = etree.SubElement(etree.SubElement(
                hcnode_el, "%ssite" % NRML), "%sPoint" % GML)

        point_el.set("srsName", SRS_EPSG_4326)

        pos_el = etree.SubElement(point_el, "%spos" % GML)
        pos_el.text = "%s %s" % (point.longitude, point.latitude)

        # nrml:hazardCurve, nrml:poE
        poe_el = etree.SubElement(etree.SubElement(
                hcnode_el, "%shazardCurve" % NRML), "%spoE" % NRML)

        poe_el.text = " ".join([str(x) for x in values["PoEValues"]])


class HazardMapXMLWriter(writer.XMLFileWriter):
    """This class serializes hazard map information to NRML format."""

    root_tag = "%snrml" % NRML
    hazard_result_tag = "%shazardResult" % NRML
    config_tag = "%sconfig" % NRML
    hazard_processing_tag = "%shazardProcessing" % NRML

    hazard_map_tag = "%shazardMap" % NRML

    node_tag = "%sHMNode" % NRML
    site_tag = "%sHMSite" % NRML
    vs30_tag = "%svs30" % NRML

    point_tag = "%sPoint" % GML
    pos_tag = "%spos" % GML
    iml_tag = "%sIML" % NRML

    PROCESSING_ATTRIBUTES_TO_CHECK = (
        {'name': 'investigationTimeSpan', 'required': False}, )

    MAP_ATTRIBUTES_TO_CHECK = (
        {'name': 'poE', 'required': True},
        {'name': 'IMT', 'required': True},
        {'name': 'endBranchLabel', 'required': False},
        {'name': 'statistics', 'required': False},
        {'name': 'quantileValue', 'required': False})

    NRML_DEFAULT_ID = 'nrml'
    HAZARD_RESULT_DEFAULT_ID = 'hr'
    HAZARD_MAP_DEFAULT_ID = 'hm'
    HAZARD_MAP_NODE_ID_PREFIX = 'n_'

    def __init__(self, path):
        """Initialize the data to be used."""
        super(HazardMapXMLWriter, self).__init__(path)
        self.hmnode_counter = 0
        self.root_node = None
        self.parent_node = None
        self.hazard_processing_node = None

    def open(self):
        """Make sure the mode is set before the base class' open is called."""
        self.mode = SerializerContext().get_mode()
        super(HazardMapXMLWriter, self).open()

    def write(self, point, val):
        """Writes hazard map for one site.

        point must be of type shapes.Site
        val is a dictionary like this::

        {'IML': 0.8,
         'IMT': 'PGA',
         'poE': 0.1,
         'endBranchLabel': '1',
         'vs30': 760.0,
         'investigationTimeSpan': 50.0
        }
        """

        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_node(point, val, self.parent_node)

    def write_header(self):
        """Header (i.e., common) information for all nodes."""

        self.mode = SerializerContext().get_mode()
        LOGGER.debug("hazard map, write header!")
        LOGGER.debug(self.mode)
        if not self.mode.start:
            return

        self.root_node = etree.Element(self.root_tag, nsmap=NSMAP)
        self.root_node.attrib['%sid' % GML] = self.NRML_DEFAULT_ID

        hazard_result_node = etree.SubElement(self.root_node,
            self.hazard_result_tag, nsmap=NSMAP)
        hazard_result_node.attrib['%sid' % GML] = self.HAZARD_RESULT_DEFAULT_ID

        config_node = etree.SubElement(hazard_result_node,
            self.config_tag, nsmap=NSMAP)

        self.hazard_processing_node = etree.SubElement(config_node,
            self.hazard_processing_tag, nsmap=NSMAP)

        # parent node for hazard map nodes: hazardMap
        self.parent_node = etree.SubElement(hazard_result_node,
            self.hazard_map_tag, nsmap=NSMAP)
        self.parent_node.attrib['%sid' % GML] = self.HAZARD_MAP_DEFAULT_ID

    def _maintain_debug_stats(self):
        """Capture the file written if debug statistics are turned on."""
        key = stats.key_name(config.Config().job_id,
                             *stats.STATS_KEYS["hcls_xmlmapwrites"])
        if key:
            stats.kvs_op("rpush", key, self.path)

    def write_footer(self):
        """Serialize tree to file."""

        self.mode = SerializerContext().get_mode()
        if self.mode.end:
            self._maintain_debug_stats()
            if self._ensure_all_attributes_set():
                et = etree.ElementTree(self.root_node)
                et.write(self.file, pretty_print=True, xml_declaration=True,
                         encoding="UTF-8")
            else:
                error_msg = ("not all required attributes set in hazard curve "
                             "dataset")
                raise ValueError(error_msg)

    def _append_node(self, point, val, parent_node):
        """Write HMNode element."""

        self.hmnode_counter += 1
        node_node = etree.SubElement(parent_node, self.node_tag, nsmap=NSMAP)
        node_node.attrib["%sid" % GML] = "%s%s" % (
            self.HAZARD_MAP_NODE_ID_PREFIX, self.hmnode_counter)

        site_node = etree.SubElement(node_node, self.site_tag, nsmap=NSMAP)
        point_node = etree.SubElement(site_node, self.point_tag, nsmap=NSMAP)
        point_node.attrib['srsName'] = 'epsg:4326'

        pos_node = etree.SubElement(point_node, self.pos_tag, nsmap=NSMAP)
        pos_node.text = "%s %s" % (str(point.x), str(point.y))

        if 'vs30' in val:
            vs30_node = etree.SubElement(site_node, self.vs30_tag,
                nsmap=NSMAP)
            vs30_node.text = str(val['vs30'])

        iml_node = etree.SubElement(node_node, self.iml_tag, nsmap=NSMAP)
        iml_node.text = str(val['IML'])

        # check/set common attributes
        # TODO(fab): this could be moved to common base class
        # of all serializers
        _set_common_attributes(self.PROCESSING_ATTRIBUTES_TO_CHECK,
                self.hazard_processing_node, val)
        _set_common_attributes(self.MAP_ATTRIBUTES_TO_CHECK,
                parent_node, val)

    def _ensure_all_attributes_set(self):
        """Ensure that all the attributes are set if required."""
        if (_ensure_attributes_set(self.PROCESSING_ATTRIBUTES_TO_CHECK,
                                        self.hazard_processing_node) and
             _ensure_attributes_set(self.MAP_ATTRIBUTES_TO_CHECK,
                                         self.parent_node) and
             self._ensure_attribute_rules()):
            return True
        else:
            return False

    def _ensure_attribute_rules(self):
        """Ensure business constraints on attributes
        of an HazardCurveField node."""

        # special checks: end branch label and statistics
        if 'endBranchLabel' in self.parent_node.attrib:

            # ensure that neither statistics nor quantileValue is set
            # together with endBranchLabel
            if ('statistics' in self.parent_node.attrib or
                'quantileValue' in self.parent_node.attrib):

                error_msg = ("attribute endBranchLabel cannot be used "
                             "together with statistics/quantileValue")
                raise ValueError(error_msg)
        elif 'statistics' not in self.parent_node.attrib:
            error_msg = ("either attribute endBranchLabel or attribute "
                         "statistics has to be set")
            raise ValueError(error_msg)

        return True


# TODO Add support rupture element (not implemented so far)
# TODO Add support full GMPEParameters (not implemented so far)
class GMFXMLWriter(writer.XMLFileWriter):
    """This class serializes ground motion field (GMF) informatiuon
    to NRML format.

    As of now, only the GMFNode information is supported. GMPEParameters is
    serialized as a stub with the only attribute that is formally required
    (but doesn't have a useful definition in the schema).
    Rupture information and full GMPEParameters are currently
    not supported."""

    root_tag = NRML + "nrml"
    hazard_result_tag = NRML + "hazardResult"
    config_tag = NRML + "config"
    hazard_processing_tag = NRML + "hazardProcessing"
    gmpe_params_tag = NRML + "GMPEParameters"
    gmf_set_tag = NRML + "groundMotionFieldSet"
    field_tag = NRML + "GMF"
    node_tag = NRML + "GMFNode"
    site_tag = NRML + "site"
    point_tag = GML + "Point"
    pos_tag = GML + "pos"
    ground_motion_attr = "groundMotion"

    def __init__(self, path):
        super(GMFXMLWriter, self).__init__(path)
        self.node_counter = 0

        # <GMF/> where all the fields are appended
        self.parent_node = None

        # <nrml/> the root of the document
        self.root_node = None

    def write(self, point, val):
        """Writes GMF for one site.

        point must be of type shapes.Site or shapes.GridPoint
        val is a dictionary:

        {'groundMotion': 0.8}
        """
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point
        self._append_site_node(point, val, self.parent_node)

    def write_header(self):
        """Write out the file header."""

        self.root_node = etree.Element(GMFXMLWriter.root_tag, nsmap=NSMAP)
        _set_gml_id(self.root_node, NRML_GML_ID)

        hazard_result_node = etree.SubElement(
            self.root_node, GMFXMLWriter.hazard_result_tag, nsmap=NSMAP)

        _set_gml_id(hazard_result_node, HAZARDRESULT_GML_ID)

        config_node = etree.SubElement(
            hazard_result_node, GMFXMLWriter.config_tag, nsmap=NSMAP)

        hazard_processing_node = etree.SubElement(
            config_node, GMFXMLWriter.hazard_processing_tag, nsmap=NSMAP)

        # stubbed value, not yet implemented...
        hazard_processing_node.set("%sinvestigationTimeSpan" % NRML, str(50.0))

        ground_motion_field_set_node = etree.SubElement(
            hazard_result_node, GMFXMLWriter.gmf_set_tag, nsmap=NSMAP)

        _set_gml_id(ground_motion_field_set_node, GMFS_GML_ID)

        gmpe_params_node = etree.SubElement(
            ground_motion_field_set_node,
            GMFXMLWriter.gmpe_params_tag, nsmap=NSMAP)

        # stubbed value, not yet implemented...
        gmpe_params_node.set("%sIMT" % NRML, "PGA")

        # right now, all the sites are appended to one GMF
        self.parent_node = etree.SubElement(
                ground_motion_field_set_node,
                GMFXMLWriter.field_tag, nsmap=NSMAP)
        _set_gml_id(self.parent_node, GMF_GML_ID)

    def write_footer(self):
        """Write out the file footer."""
        et = etree.ElementTree(self.root_node)
        et.write(self.file, pretty_print=True, xml_declaration=True,
                 encoding="UTF-8")

    def _append_site_node(self, point, val, parent_node):
        """Write a single GMFNode element."""

        gmf_node = etree.SubElement(
                parent_node, GMFXMLWriter.node_tag, nsmap=NSMAP)
        _set_gml_id(gmf_node, "node%s" % self.node_counter)

        site_node = etree.SubElement(
                gmf_node, GMFXMLWriter.site_tag, nsmap=NSMAP)

        point_node = etree.SubElement(site_node,
                GMFXMLWriter.point_tag, nsmap=NSMAP)

        pos_node = etree.SubElement(
                point_node, GMFXMLWriter.pos_tag, nsmap=NSMAP)

        pos_node.text = "%s %s" % (str(point.x), str(point.y))

        ground_motion_node = etree.SubElement(
                gmf_node, GMFXMLWriter.ground_motion_attr, nsmap=NSMAP)

        ground_motion_node.text = str(val[self.ground_motion_attr])
        self.node_counter += 1


def _set_optional_attributes(element, value_dict, attr_keys):
    """Set the attributes for the given element specified
    in attr_keys if they are present in the value_dict dictionary."""

    for curr_key in attr_keys:
        if curr_key in value_dict:
            element.set(curr_key, str(value_dict[curr_key]))


def _set_gml_id(element, gml_id):
    """Set the attribute gml:id for the given element."""
    element.set("%sid" % GML, str(gml_id))


def _gml_id(id_key, values, default_id):
    """Return the attribute gml:id using the input dictionary. Return
    a default id if it is not present."""

    if id_key in values:
        return str(values[id_key])
    else:
        return default_id


def _set_common_attributes(attr_list, node, val):
    """Set common XML attributes, if necessary. Check if consistent
    values are given for all hazard map nodes. If hazard map node
    attributes dictionary does not have the item set, do nothing.
    """
    for attr in attr_list:
        if attr['name'] in val:
            if attr['name'] not in node.attrib:
                node.attrib[attr['name']] = str(val[attr['name']])
            elif node.attrib[attr['name']] != str(val[attr['name']]):
                error_msg = "not all nodes of the hazard map have the " \
                        "same value for common attribute %s" % attr['name']
                raise ValueError(error_msg)


def _ensure_attributes_set(attr_list, node):
    """Ensure that all the given attributes are set if required."""
    for attr in attr_list:
        if attr['name'] not in node.attrib and attr['required'] is True:
            return False
    return True


class HazardMapDBReader(object):
    """
    Read hazard map data from the database, returning a data structure
    that can be passed to :func:`HazardMapXMLWriter.serialize` to
    produce an XML file.
    """

    @staticmethod
    def deserialize(output_id):
        """
        Read a the given hazard map from the database.

        The structure of the result is documented in
        :class:`HazardMapDBWriter`.
        """
        hazard_map = models.HazardMap.objects.get(output=output_id)
        hazard_map_data = hazard_map.hazardmapdata_set.all()
        params = hazard_map.output.oq_job.profile()
        points = []

        for datum in hazard_map_data:
            values = {
                'IML': datum.value,
                'IMT': REVERSE_ENUM_MAP[params.imt],
                'investigationTimeSpan': params.investigation_time,
                'poE': hazard_map.poe,
                'statistics': hazard_map.statistic_type,
                'vs30': params.reference_vs30_value,
            }

            if hazard_map.statistic_type == 'quantile':
                values['quantileValue'] = hazard_map.quantile

            loc = datum.location
            points.append((shapes.Site(loc.x, loc.y), values))

        return points


class HazardMapDBWriter(writer.DBWriter):
    """
    Serialize the location/IML data to the `uiapi.hazard_map_data` database
    table.

    The data passed to :func:`serialize()` will look something like this::

        [(Site(-121.7, 37.6),
         {'IML': 1.9266716959669603,
          'IMT': 'PGA',
          'investigationTimeSpan': '50.0',
          'poE': 0.01,
          'statistics': 'mean',
          'vs30': 760.0}),
                        . . .
         {'IML': 1.925653989154411,
          'IMT': 'PGA',
          'investigationTimeSpan': '50.0',
          'poE': 0.01,
          'statistics': 'mean',
          'vs30': 760.0})]

    with the assumption that the poE, statistic and quantile value is
    the same for all items.
    """
    def __init__(self, nrml_path, oq_job_id):
        super(HazardMapDBWriter, self).__init__(nrml_path, oq_job_id)

        self.bulk_inserter = writer.BulkInserter(models.HazardMapData)
        self.hazard_map = None

    def get_output_type(self):
        return "hazard_map"

    def serialize(self, iterable):
        self.insert_output(self.get_output_type())

        # get the value for HazardMap from the first value
        header = iterable[0][1]
        self.hazard_map = models.HazardMap(
            output=self.output, poe=header['poE'],
            statistic_type=header['statistics'])
        if header['statistics'] == 'quantile':
            self.hazard_map.quantile = header['quantileValue']

        self.hazard_map.save()

        # Update the output record with the minimum/maximum values.
        self.output.min_value = round_float(min(
            data[1].get("IML") for data in iterable))
        self.output.max_value = round_float(max(
            data[1].get("IML") for data in iterable))

        self.output.save()

        super(HazardMapDBWriter, self).serialize(iterable)

    def insert_datum(self, point, value):
        """Inserts a single hazard map datum.

        Please note that `point.x` and `point.y` store the longitude and the
        latitude respectively.

        :param point: The hazard map point/location.
        :type point: :py:class:`shapes.GridPoint` or :py:class:`shapes.Site`
        :param float value: the value for the given location
        """
        if isinstance(point, shapes.GridPoint):
            point = point.site.point
        if isinstance(point, shapes.Site):
            point = point.point

        value = value.get("IML")
        if value is None:
            LOGGER.warn(
                "No IML value for position: [%s, %s]" % (point.x, point.y))
        else:
            self.bulk_inserter.add_entry(
                hazard_map_id=self.hazard_map.id,
                value=round_float(value),
                location="POINT(%s %s)" % (point.x, point.y))


class HazardCurveDBReader(object):
    """
    Read hazard curve data from the database, returning a data
    structure that can be passed to
    :func:`HazardCurveXMLWriter.serialize` to produce an XML file.
    """
    def deserialize(self, output_id):  # pylint: disable=R0201
        """
        Read a the given hazard curve from the database.

        The structure of the result is documented in
        :class:`HazardCurveDBWriter`.
        """
        hazard_curves = models.HazardCurve.objects.filter(output=output_id)
        params = models.Output.objects.get(id=output_id).oq_job.profile()
        points = []

        for hazard_curve_datum in hazard_curves:
            hazard_curve_data = hazard_curve_datum.hazardcurvedata_set.all()

            common = {
                'IMLValues': params.imls,
                'investigationTimeSpan': params.investigation_time,
                'IMT': REVERSE_ENUM_MAP[params.imt],
            }

            if hazard_curve_datum.end_branch_label is None:
                common['statistics'] = hazard_curve_datum.statistic_type
                if hazard_curve_datum.statistic_type == 'quantile':
                    common['quantileValue'] = hazard_curve_datum.quantile
            else:
                common['endBranchLabel'] = hazard_curve_datum.end_branch_label

            for datum in hazard_curve_data:
                attrs = common.copy()
                attrs['PoEValues'] = datum.poes

                loc = datum.location
                points.append((shapes.Site(loc.x, loc.y), attrs))

        return points


class HazardCurveDBWriter(writer.DBWriter):
    """
    Serialize the location/IML data to the `hzrdr.hazard_curve` database
    table.

    The data passed to :func:`serialize()` will look something like this::

        [(Site(-122.2, 37.5),
          {'investigationTimeSpan': '50.0',
           'IMLValues': [0.778, 1.09, 1.52, 2.13],
           'PoEValues': [0.354, 0.114, 0.023, 0.002],
           'IMT': 'PGA',
           'endBranchLabel': '1_1'}),
                 . . .
         (Site(-122.0, 37.5),
          {'investigationTimeSpan': '50.0',
           'IMLValues': [0.778, 1.09, 1.52, 2.13],
           'PoEValues': [0.354, 0.114, 0.023, 0.002],
           'IMT': 'PGA',
           'quantileValue': 0.6,
           'statistics': 'quantile'})]
    """
    def __init__(self, nrml_path, oq_job_id):
        super(HazardCurveDBWriter, self).__init__(nrml_path, oq_job_id)

        self.curves_per_branch_label = {}
        self.bulk_inserter = writer.BulkInserter(models.HazardCurveData)

    def get_output_type(self):
        return "hazard_curve"

    def insert_datum(self, point, values):
        """
        Insert a single hazard curve

        :param point: location
        :type point: :class:`openquake.shapes.Site`

        :param values: dictionary of metadata/values
        """
        # check if we have hazard curves for an end branch label, or
        # for mean/median/quantile
        if 'endBranchLabel' in values and 'statistics' in values:
            error_msg = "hazardCurveField cannot have both an end branch " \
                        "and a statistics label"
            raise ValueError(error_msg)
        elif 'endBranchLabel' in values:
            curve_label = values['endBranchLabel']
        elif 'statistics' in values:
            curve_label = values['statistics']
        else:
            error_msg = "hazardCurveField has to have either an end branch " \
                        "or a statistics label"
            raise ValueError(error_msg)

        if curve_label in self.curves_per_branch_label:
            hazard_curve = self.curves_per_branch_label[curve_label]
        else:
            if 'endBranchLabel' in values:
                hazard_curve = models.HazardCurve(
                    output=self.output, end_branch_label=curve_label)
            else:
                hazard_curve = models.HazardCurve(
                    output=self.output, statistic_type=curve_label)

                if 'quantileValue' in values:
                    hazard_curve.quantile = values['quantileValue']

            self.curves_per_branch_label[curve_label] = hazard_curve
            hazard_curve.save()

        self.bulk_inserter.add_entry(
            hazard_curve_id=hazard_curve.id,
            poes=values['PoEValues'],
            location="POINT(%s %s)" % (point.point.x, point.point.y))


class GmfDBReader(object):
    """
    Read ground motion field data from the database, returning a data structure
    that can be passed to :func:`GMFXMLWriter.serialize` to
    produce an XML file.
    """
    @staticmethod
    def deserialize(output_id):
        """
        Read a the given ground motion field from the database.

        The structure of the result is documented in :class:`GmfDBWriter`.
        """
        gmf_data = models.GmfData.objects.filter(output=output_id)
        points = {}

        for datum in gmf_data:
            loc = datum.location
            points[shapes.Site(loc.x, loc.y)] = {
                'groundMotion': datum.ground_motion,
            }

        return points


class GmfDBWriter(writer.DBWriter):
    """
    Serialize the location/IML data to the `hzrdr.hazard_curve` database
    table.

    The data passed to :func:`serialize()` will look something like this::

        {Site(-117, 40): {'groundMotion': 0.0},
         Site(-116, 40): {'groundMotion': 0.1},
         Site(-116, 41): {'groundMotion': 0.2},
         Site(-117, 41): {'groundMotion': 0.3}}
    """

    def __init__(self, nrml_path, oq_job_id):
        super(GmfDBWriter, self).__init__(nrml_path, oq_job_id)

        self.curves_per_branch_label = {}
        self.bulk_inserter = writer.BulkInserter(models.GmfData)

    def get_output_type(self):
        return "gmf"

    def insert_datum(self, point, values):
        """
        Insert a single ground motion field entry.

        :param point: location
        :type point: :class:`openquake.shapes.Site`

        :param values: dictionary with the `'groundMotion'` key
        """
        self.bulk_inserter.add_entry(
            output_id=self.output.id,
            ground_motion=values['groundMotion'],
            location="POINT(%s %s)" % (point.point.x, point.point.y))


# Facilitate multi-stage XML serialization by using the same serializer
# object for a given job and NRML path.
_XML_SERIALIZER_CACHE = defaultdict(lambda: None)


def _create_writer(job_id, serialize_to, nrml_path, create_xml_writer,
                   create_db_writer, multistage_serialization=False):
    """Common code for the functions below"""

    writers = []

    if 'db' in serialize_to:
        assert job_id, "No job_id supplied"
        job_id = int(job_id)
        writers.append(create_db_writer(nrml_path, job_id))

    if 'xml' in serialize_to and nrml_path:
        if multistage_serialization:
            obj = _XML_SERIALIZER_CACHE[(job_id, nrml_path)]
            if obj is None:
                obj = create_xml_writer(nrml_path)
                _XML_SERIALIZER_CACHE[(job_id, nrml_path)] = obj
        else:
            obj = create_xml_writer(nrml_path)
        writers.append(obj)

    return writer.compose_writers(writers)


def create_hazardcurve_writer(job_id, serialize_to, nrml_path):
    """Create a hazard curve writer observing the settings in the config file.

    :param job_id: the id of the job the curve belongs to.
    :type job_id: int
    :param serialize_to: where to serialize
    :type serialize_to: list of strings. Permitted values: 'db', 'xml'.
    :param str nrml_path: the full path of the XML/NRML representation of the
        hazard curve.
    :returns: an :py:class:`output.hazard.HazardCurveXMLWriter` or an
        :py:class:`output.hazard.HazardCurveDBWriter` instance.
    """
    return _create_writer(job_id, serialize_to, nrml_path,
                          HazardCurveXMLWriter, HazardCurveDBWriter, True)


def create_hazardmap_writer(job_id, serialize_to, nrml_path):
    """Create a hazard map writer observing the settings in the config file.

    :param job_id: the id of the job the curve belongs to.
    :type job_id: int
    :param serialize_to: where to serialize
    :type serialize_to: list of strings. Permitted values: 'db', 'xml'.
    :param str nrml_path: the full path of the XML/NRML representation of the
        hazard map.
    :returns: an :py:class:`output.hazard.HazardMapXMLWriter` or an
        :py:class:`output.hazard.HazardMapDBWriter` instance.
    """
    return _create_writer(job_id, serialize_to, nrml_path, HazardMapXMLWriter,
                          HazardMapDBWriter, True)


def create_gmf_writer(job_id, serialize_to, nrml_path):
    """Create a GMF writer using the settings in the config file.

    :param job_id: the id of the job the curve belongs to.
    :type job_id: int
    :param serialize_to: where to serialize
    :type serialize_to: list of strings. Permitted values: 'db', 'xml'.
    :param str nrml_path: the full path of the XML/NRML representation of the
        ground motion field.
    :returns: an :py:class:`output.hazard.GMFXMLWriter` or an
        :py:class:`output.hazard.GmfDBWriter` instance.
    """
    return _create_writer(
        job_id, serialize_to, nrml_path, GMFXMLWriter, GmfDBWriter)


@general.singleton
class SerializerContext(object):
    """Used to facilitate multi-stage XML serialization."""
    def __init__(self):
        self.blocks = 0
        self.cblock = 0
        self.i_total = 0
        self.i_done = 0
        self.i_next = 0

    def update(self, context):
        """Updates the serialization context.

        :param namedtuple context: a `namedtuple` with the following
            five integers:
                - blocks: overall number of blocks the calculation is divided
                    into
                - cblock: current block number (1 based)
                - i_total: overall number of items to be serialized in the
                    current block
                - i_done: number of items already serialized in the
                    current block
                - i_next: number of items to be serialized next
        """
        LOGGER.debug(context)
        self.blocks = context.blocks
        self.cblock = context.cblock
        self.i_total = context.i_total
        self.i_done = context.i_done
        self.i_next = context.i_next

    def get_mode(self):
        """Figure out the XML serialization mode.

        The possible modes are:
            - start
            - middle
            - end
            - start and end (single pass serialization)

        :returns: a `namedtuple` with three booleans: start, middle and end
            that are set to reflect the current serialization mode.
        """
        # Figure out the mode, are we at the beginning, in the middle or at
        # the end of the XML file?

        mode = namedtuple("SerializerMode", "start, middle, end")

        if self.cblock > 1 and self.cblock < self.blocks:
            return mode(False, True, False)

        start = middle = end = False
        if self.cblock == 1:
            # We are serializing data from the first block.
            if self.i_done == 0:
                # First block, nothing serialized yet.
                start = True
            else:
                middle = True
        if self.cblock == self.blocks:
            # We are serializing data from the last block.
            items_left = self.i_total - self.i_done - self.i_next
            if items_left == 0:
                # Last block, last batch.
                middle = False
                end = True
            elif not start:
                middle = True

        return mode(start, middle, end)
