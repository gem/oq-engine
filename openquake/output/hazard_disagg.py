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

"""Output serialization classes for the Hazard Disaggregation calculator."""

from lxml import etree

from openquake import writer
from openquake.xml import NSMAP, NRML, GML
from openquake.output.hazard import _set_gml_id


# Disabling pylint for 'too many instance attributes' and 'too many arguments'
# pylint: disable=R0902,R0913
class DisaggregationBinaryMatrixXMLWriter(writer.FileWriter):
    """Write a file for a single disaggregation field in NRML format."""

    def __init__(self, path, poe, imt, subsets, end_branch_label=None,
                 statistics=None, quantile_value=None):
        """
        :param path:
            Path to the resulting XML file.
        :param float poe:
            Probability of Exceedence value associated with the entire result
            file.`
        :param imt:
            Intensity Measure Type. One of PGA, SA, PGV, PGD, IA, or RSD.
        :param subsets:
            List of Disaggregation subset types contained in this file. For
            example::
                ['MagnitudePMF', 'MagnitudeDistancePMF']
        :param end_branch_label: optional
        :param statistics: optional
        :param quantile_value: optional
        """
        writer.FileWriter.__init__(self, path)

        self.poe = poe
        self.imt = imt
        self.subsets = subsets
        self.end_branch_label = end_branch_label
        self.statistics = statistics
        self.quantile_value = quantile_value

        self.id_counter = 0

        self.nrml_el = None
        self.disagg_result_field_el = None

        self._write_root_elements()

    def write(self, site, value):
        """Write the disaggregation result for the given site.

        :param site: site related to the disaggregation result
        :type site: :class:`openquake.shapes.Site`
        :param value: data to write
        :type value: dict in the following format::
            {"groundMotionValue": 0.25,
             "path": "/path/to/file"}
        """
        self._write_disagg_result_node(site, value)

    def _write_root_elements(self):
        """Append the <nrml/> and <disaggregationResultField/> element under
        the current instance document."""

        # root <nrml> element:
        self.nrml_el = etree.Element("%snrml" % NRML, nsmap=NSMAP)
        self._set_id(self.nrml_el)

        # root <disaggregationResultField> element:
        disagg_result_field_tag = "%sdisaggregationResultField" % NRML

        self.disagg_result_field_el = etree.SubElement(
            self.nrml_el, disagg_result_field_tag, nsmap=NSMAP)

        self._set_id(self.disagg_result_field_el)

        self.disagg_result_field_el.set("poE", str(self.poe))
        self.disagg_result_field_el.set("IMT", str(self.imt))

        for attr, value in (("endBranchLabel", self.end_branch_label),
                            ("statistics", self.statistics),
                            ("quantileValue", self.quantile_value)):
            if value:
                self.disagg_result_field_el.set(attr, str(value))

        disagg_result_types_el = etree.SubElement(
            self.disagg_result_field_el,
            "%sdisaggregationResultTypes" % NRML,
            nsmap=NSMAP)

        disagg_result_types_el.text = " ".join(self.subsets)

    def _write_disagg_result_node(self, site, value):
        """Write a <disaggregationResult/> for a given site.

        :param site: site related to the disaggregation result
        :type site: :class:`openquake.shapes.Site`
        :param value: data to write
        :type value: dict in the following format::
            {"groundMotionValue": 0.25,
             "path": "/path/to/file"}
             "path": "/path/to/file"}

        Given an input `site` of Site(1.0, 1.0) and `value` of::
            {"groundMotionValue": 0.25,
             "path": "filea"}

        the following elements will be written to the XML tree:
            <disaggregationResultNode gml:id="IDxxx">
                <site>
                    <gml:Point>
                        <gml:pos>1.0 1.0</gml:pos>
                    </gml:Point>
                </site>
                <disaggregationResult groundMotionValue="0.25" path="filea"/>
            </disaggregationResultNode>
        """
        # disaggregationResultNode:
        disagg_result_node_tag = "%sdisaggregationResultNode" % NRML

        disagg_result_node_el = etree.SubElement(
            self.disagg_result_field_el, disagg_result_node_tag, nsmap=NSMAP)

        self._set_id(disagg_result_node_el)

        # site:
        site_el = etree.SubElement(disagg_result_node_el, "%ssite" % NRML)

        point_el = etree.SubElement(site_el, "%sPoint" % GML)

        pos_el = etree.SubElement(point_el, "%spos" % GML)
        pos_el.text = "%s %s" % (site.longitude, site.latitude)

        # disaggregationResult:
        disagg_result_tag = "%sdisaggregationResult" % NRML

        disagg_result_el = etree.SubElement(
            disagg_result_node_el, disagg_result_tag, nsmap=NSMAP)

        # set the groundMotionValue and Path
        for attr in ("groundMotionValue", "path"):
            disagg_result_el.set(attr, str(value[attr]))

    def _set_id(self, elem):
        """Set the gml:id attribute to the given element."""

        _set_gml_id(elem, "ID" + str(self.id_counter))
        self.id_counter += 1

    def close(self):
        """Write the instance document and close the file."""
        self.file.write(etree.tostring(self.nrml_el, pretty_print=True,
                xml_declaration=True, encoding="UTF-8"))

        self.file.close()
