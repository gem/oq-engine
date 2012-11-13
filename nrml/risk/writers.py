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
    """
    :param path:
        File path (including filename) for results to be saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param str source_model_tree_path:
        Id of the source model tree path (obtained concatenating the IDs of
        the branches the path is made of) for which input hazard curves
        have been computed.
    :param str gsim_tree_path:
        Id of the gsim (ground shaking intensity model) tree path (obtained
        concatenating the IDs of the branches the path is made of) for which
        input hazard curves have been computed.
    :param str unit:
        Attribute describing how the value of the assets has been measured.
    :param str statistics:
        `mean` or `quantile`. When serializing loss curves produced from
        statistical hazard inputs, it describes the type of statistic used.
    :param float quantile_value:
        When serializing loss curves produced from quantile hazard inputs,
        it describes the quantile value.
    """

    def __init__(self, path, investigation_time,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None):

        if statistics is not None:
            _check_statistics_or_logic_tree(
                source_model_tree_path, gsim_tree_path)

            _check_statistics_metadata(statistics, quantile_value)
        else:
            _check_logic_tree_metadata(source_model_tree_path, gsim_tree_path)

        self._unit = unit
        self._path = path
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._source_model_tree_path = source_model_tree_path
        self._statistics = statistics
        self._quantile_value = quantile_value

        self._loss_curves = None

    def serialize(self, data):
        """
        Serialize a collection of loss curves.

        :param data:
            An iterable of loss curves objects. Each object should:

            * define an attribute `location`, which is itself an object
            defining two attributes, `x` containing the longitude value
            and `y` containing the latitude value.
            * define an attribute `asset_ref`, which contains the unique
            identifier of the asset related to the loss curve.
            * define an attribute `poes`, which is a list of floats
            describing the probabilities of exceedance.
            * define an attribute `losses`, which is a list of floats
            describing the losses.
            * define an attribute `loss_ratios`, which is a list of floats
            describing the loss ratios.

            All attributes must be defined, except for `loss_ratios` that
            can be `None` since it is optional in the schema.

            Also, `poes`, `losses` and `loss_ratios` values must be indexed
            coherently, i.e.: the loss (and optionally loss ratio) at index
            zero is related to the probability of exceedance at the same
            index.
        """

        with open(self._path, "w") as output:
            root = etree.Element("nrml", nsmap=nrml.SERIALIZE_NS_MAP)

            for curve in data:
                if self._loss_curves is None:
                    self._create_loss_curves_elem(root)

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

    def _create_loss_curves_elem(self, root):
        """
        Create the <lossCurves /> element with associated attributes.
        """

        self._loss_curves = etree.SubElement(root, "lossCurves")

        self._loss_curves.set("investigationTime",
            str(self._investigation_time))

        if self._source_model_tree_path is not None:
            self._loss_curves.set("sourceModelTreePath",
                str(self._source_model_tree_path))

        if self._gsim_tree_path is not None:
            self._loss_curves.set("gsimTreePath",
                str(self._gsim_tree_path))

        if self._statistics is not None:
            self._loss_curves.set("statistics",
                str(self._statistics))

        if self._quantile_value is not None:
            self._loss_curves.set("quantileValue",
                str(self._quantile_value))

        if self._unit is not None:
            self._loss_curves.set("unit", str(self._unit))


def _append_location(element, location):
    """
    Append the geographical location to the given element.
    """

    gml_ns = nrml.SERIALIZE_NS_MAP["gml"]

    gml_point = etree.SubElement(element, "{%s}Point" % gml_ns)
    gml_pos = etree.SubElement(gml_point, "{%s}pos" % gml_ns)
    gml_pos.text = "%s %s" % (location.x, location.y)


def _check_statistics_metadata(statistics, quantile_value):
    """
    `statistics` must be in ("quantile", "mean") and `quantile_value`
    must be specified when `statistics` == "quantile".
    """

    if statistics not in ("quantile", "mean"):
        raise ValueError("`statistics` must be in ('quantile', 'mean').")

    if statistics == "quantile" and quantile_value is None:
        raise ValueError("When `statistics` == 'quantile', "
            "`quantile_value` must also be specified.")


def _check_logic_tree_metadata(source_model_tree_path, gsim_tree_path):
    """
    Logic tree parameters must be both specified.
    """

    if source_model_tree_path is None or gsim_tree_path is None:
        raise ValueError("When specifying a logic tree branch, "
            "both `source_model_tree_path` and `gsim_tree_path` "
            "must be specified.")


def _check_statistics_or_logic_tree(source_model_tree_path,
                                    gsim_tree_path):

    """
    When `statistics` is used, no logic tree parameters must be specified.
    """

    if source_model_tree_path is not None or gsim_tree_path is not None:
        raise ValueError("You must choose `statistics` or "
            "(`source_model_tree_path`, `gsim_tree_path`), not both.")
