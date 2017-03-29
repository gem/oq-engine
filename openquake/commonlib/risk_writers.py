# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module containing writers for risk output artifacts.
"""
import json
import operator
import collections
import numpy

from xml.etree import ElementTree as et

from openquake.hazardlib.nrml import SERIALIZE_NS_MAP
from openquake.baselib.general import groupby, writetmp
from openquake.baselib.node import Node
from openquake.hazardlib import nrml
from openquake.commonlib.writers import FIVEDIGITS


def notnan(value):
    """True if the value is not numpy.nan"""
    return not numpy.isnan(value)

DmgState = collections.namedtuple("DmgState", 'dmg_state lsi')

DmgDistPerTaxonomy = collections.namedtuple(
    'DmgDistPerTaxonomy', 'taxonomy dmg_state mean stddev')

DmgDistPerAsset = collections.namedtuple(
    'DmgDistPerAsset', 'exposure_data dmg_state mean stddev')

DmgDistTotal = collections.namedtuple(
    'DmgDistTotal', 'dmg_state mean stddev')

ExposureData = collections.namedtuple('ExposureData', 'asset_ref site')


class Site(object):
    """
    A small wrapper over a lon-lat pair (x, y). It has a .wkt attribute
    and an ordering. It is used for consistency with the export routines.
    """
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.wkt = 'POINT(%s %s)' % (x, y)

    def __lt__(self, other):
        return (self.x, self.y) < (other.x, other.y)

    def __eq__(self, other):
        # without this the groupby in the ScenarioDamageWriter would not work
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))


class LossCurveXMLWriter(object):
    """
    :param dest:
        File path (including filename) or file-like object for results to be
        saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param str loss_type:
        Loss type used in risk model input for the calculation producing this
        output (examples: structural, non-structural, business-interruption,
        occupants)
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

    def __init__(self, dest, investigation_time, loss_type,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None,
                 insured=False, poe=None, risk_investigation_time=None):

        validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                 statistics, quantile_value)

        self._unit = unit
        self._dest = dest
        self._statistics = statistics
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._risk_investigation_time = (
            risk_investigation_time or investigation_time)
        self._loss_type = loss_type
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
            * define an attribute `average_loss`, which is a float
              describing the average loss associated to the loss curve
            * define an attribute `stddev_loss`, which is a float
              describing the standard deviation of losses if the loss curve
              has been computed with an event based approach. Otherwise,
              it is None

            All attributes must be defined, except for `loss_ratios` that
            can be `None` since it is optional in the schema.

            Also, `poes`, `losses` and `loss_ratios` values must be indexed
            coherently, i.e.: the loss (and optionally loss ratio) at index
            zero is related to the probability of exceedance at the same
            index.
        """

        _assert_valid_input(data)

        with open(self._dest, 'wb') as output:
            root = et.Element("nrml")

            for curve in data:
                if self._loss_curves is None:
                    self._create_loss_curves_elem(root)

                loss_curve = et.SubElement(self._loss_curves, "lossCurve")

                _append_location(loss_curve, curve.location)
                loss_curve.set("assetRef", curve.asset_ref)

                poes = et.SubElement(loss_curve, "poEs")
                poes.text = " ".join(FIVEDIGITS % p for p in curve.poes
                                     if notnan(p))

                losses = et.SubElement(loss_curve, "losses")
                losses.text = " ".join(FIVEDIGITS % p for p in curve.losses
                                       if notnan(p))

                if curve.loss_ratios is not None:
                    loss_ratios = et.SubElement(loss_curve, "lossRatios")

                    loss_ratios.text = " ".join(
                        ['%.3f' % p for p in curve.loss_ratios if notnan(p)])

                losses = et.SubElement(loss_curve, "averageLoss")
                losses.text = FIVEDIGITS % curve.average_loss

                if curve.stddev_loss is not None:
                    losses = et.SubElement(loss_curve, "stdDevLoss")
                    losses.text = FIVEDIGITS % curve.stddev_loss

            nrml.write(list(root), output)

    def _create_loss_curves_elem(self, root):
        """
        Create the <lossCurves /> element with associated attributes.
        """

        self._loss_curves = et.SubElement(root, "lossCurves")

        if self._insured:
            self._loss_curves.set("insured", str(self._insured))

        self._loss_curves.set("investigationTime",
                              str(self._investigation_time))

        self._loss_curves.set("riskInvestigationTime",
                              str(self._risk_investigation_time))

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

        self._loss_curves.set("lossType", self._loss_type)


class AggregateLossCurveXMLWriter(object):
    """
    :param dest:
        File path (including filename) or file-like objects for results to be
        saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param str loss_type:
        Loss type used in risk model input for the calculation producing this
        output (examples: structural, non-structural, business-interruption,
        occupants)
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

    def __init__(self, dest, investigation_time, loss_type,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None, poe=None,
                 risk_investigation_time=None):

        validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                 statistics, quantile_value)

        self._unit = unit
        self._dest = dest
        self._statistics = statistics
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._risk_investigation_time = (
            risk_investigation_time or investigation_time)
        self._loss_type = loss_type
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
            * define an attribute `average_loss`, which is a float
              describing the average loss associated to the loss curve
            * define an attribute `stddev_loss`, which is a float
              describing the standard deviation of losses if the loss curve
              has been computed with an event based approach. Otherwise, it
              is None

            Also, `poes`, `losses` values must be indexed coherently,
            i.e.: the loss at index zero is related to the probability
            of exceedance at the same index.
        """

        if data is None:
            raise ValueError("You can not serialize an empty document")

        with open(self._dest, 'wb') as output:
            root = et.Element("nrml")

            aggregate_loss_curve = et.SubElement(root, "aggregateLossCurve")

            aggregate_loss_curve.set("investigationTime",
                                     str(self._investigation_time))

            aggregate_loss_curve.set("riskInvestigationTime",
                                     str(self._risk_investigation_time))

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

            aggregate_loss_curve.set("lossType", self._loss_type)

            poes = et.SubElement(aggregate_loss_curve, "poEs")
            poes.text = " ".join(FIVEDIGITS % p for p in data.poes)

            losses = et.SubElement(aggregate_loss_curve, "losses")
            losses.text = " ".join([FIVEDIGITS % p for p in data.losses])

            losses = et.SubElement(aggregate_loss_curve, "averageLoss")
            losses.text = FIVEDIGITS % data.average_loss

            if data.stddev_loss is not None:
                losses = et.SubElement(aggregate_loss_curve, "stdDevLoss")
                losses.text = FIVEDIGITS % data.stddev_loss

            nrml.write(list(root), output)


class LossMapWriter(object):
    """
    Base class for serializing loss maps produced with the classical and
    probabilistic calculators.

    Subclasses must implement the :meth:`serialize` method, which defines the
    format of the output.

    :param dest:
        File path (including filename) or file-like object for results to be
        saved to.
    :param float investigation_time:
        Investigation time (also known as Time Span) defined in
        the calculation which produced these results (in years).
    :param float poe:
        Probability of exceedance used to interpolate the losses
        producing this loss map.
    :param str loss_type:
        Loss type used in risk model input for the calculation producing this
        output (examples: structural, non-structural, business-interruption,
        occupants)
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

    def __init__(self, dest, investigation_time, poe, loss_type,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None,
                 loss_category=None, risk_investigation_time=None):

        # Relaxed constraint for scenario risk calculator
        # which doesn't have hazard metadata.
        if gsim_tree_path and source_model_tree_path:
            validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                     statistics, quantile_value)

        self._poe = poe
        self._loss_type = loss_type
        self._unit = unit
        self._dest = dest
        self._statistics = statistics
        self._loss_category = loss_category
        self._quantile_value = quantile_value
        self._gsim_tree_path = gsim_tree_path
        self._investigation_time = investigation_time
        self._risk_investigation_time = (
            risk_investigation_time or investigation_time)
        self._source_model_tree_path = source_model_tree_path

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
        raise NotImplementedError('LossMapWriter.serialize')


