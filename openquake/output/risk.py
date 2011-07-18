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

"""
NRML serialization of risk-related data sets.
- loss ratio curves
- loss curves
- loss map
"""
import os

from lxml import etree

import sqlalchemy

from db.alchemy.models import OqJob, Output
from db.alchemy.models import LossMap, LossMapData
from db.alchemy.models import LossAssetData, LossCurveData

from openquake import logs
from openquake import shapes
from openquake import xml

from openquake.output import nrml
from openquake.xml import NRML_NS, GML_NS

LOGGER = logs.RISK_LOG

NAMESPACES = {'gml': GML_NS, 'nrml': NRML_NS}


class BaseXMLWriter(nrml.TreeNRMLWriter):
    """
    This is the base class which prepares the XML document (for risk) to be
    customized in another class.
    """
    container_tag = None

    def __init__(self, path):
        super(BaseXMLWriter, self).__init__(path)

        self.result_el = None

    def write(self, point, values):
        if isinstance(point, shapes.GridPoint):
            point = point.site
        asset_object = values[1]
        if self.root_node is None:
            # nrml:nrml, needs gml:id
            self._create_root_element()

            if 'nrml_id' in asset_object:
                nrml.set_gml_id(self.root_node, str(asset_object['nrml_id']))
            else:
                nrml.set_gml_id(self.root_node, nrml.NRML_DEFAULT_ID)

            # nrml:riskResult, needs gml:id
            result_el = etree.SubElement(self.root_node, xml.RISK_RESULT_TAG)
            if 'riskres_id' in asset_object:
                nrml.set_gml_id(result_el, str(asset_object['riskres_id']))
            else:
                nrml.set_gml_id(result_el, nrml.RISKRESULT_DEFAULT_ID)

            etree.SubElement(result_el, xml.NRML_CONFIG_TAG)

            self.result_el = result_el


