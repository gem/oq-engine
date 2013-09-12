# Copyright (c) 2012-2013, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.

"""
Classes for serializing various NRML XML artifacts.
"""

import json
import numpy
import StringIO
import tokenize

from lxml import etree
from collections import OrderedDict
from itertools import izip

import openquake.nrmllib
from openquake.nrmllib import NRMLFile
from openquake.nrmllib import utils
from openquake.nrmllib import models


SM_TREE_PATH = 'sourceModelTreePath'
GSIM_TREE_PATH = 'gsimTreePath'

#: Maps XML writer constructor keywords to XML attribute names
_ATTR_MAP = OrderedDict([
    ('statistics', 'statistics'),
    ('quantile_value', 'quantileValue'),
    ('smlt_path', 'sourceModelTreePath'),
    ('gsimlt_path', 'gsimTreePath'),
    ('imt', 'IMT'),
    ('investigation_time', 'investigationTime'),
    ('sa_period', 'saPeriod'),
    ('sa_damping', 'saDamping'),
    ('poe', 'poE'),
    ('lon', 'lon'),
    ('lat', 'lat'),
])

GML_NS = openquake.nrmllib.SERIALIZE_NS_MAP['gml']


def _validate_hazard_metadata(md):
    """
    Validate metadata `dict` of attributes, which are more or less the same for
    hazard curves, hazard maps, and disaggregation histograms.

    :param dict md:
        `dict` which can contain the following keys:

        * statistics
        * gsimlt_path
        * smlt_path
        * imt
        * sa_period
        * sa_damping

    :raises:
        :exc:`ValueError` if the metadata is not valid.
    """
    if (md.get('statistics') is not None
        and (md.get('smlt_path') is not None
             or md.get('gsimlt_path') is not None)):
        raise ValueError('Cannot specify both `statistics` and logic tree '
                         'paths')

    if md.get('statistics') is not None:
        # make sure only valid statistics types are specified
        if md.get('statistics') not in ('mean', 'quantile'):
            raise ValueError('`statistics` must be either `mean` or '
                             '`quantile`')
    else:
        # must specify both logic tree paths
        if md.get('smlt_path') is None or md.get('gsimlt_path') is None:
            raise ValueError('Both logic tree paths are required for '
                             'non-statistical results')

    if md.get('statistics') == 'quantile':
        if md.get('quantile_value') is None:
            raise ValueError('quantile stastics results require a quantile'
                             ' value to be specified')

    if not md.get('statistics') == 'quantile':
        if md.get('quantile_value') is not None:
            raise ValueError('Quantile value must be specified with '
                             'quantile statistics')

    if md.get('imt') == 'SA':
        if md.get('sa_period') is None:
            raise ValueError('`sa_period` is required for IMT == `SA`')
        if md.get('sa_damping') is None:
            raise ValueError('`sa_damping` is required for IMT == `SA`')


def _set_metadata(element, metadata, attr_map, transform=str):
    """
    Set metadata attributes on a given ``element``.

    :param element:
        :class:`lxml.etree._Element` instance
    :param metadata:
        Dictionary of metadata items containing attribute data for ``element``.
    :param attr_map:
        Dictionary mapping of metadata key->attribute name.
    :param transform:
        A function accepting and returning a single value to be applied to each
        attribute value. Defaults to `str`.
    """
    for kw, attr in attr_map.iteritems():
        value = metadata.get(kw)
        if value is not None:
            element.set(attr, transform(value))


class BaseCurveWriter(object):
    """
    Base class for curve writers.

    :param dest:
        File path (including filename) or file-like object for results to
        be saved to.
    :param metadata:
        The following keyword args are required:

        * investigation_time: Investigation time (in years) defined in the
          calculation which produced these results.

        The following are more or less optional (combinational rules noted
        below where applicable):

        * statistics: 'mean' or 'quantile'
        * quantile_value: Only required if statistics = 'quantile'.
        * smlt_path: String representing the logic tree path which produced
          these curves. Only required for non-statistical curves.
        * gsimlt_path: String represeting the GSIM logic tree path which
          produced these curves. Only required for non-statisical curves.
    """

    def __init__(self, dest, **metadata):
        self.dest = dest
        self.metadata = metadata
        _validate_hazard_metadata(metadata)

    def serialize(self, _data):
        """
        Implement in subclasses.
        """
        raise NotImplementedError


