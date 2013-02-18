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