class LossMapXMLWriter(LossMapWriter):
    """
    NRML/XML implementation of a :class:`LossMapWriter`.

    See :class:`LossMapWriter` for information about constructor parameters.
    """

    def serialize(self, data):
        """
        Serialize loss map data to XML.

        See :meth:`LossMapWriter.serialize` for expected input.
        """
        _assert_valid_input(data)

        with open(self._dest, 'wb') as output:
            root = et.Element("nrml")

            loss_map_el = self._create_loss_map_elem(root)

            current_location = None
            current_node = None
            for loss in data:

                if (current_location is None or
                        loss.location.wkt != current_location):
                    current_node = et.SubElement(loss_map_el, "node")
                    current_location = _append_location(
                        current_node, loss.location)

                loss_elem = et.SubElement(current_node, "loss")
                loss_elem.set("assetRef", str(loss.asset_ref))

                if loss.std_dev is not None:
                    loss_elem.set("mean", FIVEDIGITS % loss.value)
                    loss_elem.set("stdDev", FIVEDIGITS % loss.std_dev)
                else:
                    loss_elem.set("value", FIVEDIGITS % loss.value)

            nrml.write(list(root), output)

    def _create_loss_map_elem(self, root):
        """
        Create the <lossMap /> element with associated attributes.
        """

        loss_map = et.SubElement(root, "lossMap")
        loss_map.set("investigationTime", str(self._investigation_time))
        loss_map.set("riskInvestigationTime",
                     str(self._risk_investigation_time))
        loss_map.set("poE", str(self._poe))

        if self._source_model_tree_path is not None:
            loss_map.set("sourceModelTreePath",
                         str(self._source_model_tree_path))

        if self._gsim_tree_path is not None:
            loss_map.set("gsimTreePath", str(self._gsim_tree_path))

        if self._statistics is not None:
            loss_map.set("statistics", str(self._statistics))

        if self._quantile_value is not None:
            loss_map.set("quantileValue", str(self._quantile_value))

        if self._loss_category is not None:
            loss_map.set("lossCategory", str(self._loss_category))

        if self._unit is not None:
            loss_map.set("unit", str(self._unit))

        loss_map.set("lossType", self._loss_type)

        return loss_map


