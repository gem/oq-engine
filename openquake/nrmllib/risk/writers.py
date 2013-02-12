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

import itertools

from lxml import etree

import openquake.nrmllib


class LossCurveXMLWriter(object):
    """
    :param path:
        File path (including filename) for results to be saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param str source_model_tree_path:
        Id of the source model tree path (obtained by concatenating the IDs of
        the branches the path is made of) for which input hazard curves
        have been computed.
    :param str gsim_tree_path:
        Id of the gsim (ground shaking intensity model) tree path (obtained
        by concatenating the IDs of the branches the path is made of) for
        which input hazard curves have been computed.
    :param str statistics:
        `mean` or `quantile`. When serializing loss curves produced from
        statistical hazard inputs, it describes the type of statistic used.
    :param float quantile_value:
        When serializing loss curves produced from quantile hazard inputs,
        it describes the quantile value.
    :param float quantile_value:
        When serializing loss curves produced from quantile hazard inputs,
        it describes the quantile value.
    :param str unit:
        Attribute describing how the value of the assets has been measured.
    :param bool insured:
        True if it is an insured loss curve
    """

    def __init__(self, path, investigation_time,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None,
                 insured=False):

        validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                 statistics, quantile_value)

        self._unit = unit
        self._path = path
        self._statistics = statistics
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._source_model_tree_path = source_model_tree_path
        self._insured = insured

        self._loss_curves = None

    def serialize(self, data):
        """
        Serialize a collection of loss curves.

        :param data:
            An iterable of loss curve objects. Each object should:

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

        _assert_valid_input(data)

        with open(self._path, "w") as output:
            root = etree.Element("nrml",
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

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

        if self._insured:
            self._loss_curves.set("insured", str(self._insured))

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


class AggregateLossCurveXMLWriter(object):
    """
    :param path:
        File path (including filename) for results to be saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param str source_model_tree_path:
        Id of the source model tree path (obtained by concatenating the IDs of
        the branches the path is made of) for which input hazard curves
        have been computed.
    :param str gsim_tree_path:
        Id of the gsim (ground shaking intensity model) tree path (obtained
        by concatenating the IDs of the branches the path is made of) for
        which input hazard curves have been computed.
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

        validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                 statistics, quantile_value)

        self._unit = unit
        self._path = path
        self._statistics = statistics
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._source_model_tree_path = source_model_tree_path

    def serialize(self, data):
        """
        Serialize an aggregation loss curve.

        :param data:
            An object representing an aggregate loss curve. This object should:

            * define an attribute `poes`, which is a list of floats
              describing the probabilities of exceedance.
            * define an attribute `losses`, which is a list of floats
              describing the losses.

            Also, `poes`, `losses` values must be indexed coherently,
            i.e.: the loss at index zero is related to the probability
            of exceedance at the same index.
        """

        if data is None:
            raise ValueError("You can not serialize an empty document")

        with open(self._path, "w") as output:
            root = etree.Element("nrml",
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            aggregate_loss_curve = etree.SubElement(root, "aggregateLossCurve")

            aggregate_loss_curve.set("investigationTime",
                                     str(self._investigation_time))

            if self._source_model_tree_path is not None:
                aggregate_loss_curve.set("sourceModelTreePath",
                                         str(self._source_model_tree_path))

            if self._gsim_tree_path is not None:
                aggregate_loss_curve.set("gsimTreePath",
                                         str(self._gsim_tree_path))

            if self._statistics is not None:
                aggregate_loss_curve.set("statistics", str(self._statistics))

            if self._quantile_value is not None:
                aggregate_loss_curve.set("quantileValue",
                                         str(self._quantile_value))

            if self._unit is not None:
                aggregate_loss_curve.set("unit", str(self._unit))

            poes = etree.SubElement(aggregate_loss_curve, "poEs")
            poes.text = " ".join([str(p) for p in data.poes])

            losses = etree.SubElement(aggregate_loss_curve, "losses")
            losses.text = " ".join(["%.4f" % p for p in data.losses])

            output.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))


