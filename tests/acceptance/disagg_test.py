# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
            magnitude_scaling_relationship = WC1994(),
            rupture_aspect_ratio=1.0,
            polygon=Polygon([Point(-0.5,-0.5), Point(-0.5,0.5),
                             Point(0.5,0.5), Point(0.5,-0.5)]),
            area_discretization=9.0,
            rupture_mesh_spacing=1.0
        )
        site = Site(location=Point(0.0,0.0),
                    vs30=800.0,
                    vs30measured=True,
                    z1pt0=500.0,
                    z2pt5=2.0)
        gsims = {'Active Shallow Crust': BooreAtkinson2008()}
        imt = SA(period=0.1,damping=5.0)
        iml = 0.2
        time_span = 50.0
        truncation_level = 3.0
        tom = PoissonTOM(time_span)
        n_epsilons = 3
        mag_bin_width = 0.2
        # in km
        dist_bin_width = 10.0
        # in decimal degree
        coord_bin_width = 0.2

        # compute disaggregation
        bin_edges, diss_matrix = disagg.disaggregation(
            [src], site, imt, iml, gsims, tom, truncation_level, n_epsilons,
            mag_bin_width, dist_bin_width, coord_bin_width
        )
        mag_bins, dist_bins, lon_bins, lat_bins, eps_bins, trt_bins = bin_edges
        numpy.testing.assert_almost_equal(
            mag_bins, [5., 5.2, 5.4, 5.6, 5.8, 6., 6.2, 6.4, 6.6]
        )
        numpy.testing.assert_almost_equal(
            dist_bins, [0., 10., 20., 30., 40., 50., 60., 70., 80.]
        )
        numpy.testing.assert_almost_equal(
            lat_bins, [-0.6, -0.4, -0.2, 0., 0.2, 0.4, 0.6]
        )
        numpy.testing.assert_almost_equal(
            lon_bins, [-0.6, -0.4, -0.2, 0., 0.2, 0.4, 0.6]
        )
        numpy.testing.assert_almost_equal(
            eps_bins, [-3., -1., 1., 3.]
        )
        self.assertEqual(trt_bins, ['Active Shallow Crust'])

        expected_matrix = numpy.fromstring("""\
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\
""".decode('base64').decode('zip')).reshape((8, 8, 6, 6, 3, 1))
        numpy.testing.assert_almost_equal(diss_matrix, expected_matrix)
