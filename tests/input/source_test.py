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
import unittest

from nhlib import geo
from nhlib import mfd
from nhlib import pmf
from nhlib import scalerel
from nhlib import source
from nrml import parsers as nrml_parsers

from openquake.input import source as source_input

from tests.utils import helpers


class NrmlSourceToNhlibTestCase(unittest.TestCase):
    """Tests for converting NRML source model objects to the nhlib
    representation.
    """

    # These 3 parameters would typically be specified in the job configuration.
    MESH_SPACING = 1  # km
    BIN_WIDTH = 1  # for Truncated GR MFDs
    AREA_SRC_DISC = 1  # area source discretization, in km

    # Test NRML to use (contains 1 of each source type).
    MIXED_SRC_MODEL = helpers.get_data_path('mixed_source_model.xml')

    def setUp(self):
        parser = nrml_parsers.SourceModelParser(self.MIXED_SRC_MODEL)

        self.area, self.point, self.simple, self.cmplx = list(parser.parse())

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
            rupture_mesh_spacing=self.MESH_SPACING,
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
            rupture_mesh_spacing=self.MESH_SPACING,
            magnitude_scaling_relationship=scalerel.PeerMSR(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            polygon=polygon, area_discretization=self.AREA_SRC_DISC
        )

        return area

    @property
    def _expected_simple(self):
        incr_mfd = mfd.EvenlyDiscretizedMFD(
            min_mag=6.55, bin_width=0.1,
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
            rupture_mesh_spacing=self.MESH_SPACING,
            magnitude_scaling_relationship=scalerel.WC1994(),
            rupture_aspect_ratio=1.5,
            upper_seismogenic_depth=10.0,
            lower_seismogenic_depth=20.0,
            fault_trace=geo.Line([geo.Point(-121.82290, 37.73010),
                                  geo.Point(-122.03880, 37.87710)]
            ),
            dip=45.0,
            rake=30.0
        )

        return simple


    @property
    def _expected_complex(self):
        return None

    def test_point_to_nhlib(self):
        exp = self._expected_point
        actual = source_input.nrml_to_nhlib(
            self.point, self.MESH_SPACING, self.BIN_WIDTH, self.AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_area_to_nhlib(self):
        exp = self._expected_area
        actual = source_input.nrml_to_nhlib(
            self.area, self.MESH_SPACING, self.BIN_WIDTH, self.AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_simple_to_nhlib(self):
        exp = self._expected_simple
        actual = source_input.nrml_to_nhlib(
            self.simple, self.MESH_SPACING, self.BIN_WIDTH, self.AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)

    def test_complex_to_nhlib(self):
        exp = self._expected_simple
        actual = source_input.nrml_to_nhlib(
            self.cmplx, self.MESH_SPACING, self.BIN_WIDTH, self.AREA_SRC_DISC
        )

        eq, msg = helpers.deep_eq(exp, actual)

        self.assertTrue(eq, msg)
