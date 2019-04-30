# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Classes for serializing various NRML XML artifacts.
"""
import operator

import numpy

from xml.etree import ElementTree as et

from openquake.baselib.node import Node, scientificformat, floatformat
from openquake.hazardlib import nrml

by_imt = operator.itemgetter('imt', 'sa_period', 'sa_damping')

SM_TREE_PATH = 'sourceModelTreePath'
GSIM_TREE_PATH = 'gsimTreePath'

#: Maps XML writer constructor keywords to XML attribute names
_ATTR_MAP = dict([
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

GML_NS = nrml.SERIALIZE_NS_MAP['gml']


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
    if (md.get('statistics') is not None and (
            md.get('smlt_path') is not None or
            md.get('gsimlt_path') is not None)):
        raise ValueError('Cannot specify both `statistics` and logic tree '
                         'paths')

    if md.get('statistics') is not None:
        # make sure only valid statistics types are specified
        if md.get('statistics') not in ('mean', 'max', 'quantile', 'std'):
            raise ValueError('`statistics` must be either `mean`, `max`, or '
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
        :class:`xml.etree.ElementTree.Element` instance
    :param metadata:
        Dictionary of metadata items containing attribute data for ``element``.
    :param attr_map:
        Dictionary mapping of metadata key->attribute name.
    :param transform:
        A function accepting and returning a single value to be applied to each
        attribute value. Defaults to `str`.
    """
    for kw, attr in attr_map.items():
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
        with open(self.dest, 'wb') as fh:
            root = et.Element('nrml')
            self.add_hazard_curves(root, self.metadata, data)
            nrml.write(list(root), fh)

    def add_hazard_curves(self, root, metadata, data):
        """
        Add hazard curves stored into `data` as child of the `root`
        element with `metadata`. See the documentation of the method
        `serialize` and the constructor for a description of `data`
        and `metadata`, respectively.
        """
        hazard_curves = et.SubElement(root, 'hazardCurves')

        _set_metadata(hazard_curves, metadata, _ATTR_MAP)

        imls_elem = et.SubElement(hazard_curves, 'IMLs')
        imls_elem.text = ' '.join(map(scientificformat, metadata['imls']))
        gml_ns = nrml.SERIALIZE_NS_MAP['gml']

        for hc in data:
            hc_elem = et.SubElement(hazard_curves, 'hazardCurve')
            gml_point = et.SubElement(hc_elem, '{%s}Point' % gml_ns)
            gml_pos = et.SubElement(gml_point, '{%s}pos' % gml_ns)
            gml_pos.text = '%s %s' % (hc.location.x, hc.location.y)
            poes_elem = et.SubElement(hc_elem, 'poEs')
            poes_elem.text = ' '.join(map(scientificformat, hc.poes))