class LossMapGeoJSONWriter(LossMapWriter):
    """
    GeoJSON implementation of a :class:`LossMapWriter`. Serializes loss maps as
    FeatureCollection artifacts with additional loss map metadata.

    See :class:`LossMapWriter` for information about constructor parameters.
    """

    def serialize(self, data):
        """
        Serialize loss map data to a file as a GeoJSON feature collection.

        See :meth:`LossMapWriter.serialize` for expected input.
        """
        _assert_valid_input(data)

        feature_coll = {
            'type': 'FeatureCollection',
            'features': [],
            'oqtype': 'LossMap',
            # TODO: oqnrmlversion has little meaning now
            'oqnrmlversion': '0.4',
            'oqmetadata': self._create_oqmetadata(),
        }

        for loss in data:
            loc = loss.location

            loss_node = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(loc.x), float(loc.y)]
                },
                'properties': {'loss': float(loss.value),
                               'asset_ref': loss.asset_ref},
            }
            feature_coll['features'].append(loss_node)

            if loss.std_dev is not None:
                loss_node['properties']['std_dev'] = float(loss.std_dev)

        with open(self._dest, 'w') as fh:
            json.dump(feature_coll, fh, sort_keys=True, indent=4,
                      separators=(',', ': '))

    def _create_oqmetadata(self):
        """
        Helper method to create the `oqmetadata` dictionary.
        """
        meta = dict()
        meta['investigationTime'] = str(self._investigation_time)
        meta['poE'] = str(self._poe)

        if self._source_model_tree_path is not None:
            meta['sourceModelTreePath'] = str(self._source_model_tree_path)

        if self._gsim_tree_path is not None:
            meta['gsimTreePath'] = str(self._gsim_tree_path)

        if self._statistics is not None:
            meta['statistics'] = str(self._statistics)

        if self._quantile_value is not None:
            meta['quantileValue'] = str(self._quantile_value)

        if self._loss_category is not None:
            meta['lossCategory'] = str(self._loss_category)

        if self._unit is not None:
            meta['unit'] = str(self._unit)

        meta['lossType'] = self._loss_type

        return meta


