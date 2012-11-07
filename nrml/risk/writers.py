# coding=utf-8
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
Module containing writers for risk output artifacts.
"""

from lxml import etree

import nrml


class LossCurveXMLWriter(object):

    def __init__(self, path, investigation_time,
                 source_model_tree_path=None, gsim_tree_path=None, unit=None):

        self._unit = unit
        self._path = path
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._source_model_tree_path = source_model_tree_path

        self._loss_curves = None

    def serialize(self, data):

        with open(self._path, "w") as output:
            root = etree.Element("nrml", nsmap=nrml.SERIALIZE_NS_MAP)

            for curve in data:
                if self._loss_curves is None:
                    self._create_loss_curves_container(root)

                loss_curve = etree.SubElement(self._loss_curves, "lossCurve")

                _append_location(loss_curve, curve.location)
                loss_curve.set("assetRef", curve.asset_ref)

                poes = etree.SubElement(loss_curve, "poEs")
                poes.text = " ".join([str(p) for p in curve.poes])

                losses = etree.SubElement(loss_curve, "losses")
                losses.text = " ".join([str(p) for p in curve.losses])

                if curve.loss_ratios is not None:
                    loss_ratios = etree.SubElement(loss_curve, "lossRatios")

                    loss_ratios.text = " ".join(
                        [str(p) for p in curve.loss_ratios])

            output.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_loss_curves_container(self, root):
        self._loss_curves = etree.SubElement(root, "lossCurves")

        self._loss_curves.set("investigationTime",
            str(self._investigation_time))

        if self._source_model_tree_path is not None:
            self._loss_curves.set("sourceModelTreePath",
                str(self._source_model_tree_path))

        if self._gsim_tree_path is not None:
            self._loss_curves.set("gsimTreePath",
                str(self._gsim_tree_path))

        if self._unit is not None:
            self._loss_curves.set("unit", str(self._unit))


def _append_location(element, location):
    gml_ns = nrml.SERIALIZE_NS_MAP["gml"]

    gml_point = etree.SubElement(element, "{%s}Point" % gml_ns)
    gml_pos = etree.SubElement(gml_point, "{%s}pos" % gml_ns)
    gml_pos.text = "%s %s" % (location.x, location.y)