class HazardCurveXMLWriter(BaseCurveWriter):
    """
    Hazard Curve XML writer. See :class:`BaseCurveWriter` for a list of
    general constructor inputs.

    The following additional metadata params are required:
        * imt: Intensity measure type used to compute these hazard curves.
        * imls: Intensity measure levels, which represent the x-axis values of
          each curve.

    The following parameters are optional:
        * sa_period: Only used with imt = 'SA'.
        * sa_damping: Only used with imt = 'SA'.
    """

    def serialize(self, data):
        """
        Write a sequence of hazard curves to the specified file.

        :param data:
            Iterable of hazard curve data. Each datum must be an object with
            the following attributes:

            * poes: A list of probability of exceedence values (floats).
            * location: An object representing the location of the curve; must
              have `x` and `y` to represent lon and lat, respectively.
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)
            self.add_hazard_curves(root, self.metadata, data)

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))

    def add_hazard_curves(self, root, metadata, data):
        """
        Add hazard curves stored into `data` as child of the `root`
        element with `metadata`. See the documentation of the method
        `serialize` and the constructor for a description of `data`
        and `metadata`, respectively.
        """
        hazard_curves = etree.SubElement(root, 'hazardCurves')

        _set_metadata(hazard_curves, metadata, _ATTR_MAP)

        imls_elem = etree.SubElement(hazard_curves, 'IMLs')
        imls_elem.text = ' '.join([str(x) for x in metadata['imls']])
        gml_ns = openquake.nrmllib.SERIALIZE_NS_MAP['gml']

        for hc in data:
            hc_elem = etree.SubElement(hazard_curves, 'hazardCurve')
            gml_point = etree.SubElement(hc_elem, '{%s}Point' % gml_ns)
            gml_pos = etree.SubElement(gml_point, '{%s}pos' % gml_ns)
            gml_pos.text = '%s %s' % (hc.location.x, hc.location.y)
            poes_elem = etree.SubElement(hc_elem, 'poEs')
            poes_elem.text = ' '.join([str(x) for x in hc.poes])


class HazardCurveGeoJSONWriter(BaseCurveWriter):
    """
    Writes hazard curves to GeoJSON. Has the same constructor and interface as
    :class:`HazardCurveXMLWriter`.
    """

    def serialize(self, data):
        """
        Write the hazard curves to the given as GeoJSON. The GeoJSON format
        is customized to contain various bits of metadata.

        See :meth:`HazardCurveXMLWriter.serialize` for expected input.
        """
        oqmetadata = {}
        for key, value in self.metadata.iteritems():
            if key == 'imls':
                oqmetadata['IMLs'] = value
            if value is not None:
                if key == 'imls':
                    oqmetadata['IMLs'] = value
                else:
                    oqmetadata[_ATTR_MAP.get(key)] = str(value)

        features = []
        feature_coll = {
            'type': 'FeatureCollection',
            'features': features,
            'oqtype': 'HazardCurve',
            'oqnrmlversion': '0.4',
            'oqmetadata': oqmetadata,
        }
        for hc in data:
            poes = list(hc.poes)
            lon = hc.location.x
            lat = hc.location.y

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(lon), float(lat)],
                },
                'properties': {'poEs': list(poes)},
            }
            features.append(feature)

        with NRMLFile(self.dest, 'w') as fh:
            json.dump(feature_coll, fh)


class MultiHazardCurveXMLWriter(object):
    """
    A serializer of multiple hazard curve set having multiple
    metadata. It uses
    :class:`openquake.nrmllib.hazard.writers.HazardCurveXMLWriter` to
    actually serialize the single set of curves.

    :attr str dest:
         The path of the filename to be written, or a file-like object
    :attr metadata_set:
         Iterable over metadata suitable to create instances of
         :class:`openquake.nrmllib.hazard.writers.HazardCurveXMLWriter`
    """
    def __init__(self, dest, metadata_set):
        self.dest = dest
        self.metadata_set = metadata_set

        for metadata in metadata_set:
            _validate_hazard_metadata(metadata)

    def serialize(self, curve_set):
        """
        Write a set of sequence of hazard curves to the specified file.
        :param curve_set:

           Iterable over sequence of curves. Each element returned by
           the iterable is an iterable suitable to be used by the
           :meth:`serialize` of the class
           :class:`openquake.nrmllib.hazard.writers.HazardCurveXMLWriter`
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)
            for metadata, curve_data in zip(self.metadata_set, curve_set):
                writer = HazardCurveXMLWriter(self.dest, **metadata)
                writer.add_hazard_curves(root, metadata, curve_data)

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class EventBasedGMFXMLWriter(object):
    """
    :param dest:
        File path (including filename) or a file-like object for XML results to
        be saved to.
    :param str sm_lt_path:
        Source model logic tree branch identifier of the logic tree realization
        which produced this collection of ground motion fields.
    :param gsim_lt_path:
        GSIM logic tree branch identifier of the logic tree realization which
        produced this collection of ground motion fields.
    """

    def __init__(self, dest, sm_lt_path, gsim_lt_path):
        self.dest = dest
        self.sm_lt_path = sm_lt_path
        self.gsim_lt_path = gsim_lt_path

    def serialize(self, data):
        """
        Serialize a collection of ground motion fields to XML.

        :param data:
            An iterable of "GMF set" objects.
            Each "GMF set" object should:

            * have an `investigation_time` attribute
            * have an `stochastic_event_set_id` attribute
            * be iterable, yielding a sequence of "GMF" objects

            Each "GMF" object should:

            * have an `imt` attribute
            * have an `sa_period` attribute (only if `imt` is 'SA')
            * have an `sa_damping` attribute (only if `imt` is 'SA')
            * have a `rupture_id` attribute (to indicate which rupture
              contributed to this gmf)
            * be iterable, yielding a sequence of "GMF node" objects

            Each "GMF node" object should have:

            * a `gmv` attribute (to indicate the ground motion value
            * `lon` and `lat` attributes (to indicate the geographical location
              of the ground motion field)
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            if self.sm_lt_path is not None and self.gsim_lt_path is not None:
                # A normal GMF collection
                gmf_container = etree.SubElement(root, 'gmfCollection')
                gmf_container.set(SM_TREE_PATH, self.sm_lt_path)
                gmf_container.set(GSIM_TREE_PATH, self.gsim_lt_path)
            else:
                # A collection of GMFs for a complete logic tree
                # In this case, we should only have a single <gmfSet>,
                # containing all ground motion fields.
                # NOTE: In this case, there is no need for a <gmfCollection>
                # element; instead, we just write the single <gmfSet>
                # underneath the root <nrml> element.
                gmf_container = root

            for gmf_set in data:
                gmf_set_elem = etree.SubElement(gmf_container, 'gmfSet')
                gmf_set_elem.set(
                    'investigationTime', str(gmf_set.investigation_time))
                gmf_set_elem.set(
                    'stochasticEventSetId',
                    str(gmf_set.stochastic_event_set_id))

                for gmf in gmf_set:
                    gmf_elem = etree.SubElement(gmf_set_elem, 'gmf')
                    gmf_elem.set('IMT', gmf.imt)
                    if gmf.imt == 'SA':
                        gmf_elem.set('saPeriod', str(gmf.sa_period))
                        gmf_elem.set('saDamping', str(gmf.sa_damping))
                    gmf_elem.set('ruptureId', str(gmf.rupture_id))

                    for gmf_node in gmf:
                        node_elem = etree.SubElement(gmf_elem, 'node')
                        node_elem.set('gmv', str(gmf_node.gmv))
                        node_elem.set('lon', str(gmf_node.location.x))
                        node_elem.set('lat', str(gmf_node.location.y))

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class SESXMLWriter(object):
    """
    :param dest:
        File path (including filename) or a file-like object for XML results to
        be saved to.
    :param str sm_lt_path:
        Source model logic tree branch identifier of the logic tree realization
        which produced this collection of stochastic event sets.
    :param gsim_lt_path:
        GSIM logic tree branch identifier of the logic tree realization which
        produced this collection of stochastic event sets.
    """

    def __init__(self, dest, sm_lt_path, gsim_lt_path):
        self.dest = dest
        self.sm_lt_path = sm_lt_path
        self.gsim_lt_path = gsim_lt_path

    def serialize(self, data):
        """
        Serialize a collection of stochastic event sets to XML.

        :param data:
            An iterable of "SES" ("Stochastic Event Set") objects.
            Each "SES" object should:

            * have an `investigation_time` attribute
            * have an `id` attribute
            * be iterable, yielding a sequence of "rupture" objects

            Each "rupture" should have the following attributes:
            * `id`
            * `magnitude`
            * `strike`
            * `dip`
            * `rake`
            * `tectonic_region_type`
            * `is_from_fault_source` (a `bool`)
            * `is_multi_surface` (a `bool`)
            * `lons`
            * `lats`
            * `depths`

            If `is_from_fault_source` is `True`, the rupture originated from a
            simple or complex fault sources. In this case, `lons`, `lats`, and
            `depths` should all be 2D arrays (of uniform shape). These
            coordinate triples represent nodes of the rupture mesh.

            If `is_from_fault_source` is `False`, the rupture originated from a
            point or area source. In this case, the rupture is represented by a
            quadrilateral planar surface. This planar surface is defined by 3D
            vertices. In this case, the rupture should have the following
            attributes:

            * `top_left_corner`
            * `top_right_corner`
            * `bottom_right_corner`
            * `bottom_left_corner`

            Each of these should be a triple of `lon`, `lat`, `depth`.

            If `is_multi_surface` is `True`, the rupture originated from a
            multi-surface source. In this case, `lons`, `lats`, and `depths`
            should have uniform length. The length should be a multiple of 4,
            where each segment of 4 represents the corner points of a planar
            surface in the following order:

            * top left
            * top right
            * bottom left
            * bottom right

            Each of these should be a triple of `lon`, `lat`, `depth`.
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            if self.sm_lt_path is not None and self.gsim_lt_path is not None:
                # A normal stochastic event set collection
                ses_container = etree.SubElement(
                    root, 'stochasticEventSetCollection')

                ses_container.set(SM_TREE_PATH, self.sm_lt_path)
                ses_container.set(GSIM_TREE_PATH, self.gsim_lt_path)
            else:
                # A stochastic event set collection for the complete logic tree
                # In this case, we should only have a single stochastic event
                # set.
                # NOTE: In this case, there is no need for a
                # `stochasticEventSetCollection` tag.
                # Write the _single_ stochastic event set directly under the
                # root element.
                ses_container = root
                # NOTE: The code below is written to expect 1 or more SESs in
                # `data`. Again, there will only be one in this case.

            for ses in data:
                ses_elem = etree.SubElement(
                    ses_container, 'stochasticEventSet')
                ses_elem.set('id', str(ses.id))
                ses_elem.set('investigationTime', str(ses.investigation_time))

                for rupture in ses:
                    rup_elem = etree.SubElement(ses_elem, 'rupture')
                    rup_elem.set('id', str(rupture.id))
                    rup_elem.set('magnitude', str(rupture.magnitude))
                    rup_elem.set('strike', str(rupture.strike))
                    rup_elem.set('dip', str(rupture.dip))
                    rup_elem.set('rake', str(rupture.rake))
                    rup_elem.set(
                        'tectonicRegion', str(rupture.tectonic_region_type))

                    if rupture.is_from_fault_source:
                        # rupture is from a simple or complex fault source
                        # the rupture geometry is represented by a mesh of 3D
                        # points
                        self._create_rupture_mesh(rupture, rup_elem)
                    else:
                        if rupture.is_multi_surface:
                            self._create_multi_planar_surface(rupture,
                                                              rup_elem)
                        else:
                            # rupture is from a point or area source
                            # the rupture geometry is represented by four 3D
                            # corner points
                            self._create_planar_surface(rupture, rup_elem)

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))

    @staticmethod
    def _create_rupture_mesh(rupture, rup_elem):
        """
        :param rupture:
            See documentation for :meth:`serialize` for more info.
        :param rup_elem:
            A `rupture` :class:`lxml.etree._Element`.
        """
        mesh_elem = etree.SubElement(rup_elem, 'mesh')

        # we assume the mesh components (lons, lats, depths)
        # are of uniform shape
        for i, row in enumerate(rupture.lons):
            for j, col in enumerate(row):
                node_elem = etree.SubElement(mesh_elem, 'node')
                node_elem.set('row', str(i))
                node_elem.set('col', str(j))
                node_elem.set('lon', str(rupture.lons[i][j]))
                node_elem.set('lat', str(rupture.lats[i][j]))
                node_elem.set(
                    'depth', str(rupture.depths[i][j]))

        try:
            # if we never entered the loop above, it's possible
            # that i and j will be undefined
            mesh_elem.set('rows', str(i + 1))
            mesh_elem.set('cols', str(j + 1))
        except NameError:
            raise ValueError('Invalid rupture mesh')

    @staticmethod
    def _create_planar_surface(rupture, rup_elem):
        """
        :param rupture:
            See documentation for :meth:`serialize` for more info.
        :param rup_elem:
            A `rupture` :class:`lxml.etree._Element`.
        """
        ps_elem = etree.SubElement(
            rup_elem, 'planarSurface')

        # create the corner point elements, in the order of:
        # * top left
        # * top right
        # * bottom left
        # * bottom right
        for el_name, corner in (
                ('topLeft', rupture.top_left_corner),
                ('topRight', rupture.top_right_corner),
                ('bottomLeft', rupture.bottom_left_corner),
                ('bottomRight', rupture.bottom_right_corner)):

            corner_elem = etree.SubElement(ps_elem, el_name)
            corner_elem.set('lon', str(corner[0]))
            corner_elem.set('lat', str(corner[1]))
            corner_elem.set('depth', str(corner[2]))

    @staticmethod
    def _create_multi_planar_surface(rupture, rup_elem):
        """
        """
        assert len(rupture.lons) % 4 == 0
        assert len(rupture.lons) == len(rupture.lats) == len(rupture.depths)

        for offset in xrange(len(rupture.lons) / 4):
            start = offset * 4
            end = offset * 4 + 4
            lons = rupture.lons[start:end]
            lats = rupture.lats[start:end]
            depths = rupture.depths[start:end]

            ps_elem = etree.SubElement(
                rup_elem, 'planarSurface')

            top_left, top_right, bottom_left, bottom_right = \
                izip(lons, lats, depths)

            for el_name, corner in (
                    ('topLeft', top_left),
                    ('topRight', top_right),
                    ('bottomLeft', bottom_left),
                    ('bottomRight', bottom_right)):

                corner_elem = etree.SubElement(ps_elem, el_name)
                corner_elem.set('lon', str(corner[0]))
                corner_elem.set('lat', str(corner[1]))
                corner_elem.set('depth', str(corner[2]))