def gen_gmfs(gmf_set):
    """
    Generate GMF nodes from a gmf_set
    :param gmf_set: a sequence of GMF objects with attributes
    imt, sa_period, sa_damping, event_id and containing a list
    of GMF nodes with attributes gmv and location. The nodes
    are sorted by lon/lat.
    """
    for gmf in gmf_set:
        gmf_node = Node('gmf')
        gmf_node['IMT'] = gmf.imt
        if gmf.imt == 'SA':
            gmf_node['saPeriod'] = str(gmf.sa_period)
            gmf_node['saDamping'] = str(gmf.sa_damping)
        gmf_node['ruptureId'] = gmf.event_id
        sorted_nodes = sorted(gmf)
        gmf_node.nodes = (
            Node('node', dict(gmv=n.gmv, lon=n.location.x, lat=n.location.y))
            for n in sorted_nodes)
        yield gmf_node


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

    # we want at least 1+7 digits of precision
    def serialize(self, data, fmt='%10.7E'):
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
            * have a `event_id` attribute (to indicate which rupture
              contributed to this gmf)
            * be iterable, yielding a sequence of "GMF node" objects

            Each "GMF node" object should have:

            * a `gmv` attribute (to indicate the ground motion value
            * `lon` and `lat` attributes (to indicate the geographical location
              of the ground motion field)
        """
        gmf_set_nodes = []
        for gmf_set in data:
            gmf_set_node = Node('gmfSet')
            if gmf_set.investigation_time:
                gmf_set_node['investigationTime'] = str(
                    gmf_set.investigation_time)
            gmf_set_node['stochasticEventSetId'] = str(
                gmf_set.stochastic_event_set_id)
            gmf_set_node.nodes = gen_gmfs(gmf_set)
            gmf_set_nodes.append(gmf_set_node)

        gmf_container = Node('gmfCollection')
        gmf_container[SM_TREE_PATH] = self.sm_lt_path
        gmf_container[GSIM_TREE_PATH] = self.gsim_lt_path
        gmf_container.nodes = gmf_set_nodes

        with open(self.dest, 'wb') as dest:
            nrml.write([gmf_container], dest, fmt)


def sub_elems(elem, rup, *names):
    for name in names:
        et.SubElement(elem, name).text = '%.7e' % getattr(rup, name)


def rupture_to_element(rup, parent=None):
    """
    Convert a rupture object into an Element object.

    :param rup:
        must have attributes .rupid, .events_by_ses and .seed
    :param parent:
         parent of the returned element, or None
    """
    if parent is None:
        parent = et.Element('root')
    rup_elem = et.SubElement(parent, rup.typology)
    elem = et.SubElement(rup_elem, 'stochasticEventSets')
    n = 0
    for ses in rup.events_by_ses:
        eids = rup.events_by_ses[ses]['id']
        n += len(eids)
        ses_elem = et.SubElement(elem, 'SES', id=ses)
        ses_elem.text = ' '.join(str(eid) for eid in eids)
    rup_elem.set('id', rup.rupid)
    rup_elem.set('multiplicity', str(n))
    sub_elems(rup_elem, rup, 'magnitude',  'strike', 'dip', 'rake')
    h = rup.hypocenter
    et.SubElement(rup_elem, 'hypocenter', dict(lon=h.x, lat=h.y, depth=h.z))
    if rup.is_from_fault_source:
        # rup is from a simple or complex fault source
        # the rup geometry is represented by a mesh of 3D
        # points
        mesh_elem = et.SubElement(rup_elem, 'mesh')

        # we assume the mesh components (lons, lats, depths)
        # are of uniform shape
        for i, row in enumerate(rup.lons):
            for j, col in enumerate(row):
                node_elem = et.SubElement(mesh_elem, 'node')
                node_elem.set('row', str(i))
                node_elem.set('col', str(j))
                node_elem.set('lon', str(rup.lons[i][j]))
                node_elem.set('lat', str(rup.lats[i][j]))
                node_elem.set('depth', str(rup.depths[i][j]))

        # if we never entered the loop above, it's possible
        # that i and j will be undefined
        mesh_elem.set('rows', str(i + 1))
        mesh_elem.set('cols', str(j + 1))
    elif rup.is_gridded_surface:
        # the rup geometry is represented by a mesh of (1, N) points
        mesh_elem = et.SubElement(rup_elem, 'mesh')
        for j, _ in enumerate(rup.lons):
            node_elem = et.SubElement(mesh_elem, 'node')
            node_elem.set('row', '0')
            node_elem.set('col', str(j))
            node_elem.set('lon', str(rup.lons[j]))
            node_elem.set('lat', str(rup.lats[j]))
            node_elem.set('depth', str(rup.depths[j]))
    else:
        # rupture is from a multi surface fault source
        if rup.is_multi_surface:
            # the arrays lons, lats and depths contain 4*N elements,
            # where N is the number of planar surfaces contained in the
            # multisurface; each planar surface if characterised by 4
            # vertices top_left, top_right, bottom_left, bottom_right
            assert len(rup.lons) % 4 == 0
            assert len(rup.lons) == len(rup.lats) == len(rup.depths)

            for offset in range(len(rup.lons) // 4):
                # looping on the coordinates of the sub surfaces, one
                # planar surface at the time
                start = offset * 4
                end = offset * 4 + 4
                lons = rup.lons[start:end]  # 4 lons of the current surface
                lats = rup.lats[start:end]  # 4 lats of the current surface
                depths = rup.depths[start:end]  # 4 depths

                ps_elem = et.SubElement(
                    rup_elem, 'planarSurface')

                top_left, top_right, bottom_left, bottom_right = \
                    zip(lons, lats, depths)

                for el_name, corner in (
                        ('topLeft', top_left),
                        ('topRight', top_right),
                        ('bottomLeft', bottom_left),
                        ('bottomRight', bottom_right)):

                    corner_elem = et.SubElement(ps_elem, el_name)
                    corner_elem.set('lon', '%.7f' % corner[0])
                    corner_elem.set('lat', '%.7f' % corner[1])
                    corner_elem.set('depth', '%.7f' % corner[2])
        else:
            # rupture is from a point or area source
            # the rupture geometry is represented by four 3D
            # corner points
            ps_elem = et.SubElement(rup_elem, 'planarSurface')

            # create the corner point elements, in the order of:
            # * top left
            # * top right
            # * bottom left
            # * bottom right
            for el_name, corner in (
                    ('topLeft', rup.top_left_corner),
                    ('topRight', rup.top_right_corner),
                    ('bottomLeft', rup.bottom_left_corner),
                    ('bottomRight', rup.bottom_right_corner)):

                corner_elem = et.SubElement(ps_elem, el_name)
                corner_elem.set('lon', '%.7f' % corner[0])
                corner_elem.set('lat', '%.7f' % corner[1])
                corner_elem.set('depth', '%.7f' % corner[2])
    return parent


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
    def __init__(self, dest):
        self.dest = dest

    def serialize(self, data, investigation_time):
        """
        Serialize a collection of stochastic event sets to XML.

        :param data:
            A dictionary src_group_id -> list of
            :class:`openquake.commonlib.calc.Rupture` objects.
            Each Rupture should have the following attributes:

            * `rupid`
            * `events_by_ses`
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

        :param investigation_time:
            Investigation time parameter specified in the job.ini
        """
        with open(self.dest, 'wb') as fh:
            root = et.Element('nrml')
            ses_container = et.SubElement(root, 'ruptureCollection')
            ses_container.set('investigationTime', str(investigation_time))
            for grp_id in sorted(data):
                attrs = dict(
                    id=grp_id,
                    tectonicRegion=data[grp_id][0].tectonic_region_type)
                sg = et.SubElement(ses_container, 'ruptureGroup', attrs)
                for rupture in data[grp_id]:
                    rupture_to_element(rupture, sg)
            nrml.write(list(root), fh)


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
        with open(self.dest, 'wb') as fh:
            root = et.Element('nrml')
            hazard_map = et.SubElement(root, 'hazardMap')
            _set_metadata(hazard_map, self.metadata, _ATTR_MAP)

            for lon, lat, iml in data:
                node = et.SubElement(hazard_map, 'node')
                node.set('lon', str(lon))
                node.set('lat', str(lat))
                node.set('iml', str(iml))

            nrml.write(list(root), fh)


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

        * sa_period
        * sa_damping
    """

    #: Maps metadata keywords to XML attribute names for bin edge information
    #: passed to the constructor.
    BIN_EDGE_ATTR_MAP = dict([
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

        with open(self.dest, 'wb') as fh, floatformat('%.6E'):
            root = et.Element('nrml')

            diss_matrices = et.SubElement(root, 'disaggMatrices')

            _set_metadata(diss_matrices, self.metadata, _ATTR_MAP)

            transform = lambda val: ', '.join(map(scientificformat, val))
            _set_metadata(diss_matrices, self.metadata, self.BIN_EDGE_ATTR_MAP,
                          transform=transform)

            for result in data:
                diss_matrix = et.SubElement(diss_matrices, 'disaggMatrix')

                # Check that we have bin edges defined for each dimension label
                # (mag, dist, lon, lat, eps, TRT)
                for label in result.dim_labels:
                    bin_edge_attr = self.DIM_LABEL_TO_BIN_EDGE_MAP.get(label)
                    assert self.metadata.get(bin_edge_attr) is not None, (
                        "Writer is missing '%s' metadata" % bin_edge_attr
                    )

                result_type = ','.join(result.dim_labels)
                diss_matrix.set('type', result_type)

                dims = ','.join(str(x) for x in result.matrix.shape)
                diss_matrix.set('dims', dims)

                diss_matrix.set('poE', scientificformat(result.poe))
                diss_matrix.set('iml', scientificformat(result.iml))

                for idxs, value in numpy.ndenumerate(result.matrix):
                    prob = et.SubElement(diss_matrix, 'prob')

                    index = ','.join([str(x) for x in idxs])
                    prob.set('index', index)
                    prob.set('value', scientificformat(value))

            nrml.write(list(root), fh)


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
        super().__init__(dest, **metadata)

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

            * imls: A sequence of Intensity Measure Levels
            * location: An object representing the location of the curve; must
              have `x` and `y` to represent lon and lat, respectively.
        """
        gml_ns = nrml.SERIALIZE_NS_MAP['gml']

        with open(self.dest, 'wb') as fh:
            root = et.Element('nrml')

            uh_spectra = et.SubElement(root, 'uniformHazardSpectra')

            _set_metadata(uh_spectra, self.metadata, _ATTR_MAP)

            periods_elem = et.SubElement(uh_spectra, 'periods')
            periods_elem.text = ' '.join([str(x)
                                          for x in self.metadata['periods']])

            for uhs in data:
                uhs_elem = et.SubElement(uh_spectra, 'uhs')
                gml_point = et.SubElement(uhs_elem, '{%s}Point' % gml_ns)
                gml_pos = et.SubElement(gml_point, '{%s}pos' % gml_ns)
                gml_pos.text = '%s %s' % (uhs.location.x, uhs.location.y)
                imls_elem = et.SubElement(uhs_elem, 'IMLs')
                imls_elem.text = ' '.join(['%10.7E' % x for x in uhs.imls])

            nrml.write(list(root), fh)