class LossMapXMLWriter(nrml.TreeNRMLWriter):
    """
    This class serializes loss maps to NRML. The primary contents of a loss map
    include the mean and standard deviation loss values for each asset in a
    defined region over many computed realizations.
    """

    DEFAULT_METADATA = {
        'nrmlID': 'undefined', 'riskResultID': 'undefined',
        'lossMapID': 'undefined', 'endBranchLabel': 'undefined',
        'lossCategory': 'undefined', 'unit': 'undefined'}

    def __init__(self, path):
        nrml.TreeNRMLWriter.__init__(self, path)
        self.lmnode_counter = 0

        # root <nrml> element:
        self._create_root_element()

        # <riskResult>
        self.risk_result_node = etree.SubElement(
            self.root_node, xml.RISK_RESULT_TAG)

        # <lossMap>
        self.loss_map_node = etree.SubElement(
            self.risk_result_node, xml.RISK_LOSS_MAP_CONTAINER_TAG)

    def serialize(self, data):
        """
        Overrides the base `serialize` method to handle writing metadata for
        the `nrml`, `riskResult`, and `lossMap` elements (in addition to the
        site/asset/loss data).

        :param data: List of data to serialize to the output file.

            Each element should consist of a tuple of (site, (loss, asset))
            information.
            See :py:meth:`write` for details.

            Optionally, the first element may be a dict containing metadata
            about the loss map.
            For example::

                [{'nrmlID': 'n1', 'riskResultID': 'rr1', 'lossMapID': 'lm1',
                  'endBranchLabel': 'vf1', 'lossCategory': 'economic_loss',
                  'unit': 'EUR'},
                  ...
                  <remaining data>]

            If no metadata is specified, defaults will be used.
        """
        if isinstance(data[0], dict):
            self.write_metadata(data[0])
            data = data[1:]
        else:
            self.write_metadata(self.DEFAULT_METADATA)

        nrml.TreeNRMLWriter.serialize(self, data)

    def write_metadata(self, metadata):
        """
        Write gml:ids and other meta data for `nrml`, `riskResult`, and
        `lossMap` XML elements.

        :param metadata: A dict containing metadata about the loss map.
            For example::

                {'nrmlID': 'n1', 'riskResultID': 'rr1', 'lossMapID': 'lm1',
                 'endBranchLabel': 'vf1', 'lossCategory': 'economic_loss',
                 'unit': 'EUR'}

            If any of these items are not defined in the dict, default values
            will be used.

        :type metadata: dict
        """
        # set gml:id attributes:
        for node, key in (
            (self.root_node, 'nrmlID'),
            (self.risk_result_node, 'riskResultID'),
            (self.loss_map_node, 'lossMapID')):
            nrml.set_gml_id(
                node, metadata.get(key, self.DEFAULT_METADATA[key]))

        # set the rest of the <lossMap> attributes
        for key in ('endBranchLabel', 'lossCategory', 'unit'):
            self.loss_map_node.set(
                key, metadata.get(key, self.DEFAULT_METADATA[key]))

    def write(self, site, values):
        """Writes an asset element with loss map ratio information.
        This method assumes that `riskResult` and `lossMap` element
        data has already been written.

        :param site: the region location of the data being written
        :type site: :py:class:`openquake.shapes.Site`

        :param values: contains a list of pairs in the form
            (loss dict, asset dict) with all the data
            to be written related to the given site
        :type values: tuple with the following members
            :py:class:`dict` (loss dict) with the following keys:
                ***mean_loss*** - the Mean Loss for a certain Node/Site
                ***stddev_loss*** - the Standard Deviation for a certain
                    Node/Site

            :py:class:`dict` (asset dict)
                ***assetID*** - the assetID
        """
        def new_loss_node(lmnode_el, loss_dict, asset_dict):
            """
            Create a new asset loss node under a pre-existing parent LMNode.
            """
            loss_el = etree.SubElement(lmnode_el,
                                    xml.RISK_LOSS_MAP_LOSS_CONTAINER_TAG)

            loss_el.set(xml.RISK_LOSS_MAP_ASSET_REF_ATTR,
                        str(asset_dict['assetID']))
            mean_loss = etree.SubElement(
                loss_el, xml.RISK_LOSS_MAP_MEAN_LOSS_TAG)
            mean_loss.text = "%s" % loss_dict['mean_loss']
            stddev = etree.SubElement(loss_el,
                            xml.RISK_LOSS_MAP_STANDARD_DEVIATION_TAG)
            stddev.text = "%s" % loss_dict['stddev_loss']

        # Generate an id for the new LMNode
        # Note: ids are created start at '1'
        self.lmnode_counter += 1
        lmnode_id = "lmn_%i" % self.lmnode_counter

        # Create the new LMNode
        lmnode_el = etree.SubElement(self.loss_map_node, xml.RISK_LMNODE_TAG)

        # Set the gml:id
        nrml.set_gml_id(lmnode_el, lmnode_id)

        # We also need Site, gml:Point, and gml:pos nodes
        # for the new LMNode.
        # Each one (site, point, pos) is the parent of the next.
        site_el = etree.SubElement(lmnode_el, xml.RISK_SITE_TAG)

        point_el = etree.SubElement(site_el, xml.GML_POINT_TAG)
        point_el.set(xml.GML_SRS_ATTR_NAME, xml.GML_SRS_EPSG_4326)

        pos_el = etree.SubElement(point_el, xml.GML_POS_TAG)
        pos_el.text = "%s %s" % (site.longitude, site.latitude)

        # now add the loss nodes as a child of the LMNode
        # we have loss data in first position, asset data in second position
        # ({'stddev_loss': 100, 'mean_loss': 0}, {'assetID': 'a1711'})
        for value in values:
            new_loss_node(lmnode_el, value[0], value[1])

    def _get_site_elem_for_site(self, site):
        """
        Searches the current xml document for a Site node matching the input
        Site object.

        :param site: Site object to match with Site node in the xml document
        :type site: :py:class:`shapes.Site` object

        :returns: matching Site node (of type :py:class:`lxml.etree._Element`,
            or None if no match is found
        """
        site_nodes = self.loss_map_node.xpath(
            './nrml:LMNode/nrml:site', namespaces=NAMESPACES)
        for node in site_nodes:
            if xml.element_equal_to_site(node, site):
                return node
        return None


