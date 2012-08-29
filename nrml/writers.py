# Copyright (c) 2010-2012, GEM Foundation.
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

import nrml

from lxml import etree

SM_TREE_PATH = 'sourceModelTreePath'
GSIM_TREE_PATH = 'gsimTreePath'


class HazardCurveXMLWriter(object):
    """
    :param path:
        File path (including filename) for XML results to be saved to.
    :param float investigation_time:
        Investigation time (in years) defined in the calculation which produced
        these results.
    :param str imt:
        Intensity measure type used to compute these hazard curves.
    :param list imls:
        Intensity measure levels, which represent the x-axis values of each
        curve.
    :param metadata:
        A combination of the following keyword arguments:

        * statistics: 'mean' or 'quantile'
        * quantile_value: Only required if statistics = 'quantile'.
        * smlt_path: String representing the logic tree path which produced
          these curves. Only required for non-statistical curves.
        * gsimlt_path: String represeting the GSIM logic tree path which
          produced these curves. Only required for non-statisical curves.
        * sa_period: Only used with imt = 'SA'.
        * sa_damping: Only used with imt = 'SA'.
    """

    def __init__(self, path, investigation_time, imt, imls, **metadata):
        self.path = path
        self.investigation_time = investigation_time
        self.imt = imt
        self.imls = imls

        self.statistics = metadata.get('statistics')
        self.quantile_value = metadata.get('quantile_value')
        self.smlt_path = metadata.get('smlt_path')
        self.gsimlt_path = metadata.get('gsimlt_path')
        self.sa_period = metadata.get('sa_period')
        self.sa_damping = metadata.get('sa_damping')

    def validate_metadata(self):
        """
        Validate the hazard curve collection metadata to ensure that meaningful
        results are serialized.

        :raises:
            :exc:`ValueError` if the metadata is not valid.
        """
        if (self.statistics is not None
            and (self.smlt_path is not None or self.gsimlt_path is not None)):
            raise ValueError('Cannot specify both `statistics` and logic tree '
                             'paths')

        if self.statistics is None:
            # must specify both logic tree paths
            if self.smlt_path is None or self.gsimlt_path is None:
                raise ValueError('Both logic tree paths are required for '
                                 'non-statistical results')
        else:
            if self.statistics not in ('mean', 'quantile'):
                raise ValueError('`statistics` must be either `mean` or '
                                 '`quantile`')

        if self.statistics == 'quantile':
            if self.quantile_value is None:
                raise ValueError('quantile stastics results require a quantile'
                                 ' value to be specified')

        if not self.statistics == 'quantile':
            if self.quantile_value is not None:
                raise ValueError('Quantile value must be specified with '
                                 'quantile statistics')

        if self.imt == 'SA':
            if self.sa_period is None:
                raise ValueError('`sa_period` is required for IMT == `SA`')
            if self.sa_damping is None:
                raise ValueError('`sa_damping` is required for IMT == `SA`')

    def serialize(self, data):
        """
        Write a sequence of hazard curves to the specified file.

        Metadata is validated before curve data is written.

        :param data:
            Iterable of hazard curve data. Each datum must be an object with
            the following attributes:

            * poes: A list of probability of exceedence values (floats).
            * location: An object representing the location of the curve; must
              have `x` and `y` to represent lon and lat, respectively.
        """
        self.validate_metadata()

        gml_ns = nrml.SERIALIZE_NS_MAP['gml']

        with open(self.path, 'w') as fh:
            root = etree.Element('nrml', nsmap=nrml.SERIALIZE_NS_MAP)

            hazard_curves = etree.SubElement(root, 'hazardCurves')

            # set metadata attributes
            hazard_curves.set('IMT', str(self.imt))
            hazard_curves.set('investigationTime',
                              str(self.investigation_time))
            if self.statistics is not None:
                hazard_curves.set('statistics', self.statistics)
            if self.quantile_value is not None:
                hazard_curves.set('quantileValue', str(self.quantile_value))
            if self.smlt_path is not None:
                hazard_curves.set(SM_TREE_PATH, self.smlt_path)
            if self.gsimlt_path is not None:
                hazard_curves.set(GSIM_TREE_PATH, self.gsimlt_path)
            if self.sa_period is not None:
                hazard_curves.set('saPeriod', str(self.sa_period))
            if self.sa_damping is not None:
                hazard_curves.set('saDamping', str(self.sa_damping))

            imls_elem = etree.SubElement(hazard_curves, 'IMLs')
            imls_elem.text = ' '.join([str(x) for x in self.imls])

            for hc in data:
                hc_elem = etree.SubElement(hazard_curves, 'hazardCurve')
                gml_point = etree.SubElement(hc_elem, '{%s}Point' % gml_ns)
                gml_pos = etree.SubElement(gml_point, '{%s}pos' % gml_ns)
                gml_pos.text = '%s %s' % (hc.location.x, hc.location.y)
                poes_elem = etree.SubElement(hc_elem, 'poEs')
                poes_elem.text = ' '.join([str(x) for x in hc.poes])

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class EventBasedGMFXMLWriter(object):
    """
    :param str path:
        File path (including filename) for XML results to be saved to.
    :param str sm_lt_path:
        Source model logic tree branch identifier of the logic tree realization
        which produced this collection of ground motion fields.
    :param gsim_lt_path:
        GSIM logic tree branch identifier of the logic tree realization which
        produced this collection of ground motion fields.
    """

    def __init__(self, path, sm_lt_path, gsim_lt_path):
        self.path = path
        self.sm_lt_path = sm_lt_path
        self.gsim_lt_path = gsim_lt_path

    def serialize(self, data):
        """
        Serialize a collection of ground motion fields to XML.

        :param data:
            An iterable of "GMF set" objects.
            Each "GMF set" object should:

            * have an `investigation_time` attribute
            * be iterable, yielding a sequence of "GMF" objects

            Each "GMF" object should:

            * have an `imt` attribute
            * have an `sa_period` attribute (only if `imt` is 'SA')
            * have an `sa_damping` attribute (only if `imt` is 'SA')
            * be iterable, yielding a sequence of "GMF node" objects

            Each "GMF node" object should have:

            * an `iml` attribute (to indicate the ground motion value
            * `lon` and `lat` attributes (to indicate the geographical location
              of the ground motion field
        """
        with open(self.path, 'w') as fh:
            root = etree.Element('nrml', nsmap=nrml.SERIALIZE_NS_MAP)

            gmf_coll_elem = etree.SubElement(root, 'gmfCollection')
            gmf_coll_elem.set(SM_TREE_PATH, self.sm_lt_path)
            gmf_coll_elem.set(GSIM_TREE_PATH, self.gsim_lt_path)

            for gmf_set in data:
                gmf_set_elem = etree.SubElement(gmf_coll_elem, 'gmfSet')
                gmf_set_elem.set(
                    'investigationTime', str(gmf_set.investigation_time))

                for gmf in gmf_set:
                    gmf_elem = etree.SubElement(gmf_set_elem, 'gmf')
                    gmf_elem.set('IMT', gmf.imt)
                    if gmf.imt == 'SA':
                        gmf_elem.set('saPeriod', str(gmf.sa_period))
                        gmf_elem.set('saDamping', str(gmf.sa_damping))

                    for gmf_node in gmf:
                        node_elem = etree.SubElement(gmf_elem, 'node')
                        node_elem.set('iml', str(gmf_node.iml))
                        node_elem.set('lon', str(gmf_node.location.x))
                        node_elem.set('lat', str(gmf_node.location.y))

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))


