# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import numpy

from openquake.hazardlib.source import AreaSource
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.calc import disagg
from openquake.hazardlib.geo import Point, Polygon, NodalPlane
from openquake.hazardlib.mfd import TruncatedGRMFD
from openquake.hazardlib.imt import SA
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.site import Site

ATOL = 1E-5


class DisaggTestCase(unittest.TestCase):
    def test_areasource(self):
        nodalplane = NodalPlane(strike=0.0, dip=90.0, rake=0.0)
        src = AreaSource(
            source_id='src_1',
            name='area source',
            tectonic_region_type='Active Shallow Crust',
            mfd=TruncatedGRMFD(a_val=3.5, b_val=1.0, min_mag=5.0,
                               max_mag=6.5, bin_width=0.1),
            nodal_plane_distribution=PMF([(1.0, nodalplane)]),
            hypocenter_distribution=PMF([(1.0, 5.0)]),
            upper_seismogenic_depth=0.0,
            lower_seismogenic_depth=10.0,
            magnitude_scaling_relationship=WC1994(),
            rupture_aspect_ratio=1.0,
            polygon=Polygon([Point(-0.5, -0.5), Point(-0.5, 0.5),
                             Point(0.5, 0.5), Point(0.5, -0.5)]),
            area_discretization=9.0,
            rupture_mesh_spacing=1.0,
            temporal_occurrence_model=PoissonTOM(50.)
        )
        site = Site(location=Point(0.0, 0.0),
                    vs30=800.0,
                    vs30measured=True,
                    z1pt0=500.0,
                    z2pt5=2.0)
        gsims = {'Active Shallow Crust': BooreAtkinson2008()}
        imt = SA(period=0.1, damping=5.0)
        iml = 0.2
        truncation_level = 3.0
        n_epsilons = 3
        mag_bin_width = 0.2
        # in km
        dist_bin_width = 10.0
        # in decimal degree
        coord_bin_width = 0.2

        # compute disaggregation
        bin_edges, diss_matrix = disagg.disaggregation(
            [src], site, imt, iml, gsims, truncation_level,
            n_epsilons, mag_bin_width, dist_bin_width, coord_bin_width)
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
        numpy.testing.assert_allclose(
            mag_bins, [5., 5.2, 5.4, 5.6, 5.8, 6., 6.2, 6.4, 6.6])
        numpy.testing.assert_allclose(
            dist_bins, [0., 10., 20., 30., 40., 50., 60., 70., 80.])
        numpy.testing.assert_allclose(
            lat_bins[0], [-0.655445, -0.327723, 0., 0.327723, 0.655445],
            atol=ATOL)
        numpy.testing.assert_allclose(
            lon_bins[0], [-0.655445, -0.327723, 0., 0.327723, 0.655445],
            atol=ATOL)
        numpy.testing.assert_allclose(eps_bins, [-3., -1., 1., 3.])
        self.assertEqual(trt_bins, ['Active Shallow Crust'])

        self.assertEqual(diss_matrix.shape, (8, 8, 4, 4, 3, 1))
        expected = [0.0245487, 0.0231275, 0.0210702, 0.0185196, 0.0157001,
                    0.0130175, 0.0107099, 0.0045489]
        numpy.testing.assert_allclose(
            diss_matrix.sum(axis=(1, 2, 3, 4, 5)), expected, atol=ATOL)
