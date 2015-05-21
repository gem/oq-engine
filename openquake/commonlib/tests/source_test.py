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
import mock
import unittest
from StringIO import StringIO

import numpy
from numpy.testing import assert_allclose

from openquake.hazardlib import site
from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import pmf
from openquake.hazardlib import scalerel
from openquake.hazardlib import source
from openquake.hazardlib.tom import PoissonTOM

from openquake.commonlib import tests, nrml_examples, readinput
from openquake.commonlib import sourceconverter as s
from openquake.commonlib.source import parse_source_model, DuplicatedID
from openquake.commonlib.nrml import nodefactory
from openquake.commonlib.node import read_nodes
from openquake.baselib.general import assert_close

# directory where the example files are
NRML_DIR = os.path.dirname(nrml_examples.__file__)

# Test NRML to use (contains 1 of each source type).
MIXED_SRC_MODEL = os.path.join(NRML_DIR, 'source_model/mixed.xml')

DUPLICATE_ID_SRC_MODEL = os.path.join(
    os.path.dirname(__file__), 'data', 'invalid_source_model.xml')

SIMPLE_FAULT_RUPTURE = os.path.join(
    os.path.dirname(__file__), 'data', 'simple-fault-rupture.xml')

COMPLEX_FAULT_RUPTURE = os.path.join(
    os.path.dirname(__file__), 'data', 'complex-fault-rupture.xml')

SINGLE_PLANE_RUPTURE = os.path.join(
    os.path.dirname(__file__), 'data', 'single-plane-rupture.xml')

MULTI_PLANES_RUPTURE = os.path.join(
    os.path.dirname(__file__), 'data', 'multi-planes-rupture.xml')

NONPARAMETRIC_SOURCE = os.path.join(
    os.path.dirname(__file__), 'data', 'nonparametric-source.xml')

filter_sources = lambda el: 'Source' in el.tag
filter_ruptures = lambda el: 'Rupture' in el.tag

ValidNode = nodefactory['sourceModel']