class SESXMLWriter(object):
    """
    :param str path:
        File path (including filename) for XML results to be saved to.
    :param str sm_lt_path:
        Source model logic tree branch identifier of the logic tree realization
        which produced this collection of stochastic event sets.
    :param gsim_lt_path:
        GSIM logic tree branch identifier of the logic tree realization which
        produced this collection of stochastic event sets.
    """

    def __init__(self, path, sm_lt_path, gsim_lt_path):
        self.path = path
        self.sm_lt_path = sm_lt_path
        self.gsim_lt_path = gsim_lt_path

    def serialize(self, data):
        """
        Serialize a collection of stochastic event sets to XML.

        :param data:
            An iterable of "SES" ("Stochastic Event Set") objects.
            Each "SES" object should:

            * have an `investigation_time` attribute
            * be iterable, yielding a sequence of "rupture" objects

            Each "rupture" should have the following attributes:
            * `magnitude`
            * `strike`
            * `dip`
            * `rake`
            * `tectonic_region_type`
            * `is_from_fault_source` (a `bool`)
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
        """
        with open(self.path, 'w') as fh:
            root = etree.Element('nrml', nsmap=nrml.SERIALIZE_NS_MAP)

            if self.sm_lt_path is not None and self.gsim_lt_path is not None:
                # A normal stochastic event set collection
                ses_coll_elem = etree.SubElement(
                    root, 'stochasticEventSetCollection')

                ses_coll_elem.set(SM_TREE_PATH, self.sm_lt_path)
                ses_coll_elem.set(GSIM_TREE_PATH, self.gsim_lt_path)
            else:
                # A stochastic event set collection for the complete logic tree
                ses_coll_elem = etree.SubElement(
                    root, 'completeLogicTreeStochasticEventSetCollection')

            for ses in data:
                ses_elem = etree.SubElement(
                    ses_coll_elem, 'stochasticEventSet')
                ses_elem.set('investigationTime', str(ses.investigation_time))

                for rupture in ses:
                    rup_elem = etree.SubElement(ses_elem, 'rupture')
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
                        # rupture is from a point or area source
                        # the rupture geometry is represented by four 3D corner
                        # points
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
        # * bottom right
        # * bottom left
        for el_name, corner in (
            ('topLeft', rupture.top_left_corner),
            ('topRight', rupture.top_right_corner),
            ('bottomRight', rupture.bottom_right_corner),
            ('bottomLeft', rupture.bottom_left_corner)):

            corner_elem = etree.SubElement(ps_elem, el_name)
            corner_elem.set('lon', str(corner[0]))
            corner_elem.set('lat', str(corner[1]))
            corner_elem.set('depths', str(corner[2]))
