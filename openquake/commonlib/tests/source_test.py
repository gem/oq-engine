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
import decimal
import unittest

from numpy.testing import assert_allclose

from openquake.hazardlib import site
from openquake.hazardlib import geo
from openquake.hazardlib import mfd
from openquake.hazardlib import pmf
from openquake.hazardlib import scalerel
from openquake.hazardlib import source
from openquake.hazardlib.tom import PoissonTOM

from openquake.nrmllib import parsers as nrml_parsers
from openquake.nrmllib import models as nrml_models

from openquake.commonlib import source as source_input

from openquake import nrmllib
from openquake.commonlib.general import deep_eq

# Test NRML to use (contains 1 of each source type).
MIXED_SRC_MODEL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(nrmllib.__file__))),
    'examples/source_model/mixed.xml')


class NrmlSourceToHazardlibTestCase(unittest.TestCase):
    """Tests for converting NRML source model objects to the hazardlib
    representation.
    """

    @classmethod
    def setUpClass(cls):
        parser = nrml_parsers.SourceModelParser(MIXED_SRC_MODEL)

        (cls.area, cls.point, cls.simple, cls.cmplx, cls.char_simple,
         cls.char_complex, cls.char_multi) = list(parser.parse())

        # the parameters here would typically be specified in the job .ini
        cls.investigation_time = 50.
        cls.rupture_mesh_spacing = 1  # km
        cls.width_of_mfd_bin = 1.  # for Truncated GR MFDs
        cls.area_source_discretization = 1.  # km
        cls.nrml_to_hazardlib = source_input.NrmlHazardlibConverter(
            investigation_time=50.,
            rupture_mesh_spacing=1,  # km
            width_of_mfd_bin=1.,  # for Truncated GR MFDs
            area_source_discretization=1.,  # km
        )

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
        exp = self._expected_point
        actual = self.nrml_to_hazardlib(self.point)

        eq, msg = deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_area_to_hazardlib(self):
        exp = self._expected_area
        actual = self.nrml_to_hazardlib(self.area)

        eq, msg = deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_simple_to_hazardlib(self):
        exp = self._expected_simple
        actual = self.nrml_to_hazardlib(self.simple)

        eq, msg = deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_complex_to_hazardlib(self):
        exp = self._expected_complex
        actual = self.nrml_to_hazardlib(self.cmplx)

        eq, msg = deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_characteristic_simple(self):
        exp = self._expected_char_simple
        actual = self.nrml_to_hazardlib(self.char_simple)

        eq, msg = deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_characteristic_complex(self):
        exp = self._expected_char_complex
        actual = self.nrml_to_hazardlib(self.char_complex)
        eq, msg = deep_eq(exp, actual)
        self.assertTrue(eq, msg)

    def test_characteristic_multi(self):
        exp = self._expected_char_multi
        actual = self.nrml_to_hazardlib(self.char_multi)

        eq, msg = deep_eq(exp, actual)

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

        with self.assertRaises(Exception) as ar:
            self.nrml_to_hazardlib(area_src)
        expected_error = (
            "The following error has occurred with source id='1', "
            "name='Quito': Could not create geometry because of errors while "
            "reading input."
        )
        self.assertEqual(expected_error, ar.exception.message)


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
        cls.nrml_to_hazardlib = source_input.NrmlHazardlibConverter(
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

    def test_gen_blocks(self):
        def src_filter(src):
            if src.source_id in ('1', '5'):
                return site.SiteCollection(self.SITES)

        max_weight = 100
        sc = self.source_collector['Volcanic']
        blocks = sc.gen_blocks(
            src_filter, max_weight,
            self.nrml_to_hazardlib.area_source_discretization)
        [seq] = list(blocks)
        [src] = seq
        self.assertEqual(src.source_id, '5')

    def test_repr(self):
        self.assertEqual(
            repr(self.source_collector['Volcanic']),
            '<SourceCollector TRT=Volcanic, 1 source(s)>')
        self.assertEqual(
            repr(self.source_collector['Stable Continental Crust']),
            '<SourceCollector TRT=Stable Continental Crust, 1 source(s)>')
        self.assertEqual(
            repr(self.source_collector['Subduction Interface']),
            '<SourceCollector TRT=Subduction Interface, 1 source(s)>')
        self.assertEqual(
            repr(self.source_collector['Active Shallow Crust']),
            '<SourceCollector TRT=Active Shallow Crust, 2 source(s)>')
