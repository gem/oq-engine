# Copyright (c) 2010-2014, GEM Foundation.
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

import os
import unittest
from StringIO import StringIO

from numpy.testing import assert_allclose

from openquake.hazardlib import site
from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import pmf
from openquake.hazardlib import scalerel
from openquake.hazardlib import source
from openquake.hazardlib.tom import PoissonTOM

from openquake.commonlib import source as source_input

from openquake import nrmllib
from openquake.commonlib.general import deep_eq

# directory where the example files are
NRML_DIR = os.path.dirname(os.path.dirname(os.path.dirname(nrmllib.__file__)))

# Test NRML to use (contains 1 of each source type).
MIXED_SRC_MODEL = os.path.join(NRML_DIR, 'examples/source_model/mixed.xml')

DUPLICATE_ID_SRC_MODEL = os.path.join(
    os.path.dirname(__file__), 'data', 'invalid_source_model.xml')


class NrmlSourceToHazardlibTestCase(unittest.TestCase):
    """Tests for converting NRML source model objects to the hazardlib
    representation.
    """

    @classmethod
    def setUpClass(cls):
        converter = source_input.SourceConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            width_of_mfd_bin=1.,  # for Truncated GR MFDs
            area_source_discretization=1.,  # km
        )
        source_nodes = converter.read_nrml(MIXED_SRC_MODEL).sourceModel
        (cls.area, cls.point, cls.simple, cls.cmplx, cls.char_simple,
         cls.char_complex, cls.char_multi) = map(
            converter.convert_node, source_nodes)

        # the parameters here would typically be specified in the job .ini
        cls.investigation_time = 50.
        cls.rupture_mesh_spacing = 1  # km
        cls.width_of_mfd_bin = 1.  # for Truncated GR MFDs
        cls.area_source_discretization = 1.  # km
        cls.nrml_to_hazardlib = converter

    @property
    def _expected_point(self):
        tgr_mfd = mfd.TruncatedGRMFD(
            a_val=-3.5, b_val=1.0, min_mag=5.0, max_mag=6.5, bin_width=1.0
        )

        np1 = geo.NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        np2 = geo.NodalPlane(strike=90.0, dip=45.0, rake=90.0)
        npd = pmf.PMF([(0.3, np1), (0.7, np2)])
        hd = pmf.PMF([(0.5, 4.0), (0.5, 8.0)])

        point = source.PointSource(
            source_id="2",
            name="point",
            tectonic_region_type="Stable Continental Crust",
            mfd=tgr_mfd,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=0.5,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            location=geo.Point(-122.0, 38.0),
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            temporal_occurrence_model=PoissonTOM(50.),
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
        npd = pmf.PMF([(0.3, np1), (0.7, np2)])
        hd = pmf.PMF([(0.5, 4.0), (0.5, 8.0)])

        polygon = geo.Polygon(
            [geo.Point(-122.5, 37.5), geo.Point(-121.5, 37.5),
             geo.Point(-121.5, 38.5), geo.Point(-122.5, 38.5)]
        )

        area = source.AreaSource(
            source_id="1",
            name="Quito",
            tectonic_region_type="Active Shallow Crust",
            mfd=incr_mfd,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=scalerel.PeerMSR(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            polygon=polygon,
            area_discretization=self.area_source_discretization,
            temporal_occurrence_model=PoissonTOM(50.),
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
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=10.0,
            lower_seismogenic_depth=20.0,
            fault_trace=geo.Line(
                [geo.Point(-121.82290, 37.73010),
                 geo.Point(-122.03880, 37.87710)]
            ),
            dip=45.0,
            rake=30.0,
            temporal_occurrence_model=PoissonTOM(50.)
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
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=2.0,
            edges=edges,
            rake=30.0,
            temporal_occurrence_model=PoissonTOM(50.),
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
            mesh_spacing=self.rupture_mesh_spacing
        )

        char = source.CharacteristicFaultSource(
            source_id="5",
            name="characteristic source, simple fault",
            tectonic_region_type="Volcanic",
            mfd=tgr_mfd,
            surface=surface,
            rake=30.0,
            temporal_occurrence_model=PoissonTOM(50.),
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
            edges, self.rupture_mesh_spacing
        )

        char = source.CharacteristicFaultSource(
            source_id="6",
            name="characteristic source, complex fault",
            tectonic_region_type="Volcanic",
            mfd=incr_mfd,
            surface=complex_surface,
            rake=60.0,
            temporal_occurrence_model=PoissonTOM(50.0),
        )
        return char

    @property
    def _expected_char_multi(self):
        tgr_mfd = mfd.TruncatedGRMFD(
            a_val=-3.6, b_val=1.0, min_mag=5.2, max_mag=6.4, bin_width=1.0
        )

        surfaces = [
            geo.PlanarSurface(
                mesh_spacing=self.rupture_mesh_spacing,
                strike=0.0,
                dip=90.0,
                top_left=geo.Point(-1, 1, 21),
                top_right=geo.Point(1, 1, 21),
                bottom_left=geo.Point(-1, -1, 59),
                bottom_right=geo.Point(1, -1, 59)
            ),
            geo.PlanarSurface(
                mesh_spacing=self.rupture_mesh_spacing,
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
            rake=90.0,
            temporal_occurrence_model=PoissonTOM(50.0),
        )
        return char

    def test_point_to_hazardlib(self):
        eq, msg = deep_eq(self._expected_point, self.point)
        self.assertTrue(eq, msg)

    def test_area_to_hazardlib(self):
        eq, msg = deep_eq(self.area, self._expected_area)
        self.assertTrue(eq, msg)

    def test_simple_to_hazardlib(self):
        eq, msg = deep_eq(self._expected_simple, self.simple)
        self.assertTrue(eq, msg)

    def test_complex_to_hazardlib(self):
        eq, msg = deep_eq(self._expected_complex, self.cmplx)
        self.assertTrue(eq, msg)

    def test_characteristic_simple(self):
        eq, msg = deep_eq(self._expected_char_simple, self.char_simple)
        self.assertTrue(eq, msg)

    def test_characteristic_complex(self):
        eq, msg = deep_eq(self._expected_char_complex, self.char_complex)
        self.assertTrue(eq, msg)

    def test_characteristic_multi(self):
        eq, msg = deep_eq(self._expected_char_multi, self.char_multi)
        self.assertTrue(eq, msg)

    def test_raises_useful_error(self):
        # Test that the source id and name are included with conversion errors,
        # to help the users deal with problems in their source models.
        area_file = StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <sourceModel name="Some Source Model">
        <areaSource id="1" name="Quito" tectonicRegion="Active Shallow Crust">
            <areaGeometry>
                <gml:Polygon>
                    <gml:exterior>
                        <gml:LinearRing>
                            <gml:posList>
                             -122.5 37.5
                             -121.5 37.5
                             -121.5 38.5
                             -122.5 38.5
                            </gml:posList>
                        </gml:LinearRing>
                    </gml:exterior>
                </gml:Polygon>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </areaGeometry>
            <magScaleRel>PeerMSR</magScaleRel>
            <ruptAspectRatio>1.5</ruptAspectRatio>
            <incrementalMFD minMag="6.55" binWidth="0.1">
                <occurRates>-0.0010614989 8.8291627E-4 7.3437777E-4
                            6.108288E-4 5.080653E-4
                </occurRates>
            </incrementalMFD>
            <nodalPlaneDist>
                <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.7" strike="90.0" dip="45.0" rake="90.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="0.5" depth="4.0" />
                <hypoDepth probability="0.5" depth="8.0" />
            </hypoDepthDist>
        </areaSource>

    </sourceModel>
</nrml>
""")
        msg = ('Could not convert occurRates->probabilities: -0.0010614989 is '
               'smaller than the min, 0, line 25')
        with self.assertRaises(ValueError) as ctx:
            self.nrml_to_hazardlib.read_nrml(area_file)
        self.assertEqual(str(ctx.exception), msg)


class AreaToPointsTestCase(unittest.TestCase):
    """
    Tests for
    :func:`openquake.engine.input.source.area_to_point_sources`.
    """
    rupture_mesh_spacing = 1  # km
    area_source_discretization = 1.  # km

    def test_area_with_tgr_mfd(self):
        trunc_mfd = mfd.TruncatedGRMFD(
            a_val=2.1, b_val=4.2, bin_width=0.1, min_mag=6.55, max_mag=8.91
        )
        np1 = geo.NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        np2 = geo.NodalPlane(strike=90.0, dip=45.0, rake=90.0)
        npd = pmf.PMF([(0.3, np1), (0.7, np2)])
        hd = pmf.PMF([(0.5, 4.0), (0.5, 8.0)])
        polygon = geo.Polygon(
            [geo.Point(-122.5, 37.5), geo.Point(-121.5, 37.5),
             geo.Point(-121.5, 38.5), geo.Point(-122.5, 38.5)]
        )
        area = source.AreaSource(
            source_id="1",
            name="source A",
            tectonic_region_type="Active Shallow Crust",
            mfd=trunc_mfd,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=scalerel.PeerMSR(),
            rupture_aspect_ratio=1.0,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            polygon=polygon,
            area_discretization=self.area_source_discretization,
            temporal_occurrence_model=PoissonTOM(50.),
        )
        actual = list(source_input.area_to_point_sources(area, 10))
        self.assertEqual(len(actual), 96)  # expected 96 points
        self.assertAlmostEqual(actual[0].mfd.a_val, 0.1177287669604317)

    def test_area_with_incr_mfd(self):
        incr_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=6.55, bin_width=0.1,
            occurrence_rates=[
                0.0010614989, 8.8291627E-4, 7.3437777E-4, 6.108288E-4,
                5.080653E-4,
            ]
        )
        np1 = geo.NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        np2 = geo.NodalPlane(strike=90.0, dip=45.0, rake=90.0)
        npd = pmf.PMF([(0.3, np1), (0.7, np2)])
        hd = pmf.PMF([(0.5, 4.0), (0.5, 8.0)])
        polygon = geo.Polygon(
            [geo.Point(-122.5, 37.5), geo.Point(-121.5, 37.5),
             geo.Point(-121.5, 38.5), geo.Point(-122.5, 38.5)]
        )
        area = source.AreaSource(
            source_id="1",
            name="source A",
            tectonic_region_type="Active Shallow Crust",
            mfd=incr_mfd,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=scalerel.PeerMSR(),
            rupture_aspect_ratio=1.0,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            polygon=polygon,
            area_discretization=self.area_source_discretization,
            temporal_occurrence_model=PoissonTOM(50.0),
        )
        actual = list(source_input.area_to_point_sources(area, 10))
        self.assertEqual(len(actual), 96)  # expected 96 points
        assert_allclose(
            actual[0].mfd.occurrence_rates,
            [1.10572802083e-05, 9.197044479166666e-06, 7.6497684375e-06,
             6.3627999999999995e-06, 5.292346875e-06])


class SourceCollectorTestCase(unittest.TestCase):
    SITES = [
        site.Site(geo.Point(-121.0, 37.0), 0.1, True, 3, 4),
        site.Site(geo.Point(-121.1, 37.0), 1, True, 3, 4),
        site.Site(geo.Point(-121.0, -37.15), 2, True, 3, 4),
        site.Site(geo.Point(-121.0, 37.49), 3, True, 3, 4),
        site.Site(geo.Point(-121.0, -37.5), 4, True, 3, 4),
    ]

    @classmethod
    def setUpClass(cls):
        cls.nrml_to_hazardlib = source_input.SourceConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            width_of_mfd_bin=1.,  # for Truncated GR MFDs
            area_source_discretization=1.)
        cls.source_collector = dict(
            (sc.trt, sc) for sc in source_input.parse_source_model(
                MIXED_SRC_MODEL, cls.nrml_to_hazardlib,
                lambda src: None))
        cls.sitecol = site.SiteCollection(cls.SITES)

    def check(self, trt, attr, value):
        sc = self.source_collector[trt]
        self.assertEqual(getattr(sc, attr), value)

    def test_content(self):
        trts = [sc.trt for sc in self.source_collector.itervalues()]
        self.assertEqual(
            trts,
            ['Volcanic', 'Subduction Interface', 'Stable Continental Crust',
             'Active Shallow Crust'])

        self.check('Volcanic', 'max_mag', 6.5)
        self.check('Subduction Interface', 'max_mag', 6.5)
        self.check('Stable Continental Crust', 'max_mag', 6.5)
        self.check('Active Shallow Crust', 'max_mag', 6.95)

        self.check('Volcanic', 'min_mag', 5.0)
        self.check('Subduction Interface', 'min_mag', 5.5)
        self.check('Stable Continental Crust', 'min_mag', 5.5)
        self.check('Active Shallow Crust', 'min_mag', 5.0)

        self.check('Volcanic', 'num_ruptures', 0)
        self.check('Subduction Interface', 'num_ruptures', 0)
        self.check('Stable Continental Crust', 'num_ruptures', 0)
        self.check('Active Shallow Crust', 'num_ruptures', 0)

    def test_repr(self):
        self.assertEqual(
            repr(self.source_collector['Volcanic']),
            '<SourceCollector TRT=Volcanic, 3 source(s)>')
        self.assertEqual(
            repr(self.source_collector['Stable Continental Crust']),
            '<SourceCollector TRT=Stable Continental Crust, 1 source(s)>')
        self.assertEqual(
            repr(self.source_collector['Subduction Interface']),
            '<SourceCollector TRT=Subduction Interface, 1 source(s)>')
        self.assertEqual(
            repr(self.source_collector['Active Shallow Crust']),
            '<SourceCollector TRT=Active Shallow Crust, 2 source(s)>')


class ParseSourceModelTestCase(unittest.TestCase):

    def test_well_formed_rupture(self):
        converter = source_input.RuptureConverter(rupture_mesh_spacing=1.)
        [node] = converter.read_nrml(StringIO('''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <simpleFaultRupture>
        <magnitude>7.65</magnitude>
        <rake>15.0</rake>
        <hypocenter lon="0.0" lat="0.0" depth="15.0"/>
        <simpleFaultGeometry>
                <gml:LineString>
                    <gml:posList>
                        -124.704 40.363
                        -124.977 41.214
                        -125.140 42.096
                    </gml:posList>
                </gml:LineString>
            <dip>50.0</dip>
            <upperSeismoDepth>12.5</upperSeismoDepth>
            <lowerSeismoDepth>19.5</lowerSeismoDepth>
        </simpleFaultGeometry>
    </simpleFaultRupture>
</nrml>
'''))
        rup = converter.convert_node(node)
        self.assertEqual(rup.mag, 7.65)
        self.assertEqual(rup.rake, 15.0)

    def test_ill_formed_rupture(self):
        rup_file = StringIO('''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <simpleFaultRupture>
        <magnitude>7.65</magnitude>
        <rake>15.0</rake>
        <hypocenter lon="0.0" lat="0.0" depth="-5.0"/>
        <simpleFaultGeometry>
                <gml:LineString>
                    <gml:posList>
                        -124.704 40.363
                        -124.977 41.214
                        -125.140 42.096
                    </gml:posList>
                </gml:LineString>
            <dip>50.0</dip>
            <upperSeismoDepth>12.5</upperSeismoDepth>
            <lowerSeismoDepth>19.5</lowerSeismoDepth>
        </simpleFaultGeometry>
    </simpleFaultRupture>
</nrml>
''')
        converter = source_input.RuptureConverter(rupture_mesh_spacing=1.)
        # at line 7 there is an invalid depth="-5.0"
        with self.assertRaises(ValueError) as ctx:
            converter.read_nrml(rup_file)
        self.assertIn('line 7', str(ctx.exception))

    def test_duplicate_id(self):
        converter = source_input.SourceConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            width_of_mfd_bin=0.1,  # for Truncated GR MFDs
            area_source_discretization=10.)
        with self.assertRaises(source_input.DuplicateID):
            source_input.parse_source_model(
                DUPLICATE_ID_SRC_MODEL, converter)
