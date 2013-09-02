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


"""These parsers read NRML XML files and produce object representations of the
data.

See :module:`openquake.nrmllib.models`.
"""

import decimal
import warnings
from collections import OrderedDict

from lxml import etree

import openquake.nrmllib

from openquake.nrmllib import models
from openquake.nrmllib import utils


def _xpath(elem, expr):
    """Helper function for executing xpath queries on an XML element. This
    function uses the default mapping of namespaces (which includes NRML and
    GML).

    :param str expr:
        XPath expression.
    :param elem:
        A :class:`lxml.etree._Element` instance.
    """
    return elem.xpath(expr, namespaces=openquake.nrmllib.PARSE_NS_MAP)


class FaultGeometryParserMixin(object):
    """
    Mixin with methods _parse_simple_geometry and _parse_complex_geometry.
    """

    @classmethod
    def _parse_simple_geometry(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a geometry.
        :returns:
            Fully populated
            :class:`openquake.nrmllib.models.SimpleFaultGeometry` object.
        """
        simple_geom = models.SimpleFaultGeometry()

        [gml_pos_list] = _xpath(src_elem, './/gml:posList')
        coords = gml_pos_list.text.split()
        simple_geom.wkt = utils.coords_to_linestr_wkt(coords, 2)

        simple_geom.dip = float(
            _xpath(src_elem, './/nrml:dip')[0].text)
        simple_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        simple_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        return simple_geom

    @classmethod
    def _parse_complex_geometry(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a geometry.
        :returns:
            Fully populated
            :class:`openquake.nrmllib.models.ComplexFaultGeometry` object.
        """
        complex_geom = models.ComplexFaultGeometry()

        [top_edge] = _xpath(src_elem, './/nrml:faultTopEdge//gml:posList')
        top_coords = top_edge.text.split()
        complex_geom.top_edge_wkt = utils.coords_to_linestr_wkt(top_coords, 3)

        [bottom_edge] = _xpath(
            src_elem, './/nrml:faultBottomEdge//gml:posList')
        bottom_coords = bottom_edge.text.split()
        complex_geom.bottom_edge_wkt = utils.coords_to_linestr_wkt(
            bottom_coords, 3)

        # Optional itermediate edges:
        int_edges = _xpath(src_elem, './/nrml:intermediateEdge//gml:posList')
        for edge in int_edges:
            coords = edge.text.split()
            complex_geom.int_edges.append(
                utils.coords_to_linestr_wkt(coords, 3))

        return complex_geom

    @classmethod
    def _parse_planar_surface(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a
            <planarSurface>.
        :returns:
            Fully populated
            :class:`openquake.nrmllib.models.PlanarSurface` object.
        """
        surface = models.PlanarSurface()
        surface.strike = float(src_elem.get('strike'))
        surface.dip = float(src_elem.get('dip'))
        surface.top_left = cls._parse_point_geom(
            _xpath(src_elem, './nrml:topLeft')[0]
        )
        surface.top_right = cls._parse_point_geom(
            _xpath(src_elem, './nrml:topRight')[0]
        )
        surface.bottom_left = cls._parse_point_geom(
            _xpath(src_elem, './nrml:bottomLeft')[0]
        )
        surface.bottom_right = cls._parse_point_geom(
            _xpath(src_elem, './nrml:bottomRight')[0]
        )
        return surface

    @classmethod
    def _parse_point_geom(cls, elem):
        """
        :param elem:
            :class:`lxml.etree._Element` instance representing an element
            with the following attributes:
                * `lon`
                * `lat`
                * `depth`
        :returns:
            A fully populated :class:`openquake.nrmllib.models.Point` object.
        """
        pt = models.Point()
        pt.longitude = float(elem.get('lon'))
        pt.latitude = float(elem.get('lat'))
        pt.depth = float(elem.get('depth'))

        return pt


class SourceModelParser(FaultGeometryParserMixin):
    """NRML source model parser. Reads point sources, area sources, simple
    fault sources, characteristic fault sources, and complex fault sources
    from a given source.

    :param source:
        Filename or file-like object containing the XML data.
    """

    _SM_TAG = '{%s}sourceModel' % openquake.nrmllib.NAMESPACE
    _PT_TAG = '{%s}pointSource' % openquake.nrmllib.NAMESPACE
    _AREA_TAG = '{%s}areaSource' % openquake.nrmllib.NAMESPACE
    _SIMPLE_TAG = '{%s}simpleFaultSource' % openquake.nrmllib.NAMESPACE
    _COMPLEX_TAG = '{%s}complexFaultSource' % openquake.nrmllib.NAMESPACE
    _CHAR_TAG = '{%s}characteristicFaultSource' % openquake.nrmllib.NAMESPACE

    def __init__(self, source):
        self.source = source
        self._parse_fn_map = {
            self._PT_TAG: self._parse_point_source,
            self._AREA_TAG: self._parse_area,
            self._SIMPLE_TAG: self._parse_simple,
            self._COMPLEX_TAG: self._parse_complex,
            self._CHAR_TAG: self._parse_characteristic,
        }

    def _source_gen(self, tree):
        """Returns a generator which yields source model objects."""
        for event, element in tree:
            # We only want to parse data from the 'end' tag, otherwise there is
            # no guarantee the data will actually be present. We've run into
            # this issue in the past. See http://bit.ly/lxmlendevent for a
            # detailed description of the issue.
            if event == 'end':
                parse_fn = self._parse_fn_map.get(element.tag, None)
                if parse_fn is not None:
                    yield parse_fn(element)
                    element.clear()
                    while element.getprevious() is not None:
                        # Delete previous sibling elements.
                        # We need to loop here in case there are comments in
                        # the input file which are considered siblings to
                        # source elements.
                        del element.getparent()[0]

    @classmethod
    def _set_common_attrs(cls, model, src_elem):
        """Given a source object and a source XML element, set common
        attributes on the model, such as id, name, trt, mag_scale_rel, and
        rupt_aspect_ratio.

        :param model:
            Instance of a source class from :module:`openquake.nrmllib.models`.
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        """
        model.id = src_elem.get('id')
        model.name = src_elem.get('name')
        model.trt = src_elem.get('tectonicRegion')

        model.mag_scale_rel = _xpath(
            src_elem, './nrml:magScaleRel')[0].text.strip()
        model.rupt_aspect_ratio = float(_xpath(
            src_elem, './nrml:ruptAspectRatio')[0].text)

    @classmethod
    def _parse_mfd(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        """
        [mfd_elem] = _xpath(src_elem, ('.//nrml:truncGutenbergRichterMFD | '
                                       './/nrml:incrementalMFD'))

        if mfd_elem.tag == '{%s}truncGutenbergRichterMFD' % (
                openquake.nrmllib.NAMESPACE):
            mfd = models.TGRMFD()
            mfd.a_val = float(mfd_elem.get('aValue'))
            mfd.b_val = float(mfd_elem.get('bValue'))
            mfd.min_mag = float(mfd_elem.get('minMag'))
            mfd.max_mag = float(mfd_elem.get('maxMag'))

        elif mfd_elem.tag == '{%s}incrementalMFD' % (
                openquake.nrmllib.NAMESPACE):
            mfd = models.IncrementalMFD()
            mfd.min_mag = float(mfd_elem.get('minMag'))
            mfd.bin_width = float(mfd_elem.get('binWidth'))

            [occur_rates] = _xpath(mfd_elem, './nrml:occurRates')
            mfd.occur_rates = [float(x) for x in occur_rates.text.split()]

        return mfd

    @classmethod
    def _parse_nodal_plane_dist(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            `list` of :class:`openquake.nrmllib.models.NodalPlane` objects.
        """
        npd = []

        for elem in _xpath(src_elem, './/nrml:nodalPlane'):
            nplane = models.NodalPlane()
            nplane.probability = decimal.Decimal(elem.get('probability'))
            nplane.strike = float(elem.get('strike'))
            nplane.dip = float(elem.get('dip'))
            nplane.rake = float(elem.get('rake'))

            npd.append(nplane)

        return npd

    @classmethod
    def _parse_hypo_depth_dist(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            `list` of :class:`openquake.nrmllib.models.HypocentralDepth`
            objects.
        """
        hdd = []

        for elem in _xpath(src_elem, './/nrml:hypoDepth'):
            hdepth = models.HypocentralDepth()
            hdepth.probability = decimal.Decimal(elem.get('probability'))
            hdepth.depth = float(elem.get('depth'))

            hdd.append(hdepth)

        return hdd

    @classmethod
    def _parse_point_source(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`openquake.nrmllib.models.PointSource`
            object.
        """
        point = models.PointSource()
        cls._set_common_attrs(point, src_elem)

        point_geom = models.PointGeometry()
        point.geometry = point_geom

        [gml_pos] = _xpath(src_elem, './/gml:pos')
        coords = gml_pos.text.split()
        point_geom.wkt = 'POINT(%s)' % ' '.join(coords)

        point_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        point_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        point.mfd = cls._parse_mfd(src_elem)
        point.nodal_plane_dist = cls._parse_nodal_plane_dist(src_elem)
        point.hypo_depth_dist = cls._parse_hypo_depth_dist(src_elem)

        return point

    @classmethod
    def _parse_area(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`openquake.nrmllib.models.AreaSource`
            object.
        """
        area = models.AreaSource()
        cls._set_common_attrs(area, src_elem)

        area_geom = models.AreaGeometry()
        area.geometry = area_geom

        [gml_pos_list] = _xpath(src_elem, './/gml:posList')
        coords = gml_pos_list.text.split()
        # Area source polygon geometries are always 2-dimensional and on the
        # Earth's surface (depth == 0.0).
        area_geom.wkt = utils.coords_to_poly_wkt(coords, 2)

        area_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        area_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        area.mfd = cls._parse_mfd(src_elem)
        area.nodal_plane_dist = cls._parse_nodal_plane_dist(src_elem)
        area.hypo_depth_dist = cls._parse_hypo_depth_dist(src_elem)

        return area

    @classmethod
    def _parse_simple(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated
            :class:`openquake.nrmllib.models.SimpleFaultSource` object.
        """
        simple = models.SimpleFaultSource()
        cls._set_common_attrs(simple, src_elem)

        simple_geom = cls._parse_simple_geometry(src_elem)
        simple.geometry = simple_geom
        simple.mfd = cls._parse_mfd(src_elem)
        simple.rake = float(
            _xpath(src_elem, './/nrml:rake')[0].text)

        return simple

    @classmethod
    def _parse_complex(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated
            :class:`openquake.nrmllib.models.ComplexFaultSource` object.
        """
        complx = models.ComplexFaultSource()
        cls._set_common_attrs(complx, src_elem)
        complex_geom = cls._parse_complex_geometry(src_elem)
        complx.geometry = complex_geom
        complx.mfd = cls._parse_mfd(src_elem)
        complx.rake = float(
            _xpath(src_elem, './/nrml:rake')[0].text)
        return complx

    @classmethod
    def _parse_characteristic(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated
            :class:`openquake.nrmllib.models.CharacteristicSource` object.
        """
        char = models.CharacteristicSource()
        char.id = src_elem.get('id')
        char.name = src_elem.get('name')
        char.trt = src_elem.get('tectonicRegion')
        char.rake = float(_xpath(src_elem, './nrml:rake')[0].text)
        char.mfd = cls._parse_mfd(src_elem)

        # The `surface` can be either a simple fault surface, complex fault
        # surface, or a multi surface (consisting of 1 or more planar surfaces)
        surface_elem = _xpath(src_elem, './nrml:surface')[0]
        simple_surface = _xpath(surface_elem, './nrml:simpleFaultGeometry')
        complex_surface = _xpath(surface_elem, './nrml:complexFaultGeometry')
        multi_surface = _xpath(surface_elem, './nrml:planarSurface')

        if simple_surface:
            [simple_surface] = simple_surface
            char.surface = cls._parse_simple_geometry(simple_surface)
        elif complex_surface:
            [complex_surface] = complex_surface
            char.surface = cls._parse_complex_geometry(complex_surface)
        elif multi_surface:
            char.surface = [cls._parse_planar_surface(surf)
                            for surf in multi_surface]

        return char

    def parse(self):
        """Parse the source XML content and generate a source model in object
        form.

        :returns:
            :class:`openquake.nrmllib.models.SourceModel` instance.
        """
        src_model = models.SourceModel()

        tree = openquake.nrmllib.iterparse_tree(self.source)

        for event, element in tree:
            # Find the <sourceModel> element and get the 'name' attr.
            if event == 'start':
                if element.tag == self._SM_TAG:
                    src_model.name = element.get('name')
                    break
            else:
                # If we get to here, we didn't find the <sourceModel> element.
                raise ValueError('<sourceModel> element not found.')

        src_model.sources = self._source_gen(tree)

        return src_model


class SiteModelParser(object):
    """NRML site model parser. Reads site-specific parameters from a given
    source.

    :param source:
        Filename or file-like object containing the XML data.
    """

    def __init__(self, source):
        self.source = source

    def parse(self):
        """Parse the site model XML content and generate
        :class:`openquake.nrmllib.model.SiteModel` objects.

        :returns:
            A iterable of :class:`openquake.nrmllib.model.SiteModel` objects.
        """
        tree = openquake.nrmllib.iterparse_tree(self.source,
                                                events=('start', ))

        for _, element in tree:
            if element.tag == '{%s}site' % openquake.nrmllib.NAMESPACE:
                site = models.SiteModel()
                site.vs30 = float(element.get('vs30'))
                site.vs30_type = element.get('vs30Type').strip()
                site.z1pt0 = float(element.get('z1pt0'))
                site.z2pt5 = float(element.get('z2pt5'))
                lonlat = dict(lon=element.get('lon').strip(),
                              lat=element.get('lat').strip())
                site.wkt = 'POINT(%(lon)s %(lat)s)' % lonlat

                yield site

                # Now do some clean up to free memory.
                while element.getprevious() is not None:
                    # Delete previous sibling elements.
                    # We need to loop here in case there are comments in
                    # the input file which are considered siblings to
                    # source elements.
                    del element.getparent()[0]


# notice that there must be at most one rupture per file because of the
# constraint maxOccurs="1" in nrml.xsd
class RuptureModelParser(FaultGeometryParserMixin):

    _SIMPLE_RUPT_TAG = '{%s}simpleFaultRupture' % openquake.nrmllib.NAMESPACE
    _COMPLEX_RUPT_TAG = '{%s}complexFaultRupture' % openquake.nrmllib.NAMESPACE

    def __init__(self, source):
        self.source = source
        self._parse_fn_map = {
            self._SIMPLE_RUPT_TAG: self._parse_simple_rupture,
            self._COMPLEX_RUPT_TAG: self._parse_complex_rupture,
        }

    @classmethod
    def _parse_simple_rupture(cls, element):
        """
        :param element:
            :class:`lxml.etree._Element` instance for a simple rupture.
        :returns:
            Populated
            :class:`openquake.nrmllib.models.SimpleFaultRuptureModel` object.
        """
        model = models.SimpleFaultRuptureModel()
        magnitude_elem, rake_elem, hypocenter_elem, geom_elem = list(element)
        model.magnitude = float(magnitude_elem.text)
        model.rake = float(rake_elem.text)
        h = hypocenter_elem.attrib
        model.hypocenter = map(float, [h['lon'], h['lat'], h['depth']])
        model.geometry = cls._parse_simple_geometry(geom_elem)
        return model

    @classmethod
    def _parse_complex_rupture(cls, element):
        """
        :param element:
            :class:`lxml.etree._Element` instance for a complex rupture.
        :returns:
            Populated
            :class:`openquake.nrmllib.models.ComplexFaultRuptureModel` object.
        """
        model = models.ComplexFaultRuptureModel()
        magnitude_elem, rake_elem, hypocenter_elem, geom_elem = list(element)
        model.magnitude = float(magnitude_elem.text)
        model.rake = float(rake_elem.text)
        h = hypocenter_elem.attrib
        model.hypocenter = map(float, [h['lon'], h['lat'], h['depth']])
        model.geometry = cls._parse_complex_geometry(geom_elem)
        return model

    def parse(self):
        """
        Parse the source XML content and generate a rupture model in object
        form. The file must contain a single SimpleFaultRupture object or
        a single ComplexFaultRupture object.

        :returns:
            :class:`openquake.nrmllib.models.SimpleFaultRuptureModel`
            instance or
            :class:`openquake.nrmllib.models.ComplexFaultRuptureModel` instance
        """
        tree = openquake.nrmllib.iterparse_tree(self.source)
        for _, element in tree:
            parse_fn = self._parse_fn_map.get(element.tag)
            if parse_fn:
                return parse_fn(element)
        # If we get to here, we didn't find the right element.
        raise ValueError('<%s> or <%s> element not found.'
                         % (self._SIMPLE_RUPT_TAG,
                            self._COMPLEX_RUPT_TAG))


class GMFScenarioParser(object):

    _GMF_TAG = '{%s}gmf' % openquake.nrmllib.NAMESPACE
    _NODE_TAG = '{%s}node' % openquake.nrmllib.NAMESPACE

    def __init__(self, source):
        self.source = source

    def parse(self):
        """
        Parse the source XML content for a GMF scenario.
        :returns:
            an iterable over triples (imt, gmvs, location)
        """
        tree = openquake.nrmllib.iterparse_tree(self.source, events=('end',))
        gmf = OrderedDict()  # (imt, location) -> gmvs
        point_value_list = []
        for _, element in tree:
            a = element.attrib
            if element.tag == self._NODE_TAG:
                point_value_list.append(
                    ['POINT(%(lon)s %(lat)s)' % a, a['gmv']])
            elif element.tag == self._GMF_TAG:
                imt = a['IMT']
                try:
                    imt += '(%s)' % a['saPeriod']
                except KeyError:
                    pass
                for point, value in point_value_list:
                    try:
                        values = gmf[point, imt]
                    except KeyError:
                        gmf[point, imt] = [value]
                    else:
                        values.append(value)
                point_value_list = []
        for (location, imt), gmvs in gmf.iteritems():
            yield imt, '{%s}' % ','.join(gmvs), location


class HazardCurveXMLParser(object):
    _CURVES_TAG = '{%s}hazardCurves' % openquake.nrmllib.NAMESPACE
    _CURVE_TAG = '{%s}hazardCurve' % openquake.nrmllib.NAMESPACE

    def __init__(self, source):
        self.source = source

    def parse(self):
        """
        Parse the source XML content for a hazard curve.
        :returns:
            Populated :class:`openquake.nrmllib.models.HazardCurveModel` object
        """
        tree = openquake.nrmllib.iterparse_tree(self.source)
        hc_iter = self._parse(tree)
        header = hc_iter.next()
        return models.HazardCurveModel(data_iter=hc_iter, **header)

    def _parse(self, tree):
        header = OrderedDict()
        for event, element in tree:
            if element.tag == self._CURVES_TAG and event == 'start':
                a = element.attrib
                header['statistics'] = a.get('statistics')
                header['quantile_value'] = a.get('quantileValue')
                header['smlt_path'] = a.get('sourceModelTreePath')
                header['gsimlt_path'] = a.get('gsimTreePath')
                header['imt'] = a['IMT']
                header['investigation_time'] = a['investigationTime']
                header['sa_period'] = a.get('saPeriod')
                header['sa_damping'] = a.get('saDamping')
                header['imls'] = map(float, element[0].text.split())
                yield header
            elif element.tag == self._CURVE_TAG and event == 'end':
                point, poes = element
                x, y = [float(v) for v in point[0].text.split()]
                location = models.Location(x, y)
                poes_array = map(float, poes.text.split())
                yield models.HazardCurveData(location, poes_array)


def HazardCurveParser(*args, **kwargs):
    warnings.warn(
        'HazardCurveParser is deprecated, use HazardCurveXMLParser instead',
        RuntimeWarning
    )
    return HazardCurveXMLParser(*args, **kwargs)
