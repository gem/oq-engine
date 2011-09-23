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
- loss maps for Deterministic, Probabilistic and Classical
"""

from collections import defaultdict

from lxml import etree

from openquake.db import models

from openquake import shapes
from openquake import writer
from openquake import xml

from openquake.output import nrml
from openquake.xml import NRML_NS, GML_NS

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

class LossMapNonDeterministicXMLWriter(LossMapXMLWriter):
    """
    This class serializes loss maps to NRML for Non Deterministic calculators

    Additionally in this loss map we have a timespan and a poe

    timeSpan is an integer representing time in years
    poE is a float between 0 and 1 (extremes included)

    """
    DEFAULT_METADATA = {
        'nrmlID': 'undefined', 'riskResultID': 'undefined',
        'lossMapID': 'undefined', 'endBranchLabel': 'undefined',
        'lossCategory': 'undefined', 'unit': 'undefined',
        'timeSpan': 'undefined', 'poE': 'undefined'}

    def __init__(self, path):
        super(LossMapNonDeterministicXMLWriter, self).__init__(path)

        # removes the lossMap tag inherited from LossMapXMLWriter
        self.loss_map_node.getparent().remove(self.loss_map_node)

        # changes  to <lossMapProbabilistic>
        self.loss_map_node = etree.SubElement(
            self.risk_result_node, xml.RISK_LOSS_MAP_NON_DET_CONTAINER_TAG)

    def write_metadata(self, metadata):
        super(LossMapNonDeterministicXMLWriter, self).write_metadata(metadata)

        # set the rest of the <lossMap> attributes for non deterministic
        for key in ('timeSpan', 'poE'):
            self.loss_map_node.set(
                key, str(metadata.get(key, self.DEFAULT_METADATA[key])))

LOSS_MAP_METADATA_KEYS = [
    ('loss_map_ref', 'lossMapID'),
    ('end_branch_label', 'endBranchLabel'),
    ('category', 'lossCategory'),
    ('unit', 'unit'),
    ('deterministic', 'deterministic'),
    # timespan is for non-deterministic loss maps
    ('timespan', 'timeSpan'),
    # poe is for non-deterministic loss maps
    # enforced by a SQL constraint
    ('poe', 'poE'),
]


class LossMapDBReader(object):
    """
    Read loss map data from the database, returning a data structure
    that can be passed to :func:`LossMapXMLWriter.serialize` to
    produce an XML file.
    """

    def deserialize(self, output_id):
        """
        Read a the given loss map from the database.

        The structure of the result is documented in :class:`LossMapDBWriter`.
        """
        loss_map = models.LossMap.objects.get(output=output_id)
        loss_map_data = loss_map.lossmapdata_set.all()

        items = defaultdict(list)

        for datum in loss_map_data:
            loc = datum.location
            site, loss_asset = self._get_item(loss_map, loc.x, loc.y, datum)
            items[site].append(loss_asset)

        return [self._get_metadata(loss_map)] + items.items()

    @staticmethod
    def _get_metadata(loss_map):
        """
        Returns the metadata dictionary for this loss map

        The format is documented in :class:`LossMapDBWriter`
        """
        return dict((metadata_key, getattr(loss_map, key))
                        for key, metadata_key in LOSS_MAP_METADATA_KEYS)

    @staticmethod
    def _get_item(loss_map, lon, lat, datum):
        """
        Returns the data for a point in the loss map

        :returns: tuple of ``(site, (loss, asset))``

        The format for loss and asset documented in :class:`LossMapDBWriter`.
        """
        site = shapes.Site(lon, lat)
        asset = {'assetID': datum.asset_ref}

        if loss_map.deterministic:
            loss = {'mean_loss': datum.value,
                    'stddev_loss': datum.std_dev}
        else:
            loss = {'value': datum.value}

        return site, (loss, asset)


class LossMapDBWriter(writer.DBWriter):
    """
    Serialize to the database deterministic and non-deterministic loss maps.

    Deterministic loss maps, generated by the deterministic event-based
    calculators, store, per asset, the mean and standard deviation of the loss.

    Non-deterministic loss maps, generated by classical psha-based or
    probabilistic based calculators, store a probability of exceedance and, per
    asset, a loss.

    The data passed to :func:`serialize()` for deterministic loss maps will
    look something like this::

        [# metadata
         {'nrmlID': 'test_nrml_id',
          'riskResultID': 'test_rr_id',
          'lossMapID': 'test_lm_id',
          'deterministic': True,
          'endBranchLabel': 'test_ebl',
          'lossCategory': 'economic_loss',
          'unit': 'EUR'},
         # map data
         (Site(-121.7, 37.6),
          [(# loss
            {'mean_loss': 120000.0, 'stddev_loss': 2000.0},
            # asset
            {'assetID': 'a1713'}),
           ({...}, {...}),
           ...
           ]),
         (Site(...),
          [(# loss
            {...},
            # asset
            {...}),
           ...]),
         ],

    The data passed to :func:`serialize()` for nondeterministic loss maps will
    look something like this::

        [# metadata
         {'nrmlID': 'test_nrml_id',
          'riskResultID': 'test_rr_id',
          'lossMapID': 'test_lm_id',
          'deterministic': False,
          'poe': 0.01,
          'endBranchLabel': 'test_ebl',
          'lossCategory': 'economic_loss',
          'unit': 'EUR'},
         # map data
         (Site(-121.7, 37.6),
          [(# loss
            {'value': 12},
            # asset
            {'assetID': 'a1713'}),
           ({...}, {...}),
           ...
           ]),
         (Site(...),
          [(# loss
            {...},
            # asset
            {...}),
           ...]),
         ],

    """

    def __init__(self, nrml_path, oq_job_id):
        super(LossMapDBWriter, self).__init__(nrml_path, oq_job_id)

        self.metadata = None
        self.bulk_inserter = writer.BulkInserter(models.LossMapData)

    def get_output_type(self):
        return 'loss_map'

    def serialize(self, iterable):
        self.insert_output(self.get_output_type())

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
                'loss_map_id': self.metadata.id,
                'asset_ref': asset['assetID'],
                'location': "POINT(%s %s)" % (site.longitude, site.latitude),
            }

            if self.metadata.deterministic:
                kwargs.update({
                    'value': float(loss.get('mean_loss')),
                    'std_dev': float(loss.get('stddev_loss')),
                })
            else:
                kwargs.update({
                    'value': float(loss.get('value')),
                    'std_dev': 0.0,
                })

            self.bulk_inserter.add_entry(**kwargs)

    def _insert_metadata(self, metadata):
        """
        Insert a record holding the metadata of a loss map.
        """
        kwargs = {
            'output': self.output,
        }

        for key, metadata_key in LOSS_MAP_METADATA_KEYS:
            kwargs[key] = metadata.get(metadata_key)

        self.metadata = models.LossMap(**kwargs)
        self.metadata.save()


def create_loss_map_writer(job_id, serialize_to, nrml_path, deterministic):
    """Create a loss map writer observing the settings in the config file.

    :param job_id: the id of the job the curve belongs to.
    :type job_id: int
    :param serialize_to: where to serialize
    :type serialize_to: list of strings. Permitted values: 'db', 'xml'.
    :param nrml_path: the full path of the XML/NRML representation of the
        loss map.
    :type nrml_path: string
    :param deterministic: Whether the loss map is deterministic (True) or
        non-deterministic (False)
    :type deterministic: boolean
    :returns: None or an instance of
        :py:class:`output.risk.LossMapXMLWriter` or
        :py:class:`output.risk.LossMapDBWriter`
    """
    writers = []

    if 'db' in serialize_to:
        writers.append(LossMapDBWriter(nrml_path, job_id))

    if 'xml' in serialize_to:
        if deterministic:
            writers.append(LossMapXMLWriter(nrml_path))
        else:
            writers.append(LossMapNonDeterministicXMLWriter(nrml_path))
    return writer.compose_writers(writers)


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


class LossCurveDBReader(object):
    """
    Read loss curve data from the database, returning a data structure
    that can be passed to :func:`LossCurveXMLWriter.serialize` to
    produce an XML file.
    """

    @staticmethod
    def deserialize(output_id):
        """
        Read a the given loss curve from the database.

        The structure of the result is documented in
        :class:`LossCurveDBWriter`.
        """
        loss_curve = models.LossCurve.objects.get(output=output_id)
        loss_curve_data = loss_curve.losscurvedata_set.all()

        curves = []
        asset = {
            'assetValueUnit': loss_curve.unit,
            'endBranchLabel': loss_curve.end_branch_label,
            'lossCategory': loss_curve.category,
        }

        for datum in loss_curve_data:
            curve = shapes.Curve(zip(datum.losses, datum.poes))

            asset_object = asset.copy()
            asset_object['assetID'] = datum.asset_ref

            loc = datum.location
            curves.append((shapes.Site(loc.x, loc.y), (curve, asset_object)))

        return curves


class LossCurveDBWriter(writer.DBWriter):
    """
    Serializer to the database for loss curves.

    The data passed to :func:`serialize()` will look something like this::

        [(Site(-118.077721, 33.852034),
          (Curve([(3.18e-06, 1.0), (xvalue, yvalue), (...), (...), ...]),
           {'assetValue': 5.07,
           'assetID': 'a5625',
           'listDescription': 'Collection of exposure values for ...',
           'structureCategory': 'RM1L',
           'lon': -118.077721,
           'assetDescription': 'LA building',
           'vulnerabilityFunctionReference': 'HAZUS_RM1L_LC',
           'listID': 'LA01',
           'assetValueUnit': 'EUR',
           'lat': 33.852034})),
         (Site(...), (Curve(...), {...asset data...})),
         ...
         ]
    """

    def __init__(self, nrml_path, oq_job_id):
        super(LossCurveDBWriter, self).__init__(nrml_path, oq_job_id)

        self.curve = None
        self.bulk_inserter = writer.BulkInserter(models.LossCurveData)

    def get_output_type(self):
        return "loss_curve"

    def insert_datum(self, key, values):
        """
        Called for each item in the iterable beeing serialized.

        :param key: the location of the asset for which the loss curve has been
                    calculated
        :type key: :py:class:`openquake.shapes.Site`

        :param values: a tuple (curve, asset_object). See
        :py:meth:`insert_asset_loss_curve` for more details.
        """
        point = key

        if isinstance(point, shapes.GridPoint):
            point = point.site

        curve, asset_object = values

        self.insert_asset_loss_curve(asset_object, point, curve)

    def insert_asset_loss_curve(self, asset_object, point, curve):
        """
        Store into the database the loss curve of a given asset.

        :param asset_object: the asset for which the loss curve is being stored
        :type asset_object: :py:class:`dict`

        :param point: the location of the asset
        :type point: :py:class:`openquake.shapes.Site`

        :param curve: the loss curve
        :type curve: :py:class:`openquake.shapes.Curve`

        The asset_object contains at least this items:
            * **assetID** - the assetID
            * **assetValueUnit** - the unit of the value (e.g. EUR)

        """

        if self.curve is None:
            self.curve = models.LossCurve(output=self.output,
                unit=asset_object.get('assetValueUnit'),
                # The following attributes (endBranchLabel, lossCategory) are
                # currently not passed in by the calculators
                end_branch_label=asset_object.get('endBranchLabel'),
                category=asset_object.get('lossCategory'))
            self.curve.save()

        # Note: asset_object has lon and lat attributes that appear to contain
        # the same coordinates as point
        self.bulk_inserter.add_entry(
            loss_curve_id=self.curve.id,
            asset_ref=asset_object['assetID'],
            location="POINT(%s %s)" % (point.longitude, point.latitude),
            losses=[float(x) for x in curve.abscissae],
            poes=[float(y) for y in curve.ordinates])


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


def create_loss_curve_writer(job_id, serialize_to, nrml_path, curve_mode):
    """Create a loss curve writer observing the settings in the config file.

    If no writer is available for the given curve_mode and settings, returns
    None.

    :param job_id: the id of the job the curve belongs to.
    :type job_id: int
    :param serialize_to: where to serialize
    :type serialize_to: list of strings. Permitted values: 'db', 'xml'.
    :param str nrml_path: the full path of the XML/NRML representation of the
        hazard map.
    :param str curve_mode: one of 'loss', 'loss_ratio'
    :returns: None or an instance of
        :py:class:`output.risk.LossCurveXMLWriter`,
        :py:class:`output.risk.LossCurveDBWriter`,
        :py:class:`output.risk.LossRatioCurveXMLWriter`
    """

    assert curve_mode in ('loss', 'loss_ratio')

    writers = []

    if 'db' in serialize_to:
        assert job_id, "No job_id supplied"
        job_id = int(job_id)

        if curve_mode == 'loss':
            writers.append(LossCurveDBWriter(nrml_path, job_id))
        elif curve_mode == 'loss_ratio':
            # We are non interested in storing loss ratios in the db
            pass

    if 'xml' in serialize_to:
        if curve_mode == 'loss':
            writer_class = LossCurveXMLWriter
        elif curve_mode == 'loss_ratio':
            writer_class = LossRatioCurveXMLWriter

        writers.append(writer_class(nrml_path))

    return writer.compose_writers(writers)
