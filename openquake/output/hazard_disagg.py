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


class DisaggregationBinaryMatrixXMLWriter(writer.FileWriter):
    """Write a disaggregation field in NRML format."""

    OPTIONAL_PARAMS = ("endBranchLabel", "statistics", "quantileValue")

    def __init__(self, path):
        writer.FileWriter.__init__(self, path)

        self.id_counter = 0

        self.nrml_el = None
        self.disagg_result_node_el = None
        self.disagg_result_field_el = None

    def write(self, site, values):
        """Write the disaggregation result for the given site.

        :param site: site related to the disaggregation result
        :type site: :class:`openquake.shapes.Site`
        :param values: data to write
        :type values: dict in the following format:
            {"poE": 0.1,
             "IMT": "PGA",
             "groundMotionValue": 0.25,
             "endBranchLabel": 1,
             "statistics": "mean",
             "quantileValue": 0.1,
             "mset": [
             {"disaggregationPMFType": "MagnitudePMF", "path": "filea"},
             {"disaggregationPMFType": "MagnitudePMF", "path": "fileb"}]}

        The "endBranchLabel", "statistics" and "quantileValue" keys are
        optional and are written only if specified. The other keys
        are considered mandatory.
        """

        if self.nrml_el is None:
            self._append_root_elements(values)

        self._append_disagg_result_node()
        self._append_site(site)
        self._append_matrix_set(values)

    def _append_matrix_set(self, values):
        """Append the <disaggregationMatrixSet/> element under the
        current <disaggregationResultNode/> node."""

        disagg_matrix_set_tag = "%sdisaggregationMatrixSet" % NRML

        disagg_matrix_set_el = etree.SubElement(
            self.disagg_result_node_el, disagg_matrix_set_tag, nsmap=NSMAP)

        disagg_matrix_set_el.set(
            "groundMotionValue", str(values["groundMotionValue"]))

        disagg_matrix_tag = "%sdisaggregationMatrixBinaryFile" % NRML

        if not values["mset"]:
            raise RuntimeError(
                "You need at least one matrix to produce a valid output!")

        for disagg_matrix in values["mset"]:
            disagg_matrix_el = etree.SubElement(
                disagg_matrix_set_el, disagg_matrix_tag, nsmap=NSMAP)

            disagg_matrix_el.set("path", disagg_matrix["path"])
            disagg_matrix_el.set("disaggregationPMFType",
                    disagg_matrix["disaggregationPMFType"])

    def _append_site(self, site):
        """Append the <gml:Point/> element under the current
        <disaggregationResultNode/> node."""

        point_el = etree.SubElement(etree.SubElement(
                self.disagg_result_node_el, "%ssite" % NRML), "%sPoint" % GML)

        pos_el = etree.SubElement(point_el, "%spos" % GML)
        pos_el.text = "%s %s" % (site.longitude, site.latitude)

    def _append_disagg_result_node(self):
        """Append the <disaggregationResultNode/> element under
        the current instance document."""

        disagg_result_node_tag = "%sdisaggregationResultNode" % NRML

        disagg_result_node_el = etree.SubElement(
            self.disagg_result_field_el, disagg_result_node_tag, nsmap=NSMAP)

        self._set_id(disagg_result_node_el)
        self.disagg_result_node_el = disagg_result_node_el

    def _append_root_elements(self, values):
        """Append the <nrml/> and <disaggregationResultField/> element under
        the current instance document."""

        self.nrml_el = etree.Element("%snrml" % NRML, nsmap=NSMAP)
        self._set_id(self.nrml_el)

        disagg_result_field_tag = "%sdisaggregationResultField" % NRML

        self.disagg_result_field_el = etree.SubElement(
            self.nrml_el, disagg_result_field_tag, nsmap=NSMAP)

        self._set_id(self.disagg_result_field_el)
        self.disagg_result_field_el.set("poE", str(values["poE"]))
        self.disagg_result_field_el.set("IMT", str(values["IMT"]))

        for optional_param in self.OPTIONAL_PARAMS:
            if optional_param in values:
                self.disagg_result_field_el.set(
                    optional_param, str(values[optional_param]))

    def _set_id(self, elem):
        """Set the gml:id attribute to the given element."""

        _set_gml_id(elem, "ID" + str(self.id_counter))
        self.id_counter += 1

    def close(self):
        """Write the instance document and close the file."""

        if self.nrml_el is None:
            raise RuntimeError(
                "You need at least one set to produce a valid output!")

        self.file.write(etree.tostring(self.nrml_el, pretty_print=True,
                xml_declaration=True, encoding="UTF-8"))

        self.file.close()