class OutputDBWriter(object):
    """
    Abstact class implementing the "serialize" interface to output an iterable
    to the database.

    Subclasses must implement get_output_type() and insert_datum().
    """
    def __init__(self, session, nrml_path, oq_job_id):
        self.nrml_path = nrml_path
        self.oq_job_id = oq_job_id
        self.session = session
        job = self.session.query(OqJob).filter(
            OqJob.id == self.oq_job_id).one()
        self.output = Output(owner=job.owner, oq_job=job,
                             display_name=os.path.basename(self.nrml_path),
                             output_type=self.get_output_type(),
                             db_backed=True)

    def get_output_type(self):
        """
        The type of the output record as a string (e.g. 'loss_curve')
        """
        raise NotImplementedError()

    def insert_datum(self, key, values):
        """
        Called for each item of the iterable during serialize.
        """
        raise NotImplementedError()

    def serialize(self, iterable):
        """
        Implementation of the "serialize" interface.

        An Output record with type get_output_type() will be created, then
        each item of the iterable will be serialized in turn to the database.
        """
        LOGGER.info("> serialize")
        LOGGER.info("serializing %s points" % len(iterable))

        self.session.add(self.output)
        LOGGER.info("output = '%s'" % self.output)

        for key, values in iterable:
            self.insert_datum(key, values)

        self.session.commit()

        LOGGER.info("serialized %s points" % len(iterable))
        LOGGER.info("< serialize")


class LossMapDBWriter(OutputDBWriter):
    """
    Serialize to the database deterministic and non deterministic loss maps.

    Deterministic loss maps, generated by the deterministic event-based
    calculators, store, per asset, the mean and standard deviation of the loss.

    Non deterministic loss maps, generated by classical psha-based or
    probabilistic based calculators, store a probabilty of exceedance and, per
    asset, a loss.
    """

    def __init__(self, *args, **kwargs):
        super(LossMapDBWriter, self).__init__(*args, **kwargs)

        self.metadata = None

    def get_output_type(self):
        """
        The type of the output record as a string
        """
        return 'loss_map'

    def serialize(self, iterable):
        if isinstance(iterable[0], dict):
            self._insert_metadata(iterable[0])
            iterable = iterable[1:]
        else:
            self._insert_metadata({})

        super(LossMapDBWriter, self).serialize(iterable)

    def insert_datum(self, site, values):
        """
        :param site: the region location of the data being written
        :type site: :py:class:`openquake.shapes.Site`

        :param values: contains a list of pairs in the form
            (loss dict, asset dict) with all the data
            to be written related to the given site
        :type values: tuple with the following members
            :py:class:`dict` (loss dict) with the following keys:
                ***mean_loss*** - the Mean Loss for a certain Node/Site
                ***stddev_loss*** - the Standard Deviation for a certain
                    Node/Site

            :py:class:`dict` (asset dict)
                ***assetID*** - the assetID
        """
        for loss, asset in values:
            kwargs = {
                'loss_map': self.metadata,
                'asset_ref': asset['assetID'],
                'location': "POINT(%s %s)" % (site.longitude, site.latitude),
            }
            if self.metadata.deterministic:
                kwargs.update({
                    'value': loss.get('mean_loss'),
                    'std_dev': loss.get('stddev_loss'),
                })
            else:
                kwargs.update({
                    'value': loss.get('value'),
                    'std_dev': 0.0,
                })
            data = LossMapData(**kwargs)
            self.session.add(data)

    def _insert_metadata(self, metadata):
        """
        Insert a record holding the metadata of a loss map.
        """
        kwargs = {
            'output': self.output,
        }

        for key, metadata_key in (('loss_map_ref', 'lossMapID'),
                                  ('end_branch_label', 'endBranchLabel'),
                                  ('category', 'lossCategory'),
                                  ('unit', 'unit'),
                                  ('deterministic', 'deterministic'),
                                  # poe is for non deterministic loss maps
                                  # enforced by a SQL constraint
                                  ('poe', 'poe')):
            kwargs[key] = metadata.get(metadata_key)

        self.metadata = LossMap(**kwargs)
        self.session.add(self.metadata)


