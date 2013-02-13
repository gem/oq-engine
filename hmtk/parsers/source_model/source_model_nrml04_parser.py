#!/usr/bin/env/python

"""Simple objects models to represent elements of NRML artifacts. These models
are intended to be produced by NRML XML parsers and consumed by NRML XML
serializers.
"""
import decimal

from lxml import etree

import nrml
from nrml import models
from nrml import utils
from nhlib.geo.point import Point
from nhlib.geo.line import Line
from nhlig.geo.polygon import Polygon
from hmtk.sources.source_model import mtkSourceModel
from hmtk.sources.point_source import mtkPointSource
from hmtk.sources.area_source import mtkAreaSource
from hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from hmtk.sources.complex_fault_source import mtkComplexFaultSource


TGR_MAP = {'aValue': 'a_val',
           'bValue': 'b_val',
           'minMag': 'min_mag',
           'maxMag': 'max_mag'}
             

def _xpath(elem, expr):
    """Helper function for executing xpath queries on an XML element. This
    function uses the default mapping of namespaces (which includes NRML and
    GML).

    :param str expr:
        XPath expression.
    :param elem:
        A :class:`lxml.etree._Element` instance.
    """
    return elem.xpath(expr, namespaces=nrml.PARSE_NS_MAP)


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
        #simple_geom = models.SimpleFaultGeometry()

        [gml_pos_list] = _xpath(src_elem, './/gml:posList')
        trace = cls._parse_edge_to_line(gml_pos_list, dimension=2)
        #coords = gml_pos_list.text.split()
        #simple_geom.wkt = utils.coords_to_linestr_wkt(coords, 2)

        dip = float(
            _xpath(src_elem, './/nrml:dip')[0].text)
        simple_geom.upper_seismo_depth = float(
            _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        simple_geom.lower_seismo_depth = float(
            _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)

        return trace, dip, upper_seismo_depth, lower_seismo_depth 

    @classmethod
    def _parse_complex_geometry(cls, src_elem):
        """
        :param src_elem:
            :class:`lxml.etree._Element` instance representing a geometry.
        :returns:
            Fully populated
        :class:`openquake.nrmllib.models.ComplexFaultGeometry` object.
        """
        #complex_geom = models.ComplexFaultGeometry()
        complex_edges = []
        # Top edge
        [top_edge] = _xpath(src_elem, './/nrml:faultTopEdge//gml:posList')
        complex_edges.append(cls._parse_edge_to_line(top_edge, dimension=3))
        
        #top_coords = top_edge.text.split()
        #complex_geom.top_edge_wkt = utils.coords_to_linestr_wkt(top_coords, 3)

        # Optional itermediate edges:
        int_edges = _xpath(src_elem, './/nrml:intermediateEdge//gml:posList')
        for edge in int_edges:
            complex_edges.append(cls._parse_edge_to_line(edge, dimension=3))
            #coords = edge.text.split()
            #complex_geom.int_edges.append(
            #    utils.coords_to_linestr_wkt(coords, 3))

        # Bottom edge
        [bottom_edge] = _xpath(src_elem, './/nrml:faultBottomEdge//gml:posList')
        complex_edges.append(cls._parse_edge_to_line(bottom_edge, dimension=3))
        #bottom_coords = bottom_edge.text.split()
        #complex_geom.bottom_edge_wkt = utils.coords_to_linestr_wkt(
        #    bottom_coords, 3)
        return complex_edges
        
    @classmethod
    def _parse_edge_to_line(cls, edge_string, dimension=2):
        '''
        For a string returned from the _xpath function, convert to an 
        instance of a line class
        '''
        coords = edge_string.text.split()
        
        if dimension == 3:
            # Long lat and depth
            edge = [Point(float(coords[iloc]), float(coords[iloc + 1]),
                    float(coords[iloc + 2])) for iloc in range(0, len(coords),
                    dimension)]
        else:                    
            # Only long & lat
            edge = [Point(float(coords[iloc]), float(coords[iloc + 1])) 
                    for iloc in range(0, len(coords), dimension)]      
        return Line(edge)

class SourceModelParser(FaultGeometryParserMixin):
    """NRML source model parser. Reads point sources, area sources, simple
    fault sources, and complex fault sources from a given source.

    :param source:
        Filename or file-like object containing the XML data.
    """

    _SM_TAG = '{%s}sourceModel' % nrml.NAMESPACE
    _PT_TAG = '{%s}pointSource' % nrml.NAMESPACE
    _AREA_TAG = '{%s}areaSource' % nrml.NAMESPACE
    _SIMPLE_TAG = '{%s}simpleFaultSource' % nrml.NAMESPACE
    _COMPLEX_TAG = '{%s}complexFaultSource' % nrml.NAMESPACE

    def __init__(self, source)):
        self.source = source
        self.mesh_spacing = None
        self._parse_fn_map = {
            self._PT_TAG: self._parse_point,
            self._AREA_TAG: self._parse_area,
            self._SIMPLE_TAG: self._parse_simple,
            self._COMPLEX_TAG: self._parse_complex,
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
        #model.id = src_elem.get('id')
        #model.name = src_elem.get('name')
        
        if src_elem.get('tectonicRegion'):
            model.trt = src_elem.get('tectonicRegion')
        
        msr_elem = _xpath(src_elem, './nrml:magScaleRel')[0].text
        if msr_elem:
            model.mag_scale_rel = msr_elem.strip()
        
        rup_asp = _xpath(src_elem, './nrml:ruptAspectRatio')[0].text
        if rup_asp:
            model.rupt_aspect_ratio = float(rup_asp)

    @classmethod
    def _parse_mfd(cls, src_elem):
        """
        :param src_elem:
        :class:`lxml.etree._Element` instance representing a source.
        """
        [mfd_elem] = _xpath(src_elem, ('.//nrml:truncGutenbergRichterMFD | '
                                       './/nrml:incrementalMFD'))
        
        if not mfd_elem:
            return None
        
        value_set = False
        
        if mfd_elem.tag == '{%s}truncGutenbergRichterMFD' % (nrml.NAMESPACE):
            mfd = models.TGRMFD()
            for key in TGR_MAP.keys():
                key_string = mfd_elem.get(key)
                if key_string:
                    value_set = True
                    setattr(mfd, TGR_MAP[key], float(key_string))

        elif mfd_elem.tag == '{%s}incrementalMFD' % (nrml.NAMESPACE):
            mfd = models.IncrementalMFD()
            if mfd_elem.get('minMag'):
                value_set = True
                mfd.min_mag = float(mfd_elem.get('minMag'))
            if mfd_elem.get('binWidth'):
                value_set = True
                mfd.bin_width = float(mfd_elem.get('binWidth'))
             
            [occur_rates] = _xpath(mfd_elem, './nrml:occurRates')
            if occur_rates.text:
                value_set = True
                mfd.occur_rates = [float(x) for x in occur_rates.text.split()]
        if value_set:
            return mfd
        else:
            return None

    @classmethod
    def _parse_nodal_plane_dist(cls, src_elem):
        """
        :param src_elem:
        :class:`lxml.etree._Element` instance representing a source.
        :returns:
            `list` of :class:`openquake.nrmllib.models.NodalPlane` objects.
        """
        npd = []
        value_set = False
        for elem in _xpath(src_elem, './/nrml:nodalPlane'):
            nplane = models.NodalPlane()
            if elem.get('probability'):
                nplane.probability = decimal.Decimal(elem.get('probability'))
                
            for attribute in ['strike', 'dip', 'rake']:
                if elem.get(attribute)
                    setattr(nplane, attribute, float(elem.get(attribute)))
                    value_set = True 

            npd.append(nplane)
        if value_set:
            return npd
        else:
            return None

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
        value_set = False
        for elem in _xpath(src_elem, './/nrml:hypoDepth'):
            hdepth = models.HypocentralDepth()
            if elem.get('probability'):
                hdepth.probability = decimal.Decimal(elem.get('probability'))
            if elem.get('depth')
                hdepth.depth = float(elem.get('depth'))
                value_set = True
            hdd.append(hdepth)
        if value_set
            return hdd
        else:
            return None

    @classmethod
    def _parse_point(cls, src_elem):
        """
        :param src_elem:
        :class:`lxml.etree._Element` instance representing a source.
        :returns:
            Fully populated :class:`openquake.nrmllib.models.PointSource`
            object.
        """
        # Instantiate mtkPointSource class with identifier and name
        point = mtkPointSource(src_elem.get('id'), src_elem.get('name'))
        print 'Point Source - ID: %s, name: %s' % (point.id, point.name)
        # Set common attributes
        cls._set_common_attrs(point, src_elem)

        # Define the geometry
        point_geom = models.PointGeometry()
        point.geometry = point_geom

        [gml_pos] = _xpath(src_elem, './/gml:pos')
        coords = gml_pos.text.split()
        input_point = Point(float(coords[0]), float(coords[1]))
        
        #point_geom.wkt = 'POINT(%s)' % ' '.join(coords)
        if _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text:
            upper_seismo_depth = float(
                _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        else:
            upper_seismo_depth = None
        
        if _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text:
            lower_seismo_depth = float(
                _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)
        else:
            lower_seismo_depth = None
        
        point.create_geometry(input_point, 
                              upper_seismo_depth, 
                              lower_seismo_depth)
        
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
        # Instantiate with identifier and name
        area = mtkAreaSource(src_elem.get('id'), src_elem.get('name'))
        print 'Area source - ID: %s, name: %s' % (area.id, area.name)
        # Set common attributes
        cls._set_common_attrs(area, src_elem)

        #area_geom = models.AreaGeometry()
        #area.geometry = area_geom

        # Get geometry
        [gml_pos_list] = _xpath(src_elem, './/gml:posList')
        coords = gml_pos_list.text.split()
        input_polygon = Polygon(
            [Point(float(coords[iloc]), float(coords[iloc + 1])) 
             for iloc in range(0, len(coords), 2)])
            
        # Area source polygon geometries are always 2-dimensional and on the
        # Earth's surface (depth == 0.0).
        #area_geom.wkt = utils.coords_to_poly_wkt(coords, 2)
        if _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text:
            upper_seismo_depth = float(
                _xpath(src_elem, './/nrml:upperSeismoDepth')[0].text)
        else:
            upper_seismo_depth = None
        
        if _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text:        
            lower_seismo_depth = float(
                _xpath(src_elem, './/nrml:lowerSeismoDepth')[0].text)
        else:
            lower_seismo_depth = None
        
        area.create_geometry(input_polygon, 
                             upper_seismo_depth,
                             lower_seismo_depth)
                             
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
        # Instantiate with identifier and name
        simple = mtkSimpleFaultSource(src_elem.get('id'), src_elem.get('name'))
        print 'Simple Fault source - ID: %s, name: %s' % (simple.id, 
                                                          simple.name)
        # Set common attributes
        cls._set_common_attrs(simple, src_elem)
        
        # Create the simple geometry
        trace, dip, upper_depth, lower_depth = \
            cls._parse_simple_geometry(src_elem)
        simple.create_geometry(trace, dip, upper_depth, lower_depth,
                                self.mesh_spacing)
        #simple.geometry = simple_geom
        simple.mfd = cls._parse_mfd(src_elem)
        if _xpath(src_elem, './/nrml:rake')[0].text:
            simple.rake = float(_xpath(src_elem, './/nrml:rake')[0].text)

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
        # Instantiate with identifier and name
        complx = mtkComplexFaultSource(src_elem.get('id'), src_elem.get('name'))
        print 'Complex Fault Source - ID: %s, name: %s' % (complx.id, 
                                                           complx.name)
        # Set common attributes
        cls._set_common_attrs(complx, src_elem)
        
        # Create the complex geometry
        complex_edges = cls._parse_complex_geometry(src_elem)
        complx.create_geometry(complex_edges, self.mesh_spacing)
        # Get mfd
        complx.mfd = cls._parse_mfd(src_elem)
        if _xpath(src_elem, './/nrml:rake')[0].text:
            complx.rake = float(
                _xpath(src_elem, './/nrml:rake')[0].text)
        return complx

    def parse(self, fault_mesh_spacing=1.0):
        """
        Parse the source XML content and generate a source model in object
        form.

        :returns:
            :class:`hmtk.sources.source_model.SourceModel` instance.
        """
        self.mesh_spacing = fault_mesh_spacing
        
        src_model = mtkSourceModel()

        schema = etree.XMLSchema(
            etree.parse(nrml.nrml_schema_file()))

        tree = etree.iterparse(self.source, events=('start', 'end'),
                               schema=schema)

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