class HazardMapWriter(object):
    """
    :param dest:
        File path (including filename) or a file-like object for results to be
        saved to.
    :param metadata:
        The following keyword args are required:

        * investigation_time: Investigation time (in years) defined in the
          calculation which produced these results.
        * imt: Intensity measure type used to compute these hazard curves.
        * poe: The Probability of Exceedance level for which this hazard map
          was produced.

        The following are more or less optional (combinational rules noted
        below where applicable):

        * statistics: 'mean' or 'quantile'
        * quantile_value: Only required if statistics = 'quantile'.
        * smlt_path: String representing the logic tree path which produced
          these curves. Only required for non-statistical curves.
        * gsimlt_path: String represeting the GSIM logic tree path which
          produced these curves. Only required for non-statisical curves.
        * sa_period: Only used with imt = 'SA'.
        * sa_damping: Only used with imt = 'SA'.
    """

    def __init__(self, dest, **metadata):
        self.dest = dest
        self.metadata = metadata
        _validate_hazard_metadata(metadata)

    def serialize(self, data):
        """
        Write a sequence of hazard map data to the specified file.

        :param data:
            Iterable of hazard map data. Each datum should be a triple of
            (lon, lat, iml) values.
        """
        raise NotImplementedError()


class HazardMapXMLWriter(HazardMapWriter):
    """
    NRML/XML implementation of a :class:`HazardMapWriter`.

    See :class:`HazardMapWriter` for information about constructor parameters.
    """

    def serialize(self, data):
        """
        Serialize hazard map data to XML.

        See :meth:`HazardMapWriter.serialize` for details about the expected
        input.
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            hazard_map = etree.SubElement(root, 'hazardMap')

            _set_metadata(hazard_map, self.metadata, _ATTR_MAP)

            for lon, lat, iml in data:
                node = etree.SubElement(hazard_map, 'node')
                node.set('lon', str(lon))
                node.set('lat', str(lat))
                node.set('iml', str(iml))

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class HazardMapGeoJSONWriter(HazardMapWriter):
    """
    GeoJSON implementation of a :class:`HazardMapWriter`. Serializes hazard
    maps as FeatureCollection artifacts with additional hazard map metadata.

    See :class:`HazardMapWriter` for information about constructor parameters.
    """

    def serialize(self, data):
        """
        Serialize hazard map data to GeoJSON.

        See :meth:`HazardMapWriter.serialize` for details about the expected
        input.
        """
        oqmetadata = {}
        for key, value in self.metadata.iteritems():
            if value is not None:
                oqmetadata[_ATTR_MAP.get(key)] = str(value)

        feature_coll = {
            'type': 'FeatureCollection',
            'features': [],
            'oqtype': 'HazardMap',
            'oqnrmlversion': '0.4',
            'oqmetadata': oqmetadata,
        }
        features = feature_coll['features']

        for lon, lat, iml in data:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(lon), float(lat)],
                },
                'properties': {'iml': float(iml)},
            }
            features.append(feature)

        with NRMLFile(self.dest, 'w') as fh:
            json.dump(feature_coll, fh)


class DisaggXMLWriter(object):
    """
    :param dest:
        File path (including filename) or file-like object for XML results to
        be saved to.
    :param metadata:
        The following keyword args are required:

        * investigation_time: Investigation time (in years) defined in the
          calculation which produced these results.
        * imt: Intensity measure type used to compute these matrices.
        * lon, lat: Longitude and latitude associated with these results.

        The following attributes define dimension context for the result
        matrices:

        * mag_bin_edges: List of magnitude bin edges (floats)
        * dist_bin_edges: List of distance bin edges (floats)
        * lon_bin_edges: List of longitude bin edges (floats)
        * lat_bin_edges: List of latitude bin edges (floats)
        * eps_bin_edges: List of epsilon bin edges (floats)
        * tectonic_region_types: List of tectonic region types (strings)
        * smlt_path: String representing the logic tree path which produced
          these results. Only required for non-statistical results.
        * gsimlt_path: String represeting the GSIM logic tree path which
          produced these results. Only required for non-statistical results.

        The following are optional, depending on the `imt`:

        * sa_period: Only used with imt = 'SA'.
        * sa_damping: Only used with imt = 'SA'.
    """

    #: Maps metadata keywords to XML attribute names for bin edge information
    #: passed to the constructor.
    #: The dict here is an `OrderedDict` so as to give consistent ordering of
    #: result attributes.
    BIN_EDGE_ATTR_MAP = OrderedDict([
        ('mag_bin_edges', 'magBinEdges'),
        ('dist_bin_edges', 'distBinEdges'),
        ('lon_bin_edges', 'lonBinEdges'),
        ('lat_bin_edges', 'latBinEdges'),
        ('eps_bin_edges', 'epsBinEdges'),
        ('tectonic_region_types', 'tectonicRegionTypes'),
    ])

    DIM_LABEL_TO_BIN_EDGE_MAP = dict([
        ('Mag', 'mag_bin_edges'),
        ('Dist', 'dist_bin_edges'),
        ('Lon', 'lon_bin_edges'),
        ('Lat', 'lat_bin_edges'),
        ('Eps', 'eps_bin_edges'),
        ('TRT', 'tectonic_region_types'),
    ])

    def __init__(self, dest, **metadata):
        self.dest = dest
        self.metadata = metadata
        _validate_hazard_metadata(self.metadata)

    def serialize(self, data):
        """
        :param data:
            A sequence of data where each datum has the following attributes:

            * matrix: N-dimensional numpy array containing the disaggregation
              histogram.
            * dim_labels: A list of strings which label the dimensions of a
              given histogram. For example, for a Magnitude-Distance-Epsilon
              histogram, we would expect `dim_labels` to be
              ``['Mag', 'Dist', 'Eps']``.
            * poe: The disaggregation Probability of Exceedance level for which
              these results were produced.
            * iml: Intensity measure level, interpolated from the source hazard
              curve at the given ``poe``.
        """

        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)

            diss_matrices = etree.SubElement(root, 'disaggMatrices')

            _set_metadata(diss_matrices, self.metadata, _ATTR_MAP)

            transform = lambda val: ', '.join([str(x) for x in val])
            _set_metadata(diss_matrices, self.metadata, self.BIN_EDGE_ATTR_MAP,
                          transform=transform)

            for result in data:
                diss_matrix = etree.SubElement(diss_matrices, 'disaggMatrix')

                # Check that we have bin edges defined for each dimension label
                # (mag, dist, lon, lat, eps, TRT)
                for label in result.dim_labels:
                    bin_edge_attr = self.DIM_LABEL_TO_BIN_EDGE_MAP.get(label)
                    assert self.metadata.get(bin_edge_attr) is not None, (
                        "Writer is missing '%s' metadata" % bin_edge_attr
                    )

                result_type = ','.join(result.dim_labels)
                diss_matrix.set('type', result_type)

                dims = ','.join([str(x) for x in result.matrix.shape])
                diss_matrix.set('dims', dims)

                diss_matrix.set('poE', str(result.poe))
                diss_matrix.set('iml', str(result.iml))

                for idxs, value in numpy.ndenumerate(result.matrix):
                    prob = etree.SubElement(diss_matrix, 'prob')

                    index = ','.join([str(x) for x in idxs])
                    prob.set('index', index)
                    prob.set('value', str(value))

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class ScenarioGMFXMLWriter(object):
    """
    :param dest:
        File path (including filename) or file-like object for XML results to
        be saved to.
    """

    def __init__(self, dest):
        self.dest = dest

    def serialize(self, data):
        """
        Serialize a collection of ground motion fields to XML.

        :param data:
            An iterable of "GMFScenario" objects.

            Each "GMFScenario" object should:

            * have an `imt` attribute
            * have an `sa_period` attribute (only if `imt` is 'SA')
            * have an `sa_damping` attribute (only if `imt` is 'SA')
            * be iterable, yielding a sequence of "GMF node" objects

            Each "GMF node" object should have:

            * an `gmv` attribute (to indicate the ground motion value
            * `lon` and `lat` attributes (to indicate the geographical location
              of the ground motion field
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element('nrml',
                                 nsmap=openquake.nrmllib.SERIALIZE_NS_MAP)
            gmfset = etree.SubElement(root, 'gmfSet')
            for gmf in data:
                gmf_elem = etree.SubElement(gmfset, 'gmf')
                gmf_elem.set('IMT', gmf.imt)
                if gmf.imt == 'SA':
                    gmf_elem.set('saPeriod', str(gmf.sa_period))
                    gmf_elem.set('saDamping', str(gmf.sa_damping))
                for gmf_node in gmf:
                    node_elem = etree.SubElement(gmf_elem, 'node')
                    node_elem.set('gmv', str(gmf_node.gmv))
                    node_elem.set('lon', str(gmf_node.location.x))
                    node_elem.set('lat', str(gmf_node.location.y))

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class UHSXMLWriter(BaseCurveWriter):
    """
    UHS curve XML writer. See :class:`BaseCurveWriter` for a list of general
    constructor inputs.

    The following additional metadata params are required:
        * poe: Probability of exceedance for which a given set of UHS have been
               computed
        * periods: A list of SA (Spectral Acceleration) period values, sorted
                   ascending order
    """

    def __init__(self, dest, **metadata):
        super(UHSXMLWriter, self).__init__(dest, **metadata)

        if self.metadata.get('poe') is None:
            raise ValueError('`poe` keyword arg is required')

        periods = self.metadata.get('periods')
        if periods is None:
            raise ValueError('`periods` keyword arg is required')

        if len(periods) == 0:
            raise ValueError('`periods` must contain at least one value')

        if not sorted(periods) == periods:
            raise ValueError(
                '`periods` values must be sorted in ascending order'
            )

    def serialize(self, data):
        """
        Write a sequence of uniform hazard spectra to the specified file.

        :param data:
            Iterable of UHS data. Each datum must be an object with the
            following attributes:

            * imls: A sequence of Itensity Measure Levels
            * location: An object representing the location of the curve; must
              have `x` and `y` to represent lon and lat, respectively.
        """
        gml_ns = openquake.nrmllib.SERIALIZE_NS_MAP['gml']

        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element(
                'nrml', nsmap=openquake.nrmllib.SERIALIZE_NS_MAP
            )

            uh_spectra = etree.SubElement(root, 'uniformHazardSpectra')

            _set_metadata(uh_spectra, self.metadata, _ATTR_MAP)

            periods_elem = etree.SubElement(uh_spectra, 'periods')
            periods_elem.text = ' '.join([str(x)
                                          for x in self.metadata['periods']])

            for uhs in data:
                uhs_elem = etree.SubElement(uh_spectra, 'uhs')
                gml_point = etree.SubElement(uhs_elem, '{%s}Point' % gml_ns)
                gml_pos = etree.SubElement(gml_point, '{%s}pos' % gml_ns)
                gml_pos.text = '%s %s' % (uhs.location.x, uhs.location.y)
                imls_elem = etree.SubElement(uhs_elem, 'IMLs')
                imls_elem.text = ' '.join([str(x) for x in uhs.imls])

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class SourceModelXMLWriter(object):
    """
    Writes source model XML from a given
    :class:`openquake.nrmllib.models.SourceModel`.

    This class is the writer counterpart to
    :class:`openquake.nrmllib.hazard.SourceModelParser`.

    :param dest:
        Path to the file or file-like object where we want to write the source
        model.
    """
    def __init__(self, dest):
        self.dest = dest

    @staticmethod
    def _coords_from_geom(wkt):
        """
        Get the coordinates points from a LINESTRING or POLYGON ``wkt`` string
        as a 2D list.

        The WKT parsing method was heavily inspired by GeoMet
        (https://github.com/larsbutler/geomet).

        This only works for simple shapes, and does not work for polygons with
        holes, etc.. Example:

        POLYGON ((35 10, 10 20, 15 40, 45 45, 35 10),
        (20 30, 35 35, 30 20, 20 30))
        """
        sio = StringIO.StringIO(wkt)

        tokens = (x[1] for x in tokenize.generate_tokens(sio.readline))
        geom_type = tokens.next()
        assert geom_type in ('POINT', 'LINESTRING', 'POLYGON')

        coords = []
        pt = []
        negative = False

        for t in tokens:
            if t == '(':
                continue
            elif t == ')':
                coords.append(pt)
                break
            elif t == ',':
                coords.append(pt)
                pt = []
            elif t == '-':
                negative = True
            else:
                if negative:
                    t = '-' + t
                pt.append(float(t))
                negative = False

        return coords

    def _append_mfd(self, elem, src):
        """
        Append a MFD element to the XML tree for a given ``src``.

        :param elem:
            A :class:`lxml.etree._Element`.
        :param src:
            One of the five source types defined in
            :mod:`openquake.nrmllib.models`.
        """
        if isinstance(src.mfd, models.IncrementalMFD):
            mfd = etree.SubElement(
                elem,
                'incrementalMFD',
                attrib=src.mfd.attrib
            )
            occ_rates = etree.SubElement(mfd, 'occurRates')
            occ_rates.text = ' '.join([str(x) for x in src.mfd.occur_rates])
        elif isinstance(src.mfd, models.TGRMFD):
            etree.SubElement(
                elem,
                'truncGutenbergRichterMFD',
                attrib=src.mfd.attrib
            )

    def _append_npd(self, elem, src):
        """
        Append a nodal plane disitribution element to the XML tree for a given
        ``src``.

        :param elem:
            A :class:`lxml.etree._Element`.
        :param src:
            One of the five source types defined in
            :mod:`openquake.nrmllib.models`.
        """
        npd = etree.SubElement(elem, 'nodalPlaneDist')
        for np in src.nodal_plane_dist:
            etree.SubElement(
                npd,
                'nodalPlane',
                attrib=np.attrib
            )

    def _append_hdd(self, elem, src):
        """
        Append a hypocentral depth distribution element to XML tree for a given
        ``src``.

        :param elem:
            A :class:`lxml.etree._Element`.
        :param src:
            One of the five source types defined in
            :mod:`openquake.nrmllib.models`.
        """
        hdd = etree.SubElement(elem, 'hypoDepthDist')
        for hd in src.hypo_depth_dist:
            etree.SubElement(
                hdd,
                'hypoDepth',
                attrib=hd.attrib
            )

    def _append_area(self, src_model_elem, src):
        """
        Append an area source element to the XML tree.

        :param src_model_elem:
            The :class:`lxml.etree._Element` representing the <sourceModel>
            element in the document.
        :param src:
            A :class:`openquake.nrmllib.models.AreaSource`.
        """
        area_elem = etree.SubElement(
            src_model_elem,
            'areaSource',
            attrib=src.attrib
        )

        # geometry
        area_geom_elem = etree.SubElement(area_elem, 'areaGeometry')
        poly = etree.SubElement(area_geom_elem, '{%s}Polygon' % GML_NS)
        exterior = etree.SubElement(poly, '{%s}exterior' % GML_NS)
        linearring = etree.SubElement(exterior, '{%s}LinearRing' % GML_NS)
        poslist = etree.SubElement(linearring, '{%s}posList' % GML_NS)
        coords = self._coords_from_geom(src.geometry.wkt)
        # Since the polygon froms a closed ring, but is not usually modeled as
        # such, remove the last vertex; in POLYGON WKT, we expect the last
        # vertex should be a duplicate of the first.
        coords.pop()
        poslist.text = ' '.join([' '.join([str(x) for x in pt])
                                 for pt in coords])
        upp_seis_depth = etree.SubElement(area_geom_elem, 'upperSeismoDepth')
        upp_seis_depth.text = str(src.geometry.upper_seismo_depth)
        low_seis_depth = etree.SubElement(area_geom_elem, 'lowerSeismoDepth')
        low_seis_depth.text = str(src.geometry.lower_seismo_depth)

        mag_scale_rel = etree.SubElement(area_elem, 'magScaleRel')
        mag_scale_rel.text = src.mag_scale_rel
        rar = etree.SubElement(area_elem, 'ruptAspectRatio')
        rar.text = str(src.rupt_aspect_ratio)

        self._append_mfd(area_elem, src)
        self._append_npd(area_elem, src)
        self._append_hdd(area_elem, src)

    def _append_point(self, src_model_elem, src):
        """
        Append a point source element to the source model XML tree.

        :param src_model_elem:
            The :class:`lxml.etree._Element` representing the <sourceModel>
            element in the document.
        :param src:
            A :class:`openquake.nrmllib.models.PointSource`.
        """
        pt_elem = etree.SubElement(
            src_model_elem,
            'pointSource',
            attrib=src.attrib
        )

        # geometry
        pt_geom_elem = etree.SubElement(pt_elem, 'pointGeometry')
        point = etree.SubElement(pt_geom_elem, '{%s}Point' % GML_NS)
        pos = etree.SubElement(point, '{%s}pos' % GML_NS)
        [coord] = self._coords_from_geom(src.geometry.wkt)
        pos.text = ' '.join([str(x) for x in coord])
        upp_seis_depth = etree.SubElement(pt_geom_elem, 'upperSeismoDepth')
        upp_seis_depth.text = str(src.geometry.upper_seismo_depth)
        low_seis_depth = etree.SubElement(pt_geom_elem, 'lowerSeismoDepth')
        low_seis_depth.text = str(src.geometry.lower_seismo_depth)

        mag_scale_rel = etree.SubElement(pt_elem, 'magScaleRel')
        mag_scale_rel.text = src.mag_scale_rel
        rar = etree.SubElement(pt_elem, 'ruptAspectRatio')
        rar.text = str(src.rupt_aspect_ratio)

        self._append_mfd(pt_elem, src)
        self._append_npd(pt_elem, src)
        self._append_hdd(pt_elem, src)

    def _append_fault_edge(self, edge_elem, wkt):
        """
        Append a <gml:LineString> geometry element to the given ``edge_elem``,
        where the geometry is defined by ``wkt``.

        :param elem:
            An instance of :class:`lxml.etree._Element`.
        :param str wkt:
            A LINESTRING represented as WKT.
        """
        linestring = etree.SubElement(edge_elem, '{%s}LineString' % GML_NS)
        poslist = etree.SubElement(linestring, '{%s}posList' % GML_NS)
        coords = self._coords_from_geom(wkt)
        poslist.text = ' '.join([' '.join([str(x) for x in pt])
                                 for pt in coords])

    def _append_simple_fault_geom(self, elem, geometry):
        """
        Append simple fault geometry elements to a given ``elem``.

        :param elem:
            An instance of :class:`lxml.etree._Element`.
        :param geometry:
            An instance of
            :class:`openquake.nrmllib.models.SimpleFaultGeometry`.
        """
        simple_geom = etree.SubElement(elem, 'simpleFaultGeometry')
        self._append_fault_edge(simple_geom, geometry.wkt)
        dip = etree.SubElement(simple_geom, 'dip')
        dip.text = str(geometry.dip)
        upp_seis_depth = etree.SubElement(simple_geom, 'upperSeismoDepth')
        upp_seis_depth.text = str(geometry.upper_seismo_depth)
        low_seis_depth = etree.SubElement(simple_geom, 'lowerSeismoDepth')
        low_seis_depth.text = str(geometry.lower_seismo_depth)

    def _append_complex_fault_geom(self, elem, geometry):
        """
        Append complex fault geometry elements to a given ``elem``.

        :param elem:
            An instance of :class:`lxml.etree._Element`.
        :param geometry:
            An instance of
            :class:`openquake.nrmllib.models.ComplexFaultGeometry`.
        """
        complex_geom = etree.SubElement(elem, 'complexFaultGeometry')
        # top edge
        top_edge = etree.SubElement(complex_geom, 'faultTopEdge')
        self._append_fault_edge(top_edge, geometry.top_edge_wkt)
        # intermedate edges
        for edge in geometry.int_edges:
            edge_elem = etree.SubElement(complex_geom, 'intermediateEdge')
            self._append_fault_edge(edge_elem, edge)
        # bottom edge
        bottom_edge = etree.SubElement(complex_geom, 'faultBottomEdge')
        self._append_fault_edge(bottom_edge, geometry.bottom_edge_wkt)

    def _append_complex(self, src_model_elem, src):
        """
        Append a complex fault source element to the source model XML tree.

        :param src_model_elem:
            The :class:`lxml.etree._Element` representing the <sourceModel>
            element in the document.
        :param src:
            A :class:`openquake.nrmllib.models.ComplexFaultSource`.
        """
        complex_elem = etree.SubElement(
            src_model_elem,
            'complexFaultSource',
            attrib=src.attrib
        )

        # geometry
        self._append_complex_fault_geom(complex_elem, src.geometry)

        mag_scale_rel = etree.SubElement(complex_elem, 'magScaleRel')
        mag_scale_rel.text = src.mag_scale_rel
        rar = etree.SubElement(complex_elem, 'ruptAspectRatio')
        rar.text = str(src.rupt_aspect_ratio)

        self._append_mfd(complex_elem, src)
        rake = etree.SubElement(complex_elem, 'rake')
        rake.text = str(src.rake)

    def _append_simple(self, src_model_elem, src):
        """
        Append a simple fault source element to the source model XML tree.

        :param src_model_elem:
            The :class:`lxml.etree._Element` representing the <sourceModel>
            element in the document.
        :param src:
            A :class:`openquake.nrmllib.models.SimpleFaultSource`.
        """
        simple_elem = etree.SubElement(
            src_model_elem,
            'simpleFaultSource',
            attrib=src.attrib
        )

        # geometry
        self._append_simple_fault_geom(simple_elem, src.geometry)

        mag_scale_rel = etree.SubElement(simple_elem, 'magScaleRel')
        mag_scale_rel.text = src.mag_scale_rel
        rar = etree.SubElement(simple_elem, 'ruptAspectRatio')
        rar.text = str(src.rupt_aspect_ratio)

        self._append_mfd(simple_elem, src)

        rake = etree.SubElement(simple_elem, 'rake')
        rake.text = str(src.rake)

    def _append_characteristic(self, src_model_elem, src):
        """
        Append a characteristic fault source to the source model XML tree.

        Characteristic fault source geometries can be represented either by a
        simple fault geometry, a complex fault geometry, or a collection of
        planar surfaces.

        :param src_model_elem:
            The :class:`lxml.etree._Element` representing the <sourceModel>
            element in the document.
        :param src:
            A :class:`openquake.nrmllib.models.CharacteristicSource`.
        """
        char_elem = etree.SubElement(
            src_model_elem,
            'characteristicFaultSource',
            attrib=src.attrib
        )

        self._append_mfd(char_elem, src)
        rake = etree.SubElement(char_elem, 'rake')
        rake.text = str(src.rake)

        # TODO: <surface>...</surface>
        surface = etree.SubElement(char_elem, 'surface')

        if isinstance(src.surface, models.ComplexFaultGeometry):
            self._append_complex_fault_geom(surface, src.surface)
        elif isinstance(src.surface, models.SimpleFaultGeometry):
            self._append_simple_fault_geom(surface, src.surface)
        else:
            for planar_surface in src.surface:
                ps_elem = etree.SubElement(surface, 'planarSurface')
                ps_elem.set('strike', str(planar_surface.strike))
                ps_elem.set('dip', str(planar_surface.dip))

                for el_name, corner in (
                        ('topLeft', planar_surface.top_left),
                        ('topRight', planar_surface.top_right),
                        ('bottomLeft', planar_surface.bottom_left),
                        ('bottomRight', planar_surface.bottom_right)):

                    corner_elem = etree.SubElement(ps_elem, el_name)
                    corner_elem.set('lon', str(corner.longitude))
                    corner_elem.set('lat', str(corner.latitude))
                    corner_elem.set('depth', str(corner.depth))

    def serialize(self, src_model):
        """
        Write a source model to the target file.

        :param src_model:
            A :class:`openquake.nrmllib.models.SourceModel` object, which is an
            iterable collection of sources.
        """
        with NRMLFile(self.dest, 'w') as fh:
            root = etree.Element(
                'nrml', nsmap=openquake.nrmllib.SERIALIZE_NS_MAP
            )

            src_model_elem = etree.SubElement(root, 'sourceModel')
            if src_model.name is not None:
                src_model_elem.set('name', src_model.name)

            for src in src_model:
                if isinstance(src, models.AreaSource):
                    self._append_area(src_model_elem, src)
                elif isinstance(src, models.PointSource):
                    self._append_point(src_model_elem, src)
                elif isinstance(src, models.ComplexFaultSource):
                    self._append_complex(src_model_elem, src)
                elif isinstance(src, models.SimpleFaultSource):
                    self._append_simple(src_model_elem, src)
                elif isinstance(src, models.CharacteristicSource):
                    self._append_characteristic(src_model_elem, src)

            fh.write(etree.tostring(root, pretty_print=True,
                                    xml_declaration=True, encoding='UTF-8'))