class CurveXMLWriter(BaseXMLWriter):
    """This class serializes a set of loss or loss ratio curves to NRML.
    Since the curves have to be collected under several different asset
    objects, we have to build the whole tree before serializing
    (uses base class BaseXMLWriter).
    """

    # these tag names have to be redefined in the derived classes
    container_tag = None
    curves_tag = None
    curve_tag = None
    abscissa_tag = None

    CONTAINER_DEFAULT_ID = 'c1'

    def __init__(self, path):
        super(CurveXMLWriter, self).__init__(path)

        self.curve_list_el = None
        self.assets_per_id = {}

    def write(self, point, values):
        """Writes an asset element with loss map ratio information.

        :param point: the point of the grid we want to compute
        :type point: :py:class:`openquake.shapes.Site`,
                     :py:class:`openquake.shapes.GridPoint`

        :param values: is a pair of (loss map values, asset_object)
        :type values: with the following members
            :py:class:`openquake.shapes.Curve`

            :py:class:`dict` (asset_object)
                ***assetID*** - the assetID
                ***endBranchLabel*** - endBranchLabel
                ***riskres_id*** - for example, 'rr'
                ***list_id*** - 'list'
        """
        super(CurveXMLWriter, self).write(point, values)

        if isinstance(point, shapes.GridPoint):
            point = point.site

        (curve_object, asset_object) = values

        # container element, needs gml:id
        if self.curve_list_el is None:
            self.curve_list_el = etree.SubElement(self.result_el,
                self.container_tag)

        if 'list_id' in asset_object:
            nrml.set_gml_id(self.curve_list_el, str(
                asset_object['list_id']))
        else:
            nrml.set_gml_id(self.curve_list_el, self.CONTAINER_DEFAULT_ID)

        asset_id = str(asset_object['assetID'])
        try:
            asset_el = self.assets_per_id[asset_id]
        except KeyError:

            # nrml:asset, needs gml:id
            asset_el = etree.SubElement(self.curve_list_el,
                xml.RISK_ASSET_TAG)
            nrml.set_gml_id(asset_el, asset_id)
            self.assets_per_id[asset_id] = asset_el

        # check if nrml:site is already existing
        site_el = asset_el.find(xml.RISK_SITE_TAG)
        if site_el is None:
            site_el = etree.SubElement(asset_el, xml.RISK_SITE_TAG)

            point_el = etree.SubElement(site_el, xml.GML_POINT_TAG)
            point_el.set(xml.GML_SRS_ATTR_NAME, xml.GML_SRS_EPSG_4326)

            pos_el = etree.SubElement(point_el, xml.GML_POS_TAG)
            pos_el.text = "%s %s" % (point.longitude, point.latitude)

        elif not xml.element_equal_to_site(site_el, point):
            error_msg = "asset %s cannot have two differing sites: %s, %s " \
                % (asset_id, xml.lon_lat_from_site(site_el), point)
            raise ValueError(error_msg)

        # loss/loss ratio curves - sub-element already created?
        curves_el = asset_el.find(self.curves_tag)
        if curves_el is None:
            curves_el = etree.SubElement(asset_el, self.curves_tag)

        curve_el = etree.SubElement(curves_el, self.curve_tag)

        # attribute for endBranchLabel (optional)
        if 'endBranchLabel' in asset_object:
            curve_el.set(xml.RISK_END_BRANCH_ATTR_NAME,
                str(asset_object[xml.RISK_END_BRANCH_ATTR_NAME]))

        abscissa_el = etree.SubElement(curve_el, self.abscissa_tag)
        abscissa_el.text = _curve_vals_as_gmldoublelist(curve_object)

        poe_el = etree.SubElement(curve_el, xml.RISK_POE_TAG)
        poe_el.text = _curve_poe_as_gmldoublelist(curve_object)