class NrmlSourceToHazardlibTestCase(unittest.TestCase):
    """Tests for converting NRML source model objects to the hazardlib
    representation.
    """

    @classmethod
    def setUpClass(cls):
        cls.converter = s.SourceConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            complex_fault_mesh_spacing=1,  # km
            width_of_mfd_bin=1.,  # for Truncated GR MFDs
            area_source_discretization=1.,  # km
        )
        source_nodes = read_nodes(MIXED_SRC_MODEL, filter_sources, ValidNode)
        (cls.area, cls.point, cls.simple, cls.cmplx, cls.char_simple,
         cls.char_complex, cls.char_multi) = map(
            cls.converter.convert_node, source_nodes)
        # the parameters here would typically be specified in the job .ini
        cls.investigation_time = 50.
        cls.rupture_mesh_spacing = 1  # km
        cls.complex_fault_mesh_spacing = 1  # km
        cls.width_of_mfd_bin = 1.  # for Truncated GR MFDs
        cls.area_source_discretization = 1.  # km

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
            temporal_occurrence_model=PoissonTOM(50.),
            hypo_list=numpy.array([[0.25, 0.25, 0.3], [0.75, 0.75, 0.7]]),
            slip_list=numpy.array([[90, 0.7], [135, 0.3]])
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
            rupture_mesh_spacing=self.complex_fault_mesh_spacing,
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
            edges, self.complex_fault_mesh_spacing
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
                strike=89.98254582,
                dip=9.696547068,
                top_left=geo.Point(-1, 1, 21),
                top_right=geo.Point(1, 1, 21),
                bottom_left=geo.Point(-1, -1, 59),
                bottom_right=geo.Point(1, -1, 59)
            ),
            geo.PlanarSurface(
                mesh_spacing=self.rupture_mesh_spacing,
                strike=89.98254582,
                dip=15.0987061388,
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
        assert_close(self._expected_point, self.point)

    def test_area_to_hazardlib(self):
        assert_close(self.area, self._expected_area)

    def test_simple_to_hazardlib(self):
        assert_close(self._expected_simple, self.simple)

    def test_complex_to_hazardlib(self):
        assert_close(self._expected_complex, self.cmplx)

    def test_characteristic_simple(self):
        self.char_simple.surface_node = None
        assert_close(self._expected_char_simple, self.char_simple)

    def test_characteristic_complex(self):
        self.char_complex.surface_node = None
        assert_close(self._expected_char_complex, self.char_complex)

    def test_characteristic_multi(self):
        assert_close(self._expected_char_multi, self.char_multi)

    def test_duplicate_id(self):
        converter = s.SourceConverter(  # different from self.converter
            investigation_time=50.,
            rupture_mesh_spacing=1,
            complex_fault_mesh_spacing=1,
            width_of_mfd_bin=0.1,
            area_source_discretization=10,
        )
        with self.assertRaises(DuplicatedID):
            parse_source_model(
                DUPLICATE_ID_SRC_MODEL, converter)

    def test_raises_useful_error_1(self):
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
        msg = ('Could not convert occurRates->positivefloats: '
               'float -0.0010614989 < 0, line 25')
        with self.assertRaises(ValueError) as ctx:
            read_nodes(area_file, filter_sources, ValidNode).next()
        self.assertIn(msg, str(ctx.exception))

    def test_raises_useful_error_2(self):
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
                <occurRates>0.0010614989 8.8291627E-4 7.3437777E-4
                            6.108288E-4 5.080653E-4
                </occurRates>
            </incrementalMFD>
            <nodalPlanedist>
         <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0" />
         <nodalPlane probability="0.7" strike="90.0" dip="45.0" rake="90.0" />
            </nodalPlanedist>
            <hypoDepthDist>
                <hypoDepth probability="0.5" depth="4.0" />
                <hypoDepth probability="0.5" depth="8.0" />
            </hypoDepthDist>
        </areaSource>

    </sourceModel>
</nrml>
""")
        [area] = read_nodes(area_file, filter_sources, ValidNode)
        with self.assertRaises(NameError) as ctx:
            self.converter.convert_node(area)
        self.assertIn(
            "node areaSource: No subnode named 'nodalPlaneDist'"
            " found in 'areaSource', line 5 of", str(ctx.exception))

    def test_hypolist_but_not_sliplist(self):
        simple_file = StringIO("""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <sourceModel name="Some Source Model">
        <simpleFaultSource
        id="3"
        name="Mount Diablo Thrust"
        tectonicRegion="Active Shallow Crust"
        >
            <simpleFaultGeometry>
                <gml:LineString>
                    <gml:posList>
                        -121.8229 37.7301 -122.0388 37.8771
                    </gml:posList>
                </gml:LineString>
                <dip>
                    45.0
                </dip>
                <upperSeismoDepth>
                    10.0
                </upperSeismoDepth>
                <lowerSeismoDepth>
                    20.0
                </lowerSeismoDepth>
            </simpleFaultGeometry>
            <magScaleRel>
                WC1994
            </magScaleRel>
            <ruptAspectRatio>
                1.5
            </ruptAspectRatio>
            <incrementalMFD
            binWidth="0.1"
            minMag="5.0"
            >
                <occurRates>
                    0.0010614989 0.00088291627 0.00073437777 0.0006108288 0.0005080653
                </occurRates>
            </incrementalMFD>
            <rake>
                30.0
            </rake>
            <hypoList>
                <hypo alongStrike="0.25" downDip="0.25" weight="0.3"/>
                <hypo alongStrike="0.75" downDip="0.75" weight="0.7"/>
            </hypoList>
        </simpleFaultSource>
    </sourceModel>
</nrml>
""")
        # check that the error raised by hazardlib is wrapped correctly
        msg = ('node simpleFaultSource: hypo_list and slip_list have to be '
               'both given')
        with self.assertRaises(ValueError) as ctx:
            parse_source_model(simple_file, self.converter)
        self.assertIn(msg, str(ctx.exception))

    def test_nonparametric_source_ok(self):
        converter = s.SourceConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            complex_fault_mesh_spacing=1,  # km
            width_of_mfd_bin=1.,  # for Truncated GR MFDs
            area_source_discretization=1.)
        np, = read_nodes(NONPARAMETRIC_SOURCE, filter_sources, ValidNode)
        converter.convert_node(np)


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
        actual = list(s.area_to_point_sources(area, 10))
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
        actual = list(s.area_to_point_sources(area, 10))
        self.assertEqual(len(actual), 96)  # expected 96 points
        assert_allclose(
            actual[0].mfd.occurrence_rates,
            [1.10572802083e-05, 9.197044479166666e-06, 7.6497684375e-06,
             6.3627999999999995e-06, 5.292346875e-06])


class TrtModelTestCase(unittest.TestCase):
    SITES = [
        site.Site(geo.Point(-121.0, 37.0), 0.1, True, 3, 4),
        site.Site(geo.Point(-121.1, 37.0), 1, True, 3, 4),
        site.Site(geo.Point(-121.0, -37.15), 2, True, 3, 4),
        site.Site(geo.Point(-121.0, 37.49), 3, True, 3, 4),
        site.Site(geo.Point(-121.0, -37.5), 4, True, 3, 4),
    ]

    @classmethod
    def setUpClass(cls):
        cls.converter = s.SourceConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            complex_fault_mesh_spacing=1,  # km
            width_of_mfd_bin=1.,  # for Truncated GR MFDs
            area_source_discretization=1.)
        cls.source_collector = dict(
            (sc.trt, sc) for sc in parse_source_model(
                MIXED_SRC_MODEL, cls.converter, lambda src: None))
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
            '<TrtModel #0 Volcanic, 3 source(s), 0 rupture(s)>')
        self.assertEqual(
            repr(self.source_collector['Stable Continental Crust']),
            '<TrtModel #0 Stable Continental Crust, 1 source(s), 0 rupture(s)>'
        )
        self.assertEqual(
            repr(self.source_collector['Subduction Interface']),
            '<TrtModel #0 Subduction Interface, 1 source(s), 0 rupture(s)>')
        self.assertEqual(
            repr(self.source_collector['Active Shallow Crust']),
            '<TrtModel #0 Active Shallow Crust, 2 source(s), 0 rupture(s)>')


class RuptureConverterTestCase(unittest.TestCase):

    def test_well_formed_ruptures(self):
        converter = s.RuptureConverter(rupture_mesh_spacing=1.5,
                                       complex_fault_mesh_spacing=1.5)
        for fname in (SIMPLE_FAULT_RUPTURE, COMPLEX_FAULT_RUPTURE,
                      SINGLE_PLANE_RUPTURE, MULTI_PLANES_RUPTURE):
            node, = read_nodes(fname, filter_ruptures, ValidNode)
            converter.convert_node(node)

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

        # at line 7 there is an invalid depth="-5.0"
        with self.assertRaises(ValueError) as ctx:
            read_nodes(rup_file, filter_ruptures, ValidNode).next()
        self.assertIn('line 7', str(ctx.exception))


class CompositeSourceModelTestCase(unittest.TestCase):
    def test_one_rlz(self):
        oqparam = tests.get_oqparam('classical_job.ini')
        # the example has number_of_logic_tree_samples = 1
        sitecol = readinput.get_site_collection(oqparam)
        csm = readinput.get_composite_source_model(oqparam, sitecol)
        self.assertEqual(str(csm[0].gsim_lt), '''\
<GsimLogicTree
Active Shallow Crust,b1,SadighEtAl1997,w=0.5
Active Shallow Crust,b2,ChiouYoungs2008,w=0.5
Subduction Interface,b3,SadighEtAl1997,w=1.0>''')
        assoc = csm.get_rlzs_assoc(
            lambda trtmod: sum(src.count_ruptures() for src in trtmod.sources))
        [rlz] = assoc.realizations
        self.assertEqual(assoc.gsim_by_trt[rlz.ordinal],
                         {'Subduction Interface': 'SadighEtAl1997',
                          'Active Shallow Crust': 'ChiouYoungs2008'})
        # ignoring the end of the tuple, with the uid field
        self.assertEqual(rlz.ordinal, 0)
        self.assertEqual(rlz.sm_lt_path, ('b1', 'b5', 'b8'))
        self.assertEqual(rlz.gsim_lt_path, ('b2', 'b3'))
        self.assertEqual(rlz.weight, 1.)
        self.assertEqual(
            str(assoc),
            "<RlzsAssoc\n0,SadighEtAl1997: ['<0,b1_b5_b8,b2_b3,w=1.0>']\n"
            "1,ChiouYoungs2008: ['<0,b1_b5_b8,b2_b3,w=1.0>']>")

    def test_many_rlzs(self):
        oqparam = tests.get_oqparam('classical_job.ini')
        oqparam.number_of_logic_tree_samples = 0
        sitecol = readinput.get_site_collection(oqparam)
        csm = readinput.get_composite_source_model(
            oqparam, sitecol, prefilter=True)
        self.assertEqual(len(csm), 9)  # the smlt example has 1 x 3 x 3 paths;
        # there are 2 distinct tectonic region types, so 18 trt_models
        rlzs_assoc = csm.get_rlzs_assoc()
        rlzs = rlzs_assoc.realizations
        self.assertEqual(len(rlzs), 18)  # the gsimlt has 1 x 2 paths
        self.assertEqual([1, 584, 1, 584, 1, 584, 1, 582, 1, 582,
                          1, 582, 1, 582, 1, 582, 1, 582],
                         map(len, csm.trt_models))

        # test the method csm_info.get_col_ids
        col_ids_first = rlzs_assoc.csm_info.get_col_ids(rlzs[0])
        self.assertEqual(col_ids_first, set([0, 1]))
        col_ids_last = rlzs_assoc.csm_info.get_col_ids(rlzs[-1])
        self.assertEqual(col_ids_last, set([16, 17]))

        # removing 9 trt_models out of 18
        for trt_model in csm.trt_models:
            if trt_model.trt == 'Active Shallow Crust':  # no ruptures
                trt_model.num_ruptures = 0
        assoc = csm.get_rlzs_assoc()

        expected_assoc = """\
<RlzsAssoc
0,SadighEtAl1997: ['<0,b1_b3_b6,*_b3,w=0.04>']
1,SadighEtAl1997: ['<0,b1_b3_b6,*_b3,w=0.04>']
2,SadighEtAl1997: ['<1,b1_b3_b7,*_b3,w=0.12>']
3,SadighEtAl1997: ['<1,b1_b3_b7,*_b3,w=0.12>']
4,SadighEtAl1997: ['<2,b1_b3_b8,*_b3,w=0.04>']
5,SadighEtAl1997: ['<2,b1_b3_b8,*_b3,w=0.04>']
6,SadighEtAl1997: ['<3,b1_b4_b6,*_b3,w=0.12>']
7,SadighEtAl1997: ['<3,b1_b4_b6,*_b3,w=0.12>']
8,SadighEtAl1997: ['<4,b1_b4_b7,*_b3,w=0.36>']
9,SadighEtAl1997: ['<4,b1_b4_b7,*_b3,w=0.36>']
10,SadighEtAl1997: ['<5,b1_b4_b8,*_b3,w=0.12>']
11,SadighEtAl1997: ['<5,b1_b4_b8,*_b3,w=0.12>']
12,SadighEtAl1997: ['<6,b1_b5_b6,*_b3,w=0.04>']
13,SadighEtAl1997: ['<6,b1_b5_b6,*_b3,w=0.04>']
14,SadighEtAl1997: ['<7,b1_b5_b7,*_b3,w=0.12>']
15,SadighEtAl1997: ['<7,b1_b5_b7,*_b3,w=0.12>']
16,SadighEtAl1997: ['<8,b1_b5_b8,*_b3,w=0.04>']
17,SadighEtAl1997: ['<8,b1_b5_b8,*_b3,w=0.04>']>"""
        self.assertEqual(str(assoc), expected_assoc)
        self.assertEqual(len(assoc.realizations), 9)

        # removing all trt_models
        for trt_model in csm.trt_models:
            if trt_model.trt == 'Subduction Interface':  # no ruptures
                trt_model.num_ruptures = 0
        self.assertEqual(csm.get_rlzs_assoc().realizations, [])

    def test_oversampling(self):
        from openquake.qa_tests_data.classical import case_17
        oq = readinput.get_oqparam(
            os.path.join(os.path.dirname(case_17.__file__), 'job.ini'))
        sitecol = readinput.get_site_collection(oq)
        with mock.patch('logging.warn') as warn:
            csm = readinput.get_composite_source_model(
                oq, sitecol, prefilter=True)
        args = warn.call_args[0]
        msg = args[0] % args[1:]
        self.assertEqual(
            msg, "The source path ('b2',) was sampled 4 times")
        assoc = csm.get_rlzs_assoc()
        self.assertEqual(
            str(assoc),
            "<RlzsAssoc\n"
            "0,SadighEtAl1997: ['<0,b1,b1,w=0.2>']\n"
            "1,SadighEtAl1997: ['<1,b2,b1,w=0.2,col=1>', '<2,b2,b1,w=0.2,col=2>', '<3,b2,b1,w=0.2,col=3>', '<4,b2,b1,w=0.2,col=4>']>")

        # test the method csm_info.get_col_ids
        col_ids_first = assoc.csm_info.get_col_ids(assoc.realizations[0])
        self.assertEqual(col_ids_first, set([0]))
        col_ids_last = assoc.csm_info.get_col_ids(assoc.realizations[-1])
        self.assertEqual(col_ids_last, set([4]))
