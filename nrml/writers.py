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
                hazard_curves.set('sourceModelTreePath', self.smlt_path)
            if self.gsimlt_path is not None:
                hazard_curves.set('gsimTreePath', self.gsimlt_path)
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
            gmf_coll_elem.set('sourceModelTreePath', self.sm_lt_path)
            gmf_coll_elem.set('gsimTreePath', self.gsim_lt_path)

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