class LossCurveXMLWriter(CurveXMLWriter):
    """NRML serialization of loss curves"""
    container_tag = xml.RISK_LOSS_CONTAINER_TAG
    curves_tag = xml.RISK_LOSS_CURVES_TAG
    curve_tag = xml.RISK_LOSS_CURVE_TAG
    abscissa_tag = xml.RISK_LOSS_ABSCISSA_TAG


class LossRatioCurveXMLWriter(CurveXMLWriter):
    """NRML serialization of loss ratio curves"""
    container_tag = xml.RISK_LOSS_RATIO_CONTAINER_TAG
    curves_tag = xml.RISK_LOSS_RATIO_CURVES_TAG
    curve_tag = xml.RISK_LOSS_RATIO_CURVE_TAG
    abscissa_tag = xml.RISK_LOSS_RATIO_ABSCISSA_TAG


class CurveDBWriter(OutputDBWriter):
    """
    Abstract class implementing a serializer to output loss curves to the
    database.

    Subclasses must implement get_output_type().
    """

    def get_output_type(self):
        return super(CurveDBWriter, self).get_output_type()

    def insert_datum(self, key, values):
        """
        Called for each item in the iterable beeing serialized.

        Parameters will look something like:

        key=Site(-118.077721, 33.852034)
        values=(Curve([...]), {..., u'assetID': u'a5625', ...})
        """
        point = key

        if isinstance(point, shapes.GridPoint):
            point = point.site

        curve_object, asset_object = values

        self._real_insert_datum(asset_object, point, curve_object)

    def _real_insert_datum(self, asset_object, point, curve_object):
        """
        Called for each item in the iterable beeing serialized.

        Parameters will look something like:

        asset_object={..., u'assetID': u'a5625', ...}
        point=Site(-118.077721, 33.852034)
        curve_object=Curve([...]),
        """
        asset = self._get_or_create_loss_asset_data(asset_object, point)

        curve = LossCurveData(
            loss_asset=asset,
            end_branch_label=asset_object.get('endBranchLabel'),
            abscissae=[float(x) for x in curve_object.abscissae],
            poes=[float(y) for y in curve_object.ordinates])
        self.session.add(curve)

    def _get_or_create_loss_asset_data(self, asset_object, point):
        """
        Return the LossAssetData record for the given asset_object, creating it
        if necessary.
        """
        asset_id = asset_object['assetID']

        try:
            asset = self.session.query(LossAssetData)\
                .filter(LossAssetData.output == self.output)\
                .filter(LossAssetData.asset_id == asset_id).one()
        except sqlalchemy.orm.exc.NoResultFound:
            asset = LossAssetData(
                output=self.output,
                asset_id=asset_id,
                pos="POINT(%s %s)" % (point.longitude, point.latitude))
            self.session.add(asset)
        else:
            if not asset.pos == point:
                error_msg = "asset %s has two different positions" % asset_id
                raise ValueError(error_msg)

        return asset


class LossCurveDBWriter(CurveDBWriter):
    """
    Serializer to the database for loss curves.
    """
    def get_output_type(self):
        return "loss_curve"


class LossRatioCurveDBWriter(CurveDBWriter):
    """
    Serializer to the database for loss ratio curves.
    """
    def get_output_type(self):
        return "loss_ratio_curve"


def _curve_vals_as_gmldoublelist(curve_object):
    """Return the list of loss/loss ratio values from a curve object.
    This is the abscissa of the curve.
    The list of values is converted to string joined by a space.
    """
    return " ".join([str(abscissa) for abscissa in curve_object.abscissae])


def _curve_poe_as_gmldoublelist(curve_object):
    """Return the list of PoE values from a curve object.
    This is the ordinate of the curve.
    The list of values is converted to string joined by a space.
    """
    return " ".join([str(ordinate) for ordinate in curve_object.ordinates])