class LossFractionsWriter(object):
    """
    Serializer for loss fractions produced with the classical and
    event based calculators.

    :attr dest:
        Full path including file name or file-like object where the results
        will be saved into.
    :attr str variable:
        The variable used for disaggregation
    :attr str loss_unit:
        Attribute describing how the value of the assets has been measured.
    :param str loss_type:
        Loss type used in risk model input for the calculation producing this
        output (examples: structural, non-structural, business-interruption,
        occupants)
    :attr str loss_category:
        Attribute describing the category (economic, population, buildings,
        etc..) of the losses producing this loss map.
    :attr object hazard_metadata:
       metadata of hazard outputs used by risk calculation. It has the
        attributes: investigation_time, source_model_tree_path, gsim_tree_path,
        statistics, quantile_value
    :attr float poe:
        Probability of exceedance used to interpolate the losses
        producing this fraction map.
    """

    def __init__(self, dest, variable, loss_unit, loss_type,
                 loss_category, hazard_metadata, poe=None):
        self.dest = dest
        self.variable = variable
        self.loss_unit = loss_unit
        self.loss_type = loss_type
        self.loss_category = loss_category
        self.hazard_metadata = hm = hazard_metadata
        self.poe = poe

        validate_hazard_metadata(
            hm.gsim_path,
            hm.sm_path,
            hm.statistics,
            hm.quantile)

    def serialize(self, total_fractions, locations_fractions):
        """
        Actually serialize the fractions.

        :param dict total_fractions:
            maps a value of `variable` with a tuple representing the absolute
            losses and the fraction
        :param dict locations_fractions:
            a dictionary mapping a tuple (longitude, latitude) to
            bins. Each bin is a dictionary with the same structure of
            `total_fractions`.
        """

        def write_bins(parent, bin_data):
            for value, (absolute_loss, fraction) in bin_data.items():
                bin_element = et.SubElement(parent, "bin")
                bin_element.set("value", str(value))
                bin_element.set("absoluteLoss", FIVEDIGITS % absolute_loss)
                bin_element.set("fraction", FIVEDIGITS % fraction)

        with open(self.dest, 'wb') as output:
            root = et.Element("nrml")

            # container element
            container = et.SubElement(root, "lossFraction")
            container.set("investigationTime",
                          "%.2f" % self.hazard_metadata.investigation_time)

            if self.poe is not None:
                container.set("poE", "%.4f" % self.poe)

            container.set(
                "sourceModelTreePath", self.hazard_metadata.sm_path or "")
            container.set("gsimTreePath", self.hazard_metadata.gsim_path or "")

            if self.hazard_metadata.statistics is not None:
                container.set("statistics", self.hazard_metadata.statistics)

            if self.hazard_metadata.quantile is not None:
                container.set(
                    "quantileValue", "%.4f" % self.hazard_metadata.quantile)
            container.set("lossCategory", self.loss_category)
            container.set("unit", self.loss_unit)
            container.set("variable", self.variable)
            container.set("lossType", self.loss_type)

            # total fractions
            total = et.SubElement(container, "total")
            write_bins(total, total_fractions)

            # map
            map_element = et.SubElement(container, "map")

            for lon_lat, bin_data in locations_fractions.items():
                node_element = et.SubElement(map_element, "node")
                node_element.set("lon", str(lon_lat[0]))
                node_element.set("lat", str(lon_lat[1]))
                write_bins(node_element, bin_data)

            nrml.write(list(root), output)