class LossMapXMLWriter(object):
    """
    Serializer for loss maps produced with the classical and
    probabilistic calculators.

    :param path:
        File path (including filename) for results to be saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param float poe:
        Probability of exceedance used to interpolate the losses
        producing this loss map.
    :param str source_model_tree_path:
        Id of the source model tree path (obtained by concatenating the IDs of
        the branches the path is made of) for which input hazard curves
        have been computed.
    :param str gsim_tree_path:
        Id of the gsim (ground shaking intensity model) tree path (obtained
        by concatenating the IDs of the branches the path is made of) for
        which input hazard curves have been computed.
    :param str unit:
        Attribute describing how the value of the assets has been measured.
    :param str loss_category:
        Attribute describing the category (economic, population, buildings,
        etc..) of the losses producing this loss map.
    :param str statistics:
        `mean` or `quantile`. When serializing loss curves produced from
        statistical hazard inputs, it describes the type of statistic used.
    :param float quantile_value:
        When serializing loss curves produced from quantile hazard inputs,
        it describes the quantile value.
    """

    def __init__(self, path, investigation_time, poe,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None,
                 loss_category=None):

        # FIXME Relaxed constraint for scenario risk calculator
        # which doesn't have hazard metadata.
        if gsim_tree_path and source_model_tree_path:
            validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                     statistics, quantile_value)

        self._poe = poe
        self._unit = unit
        self._path = path
        self._statistics = statistics
        self._loss_category = loss_category
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._source_model_tree_path = source_model_tree_path

        self._loss_map = None
        self._loss_nodes = {}

    def serialize(self, data):
        """
        Serialize a collection of losses.

        :param data:
            An iterable of loss objects. Each object should:

            * define an attribute `location`, which is itself an object
              defining two attributes, `x` containing the longitude value
              and `y` containing the latitude value. Also, it must define
              an attribute `wkt`, which is the Well-known text
              representation of the location.
            * define an attribute `asset_ref`, which contains the unique
              identifier of the asset related to the loss curve.
            * define an attribute `value`, which is the value of the loss.
        """

        _assert_valid_input(data)

        with open(self._path, "w") as output:
            root = etree.Element("nrml",
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            for loss in data:
                if self._loss_map is None:
                    self._create_loss_map_elem(root)

                loss_node = self._loss_nodes.get(loss.location.wkt)

                if loss_node is None:
                    loss_node = etree.SubElement(self._loss_map, "node")
                    _append_location(loss_node, loss.location)
                    self._loss_nodes[loss.location.wkt] = loss_node

                loss_elem = etree.SubElement(loss_node, "loss")
                loss_elem.set("assetRef", str(loss.asset_ref))

                if loss.std_dev:
                    loss_elem.set("mean", str(loss.value))
                    loss_elem.set("stdDev", str(loss.std_dev))
                else:
                    loss_elem.set("value", str(loss.value))

            output.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_loss_map_elem(self, root):
        """
        Create the <lossMap /> element with associated attributes.
        """

        self._loss_map = etree.SubElement(root, "lossMap")
        self._loss_map.set("investigationTime", str(self._investigation_time))
        self._loss_map.set("poE", str(self._poe))

        if self._source_model_tree_path is not None:
            self._loss_map.set("sourceModelTreePath",
                               str(self._source_model_tree_path))

        if self._gsim_tree_path is not None:
            self._loss_map.set("gsimTreePath", str(self._gsim_tree_path))

        if self._statistics is not None:
            self._loss_map.set("statistics", str(self._statistics))

        if self._quantile_value is not None:
            self._loss_map.set("quantileValue", str(self._quantile_value))

        if self._loss_category is not None:
            self._loss_map.set("lossCategory", str(self._loss_category))

        if self._unit is not None:
            self._loss_map.set("unit", str(self._unit))


class BCRMapXMLWriter(object):
    """
    Serializer for bcr (benefit cost ratio) maps produced with the classical
    and probabilistic calculators.

    :param path:
        File path (including filename) for results to be saved to.
    :param float interest_rate:
        The inflation discount rate.
    :param float asset_life_expectancy:
        The period of time in which the building is expected to be used.
    :param str source_model_tree_path:
        Id of the source model tree path (obtained by concatenating the IDs of
        the branches the path is made of) for which input hazard curves
        have been computed.
    :param str gsim_tree_path:
        Id of the gsim (ground shaking intensity model) tree path (obtained
        by concatenating the IDs of the branches the path is made of) for
        which input hazard curves have been computed.
    :param str unit:
        Attribute describing how the value of the assets has been measured.
    :param str loss_category:
        Attribute describing the category (economic, population, buildings,
        etc..) of the losses producing this bcr map.
    :param str statistics:
        `mean` or `quantile`. When serializing bcr values produced from
        statistical hazard inputs, it describes the type of statistic used.
    :param float quantile_value:
        When serializing bcr values produced from quantile hazard inputs,
        it describes the quantile value.
    """

    def __init__(self, path, interest_rate, asset_life_expectancy,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None,
                 loss_category=None):

        validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                 statistics, quantile_value)

        self._unit = unit
        self._path = path
        self._statistics = statistics
        self._interest_rate = interest_rate
        self._loss_category = loss_category
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._asset_life_expectancy = asset_life_expectancy
        self._source_model_tree_path = source_model_tree_path

        self._bcr_map = None
        self._bcr_nodes = {}

    def serialize(self, data):
        """
        Serialize a collection of (benefit cost) ratios.

        :param data:
            An iterable of bcr objects. Each object should:

            * define an attribute `location`, which is itself an object
              defining two attributes, `x` containing the longitude value
              and `y` containing the latitude value. Also, it must define
              an attribute `wkt`, which is the Well-known text
              representation of the location.
            * define an attribute `asset_ref`, which contains the unique
              identifier of the asset related to the (benefit cost) ratio.
            * define an attribute `average_annual_loss_original`, which is
              the expected average annual economic loss using the original
              vulnerability of the asset.
            * define an attribute `average_annual_loss_retrofitted`,
              which is the expected average annual economic loss using the
              improved (better design or retrofitted) vulnerability
              of the asset.
            * define an attribute `bcr`, which is the value of the (
              benefit cost) ratio.
        """

        _assert_valid_input(data)

        with open(self._path, "w") as output:
            root = etree.Element("nrml",
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            for bcr in data:
                if self._bcr_map is None:
                    self._create_bcr_map_elem(root)

                bcr_node = self._bcr_nodes.get(bcr.location.wkt)

                if bcr_node is None:
                    bcr_node = etree.SubElement(self._bcr_map, "node")
                    _append_location(bcr_node, bcr.location)
                    self._bcr_nodes[bcr.location.wkt] = bcr_node

                bcr_elem = etree.SubElement(bcr_node, "bcr")
                bcr_elem.set("assetRef", str(bcr.asset_ref))
                bcr_elem.set("ratio", str(bcr.bcr))

                bcr_elem.set("aalOrig", str(
                    bcr.average_annual_loss_original))

                bcr_elem.set("aalRetr", str(
                    bcr.average_annual_loss_retrofitted))

            output.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_bcr_map_elem(self, root):
        """
        Create the <bcrMap /> element with associated attributes.
        """

        self._bcr_map = etree.SubElement(root, "bcrMap")

        self._bcr_map.set("interestRate", str(self._interest_rate))
        self._bcr_map.set("assetLifeExpectancy",
                          str(self._asset_life_expectancy))

        if self._source_model_tree_path is not None:
            self._bcr_map.set("sourceModelTreePath",
                              str(self._source_model_tree_path))

        if self._gsim_tree_path is not None:
            self._bcr_map.set("gsimTreePath", str(self._gsim_tree_path))

        if self._statistics is not None:
            self._bcr_map.set("statistics", str(self._statistics))

        if self._quantile_value is not None:
            self._bcr_map.set("quantileValue", str(self._quantile_value))

        if self._loss_category is not None:
            self._bcr_map.set("lossCategory", str(self._loss_category))

        if self._unit is not None:
            self._bcr_map.set("unit", str(self._unit))


class DmgDistPerAssetXMLWriter(object):
    """
    Write the damage distribution per asset artifact
    to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param damage_states: the damage states considered in this distribution.
    :type damage_states: list of strings, for example:
        ["no_damage", "slight", "moderate", "extensive", "complete"]
    """

    def __init__(self, path, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.root = None
        self.dmg_dist_el = None

    def serialize(self, assets_data):
        """
        Serialize the entire distribution.

        :param assets_data: the distribution to be written.
        :type assets_data: list of
            :class:`openquake.db.models.DmgDistPerAsset` instances.
            The component is able to correctly re-order the elements by
            site and asset, but the damage states must be ordered in advance.

        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if assets_data is None or not len(assets_data):
            raise RuntimeError(
                "empty damage distributions are not supported by the schema.")

        # contains the set of <DDNode /> elements indexed per site
        dd_nodes = {}

        # contains the set of <asset /> elements indexed per asset ref
        asset_nodes = {}

        with open(self.path, "w") as fh:
            self.root, self.dmg_dist_el = _create_root_elems(
                self.damage_states, "dmgDistPerAsset")

            assets = []
            # group by limit state index (lsi)
            for lsi, rows in itertools.groupby(
                    assets_data, lambda r: r.dmg_state.lsi):
                # sort by asset_ref
                for asset_data in sorted(
                        rows, key=lambda r: r.exposure_data.asset_ref):
                    assets.append(asset_data)
            for asset_data in assets:
                site = asset_data.exposure_data.site
                asset_ref = asset_data.exposure_data.asset_ref

                # lookup the correct <DDNode /> element
                dd_node_el = dd_nodes.get(site.wkt, None)

                # nothing yet related to this site,
                # creating the <DDNode /> element
                if dd_node_el is None:
                    dd_node_el = dd_nodes[site.wkt] = \
                        self._create_dd_node_elem(site)

                # lookup the correct <asset /> element
                asset_node_el = asset_nodes.get(asset_ref, None)

                # nothing yet related to this asset,
                # creating the <asset /> element
                if asset_node_el is None:
                    asset_node_el = asset_nodes[asset_ref] = \
                        _create_asset_elem(dd_node_el, asset_ref)

                _create_damage_elem(
                    asset_node_el, asset_data.dmg_state.dmg_state,
                    asset_data.mean, asset_data.stddev)

            fh.write(etree.tostring(
                self.root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_dd_node_elem(self, site):
        """
        Create the <DDNode /> element related to the given site.
        """
        dd_node_el = etree.SubElement(self.dmg_dist_el, "DDNode")
        _append_location(dd_node_el, site)
        return dd_node_el


class CollapseMapXMLWriter(object):
    """
    Write the collapse map artifact to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    """

    def __init__(self, path):
        self.path = path
        self.root = None
        self.collapse_map_el = None

    def serialize(self, cmap_data):
        """
        Serialize the entire distribution.

        :param cmap_data: the distribution to be written.
        :type cmap_data: list of
            :py:class:`openquake.db.models.CollapseMapData` instances.
            There are no restrictions about the ordering of the elements,
            the component is able to correctly re-order the elements by
            site and asset.
        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if cmap_data is None or not len(cmap_data):
            raise RuntimeError(
                "empty maps are not supported by the schema.")

        # contains the set of <CMNode /> elements indexed per site
        cm_nodes = {}

        with open(self.path, "w") as fh:
            self.root, self.collapse_map_el = self._create_root_elems()

            # order by asset_ref
            for cfraction in sorted(
                    cmap_data, key=lambda r: r.exposure_data.asset_ref):
                site = cfraction.exposure_data.site

                # lookup the correct <CMNode /> element
                cm_node_el = cm_nodes.get(site.wkt, None)

                # nothing yet related to this site,
                # creating the <CMNode /> element
                if cm_node_el is None:
                    cm_node_el = cm_nodes[site.wkt] = \
                        self._create_cm_node_elem(site)

                _create_cf_elem(cfraction, cm_node_el)

            fh.write(etree.tostring(
                self.root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))

    def _create_cm_node_elem(self, site):
        """
        Create the <CMNode /> element related to the given site.
        """
        cm_node_el = etree.SubElement(self.collapse_map_el, "CMNode")
        _append_location(cm_node_el, site)
        return cm_node_el

    def _create_root_elems(self):
        """
        Create the <nrml /> and <collapseMap /> elements.
        """
        root = etree.Element("nrml", nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)
        cm_el = etree.SubElement(root, "collapseMap")
        return root, cm_el


def _create_cf_elem(cfraction, cm_node_el):
    """
    Create the <cf /> element related to the given site.
    """
    cf_el = etree.SubElement(cm_node_el, "cf")
    cf_el.set("assetRef", cfraction.exposure_data.asset_ref)
    cf_el.set("mean", str(cfraction.mean))
    cf_el.set("stdDev", str(cfraction.stddev))


class DmgDistPerTaxonomyXMLWriter(object):
    """
    Write the damage distribution per taxonomy artifact
    to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param damage_states: the damage states considered in this distribution.
    :type damage_states: list of strings, for example:
        ["no_damage", "slight", "moderate", "extensive", "complete"]
    """

    def __init__(self, path, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.root = None
        self.dmg_dist_el = None

    def serialize(self, taxonomy_data):
        """
        Serialize the entire distribution.

        :param taxonomy_data: the distribution to be written.
        :type taxonomy_data: list of
            :py:class:`openquake.db.models.DmgDistPerTaxonomy` instances.
            There are no restrictions about the ordering of the elements,
            the component is able to correctly re-order the elements by
            asset taxonomy.
        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if taxonomy_data is None or not len(taxonomy_data):
            raise RuntimeError(
                "empty damage distributions are not supported by the schema.")

        # contains the set of <DDNode /> elements indexed per taxonomy
        dd_nodes = {}

        with open(self.path, "w") as fh:
            self.root, self.dmg_dist_el = _create_root_elems(
                self.damage_states, "dmgDistPerTaxonomy")

            for tdata in taxonomy_data:
                # lookup the correct <DDNode /> element
                dd_node_el = dd_nodes.get(tdata.taxonomy, None)

                # nothing yet related to this taxonomy,
                # creating the <DDNode /> element
                if dd_node_el is None:
                    dd_node_el = dd_nodes[tdata.taxonomy] = \
                        self._create_dd_node_elem(tdata.taxonomy)

                _create_damage_elem(dd_node_el, tdata.dmg_state.dmg_state,
                                    tdata.mean, tdata.stddev)

            fh.write(
                etree.tostring(
                    self.root, pretty_print=True, xml_declaration=True,
                    encoding="UTF-8"))

    def _create_dd_node_elem(self, taxonomy):
        """
        Create the <DDNode /> element related to the given taxonomy.
        """

        dd_node_el = etree.SubElement(self.dmg_dist_el, "DDNode")

        # <taxonomy /> node
        taxonomy_el = etree.SubElement(dd_node_el, "taxonomy")
        taxonomy_el.text = taxonomy

        return dd_node_el


class DmgDistTotalXMLWriter(object):
    """
    Write the total damage distribution artifact
    to the defined NRML format.

    :param path: full path to the resulting XML file (including file name).
    :type path: string
    :param damage_states: the damage states considered in this distribution.
    :type damage_states: list of strings, for example:
        ["no_damage", "slight", "moderate", "extensive", "complete"]
    """

    def __init__(self, path, damage_states):
        self.path = path
        self.damage_states = damage_states
        self.root = None

    def serialize(self, total_dist_data):
        """
        Serialize the entire distribution.

        :param total_dist_data: the distribution to be written.
        :type total_dist_data: list of
            :py:class:`openquake.db.models.DmgDistTotalData` instances.
        :raises: `RuntimeError` in case of list empty or `None`.
        """

        if total_dist_data is None or not len(total_dist_data):
            raise RuntimeError(
                "empty damage distributions are not supported by the schema.")

        with open(self.path, "w") as fh:
            self.root, dmg_dist_el = _create_root_elems(
                self.damage_states, "totalDmgDist")

            for tdata in total_dist_data:

                _create_damage_elem(dmg_dist_el, tdata.dmg_state.dmg_state,
                                    tdata.mean, tdata.stddev)

            fh.write(
                etree.tostring(self.root, pretty_print=True,
                               xml_declaration=True, encoding="UTF-8"))


def _create_root_elems(damage_states, distribution):
    """
    Create the <nrml /> and <dmgDistPer{Taxonomy,Asset} /> elements.
    """

    root = etree.Element("nrml", nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

    dmg_dist_el = etree.SubElement(root, distribution)
    dmg_states = etree.SubElement(dmg_dist_el, "damageStates")
    dmg_states.text = " ".join(damage_states)

    return root, dmg_dist_el


def _create_damage_elem(dd_node, dmg_state, mean, stddev):
    """
    Create the <damage /> element.
    """
    ds_node = etree.SubElement(dd_node, "damage")
    ds_node.set("ds", dmg_state)
    ds_node.set("mean", str(mean))
    ds_node.set("stddev", str(stddev))


def _create_asset_elem(dd_node_el, asset_ref):
    """
    Create the <asset /> element.
    """
    asset_node_el = etree.SubElement(dd_node_el, "asset")
    asset_node_el.set("assetRef", asset_ref)
    return asset_node_el


def _append_location(element, location):
    """
    Append the geographical location to the given element.
    """
    gml_ns = openquake.nrmllib.SERIALIZE_NS_MAP["gml"]
    gml_point = etree.SubElement(element, "{%s}Point" % gml_ns)
    gml_pos = etree.SubElement(gml_point, "{%s}pos" % gml_ns)
    gml_pos.text = "%s %s" % (location.x, location.y)


def validate_hazard_metadata(gsim_tree_path=None, source_model_tree_path=None,
                             statistics=None, quantile_value=None):
    """
    Validate the hazard input metadata.
    """

    if statistics is not None:
        _check_statistics_or_logic_tree(source_model_tree_path, gsim_tree_path)
        _check_statistics_metadata(statistics, quantile_value)
    else:
        _check_logic_tree_metadata(source_model_tree_path, gsim_tree_path)


def _check_statistics_metadata(statistics, quantile_value):
    """
    `statistics` must be in ("quantile", "mean") and `quantile_value`
    must be specified when `statistics` == "quantile". If `statistics` ==
    "mean", `quantile_value` must be empty.
    """

    if statistics not in ("quantile", "mean"):
        raise ValueError("`statistics` must be in ('quantile', 'mean').")

    if statistics == "quantile" and quantile_value is None:
        raise ValueError("When `statistics` == 'quantile', "
                         "`quantile_value` must also be specified.")

    if statistics == "mean" and quantile_value is not None:
        raise ValueError("When `statistics` == 'mean', "
                         "`quantile_value` must not be specified.")


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
        raise ValueError(
            "You must choose `statistics` or "
            "(`source_model_tree_path`, `gsim_tree_path`), not both.")


def _assert_valid_input(data):
    """
    We don't support empty outputs, so there must be at least one
    element in the collection.
    """

    if not data or len(data) == 0:
        raise ValueError("At least one element must be present, "
                         "an empty document is not supported by the schema.")
