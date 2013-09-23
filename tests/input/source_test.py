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


import decimal
import os
import StringIO
import unittest

from xml.etree import ElementTree

from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import pmf
from openquake.hazardlib import scalerel
from openquake.hazardlib import source
from openquake.nrmllib import parsers as nrml_parsers
from openquake.nrmllib import models as nrml_models

from openquake.engine.db import models
from openquake.engine.input import source as source_input

from tests.utils import helpers


# Test NRML to use (contains 1 of each source type).
MIXED_SRC_MODEL = helpers.get_data_path('mixed_source_model.xml')

# These 3 parameters would typically be specified in the job configuration.
MESH_SPACING = 1  # km
BIN_WIDTH = 1  # for Truncated GR MFDs
AREA_SRC_DISC = 1  # area source discretization, in km


class NrmlSourceToHazardlibTestCase(unittest.TestCase):
    """Tests for converting NRML source model objects to the hazardlib
    representation.
    """

    @classmethod
    def setUpClass(cls):
        parser = nrml_parsers.SourceModelParser(MIXED_SRC_MODEL)

        (cls.area, cls.point, cls.simple, cls.cmplx, cls.char_simple,
         cls.char_complex, cls.char_multi) = list(parser.parse())

    @property
    def _expected_point(self):
        tgr_mfd = mfd.TruncatedGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5, bin_width=1.0
        )

        np1 = geo.NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        np2 = geo.NodalPlane(strike=90.0, dip=45.0, rake=90.0)
        npd = pmf.PMF(
            [(decimal.Decimal("0.3"), np1), (decimal.Decimal("0.7"), np2)]
        )

        hd = pmf.PMF(
            [(decimal.Decimal("0.5"), 4.0), (decimal.Decimal("0.5"), 8.0)]
        )

        point = source.PointSource(
            source_id="2",
            name="point",
            tectonic_region_type="Stable Continental Crust",
            mfd=tgr_mfd,
            rupture_mesh_spacing=MESH_SPACING,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=0.5,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            location=geo.Point(-122.0, 38.0),
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd
        )
        return point

    @property
    def _expected_area(self):
        incr_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=6.55, bin_width=0.1,
            occurrence_rates=[
                0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                5.080653E-4,
            ]
        )

        np1 = geo.NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        np2 = geo.NodalPlane(strike=90.0, dip=45.0, rake=90.0)
        npd = pmf.PMF(
            [(decimal.Decimal("0.3"), np1), (decimal.Decimal("0.7"), np2)]
        )

        hd = pmf.PMF(
            [(decimal.Decimal("0.5"), 4.0), (decimal.Decimal("0.5"), 8.0)]
        )

        polygon = geo.Polygon(
            [geo.Point(-122.5, 37.5), geo.Point(-121.5, 37.5),
             geo.Point(-121.5, 38.5), geo.Point(-122.5, 38.5)]
        )

        area = source.AreaSource(
            source_id="1",
            name="Quito",
            tectonic_region_type="Active Shallow Crust",
            mfd=incr_mfd,
            rupture_mesh_spacing=MESH_SPACING,
            magnitude_scaling_relationship=scalerel.PeerMSR(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            polygon=polygon, area_discretization=AREA_SRC_DISC
        )

        return area

    @property
    def _expected_simple(self):
        incr_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=5.0, bin_width=0.1,
            occurrence_rates=[
                0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                5.080653E-4,
            ]
        )

        simple = source.SimpleFaultSource(
            source_id="3",
            name="Mount Diablo Thrust",
            tectonic_region_type="Active Shallow Crust",
            mfd=incr_mfd,
            rupture_mesh_spacing=MESH_SPACING,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=10.0,
            lower_seismogenic_depth=20.0,
            fault_trace=geo.Line(
                [geo.Point(-121.82290, 37.73010),
                 geo.Point(-122.03880, 37.87710)]
            ),
            dip=45.0,
            rake=30.0
        )

        return simple

    @property
    def _expected_complex(self):
        tgr_mfd = mfd.TruncatedGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5, bin_width=1.0
        )

        edges = [
            geo.Line([
                geo.Point(-124.704, 40.363, 0.5493260E+01),
                geo.Point(-124.977, 41.214, 0.4988560E+01),
                geo.Point(-125.140, 42.096, 0.4897340E+01),
            ]),
            geo.Line([
                geo.Point(-124.704, 40.363, 0.5593260E+01),
                geo.Point(-124.977, 41.214, 0.5088560E+01),
                geo.Point(-125.140, 42.096, 0.4997340E+01),
            ]),
            geo.Line([
                geo.Point(-124.704, 40.363, 0.5693260E+01),
                geo.Point(-124.977, 41.214, 0.5188560E+01),
                geo.Point(-125.140, 42.096, 0.5097340E+01),
            ]),
            geo.Line([
                geo.Point(-123.829, 40.347, 0.2038490E+02),
                geo.Point(-124.137, 41.218, 0.1741390E+02),
                geo.Point(-124.252, 42.115, 0.1752740E+02),
            ]),
        ]

        cmplx = source.ComplexFaultSource(
            source_id="4",
            name="Cascadia Megathrust",
            tectonic_region_type="Subduction Interface",
            mfd=tgr_mfd,
            rupture_mesh_spacing=MESH_SPACING,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=2.0,
            edges=edges,
            rake=30.0
        )

        return cmplx

    @property
    def _expected_char_simple(self):
        tgr_mfd = mfd.TruncatedGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5, bin_width=1.0
        )

        fault_trace = geo.Line([geo.Point(-121.82290, 37.73010),
                                geo.Point(-122.03880, 37.87710)])

        surface = geo.SimpleFaultSurface.from_fault_data(
            fault_trace=fault_trace,
            upper_seismogenic_depth=10.0,
            lower_seismogenic_depth=20.0,
            dip=45.0,
            mesh_spacing=MESH_SPACING
        )

        char = source.CharacteristicFaultSource(
            source_id="5",
            name="characteristic source, simple fault",
            tectonic_region_type="Volcanic",
            mfd=tgr_mfd,
            surface=surface,
            rake=30.0
        )
        return char

    @property
    def _expected_char_complex(self):
        incr_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=5.0, bin_width=0.1,
            occurrence_rates=[
                0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                5.080653E-4,
            ]
        )

        edges = [
            geo.Line([
                geo.Point(-124.704, 40.363, 0.5493260E+01),
                geo.Point(-124.977, 41.214, 0.4988560E+01),
                geo.Point(-125.140, 42.096, 0.4897340E+01),
            ]),
            geo.Line([
                geo.Point(-124.704, 40.363, 0.5593260E+01),
                geo.Point(-124.977, 41.214, 0.5088560E+01),
                geo.Point(-125.140, 42.096, 0.4997340E+01),
            ]),
            geo.Line([
                geo.Point(-124.704, 40.363, 0.5693260E+01),
                geo.Point(-124.977, 41.214, 0.5188560E+01),
                geo.Point(-125.140, 42.096, 0.5097340E+01),
            ]),
            geo.Line([
                geo.Point(-123.829, 40.347, 0.2038490E+02),
                geo.Point(-124.137, 41.218, 0.1741390E+02),
                geo.Point(-124.252, 42.115, 0.1752740E+02),
            ]),
        ]
        complex_surface = geo.ComplexFaultSurface.from_fault_data(
            edges, 10
        )

        char = source.CharacteristicFaultSource(
            source_id="6",
            name="characteristic source, complex fault",
            tectonic_region_type="Volcanic",
            mfd=incr_mfd,
            surface=complex_surface,
            rake=60.0
        )
        return char

    @property
    def _expected_char_multi(self):
        tgr_mfd = mfd.TruncatedGRMFD(
            a_val=-3.6, b_val=1.0, min_mag=5.2, max_mag=6.4, bin_width=1.0
        )

        surfaces = [
            geo.PlanarSurface(
                mesh_spacing=MESH_SPACING,
                strike=0.0,
                dip=90.0,
                top_left=geo.Point(-1, 1, 21),
                top_right=geo.Point(1, 1, 21),
                bottom_left=geo.Point(-1, -1, 59),
                bottom_right=geo.Point(1, -1, 59)
            ),
            geo.PlanarSurface(
                mesh_spacing=MESH_SPACING,
                strike=20.0,
                dip=45.0,
                top_left=geo.Point(1, 1, 20),
                top_right=geo.Point(3, 1, 20),
                bottom_left=geo.Point(1, -1, 80),
                bottom_right=geo.Point(3, -1, 80)
            )
        ]
        multi_surface = geo.MultiSurface(surfaces)

        char = source.CharacteristicFaultSource(
            source_id="7",
            name="characteristic source, multi surface",
            tectonic_region_type="Volcanic",
            mfd=tgr_mfd,
            surface=multi_surface,
            rake=90.0
        )
        return char

    def test_point_to_hazardlib(self):
        exp = self._expected_point
        actual = source_input.nrml_to_hazardlib(
            self.point, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_area_to_hazardlib(self):
        exp = self._expected_area
        actual = source_input.nrml_to_hazardlib(
            self.area, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_simple_to_hazardlib(self):
        exp = self._expected_simple
        actual = source_input.nrml_to_hazardlib(
            self.simple, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_complex_to_hazardlib(self):
        exp = self._expected_complex
        actual = source_input.nrml_to_hazardlib(
            self.cmplx, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_characteristic_simple(self):
        exp = self._expected_char_simple
        actual = source_input.nrml_to_hazardlib(
            self.char_simple, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_characteristic_complex(self):
        exp = self._expected_char_complex
        actual = source_input.nrml_to_hazardlib(
            self.char_complex, 10, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_characteristic_multi(self):
        exp = self._expected_char_multi
        actual = source_input.nrml_to_hazardlib(
            self.char_multi, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_raises_useful_error(self):
        # Test that the source id and name are included with conversion errors,
        # to help the users deal with problems in their source models.
        area_geom = nrml_models.AreaGeometry(
            wkt='POLYGON((0.0 0.0, 1.0 0.0, 0.0 0.0 ))',
            upper_seismo_depth=0.0, lower_seismo_depth=10.0,
        )
        area_mfd = nrml_models.IncrementalMFD(
            min_mag=6.55, bin_width=0.1,
            occur_rates=[0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                         5.080653E-4],
        )
        area_npd = [
            nrml_models.NodalPlane(probability=decimal.Decimal("0.3"),
                                   strike=0.0, dip=90.0, rake=0.0),
            nrml_models.NodalPlane(probability=decimal.Decimal("0.7"),
                                   strike=90.0, dip=45.0, rake=90.0),
        ]
        area_hdd = [
            nrml_models.HypocentralDepth(probability=decimal.Decimal("0.5"),
                                    depth=4.0),
            nrml_models.HypocentralDepth(probability=decimal.Decimal("0.5"),
                                    depth=8.0),
        ]
        area_src = nrml_models.AreaSource(
            id='1', name='Quito', trt='Active Shallow Crust',
            geometry=area_geom, mag_scale_rel='PeerMSR',
            rupt_aspect_ratio=1.5, mfd=area_mfd, nodal_plane_dist=area_npd,
            hypo_depth_dist=area_hdd,
        )

        with self.assertRaises(RuntimeError) as ar:
            source_input.nrml_to_hazardlib(area_src, MESH_SPACING, BIN_WIDTH,
                                           AREA_SRC_DISC)
        expected_error = (
            "The following error has occurred with source id='1', "
            "name='Quito': Could not create geometry because of errors while "
            "reading input."
        )
        self.assertEqual(expected_error, ar.exception.message)


class SourceDBWriterTestCase(unittest.TestCase):
    """Test DB serialization of seismic sources using
    :class:`openquake.engine.input.source.SourceDBWriter`.
    """

    def test_serialize(self):
        parser = nrml_parsers.SourceModelParser(MIXED_SRC_MODEL)
        source_model = parser.parse()

        inp = models.Input(
            owner=helpers.default_user(),
            digest='fake',
            path='fake',
            input_type='source',
            size=0
        )
        inp.save()

        db_writer = source_input.SourceDBWriter(
            inp, source_model, MESH_SPACING, BIN_WIDTH, AREA_SRC_DISC
        )
        db_writer.serialize()

        # Check that everything was saved properly.

        # First, check the Input:
        # refresh the record
        [inp] = models.Input.objects.filter(id=inp.id)
        self.assertEquals(source_model.name, inp.name)

        # re-reparse the test file for comparisons:
        nrml_sources = list(
            nrml_parsers.SourceModelParser(MIXED_SRC_MODEL).parse()
        )

        parsed_sources = list(
            models.ParsedSource.objects.filter(input=inp.id).order_by('id')
        )

        # compare pristine nrml sources to those stored in pickled form in the
        # database (by unpickling them first, of course):
        for i, ns in enumerate(nrml_sources):
            self.assertTrue(*helpers.deep_eq(ns, parsed_sources[i].nrml))


class AreaSourceToPointSourcesTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.engine.input.source.area_source_to_point_sources`.
    """

    def setUp(self):
        self.area_source_attrib = dict(
            id='1',
            name='source A',
            trt='Active Shallow Crust',
            geometry=nrml_models.AreaGeometry(
                upper_seismo_depth=10,
                lower_seismo_depth=20,
                wkt=('POLYGON((1.0 1.0, 1.0 -1.0, -1.0 -1.0, -1.0 1.0, '
                     '1.0 1.0))'),
            ),
            mag_scale_rel='WC1994',
            rupt_aspect_ratio=1.0,
            mfd=None,
            nodal_plane_dist=[
                nrml_models.NodalPlane(probability=1.0, strike=0.0,
                                       dip=90.0, rake=0.0)
            ],
            hypo_depth_dist=[
                nrml_models.HypocentralDepth(probability=1.0, depth=10.0)
            ],
        )

        self.expected = []
        lons = [-0.100677001712, 0.798645996576, -0.100591068089,
                0.798817863822]
        lats = [0.100830691185, 0.100830691185, -0.798490914733,
                -0.798490914733]
        for i, (lon, lat) in enumerate(zip(lons, lats)):
            point_attrib = self.area_source_attrib.copy()
            del point_attrib['geometry']
            point_attrib['id'] = '1-%s' % i
            point_attrib['name'] = 'source A-%s' % i

            pt_source = nrml_models.PointSource(**point_attrib)
            pt_source.geometry = nrml_models.PointGeometry(
                upper_seismo_depth=10,
                lower_seismo_depth=20,
                wkt='POINT(%s %s)' % (lon, lat),
            )
            self.expected.append(pt_source)


    def test_area_with_tgr_mfd(self):
        area_mfd = nrml_models.TGRMFD(a_val=-3.5, b_val=1.0,
                                 min_mag=5.0, max_mag=6.5)
        self.area_source_attrib['mfd'] = area_mfd

        area_source = nrml_models.AreaSource(**self.area_source_attrib)

        # Re-scaled MFD for the points
        point_mfd = nrml_models.TGRMFD(a_val=-4.1020599913279625, b_val=1.0,
                                       min_mag=5.0, max_mag=6.5)
        for exp in self.expected:
            exp.mfd = point_mfd

        actual = list(source_input.area_source_to_point_sources(area_source,
                                                                100))
        equal, err = helpers.deep_eq(self.expected, actual)
        self.assertTrue(equal, err)

    def test_area_with_incr_mfd(self):
        area_mfd = nrml_models.IncrementalMFD(
            min_mag=6.55, bin_width=0.1, occur_rates=[0.1, 0.2, 0.3, 0.4]
        )
        self.area_source_attrib['mfd'] = area_mfd

        area_source = nrml_models.AreaSource(**self.area_source_attrib)

        # Re-scaled MFD for the points
        point_mfd = nrml_models.IncrementalMFD(
            min_mag=6.55, bin_width=0.1, occur_rates=[0.025, 0.05, 0.075, 0.1]
        )

        for exp in self.expected:
            exp.mfd = point_mfd

        actual = list(source_input.area_source_to_point_sources(area_source,
                                                                100))
        equal, err = helpers.deep_eq(self.expected, actual)
        self.assertTrue(equal, err)


class OptimizeSourceModelTestCase(unittest.TestCase):

    input_source_model = """\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
    <sourceModel>
        <pointSource id="1" name="point" tectonicRegion="Active Shallow Crust">
          <pointGeometry>
            <gml:Point>
              <gml:pos>0.0 0.0</gml:pos>
            </gml:Point>
            <upperSeismoDepth>0.0</upperSeismoDepth>
            <lowerSeismoDepth>20.0</lowerSeismoDepth>
          </pointGeometry>
          <magScaleRel>WC1994</magScaleRel>
          <ruptAspectRatio>2.0</ruptAspectRatio>
          <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0000" maxMag="8.0000" />
          <nodalPlaneDist>
            <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
          </nodalPlaneDist>
          <hypoDepthDist>
            <hypoDepth probability="1.0" depth="10.0"/>
          </hypoDepthDist>
        </pointSource>
        <areaSource id="2" name="area" tectonicRegion="Active Shallow Crust">
          <areaGeometry>
            <gml:Polygon>
              <gml:exterior>
                <gml:LinearRing>
                  <gml:posList>-0.5 -0.5 -0.5 0.5 0.5 0.5 0.5 -0.5</gml:posList>
                </gml:LinearRing>
              </gml:exterior>
            </gml:Polygon>
            <upperSeismoDepth>0.0</upperSeismoDepth>
            <lowerSeismoDepth>20.0</lowerSeismoDepth>
          </areaGeometry>
          <magScaleRel>WC1994</magScaleRel>
          <ruptAspectRatio>2.0</ruptAspectRatio>
          <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0000" maxMag="8.0000" />
          <nodalPlaneDist>
            <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
          </nodalPlaneDist>
          <hypoDepthDist>
            <hypoDepth probability="1.0" depth="10.0"/>
          </hypoDepthDist>
        </areaSource>
        <simpleFaultSource id="3" name="simple fault" tectonicRegion="Active Shallow Crust">
          <simpleFaultGeometry>
            <gml:LineString>
              <gml:posList>-0.5 -0.5 0.5 0.5</gml:posList>
            </gml:LineString>
            <dip>90.0</dip>
            <upperSeismoDepth>1.0</upperSeismoDepth>
            <lowerSeismoDepth>20.0</lowerSeismoDepth>
          </simpleFaultGeometry>
          <magScaleRel>WC1994</magScaleRel>
          <ruptAspectRatio>1.0</ruptAspectRatio>
          <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0000" maxMag="7.0000" />
          <rake>90.0</rake>
        </simpleFaultSource>
        <complexFaultSource id="4" name="complex fault" tectonicRegion="Active Shallow Crust">
          <complexFaultGeometry>
            <faultTopEdge>
              <gml:LineString>
                <gml:posList>-0.5 -0.45 5.0 0.45 0.5 5.0</gml:posList>
              </gml:LineString>
            </faultTopEdge>
            <faultBottomEdge>
              <gml:LineString>
                <gml:posList>-0.45 -0.5 10.0 0.5 0.45 10.0</gml:posList>
              </gml:LineString>
            </faultBottomEdge>
          </complexFaultGeometry>
          <magScaleRel>WC1994</magScaleRel>
          <ruptAspectRatio>1.0</ruptAspectRatio>
          <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0000" maxMag="7.0000" />
          <rake>90.0</rake>
        </complexFaultSource>
        <characteristicFaultSource id="7" name="characteristic source, multi surface" tectonicRegion="Active Shallow Crust">
            <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0000" maxMag="8.0000" />
            <rake>90.0</rake>
            <surface>
                <!-- Characteristic source with a collection of planar surfaces -->
                <planarSurface strike="0.0" dip="90.0">
                    <topLeft lon="-1.0" lat="1.0" depth="21.0" />
                    <topRight lon="1.0" lat="1.0" depth="21.0" />
                    <bottomLeft lon="-1.0" lat="-1.0" depth="59.0" />
                    <bottomRight lon="1.0" lat="-1.0" depth="59.0" />
                </planarSurface>
                <planarSurface strike="20.0" dip="45.0">
                    <topLeft lon="0" lat="1.1" depth="20.0" />
                    <topRight lon="1.1" lat="2" depth="20.0" />
                    <bottomLeft lon="0.9" lat="0" depth="80.0" />
                    <bottomRight lon="2" lat="0.9" depth="80.0" />
                </planarSurface>
            </surface>
        </characteristicFaultSource>
    </sourceModel>
</nrml>
"""

    output_source_model = """\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <sourceModel>
    <pointSource id="1" name="point" tectonicRegion="Active Shallow Crust">
      <pointGeometry>
        <gml:Point>
          <gml:pos>0.0 0.0</gml:pos>
        </gml:Point>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </pointGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>2.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0" maxMag="8.0"/>
      <nodalPlaneDist>
        <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="1.0" depth="10.0"/>
      </hypoDepthDist>
    </pointSource>
    <pointSource id="2-0" name="area-0" tectonicRegion="Active Shallow Crust">
      <pointGeometry>
        <gml:Point>
          <gml:pos>-0.0503390234986 0.0503391970406</gml:pos>
        </gml:Point>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </pointGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>2.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="3.39794000867" bValue="1.0" minMag="5.0" maxMag="8.0"/>
      <nodalPlaneDist>
        <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="1.0" depth="10.0"/>
      </hypoDepthDist>
    </pointSource>
    <pointSource id="2-1" name="area-1" tectonicRegion="Active Shallow Crust">
      <pointGeometry>
        <gml:Point>
          <gml:pos>0.399321953003 0.0503391970406</gml:pos>
        </gml:Point>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </pointGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>2.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="3.39794000867" bValue="1.0" minMag="5.0" maxMag="8.0"/>
      <nodalPlaneDist>
        <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="1.0" depth="10.0"/>
      </hypoDepthDist>
    </pointSource>
    <pointSource id="2-2" name="area-2" tectonicRegion="Active Shallow Crust">
      <pointGeometry>
        <gml:Point>
          <gml:pos>-0.0503282764445 -0.399321605919</gml:pos>
        </gml:Point>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </pointGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>2.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="3.39794000867" bValue="1.0" minMag="5.0" maxMag="8.0"/>
      <nodalPlaneDist>
        <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="1.0" depth="10.0"/>
      </hypoDepthDist>
    </pointSource>
    <pointSource id="2-3" name="area-3" tectonicRegion="Active Shallow Crust">
      <pointGeometry>
        <gml:Point>
          <gml:pos>0.399343447111 -0.399321605919</gml:pos>
        </gml:Point>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </pointGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>2.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="3.39794000867" bValue="1.0" minMag="5.0" maxMag="8.0"/>
      <nodalPlaneDist>
        <nodalPlane probability="1.0" strike="0.0" dip="90.0" rake="0.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="1.0" depth="10.0"/>
      </hypoDepthDist>
    </pointSource>
    <simpleFaultSource id="3" name="simple fault" tectonicRegion="Active Shallow Crust">
      <simpleFaultGeometry>
        <gml:LineString>
          <gml:posList>-0.5 -0.5 0.5 0.5</gml:posList>
        </gml:LineString>
        <dip>90.0</dip>
        <upperSeismoDepth>1.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </simpleFaultGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>1.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0" maxMag="7.0"/>
      <rake>90.0</rake>
    </simpleFaultSource>
    <complexFaultSource id="4" name="complex fault" tectonicRegion="Active Shallow Crust">
      <complexFaultGeometry>
        <faultTopEdge>
          <gml:LineString>
            <gml:posList>-0.5 -0.45 5.0 0.45 0.5 5.0</gml:posList>
          </gml:LineString>
        </faultTopEdge>
        <faultBottomEdge>
          <gml:LineString>
            <gml:posList>-0.45 -0.5 10.0 0.5 0.45 10.0</gml:posList>
          </gml:LineString>
        </faultBottomEdge>
      </complexFaultGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>1.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0" maxMag="7.0"/>
      <rake>90.0</rake>
    </complexFaultSource>
    <characteristicFaultSource id="7" name="characteristic source, multi surface" tectonicRegion="Active Shallow Crust">
      <truncGutenbergRichterMFD aValue="4.0" bValue="1.0" minMag="5.0" maxMag="8.0"/>
      <rake>90.0</rake>
      <surface>
        <planarSurface strike="0.0" dip="90.0">
          <topLeft lon="-1.0" lat="1.0" depth="21.0"/>
          <topRight lon="1.0" lat="1.0" depth="21.0"/>
          <bottomLeft lon="-1.0" lat="-1.0" depth="59.0"/>
          <bottomRight lon="1.0" lat="-1.0" depth="59.0"/>
        </planarSurface>
        <planarSurface strike="20.0" dip="45.0">
          <topLeft lon="0.0" lat="1.1" depth="20.0"/>
          <topRight lon="1.1" lat="2.0" depth="20.0"/>
          <bottomLeft lon="0.9" lat="0.0" depth="80.0"/>
          <bottomRight lon="2.0" lat="0.9" depth="80.0"/>
        </planarSurface>
      </surface>
    </characteristicFaultSource>
  </sourceModel>
</nrml>
"""

    def test_optimize_source_model(self):
        in_file = helpers.touch(content=self.input_source_model)
        out_file = helpers.touch(content=self.output_source_model)
        area_src_disc = 50.0
        try:
            source_input.optimize_source_model(in_file, area_src_disc,
                                               out_file)
            expected = ElementTree.tostring(
                ElementTree.XML(self.output_source_model))

            actual = ElementTree.tostring(
                ElementTree.XML(open(out_file).read()))
            self.assertEqual(expected, actual)
        finally:
            os.unlink(in_file)
            os.unlink(out_file)