class BCRMapXMLWriter(object):
    """
    Serializer for bcr (benefit cost ratio) maps produced with the classical
    and probabilistic calculators.

    :param dest:
        File path (including filename) or file-like object for results to be
        saved to.
    :param float interest_rate:
        The inflation discount rate.
    :param float asset_life_expectancy:
        The period of time in which the building is expected to be used.
    :param str loss_type:
        Loss type used in risk model input for the calculation producing this
        output (examples: structural, non-structural, business-interruption,
        occupants)
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

    def __init__(self, path, interest_rate, asset_life_expectancy, loss_type,
                 source_model_tree_path=None, gsim_tree_path=None,
                 statistics=None, quantile_value=None, unit=None,
                 loss_category=None, poe=None):

        validate_hazard_metadata(gsim_tree_path, source_model_tree_path,
                                 statistics, quantile_value)

        self._unit = unit
        self._path = path
        self._statistics = statistics
        self._interest_rate = interest_rate
        self._loss_type = loss_type
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

        with open(self._path, "wb") as output:
            root = et.Element("nrml")

            for bcr in data:
                if self._bcr_map is None:
                    self._create_bcr_map_elem(root)

                bcr_node = self._bcr_nodes.get(bcr.location.wkt)

                if bcr_node is None:
                    bcr_node = et.SubElement(self._bcr_map, "node")
                    _append_location(bcr_node, bcr.location)
                    self._bcr_nodes[bcr.location.wkt] = bcr_node

                bcr_elem = et.SubElement(bcr_node, "bcr")
                bcr_elem.set("assetRef", str(bcr.asset_ref))
                bcr_elem.set("ratio", str(bcr.bcr))

                bcr_elem.set("aalOrig", str(
                    bcr.average_annual_loss_original))

                bcr_elem.set("aalRetr", str(
                    bcr.average_annual_loss_retrofitted))

            nrml.write(list(root), output)

    def _create_bcr_map_elem(self, root):
        """
        Create the <bcrMap /> element with associated attributes.
        """

        self._bcr_map = et.SubElement(root, "bcrMap")

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

        self._bcr_map.set("lossType", self._loss_type)


def _append_location(element, location):
    """
    Append the geographical location to the given element.
    """
    gml_ns = SERIALIZE_NS_MAP["gml"]
    gml_point = et.SubElement(element, "{%s}Point" % gml_ns)
    gml_pos = et.SubElement(gml_point, "{%s}pos" % gml_ns)
    gml_pos.text = "%s %s" % (location.x, location.y)

    return location.wkt


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


class DamageWriter(object):
    """
    A class to convert scenario_damage outputs into nodes and then XML.

    :param damage_states:
        a sequence of DamageState objects with attributes .dmg_state and .lsi
    """
    def __init__(self, damage_states):
        self.damage_states = damage_states
        self.dmg_states = Node(
            'damageStates',
            text=' '.join(ds.dmg_state for ds in damage_states))

    def damage_nodes(self, means, stddevs):
        """
        :param means: array of means, one per damage state
        :param stddevs: array of stddevs, one per damage state
        :returns: a list of `damage` nodes
        """
        nodes = []
        for dmg_state, mean, stddev in zip(self.damage_states, means, stddevs):
            nodes.append(
                Node('damage', dict(ds=dmg_state.dmg_state,
                                    mean=mean, stddev=stddev)))
        return nodes

    def point_node(self, loc):
        """
        :param loc: a location object with attributes x and y
        :returns: a `gml:Point` node
        """
        return Node('gml:Point',
                    nodes=[Node('gml:pos', text='%.5f %.5f' % (loc.x, loc.y))])

    def asset_node(self, asset_ref, means, stddevs):
        """
        :param asset_ref: asset reference string
        :param means: array of means, one per damage state
        :param stddevs: array of stddevs, one per damage state
        :returns: an `asset` node
        """
        return Node('asset', dict(assetRef=asset_ref),
                    nodes=self.damage_nodes(means, stddevs))

    def cm_node(self, loc, asset_refs, means, stddevs):
        """
        :param loc: a location object with attributes x and y
        :param asset_refs: asset reference strings
        :param means: array of means, one per asset
        :param stddevs: array of stddevs, one per asset
        :returns: a `CMNode` node
        """
        cm = Node('CMNode', nodes=[self.point_node(loc)])
        for asset_ref, mean, stddev in zip(asset_refs, means, stddevs):
            cf = Node('cf', dict(assetRef=asset_ref, mean=mean, stdDev=stddev))
            cm.append(cf)
        return cm

    def dd_node_taxo(self, taxonomy, means, stddevs):
        """
        :param taxonomy: taxonomy string
        :param means: array of means, one per damage state
        :param stddevs: array of stddevs, one per damage state
        :returns: a `DDNode` node
        """
        taxonomy = Node('taxonomy', text=taxonomy)
        dd = Node('DDNode', nodes=[taxonomy] +
                  self.damage_nodes(means, stddevs))
        return dd

    def dmg_dist_per_asset_node(self, data):
        """
        :param data: a sequence of records with attributes .exposure_data,
                     .mean and .stddev
        :returns: a `dmgDistPerAsset` node
        """
        node = Node('dmgDistPerAsset', nodes=[self.dmg_states])
        data_by_location = groupby(data, lambda r: r.exposure_data.site)
        for loc in data_by_location:
            dd = Node('DDNode', nodes=[self.point_node(loc)])
            data_by_asset = groupby(
                data_by_location[loc],
                lambda r: r.exposure_data.asset_ref,
                lambda rows: [(r.mean, r.stddev) for r in rows])
            for asset_ref, data in data_by_asset.items():
                means, stddevs = zip(*data)
                dd.append(self.asset_node(asset_ref, means, stddevs))
            node.append(dd)
        return node

    def dmg_dist_per_taxonomy_node(self, data):
        """
        :param data: a sequence of records with attributes .taxonomy,
                     .mean and .stddev
        :returns: a `dmgDistPerTaxonomy` node
        """
        node = Node('dmgDistPerTaxonomy', nodes=[self.dmg_states])
        data_by_taxo = groupby(data, operator.attrgetter('taxonomy'))
        for taxonomy in data_by_taxo:
            means = [row.mean for row in data_by_taxo[taxonomy]]
            stddevs = [row.stddev for row in data_by_taxo[taxonomy]]
            node.append(self.dd_node_taxo(taxonomy, means, stddevs))
        return node

    def dmg_dist_total_node(self, data):
        """
        :param data: a sequence of records with attributes .dmg_state,
                     .mean and .stddev
        :returns: a `totalDmgDist` node
        """
        total = Node('totalDmgDist', nodes=[self.dmg_states])
        for row in sorted(data, key=lambda r: r.dmg_state.lsi):
            damage = Node('damage',
                          dict(ds=row.dmg_state.dmg_state, mean=row.mean,
                               stddev=row.stddev))
            total.append(damage)
        return total

    def collapse_map_node(self, data):
        """
        :param data: a sequence of records with attributes .exposure_data,
                     .mean and .stddev
        :returns: a `dmgDistPerAsset` node
        """
        node = Node('collapseMap')
        data_by_location = groupby(data, lambda r: r.exposure_data.site)
        for loc in data_by_location:
            asset_refs = []
            means = []
            stddevs = []
            for row in sorted(data_by_location[loc],
                              key=lambda r: r.exposure_data.asset_ref):
                asset_refs.append(row.exposure_data.asset_ref)
                means.append(row.mean)
                stddevs.append(row.stddev)
            node.append(self.cm_node(loc, asset_refs, means, stddevs))
        return node

    def to_nrml(self, key, data, fname=None, fmt=FIVEDIGITS):
        """
        :param key:
         `dmg_dist_per_asset|dmg_dist_per_taxonomy|dmg_dist_total|collapse_map`
        :param data: sequence of rows to serialize
        :fname: the path name of the output file; if None, build a name
        :returns: path name of the saved file
        """
        fname = fname or writetmp()
        node = getattr(self, key + '_node')(data)
        with open(fname, 'wb') as out:
            nrml.write([node], out, fmt)
        return fname
